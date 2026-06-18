"""ROAS Overall — methodology §S004 (총매출 ÷ 총마케팅비) = MER.

★ A3/P3 (2026-06-17): canonical_translator 소비로 전환 (ad_cost_helper + orders 직독 폐기).
roas = computed.mer (= total_order_revenue_krw / total_marketing_cost_krw).
★ 가 결정 A-5.2(2026-06-17): google 포함 re-baseline 6.53 → 4.46.

회귀 (4월): 4.46 (= 119,539,660 / 26,806,923)
"""
from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.normalization.canonical_translator import CanonicalTranslator
from app.dream_agent.tools.registry import get_registry

logger = get_logger(__name__)


class RoasOverall(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        period = merged.get("period")
        if not period:
            raise ValueError("Missing required param: period (YYYY-MM)")
        if "/" in period:
            raise ValueError("roas_overall 는 단일 월만")

        # P3: canonical_translator 소비 (총매출·총마케팅비·mer 모두 computed에). World-B 직독 대체.
        translator = CanonicalTranslator(get_registry().get("canonical_translator"))
        canon = await translator.execute({"period": period}, context)
        computed = canon["computed"]
        revenue = computed["total_order_revenue_krw"]
        cost = computed["total_marketing_cost_krw"]
        roas = computed["mer"] if computed.get("mer") is not None else (round(revenue / cost, 2) if cost else 0.0)

        key = f"S004_roas_overall_{period}.json"
        logger.info("roas_overall", period=period, roas=roas, rev=revenue, cost=cost)
        return {
            "roas": roas,
            "total_revenue": revenue,
            "total_marketing_cost": cost,
            "period": period,
            "_storage": {"layer": "computed", "key": key},
            "_meta": {"formula": "canonical mer = total_order_revenue / total_marketing_cost (round 2)",
                      "source": "canonical_translator (P3 전환)"},
        }
