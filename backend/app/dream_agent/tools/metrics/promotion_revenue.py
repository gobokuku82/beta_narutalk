"""Promotion Revenue — methodology §S002 (활성 + promotion_code IS NOT NULL).

회귀 (4월): 43,400,360 (36.3% / 전체 119,539,660 중)
"""
from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.missing_helper import safe_int, safe_str
from app.dream_agent.tools.shared.order_helper import filter_active_orders

logger = get_logger(__name__)


class PromotionRevenue(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        period = merged.get("period")
        if not period:
            raise ValueError("Missing required param: period (YYYY-MM)")
        if "/" in period:
            raise ValueError("promotion_revenue 는 단일 월만")

        df = self.fetch("orders", context)
        df_active = filter_active_orders(df, period=period)
        total = sum(safe_int(v) for v in df_active["payment_amount"])

        # promotion_code 빈/NaN 제외
        df_promo = df_active[df_active["promotion_code"].apply(lambda v: bool(safe_str(v)))]
        promo_rev = sum(safe_int(v) for v in df_promo["payment_amount"])
        promo_count = len(df_promo)
        share = round(promo_rev / total * 100, 1) if total else 0.0

        key = f"S002_promotion_revenue_{period}.json"
        logger.info("promotion_revenue", period=period, rev=promo_rev, share=share)
        return {
            "promotion_revenue": promo_rev,
            "promotion_share_pct": share,
            "promotion_orders_count": promo_count,
            "total_revenue": total,
            "period": period,
            "_storage": {"layer": "computed", "key": key},
            "_meta": {"formula": "SUM(payment_amount) WHERE active AND promotion_code IS NOT NULL"},
        }
