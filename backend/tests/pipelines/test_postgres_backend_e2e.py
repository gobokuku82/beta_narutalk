# -*- coding: utf-8 -*-
"""항목① E2E — DATA_BACKEND=postgres 전체 체인 (raw 읽기 → 파이프라인 → 정제/계산 쓰기).

set_data_source(PostgresDataSource) + set_workspace(PostgresWorkspace) 로 양쪽 전환 후,
throwaway client schema(e2e_pg) 에 raw 시드 → 실 PipelineRunner 로 dashboard_v1 실행 →
  E1 KPI 값이 clumi 와 동일 (raw 가 Postgres 에서 읽힘을 입증 — FileDataSource 대체됨)
  E2 실행 후 normalized/computed 산출이 octormate_data e2e_pg._workspace 에 기록됨 (출력도 Postgres)
테스트 후 schema drop. DB 미가용 시 skip.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

psycopg = pytest.importorskip("psycopg")

from app.data_pg_util import connect, data_dsn  # noqa: E402
from app.data_sources import reset_data_source, set_data_source  # noqa: E402
from app.data_sources.file import FileDataSource  # noqa: E402
from app.data_sources.postgres import PostgresDataSource  # noqa: E402
from app.pipelines import PipelineRunner, load_pipeline  # noqa: E402
from app.workspace import reset_workspace, set_workspace  # noqa: E402
from app.workspace.postgres import PostgresWorkspace  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
E2E_CLIENT = "e2e_pg"
# dashboard_v1 KPI(campaigns) + daily_performance_line 이 필요로 하는 raw source.
# A-5.3: daily_performance_aggregate가 canonical_translator(전 채널 normalize) 경유로 전환됨 →
# 옛 daily_performance.csv 대신 canonical 원천 raw 7종을 Postgres 에 시드해야 함.
SEED_SOURCES = [
    "campaigns",
    "meta_ads_performance", "naver_searchad", "naver_advoost", "google_ads_performance",
    "kakao_bizmessage", "naver_talktalk", "orders",
]


@pytest.fixture(scope="module")
def pg_backend():
    # DB 가용 확인
    try:
        with connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
    except psycopg.Error as e:
        pytest.skip(f"octormate_data 미가용 — skip ({data_dsn()}): {e}")

    # e2e_pg schema 정리 후 raw 시드 (clumi 파일 → Postgres raw, client=e2e_pg)
    file_ds = FileDataSource(REPO_ROOT)
    pg_ws = PostgresWorkspace()
    with connect() as conn, conn.cursor() as cur:
        cur.execute(f'DROP SCHEMA IF EXISTS "{E2E_CLIENT}" CASCADE')
        conn.commit()
    for sid in SEED_SOURCES:
        pg_ws.save("raw", file_ds.mapping[sid], file_ds.get("clumi", sid), client=E2E_CLIENT)

    # 양쪽 백엔드 Postgres 로 전환
    set_data_source(PostgresDataSource())
    set_workspace(pg_ws)
    yield
    reset_data_source()
    reset_workspace()
    with connect() as conn, conn.cursor() as cur:
        cur.execute(f'DROP SCHEMA IF EXISTS "{E2E_CLIENT}" CASCADE')
        conn.commit()


def _run(name: str, variables: dict):
    return asyncio.run(PipelineRunner().run(load_pipeline(name), variables))


# ── E1: raw 가 Postgres 에서 읽힘 (값이 clumi 와 동일) ──
def test_kpi_campaign_total_from_postgres_raw(pg_backend):
    r = _run("dashboard_v1_kpi_campaign_total", {"client": E2E_CLIENT})
    assert r.status == "completed", r.error
    assert r.output["value"] == 12  # clumi campaigns 12행 — Postgres raw 경유


def test_kpi_budget_total_from_postgres_raw(pg_backend):
    r = _run("dashboard_v1_kpi_budget_total", {"client": E2E_CLIENT})
    assert r.status == "completed", r.error
    assert r.output["value"] == 158_000_000


def test_daily_line_from_postgres_raw(pg_backend):
    r = _run("dashboard_v1_daily_performance_line", {"client": E2E_CLIENT, "period": "2026-04"})
    assert r.status == "completed", r.error
    assert len(r.output["rows"]) == 30  # A-5.3 canonical 전체월 (옛 csv는 8일)


# ── E2: 산출(normalized/computed)이 Postgres 에 기록됨 ──
def test_outputs_written_to_postgres(pg_backend):
    # 파이프라인 실행이 e2e_pg._workspace 에 normalized/computed 를 적재
    _run("dashboard_v1_kpi_campaign_total", {"client": E2E_CLIENT})
    _run("dashboard_v1_daily_performance_line", {"client": E2E_CLIENT, "period": "2026-04"})
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT layer, count(*) FROM e2e_pg._workspace "
            "WHERE layer IN ('normalized','computed') GROUP BY layer"
        )
        counts = dict(cur.fetchall())
    # 적어도 한 종류 이상의 산출이 Postgres 에 기록됨
    assert sum(counts.values()) > 0, f"산출 미기록 (counts={counts})"
