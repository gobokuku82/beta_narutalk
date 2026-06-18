"""keyword_performance 표준 schema — 컬럼명 단일 진실 소스 (Batch 6).

mock raw: data/clumi/raw/keyword_performance.csv (키워드 성과 + 경쟁강도·품질지수).

Status: complete — Phase 1 Batch 6 (2026-05-28).
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field


class KeywordRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    keyword: str
    channel: str = ""
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    ad_cost: int = 0
    conversion_revenue: int = 0
    roas: float = 0.0
    competition: str = ""
    quality_score: float = 0.0
    keyword_group: str = ""


class KeywordPerformanceSchema(BaseModel):
    rows: list[KeywordRow] = Field(default_factory=list)


def load_keyword_performance(df: pd.DataFrame) -> KeywordPerformanceSchema:
    records: list[dict[str, Any]] = json.loads(df.to_json(orient="records"))
    return KeywordPerformanceSchema(rows=[KeywordRow.model_validate(r) for r in records])


__all__ = ["KeywordRow", "KeywordPerformanceSchema", "load_keyword_performance"]
