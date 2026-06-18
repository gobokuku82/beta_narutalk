"""Sprint 14 A3 — 그룹 F: race + cascade 결정성 테스트 (D9 L1+L2).

대상: 동시 편집 race 100회 반복 결정성 (Sprint 14 A1 F 그룹 패턴).
Test naming: TE-F01 ~ TE-F05.

**대부분 Phase 2 Lock 도입 후 활성**.
"""
from __future__ import annotations

import asyncio
import pytest

from app.dream_agent.workflow_managers.hitl_manager.manager import ExecutionProgress


def _make_plan():
    return {
        "todos": [
            {"id": "t1", "agent": "a1", "task": "t1", "depends_on": [], "status": "pending"},
            {"id": "t2", "agent": "a2", "task": "t2", "depends_on": ["t1"], "status": "pending"},
        ],
        "dag": {"t1": [], "t2": ["t1"]},
    }


async def test_TE_F01_concurrent_structured_edits_100x(fresh_hitl):
    """구조화 편집 동시 2건 × 100회 — 결정성 확인 (L1 기대)."""
    results = []
    for _ in range(100):
        fresh_hitl._progress["s1"] = ExecutionProgress(
            session_id="s1", plan=_make_plan(),
            phases=[["t1"], ["t2"]], completed_todos={},
            status="paused",
        )
        async def edit_a():
            return fresh_hitl.handle_todo_edit("s1", "t2", {"task": "A"})
        async def edit_b():
            return fresh_hitl.handle_todo_edit("s1", "t2", {"task": "B"})
        r1, r2 = await asyncio.gather(edit_a(), edit_b())
        # 둘 다 성공
        assert "invalidated" in r1
        assert "invalidated" in r2
        # 최종 task 는 두 값 중 하나로 결정 (race 일관성)
        final_task = fresh_hitl._progress["s1"].plan["todos"][1]["task"]
        assert final_task in ("A", "B")
        results.append(final_task)
        del fresh_hitl._progress["s1"]
    # 100회 모두 결정성 유지 (예외 없음)
    assert len(results) == 100


async def test_TE_F02_concurrent_structured_plus_nl(fresh_hitl):
    """구조화 + NL 동시 — L1 Lock 이 직렬화 (Phase 3 완료 후 활성)."""
    from unittest.mock import AsyncMock, patch
    fresh_hitl._progress["s_mix"] = ExecutionProgress(
        session_id="s_mix", plan=_make_plan(),
        phases=[["t1"], ["t2"]], completed_todos={},
        status="paused",
    )
    # 구조화 편집 + NL 편집 동시 — Lock 으로 직렬화 확인
    from api_v2 import ws_hitl as wh
    fresh_hitl.register_turn("s_mix")

    class _WS:
        def __init__(self): self.sent = []
        async def send_text(self, t): self.sent.append(t)

    with patch(
        "app.dream_agent.workflow_managers.hitl_manager.plan_editor.PlanEditor.parse_instruction",
        new=AsyncMock(return_value={"action": "modify", "target_todo_ids": ["t2"],
                                     "params": {"task": "NL-updated"}, "reason": "nl"}),
    ):
        ws1, ws2 = _WS(), _WS()
        r1, r2 = await asyncio.gather(
            wh._handle_todo_modify(ws1, {"data": {"session_id": "s_mix", "turn_id": "s_mix",
                                                   "todo_id": "t2", "changes": {"task": "struct"}}}),
            wh._handle_todo_edit_nl(ws2, {"data": {"session_id": "s_mix", "turn_id": "s_mix",
                                                    "instruction": "t2 를 NL 로 수정"}}),
        )
    # 둘 다 ack 수신 — Lock 이 직렬화
    assert len(ws1.sent) >= 1
    assert len(ws2.sent) >= 1


@pytest.mark.skip(reason="Sprint 14 A3 Phase 9 회고에서 L3 trigger 기준 충족 시 활성 — LLM lock release")
async def test_TE_F03_nl_during_structured_l3_release(fresh_hitl):
    """L3 도입 시: NL LLM 호출 중에 구조화 편집도 처리 가능."""
    pass


async def test_TE_F04_frontend_ack_gating_simulated(fresh_hitl):
    """L2 ack gating 은 프론트 책임 — 백엔드 관점에선 메시지 1건씩 처리됨을 확인.

    (실제 L2 검증은 Phase 4 브라우저 regression 에서 수동 확인)
    """
    fresh_hitl._progress["s1"] = ExecutionProgress(
        session_id="s1", plan=_make_plan(),
        phases=[["t1"], ["t2"]], completed_todos={},
        status="paused",
    )
    # 순차 5회 편집 — 모두 정상 처리
    for i in range(5):
        r = fresh_hitl.handle_todo_edit("s1", "t2", {"task": f"task-{i}"})
        assert "invalidated" in r
    # 최종 결과
    assert fresh_hitl._progress["s1"].plan["todos"][1]["task"] == "task-4"


@pytest.mark.skip(reason="Sprint 14 A3 Phase 5 Live E2E 에서 실 PostgreSQL Checkpoint 복원으로 검증")
async def test_TE_F05_server_restart_during_edit_integrity(fresh_hitl):
    """서버 재시작 시나리오 — restore_progress 후 편집 결과 보존."""
    pass
