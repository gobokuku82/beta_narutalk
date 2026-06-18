# -*- coding: utf-8 -*-
"""member_metrics_validator — cleaning 2번째 tool.

검증 항목:
  M1 mock_정합 (mismatch_count = 0)        ← 회귀: methodology "이미 갱신" 검증
  M2 customer_count = 8500                  ← 회귀
  M3 active_orders_member = 3007            ← 회귀 (활성 회원주문, 비회원 258 제외)
  M4 fields 부분 선택 (total_orders 만)
  M5 validated_customers 컬럼 보존
  ※ M6(tool-save parquet+_schema) — ②-b contract C 후 삭제: tool 미저장.
"""
from __future__ import annotations

import asyncio

import pytest

from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.registry import get_registry
from app.dream_agent.tools.cleaning.member_metrics_validator import MemberMetricsValidator
from app.dream_agent.tools.shared.storage import (
    FileStorage, reset_storage, set_storage,
)


@pytest.fixture
def ctx() -> ExecutionContext:
    return ExecutionContext(session_id="test_validator", plan_id="test_validator", client_id="clumi")


@pytest.fixture
def tool() -> MemberMetricsValidator:
    reg = get_registry()
    spec = reg.get("member_metrics_validator")
    assert spec is not None
    return MemberMetricsValidator(spec)


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path):
    set_storage(FileStorage(tmp_path))
    yield tmp_path
    reset_storage()


# ── 회귀 (mock 정합성 검증) ──
def test_mock_is_consistent(tool, ctx):
    """M1: mock 데이터가 methodology §정제 3 기준 정합 → mismatch=0."""
    r = asyncio.run(tool.execute({}, ctx))
    assert r["mismatch_count"] == 0, (
        f"expected 0 (mock 정합), got {r['mismatch_count']}. "
        f"sample: {r['mismatches'][:3]}"
    )


def test_customer_count_8500(tool, ctx):
    """M2: customers 전체 = 8,500."""
    r = asyncio.run(tool.execute({}, ctx))
    assert r["customer_count"] == 8500


def test_active_orders_member_3007(tool, ctx):
    """M3: 활성주문 (회원만) = 3,007 (전체 활성 3,265 - 비회원 258)."""
    r = asyncio.run(tool.execute({}, ctx))
    assert r["active_orders_member"] == 3007


# ── 옵션 검증 ──
def test_fields_partial_selection(tool, ctx):
    """M4: fields 일부만 검증 — total_orders 만."""
    r = asyncio.run(tool.execute({"fields": ["total_orders"]}, ctx))
    assert r["mismatch_count"] == 0
    assert r["_meta"]["fields"] == ["total_orders"]


# ── 산출 검증 ──
def test_validated_customers_preserves_columns(tool, ctx):
    """M5: validated_customers 가 customers 의 모든 컬럼 보존 (29 cols)."""
    r = asyncio.run(tool.execute({}, ctx))
    assert len(r["validated_customers"]) == 8500
    first = r["validated_customers"][0]
    expected_cols = {
        "member_id", "member_email", "gender", "birth_year",
        "total_orders", "total_purchase_amount", "last_order_date",
        "member_grade", "created_at",
    }
    assert expected_cols.issubset(set(first.keys()))
