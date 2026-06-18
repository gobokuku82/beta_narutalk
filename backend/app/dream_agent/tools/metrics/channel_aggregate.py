"""channel_aggregate — canonical AD 채널별 집계 (C05 bar + T05 table 공용).

합산(impressions·clicks·conversions·ad_cost·conversion_revenue) + 파생율(ctr·cvr·cpc·cpa·roas).
C05/T05 가 같은 cache_key 공유 → 1회 산출 2 시각화.

★ A-5.3 (2026-06-18): daily_performance.csv 직독 → canonical(AD 4채널: meta·naver_sa·advoost·google) 소비.
채널셋이 옛 csv(google/kakao/meta/naver)와 다름 — kakao는 메시징(C6.3 분리)이라 제외, naver는 검색(naver_sa)·
디스플레이(advoost)로 분리. ★roas = 배수(canonical roas_x 일치, 옛 %×100 아님). period 선택 지원.

Status: complete — A-5.3 canonical 전환 (2026-06-18).
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.canonical_daily import load_canonical_ad_rows
from app.schemas.outputs.channel import ChannelMetricsOutput

logger = get_logger(__name__)
_SUM_FIELDS = ["impressions", "clicks", "conversions", "ad_cost", "conversion_revenue"]


def _rate(numer: float, denom: float, *, pct: bool = False, zero: float | None = 0.0) -> float | None:
    """0분모 시 zero 반환. ★cost 지표(cpa·cpc, 낮을수록 좋음)는 zero=None — '전환/클릭 0(undefined)'을
    0(=최저비용=최고)으로 위장하면 순위·target_cpa 비교서 오독(canonical_translator의 'X if denom else None'
    규약과 정합). ctr/cvr/roas(높을수록 좋음)는 분모0이 '데이터 없음=0'이라 0.0 유지(2026-06-18 검증 wb7456v44)."""
    if not denom:
        return zero
    r = numer / denom
    return round(r * 100, 2) if pct else round(r, 2)


class ChannelAggregate(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        period = merged.get("period")  # 선택 — 없으면 전체
        rows = await load_canonical_ad_rows(context, period)

        agg: dict[str, dict[str, int]] = defaultdict(lambda: {f: 0 for f in _SUM_FIELDS})
        for r in rows:
            for f in _SUM_FIELDS:
                agg[r["channel"]][f] += int(r.get(f, 0) or 0)

        out_rows: list[dict[str, Any]] = []
        for channel in sorted(agg):
            s = agg[channel]
            out_rows.append({
                "channel": channel,
                **s,
                "ctr": _rate(s["clicks"], s["impressions"], pct=True),
                "cvr": _rate(s["conversions"], s["clicks"], pct=True),
                "cpc": _rate(s["ad_cost"], s["clicks"], zero=None),       # 클릭0=비용/클릭 정의불가 → None(0=최고 위장 방지)
                "cpa": _rate(s["ad_cost"], s["conversions"], zero=None),  # 전환0=비용/전환 정의불가 → None
                "roas": _rate(s["conversion_revenue"], s["ad_cost"]),  # 배수 (canonical roas_x 규약)
            })

        logger.info("channel_aggregate", channels=len(out_rows))
        return ChannelMetricsOutput(rows=out_rows, count=len(out_rows)).model_dump()
