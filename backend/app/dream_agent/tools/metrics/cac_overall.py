"""CAC Overall — methodology §S032 (총마케팅비 ÷ 신규회원수).

★ A3/P3 (2026-06-17): 총마케팅비 출처를 canonical_translator로 전환 (ad_cost_helper 폐기).
신규회원(customers)은 단일세계 KEEP 도메인 — 그대로 직독.
★ 가 결정 A-5.2(2026-06-17): cost google 포함 re-baseline 18,306,923 → 26,806,923 → CAC 30,512 → 44,678.

회귀 (4월): 44,678 (= 26,806,923 / 600)
"""
from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.normalization.canonical_translator import CanonicalTranslator
from app.dream_agent.tools.registry import get_registry

logger = get_logger(__name__)


class CacOverall(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        period = merged.get("period")
        if not period:
            raise ValueError("Missing required param: period (YYYY-MM)")
        if "/" in period:
            raise ValueError("cac_overall 는 단일 월만")

        # 분자: 총마케팅비 (canonical, P3 — World-B aggregate_ad_cost 대체)
        translator = CanonicalTranslator(get_registry().get("canonical_translator"))
        canon = await translator.execute({"period": period}, context)
        cost = canon["computed"]["total_marketing_cost_krw"]

        # 분모: 신규회원 (S069) — customers = 단일세계 KEEP 도메인, 직독 유지
        df_c = self.fetch("customers", context)
        new_count = int(df_c["signup_date"].astype(str).str.startswith(period).sum())

        cac = round(cost / new_count) if new_count else 0

        key = f"S032_cac_overall_{period}.json"
        logger.info("cac_overall", period=period, cac=cac, cost=cost, new=new_count)
        return {
            "cac": cac,
            "total_marketing_cost": cost,
            "new_members_count": new_count,
            "period": period,
            "_storage": {"layer": "computed", "key": key},
            "_meta": {"formula": "total_marketing_cost(canonical) / new_members_count (round)",
                      "source": "canonical_translator (P3) + customers(KEEP)"},
        }
