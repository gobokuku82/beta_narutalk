"""질의응답(Q&A) 카테고리 — 결정론 라우팅·등록 단위테스트 (2026-06-10).

설계: 질의응답_설계서_260610.md. cognitive 가 Q&A 에 tasks=[factual_lookup] emit →
planner 가 결정론 short-circuit 으로 qa_responder 단일 todo (LLM 팀선택 우회).
배선(enum·tool·catalog·team_catalog·hint)이 다 연결됐는지 LLM 없이 못박는다.
"""
from __future__ import annotations

import pytest

from app.dream_agent.planning.planner import Planner
from app.dream_agent.schemas.structured_query import StructuredQuery


def _sq(tasks: list[str], raw: str = "", cleaned: str = "") -> StructuredQuery:
    return StructuredQuery.model_validate({
        "targets": {},
        "goal": {"type": "answer", "output_format": "text"},
        "tasks": [{"id": t, "priority": 1} for t in tasks],
        "meta": {"raw_input": raw, "cleaned": cleaned},
    })


# ── _is_qa 신호 판별 ──

def test_is_qa_true_for_factual_lookup():
    assert Planner._is_qa(_sq(["factual_lookup"])) is True


def test_is_qa_false_for_metric():
    assert Planner._is_qa(_sq(["metric_calculation"])) is False


def test_is_qa_false_for_empty_tasks():
    # 모호(ambiguity, tasks=[]) 는 Q&A 아님 (clarification 경로) — factual_lookup 만 신호
    assert Planner._is_qa(_sq([])) is False


def test_is_qa_false_when_compound():
    # 다의도(sub_intents≥2)면 short-circuit 우회 → Stage3 가 다의도 처리 (stage2 ⒟)
    sq = StructuredQuery.model_validate({
        "targets": {}, "goal": {"type": "answer", "output_format": "text"},
        "intent": {"operation": "measure", "sub_intents": [{"operation": "measure"}, {"operation": "measure"}]},
        "tasks": [{"id": "factual_lookup", "priority": 1}], "meta": {"raw_input": "복합"},
    })
    assert Planner._is_qa(sq) is False


# ── 결정론 plan 구성 ──

def test_build_qa_plan_single_qa_responder_todo():
    plan = Planner._build_qa_plan(_sq(["factual_lookup"], raw="ROAS가 뭐야?"))
    assert [t.tool for t in plan.todos] == ["qa_responder"]
    assert plan.teams_selected == ["qa_team"]


def test_build_qa_plan_injects_question_from_raw_input():
    plan = Planner._build_qa_plan(_sq(["factual_lookup"], raw="CAC가 뭐야?"))
    assert plan.todos[0].tool_params.get("question") == "CAC가 뭐야?"


def test_build_qa_plan_falls_back_to_cleaned():
    plan = Planner._build_qa_plan(_sq(["factual_lookup"], raw="", cleaned="ROAS 정의 질문"))
    assert plan.todos[0].tool_params.get("question") == "ROAS 정의 질문"


# ── 등록 (registry · agent pool · catalog) ──

def test_qa_responder_registered_under_qa_category():
    from app.dream_agent.tools.registry import get_registry
    r = get_registry()
    assert r.exists("qa_responder")
    spec = r.get("qa_responder")
    assert spec.category.value == "qa"
    assert "answer" in spec.produces


def test_qa_responder_importable_class():
    from app.dream_agent.tools.registry import get_registry
    cls = get_registry().import_tool("qa_responder")
    assert cls.__name__ == "QaResponder"


def test_qa_responder_implemented_in_team_catalog():
    # executor 는 team_catalog 의 status=implemented 로 실재 dispatch — 미등록이면 "neither" RuntimeError.
    from app.dream_agent.execution.agent_pool import get_agent_pool
    pool = get_agent_pool()
    assert pool.is_tool_implemented("qa_agent", "qa_responder") is True
    assert pool.is_tool_stub("qa_agent", "qa_responder") is False
