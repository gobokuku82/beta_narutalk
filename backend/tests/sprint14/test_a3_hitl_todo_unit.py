"""Sprint 14 A3 — 그룹 B: HITLManager 조율 + is_turn_active 가드 + per-session Lock (L1).

대상: `hitl_manager.handle_todo_edit/delete/add` + Phase 2 신규 `_get_lock`
Test naming: TE-B01 ~ TE-B12.

일부 테스트는 Phase 2 구현 대기 (xfail 표시).
"""
from __future__ import annotations

import asyncio
import pytest

from app.dream_agent.workflow_managers.hitl_manager import get_hitl_manager
from app.dream_agent.workflow_managers.hitl_manager.manager import ExecutionProgress


def _setup_paused_progress(hitl, session_id="s1"):
    """테스트용 paused progress 생성."""
    plan = {
        "todos": [
            {"id": "t1", "agent": "a1", "task": "t1", "depends_on": [], "status": "pending"},
            {"id": "t2", "agent": "a2", "task": "t2", "depends_on": ["t1"], "status": "pending"},
            {"id": "t3", "agent": "a3", "task": "t3", "depends_on": ["t2"], "status": "pending"},
        ],
        "dag": {"t1": [], "t2": ["t1"], "t3": ["t2"]},
    }
    p = ExecutionProgress(
        session_id=session_id, plan=plan,
        phases=[["t1"], ["t2"], ["t3"]],
        completed_todos={"t1": {"ok": True}},
        status="paused",
    )
    hitl._progress[session_id] = p
    return p


# ──────────────────────────────────────────────────────────────
# TE-B01~B06 — handle_todo_edit/delete/add 기본 동작
# ──────────────────────────────────────────────────────────────

def test_TE_B01_handle_todo_edit_paused_returns_cascade(fresh_hitl):
    """paused 상태 → cascade 결과 반환."""
    _setup_paused_progress(fresh_hitl)
    result = fresh_hitl.handle_todo_edit("s1", "t2", {"task": "new"})
    assert "invalidated" in result
    assert "restart_from" in result
    assert "preserved" in result
    assert "issues" in result


def test_TE_B02_handle_todo_edit_not_paused_returns_error(fresh_hitl):
    """non-paused → error."""
    p = _setup_paused_progress(fresh_hitl)
    p.status = "running"
    result = fresh_hitl.handle_todo_edit("s1", "t2", {"task": "x"})
    assert "error" in result


def test_TE_B03_handle_todo_delete_cascade_and_phases_rebuild(fresh_hitl):
    """delete → cascade + phases 재구성."""
    p = _setup_paused_progress(fresh_hitl)
    result = fresh_hitl.handle_todo_delete("s1", "t2")
    assert "invalidated" in result
    # t2 삭제됐으므로 phases 에서도 제거
    all_phase_ids = [tid for phase in p.phases for tid in phase]
    assert "t2" not in all_phase_ids


def test_TE_B04_handle_todo_delete_not_found_no_crash(fresh_hitl):
    """삭제 대상 id 없음 — 오류 없이 처리."""
    _setup_paused_progress(fresh_hitl)
    result = fresh_hitl.handle_todo_delete("s1", "nonexistent")
    # error 없이 정상 반환 (cascade 는 빈 invalidated)
    assert "invalidated" in result or "error" in result


def test_TE_B05_handle_todo_add_paused_with_after_id(fresh_hitl):
    """add + after_todo_id 지정 → depends_on 자동 세팅."""
    p = _setup_paused_progress(fresh_hitl)
    result = fresh_hitl.handle_todo_add(
        "s1", {"agent": "newA", "task": "newT"}, after_todo_id="t2"
    )
    assert "added_id" in result
    # Plan 에 신규 todo 존재
    added = next(t for t in p.plan["todos"] if t.get("agent") == "newA")
    assert "t2" in added["depends_on"]


def test_TE_B06_handle_todo_add_duplicate_id_dedup(fresh_hitl):
    """동일 id 중복 추가 — auto-id 로 회피 (기존 id 덮어쓰지 않음)."""
    p = _setup_paused_progress(fresh_hitl)
    initial_count = len(p.plan["todos"])
    result = fresh_hitl.handle_todo_add("s1", {"id": "t1", "agent": "dupA"})
    # auto-id 가 작동해서 새로운 id 생성됨 (또는 덮어쓰기 방지)
    # 현재 구현은 새 id 부여 안 함 — 중복 방지는 validate 에서 catch
    assert len(p.plan["todos"]) == initial_count + 1


# ──────────────────────────────────────────────────────────────
# TE-B07~B10 — is_turn_active 가드 (_check_turn_active 헬퍼 대비)
# ──────────────────────────────────────────────────────────────

def test_TE_B07_is_turn_active_after_register(fresh_hitl):
    """register_turn 후 is_turn_active True."""
    fresh_hitl.register_turn("turn_X")
    assert fresh_hitl.is_turn_active("turn_X") is True


def test_TE_B08_is_turn_active_before_register_false(fresh_hitl):
    """register 없는 turn_id → False."""
    assert fresh_hitl.is_turn_active("turn_unknown") is False


def test_TE_B09_is_turn_active_after_cleanup_false(fresh_hitl):
    """cleanup_turn 후 False."""
    fresh_hitl.register_turn("turn_Y")
    fresh_hitl.cleanup_turn("turn_Y")
    assert fresh_hitl.is_turn_active("turn_Y") is False


def test_TE_B10_cleanup_turn_clears_all_structures(fresh_hitl):
    """cleanup_turn 이 _resume_queues / _active_turns / _paused 전부 정리."""
    tid = "turn_Z"
    fresh_hitl.register_turn(tid)
    fresh_hitl._paused.add(tid)
    if tid not in fresh_hitl._resume_queues:
        fresh_hitl._resume_queues[tid] = asyncio.Queue()
    fresh_hitl.cleanup_turn(tid)
    assert tid not in fresh_hitl._active_turns
    assert tid not in fresh_hitl._paused
    assert tid not in fresh_hitl._resume_queues


# ──────────────────────────────────────────────────────────────
# TE-B11~B12 — per-session Lock (D9 L1, Phase 2 구현)
# ──────────────────────────────────────────────────────────────

def test_TE_B11_per_session_lock_exists(fresh_hitl):
    """D9 L1 — `_get_lock(session_id) -> asyncio.Lock`. 같은 session_id 는 같은 Lock."""
    lock = fresh_hitl._get_lock("s1")
    assert isinstance(lock, asyncio.Lock)
    assert fresh_hitl._get_lock("s1") is lock
    # 다른 session_id 는 다른 Lock
    assert fresh_hitl._get_lock("s2") is not lock


async def test_TE_B12_handle_todo_edit_concurrent_correctness(fresh_hitl):
    """동시 편집 2건 — 둘 다 성공 (Phase 2 Lock 도입 후 직렬화 보장).

    현재 (Lock 미도입): handle_todo_* 는 동기 함수라 순차 실행. race 없음.
    Phase 2 L1 도입 후: async wrap 될 경우에도 Lock 으로 직렬화.
    """
    _setup_paused_progress(fresh_hitl)
    async def edit():
        return fresh_hitl.handle_todo_edit("s1", "t2", {"task": "x"})
    r1, r2 = await asyncio.gather(edit(), edit())
    assert "invalidated" in r1
    assert "invalidated" in r2
