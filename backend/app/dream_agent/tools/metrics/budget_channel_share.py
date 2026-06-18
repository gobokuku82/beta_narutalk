"""budget_channel_share — 채널별 예산 비중 (C09 도넛).

채널 필드 = CHANNEL_FIELDS (budget_allocation schema 상수, 표준 영어 — normalizer 불필요).

Status: complete — Phase 1 Batch 6 (2026-05-28).
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.schemas.inputs.budget_allocation import CHANNEL_FIELDS, load_budget_allocation
from app.schemas.outputs.cost import BudgetChannelShareOutput

logger = get_logger(__name__)


class BudgetChannelShare(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        rows = load_budget_allocation(self.fetch("budget_allocation", context)).rows

        totals = {f: sum(int(getattr(r, f, 0)) for r in rows) for f in CHANNEL_FIELDS}
        grand = sum(totals.values()) or 1
        out = [
            {"channel": f.replace("_budget", ""), "budget": v, "share": round(v / grand * 100, 2)}
            for f, v in totals.items()
        ]
        return BudgetChannelShareOutput(rows=out, total_budget=sum(totals.values())).model_dump()
