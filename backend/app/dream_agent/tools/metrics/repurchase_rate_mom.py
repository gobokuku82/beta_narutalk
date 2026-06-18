"""Repurchase Rate MoM — methodology §S028 (재구매율, 월 단위).

회귀 (정답):
    "2026-04": 79.0% (전체 1,386 / 기존 1,095)
    "2026-03": 76.2% (전체 1,206 / 기존 919)

규칙:
    전체 구매 고객 = COUNT(DISTINCT member_id) WHERE 활성 AND 월 AND member_id 있음
    기존 (재구매) = same + is_first_order=0
    재구매율 = 기존 / 전체 × 100

Status: complete — 2026-05-23 metrics 3번째.
"""
from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.missing_helper import safe_str
from app.dream_agent.tools.shared.order_helper import filter_active_orders

logger = get_logger(__name__)

ORDERS_FILE_NO = 5


class RepurchaseRateMom(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        period = merged.get("period")
        if not period:
            raise ValueError("Missing required param: period (YYYY-MM)")
        if "/" in period:
            raise ValueError("repurchase_rate_mom 은 단일 월만 — '/' 미지원 (MoM 비교 별도)")

        df = self.fetch("orders", context)
        df_active = filter_active_orders(df, period=period)

        # 회원만 (비회원 제외)
        df_member = df_active[df_active["member_id"].apply(lambda v: bool(safe_str(v)))]

        # DISTINCT member_id — 전체
        total_set = {safe_str(v) for v in df_member["member_id"]}
        # is_first_order=0 (기존)
        existing_df = df_member[df_member["is_first_order"].astype(str) == "0"]
        existing_set = {safe_str(v) for v in existing_df["member_id"]}
        # is_first_order=1 (신규)
        new_df = df_member[df_member["is_first_order"].astype(str) == "1"]
        new_set = {safe_str(v) for v in new_df["member_id"]}

        total = len(total_set)
        existing = len(existing_set)
        new = len(new_set)
        rate = round(existing / total * 100, 1) if total else 0.0

        key = f"S028_repurchase_rate_{period}.json"
        logger.info("repurchase_rate", period=period, rate=rate, total=total, existing=existing)

        return {
            "repurchase_rate": rate,
            "total_buyers": total, "existing_buyers": existing, "new_buyers": new,
            "period": period,
            "_storage": {"layer": "computed", "key": key},
            "_meta": {"formula": "existing(is_first_order=0) / total(distinct member_id) * 100"},
        }
