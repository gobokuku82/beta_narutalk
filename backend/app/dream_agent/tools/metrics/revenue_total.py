"""Revenue Total — methodology §S001 (SUM activeorders.payment_amount WHERE 기간).

회귀 (methodology 정답):
    "2026-04":              119,539,660
    "2026-03/2026-04":      198,951,769 (자체 산출)

shared/order_helper.filter_active_orders 사용 — cleaning/active_orders_filter 와 동일 로직.
storage.layer = "computed" → data/{client}/computed/S001_revenue_total_*.json

Status: complete — 2026-05-23 metrics 1차 (S001).
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.missing_helper import safe_int
from app.dream_agent.tools.shared.order_helper import filter_active_orders

logger = get_logger(__name__)



class RevenueTotal(BaseTool):
    """S001 총 매출 — 활성주문 payment_amount 합."""

    async def execute(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        merged = self.merge_params(params)
        period = merged.get("period")
        if not period:
            raise ValueError("Missing required param: period (YYYY-MM or YYYY-MM/YYYY-MM)")


        # 1. raw 로드 (DataSource 관절) + 활성 + 기간 (shared helper)
        df_raw = self.fetch("orders", context)
        df_active = filter_active_orders(df_raw, period=period)

        # 2. 합산 (safe_int 로 NaN 안전)
        revenue = sum(safe_int(v, default=0) for v in df_active["payment_amount"])
        count = len(df_active)

        # 3. 저장은 진입점(②-b). tool 은 산출만 반환.
        period_safe = period.replace("/", "_")
        key = f"S001_revenue_total_{period_safe}.json"

        logger.info("revenue_total computed", period=period, revenue=revenue, count=count)

        return {
            "revenue_total": revenue,
            "active_orders_count": count,
            "period": period,
            "_storage": {"layer": "computed", "key": key},
            "_meta": {"formula": "SUM payment_amount WHERE 활성 AND 기간"},
        }
