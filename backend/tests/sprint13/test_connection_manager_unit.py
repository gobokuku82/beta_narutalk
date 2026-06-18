"""T1 Level 1 — ConnectionManager Unit 테스트 (Mock WebSocket)

명세서: docs/_claude/checkpointer/sprint13_test_t1_connection_manager_spec.md §5
대상: backend/api_v2/connection_manager.py ConnectionManager

14 케이스 중 10개 (Unit).

ADR-011 (2026-05-16) — 채널 분리 후 시그니처 마이그레이션:
- connect/disconnect/broadcast_to_user 에 channel="agent" 추가.
- _connections["u1"] 직접 접근은 _connections["u1"]["agent"] 로 변경.
- 본 파일은 agent 채널 기준 회귀 — 채널 격리 자체 검증은
  test_connection_manager_channel.py (신규) 에 별도.
"""

import asyncio
import pytest


# ──────────────────────────────────────────────────────────────────
# Mock WebSocket (명세서 §3)
# ──────────────────────────────────────────────────────────────────

class MockWebSocket:
    """실 Starlette WebSocket의 최소 호환 Mock.

    send_json / close 만 제공. accept는 외부에서 호출된 것으로 가정.
    """

    def __init__(self, name: str, raise_on_send: bool = False):
        self.name = name
        self.raise_on_send = raise_on_send
        self.sent: list[dict] = []
        self.closed = False
        self.close_code: int | None = None
        self.close_reason: str | None = None

    async def send_json(self, data: dict) -> None:
        if self.raise_on_send:
            raise ConnectionError(f"{self.name} disconnected")
        self.sent.append(data)

    async def close(self, code: int | None = None, reason: str | None = None) -> None:
        self.closed = True
        self.close_code = code
        self.close_reason = reason


# ──────────────────────────────────────────────────────────────────
# C-01
# ──────────────────────────────────────────────────────────────────

async def test_C01_connect_basic(fresh_conn_manager):
    mgr = fresh_conn_manager
    ws1 = MockWebSocket("A")

    result = await mgr.connect("u1", "agent", ws1)

    assert result is True
    assert mgr._connections["u1"]["agent"] == [ws1]
    assert ws1.closed is False


# ──────────────────────────────────────────────────────────────────
# C-02
# ──────────────────────────────────────────────────────────────────

async def test_C02_connect_multiple_tabs(fresh_conn_manager):
    """기본 MAX=5 가정. 5개 모두 성공."""
    mgr = fresh_conn_manager
    ws_list = [MockWebSocket(f"ws_{i}") for i in range(5)]

    results = []
    for ws in ws_list:
        results.append(await mgr.connect("u1", "agent", ws))

    assert all(results), f"모든 connect 성공해야 함: {results}"
    assert len(mgr._connections["u1"]["agent"]) == 5
    assert mgr._connections["u1"]["agent"] == ws_list  # 순서 유지


# ──────────────────────────────────────────────────────────────────
# C-03
# ──────────────────────────────────────────────────────────────────

async def test_C03_connect_exceeds_max():
    """MAX=2로 오버라이드 후 3번째 거부 확인."""
    from api_v2.connection_manager import ConnectionManager
    mgr = ConnectionManager(max_connections=2)  # DI 주입

    ws1, ws2, ws3 = MockWebSocket("A"), MockWebSocket("B"), MockWebSocket("C")

    assert await mgr.connect("u1", "agent", ws1) is True
    assert await mgr.connect("u1", "agent", ws2) is True

    # 3번째 — False + close(1008) 호출
    result3 = await mgr.connect("u1", "agent", ws3)

    assert result3 is False
    assert ws3.closed is True
    assert ws3.close_code == 1008
    assert ws3.close_reason == "connection_limit_exceeded"
    assert len(mgr._connections["u1"]["agent"]) == 2  # 변동 없음


# ──────────────────────────────────────────────────────────────────
# C-04
# ──────────────────────────────────────────────────────────────────

async def test_C04_disconnect_removes_ws(fresh_conn_manager):
    mgr = fresh_conn_manager
    ws1, ws2 = MockWebSocket("A"), MockWebSocket("B")
    await mgr.connect("u1", "agent", ws1)
    await mgr.connect("u1", "agent", ws2)

    await mgr.disconnect("u1", "agent", ws1)

    assert mgr._connections["u1"]["agent"] == [ws2]  # ws1 제거됨

    await mgr.disconnect("u1", "agent", ws2)

    assert "u1" not in mgr._connections  # 빈 리스트면 key 자체 삭제


# ──────────────────────────────────────────────────────────────────
# C-05
# ──────────────────────────────────────────────────────────────────

