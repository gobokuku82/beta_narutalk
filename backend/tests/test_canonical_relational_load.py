# -*- coding: utf-8 -*-
"""test_canonical_relational_load.py — DB제작 Step3~5: translator 행 emitter + 정형 적재.

세부05 §6 검증: 소스별 행 emit이 (1)기대 행수 (2)합 불변(Σ행=채널합) (3)PK 유일·non-null
(4)행단위 lineage 를 만족하고, MER 4.46·26.8M(가 결정 A-5.2 google 포함). + 정형 테이블 UPSERT 멱등.

실행: uv run pytest backend/tests/test_canonical_relational_load.py -v
"""
from __future__ import annotations

import asyncio

import pytest

PERIOD = "2026-04"
# 가 결정 A-5.2(2026-06-17): google 광고 매체 포함 re-baseline (18.3M/6.53 → 26.8M/4.46).
AD = ("meta", "naver_sa", "advoost", "google")
MSG = ("kakao", "talktalk")
EXPECT_ROWS = {"meta": 90, "naver_sa": 180, "advoost": 90, "google": 180, "kakao": 2, "talktalk": 2, "orders": 1919}
EXPECT_SUM = {"meta": 9_235_826, "naver_sa": 5_999_627, "advoost": 3_000_000, "google": 8_500_000,
              "kakao": 59_020, "talktalk": 12_450, "orders": 119_539_660}
EXPECT_TOTAL, EXPECT_MER = 26_806_923, 4.46


def _measure_col(channel: str) -> str:
    return "ad_cost_krw" if channel in AD else ("msg_cost_krw" if channel in MSG else "order_revenue_krw")


def _ctx():
    from app.dream_agent.models import ExecutionContext
    return ExecutionContext(session_id="t", plan_id="t", client_id="clumi")


@pytest.fixture(scope="module")
def result():
    from app.dream_agent.tools.registry import get_registry
    from app.dream_agent.tools.normalization.canonical_translator import CanonicalTranslator
    tool = CanonicalTranslator(get_registry().get("canonical_translator"))
    return asyncio.run(tool.execute({"period": PERIOD}, _ctx()))


# ── 순수(행 emit) 검증 — DB 불필요 ──
def test_row_counts(result):
    for c, v in result["normalized"].items():
        assert len(v["rows"]) == EXPECT_ROWS[c], f"{c}: {len(v['rows'])} != {EXPECT_ROWS[c]}"


def test_sum_invariance(result):
    """★ 행을 펼쳐도 Σ측정값 == 채널합 (피봇 thesis 유지). naver_sa 1680→180 그룹핑 포함."""
    for c, v in result["normalized"].items():
        col = _measure_col(c)
        s = sum(r.get(col, 0) for r in v["rows"])
        assert s == EXPECT_SUM[c], f"{c} {col}: {s:,} != {EXPECT_SUM[c]:,}"


def test_pk_unique_and_nonnull(result):
    for c, v in result["normalized"].items():
        pks = [tuple(r[k] for k in v["pk_cols"]) for r in v["rows"]]
        assert len(set(pks)) == len(pks), f"{c}: PK 중복"
        assert all(all(r[k] is not None for k in v["pk_cols"]) for r in v["rows"]), f"{c}: PK null"


def test_lineage_per_row(result):
    for c, v in result["normalized"].items():
        assert all(r.get("_lineage") for r in v["rows"]), f"{c}: 행 lineage 비어있음"


def test_mer_preserved(result):
    assert result["computed"]["total_marketing_cost_krw"] == EXPECT_TOTAL
    assert abs(result["computed"]["mer"] - EXPECT_MER) <= 0.05


def test_schema_spec_present(result):
    """각 소스가 적재용 spec(table·pk_cols·col_types)을 동반 — persist 계약."""
    for v in result["normalized"].values():
        assert v["table"].endswith("_normalized")
        assert v["pk_cols"] and v["col_types"]
        assert "_lineage" in v["col_types"]


# ── 정형 적재(persist) 검증 — 임시 schema (live DB 필요) ──
@pytest.fixture
def temp_schema():
    from app.data_pg_util import connect
    from psycopg import sql
    s = "test_canonical_rel"
    try:
        with connect() as conn:
            with conn.cursor() as c:
                c.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(s)))
                c.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(s)))
            conn.commit()
    except Exception as e:
        pytest.skip(f"live DB 미가용: {e}")
    yield s
    with connect() as conn:
        with conn.cursor() as c:
            c.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(s)))
        conn.commit()


