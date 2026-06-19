"""WebSocket 멀티플렉싱 ConnectionManager (Sprint 13 T1 + ADR-011 채널 분리).

(user_id, channel) 쌍 기반 연결 관리 + fan-out broadcast.
- 채널: "agent" / "hitl" — spec 21 v1.5 §1.2 (ADR-011)
- 유저+채널당 WS 여러 개 (multi-tab 동기화 의도 보존)
- MAX_WS_CONNECTIONS_PER_USER 초과 차단 — (user, channel) 별 카운트
- 전송 실패 WS 자동 정리 (P2)
- asyncio 단일 스레드 atomic 활용 (P1)

명세서:
- docs/agent_specs/21_WEBSOCKET_PROTOCOL_v1.5.md §1.2 §1.3 §3.2
- docs/agent_specs/adr/ADR-011_connection_channel_separation.md
- docs/_claude/checkpointer/sprint13_test_t1_connection_manager_spec.md §2.1 (v1 이력)
"""

from typing import Any, Literal


# 채널 타입 — spec 21 v1.5 §1.2.
Channel = Literal["agent", "hitl"]

# 기본 상한 — Sprint 13에서 settings.MAX_WS_CONNECTIONS_PER_USER 필드 추가 예정.
# ADR-011: (user, channel) 별 카운트 — 한 사용자가 agent 5 + hitl 5 = 총 10 ws 가능.
_DEFAULT_MAX_CONNECTIONS = 5


class ConnectionManager:
    """`(user_id, channel)` → `[WebSocket, ...]` 관리.

    DI 주입:
      ConnectionManager(max_connections=5)  # 테스트용 명시 주입
      ConnectionManager()                    # settings에서 조회 (프로덕션)

    내부 자료구조 (spec 21 v1.5 §1.2):
      _connections: dict[user_id, dict[channel, list[WebSocket]]]
      예: {"demo": {"agent": [ws1, ws2], "hitl": [ws3]}}
    """

    def __init__(self, max_connections: int | None = None):
        self._connections: dict[str, dict[Channel, list[Any]]] = {}
        self._max_connections = max_connections

    def _get_max(self) -> int:
        """DI 우선, None이면 settings, 없으면 기본값."""
        if self._max_connections is not None:
            return self._max_connections
        try:
            from app.core.config import settings
            return getattr(
                settings, "MAX_WS_CONNECTIONS_PER_USER", _DEFAULT_MAX_CONNECTIONS
            )
        except Exception:
            return _DEFAULT_MAX_CONNECTIONS

    async def connect(self, user_id: str, channel: Channel, ws: Any) -> bool:
        """`(user_id, channel)` 등록.

        성공 True. (user, channel) 별 MAX 초과 시 close(1008) + False.
        MAX 정책 = (user, channel) 별 — agent 5 + hitl 5 = 총 10 ws 가능.
        """
        channels = self._connections.setdefault(user_id, {})
        current = channels.get(channel, [])
        if len(current) >= self._get_max():
            await ws.close(code=1008, reason="connection_limit_exceeded")
            return False
        channels.setdefault(channel, []).append(ws)
        return True

    async def disconnect(self, user_id: str, channel: Channel, ws: Any) -> None:
        """`(user_id, channel)` 에서 WS 제거. idempotent."""
        if user_id not in self._connections:
            return
        channels = self._connections[user_id]
        if channel not in channels:
            return
        channels[channel] = [w for w in channels[channel] if w is not ws]
        if not channels[channel]:
            del channels[channel]
        if not channels:
            del self._connections[user_id]

    async def broadcast_to_user(
        self, user_id: str, channel: Channel, message: dict
    ) -> None:
        """`(user_id, channel)` 의 모든 WS 에 fan-out. 실패 WS 자동 disconnect.

        다른 채널로 leak 되지 않음 — spec 21 v1.5 §1.2 / §3.2 카탈로그 정합.
        list(...) 복사본 순회 — send_json await 중 _connections 수정 안전 (P1).
        dead WS 즉시 disconnect로 다음 broadcast 낭비 방지 (P2).
        """
        channels = self._connections.get(user_id, {})
        target_list = channels.get(channel, [])
        dead = []
        for ws in list(target_list):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(user_id, channel, ws)


# 싱글톤 — 프로덕션 기본
conn_manager = ConnectionManager()
