# -*- coding: utf-8 -*-
"""pushdown v1 (ADR-031) — Postgres override + 교차 일관성 + G28 마커 가드.

검증:
  PQ1 generic 행-테이블 (_id, data jsonb) — query/aggregate SQL 경로
  PQ2 typed 행-테이블 (수집 경로별 모양 — §8 V1 실측) — 동일 답
  PQ3 blob 소스 — 기본 구현 fallback (super)
  PQ4 교차 일관성 (ADR-031-3): 같은 데이터 File vs Postgres 동일 결과
  PQ5 G28 save 라우팅 — 기존 마커 위 blob save 금지 (save_stream 재라우팅) + 대용량 자동 스트림
  PQ6 G28 가드 (clumi 실DB): GA4 마커 2종 존재 + 행-테이블 생존 assert (침묵 강등 → RED)
DB 미가용 시 skip (PQ6 제외 의도 — 단 동일 DB 라 동시 skip). throwaway schema drop.
"""
from __future__ import annotations

import json

import pytest

psycopg = pytest.importorskip("psycopg")

from psycopg import sql  # noqa: E402

import app.workspace.postgres as pgws_mod  # noqa: E402
from app.data_pg_util import STREAM_MARKER_KEY, connect, data_dsn, write_typed_table  # noqa: E402
from app.data_sources.file import FileDataSource  # noqa: E402
from app.data_sources.postgres import PostgresDataSource  # noqa: E402
from app.workspace.postgres import PostgresWorkspace  # noqa: E402

CLIENT = "test_pgquery"
SRC_STREAM = "ga4_traffic_source"          # registry .jsonl — generic 행-테이블 fixture
SRC_TYPED = "ga4_page_events"              # registry .jsonl — typed 행-테이블 fixture
SRC_BLOB = "naver_talktalk"                # registry .json — blob fallback fixture

EVENTS = [
    {"event_name": "session_start", "event_date": "20260401", "value": 10, "src": "meta"},
    {"event_name": "session_start", "event_date": "20260402", "value": 5, "src": "naver"},
    {"event_name": "purchase", "event_date": "20260403", "value": 3, "src": "meta"},
    {"event_name": "purchase", "event_date": "20260301", "value": None, "src": None},
]


@pytest.fixture(scope="module")
def seeded():
    try:
        with connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
    except psycopg.Error as e:
        pytest.skip(f"octormate_data 미가용 — skip ({data_dsn()}): {e}")

    ws = PostgresWorkspace()
    with connect() as conn, conn.cursor() as cur:
        cur.execute(f'DROP SCHEMA IF EXISTS "{CLIENT}" CASCADE')
        conn.commit()

    # generic: save_stream 정석 경로
    ws.save_stream("raw", "ga4_traffic_source.jsonl", iter(EVENTS), client=CLIENT)
    # typed: write_typed_table + 수동 마커 (V1 실측 모양 재현 — 수집 사고가 만들던 형태)
    with connect() as conn:
        write_typed_table(conn, CLIENT, "ga4_page_events_raw", EVENTS)
        conn.commit()
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("INSERT INTO {}.{} (layer, key, payload) VALUES (%s,%s,%s) "
                        "ON CONFLICT (layer, key) DO UPDATE SET payload=EXCLUDED.payload").format(
                    sql.Identifier(CLIENT), sql.Identifier("_workspace")),
                ("raw", "ga4_page_events.jsonl",
                 psycopg.types.json.Json({STREAM_MARKER_KEY: "ga4_page_events_raw",
                                          "format": "jsonl", "count": len(EVENTS)})),
            )
            conn.commit()
    # blob: 소형 json — save() 경로 (threshold 미만 → blob 유지)
    ws.save("raw", "naver_talktalk.json", EVENTS, client=CLIENT)

    yield PostgresDataSource()
    with connect() as conn, conn.cursor() as cur:
        cur.execute(f'DROP SCHEMA IF EXISTS "{CLIENT}" CASCADE')
        conn.commit()


# ── PQ1 generic SQL 경로 ──

def test_pq1_generic_query_and_aggregate(seeded):
    ds = seeded
    rows = ds.query(CLIENT, SRC_STREAM, where={"event_name": "session_start"},
                    columns=["src", "value", "ghost"])
    assert rows == [{"src": "meta", "value": 10, "ghost": None},
                    {"src": "naver", "value": 5, "ghost": None}]
    assert ds.aggregate(CLIENT, SRC_STREAM, op="count", by="event_name") == {
        "session_start": 2, "purchase": 2}
    assert ds.aggregate(CLIENT, SRC_STREAM, op="sum", column="value",
                        where={"event_date__prefix": "202604"}) == 18.0
    assert ds.aggregate(CLIENT, SRC_STREAM, op="count", by="src") == {
        "meta": 2, "naver": 1, None: 1}


# ── PQ2 typed 모양 — 동일 답 ──

def test_pq2_typed_same_answers(seeded):
    ds = seeded
    rows = ds.query(CLIENT, SRC_TYPED, where={"event_name": "session_start"},
                    columns=["src", "value", "ghost"])
    assert rows == [{"src": "meta", "value": 10, "ghost": None},
                    {"src": "naver", "value": 5, "ghost": None}]
    assert ds.aggregate(CLIENT, SRC_TYPED, op="count", by="event_name") == {
        "session_start": 2, "purchase": 2}
    assert ds.aggregate(CLIENT, SRC_TYPED, op="sum", column="value") == 18.0
    # 부재 컬럼: where → 빈 결과 / by → 전부 None 그룹 / sum → 0
    assert ds.query(CLIENT, SRC_TYPED, where={"ghost": "x"}) == []
    assert ds.aggregate(CLIENT, SRC_TYPED, op="count", by="ghost") == {None: 4}
    assert ds.aggregate(CLIENT, SRC_TYPED, op="sum", column="ghost") == 0.0


