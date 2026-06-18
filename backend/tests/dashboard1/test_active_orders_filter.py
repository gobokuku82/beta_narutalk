# -*- coding: utf-8 -*-
"""active_orders_filter — 세부계획 §3 Step 7.

검증 항목:
  T9  april_2026_returns_1919          (회귀 — methodology 정답)
  T10 march_april_combined_3265        (회귀)
  T11 period_missing_raises            (ValueError)
  T12 no_c40_in_output                 (필터 정확성)
  ※ T13·T14·T15(tool-save parquet/schema/roundtrip) — ②-b contract C 후 삭제:
     tool 은 더는 저장하지 않음. DataFrame 중간물 prod 미소비, 단언만 obsolete.
     workspace parquet 동작은 backend/tests/workspace/test_file.py 가 검증.
"""
from __future__ import annotations

import asyncio

import pytest

from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.registry import get_registry
from app.dream_agent.tools.cleaning.active_orders_filter import ActiveOrdersFilter
from app.dream_agent.tools.shared.storage import (
    FileStorage,
    reset_storage,
    set_storage,
)


# ── fixture ──
@pytest.fixture
def ctx() -> ExecutionContext:
    return ExecutionContext(session_id="test_clumi", plan_id="test_clumi", client_id="clumi")


@pytest.fixture
def tool() -> ActiveOrdersFilter:
    reg = get_registry()
    spec = reg.get("active_orders_filter")
    assert spec is not None, "active_orders_filter not registered in catalog"
    return ActiveOrdersFilter(spec)


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path):
    """매 테스트마다 tmp_path 기반 storage 주입 → 실 data/ 변경 없음.

    T13~T15 는 tmp_path/data/clumi/normalized/ 에 산출물 생성.
    """
    set_storage(FileStorage(tmp_path))
    yield tmp_path
    reset_storage()


# ── 회귀 (methodology 정답) ──
def test_april_2026_returns_1919(tool, ctx):
    """T9: methodology 정답 — 2026-04 활성 = 1,919."""
    result = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert result["count"] == 1919, f"expected 1919, got {result['count']}"
    assert result["dropped"] == 81


def test_march_april_combined_3265(tool, ctx):
    """T10: methodology 정답 — 3-4월 통합 활성 = 3,265."""
    result = asyncio.run(tool.execute({"period": "2026-03/2026-04"}, ctx))
    assert result["count"] == 3265, f"expected 3265, got {result['count']}"
    assert result["dropped"] == 155  # 3420 - 3265


# ── 입력 검증 ──
def test_period_missing_raises(tool, ctx):
    """T11: period 누락 시 ValueError."""
    with pytest.raises(ValueError, match="period"):
        asyncio.run(tool.execute({}, ctx))


# ── 필터 정확성 ──
def test_no_c40_in_output(tool, ctx):
    """T12: 필터 후 어떤 행도 order_status == 'C40' 아님."""
    result = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    statuses = {r["order_status"] for r in result["orders_active"]}
    assert "C40" not in statuses, f"C40 누락 — 발견 statuses: {statuses}"
