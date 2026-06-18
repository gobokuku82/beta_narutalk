"""creatives 표준 schema — 컬럼명 단일 진실 소스 (Batch 5).

mock raw: data/clumi/raw/creatives.csv. AI 5축·피로 = raw 아님 → MockMlModel(M3) 제공.

Status: complete — Phase 1 Batch 5 (2026-05-28).
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field


class CreativeRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    creative_id: str
    campaign_id: str = ""
    name: str = ""
    channel: str = ""
    format: str = ""
    headline: str = ""
    body: str = ""
    image_url: str = ""
    landing_url: str = ""
    start_date: str = ""
    status: str = ""
    frequency: float = 0.0
    run_days: int = 0
    ctr: float = 0.0
    cvr: float = 0.0
    cpc: float = 0.0
    roas: float = 0.0
    cpa: float = 0.0


class CreativesSchema(BaseModel):
    rows: list[CreativeRow] = Field(default_factory=list)


def load_creatives(df: pd.DataFrame) -> CreativesSchema:
    records: list[dict[str, Any]] = json.loads(df.to_json(orient="records"))
    return CreativesSchema(rows=[CreativeRow.model_validate(r) for r in records])


__all__ = ["CreativeRow", "CreativesSchema", "load_creatives"]
