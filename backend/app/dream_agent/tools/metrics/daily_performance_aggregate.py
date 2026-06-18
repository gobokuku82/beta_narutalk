"""daily_performance_aggregate — 일별 성과 date 별 metric 합산 (C04 라인차트).

★ A-5.3 (2026-06-18): daily_performance.csv 직독 → canonical(AD 4채널 normalized) 소비 전환.
date=report_date 별 합산. metrics는 가산 측정치(ad_cost·conversion_revenue·impressions·clicks·conversions)만
의미 — canonical엔 행단위 비율(ctr/roas 등) 컬럼 없음(computed에서 합산 후 재계산).

Status: complete — A-5.3 canonical 전환 (2026-06-18).
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.canonical_daily import load_canonical_ad_rows
from app.schemas.outputs.dashboard_v1 import DailySeriesOutput

logger = get_logger(__name__)
DEFAULT_METRICS = ["ad_cost", "conversion_revenue"]


class DailyPerformanceAggregate(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        metrics = merged.get("metrics") or DEFAULT_METRICS
        period = merged.get("period")  # YYYY-MM (선택 — 없으면 전체)

        rows = await load_canonical_ad_rows(context, period)

        agg: dict[str, dict[str, int]] = defaultdict(lambda: {m: 0 for m in metrics})
        for r in rows:
            for m in metrics:
                agg[r["date"]][m] += int(r.get(m, 0) or 0)

        out_rows = [{"date": d, **{m: agg[d][m] for m in metrics}} for d in sorted(agg)]
        logger.info("daily_performance_aggregate", metrics=metrics, period=period, days=len(out_rows))
        result = DailySeriesOutput(rows=out_rows, metrics=metrics, period=period or "").model_dump()
        if not period:  # 빈 스코프 라벨('') 데이터 방출 금지 — 오염원 5곳과 동일 규약 (슬라이스 1 보강)
            result.pop("period", None)
        return result
