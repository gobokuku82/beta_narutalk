"""Dashboard1 출력 schema — Pydantic Output 모델 (frontend typed contract).

dashboard1(Batch 1) 의 KPI 9 + MoM 4 + Segment 7 = 20 출력 스키마.
각 모델은 `app/dream_agent/tools/` 의 BaseTool execute() 결과(`_storage`·`_meta` 제외) 와 1:1.

ADR-027 §4: 출력 schema 는 client 무관 표준 위치(`app/schemas/outputs/`) 에 둔다.
(구 `app/dream_agent/models/clumi_outputs.py` 에서 이전 — 2026-05-28, 이름 정리 E2)

Status: complete — 2026-05-28 (clumi_outputs → schemas/outputs 통합).
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


# ─────────────────────────────────────────────────────────────────────────
# 공통 — _storage / _meta 무시 (tool 결과 dict 그대로 model_validate 가능)
# ─────────────────────────────────────────────────────────────────────────


class _OutputBase(BaseModel):
    """모든 dashboard1 output 의 base — extra='ignore' 로 _storage·_meta 자동 무시."""

    model_config = ConfigDict(extra="ignore")


# =========================================================================
# Section 1. 핵심 KPI 9 (정량 17/17 답)
# =========================================================================


class RevenueOutput(_OutputBase):
    """K-1 매출 — methodology §S001 (4월 정답 119,539,660)."""

    revenue_total: int
    active_orders_count: int
    period: str


class AdCostOutput(_OutputBase):
    """K-2 마케팅비 — methodology §S003 (4월 정답 26,806,923, 6매체 — 가 결정 A-5.2 google 포함)."""

    total_cost: int
    by_channel: dict[str, int]
    period: str


class RoasOutput(_OutputBase):
    """K-3 전체 ROAS — methodology §S004 (4월 정답 4.46 — 가 결정 A-5.2 google 포함)."""

    roas: float
    total_revenue: int
    total_marketing_cost: int
    period: str


class CacOutput(_OutputBase):
    """K-4 전체 CAC — methodology §S032 (4월 정답 44,678 — 가 결정 A-5.2 google 포함)."""

    cac: int
    total_marketing_cost: int
    new_members_count: int
    period: str


class PromoRevenueOutput(_OutputBase):
    """K-5 프로모션 매출 — methodology §S002 (4월 정답 43,400,360 / 36.3%)."""

    promotion_revenue: int
    promotion_share_pct: float
    promotion_orders_count: int
    total_revenue: int
    period: str


class PromoRoasOutput(_OutputBase):
    """K-6 프로모션 ROAS — methodology §S005 (4월 정답 1.62 — 가 결정 A-5.2 google 포함)."""

    promotion_roas: float
    promotion_revenue: int
    total_marketing_cost: int
    period: str


class NewMembersOutput(_OutputBase):
    """K-7 신규 회원 — methodology §S069 (4월 정답 600, 채널별 분포 동반)."""

    new_members_total: int
    new_members_by_channel: dict[str, int]
    period: str


class AovOutput(_OutputBase):
    """K-8 객단가 — methodology §S048 (4월 정답 62,293 / 구매자 1,386 / 주문 1,919)."""

    aov: int
    unique_buyers: int
    orders_count: int
    period: str


class SignupConversionOutput(_OutputBase):
    """K-9 가입 전환율 — methodology §S067 (4월 정답 2.50%)."""

    signup_conversion_pct: float
    signups: int
    sessions: int
    period: str


# =========================================================================
# Section 2. MoM 변화 4 (4월 vs 3월)
# =========================================================================


class MomRevenueOutput(_OutputBase):
    """M-1 매출 MoM — methodology §S001 MoM (정답 +50.5%)."""

    period_a_revenue: int
    period_b_revenue: int
    delta_pct: float
    period_a: str
    period_b: str


class _RepurchaseStats(BaseModel):
    """RepurchaseMom 각 월 stat block."""

    total_buyers: int
    existing_buyers: int
    new_buyers: int
    repurchase_rate: float


class _RepurchaseDelta(BaseModel):
    """RepurchaseMom delta block (정답: existing +19.2%·new +1.4%·rate +2.8%p)."""

    total_buyers_pct: float
    existing_buyers_pct: float
    new_buyers_pct: float
    repurchase_rate_pp: float


class RepurchaseMomOutput(_OutputBase):
    """M-3·M-4·B-2·B-3 재구매율 MoM — methodology §S028 MoM."""

    period_a_stats: _RepurchaseStats
    period_b_stats: _RepurchaseStats
    delta: _RepurchaseDelta
    period_a: str
    period_b: str


class _AovStats(BaseModel):
    """AovMom 각 월 stat block."""

    aov: int
    unique_buyers: int
    orders_count: int


class _AovDelta(BaseModel):
    """AovMom delta block (정답: orders +42.6%·aov +5.6%·buyers +14.9%)."""

    aov_pct: float
    buyers_pct: float
    orders_pct: float


class AovMomOutput(_OutputBase):
    """M-2 객단가/주문 MoM — methodology §S048 MoM."""

    period_a_stats: _AovStats
    period_b_stats: _AovStats
    delta: _AovDelta
    period_a: str
    period_b: str


class NewMembersMomOutput(_OutputBase):
    """B-4 신규 가입 MoM — methodology §S069 MoM (정답 601→600 = -0.2%)."""

    period_a_total: int
    period_b_total: int
    delta_pct: float
    by_channel_a: dict[str, int]
    by_channel_b: dict[str, int]
    period_a: str
    period_b: str


# =========================================================================
# Section 3-8. Segment 7
# =========================================================================


class _GradeRow(BaseModel):
    """GradeRevenue 등급별 row (회원·매출)."""

    member_count: int
    member_share_pct: float
    buyer_count: int
    revenue: int
    revenue_share_pct: float


class GradeRevenueOutput(_OutputBase):
    """L-2 등급별 회원·매출 — methodology §S046 (정답: SILVER 65,757,080·WELCOME 74.5%)."""

    table: dict[str, _GradeRow]
    total_members: int
    total_member_revenue: int
    silver_revenue: int
    welcome_member_share: float
    period: str


class _GradeSnapshot(BaseModel):
    """GradeTimeseries 시계열 1 시점 (4시점 = 1·2·3·4월 말)."""

    snapshot_date: str
    grade_counts: dict[str, int]
    total: int


class GradeTimeseriesOutput(_OutputBase):
    """L-1 등급 회원수 시계열 — methodology §S045 (정답 6,680→7,299→7,900→8,500)."""

    timeline: list[_GradeSnapshot]
    latest_snapshot: _GradeSnapshot | None = None
    growth_rates: dict[str, float | None]
    snapshot_count: int


class _AgeBucketRow(BaseModel):
    """AgeSegment 5세 bucket row."""

    count: int
    share_pct: float


class AgeSegmentOutput(_OutputBase):
    """G-1·G-2 연령 분포 — methodology §S037 (정답 11 bucket + 35-44 합 2,884)."""

    table: dict[str, _AgeBucketRow]
    total_members: int
    core_segment_35_44: int


class _CategoryRow(BaseModel):
    """CategoryMultiDistributor 카테고리 row (count + 분배 매출)."""

    count: int
    revenue: int


class CategoryDistOutput(_OutputBase):
    """T-1 카테고리 5 분배 — methodology §정제 7 (정답: 스킨케어 67.7M·클렌징 19.1M)."""

    by_category: dict[str, _CategoryRow]
    total_categories: int
    total_distributed_revenue: int
    period: str


class ChannelDistOutput(_OutputBase):
    """C-1 채널 분포 — methodology §정제 4 (정답: Naver 530·Unknown 481·Meta 388·...)."""

    by_raw_channel: dict[str, int]
    by_group: dict[str, int]
    mapping: dict[str, str]
    period: str


class MemberGuestOutput(_OutputBase):
    """B-1 회원/비회원 — methodology §정제 10 (정답: 회원 1,779 / 비회원 140)."""

    member_count: int
    guest_count: int
    total_active: int
    member_share_pct: float
    guest_share_pct: float
    period: str


class UnknownShareOutput(_OutputBase):
    """C-2 알수없음 매출비중 — methodology §S054 (정답 39.8%)."""

    unknown_share_pct: float
    unknown_revenue: int
    total_revenue: int
    unknown_orders: int
    period: str


__all__ = [
    # KPI 9
    "RevenueOutput",
    "AdCostOutput",
    "RoasOutput",
    "CacOutput",
    "PromoRevenueOutput",
    "PromoRoasOutput",
    "NewMembersOutput",
    "AovOutput",
    "SignupConversionOutput",
    # MoM 4
    "MomRevenueOutput",
    "RepurchaseMomOutput",
    "AovMomOutput",
    "NewMembersMomOutput",
    # Segment 7
    "GradeRevenueOutput",
    "GradeTimeseriesOutput",
    "AgeSegmentOutput",
    "CategoryDistOutput",
    "ChannelDistOutput",
    "MemberGuestOutput",
    "UnknownShareOutput",
]
