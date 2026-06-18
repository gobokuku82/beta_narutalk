"""ADR-011 Stage 1 — ConnectionManager 채널 분리 RED 테스트.

본 파일은 *변경 후* (Stage 2 GREEN) 의 동작을 명세.
Stage 1 시점에는 모두 fail (RED) — 옛 ConnectionManager 가 channel 인자 없음.

ADR: docs/agent_specs/adr/ADR-011_connection_channel_separation.md
spec: docs/agent_specs/21_WEBSOCKET_PROTOCOL_v1.5.md §1.2

내용:
- C-CH-01 ~ C-CH-08: 채널 분리 기본 동작 + 격리
- C-CH-09 ~ C-CH-11: MAX 정책 (user, channel) 별
- C-CH-12 ~ C-CH-14: multi-tab 동기화 의도 보존
- C-CH-15 ~ C-CH-16: dead WS cleanup (채널 컨텍스트)
"""

import asyncio
import pytest

from .test_connection_manager_unit import MockWebSocket


# ──────────────────────────────────────────────────────────────────
# C-CH-01 ~ C-CH-04: 채널 인자 도입 (기본)
# ──────────────────────────────────────────────────────────────────


async def test_CH01_connect_with_channel(fresh_conn_manager):
    """connect(user_id, channel, ws) — agent 채널 등록."""
    mgr = fresh_conn_manager
    ws = MockWebSocket("agent_ws")

    result = await mgr.connect("u1", "agent", ws)

    assert result is True
    assert mgr._connections["u1"]["agent"] == [ws]
    # hitl 채널은 아예 없음 — 자료구조 격리.
    assert "hitl" not in mgr._connections.get("u1", {})


async def test_CH02_connect_hitl_channel(fresh_conn_manager):
    """connect(user_id, 'hitl', ws) — hitl 채널 등록."""
    mgr = fresh_conn_manager
    ws = MockWebSocket("hitl_ws")

    await mgr.connect("u1", "hitl", ws)

    assert mgr._connections["u1"]["hitl"] == [ws]
    assert "agent" not in mgr._connections.get("u1", {})


async def test_CH03_disconnect_with_channel(fresh_conn_manager):
    """disconnect(user_id, channel, ws) — 해당 채널만 제거."""
    mgr = fresh_conn_manager
    ws_agent = MockWebSocket("agent")
    ws_hitl = MockWebSocket("hitl")

    await mgr.connect("u1", "agent", ws_agent)
    await mgr.connect("u1", "hitl", ws_hitl)
    await mgr.disconnect("u1", "agent", ws_agent)

    # agent 만 제거, hitl 유지.
    assert "agent" not in mgr._connections.get("u1", {})
    assert mgr._connections["u1"]["hitl"] == [ws_hitl]


async def test_CH04_disconnect_idempotent(fresh_conn_manager):
    """disconnect 중복 호출 — 예외 없이 idempotent."""
    mgr = fresh_conn_manager
    ws = MockWebSocket("a")
    await mgr.connect("u1", "agent", ws)

    await mgr.disconnect("u1", "agent", ws)
    await mgr.disconnect("u1", "agent", ws)  # 2 회차 — 예외 X
    await mgr.disconnect("nonexistent", "agent", ws)  # 존재 안 함 — 예외 X
    await mgr.disconnect("u1", "hitl", ws)  # 빈 채널 — 예외 X


# ──────────────────────────────────────────────────────────────────
# C-CH-05 ~ C-CH-08: broadcast 채널 격리 (핵심 — leak 방지)
# ──────────────────────────────────────────────────────────────────


async def test_CH05_broadcast_only_target_channel(fresh_conn_manager):
    """broadcast_to_user(uid, 'agent', msg) — agent 만 받음, hitl 안 받음."""
    mgr = fresh_conn_manager
    ws_agent = MockWebSocket("agent")
    ws_hitl = MockWebSocket("hitl")
    await mgr.connect("u1", "agent", ws_agent)
    await mgr.connect("u1", "hitl", ws_hitl)

    msg = {"type": "complete", "data": {"status": "success"}}
    await mgr.broadcast_to_user("u1", "agent", msg)

    assert ws_agent.sent == [msg]
    assert ws_hitl.sent == []  # ← 핵심: hitl 로 leak 없음


async def test_CH06_broadcast_hitl_isolated_from_agent(fresh_conn_manager):
    """hitl broadcast — agent 채널 안 옴 (역방향 격리)."""
    mgr = fresh_conn_manager
    ws_agent = MockWebSocket("agent")
    ws_hitl = MockWebSocket("hitl")
    await mgr.connect("u1", "agent", ws_agent)
    await mgr.connect("u1", "hitl", ws_hitl)

    msg = {"type": "hitl_ack", "data": {"action": "approve", "accepted": True}}
    await mgr.broadcast_to_user("u1", "hitl", msg)

    assert ws_hitl.sent == [msg]
    assert ws_agent.sent == []


