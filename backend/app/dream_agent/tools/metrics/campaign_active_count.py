"""Campaign Active Count — K11 (진행중 캠페인 수).

methodology: M01.
campaigns.status == 'active' 행 수.

Status: complete — 2026-05-30 campaigns_aggregate 분리 (2/4).
"""
from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.schemas.inputs.campaigns import load_campaigns
from app.schemas.outputs.dashboard_v1 import MetricScalarOutput

logger = get_logger(__name__)

ACTIVE_STATUS = "active"


class CampaignActiveCount(BaseTool):
    """진행중 캠페인 수 — K11."""

    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        rows = load_campaigns(self.fetch("campaigns", context)).rows
        active = [r for r in rows if str(getattr(r, "status", None)) == ACTIVE_STATUS]
        value = float(len(active))
        logger.info("campaign_active_count", value=value, total=len(rows))
        return MetricScalarOutput(
            value=value, op="count_where", field="status",
            label=merged.get("label", "진행중 캠페인 수"), unit=merged.get("unit", ""),
        ).model_dump()
