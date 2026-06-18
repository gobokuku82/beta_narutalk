"""canonical_daily — AD canonical normalized 행을 일별/채널 집계용 dict 목록으로 평탄화.

A-5.3 (2026-06-18): daily/channel/funnel tool이 옛 daily_performance.csv(World-C, 별개 가짜 요약)
대신 canonical을 소비. AD_CHANNELS(meta·naver_sa·advoost·google)만 — kakao/talktalk은
메시징(C6.3 분리, msg_* measure)이라 광고 집계에서 제외.

데이터 접근: canonical_translator.execute()(=self.fetch 경유 raw→normalized, 순수)만. raw 직독 금지.
출력 필드명은 daily_performance 호환(date/channel/impressions/clicks/conversions/ad_cost/conversion_revenue)
유지 — 소비 tool의 집계 로직·출력 스키마 안정. canonical 컬럼명은 _FIELD_MAP으로 매핑.

Status: complete — A-5.3 daily_performance→canonical 전환 (2026-06-18).
"""
from __future__ import annotations

from typing import Any

from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.normalization.canonical_translator import (
    AD_CHANNELS,
    CanonicalTranslator,
)
from app.dream_agent.tools.registry import get_registry

# 출력(공개) 필드명 → canonical normalized 컬럼명. (가산 측정치만 — 파생율은 소비 tool이 합산 후 재계산)
_FIELD_MAP = {
    "impressions": "impressions",
    "clicks": "clicks",
    "conversions": "conversion_count",
    "ad_cost": "ad_cost_krw",
    "conversion_revenue": "conversion_revenue_krw",
}


async def load_canonical_ad_rows(
    context: ExecutionContext, period: str | None = None
) -> list[dict[str, Any]]:
    """canonical AD 4채널 normalized 행 → 일별/채널 집계용 평탄 dict 목록.

    period(YYYY-MM) 주면 translator가 해당 월로 필터(report_date 기준). 없으면 전체.
    각 dict = {date, channel, impressions, clicks, conversions, ad_cost, conversion_revenue}.
    """
    translator = CanonicalTranslator(get_registry().get("canonical_translator"))
    canon = await translator.execute({"period": period} if period else {}, context)
    normalized = canon["normalized"]
    out: list[dict[str, Any]] = []
    for ch in AD_CHANNELS:
        for r in normalized[ch]["rows"]:
            row: dict[str, Any] = {"date": r.get("report_date"), "channel": ch}
            for pub, canon_col in _FIELD_MAP.items():
                row[pub] = int(r.get(canon_col, 0) or 0)
            out.append(row)
    return out
