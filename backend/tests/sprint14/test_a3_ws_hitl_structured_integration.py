"""Sprint 14 A3 — 그룹 C: ws_hitl structured 3핸들러 통합 테스트.

대상: `_handle_todo_modify/delete/add` + B1~B5 가드/스키마/silent fail 수정
Test naming: TE-C01 ~ TE-C10.

대부분 Phase 2 구현 대기 (xfail).
"""
from __future__ import annotations

import asyncio
import json
import pytest

from api_v2 import ws_hitl as wh
from app.dream_agent.workflow_managers.hitl_manager import get_hitl_manager


class _MockWS:
    """간단한 WebSocket mock — send_text 캡처."""
    def __init__(self):
        self.sent = []
    async def send_text(self, text):
        self.sent.append(json.loads(text))
    def last(self):
        return self.sent[-1] if self.sent else None
    def find(self, type_=None, action=None):
        for m in self.sent:
            if type_ and m.get("type") != type_:
                continue
            if action and m.get("data", {}).get("action") != action:
                continue
            return m
        return None


def _setup(hitl, turn_id="turn_C", session_id="turn_C"):
    """Paused progress + active turn 세팅 (turn_id == session_id 가정)."""
    from app.dream_agent.workflow_managers.hitl_manager.manager import ExecutionProgress
    plan = {
        "todos": [
            {"id": "t1", "agent": "a1", "task": "t1", "depends_on": [], "status": "pending"},
            {"id": "t2", "agent": "a2", "task": "t2", "depends_on": ["t1"], "status": "pending"},
        ],
        "dag": {"t1": [], "t2": ["t1"]},
    }
    hitl._progress[session_id] = ExecutionProgress(
        session_id=session_id, plan=plan,
        phases=[["t1"], ["t2"]],
        completed_todos={"t1": {"ok": True}},
        status="paused",
    )
    hitl.register_turn(turn_id)


# ──────────────────────────────────────────────────────────────
# TE-C01~C04 — 핸들러 기본 동작 (pause 분기)
# ──────────────────────────────────────────────────────────────

async def test_TE_C01_handle_todo_modify_pause_branch_returns_ack(fresh_hitl):
    _setup(fresh_hitl)
    ws = _MockWS()
    await wh._handle_todo_modify(ws, {
        "type": "todo_modify",
        "data": {"session_id": "turn_C", "turn_id": "turn_C", "todo_id": "t2",
                 "changes": {"task": "new"}},
    })
    msg = ws.find(type_="hitl_ack", action="todo_modify")
    assert msg is not None
    # Phase 2 B2: accepted 필드 존재 예정
    # 현재는 누락 가능 — xfail 로 검증 (아래 C02)


async def test_TE_C02_handle_todo_delete_pause_branch_cascade_in_ack(fresh_hitl):
    _setup(fresh_hitl)
    ws = _MockWS()
    await wh._handle_todo_delete(ws, {
        "type": "todo_delete",
        "data": {"session_id": "turn_C", "turn_id": "turn_C", "todo_id": "t2"},
    })
    msg = ws.find(type_="hitl_ack", action="todo_delete")
    assert msg is not None
    assert "invalidated" in msg["data"]


async def test_TE_C03_handle_todo_add_pause_branch(fresh_hitl):
    _setup(fresh_hitl)
    ws = _MockWS()
    await wh._handle_todo_add(ws, {
        "type": "todo_add",
        "data": {"session_id": "turn_C", "turn_id": "turn_C",
                 "new_todo": {"agent": "newA", "task": "newT"}},
    })
    msg = ws.find(type_="hitl_ack", action="todo_add")
    assert msg is not None


async def test_TE_C04_handle_todo_missing_session_id_returns_error(fresh_hitl):
    _setup(fresh_hitl)
    ws = _MockWS()
    await wh._handle_todo_modify(ws, {
        "type": "todo_modify",
        "data": {"todo_id": "t2", "changes": {"task": "x"}},  # session_id 누락
    })
    msg = ws.sent[-1]
    assert msg["type"] == "error"


