# -*- coding: utf-8 -*-
"""Phase 1 Batch 4 (Trend) — reviews + daily_performance + ml_model(M3) 8 pipeline.

  K14~K17 daily_performance_totals (cache 공유)
  C07 일별 area (daily_performance_aggregate 재사용)
  C08 감성 도넛 (MockMlModel — clumi.json 17/3/4)
  C12 키워드 Top10 (MockMlModel — 보습 최상위)
  O03 최근 리뷰 6 (작성일 desc)
"""
from __future__ import annotations

import asyncio

import pytest

from app.data_sources import get_default_data_source, reset_data_source
from app.dream_agent.tools.shared.storage import FileStorage, reset_storage, set_storage
from app.ml_models import reset_ml_model
from app.pipelines import PipelineRunner, list_pipelines, load_pipeline
from app.schemas.inputs import load_reviews

PER = {"client": "clumi", "period": "2026-04"}
CLIENT = {"client": "clumi"}


@pytest.fixture(autouse=True)
def _isolated(tmp_path):
    reset_data_source()
    reset_ml_model()  # 기본 MockMlModel (data/ml_mock/*/clumi.json)
    set_storage(FileStorage(tmp_path))
    yield
    reset_storage()
    reset_ml_model()


def _run(name, variables, runner=None):
    return asyncio.run((runner or PipelineRunner()).run(load_pipeline(name), variables))


def test_reviews_schema_load():
    reviews = load_reviews(get_default_data_source().get("clumi", "reviews"))
    assert len(reviews.rows) == 24
    assert reviews.rows[0].review_id == "RV-001"


def test_k14_totals():
    r = _run("trend_kpi_impressions", PER)
    assert r.status == "completed", r.error
    out = r.output
    assert {"total_impressions", "total_clicks", "total_conversions", "total_ad_cost"} <= set(out)
    # ★ A-5.3 canonical 앵커 — 옛 csv(1,548,400/58,470/2,010/26,579,010) → canonical 진짜 raw 합.
    # 값 고정으로 향후 silent drift 차단(critic 권장).
    assert out["total_impressions"] == 4_834_911
    assert out["total_clicks"] == 63_659
    assert out["total_conversions"] == 1_695
    assert out["total_ad_cost"] == 26_735_453


def test_k14_k15_cache_shared():
    runner = PipelineRunner()
    _run("trend_kpi_impressions", PER, runner=runner)
    r2 = _run("trend_kpi_clicks", PER, runner=runner)  # 동일 cache key
    assert r2.cache_hit is True


def test_c07_area_timeseries():
    r = _run("trend_area_3metric", PER)
    assert r.status == "completed", r.error
    assert len(r.output["rows"]) == 30  # 30 distinct dates (canonical 전체월, A-5.3 — 옛 csv는 8일)
    assert "impressions" in r.output["rows"][0]


def test_c08_sentiment_from_ml_mock():
    r = _run("trend_pie_sentiment", CLIENT)
    assert r.status == "completed", r.error
    assert (r.output["positive"], r.output["neutral"], r.output["negative"]) == (17, 3, 4)
    assert r.output["total"] == 24


def test_c12_keywords_from_ml_mock():
    r = _run("trend_bar_keywords_top10", CLIENT)
    assert r.status == "completed", r.error
    assert len(r.output["rows"]) == 10
    assert r.output["rows"][0]["keyword"] == "보습"


def test_o03_recent_reviews():
    r = _run("trend_cards_recent_reviews", CLIENT)
    assert r.status == "completed", r.error
    assert r.output["count"] == 6
    assert r.output["rows"][0]["date"] == "2026-04-21"  # 최신


def test_catalog_trend_has_8():
    tr = [p for p in list_pipelines() if p.category == "trend"]
    assert len(tr) == 8, sorted(p.name for p in tr)
