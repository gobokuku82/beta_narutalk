"""CallbackManager — 세션별 이벤트 라우팅 매니저

Executor, Stage 등 내부 컴포넌트에서 발생하는 이벤트를
WebSocket, 로그 등 외부 리스너에게 전달.

EventBus(api_v2/event_bus.py)의 기능을 흡수 + 다중 리스너 지원.
"""

from __future__ import annotations

from typing import Any, Callable, Coroutine, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)

CallbackType = Callable[[dict[str, Any]], Coroutine[Any, Any, None]]


class CallbackManager:
    """세션별 다중 리스너 이벤트 라우팅."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[CallbackType]] = {}

    def register(self, session_id: str, callback: CallbackType) -> None:
        if session_id not in self._listeners:
            self._listeners[session_id] = []
        self._listeners[session_id].append(callback)
        logger.debug("CallbackManager registered", session_id=session_id)

    def unregister(self, session_id: str) -> None:
        self._listeners.pop(session_id, None)
        logger.debug("CallbackManager unregistered", session_id=session_id)

    async def emit(self, session_id: str, event: dict[str, Any]) -> None:
        for cb in self._listeners.get(session_id, []):
            try:
                await cb(event)
            except Exception as e:
                logger.warning(
                    "CallbackManager emit failed",
                    session_id=session_id,
                    error=str(e),
                )


_manager: Optional[CallbackManager] = None


def get_callback_manager() -> CallbackManager:
    global _manager
    if _manager is None:
        _manager = CallbackManager()
    return _manager
