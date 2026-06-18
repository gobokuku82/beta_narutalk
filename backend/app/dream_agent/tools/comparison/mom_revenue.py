"""Revenue MoM — recovery 핵심 +50.5% 답.

회귀 (2026-03 → 2026-04): 79,412,109 → 119,539,660 = +50.5%

Status: complete — 2026-05-25.
"""
from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.metrics.revenue_total import RevenueTotal
from app.dream_agent.tools.registry import get_registry

logger = get_logger(__name__)


def _pct(a, b):
    return round((b - a) / a * 100, 1) if a else 0.0


class MomRevenue(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        a = merged.get("period_a"); b = merged.get("period_b")
        if not a or not b:
            raise ValueError("Missing required params: period_a, period_b")

        reg = get_registry()
        rt = RevenueTotal(reg.get("revenue_total"))
        a_res = await rt.execute({"period": a}, context)
        b_res = await rt.execute({"period": b}, context)

        a_rev = a_res["revenue_total"]; b_rev = b_res["revenue_total"]
        delta = _pct(a_rev, b_rev)

        key = f"S001mom_revenue_{a}_to_{b}.json"
        logger.info("mom_revenue", a=a, b=b, delta=delta)
        return {
            "period_a_revenue": a_rev,
            "period_b_revenue": b_rev,
            "delta_pct": delta,
            "period_a": a, "period_b": b,
            "_storage": {"layer": "computed", "key": key},
            "_meta": {"formula": "(b - a) / a * 100"},
        }
