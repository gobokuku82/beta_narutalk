"""I10f — /ws/agent query 경로 + 호환성 구조 테스트 (non-live)

명세서: sprint13_integration_i10f_e2e_spec.md

8 케이스 (FastAPI TestClient + monkey patch).
"""

import asyncio
import threading
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def agent_app(reset_conn_manager, fresh_hitl):
    """/ws/agent + /ws/hitl 라우터를 가진 최소 앱."""
    from api_v2.ws_agent import router as agent_router
    from api_v2.ws_hitl import router as hitl_router
    from app.dream_agent.workflow_managers.concurrency_manager import concurrency
    concurrency._reset_for_test()
    concurrency._max_concurrent = 10
    app = FastAPI()
    app.include_router(agent_router)
    app.include_router(hitl_router)
    yield app
    concurrency._reset_for_test()
    concurrency._max_concurrent = None


# ──────────────────────────────────────────────────────────────────
# WQ-01~05 INVALID_MESSAGE
# ──────────────────────────────────────────────────────────────────

def _send_query_and_get_error(client, payload):
    with client.websocket_connect("/ws/agent?user_id=u1") as ws:
        ws.receive_json()  # connected
        ws.send_json({"type": "query", **payload})
        err = ws.receive_json()
    # I11-a: INVALID_MESSAGE 포맷 통일 (severity/layer)
    assert err.get("severity") == "fatal"
    assert err.get("layer") == "transport"
    return err


def test_WQ01_invalid_missing_conv_id(agent_app):
    err = _send_query_and_get_error(TestClient(agent_app), {
        "turn_id": "t1", "user_input": "x",
    })
    assert err["type"] == "error"
    assert err["code"] == "INVALID_MESSAGE"
    assert "conversation_id" in err["message"]


def test_WQ02_invalid_empty_conv_id(agent_app):
    err = _send_query_and_get_error(TestClient(agent_app), {
        "conversation_id": "", "turn_id": "t1", "user_input": "x",
    })
    assert err["code"] == "INVALID_MESSAGE"


def test_WQ03_invalid_missing_turn_id(agent_app):
    err = _send_query_and_get_error(TestClient(agent_app), {
        "conversation_id": "c1", "user_input": "x",
    })
    assert err["code"] == "INVALID_MESSAGE"
    assert "turn_id" in err["message"]


def test_WQ04_invalid_empty_turn_id(agent_app):
    err = _send_query_and_get_error(TestClient(agent_app), {
        "conversation_id": "c1", "turn_id": "", "user_input": "x",
    })
    assert err["code"] == "INVALID_MESSAGE"


def test_WQ05_invalid_missing_user_input(agent_app):
    err = _send_query_and_get_error(TestClient(agent_app), {
        "conversation_id": "c1", "turn_id": "t1",
    })
    assert err["code"] == "INVALID_MESSAGE"
    assert "user_input" in err["message"]


# ──────────────────────────────────────────────────────────────────
# WQ-06 query → run_turn task 분리 (D-7)
# ──────────────────────────────────────────────────────────────────

def test_WQ06_query_creates_async_task(agent_app, monkeypatch):
    """query 수신 → asyncio.create_task로 runner 호출 검증.

    참고: 실제 D-7 (WS 끊겨도 task 지속) 격리는 TestClient 환경에서 검증 불가
    (WS 종료 시 event loop teardown). 여기선 task 스케줄+진입까지만 확인.
    완전한 D-7 격리는 live 테스트(WL-*)에서 검증.
    """
    import api_v2.ws_agent as ws_agent_mod

    started = threading.Event()
    payload_seen = []

    async def runner(user_id, conv, turn, payload, *, _app=None):
        payload_seen.append((user_id, conv, turn, payload))
        started.set()
        # WS는 살아있는 동안 응답 송신 가능 — broadcast로 ack
        from api_v2.connection_manager import conn_manager
        await conn_manager.broadcast_to_user(user_id, "agent", {
            "type": "node_event", "node": "ack",
            "conversation_id": conv, "turn_id": turn, "data": {},
        })

    monkeypatch.setattr(ws_agent_mod, "_graph_runner_with_resume", runner)

    client = TestClient(agent_app)
    with client.websocket_connect("/ws/agent?user_id=u1") as ws:
        ws.receive_json()  # connected
        ws.send_json({
            "type": "query",
            "conversation_id": "c1", "turn_id": "t1", "user_input": "hello",
        })
        ack = ws.receive_json()
        assert ack["node"] == "ack"

    # task 진입 확인 + payload 정확성
    assert started.wait(timeout=2.0)
    assert payload_seen[0] == ("u1", "c1", "t1", {"user_input": "hello"})


