"""대화이력(Conversation History) 조회 — checkpoint 기반 (Phase 1).

GET /api/conversations                            → 대화 목록 (client 필터, 최신순)
GET /api/conversations/{id}/turns                 → 대화의 turn(메시지) 목록 (채팅 복원용)
GET /api/conversations/{id}/turns/{tid}/state     → 턴 실행 라이브 상태 (세션 연속성 재접속 복원)

ConversationManager(대화 전용, MemoryManager와 분리)가 octormate_system checkpoint를 읽음.
app.state.checkpointer(AsyncPostgresSaver) + app.state.db_pool(asyncpg) 재활용.
턴 상태는 checkpoint(static)가 아니라 hitl_manager 런타임 싱글톤(live)에서 읽음.
설계: docs/reports/대화이력_설계_단계적_2026-06-09.md · docs/reports/세션연속성_복원_설계계획_2026-06-11.md
Status: partial — Phase 1 read-only (목록·복원-보기). 이어서작업(P1.5)·회상(P3)은 후속.
"""
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from app.dream_agent.workflow_managers.conversation_manager import ConversationManager

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


def build_turn_state(hitl: Any, conversation_id: str, turn_id: str) -> dict:
    """진행 중 턴의 라이브 상태 스냅샷 (세션 연속성 P3).

    소스 = hitl_manager 런타임 싱글톤:
      - is_turn_active(turn_id): run_turn 진입~종료 사이면 True (실행 중)
      - get_progress(turn_id): ExecutionProgress(plan·completed_todos·current_phase·status)
        execution_stage 가 create_progress(시작)/report_phase_complete(매 phase) 로 유지 — pause 무관.
    실행 전(cognitive/planning) 이면 progress 아직 없음 → plan=None, completed=[].
    실행 중 아니면 is_running=False (정적 복원으로 충분).

    반환은 프론트 execution store rehydrate 입력과 정합:
      plan(node_event planning 과 동일 shape) / completed_todos(→todoRuntime completed) / total(progress total).
    """
    is_running = bool(hitl.is_turn_active(turn_id))
    progress = hitl.get_progress(turn_id)
    plan = progress.plan if progress else None
    completed = list(progress.completed_todos.keys()) if progress else []
    total = len(plan.get("todos", [])) if isinstance(plan, dict) else 0
    return {
        "turn_id": turn_id,
        "conversation_id": conversation_id,
        "is_running": is_running,
        "status": progress.status if progress else ("running" if is_running else "unknown"),
        "plan": plan,
        "completed_todos": completed,
        "current_phase": progress.current_phase if progress else 0,
        "total_todos": total,
    }


def _manager(request: Request) -> ConversationManager:
    cp = getattr(request.app.state, "checkpointer", None)
    pool = getattr(request.app.state, "db_pool", None)
    if cp is None or pool is None:
        raise HTTPException(status_code=503, detail="checkpointer/db_pool 미초기화")
    return ConversationManager(cp, pool)


@router.get("", summary="대화 목록 (checkpoint, 최신순)")
async def list_conversations(
    request: Request,
    client: str | None = Query(None, description="client 필터"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict:
    return await _manager(request).list_conversations(client, limit, offset)


@router.get("/{conversation_id}/turns", summary="대화의 turn(메시지) 목록")
async def get_conversation_turns(request: Request, conversation_id: str) -> dict:
    return await _manager(request).get_turns(conversation_id)


@router.get(
    "/{conversation_id}/turns/{turn_id}/state",
    summary="턴 실행 라이브 상태 (재접속 복원용 — hitl_manager 런타임)",
)
async def get_turn_state(request: Request, conversation_id: str, turn_id: str) -> dict:
    """세션 연속성 — 재접속 시 진행 중 턴의 라이브 상태(plan·완료 todo·진행).

    소스 = hitl_manager 싱글톤(같은 프로세스의 run_turn task 와 공유). DB 불요.
    설계: docs/reports/세션연속성_복원_설계계획_2026-06-11.md §4
    """
    from app.dream_agent.workflow_managers.hitl_manager import get_hitl_manager

    return build_turn_state(get_hitl_manager(), conversation_id, turn_id)


@router.delete("/{conversation_id}", summary="대화 삭제 (checkpoint 제거, 되돌릴 수 없음)")
async def delete_conversation(request: Request, conversation_id: str) -> dict:
    return await _manager(request).delete_conversation(conversation_id)
