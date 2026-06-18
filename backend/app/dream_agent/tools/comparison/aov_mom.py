"""AOV MoM — methodology §S048 (객단가·구매자·주문 MoM 변화율).

회귀 (2026-03 → 2026-04):
    aov:    58,999 → 62,293 (+5.6%)
    orders: 1,346 → 1,919 (+42.6%)
    buyers: 1,206 → 1,386 (+14.9%)

Composer 패턴: aov_monthly 두 번 호출.

Status: complete — 2026-05-23 comparison 2번째.
"""
from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.metrics.aov_monthly import AovMonthly
from app.dream_agent.tools.registry import get_registry

logger = get_logger(__name__)


def _pct_change(a: float, b: float) -> float:
    if a == 0:
        return 0.0
    return round((b - a) / a * 100, 1)


class AovMom(BaseTool):
    async def execute(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        merged = self.merge_params(params)
        a = merged.get("period_a")
        b = merged.get("period_b")
        if not a or not b:
            raise ValueError("Missing required params: period_a, period_b")

        reg = get_registry()
        am_spec = reg.get("aov_monthly")
        am = AovMonthly(am_spec)
        a_res = await am.execute({"period": a}, context)
        b_res = await am.execute({"period": b}, context)

        def _stats(r):
            return {
                "aov": r["aov"],
                "unique_buyers": r["unique_buyers"],
                "orders_count": r["orders_count"],
            }

        a_stats = _stats(a_res)
        b_stats = _stats(b_res)
        delta = {
            "aov_pct": _pct_change(a_stats["aov"], b_stats["aov"]),
            "buyers_pct": _pct_change(a_stats["unique_buyers"], b_stats["unique_buyers"]),
            "orders_pct": _pct_change(a_stats["orders_count"], b_stats["orders_count"]),
        }

        key = f"S048mom_aov_{a}_to_{b}.json"
        logger.info("aov_mom", a=a, b=b, delta=delta)
        return {
            "period_a_stats": a_stats, "period_b_stats": b_stats, "delta": delta,
            "period_a": a, "period_b": b,
            "_storage": {"layer": "computed", "key": key},
            "_meta": {"formula": "delta_pct = (b - a) / a * 100"},
        }
