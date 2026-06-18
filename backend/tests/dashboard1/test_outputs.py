# -*- coding: utf-8 -*-
"""C:LUMI Pydantic Output 20 모델 — frontend typed contract 회귀.

검증:
  T1 각 tool 의 execute() 결과를 Pydantic Output 으로 validate 통과 (20 케이스)
  T2 핵심 회귀값 (4월 정답) 이 Pydantic field 에서 그대로 노출
  T3 _storage / _meta 자동 무시 (extra='ignore')

계획서: docs/_claude/frontend/clumi_2026_04_대시보드_계획서_2026-05-26.md §2.3 / §5 DoD Step 1
신설: 2026-05-26 — frontend Step 1.
"""
from __future__ import annotations
import asyncio
import pytest

from app.dream_agent.models import ExecutionContext
from app.schemas.outputs.dashboard1 import (
    # KPI 9
    RevenueOutput, AdCostOutput, RoasOutput, CacOutput,
    PromoRevenueOutput, PromoRoasOutput, NewMembersOutput,
    AovOutput, SignupConversionOutput,
    # MoM 4
    MomRevenueOutput, RepurchaseMomOutput, AovMomOutput, NewMembersMomOutput,
    # Segment 7
    GradeRevenueOutput, GradeTimeseriesOutput, AgeSegmentOutput,
    CategoryDistOutput, ChannelDistOutput, MemberGuestOutput, UnknownShareOutput,
)
from app.dream_agent.tools.comparison.aov_mom import AovMom
from app.dream_agent.tools.comparison.grade_timeseries import GradeTimeseries
from app.dream_agent.tools.comparison.mom_revenue import MomRevenue
from app.dream_agent.tools.comparison.new_members_mom import NewMembersMom
from app.dream_agent.tools.comparison.repurchase_mom import RepurchaseMom
from app.dream_agent.tools.metrics.age_segment import AgeSegment
from app.dream_agent.tools.metrics.aov_monthly import AovMonthly
from app.dream_agent.tools.metrics.cac_overall import CacOverall
from app.dream_agent.tools.metrics.grade_revenue import GradeRevenue
from app.dream_agent.tools.metrics.new_members_monthly import NewMembersMonthly
from app.dream_agent.tools.metrics.promotion_revenue import PromotionRevenue
from app.dream_agent.tools.metrics.promotion_roas import PromotionRoas
from app.dream_agent.tools.metrics.revenue_total import RevenueTotal
from app.dream_agent.tools.metrics.roas_overall import RoasOverall
from app.dream_agent.tools.metrics.signup_conversion import SignupConversion
from app.dream_agent.tools.metrics.unknown_revenue_share import UnknownRevenueShare
from app.dream_agent.tools.normalization.channel_attribution_normalizer import (
    ChannelAttributionNormalizer,
)
from app.dream_agent.tools.metrics.ad_cost_total import AdCostTotal
from app.dream_agent.tools.metrics.category_multi_distributor import (
    CategoryMultiDistributor,
)
from app.dream_agent.tools.metrics.member_guest_stats import (
    MemberGuestStats,
)
from app.dream_agent.tools.registry import get_registry
from app.dream_agent.tools.shared.storage import (
    FileStorage, reset_storage, set_storage,
)


PERIOD = "2026-04"
PERIOD_PREV = "2026-03"


@pytest.fixture
def ctx() -> ExecutionContext:
    return ExecutionContext(session_id="t", plan_id="t", client_id="clumi")


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path):
    set_storage(FileStorage(tmp_path))
    yield
    reset_storage()


# =========================================================================
# Section 1. KPI 9 — execute 결과 → Pydantic validate (회귀값 동시 확인)
# =========================================================================


def test_revenue_output_validates(ctx):
    """K-1 매출 119,539,660 + Pydantic validate."""
    reg = get_registry()
    r = asyncio.run(RevenueTotal(reg.get("revenue_total")).execute({"period": PERIOD}, ctx))
    out = RevenueOutput.model_validate(r)
    assert out.revenue_total == 119_539_660
    assert out.period == PERIOD
    assert out.active_orders_count > 0


def test_ad_cost_output_validates(ctx):
    """K-2 마케팅비 26,806,923 (가 결정 A-5.2 google 포함) + Pydantic validate."""
    reg = get_registry()
    r = asyncio.run(AdCostTotal(reg.get("ad_cost_total")).execute({"period": PERIOD}, ctx))
    out = AdCostOutput.model_validate(r)
    assert out.total_cost == 26_806_923
    assert out.by_channel["meta"] == 9_235_826
    assert out.by_channel["naver_sa"] == 5_999_627
    assert out.by_channel["google"] == 8_500_000


