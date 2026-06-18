# -*- coding: utf-8 -*-
"""대용량 스트리밍 적재/조회 — save_stream + PostgresDataSource.stream_jsonl/get (라운드트립).

검증:
  ST1 save_stream 이 N행을 행-테이블에 적재 (배치 경계 넘김)
  ST2 _workspace 엔 marker 만 (거대 blob 아님)
  ST3 get() → 전체 list[dict] 복원 (내용·순서 일치)
  ST4 stream_jsonl() → generator 로 한 행씩 (전수 일치)
  ST5 has / list_sources 동작
DB 미가용 시 skip. throwaway schema(test_pgstream) drop.
"""
from __future__ import annotations

import types

import pytest

psycopg = pytest.importorskip("psycopg")

from app.data_pg_util import STREAM_MARKER_KEY, connect, data_dsn  # noqa: E402
from app.data_sources.postgres import PostgresDataSource  # noqa: E402
from app.workspace.postgres import PostgresWorkspace  # noqa: E402

CLIENT = "test_pgstream"
SOURCE_ID = "ga4_traffic_source"      # registry 의 .jsonl source
FILENAME = "ga4_traffic_source.jsonl"
N = 1200                               # batch_size=500 → 3배치 (경계 검증)


def _records(n):
    for i in range(n):
        yield {"event_name": "session_start", "i": i, "nested": {"src": f"s{i % 3}"}}


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
    loc = ws.save_stream("raw", FILENAME, _records(N), client=CLIENT, batch_size=500)
    yield PostgresDataSource(), loc
    with connect() as conn, conn.cursor() as cur:
        cur.execute(f'DROP SCHEMA IF EXISTS "{CLIENT}" CASCADE')
        conn.commit()


# ── ST1: 행-테이블 적재 ──
def test_rows_inserted(seeded):
    _, loc = seeded
    assert f"streamed {N} rows" in loc
    with connect() as conn, conn.cursor() as cur:
        cur.execute(f'SELECT count(*) FROM "{CLIENT}".ga4_traffic_source_raw')
        assert cur.fetchone()[0] == N


# ── ST2: _workspace 엔 marker 만 (거대 blob 아님) ──
def test_workspace_holds_marker_only(seeded):
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT payload FROM \"{CLIENT}\"._workspace WHERE layer='raw' AND key=%s",
            (FILENAME,),
        )
        payload = cur.fetchone()[0]
    assert payload.get(STREAM_MARKER_KEY) == "ga4_traffic_source_raw"
    assert payload["count"] == N
    assert "data" not in payload  # 실데이터는 marker 에 없음


# ── ST3: get() 전체 복원 ──
def test_get_reconstructs_full_list(seeded):
    ds, _ = seeded
    data = ds.get(CLIENT, SOURCE_ID)
    assert isinstance(data, list)
    assert len(data) == N
    assert data[0]["i"] == 0 and data[-1]["i"] == N - 1
    assert data[5]["nested"] == {"src": "s2"}  # 5 % 3 = 2


# ── ST4: stream_jsonl generator ──
def test_stream_jsonl_yields_all(seeded):
    ds, _ = seeded
    gen = ds.stream_jsonl(CLIENT, SOURCE_ID)
    assert isinstance(gen, types.GeneratorType)
    seen = [rec["i"] for rec in gen]
    assert seen == list(range(N))


# ── ST5: has / list_sources ──
def test_has_and_list(seeded):
    ds, _ = seeded
    assert ds.has(CLIENT, SOURCE_ID) is True
    assert SOURCE_ID in ds.list_sources(CLIENT)
