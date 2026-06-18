"""google_ads_performance 표준 schema — clumi_mock_18 (canonical 18번째 벤더소스).

mock raw: data/clumi/raw/google_ads_performance.csv (일별·캠페인별 Google Ads 유료 성과).
A1 결정(2026-06-16): google = canonical ad 채널 6번째. 컬럼 변경 시 *여기 1곳* + CSV.
생성기: backend/scripts/gen_google_ads_mock.py (결정론).

Status: complete — 2026-06-16 (A1).
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator


class GoogleAdsRow(BaseModel):
    """일별 × 캠페인 Google Ads 성과 1행."""

    model_config = ConfigDict(extra="ignore")

    report_date: str
    campaign_id: str = ""
    campaign_name: str = ""
    campaign_type: str = ""            # SEARCH·PMAX·DISPLAY·SHOPPING·VIDEO
    network: str = ""                  # SEARCH·DISPLAY·YOUTUBE
    impressions: int = 0
    clicks: int = 0
    ctr: float = 0.0
    avg_cpc: int = 0
    cost: int = 0                      # → canonical ad_cost_krw (google source)
    conversions: int = 0              # → conversion_count
    conversion_value: int = 0         # → conversion_revenue_krw
    cost_per_conversion: int = 0
    conversion_rate: float = 0.0
    search_impression_share: float = 0.0   # 비-SEARCH 네트워크는 공란(→0.0)
    video_views: int = 0

    @field_validator("search_impression_share", mode="before")
    @classmethod
    def _blank_to_zero(cls, v: Any) -> Any:
        return 0.0 if v in ("", None) else v


class GoogleAdsSchema(BaseModel):
    rows: list[GoogleAdsRow] = Field(default_factory=list)


def load_google_ads_performance(df: pd.DataFrame) -> GoogleAdsSchema:
    records: list[dict[str, Any]] = json.loads(df.to_json(orient="records"))
    return GoogleAdsSchema(rows=[GoogleAdsRow.model_validate(r) for r in records])


__all__ = ["GoogleAdsRow", "GoogleAdsSchema", "load_google_ads_performance"]
