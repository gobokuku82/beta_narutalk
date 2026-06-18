"""Channel CAC Compare — methodology §S033.

채널별 마케팅비 ÷ 채널별 신규회원 수.

★ A3/P3 (2026-06-17): 채널별 마케팅비 출처를 canonical_translator로 전환 (ad_cost_helper 폐기 — 마지막 소비처).
신규회원(customers)은 단일세계 KEEP — 직독 유지.
★ 가 결정 A-5.2(2026-06-17): google 포함 re-baseline → weighted_avg 30,512 → 44,678. kakao_cac 2,270 불변(kakao 비용 동일).

회귀 (4월):
    weighted_avg_cac = 44,678 (= S032, 26,806,923 / 600)
    kakao_cac = 2,270 (= 59,020 / 26) — 명확
    advoost·talktalk·meta·naver_sub-channels = 분리 어려움 (methodology 명시)

Status: complete — A3 P3 canonical 전환 (2026-06-17).
"""
from __future__ import annotations
from collections import Counter
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.normalization.canonical_translator import CanonicalTranslator
from app.dream_agent.tools.registry import get_registry
from app.dream_agent.tools.shared.missing_helper import safe_str

logger = get_logger(__name__)

# methodology §S033 — 명확 매칭 (utm_source ↔ 광고 cost)
DIRECT_MATCH = {
    "kakao": "kakao",        # signup_utm_source = "kakao" → kakao cost
}
# 분리 어려움: advoost (매체 측정), talktalk (자사몰 X), meta·naver_sub
UNMATCHED = ["advoost", "talktalk", "meta_subchannels", "naver_subchannels"]


class ChannelCacCompare(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        period = merged.get("period")
        if not period:
            raise ValueError("Missing required param: period")
        if "/" in period:
            # startswith(period) 식 단일 월 필터 — 범위가 들어오면 0건/부분합산 silent-0 (리뷰 R-2)
            raise ValueError("channel_cac_compare 는 단일 월만 (YYYY-MM)")

        # 1. 채널별 마케팅비 (canonical, P3 — World-B aggregate_ad_cost 대체)
        translator = CanonicalTranslator(get_registry().get("canonical_translator"))
        canon = await translator.execute({"period": period}, context)
        computed = canon["computed"]
        total_cost = computed["total_marketing_cost_krw"]
        ad = {**computed["ad_cost_by_channel"], **computed["msg_cost_by_channel"]}  # 5매체 (total 제외)

        # 2. 채널별 신규 회원 (customers = 단일세계 KEEP, 직독 유지)
        df_c = self.fetch("customers", context)
        df_apr = df_c[df_c["signup_date"].astype(str).str.startswith(period)]
        new_total = len(df_apr)
        new_by_source = Counter(safe_str(v) or "(unknown)" for v in df_apr["signup_utm_source"])

        # 3. 명확 매칭 채널 — CAC 산출
        by_channel: dict[str, dict] = {}
        for cost_key, signup_key in DIRECT_MATCH.items():
            cost = ad.get(cost_key, 0)
            members = new_by_source.get(signup_key, 0)
            cac = round(cost / members) if members else None
            by_channel[cost_key] = {
                "cost": cost,
                "new_members": members,
                "cac": cac,
            }

        # 4. 가중평균 CAC (전체)
        weighted_avg = round(total_cost / new_total) if new_total else 0

        key = f"S033_channel_cac_{period}.json"
        logger.info("channel_cac_compare",
                    period=period, weighted_avg=weighted_avg,
                    kakao_cac=by_channel.get("kakao", {}).get("cac"))
        return {
            "by_channel": by_channel,
            "weighted_avg_cac": weighted_avg,
            "new_members_total": new_total,
            "new_members_by_source": dict(new_by_source.most_common()),
            "unmatched_channels": UNMATCHED,
            "period": period,
            "_storage": {"layer": "computed", "key": key},
            "_meta": {"formula": "channel: cost(canonical) / new_members(customers KEEP); weighted_avg = total_cost / new_total",
                      "source": "canonical_translator (P3) + customers(KEEP)"},
        }
