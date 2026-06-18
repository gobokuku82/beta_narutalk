"""의사결정(Decision) 카테고리 — 추천 라우팅·등록 단위테스트 (2026-06-10).

설계: 의사결정_설계서_260610.md. cognitive operation=recommend → intent_shim RECOMMENDATION
task → planner 결정론 short-circuit → recommender(ml_model mock) 단일 todo.
배선(enum·tool·intent_shim·catalog·team_catalog·hint)을 LLM 없이 못박는다.
"""
from __future__ import annotations

from app.dream_agent.cognitive.intent_shim import intent_to_tasks
from app.dream_agent.planning.planner import Planner
from app.dream_agent.schemas.structured_query import Intent, StructuredQuery, TaskType


def _sq(tasks: list[str]) -> StructuredQuery:
    return StructuredQuery.model_validate({
        "targets": {}, "goal": {"type": "answer", "output_format": "text"},
        "tasks": [{"id": t, "priority": 1} for t in tasks],
        "meta": {"raw_input": "추천 쿼리"},
    })


# ── intent_shim: recommend → RECOMMENDATION ──

def test_intent_shim_recommend_to_recommendation():
    out = intent_to_tasks(Intent(operation="recommend", domain=["ad_performance"]))
    assert [t.id for t in out] == [TaskType.RECOMMENDATION]


def test_intent_shim_recommend_priority_over_numeric():
    # recommend 는 measure 로 새지 않음
    assert [t.id for t in intent_to_tasks(Intent(operation="recommend", domain=["revenue"]))] == [TaskType.RECOMMENDATION]


# ── planner 결정론 short-circuit ──

def test_is_recommendation_true():
    assert Planner._is_recommendation(_sq(["recommendation"])) is True


def test_is_recommendation_false_for_metric():
    assert Planner._is_recommendation(_sq(["metric_calculation"])) is False


def test_is_recommendation_false_when_compound():
    # 다의도(sub_intents≥2, 예 "부진채널 찾아서 추천")면 short-circuit 우회 → Stage3 가 분석+추천 체인 (stage2 ⒟)
    sq = StructuredQuery.model_validate({
        "targets": {}, "goal": {"type": "answer", "output_format": "text"},
        "intent": {"operation": "recommend", "sub_intents": [{"operation": "measure"}, {"operation": "recommend"}]},
        "tasks": [{"id": "recommendation", "priority": 1}], "meta": {"raw_input": "찾아서 추천"},
    })
    assert Planner._is_recommendation(sq) is False


def test_build_recommendation_plan_single_recommender():
    plan = Planner._build_recommendation_plan(_sq(["recommendation"]))
    assert [t.tool for t in plan.todos] == ["recommender"]
    assert plan.teams_selected == ["decision_team"]


# ── 등록 (registry · agent pool) ──

def test_recommender_registered_under_decision_category():
    from app.dream_agent.tools.registry import get_registry
    r = get_registry()
    assert r.exists("recommender")
    spec = r.get("recommender")
    assert spec.category.value == "decision"
    assert "recommendation_text" in spec.produces


def test_recommender_importable_class():
    from app.dream_agent.tools.registry import get_registry
    assert get_registry().import_tool("recommender").__name__ == "Recommender"


def test_recommender_implemented_in_team_catalog():
    from app.dream_agent.execution.agent_pool import get_agent_pool
    pool = get_agent_pool()
    assert pool.is_tool_implemented("decision_agent", "recommender") is True
