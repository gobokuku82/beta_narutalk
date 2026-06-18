"""ab_tests 표준 schema — 컬럼명 단일 진실 소스 (Batch 5).

mock raw: data/clumi/raw/ab_tests.csv. winner·lift = tool 파생.

Status: complete — Phase 1 Batch 5 (2026-05-28).
"""
from __future__ import annotations

import json
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field


class AbTestRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    test_id: str
    name: str = ""
    metric: str = ""
    variant_a: str = ""
    variant_b: str = ""
    a_value: float = 0.0
    b_value: float = 0.0


class AbTestsSchema(BaseModel):
    rows: list[AbTestRow] = Field(default_factory=list)


def load_ab_tests(df: pd.DataFrame) -> AbTestsSchema:
    records: list[dict[str, Any]] = json.loads(df.to_json(orient="records"))
    return AbTestsSchema(rows=[AbTestRow.model_validate(r) for r in records])


__all__ = ["AbTestRow", "AbTestsSchema", "load_ab_tests"]
