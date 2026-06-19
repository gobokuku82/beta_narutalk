"""Execution Stage — Plan → ExecutionResult 실행 (hitl_manager PM 구조)

4-Layer 파이프라인의 세 번째 단계. Phase 루프를 실제로 돌리는 노드.

구조:
  execution_stage (LangGraph 노드)
    → hitl_manager (PM): 진행 상태 관리, "다음 뭐 해?" 지시
    → executor.execute_phase: 실제 Todo 실행 (결과 반환만)
    → callback_manager: 이벤트 전달 (todo_start/complete/progress)

흐름:
  1. 빈 plan → 스킵
  2. hitl_manager.create_progress 또는 restore_progress
  3. Phase 루프 (while True → get_remaining_phases):
     - should_continue() → pause 감지 시 interrupt()
     - 완료된 Todo skip
     - execute_phase 호출
     - report_phase_complete
     - callback emit
  4. 최종 ExecutionResult 조합 → response로 hand-off

LangGraph 특성:
  - resume 시 이 함수 전체가 재실행됨
  - hitl_manager(싱글톤)에서 completed_todos 조회 → 완료된 건 skip
  - 서버 재시작 시 ws_agent가 interrupt payload에서 restore_progress 호출
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from langgraph.graph import END
from langgraph.types import Command, interrupt

from app.core.logging import get_logger
from app.dream_agent.execution.executor import execute_phase
from app.dream_agent.models import ExecutionContext
from app.dream_agent.planning.planner import Plan
from app.dream_agent.schemas.execution_result import (
    ExecutionResult,
    TodoResult,
    TodoStatus,
)
from app.dream_agent.states.agent_state import AgentState

logger = get_logger(__name__)


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


async def _emit_layer_start(session_id: str) -> None:
    """실행 시작 즉시 layer_start emit (UI 타이밍 개선용)."""
    try:
        from app.dream_agent.workflow_managers.callback_manager import get_callback_manager
        await get_callback_manager().emit(session_id, {
            "type": "layer_start",
            "session_id": session_id,
            "timestamp": _iso_now(),
            "data": {"layer": "execution"},
        })
    except Exception:
        pass


async def _emit_todo_events(
    session_id: str,
    phase_todos: list,
    results: list[TodoResult],
    completed_count: int,
    total_todos: int,
    phase_idx: int,
    phases_total: int,
) -> None:
    """todo_start, todo_complete, progress 이벤트 emit."""
    try:
        from app.dream_agent.workflow_managers.callback_manager import get_callback_manager
        from app.dream_agent.execution.executor import _generate_summary

        cb = get_callback_manager()

        # todo_start
        for t in phase_todos:
            await cb.emit(session_id, {
                "type": "todo_start",
                "session_id": session_id,
                "timestamp": _iso_now(),
                "data": {
                    "todo_id": t.id,
                    "tool": t.tool or "",
                    "agent": t.agent or "",
                    "team": t.team or "",
                    "priority": getattr(t, "priority", 5),
                },
            })

        # todo_complete
        for r in results:
            summary = _generate_summary(
                r.tool or "", r.data if isinstance(r.data, dict) else {},
                r.is_mock, r.status.value,
            )
            await cb.emit(session_id, {
                "type": "todo_complete",
                "session_id": session_id,
                "timestamp": _iso_now(),
                "data": {
                    "todo_id": r.todo_id,
                    "tool": r.tool or "",
                    "status": r.status.value,
                    "duration_ms": round(r.duration_ms, 1),
                    "is_mock": r.is_mock,
                    "summary": summary,
                },
            })

        # progress
        pct = round(completed_count / total_todos * 100, 1) if total_todos else 0
        await cb.emit(session_id, {
            "type": "progress",
            "session_id": session_id,
            "timestamp": _iso_now(),
            "data": {
                "completed": completed_count,
                "total": total_todos,
                "percent": pct,
                "phase": phase_idx,
                "phases_total": phases_total,
            },
        })
    except Exception as e:
        logger.warning("event emit failed", error=str(e))


async def execution_stage(state: AgentState) -> Command[Any]:
    """Plan → ExecutionResult 실행 (PM 패턴).

    hitl_manager(PM)가 진행을 지시, execute_phase가 실제 실행.
    """
    plan_dict = state.get("plan") or {}
    session_id = state.get("session_id", "e2e")

    # ── 1. 실행 시작 즉시 layer_start emit ──
    await _emit_layer_start(session_id)

    # ── 2. 빈 plan 스킵 ──
    if not plan_dict.get("todos"):
        logger.info("execution skipped (empty plan)")
        return Command(
            update={
                "execution_result": ExecutionResult(
                    plan_id=session_id,
                    overall_status=TodoStatus.COMPLETED,
                ).model_dump(mode="json"),
            },
            goto="response",
        )

    # ── 3. hitl_manager: progress 생성 또는 재사용 ──
    from app.dream_agent.workflow_managers.hitl_manager import get_hitl_manager
    hitl = get_hitl_manager()

    # resume 시 이미 progress가 있을 수 있음 (싱글톤 재사용)
    if not hitl.get_progress(session_id):
        hitl.create_progress(session_id, plan_dict)

    progress = hitl.get_progress(session_id)
    plan = Plan.model_validate(progress.plan)
    todo_by_id = {t.id: t for t in plan.todos}
    context = ExecutionContext(
        session_id=session_id,
        plan_id=session_id,
        client_id=state.get("client_id"),     # ⑪.C — AgentState → ExecutionContext (ADR-022 helper-B)
    )
    total_todos = len(plan.todos)
    total_start = time.time()
    phase_timings: list[dict] = []

    # ── 4. Phase 루프 ──
    halt = False
    while True:
        remaining_phases = hitl.get_remaining_phases(session_id)
        if not remaining_phases:
            break

        broke_for_pause = False
        for phase_idx, phase in enumerate(remaining_phases, start=1):
            # 4-a. hitl_manager에 질문: "다음 뭐 해?"
            decision = hitl.should_continue(session_id)

            if decision["action"] == "pause":
                # Pause 감지 → Checkpoint 저장용 interrupt
                user_decision = interrupt({
                    "type": "execution_pause",
                    "progress": hitl.get_progress_snapshot(session_id),
                })
                # resume 후 여기로 돌아옴
                action = user_decision.get("action", "resume") if isinstance(user_decision, dict) else "resume"
                if action == "cancel":
                    return Command(
                        update={"execution_result": _build_execution_result(
                            session_id, hitl, phase_timings, total_start, halted=True,
                            halt_reason="cancelled by user",
                        )},
                        goto=END,
                    )
                # Plan이 수정됐을 수 있음 (hitl_manager 싱글톤에 이미 반영)
                plan = Plan.model_validate(progress.plan)
                todo_by_id = {t.id: t for t in plan.todos}
                broke_for_pause = True
                break

            # 4-b. 완료된 Todo skip
            completed = hitl.get_completed(session_id)
            phase_todos_objs = [
                todo_by_id[tid] for tid in phase
                if tid not in completed and tid in todo_by_id
            ]
            if not phase_todos_objs:
                continue

            # 4-c. previous_results 구성 (hitl_manager의 completed_todos로부터)
            previous_results = _build_previous_results(progress.completed_todos)

            # 4-d. executor에 실행 지시
            phase_start = time.time()
            results = await execute_phase(phase_todos_objs, context, previous_results)
            phase_end = time.time()

            # 4-e. hitl_manager에 보고
            hitl.report_phase_complete(session_id, results)

            # 4-f. 이벤트 emit
            completed_count = len(hitl.get_completed(session_id))
            await _emit_todo_events(
                session_id, phase_todos_objs, results,
                completed_count, total_todos, phase_idx, len(remaining_phases),
            )

            phase_timings.append({
                "phase": phase_idx,
                "todos": [t.id for t in phase_todos_objs],
                "duration_ms": round((phase_end - phase_start) * 1000, 1),
            })

            # 4-g. halt on failure
            for r in results:
                if r.status == TodoStatus.FAILED:
                    halt = True
                    break
            if halt:
                break

        if halt:
            break
        if broke_for_pause:
            continue  # remaining_phases 재조회

        # for 정상 완료 → while 탈출
        break

    # ── 5. 최종 ExecutionResult 조합 ──
    execution_result = _build_execution_result(
        session_id, hitl, phase_timings, total_start, halted=halt,
    )

    logger.info(
        "execution done",
        phases=len(phase_timings),
        todos=len(execution_result.get("todos", {})),
        status=execution_result.get("overall_status"),
    )

    # ── 5.5 G6 (감지 단계): 데이터 없음 → 복구 메뉴 준비 ──
    # R1 의 data_insufficient 신호로 "막힘" 감지. detect_recovery 는 never-raise(actions.yaml
    # 오류여도 None → 정상 실행 보호). 막힘 아니면 None → no-op(정상 흐름 무영향).
    # ⚠️ 실제 interactive interrupt(메뉴 띄우고 선택받기)는 graph+ws_agent+ws_hitl+frontend 협응
    #    → 현재는 *감지·로그까지*(안전).
    from app.dream_agent.workflow_managers.recovery import detect_recovery
    recovery_menu = detect_recovery(execution_result)
    if recovery_menu:
        logger.info(
            "data_recovery detected (감지 전용 — interactive interrupt 는 ws/frontend 와 별도)",
            options=[o.get("id") for o in recovery_menu.get("options", [])],
        )
        # 다음(별도, 계획): interrupt 재활성 + ws_agent data_recovery 분기 + ws_hitl 수신 핸들러
        #  → 사용자 선택 → resolve_choice(verb) 라우팅. 현재는 response(R1 정직 메시지)로 진행.

    # L5 (2026-06-11 state 경계 게이트): execution_progress 미러 쓰기 제거.
    # 전수 감사 결과 이 채널을 읽는 곳 0 (pause 복원은 interrupt payload 를 읽음) —
    # execution_result 와 같은 내용을 한 번 더 저장해 checkpoint 를 2배로 만들던 죽은 무게.
    return Command(
        update={"execution_result": execution_result},
        goto="response",
    )


def _build_previous_results(completed_todos: dict[str, dict]) -> dict[str, TodoResult]:
    """hitl_manager의 completed_todos dict → TodoResult Pydantic 변환."""
    out: dict[str, TodoResult] = {}
    for tid, r in completed_todos.items():
        if isinstance(r, dict):
            try:
                out[tid] = TodoResult.model_validate(r)
            except Exception:
                # 스키마가 안 맞으면 skip (방어)
                pass
        elif isinstance(r, TodoResult):
            out[tid] = r
    return out


def _build_execution_result(
    session_id: str,
    hitl,
    phase_timings: list[dict],
    total_start: float,
    halted: bool = False,
    halt_reason: str | None = None,
) -> dict:
    """완료된 결과를 ExecutionResult 형식으로 조합."""
    progress = hitl.get_progress(session_id)
    if not progress:
        return ExecutionResult(plan_id=session_id).model_dump(mode="json")

    todos: dict[str, TodoResult] = {}
    halted_at = None
    for tid, r in progress.completed_todos.items():
        if isinstance(r, dict):
            try:
                todos[tid] = TodoResult.model_validate(r)
                if todos[tid].status == TodoStatus.FAILED and halted_at is None:
                    halted_at = tid
                    halt_reason = halt_reason or todos[tid].error
            except Exception:
                pass
        elif isinstance(r, TodoResult):
            todos[tid] = r

    # M1-S3 (2026-06-12, 계획_멀티쿼리 v2 — 실행 침묵 드롭 가시화): 계획에는 있는데
    # 실행 기록이 없는 todo(DAG 미해결 의존으로 phase 미편성·halt/취소 잔여)를 SKIPPED 로
    # 명시 등기. 실측: 계획 11 vs 실행 8, 누락 3개가 무기록 증발 → 응답 "분석을 완료했습니다"
    # EMPTY 둔갑. responder 의 skipped 고지·귀속 판정(T4)이 이 행을 소비.
    plan_todos = progress.plan.get("todos") or []
    for t in plan_todos:
        tid = t.get("id")
        if not tid or tid in todos:
            continue
        now = time.time()
        todos[tid] = TodoResult(
            todo_id=tid,
            task_type=t.get("task_type") or t.get("task") or "unknown",
            tool=t.get("tool"),
            status=TodoStatus.SKIPPED,
            data={"reason": "not_executed",
                  "detail": "halt/취소 잔여 또는 DAG 미해결 의존으로 phase 미편성"},
            started_at=now, ended_at=now, duration_ms=0.0,
        )

    overall = TodoStatus.FAILED if (halted or halted_at) else TodoStatus.COMPLETED

    result = ExecutionResult(
        plan_id=progress.plan.get("plan_id", session_id),
        todos=todos,
        phase_timings=phase_timings,
        total_duration_ms=round((time.time() - total_start) * 1000, 1),
        overall_status=overall,
        halted_at=halted_at,
        halt_reason=halt_reason,
    )
    # L3 (2026-06-11 state 경계 게이트): state/checkpoint 진입 직전 임계치 슬림.
    # 대용량 값(데이터셋 류)은 참조 스텁으로 치환 — in-memory 체이닝(hitl completed_todos)은
    # 불변이라 previous_results·데이터 게이트·리뷰 체인 무영향.
    from app.dream_agent.execution.state_guard import slim_execution_result
    return slim_execution_result(result.model_dump(mode="json"))
