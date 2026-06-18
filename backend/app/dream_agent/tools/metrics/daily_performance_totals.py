"""daily_performance_totals — 기간 총 노출·클릭·전환·광고비 (K14~K17 공유).

4 KPI 가 같은 cache_key 공유 → 1회 산출 4 카드.

★ A-5.3 (2026-06-18): daily_performance.csv 직독 → canonical(AD 4채널 normalized) 소비 전환.
값 = canonical 합(google 포함·kakao=메시징 제외). 옛 csv(World-C)와 다름 = 진짜 raw 정합.

Status: complete — A-5.3 canonical 전환 (2026-06-18).
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.canonical_daily import load_canonical_ad_rows
from app.schemas.outputs.trend import DailyPerformanceTotalsOutput

logger = get_logger(__name__)


class DailyPerformanceTotals(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        period = merged.get("period")

        rows = await load_canonical_ad_rows(context, period)

        result = DailyPerformanceTotalsOutput(
            total_impressions=sum(r["impressions"] for r in rows),
            total_clicks=sum(r["clicks"] for r in rows),
            total_conversions=sum(r["conversions"] for r in rows),
            total_ad_cost=sum(r["ad_cost"] for r in rows),
            period=period or "",
        ).model_dump()
        if not period:  # 빈 스코프 라벨('') 데이터 방출 금지 — 오염원 5곳과 동일 규약 (슬라이스 1 보강)
            result.pop("period", None)
        return result
