"""Planning 데이터플로우 체인 완성 — Stage3 LLM 이 필수 전처리 tool 을 빠뜨려도
produces/consumes 메타로 생산자를 결정론적으로 삽입·배선해 체인 단절(silent 0)을 막는다.
(tool compose 신뢰성 fix, 2026-06-05)

발견(구조 분석 + flakiness 실측): "리뷰 반응?" → Stage3 가 review_collector→text_preprocessor 로
review_normalizer 를 ~40% 누락 → text_preprocessor 가 normalized_reviews 를 못 받아 cleaned_texts=0
→ 감성 0. 근본: (a) Stage3 가 고정 체인을 매번 LLM 으로 재조립 (b) few-shot 예시가 normalizer 생략
(c) text_preprocessor 카탈로그 메타가 raw_reviews 라고 거짓말(코드는 normalized_reviews 소비).

체인(코드 기준): review_collector(raw_reviews) → review_normalizer(normalized_reviews)
              → text_preprocessor(cleaned_texts) → sentiment_analyzer/keyword_extractor.

complete_dataflow_chain = 순수 함수. consumer.consumes 의 생산자가 plan 에 없으면 카탈로그
producer 를 삽입하고 depends_on/dag 배선. 이미 있으면 멱등(안 건드림).
"""
from __future__ import annotations

from app.dream_agent.planning.planner import (
    Plan,
    PlannedTodo,
    _load_catalog,
    complete_dataflow_chain,
    validate_dag,
)


def _broken_review_plan() -> Plan:
    # LLM 이 자주 내놓는 깨진 plan: review_normalizer 누락 (collector→preprocessor 직결)
    return Plan(
        teams_selected=["analysis_team"],
        todos=[
            PlannedTodo(id="t1", task_type="data_collection",
                        agent="collection_agent", tool="review_collector", depends_on=[]),
            PlannedTodo(id="t2", task_type="data_preprocessing",
                        agent="text_preprocessing_agent", tool="text_preprocessor", depends_on=["t1"]),
            PlannedTodo(id="t3", task_type="sentiment_analysis",
                        agent="analysis_agent", tool="sentiment_analyzer", depends_on=["t2"]),
        ],
        dag={"t1": [], "t2": ["t1"], "t3": ["t2"]},
    )


def _correct_review_plan() -> Plan:
    return Plan(
        teams_selected=["analysis_team"],
        todos=[
            PlannedTodo(id="t1", task_type="data_collection",
                        agent="collection_agent", tool="review_collector", depends_on=[]),
            PlannedTodo(id="t2", task_type="data_preprocessing",
                        agent="channel_normalizing_agent", tool="review_normalizer", depends_on=["t1"]),
            PlannedTodo(id="t3", task_type="data_preprocessing",
                        agent="text_preprocessing_agent", tool="text_preprocessor", depends_on=["t2"]),
            PlannedTodo(id="t4", task_type="sentiment_analysis",
                        agent="analysis_agent", tool="sentiment_analyzer", depends_on=["t3"]),
        ],
        dag={"t1": [], "t2": ["t1"], "t3": ["t2"], "t4": ["t3"]},
    )


def test_inserts_missing_review_normalizer():
    plan = complete_dataflow_chain(_broken_review_plan(), _load_catalog())
    tools = [t.tool for t in plan.todos]
    assert "review_normalizer" in tools, f"normalizer 가 삽입돼야 함: {tools}"
    norm = next(t for t in plan.todos if t.tool == "review_normalizer")
    tp = next(t for t in plan.todos if t.tool == "text_preprocessor")
    coll = next(t for t in plan.todos if t.tool == "review_collector")
    # text_preprocessor 는 review_normalizer 에 의존(= 더 늦은 phase)
    assert norm.id in tp.depends_on
    # review_normalizer 는 review_collector(raw_reviews 생산자)에 의존
    assert coll.id in norm.depends_on


def test_no_cycle_or_unknown_dep_after_completion():
    plan = complete_dataflow_chain(_broken_review_plan(), _load_catalog())
    assert validate_dag(plan) == []


def test_idempotent_on_correct_plan():
    plan = _correct_review_plan()
    before = sorted(t.tool for t in plan.todos)
    after = complete_dataflow_chain(plan, _load_catalog())
    assert sorted(t.tool for t in after.todos) == before  # 삽입 없음


def test_metric_plan_untouched():
    # 매출(숫자) plan — 전처리 체인 consumes 없음 → 변경 없음
    plan = Plan(
        teams_selected=["analysis_team"],
        todos=[
            PlannedTodo(id="t1", task_type="data_collection",
                        agent="collection_agent", tool="orders_collector", depends_on=[]),
            PlannedTodo(id="t2", task_type="metric_calculation",
                        agent="metrics_agent", tool="revenue_total", depends_on=["t1"]),
        ],
        dag={"t1": [], "t2": ["t1"]},
    )
    after = complete_dataflow_chain(plan, _load_catalog())
    assert len(after.todos) == 2
    assert sorted(t.tool for t in after.todos) == ["orders_collector", "revenue_total"]


def test_inserted_normalizer_has_correct_agent_and_task():
    plan = complete_dataflow_chain(_broken_review_plan(), _load_catalog())
    norm = next(t for t in plan.todos if t.tool == "review_normalizer")
    # 카탈로그상 review_normalizer 는 channel_normalizing_agent 소속, data_preprocessing
    assert norm.agent == "channel_normalizing_agent"
    assert norm.task_type == "data_preprocessing"
