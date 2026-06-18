"""ADR-011 Stage 1-3 — 이중 채널 dedup 통합 테스트 (RED).

핵심 시나리오: 한 user_id 가 /ws/agent + /ws/hitl 둘 다 연결한 상태에서
- agent 채널 broadcast 는 agent 소켓만 받는다 (hitl leak 없음)
- hitl 채널 broadcast 는 hitl 소켓만 받는다 (agent leak 없음)

Stage 1 RED — 옛 시그니처에서는 한 user_id 의 모든 ws 에 fan-out 되어
*두 소켓이 같은 메시지를 받음* (P1 통합 직후 "답변 중복" 버그 메커니즘).

Stage 2 GREEN 후 모두 통과 — 진정한 채널 격리 증명.

명세: docs/agent_specs/adr/ADR-011_connection_channel_separation.md
spec: docs/agent_specs/21_WEBSOCKET_PROTOCOL_v1.5.md §1.2 §3.2
"""

import pytest
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.testclient import TestClient


@pytest.fixture
def dual_channel_app():
    """최소 FastAPI 앱 — /ws/agent + /ws/hitl 둘 다 같은 ConnectionManager 사용.

    각 핸들러는 자기 채널로 connect/disconnect 호출.
    테스트 도우미: /trigger/agent 또는 /trigger/hitl POST → 해당 채널 broadcast.
    """
    from api_v2.connection_manager import ConnectionManager

    app = FastAPI()
    mgr = ConnectionManager(max_connections=5)
    app.state.mgr = mgr

    @app.websocket("/ws/agent")
    async def ws_agent(ws: WebSocket, user_id: str = Query("demo")):
        await ws.accept()
        if not await app.state.mgr.connect(user_id, "agent", ws):
            return
        try:
            while True:
                msg = await ws.receive_json()
                if msg.get("type") == "trigger_agent_broadcast":
                    # 테스트에서 어떤 ws 가 송신해도 agent 채널 전체 broadcast.
                    await app.state.mgr.broadcast_to_user(
                        user_id, "agent", {"type": "complete", "data": {"status": "success"}}
                    )
        except WebSocketDisconnect:
            await app.state.mgr.disconnect(user_id, "agent", ws)

    @app.websocket("/ws/hitl")
    async def ws_hitl(ws: WebSocket, user_id: str = Query("demo")):
        await ws.accept()
        if not await app.state.mgr.connect(user_id, "hitl", ws):
            return
        try:
            while True:
                msg = await ws.receive_json()
                if msg.get("type") == "trigger_hitl_broadcast":
                    await app.state.mgr.broadcast_to_user(
                        user_id, "hitl", {"type": "hitl_ack", "data": {"action": "approve", "accepted": True}}
                    )
        except WebSocketDisconnect:
            await app.state.mgr.disconnect(user_id, "hitl", ws)

    return app


# ──────────────────────────────────────────────────────────────────
# D-01 — agent broadcast → hitl 채널 leak 없음 (P1 답변 중복 메커니즘 차단)
# ──────────────────────────────────────────────────────────────────


def test_D01_agent_broadcast_does_not_leak_to_hitl(dual_channel_app):
    """agent 채널 broadcast 후 hitl 채널 broadcast — hitl 의 *첫* 메시지가 hitl_ack 이면
    agent broadcast 가 hitl 로 leak 안 됐음. (leak 됐다면 hitl 큐의 첫 메시지가 complete 였음)."""
    client = TestClient(dual_channel_app)

    with client.websocket_connect("/ws/agent?user_id=u1") as ws_agent, \
         client.websocket_connect("/ws/hitl?user_id=u1") as ws_hitl:

        # 1. agent 채널에 broadcast.
        ws_agent.send_json({"type": "trigger_agent_broadcast"})
        agent_msg = ws_agent.receive_json()
        assert agent_msg["type"] == "complete"

        # 2. hitl 채널에 별도 broadcast.
        ws_hitl.send_json({"type": "trigger_hitl_broadcast"})
        hitl_first = ws_hitl.receive_json()

        # leak 됐다면 hitl 큐의 첫 메시지가 step 1 의 complete 였을 것.
        # 정상이면 hitl_ack 만 와야 함.
        assert hitl_first["type"] == "hitl_ack", (
            f"hitl 첫 메시지가 hitl_ack 이 아님 — agent broadcast leak 의심: {hitl_first}"
        )


