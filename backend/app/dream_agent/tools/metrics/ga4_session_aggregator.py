"""GA4 Session Aggregator — methodology §정제 6 (세션 단위 집계).

회귀 (정답):
    session_start_total = 24,000           ← S067 분모
    by_event.first_visit = 12,496
    by_event.purchase = 1,823

pushdown 전환 (ADR-031, 2026-06-12 — 시범 tool 1호):
    구현: 38,319행 전량 스트리밍 2-Counter → 관절 query/aggregate 2호출.
    - by_event  = ds.aggregate(count by event_name)   — Postgres 행-테이블이면 SQL GROUP BY 1방
    - by_source = session_start 행만 2컬럼 투영(query_iter, 스트리밍) 후 _extract_source
      (도메인 규칙은 tool 유지 — ADR-031-2. query 아닌 query_iter = 24,000행 투영의 materialize 방지)
    File 백엔드는 기본 구현(스트리밍 2-pass — V3: 피크 메모리 비역행, 시간 ~2× 상한 허용)으로 동일 정답.
    실측은 완료보고서(pushdown) §효과 표 참조.

Status: complete — 2026-05-23 GA4 1차 (S067 입력) · 2026-06-12 pushdown 전환.
"""
from __future__ import annotations
from collections import Counter
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool
from app.dream_agent.tools.shared.ga4_helper import (
    get_event_param,
)

logger = get_logger(__name__)

GA4_SOURCE_ID = "ga4_traffic_source"


class Ga4SessionAggregator(BaseTool):
    async def execute(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        client = context.client_id

        # 집계 내리기 — event_name 분포 (Postgres 행-테이블 = SQL GROUP BY / File = 스트리밍 1-pass)
        by_event_raw = self.ds.aggregate(client, GA4_SOURCE_ID, op="count", by="event_name")
        by_event: Counter = Counter({k: int(v) for k, v in by_event_raw.items() if k is not None})

        # 범위 내리기 — session_start 행 × 2컬럼 투영, 스트리밍 소비 (V3: 피크 메모리 비역행)
        rows = self.ds.query_iter(
            client, GA4_SOURCE_ID,
            where={"event_name": "session_start"},
            columns=["session_traffic_source_last_click", "event_params"],
        )
        by_source: Counter = Counter(self._extract_source(r) for r in rows)

        session_total = by_event.get("session_start", 0)
        by_event_dict = dict(by_event.most_common())
        by_source_dict = dict(by_source.most_common())

        key = "ga4_sessions_summary.json"
        logger.info(
            "ga4_session_aggregator",
            session_total=session_total,
            events=len(by_event_dict),
            sources=len(by_source_dict),
        )
        return {
            "session_start_total": session_total,
            "by_event": by_event_dict,
            "by_source": by_source_dict,
            "_storage": {"layer": "normalized", "key": key},
            "_meta": {"formula": "COUNT WHERE event_name='session_start' GROUP BY source"},
        }

    @staticmethod
    def _extract_source(rec: dict) -> str:
        """session_traffic_source_last_click 우선 + fallback event_params.source."""
        last_click = rec.get("session_traffic_source_last_click") or {}
        for path in ("manual_campaign", "cross_channel_campaign"):
            block = last_click.get(path) or {}
            src = block.get("source")
            if src:
                return src
        return get_event_param(rec, "source") or "unknown"
