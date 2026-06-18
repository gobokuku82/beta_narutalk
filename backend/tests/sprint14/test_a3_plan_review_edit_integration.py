"""Sprint 14 A3 Phase 5 — 그룹 H: Plan review 편집 통합 테스트.

사용자 §9 "hitl/pause 는 같은 개념" → plan_review 에서도 편집 가능.
구현 경로 (옵션 1 — 임시 progress):
  1. ws_agent `_graph_runner_with_resume` 의 plan_review 분기에서 `create_progress` + `status="paused"`.
  2. ws_hitl `_handle_todo_{modify|delete}` 의 plan_review 분기 제거 → 단일 pause 경로.
  3. ws_hitl `_handle_hitl_response` approve + progress 존재 시 `{action:"modify", value:progress.plan}` 로 변환.
  4. `cleanup_turn` 에 `_progress.pop` 추가 (leak 방지).

Test naming: TE-H01 ~ TE-H08.
"""
from __future__ import annotations

import json

import pytest

from api_v2 import ws_hitl as wh
from app.dream_agent.workflow_managers.hitl_manager.manager import ExecutionProgress


class _MockWS:
    def __init__(self):
        self.sent = []

    async def send_text(self, text):
        self.sent.append(json.loads(text))

    def find(self, type_=None, action=None):
        for m in self.sent:
            if type_ and m.get("type") != type_:
                continue
            if action and m.get("data", {}).get("action") != action:
                continue
            return m
        return None


def _plan_review_progress(hitl, turn_id="turn_H"):
    """plan_review 진입 시 ws_agent 가 만드는 임시 progress 모사.

    특징:
      - completed_todos 비어있음 (실행 전)
      - status="paused" (편집 가능)
      - phases 는 plan 기반 빌드
    """
    plan = {
        "teams_selected": [],
        "plan_notes": "",
        "todos": [
            {"id": "t1", "task_type": "demo", "agent": "a1", "tool": "mock",
             "tool_params": {}, "depends_on": [], "priority": 5, "rationale": "t1"},
            {"id": "t2", "task_type": "demo", "agent": "a2", "tool": "mock",
             "tool_params": {}, "depends_on": ["t1"], "priority": 5, "rationale": "t2"},
            {"id": "t3", "task_type": "demo", "agent": "a3", "tool": "mock",
             "tool_params": {}, "depends_on": ["t2"], "priority": 5, "rationale": "t3"},
        ],
        "dag": {"t1": [], "t2": ["t1"], "t3": ["t2"]},
    }
    hitl._progress[turn_id] = ExecutionProgress(
        session_id=turn_id,
        plan=plan,
        phases=[["t1"], ["t2"], ["t3"]],
        completed_todos={},
        status="paused",
    )
    hitl.register_turn(turn_id)


# ──────────────────────────────────────────────────────────────
# TE-H01 — plan_review 임시 progress 계약
# ──────────────────────────────────────────────────────────────

async def test_TE_H01_plan_review_temp_progress_is_paused_with_empty_completed(
    fresh_hitl,
):
    """ws_agent plan_review 분기가 만드는 임시 progress 계약:
    - status="paused"
    - completed_todos={}
    → 편집 경로가 정상 동작하는 상태.
    """
    _plan_review_progress(fresh_hitl)
    p = fresh_hitl.get_progress("turn_H")
    assert p is not None
    assert p.status == "paused"
    assert p.completed_todos == {}
    assert len(p.plan["todos"]) == 3


# ──────────────────────────────────────────────────────────────
# TE-H02~H04 — plan_review 상태에서 구조화/NL 편집 모두 단일 경로
# ──────────────────────────────────────────────────────────────

async def test_TE_H02_plan_review_todo_delete_via_pause_branch(fresh_hitl):
    """plan_review 에서 todo_delete → _handle_todo_delete 가 pause 분기로 처리 + progress.plan 에서 해당 todo 제거."""
    _plan_review_progress(fresh_hitl)
    ws = _MockWS()
    await wh._handle_todo_delete(ws, {
        "type": "todo_delete",
        "data": {
            "session_id": "turn_H",
            "turn_id": "turn_H",
            "todo_id": "t2",
        },
    })
    msg = ws.find(type_="hitl_ack", action="todo_delete")
    assert msg is not None
    assert msg["data"]["accepted"] is True

    # progress.plan 에서 t2 삭제됨
    plan = msg["data"]["plan"]
    ids = [t["id"] for t in plan["todos"]]
    assert "t2" not in ids
    # cascade 는 downstream 을 invalidated 로 반환 (completed_todos 비어있어도 동일).
    # plan_review 단계에서도 "영향 받는 Todo" 시각화 의미는 유지 — UI 에서 🔴 tint + ⛓ 라벨 표시.
    invalidated = msg["data"].get("invalidated", [])
    assert "t2" in invalidated
    assert "t3" in invalidated   # t2 의 downstream 포함
    # ISSUE-005 fix (2026-04-27): restart_from 필드 ack 에 포함되어야 UI 가 ⛓ 라벨 표시 가능
    assert "restart_from" in msg["data"]
    assert msg["data"]["restart_from"] is not None


async def test_TE_H03_plan_review_todo_modify_via_pause_branch(fresh_hitl):
    """plan_review 에서 todo_modify → _handle_todo_modify 가 pause 분기로 처리 + progress.plan 반영."""
    _plan_review_progress(fresh_hitl)
    ws = _MockWS()
    await wh._handle_todo_modify(ws, {
        "type": "todo_modify",
        "data": {
            "session_id": "turn_H",
            "turn_id": "turn_H",
            "todo_id": "t2",
            "changes": {"task": "edited_task"},
        },
    })
    msg = ws.find(type_="hitl_ack", action="todo_modify")
    assert msg is not None
    assert msg["data"]["accepted"] is True
    # plan 에 수정 반영
    edited = next(t for t in msg["data"]["plan"]["todos"] if t["id"] == "t2")
    assert edited["task"] == "edited_task"


