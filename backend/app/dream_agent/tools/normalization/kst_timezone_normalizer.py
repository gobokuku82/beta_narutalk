"""KST Timezone Normalizer — methodology §정제 2.

GA4 #07/#08 의 event_timestamp (microsec UTC) → KST datetime 변환.
event_date (UTC YYYYMMDD) 는 *사용 금지* — KST 자정 경계 불일치.

핵심:
    timestamp_us / 1e6 + KST(+9hr) → datetime
    KST date = DATE(KST datetime) (event_date 와 다를 수 있음)

Status: complete — 2026-05-25.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.logging import get_logger
from app.dream_agent.models import ExecutionContext
from app.dream_agent.tools.base_tool import BaseTool

logger = get_logger(__name__)

KST = timezone(timedelta(hours=9))


def to_kst_datetime(timestamp_us: int) -> datetime:
    """microsec UTC → KST datetime."""
    return datetime.fromtimestamp(timestamp_us / 1_000_000, tz=KST)


class KstTimezoneNormalizer(BaseTool):
    async def execute(self, params: dict[str, Any], context: ExecutionContext) -> dict[str, Any]:
        merged = self.merge_params(params)
        source_id = merged.get("source_id")
        if not source_id:
            raise ValueError("Missing required param: source_id (ga4 jsonl)")
        sample_size = int(merged.get("sample_size", 1000))

        total = 0
        boundary_shifts = 0
        sample: list[dict] = []

        for rec in self.ds.stream_jsonl(context.client_id, source_id):
            total += 1
            ts_us = rec.get("event_timestamp")
            event_date = rec.get("event_date") or ""
            if ts_us is None:
                continue
            try:
                ts_us_int = int(ts_us)
            except (TypeError, ValueError):
                continue
            kst_dt = to_kst_datetime(ts_us_int)
            kst_date = kst_dt.strftime("%Y%m%d")
            if event_date and event_date != kst_date:
                boundary_shifts += 1
            if len(sample) < sample_size:
                sample.append({
                    "event_timestamp": ts_us_int,
                    "kst_datetime": kst_dt.isoformat(),
                    "kst_date": kst_date,
                    "event_date_utc": event_date,
                })

        key = f"kst_summary_{source_id}.json"
        logger.info("kst_normalizer", source_id=source_id, total=total, shifts=boundary_shifts)
        return {
            "total_events": total,
            "sample_converted": sample,
            "date_boundary_shifts": boundary_shifts,
            "_storage": {"layer": "normalized", "key": key},
            "_meta": {"formula": "datetime.fromtimestamp(event_timestamp/1e6, tz=KST(+9))"},
        }
