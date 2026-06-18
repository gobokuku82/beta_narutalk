"""Sprint 14 A1 — 그룹 A: HITLManager Unit (6건)

명세: docs/_claude/sprint14_a1_hitl_timeout_plan.md §R2 그룹 A
대상: backend/app/dream_agent/workflow_managers/hitl_manager/manager.py
  - wait_for_resume(turn_id, timeout=None) — Sprint 14 timeout 인자
  - register_turn / is_turn_active — Sprint 14 신규
  - cleanup_turn 확장 — _active_turns + _paused.discard (CS-2)
"""

import asyncio
import time

import pytest


# ──────────────────────────────────────────────────────────────────
# HT-01 — timeout 도달 (put 없음) → {"action":"timeout"}
# ──────────────────────────────────────────────────────────────────

async def test_HT01_wait_for_resume_timeout_no_signal(fresh_hitl):
    hitl = fresh_hitl

    t0 = time.monotonic()
    result = await hitl.wait_for_resume("t1", timeout=0.1)
    elapsed = time.monotonic() - t0

    assert result == {"action": "timeout"}
    assert 0.08 <= elapsed <= 0.25, f"경과시간 {elapsed:.3f}s 예상 범위 밖"
    # 부작용 없음 — _active_turns / _paused 변화 없음 (Round 14 F-1)
    assert "t1" not in hitl._active_turns
    assert "t1" not in hitl._paused


# ──────────────────────────────────────────────────────────────────
# HT-02 — signal in time → 정상 action 반환, Queue 비어있음
# ──────────────────────────────────────────────────────────────────

async def test_HT02_wait_for_resume_signal_in_time(fresh_hitl):
    hitl = fresh_hitl

    async def signaler():
        await asyncio.sleep(0.05)
        hitl.signal_resume("t1", {"action": "approve"})

    signal_task = asyncio.create_task(signaler())
    try:
        t0 = time.monotonic()
        result = await hitl.wait_for_resume("t1", timeout=1.0)
        elapsed = time.monotonic() - t0

        assert result == {"action": "approve"}
        assert elapsed < 0.2, f"경과시간 {elapsed:.3f}s 너무 느림"
        # get 후 Queue 비어있음 (FIFO 소비 확인)
        assert hitl._resume_queues["t1"].qsize() == 0
    finally:
        await signal_task


# ──────────────────────────────────────────────────────────────────
# HT-03 — timeout=None 기본값 — 영원 대기 (하위 호환)
# ──────────────────────────────────────────────────────────────────

async def test_HT03_wait_for_resume_default_timeout_none(fresh_hitl):
    hitl = fresh_hitl

    async def waiter():
        return await hitl.wait_for_resume("t1")  # timeout 인자 없음

    task = asyncio.create_task(waiter())
    try:
        await asyncio.sleep(0.05)
        assert not task.done(), "timeout=None 이면 영원 대기해야 함"

        hitl.signal_resume("t1", {"action": "continue"})
        result = await asyncio.wait_for(task, timeout=1.0)
        assert result == {"action": "continue"}
    finally:
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


# ──────────────────────────────────────────────────────────────────
# HT-04 — register / is_active / cleanup 토글
# ──────────────────────────────────────────────────────────────────

async def test_HT04_register_and_cleanup_toggles(fresh_hitl):
    hitl = fresh_hitl
    assert not hitl.is_turn_active("t1")

    hitl.register_turn("t1")
    assert hitl.is_turn_active("t1")

    hitl.cleanup_turn("t1")
    assert not hitl.is_turn_active("t1")


# ──────────────────────────────────────────────────────────────────
# HT-04b — cleanup_turn 3구조 정리 + idempotent
# ──────────────────────────────────────────────────────────────────

async def test_HT04b_cleanup_turn_clears_3_structures_idempotent(fresh_hitl):
    hitl = fresh_hitl

    # 3 구조에 데이터 주입
    hitl.register_turn("t1")                          # _active_turns
    hitl.request_pause("t1")                          # _paused
    hitl.signal_resume("t1", {"action": "x"})         # _resume_queues

    assert "t1" in hitl._active_turns
    assert "t1" in hitl._paused
    assert "t1" in hitl._resume_queues

    # 1차 cleanup
    hitl.cleanup_turn("t1")
    assert "t1" not in hitl._active_turns
    assert "t1" not in hitl._paused
    assert "t1" not in hitl._resume_queues

    # 2차 cleanup idempotent (예외 X, 상태 유지)
    hitl.cleanup_turn("t1")
    assert "t1" not in hitl._active_turns
    assert "t1" not in hitl._paused
    assert "t1" not in hitl._resume_queues


# ──────────────────────────────────────────────────────────────────
# HT-04c — register_turn idempotent
# ──────────────────────────────────────────────────────────────────

async def test_HT04c_register_turn_idempotent(fresh_hitl):
    hitl = fresh_hitl

    hitl.register_turn("t1")
    hitl.register_turn("t1")  # 2회 연속
    hitl.register_turn("t1")  # 3회

    assert hitl.is_turn_active("t1")
    # set 크기 1 (idempotent)
    assert len([x for x in hitl._active_turns if x == "t1"]) == 1
