"""Pipeline 정의 + 실행 결과 Pydantic 모델.

ADR-023 (5 외부 주체 + Trigger) + ADR-027 (5 내부 주체 권한) 의 *Pipeline* 영역.
Pipeline = Tool 조합 + step 순서 + depends_on + cache_key + trigger (계산·fetch 금지).

YAML 계약 = 68 spec §6.1.1 (K01). 본 모델이 그 YAML 을 파싱한다.

Status: complete — Phase 1 M1 (2026-05-28) Runner walking skeleton.
"""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.workspace import Layer

# 63 spec §2.3.3.3 PipelineRunStatus 와 정합 (pending→running→validating→completed/failed/cancelled)
RunStatus = Literal["pending", "running", "validating", "completed", "failed", "cancelled"]
StepStatus = Literal["pending", "running", "completed", "failed", "skipped"]


# ─────────────────────────────────────────────────────────────────
# 1. Pipeline 정의 (YAML → 모델)
# ─────────────────────────────────────────────────────────────────


class StepDef(BaseModel):
    """pipeline step 1개 = Tool 1회 호출."""

    id: str
    tool: str  # registry 도구 이름 (snake_case, catalog `name:` 과 일치)
    inputs: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)


class TriggerDef(BaseModel):
    """ADR-023 Trigger 추상화 (manual/upload/cron/webhook/agent).

    Status: planned — 모델 선언만 선행 배치. 실측 52/52 flow 가 type: manual 이고
    runner 는 trigger 필드를 읽지 않음 — cron/webhook/agent 트리거는 스케줄러 연결 시 구현.
    """

    model_config = ConfigDict(extra="allow")
    type: str = "manual"


class ValidatorDef(BaseModel):
    """산출 검증 (ADR-024 V4 정답 보존). `schema` 는 예약어 회피 위해 alias."""

    model_config = ConfigDict(populate_by_name=True)
    output_schema: Optional[str] = Field(default=None, alias="schema")
    expected: dict[str, Any] = Field(default_factory=dict)
    reference: Optional[dict[str, Any]] = None
    fail_policy: Literal["alert", "block", "ignore"] = "alert"


class CacheDef(BaseModel):
    """cache = Workspace 변환 산출물 (68 §3.6 — 임시 사본 아님, 영속 자산)."""

    layer: Layer = "computed"
    key_template: Optional[str] = None
    ttl_seconds: Optional[int] = None


class PipelineDef(BaseModel):
    """pipeline 1개 정의. extra='allow' → client/period 등 ${var} 선언 흡수."""

    model_config = ConfigDict(extra="allow")

    name: str
    visualization_id: Optional[str] = None
    category: Optional[str] = None
    description: str = ""
    methodology_id: Optional[str] = None
    priority: Optional[str] = None
    trigger: TriggerDef = Field(default_factory=TriggerDef)
    steps: list[StepDef]
    validator: Optional[ValidatorDef] = None
    cache: Optional[CacheDef] = None
    owner: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────
# 2. 실행 결과 (Runner → API)
# ─────────────────────────────────────────────────────────────────


class StepResult(BaseModel):
    """step 1개 실행 결과 (직렬화 안전 — raw 산출물 보관 X)."""

    id: str
    tool: str
    status: StepStatus = "pending"
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    duration_ms: Optional[float] = None
    error: Optional[str] = None


class RunResult(BaseModel):
    """pipeline 1회 실행 결과. 63 §2.3.3.3 PipelineRunStatus 와 정합."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    run_id: str
    pipeline: str
    status: RunStatus = "pending"
    variables: dict[str, Any] = Field(default_factory=dict)
    trigger: str = "manual"
    total_steps: Optional[int] = None
    cache_hit: bool = False
    cache_key: Optional[str] = None
    cache_layer: Optional[str] = None
    output: Optional[dict[str, Any]] = None
    steps: list[StepResult] = Field(default_factory=list)
    validation: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    error_layer: Optional[str] = None  # runner | tool | validator | data_source
    failed_step: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    duration_ms: Optional[float] = None


__all__ = [
    "RunStatus",
    "StepStatus",
    "StepDef",
    "TriggerDef",
    "ValidatorDef",
    "CacheDef",
    "PipelineDef",
    "StepResult",
    "RunResult",
]
