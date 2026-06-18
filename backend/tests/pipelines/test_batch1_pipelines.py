# -*- coding: utf-8 -*-
"""Phase 1 M1b-2 — Batch 1 전체 21 pipeline 이 Runner 로 실행됨 검증.

실 workspace (격리 X) → 정답 17 cache hit 반환 → status=completed + schema 검증 통과.
cache miss 시 기존 tool 이 raw 에서 재계산 (값 동일 — V4 정답 보존, tool 무변경).

  B1 21 pipeline 전부 catalog 등록 + 변수 선언 정합
  B2 21 pipeline 전부 Runner 실행 → completed + schema OK
"""
from __future__ import annotations

import asyncio

import pytest

from app.dream_agent.tools.shared.storage import reset_storage
from app.pipelines import PipelineRunner, list_pipelines, load_pipeline

PER = {"client": "clumi", "period": "2026-04"}
MOM = {"client": "clumi", "period_a": "2026-03", "period_b": "2026-04"}
NONE = {"client": "clumi"}

# 21 pipeline (viz id 기준) — (name, variables)
CASES = [
    ("dashboard1_kpi_revenue", PER),
    ("dashboard1_kpi_ad_cost", PER),
    ("dashboard1_kpi_roas", PER),
    ("dashboard1_kpi_cac", PER),
    ("dashboard1_kpi_promotion_revenue", PER),
    ("dashboard1_kpi_promotion_roas", PER),
    ("dashboard1_kpi_new_members", PER),
    ("dashboard1_kpi_aov", PER),
    ("dashboard1_kpi_signup_conversion", PER),
    ("dashboard1_mom_revenue", MOM),
    ("dashboard1_mom_aov", MOM),
    ("dashboard1_mom_repurchase", MOM),
    ("dashboard1_mom_new_members", MOM),
    ("dashboard1_segment_grade_timeseries", NONE),
    ("dashboard1_segment_age", NONE),
    ("dashboard1_segment_grade", PER),
    ("dashboard1_segment_channel", PER),
    ("dashboard1_segment_category", PER),
    ("dashboard1_segment_member_guest", PER),
    ("dashboard1_segment_unknown_share", PER),
    ("dashboard1_kpi_ad_cost_bar", PER),
]


@pytest.fixture(autouse=True)
def _real_workspace():
    """실 repo workspace (정답 17 cache) 보장 — 다른 test 의 tmp override 무력화."""
    reset_storage()
    yield
    reset_storage()


def test_batch1_catalog_has_21():
    """B1: flows/ 의 dashboard1 카테고리 = 21 + CASES 와 이름 정합."""
    dash1 = [p for p in list_pipelines() if p.category == "dashboard1"]
    names = {p.name for p in dash1}
    assert len(dash1) == 21, sorted(names)
    assert names == {name for name, _ in CASES}


@pytest.mark.parametrize("name,variables", CASES)
def test_batch1_pipeline_runs_and_validates(name, variables):
    """B2: 21 pipeline 각각 Runner 실행 → completed + schema 검증 OK (정답 보존)."""
    pipeline = load_pipeline(name)
    result = asyncio.run(PipelineRunner().run(pipeline, variables))

    assert result.status == "completed", f"{name} failed: {result.error}"
    assert result.output, f"{name}: empty output"

    if result.validation:
        checks = {c["check"]: c for c in result.validation["checks"]}
        if "schema" in checks:
            assert checks["schema"]["ok"], f"{name} schema: {checks['schema']}"