# ── PQ3 blob fallback ──

def test_pq3_blob_falls_back_to_base(seeded):
    ds = seeded
    assert ds.aggregate(CLIENT, SRC_BLOB, op="count") == 4
    rows = ds.query(CLIENT, SRC_BLOB, where={"src": "meta"}, columns=["value"])
    assert rows == [{"value": 10}, {"value": 3}]


# ── PQ4 교차 일관성 (ADR-031-3) ──

def test_pq4_cross_backend_same_answers(seeded, tmp_path):
    pg = seeded
    raw = tmp_path / "data" / CLIENT / "raw"
    raw.mkdir(parents=True)
    (raw / "ga4_traffic_source.jsonl").write_text(
        "\n".join(json.dumps(r) for r in EVENTS), encoding="utf-8")
    fl = FileDataSource(tmp_path)

    calls = [
        dict(where={"event_name": "session_start"}, columns=["src", "value"]),
        dict(where={"event_date__prefix": "202604"}),
        dict(where=None, columns=None),
    ]
    for kw in calls:
        assert fl.query(CLIENT, SRC_STREAM, **kw) == pg.query(CLIENT, SRC_STREAM, **kw)
    aggs = [
        dict(op="count"), dict(op="count", by="event_name"), dict(op="count", by="src"),
        dict(op="sum", column="value"), dict(op="sum", column="value", by="src"),
        dict(op="sum", column="value", where={"event_name": "ghost"}),
    ]
    for kw in aggs:
        assert fl.aggregate(CLIENT, SRC_STREAM, **kw) == pg.aggregate(CLIENT, SRC_STREAM, **kw)


# ── PQ5 G28 save 라우팅 ──

def test_pq5_g28_save_routing_preserves_marker(seeded):
    ws = PostgresWorkspace()
    # 기존 마커 위에 blob save 시도 → save_stream 재라우팅 (마커 생존)
    loc = ws.save("raw", "ga4_traffic_source.jsonl", EVENTS, client=CLIENT)
    assert "streamed" in loc
    payload = ws.load("raw", "ga4_traffic_source.jsonl", client=CLIENT)
    assert payload.get(STREAM_MARKER_KEY) == "ga4_traffic_source_raw"
    # 행-테이블이 generic 으로 생존
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema=%s AND table_name='ga4_traffic_source_raw' "
                    "ORDER BY ordinal_position", (CLIENT,))
        assert [r[0] for r in cur.fetchall()] == ["_id", "data"]


def test_pq5b_g28_large_list_auto_streams(seeded, monkeypatch):
    monkeypatch.setattr(pgws_mod, "STREAM_ROUTE_THRESHOLD", 3)
    ws = PostgresWorkspace()
    loc = ws.save("raw", "ga4_page_events.jsonl", EVENTS, client=CLIENT)   # 4행 ≥ 3
    assert "streamed" in loc
    payload = ws.load("raw", "ga4_page_events.jsonl", client=CLIENT)
    assert payload.get(STREAM_MARKER_KEY) == "ga4_page_events_raw"


# ── PQ7 V5 — 시범 tool 정답값 3 + S067 을 postgres 경로에서 실측 (계획 §8 V5: skip 0 전제) ──

def test_pq7_v5_ga4_answers_on_postgres_path(seeded):
    import asyncio
    from app.data_sources import reset_data_source, set_data_source
    from app.dream_agent.models import ExecutionContext
    from app.dream_agent.tools.metrics.ga4_session_aggregator import Ga4SessionAggregator
    from app.dream_agent.tools.metrics.signup_conversion import SignupConversion
    from app.dream_agent.tools.registry import get_registry

    ctx = ExecutionContext(session_id="v5", plan_id="v5", client_id="clumi")
    set_data_source(PostgresDataSource())
    try:
        agg = Ga4SessionAggregator(get_registry().get("ga4_session_aggregator"))
        r = asyncio.run(agg.execute({}, ctx))
        assert r["session_start_total"] == 24_000
        assert r["by_event"]["first_visit"] == 12_496
        assert r["by_event"]["purchase"] == 1_823
        sc = SignupConversion(get_registry().get("signup_conversion"))
        s = asyncio.run(sc.execute({"period": "2026-04"}, ctx))
        assert s["signup_conversion_pct"] == 2.50 and s["sessions"] == 24_000
    finally:
        reset_data_source()


# ── PQ6 G28 가드 — clumi 실DB 마커 생존 (계획 §8 V2·V5: fixture 아닌 실DB) ──

def test_pq6_clumi_live_markers_alive(seeded):
    ws = PostgresWorkspace()
    for key, table in (("ga4_traffic_source.jsonl", "ga4_traffic_source_raw"),
                       ("ga4_page_events.jsonl", "ga4_page_events_raw")):
        payload = ws.load("raw", key, client="clumi")
        assert isinstance(payload, dict) and payload.get(STREAM_MARKER_KEY) == table, (
            f"G28 RED: clumi {key} 마커 침묵 소멸 — 외부 수집 save 가 blob 으로 덮음 의심. "
            f"복구: V1 절차 (file → save_stream 재적재)")
        with connect() as conn, conn.cursor() as cur:
            cur.execute(sql.SQL("SELECT count(*) FROM {}.{}").format(
                sql.Identifier("clumi"), sql.Identifier(table)))
            n = cur.fetchone()[0]
        assert n == payload["count"], f"행-테이블 {table} 행수 {n} ≠ 마커 count {payload['count']}"
