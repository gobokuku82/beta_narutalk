"""I7 — hitl_manager Resume Queue 메서드 Unit 테스트

명세서: docs/_claude/checkpointer/sprint13_integration_i7_hitl_resume_queue_spec.md
대상: backend/app/dream_agent/workflow_managers/hitl_manager/manager.py
  - wait_for_resume (async)
  - signal_resume (sync)
  - cleanup_turn (sync)
  - _reset_resume_queues_for_test (sync, 테스트 전용)

8 케이스 (async Unit).
"""

import asyncio


# ──────────────────────────────────────────────────────────────────
# HQ-01 — signal 먼저, wait 나중 (Queue 버퍼링)
# ──────────────────────────────────────────────────────────────────

async def test_HQ01_signal_then_wait(fresh_hitl):
    hitl = fresh_hitl

    hitl.signal_resume("t1", {"action": "approve"})
    action = await asyncio.wait_for(hitl.wait_for_resume("t1"), timeout=1.0)

    assert action == {"action": "approve"}


# ──────────────────────────────────────────────────────────────────
# HQ-02 🔴 wait 먼저, signal 나중
# ──────────────────────────────────────────────────────────────────

async def test_HQ02_wait_then_signal(fresh_hitl):
    hitl = fresh_hitl

    async def waiter():
        return await hitl.wait_for_resume("t1")

    task = asyncio.create_task(waiter())
    try:
        await asyncio.sleep(0.01)
        assert not task.done(), "waiter는 대기 중이어야 함"

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
# HQ-03 — FIFO 순서 보장
# ──────────────────────────────────────────────────────────────────

async def test_HQ03_fifo_order(fresh_hitl):
    hitl = fresh_hitl

    hitl.signal_resume("t1", {"action": "approve"})
    hitl.signal_resume("t1", {"action": "reject"})
    hitl.signal_resume("t1", {"action": "cancel"})

    a1 = await asyncio.wait_for(hitl.wait_for_resume("t1"), timeout=1.0)
    a2 = await asyncio.wait_for(hitl.wait_for_resume("t1"), timeout=1.0)
    a3 = await asyncio.wait_for(hitl.wait_for_resume("t1"), timeout=1.0)

    assert a1["action"] == "approve"
    assert a2["action"] == "reject"
    assert a3["action"] == "cancel"


# ──────────────────────────────────────────────────────────────────
# HQ-04 — cleanup 후 Queue 제거
# ──────────────────────────────────────────────────────────────────

async def test_HQ04_cleanup_turn_removes_queue(fresh_hitl):
    hitl = fresh_hitl

    # signal_resume 내부 setdefault로 Queue 자동 생성 (W2)
    hitl.signal_resume("t1", {"action": "approve"})
    assert "t1" in hitl._resume_queues

    hitl.cleanup_turn("t1")

    assert "t1" not in hitl._resume_queues


# ──────────────────────────────────────────────────────────────────
# HQ-05 — cleanup idempotent
# ──────────────────────────────────────────────────────────────────

async def test_HQ05_cleanup_nonexistent_safe(fresh_hitl):
    hitl = fresh_hitl

    # 없는 turn_id 여러 번 — 예외 X
    hitl.cleanup_turn("never_existed")
    hitl.cleanup_turn("never_existed")

    # signal 후 cleanup + 재 cleanup
    hitl.signal_resume("t2", {"action": "x"})
    hitl.cleanup_turn("t2")
    hitl.cleanup_turn("t2")  # 이미 없어도 안전

    assert "t2" not in hitl._resume_queues


# ──────────────────────────────────────────────────────────────────
# HQ-06 🔴 turn_id 격리
# ──────────────────────────────────────────────────────────────────

async def test_HQ06_turn_id_isolation(fresh_hitl):
    hitl = fresh_hitl

    async def wait_b():
        return await hitl.wait_for_resume("turn_B")

    task_b = asyncio.create_task(wait_b())
    try:
        await asyncio.sleep(0.01)

        # turn_A에 signal — turn_B는 깨우면 안 됨
        hitl.signal_resume("turn_A", {"action": "approve"})
        await asyncio.sleep(0.01)
        assert not task_b.done(), "turn_B는 여전히 대기 중이어야 함"

        # turn_B에 signal → 깨어남
        hitl.signal_resume("turn_B", {"action": "continue"})
        result_b = await asyncio.wait_for(task_b, timeout=1.0)

        assert result_b == {"action": "continue"}
    finally:
        if not task_b.done():
            task_b.cancel()
            try:
                await task_b
            except asyncio.CancelledError:
                pass


# ──────────────────────────────────────────────────────────────────
# HQ-07 — cleanup 후 재사용 허용 (setdefault 보증)
# ──────────────────────────────────────────────────────────────────

async def test_HQ07_cleanup_then_signal_creates_new_queue(fresh_hitl):
    hitl = fresh_hitl

    hitl.signal_resume("t1", {"action": "first"})
    await asyncio.wait_for(hitl.wait_for_resume("t1"), timeout=1.0)
    hitl.cleanup_turn("t1")

    # cleanup 후 같은 turn_id 재사용 (실무에선 없지만 계약 증명)
    hitl.signal_resume("t1", {"action": "second"})
    result = await asyncio.wait_for(hitl.wait_for_resume("t1"), timeout=1.0)

    assert result == {"action": "second"}


# ──────────────────────────────────────────────────────────────────
# HQ-08 — _reset_resume_queues_for_test 동작
# ──────────────────────────────────────────────────────────────────

async def test_HQ08_reset_for_test_clears_all(fresh_hitl):
    hitl = fresh_hitl

    hitl.signal_resume("t1", {"action": "x"})
    hitl.signal_resume("t2", {"action": "y"})
    assert len(hitl._resume_queues) == 2

    hitl._reset_resume_queues_for_test()

    assert hitl._resume_queues == {}

    # 리셋 후 새 signal/wait 정상
    hitl.signal_resume("t_new", {"action": "fresh"})
    result = await asyncio.wait_for(hitl.wait_for_resume("t_new"), timeout=1.0)
    assert result == {"action": "fresh"}
