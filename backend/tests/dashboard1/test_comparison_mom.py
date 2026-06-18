# -*- coding: utf-8 -*-
"""comparison/repurchase_mom + aov_mom — MoM 패턴 회귀.

검증 (2026-03 → 2026-04):
  RM1 total_buyers_pct = +14.9%
  RM2 existing_buyers_pct = +19.2%
  RM3 repurchase_rate_pp = +2.8
  AM1 aov_pct = +5.6%
  AM2 orders_pct = +42.6%
  AM3 buyers_pct = +14.9%
  + params 검증
"""
from __future__ import annotations
import asyncio
import pytest

from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.comparison.aov_mom import AovMom
from app.dream_agent.tools.comparison.new_members_mom import NewMembersMom
from app.dream_agent.tools.comparison.repurchase_mom import RepurchaseMom
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


# ── Repurchase MoM (S028) ──
def test_repurchase_mom_methodology(ctx):
    """RM1·RM2·RM3·RM4: methodology 정답 +14.9% / +19.2% / +2.8%p / +1.4% (신규 주문)."""
    tool = RepurchaseMom(get_registry().get("repurchase_mom"))
    r = asyncio.run(tool.execute({"period_a": "2026-03", "period_b": "2026-04"}, ctx))
    assert r["delta"]["total_buyers_pct"] == 14.9
    assert r["delta"]["existing_buyers_pct"] == 19.2
    assert r["delta"]["repurchase_rate_pp"] == 2.8
    # RM4: recovery 핵심 질문 답 — "신규 주문 고객 +1.4%" (methodology_insights)
    assert r["delta"]["new_buyers_pct"] == 1.4
    # 두 월 stats 도 확인
    assert r["period_a_stats"]["total_buyers"] == 1206
    assert r["period_b_stats"]["total_buyers"] == 1386
    assert r["period_a_stats"]["existing_buyers"] == 919
    assert r["period_b_stats"]["existing_buyers"] == 1095
    assert r["period_a_stats"]["new_buyers"] == 287   # 1206 - 919
    assert r["period_b_stats"]["new_buyers"] == 291   # 1386 - 1095
    assert r["period_a_stats"]["repurchase_rate"] == 76.2
    assert r["period_b_stats"]["repurchase_rate"] == 79.0


def test_repurchase_mom_missing_params(ctx):
    tool = RepurchaseMom(get_registry().get("repurchase_mom"))
    with pytest.raises(ValueError, match="period_a"):
        asyncio.run(tool.execute({}, ctx))
    with pytest.raises(ValueError, match="period_a"):
        asyncio.run(tool.execute({"period_a": "2026-03"}, ctx))


# ── AOV MoM (S048) ──
def test_aov_mom_methodology(ctx):
    """AM1·AM2·AM3: +5.6% (aov) / +42.6% (orders) / +14.9% (buyers)."""
    tool = AovMom(get_registry().get("aov_mom"))
    r = asyncio.run(tool.execute({"period_a": "2026-03", "period_b": "2026-04"}, ctx))
    assert r["delta"]["aov_pct"] == 5.6
    assert r["delta"]["orders_pct"] == 42.6
    assert r["delta"]["buyers_pct"] == 14.9
    # 두 월 stats
    assert r["period_a_stats"]["aov"] == 58999
    assert r["period_b_stats"]["aov"] == 62293
    assert r["period_a_stats"]["orders_count"] == 1346
    assert r["period_b_stats"]["orders_count"] == 1919


def test_aov_mom_missing_params(ctx):
    tool = AovMom(get_registry().get("aov_mom"))
    with pytest.raises(ValueError):
        asyncio.run(tool.execute({}, ctx))


# ── New Members MoM (S069) ──
def test_new_members_mom_methodology(ctx):
    """가입 회원 기준 MoM — 601 → 600 = -0.2%.

    ⚠ recovery '+1.4%' 와 구분:
        +1.4% = 신규 주문 고객 (test_repurchase_mom_methodology 의 new_buyers_pct)
        -0.2% = 신규 가입 회원 (본 케이스)
    """
    tool = NewMembersMom(get_registry().get("new_members_mom"))
    r = asyncio.run(tool.execute({"period_a": "2026-03", "period_b": "2026-04"}, ctx))
    assert r["period_a_total"] == 601
    assert r["period_b_total"] == 600
    assert r["delta_pct"] == -0.2


def test_new_members_mom_by_channel(ctx):
    """채널 분포가 두 월 모두 반환됨."""
    tool = NewMembersMom(get_registry().get("new_members_mom"))
    r = asyncio.run(tool.execute({"period_a": "2026-03", "period_b": "2026-04"}, ctx))
    assert sum(r["by_channel_a"].values()) == r["period_a_total"]
    assert sum(r["by_channel_b"].values()) == r["period_b_total"]


def test_new_members_mom_missing_params(ctx):
    tool = NewMembersMom(get_registry().get("new_members_mom"))
    with pytest.raises(ValueError):
        asyncio.run(tool.execute({}, ctx))
