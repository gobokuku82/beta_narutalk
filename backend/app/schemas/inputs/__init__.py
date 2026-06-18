"""표준 입력 schema — DataSource raw → Pydantic. 컬럼명 = 필드명 (단일 진실 소스)."""
from app.schemas.inputs.campaigns import CampaignRow, CampaignsSchema, load_campaigns
# daily_performance 입력 스키마 제거 (A-5.3): 4 tool이 canonical 소비로 전환되어 로더 불요.
from app.schemas.inputs.ab_tests import AbTestRow, AbTestsSchema, load_ab_tests
from app.schemas.inputs.budget_allocation import (
    BudgetAllocationSchema,
    BudgetRow,
    load_budget_allocation,
)
from app.schemas.inputs.creatives import CreativeRow, CreativesSchema, load_creatives
from app.schemas.inputs.keyword_performance import (
    KeywordPerformanceSchema,
    KeywordRow,
    load_keyword_performance,
)
from app.schemas.inputs.reviews import ReviewRow, ReviewsSchema, load_reviews

__all__ = [
    "CampaignRow",
    "CampaignsSchema",
    "load_campaigns",
    "ReviewRow",
    "ReviewsSchema",
    "load_reviews",
    "CreativeRow",
    "CreativesSchema",
    "load_creatives",
    "AbTestRow",
    "AbTestsSchema",
    "load_ab_tests",
    "BudgetRow",
    "BudgetAllocationSchema",
    "load_budget_allocation",
    "KeywordRow",
    "KeywordPerformanceSchema",
    "load_keyword_performance",
]
