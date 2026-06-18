# -*- coding: utf-8 -*-
"""Phase 1 Batch 6 (Cost+AI) — budget·keyword + O05 ml_model 7 pipeline.

  K22 총예산=178,000,000 / K23 평균집행률=88.38 (cache 공유)
  K24 키워드 수=18 / C09 채널비중 4 / C10 누적 5 segment / T07 Top12 루미
  O05 AI 추천 3 카드 (MockMlModel.generate_recommendation)
  + 전체 52 pipeline 합계
"""
from __future__ import annotations

import asyncio

import pytest

from app.data_sources import get_default_data_source, reset_data_source
from app.dream_agent.tools.shared.storage import FileStorage, reset_storage, set_storage
from app.ml_models import reset_ml_model
from app.pipelines import PipelineRunner, list_pipelines, load_pipeline
from app.schemas.inputs import load_budget_allocation, load_keyword_performance

CLIENT = {"client": "clumi"}


@pytest.fixture(autouse=True)
def _isolated(tmp_path):
    reset_data_source()
    reset_ml_model()
    set_storage(FileStorage(tmp_path))
    yield
    reset_storage()
    reset_ml_model()


def _run(name, variables=CLIENT, runner=None):
    return asyncio.run((runner or PipelineRunner()).run(load_pipeline(name), variables))


def test_schemas_load():
    ds = get_default_data_source()
    assert len(load_budget_allocation(ds.get("clumi", "budget_allocation")).rows) == 5
    assert len(load_keyword_performance(ds.get("clumi", "keyword_performance")).rows) == 18


def test_k22_budget_total():
    r = _run("cost_kpi_budget_total")
    assert r.status == "completed", r.error
    assert r.output["total_budget"] == 178_000_000


def test_k23_exec_rate_and_cache_shared():
    runner = PipelineRunner()
    r22 = _run("cost_kpi_budget_total", runner=runner)
    assert r22.output["avg_exec_rate"] == 88.38
    r23 = _run("cost_kpi_exec_rate_avg", runner=runner)
    assert r23.cache_hit is True  # K22 와 동일 cache


def test_k24_keyword_metrics():
    r = _run("cost_kpi_keyword_metrics")
    assert r.status == "completed", r.error
    assert r.output["keyword_count"] == 18
    assert r.output["avg_roas"] > 0


def test_c09_channel_share():
    r = _run("cost_pie_channel_share")
    assert r.status == "completed", r.error
    rows = r.output["rows"]
    assert len(rows) == 4
    assert round(sum(x["share"] for x in rows)) == 100


def test_c10_stacked():
    r = _run("cost_bar_budget_stacked")
    assert r.status == "completed", r.error
    assert len(r.output["rows"]) == 5
    assert r.output["channels"] == ["naver", "kakao", "meta", "google"]


def test_t07_keyword_top12():
    r = _run("cost_table_keyword_top12")
    assert r.status == "completed", r.error
    assert r.output["count"] == 12
    assert r.output["rows"][0]["keyword"] == "루미"  # roas 700 최고 (브랜드명)


def test_o05_ai_recommendation():
    r = _run("cost_ai_recommendation")
    assert r.status == "completed", r.error
    assert r.output["count"] == 3
    assert r.output["rows"][0]["priority"] == "high"


def test_catalog_cost_has_7():
    cost = [p for p in list_pipelines() if p.category == "cost"]
    assert len(cost) == 7, sorted(p.name for p in cost)


def test_all_52_pipelines_total():
    """Phase 1 전체 6 batch = 52 pipeline."""
    pipelines = list_pipelines()
    by_cat: dict[str, int] = {}
    for p in pipelines:
        by_cat[p.category or "?"] = by_cat.get(p.category or "?", 0) + 1
    assert by_cat == {
        "dashboard1": 21,
        "dashboard_v1": 6,
        "channel": 3,
        "trend": 8,
        "creative": 7,
        "cost": 7,
    }, by_cat
    assert len(pipelines) == 52
