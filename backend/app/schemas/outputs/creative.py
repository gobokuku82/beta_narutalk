"""creative (Batch 5) 출력 schema.

K18~K21 = MetricScalarOutput 재사용(scalar). C11 = AiAxesRadarOutput(ml_model).
O04 = CreativeCardsOutput. T06 = AbTestTableOutput.

Status: complete — Phase 1 Batch 5 (2026-05-28).
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AiAxesRadarOutput(BaseModel):
    """소재 AI 5축 (C11 radar) — MockMlModel.score_ai_axes 결과."""

    model_config = ConfigDict(extra="ignore")

    ai_sales: float = 0.0
    ai_short: float = 0.0
    ai_clear: float = 0.0
    ai_visual: float = 0.0
    ai_benefit: float = 0.0


class CreativeCardsOutput(BaseModel):
    """소재 카드 Top-N (O04)."""

    model_config = ConfigDict(extra="ignore")

    rows: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0


class AbTestTableOutput(BaseModel):
    """AB 테스트 테이블 (T06) — winner·lift tool 파생 포함."""

    model_config = ConfigDict(extra="ignore")

    rows: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0


__all__ = ["AiAxesRadarOutput", "CreativeCardsOutput", "AbTestTableOutput"]
