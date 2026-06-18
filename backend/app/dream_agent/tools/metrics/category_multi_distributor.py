"""Category Multi Distributor — methodology §정제 7 (옵션 A: 균등 분배).

orders.product_categories 콤마 분리 → 매출 균등 분배.

회귀 (4월):
    스킨케어:   count=1400, revenue=67,652,216
    클렌징:     count=497,  revenue=19,126,163
    마스크팩:   count=464,  revenue=19,366,323
    자외선차단: count=161,  revenue=6,864,031
    기타:       count=166,  revenue=6,530,924

Status: complete — 2026-05-25.
"""
from __future__ import annotations
from collections import defaultdict
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.missing_helper import safe_int, safe_str
from app.dream_agent.tools.shared.order_helper import filter_active_orders

logger = get_logger(__name__)


class CategoryMultiDistributor(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        period = merged.get("period")
        method = merged.get("method", "equal")
        if method != "equal":
            raise ValueError(f"method='{method}' 미지원 (POC: equal 만). category_sales 는 후속")

        df = self.fetch("orders", context)
        df_active = filter_active_orders(df, period=period)

        by_count: dict[str, int] = defaultdict(int)
        by_rev: dict[str, float] = defaultdict(float)
        total_rev = 0
        for _, row in df_active.iterrows():
            cats_raw = safe_str(row.get("product_categories", ""))
            if not cats_raw:
                continue
            parts = [c.strip() for c in cats_raw.split(",") if c.strip()]
            if not parts:
                continue
            amt = safe_int(row.get("payment_amount", 0))
            share = amt / len(parts)
            for c in parts:
                by_count[c] += 1
                by_rev[c] += share
            total_rev += amt

        # by_category — count 내림차순
        sorted_cats = sorted(by_count.keys(), key=lambda k: -by_count[k])
        # int() = truncate (methodology 정답표가 truncate 기준 — round 시 ±1 오차)
        by_category = {
            c: {"count": by_count[c], "revenue": int(by_rev[c])}
            for c in sorted_cats
        }
        distributed_revenue = sum(v["revenue"] for v in by_category.values())

        period_safe = (period or "all").replace("/", "_")
        key = f"category_distributed_{period_safe}.json"
        logger.info("category_multi_distributor",
                    period=period, total_cats=len(by_category), dist_rev=distributed_revenue)
        result = {
            "by_category": by_category,
            "total_categories": len(by_category),
            "total_distributed_revenue": distributed_revenue,
            "_storage": {"layer": "normalized", "key": key},
            "_meta": {"formula": "EACH order: split payment_amount equally across product_categories.split(',')"},
        }
        if period:  # 'all' 라벨 데이터 방출 금지 (슬라이스 1, 헌법 D3·R2 — silent-0 오염원)
            result["period"] = period
        return result
