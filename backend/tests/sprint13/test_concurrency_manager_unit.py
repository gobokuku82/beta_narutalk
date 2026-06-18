"""T2 — ConcurrencyManager Unit 테스트

명세서: docs/_claude/checkpointer/sprint13_test_t2_concurrency_manager_spec.md
대상: backend/app/dream_agent/workflow_managers/concurrency_manager.py

9 케이스 (Unit only, Integration은 T6에서).
"""


# ──────────────────────────────────────────────────────────────────
# CC-01
# ──────────────────────────────────────────────────────────────────

def test_CC01_acquire_basic(fresh_concurrency):
    mgr = fresh_concurrency

    result = mgr.try_acquire("u1", "t1")

    assert result is True
    assert mgr.active_count("u1") == 1
    assert "t1" in mgr._active["u1"]


# ──────────────────────────────────────────────────────────────────
# CC-02
# ──────────────────────────────────────────────────────────────────

def test_CC02_acquire_multiple_within_limit():
    from app.dream_agent.workflow_managers.concurrency_manager import ConcurrencyManager
    mgr = ConcurrencyManager(max_concurrent=3)

    r1 = mgr.try_acquire("u1", "t1")
    r2 = mgr.try_acquire("u1", "t2")
    r3 = mgr.try_acquire("u1", "t3")

    assert r1 is r2 is r3 is True
    assert mgr.active_count("u1") == 3


# ──────────────────────────────────────────────────────────────────
# CC-03 🔴 핵심
# ──────────────────────────────────────────────────────────────────

def test_CC03_acquire_exceeds_limit():
    from app.dream_agent.workflow_managers.concurrency_manager import ConcurrencyManager
    mgr = ConcurrencyManager(max_concurrent=3)

    mgr.try_acquire("u1", "t1")
    mgr.try_acquire("u1", "t2")
    mgr.try_acquire("u1", "t3")

    result = mgr.try_acquire("u1", "t4")

    assert result is False
    assert mgr.active_count("u1") == 3  # 변동 없음
    assert "t4" not in mgr._active.get("u1", set())


# ──────────────────────────────────────────────────────────────────
# CC-04
# ──────────────────────────────────────────────────────────────────

def test_CC04_release_basic(fresh_concurrency):
    mgr = fresh_concurrency
    mgr.try_acquire("u1", "t1")
    mgr.try_acquire("u1", "t2")

    mgr.release("u1", "t1")
    assert mgr.active_count("u1") == 1
    assert "t2" in mgr._active["u1"]

    # 나머지 release → 키 자체 삭제
    mgr.release("u1", "t2")
    assert "u1" not in mgr._active


# ──────────────────────────────────────────────────────────────────
# CC-05
# ──────────────────────────────────────────────────────────────────

def test_CC05_release_idempotent(fresh_concurrency):
    mgr = fresh_concurrency

    # 없는 유저 — 예외 X
    mgr.release("nonexistent_user", "t1")

    # acquire 후 2번 release — 예외 X
    mgr.try_acquire("u1", "t1")
    mgr.release("u1", "t1")
    mgr.release("u1", "t1")

    # 없는 turn_id — 예외 X
    mgr.try_acquire("u2", "t2")
    mgr.release("u2", "nonexistent_turn")
    assert "t2" in mgr._active["u2"]


# ──────────────────────────────────────────────────────────────────
# CC-06
# ──────────────────────────────────────────────────────────────────

def test_CC06_acquire_release_cycle():
    from app.dream_agent.workflow_managers.concurrency_manager import ConcurrencyManager
    mgr = ConcurrencyManager(max_concurrent=3)

    mgr.try_acquire("u1", "t1")
    mgr.try_acquire("u1", "t2")
    mgr.try_acquire("u1", "t3")
    assert mgr.active_count("u1") == 3

    # 1개 release → 슬롯 비어짐
    mgr.release("u1", "t1")
    assert mgr.active_count("u1") == 2

    # 새 turn 추가 성공
    result = mgr.try_acquire("u1", "t4")
    assert result is True
    assert mgr.active_count("u1") == 3


# ──────────────────────────────────────────────────────────────────
# CC-07 — 멱등성 (같은 turn_id 재 acquire)
# ──────────────────────────────────────────────────────────────────

def test_CC07_acquire_same_turn_idempotent():
    from app.dream_agent.workflow_managers.concurrency_manager import ConcurrencyManager
    mgr = ConcurrencyManager(max_concurrent=3)

    r1 = mgr.try_acquire("u1", "t1")
    r2 = mgr.try_acquire("u1", "t1")  # 같은 turn 재시도

    assert r1 is True
    assert r2 is True  # 이미 있어도 허용 (멱등)
    assert mgr.active_count("u1") == 1  # set이므로 중복 X


# ──────────────────────────────────────────────────────────────────
# CC-08 — 유저 격리
# ──────────────────────────────────────────────────────────────────

def test_CC08_isolation_between_users():
    from app.dream_agent.workflow_managers.concurrency_manager import ConcurrencyManager
    mgr = ConcurrencyManager(max_concurrent=2)

    mgr.try_acquire("u1", "t1")
    mgr.try_acquire("u1", "t2")
    mgr.try_acquire("u2", "t3")
    mgr.try_acquire("u2", "t4")

    assert mgr.active_count("u1") == 2
    assert mgr.active_count("u2") == 2

    # 각 유저 MAX 초과 시도
    assert mgr.try_acquire("u1", "t5") is False
    assert mgr.try_acquire("u2", "t6") is False

    # u1 release → u2 영향 없음
    mgr.release("u1", "t1")
    assert mgr.active_count("u1") == 1
    assert mgr.active_count("u2") == 2


# ──────────────────────────────────────────────────────────────────
# CC-09 — 서버 재시작 시뮬 (C-3)
# ──────────────────────────────────────────────────────────────────

def test_CC09_reset_clears_all(fresh_concurrency):
    mgr = fresh_concurrency

    mgr.try_acquire("u1", "t1")
    mgr.try_acquire("u1", "t2")
    mgr.try_acquire("u2", "t3")
    assert mgr.active_count("u1") == 2
    assert mgr.active_count("u2") == 1

    mgr._reset_for_test()

    assert mgr._active == {}
    assert mgr.active_count("u1") == 0
    assert mgr.active_count("u2") == 0

    # 리셋 후 새 acquire 정상
    assert mgr.try_acquire("u1", "t_new") is True
