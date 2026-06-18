# -*- coding: utf-8 -*-
"""revenue_total 6 케이스 — metrics 1차 (S001).

검증 항목:
  R1 april_2026 = 119,539,660             ← methodology 정답 회귀
  R2 march_april = 198,951,769            ← 자체 산출 회귀
  R3 active_orders_count 일치 (1,919 / 3,265)
  R4 period 누락 → ValueError
  R5 storage layer = 'computed' + JSON 키
  R6 _schema 동반 + formula 메타 포함
"""
from __future__ import annotations

import asyncio
import json

import pytest

from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.metrics.revenue_total import RevenueTotal
from app.dream_agent.tools.registry import get_registry
from app.dream_agent.tools.shared.storage import (
    FileStorage, get_storage, reset_storage, set_storage,
)


@pytest.fixture
def ctx() -> ExecutionContext:
    return ExecutionContext(session_id="test_rev", plan_id="test_rev", client_id="clumi")


@pytest.fixture
def tool() -> RevenueTotal:
    reg = get_registry()
    spec = reg.get("revenue_total")
    assert spec is not None
    return RevenueTotal(spec)


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path):
    set_storage(FileStorage(tmp_path))
    yield tmp_path
    reset_storage()


def test_april_2026_returns_119539660(tool, ctx):
    """R1: methodology §S001 정답 — 2026-04 총매출 = 119,539,660."""
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert r["revenue_total"] == 119_539_660, (
        f"expected 119,539,660 got {r['revenue_total']:,}"
    )


def test_march_april_combined(tool, ctx):
    """R2: 3-4월 통합 = 198,951,769 (자체 산출)."""
    r = asyncio.run(tool.execute({"period": "2026-03/2026-04"}, ctx))
    assert r["revenue_total"] == 198_951_769


def test_active_orders_count_consistency(tool, ctx):
    """R3: active_orders_count 가 cleaning/active_orders_filter 결과와 일치."""
    r_apr = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert r_apr["active_orders_count"] == 1919
    r_q = asyncio.run(tool.execute({"period": "2026-03/2026-04"}, ctx))
    assert r_q["active_orders_count"] == 3265


def test_period_missing_raises(tool, ctx):
    """R4: period 누락 → ValueError."""
    with pytest.raises(ValueError, match="period"):
        asyncio.run(tool.execute({}, ctx))


# R5·R6 (tool-save 단언) — ②-b 후 삭제: tool 은 더는 저장하지 않음.
# entry-save 동작은 test_route::test_cache_consistency_revenue 가 검증.
