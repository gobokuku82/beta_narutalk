"""trend (Batch 4) 출력 schema.

K14~K17 = DailyPerformanceTotalsOutput 공유(4 필드 동시). C07 = DailySeriesOutput(reuse).
C08 = SentimentDistributionOutput(ml_model). C12 = KeywordsTopNOutput(ml_model). O03 = ReviewCardsOutput.

Status: complete — Phase 1 Batch 4 (2026-05-28).
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DailyPerformanceTotalsOutput(BaseModel):
    """daily_performance 기간 총합 (K14~K17 공유 — frontend 가 필드 1개씩 카드)."""

    model_config = ConfigDict(extra="ignore")

    total_impressions: int = 0
    total_clicks: int = 0
    total_conversions: int = 0
    total_ad_cost: int = 0
    period: str = ""


class SentimentDistributionOutput(BaseModel):
    """리뷰 감성 분포 (C08) — MockMlModel.analyze_sentiment 결과."""

    model_config = ConfigDict(extra="ignore")

    positive: int = 0
    neutral: int = 0
    negative: int = 0
    total: int = 0


class KeywordsTopNOutput(BaseModel):
    """키워드 랭킹 (C12) — MockMlModel.extract_keywords 결과. rows=[{keyword,count}]."""

    model_config = ConfigDict(extra="ignore")

    rows: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0


class ReviewCardsOutput(BaseModel):
    """최근 리뷰 카드 (O03). rows = 최신순 리뷰 n건."""

    model_config = ConfigDict(extra="ignore")

    rows: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0


__all__ = [
    "DailyPerformanceTotalsOutput",
    "SentimentDistributionOutput",
    "KeywordsTopNOutput",
    "ReviewCardsOutput",
]
