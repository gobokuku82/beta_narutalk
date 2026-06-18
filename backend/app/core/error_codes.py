"""Error Code 카탈로그 (진실 소스).

Sprint 13 I11-a에서 모든 error 이벤트에 `severity`/`layer` 필드 통일.
이 모듈은 error code/layer/severity/message 의 **단일 진실 소스**.

명세서: docs/agent_specs/22_error_codes_v1.0.md
WS 포맷: docs/agent_specs/21_WEBSOCKET_PROTOCOL_v1.0.md §6

사용:
    from app.core.error_codes import ErrorCodes  # (2026-06-10 api_v2→core 이전: 전송·에이전트 공용 중립 계약)

    await conn_manager.broadcast_to_user(user_id, "agent", {
        "type": "error",
        **ErrorCodes.CONCURRENT_LIMIT_EXCEEDED,
        "conversation_id": conv_id,
        "turn_id": turn_id,
        "message": "동시 실행 쿼리 개수 제한 초과",  # 기본 message 오버라이드 가능
    })
"""

from __future__ import annotations

from typing import Literal, TypedDict


Severity = Literal["fatal", "warning"]
Layer = Literal["transport", "cognitive", "planning", "execution", "response", "runtime"]


class ErrorSpec(TypedDict):
    """Error 이벤트 기본 필드 (code/layer/severity/message).

    호출자는 이 dict에 conversation_id/turn_id/detail 등을 보강해서 broadcast.
    """
    code: str
    layer: Layer
    severity: Severity
    message: str


class ErrorCodes:
    """모든 error code 중앙 카탈로그.

    각 에러는 기본 `code`, `layer`, `severity`, `message` 제공.
    `message`는 호출 시점에 상세 컨텍스트로 오버라이드 가능.
    """

    # ── Transport (전송/프로토콜) ──

    INVALID_MESSAGE: ErrorSpec = {
        "code": "INVALID_MESSAGE",
        "layer": "transport",
        "severity": "fatal",
        "message": "메시지 형식이 올바르지 않습니다.",
    }

    CONCURRENT_LIMIT_EXCEEDED: ErrorSpec = {
        "code": "CONCURRENT_LIMIT_EXCEEDED",
        "layer": "transport",
        "severity": "fatal",
        "message": "동시 실행 쿼리 개수 제한 초과",
    }

    # ── Runtime (실행 래퍼) ──

    EXECUTION_ERROR: ErrorSpec = {
        "code": "EXECUTION_ERROR",
        "layer": "runtime",
        "severity": "fatal",
        "message": "실행 중 오류가 발생했습니다.",
    }

    # (2026-06-11) stage 가 Command(update={"error": ...}, goto=END) 로 끝난 경우.
    # 과거엔 이 경로가 complete(status=success) + 빈 화면으로 나가던 "무언의 성공"
    # (정직 불변식 위반) — ws_agent 종료부가 본 코드로 aborted 처리.
    LAYER_ERROR: ErrorSpec = {
        "code": "LAYER_ERROR",
        "layer": "runtime",
        "severity": "fatal",
        "message": "처리 단계에서 오류가 발생해 중단되었습니다.",
    }

    # ── Layer Guard (품질 검증, Sprint 13 I11-a) ──

    COGNITIVE_EMPTY_QUERY: ErrorSpec = {
        "code": "COGNITIVE_EMPTY_QUERY",
        "layer": "cognitive",
        "severity": "fatal",
        "message": "인식 단계에서 구조화 쿼리를 생성하지 못했습니다.",
    }

    PLANNING_EMPTY_PLAN: ErrorSpec = {
        "code": "PLANNING_EMPTY_PLAN",
        "layer": "planning",
        "severity": "fatal",
        "message": "계획 단계에서 실행할 Todo가 생성되지 않았습니다.",
    }

    EXECUTION_ALL_FAILED: ErrorSpec = {
        "code": "EXECUTION_ALL_FAILED",
        "layer": "execution",
        "severity": "fatal",
        "message": "모든 Todo 실행이 실패했습니다.",
    }

    EXECUTION_PARTIAL_FAILED: ErrorSpec = {
        "code": "EXECUTION_PARTIAL_FAILED",
        "layer": "execution",
        "severity": "warning",
        "message": "일부 Todo 실행이 실패했습니다.",
    }

    RESPONSE_EMPTY: ErrorSpec = {
        "code": "RESPONSE_EMPTY",
        "layer": "response",
        "severity": "fatal",
        "message": "응답 단계에서 빈 응답이 생성되었습니다.",
    }

    # ── Todo 편집 HITL (Sprint 14 A3, D7=A- 축소 3개) ──
    # 나머지 4개 (TODO_NOT_FOUND, CASCADE_FAILED, NL_LLM_UNAVAILABLE,
    # REORDER_INVALID_DAG) 는 free-form reason 으로 처리 — Sprint 15+ 에 실
    # UX 문제 발생 시 승격 가능.

    TODO_EDIT_NOT_PAUSED: ErrorSpec = {
        "code": "TODO_EDIT_NOT_PAUSED",
        "layer": "runtime",
        "severity": "warning",
        "message": "편집하려면 일시정지 상태가 필요합니다.",
    }

    INVALID_DAG: ErrorSpec = {
        "code": "INVALID_DAG",
        "layer": "planning",
        "severity": "warning",
        "message": "Todo 의존 관계에 문제가 있습니다.",
    }

    NL_INTENT_UNCLEAR: ErrorSpec = {
        "code": "NL_INTENT_UNCLEAR",
        "layer": "planning",
        "severity": "warning",
        "message": "어떤 작업을 원하시는지 이해하지 못했습니다 — 구조화 UI 로 시도해보세요.",
    }

    # ── 전체 목록 (INDEX) ──

    @classmethod
    def all_codes(cls) -> list[str]:
        """모든 error code 문자열 목록 반환. 테스트/문서 검증용."""
        return [
            cls.INVALID_MESSAGE["code"],
            cls.CONCURRENT_LIMIT_EXCEEDED["code"],
            cls.EXECUTION_ERROR["code"],
            cls.COGNITIVE_EMPTY_QUERY["code"],
            cls.PLANNING_EMPTY_PLAN["code"],
            cls.EXECUTION_ALL_FAILED["code"],
            cls.EXECUTION_PARTIAL_FAILED["code"],
            cls.RESPONSE_EMPTY["code"],
            cls.TODO_EDIT_NOT_PAUSED["code"],
            cls.INVALID_DAG["code"],
            cls.NL_INTENT_UNCLEAR["code"],
        ]

    @classmethod
    def all_specs(cls) -> list[ErrorSpec]:
        """모든 ErrorSpec 목록. 문서 검증/타입 체크용."""
        return [
            cls.INVALID_MESSAGE,
            cls.CONCURRENT_LIMIT_EXCEEDED,
            cls.EXECUTION_ERROR,
            cls.COGNITIVE_EMPTY_QUERY,
            cls.PLANNING_EMPTY_PLAN,
            cls.EXECUTION_ALL_FAILED,
            cls.EXECUTION_PARTIAL_FAILED,
            cls.RESPONSE_EMPTY,
            cls.TODO_EDIT_NOT_PAUSED,
            cls.INVALID_DAG,
            cls.NL_INTENT_UNCLEAR,
        ]
