"""Sprint 14 A1 — 그룹 F: Race 결정성 (2건, 100회 반복)

명세: docs/_claude/sprint14_a1_hitl_timeout_plan.md §R2 그룹 F
시나리오: T-3 / CS-3 / CS-4 race — 허용 결과 집합 검증
"""

import asyncio

import pytest


# ──────────────────────────────────────────────────────────────────
# HT-13 — timeout ↔ continue race, 100회 반복, 결과 2택 확인
# ──────────────────────────────────────────────────────────────────

async def test_HT13_timeout_vs_continue_race_2way_only(fresh_hitl):
    """100회: wait_for_resume(timeout=0.05) + signal_resume 0.04s → 결과 ∈ {timeout, continue}."""
    hitl = fresh_hitl
    allowed = {frozenset({"action": "timeout"}.items()), frozenset({"action": "continue"}.items())}

    outcomes: list[dict] = []
    for _ in range(100):
        hitl._reset_resume_queues_for_test()

        async def signaler():
            await asyncio.sleep(0.04)
            hitl.signal_resume("t1", {"action": "continue"})

        sig_task = asyncio.create_task(signaler())
        try:
            result = await hitl.wait_for_resume("t1", timeout=0.05)
            outcomes.append(result)
            assert frozenset(result.items()) in allowed, (
                f"race 결과 예상 밖: {result}"
            )
        finally:
            if not sig_task.done():
                sig_task.cancel()
                try:
                    await sig_task
                except asyncio.CancelledError:
                    pass

    assert len(outcomes) == 100


# ──────────────────────────────────────────────────────────────────
# HT-13b — timeout ↔ cancel race, 100회 반복
# ──────────────────────────────────────────────────────────────────

async def test_HT13b_timeout_vs_cancel_race_2way_only(fresh_hitl):
    """100회: wait_for_resume(timeout=0.05) + signal_resume(cancel) 0.04s → 결과 ∈ {timeout, cancel}."""
    hitl = fresh_hitl
    allowed = {frozenset({"action": "timeout"}.items()), frozenset({"action": "cancel"}.items())}

    outcomes: list[dict] = []
    for _ in range(100):
        hitl._reset_resume_queues_for_test()

        async def signaler():
            await asyncio.sleep(0.04)
            hitl.signal_resume("t1", {"action": "cancel"})

        sig_task = asyncio.create_task(signaler())
        try:
            result = await hitl.wait_for_resume("t1", timeout=0.05)
            outcomes.append(result)
            assert frozenset(result.items()) in allowed, (
                f"race 결과 예상 밖: {result}"
            )
        finally:
            if not sig_task.done():
                sig_task.cancel()
                try:
                    await sig_task
                except asyncio.CancelledError:
                    pass

    assert len(outcomes) == 100
