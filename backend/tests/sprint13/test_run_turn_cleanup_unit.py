"""I10e — run_turn 예외 처리 + finally cleanup Unit 테스트

명세서: sprint13_integration_i10e_error_cleanup_spec.md

3 케이스 (async Unit).
"""

import pytest


class MockWebSocket:
    def __init__(self, name):
        self.name = name
        self.sent = []

    async def send_json(self, data):
        self.sent.append(data)

    async def close(self, code=None, reason=None):
        pass


@pytest.fixture
def mock_ws_u1(reset_conn_manager):
    ws = MockWebSocket("u1_ws")
    reset_conn_manager._connections.setdefault("u1", {}).setdefault("agent", []).append(ws)
    return ws


@pytest.fixture
def fresh_concurrency_singleton():
    from app.dream_agent.workflow_managers.concurrency_manager import concurrency
    concurrency._reset_for_test()
    concurrency._max_concurrent = 10
    yield concurrency
    concurrency._reset_for_test()
    concurrency._max_concurrent = None


# ──────────────────────────────────────────────────────────────────
# EX-01 🔴 runner 예외 → error broadcast + release + cleanup
# ──────────────────────────────────────────────────────────────────

async def test_EX01_runner_exception_broadcast_error_and_release(
    mock_ws_u1, fresh_concurrency_singleton, fresh_hitl,
):
    from api_v2.ws_agent import run_turn

    async def bad_runner(*args):
        raise RuntimeError("graph exploded")

    fresh_hitl.signal_resume("t1", {"action": "x"})
    assert "t1" in fresh_hitl._resume_queues

    # 예외 swallow (raise 되지 않음)
    await run_turn("u1", "c1", "t1", {"user_input": "x"}, _runner=bad_runner)

    # error broadcast
    errors = [s for s in mock_ws_u1.sent if s.get("type") == "error"]
    assert len(errors) == 1
    err = errors[0]
    assert err["code"] == "EXECUTION_ERROR"
    assert err["layer"] == "runtime"              # I11-a: 포맷 통일
    assert err["severity"] == "fatal"             # I11-a: 포맷 통일
    assert err["conversation_id"] == "c1"
    assert err["turn_id"] == "t1"
    assert "graph exploded" in err["message"]

    # release
    assert fresh_concurrency_singleton.active_count("u1") == 0

    # cleanup_turn
    assert "t1" not in fresh_hitl._resume_queues


# ──────────────────────────────────────────────────────────────────
# EX-02 정상 완료 → error 없음, release + cleanup
# ──────────────────────────────────────────────────────────────────

async def test_EX02_normal_completion_cleanup(
    mock_ws_u1, fresh_concurrency_singleton, fresh_hitl,
):
    from api_v2.ws_agent import run_turn

    async def ok_runner(user_id, conv, turn, payload):
        pass

    fresh_hitl.signal_resume("t1", {"action": "x"})

    await run_turn("u1", "c1", "t1", {"user_input": "x"}, _runner=ok_runner)

    errors = [s for s in mock_ws_u1.sent if s.get("type") == "error"]
    assert errors == []

    assert fresh_concurrency_singleton.active_count("u1") == 0
    assert "t1" not in fresh_hitl._resume_queues


# ──────────────────────────────────────────────────────────────────
# EX-03 🔴 default _runner = _graph_runner_with_resume
# ──────────────────────────────────────────────────────────────────

async def test_EX03_default_runner_is_graph_runner_with_resume(
    mock_ws_u1, fresh_concurrency_singleton, fresh_hitl, monkeypatch,
):
    import api_v2.ws_agent as ws_agent_mod
    from api_v2.ws_agent import run_turn

    called = []

    async def fake_runner(user_id, conv, turn, payload, *, _app=None):
        called.append((user_id, conv, turn))

    monkeypatch.setattr(ws_agent_mod, "_graph_runner_with_resume", fake_runner)

    await run_turn("u1", "c1", "t1", {"user_input": "x"})

    assert called == [("u1", "c1", "t1")]