# ──────────────────────────────────────────────────────────────────
# WQ-07 (작업 ⑬, 2026-05-31) 폐기 — legacy `type=="start"` 진입점 폐기
# 이유: frontend api/ws.ts 에 `type: 'start'` 송신 0 hit. _run_agent 함수 폐기됨.
# 활성 = `type=="query"` (WQ-01~06) + `type=="resume_query"` (test_resume_only_unit.py)
# ──────────────────────────────────────────────────────────────────


# ──────────────────────────────────────────────────────────────────
# WQ-08 Multi-tab broadcast via conn_manager
# ──────────────────────────────────────────────────────────────────

def test_WQ08_multi_tab_broadcast(agent_app, monkeypatch):
    import api_v2.ws_agent as ws_agent_mod

    async def runner(user_id, conv, turn, payload, *, _app=None):
        from api_v2.connection_manager import conn_manager
        # 약간 지연 — 두 WS 모두 등록 후 broadcast 보장
        await asyncio.sleep(0.1)
        await conn_manager.broadcast_to_user(user_id, "agent", {
            "type": "node_event",
            "node": "cognitive_stage",
            "conversation_id": conv,
            "turn_id": turn,
            "data": {},
        })

    monkeypatch.setattr(ws_agent_mod, "_graph_runner_with_resume", runner)

    client = TestClient(agent_app)
    with client.websocket_connect("/ws/agent?user_id=u_multi") as ws_a:
        ws_a.receive_json()  # connected
        with client.websocket_connect("/ws/agent?user_id=u_multi") as ws_b:
            ws_b.receive_json()  # connected
            ws_a.send_json({
                "type": "query",
                "conversation_id": "c1", "turn_id": "t1", "user_input": "x",
            })
            evt_a = ws_a.receive_json()
            evt_b = ws_b.receive_json()
            assert evt_a["node"] == "cognitive_stage"
            assert evt_b["node"] == "cognitive_stage"
            assert evt_a["turn_id"] == "t1"
            assert evt_b["turn_id"] == "t1"


# ──────────────────────────────────────────────────────────────────
# WQ-09~11 resume_query (R-9 서버 재시작 복원) 경로
# ──────────────────────────────────────────────────────────────────

def test_WQ09_resume_query_invokes_runner_with_resume_only(agent_app, monkeypatch):
    """resume_query 수신 시 run_turn → _graph_runner_with_resume 가
    payload={"resume_only": True} 로 호출되는지 검증."""
    import api_v2.ws_agent as ws_agent_mod

    payload_seen = []
    started = threading.Event()

    async def runner(user_id, conv, turn, payload, *, _app=None):
        payload_seen.append((user_id, conv, turn, payload))
        started.set()
        from api_v2.connection_manager import conn_manager
        await conn_manager.broadcast_to_user(user_id, "agent", {
            "type": "node_event", "node": "ack",
            "conversation_id": conv, "turn_id": turn, "data": {},
        })

    monkeypatch.setattr(ws_agent_mod, "_graph_runner_with_resume", runner)

    client = TestClient(agent_app)
    with client.websocket_connect("/ws/agent?user_id=u_resume") as ws:
        ws.receive_json()  # connected
        ws.send_json({
            "type": "resume_query",
            "conversation_id": "c_r9",
            "turn_id": "t_r9",
        })
        ack = ws.receive_json()
        assert ack["node"] == "ack"

    assert started.wait(timeout=2.0)
    assert payload_seen[0] == ("u_resume", "c_r9", "t_r9", {"resume_only": True})


def test_WQ10_resume_query_missing_conv_id(agent_app):
    """resume_query 에 conversation_id 없으면 INVALID_MESSAGE."""
    client = TestClient(agent_app)
    with client.websocket_connect("/ws/agent?user_id=u1") as ws:
        ws.receive_json()  # connected
        ws.send_json({"type": "resume_query", "turn_id": "t_r9"})
        err = ws.receive_json()
    assert err["type"] == "error"
    assert err["code"] == "INVALID_MESSAGE"
    assert err["severity"] == "fatal"


def test_WQ11_resume_query_missing_turn_id(agent_app):
    """resume_query 에 turn_id 없으면 INVALID_MESSAGE."""
    client = TestClient(agent_app)
    with client.websocket_connect("/ws/agent?user_id=u1") as ws:
        ws.receive_json()  # connected
        ws.send_json({"type": "resume_query", "conversation_id": "c_r9"})
        err = ws.receive_json()
    assert err["type"] == "error"
    assert err["code"] == "INVALID_MESSAGE"
