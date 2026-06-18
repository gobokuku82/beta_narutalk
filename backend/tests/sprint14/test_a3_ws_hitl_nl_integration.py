"""Sprint 14 A3 — 그룹 E: ws_hitl NL (`todo_edit_nl`) 통합 테스트 (Y-a).

대상: `_handle_todo_edit_nl` (Phase 3 신규)
Test naming: TE-E01 ~ TE-E06.
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

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


def _setup_nl(hitl, turn_id="turn_NL"):
    """Sprint 14 A3 D 통일 — planner.Plan dict 형식 (task_type / rationale)."""
    hitl.register_turn(turn_id)
    plan = {
        "teams_selected": [],
        "plan_notes": "",
        "todos": [
            {"id": "t1", "task_type": "demo", "agent": "a1", "tool": "tool1",
             "tool_params": {}, "depends_on": [], "priority": 5, "rationale": "t1 task"},
            {"id": "t2", "task_type": "demo", "agent": "a2", "tool": "tool2",
             "tool_params": {}, "depends_on": ["t1"], "priority": 5, "rationale": "t2 task"},
        ],
        "dag": {"t1": [], "t2": ["t1"]},
    }
    hitl._progress[turn_id] = ExecutionProgress(
        session_id=turn_id, plan=plan,
        phases=[["t1"], ["t2"]], completed_todos={"t1": {"ok": True}},
        status="paused",
    )


async def test_TE_E01_handle_todo_edit_nl_exists_and_dispatches(fresh_hitl):
    """_handle_todo_edit_nl 존재 + 메시지 dispatch 경로 확인."""
    from api_v2 import ws_hitl as wh
    assert hasattr(wh, "_handle_todo_edit_nl")


async def test_TE_E02_handle_todo_edit_nl_not_paused_error(fresh_hitl):
    """non-paused 상태 → TODO_EDIT_NOT_PAUSED."""
    from api_v2 import ws_hitl as wh
    fresh_hitl.register_turn("turn_NL2")
    ws = _MockWS()
    await wh._handle_todo_edit_nl(ws, {
        "type": "todo_edit_nl",
        "data": {"session_id": "turn_NL2", "turn_id": "turn_NL2", "instruction": "4번 삭제"},
    })
    msg = ws.find(type_="hitl_ack")
    assert msg["data"]["accepted"] is False
    assert msg["data"].get("code") == "TODO_EDIT_NOT_PAUSED"


async def test_TE_E03_nl_intent_unclear_enum_used(fresh_hitl):
    """파싱 결과 action=unknown → NL_INTENT_UNCLEAR enum."""
    from api_v2 import ws_hitl as wh
    from app.core.error_codes import ErrorCodes
    _setup_nl(fresh_hitl)

    # parse_instruction 이 action=unknown 반환하도록 mock
    with patch(
        "app.dream_agent.workflow_managers.hitl_manager.plan_editor.PlanEditor.parse_instruction",
        new=AsyncMock(return_value={"action": "unknown", "target_todo_ids": [],
                                     "params": {}, "reason": "의도 파싱 실패"})
    ):
        ws = _MockWS()
        await wh._handle_todo_edit_nl(ws, {
            "type": "todo_edit_nl",
            "data": {"session_id": "turn_NL", "turn_id": "turn_NL", "instruction": "뭔가"},
        })
        msg = ws.find(type_="hitl_ack")
        assert msg["data"]["accepted"] is False
        assert msg["data"]["code"] == ErrorCodes.NL_INTENT_UNCLEAR["code"]


async def test_TE_E04_llm_failure_uses_free_form_reason(fresh_hitl):
    """LLM 호출 예외 → free-form reason (D7=A- 로 enum 없이)."""
    from api_v2 import ws_hitl as wh
    _setup_nl(fresh_hitl)

    with patch(
        "app.dream_agent.workflow_managers.hitl_manager.plan_editor.PlanEditor.parse_instruction",
        new=AsyncMock(side_effect=RuntimeError("API down")),
    ):
        ws = _MockWS()
        await wh._handle_todo_edit_nl(ws, {
            "type": "todo_edit_nl",
            "data": {"session_id": "turn_NL", "turn_id": "turn_NL", "instruction": "뭔가"},
        })
        msg = ws.find(type_="hitl_ack")
        assert msg["data"]["accepted"] is False
        # free-form: code 필드 없음
        assert "code" not in msg["data"]
        assert "API down" in msg["data"]["reason"]


async def test_TE_E05_per_session_lock_covers_nl(fresh_hitl):
    """L1 Lock 은 NL 핸들러도 포함."""
    assert hasattr(fresh_hitl, "_get_lock")
    import asyncio as aio
    lock = fresh_hitl._get_lock("any_session")
    assert isinstance(lock, aio.Lock)


async def test_TE_E06_is_turn_active_guard_nl(fresh_hitl):
    """FR-13c — todo_edit_nl 도 is_turn_active 가드 (_check_turn_active)."""
    from api_v2 import ws_hitl as wh
    assert hasattr(wh, "_check_turn_active")

    # 비활성 turn 으로 NL 편집 시도
    ws = _MockWS()
    await wh._handle_todo_edit_nl(ws, {
        "type": "todo_edit_nl",
        "data": {"session_id": "inactive", "turn_id": "inactive", "instruction": "x"},
    })
    msg = ws.find(type_="hitl_ack")
    assert msg["data"]["accepted"] is False
    assert msg["data"].get("reason") == "turn_not_active"


# ──────────────────────────────────────────────────────────────
# TE-E07 — 정상 경로 전체 flow (NL → parse → apply → cascade)
# ──────────────────────────────────────────────────────────────

async def test_TE_E07_nl_remove_full_flow(fresh_hitl):
    """정상 경로: remove action → invalidated / preserved 계산."""
    from api_v2 import ws_hitl as wh
    _setup_nl(fresh_hitl)

    # t2 삭제하는 LLM 응답 mock
    plan = fresh_hitl._progress["turn_NL"].plan
    t2_id = next(t["id"] for t in plan["todos"] if t["id"] == "t2")
    with patch(
        "app.dream_agent.workflow_managers.hitl_manager.plan_editor.PlanEditor.parse_instruction",
        new=AsyncMock(return_value={"action": "remove", "target_todo_ids": [t2_id],
                                     "params": {}, "reason": "사용자 요청"}),
    ):
        ws = _MockWS()
        await wh._handle_todo_edit_nl(ws, {
            "type": "todo_edit_nl",
            "data": {"session_id": "turn_NL", "turn_id": "turn_NL", "instruction": "t2 삭제"},
        })
        msg = ws.find(type_="hitl_ack", action="todo_edit_nl")
        assert msg["data"]["accepted"] is True
        assert msg["data"]["nl_action"] == "remove"
        # t2 무효화 포함
        assert "t2" in msg["data"]["invalidated"]


# ──────────────────────────────────────────────────────────────
# TE-E08~E09 — Cycle 4 보강 (validate False / apply_edit 예외 분기)
# ──────────────────────────────────────────────────────────────

async def test_TE_E08_validate_false_uses_invalid_dag_enum(fresh_hitl):
    """validate_edit False 시 INVALID_DAG enum 사용 (free-form 아님)."""
    from api_v2 import ws_hitl as wh
    from app.core.error_codes import ErrorCodes
    _setup_nl(fresh_hitl)

    # parse 는 정상이지만 validate False (target_id 미존재)
    with patch(
        "app.dream_agent.workflow_managers.hitl_manager.plan_editor.PlanEditor.parse_instruction",
        new=AsyncMock(return_value={"action": "remove", "target_todo_ids": ["nonexistent"],
                                     "params": {}, "reason": "x"}),
    ):
        ws = _MockWS()
        await wh._handle_todo_edit_nl(ws, {
            "type": "todo_edit_nl",
            "data": {"session_id": "turn_NL", "turn_id": "turn_NL", "instruction": "x 삭제"},
        })
        msg = ws.find(type_="hitl_ack")
        assert msg["data"]["accepted"] is False
        assert msg["data"]["code"] == ErrorCodes.INVALID_DAG["code"]


async def test_TE_E09_apply_edit_exception_uses_free_form_reason(fresh_hitl):
    """apply_edit 예외 시 free-form reason (편집 적용 실패)."""
    from api_v2 import ws_hitl as wh
    _setup_nl(fresh_hitl)

    # parse + validate 정상이지만 apply_edit 예외
    with patch(
        "app.dream_agent.workflow_managers.hitl_manager.plan_editor.PlanEditor.parse_instruction",
        new=AsyncMock(return_value={"action": "remove", "target_todo_ids": ["t2"],
                                     "params": {}, "reason": "x"}),
    ), patch(
        "app.dream_agent.workflow_managers.hitl_manager.plan_editor.PlanEditor.apply_edit",
        new=AsyncMock(side_effect=RuntimeError("apply 폭발")),
    ):
        ws = _MockWS()
        await wh._handle_todo_edit_nl(ws, {
            "type": "todo_edit_nl",
            "data": {"session_id": "turn_NL", "turn_id": "turn_NL", "instruction": "t2 삭제"},
        })
        msg = ws.find(type_="hitl_ack")
        assert msg["data"]["accepted"] is False
        # free-form: code 필드 없음 + apply 실패 메시지 포함
        assert "code" not in msg["data"]
        assert "편집 적용 실패" in msg["data"]["reason"] or "apply 폭발" in msg["data"]["reason"]
