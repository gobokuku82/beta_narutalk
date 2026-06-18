"""동시 실행 turn 개수 제어 (Sprint 13).

유저당 `MAX_CONCURRENT_TURNS_PER_USER` 초과 시 신규 쿼리 거부.

자료구조:
  _active: dict[user_id, set[turn_id]]

**sync 메서드** — 순수 메모리 연산이라 asyncio atomic (P1).

명세서: docs/_claude/checkpointer/sprint13_test_t2_concurrency_manager_spec.md
정책: docs/_claude/checkpointer/sprint13_session_thread_redesign_plan.md §3.5, §3.5.1
"""


_DEFAULT_MAX_CONCURRENT = 3


class ConcurrencyManager:
    """유저당 동시 실행 turn 슬롯 관리.

    DI 주입:
      ConcurrencyManager(max_concurrent=3)  # 테스트용 명시 주입
      ConcurrencyManager()                   # settings에서 조회 (프로덕션)
    """

    def __init__(self, max_concurrent: int | None = None):
        self._active: dict[str, set[str]] = {}
        self._max_concurrent = max_concurrent

    def _get_max(self) -> int:
        """DI 우선, None이면 settings, 없으면 기본값."""
        if self._max_concurrent is not None:
            return self._max_concurrent
        try:
            from app.core.config import settings
            return getattr(
                settings, "MAX_CONCURRENT_TURNS_PER_USER", _DEFAULT_MAX_CONCURRENT
            )
        except Exception:
            return _DEFAULT_MAX_CONCURRENT

    def try_acquire(self, user_id: str, turn_id: str) -> bool:
        """슬롯 획득 시도.

        - 이미 존재하는 turn_id 재 acquire → True (멱등, set 중복 자동 무시)
        - MAX 미만이면 등록 후 True
        - 초과면 False
        """
        active = self._active.setdefault(user_id, set())
        # CC-07 멱등성: 이미 있으면 True (set.add 무시되므로 count 변동 X)
        if turn_id in active:
            return True
        if len(active) >= self._get_max():
            return False
        active.add(turn_id)
        return True

    def release(self, user_id: str, turn_id: str) -> None:
        """슬롯 해제. 없으면 no-op. set 비면 user_id 키 삭제."""
        if user_id not in self._active:
            return
        self._active[user_id].discard(turn_id)
        if not self._active[user_id]:
            del self._active[user_id]

    def active_count(self, user_id: str) -> int:
        """현재 활성 turn 개수."""
        return len(self._active.get(user_id, set()))

    def _reset_for_test(self) -> None:
        """테스트 전용 — 프로덕션 호출 금지.

        서버 재시작 시뮬 (§3.5.1 C-3 정책 실증용).
        언더스코어 prefix로 프로덕션 실수 호출 방지.
        """
        self._active = {}


# 싱글톤 — 프로덕션 기본
concurrency = ConcurrencyManager()
