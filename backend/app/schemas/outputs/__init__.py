"""표준 출력 schema — Tool 산출 형식 (ADR-027 §4)."""
from app.schemas.outputs.dashboard1 import (
    AdCostOutput,
    AgeSegmentOutput,
    AovMomOutput,
    AovOutput,
    CacOutput,
    CategoryDistOutput,
    ChannelDistOutput,
    GradeRevenueOutput,
    GradeTimeseriesOutput,
    MemberGuestOutput,
    MomRevenueOutput,
    NewMembersMomOutput,
    NewMembersOutput,
    PromoRevenueOutput,
    PromoRoasOutput,
    RepurchaseMomOutput,
    RevenueOutput,
    RoasOutput,
    SignupConversionOutput,
    UnknownShareOutput,
)
from app.schemas.outputs.channel import ChannelMetricsOutput, ConversionFunnelOutput
from app.schemas.outputs.cost import (
    BudgetChannelShareOutput,
    BudgetStackedOutput,
    BudgetTotalsOutput,
    KeywordMetricsOutput,
    KeywordTableOutput,
    RecommendationOutput,
)
from app.schemas.outputs.dashboard_v1 import (
    CampaignsTableOutput,
    DailySeriesOutput,
    MetricScalarOutput,
)
from app.schemas.outputs.creative import (
    AbTestTableOutput,
    AiAxesRadarOutput,
    CreativeCardsOutput,
)
from app.schemas.outputs.trend import (
    DailyPerformanceTotalsOutput,
    KeywordsTopNOutput,
    ReviewCardsOutput,
    SentimentDistributionOutput,
)

__all__ = [
    # dashboard1 (KPI 9 + MoM 4 + Segment 7)
    "RevenueOutput", "AdCostOutput", "RoasOutput", "CacOutput",
    "PromoRevenueOutput", "PromoRoasOutput", "NewMembersOutput", "AovOutput",
    "SignupConversionOutput", "MomRevenueOutput", "RepurchaseMomOutput",
    "AovMomOutput", "NewMembersMomOutput", "GradeRevenueOutput",
    "GradeTimeseriesOutput", "AgeSegmentOutput", "CategoryDistOutput",
    "ChannelDistOutput", "MemberGuestOutput", "UnknownShareOutput",
    # dashboard_v1 / channel / trend / creative / cost
    "MetricScalarOutput",
    "CampaignsTableOutput",
    "DailySeriesOutput",
    "ChannelMetricsOutput",
    "ConversionFunnelOutput",
    "DailyPerformanceTotalsOutput",
    "SentimentDistributionOutput",
    "KeywordsTopNOutput",
    "ReviewCardsOutput",
    "AiAxesRadarOutput",
    "CreativeCardsOutput",
    "AbTestTableOutput",
    "BudgetTotalsOutput",
    "KeywordMetricsOutput",
    "BudgetChannelShareOutput",
    "BudgetStackedOutput",
    "KeywordTableOutput",
    "RecommendationOutput",
]
