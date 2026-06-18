# -*- coding: utf-8 -*-
"""missing_value_diagnostic 6 케이스 + missing_helper 5 케이스 — cleaning 3번째.

검증:
  D1 source_id='orders'     rows=3420 cols=26
  D2 source_id='customers'  rows=8500 cols=29
  D3 source_id 미등록 → ValueError
  D4 source_id 누락 → ValueError
  D5 semantic NaN 분류 (orders.member_id 비회원 = 'semantic')
  D6 semantic NaN 분류 (customers.last_order_date 비주문 = 'semantic')

  H1 is_missing(None / NaN / "") = True
  H2 safe_int(NaN, 0) = 0 / safe_int("5") = 5
  H3 safe_str(NaN) = ""
  H4 null_stats(df) — 결측 카운트 정확
  H5 classify_missing — 5 분류 (complete/semantic/minor/partial/major)
"""
from __future__ import annotations

import asyncio
import math

import pandas as pd
import pytest

from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.cleaning.missing_value_diagnostic import MissingValueDiagnostic
from app.dream_agent.tools.registry import get_registry
from app.dream_agent.tools.shared.missing_helper import (
    classify_missing,
    is_missing,
    null_stats,
    safe_float,
    safe_int,
    safe_str,
)
from app.dream_agent.tools.shared.storage import (
    FileStorage, reset_storage, set_storage,
)


@pytest.fixture
def ctx() -> ExecutionContext:
    return ExecutionContext(session_id="test_diag", plan_id="test_diag", client_id="clumi")


@pytest.fixture
def tool() -> MissingValueDiagnostic:
    reg = get_registry()
    spec = reg.get("missing_value_diagnostic")
    assert spec is not None
    return MissingValueDiagnostic(spec)


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path):
    set_storage(FileStorage(tmp_path))
    yield tmp_path
    reset_storage()


# ── missing_value_diagnostic tool ──
def test_orders_diagnostic(tool, ctx):
    """D1: orders rows=3420 cols=26."""
    r = asyncio.run(tool.execute({"source_id": "orders"}, ctx))
    assert r["total_rows"] == 3420
    assert r["total_columns"] == 26


def test_customers_diagnostic(tool, ctx):
    """D2: customers rows=8500 cols=29."""
    r = asyncio.run(tool.execute({"source_id": "customers"}, ctx))
    assert r["total_rows"] == 8500
    assert r["total_columns"] == 29


def test_unregistered_source_id_raises(tool, ctx):
    """D3: 미등록 source_id → ValueError."""
    with pytest.raises(ValueError, match="not registered"):
        asyncio.run(tool.execute({"source_id": "nonexistent_source"}, ctx))


def test_source_id_missing_raises(tool, ctx):
    """D4: source_id 누락 → ValueError."""
    with pytest.raises(ValueError, match="source_id"):
        asyncio.run(tool.execute({}, ctx))


def test_orders_member_id_semantic(tool, ctx):
    """D5: orders.member_id 비회원 NaN = 'semantic'."""
    r = asyncio.run(tool.execute({"source_id": "orders"}, ctx))
    mid = next(s for s in r["column_stats"] if s["column"] == "member_id")
    assert mid["classification"] == "semantic"
    assert mid["null_count"] > 0  # 비회원 258 존재


def test_customers_last_order_date_semantic(tool, ctx):
    """D6: customers.last_order_date 74.5% NaN = 'semantic'."""
    r = asyncio.run(tool.execute({"source_id": "customers"}, ctx))
    last = next(s for s in r["column_stats"] if s["column"] == "last_order_date")
    assert last["classification"] == "semantic"
    assert last["null_rate"] > 0.7  # 비주문 회원 74.5%


# ── missing_helper unit ──
def test_is_missing():
    """H1: None / NaN / 빈문자열 모두 True."""
    assert is_missing(None) is True
    assert is_missing(float("nan")) is True
    assert is_missing("") is True
    assert is_missing("  ") is True
    # 비결측
    assert is_missing("hello") is False
    assert is_missing(0) is False  # 0 은 결측 아님
    assert is_missing(False) is False


def test_safe_int_and_float():
    """H2: safe_int·safe_float — NaN→default, 정상→변환."""
    assert safe_int(None) == 0
    assert safe_int(float("nan")) == 0
    assert safe_int("") == 0
    assert safe_int("5") == 5
    assert safe_int("5.7") == 5
    assert safe_int("abc", default=-1) == -1
    assert safe_float(None) == 0.0
    assert safe_float("3.14") == 3.14


def test_safe_str():
    """H3: NaN → "" / 정상 → strip()."""
    assert safe_str(float("nan")) == ""
    assert safe_str(None) == ""
    assert safe_str("  hello  ") == "hello"
    assert safe_str(123) == "123"


def test_null_stats():
    """H4: null_stats — 컬럼별 결측 카운트 정확."""
    df = pd.DataFrame({
        "a": [1, 2, 3, 4],
        "b": [None, "x", "", "y"],  # 2 결측 (None + "")
        "c": [float("nan"), 1.0, 2.0, 3.0],  # 1 결측
    })
    stats = null_stats(df)
    by_col = {s["column"]: s for s in stats}
    assert by_col["a"]["null_count"] == 0
    assert by_col["b"]["null_count"] == 2
    assert by_col["c"]["null_count"] == 1
    assert by_col["b"]["null_rate"] == 0.5


def test_classify_missing():
    """H5: 5 분류 — complete / semantic / minor / partial / major."""
    stats = [
        {"column": "a", "null_rate": 0.0, "null_count": 0, "total": 100, "dtype": "int"},
        {"column": "last_date", "null_rate": 0.75, "null_count": 75, "total": 100, "dtype": "object"},
        {"column": "minor", "null_rate": 0.02, "null_count": 2, "total": 100, "dtype": "object"},
        {"column": "partial", "null_rate": 0.3, "null_count": 30, "total": 100, "dtype": "object"},
        {"column": "major", "null_rate": 0.8, "null_count": 80, "total": 100, "dtype": "object"},
    ]
    out = classify_missing(stats, semantic_nulls={"last_date": "비주문자"})
    by_col = {s["column"]: s["classification"] for s in out}
    assert by_col["a"] == "complete"
    assert by_col["last_date"] == "semantic"   # semantic_nulls 명시
    assert by_col["minor"] == "minor_gap"
    assert by_col["partial"] == "partial_gap"
    assert by_col["major"] == "major_gap"
