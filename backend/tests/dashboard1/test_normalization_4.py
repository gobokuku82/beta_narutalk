# -*- coding: utf-8 -*-
"""normalization 4 — 정제 2·4·8·9.

검증:
  K1 KST: total_events=38,319 (GA4 #07 stream 전체)
  K2 KST: date_boundary_shifts > 0 (UTC vs KST 자정 차이)
  K3 KST: helper to_kst_datetime 정확
  CH1 channel: by_group Meta=388 / Naver=530 / Unknown=481
  CH2 channel: by_raw 정답 (unknown=481·naver_search=283 등)
  GR1 grade: WELCOME 6333·REGULAR 1539·SILVER 600·GOLD 28·VIP 0
  UT1 utm: normalized_count > 0 (mock 에 (not set) 등 존재)
  UT2 utm: source_dist 정확
"""
from __future__ import annotations
import asyncio
import pytest

from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.normalization.channel_attribution_normalizer import (
    ChannelAttributionNormalizer,
)
from app.dream_agent.tools.normalization.grade_system_unifier import GradeSystemUnifier
from app.dream_agent.tools.normalization.kst_timezone_normalizer import (
    KstTimezoneNormalizer, to_kst_datetime,
)
from app.dream_agent.tools.normalization.utm_normalizer import UtmNormalizer, normalize_utm
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


# ── KST ──
def test_kst_total_events(ctx):
    """K1: ga4_traffic_source total = 38,319."""
    tool = KstTimezoneNormalizer(get_registry().get("kst_timezone_normalizer"))
    r = asyncio.run(tool.execute({"source_id": "ga4_traffic_source", "sample_size": 5}, ctx))
    assert r["total_events"] == 38_319


def test_kst_boundary_shifts(ctx):
    """K2: UTC vs KST 자정 경계 이동 > 0."""
    tool = KstTimezoneNormalizer(get_registry().get("kst_timezone_normalizer"))
    r = asyncio.run(tool.execute({"source_id": "ga4_traffic_source", "sample_size": 5}, ctx))
    assert r["date_boundary_shifts"] > 0


def test_to_kst_datetime_helper():
    """K3: microsec UTC → KST datetime."""
    dt = to_kst_datetime(1774969258000000)
    assert dt.isoformat() == "2026-04-01T00:00:58+09:00"


# ── Channel ──
def test_channel_groups(ctx):
    """CH1: group 분포 — Meta 388 (insta 253 + face 135), Naver 530 (search 283 + shopping 191 + brand 56)."""
    tool = ChannelAttributionNormalizer(get_registry().get("channel_attribution_normalizer"))
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert r["by_group"]["Meta"] == 388
    assert r["by_group"]["Naver"] == 530
    assert r["by_group"]["Unknown"] == 481
    assert r["by_group"]["Direct"] == 273


def test_channel_raw_top(ctx):
    """CH2: raw 분포 정답."""
    tool = ChannelAttributionNormalizer(get_registry().get("channel_attribution_normalizer"))
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert r["by_raw_channel"]["unknown"] == 481
    assert r["by_raw_channel"]["naver_search"] == 283
    assert r["by_raw_channel"]["meta_instagram"] == 253
    assert r["by_raw_channel"]["direct"] == 273


# ── Grade ──
def test_grade_standard_dist(ctx):
    """GR1: WELCOME 6333·REGULAR 1539·SILVER 600·GOLD 28·VIP 0."""
    tool = GradeSystemUnifier(get_registry().get("grade_system_unifier"))
    r = asyncio.run(tool.execute({}, ctx))
    expected = {"WELCOME": 6333, "REGULAR": 1539, "SILVER": 600, "GOLD": 28, "VIP": 0}
    assert r["standard_grade_dist"] == expected


# ── UTM ──
def test_utm_normalized_count(ctx):
    """UT1: (not set) 등 정규화 행 > 0 (4월)."""
    tool = UtmNormalizer(get_registry().get("utm_normalizer"))
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert r["normalized_count"] > 0


def test_utm_source_dist(ctx):
    """UT2: source 정규화 분포 (unknown 481 = (not set) 변환)."""
    tool = UtmNormalizer(get_registry().get("utm_normalizer"))
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert r["source_dist"]["unknown"] == 481
    assert r["source_dist"]["naver"] == 530


def test_normalize_utm_helper():
    """utm helper unit."""
    assert normalize_utm("(not set)") == "unknown"
    assert normalize_utm("(direct)") == "direct"
    assert normalize_utm("(none)") == ""
    assert normalize_utm("meta") == "meta"
    assert normalize_utm(None) == ""
