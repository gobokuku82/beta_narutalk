"""reviews 표준 schema — 컬럼명 단일 진실 소스 (Batch 4).

mock raw: data/clumi/raw/reviews.csv. 감성·키워드는 raw 아님 → MockMlModel(M3) 제공.

Status: complete — Phase 1 Batch 4 (2026-05-28).
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field


class ReviewRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    review_id: str
    date: str = ""
    product: str = ""
    rating: int = 0
    text: str = ""


class ReviewsSchema(BaseModel):
    rows: list[ReviewRow] = Field(default_factory=list)


def load_reviews(df: pd.DataFrame) -> ReviewsSchema:
    records: list[dict[str, Any]] = json.loads(df.to_json(orient="records"))
    return ReviewsSchema(rows=[ReviewRow.model_validate(r) for r in records])


__all__ = ["ReviewRow", "ReviewsSchema", "load_reviews"]
