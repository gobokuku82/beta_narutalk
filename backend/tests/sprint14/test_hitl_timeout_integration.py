"""Sprint 14 A1 — 그룹 C: run_turn 통합 (12건)

명세: docs/_claude/sprint14_a1_hitl_timeout_plan.md §R2 그룹 C
대상: backend/api_v2/ws_agent.py
  - run_turn (register_turn + finally cleanup)
  - _graph_runner_with_resume (timeout 분기 + reject/cancel 주입)
  - MockAgentWithInterrupt 재사용 (sprint13/test_resume_loop_unit.py 패턴)
"""

import asyncio

import pytest
import structlog

# Sprint 13 MockAgentWithInterrupt 재사용
from backend.tests.sprint13.test_resume_loop_unit import (
    MockAgentWithInterrupt,
    MockWebSocket,
)


@pytest.fixture
def mock_ws_u1(reset_conn_manager):
    ws = MockWebSocket("u1_ws")
    # (2026-06-12 수리) conn_manager 채널 구조({user: {channel: [ws]}}) 정합 —
    # sprint13 픽스처들은 갱신됐는데 이 파일만 구 평면 구조로 남아 11건이 헛붉음(하네스 부패).
    reset_conn_manager._connections.setdefault("u1", {}).setdefault("agent", []).append(ws)
    return ws


def _types(sent_list):
    return [s.get("type") for s in sent_list if isinstance(s, dict)]


def _short_timeout(monkeypatch, value=0.1):
    from app.core.config import settings
    monkeypatch.setattr(settings, "HITL_RESUME_TIMEOUT_SEC", value)


# ──────────────────────────────────────────────────────────────────
# HT-07 — register_turn 호출 (run_turn 진입 직후)
# ──────────────────────────────────────────────────────────────────

async def test_HT07_register_turn_called_on_run_turn_entry(
    mock_ws_u1, fresh_hitl, fresh_concurrency
):
    """run_turn 중 is_turn_active=True 확인 (runner 내부에서 체크)."""
    from api_v2.ws_agent import run_turn

    observed = {"active_during": None}

    async def _runner(uid, cid, tid, payload):
        observed["active_during"] = fresh_hitl.is_turn_active(tid)

    await run_turn("u1", "c1", "t1", {"user_input": "x"}, _runner=_runner)

    assert observed["active_during"] is True
    # 종료 후 cleanup
    assert fresh_hitl.is_turn_active("t1") is False


# ──────────────────────────────────────────────────────────────────
# HT-07b — 정상 종료 finally cleanup
# ──────────────────────────────────────────────────────────────────

async def test_HT07b_cleanup_turn_called_on_normal_finally(
    mock_ws_u1, fresh_hitl, fresh_concurrency
):
    from api_v2.ws_agent import run_turn

    async def _runner(uid, cid, tid, payload):
        pass  # no-op

    await run_turn("u1", "c1", "t1", {"user_input": "x"}, _runner=_runner)

    assert fresh_hitl.is_turn_active("t1") is False
    # concurrency slot 해제 — try_acquire 다시 가능
    assert fresh_concurrency.try_acquire("u1", "t1") is True


# ──────────────────────────────────────────────────────────────────
# HT-07c — runner 예외 시 finally cleanup
# ──────────────────────────────────────────────────────────────────

async def test_HT07c_cleanup_turn_called_on_runner_exception(
    mock_ws_u1, fresh_hitl, fresh_concurrency
):
    from api_v2.ws_agent import run_turn

    async def _runner(uid, cid, tid, payload):
        raise RuntimeError("simulated runner failure")

    await run_turn("u1", "c1", "t1", {"user_input": "x"}, _runner=_runner)
    # 예외 잡혀서 run_turn 자체는 완료

    assert fresh_hitl.is_turn_active("t1") is False
    assert fresh_concurrency.try_acquire("u1", "t1") is True
    # error broadcast 전송됐는지
    assert any(e.get("type") == "error" for e in mock_ws_u1.sent)


# ──────────────────────────────────────────────────────────────────
# HT-08 — execution_pause timeout → aborted + cancel 주입
# ──────────────────────────────────────────────────────────────────

async def test_HT08_execution_pause_timeout_emits_aborted(
    mock_ws_u1, fresh_hitl, monkeypatch
):
    from api_v2.ws_agent import _graph_runner_with_resume
    _short_timeout(monkeypatch, 0.05)

    agent = MockAgentWithInterrupt(
        streams=[[{"execution": {}}]],
        pending_sequence=[True, False],
        intr_values=[{"type": "execution_pause", "progress": {}}],
    )
    # signal_resume 호출 안 함 → timeout
    await _graph_runner_with_resume(
        "u1", "c1", "t1", {"user_input": "x"}, _agent=agent,
    )

    types = _types(mock_ws_u1.sent)
    assert "complete" in types
    complete_evt = [e for e in mock_ws_u1.sent if e.get("type") == "complete"][-1]
    assert complete_evt["data"]["status"] == "aborted"
    assert complete_evt["data"]["reason"] == "hitl_timeout"
    # execution_pause → cancel 주입
    assert agent.resume_values == [{"action": "cancel"}]


