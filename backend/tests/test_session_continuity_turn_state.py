"""세션 연속성 P3 — 턴 라이브 상태 스냅샷(build_turn_state) 단위 테스트.

소스 = hitl_manager 런타임(is_turn_active + get_progress). DB 불요.
설계: docs/reports/세션연속성_복원_설계계획_2026-06-11.md §4
"""
from api_v2.routes.conversations import build_turn_state
from app.dream_agent.workflow_managers.hitl_manager.manager import (
    ExecutionProgress,
    HITLManager,
)


def _plan(n: int) -> dict:
    return {"todos": [{"id": f"t{i}"} for i in range(1, n + 1)]}


def test_running_with_progress_snapshot():
    """실행 중 + progress 존재 → plan·완료todo·진행 정확 반영."""
    hitl = HITLManager()
    tid = "turn_abc"
    hitl.register_turn(tid)
    hitl._progress[tid] = ExecutionProgress(
        session_id=tid,
        plan=_plan(3),
        phases=[["t1"], ["t2"], ["t3"]],
        current_phase=1,
        completed_todos={"t1": {"todo_id": "t1", "status": "completed"}},
        status="running",
    )

    snap = build_turn_state(hitl, "conv_x", tid)

    assert snap["is_running"] is True
    assert snap["status"] == "running"
    assert snap["completed_todos"] == ["t1"]
    assert snap["total_todos"] == 3
    assert snap["current_phase"] == 1
    assert snap["plan"]["todos"][0]["id"] == "t1"
    assert snap["conversation_id"] == "conv_x"
    assert snap["turn_id"] == tid


def test_active_but_no_progress_yet():
    """실행 진입했으나 execution 전(cognitive/planning) → is_running True, plan 없음."""
    hitl = HITLManager()
    tid = "turn_pre"
    hitl.register_turn(tid)

    snap = build_turn_state(hitl, "conv_x", tid)

    assert snap["is_running"] is True
    assert snap["status"] == "running"  # active 인데 progress 없으면 running 으로 표기
    assert snap["plan"] is None
    assert snap["completed_todos"] == []
    assert snap["total_todos"] == 0
    assert snap["current_phase"] == 0


def test_not_running_returns_unknown():
    """활성 레지스트리에 없으면(완료/없는 턴) is_running False — 정적 복원으로 충분."""
    hitl = HITLManager()

    snap = build_turn_state(hitl, "conv_x", "turn_done")

    assert snap["is_running"] is False
    assert snap["status"] == "unknown"
    assert snap["plan"] is None
    assert snap["completed_todos"] == []


def test_cleanup_turn_makes_it_not_running():
    """run_turn 종료(cleanup_turn) 후엔 is_running False + progress 제거."""
    hitl = HITLManager()
    tid = "turn_z"
    hitl.register_turn(tid)
    hitl._progress[tid] = ExecutionProgress(
        session_id=tid, plan=_plan(2), phases=[], completed_todos={}, status="running"
    )

    assert build_turn_state(hitl, "c", tid)["is_running"] is True

    hitl.cleanup_turn(tid)  # finally 경로

    snap = build_turn_state(hitl, "c", tid)
    assert snap["is_running"] is False
    assert snap["plan"] is None
