"""ADR-011 Stage 1-4 — spec 21 v1.5 §3.2 카탈로그 Contract 테스트 (RED).

spec 21 v1.5 §3.2 가 /ws/hitl Server→Client 카탈로그를 4종으로 엄격 정의:
  - connected
  - pong
  - error
  - hitl_ack

본 테스트는 *agent 채널 이벤트가 hitl 채널로 leak 안 됨* 을 contract 로 검증.
spec 위반 leak 이 다시 나타나면 본 테스트가 첫번째로 fail.

명세: docs/agent_specs/21_WEBSOCKET_PROTOCOL_v1.5.md §3.2
ADR: docs/agent_specs/adr/ADR-011_connection_channel_separation.md
"""

from typing import Final

import pytest

from .test_connection_manager_unit import MockWebSocket


# spec 21 v1.5 §3.2 — /ws/hitl Server→Client 정식 카탈로그.
HITL_ALLOWED_TYPES: Final[frozenset[str]] = frozenset({
    "connected",
    "pong",
    "error",
    "hitl_ack",
})

# spec 21 v1.5 §2.2 — /ws/agent Server→Client 카탈로그 (참고).
AGENT_ONLY_TYPES: Final[frozenset[str]] = frozenset({
    "node_event",
    "hitl_request",
    "paused",
    "resumed",
    "complete",
    "layer_start",
    "todo_start",
    "todo_complete",
    "progress",
})


# ──────────────────────────────────────────────────────────────────
# K-01 — agent-only type 들이 hitl 소켓에 도착하지 않음 (12종)
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("msg_type", sorted(AGENT_ONLY_TYPES))
async def test_K01_agent_only_type_never_reaches_hitl_socket(
    fresh_conn_manager, msg_type: str
):
    """spec 21 §2.2 의 agent-only type 이 broadcast_to_user(uid, 'agent', ...) 호출 시
    hitl 소켓에 도착하면 안 됨."""
    mgr = fresh_conn_manager
    ws_agent = MockWebSocket("agent")
    ws_hitl = MockWebSocket("hitl")
    await mgr.connect("u1", "agent", ws_agent)
    await mgr.connect("u1", "hitl", ws_hitl)

    msg = {"type": msg_type, "data": {}}
    await mgr.broadcast_to_user("u1", "agent", msg)

    # agent 만 받음.
    assert ws_agent.sent == [msg], f"agent 소켓이 {msg_type} 받아야 함"
    # hitl 은 절대 안 받음 — spec 21 §3.2 contract.
    assert ws_hitl.sent == [], (
        f"hitl 소켓이 agent-only type '{msg_type}' 을 받음 — spec 21 §3.2 위반"
    )


# ──────────────────────────────────────────────────────────────────
# K-02 — hitl 카탈로그의 4종은 hitl 채널로 broadcast 가능
# ──────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("msg_type", sorted(HITL_ALLOWED_TYPES))
async def test_K02_hitl_allowed_type_reaches_hitl_socket(
    fresh_conn_manager, msg_type: str
):
    """spec 21 §3.2 카탈로그의 4종은 hitl 채널로 정상 broadcast."""
    mgr = fresh_conn_manager
    ws_hitl = MockWebSocket("hitl")
    await mgr.connect("u1", "hitl", ws_hitl)

    msg = {"type": msg_type, "data": {}}
    await mgr.broadcast_to_user("u1", "hitl", msg)

    assert ws_hitl.sent == [msg]


# ──────────────────────────────────────────────────────────────────
# K-03 — agent 채널이 hitl 카탈로그 type 을 보낼 수도 있음 (connected 등 공통)
#         단, 채널 호출 시 채널 안에서만 격리 되어야 함
# ──────────────────────────────────────────────────────────────────


async def test_K03_common_types_are_per_channel_isolated(fresh_conn_manager):
    """connected / pong / error 는 양 채널 공통 type 이지만,
    broadcast 시 호출된 채널 안에서만 fan-out — 다른 채널 leak X."""
    mgr = fresh_conn_manager
    ws_agent = MockWebSocket("agent")
    ws_hitl = MockWebSocket("hitl")
    await mgr.connect("u1", "agent", ws_agent)
    await mgr.connect("u1", "hitl", ws_hitl)

    # agent 채널로 connected 송신.
    await mgr.broadcast_to_user("u1", "agent", {"type": "connected"})
    assert ws_agent.sent == [{"type": "connected"}]
    assert ws_hitl.sent == []  # hitl 안 받음

    # hitl 채널로 별도 connected 송신.
    await mgr.broadcast_to_user("u1", "hitl", {"type": "connected", "channel": "hitl"})
    assert ws_hitl.sent == [{"type": "connected", "channel": "hitl"}]
    # agent 는 두 번째 connected 안 받음.
    assert ws_agent.sent == [{"type": "connected"}]


# ──────────────────────────────────────────────────────────────────
# K-04 — 카탈로그 갱신 시 본 테스트가 자동으로 알림 (DC 가드)
# ──────────────────────────────────────────────────────────────────


def test_K04_catalog_sizes_match_spec21_v1_5():
    """spec 21 v1.5 의 카탈로그 크기가 코드 상수와 일치.
    spec 갱신 시 본 테스트로 drift 감지."""
    # spec 21 v1.5 §3.2 = 4종 (connected/pong/error/hitl_ack).
    assert len(HITL_ALLOWED_TYPES) == 4

    # spec 21 v1.5 §2.2 agent-only = 9종.
    assert len(AGENT_ONLY_TYPES) == 9

    # 공통 type (connected/pong/error) 은 양쪽 카탈로그에 속할 수 있으나
    # AGENT_ONLY_TYPES 는 hitl 에 없는 것만.
    assert HITL_ALLOWED_TYPES.isdisjoint(AGENT_ONLY_TYPES)
