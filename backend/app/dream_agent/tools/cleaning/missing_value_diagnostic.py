"""Missing Value Diagnostic — entity 의 결측 통계 리포트.

methodology 외 — POC 운영 도구. 정제 1·3 디버깅 시 발견한 NaN 처리 패턴
(pandas float('nan'), 의미있는 NaN vs 누락) 을 운영 가시화.

shared/missing_helper.py 의 null_stats + classify_missing 사용.

데이터셋별 의미있는 NaN 사전 정의 (SEMANTIC_NULLS):
    orders.member_id          — 비회원 주문 (의미있음)
    customers.last_order_date — 비주문 회원 (의미있음, 74.5% 정상)
    customers.last_login_date — 미접속 회원
    ... (추후 entity 추가 시 확장)

Status: complete — 2026-05-23 cleaning 3번째 tool.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.missing_helper import classify_missing, null_stats

logger = get_logger(__name__)


# source_id 별 *의미있는 NaN* (데이터셋 본질, 데이터 누락 아님)
SEMANTIC_NULLS: dict[str, dict[str, str]] = {
    "orders": {
        "member_id": "비회원 주문 — 빈값이 정상 (orders 의 258건)",
    },
    "customers": {
        "last_order_date": "비주문 회원 — NaN 정상 (6,333명, 74.5%)",
        "last_login_date": "미접속 회원 — NaN 정상",
    },
}


class MissingValueDiagnostic(BaseTool):
    """entity 의 결측 통계 + 의미 분류 리포트."""

    async def execute(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        merged = self.merge_params(params)
        source_id = merged.get("source_id")
        if not source_id:
            raise ValueError("Missing required param: source_id (예: 'orders', 'customers')")

        if not self.ds.has(context.client_id, source_id):
            raise ValueError(
                f"source_id={source_id!r} not registered for client={context.client_id!r}"
            )

        data = self.fetch(source_id, context)
        # CSV 만 지원 (DataFrame). JSON·JSONL 은 후속.
        if not isinstance(data, pd.DataFrame):
            raise ValueError(
                f"source_id={source_id!r} 는 DataFrame 아님 ({type(data).__name__}). "
                "POC: CSV 만 지원 — JSON/JSONL 은 후속 확장"
            )
        df = data

        entity_name = merged.get("entity_name") or source_id

        stats = null_stats(df)
        classified = classify_missing(stats, semantic_nulls=SEMANTIC_NULLS.get(source_id))

        complete = sum(1 for s in classified if s["classification"] == "complete")
        with_gap = len(classified) - complete

        key = f"missing_diagnostic_{entity_name}.json"
        logger.info(
            "missing_value_diagnostic completed",
            source_id=source_id,
            entity=entity_name,
            rows=len(df),
            cols=len(df.columns),
            complete=complete,
            with_gap=with_gap,
        )

        return {
            "column_stats": classified,
            "total_columns": len(df.columns),
            "total_rows": len(df),
            "complete_columns": complete,
            "columns_with_gap": with_gap,
            "_storage": {"layer": "normalized", "key": key},
            "_meta": {"source_id": source_id, "entity_name": entity_name},
        }
