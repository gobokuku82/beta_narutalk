"""Tool Models"""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from app.dream_agent.models.enums import ToolCategory, ToolParameterType


# pipeline 3-layer (raw/normalized/computed) — storage backend 와 짝 (피봇 P1: cleaned→normalized)
Layer = Literal["raw", "normalized", "computed", "blended"]


class StoragePolicy(BaseModel):
    """Tool 산출물의 저장 정책 — app/data_layer/workspace/ 의 WorkspaceBackend 와 짝.

    POC: FileWorkspace 가 data/{client}/{layer}/{key} 로 저장.
    MVP+: PostgresWorkspace 가 {client}_{layer} → 테이블 매핑.
    """
    layer: Layer
    key_template: str          # 예: "orders_active_{period}.parquet" — tool 내부 format
    partition: list[str] = Field(default_factory=list)  # DB 전환 시 partition 컬럼
    cache_ttl_sec: int = 0     # 0 = 캐시 안 함 (재실행마다 새로 계산)


class ToolParameter(BaseModel):
    """도구 파라미터 정의"""

    name: str
    type: ToolParameterType
    required: bool = False
    default: Optional[Any] = None
    description: str = ""


class ToolSpec(BaseModel):
    """도구 명세 (YAML에서 로드)"""

    name: str
    description: str
    category: ToolCategory
    executor: str  # executor class path

    # Parameters
    parameters: list[ToolParameter] = Field(default_factory=list)

    # Execution
    timeout_sec: int = 300
    max_retries: int = 3

    # Dependencies
    dependencies: list[str] = Field(default_factory=list)  # 선행 도구
    produces: list[str] = Field(default_factory=list)  # 산출물 키

    # Approval
    requires_approval: bool = False

    # Cost
    has_cost: bool = False
    estimated_cost_usd: float = 0.0

    # Storage (tool — cleaned/computed 산출물 저장 정책)
    # None = 저장 안 함 (in-memory 만, 기존 tool 호환)
    storage: Optional[StoragePolicy] = None
