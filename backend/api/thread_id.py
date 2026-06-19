"""thread_id 조합/분해 헬퍼 (Sprint 13).

LangGraph Checkpointer의 thread_id를 conversation_id + turn_id 조합으로 구성.

형식: f"{conversation_id}_{turn_id}"
전제: 두 ID 모두 UUID v4 (클라이언트 crypto.randomUUID() 발급).
      UUID는 `-`만 포함하므로 `_` 구분자 안전.
"""

from __future__ import annotations


def make_thread_id(conversation_id: str, turn_id: str) -> str:
    """conversation_id + turn_id → thread_id.

    Example:
        >>> make_thread_id("550e...", "6ba7...")
        '550e..._6ba7...'
    """
    return f"{conversation_id}_{turn_id}"


def parse_thread_id(thread_id: str) -> tuple[str, str]:
    """thread_id 분해 → (conversation_id, turn_id).

    첫 `_` 구분자 기준 split. UUID 전제이므로 `_` 1개만 존재.

    Raises:
        ValueError: `_` 구분자 없거나 빈 문자열.
    """
    if not thread_id or "_" not in thread_id:
        raise ValueError(
            f"invalid thread_id format: {thread_id!r} (expected 'conv_turn')"
        )
    idx = thread_id.index("_")
    return thread_id[:idx], thread_id[idx + 1:]
