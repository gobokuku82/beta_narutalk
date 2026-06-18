"""해석 tool feeding 보강 — ensure_interpretation_fed 단위테스트 (2026-06-10, stage1 감사 B).

근거: insight_extractor/diagnoser/forecaster 는 도메인무관(consumes 미선언)이라
complete_dataflow_chain 이 metric 생산자를 못 끼움 → Stage3 가 metric 단계를 빠뜨리면
빈입력 가드로 EMPTY. 안전망: 계산 산출자 없으면 도메인 대표 metric 삽입 + 의존 배선.
"""
from __future__ import annotations

from app.dream_agent.planning.planner import (
    Plan,
    PlannedTodo,
    Planner,
    ensure_interpretation_fed,
)
from app.dream_agent.schemas.structured_query import StructuredQuery

_CATALOG = Planner()._catalog


def _sq(domain: list[str]) -> StructuredQuery:
    # period.resolved 필수 — metric 삽입은 결정론 월이 있어야 발동(없으면 미발동=degrade 유지).
    return StructuredQuery.model_validate({
        "targets": {"period": {"raw": "4월", "resolved": "2026-04"}},
        "goal": {"type": "insight", "output_format": "text"},
        "intent": {"operation": "attribute", "domain": domain},
        "tasks": [{"id": "insight_generation", "priority": 1}],
        "meta": {"raw_input": "시사점"},
    })


def test_inserts_metric_when_interpretation_starved():
    # [collector → insight] (metric 없음) → revenue_total 삽입 + insight 의존
    plan = Plan(
        todos=[
            PlannedTodo(id="c", task_type="data_collection", tool="orders_collector"),
            PlannedTodo(id="i", task_type="insight_generation", tool="insight_extractor"),
        ],
        dag={"c": [], "i": []},
    )
    out = ensure_interpretation_fed(plan, _sq(["revenue"]), _CATALOG)
    assert "revenue_total" in [t.tool for t in out.todos]
    insight = next(t for t in out.todos if t.tool == "insight_extractor")
    metric_ids = [t.id for t in out.todos if t.tool == "revenue_total"]
    assert any(mid in insight.depends_on for mid in metric_ids)


def test_ad_domain_inserts_roas():
    plan = Plan(
        todos=[
            PlannedTodo(id="c", task_type="data_collection", tool="meta_ads_performance_collector"),
            PlannedTodo(id="i", task_type="insight_generation", tool="insight_extractor"),
        ],
        dag={"c": [], "i": []},
    )
    out = ensure_interpretation_fed(plan, _sq(["ad_performance"]), _CATALOG)
    assert "roas_overall" in [t.tool for t in out.todos]


def test_no_insert_when_computed_present_but_wires_dependency():
    # 이미 metric 있으면 삽입 X, 단 insight 가 metric 에 의존하도록 배선
    plan = Plan(
        todos=[
            PlannedTodo(id="c", task_type="data_collection", tool="orders_collector"),
            PlannedTodo(id="m", task_type="metric_calculation", tool="revenue_total"),
            PlannedTodo(id="i", task_type="insight_generation", tool="insight_extractor"),
        ],
        dag={"c": [], "m": [], "i": []},
    )
    out = ensure_interpretation_fed(plan, _sq(["revenue"]), _CATALOG)
    assert [t.tool for t in out.todos].count("revenue_total") == 1   # 중복 삽입 없음
    insight = next(t for t in out.todos if t.tool == "insight_extractor")
    assert "m" in insight.depends_on


def test_noop_without_interpretation_tool():
    plan = Plan(
        todos=[PlannedTodo(id="m", task_type="metric_calculation", tool="revenue_total")],
        dag={"m": []},
    )
    out = ensure_interpretation_fed(plan, _sq(["revenue"]), _CATALOG)
    assert len(out.todos) == 1   # 해석 tool 없으면 무변경


def test_no_insert_without_resolved_period():
    # period.resolved 없으면 미발동 — metric 은 period 필수라 삽입 시 실패→halt(악화). graceful degrade 유지.
    sq = StructuredQuery.model_validate({
        "targets": {}, "goal": {"type": "insight", "output_format": "text"},
        "intent": {"operation": "attribute", "domain": ["revenue"]},
        "tasks": [{"id": "insight_generation", "priority": 1}], "meta": {"raw_input": "시사점"},
    })
    plan = Plan(
        todos=[
            PlannedTodo(id="c", task_type="data_collection", tool="orders_collector"),
            PlannedTodo(id="i", task_type="insight_generation", tool="insight_extractor"),
        ],
        dag={"c": [], "i": []},
    )
    out = ensure_interpretation_fed(plan, sq, _CATALOG)
    assert "revenue_total" not in [t.tool for t in out.todos]


def test_inserted_metric_carries_period():
    # 삽입한 metric 은 period 를 갖는다(bind_temporal 이 revenue_total drift 로 못 챙김 → 직접).
    plan = Plan(
        todos=[PlannedTodo(id="i", task_type="insight_generation", tool="insight_extractor")],
        dag={"i": []},
    )
    out = ensure_interpretation_fed(plan, _sq(["revenue"]), _CATALOG)
    metric = next(t for t in out.todos if t.tool == "revenue_total")
    assert metric.tool_params.get("period") == "2026-04"


def test_diagnoser_also_fed():
    # diagnoser 도 해석 tool — 굶으면 보강
    plan = Plan(
        todos=[
            PlannedTodo(id="c", task_type="data_collection", tool="orders_collector"),
            PlannedTodo(id="d", task_type="causal_analysis", tool="diagnoser"),
        ],
        dag={"c": [], "d": []},
    )
    out = ensure_interpretation_fed(plan, _sq(["revenue"]), _CATALOG)
    assert "revenue_total" in [t.tool for t in out.todos]
