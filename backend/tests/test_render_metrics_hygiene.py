"""display raw-leak 정직화 — _render_metrics 위생 (2026-06-10, stage1 감사 C).

서술 tool(summary/report) 부재 시 fallback 으로 metric 을 text 렌더하는데,
구조/provenance(schema_version·op·field)가 답처럼 새던 것("schema_version: ads.v1") 차단.
metric tool 관례 {label, value, unit} 은 "label: value unit" 으로 합쳐 렌더.
"""
from __future__ import annotations

from app.dream_agent.response.responder import _render_metrics
from app.dream_agent.schemas.execution_result import (
    ExecutionResult,
    TodoResult,
    TodoStatus,
)


def _er(datas: list[dict]) -> ExecutionResult:
    todos = {
        f"t{i}": TodoResult(
            todo_id=f"t{i}", task_type="x", tool="x", status=TodoStatus.COMPLETED,
            data=d, started_at=0.0, ended_at=0.0, duration_ms=0.0,
        )
        for i, d in enumerate(datas)
    }
    return ExecutionResult(todos=todos)


def test_no_schema_version_leak():
    out = _render_metrics(_er([{
        "normalized_ads": [1, 2], "schema_version": "ads.v1",
        "channel_counts": {"a": 1}, "count": 5,
    }]))
    assert "schema_version" not in out and "ads.v1" not in out


def test_pairs_label_value_unit():
    out = _render_metrics(_er([{
        "value": 12, "label": "캠페인 수", "op": "count", "field": "campaign_id", "unit": "개",
    }]))
    assert "캠페인 수: 12개" in out
    assert "op" not in out and "field" not in out   # provenance 미노출


def test_named_scalar_kept():
    out = _render_metrics(_er([{
        "revenue_total": 119539660, "active_orders_count": 1919,
        "period": "2026-04", "_storage": {"layer": "computed"},
    }]))
    assert "revenue_total: 119539660" in out
    assert "_storage" not in out   # _ prefix 제외


def test_empty_when_only_provenance():
    # 구조/provenance 만 있으면 빈 문자열(→ build_display 가 fallback 문구로) — raw 덤프 안 함
    out = _render_metrics(_er([{"schema_version": "ads.v1", "op": "sum", "field": "x"}]))
    assert out.strip() == ""
