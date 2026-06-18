"""AOV Monthly — methodology §S048 (객단가·구매자·주문수, 월 단위).

회귀 (4월 정답):
    aov = 62,293
    unique_buyers = 1,386
    orders_count = 1,919

Status: complete — 2026-05-23 metrics 2번째.
"""
from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.missing_helper import safe_int, safe_str
from app.dream_agent.tools.shared.order_helper import filter_active_orders

logger = get_logger(__name__)

ORDERS_FILE_NO = 5


class AovMonthly(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        period = merged.get("period")
        if not period:
            raise ValueError("Missing required param: period (YYYY-MM)")

        df = self.fetch("orders", context)
        df_active = filter_active_orders(df, period=period)

        total_payment = sum(safe_int(v) for v in df_active["payment_amount"])
        orders_count = len(df_active)
        # methodology §S048: round (truncate 가 아닌 반올림 — 정답값 62,293 일치)
        aov = round(total_payment / orders_count) if orders_count else 0

        # unique buyers (회원만 — 비회원 NaN/빈 제외)
        member_ids = {safe_str(v) for v in df_active["member_id"]}
        member_ids.discard("")
        unique_buyers = len(member_ids)

        key = f"S048_aov_{period}.json"
        logger.info("aov_monthly", period=period, aov=aov, buyers=unique_buyers, orders=orders_count)

        return {
            "aov": aov, "unique_buyers": unique_buyers, "orders_count": orders_count,
            "period": period,
            "_storage": {"layer": "computed", "key": key},
            "_meta": {"formula": "aov = SUM(payment_amount) / COUNT(order_id) WHERE active AND period"},
        }
