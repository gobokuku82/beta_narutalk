"""Member/Guest Stats — methodology §정제 10 (회원/비회원 카운트·비율 묶음).

산출 = member_count·guest_count·total_active·member_share_pct·guest_share_pct (5 묶음).
이름: '분리'(splitter)가 아니라 통계 산출 — orders.member_id 기준 라벨 후 집계.

회귀:
    "2026-04": 회원 1,779 / 비회원 140 / 합 1,919
    "all":     회원 3,007 / 비회원 258 / 합 3,265

Status: complete — 2026-05-25 (rename 2026-05-30).
"""
from __future__ import annotations
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.missing_helper import safe_str
from app.dream_agent.tools.shared.order_helper import filter_active_orders

logger = get_logger(__name__)


class MemberGuestStats(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        period = merged.get("period")

        df = self.fetch("orders", context)
        df_active = filter_active_orders(df, period=period)
        # member_id 정규화 — NaN/빈 → 비회원
        is_member = df_active["member_id"].apply(lambda v: bool(safe_str(v)))
        df_member = df_active[is_member]
        df_guest = df_active[~is_member]

        mc = len(df_member)
        gc = len(df_guest)
        total = mc + gc
        ms = round(mc / total * 100, 1) if total else 0.0
        gs = round(gc / total * 100, 1) if total else 0.0

        period_safe = (period or "all").replace("/", "_")
        key = f"orders_split_{period_safe}.json"
        logger.info("member_guest_stats", period=period, member=mc, guest=gc, total=total)
        result = {
            "member_count": mc, "guest_count": gc, "total_active": total,
            "member_share_pct": ms, "guest_share_pct": gs,
            "_storage": {"layer": "normalized", "key": key},
            "_meta": {"formula": "is_guest = (member_id IS NULL); split active orders"},
        }
        if period:  # 'all' 라벨 데이터 방출 금지 (슬라이스 1, 헌법 D3·R2 — silent-0 오염원)
            result["period"] = period
        return result
