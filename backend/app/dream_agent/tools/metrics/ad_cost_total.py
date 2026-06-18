"""Ad Cost Total — 마케팅비(ad+msg) 합산.

★ A3/P3 (2026-06-17): **canonical_translator 소비로 전환** — World-B `ad_cost_helper.aggregate_ad_cost`
(raw 직독·산발) 폐기. 이제 단일 contract translator(raw→normalized→computed)의 computed를 읽음.
값 = canonical computed. ★ 가 결정 A-5.2(2026-06-17): google 광고 매체 포함 re-baseline
**18,306,923 → 26,806,923**(canonical 내부 ad 26,735,453 / msg 71,470 분리 — C6.3). 대시보드·에이전트가
같은 tool을 쓰므로 둘 다 자동 정합(단일 세계).

산출 = total_cost(총 마케팅비) + by_channel(6매체: meta·naver_sa·advoost·google·kakao·talktalk).
회귀(4월): meta 9,235,826·naver_sa 5,999,627·advoost 3,000,000·google 8,500,000·kakao 59,020·talktalk 12,450 = 26,806,923.
다음 P3 전환: roas_overall·cac_overall·promotion_roas·channel_cac_compare.

Status: complete — A3 P3 canonical 전환 (2026-06-17). ad_cost_helper 의존 제거.
"""
from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.normalization.canonical_translator import CanonicalTranslator
from app.dream_agent.tools.registry import get_registry

logger = get_logger(__name__)


class AdCostTotal(BaseTool):
    async def execute(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        merged = self.merge_params(params)
        period = merged.get("period")  # optional

        # P3: canonical_translator 소비 (raw→normalized→computed). World-B aggregate_ad_cost 대체.
        translator = CanonicalTranslator(get_registry().get("canonical_translator"))
        canon = await translator.execute({"period": period} if period else {}, context)
        computed = canon["computed"]
        total = computed["total_marketing_cost_krw"]                       # ad + msg = 총 마케팅비
        by_channel = {**computed["ad_cost_by_channel"], **computed["msg_cost_by_channel"]}

        period_safe = (period or "all").replace("/", "_")
        key = f"ad_cost_total_{period_safe}.json"
        logger.info("ad_cost_total", period=period, total=total, by_channel=by_channel)

        result = {
            "total_cost": total,
            "by_channel": by_channel,
            "_storage": {"layer": "normalized", "key": key},
            "_meta": {"formula": "canonical total_marketing_cost = Σad_cost(meta·naver_sa·advoost) + Σmsg_cost(kakao·talktalk)",
                      "source": "canonical_translator (P3 전환)"},
        }
        # period 미지정 시 'all' 라벨 데이터 방출 금지 (silent-0 오염원) — 실제 값만.
        if period:
            result["period"] = period
        return result
