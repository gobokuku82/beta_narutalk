"""Response 정직-degrade — diagnose/forecast/attribute 가 빈-실행으로 떨어질 때
거짓 이유("데이터 없음")·내부용어("execution_summary") 대신 *진짜 이유*(기능 미구현)를
결정론적으로 말한다 (B1 닫기, 2026-06-04).

발견(end-to-end response_check): "왜 4월 매출 늘었어?" → op=diagnose → shim 빈 tasks →
planning skip → execution 빈 채 response 도달. Responder LLM 이 빈 execution_summary 를 보고
"데이터(orders 매출)가 제공되지 않아"(거짓 — 119M 잘 계산됨) 라고 지어내고 "execution_summary"
내부용어를 누출. 데이터 0 케이스에서 LLM 은 요약할 게 없고 표현만 하는데 거기서 거짓말 → 결정론 렌더.

build_degrade_payload = 순수 함수(LLM 무관). degrade op + 빈 todos → 정직 payload, 아니면 None.
"""
from __future__ import annotations

import pytest

from app.dream_agent.response.responder import build_degrade_payload
from app.dream_agent.schemas.execution_result import (
    ExecutionResult,
    TodoResult,
    TodoStatus,
)
from app.dream_agent.schemas.response_payload import ResponseFormat
from app.dream_agent.schemas.structured_query import (
    Goal,
    GoalType,
    Intent,
    OutputFormat,
    QueryMeta,
    StructuredQuery,
    Targets,
)


def _sq(operation: str, domain: list[str] | None = None) -> StructuredQuery:
    return StructuredQuery(
        targets=Targets(),
        goal=Goal(type=GoalType.ANSWER, output_format=OutputFormat.TEXT),
        meta=QueryMeta(raw_input="..."),
        tasks=[],
        intent=Intent(operation=operation, domain=domain or ["revenue"]),
    )


def _empty_exec() -> ExecutionResult:
    return ExecutionResult()


def _exec_with_one_todo() -> ExecutionResult:
    return ExecutionResult(
        todos={
            "t1": TodoResult(
                todo_id="t1",
                task_type="metric_calculation",
                tool="revenue_total",
                agent="metrics_agent",
                status=TodoStatus.COMPLETED,
                started_at=0.0,
                ended_at=1.0,
                duration_ms=1.0,
            )
        }
    )


@pytest.mark.parametrize("op", ["diagnose", "forecast", "attribute"])
def test_degrade_op_empty_exec_returns_honest_payload(op):
    payload = build_degrade_payload(_sq(op), _empty_exec())
    assert payload is not None
    # 진짜 이유 = 기능 미구현/준비 중. 거짓("데이터 없음") 아님.
    assert ("준비 중" in payload.text) or ("미구현" in payload.text)
    # 정직 degrade 는 오류가 아니다 — 유효한 답.
    assert payload.format == ResponseFormat.TEXT
    # 내부용어 누출 금지 (정확히 죽이려는 회귀).
    assert "execution_summary" not in payload.text


def test_diagnose_payload_does_not_falsely_claim_missing_data():
    # 데이터가 없어서가 아니라 *기능*이 없어서임을 분명히 — 거짓 "데이터 제공 안 됨" 금지.
    payload = build_degrade_payload(_sq("diagnose", ["revenue"]), _empty_exec())
    assert payload is not None
    assert "제공되지 않" not in payload.text


def test_measure_does_not_degrade():
    # 일반 measure 는 정상 경로(LLM) — 결정론 short-circuit 발화 X.
    assert build_degrade_payload(_sq("measure"), _empty_exec()) is None


def test_degrade_op_with_executed_todos_defers_to_llm():
    # degrade op 이라도 뭔가 실행됐으면(todos 참) LLM 이 요약해야 함 — short-circuit X.
    # (예: "왜 리뷰 나빠졌어" → reviews→sentiment 실행됨 → 실제 답을 LLM 이 작성)
    assert build_degrade_payload(_sq("diagnose"), _exec_with_one_todo()) is None


def test_no_intent_does_not_degrade():
    sq = StructuredQuery(
        targets=Targets(),
        goal=Goal(type=GoalType.ANSWER, output_format=OutputFormat.TEXT),
        meta=QueryMeta(),
        tasks=[],
        intent=None,
    )
    assert build_degrade_payload(sq, _empty_exec()) is None
