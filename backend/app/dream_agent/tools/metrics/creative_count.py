"""Creative Count — K18 (총 소재 수).

methodology: M01.
creatives 행 수.

Status: complete — 2026-05-30 creatives_aggregate 분리 (1/3).
"""
from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.schemas.inputs.creatives import load_creatives
from app.schemas.outputs.dashboard_v1 import MetricScalarOutput

logger = get_logger(__name__)


class CreativeCount(BaseTool):
    """소재 행 수 — K18."""

    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        rows = load_creatives(self.fetch("creatives", context)).rows
        value = float(len(rows))
        logger.info("creative_count", value=value)
        return MetricScalarOutput(
            value=value, op="count", field="",
            label=merged.get("label", "총 소재 수"), unit=merged.get("unit", ""),
        ).model_dump()
