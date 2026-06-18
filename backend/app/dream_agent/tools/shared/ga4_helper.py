"""GA4 streaming helper — methodology_cleaning §정제 6 (세션 단위 집계).

#07/#08 jsonl 대용량 (96MB / 265MB) — streaming 필수.
event_params 는 typed key/value array — 추출 helper 통합.

회귀 (4월 #07):
    session_start 이벤트 = 24,000 (S067 분모)
    first_visit = 12,496
    purchase = 1,823

Status: complete — 2026-05-23 GA4 진입 1차 (signup_conversion 입력).
"""
from __future__ import annotations
from collections import Counter
from typing import Any, Iterable


def get_event_param(record: dict, key: str) -> Any:
    """GA4 event_params 배열에서 특정 key 의 value 추출.

    event_params: [{"key": "...", "value": {"string_value"·"int_value"·"float_value"·...}}, ...]
    """
    for p in record.get("event_params") or []:
        if p.get("key") == key:
            v = p.get("value") or {}
            # 값 타입 우선순위
            for vtype in ("string_value", "int_value", "float_value", "double_value"):
                if v.get(vtype) is not None:
                    return v[vtype]
    return None


def count_events_by_name(stream: Iterable[dict]) -> Counter:
    """event_name 별 카운트 (전체 stream 소비)."""
    counts: Counter = Counter()
    for rec in stream:
        counts[rec.get("event_name", "")] += 1
    return counts


def count_session_starts(stream: Iterable[dict]) -> int:
    """methodology §S067 분모 = session_start 이벤트 수."""
    return sum(1 for rec in stream if rec.get("event_name") == "session_start")


def session_start_by_source(stream: Iterable[dict]) -> dict[str, int]:
    """session_start 이벤트의 traffic_source 채널별 카운트.

    채널 추출: session_traffic_source_last_click 또는 event_params 의 'source'/'campaign'.
    fallback = 'unknown'.
    """
    counts: Counter = Counter()
    for rec in stream:
        if rec.get("event_name") != "session_start":
            continue
        # session_traffic_source_last_click 우선
        src = None
        last_click = (rec.get("session_traffic_source_last_click") or {})
        # manual_campaign 또는 cross_channel_campaign 의 source
        for path in ("manual_campaign", "cross_channel_campaign"):
            block = last_click.get(path) or {}
            src = block.get("source")
            if src:
                break
        if not src:
            # fallback — event_params 의 source 키
            src = get_event_param(rec, "source")
        counts[src or "unknown"] += 1
    return dict(counts.most_common())


__all__ = [
    "get_event_param",
    "count_events_by_name",
    "count_session_starts",
    "session_start_by_source",
]
