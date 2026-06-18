"""F2 subject-coherence 게이트 — 결정론적 단위테스트 (2026-06-04).

배경: cognitive 가 causal_analysis/insight_generation 라벨 시 planning 이 리뷰 파이프로
새는 누출(F2). 게이트 2겹:
  1) menu-filter (_get_agent_tools): allow_text=False 시 리뷰-데이터 tool 을 Stage3 메뉴에서 제외.
  2) post-filter (apply_subject_coherence_filter): LLM 이 Stage3 프롬프트 예시를 복사해도
     결정론적으로 리뷰-데이터 todo 제거 + DAG/deps 정리.

일반화(LLM) 테스트는 _scratch/agent_generalization_test.py 에서 routing 으로 검증.
여기선 게이트 *로직* 을 LLM 운 없이 결정론적으로 못박는다 (anti-tautological 보강).
"""
from __future__ import annotations

from app.dream_agent.planning.planner import (
    Plan,
    PlannedTodo,
    Planner,
    _collect_review_data_tool_names,
    _get_agent_tools,
    _load_catalog,
    _tool_needs_review_data,
    apply_subject_coherence_filter,
)
from app.dream_agent.schemas.structured_query import (
    Goal,
    GoalType,
    OutputFormat,
    QueryMeta,
    StructuredQuery,
    Targets,
    Task,
    TaskType,
)


def _sq(task_ids, raw="", keywords=None) -> StructuredQuery:
    return StructuredQuery(
        targets=Targets(keywords=keywords or []),
        goal=Goal(type=GoalType.METRIC, output_format=OutputFormat.TEXT),
        tasks=[Task(id=t) for t in task_ids],
        meta=QueryMeta(raw_input=raw),
    )


# ── 리뷰-데이터 tool 식별 ──

def test_tool_needs_review_data_by_artifact():
    # insight_extractor: 산출물 규칙 (sentiment_distribution/top_keywords)
    assert _tool_needs_review_data(
        {"name": "insight_extractor",
         "params_required": ["sentiment_distribution", "top_keywords"],
         "produces": ["insights"]})
    assert _tool_needs_review_data(
        {"name": "format_normalizer_text", "params_required": ["cleaned_texts"]})


def test_tool_needs_review_data_by_naming():
    # review_recent: produces 가 generic([rows,count]) → 명명 규칙으로 잡아야
    assert _tool_needs_review_data({"name": "review_recent", "produces": ["rows", "count"]})
    assert _tool_needs_review_data({"name": "sentiment_analyzer", "params_required": ["cleaned_texts"]})


def test_tool_needs_review_data_negative():
    assert not _tool_needs_review_data({"name": "revenue_total", "produces": ["revenue_total"]})
    assert not _tool_needs_review_data({"name": "mom_revenue", "params_required": ["period_a", "period_b"]})
    assert not _tool_needs_review_data({"name": "report_writer", "params_required": ["analysis_results"]})


# ── 텍스트 의도 판정 ──

def test_has_text_intent_by_task():
    assert Planner._has_text_intent(_sq([TaskType.SENTIMENT_ANALYSIS]))
    assert Planner._has_text_intent(_sq([TaskType.KEYWORD_EXTRACTION]))


def test_has_text_intent_by_subject_marker():
    assert Planner._has_text_intent(_sq([TaskType.METRIC_CALCULATION], raw="4월 리뷰 반응 어때?"))
    assert Planner._has_text_intent(_sq([TaskType.METRIC_CALCULATION], keywords=["후기"]))


def test_has_text_intent_false_for_numeric():
    assert not Planner._has_text_intent(_sq([TaskType.METRIC_CALCULATION], raw="4월 매출 얼마야?"))
    assert not Planner._has_text_intent(_sq([TaskType.CAUSAL_ANALYSIS], raw="왜 매출 늘었어?"))


# ── post-filter (핵심: LLM 이 리뷰 tool 을 복사해도 제거) ──

def _leaky_plan() -> Plan:
    # "왜 매출 늘었어?" 류에서 LLM 이 복사하는 전형: insight_extractor → report_writer
    return Plan(
        todos=[
            PlannedTodo(id="t1", task_type="data_collection", tool="orders_collector", depends_on=[]),
            PlannedTodo(id="t2", task_type="metric_calculation", tool="mom_revenue", depends_on=["t1"]),
            PlannedTodo(id="t3", task_type="insight_generation", tool="insight_extractor", depends_on=["t1"]),
            PlannedTodo(id="t4", task_type="report_generation", tool="report_writer", depends_on=["t3"]),
        ],
        dag={"t1": [], "t2": ["t1"], "t3": ["t1"], "t4": ["t3"]},
    )


def test_post_filter_drops_review_todo_and_cleans_dag():
    review_names = {"insight_extractor", "review_collector", "sentiment_analyzer"}
    out = apply_subject_coherence_filter(_leaky_plan(), review_names, allow_text=False)
    ids = {t.id for t in out.todos}
    assert ids == {"t1", "t2", "t4"}              # insight_extractor(t3) 제거
    assert "t3" not in out.dag                    # dag 키 제거
    assert all("t3" not in deps for deps in out.dag.values())  # dag 참조 제거
    t4 = next(t for t in out.todos if t.id == "t4")
    assert t4.depends_on == []                    # dangling dep(t3) 정리
    assert "subject-coherence" in out.plan_notes


def test_post_filter_noop_when_allow_text():
    # 진짜 리뷰 질문(allow_text=True) → 제거 안 함 (과차단 방지)
    out = apply_subject_coherence_filter(_leaky_plan(), {"insight_extractor"}, allow_text=True)
    assert len(out.todos) == 4


def test_post_filter_noop_when_no_review_todo():
    plan = Plan(
        todos=[PlannedTodo(id="t1", task_type="metric_calculation", tool="revenue_total", depends_on=[])],
        dag={"t1": []},
    )
    out = apply_subject_coherence_filter(plan, {"insight_extractor"}, allow_text=False)
    assert len(out.todos) == 1


# ── menu-filter + 카탈로그 집합 (실제 catalog 기반) ──

def test_menu_filter_removes_review_tools_keeps_numeric():
    catalog = _load_catalog()
    allowed = {t["name"] for t in _get_agent_tools(catalog, ["analysis_agent"], allow_text=True)["analysis_agent"]["tools"]}
    blocked = {t["name"] for t in _get_agent_tools(catalog, ["analysis_agent"], allow_text=False)["analysis_agent"]["tools"]}
    # 리뷰 전용 tool(sentiment_analyzer)은 텍스트 의도 없으면 메뉴에서 제거
    assert "sentiment_analyzer" in allowed
    assert "sentiment_analyzer" not in blocked
    # insight_extractor 는 도메인무관化(2026-06-10) → 메뉴 유지(매출 인사이트 가능)
    assert "insight_extractor" in blocked
    assert "mom_revenue" in blocked             # 숫자 비교 tool 은 유지


def test_collect_review_names_from_catalog():
    names = _collect_review_data_tool_names(_load_catalog())
    # insight_extractor 는 도메인무관化(2026-06-10)로 리뷰 전용 아님 → review_names 에서 빠짐
    assert {"review_recent", "sentiment_analyzer", "text_preprocessor"} <= names
    assert "insight_extractor" not in names
    assert "revenue_total" not in names
    assert "report_writer" not in names
