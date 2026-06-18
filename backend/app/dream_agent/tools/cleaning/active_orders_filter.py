"""Active Orders Filter — methodology_cleaning §정제 1 (order_status != 'C40').

세부계획: docs/_claude/data/tool_세부계획_시범+인프라_2026-05-23.md §3 Step 6
입력: period (required) — YYYY-MM or YYYY-MM/YYYY-MM
출력: orders_active (list[dict]), count, dropped, _storage (저장 위치)

검증값 (methodology + clumi_analysis 정답표):
  - "2026-04":              활성 1,919 (2,000 - 81 취소)
  - "2026-03/2026-04":      활성 3,265 (3,420 - 155 취소)

Status: complete — 2026-05-23 시범 구현 1차.
"""
from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.order_helper import is_active_order  # 활성주문 SSOT (ADR-032 D3)

logger = get_logger(__name__)

# DataSource source_id="orders" (data/{client}/raw/orders.csv)
STATUS_COL = "order_status"
DATE_COL = "order_date"


class ActiveOrdersFilter(BaseTool):
    """활성 주문 필터 — 취소(C40) 제외, 기간 필터 후 normalized layer 저장."""

    async def execute(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        merged = self.merge_params(params)
        period = merged.get("period")
        if not period:
            raise ValueError(
                "Missing required param: period (YYYY-MM or YYYY-MM/YYYY-MM). "
                "Cognitive Layer 가 자연어에서 기간 추출 실패 시 HITL clarification 권장."
            )

        # 1. raw 로드
        df_raw = self.fetch("orders", context).copy()
        before = len(df_raw)

        # 2. 기간 필터 (order_date prefix)
        df_period = self._filter_period(df_raw, period)

        # 3. 활성 필터 (methodology §정제 1)
        df_active = df_period[df_period[STATUS_COL].map(is_active_order)]
        dropped = len(df_period) - len(df_active)

        period_safe = period.replace("/", "_")
        key = f"orders_active_{period_safe}.parquet"
        logger.info(
            "active_orders_filter completed",
            period=period,
            input=before,
            active=len(df_active),
            dropped=dropped,
        )

        return {
            "orders_active": df_active.to_dict(orient="records"),
            "count": len(df_active),
            "dropped": dropped,
            "_storage": {"layer": "normalized", "key": key},
            "_meta": {
                "period": period,
                "filter": f"{STATUS_COL} 취소(C계열) 전체 제외 — is_active_order (ADR-032 D3)",
                "input_rows": before,
            },
        }

    @staticmethod
    def _filter_period(df, period: str):
        """period 'YYYY-MM' 또는 'YYYY-MM/YYYY-MM' → order_date prefix 매치.

        POC: YYYY-MM 단위 prefix. YYYY-MM-DD 정밀 필터는 후속.
        """
        if "/" in period:
            start, end = period.split("/")
            return df[df[DATE_COL].str[:7].between(start, end)]
        return df[df[DATE_COL].str.startswith(period)]
