"""I11-a — Error 이벤트 포맷 통일 (severity/layer) Unit 테스트.

명세서: sprint13_i11_i12_plan.md §2.6

EF-01 CONCURRENT_LIMIT_EXCEEDED 에 severity/layer 필드 (fan-out)
EF-02 EXECUTION_ERROR 에 severity/layer 필드 (fan-out)
"""

import pytest


class MockWebSocket:
    def __init__(self, name):
        self.name = name
        self.sent: list[dict] = []

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
# EF-01 CONCURRENT_LIMIT_EXCEEDED: severity=fatal, layer=transport
# ──────────────────────────────────────────────────────────────────

async def test_EF01_concurrent_limit_has_severity_layer(
    mock_ws_u1, fresh_concurrency_singleton, fresh_hitl,
):
    from api_v2.ws_agent import run_turn

    fresh_concurrency_singleton._max_concurrent = 1
    fresh_concurrency_singleton.try_acquire("u1", "t_existing")

    async def noop_runner(*args, **kwargs):
        pass

    await run_turn("u1", "c1", "t_new", {"user_input": "x"}, _runner=noop_runner)

    errs = [s for s in mock_ws_u1.sent if s.get("type") == "error"]
    assert len(errs) == 1
    err = errs[0]
    assert err["code"] == "CONCURRENT_LIMIT_EXCEEDED"
    assert err["layer"] == "transport"
    assert err["severity"] == "fatal"
    assert err["conversation_id"] == "c1"
    assert err["turn_id"] == "t_new"


# ──────────────────────────────────────────────────────────────────
# EF-02 EXECUTION_ERROR: severity=fatal, layer=runtime
# ──────────────────────────────────────────────────────────────────

async def test_EF02_execution_error_has_severity_layer(
    mock_ws_u1, fresh_concurrency_singleton, fresh_hitl,
):
    from api_v2.ws_agent import run_turn

    async def bad_runner(*args, **kwargs):
        raise RuntimeError("graph exploded")

    await run_turn("u1", "c1", "t1", {"user_input": "x"}, _runner=bad_runner)

    errs = [s for s in mock_ws_u1.sent if s.get("type") == "error"]
    assert len(errs) == 1
    err = errs[0]
    assert err["code"] == "EXECUTION_ERROR"
    assert err["layer"] == "runtime"
    assert err["severity"] == "fatal"
    assert "graph exploded" in err["message"]
