"""AgentState — LangGraph 전역 상태 (TypedDict)

Dream Agent의 LangGraph 전역 상태. 각 레이어는 자기 필드만 쓰고 다음 레이어로 hand-off.

Sprint 13 Integration (I6) — 식별 체계 + 대화 컨텍스트 필드 추가:
  - user_id / conversation_id / turn_id (신규)
  - session_id (deprecated alias = turn_id)
  - conversation_history / history_limit (Cognitive 주입용)

Reference: docs/agent_specs/main_graph_state_spec_v1.2.md
"""

from __future__ import annotations

from typing import Any, Optional

from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """LangGraph 전역 상태 (TypedDict).

    모든 필드가 optional (total=False) — reducer가 부분 업데이트 가능.
    """
    # ─── Sprint 13 신규 — 식별 체계 ───
    user_id: str                          # 사용자 식별 (Sprint 16+ 실제 로그인)
    conversation_id: str                  # 대화방 단위 (UUID, 클라이언트 생성)
    turn_id: str                          # 쿼리 단위 (UUID, 클라이언트 생성)
    session_id: str                       # deprecated alias of turn_id (값 동기화)

    # ─── Sprint 13 신규 — 대화 컨텍스트 ───
    conversation_history: list[dict[str, Any]]   # Cognitive 주입용 (Sprint 15에서 채움)
    history_limit: int                            # 주입할 최근 N턴 개수

    # ─── 입력 ───
    user_input: str
    language: str
    client_id: str                        # 진입점 명시 시 set, 미명시 시 키 자체 absent (total=False)
                                          # 접근 컨벤션: 항상 state.get("client_id") (직접 인덱싱 금지)

    # ─── Plan 검토 토글 (Phase 1 후속, 2026-05-15) ───
    # True / 누락 → planning_stage 가 interrupt(plan_review) 발동 (현재 동작).
    # False → interrupt 스킵 — AI 가 Plan 만들자마자 바로 execution 진행.
    # 프론트 useSession.requireReview 토글이 query payload 로 전달.
    require_review: bool

    # ─── Cognitive 산출 ───
    structured_query: dict[str, Any]     # StructuredQuery.model_dump()

    # ─── Planning 산출 ───
    plan: dict[str, Any]                  # Plan.model_dump()

    # ─── Execution 산출 ───
    execution_result: dict[str, Any]      # ExecutionResult.model_dump()

    # ─── Execution 진행 상태 (Sprint 12, HITL pause/resume용) ───
    execution_progress: dict[str, Any]

    # ─── Response 산출 ───
    response: dict[str, Any]              # ResponsePayload.model_dump()

    # ─── 횡단 ───
    error: Optional[str]
    trace: list[dict[str, Any]]
    hitl_pending: Optional[dict[str, Any]]


def init_agent_state(
    *,
    user_input: str,
    conversation_id: str,
    turn_id: str,
    user_id: str | None = None,
    client_id: str | None = None,
    language: str = "ko",
    conversation_history: list[dict[str, Any]] | None = None,
    history_limit: int | None = None,
    require_review: bool | None = None,
) -> AgentState:
    """AgentState 생성 헬퍼 (Sprint 13 I6).

    단일 진입점으로:
      - session_id = turn_id 자동 동기화 (alias 보장)
      - Settings fallback 일관성 (user_id, history_limit)
      - trace / conversation_history 기본 [] (append-only 대비)

    Args:
        user_input: 사용자 쿼리 (필수)
        conversation_id: 대화방 UUID (필수)
        turn_id: 쿼리 UUID (필수)
        user_id: None → settings.DEFAULT_USER_ID, 명시 값 우선
        language: 기본 "ko"
        conversation_history: None → []. list 참조 pass-through (defensive copy X)
        history_limit: None → settings.DEFAULT_HISTORY_LIMIT. clip은 history_injector 책임.

    Returns:
        AgentState dict.

    주의:
        빈 문자열 conversation_id/turn_id는 방어 안 함 — 호출자(ws_agent.run_turn)가
        D-3/D-4 INVALID_MESSAGE 정책으로 사전 차단.
    """
    # Settings fallback (import 시점 순환 방지용 함수 내부 import)
    if user_id is None or history_limit is None:
        from app.core.config import settings
        if user_id is None:
            user_id = settings.DEFAULT_USER_ID
        if history_limit is None:
            history_limit = settings.DEFAULT_HISTORY_LIMIT

    if conversation_history is None:
        conversation_history = []

    state: AgentState = {
        "user_id": user_id,
        "conversation_id": conversation_id,
        "turn_id": turn_id,
        "session_id": turn_id,                 # alias 동기화
        "conversation_history": conversation_history,
        "history_limit": history_limit,
        "user_input": user_input,
        "language": language,
        "trace": [],
    }
    # client_id — 진입점 명시 시만 set (ADR-022 helper-B fail-fast 정합, payload 미명시 시 키 absent)
    if client_id is not None:
        state["client_id"] = client_id
    # Plan 검토 토글 — None 이면 필드 자체 미포함 (default True 처럼 동작, planning_stage 가 fallback).
    if require_review is not None:
        state["require_review"] = require_review
    return state
