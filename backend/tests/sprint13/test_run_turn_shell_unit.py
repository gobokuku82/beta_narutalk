"""I10b — run_turn shell (슬롯 관리 + 에러 broadcast) Unit 테스트

명세서: sprint13_integration_i10b_run_turn_shell_spec.md

5 케이스 (async Unit).
"""

import pytest


# MockWebSocket는 T1과 동일 형태 — conn_manager에 register
class MockWebSocket:
    def __init__(self, name, raise_on_send=False):
        self.name = name
        self.raise_on_send = raise_on_send
        self.sent = []

    async def send_json(self, data):
        if self.raise_on_send:
            raise ConnectionError(f"{self.name} disconnected")
        self.sent.append(data)

    async def close(self, code=None, reason=None):
        pass


@pytest.fixture
def mock_ws_u1(reset_conn_manager):
    """u1에 MockWebSocket 등록 (broadcast 검증용)."""
    ws = MockWebSocket("u1_ws")
    reset_conn_manager._connections.setdefault("u1", {}).setdefault("agent", []).append(ws)
    return ws


@pytest.fixture
def fresh_concurrency_singleton():
    """싱글톤 concurrency 초기화 + MAX=10 (테스트 자유도 확보)."""
    from app.dream_agent.workflow_managers.concurrency_manager import concurrency
    concurrency._reset_for_test()
    concurrency._max_concurrent = 10  # 기본 높게, 테스트마다 조정
    yield concurrency
    concurrency._reset_for_test()
    concurrency._max_concurrent = None  # 기본값 복원


# ──────────────────────────────────────────────────────────────────
# RS-01 정상 흐름 — acquire + release
# ──────────────────────────────────────────────────────────────────

async def test_RS01_acquire_and_release_normal(
    mock_ws_u1, fresh_concurrency_singleton
):
    from api_v2.ws_agent import run_turn

    await run_turn("u1", "c1", "t1", {"user_input": "x"})

    # release 정상
    assert fresh_concurrency_singleton.active_count("u1") == 0


# ──────────────────────────────────────────────────────────────────
# RS-02 🔴 slot 초과 시 에러 broadcast
# ──────────────────────────────────────────────────────────────────

async def test_RS02_concurrent_limit_exceeded(
    mock_ws_u1, fresh_concurrency_singleton
):
    from api_v2.ws_agent import run_turn

    # MAX=1 강제
    fresh_concurrency_singleton._max_concurrent = 1
    fresh_concurrency_singleton.try_acquire("u1", "t_existing")

    await run_turn("u1", "c1", "t_new", {"user_input": "x"})

    # mock_ws가 error 메시지 받음
    assert len(mock_ws_u1.sent) == 1
    err = mock_ws_u1.sent[0]
    assert err["type"] == "error"
    assert err["code"] == "CONCURRENT_LIMIT_EXCEEDED"
    assert err["layer"] == "transport"           # I11-a: 포맷 통일
    assert err["severity"] == "fatal"            # I11-a: 포맷 통일
    assert err["conversation_id"] == "c1"
    assert err["turn_id"] == "t_new"
    # 기존 t_existing만 점유
    assert fresh_concurrency_singleton.active_count("u1") == 1


# ──────────────────────────────────────────────────────────────────
# RS-03 _runner 호출됨
# ──────────────────────────────────────────────────────────────────

async def test_RS03_runner_called_when_slot_acquired(
    mock_ws_u1, fresh_concurrency_singleton
):
    from api_v2.ws_agent import run_turn

    called = []

    async def runner(user_id, conv, turn, payload):
        called.append((user_id, conv, turn, payload))

    await run_turn("u1", "c1", "t1", {"user_input": "hello"}, _runner=runner)

    assert len(called) == 1
    assert called[0] == ("u1", "c1", "t1", {"user_input": "hello"})


# ──────────────────────────────────────────────────────────────────
# RS-04 예외 발생해도 release
# ──────────────────────────────────────────────────────────────────

async def test_RS04_release_on_runner_exception(
    mock_ws_u1, fresh_concurrency_singleton, fresh_hitl,
):
    from api_v2.ws_agent import run_turn

    async def bad_runner(*args):
        raise RuntimeError("graph error")

    # I10e: 예외 swallow + error broadcast
    await run_turn("u1", "c1", "t1", {"user_input": "x"}, _runner=bad_runner)

    # release
    assert fresh_concurrency_singleton.active_count("u1") == 0
    # error broadcast
    errors = [s for s in mock_ws_u1.sent if s.get("type") == "error"]
    assert len(errors) == 1
    assert errors[0]["code"] == "EXECUTION_ERROR"


# ──────────────────────────────────────────────────────────────────
# RS-05 slot 초과 시 _runner 호출 안 됨
# ──────────────────────────────────────────────────────────────────

async def test_RS05_runner_not_called_when_limit_exceeded(
    mock_ws_u1, fresh_concurrency_singleton
):
    from api_v2.ws_agent import run_turn

    # MAX=0 → 모두 거부
    fresh_concurrency_singleton._max_concurrent = 0

    called = []

    async def runner(*args):
        called.append(args)

    await run_turn("u1", "c1", "t1", {"user_input": "x"}, _runner=runner)

    assert len(called) == 0
