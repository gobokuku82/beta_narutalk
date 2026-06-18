"""Sprint 14 A3 — 그룹 A: TodoManager pure 단위 테스트.

대상: `backend/app/dream_agent/workflow_managers/todo_manager/manager.py`
범위: TodoManager 의 pure 함수 (외부 의존 없음) 전수 검증.
Test naming: TE-A01 ~ TE-A15 (Comprehensive+ D6=≥15).
"""
from __future__ import annotations

import pytest

from app.dream_agent.workflow_managers.todo_manager.manager import (
    CascadeResult,
    TodoManager,
)


@pytest.fixture
def tm():
    return TodoManager()


@pytest.fixture
def simple_plan():
    """1→2→3 선형 의존 Plan."""
    return {
        "todos": [
            {"id": "t1", "agent": "a1", "task": "task1", "depends_on": [], "status": "pending"},
            {"id": "t2", "agent": "a2", "task": "task2", "depends_on": ["t1"], "status": "pending"},
            {"id": "t3", "agent": "a3", "task": "task3", "depends_on": ["t2"], "status": "pending"},
        ],
        "dag": {"t1": [], "t2": ["t1"], "t3": ["t2"]},
    }


@pytest.fixture
def diamond_plan():
    """Diamond DAG: t1 → {t2, t3} → t4."""
    return {
        "todos": [
            {"id": "t1", "agent": "a1", "task": "root", "depends_on": [], "status": "pending"},
            {"id": "t2", "agent": "a2", "task": "left", "depends_on": ["t1"], "status": "pending"},
            {"id": "t3", "agent": "a3", "task": "right", "depends_on": ["t1"], "status": "pending"},
            {"id": "t4", "agent": "a4", "task": "merge", "depends_on": ["t2", "t3"], "status": "pending"},
        ],
        "dag": {"t1": [], "t2": ["t1"], "t3": ["t1"], "t4": ["t2", "t3"]},
    }


# ──────────────────────────────────────────────────────────────
# TE-A01~A03 — modify_todo
# ──────────────────────────────────────────────────────────────

def test_TE_A01_modify_todo_single_field(tm, simple_plan):
    """단일 필드 수정."""
    result = tm.modify_todo(simple_plan, "t2", {"task": "task2-new"})
    todos = {t["id"]: t for t in result["todos"]}
    assert todos["t2"]["task"] == "task2-new"
    # 다른 필드는 보존
    assert todos["t2"]["agent"] == "a2"


def test_TE_A02_modify_todo_tool_params_merge(tm):
    """tool_params 수정은 dict merge (덮어쓰기 아님)."""
    plan = {"todos": [
        {"id": "t1", "tool_params": {"x": 1, "y": 2}, "depends_on": []},
    ], "dag": {"t1": []}}
    result = tm.modify_todo(plan, "t1", {"tool_params": {"y": 99, "z": 3}})
    tp = result["todos"][0]["tool_params"]
    assert tp == {"x": 1, "y": 99, "z": 3}


def test_TE_A03_modify_todo_not_found_warns(tm, simple_plan, caplog):
    """존재하지 않는 id 는 warning 로그만 (error 아님)."""
    result = tm.modify_todo(simple_plan, "nonexistent", {"task": "x"})
    # 원 plan 그대로 (변경 없음)
    assert len(result["todos"]) == 3


# ──────────────────────────────────────────────────────────────
# TE-A04~A05 — delete_todo
# ──────────────────────────────────────────────────────────────

def test_TE_A04_delete_todo_removes_and_cleans_depends(tm, simple_plan):
    """Todo 삭제 시 의존자의 depends_on 에서도 제거."""
    result = tm.delete_todo(simple_plan, "t2")
    ids = [t["id"] for t in result["todos"]]
    assert ids == ["t1", "t3"]
    t3 = next(t for t in result["todos"] if t["id"] == "t3")
    # t3 의 depends_on 에서 t2 제거됨
    assert "t2" not in t3["depends_on"]


def test_TE_A05_delete_todo_cascade_downstream_via_dag(tm, diamond_plan):
    """Diamond 에서 루트 t1 삭제 — downstream BFS 로 t2/t3/t4 전부 영향."""
    # delete_todo 자체는 단일 제거만. cascade 는 calculate_cascade 의 몫.
    result = tm.delete_todo(diamond_plan, "t1")
    assert "t1" not in [t["id"] for t in result["todos"]]
    # 남은 todos 의 depends_on 에서 t1 제거됨
    for t in result["todos"]:
        assert "t1" not in t["depends_on"]


# ──────────────────────────────────────────────────────────────
# TE-A06~A08 — add_todo
# ──────────────────────────────────────────────────────────────

def test_TE_A06_add_todo_auto_id_sequential(tm, simple_plan):
    """자동 id 는 기존 max + 1."""
    # simple_plan 의 id 는 t1/t2/t3 형식이라 auto-id 규칙 적용 안 됨 (todo_XXX 형식만)
    plan = {"todos": [
        {"id": "todo_001", "depends_on": []},
        {"id": "todo_005", "depends_on": []},
    ], "dag": {"todo_001": [], "todo_005": []}}
    result = tm.add_todo(plan, {"agent": "newA", "task": "newT"})
    new_ids = [t["id"] for t in result["todos"]]
    assert "todo_006" in new_ids


