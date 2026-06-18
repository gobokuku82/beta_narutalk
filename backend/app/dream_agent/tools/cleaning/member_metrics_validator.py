"""Member Metrics Validator — methodology_cleaning §정제 3.

세부계획: cleaning 2번째 tool (시범 통과 후 패턴 재사용 검증).

규칙:
    customers.total_orders          vs COUNT(orders WHERE member_id=X AND order_status != 'C40')
    customers.total_purchase_amount vs SUM(orders.payment_amount WHERE member_id=X AND 활성)
    customers.last_order_date       vs MAX(orders.order_date WHERE member_id=X AND 활성)

→ 불일치 시 customers 값을 orders 기반으로 재계산.

검증값 (mock 정합):
    customer_count = 8,500
    active_orders_member = 3,007 (전체 활성 3,265 - 비회원 258)
    mismatch_count = 0 (methodology: "이미 3월 추가 후 갱신")

Status: complete — 2026-05-23 cleaning 2번째 tool.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.missing_helper import safe_int, safe_str
from app.dream_agent.tools.shared.order_helper import is_active_order  # 활성주문 SSOT (ADR-032 D3)

logger = get_logger(__name__)

ORDERS_FILE_NO = 5
CUSTOMERS_FILE_NO = 6

# methodology 명시 3 필드
DEFAULT_FIELDS = ["total_orders", "total_purchase_amount", "last_order_date"]


class MemberMetricsValidator(BaseTool):
    """customers 누적 지표 vs orders 실측 정합 검증 + 보정."""

    async def execute(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        merged = self.merge_params(params)
        fields = merged.get("fields") or DEFAULT_FIELDS
        include_lifetime = bool(merged.get("include_lifetime", False))

        # 1. raw 로드
        df_orders = self.fetch("orders", context).copy()
        df_customers = self.fetch("customers", context).copy()

        # 2. orders 활성 (회원만) 집계
        df_active = df_orders[
            df_orders["order_status"].map(is_active_order)
            & df_orders["member_id"].notna()
            & (df_orders["member_id"].astype(str).str.strip() != "")
        ]
        active_orders_member = len(df_active)

        # member_id → (count, sum_payment, last_date)
        actual: dict[str, dict] = defaultdict(
            lambda: {"total_orders": 0, "total_purchase_amount": 0, "last_order_date": ""}
        )
        for _, row in df_active.iterrows():
            mid = row["member_id"]
            a = actual[mid]
            a["total_orders"] += 1
            a["total_purchase_amount"] += int(float(row["payment_amount"]))
            if row["order_date"] > a["last_order_date"]:
                a["last_order_date"] = row["order_date"]

        # 3. customers 한 행씩 비교 + 보정
        mismatches: list[dict] = []
        validated: list[dict] = []
        for _, c in df_customers.iterrows():
            mid = c["member_id"]
            row = dict(c)
            a = actual.get(mid, {"total_orders": 0, "total_purchase_amount": 0, "last_order_date": ""})

            for field in fields:
                cust_v = row.get(field)
                act_v = a[field]
                # 타입 정규화 — shared/missing_helper (NaN/None/빈문자열 통일)
                if field in ("total_orders", "total_purchase_amount"):
                    cust_num = safe_int(cust_v, default=0)
                    if cust_num != act_v:
                        mismatches.append({
                            "member_id": mid, "field": field,
                            "customer_value": cust_num, "actual_value": act_v,
                        })
                        row[field] = act_v  # 보정
                else:  # last_order_date
                    cust_s = safe_str(cust_v, default="")
                    act_s = act_v
                    if include_lifetime and cust_s and not act_s:
                        # lifetime 모드: orders 데이터 외(이전 주문) customers last 유지 OK
                        continue
                    if cust_s != act_s:
                        mismatches.append({
                            "member_id": mid, "field": field,
                            "customer_value": cust_s, "actual_value": act_s,
                        })
                        row[field] = act_s

            validated.append(row)

        mismatch_count = len(mismatches)

        key = "customers_validated.parquet"
        logger.info(
            "member_metrics_validator completed",
            customer_count=len(df_customers),
            active_orders_member=active_orders_member,
            mismatch_count=mismatch_count,
        )

        return {
            "validated_customers": validated,
            "mismatches": mismatches,
            "mismatch_count": mismatch_count,
            "customer_count": len(df_customers),
            "active_orders_member": active_orders_member,
            "_storage": {"layer": "normalized", "key": key},
            "_meta": {"fields": fields, "include_lifetime": include_lifetime},
        }
