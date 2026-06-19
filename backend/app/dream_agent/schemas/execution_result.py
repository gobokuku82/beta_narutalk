"""ExecutionResult — Execution 레이어 산출물"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TodoStatus(str, Enum):
    PENDING     = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED   = "completed"
    FAILED      = "failed"
    SKIPPED     = "skipped"


class TodoResult(BaseModel):
    """단일 Todo 실행 결과"""
    todo_id: str
    task_type: str
    tool: str | None = None
    agent: str | None = None
    status: TodoStatus
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    is_mock: bool = False               # stub Tool이 mock 반환했는지
    started_at: float                    # unix ts
    ended_at: float
    duration_ms: float


class ExecutionResult(BaseModel):
    """Execution 레이어 전체 결과"""
    plan_id: str = ""
    todos: dict[str, TodoResult] = Field(default_factory=dict)   # todo_id → result
    phase_timings: list[dict[str, Any]] = Field(default_factory=list)  # [{phase: 1, duration_ms: ...}]
    total_duration_ms: float = 0.0
    overall_status: TodoStatus = TodoStatus.COMPLETED
    halted_at: str | None = None         # 실패한 todo_id
    halt_reason: str | None = None
