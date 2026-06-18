# -*- coding: utf-8 -*-
"""Canonical 파이프라인 연결 검증 (① 연결 테스트 — 페이지 아님).

오너 roadmap ①: "새 데이터구조(raw→normalized→computed)가 *제대로 연결됐는지* 테스트."
각 in-scope 소스가 raw→translator(normalized/computed)→라이브 DB 테이블→API 까지
끊김 없이 흐르는지 + 정답(MER 4.46, 가 결정 A-5.2 google 포함) 재현 + gap 추적 기제 유지(silent 금지).

읽기 전용 — 라이브 clumi 미변경(translator.execute=순수, DB/API는 SELECT만).
실행: uv run pytest tests/canonical/test_pipeline_connection.py -v
"""
from __future__ import annotations

import asyncio

import httpx
import pytest
from httpx import ASGITransport

CLIENT = "clumi"
PERIOD = "2026-04"
# 가 결정 A-5.2(2026-06-17): google 광고 매체 포함 re-baseline (18.3M/6.53 → 26.8M/4.46).
EXPECT_TOTAL, EXPECT_MER = 26_806_923, 4.46

# in-scope("필요시 피봇" 범위) 소스 stem → 기대 normalized 행수 / computed 유무
IN_SCOPE = {
    "meta_ads_performance": (90, True),
    "naver_searchad": (180, True),
    "naver_advoost": (90, True),
    "google_ads_performance": (180, True),   # 가 결정 A-5.2: 피봇 완료(종전 KNOWN_GAPS)
    "kakao_bizmessage": (2, True),
    "naver_talktalk": (2, True),
    "orders": (1919, False),   # 주문=normalized만(computed 없음, blended 분자)
}
# 알려진 gap(미피봇 — 필요시 후속). google 은 A-5.2 피봇 완료 → 현 canonical 채널 gap 0. (기제는 유지: 후속 gap 추적용)
KNOWN_GAPS = ()


async def _app_client():
    import asyncpg
    from fastapi import FastAPI
    from app.data_pg_util import data_dsn
    from api_v2.routes.canonical import router
    try:
        pool = await asyncpg.create_pool(data_dsn(), min_size=1, max_size=2)
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"data DB 미가용: {e}")
    app = FastAPI()
    app.state.data_db_pool = pool
    app.include_router(router)
    return httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://t"), pool


async def _catalog():
    ac, pool = await _app_client()
    try:
        async with ac:
            return (await ac.get("/api/canonical/catalog", params={"client": CLIENT})).json()
    finally:
        await pool.close()


# ── 1단: raw → translator (순수, DB 무관) — 새 normalized/computed 산출 정합 ──
def test_translator_emits_normalized_and_reproduces_answer():
    """translator가 raw에서 normalized/computed/blended를 산출 + 옛 정답 재현(=옛 normalized 오류 교정)."""
    from app.dream_agent.models import ExecutionContext
    from app.dream_agent.tools.registry import get_registry
    from app.dream_agent.tools.normalization.canonical_translator import CanonicalTranslator
    tool = CanonicalTranslator(get_registry().get("canonical_translator"))
    result = asyncio.run(tool.execute({"period": PERIOD},
                                      ExecutionContext(session_id="t", plan_id="t", client_id=CLIENT)))
    for stem, (n, has_comp) in IN_SCOPE.items():
        ch = next(c for c, v in result["normalized"].items() if v["table"] == f"{stem}_normalized")
        assert len(result["normalized"][ch]["rows"]) == n, f"{stem} normalized 행수"
        if has_comp:
            assert ch in result["computed_tables"], f"{stem} computed 누락"
    assert result["computed"]["total_marketing_cost_krw"] == EXPECT_TOTAL
    assert abs(result["computed"]["mer"] - EXPECT_MER) <= 0.05


# ── 2단: 라이브 DB 적재 연결 — 카탈로그가 in-scope 테이블 전부 노출 + 행수 ──
async def test_live_db_has_all_in_scope_tables():
    """라이브 clumi에 in-scope normalized(+computed) 테이블이 실제 존재 + 행수 일치 (DB 연결)."""
    data = await _catalog()
    tables = {t["table"]: t["row_count"] for s in data["sources"] for t in s["tables"]}
    for stem, (n, has_comp) in IN_SCOPE.items():
        assert tables.get(f"{stem}_normalized") == n, f"{stem}_normalized DB 미연결/행수 {tables.get(f'{stem}_normalized')}≠{n}"
        if has_comp:
            assert f"{stem}_computed" in tables, f"{stem}_computed DB 미연결"
    assert "blended_computed" in tables


# ── 3단: API 연결 — DB → /api/canonical 서빙 + 교차세계 정답 ──
async def test_api_serves_marketing_performance():
    """DB→API 연결: marketing-performance가 MER 4.46·총비용 26.8M 재현 (가 결정 google 포함)."""
    ac, pool = await _app_client()
    try:
        async with ac:
            r = await ac.get("/api/canonical/marketing-performance",
                             params={"client": CLIENT, "period": PERIOD})
        assert r.status_code == 200, r.text
        kpi = r.json()["kpi"]
        assert kpi["total_marketing_cost_krw"] == EXPECT_TOTAL
        assert abs(kpi["mer"] - EXPECT_MER) <= 0.05
    finally:
        await pool.close()


# ── 4단: 알려진 gap 명시 (silent 금지) — 미피봇 도메인이 분명히 부재 ──
async def test_known_gaps_are_absent_not_silent():
    """미피봇 소스가 카탈로그에 *없음*을 명시 검증 — 연결됐다 착각 금지. (google=A-5.2 피봇완료 → 현 gap 0, 기제는 후속 gap 대비 유지.)"""
    data = await _catalog()
    stems = {s["source"] for s in data["sources"]}
    for gap in KNOWN_GAPS:
        assert gap not in stems, f"{gap}=미피봇 가정인데 등장 — 가정 갱신 필요"
