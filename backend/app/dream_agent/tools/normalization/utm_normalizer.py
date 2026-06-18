"""UTM Normalizer — methodology §정제 9.

규칙:
    "" / NULL          → "" (drop)
    "(not set)"        → "unknown"
    "(direct)"         → "direct"
    "(none)"           → "" (drop)

Status: complete — 2026-05-25.
"""
from __future__ import annotations
from collections import Counter
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.missing_helper import safe_str
from app.dream_agent.tools.shared.order_helper import filter_active_orders

logger = get_logger(__name__)


def normalize_utm(v: Any) -> str:
    """methodology §정제 9 표 — 정규화."""
    s = safe_str(v)
    if s == "(not set)":
        return "unknown"
    if s == "(direct)":
        return "direct"
    if s == "(none)":
        return ""
    return s


class UtmNormalizer(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        period = merged.get("period")

        df = self.fetch("orders", context)
        df_active = filter_active_orders(df, period=period)

        src_dist: Counter = Counter()
        med_dist: Counter = Counter()
        normalized = 0
        for _, row in df_active.iterrows():
            raw_src = safe_str(row.get("utm_source"))
            raw_med = safe_str(row.get("utm_medium"))
            src = normalize_utm(raw_src)
            med = normalize_utm(raw_med)
            if src != raw_src or med != raw_med:
                normalized += 1
            src_dist[src or "(empty)"] += 1
            med_dist[med or "(empty)"] += 1

        period_safe = (period or "all").replace("/", "_")
        key = f"utm_normalized_{period_safe}.json"
        logger.info("utm_normalizer", period=period, normalized=normalized,
                    sources=len(src_dist), mediums=len(med_dist))
        result = {
            "source_dist": dict(src_dist.most_common()),
            "medium_dist": dict(med_dist.most_common()),
            "normalized_count": normalized,
            "_storage": {"layer": "normalized", "key": key},
            "_meta": {"formula": "(not set)→unknown, (direct)→direct, (none)/empty→drop"},
        }
        if period:  # 'all' 라벨 데이터 방출 금지 (슬라이스 1, 헌법 D3·R2 — silent-0 오염원)
            result["period"] = period
        return result
