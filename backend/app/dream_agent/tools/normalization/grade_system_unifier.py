"""Grade System Unifier — methodology §정제 8.

표준 = #06 customers.member_grade (WELCOME~VIP, 5등급).
#10 customer_rfm.customer_tier (Platinum~Inactive) 는 RFM 용 — 별도.

회귀 (정답): WELCOME 6333 · REGULAR 1539 · SILVER 600 · GOLD 28 · VIP 0

Status: complete — 2026-05-25.
"""
from __future__ import annotations
from collections import Counter
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.missing_helper import safe_str

logger = get_logger(__name__)

STANDARD_ORDER = ["WELCOME", "REGULAR", "SILVER", "GOLD", "VIP"]


class GradeSystemUnifier(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        client = context.client_id
        # #06 표준 등급 분포
        df_c = self.fetch("customers", context)
        std_dist = Counter(safe_str(v) for v in df_c["member_grade"])
        std_dist.pop("", None)
        standard_grade_dist = {g: std_dist.get(g, 0) for g in STANDARD_ORDER}

        # customer_rfm (등록되어 있으면)
        tier_dist: dict[str, int] = {}
        if self.ds.has(client, "customer_rfm"):
            df_r = self.fetch("customer_rfm", context)
            tc = Counter(safe_str(v) for v in df_r.get("customer_tier", []))
            tc.pop("", None)
            tier_dist = dict(tc.most_common())

        # grade_history last snapshot 일치 확인 (등록되어 있으면)
        consistency = None
        if self.ds.has(client, "grade_history"):
            df_h = self.fetch("grade_history", context)
            last_snap = df_h["snapshot_date"].astype(str).max()
            df_last = df_h[df_h["snapshot_date"].astype(str) == last_snap]
            h_dist = Counter(safe_str(v) for v in df_last["grade"])
            h_dist.pop("", None)
            consistency = {
                g: {"customers": standard_grade_dist.get(g, 0),
                    "history_last": h_dist.get(g, 0)}
                for g in STANDARD_ORDER
            }

        key = "grade_unified.json"
        logger.info("grade_unifier", standard=standard_grade_dist,
                    tier_count=len(tier_dist),
                    consistency=consistency is not None)
        return {
            "standard_grade_dist": standard_grade_dist,
            "tier_dist": tier_dist,
            "consistency_check": consistency,
            "_storage": {"layer": "normalized", "key": key},
            "_meta": {"formula": "GROUP BY member_grade — standard order = WELCOME, REGULAR, SILVER, GOLD, VIP"},
        }