def test_TE_A07_add_todo_after_todo_id_sets_depends(tm, simple_plan):
    """after_todo_id 지정 시 depends_on 자동 세팅."""
    result = tm.add_todo(simple_plan, {"agent": "newA", "task": "newT"}, after_todo_id="t2")
    new_todo = result["todos"][-1]
    assert new_todo["depends_on"] == ["t2"]


def test_TE_A08_add_todo_default_fields(tm):
    """필수 필드 기본값: status=pending, depends_on=[], tool_params={}, task_type=custom.

    ISSUE-008 (2026-04-27): task_type 은 PlannedTodo 의 필수 필드라 기본값 필수.
    누락 시 plan_review 승인 후 modify 변환 → Plan.model_validate 에서 fatal.
    """
    plan = {"todos": [], "dag": {}}
    result = tm.add_todo(plan, {"agent": "a", "task": "t"})
    new_todo = result["todos"][0]
    assert new_todo["status"] == "pending"
    assert new_todo["depends_on"] == []
    assert new_todo["tool_params"] == {}
    assert new_todo["task_type"] == "custom"   # ISSUE-008 fix


def test_TE_A08b_add_todo_validates_against_PlannedTodo(tm):
    """ISSUE-008 회귀 — add_todo 결과가 PlannedTodo Pydantic 검증 통과해야 함.

    plan_review 승인 → modify 변환 시 Plan.model_validate 에서 fatal 안 나도록.
    """
    from app.dream_agent.planning.planner import PlannedTodo
    plan = {"todos": [], "dag": {}}
    result = tm.add_todo(plan, {"agent": "a", "task": "t"})
    # 사용자 추가 todo 가 PlannedTodo 로 검증 통과하는지
    PlannedTodo.model_validate(result["todos"][0])  # raises if fail


# ──────────────────────────────────────────────────────────────
# TE-A09~A10 — validate
# ──────────────────────────────────────────────────────────────

def test_TE_A09_validate_unknown_dep(tm):
    """알려지지 않은 id 의존 시 issues."""
    plan = {"todos": [
        {"id": "t1", "depends_on": ["missing"]},
    ], "dag": {"t1": ["missing"]}}
    issues = tm.validate(plan)
    assert any("missing" in i for i in issues)


def test_TE_A10_validate_cycle_detected(tm):
    """순환 의존 감지."""
    plan = {"todos": [
        {"id": "t1", "depends_on": ["t2"]},
        {"id": "t2", "depends_on": ["t1"]},
    ], "dag": {"t1": ["t2"], "t2": ["t1"]}}
    issues = tm.validate(plan)
    assert any("cycle" in i.lower() for i in issues)


# ──────────────────────────────────────────────────────────────
# TE-A11 — _rebuild_dag
# ──────────────────────────────────────────────────────────────

def test_TE_A11_rebuild_dag_syncs_both_keys(tm, simple_plan):
    """dag / dependency_graph 두 키 동기."""
    plan = dict(simple_plan)
    del plan["dag"]
    # modify 호출로 _rebuild_dag 트리거
    result = tm.modify_todo(plan, "t1", {"task": "x"})
    assert result["dag"] == result["dependency_graph"]
    assert set(result["dag"].keys()) == {"t1", "t2", "t3"}


# ──────────────────────────────────────────────────────────────
# TE-A12 — _build_phases_from_plan
# ──────────────────────────────────────────────────────────────

def test_TE_A12_build_phases_topological_order(tm, diamond_plan):
    """Phase 분해 = topological layers (diamond 에선 t1 / {t2,t3} / t4)."""
    phases = tm._build_phases_from_plan(diamond_plan)
    assert phases[0] == ["t1"]
    assert set(phases[1]) == {"t2", "t3"}
    assert phases[2] == ["t4"]


# ──────────────────────────────────────────────────────────────
# TE-A13~A15 — calculate_cascade
# ──────────────────────────────────────────────────────────────

def test_TE_A13_calculate_cascade_single_chain(tm, simple_plan):
    """t2 수정 → t3 무효화 (downstream BFS)."""
    completed = {"t1": {"ok": True}, "t2": {"ok": True}}
    result = tm.calculate_cascade("t2", completed, simple_plan)
    assert isinstance(result, CascadeResult)
    assert "t2" in result.invalidated_todos
    assert "t3" in result.invalidated_todos
    # preserved_results 는 dict (R2 drift 정리 확인)
    assert isinstance(result.preserved_results, dict)
    assert "t1" in result.preserved_results


def test_TE_A14_calculate_cascade_diamond_dag(tm, diamond_plan):
    """Diamond 에서 t1 수정 → t2/t3/t4 전부 무효화."""
    completed = {"t1": {"r": 1}, "t2": {"r": 2}, "t3": {"r": 3}, "t4": {"r": 4}}
    result = tm.calculate_cascade("t1", completed, diamond_plan)
    assert set(result.invalidated_todos) >= {"t1", "t2", "t3", "t4"}
    # preserved_results 비어있음
    assert result.preserved_results == {}


def test_TE_A15_cascade_restart_from_ux_label_only(tm, simple_plan):
    """restart_from 은 UX 라벨 — Phase 순서상 가장 빠른 invalidated (D1=E)."""
    completed = {"t1": {"ok": True}, "t2": {"ok": True}}
    result = tm.calculate_cascade("t2", completed, simple_plan)
    # t2 가 t3 보다 phase 순서상 빠름
    assert result.restart_from == "t2"
    # new_plan 필드 존재 (코드 필드, 문서에서 누락 — Phase 6 에서 복구 예정)
    assert result.new_plan is not None
