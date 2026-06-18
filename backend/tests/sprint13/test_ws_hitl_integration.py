"""I9 — ws_hitl 전환 Integration 테스트

명세서: docs/_claude/checkpointer/sprint13_integration_i9_ws_hitl_spec.md
대상: backend/api_v2/ws_hitl.py

7 케이스 (FastAPI TestClient WebSocket).
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def hitl_app(fresh_hitl, reset_conn_manager):
    """/ws/hitl 엔드포인트만 있는 최소 앱."""
    from api_v2.ws_hitl import router
    app = FastAPI()
    app.include_router(router)
    return app


# ──────────────────────────────────────────────────────────────────
# WH-01
# ──────────────────────────────────────────────────────────────────

def test_WH01_connect_registers_to_conn_manager(hitl_app, reset_conn_manager):
    client = TestClient(hitl_app)
    with client.websocket_connect("/ws/hitl?user_id=u1") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "connected"
        assert len(reset_conn_manager._connections["u1"]["hitl"]) == 1


# ──────────────────────────────────────────────────────────────────
# WH-02
# ──────────────────────────────────────────────────────────────────

def test_WH02_disconnect_removes_from_conn_manager(hitl_app, reset_conn_manager):
    client = TestClient(hitl_app)
    with client.websocket_connect("/ws/hitl?user_id=u1") as ws:
        ws.receive_json()
        assert len(reset_conn_manager._connections.get("u1", [])) == 1
    # context exit → ws.close() → 서버 disconnect 처리
    assert len(reset_conn_manager._connections.get("u1", [])) == 0


# ──────────────────────────────────────────────────────────────────
# WH-03 🔴 hitl_response → signal_resume
# ──────────────────────────────────────────────────────────────────

def test_WH03_hitl_response_triggers_signal_resume(hitl_app, fresh_hitl):
    # Sprint 14 A1 — register_turn 선행 (hitl_response 가드 통과)
    fresh_hitl.register_turn("turn_abc")
    client = TestClient(hitl_app)
    with client.websocket_connect("/ws/hitl?user_id=u1") as ws:
        ws.receive_json()  # connected
        ws.send_json({
            "type": "hitl_response",
            "data": {
                "request_id": "req_xxx",
                "action": "approve",
                "turn_id": "turn_abc",
            },
        })
        ack = ws.receive_json()

    assert ack["type"] == "hitl_ack"
    assert ack["data"]["action"] == "approve"
    # (2026-06-11) 정직 ack — 장부 트랙 폐기, accepted = 재개 신호 전달 기준 (활성 turn → True)
    assert ack["data"]["accepted"] is True

    # Queue에 signal_resume이 put한 내용 확인
    q = fresh_hitl._resume_queues.get("turn_abc")
    assert q is not None and q.qsize() == 1
    payload = q.get_nowait()
    assert payload["action"] == "approve"


# ──────────────────────────────────────────────────────────────────
# WH-04 🔴 resume → signal_resume("continue")
# ──────────────────────────────────────────────────────────────────

def test_WH04_resume_triggers_signal_continue(hitl_app, fresh_hitl):
    # Sprint 14 A1 — register_turn 선행 (가드 통과용)
    fresh_hitl.register_turn("turn_xyz")
    client = TestClient(hitl_app)
    with client.websocket_connect("/ws/hitl?user_id=u1") as ws:
        ws.receive_json()
        ws.send_json({
            "type": "resume",
            "data": {"turn_id": "turn_xyz"},
        })
        ack = ws.receive_json()

    assert ack["data"]["action"] == "resume"

    q = fresh_hitl._resume_queues["turn_xyz"]
    assert q.qsize() == 1
    assert q.get_nowait() == {"action": "continue"}


# ──────────────────────────────────────────────────────────────────
# WH-05 신규 cancel 타입
# ──────────────────────────────────────────────────────────────────

def test_WH05_cancel_triggers_signal_cancel(hitl_app, fresh_hitl):
    # Sprint 14 A1 — register_turn 선행 (가드 통과용)
    fresh_hitl.register_turn("turn_c")
    client = TestClient(hitl_app)
    with client.websocket_connect("/ws/hitl?user_id=u1") as ws:
        ws.receive_json()
        ws.send_json({
            "type": "cancel",
            "data": {"turn_id": "turn_c"},
        })
        ack = ws.receive_json()

    assert ack["data"]["action"] == "cancel"
    q = fresh_hitl._resume_queues["turn_c"]
    assert q.qsize() == 1
    assert q.get_nowait() == {"action": "cancel"}


# ──────────────────────────────────────────────────────────────────
# WH-06 pause → signal_resume 호출 안 됨
# ──────────────────────────────────────────────────────────────────

def test_WH06_pause_does_not_signal_resume(hitl_app, fresh_hitl):
    # Sprint 14 A1 — register_turn 선행 (가드 통과용)
    fresh_hitl.register_turn("turn_p")
    client = TestClient(hitl_app)
    with client.websocket_connect("/ws/hitl?user_id=u1") as ws:
        ws.receive_json()
        ws.send_json({
            "type": "pause",
            "data": {"session_id": "turn_p"},
        })
        ack = ws.receive_json()

    assert ack["data"]["action"] == "pause"
    # Sprint 12 동작: _paused에 추가됨
    assert "turn_p" in fresh_hitl._paused
    # I7 Queue에는 signal 없음
    q = fresh_hitl._resume_queues.get("turn_p")
    assert q is None or q.qsize() == 0


# ──────────────────────────────────────────────────────────────────
# WH-07 session_id → turn_id 폴백
# ──────────────────────────────────────────────────────────────────

def test_WH07_session_id_fallback_to_turn_id(hitl_app, fresh_hitl):
    # Sprint 14 A1 — register_turn 선행 (가드 통과용, fallback 동작 확인)
    fresh_hitl.register_turn("turn_legacy")
    client = TestClient(hitl_app)
    with client.websocket_connect("/ws/hitl?user_id=u1") as ws:
        ws.receive_json()
        # session_id만 있고 turn_id 없음 (Sprint 12 호환)
        ws.send_json({
            "type": "resume",
            "data": {"session_id": "turn_legacy"},
        })
        ws.receive_json()  # ack

    q = fresh_hitl._resume_queues["turn_legacy"]
    assert q.qsize() == 1
    assert q.get_nowait() == {"action": "continue"}
