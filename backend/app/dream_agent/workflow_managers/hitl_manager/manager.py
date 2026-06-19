"""HITL Manager

Human-in-the-Loop 요청/응답 관리

Reference: docs/agent_specs/12_manager_layer_v1.4.md §4 (HITLManager)
"""

import asyncio
from dataclasses import dataclass, field
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ExecutionProgress:
    """Execution 진행 상태 — hitl_manager(PM)가 관리.

    Phase 루프 실행 중 어디까지 완료됐는지, 어떤 결과가 있는지 추적.
    Pause 시 interrupt payload에 snapshot으로 전달되어 Checkpoint에 저장됨.
    """
    session_id: str
    plan: dict                                          # 현재 Plan (수정 가능)
    phases: list[list[str]]                             # todo_manager._build_phases_from_plan 결과
    current_phase: int = 0                              # 진행한 Phase 수
    completed_todos: dict[str, dict] = field(default_factory=dict)  # todo_id → result
    status: str = "running"                             # running | paused | completed | cancelled
    paused_at_phase: Optional[int] = None


class HITLManager:
    """HITL 관리자

    interrupt 요청을 관리하고 사용자 응답을 처리
    """

    def __init__(self):
        # (2026-06-11 폐기) Sprint 12 event 트랙 제거 — 요청 장부(_pending_requests/
        # _response_events/_responses)와 create_request/wait_for_response/submit_response/
        # get_pending_request/cancel_request/cleanup. _run_agent 폐기(533a632, 05-31)가
        # 본체만 지우고 이 장부를 남겨, ws_hitl 의 hitl_ack.accepted 가 빈 장부 조회로
        # 항상 False 였음(거짓 신호 버그). 재개 동기화 = _resume_queues 단일 트랙.
        # 복원 필요 시 git 히스토리(2ce4aff 출생 · 본 커밋 삭제) 참조.

        # ── PM 역할 (Execution 진행 추적 + Pause 제어) ──
        # session_id → ExecutionProgress
        self._progress: dict[str, ExecutionProgress] = {}
        # Pause 요청된 세션 ID
        self._paused: set[str] = set()

        # ── Sprint 13 I7: run_turn task ↔ ws_hitl 동기화 ──
        # turn_id → Queue[dict]  (action payload FIFO)
        # run_turn이 wait_for_resume()로 대기, ws_hitl이 signal_resume()로 깨움.
        # Queue는 대기자 없어도 put 버퍼링 허용 → Event의 wait/clear race 회피.
        self._resume_queues: dict[str, asyncio.Queue] = {}

        # ── Sprint 14 A1: HITL timeout 활성 turn 레지스트리 ──
        # run_turn 진입 시 register_turn, finally 에서 cleanup_turn 으로 제거.
        # ws_hitl 4개 핸들러(pause/resume/cancel/hitl_response) + A3 4개 (todo_modify/delete/add/edit_nl)
        # 가 is_turn_active 로 stale guard.
        self._active_turns: set[str] = set()

        # ── Sprint 14 A3 (D9 L1): per-session Lock for Todo 편집 ──
        # handle_todo_edit/delete/add + (Phase 3 의 NL 경로) 동시 호출 시 직렬화.
        # D5=B 정책 (pause 상태만 편집) 으로 main race window 는 이미 좁지만,
        # 단일 사용자 다중 탭 연타 / NL LLM 호출 중 race 완화.
        self._session_locks: dict[str, asyncio.Lock] = {}

    # ══════════════════════════════════════════
    # PM 역할: Execution 진행 상태 관리
    # ══════════════════════════════════════════

    def create_progress(self, session_id: str, plan: dict) -> ExecutionProgress:
        """Execution 시작 시 — 진행 상태 생성.

        중복 호출 시 덮어쓰기 (경고 로그).
        """
        # 런타임 import (순환 방지)
        from app.dream_agent.workflow_managers.todo_manager import get_todo_manager
        tm = get_todo_manager()

        if session_id in self._progress:
            logger.warning("progress already exists, overwriting", session_id=session_id)

        # Sprint 14 A3 Phase 4 bugfix (2026-04-23):
        # 사용자가 plan_review 승인 직후 execution_stage 진입 전에 pause 버튼을 누르면
        # request_pause 는 _paused.add 만 하고 progress 가 없어 status 업데이트 못 함.
        # 그 후 create_progress 는 기본 "running" 으로 만들어져 Todo 편집이 거부됨.
        # 수정: _paused 에 이미 있으면 초기 status 를 "paused" 로 설정.
        initial_status = "paused" if session_id in self._paused else "running"
        progress = ExecutionProgress(
            session_id=session_id,
            plan=plan,
            phases=tm._build_phases_from_plan(plan),
            status=initial_status,
        )
        self._progress[session_id] = progress
        logger.info(
            "progress created",
            session_id=session_id,
            todos=len(plan.get("todos", [])),
            phases=len(progress.phases),
        )
        return progress

    def restore_progress(self, session_id: str, saved: dict) -> ExecutionProgress:
        """Checkpoint snapshot에서 복원 (서버 재시작 시).

        ws_agent가 interrupt payload에서 읽은 progress를 전달.
        """
        from app.dream_agent.workflow_managers.todo_manager import get_todo_manager
        tm = get_todo_manager()

        plan = saved.get("plan", {})
        progress = ExecutionProgress(
            session_id=session_id,
            plan=plan,
            phases=tm._build_phases_from_plan(plan),
            current_phase=saved.get("current_phase", 0),
            completed_todos=dict(saved.get("completed_results", {})),
            status=saved.get("status", "running"),
        )
        self._progress[session_id] = progress
        logger.info(
            "progress restored",
            session_id=session_id,
            completed=len(progress.completed_todos),
        )
        return progress

    def get_progress(self, session_id: str) -> Optional[ExecutionProgress]:
        """현재 진행 상태 조회. 없으면 None."""
        return self._progress.get(session_id)

    def get_completed(self, session_id: str) -> set[str]:
        """완료된 Todo ID 집합. progress 없으면 빈 set."""
        p = self._progress.get(session_id)
        return set(p.completed_todos.keys()) if p else set()

    def report_phase_complete(
        self,
        session_id: str,
        results: list[dict],
    ) -> None:
        """Phase 완료 보고 — 결과를 completed_todos에 누적.

        results는 executor.execute_phase()의 반환값 — list[TodoResult(dict)].
        """
        p = self._progress.get(session_id)
        if not p:
            logger.warning("progress not found for report", session_id=session_id)
            return
        for r in results:
            tid = r.get("todo_id") if isinstance(r, dict) else getattr(r, "todo_id", None)
            if not tid:
                continue
            # TodoResult가 Pydantic이면 dict로 변환
            if hasattr(r, "model_dump"):
                r = r.model_dump(mode="json")
            p.completed_todos[tid] = r
        p.current_phase += 1

    # (2026-06-11 폐기) get_execution_result — 호출처 0 의 死 메서드.
    # progress 부재 시 {"status": "completed"} 를 조작 반환하던 거짓-성공 제조기.
    # 실제 결과 조합은 execution_stage._build_execution_result 가 담당.

    def get_progress_snapshot(self, session_id: str) -> dict:
        """Checkpoint 저장용 스냅샷 (JSON 직렬화 가능한 dict).

        interrupt payload에 포함되어 Checkpoint에 저장됨.
        """
        p = self._progress.get(session_id)
        if not p:
            return {}
        return {
            "completed_todos": list(p.completed_todos.keys()),
            "completed_results": {k: v for k, v in p.completed_todos.items()},
            "plan": p.plan,
            "status": p.status,
            "current_phase": p.current_phase,
        }

    # ══════════════════════════════════════════
    # PM 역할: 실행 제어 (Pause/Resume/Continue)
    # ══════════════════════════════════════════

    def should_continue(self, session_id: str) -> dict:
        """execution_stage가 매 Phase 전에 질문 — "다음 뭐 해?"

        반환:
            {"action": "continue"} — 다음 Phase 실행
            {"action": "pause"}    — Pause 요청됨, interrupt() 필요
            {"action": "cancel"}   — 취소 요청됨 (추후 확장)
        """
        p = self._progress.get(session_id)
        if p and p.status == "cancelled":
            return {"action": "cancel"}
        if session_id in self._paused:
            return {"action": "pause"}
        return {"action": "continue"}

    def request_pause(self, session_id: str, reason: str = "user_request") -> None:
        """Pause 플래그 세팅 — 다음 Phase 전에 execution_stage가 감지해 interrupt()."""
        self._paused.add(session_id)
        p = self._progress.get(session_id)
        if p:
            p.status = "paused"
            p.paused_at_phase = p.current_phase
        logger.info("pause requested", session_id=session_id, reason=reason)

    def request_resume(self, session_id: str) -> None:
        """Resume — Pause 해제."""
        self._paused.discard(session_id)
        p = self._progress.get(session_id)
        if p:
            p.status = "running"
            p.paused_at_phase = None
        logger.info("resume requested", session_id=session_id)

    def request_cancel(self, session_id: str) -> None:
        """Cancel — 실행 취소. should_continue가 "cancel" 반환."""
        self._paused.discard(session_id)  # pause 해제 (cancel이 우선)
        p = self._progress.get(session_id)
        if p:
            p.status = "cancelled"
        logger.info("cancel requested", session_id=session_id)

    def is_paused(self, session_id: str) -> bool:
        """Pause 상태 조회."""
        return session_id in self._paused

    def get_remaining_phases(self, session_id: str) -> list[list[str]]:
        """미완료 Todo만 남은 Phase 목록.

        execution_stage가 while 루프 재진입 시 사용.
        Plan 수정 후 phases가 재구성되면 자동 반영.
        """
        p = self._progress.get(session_id)
        if not p:
            return []
        completed = self.get_completed(session_id)
        remaining = []
        for phase in p.phases:
            phase_remaining = [tid for tid in phase if tid not in completed]
            if phase_remaining:
                remaining.append(phase_remaining)
        return remaining

    # ══════════════════════════════════════════
    # PM 역할: Todo 수정 조율 (todo_manager 위임)
    # ══════════════════════════════════════════

    def handle_todo_edit(
        self,
        session_id: str,
        todo_id: str,
        changes: dict,
    ) -> dict:
        """Todo 수정 조율 — pause 상태에서만 허용.

        Status: complete — Sprint 12 구현 + A3 Phase 2 (ws_hitl is_turn_active 가드 / hitl_ack accepted 필드 / per-session Lock D9 L1 / 테스트 그룹 B) + A3 Phase 5 (편집 경로 통합 — plan_review 도 임시 progress 로 동일 경로)

        흐름:
          1. Pause 상태 확인
          2. todo_manager.modify_todo → Plan 수정 (progress.plan 직접 mutate)
          3. todo_manager.calculate_cascade → 연쇄 무효화 계산
          4. progress.completed_todos에서 무효화된 결과 제거
          5. phases 재구성
          6. validate → issues 반환

        Returns:
            {"invalidated": [...], "restart_from": "...", "preserved": [...], "issues": [...]}
            또는 {"error": "..."}
        """
        p = self._progress.get(session_id)
        if not p:
            return {"error": f"progress not found: {session_id}"}
        if p.status != "paused":
            return {"error": f"not paused (status={p.status})"}

        from app.dream_agent.workflow_managers.todo_manager import get_todo_manager
        tm = get_todo_manager()

        # 1) 수정 적용 (progress.plan mutate)
        p.plan = tm.modify_todo(p.plan, todo_id, changes)

        # 2) 연쇄 무효화 계산 (read-only)
        cascade = tm.calculate_cascade(todo_id, p.completed_todos, p.plan)

        # 3) 무효화된 결과 제거
        for tid in cascade.invalidated_todos:
            p.completed_todos.pop(tid, None)

        # 4) phases 재구성
        p.phases = tm._build_phases_from_plan(p.plan)

        # 5) 검증
        issues = tm.validate(p.plan)

        logger.info(
            "todo edited via HITL",
            session_id=session_id, todo_id=todo_id,
            invalidated=cascade.invalidated_todos,
            issues=len(issues),
        )
        return {
            "invalidated": cascade.invalidated_todos,
            "restart_from": cascade.restart_from,
            "preserved": list(cascade.preserved_results.keys()),
            "issues": issues,
        }

    def handle_todo_delete(self, session_id: str, todo_id: str) -> dict:
        """Todo 삭제 조율 — pause 상태에서만 허용.

        Status: complete — Sprint 12 구현 + A3 Phase 2 (가드/Lock/테스트) + A3 Phase 5 (편집 경로 통합)
        """
        p = self._progress.get(session_id)
        if not p:
            return {"error": f"progress not found: {session_id}"}
        if p.status != "paused":
            return {"error": f"not paused (status={p.status})"}

        from app.dream_agent.workflow_managers.todo_manager import get_todo_manager
        tm = get_todo_manager()

        # cascade 먼저 계산 (삭제 전 의존성 기준)
        cascade = tm.calculate_cascade(todo_id, p.completed_todos, p.plan)
        p.plan = tm.delete_todo(p.plan, todo_id)

        for tid in cascade.invalidated_todos:
            p.completed_todos.pop(tid, None)

        p.phases = tm._build_phases_from_plan(p.plan)
        issues = tm.validate(p.plan)

        logger.info(
            "todo deleted via HITL",
            session_id=session_id, todo_id=todo_id,
            invalidated=cascade.invalidated_todos,
            issues=len(issues),
        )
        return {
            "invalidated": cascade.invalidated_todos,
            "restart_from": cascade.restart_from,
            "preserved": list(cascade.preserved_results.keys()),
            "issues": issues,
        }

    def handle_todo_add(
        self,
        session_id: str,
        new_todo: dict,
        after_todo_id: Optional[str] = None,
    ) -> dict:
        """Todo 추가 조율 — pause 상태에서만 허용.

        Status: complete — Sprint 12 구현 + A3 Phase 2 (가드/Lock/테스트) + A3 Phase 5 (편집 경로 통합)

        추가된 Todo는 미완료이므로 무효화 없음.
        phases만 재구성.
        """
        p = self._progress.get(session_id)
        if not p:
            return {"error": f"progress not found: {session_id}"}
        if p.status != "paused":
            return {"error": f"not paused (status={p.status})"}

        from app.dream_agent.workflow_managers.todo_manager import get_todo_manager
        tm = get_todo_manager()

        p.plan = tm.add_todo(p.plan, new_todo, after_todo_id=after_todo_id)
        added_id = new_todo.get("id", "")

        p.phases = tm._build_phases_from_plan(p.plan)
        issues = tm.validate(p.plan)

        logger.info(
            "todo added via HITL",
            session_id=session_id, todo_id=added_id,
            issues=len(issues),
        )
        return {"added_id": added_id, "issues": issues}


    # ─────────────────────────────────────────────────────────────
    # Sprint 13 I7 — run_turn task ↔ ws_hitl Resume Queue
    # ─────────────────────────────────────────────────────────────

    async def wait_for_resume(
        self,
        turn_id: str,
        timeout: Optional[float] = None,
    ) -> dict:
        """`run_turn`이 interrupt 후 호출 — 사용자 응답(action) 대기.

        Queue가 비어있으면 put 될 때까지 await.
        Queue에 이미 값 있으면 FIFO로 즉시 반환.

        Sprint 14 A1: timeout 인자 추가. 초과 시 {"action":"timeout"} 반환.
        기본값 None 유지로 Sprint 13 경로 (HQ-01~06) 하위 호환.
        """
        q = self._resume_queues.setdefault(turn_id, asyncio.Queue())
        if timeout is None:
            return await q.get()
        try:
            return await asyncio.wait_for(q.get(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("resume timeout", turn_id=turn_id, timeout=timeout)
            return {"action": "timeout"}

    # ─────────────────────────────────────────────────────────────
    # Sprint 14 A1 — 활성 turn 레지스트리 (HITL timeout 가드)
    # ─────────────────────────────────────────────────────────────

    def register_turn(self, turn_id: str) -> None:
        """run_turn 진입 시 호출 — 활성 turn 표시.

        idempotent (set.add). 이미 있으면 no-op.
        """
        self._active_turns.add(turn_id)

    def is_turn_active(self, turn_id: str) -> bool:
        """ws_hitl 가드에서 사용 — stale turn 차단."""
        return turn_id in self._active_turns

    def signal_resume(self, turn_id: str, action: dict) -> None:
        """ws_hitl이 사용자 명령 수신 시 호출 — wait 깨움.

        put_nowait로 즉시 리턴 (sync context 안전).
        대기자 없으면 Queue에 버퍼링 (손실 없음).
        """
        q = self._resume_queues.setdefault(turn_id, asyncio.Queue())
        q.put_nowait(action)

    def cleanup_turn(self, turn_id: str) -> None:
        """run_turn task 종료 시 호출 — Queue + 활성 레지스트리 + pause 플래그 + session Lock + progress 제거.

        없으면 no-op (idempotent).
        호출 전 wait 중인 task 없어야 함 (계약 — run_turn이 보장).

        Sprint 14 A1 확장 (CS-2):
          - _active_turns.discard — 활성 표시 해제
          - _paused.discard — timeout 으로 종료된 turn 의 pause 플래그 잔류 방지

        Sprint 14 A3 Phase 2 확장 (D9 L1):
          - _session_locks.pop — 편집 Lock 누수 방지 (turn_id == session_id 가정)

        Sprint 14 A3 Phase 5 확장 (2026-04-24, 통합 편집 경로):
          - _progress.pop — plan_review 임시 progress + 완료된 execution progress 누수 방지
        """
        self._resume_queues.pop(turn_id, None)
        self._active_turns.discard(turn_id)
        self._paused.discard(turn_id)
        self._session_locks.pop(turn_id, None)
        self._progress.pop(turn_id, None)

    def _get_lock(self, session_id: str) -> asyncio.Lock:
        """per-session asyncio.Lock 반환.

        Status: complete — Sprint 14 A3 Phase 2 (D9 L1) 도입.

        동일 session_id 는 동일 Lock 반환 (setdefault).
        handle_todo_edit/delete/add + NL 핸들러가 `async with lock:` 로 wrap.
        LLM 호출 같은 긴 작업 중 다른 편집은 대기 (UX-10 로딩 indicator 로 피드백).
        L3 도입 시 (Phase 9 회고) LLM 호출 전 release → 결과 후 재획득.
        """
        return self._session_locks.setdefault(session_id, asyncio.Lock())

    def _reset_resume_queues_for_test(self) -> None:
        """테스트 전용 — 프로덕션 호출 금지.

        _resume_queues 전체 초기화. 언더스코어 prefix로 실수 호출 방지.
        """
        self._resume_queues = {}


# 싱글톤
_hitl_manager: Optional[HITLManager] = None


def get_hitl_manager() -> HITLManager:
    """HITL Manager 싱글톤 반환"""
    global _hitl_manager
    if _hitl_manager is None:
        _hitl_manager = HITLManager()
    return _hitl_manager