# ──────────────────────────────────────────────────────────────────
# HT-08a — resume_values intr_type 별 일치
# ──────────────────────────────────────────────────────────────────

async def test_HT08a_timeout_resume_values_match_intr_type(
    mock_ws_u1, fresh_hitl, monkeypatch
):
    from api_v2.ws_agent import _graph_runner_with_resume
    _short_timeout(monkeypatch, 0.05)

    # plan_review 경로
    agent = MockAgentWithInterrupt(
        streams=[[{"planning": {}}]],
        pending_sequence=[True, False],
        intr_values=[{"type": "plan_review", "plan": {"todos": []}}],
    )
    await _graph_runner_with_resume(
        "u1", "c1", "t1", {"user_input": "x"}, _agent=agent,
    )
    assert agent.resume_values == [{"action": "reject"}]


# ──────────────────────────────────────────────────────────────────
# HT-08b — timeout 경로 resumed 이벤트 부재
# ──────────────────────────────────────────────────────────────────

async def test_HT08b_timeout_does_not_emit_resumed_event(
    mock_ws_u1, fresh_hitl, monkeypatch
):
    from api_v2.ws_agent import _graph_runner_with_resume
    _short_timeout(monkeypatch, 0.05)

    agent = MockAgentWithInterrupt(
        streams=[[{"execution": {}}]],
        pending_sequence=[True, False],
        intr_values=[{"type": "execution_pause", "progress": {}}],
    )
    await _graph_runner_with_resume(
        "u1", "c1", "t1", {"user_input": "x"}, _agent=agent,
    )

    types = _types(mock_ws_u1.sent)
    assert "resumed" not in types, f"timeout 경로에 resumed 부재해야 함. types={types}"


# ──────────────────────────────────────────────────────────────────
# HT-08c ⭐ — plan_review timeout (G-11) → reject 주입, complete aborted (NOT rejected)
# ──────────────────────────────────────────────────────────────────

async def test_HT08c_plan_review_timeout_injects_reject(
    mock_ws_u1, fresh_hitl, monkeypatch
):
    from api_v2.ws_agent import _graph_runner_with_resume
    _short_timeout(monkeypatch, 0.05)

    agent = MockAgentWithInterrupt(
        streams=[[{"planning": {}}]],
        pending_sequence=[True, False],
        intr_values=[{"type": "plan_review", "plan": {"todos": []}}],
    )
    await _graph_runner_with_resume(
        "u1", "c1", "t1", {"user_input": "x"}, _agent=agent,
    )

    # G-11: plan_review → reject 주입 (NOT cancel)
    assert agent.resume_values == [{"action": "reject"}]
    complete_evt = [e for e in mock_ws_u1.sent if e.get("type") == "complete"][-1]
    # status 는 aborted (rejected 아님 — timeout 고유 종결)
    assert complete_evt["data"]["status"] == "aborted"
    assert complete_evt["data"]["reason"] == "hitl_timeout"


# ──────────────────────────────────────────────────────────────────
# HT-08d — execution_pause 이벤트 순서: paused → complete(aborted)
# ──────────────────────────────────────────────────────────────────

async def test_HT08d_execution_pause_event_order_paused_before_aborted(
    mock_ws_u1, fresh_hitl, monkeypatch
):
    from api_v2.ws_agent import _graph_runner_with_resume
    _short_timeout(monkeypatch, 0.05)

    agent = MockAgentWithInterrupt(
        streams=[[{"execution": {}}]],
        pending_sequence=[True, False],
        intr_values=[{"type": "execution_pause", "progress": {}}],
    )
    await _graph_runner_with_resume(
        "u1", "c1", "t1", {"user_input": "x"}, _agent=agent,
    )

    types = _types(mock_ws_u1.sent)
    paused_idx = types.index("paused")
    complete_idx = types.index("complete")
    assert paused_idx < complete_idx, f"순서 위반: {types}"


# ──────────────────────────────────────────────────────────────────
# HT-08e — plan_review 이벤트 순서: hitl_request → complete(aborted)
# ──────────────────────────────────────────────────────────────────

async def test_HT08e_plan_review_event_order_hitl_request_before_aborted(
    mock_ws_u1, fresh_hitl, monkeypatch
):
    from api_v2.ws_agent import _graph_runner_with_resume
    _short_timeout(monkeypatch, 0.05)

    agent = MockAgentWithInterrupt(
        streams=[[{"planning": {}}]],
        pending_sequence=[True, False],
        intr_values=[{"type": "plan_review", "plan": {"todos": []}}],
    )
    await _graph_runner_with_resume(
        "u1", "c1", "t1", {"user_input": "x"}, _agent=agent,
    )

    types = _types(mock_ws_u1.sent)
    hreq_idx = types.index("hitl_request")
    complete_idx = types.index("complete")
    assert hreq_idx < complete_idx, f"순서 위반: {types}"