async def test_CH07_broadcast_isolation_between_users(fresh_conn_manager):
    """다른 user 의 같은 채널 — 격리."""
    mgr = fresh_conn_manager
    ws_u1_a = MockWebSocket("u1_a")
    ws_u2_a = MockWebSocket("u2_a")
    await mgr.connect("u1", "agent", ws_u1_a)
    await mgr.connect("u2", "agent", ws_u2_a)

    msg = {"only": "u1"}
    await mgr.broadcast_to_user("u1", "agent", msg)

    assert ws_u1_a.sent == [msg]
    assert ws_u2_a.sent == []


async def test_CH08_broadcast_no_connection_noop(fresh_conn_manager):
    """존재 안 하는 (user, channel) — no-op, 예외 없음."""
    mgr = fresh_conn_manager

    await mgr.broadcast_to_user("nonexistent", "agent", {"x": 1})
    await mgr.broadcast_to_user("u1", "hitl", {"x": 1})  # u1 등록 0 — 무해

    # 등록 후 다른 채널만 broadcast — 무해
    await mgr.connect("u1", "agent", MockWebSocket("a"))
    await mgr.broadcast_to_user("u1", "hitl", {"x": 1})  # hitl 등록 0


# ──────────────────────────────────────────────────────────────────
# C-CH-09 ~ C-CH-11: MAX 정책 (user, channel) 별
# ──────────────────────────────────────────────────────────────────


async def test_CH09_max_per_channel_not_per_user():
    """ADR-011 결정 — MAX 가 (user, channel) 별. agent 5 + hitl 5 = 10 ws OK."""
    from api_v2.connection_manager import ConnectionManager
    mgr = ConnectionManager(max_connections=2)  # 채널당 2 (테스트 단순화)

    # agent 채널 2개 — OK
    ws_a1, ws_a2 = MockWebSocket("a1"), MockWebSocket("a2")
    assert await mgr.connect("u1", "agent", ws_a1) is True
    assert await mgr.connect("u1", "agent", ws_a2) is True

    # hitl 채널 2개 — OK (agent 와 독립 카운트)
    ws_h1, ws_h2 = MockWebSocket("h1"), MockWebSocket("h2")
    assert await mgr.connect("u1", "hitl", ws_h1) is True
    assert await mgr.connect("u1", "hitl", ws_h2) is True

    # 합 4개여도 MAX 초과 아님.
    assert len(mgr._connections["u1"]["agent"]) == 2
    assert len(mgr._connections["u1"]["hitl"]) == 2


async def test_CH10_max_exceed_per_channel():
    """MAX=2, agent 3번째 거부. hitl 은 영향 안 받음."""
    from api_v2.connection_manager import ConnectionManager
    mgr = ConnectionManager(max_connections=2)

    ws_a1, ws_a2, ws_a3 = (
        MockWebSocket("a1"),
        MockWebSocket("a2"),
        MockWebSocket("a3"),
    )
    await mgr.connect("u1", "agent", ws_a1)
    await mgr.connect("u1", "agent", ws_a2)

    # 3번째 agent — close(1008) 거부.
    result3 = await mgr.connect("u1", "agent", ws_a3)
    assert result3 is False
    assert ws_a3.closed is True
    assert ws_a3.close_code == 1008
    assert ws_a3.close_reason == "connection_limit_exceeded"

    # hitl 은 정상 등록 가능 — 채널별 독립 카운트 증명.
    ws_h1 = MockWebSocket("h1")
    assert await mgr.connect("u1", "hitl", ws_h1) is True


async def test_CH11_concurrent_connect_per_channel():
    """동시 connect 10 개 (channel 분산) — 모두 성공, 일관 상태."""
    from api_v2.connection_manager import ConnectionManager
    mgr = ConnectionManager(max_connections=10)

    agent_ws = [MockWebSocket(f"a{i}") for i in range(5)]
    hitl_ws = [MockWebSocket(f"h{i}") for i in range(5)]

    results = await asyncio.gather(
        *[mgr.connect("u1", "agent", w) for w in agent_ws],
        *[mgr.connect("u1", "hitl", w) for w in hitl_ws],
    )
    assert all(results)
    assert len(mgr._connections["u1"]["agent"]) == 5
    assert len(mgr._connections["u1"]["hitl"]) == 5


