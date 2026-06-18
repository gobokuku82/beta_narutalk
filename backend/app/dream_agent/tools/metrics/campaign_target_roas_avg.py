"""Campaign Target ROAS Avg — K13 (평균 목표 ROAS).

methodology: M01.
AVG(campaigns.target_roas).

Status: complete — 2026-05-30 campaigns_aggregate 분리 (4/4).
"""
from __future__ import annotations
from statistics import mean
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.schemas.inputs.campaigns import load_campaigns
from app.schemas.outputs.dashboard_v1 import MetricScalarOutput

logger = get_logger(__name__)


class CampaignTargetRoasAvg(BaseTool):
    """평균 목표 ROAS — K13."""

    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        rows = load_campaigns(self.fetch("campaigns", context)).rows
        vals = [getattr(r, "target_roas", 0) for r in rows]
        value = round(float(mean(vals)), 4) if vals else 0.0
        logger.info("campaign_target_roas_avg", value=value, n=len(rows))
        return MetricScalarOutput(
            value=value, op="avg", field="target_roas",
            label=merged.get("label", "평균 목표 ROAS"), unit=merged.get("unit", "%"),
        ).model_dump()
