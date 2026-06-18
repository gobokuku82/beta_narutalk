"""CP#1 repro — 비리뷰('매출 보고서') 쿼리에 리뷰 파이프가 역주입되는 순서갬.

진단: docs/_claude/4layer_system/cp1_report_review_decoupling_diagnosis_260610.md §9

메커니즘(코드 실측):
  plan() 후처리 순서 = apply_subject_coherence_filter(:640, _build_todos 끝)  →  complete_dataflow_chain(:541)
  - 주제필터: allow_text=False 면 리뷰-데이터 todo 를 *제거*(planner.py:164).
  - dataflow: report_writer.consumes=[insights] 의 생산자가 없으면 카탈로그에서 *삽입*(planner.py:325-345).
    그런데 complete_dataflow_chain 시그니처는 (plan, catalog) — allow_text 를 *안 받는다*.
  → 매출 보고서 쿼리(allow_text=False)에서 report_writer 가 살아있으면 dataflow 가
    insight_extractor → sentiment/keyword → text_preprocessor → review_normalizer → review_collector
    전체를 되살린다 = noise #1. 주제필터가 청소한 걸 dataflow 가 다시 더럽힘(필터 재실행 안 됨).

이 테스트는 *원하는(고친 후) 동작*을 단언한다. **해소책 = insight_extractor 도메인무관化**
(2026-06-10 분석레이어 v2 '추론'): insight_extractor 가 리뷰 전용이 아니게 되어 (a) 주제필터가
안 떨구고 (b) consumes 미선언이라 dataflow 가 리뷰 생산자를 역추적하지 않음 → 리뷰 파이프 0.

Status: complete — insight_extractor 도메인무관化로 GREEN. 회귀가드.
"""
from __future__ import annotations

from app.dream_agent.planning.planner import (
    Plan,
    PlannedTodo,
    _collect_review_data_tool_names,
    _load_catalog,
    apply_subject_coherence_filter,
    complete_dataflow_chain,
)


def _clean_metric_report_plan() -> Plan:
    """'4월 매출 분석해서 보고서로 정리해줘' — 리뷰 tool 0, 순수 매출+보고서.

    LLM 이 리뷰 tool 을 *안* 넣어도 report_writer 하나로 리뷰 파이프가 주입됨을 보이는 가장 순수한 repro.
    """
    return Plan(
        teams_selected=["analysis_team"],
        todos=[
            PlannedTodo(id="t1", task_type="data_collection",
                        agent="collection_agent", tool="orders_collector", depends_on=[]),
            PlannedTodo(id="t2", task_type="metric_calculation",
                        agent="metrics_agent", tool="revenue_total", depends_on=["t1"]),
            PlannedTodo(id="t3", task_type="report_generation",
                        agent="report_agent", tool="report_writer", depends_on=["t2"]),
        ],
        dag={"t1": [], "t2": ["t1"], "t3": ["t2"]},
    )


def _leaky_metric_report_plan() -> Plan:
    """LLM 이 few-shot 에서 insight_extractor 까지 복사한 전형 — 순서갬을 명시적으로 드러냄."""
    return Plan(
        teams_selected=["analysis_team"],
        todos=[
            PlannedTodo(id="t1", task_type="data_collection",
                        agent="collection_agent", tool="orders_collector", depends_on=[]),
            PlannedTodo(id="t2", task_type="metric_calculation",
                        agent="metrics_agent", tool="revenue_total", depends_on=["t1"]),
            PlannedTodo(id="t3", task_type="insight_generation",
                        agent="analysis_agent", tool="insight_extractor", depends_on=["t1"]),
            PlannedTodo(id="t4", task_type="report_generation",
                        agent="report_agent", tool="report_writer", depends_on=["t3"]),
        ],
        dag={"t1": [], "t2": ["t1"], "t3": ["t1"], "t4": ["t3"]},
    )


def _post_llm_sequence(plan: Plan, allow_text: bool) -> Plan:
    """plan() 의 실제 후처리 순서 재현: 주제필터 → dataflow 완성."""
    catalog = _load_catalog()
    review_names = _collect_review_data_tool_names(catalog)
    plan = apply_subject_coherence_filter(plan, review_names, allow_text)
    plan = complete_dataflow_chain(plan, catalog)
    return plan


def _review_tools_in(plan: Plan) -> list[str]:
    review_names = _collect_review_data_tool_names(_load_catalog())
    return sorted({t.tool for t in plan.todos if t.tool in review_names})


def test_cp1_clean_metric_report_excludes_review_pipe():
    """매출+보고서(allow_text=False)는 리뷰 파이프가 0이어야 한다.

    insight_extractor 도메인무관化 후 GREEN: report_writer.consumes=[insights] → producer
    insight_extractor 가 back-fill 되나, insight_extractor.consumes 미선언이라 리뷰 체인을
    역추적하지 않음 → review_collector/normalizer/sentiment/keyword/preprocessor 0.
    """
    plan = _post_llm_sequence(_clean_metric_report_plan(), allow_text=False)
    leaked = _review_tools_in(plan)
    assert leaked == [], f"매출 쿼리에 리뷰 파이프 누수: {leaked}"


def test_cp1_insight_extractor_domain_agnostic_no_review_pipe():
    """insight_extractor 도메인무관化 후: 매출+insight+보고서 plan(allow_text=False)에서
    insight_extractor 는 *살아남고*(리뷰 전용 아님) 리뷰 파이프는 주입되지 않는다.

    구(리뷰 고정): 필터가 insight_extractor 떨굼 → dataflow 가 report_writer.consumes 로 리뷰 체인 역주입.
    현(도메인무관): insight_extractor 가 리뷰-데이터 tool 이 아니라 필터에 안 걸리고, consumes 미선언이라
    dataflow 가 리뷰 생산자를 끌어오지 않음 → CP#1 해소 + insight 는 metric 으로 해석.
    """
    catalog = _load_catalog()
    review_names = _collect_review_data_tool_names(catalog)
    filtered = apply_subject_coherence_filter(_leaky_metric_report_plan(), review_names, allow_text=False)
    # insight_extractor 는 도메인무관 → 필터에 안 걸리고 생존
    assert "insight_extractor" in {t.tool for t in filtered.todos}, "도메인무관 insight 는 제거되면 안 됨"
    completed = complete_dataflow_chain(filtered, catalog)
    # 리뷰 파이프(collector/normalizer/sentiment/keyword/preprocessor)는 0
    leaked = _review_tools_in(completed)
    assert leaked == [], f"매출 쿼리에 리뷰 파이프 누수: {leaked}"
