"""New Members MoM — S069 MoM (가입 회원 기준).

회귀 (2026-03 → 2026-04):
    3월 신규 = 601
    4월 신규 = 600
    변화율 = -0.2%

⚠ recovery 핵심 질문 "+1.4%" 와 다름:
    +1.4% = 신규 *주문 고객* MoM (RepurchaseMom.delta.new_buyers_pct, 287→291)
    -0.2% = 신규 *가입 회원* MoM (본 tool, customers.signup_date 601→600)
    두 지표는 비즈니스 의미 다름.

Status: complete — 2026-05-23 comparison 3번째.
"""
from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.metrics.new_members_monthly import NewMembersMonthly
from app.dream_agent.tools.registry import get_registry

logger = get_logger(__name__)


def _pct_change(a: float, b: float) -> float:
    if a == 0:
        return 0.0
    return round((b - a) / a * 100, 1)


class NewMembersMom(BaseTool):
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
        nmm_spec = reg.get("new_members_monthly")
        nmm = NewMembersMonthly(nmm_spec)
        a_res = await nmm.execute({"period": a}, context)
        b_res = await nmm.execute({"period": b}, context)

        a_total = a_res["new_members_total"]
        b_total = b_res["new_members_total"]
        delta_pct = _pct_change(a_total, b_total)

        key = f"S069mom_new_members_{a}_to_{b}.json"
        logger.info("new_members_mom", a=a, b=b, delta_pct=delta_pct,
                    a_total=a_total, b_total=b_total)
        return {
            "period_a_total": a_total,
            "period_b_total": b_total,
            "delta_pct": delta_pct,
            "by_channel_a": a_res["new_members_by_channel"],
            "by_channel_b": b_res["new_members_by_channel"],
            "period_a": a, "period_b": b,
            "_storage": {"layer": "computed", "key": key},
            "_meta": {"formula": "(b - a) / a * 100"},
        }
