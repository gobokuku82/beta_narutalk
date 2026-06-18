# -*- coding: utf-8 -*-
"""grade_revenue 7 케이스 — S046 (orders × customers join, 첫 join 패턴).

검증:
  G1 SILVER 매출 = 65,757,080            ← methodology 정답
  G2 WELCOME 회원비중 = 74.5%            ← methodology 정답
  G3 total_members = 8,500
  G4 등급별 회원수 정확 (SILVER 600·GOLD 28·REGULAR 1539·WELCOME 6333·VIP 0)
  G5 등급별 매출 비중 합 = 100% (반올림 오차 ±0.5)
  G6 GOLD/REGULAR 매출 검증 (8,511,200 / 39,496,930)
  G7 period 누락·범위 거부
"""
from __future__ import annotations
import asyncio
import pytest

from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.metrics.grade_revenue import GradeRevenue
from app.dream_agent.tools.registry import get_registry
from app.dream_agent.tools.shared.storage import (
    FileStorage, reset_storage, set_storage,
)


@pytest.fixture
def ctx() -> ExecutionContext:
    return ExecutionContext(session_id="t", plan_id="t", client_id="clumi")


@pytest.fixture
def tool() -> GradeRevenue:
    return GradeRevenue(get_registry().get("grade_revenue"))


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path):
    set_storage(FileStorage(tmp_path))
    yield
    reset_storage()


def test_silver_revenue_65757080(tool, ctx):
    """G1: SILVER 매출 = 65,757,080 (methodology §S046 정답)."""
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert r["silver_revenue"] == 65_757_080, f"silver {r['silver_revenue']:,}"


def test_welcome_member_share_745(tool, ctx):
    """G2: WELCOME 회원비중 = 74.5%."""
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert r["welcome_member_share"] == 74.5


def test_total_members_8500(tool, ctx):
    """G3: customers 전체 = 8,500."""
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert r["total_members"] == 8500


def test_grade_member_counts(tool, ctx):
    """G4: 등급별 회원수 정확."""
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    expected = {"VIP": 0, "GOLD": 28, "SILVER": 600, "REGULAR": 1539, "WELCOME": 6333}
    actual = {g: r["table"][g]["member_count"] for g in expected}
    assert actual == expected


def test_revenue_share_sums_to_100(tool, ctx):
    """G5: 매출 비중 합 ≈ 100% (반올림 ±0.5)."""
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    total_share = sum(g["revenue_share_pct"] for g in r["table"].values())
    assert 99.5 <= total_share <= 100.5, f"share sum {total_share}"


def test_gold_and_regular_revenue(tool, ctx):
    """G6: GOLD 8,511,200 / REGULAR 39,496,930."""
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert r["table"]["GOLD"]["revenue"] == 8_511_200
    assert r["table"]["REGULAR"]["revenue"] == 39_496_930


def test_invalid_period(tool, ctx):
    """G7: period 누락 + 범위 거부."""
    with pytest.raises(ValueError, match="period"):
        asyncio.run(tool.execute({}, ctx))
    with pytest.raises(ValueError, match="단일 월"):
        asyncio.run(tool.execute({"period": "2026-03/2026-04"}, ctx))
