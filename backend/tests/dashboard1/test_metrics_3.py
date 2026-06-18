# -*- coding: utf-8 -*-
"""S048·S028·S069 묶음 — 마케팅비 무관 metrics 3개 회귀.

각 tool 의 정답값을 methodology 정답표 기준으로 박제.
"""
from __future__ import annotations
import asyncio

import pytest

from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.metrics.aov_monthly import AovMonthly
from app.dream_agent.tools.metrics.new_members_monthly import NewMembersMonthly
from app.dream_agent.tools.metrics.repurchase_rate_mom import RepurchaseRateMom
from app.dream_agent.tools.registry import get_registry
from app.dream_agent.tools.shared.storage import (
    FileStorage, reset_storage, set_storage,
)


@pytest.fixture
def ctx() -> ExecutionContext:
    return ExecutionContext(session_id="t", plan_id="t", client_id="clumi")


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path):
    set_storage(FileStorage(tmp_path))
    yield
    reset_storage()


# ── S048 AOV ──
def test_aov_april_2026(ctx):
    """S048: 4월 객단가=62293 / 구매자=1386 / 주문=1919."""
    reg = get_registry()
    tool = AovMonthly(reg.get("aov_monthly"))
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert r["aov"] == 62293, f"aov {r['aov']}"
    assert r["unique_buyers"] == 1386
    assert r["orders_count"] == 1919


def test_aov_period_missing(ctx):
    tool = AovMonthly(get_registry().get("aov_monthly"))
    with pytest.raises(ValueError, match="period"):
        asyncio.run(tool.execute({}, ctx))


# ── S028 재구매율 ──
def test_repurchase_april_790(ctx):
    """S028 4월: 재구매율=79.0% / 전체=1386."""
    tool = RepurchaseRateMom(get_registry().get("repurchase_rate_mom"))
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert r["repurchase_rate"] == 79.0
    assert r["total_buyers"] == 1386


def test_repurchase_march_762(ctx):
    """S028 3월: 재구매율=76.2% / 전체=1206."""
    tool = RepurchaseRateMom(get_registry().get("repurchase_rate_mom"))
    r = asyncio.run(tool.execute({"period": "2026-03"}, ctx))
    assert r["repurchase_rate"] == 76.2
    assert r["total_buyers"] == 1206


def test_repurchase_rejects_range(ctx):
    """S028 은 단일 월만 — '/' 구간 거부."""
    tool = RepurchaseRateMom(get_registry().get("repurchase_rate_mom"))
    with pytest.raises(ValueError, match="단일 월"):
        asyncio.run(tool.execute({"period": "2026-03/2026-04"}, ctx))


# ── S069 신규회원 ──
def test_new_members_april_600(ctx):
    """S069: 4월 신규 합계 = 600."""
    tool = NewMembersMonthly(get_registry().get("new_members_monthly"))
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert r["new_members_total"] == 600


def test_new_members_by_channel(ctx):
    """S069: 채널 분포 dict 존재 + 합 = total."""
    tool = NewMembersMonthly(get_registry().get("new_members_monthly"))
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert sum(r["new_members_by_channel"].values()) == r["new_members_total"]
    assert len(r["new_members_by_channel"]) >= 2
