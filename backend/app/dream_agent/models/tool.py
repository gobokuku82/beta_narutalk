"""Tool Models"""

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.dream_agent.models.enums import ToolParameterType  # ToolCategory: open-vocab → category=str


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


class DisplaySpec(BaseModel):
    """표시 메타 (2026-07-02) — Response 레이어가 tool 산출을 '어떻게 보여줄지' 선언.

    미선언(None) 또는 전 필드 기본 = 표시 비활성/일반 렌더 (inert). 도메인이 tool 카탈로그
    (tools/catalog/*.yaml)에 선언하면 responder·executor._generate_summary 가 이 메타로 디스패치한다
    (하드코딩 산출키·'collector' 이름 규약 폐지). 리졸버: `tools/shared/display.py`.
    """
    narrative_keys: list[str] = Field(default_factory=list)   # 서술형 산출 키(report/answer 류). 순서=우선순위
    insight_keys: list[str] = Field(default_factory=list)     # list[{title,description}] 인사이트 키
    table_key: Optional[str] = None                           # list[dict] 표(행) 산출 키
    attachment: list[dict] = Field(default_factory=list)      # [{key, kind, multi}] 파일 산출 → 첨부
    summary_template: Optional[str] = None                    # UI 1줄 요약 (data 키를 {name} 치환)
    infra: bool = False                                       # true=인프라 tool(구 'collector' 규약) — 산출 판정/skip 고지서 제외


class ToolSpec(BaseModel):
    """도구 명세 (YAML에서 로드)"""

    name: str
    description: str
    category: str  # open-vocab: 검증된 자유 문자열(non-empty). 관례값 = enums.KNOWN_TOOL_CATEGORIES
    executor: str  # executor class path

    @field_validator("category")
    @classmethod
    def _category_non_empty(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("ToolSpec.category must be a non-empty string")
        return v

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

    # Display (Response 레이어 표시 메타). None = 표시 비활성/일반 렌더 (inert)
    display: Optional[DisplaySpec] = None
