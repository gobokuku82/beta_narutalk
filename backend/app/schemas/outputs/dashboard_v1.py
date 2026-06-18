"""dashboard_v1 (Batch 2) 출력 schema.

수정영역 최소 설계: KPI 4종(K10~K13)은 *단일* MetricScalarOutput 공유
(campaign_count·campaign_active_count·campaign_budget_total·campaign_target_roas_avg —
작업 ③ 에서 단일 책임 4 tool 로 분리, 출력 schema 는 공유).

Status: complete — Phase 1 Batch 2 (2026-05-28, 작업 ③ 갱신 2026-05-30).
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MetricScalarOutput(BaseModel):
    """단일 스칼라 KPI (count·count_where·sum·avg 공통). K10~K13."""

    model_config = ConfigDict(extra="ignore")

    value: float
    op: str = ""
    field: str = ""
    label: str = ""
    unit: str = ""


class CampaignsTableOutput(BaseModel):
    """캠페인 테이블 (T04) — 행 목록 + 수."""

    model_config = ConfigDict(extra="ignore")

    rows: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0


class DailySeriesOutput(BaseModel):
    """일별 시계열 (C04) — date 별 metric 합산 행."""

    model_config = ConfigDict(extra="ignore")

    rows: list[dict[str, Any]] = Field(default_factory=list)
    metrics: list[str] = Field(default_factory=list)
    period: str = ""


__all__ = ["MetricScalarOutput", "CampaignsTableOutput", "DailySeriesOutput"]
