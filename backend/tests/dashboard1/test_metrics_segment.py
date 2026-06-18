# -*- coding: utf-8 -*-
"""S054 + S037 묶음 — 채널 비중 + 연령 segment 회귀.

검증:
  U1 unknown_share = 39.8% (4월)
  U2 unknown_revenue = 47,539,330 / total = 119,539,660
  U3 period 누락·범위 거부
  A1 35-44 합 = 2,884 (회귀 핵심)
  A2 정답표 11 bucket 모두 일치 (40-44=1455, 35-39=1429, ...)
  A3 total_members = 8,500
  A4 bucket share 합 = 100% (반올림 ±0.5)
"""
from __future__ import annotations
import asyncio
import pytest

from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.metrics.age_segment import AgeSegment
from app.dream_agent.tools.metrics.unknown_revenue_share import UnknownRevenueShare
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


# ── S054 ──
def test_unknown_share_398(ctx):
    """U1: 4월 알수없음 비중 = 39.8%."""
    tool = UnknownRevenueShare(get_registry().get("unknown_revenue_share"))
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert r["unknown_share_pct"] == 39.8


def test_unknown_revenue_and_total(ctx):
    """U2: unknown 47,539,330 / total 119,539,660."""
    tool = UnknownRevenueShare(get_registry().get("unknown_revenue_share"))
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert r["unknown_revenue"] == 47_539_330
    assert r["total_revenue"] == 119_539_660


def test_unknown_share_invalid_period(ctx):
    tool = UnknownRevenueShare(get_registry().get("unknown_revenue_share"))
    with pytest.raises(ValueError, match="period"):
        asyncio.run(tool.execute({}, ctx))
    with pytest.raises(ValueError, match="단일 월"):
        asyncio.run(tool.execute({"period": "2026-03/2026-04"}, ctx))


# ── S037 ──
def test_age_core_35_44_2884(ctx):
    """A1: 핵심 35-44 합 = 2,884."""
    tool = AgeSegment(get_registry().get("age_segment"))
    r = asyncio.run(tool.execute({}, ctx))
    assert r["core_segment_35_44"] == 2884


def test_age_buckets_match_methodology(ctx):
    """A2: methodology 정답표 11 bucket 모두 일치."""
    tool = AgeSegment(get_registry().get("age_segment"))
    r = asyncio.run(tool.execute({}, ctx))
    expected = {
        "40-44": 1455, "35-39": 1429,
        "30-34": 1407, "25-29": 1393,
        "50-54": 800,  "45-49": 778,
        "20-24": 477,
        "60-64": 254,  "55-59": 241,
        "15-19": 182,
        # 65+ 합 84 (methodology 의 '기타')
    }
    for bucket, count in expected.items():
        assert r["table"][bucket]["count"] == count, (
            f"{bucket}: expected {count}, got {r['table'][bucket]['count']}"
        )
    # 기타 (65+)
    assert r["table"].get("65+", {}).get("count", 0) == 84


def test_age_total_8500(ctx):
    """A3: total_members = 8,500."""
    tool = AgeSegment(get_registry().get("age_segment"))
    r = asyncio.run(tool.execute({}, ctx))
    assert r["total_members"] == 8500


def test_age_share_sums_to_100(ctx):
    """A4: bucket share 합 ≈ 100%."""
    tool = AgeSegment(get_registry().get("age_segment"))
    r = asyncio.run(tool.execute({}, ctx))
    total = sum(b["share_pct"] for b in r["table"].values())
    assert 99.5 <= total <= 100.5
