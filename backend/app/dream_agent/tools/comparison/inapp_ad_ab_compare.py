"""Inapp Ad A/B Compare — methodology §S017~S021.

⚠ POC partial: mock 에 명확한 A/B 없음. methodology 명시 "캠페인 선정 룰 정의 필요".
   분석가 가정 = campaign_name substring 으로 2개 그룹 선정.

데이터 한계 (methodology §S019·§S020 명시):
    S019 프로필 방문 미수록
    S020 메시지 시작 미수록

POC 산출: S017 (메타 정보) + S018 (광고 성과) 만 — sub-string 매칭으로 2 그룹.

Status: partial — methodology 추가 정의 후 보강 가능.
"""
from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.missing_helper import safe_int, safe_str

logger = get_logger(__name__)

META_FILE_NO = 1


class InappAdAbCompare(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        a_sub = merged.get("campaign_a_substr", "NewSet")
        b_sub = merged.get("campaign_b_substr", "Serum")
        period = "2026-04"  # mock 단일

        data = self.fetch("meta_ads_performance", context)
        records = data.get("data", data) if isinstance(data, dict) else data

        def _filter_agg(substr: str) -> dict:
            rows = [r for r in records if substr.lower() in safe_str(r.get("campaign_name")).lower()]
            spend = sum(safe_int(r.get("spend", 0)) for r in rows)
            impressions = sum(safe_int(r.get("impressions", 0)) for r in rows)
            clicks = sum(safe_int(r.get("clicks", 0)) for r in rows)
            ctr = round(clicks / impressions * 100, 4) if impressions else 0.0
            return {
                "rows_matched": len(rows),
                "spend": spend,
                "impressions": impressions,
                "clicks": clicks,
                "ctr_pct": ctr,
            }

        a_meta = _filter_agg(a_sub)
        b_meta = _filter_agg(b_sub)

        key = f"S017_inapp_ab_compare_{period}.json"
        logger.info("inapp_ab_compare",
                    a_rows=a_meta["rows_matched"], b_rows=b_meta["rows_matched"],
                    status="partial")
        return {
            "a_meta": a_meta, "b_meta": b_meta,
            "status": "partial",
            "data_gaps": ["S019", "S020"],
            "period": period,
            "_storage": {"layer": "computed", "key": key},
            "_meta": {"formula": "filter campaign_name CONTAINS substring → SUM(spend·impressions·clicks)"},
        }
