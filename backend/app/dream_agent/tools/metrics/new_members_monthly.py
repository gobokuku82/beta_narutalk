"""New Members Monthly — methodology §S069 (월별 신규 회원 + 채널 분포).

회귀: "2026-04" = 600 (네이버 검색 196 + 메타 166 + 직접 82 + ...)

규칙:
    COUNT(*) FROM customers WHERE signup_date IN <month>
    GROUP BY signup_utm_source

Status: complete — 2026-05-23 metrics 4번째.
"""
from __future__ import annotations
from collections import Counter
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.missing_helper import safe_str

logger = get_logger(__name__)

CUSTOMERS_FILE_NO = 6


class NewMembersMonthly(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        period = merged.get("period")
        if not period:
            raise ValueError("Missing required param: period (YYYY-MM)")
        if "/" in period:
            raise ValueError("new_members_monthly 는 단일 월만")

        df = self.fetch("customers", context)
        # signup_date prefix 매치
        df_period = df[df["signup_date"].astype(str).str.startswith(period)]
        total = len(df_period)

        # 채널 분포
        channels = Counter(safe_str(v) or "(unknown)" for v in df_period["signup_utm_source"])
        by_channel = dict(channels.most_common())

        key = f"S069_new_members_{period}.json"
        logger.info("new_members", period=period, total=total, channels=len(by_channel))

        return {
            "new_members_total": total,
            "new_members_by_channel": by_channel,
            "period": period,
            "_storage": {"layer": "computed", "key": key},
            "_meta": {"formula": "COUNT(*) FROM customers WHERE signup_date prefix period GROUP BY signup_utm_source"},
        }
