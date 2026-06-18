"""Execution Models — ExecutionContext

2026-05-15 정리 (models/ cleanup A6):
  - 제거: `ExecutionResult` (단일 Tool 결과 wrapper) — 활성 사용 0
    활성 ExecutionResult = `app.dream_agent.schemas.execution_result.ExecutionResult`
    (Plan 전체의 집계 결과 — 4-Layer 가 사용)
  - 유지: `ExecutionContext` — 모든 Tool 의 입력 컨텍스트

Reference: docs/_claude/models_cleanup_plan_2026-05-15.md
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class ExecutionContext(BaseModel):
    """Tool 에 전달되는 실행 컨텍스트.

    각 Tool 의 `execute(params, context)` 두 번째 인자.
    `previous_results` 를 통해 이전 Phase 의 출력이 다음 Todo 로 흐른다.
    """

    # === Identity ===
    session_id: str
    plan_id: str
    client_id: Optional[str] = None
    user_id: Optional[str] = None

    # === Locale ===
    language: str = "ko"

    # === Context ===
    previous_results: dict[str, Any] = Field(default_factory=dict)
    session_memory: dict[str, Any] = Field(default_factory=dict)

    # === 공유 데이터 ===
    collected_data: Optional[dict[str, Any]] = None
    preprocessed_data: Optional[dict[str, Any]] = None

    # === Metadata ===
    metadata: dict[str, Any] = Field(default_factory=dict)