async def test_C05_disconnect_idempotent(fresh_conn_manager):
    """같은 WS 2번 disconnect → 예외 없음."""
    mgr = fresh_conn_manager
    ws1 = MockWebSocket("A")
    await mgr.connect("u1", "agent", ws1)

    await mgr.disconnect("u1", "agent", ws1)
    # 두 번째 disconnect — 이미 제거된 상태
    await mgr.disconnect("u1", "agent", ws1)  # 예외 나면 안 됨

    assert "u1" not in mgr._connections

    # 존재 안 하는 user_id로 disconnect
    await mgr.disconnect("nonexistent", "agent", ws1)  # 예외 나면 안 됨


# ──────────────────────────────────────────────────────────────────
# C-06
# ──────────────────────────────────────────────────────────────────

async def test_C06_broadcast_to_all_tabs(fresh_conn_manager):
    mgr = fresh_conn_manager
    ws1, ws2, ws3 = MockWebSocket("A"), MockWebSocket("B"), MockWebSocket("C")
    await mgr.connect("u1", "agent", ws1)
    await mgr.connect("u1", "agent", ws2)
    await mgr.connect("u1", "agent", ws3)

    msg = {"type": "test", "n": 1}
    await mgr.broadcast_to_user("u1", "agent", msg)

    assert ws1.sent == [msg]
    assert ws2.sent == [msg]
    assert ws3.sent == [msg]


# ──────────────────────────────────────────────────────────────────
# C-07 🔴 핵심 — dead WS 자동 정리 (P2)
# ──────────────────────────────────────────────────────────────────

async def test_C07_broadcast_dead_ws_auto_cleanup(fresh_conn_manager):
    """ws2 전송 실패 → 자동 disconnect → 리스트에서 제거."""
    mgr = fresh_conn_manager
    ws1 = MockWebSocket("A")
    ws2 = MockWebSocket("B", raise_on_send=True)  # 끊김 시뮬
    ws3 = MockWebSocket("C")

    await mgr.connect("u1", "agent", ws1)
    await mgr.connect("u1", "agent", ws2)
    await mgr.connect("u1", "agent", ws3)

    msg = {"msg": "x"}
    await mgr.broadcast_to_user("u1", "agent", msg)

    # ws1, ws3는 수신
    assert ws1.sent == [msg]
    assert ws3.sent == [msg]
    # ws2는 전송 실패로 sent 비어있음
    assert ws2.sent == []

    # ws2 자동 제거됨
    assert mgr._connections["u1"]["agent"] == [ws1, ws3]

    # 재 broadcast — ws2에 try 안 함 (cleanup 완료 증명)
    msg2 = {"msg": "y"}
    await mgr.broadcast_to_user("u1", "agent", msg2)
    assert ws1.sent == [msg, msg2]
    assert ws3.sent == [msg, msg2]
    assert ws2.sent == []  # 여전히 비어있음 (재시도 없음)


# ──────────────────────────────────────────────────────────────────
# C-08
# ──────────────────────────────────────────────────────────────────

async def test_C08_broadcast_no_connections(fresh_conn_manager):
    """존재하지 않는 user_id로 broadcast — no-op."""
    mgr = fresh_conn_manager

    # 예외 없이 실행되어야 함
    await mgr.broadcast_to_user("nonexistent", "agent", {"msg": "x"})

    assert mgr._connections == {}


# ──────────────────────────────────────────────────────────────────
# C-09
# ──────────────────────────────────────────────────────────────────

async def test_C09_broadcast_isolation_between_users(fresh_conn_manager):
    mgr = fresh_conn_manager
    ws_a = MockWebSocket("A")
    ws_b = MockWebSocket("B")
    ws_c = MockWebSocket("C")
    await mgr.connect("u1", "agent", ws_a)
    await mgr.connect("u1", "agent", ws_b)
    await mgr.connect("u2", "agent", ws_c)

    msg = {"msg": "only u1"}
    await mgr.broadcast_to_user("u1", "agent", msg)

    assert ws_a.sent == [msg]
    assert ws_b.sent == [msg]
    assert ws_c.sent == []  # 격리


# ──────────────────────────────────────────────────────────────────
# C-10 🔴 핵심 — asyncio atomic 실증 (P1)
# ──────────────────────────────────────────────────────────────────

async def test_C10_concurrent_connect_disconnect():
    """10개 동시 connect + 10개 동시 disconnect, 최종 일관 상태."""
    from api_v2.connection_manager import ConnectionManager
    mgr = ConnectionManager(max_connections=10)

    ws_list = [MockWebSocket(f"ws_{i}") for i in range(10)]

    # 동시 connect 10개
    results = await asyncio.gather(*[mgr.connect("u1", "agent", ws) for ws in ws_list])
    assert all(results), f"모든 connect 성공해야 함: {results}"
    assert len(mgr._connections["u1"]["agent"]) == 10

    # 동시 disconnect 10개
    await asyncio.gather(*[mgr.disconnect("u1", "agent", ws) for ws in ws_list])

    # 최종 상태: 비어있음
    assert "u1" not in mgr._connections, (
        f"모든 disconnect 후 키 삭제 실패: {mgr._connections}"
    )
