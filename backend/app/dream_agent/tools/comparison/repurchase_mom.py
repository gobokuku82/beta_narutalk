"""Repurchase MoM — methodology §S028 (MoM 변화율).

회귀 (2026-03 → 2026-04):
    total_buyers: 1,206 → 1,386 (+14.9%)
    existing_buyers: 919 → 1,095 (+19.2%)
    repurchase_rate: 76.2% → 79.0% (+2.8%p)

Tool composer 패턴: repurchase_rate_mom (S028) 을 두 번 호출.

Status: complete — 2026-05-23 comparison 1차.
"""
from __future__ import annotations
import asyncio
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.metrics.repurchase_rate_mom import RepurchaseRateMom
from app.dream_agent.tools.registry import get_registry

logger = get_logger(__name__)


def _pct_change(a: float, b: float) -> float:
    if a == 0:
        return 0.0
    return round((b - a) / a * 100, 1)


class RepurchaseMom(BaseTool):
    async def execute(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        merged = self.merge_params(params)
        a = merged.get("period_a")
        b = merged.get("period_b")
        if not a or not b:
            raise ValueError("Missing required params: period_a, period_b (YYYY-MM)")

        # 1. S028 두 번 호출 (composer)
        reg = get_registry()
        rrm_spec = reg.get("repurchase_rate_mom")
        rrm = RepurchaseRateMom(rrm_spec)
        a_res = await rrm.execute({"period": a}, context)
        b_res = await rrm.execute({"period": b}, context)

        def _stats(r):
            return {
                "total_buyers": r["total_buyers"],
                "existing_buyers": r["existing_buyers"],
                "new_buyers": r["new_buyers"],
                "repurchase_rate": r["repurchase_rate"],
            }

        a_stats = _stats(a_res)
        b_stats = _stats(b_res)
        delta = {
            "total_buyers_pct": _pct_change(a_stats["total_buyers"], b_stats["total_buyers"]),
            "existing_buyers_pct": _pct_change(a_stats["existing_buyers"], b_stats["existing_buyers"]),
            "new_buyers_pct": _pct_change(a_stats["new_buyers"], b_stats["new_buyers"]),
            "repurchase_rate_pp": round(b_stats["repurchase_rate"] - a_stats["repurchase_rate"], 1),
        }

        key = f"S028mom_repurchase_{a}_to_{b}.json"
        logger.info("repurchase_mom", a=a, b=b, delta=delta)
        return {
            "period_a_stats": a_stats, "period_b_stats": b_stats, "delta": delta,
            "period_a": a, "period_b": b,
            "_storage": {"layer": "computed", "key": key},
            "_meta": {"formula": "delta_pct = (b - a) / a * 100; delta_pp = b - a (rate diff)"},
        }
