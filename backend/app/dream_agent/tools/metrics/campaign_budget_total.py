"""Campaign Budget Total — K12 (총 월예산).

methodology: M01.
SUM(campaigns.monthly_budget).

Status: complete — 2026-05-30 campaigns_aggregate 분리 (3/4).
"""
from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.schemas.inputs.campaigns import load_campaigns
from app.schemas.outputs.dashboard_v1 import MetricScalarOutput

logger = get_logger(__name__)


class CampaignBudgetTotal(BaseTool):
    """총 월예산 합산 — K12."""

    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        rows = load_campaigns(self.fetch("campaigns", context)).rows
        value = float(sum(getattr(r, "monthly_budget", 0) for r in rows))
        logger.info("campaign_budget_total", value=value, n=len(rows))
        return MetricScalarOutput(
            value=value, op="sum", field="monthly_budget",
            label=merged.get("label", "총 월예산"), unit=merged.get("unit", "KRW"),
        ).model_dump()
