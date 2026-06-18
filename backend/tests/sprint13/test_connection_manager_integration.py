"""T1 Level 2 — ConnectionManager Integration 테스트 (실 WebSocket)

FastAPI TestClient.websocket_connect() 로 실제 ASGI WS 업그레이드 경로 검증.

명세서: docs/_claude/checkpointer/sprint13_test_t1_connection_manager_spec.md §6
"""

import pytest
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.testclient import TestClient


# ──────────────────────────────────────────────────────────────────
# Fixture — 최소 FastAPI 앱 (Integration 전용)
# ──────────────────────────────────────────────────────────────────

@pytest.fixture
def integration_app():
    """/ws/agent 엔드포인트만 갖는 최소 앱.

    max_connections 값은 테스트마다 별도 manager로 주입받으므로
    Request가 아니라 app.state에 저장하여 테스트에서 관찰 가능.
    """
    from api_v2.connection_manager import ConnectionManager

    app = FastAPI()
    mgr = ConnectionManager(max_connections=5)  # 기본값
    app.state.mgr = mgr

    @app.websocket("/ws/agent")
    async def ws_agent(ws: WebSocket, user_id: str = Query("demo")):
        await ws.accept()
        if not await app.state.mgr.connect(user_id, "agent", ws):
            return  # connect 내부에서 close 완료
        try:
            while True:
                msg = await ws.receive_json()
                if msg.get("type") == "ping":
                    await app.state.mgr.broadcast_to_user(
                        user_id, "agent", {"type": "pong", "echo": msg}
                    )
        except WebSocketDisconnect:
            await app.state.mgr.disconnect(user_id, "agent", ws)

    return app


@pytest.fixture
def integration_app_max2():
    """MAX=2로 제한된 별도 앱 (I-02 전용)."""
    from api_v2.connection_manager import ConnectionManager

    app = FastAPI()
    mgr = ConnectionManager(max_connections=2)
    app.state.mgr = mgr

    @app.websocket("/ws/agent")
    async def ws_agent(ws: WebSocket, user_id: str = Query("demo")):
        await ws.accept()
        if not await app.state.mgr.connect(user_id, "agent", ws):
            return
        try:
            while True:
                await ws.receive_json()
        except WebSocketDisconnect:
            await app.state.mgr.disconnect(user_id, "agent", ws)

    return app


# ──────────────────────────────────────────────────────────────────
# I-01
# ──────────────────────────────────────────────────────────────────

def test_I01_real_ws_connect(integration_app):
    """실 WS 연결 성공 → 서버 측 manager에 등록됨."""
    client = TestClient(integration_app)
    with client.websocket_connect("/ws/agent?user_id=u1"):
        assert len(integration_app.state.mgr._connections["u1"]["agent"]) == 1


# ──────────────────────────────────────────────────────────────────
# I-02 — MAX 초과 시 서버가 close(1008) 발송, 클라 WebSocketDisconnect 수신
# ──────────────────────────────────────────────────────────────────

def test_I02_real_ws_max_exceeded(integration_app_max2):
    """MAX=2 환경에서 3번째 연결 거부."""
    client = TestClient(integration_app_max2)

    ws1 = client.websocket_connect("/ws/agent?user_id=u1").__enter__()
    ws2 = client.websocket_connect("/ws/agent?user_id=u1").__enter__()

    try:
        # 3번째 — 서버가 close(1008) 보냄
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect("/ws/agent?user_id=u1") as ws3:
                # 연결 직후 서버 측 close로 인해 receive 시 예외
                ws3.receive_text()

        assert exc_info.value.code == 1008
        assert len(integration_app_max2.state.mgr._connections["u1"]["agent"]) == 2
    finally:
        ws1.close()
        ws2.close()


# ──────────────────────────────────────────────────────────────────
# I-03 — 같은 유저 WS 2개 → broadcast → 양쪽 수신
# ──────────────────────────────────────────────────────────────────

def test_I03_real_ws_broadcast(integration_app):
    client = TestClient(integration_app)

    with client.websocket_connect("/ws/agent?user_id=u1") as ws_a, \
         client.websocket_connect("/ws/agent?user_id=u1") as ws_b:

        # ws_a가 ping → 서버가 broadcast → ws_a + ws_b 양쪽 수신
        ws_a.send_json({"type": "ping", "from": "a"})

        msg_a = ws_a.receive_json()
        msg_b = ws_b.receive_json()

        assert msg_a["type"] == "pong"
        assert msg_b["type"] == "pong"
        assert msg_a == msg_b  # 동일 메시지


# ──────────────────────────────────────────────────────────────────
# I-04 — 한 WS close 후 남은 WS 정상 수신
# ──────────────────────────────────────────────────────────────────

def test_I04_real_ws_disconnect_cleanup(integration_app):
    client = TestClient(integration_app)

    ws_a = client.websocket_connect("/ws/agent?user_id=u1").__enter__()
    ws_b = client.websocket_connect("/ws/agent?user_id=u1").__enter__()

    assert len(integration_app.state.mgr._connections["u1"]["agent"]) == 2

    # ws_a close
    ws_a.close()

    # ws_b에서 ping → 서버가 broadcast 시도
    # ws_a는 끊긴 상태이므로 두 경로 중 하나로 정리됨:
    #   (a) WebSocketDisconnect 예외 → mgr.disconnect(ws_a)
    #   (b) broadcast send 실패 → dead 자동 정리
    ws_b.send_json({"type": "ping"})
    msg_b = ws_b.receive_json()
    assert msg_b["type"] == "pong"

    # 남은 연결 1개만 (ws_a 제거됨)
    # 주의: ws_b (클라이언트 객체 WebSocketTestSession) ≠ 서버 리스트의 WebSocket
    #       객체 동일성(`in`) 비교 불가. 개수로 확인.
    assert len(integration_app.state.mgr._connections.get("u1", {}).get("agent", [])) == 1

    ws_b.close()
