"""conversation_history → Cognitive 프롬프트 주입 문자열 생성 (Sprint 13).

Sprint 13은 **슬롯만 준비** (빈 history 기본).
Sprint 15 MemoryManager가 실제 데이터 채우면 바로 동작.

명세서: docs/_claude/checkpointer/sprint13_test_t4_history_injector_spec.md
계획서: docs/_claude/checkpointer/sprint13_session_thread_redesign_plan.md §3.6
"""

from __future__ import annotations


_DEFAULT_HISTORY_LIMIT = 3
_DEFAULT_MAX_HISTORY_LIMIT = 10


def _get_default_limit() -> int:
    """settings.DEFAULT_HISTORY_LIMIT 조회, 없으면 3."""
    try:
        from app.core.config import settings
        return getattr(settings, "DEFAULT_HISTORY_LIMIT", _DEFAULT_HISTORY_LIMIT)
    except Exception:
        return _DEFAULT_HISTORY_LIMIT


def _get_max_history_limit() -> int:
    """settings.MAX_HISTORY_LIMIT 조회, 없으면 10.

    monkeypatch로 테스트에서 오버라이드 가능.
    """
    try:
        from app.core.config import settings
        return getattr(settings, "MAX_HISTORY_LIMIT", _DEFAULT_MAX_HISTORY_LIMIT)
    except Exception:
        return _DEFAULT_MAX_HISTORY_LIMIT


def build_context_summary(
    history: list[dict] | None,
    limit: int | None = None,
) -> str:
    """conversation_history를 프롬프트 주입용 문자열로 변환.

    Args:
        history: 최신순 list (index 0=오래된, -1=최근). None 또는 [] 허용.
            요소 필드: turn_index, user_input, response_summary (누락 시 빈 값)
        limit: 주입할 최근 N개. None이면 settings.DEFAULT_HISTORY_LIMIT.
            MAX_HISTORY_LIMIT 초과 요청은 자동 clip.

    Returns:
        포맷팅된 문자열. 빈 값이면 "".
        각 turn 포맷: "[T{turn_index}] 사용자: {user_input} → 답변: {response_summary}"
    """
    if not history:
        return ""

    # limit 결정 + MAX clip
    if limit is None:
        limit = _get_default_limit()
    if limit <= 0:
        return ""
    max_limit = _get_max_history_limit()
    effective_limit = min(limit, max_limit)

    # tail N개 (최근)
    selected = history[-effective_limit:]

    lines = []
    for t in selected:
        idx = t.get("turn_index", "?")
        user = t.get("user_input", "")
        answer = t.get("response_summary", "")
        lines.append(f"[T{idx}] 사용자: {user} → 답변: {answer}")

    return "\n".join(lines)