def test_roas_output_validates(ctx):
    """K-3 ROAS 4.46 (가 결정 A-5.2 google 포함) + Pydantic validate."""
    reg = get_registry()
    r = asyncio.run(RoasOverall(reg.get("roas_overall")).execute({"period": PERIOD}, ctx))
    out = RoasOutput.model_validate(r)
    assert out.roas == 4.46
    assert out.total_revenue == 119_539_660
    assert out.total_marketing_cost == 26_806_923


def test_cac_output_validates(ctx):
    """K-4 CAC 44,678 (가 결정 A-5.2 google 포함) + Pydantic validate."""
    reg = get_registry()
    r = asyncio.run(CacOverall(reg.get("cac_overall")).execute({"period": PERIOD}, ctx))
    out = CacOutput.model_validate(r)
    assert out.cac == 44_678
    assert out.new_members_count == 600


def test_promo_revenue_output_validates(ctx):
    """K-5 프로모션 매출 43,400,360 + Pydantic validate."""
    reg = get_registry()
    r = asyncio.run(PromotionRevenue(reg.get("promotion_revenue")).execute({"period": PERIOD}, ctx))
    out = PromoRevenueOutput.model_validate(r)
    assert out.promotion_revenue == 43_400_360
    assert out.promotion_share_pct == 36.3
    assert out.total_revenue == 119_539_660


def test_promo_roas_output_validates(ctx):
    """K-6 프로모션 ROAS 1.62 (가 결정 A-5.2 google 포함) + Pydantic validate."""
    reg = get_registry()
    r = asyncio.run(PromotionRoas(reg.get("promotion_roas")).execute({"period": PERIOD}, ctx))
    out = PromoRoasOutput.model_validate(r)
    assert out.promotion_roas == 1.62
    assert out.promotion_revenue == 43_400_360


def test_new_members_output_validates(ctx):
    """K-7 신규 600 + 채널 dict + Pydantic validate."""
    reg = get_registry()
    r = asyncio.run(NewMembersMonthly(reg.get("new_members_monthly")).execute({"period": PERIOD}, ctx))
    out = NewMembersOutput.model_validate(r)
    assert out.new_members_total == 600
    # 채널 분포 sum == total
    assert sum(out.new_members_by_channel.values()) == 600


def test_aov_output_validates(ctx):
    """K-8 객단가 62,293 + Pydantic validate."""
    reg = get_registry()
    r = asyncio.run(AovMonthly(reg.get("aov_monthly")).execute({"period": PERIOD}, ctx))
    out = AovOutput.model_validate(r)
    assert out.aov == 62_293
    assert out.unique_buyers == 1_386
    assert out.orders_count == 1_919


def test_signup_conversion_output_validates(ctx):
    """K-9 가입전환 2.50% + Pydantic validate."""
    reg = get_registry()
    r = asyncio.run(SignupConversion(reg.get("signup_conversion")).execute({"period": PERIOD}, ctx))
    out = SignupConversionOutput.model_validate(r)
    assert out.signup_conversion_pct == 2.50
    assert out.signups == 600


# =========================================================================
# Section 2. MoM 4 — period_a / period_b
# =========================================================================


def test_mom_revenue_output_validates(ctx):
    """M-1 매출 MoM +50.5% + Pydantic validate."""
    reg = get_registry()
    r = asyncio.run(MomRevenue(reg.get("mom_revenue")).execute(
        {"period_a": PERIOD_PREV, "period_b": PERIOD}, ctx))
    out = MomRevenueOutput.model_validate(r)
    assert out.delta_pct == 50.5
    assert out.period_b_revenue == 119_539_660


def test_repurchase_mom_output_validates(ctx):
    """M-3·M-4·B-2·B-3 재구매율 MoM (existing +19.2 / new +1.4 / rate +2.8pp)."""
    reg = get_registry()
    r = asyncio.run(RepurchaseMom(reg.get("repurchase_mom")).execute(
        {"period_a": PERIOD_PREV, "period_b": PERIOD}, ctx))
    out = RepurchaseMomOutput.model_validate(r)
    assert out.delta.existing_buyers_pct == 19.2
    assert out.delta.new_buyers_pct == 1.4
    assert out.delta.repurchase_rate_pp == 2.8
    assert out.period_a_stats.repurchase_rate == 76.2
    assert out.period_b_stats.repurchase_rate == 79.0


def test_aov_mom_output_validates(ctx):
    """M-2 주문 MoM +42.6% + 객단가 MoM +5.6% + Pydantic validate."""
    reg = get_registry()
    r = asyncio.run(AovMom(reg.get("aov_mom")).execute(
        {"period_a": PERIOD_PREV, "period_b": PERIOD}, ctx))
    out = AovMomOutput.model_validate(r)
    assert out.delta.orders_pct == 42.6
    assert out.delta.aov_pct == 5.6
    assert out.period_b_stats.aov == 62_293


