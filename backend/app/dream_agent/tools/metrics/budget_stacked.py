"""budget_stacked — 구분 × 채널 예산 누적 (C10 stacked bar).

Status: complete — Phase 1 Batch 6 (2026-05-28).
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.schemas.inputs.budget_allocation import CHANNEL_FIELDS, load_budget_allocation
from app.schemas.outputs.cost import BudgetStackedOutput

logger = get_logger(__name__)


class BudgetStacked(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        rows = load_budget_allocation(self.fetch("budget_allocation", context)).rows

        out = [
            {"segment": r.segment, **{f: int(getattr(r, f, 0)) for f in CHANNEL_FIELDS}}
            for r in rows
        ]
        channels = [f.replace("_budget", "") for f in CHANNEL_FIELDS]
        return BudgetStackedOutput(rows=out, channels=channels).model_dump()
