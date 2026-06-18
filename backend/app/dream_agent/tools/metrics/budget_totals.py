"""budget_totals — 총 예산 + 평균 집행률 (K22·K23 공유, 2 필드 동시).

Status: complete — Phase 1 Batch 6 (2026-05-28).
"""
from __future__ import annotations

from statistics import mean
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.schemas.inputs.budget_allocation import load_budget_allocation
from app.schemas.outputs.cost import BudgetTotalsOutput

logger = get_logger(__name__)


class BudgetTotals(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        rows = load_budget_allocation(self.fetch("budget_allocation", context)).rows
        return BudgetTotalsOutput(
            total_budget=sum(int(r.total_budget) for r in rows),
            avg_exec_rate=round(float(mean([r.exec_rate for r in rows])), 2) if rows else 0.0,
        ).model_dump()
