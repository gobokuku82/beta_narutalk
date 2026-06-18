"""HITL 레이어/통로 아키텍처 가설 검증 (2026-06-08).

배경: 사용자가 "HITL은 execution 전용, 다른 레이어 HITL은 재설계/3번째 통로 필요" 라고 이해.
코드+외부(langgraph 1.1.6) 검증으로 반증:
  - interrupt()는 node-agnostic (어느 레이어 노드에서든 호출 가능 — LangChain 공식 문서).
  - HITL은 이미 planning(plan_review) + execution(execution_pause) 2 레이어에서 발동.
  - resume 인프라(signal/wait)는 turn_id 키·payload 무관 → 레이어/타입별 통로 불요(2통로로 충분).

H1 resume 인프라가 turn_id 키 + payload 무관 (→ 3번째 통로 불요)
H2 HITL interrupt 가 planning + execution 2 레이어에 존재 (→ execution 전용 아님)

외부 근거:
  https://docs.langchain.com/oss/python/langgraph/interrupts
  https://reference.langchain.com/python/langgraph/types/interrupt
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from app.dream_agent.workflow_managers.hitl_manager.manager import HITLManager

_AGENT = Path(__file__).parents[1] / "app" / "dream_agent"


# ── H1: resume 인프라는 turn_id 키 + payload 무관 → 레이어/타입별 3번째 통로 불요 ──

def test_h1_resume_infra_is_turn_keyed_and_type_agnostic():
    """signal_resume/wait_for_resume 가 turn_id 로만 라우팅하고 payload 종류를 안 가린다.

    plan_review(planning) / execution_pause(execution) / data_recovery(미래·어느 레이어든)
    가 *같은* turn_id Queue 를 통해 운반됨 → interrupt 타입·발생 레이어와 무관하게 2통로로 충분.
    """
    async def _run():
        hitl = HITLManager()
        turn = "turn-x"
        payloads = [
            {"action": "approve"},          # plan_review (planning 레이어)
            {"action": "continue"},         # execution_pause (execution 레이어)
            {"action": "broaden_period"},   # data_recovery (가상 — 어느 레이어든)
        ]
        for p in payloads:
            hitl.signal_resume(turn, p)
            got = await hitl.wait_for_resume(turn, timeout=2)
            assert got == p, f"resume Queue 가 payload 를 그대로 운반해야: {p} != {got}"

        # 다른 turn_id 는 독립 채널 (격리)
        hitl.signal_resume("turn-y", {"action": "cancel"})
        assert await hitl.wait_for_resume("turn-y", timeout=2) == {"action": "cancel"}

    asyncio.run(_run())


# ── H2: HITL interrupt 가 planning + execution 2 레이어에 존재 (execution 전용 아님) ──

def test_h2_hitl_interrupt_spans_planning_and_execution():
    """plan_review interrupt 가 planning_stage 에, execution_pause interrupt 가 execution_stage 에.

    = HITL 은 'execution 전용'이 아니라 최소 2 레이어. (사용자 전제 반증)
    """
    planning = (_AGENT / "planning" / "planning_stage.py").read_text(encoding="utf-8")
    execution = (_AGENT / "execution" / "execution_stage.py").read_text(encoding="utf-8")

    assert "interrupt(" in planning and "plan_review" in planning, \
        "plan_review HITL interrupt 가 planning_stage 에 있어야 (HITL=execution 전용 반증)"
    assert "interrupt(" in execution and "execution_pause" in execution, \
        "execution_pause HITL interrupt 가 execution_stage 에 있어야"


# ── H1-보강: timeout 시 안전 반환 (무한 대기 아님) ──

def test_h1b_wait_for_resume_timeout_returns_timeout_action():
    """대기 채널에 아무도 signal 안 하면 timeout → {'action':'timeout'} (무한 블록 X).

    = 새 레이어/타입 interrupt 도 같은 타임아웃 안전망을 공유.
    """
    async def _run():
        hitl = HITLManager()
        got = await hitl.wait_for_resume("turn-none", timeout=0.2)
        assert got == {"action": "timeout"}

    asyncio.run(_run())
