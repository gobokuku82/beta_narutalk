"""Channel Attribution Normalizer — methodology §정제 4.

orders.channel_attribution 10채널을 그룹으로 매핑.

회귀 (4월): 481 unknown / 283 naver_search / 273 direct / 253 meta_instagram / ...

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


# methodology §정제 4 표 (10채널 → 그룹)
CHANNEL_GROUP_MAP: dict[str, str] = {
    "meta_facebook": "Meta",
    "meta_instagram": "Meta",
    "naver_search": "Naver",
    "naver_shopping": "Naver",
    "naver_brand": "Naver",
    "naver_advoost": "Naver",        # 매체 (orders 에 거의 없음)
    "naver_talktalk": "CRM",
    "kakao_message": "CRM",
    "direct": "Direct",
    "google_organic": "Organic",
    "oliveyoung_referral": "Referral",
    "unknown": "Unknown",
}


class ChannelAttributionNormalizer(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        period = merged.get("period")

        df = self.fetch("orders", context)
        df_active = filter_active_orders(df, period=period)

        by_raw: Counter = Counter()
        by_group: Counter = Counter()
        for v in df_active["channel_attribution"]:
            raw = safe_str(v) or "(empty)"
            by_raw[raw] += 1
            grp = CHANNEL_GROUP_MAP.get(raw, "Other")
            by_group[grp] += 1

        # mapping: 발견된 raw 값만
        mapping = {raw: CHANNEL_GROUP_MAP.get(raw, "Other") for raw in by_raw.keys()}

        period_safe = (period or "all").replace("/", "_")
        key = f"channel_normalized_{period_safe}.json"
        logger.info("channel_normalizer", period=period,
                    raw_channels=len(by_raw), groups=len(by_group))
        result = {
            "by_raw_channel": dict(by_raw.most_common()),
            "by_group": dict(by_group.most_common()),
            "mapping": mapping,
            "_storage": {"layer": "normalized", "key": key},
            "_meta": {"formula": "GROUP BY channel_attribution → CHANNEL_GROUP_MAP"},
        }
        if period:  # 'all' 라벨 데이터 방출 금지 (슬라이스 1, 헌법 D3·R2 — silent-0 오염원)
            result["period"] = period
        return result
