"""budget_allocation 표준 schema — 컬럼명 단일 진실 소스 (Batch 6).

mock raw: data/clumi/raw/budget_allocation.csv (구분 × 채널 예산 매트릭스).

Status: complete — Phase 1 Batch 6 (2026-05-28).
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field


class BudgetRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    segment: str
    campaign_type: str = ""
    naver_budget: int = 0
    kakao_budget: int = 0
    meta_budget: int = 0
    google_budget: int = 0
    total_budget: int = 0
    exec_rate: float = 0.0


class BudgetAllocationSchema(BaseModel):
    rows: list[BudgetRow] = Field(default_factory=list)


# 표준 채널 예산 필드 (normalizer 불필요 — 컬럼명 그 자체). C09·C10 채널 분해 기준.
CHANNEL_FIELDS = ("naver_budget", "kakao_budget", "meta_budget", "google_budget")


def load_budget_allocation(df: pd.DataFrame) -> BudgetAllocationSchema:
    records: list[dict[str, Any]] = json.loads(df.to_json(orient="records"))
    return BudgetAllocationSchema(rows=[BudgetRow.model_validate(r) for r in records])


__all__ = ["BudgetRow", "BudgetAllocationSchema", "load_budget_allocation", "CHANNEL_FIELDS"]
