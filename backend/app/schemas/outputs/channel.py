"""channel (Batch 3) 출력 schema — daily_performance 의 channel 집계.

clumi 방향: 별 channel_performance dataset 없이 daily_performance 재사용.
C05(bar)·T05(table) = 동일 ChannelMetricsOutput 공유(frontend projection) → cache 공유.

Status: complete — Phase 1 Batch 3 (2026-05-28).
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ChannelMetricsOutput(BaseModel):
    """매체별 집계 행 (C05 bar 3 시리즈 + T05 9 컬럼 공용)."""

    model_config = ConfigDict(extra="ignore")

    rows: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0


class ConversionFunnelOutput(BaseModel):
    """전환 퍼널 단계 (C06). rows = [{stage, value, pct_of_top}]."""

    model_config = ConfigDict(extra="ignore")

    rows: list[dict[str, Any]] = Field(default_factory=list)


__all__ = ["ChannelMetricsOutput", "ConversionFunnelOutput"]
