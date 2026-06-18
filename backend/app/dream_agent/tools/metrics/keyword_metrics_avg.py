"""keyword_metrics_avg — 키워드 평균 ROAS + 운영 수 (K24).

Status: complete — Phase 1 Batch 6 (2026-05-28).
"""
from __future__ import annotations

from statistics import mean
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.schemas.inputs.keyword_performance import load_keyword_performance
from app.schemas.outputs.cost import KeywordMetricsOutput

logger = get_logger(__name__)


class KeywordMetricsAvg(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        rows = load_keyword_performance(self.fetch("keyword_performance", context)).rows
        return KeywordMetricsOutput(
            avg_roas=round(float(mean([r.roas for r in rows])), 2) if rows else 0.0,
            keyword_count=len(rows),
        ).model_dump()
