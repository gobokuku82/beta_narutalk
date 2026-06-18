"""Sprint 14 A1 — 그룹 E: resume_query 재진입 (1건)

명세: docs/_claude/sprint14_a1_hitl_timeout_plan.md §R2 그룹 E
"""

import pytest

from backend.tests.sprint13.test_resume_loop_unit import (
    MockAgentWithInterrupt,
    MockWebSocket,
)


@pytest.fixture
def mock_ws_u1(reset_conn_manager):
    ws = MockWebSocket("u1_ws")
    # (2026-06-12 수리) conn_manager 채널 구조 정합 — test_hitl_timeout_integration 과 동일 부패
    reset_conn_manager._connections.setdefault("u1", {}).setdefault("agent", []).append(ws)
    return ws


# ──────────────────────────────────────────────────────────────────
# HT-11 — timeout 후 resume_query 재전송 → INVALID_MESSAGE
# ──────────────────────────────────────────────────────────────────

async def test_HT11_resume_query_on_timeouted_turn_emits_invalid_message(
    mock_ws_u1, fresh_hitl
):
    """MockAgent 로 resume_only=True + 최초 aget_state 에서 pending=False → INVALID_MESSAGE."""
    from api_v2.ws_agent import _graph_runner_with_resume

    agent = MockAgentWithInterrupt(
        streams=[],
        pending_sequence=[False],   # 이미 종료된 turn — pending 없음
        intr_values=[],
    )
    await _graph_runner_with_resume(
        "u1", "c1", "t_finished",
        {"resume_only": True},
        _agent=agent,
    )

    errors = [e for e in mock_ws_u1.sent if e.get("type") == "error"]
    assert len(errors) == 1
    err = errors[0]
    assert err.get("code") == "INVALID_MESSAGE"
    assert err.get("conversation_id") == "c1"
    assert err.get("turn_id") == "t_finished"