# ──────────────────────────────────────────────────────────────────
# D-02 — hitl broadcast → agent 채널 leak 없음
# ──────────────────────────────────────────────────────────────────


def test_D02_hitl_broadcast_does_not_leak_to_agent(dual_channel_app):
    """hitl broadcast 후 agent broadcast — agent 첫 메시지가 complete 이면 leak 없음."""
    client = TestClient(dual_channel_app)

    with client.websocket_connect("/ws/agent?user_id=u1") as ws_agent, \
         client.websocket_connect("/ws/hitl?user_id=u1") as ws_hitl:

        # 1. hitl 채널에 broadcast.
        ws_hitl.send_json({"type": "trigger_hitl_broadcast"})
        hitl_msg = ws_hitl.receive_json()
        assert hitl_msg["type"] == "hitl_ack"

        # 2. agent 채널에 별도 broadcast.
        ws_agent.send_json({"type": "trigger_agent_broadcast"})
        agent_first = ws_agent.receive_json()

        # leak 됐다면 agent 큐의 첫 메시지가 step 1 의 hitl_ack 였을 것.
        assert agent_first["type"] == "complete", (
            f"agent 첫 메시지가 complete 아님 — hitl broadcast leak 의심: {agent_first}"
        )


# ──────────────────────────────────────────────────────────────────
# D-03 — 자료구조 격리 확인
# ──────────────────────────────────────────────────────────────────


def test_D03_connection_manager_structure_after_dual_connect(dual_channel_app):
    """두 채널 연결 후 _connections 자료구조 확인 — (user, channel) 분리."""
    client = TestClient(dual_channel_app)

    with client.websocket_connect("/ws/agent?user_id=u1") as ws_agent, \
         client.websocket_connect("/ws/hitl?user_id=u1") as ws_hitl:

        mgr = dual_channel_app.state.mgr
        assert "u1" in mgr._connections
        assert "agent" in mgr._connections["u1"]
        assert "hitl" in mgr._connections["u1"]
        assert len(mgr._connections["u1"]["agent"]) == 1
        assert len(mgr._connections["u1"]["hitl"]) == 1


# ──────────────────────────────────────────────────────────────────
# D-04 — 한 채널 disconnect 시 다른 채널 영향 X
# ──────────────────────────────────────────────────────────────────


def test_D04_disconnect_one_channel_other_unaffected(dual_channel_app):
    """agent 채널 close → hitl 채널은 계속 broadcast 받음."""
    client = TestClient(dual_channel_app)

    ws_agent = client.websocket_connect("/ws/agent?user_id=u1").__enter__()
    ws_hitl = client.websocket_connect("/ws/hitl?user_id=u1").__enter__()

    try:
        # agent 닫기.
        ws_agent.close()

        # hitl 은 여전히 동작.
        ws_hitl.send_json({"type": "trigger_hitl_broadcast"})
        msg = ws_hitl.receive_json()
        assert msg["type"] == "hitl_ack"

        # 서버 측 자료구조 — agent 제거, hitl 유지.
        mgr = dual_channel_app.state.mgr
        # agent 채널은 빈 list 또는 키 자체 제거 (구현 정책).
        agent_list = mgr._connections.get("u1", {}).get("agent", [])
        assert len(agent_list) == 0
        # hitl 은 1개 유지.
        assert len(mgr._connections["u1"]["hitl"]) == 1
    finally:
        ws_hitl.close()
