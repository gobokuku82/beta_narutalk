# -*- coding: utf-8 -*-
"""Phase 1 M1 — Pipeline Runner walking skeleton 검증.

핵심 (ADR-024 V4 정답 보존):
  P1 substitute  — ${var} 단일 치환 타입 보존 + 임베디드 문자열 치환
  P2 topo_order  — depends_on 위상 정렬 + 사이클/미존재 의존 ValueError
  P3 compute     — K01 pipeline cache miss → revenue_total 정답 119,539,660
  P4 cache hit   — 재실행 시 cache_hit=True, 동일 정답
  P5 validation  — RevenueOutput schema + value_min 통과
  P6 step trace  — orders_load → revenue_compute 순서 + 둘 다 completed
"""
from __future__ import annotations

import asyncio

import pytest

from app.dream_agent.tools.shared.storage import (
    FileStorage,
    get_storage,
    reset_storage,
    set_storage,
)
from app.pipelines import PipelineRunner, load_pipeline
from app.pipelines.models import StepDef
from app.pipelines.runner import substitute, topo_order

K01_VARS = {"client": "clumi", "period": "2026-04"}
ANSWER_S001 = 119_539_660
ANSWER_COUNT = 1919


# ─────────────────────────────────────────────────────────────────
# P1·P2 — pure helper unit
# ─────────────────────────────────────────────────────────────────


def test_substitute_exact_preserves_type():
    """단일 ${var} = 원본 값 (str 그대로). 임베디드 = 문자열 치환."""
    assert substitute("${client}", {"client": "clumi"}) == "clumi"
    assert substitute("S001_${period}.json", {"period": "2026-04"}) == "S001_2026-04.json"
    # 미정의 변수 → placeholder 보존
    assert substitute("${missing}", {}) == "${missing}"


def test_substitute_nested():
    out = substitute({"client": "${client}", "k": ["${period}", "x"]}, K01_VARS)
    assert out == {"client": "clumi", "k": ["2026-04", "x"]}


def test_topo_order_respects_depends_on():
    steps = [
        StepDef(id="b", tool="t", depends_on=["a"]),
        StepDef(id="a", tool="t"),
    ]
    ordered = [s.id for s in topo_order(steps)]
    assert ordered == ["a", "b"]


def test_topo_order_cycle_raises():
    steps = [
        StepDef(id="a", tool="t", depends_on=["b"]),
        StepDef(id="b", tool="t", depends_on=["a"]),
    ]
    with pytest.raises(ValueError, match="cycle"):
        topo_order(steps)


def test_topo_order_unknown_dep_raises():
    steps = [StepDef(id="a", tool="t", depends_on=["ghost"])]
    with pytest.raises(ValueError, match="unknown"):
        topo_order(steps)


# ─────────────────────────────────────────────────────────────────
# P3~P6 — K01 end-to-end (정답 보존)
# ─────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path):
    """tmp workspace → cache miss 강제 (compute path 검증). raw 는 실 repo 사용."""
    set_storage(FileStorage(tmp_path))
    yield tmp_path
    reset_storage()


def test_k01_compute_preserves_answer():
    """P3: cache miss → revenue_total 계산 → 정답 119,539,660."""
    pipeline = load_pipeline("dashboard1_kpi_revenue")
    runner = PipelineRunner()  # isolated_storage 적용 후 생성 → tmp workspace
    result = asyncio.run(runner.run(pipeline, K01_VARS))

    assert result.status == "completed", result.error
    assert result.cache_hit is False
    assert result.output["revenue_total"] == ANSWER_S001
    assert result.output["active_orders_count"] == ANSWER_COUNT


def test_k01_cache_hit_second_run():
    """P4: 1회 실행 후 재실행 → cache_hit=True, 동일 정답."""
    pipeline = load_pipeline("dashboard1_kpi_revenue")
    runner = PipelineRunner()
    asyncio.run(runner.run(pipeline, K01_VARS))  # 1회 — self-save

    result2 = asyncio.run(runner.run(pipeline, K01_VARS))
    assert result2.cache_hit is True
    assert result2.output["revenue_total"] == ANSWER_S001


def test_k01_validation_ok():
    """P5: RevenueOutput schema + value_min 통과."""
    pipeline = load_pipeline("dashboard1_kpi_revenue")
    result = asyncio.run(PipelineRunner().run(pipeline, K01_VARS))
    assert result.validation["ok"] is True
    checks = {c["check"]: c for c in result.validation["checks"]}
    assert checks["schema"]["ok"] is True
    assert checks["value_min"]["ok"] is True


def test_k01_step_trace():
    """P6: orders_load → revenue_compute 순서 + 둘 다 completed."""
    pipeline = load_pipeline("dashboard1_kpi_revenue")
    result = asyncio.run(PipelineRunner().run(pipeline, K01_VARS))
    ids = [s.id for s in result.steps]
    assert ids == ["orders_load", "revenue_compute"]
    assert all(s.status == "completed" for s in result.steps)
