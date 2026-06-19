"""ConversationManager 패키지 — 대화(turn) 조회 전용 (checkpoint 읽기).

메모리(MemoryManager)와 분리된 대화 경로 매니저.
"""
from .manager import ConversationManager

__all__ = ["ConversationManager"]