def test_new_members_mom_output_validates(ctx):
    """B-4 신규가입 MoM -0.2% + Pydantic validate."""
    reg = get_registry()
    r = asyncio.run(NewMembersMom(reg.get("new_members_mom")).execute(
        {"period_a": PERIOD_PREV, "period_b": PERIOD}, ctx))
    out = NewMembersMomOutput.model_validate(r)
    assert out.delta_pct == -0.2
    assert out.period_b_total == 600
    assert out.period_a_total == 601


# =========================================================================
# Section 3-8. Segment 7
# =========================================================================


def test_grade_revenue_output_validates(ctx):
    """L-2 등급 표 — SILVER 매출 65,757,080 + WELCOME 74.5% + Pydantic validate."""
    reg = get_registry()
    r = asyncio.run(GradeRevenue(reg.get("grade_revenue")).execute({"period": PERIOD}, ctx))
    out = GradeRevenueOutput.model_validate(r)
    assert out.silver_revenue == 65_757_080
    assert out.welcome_member_share == 74.5
    assert out.total_members == 8_500
    # 표의 5등급 키 존재
    for g in ("VIP", "GOLD", "SILVER", "REGULAR", "WELCOME"):
        assert g in out.table


def test_grade_timeseries_output_validates(ctx):
    """L-1 등급 시계열 4시점 6,680→7,299→7,900→8,500 + Pydantic validate."""
    reg = get_registry()
    r = asyncio.run(GradeTimeseries(reg.get("grade_timeseries")).execute({}, ctx))
    out = GradeTimeseriesOutput.model_validate(r)
    totals = [snap.total for snap in out.timeline]
    assert totals == [6_680, 7_299, 7_900, 8_500]
    assert out.snapshot_count == 4
    assert out.latest_snapshot is not None
    assert out.latest_snapshot.total == 8_500


def test_age_segment_output_validates(ctx):
    """G-1·G-2 연령 11 bucket + 35-44 합 2,884 + Pydantic validate."""
    reg = get_registry()
    r = asyncio.run(AgeSegment(reg.get("age_segment")).execute({}, ctx))
    out = AgeSegmentOutput.model_validate(r)
    assert out.core_segment_35_44 == 2_884
    assert out.total_members == 8_500
    assert out.table["40-44"].count == 1_455
    assert out.table["35-39"].count == 1_429


def test_category_dist_output_validates(ctx):
    """T-1 카테고리 5 — 스킨케어 67,652,216 + Pydantic validate."""
    reg = get_registry()
    r = asyncio.run(CategoryMultiDistributor(reg.get("category_multi_distributor")).execute(
        {"period": PERIOD}, ctx))
    out = CategoryDistOutput.model_validate(r)
    assert out.by_category["스킨케어"].revenue == 67_652_216
    assert out.by_category["스킨케어"].count == 1_400
    assert out.total_categories >= 5


def test_channel_dist_output_validates(ctx):
    """C-1 채널 분포 (10채널) + Pydantic validate."""
    reg = get_registry()
    r = asyncio.run(ChannelAttributionNormalizer(reg.get("channel_attribution_normalizer")).execute(
        {"period": PERIOD}, ctx))
    out = ChannelDistOutput.model_validate(r)
    assert out.by_raw_channel["unknown"] == 481
    assert out.by_raw_channel["naver_search"] == 283
    assert out.by_group["Naver"] == 530
    assert out.by_group["Meta"] == 388


def test_member_guest_output_validates(ctx):
    """B-1 회원 1,779 / 비회원 140 + Pydantic validate."""
    reg = get_registry()
    r = asyncio.run(MemberGuestStats(reg.get("member_guest_stats")).execute(
        {"period": PERIOD}, ctx))
    out = MemberGuestOutput.model_validate(r)
    assert out.member_count == 1_779
    assert out.guest_count == 140
    assert out.total_active == 1_919


def test_unknown_share_output_validates(ctx):
    """C-2 알수없음 매출비중 39.8% + Pydantic validate."""
    reg = get_registry()
    r = asyncio.run(UnknownRevenueShare(reg.get("unknown_revenue_share")).execute(
        {"period": PERIOD}, ctx))
    out = UnknownShareOutput.model_validate(r)
    assert out.unknown_share_pct == 39.8
    assert out.total_revenue == 119_539_660


# =========================================================================
# T3. extra='ignore' — _storage / _meta 자동 무시 확인
# =========================================================================


def test_extra_storage_meta_ignored(ctx):
    """_storage / _meta 같이 들어와도 Pydantic validate 통과 (extra='ignore')."""
    reg = get_registry()
    r = asyncio.run(RevenueTotal(reg.get("revenue_total")).execute({"period": PERIOD}, ctx))
    # 실제 tool 결과는 _storage / _meta 를 포함
    assert "_storage" in r or "_meta" in r
    # validate 통과 — 추가 키 무시
    out = RevenueOutput.model_validate(r)
    # dump 시에는 _storage / _meta 가 들어가지 않음
    dumped = out.model_dump()
    assert "_storage" not in dumped
    assert "_meta" not in dumped
