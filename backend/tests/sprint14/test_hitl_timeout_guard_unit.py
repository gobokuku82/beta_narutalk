"""Sprint 14 A1 — 그룹 B: ws_hitl 가드 Unit (7건)

명세: docs/_claude/sprint14_a1_hitl_timeout_plan.md §R2 그룹 B
대상: backend/api_v2/ws_hitl.py
  - _handle_pause (L317) / _handle_resume (L333) / _handle_cancel (L352) 가드
  - 비활성 turn → accepted:False, reason:"turn_not_active"
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def hitl_app(fresh_hitl, reset_conn_manager):
    """sprint13 test_ws_hitl_integration 과 동일 pattern."""
    from api_v2.ws_hitl import router
    app = FastAPI()
    app.include_router(router)
    return app


# ──────────────────────────────────────────────────────────────────
# HT-05 — 비활성 turn resume → accepted:False
# ──────────────────────────────────────────────────────────────────

def test_HT05_resume_inactive_turn_rejected(hitl_app, fresh_hitl):
    client = TestClient(hitl_app)
    with client.websocket_connect("/ws/hitl?user_id=u1") as ws:
        ws.receive_json()  # connected
        ws.send_json({"type": "resume", "data": {"turn_id": "stale_A"}})
        ack = ws.receive_json()

    assert ack["data"]["action"] == "resume"
    assert ack["data"]["accepted"] is False
    assert ack["data"]["reason"] == "turn_not_active"
    # Queue 미생성 확인
    assert "stale_A" not in fresh_hitl._resume_queues


# ──────────────────────────────────────────────────────────────────
# HT-05b — 활성 turn resume (회귀 회로)
# ──────────────────────────────────────────────────────────────────

def test_HT05b_resume_active_turn_passes_regression(hitl_app, fresh_hitl):
    fresh_hitl.register_turn("active_A")
    client = TestClient(hitl_app)
    with client.websocket_connect("/ws/hitl?user_id=u1") as ws:
        ws.receive_json()
        ws.send_json({"type": "resume", "data": {"turn_id": "active_A"}})
        ack = ws.receive_json()

    assert ack["data"]["accepted"] is True
    assert fresh_hitl._resume_queues["active_A"].qsize() == 1


# ──────────────────────────────────────────────────────────────────
# HT-05c — session_id / turn_id fallback 동일 가드 적용
# ──────────────────────────────────────────────────────────────────

def test_HT05c_fallback_turn_id_or_session_id(hitl_app, fresh_hitl):
    client = TestClient(hitl_app)
    # (1) turn_id 만 — 비활성 → 거부
    with client.websocket_connect("/ws/hitl?user_id=u1") as ws:
        ws.receive_json()
        ws.send_json({"type": "resume", "data": {"turn_id": "x"}})
        ack = ws.receive_json()
    assert ack["data"]["accepted"] is False
    assert ack["data"]["reason"] == "turn_not_active"

    # (2) session_id 만 — 비활성 → 거부
    with client.websocket_connect("/ws/hitl?user_id=u2") as ws:
        ws.receive_json()
        ws.send_json({"type": "resume", "data": {"session_id": "y"}})
        ack = ws.receive_json()
    assert ack["data"]["accepted"] is False
    assert ack["data"]["reason"] == "turn_not_active"


# ──────────────────────────────────────────────────────────────────
# HT-06 — 비활성 pause → accepted:False
# ──────────────────────────────────────────────────────────────────

def test_HT06_pause_inactive_turn_rejected(hitl_app, fresh_hitl):
    client = TestClient(hitl_app)
    with client.websocket_connect("/ws/hitl?user_id=u1") as ws:
        ws.receive_json()
        ws.send_json({"type": "pause", "data": {"turn_id": "stale"}})
        ack = ws.receive_json()

    assert ack["data"]["accepted"] is False
    assert ack["data"]["reason"] == "turn_not_active"
    assert "stale" not in fresh_hitl._paused


# ──────────────────────────────────────────────────────────────────
# HT-06b — 비활성 cancel → accepted:False
# ──────────────────────────────────────────────────────────────────

def test_HT06b_cancel_inactive_turn_rejected(hitl_app, fresh_hitl):
    client = TestClient(hitl_app)
    with client.websocket_connect("/ws/hitl?user_id=u1") as ws:
        ws.receive_json()
        ws.send_json({"type": "cancel", "data": {"turn_id": "stale"}})
        ack = ws.receive_json()

    assert ack["data"]["accepted"] is False
    assert ack["data"]["reason"] == "turn_not_active"
    # request_cancel 호출 안 됨 — progress 없으니 간접 확인
    assert fresh_hitl.get_progress("stale") is None


# ──────────────────────────────────────────────────────────────────
# HT-06c — 활성 pause (회귀 대칭)
# ──────────────────────────────────────────────────────────────────

def test_HT06c_pause_active_turn_passes_regression(hitl_app, fresh_hitl):
    fresh_hitl.register_turn("p1")
    client = TestClient(hitl_app)
    with client.websocket_connect("/ws/hitl?user_id=u1") as ws:
        ws.receive_json()
        ws.send_json({"type": "pause", "data": {"turn_id": "p1"}})
        ack = ws.receive_json()

    assert ack["data"]["accepted"] is True
    assert "p1" in fresh_hitl._paused


# ──────────────────────────────────────────────────────────────────
# HT-06d — 활성 cancel (회귀 대칭)
# ──────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────
# HT-06e — 비활성 turn 에 hitl_response 거부 (Round 17 drift 보완)
# ──────────────────────────────────────────────────────────────────

def test_HT06e_hitl_response_inactive_turn_rejected(hitl_app, fresh_hitl):
    """timeout 된 turn 에 승인/거부 응답 도달 시 turn_not_active ack + signal_resume 호출 없음."""
    client = TestClient(hitl_app)
    with client.websocket_connect("/ws/hitl?user_id=u1") as ws:
        ws.receive_json()
        ws.send_json({
            "type": "hitl_response",
            "data": {
                "request_id": "req_stale",
                "turn_id": "stale_X",
                "action": "approve",
            },
        })
        ack = ws.receive_json()

    assert ack["data"]["accepted"] is False
    assert ack["data"]["reason"] == "turn_not_active"
    # Queue leak 방지 — signal_resume 가 setdefault 로 Queue 생성하지 않음
    assert "stale_X" not in fresh_hitl._resume_queues


# ──────────────────────────────────────────────────────────────────
# HT-06f — 활성 turn 에 hitl_response 회귀 (WH-03 대칭)
# ──────────────────────────────────────────────────────────────────

def test_HT06f_hitl_response_active_turn_passes_regression(hitl_app, fresh_hitl):
    """활성 turn 에 응답 → 가드 통과, signal_resume Queue put (기존 WH-03 동작).

    주 (2026-06-11): Sprint 12 장부 트랙(submit_response) 폐기 — accepted 는 이제
    "재개 신호가 실제 전달됐는가" 기준이라 활성 turn 이면 True (거짓 신호 버그 수정).
    reason 필드는 없어야 함 (turn_not_active 와 구분).
    """
    fresh_hitl.register_turn("t_active")
    client = TestClient(hitl_app)
    with client.websocket_connect("/ws/hitl?user_id=u1") as ws:
        ws.receive_json()
        ws.send_json({
            "type": "hitl_response",
            "data": {
                "request_id": "req_any",
                "turn_id": "t_active",
                "action": "approve",
            },
        })
        ack = ws.receive_json()

    # 가드 통과 확인 — reason 필드 부재 (turn_not_active 아님)
    assert "reason" not in ack["data"], f"가드 거부됨: {ack}"
    # (2026-06-11) 정직 ack — 재개 신호 전달됐으므로 accepted=True (장부 트랙 폐기)
    assert ack["data"]["accepted"] is True
    # Queue 에 signal 도달 (가드 통과 → signal_resume 실행)
    assert "t_active" in fresh_hitl._resume_queues
    q = fresh_hitl._resume_queues["t_active"]
    assert q.qsize() == 1


def test_HT06d_cancel_active_turn_passes_regression(hitl_app, fresh_hitl):
    fresh_hitl.register_turn("c1")
    # cancel 은 progress 필요 (request_cancel 내부 동작) — 간이 setup
    fresh_hitl.create_progress("c1", {"todos": []})
    client = TestClient(hitl_app)
    with client.websocket_connect("/ws/hitl?user_id=u1") as ws:
        ws.receive_json()
        ws.send_json({"type": "cancel", "data": {"turn_id": "c1"}})
        ack = ws.receive_json()

    assert ack["data"]["accepted"] is True
    # Queue 에 cancel signal put
    assert fresh_hitl._resume_queues["c1"].qsize() == 1
