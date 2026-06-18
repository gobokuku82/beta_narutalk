"""campaigns 표준 schema — 컬럼명 단일 진실 소스.

mock raw: data/clumi/raw/campaigns.csv (표준 영어 컬럼명 → 필드명 identity).
컬럼 변경 시 *여기 1곳* + CSV 만 수정 (tool 은 필드명 사용 → 무변경).

Status: complete — Phase 1 Batch 2 (2026-05-28).
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field


class CampaignRow(BaseModel):
    """캠페인 1건. status = active|ended|scheduled (표준값)."""

    model_config = ConfigDict(extra="ignore")

    campaign_id: str
    campaign_type: str = ""
    name: str = ""
    product: str = ""
    start_date: str = ""
    end_date: str = ""
    monthly_budget: int = 0
    goal: str = ""
    status: str = ""
    owner: str = ""
    target_roas: float = 0.0
    target_cpa: float = 0.0
    target_conversions: int = 0


class CampaignsSchema(BaseModel):
    rows: list[CampaignRow] = Field(default_factory=list)


def load_campaigns(df: pd.DataFrame) -> CampaignsSchema:
    """raw DataFrame → CampaignsSchema. json 라운드트립으로 NaN→null·numpy→native."""
    records: list[dict[str, Any]] = json.loads(df.to_json(orient="records"))
    return CampaignsSchema(rows=[CampaignRow.model_validate(r) for r in records])


__all__ = ["CampaignRow", "CampaignsSchema", "load_campaigns"]
