"""Creative ROAS Avg — K20 (평균 소재 ROAS).

methodology: M01.
AVG(creatives.roas).

Status: complete — 2026-05-30 creatives_aggregate 분리 (3/3).
"""
from __future__ import annotations
from statistics import mean
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.schemas.inputs.creatives import load_creatives
from app.schemas.outputs.dashboard_v1 import MetricScalarOutput

logger = get_logger(__name__)


class CreativeRoasAvg(BaseTool):
    """평균 소재 ROAS — K20."""

    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        rows = load_creatives(self.fetch("creatives", context)).rows
        vals = [getattr(r, "roas", 0) for r in rows]
        value = round(float(mean(vals)), 2) if vals else 0.0
        logger.info("creative_roas_avg", value=value, n=len(rows))
        return MetricScalarOutput(
            value=value, op="avg", field="roas",
            label=merged.get("label", "평균 ROAS"), unit=merged.get("unit", "%"),
        ).model_dump()
