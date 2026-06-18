"""Execution 데이터 게이트 배선 (B2.1 W2) — _run_single_todo 가 consumes 불충분 시
execute() 를 건너뛰고 SKIPPED + 정밀 사유 TodoResult 를 반환하는지.

게이트가 execute() 전에 단락하므로 LLM/실제 tool 호출 없이 결정론 검증.
순수 함수 자체는 test_execution_data_gate.py 가 검증 — 여기선 executor 배선만.
"""
from __future__ import annotations

import asyncio

from app.dream_agent.execution.executor import _run_single_todo
from app.dream_agent.models import ExecutionContext
from app.dream_agent.planning.planner import PlannedTodo
from app.dream_agent.schemas.execution_result import TodoStatus


def _ctx(previous: dict) -> ExecutionContext:
    return ExecutionContext(session_id="s", plan_id="p", previous_results=previous)


def test_skips_when_consume_absent():
    # review_normalizer 는 raw_reviews 를 consume — 이전 결과에 없음 → SKIPPED
    todo = PlannedTodo(
        id="t2", task_type="data_preprocessing",
        agent="channel_normalizing_agent", tool="review_normalizer", depends_on=["t1"],
    )
    result = asyncio.run(_run_single_todo(todo, _ctx({}), {}))
    assert result.status == TodoStatus.SKIPPED
    assert result.data["reason"] == "data_insufficient"
    assert result.data["artifact"] == "raw_reviews"
    assert "부재" in result.data["detail"]


def test_skips_when_consume_empty():
    # 생산자가 COMPLETED 했으나 raw_reviews=[] (4월 리뷰 0건) → 하류 SKIPPED
    todo = PlannedTodo(
        id="t2", task_type="data_preprocessing",
        agent="channel_normalizing_agent", tool="review_normalizer", depends_on=["t1"],
    )
    result = asyncio.run(_run_single_todo(todo, _ctx({"t1": {"raw_reviews": [], "count": 0}}), {}))
    assert result.status == TodoStatus.SKIPPED
    assert result.data["artifact"] == "raw_reviews"
    assert "0건" in result.data["detail"]


def test_no_consumes_tool_not_gated():
    # review_collector 는 consumes 미선언 → 게이트가 막지 않음(SKIPPED 아님).
    # (실제 수집 결과는 데이터 유무에 따르나, 적어도 게이트 SKIPPED 는 아님)
    todo = PlannedTodo(
        id="t1", task_type="data_collection",
        agent="collection_agent", tool="review_collector", depends_on=[],
    )
    result = asyncio.run(_run_single_todo(todo, _ctx({}), {}))
    assert result.data.get("reason") != "data_insufficient"