def test_persist_and_idempotent(result, temp_schema):
    from app.data_pg_util import connect
    from app.dream_agent.tools.registry import get_registry
    from app.dream_agent.tools.normalization.canonical_translator import CanonicalTranslator
    from psycopg import sql
    tool = CanonicalTranslator(get_registry().get("canonical_translator"))
    out1 = tool.persist_normalized(result, temp_schema)
    out2 = tool.persist_normalized(result, temp_schema)   # 멱등(UPSERT)
    assert out1 == out2, "persist 멱등 위반"
    for v in result["normalized"].values():
        assert out1[v["table"]] == EXPECT_ROWS[v["channel"]]
    # DB 실제 행수 + 합 불변
    with connect() as conn, conn.cursor() as cur:
        for c, v in result["normalized"].items():
            cur.execute(sql.SQL("SELECT count(*) FROM {}.{}").format(
                sql.Identifier(temp_schema), sql.Identifier(v["table"])))
            assert cur.fetchone()[0] == EXPECT_ROWS[c], f"{v['table']} DB행 != {EXPECT_ROWS[c]}"
        cur.execute(sql.SQL("SELECT sum(ad_cost_krw) FROM {}.meta_ads_performance_normalized").format(
            sql.Identifier(temp_schema)))
        assert cur.fetchone()[0] == EXPECT_SUM["meta"]


# ── Step5b/6: computed (소스별 파생) + blended (period 1행) 검증 ──
COMPUTED_TABLES = {
    "meta": "meta_ads_performance_computed", "naver_sa": "naver_searchad_computed",
    "advoost": "naver_advoost_computed", "google": "google_ads_performance_computed",
    "kakao": "kakao_bizmessage_computed", "talktalk": "naver_talktalk_computed",
}


def test_computed_row_counts(result):
    """computed 행수 == normalized 행수 (행단위 1:1 파생). orders는 computed 없음."""
    ct = result["computed_tables"]
    assert "orders" not in ct, "orders는 computed 테이블 없어야(blended 분자만)"
    for c, v in ct.items():
        assert len(v["rows"]) == EXPECT_ROWS[c], f"{c} computed: {len(v['rows'])} != {EXPECT_ROWS[c]}"
        assert v["table"] == COMPUTED_TABLES[c]
        assert v["table"].endswith("_computed")


def test_computed_metrics_recompute(result):
    """파생값이 normalized 행에서 결정론적으로 재계산됨 (roas=rev/cost, msg_roi=(rev/cost-1)*100)."""
    norm, ct = result["normalized"], result["computed_tables"]
    for c in ("meta", "naver_sa", "advoost", "google"):
        nrows = {tuple(r[k] for k in norm[c]["pk_cols"]): r for r in norm[c]["rows"]}
        for cr in ct[c]["rows"]:
            n = nrows[tuple(cr[k] for k in ct[c]["pk_cols"])]
            cost, rev = n.get("ad_cost_krw", 0), n.get("conversion_revenue_krw", 0)
            assert cr["roas_x"] == (round(rev / cost, 2) if cost else None), f"{c} roas 불일치"
        if c == "meta":   # meta 전용 link_ctr_pct 존재
            assert "link_ctr_pct" in ct[c]["col_types"]
    for c in ("kakao", "talktalk"):
        assert all("msg_roi_pct" in r for r in ct[c]["rows"])


def test_blended_single_row_mer(result):
    """blended = period 1행, MER/총비용 = 정답(가 결정 A-5.2 google 포함 26.8M·4.46)."""
    b = result["blended"]
    assert b["table"] == "blended_computed" and b["pk_cols"] == ["period"]
    assert len(b["rows"]) == 1
    row = b["rows"][0]
    assert row["period"] == PERIOD
    assert row["total_marketing_cost_krw"] == EXPECT_TOTAL
    assert abs(row["mer"] - EXPECT_MER) <= 0.05
    assert row["total_order_revenue_krw"] == EXPECT_SUM["orders"]


def test_persist_computed_blended_idempotent(result, temp_schema):
    """computed/blended persist 멱등 + DB 행수 (live DB 필요)."""
    from app.data_pg_util import connect
    from app.dream_agent.tools.registry import get_registry
    from app.dream_agent.tools.normalization.canonical_translator import CanonicalTranslator
    from psycopg import sql
    tool = CanonicalTranslator(get_registry().get("canonical_translator"))
    tool.persist_normalized(result, temp_schema)   # FK는 없지만 전 레이어 동시 존재 재현
    c1 = tool.persist_computed(result, temp_schema)
    c2 = tool.persist_computed(result, temp_schema)
    bl1 = tool.persist_blended(result, temp_schema)
    bl2 = tool.persist_blended(result, temp_schema)
    assert c1 == c2 and bl1 == bl2, "computed/blended 멱등 위반"
    assert bl1["blended_computed"] == 1
    with connect() as conn, conn.cursor() as cur:
        for c, tbl in COMPUTED_TABLES.items():
            cur.execute(sql.SQL("SELECT count(*) FROM {}.{}").format(
                sql.Identifier(temp_schema), sql.Identifier(tbl)))
            assert cur.fetchone()[0] == EXPECT_ROWS[c], f"{tbl} DB행 != {EXPECT_ROWS[c]}"
        # blended MER 보존
        cur.execute(sql.SQL("SELECT total_marketing_cost_krw, mer FROM {}.blended_computed").format(
            sql.Identifier(temp_schema)))
        tot, mer = cur.fetchone()
        assert tot == EXPECT_TOTAL and abs(mer - EXPECT_MER) <= 0.05
