"""conversion_funnel — canonical AD 전체 노출→클릭→전환 퍼널 (C06).

각 단계 value + 직전 단계 대비 비율(pct_of_prev) + 최상단 대비(pct_of_top).

★ A-5.3 (2026-06-18): daily_performance.csv 직독 → canonical(AD 4채널 normalized) 소비.
AD 채널만(kakao=메시징 제외). period 선택 지원. 합산 모수가 옛 csv와 다름 = 진짜 raw 정합.

Status: complete — A-5.3 canonical 전환 (2026-06-18).
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.canonical_daily import load_canonical_ad_rows
from app.schemas.outputs.channel import ConversionFunnelOutput

logger = get_logger(__name__)
_STAGES = [("impressions", "노출"), ("clicks", "클릭"), ("conversions", "전환")]


class ConversionFunnel(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        period = merged.get("period")  # 선택 — 없으면 전체
        rows = await load_canonical_ad_rows(context, period)

        totals = {field: sum(int(r.get(field, 0) or 0) for r in rows)
                  for field, _ in _STAGES}
        top = totals[_STAGES[0][0]] or 1

        out_rows: list[dict[str, Any]] = []
        prev: int | None = None
        for field, label in _STAGES:
            value = totals[field]
            out_rows.append({
                "stage": label,
                "field": field,
                "value": value,
                "pct_of_top": round(value / top * 100, 2),
                "pct_of_prev": round(value / prev * 100, 2) if prev else 100.0,
            })
            prev = value

        logger.info("conversion_funnel", stages=len(out_rows), top=top)
        return ConversionFunnelOutput(rows=out_rows).model_dump()