# ──────────────────────────────────────────────────────────────────
# HT-08f — structured log (G-12) via structlog.testing.capture_logs
# ──────────────────────────────────────────────────────────────────

async def test_HT08f_timeout_emits_structlog_event(
    mock_ws_u1, fresh_hitl, monkeypatch
):
    from api_v2.ws_agent import _graph_runner_with_resume
    _short_timeout(monkeypatch, 0.05)

    agent = MockAgentWithInterrupt(
        streams=[[{"execution": {}}]],
        pending_sequence=[True, False],
        intr_values=[{"type": "execution_pause", "progress": {}}],
    )

    with structlog.testing.capture_logs() as cap_logs:
        await _graph_runner_with_resume(
            "u1", "c1", "t1", {"user_input": "x"}, _agent=agent,
        )

    timeouts = [log for log in cap_logs if log.get("event") == "hitl timeout aborted turn"]
    assert len(timeouts) == 1, f"구조화 log 1회 기대. 전체: {cap_logs}"
    entry = timeouts[0]
    assert entry["user_id"] == "u1"
    assert entry["conv_id"] == "c1"
    assert entry["turn_id"] == "t1"
    assert entry["intr_type"] == "execution_pause"
    assert entry["timeout_sec"] == 0.05


# ──────────────────────────────────────────────────────────────────
# HT-08g — plan_review timeout 후 execution 진입 안 함 (G-11 regression)
# ──────────────────────────────────────────────────────────────────

async def test_HT08g_plan_review_timeout_does_not_enter_execution(
    mock_ws_u1, fresh_hitl, monkeypatch
):
    """MockAgent 는 execution chunk 를 yield 하지 않아야 함 (reject 주입 후 END)."""
    from api_v2.ws_agent import _graph_runner_with_resume
    _short_timeout(monkeypatch, 0.05)

    # reject 주입 후의 stream 은 빈 generator — execution chunk 없음
    agent = MockAgentWithInterrupt(
        streams=[[{"planning": {}}]],  # 1번째 astream 만. 2번째 (resume) 은 없음
        pending_sequence=[True, False],
        intr_values=[{"type": "plan_review", "plan": {"todos": []}}],
    )
    await _graph_runner_with_resume(
        "u1", "c1", "t1", {"user_input": "x"}, _agent=agent,
    )

    node_events = [e for e in mock_ws_u1.sent if e.get("type") == "node_event"]
    nodes = [e.get("node") for e in node_events]
    assert "execution" not in nodes, (
        f"plan_review timeout 후 execution 노드 진입 감지: {nodes}"
    )


# ──────────────────────────────────────────────────────────────────
# HT-09 — mocker.spy release + cleanup_turn
# ──────────────────────────────────────────────────────────────────

async def test_HT09_finally_spies_release_and_cleanup(
    mock_ws_u1, fresh_hitl, fresh_concurrency, mocker, monkeypatch
):
    from api_v2.ws_agent import run_turn

    # run_turn 내부는 global concurrency singleton 사용 — 그것을 spy
    from app.dream_agent.workflow_managers import concurrency_manager
    from app.dream_agent.workflow_managers.hitl_manager import get_hitl_manager

    release_spy = mocker.spy(concurrency_manager.concurrency, "release")
    cleanup_spy = mocker.spy(get_hitl_manager(), "cleanup_turn")

    async def _runner(uid, cid, tid, payload):
        pass

    await run_turn("u1", "c1", "t1", {"user_input": "x"}, _runner=_runner)

    assert release_spy.call_count == 1
    assert cleanup_spy.call_count == 1


# ──────────────────────────────────────────────────────────────────
# HT-10 — MockAgent pending_sequence [True, False] + timeout → runner 탈출
# ──────────────────────────────────────────────────────────────────

async def test_HT10_runner_exits_loop_on_pending_false(
    mock_ws_u1, fresh_hitl, monkeypatch
):
    from api_v2.ws_agent import _graph_runner_with_resume
    _short_timeout(monkeypatch, 0.05)

    agent = MockAgentWithInterrupt(
        streams=[[{"planning": {}}]],
        pending_sequence=[True, False],
        intr_values=[{"type": "plan_review", "plan": {"todos": []}}],
    )
    await _graph_runner_with_resume(
        "u1", "c1", "t1", {"user_input": "x"}, _agent=agent,
    )

    complete_count = sum(1 for e in mock_ws_u1.sent if e.get("type") == "complete")
    assert complete_count == 1, f"complete 1회 기대. 전체: {_types(mock_ws_u1.sent)}"
    # 추가 paused/hitl_request 없음 (1회만)
    hreq_count = sum(1 for e in mock_ws_u1.sent if e.get("type") == "hitl_request")
    paused_count = sum(1 for e in mock_ws_u1.sent if e.get("type") == "paused")
    assert hreq_count <= 1 and paused_count <= 1
