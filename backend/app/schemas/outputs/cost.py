"""cost (Batch 6) 출력 schema.

K22/K23 = BudgetTotalsOutput 공유. K24 = KeywordMetricsOutput. C09 = BudgetChannelShareOutput.
C10 = BudgetStackedOutput. T07 = KeywordTableOutput. O05 = RecommendationOutput(ml_model).

Status: complete — Phase 1 Batch 6 (2026-05-28).
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BudgetTotalsOutput(BaseModel):
    """총 예산 + 평균 집행률 (K22·K23 공유)."""

    model_config = ConfigDict(extra="ignore")

    total_budget: int = 0
    avg_exec_rate: float = 0.0


class KeywordMetricsOutput(BaseModel):
    """키워드 평균 ROAS + 운영 수 (K24)."""

    model_config = ConfigDict(extra="ignore")

    avg_roas: float = 0.0
    keyword_count: int = 0


class BudgetChannelShareOutput(BaseModel):
    """채널별 예산 비중 (C09 도넛). rows=[{channel, budget, share}]."""

    model_config = ConfigDict(extra="ignore")

    rows: list[dict[str, Any]] = Field(default_factory=list)
    total_budget: int = 0


class BudgetStackedOutput(BaseModel):
    """구분 × 채널 예산 누적 (C10 stacked bar). rows=[{segment, naver_budget, ...}]."""

    model_config = ConfigDict(extra="ignore")

    rows: list[dict[str, Any]] = Field(default_factory=list)
    channels: list[str] = Field(default_factory=list)


class KeywordTableOutput(BaseModel):
    """키워드 ROI 테이블 + 경쟁 Badge (T07). rows=[{keyword, roas, competition, ...}]."""

    model_config = ConfigDict(extra="ignore")

    rows: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0


class RecommendationOutput(BaseModel):
    """AI 추천 카드 (O05). rows=[{priority, title, detail}]. ml_model.generate_recommendation."""

    model_config = ConfigDict(extra="ignore")

    rows: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0


__all__ = [
    "BudgetTotalsOutput",
    "KeywordMetricsOutput",
    "BudgetChannelShareOutput",
    "BudgetStackedOutput",
    "KeywordTableOutput",
    "RecommendationOutput",
]
