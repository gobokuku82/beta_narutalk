# -*- coding: utf-8 -*-
"""Phase A.3 comparison 4 — mom_revenue · grade_timeseries · channel_cac · inapp_ab.

검증:
  MR1 mom_revenue: 3월 79,412,109 → 4월 119,539,660 = +50.5%
  GT1 grade_timeseries 4시점 (1월~4월) 회원수: 6680/7299/7900/8500
  GT2 4월 등급 분포 (= grade_revenue 와 일치)
  CC1 channel_cac: weighted_avg=44,678 (가 결정 A-5.2 google 포함; 원안 30,512), kakao=2,270
  CC2 channel_cac: new_members_total=600
  IB1 inapp_ab: status='partial', data_gaps 명시
"""
from __future__ import annotations
import asyncio
import pytest

from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.comparison.channel_cac_compare import ChannelCacCompare
from app.dream_agent.tools.comparison.grade_timeseries import GradeTimeseries
from app.dream_agent.tools.comparison.inapp_ad_ab_compare import InappAdAbCompare
from app.dream_agent.tools.comparison.mom_revenue import MomRevenue
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


# ── mom_revenue ──
def test_mom_revenue_50pct(ctx):
    """MR1: 매출 MoM = +50.5% (recovery 핵심 답)."""
    tool = MomRevenue(get_registry().get("mom_revenue"))
    r = asyncio.run(tool.execute({"period_a": "2026-03", "period_b": "2026-04"}, ctx))
    assert r["period_a_revenue"] == 79_412_109
    assert r["period_b_revenue"] == 119_539_660
    assert r["delta_pct"] == 50.5


# ── grade_timeseries ──
def test_grade_timeseries_4_snapshots(ctx):
    """GT1: 4시점 회원수 = 6680/7299/7900/8500 (methodology §S045 정답)."""
    tool = GradeTimeseries(get_registry().get("grade_timeseries"))
    r = asyncio.run(tool.execute({}, ctx))
    assert r["snapshot_count"] == 4
    totals = {t["snapshot_date"]: t["total"] for t in r["timeline"]}
    assert totals["2026-01-31"] == 6680
    assert totals["2026-02-28"] == 7299
    assert totals["2026-03-31"] == 7900
    assert totals["2026-04-30"] == 8500


def test_grade_timeseries_latest_match_grade_revenue(ctx):
    """GT2: 4월 등급 분포 = grade_revenue 와 일치."""
    tool = GradeTimeseries(get_registry().get("grade_timeseries"))
    r = asyncio.run(tool.execute({}, ctx))
    latest = r["latest_snapshot"]["grade_counts"]
    assert latest == {"WELCOME": 6333, "REGULAR": 1539, "SILVER": 600, "GOLD": 28, "VIP": 0}


# ── channel_cac_compare ──
def test_channel_cac_weighted_avg(ctx):
    """CC1: 가중평균 CAC = 44,678 (= S032, 가 결정 A-5.2 google 포함; 원안 30,512), kakao CAC = 2,270."""
    tool = ChannelCacCompare(get_registry().get("channel_cac_compare"))
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert r["weighted_avg_cac"] == 44_678
    assert r["by_channel"]["kakao"]["cac"] == 2_270


def test_channel_cac_new_members_600(ctx):
    """CC2: new_members_total = 600."""
    tool = ChannelCacCompare(get_registry().get("channel_cac_compare"))
    r = asyncio.run(tool.execute({"period": "2026-04"}, ctx))
    assert r["new_members_total"] == 600


# ── inapp_ad_ab_compare (partial) ──
def test_inapp_ab_partial_status(ctx):
    """IB1: status='partial', data_gaps 명시."""
    tool = InappAdAbCompare(get_registry().get("inapp_ad_ab_compare"))
    r = asyncio.run(tool.execute({}, ctx))
    assert r["status"] == "partial"
    assert "S019" in r["data_gaps"]
    assert "S020" in r["data_gaps"]
    # 데이터는 일부 산출 (campaign_name substring 매칭 결과)
    assert "a_meta" in r and "b_meta" in r
