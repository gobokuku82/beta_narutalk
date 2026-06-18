# -*- coding: utf-8 -*-
"""ga4_session_aggregator + signup_conversion — 마지막 정량 정답.

검증:
  GA1 session_start_total = 24,000          ← methodology §정제 6 / S067 분모
  GA2 by_event 정답 3종 (session_start·first_visit·purchase)
  GA3 by_source 채널 분포 (8 채널 추정)
  SC1 S067 signup_conversion_pct = 2.50%    ← methodology 마지막 정량 정답
  SC2 signups=600 / sessions=24,000
  SC3 period 누락·범위 거부

  H1 get_event_param — typed value 추출
"""
from __future__ import annotations
import asyncio
import pytest

from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.metrics.signup_conversion import SignupConversion
from app.dream_agent.tools.metrics.ga4_session_aggregator import (
    Ga4SessionAggregator,
)
from app.dream_agent.tools.registry import get_registry
from app.dream_agent.tools.shared.ga4_helper import get_event_param
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


# ── ga4_session_aggregator ──
def test_session_start_24000(ctx):
    """GA1: session_start_total = 24,000 (S067 분모)."""
    tool = Ga4SessionAggregator(get_registry().get("ga4_session_aggregator"))
    r = asyncio.run(tool.execute({}, ctx))
    assert r["session_start_total"] == 24_000


def test_by_event_match(ctx):
    """GA2: methodology §정제 6 정답."""
    tool = Ga4SessionAggregator(get_registry().get("ga4_session_aggregator"))
    r = asyncio.run(tool.execute({}, ctx))
    assert r["by_event"]["session_start"] == 24_000
    assert r["by_event"]["first_visit"] == 12_496
    assert r["by_event"]["purchase"] == 1_823


def test_by_source_distribution(ctx):
    """GA3: 채널 분포 — 합 = session_start_total."""
    tool = Ga4SessionAggregator(get_registry().get("ga4_session_aggregator"))
    r = asyncio.run(tool.execute({}, ctx))
    assert sum(r["by_source"].values()) == r["session_start_total"]
    assert len(r["by_source"]) >= 3


# ── signup_conversion (S067) ──
def test_signup_conversion_250(ctx):
    """SC1·SC2: S067 = 2.50% (600 / 24,000) — methodology 마지막 정량 정답."""
    tool = SignupConversion(get_registry().get("signup_conversion"))
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert r["signup_conversion_pct"] == 2.50
    assert r["signups"] == 600
    assert r["sessions"] == 24_000


def test_signup_conversion_invalid_period(ctx):
    """SC3: period 누락 + 범위 거부."""
    tool = SignupConversion(get_registry().get("signup_conversion"))
    with pytest.raises(ValueError, match="period"):
        asyncio.run(tool.execute({}, ctx))
    with pytest.raises(ValueError, match="단일 월"):
        asyncio.run(tool.execute({"period": "2026-03/2026-04"}, ctx))


# ── helper unit ──
def test_get_event_param_string():
    """H1: event_params 의 typed value 추출."""
    rec = {"event_params": [
        {"key": "page_title", "value": {"string_value": "Home"}},
        {"key": "ga_session_id", "value": {"int_value": 123}},
        {"key": "engagement_time_msec", "value": {"int_value": 5000}},
    ]}
    assert get_event_param(rec, "page_title") == "Home"
    assert get_event_param(rec, "ga_session_id") == 123
    assert get_event_param(rec, "missing") is None
