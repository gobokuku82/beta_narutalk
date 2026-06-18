"""Response 정직 degrade — 데이터 불충분 (B2.1 W3).

data_gate(W2)가 consumes 0건/부재로 SKIPPED 처리한 cascade 결과를, responder 가
거짓 요약(LLM 추측) 대신 결정론 정직 문구로 답하는지. build_degrade_payload(미구현
기능 degrade)의 데이터 계약 자매. 순수 함수라 LLM 없이 결정론 검증.

핵심: 전 분석이 데이터 0건에 막힌 경우만 결정론 degrade. 부분 성공(다른 체인 완료)은
None → LLM 이 부분 결과를 요약 (false degrade 0).
"""
from __future__ import annotations

from app.dream_agent.response.responder import build_insufficient_data_payload
from app.dream_agent.schemas.execution_result import (
    ExecutionResult,
    TodoResult,
    TodoStatus,
)


def _todo(tid: str, tool: str, status: TodoStatus, data: dict) -> TodoResult:
    return TodoResult(
        todo_id=tid, task_type="x", tool=tool, agent="a", status=status,
        data=data, started_at=0.0, ended_at=0.0, duration_ms=0.0,
    )


def _insuf(artifact: str, detail: str) -> dict:
    return {"reason": "data_insufficient", "artifact": artifact, "detail": detail}


def test_all_chain_skipped_returns_honest_degrade():
    # 리뷰 0건 → collector COMPLETED(count=0), 하류 전부 SKIPPED → 결정론 정직 degrade
    er = ExecutionResult(todos={
        "t1": _todo("t1", "review_collector", TodoStatus.COMPLETED, {"raw_reviews": [], "count": 0}),
        "t2": _todo("t2", "review_normalizer", TodoStatus.SKIPPED, _insuf("raw_reviews", "raw_reviews 0건")),
        "t3": _todo("t3", "text_preprocessor", TodoStatus.SKIPPED, _insuf("normalized_reviews", "normalized_reviews 부재")),
        "t4": _todo("t4", "sentiment_analyzer", TodoStatus.SKIPPED, _insuf("cleaned_texts", "cleaned_texts 부재")),
    })
    payload = build_insufficient_data_payload(er)
    assert payload is not None
    assert payload.meta.get("reason") == "data_insufficient"
    assert "데이터" in payload.text
    # 거짓 수치를 만들지 않음 — 정직 문구
    assert payload.format.value == "text"
    assert payload.meta.get("details")  # skip 사유가 meta 에 보존


def test_partial_success_returns_none_for_llm():
    # 리뷰 체인은 skip 됐지만 매출(metric) 체인은 완료 → LLM 이 부분 결과 요약 (degrade 아님)
    er = ExecutionResult(todos={
        "t1": _todo("t1", "review_collector", TodoStatus.COMPLETED, {"raw_reviews": []}),
        "t2": _todo("t2", "review_normalizer", TodoStatus.SKIPPED, _insuf("raw_reviews", "raw_reviews 0건")),
        "t3": _todo("t3", "revenue_total", TodoStatus.COMPLETED, {"revenue_total": 119539660}),
    })
    assert build_insufficient_data_payload(er) is None


def test_no_insufficiency_returns_none():
    # 정상 감성 분석 완료 → degrade 아님 (false positive 0)
    er = ExecutionResult(todos={
        "t1": _todo("t1", "sentiment_analyzer", TodoStatus.COMPLETED,
                    {"sentiment_distribution": {"positive": 58.3}}),
    })
    assert build_insufficient_data_payload(er) is None


def test_empty_todos_returns_none():
    # 실행 자체가 없음 → build_degrade_payload(미구현 degrade) 영역, 여기선 None
    assert build_insufficient_data_payload(ExecutionResult(todos={})) is None


def test_only_collector_completed_still_degrades():
    # collector 만 COMPLETED(0건) 이고 분석은 전부 skip → collector 는 산출로 안 침 → degrade
    er = ExecutionResult(todos={
        "t1": _todo("t1", "review_collector", TodoStatus.COMPLETED, {"raw_reviews": [], "count": 0}),
        "t2": _todo("t2", "keyword_extractor", TodoStatus.SKIPPED, _insuf("cleaned_texts", "cleaned_texts 부재")),
    })
    assert build_insufficient_data_payload(er) is not None