# ──────────────────────────────────────────────────────────────────
# C-CH-12 ~ C-CH-14: Multi-tab 동기화 의도 보존
# ──────────────────────────────────────────────────────────────────


async def test_CH12_multi_tab_within_channel_fanout(fresh_conn_manager):
    """spec 21 §1.2 multi-tab 동기화 — 같은 (user, channel) 안의 fan-out."""
    mgr = fresh_conn_manager
    # 같은 user 가 탭 2개 열음 — 각 탭의 ws_agent 둘 다 등록.
    tab1_agent = MockWebSocket("tab1_agent")
    tab2_agent = MockWebSocket("tab2_agent")
    await mgr.connect("u1", "agent", tab1_agent)
    await mgr.connect("u1", "agent", tab2_agent)

    msg = {"type": "complete", "data": {}}
    await mgr.broadcast_to_user("u1", "agent", msg)

    # 두 탭 모두 받음.
    assert tab1_agent.sent == [msg]
    assert tab2_agent.sent == [msg]


async def test_CH13_multi_tab_with_dual_channels(fresh_conn_manager):
    """2 탭 × 2 채널 = 4 ws 등록. agent broadcast 시 2 agent ws 만 받음."""
    mgr = fresh_conn_manager
    tab1_agent = MockWebSocket("t1a")
    tab1_hitl = MockWebSocket("t1h")
    tab2_agent = MockWebSocket("t2a")
    tab2_hitl = MockWebSocket("t2h")
    await mgr.connect("u1", "agent", tab1_agent)
    await mgr.connect("u1", "hitl", tab1_hitl)
    await mgr.connect("u1", "agent", tab2_agent)
    await mgr.connect("u1", "hitl", tab2_hitl)

    msg = {"type": "node_event"}
    await mgr.broadcast_to_user("u1", "agent", msg)

    # agent 채널 2개만 받음.
    assert tab1_agent.sent == [msg]
    assert tab2_agent.sent == [msg]
    # hitl 채널은 아무도 안 받음 — leak 없음.
    assert tab1_hitl.sent == []
    assert tab2_hitl.sent == []


async def test_CH14_disconnect_one_tab_other_tabs_unaffected(fresh_conn_manager):
    """탭 하나 닫혀도 다른 탭의 같은 채널은 유지."""
    mgr = fresh_conn_manager
    t1 = MockWebSocket("t1")
    t2 = MockWebSocket("t2")
    await mgr.connect("u1", "agent", t1)
    await mgr.connect("u1", "agent", t2)

    await mgr.disconnect("u1", "agent", t1)

    assert mgr._connections["u1"]["agent"] == [t2]

    msg = {"x": 1}
    await mgr.broadcast_to_user("u1", "agent", msg)
    assert t2.sent == [msg]
    assert t1.sent == []  # 이미 disconnect 됨


# ──────────────────────────────────────────────────────────────────
# C-CH-15 ~ C-CH-16: dead WS cleanup — 채널 컨텍스트
# ──────────────────────────────────────────────────────────────────


async def test_CH15_dead_ws_cleanup_in_target_channel(fresh_conn_manager):
    """전송 실패 ws 는 *해당 채널* 리스트에서만 제거. 다른 채널 영향 X."""
    mgr = fresh_conn_manager
    ws_a_ok = MockWebSocket("a_ok")
    ws_a_dead = MockWebSocket("a_dead", raise_on_send=True)
    ws_h = MockWebSocket("h")
    await mgr.connect("u1", "agent", ws_a_ok)
    await mgr.connect("u1", "agent", ws_a_dead)
    await mgr.connect("u1", "hitl", ws_h)

    await mgr.broadcast_to_user("u1", "agent", {"x": 1})

    # ws_a_dead 자동 제거.
    assert mgr._connections["u1"]["agent"] == [ws_a_ok]
    # hitl 영향 없음.
    assert mgr._connections["u1"]["hitl"] == [ws_h]


async def test_CH16_empty_channel_key_cleanup(fresh_conn_manager):
    """모든 ws 가 disconnect 되면 (user, channel) 키 자체 정리."""
    mgr = fresh_conn_manager
    ws = MockWebSocket("a")
    await mgr.connect("u1", "agent", ws)
    await mgr.disconnect("u1", "agent", ws)

    # agent 채널 자체가 빈 dict 일 수도 있고 키 삭제일 수도 있음 — 구현 자유.
    # 핵심: broadcast 호출이 no-op 이어야.
    await mgr.broadcast_to_user("u1", "agent", {"x": 1})  # 예외 X

    # user 의 다른 채널도 없으면 user 키 자체 정리.
    user_dict = mgr._connections.get("u1", {})
    assert user_dict.get("agent", []) == []
