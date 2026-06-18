"""Campaign Count — K10 (총 캠페인 수).

methodology: M01 (campaign KPI).
campaigns 행 수 (period 무관, 전체).

Status: complete — 2026-05-30 campaigns_aggregate 분리 (1/4).
"""
from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.schemas.inputs.campaigns import load_campaigns
from app.schemas.outputs.dashboard_v1 import MetricScalarOutput

logger = get_logger(__name__)


class CampaignCount(BaseTool):
    """캠페인 행 수 — K10."""

    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        rows = load_campaigns(self.fetch("campaigns", context)).rows
        value = float(len(rows))
        logger.info("campaign_count", value=value)
        return MetricScalarOutput(
            value=value, op="count", field="",
            label=merged.get("label", "총 캠페인 수"), unit=merged.get("unit", ""),
        ).model_dump()