# ──────────────────────────────────────────────────────────────
# TE-C05 — B2 hitl_ack accepted:true (Phase 2 구현 대기)
# ──────────────────────────────────────────────────────────────

async def test_TE_C05_hitl_ack_has_accepted_true_on_success(fresh_hitl):
    _setup(fresh_hitl)
    ws = _MockWS()
    await wh._handle_todo_modify(ws, {
        "type": "todo_modify",
        "data": {"session_id": "turn_C", "turn_id": "turn_C", "todo_id": "t2",
                 "changes": {"task": "x"}},
    })
    msg = ws.find(type_="hitl_ack")
    assert msg["data"].get("accepted") is True


# ──────────────────────────────────────────────────────────────
# TE-C06~C08 — B5 입력 검증 (Phase 2 구현 대기)
# ──────────────────────────────────────────────────────────────

async def test_TE_C06_input_validation_empty_changes(fresh_hitl):
    _setup(fresh_hitl)
    ws = _MockWS()
    await wh._handle_todo_modify(ws, {
        "type": "todo_modify",
        "data": {"session_id": "turn_C", "turn_id": "turn_C", "todo_id": "t2",
                 "changes": {}},
    })
    msg = ws.sent[-1]
    # 빈 changes → INVALID_MESSAGE
    assert msg["type"] == "error" or msg["data"].get("accepted") is False


async def test_TE_C07_input_validation_new_todo_missing_required(fresh_hitl):
    _setup(fresh_hitl)
    ws = _MockWS()
    await wh._handle_todo_add(ws, {
        "type": "todo_add",
        "data": {"session_id": "turn_C", "turn_id": "turn_C",
                 "new_todo": {}},  # agent/task 누락
    })
    msg = ws.sent[-1]
    assert msg["type"] == "error" or msg["data"].get("accepted") is False


async def test_TE_C08_input_validation_missing_todo_id(fresh_hitl):
    _setup(fresh_hitl)
    ws = _MockWS()
    await wh._handle_todo_delete(ws, {
        "type": "todo_delete",
        "data": {"session_id": "turn_C", "turn_id": "turn_C"},
    })
    msg = ws.sent[-1]
    assert msg["type"] == "error"


# ──────────────────────────────────────────────────────────────
# TE-C09 — B1 is_turn_active 가드 (Phase 2 구현 대기)
# ──────────────────────────────────────────────────────────────

async def test_TE_C09_turn_not_active_returns_ack_accepted_false(fresh_hitl):
    """비활성 turn 에 todo_modify 시 hitl_ack accepted=false + reason=turn_not_active."""
    _setup(fresh_hitl)
    fresh_hitl.cleanup_turn("turn_C")  # 비활성화
    ws = _MockWS()
    await wh._handle_todo_modify(ws, {
        "type": "todo_modify",
        "data": {"session_id": "turn_C", "turn_id": "turn_C", "todo_id": "t2",
                 "changes": {"task": "x"}},
    })
    msg = ws.find(type_="hitl_ack")
    assert msg["data"].get("accepted") is False
    assert msg["data"].get("reason") == "turn_not_active"


# ──────────────────────────────────────────────────────────────
# TE-C10 — B4 plan_review 분기 silent fail 수정 (Phase 2 구현 대기)
# ──────────────────────────────────────────────────────────────

async def test_TE_C10_plan_review_request_none_explicit_error(fresh_hitl):
    """plan_review 분기에서 pending_request 없을 때 silent 아닌 명시적 에러."""
    # progress 없음 → plan_review 분기 진입
    fresh_hitl.register_turn("turn_PR")
    ws = _MockWS()
    await wh._handle_todo_modify(ws, {
        "type": "todo_modify",
        "data": {"session_id": "turn_PR", "turn_id": "turn_PR", "todo_id": "t2",
                 "changes": {"task": "x"}},
    })
    msg = ws.sent[-1]
    # Phase 2 B4: TODO_EDIT_NOT_PAUSED + reason=plan_review_expired 기대
    assert msg["data"].get("accepted") is False
    assert msg["data"].get("code") == "TODO_EDIT_NOT_PAUSED"
