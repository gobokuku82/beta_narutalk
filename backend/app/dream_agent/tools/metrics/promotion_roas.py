"""Promotion ROAS — methodology §S005 (프로모션매출 ÷ 총마케팅비).

★ A3/P3 (2026-06-17): 총마케팅비 출처를 canonical_translator로 전환 (ad_cost_helper 폐기).
프로모션 매출(orders.promotion_code)은 단일세계 KEEP 도메인 — 그대로 직독.
★ 가 결정 A-5.2(2026-06-17): cost google 포함 re-baseline 18,306,923 → 26,806,923 → promotion_roas 2.37 → 1.62.

회귀 (4월): 1.62 (= 43,400,360 / 26,806,923)
"""
from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.normalization.canonical_translator import CanonicalTranslator
from app.dream_agent.tools.registry import get_registry
from app.dream_agent.tools.shared.missing_helper import safe_int, safe_str
from app.dream_agent.tools.shared.order_helper import filter_active_orders

logger = get_logger(__name__)


class PromotionRoas(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        period = merged.get("period")
        if not period:
            raise ValueError("Missing required param: period (YYYY-MM)")
        if "/" in period:
            raise ValueError("promotion_roas 는 단일 월만")

        # 프로모션 매출 (S002) — orders.promotion_code = 단일세계 KEEP 도메인, 직독 유지
        df = self.fetch("orders", context)
        df_active = filter_active_orders(df, period=period)
        df_promo = df_active[df_active["promotion_code"].apply(lambda v: bool(safe_str(v)))]
        promo_rev = sum(safe_int(v) for v in df_promo["payment_amount"])

        # 총마케팅비 (canonical, P3 — World-B aggregate_ad_cost 대체)
        translator = CanonicalTranslator(get_registry().get("canonical_translator"))
        canon = await translator.execute({"period": period}, context)
        cost = canon["computed"]["total_marketing_cost_krw"]

        roas = round(promo_rev / cost, 2) if cost else 0.0

        key = f"S005_promotion_roas_{period}.json"
        logger.info("promotion_roas", period=period, roas=roas, promo_rev=promo_rev, cost=cost)
        return {
            "promotion_roas": roas,
            "promotion_revenue": promo_rev,
            "total_marketing_cost": cost,
            "period": period,
            "_storage": {"layer": "computed", "key": key},
            "_meta": {"formula": "promotion_revenue(orders KEEP) / total_marketing_cost(canonical) (round 2)",
                      "source": "canonical_translator (P3) + orders(KEEP)"},
        }
