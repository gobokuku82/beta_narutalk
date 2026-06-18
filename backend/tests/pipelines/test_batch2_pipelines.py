# -*- coding: utf-8 -*-
"""Phase 1 Batch 2 (dashboard_v1) — clumi mock raw 기반 6 pipeline 검증.

clumi 단일 client + 표준 영어 컬럼 mock raw (normalizer 없음).
컬럼명 = schemas/inputs Pydantic 한 곳 집중. metric tool = generic (op·field).

  S  schema 로드 (campaigns 12 / daily는 canonical 전환·로더 폐기 A-5.3)
  K10 count=12 / K11 active=8 / K12 budget=158,000,000 / K13 roas avg=340.0
  C04 일별 라인 30 date (A-5.3 canonical) / T04 테이블 12행
  + catalog dashboard_v1 = 6 + schema 검증 OK
"""
from __future__ import annotations

import asyncio

import pytest

from app.data_sources import get_default_data_source, reset_data_source
from app.dream_agent.tools.shared.storage import FileStorage, reset_storage, set_storage
from app.pipelines import PipelineRunner, list_pipelines, load_pipeline
from app.schemas.inputs import load_campaigns

CLIENT = {"client": "clumi"}
PER = {"client": "clumi", "period": "2026-04"}


@pytest.fixture(autouse=True)
def _isolated(tmp_path):
    """실 DataSource(campaigns.csv) + tmp workspace(compute path 강제)."""
    reset_data_source()
    set_storage(FileStorage(tmp_path))
    yield
    reset_storage()


def _run(name: str, variables: dict):
    return asyncio.run(PipelineRunner().run(load_pipeline(name), variables))


def test_schemas_load_from_raw():
    ds = get_default_data_source()
    camps = load_campaigns(ds.get("clumi", "campaigns"))
    assert len(camps.rows) == 12
    assert camps.rows[0].campaign_id == "BRP-001"
    assert camps.rows[0].monthly_budget == 25_000_000
    # daily_performance 로더 단언 제거 (A-5.3): csv·로더 폐기, daily는 canonical 집계로 전환.


def test_k10_campaign_total():
    r = _run("dashboard_v1_kpi_campaign_total", CLIENT)
    assert r.status == "completed", r.error
    assert r.output["value"] == 12
    assert r.validation["checks"][0]["ok"]  # schema


def test_k11_campaign_active():
    r = _run("dashboard_v1_kpi_campaign_active", CLIENT)
    assert r.output["value"] == 8  # active 8 / ended 2 / scheduled 2


def test_k12_budget_total():
    r = _run("dashboard_v1_kpi_budget_total", CLIENT)
    assert r.output["value"] == 158_000_000


def test_k13_target_roas_avg():
    r = _run("dashboard_v1_kpi_target_roas_avg", CLIENT)
    assert r.output["value"] == 340.0


def test_c04_daily_line():
    r = _run("dashboard_v1_daily_performance_line", PER)
    assert r.status == "completed", r.error
    assert len(r.output["rows"]) == 30  # 30 distinct dates (canonical 전체월, A-5.3 — 옛 csv는 8일)
    assert {"date", "ad_cost", "conversion_revenue"} <= set(r.output["rows"][0])


def test_t04_table():
    r = _run("dashboard_v1_table_campaigns", CLIENT)
    assert r.status == "completed", r.error
    assert r.output["count"] == 12
    assert "campaign_id" in r.output["rows"][0]


def test_catalog_dashboard_v1_has_6():
    dv1 = [p for p in list_pipelines() if p.category == "dashboard_v1"]
    assert len(dv1) == 6, sorted(p.name for p in dv1)
