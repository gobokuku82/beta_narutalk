"""Unknown Revenue Share — methodology §S054 (알수없음 채널 매출 비중).

회귀: "2026-04" = 39.8% (unknown 47,539,330 / total 119,539,660)

Status: complete — 2026-05-23 metrics 6번째.
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
UNKNOWN_CHANNEL = "unknown"


class UnknownRevenueShare(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        period = merged.get("period")
        if not period:
            raise ValueError("Missing required param: period (YYYY-MM)")
        if "/" in period:
            raise ValueError("unknown_revenue_share 는 단일 월만")

        df = self.fetch("orders", context)
        df_active = filter_active_orders(df, period=period)

        total_revenue = sum(safe_int(v) for v in df_active["payment_amount"])
        unknown_mask = df_active["channel_attribution"].apply(
            lambda v: safe_str(v) == UNKNOWN_CHANNEL
        )
        df_unknown = df_active[unknown_mask]
        unknown_revenue = sum(safe_int(v) for v in df_unknown["payment_amount"])
        unknown_orders = len(df_unknown)
        share = round(unknown_revenue / total_revenue * 100, 1) if total_revenue else 0.0

        key = f"S054_unknown_share_{period}.json"
        logger.info("unknown_revenue_share", period=period, share=share, rev=unknown_revenue)

        return {
            "unknown_share_pct": share,
            "unknown_revenue": unknown_revenue,
            "total_revenue": total_revenue,
            "unknown_orders": unknown_orders,
            "period": period,
            "_storage": {"layer": "computed", "key": key},
            "_meta": {"formula": "SUM(payment_amount) WHERE channel='unknown' / total * 100"},
        }
