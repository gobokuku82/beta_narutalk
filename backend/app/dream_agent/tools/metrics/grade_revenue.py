"""Grade Revenue — methodology §S046 (등급별 회원수·매출 표).

회귀 (4월 정답):
    SILVER: 600 회원 / 571 구매자 / 65,757,080 매출
    GOLD:    28 회원 /  28 구매자 /  8,511,200
    REGULAR: 1,539 회원 / 787 구매자 / 39,496,930
    WELCOME: 6,333 회원 / 0   구매자 / 0
    VIP:     0   회원 / 0   구매자 / 0
    합계:    8,500 회원

분모 정책 (methodology §S046 명시):
    회원 비중 % = 등급별 회원수 / 8,500 × 100
    매출 비중 % = 등급별 매출   / 회원 매출 합 × 100 (비회원 매출 제외)

Status: complete — 2026-05-23 metrics 5번째 (첫 join 패턴).
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.missing_helper import safe_int, safe_str
from app.dream_agent.tools.shared.order_helper import filter_active_orders

logger = get_logger(__name__)

ORDERS_FILE_NO = 5
CUSTOMERS_FILE_NO = 6

# methodology §S046 등급 순서 (PDF 표시 순)
GRADE_ORDER = ["VIP", "GOLD", "SILVER", "REGULAR", "WELCOME"]


class GradeRevenue(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        period = merged.get("period")
        if not period:
            raise ValueError("Missing required param: period (YYYY-MM)")
        if "/" in period:
            raise ValueError("grade_revenue 는 단일 월만")

        # 1. raw 로드
        df_customers = self.fetch("customers", context)
        df_orders = self.fetch("orders", context)

        # 2. member_id → grade 매핑 (현재 시점)
        grade_by_member = {
            safe_str(c["member_id"]): safe_str(c.get("member_grade", ""))
            for _, c in df_customers.iterrows()
        }
        total_members = len(df_customers)

        # 3. 등급별 회원 수
        member_count: dict[str, int] = defaultdict(int)
        for g in grade_by_member.values():
            if g:
                member_count[g] += 1

        # 4. 4월 활성주문 (회원만)
        df_active = filter_active_orders(df_orders, period=period)
        df_member = df_active[df_active["member_id"].apply(lambda v: bool(safe_str(v)))]

        # 5. 등급별 매출·구매자 집계
        rev_by_grade: dict[str, int] = defaultdict(int)
        buyers_by_grade: dict[str, set] = defaultdict(set)
        for _, o in df_member.iterrows():
            mid = safe_str(o["member_id"])
            g = grade_by_member.get(mid, "")
            if not g:
                continue
            rev_by_grade[g] += safe_int(o["payment_amount"])
            buyers_by_grade[g].add(mid)

        total_member_revenue = sum(rev_by_grade.values())

        # 6. 표 구성 (정해진 순서, 누락 등급도 0 으로)
        table: dict[str, dict] = {}
        for g in GRADE_ORDER:
            mc = member_count.get(g, 0)
            ms = round(mc / total_members * 100, 1) if total_members else 0.0
            rev = rev_by_grade.get(g, 0)
            rs = round(rev / total_member_revenue * 100, 1) if total_member_revenue else 0.0
            table[g] = {
                "member_count": mc,
                "member_share_pct": ms,
                "buyer_count": len(buyers_by_grade.get(g, set())),
                "revenue": rev,
                "revenue_share_pct": rs,
            }

        # 7. 회귀 검증용 단일값 노출
        silver_revenue = table["SILVER"]["revenue"]
        welcome_member_share = table["WELCOME"]["member_share_pct"]

        key = f"S046_grade_revenue_{period}.json"
        logger.info(
            "grade_revenue", period=period,
            silver=silver_revenue, welcome_share=welcome_member_share,
            total_rev=total_member_revenue,
        )

        return {
            "table": table,
            "total_members": total_members,
            "total_member_revenue": total_member_revenue,
            "silver_revenue": silver_revenue,
            "welcome_member_share": welcome_member_share,
            "period": period,
            "_storage": {"layer": "computed", "key": key},
            "_meta": {"formula": "GROUP BY member_grade — member_share=mc/total_members, revenue_share=rev/total_member_revenue (비회원 제외)"},
        }
