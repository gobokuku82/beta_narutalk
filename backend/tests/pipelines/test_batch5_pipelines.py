# -*- coding: utf-8 -*-
"""Phase 1 Batch 5 (Creative) — creatives·ab_tests + ml_model(M3) 7 pipeline.

  K18 count=12 / K19 avg CTR / K20 avg ROAS / K21 피로=3 (MockMlModel fatigue)
  C11 AI 5축 (MockMlModel ai_axes — ai_clear 80) / O04 카드 Top9(ROAS desc) / T06 AB 테이블
"""
from __future__ import annotations

import asyncio

import pytest

from app.data_sources import get_default_data_source, reset_data_source
from app.dream_agent.tools.shared.storage import FileStorage, reset_storage, set_storage
from app.ml_models import reset_ml_model
from app.pipelines import PipelineRunner, list_pipelines, load_pipeline
from app.schemas.inputs import load_ab_tests, load_creatives

CLIENT = {"client": "clumi"}


@pytest.fixture(autouse=True)
def _isolated(tmp_path):
    reset_data_source()
    reset_ml_model()
    set_storage(FileStorage(tmp_path))
    yield
    reset_storage()
    reset_ml_model()


def _run(name, variables=CLIENT):
    return asyncio.run(PipelineRunner().run(load_pipeline(name), variables))


def test_schemas_load():
    ds = get_default_data_source()
    assert len(load_creatives(ds.get("clumi", "creatives")).rows) == 12
    assert len(load_ab_tests(ds.get("clumi", "ab_tests")).rows) == 5


def test_k18_count():
    r = _run("creative_kpi_total")
    assert r.status == "completed", r.error
    assert r.output["value"] == 12


def test_k19_k20_avg_positive():
    assert _run("creative_kpi_ctr_avg").output["value"] > 0
    assert _run("creative_kpi_roas_avg").output["value"] > 0


def test_k21_fatigue_from_ml_mock():
    r = _run("creative_kpi_fatigue")
    assert r.status == "completed", r.error
    assert r.output["value"] == 3  # CR-020·021·028 (fixture)


def test_c11_ai_axes_from_ml_mock():
    r = _run("creative_radar_ai")
    assert r.status == "completed", r.error
    assert r.output["ai_clear"] == 80.0
    assert {"ai_sales", "ai_short", "ai_clear", "ai_visual", "ai_benefit"} <= set(r.output)


def test_o04_cards_sorted_by_roas():
    r = _run("creative_cards_top")
    assert r.status == "completed", r.error
    assert r.output["count"] == 9
    assert r.output["rows"][0]["creative_id"] == "CR-015"  # roas 5520 최고


def test_t06_ab_table_winner():
    r = _run("creative_ab_table")
    assert r.status == "completed", r.error
    assert r.output["count"] == 5
    ab005 = next(x for x in r.output["rows"] if x["test_id"] == "AB-005")
    assert ab005["winner"] == "A"  # 4020 > 1980


def test_catalog_creative_has_7():
    cr = [p for p in list_pipelines() if p.category == "creative"]
    assert len(cr) == 7, sorted(p.name for p in cr)