async def test_TE_H04_plan_review_todo_edit_nl_via_pause_branch(
    fresh_hitl, monkeypatch,
):
    """plan_review 에서 todo_edit_nl → pause 분기로 처리 (pause 상태 체크 통과).
    plan_editor 는 mock — NL 파싱 로직이 아니라 편집 경로 통합만 검증.
    """
    # Sprint 14 A3 D 통일 — planner.Plan / PlannedTodo 사용, apply_edit 단일 반환
    from app.dream_agent.workflow_managers.hitl_manager import plan_editor as pe_mod

    _plan_review_progress(fresh_hitl)

    class _FakeEditor:
        async def parse_instruction(self, instruction, plan):
            return {"action": "remove", "target_todo_ids": ["t2"], "reason": "ok"}

        async def validate_edit(self, plan, parsed):
            return True, []

        async def apply_edit(self, plan, parsed, instruction):
            new_todos = [t for t in plan.todos if t.id != "t2"]
            new_plan = plan.model_copy(update={"todos": new_todos})
            return new_plan  # D 통일 — 단일 반환 (PlanChange 폐기)

    monkeypatch.setattr(pe_mod, "PlanEditor", _FakeEditor)

    ws = _MockWS()
    await wh._handle_todo_edit_nl(ws, {
        "type": "todo_edit_nl",
        "data": {
            "session_id": "turn_H",
            "turn_id": "turn_H",
            "instruction": "t2 제거",
        },
    })
    msg = ws.find(type_="hitl_ack", action="todo_edit_nl")
    assert msg is not None
    assert msg["data"]["accepted"] is True
    assert msg["data"]["nl_action"] == "remove"


# ──────────────────────────────────────────────────────────────
# TE-H05~H07 — approve 시 modify 변환 / reject 보존 / legacy 공존
# ──────────────────────────────────────────────────────────────

async def test_TE_H05_approve_with_progress_signals_modify_with_edited_plan(
    fresh_hitl, monkeypatch,
):
    """plan_review 편집 후 approve → signal_resume 가 {action:"modify", value:progress.plan} 전송.
    planning_stage L88-92 modify 분기가 edited plan 으로 교체.
    """
    _plan_review_progress(fresh_hitl)
    # 편집 모사: plan 에서 t2 제거
    fresh_hitl._progress["turn_H"].plan["todos"] = [
        t for t in fresh_hitl._progress["turn_H"].plan["todos"] if t["id"] != "t2"
    ]
    captured: list[dict] = []
    monkeypatch.setattr(
        fresh_hitl,
        "signal_resume",
        lambda turn_id, action: captured.append({"turn_id": turn_id, "action": action}),
    )

    ws = _MockWS()
    await wh._handle_hitl_response(ws, {
        "type": "hitl_response",
        "data": {
            "request_id": "req_x",
            "turn_id": "turn_H",
            "action": "approve",
        },
    })

    assert len(captured) == 1
    signaled = captured[0]["action"]
    assert signaled["action"] == "modify"   # approve → modify 변환
    assert signaled["value"] is not None
    assert "t2" not in [t["id"] for t in signaled["value"]["todos"]]
    # request_resume 호출로 status 가 running 으로 복귀
    assert fresh_hitl.get_progress("turn_H").status == "running"


async def test_TE_H06_approve_without_progress_keeps_original_action(
    fresh_hitl, monkeypatch,
):
    """progress 없음 (legacy `_run_agent` 경로 등) → approve 는 변환 없이 원래대로."""
    fresh_hitl.register_turn("turn_H")
    captured: list[dict] = []
    monkeypatch.setattr(
        fresh_hitl,
        "signal_resume",
        lambda turn_id, action: captured.append({"turn_id": turn_id, "action": action}),
    )

    ws = _MockWS()
    await wh._handle_hitl_response(ws, {
        "type": "hitl_response",
        "data": {
            "request_id": "req_x",
            "turn_id": "turn_H",
            "action": "approve",
        },
    })

    assert len(captured) == 1
    assert captured[0]["action"] == {"action": "approve", "value": None}


async def test_TE_H07_reject_never_converted_to_modify(
    fresh_hitl, monkeypatch,
):
    """progress 존재해도 reject 는 변환 안 됨 — 사용자가 거부한 plan 을 실행하면 안 됨."""
    _plan_review_progress(fresh_hitl)
    captured: list[dict] = []
    monkeypatch.setattr(
        fresh_hitl,
        "signal_resume",
        lambda turn_id, action: captured.append({"turn_id": turn_id, "action": action}),
    )

    ws = _MockWS()
    await wh._handle_hitl_response(ws, {
        "type": "hitl_response",
        "data": {
            "request_id": "req_x",
            "turn_id": "turn_H",
            "action": "reject",
        },
    })

    assert len(captured) == 1
    assert captured[0]["action"] == {"action": "reject", "value": None}


# ──────────────────────────────────────────────────────────────
# TE-H08 — cleanup_turn 이 _progress leak 방지
# ──────────────────────────────────────────────────────────────

async def test_TE_H08_cleanup_turn_pops_progress(fresh_hitl):
    """run_turn finally 의 cleanup_turn 이 임시 progress 포함 _progress 제거 — leak 방지."""
    _plan_review_progress(fresh_hitl)
    assert fresh_hitl.get_progress("turn_H") is not None

    fresh_hitl.cleanup_turn("turn_H")

    assert fresh_hitl.get_progress("turn_H") is None
    assert "turn_H" not in fresh_hitl._active_turns
    assert "turn_H" not in fresh_hitl._paused
