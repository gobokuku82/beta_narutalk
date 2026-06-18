# Data Models Specification — ADALLPIN POC

**Version**: 1.1 | **Date**: 2026-04-10 | **Status**: Active — POC
**기준 문서**: [DATA_MODELS.md](DATA_MODELS.md) (v3.2), [Graph State 명세서](../main_gratph_state_명세서_260401.md), [ERD v2](../ADALLPIN_ERD_v2.md)

> **POC 범위**: collection_agent, preprocessing_agent, analysis_agent, report_agent, pdf_agent, image_creation_agent, video_creation_agent, 공유 Tool
> **제외**: fallback, fail 재시도, 실시간 모니터링 (anomaly_detector), SWARM/CYCLIC 전략

---

## 목차

1. [Overview](#1-overview)
2. [Core Enums — POC](#2-core-enums--poc)
3. [Agent & Tool 정의](#3-agent--tool-정의)
4. [Chat Session & Memory Models](#4-chat-session--memory-models)
5. [Intent Models](#5-intent-models)
6. [Todo Models](#6-todo-models)
7. [Plan Models](#7-plan-models)
8. [Execution Models](#8-execution-models) 
9. [Step Preview Models](#9-step-preview-models)
10. [Response Models](#10-response-models)
11. [HITL Models](#11-hitl-models)
12. [AgentState — POC](#12-agentstate--poc)
13. [Reducers — POC](#13-reducers--poc)
14. [Validation Rules](#14-validation-rules)

---

## 1. Overview

ADALLPIN POC의 AI 에이전트 파이프라인 데이터 모델을 정의합니다.

> **네이밍 규칙 — session_id vs agent_session_id:**
> - `session_id` = `chat_sessions.id` — 채팅방 식별자 (FE/사용자 컨텍스트). 본 문서와 POC API/WS에서 사용.
> - `agent_session_id` = `agent_sessions.id` — LangGraph 실행 세션 (BE/에이전트 컨텍스트). ERD FK에서 사용.
> - 이 둘은 **서로 다른 테이블**이며, 하나의 chat_session에서 여러 agent_session이 생성될 수 있다.

### 1.1 POC vs Full 차이점

| 항목 | Full (v3.2) | POC |
|------|-------------|-----|
| Agent/Tool | AdallpinTool 9종 (추상) | 7 Agent + 34 Tool (구체) |
| Fallback | 있음 | **없음** |
| Fail 재시도 | in_progress 내부 retry | **없음 — 즉시 failed (final)** |
| 실시간 모니터링 | anomaly_detector 24h | **없음** |
| 채팅 | 세션 1개 | **멀티 채팅 세션 (AE당 N개)** |
| 메모리 | trace only | **단기 메모리 + 장기 기억 압축** |
| 중간 미리보기 | 없음 | **각 단계 완료 시 FE에 결과 일부 전송** |
| WebSocket | 세션당 2개 | **AE당 2개 고정 (멀티플렉싱)** |
| ExecutionStrategy | 5종 | **SINGLE, SEQUENTIAL, PARALLEL** |

---

## 2. Core Enums — POC

### 2.1 PocAgent

```python
from enum import Enum

class PocAgent(str, Enum):
    """POC 에이전트 — 7종"""
    COLLECTION      = "collection_agent"        # ← data_analysis 분리
    PREPROCESSING   = "preprocessing_agent"     # ← data_analysis 분리
    ANALYSIS        = "analysis_agent"          # ← data_analysis 분리
    REPORT          = "report_agent"            # ← enum에 명시 추가
    PDF             = "pdf_agent"               # ← v0.5 신설
    IMAGE_CREATION  = "image_creation_agent"
    VIDEO_CREATION  = "video_creation_agent"
    SHARED          = "shared"
```

### 2.2 PocTool

```python
class PocTool(str, Enum):
    """POC Tool — 34종"""
    # === collection_agent (4) ===
    NAVER_COLLECTOR      = "naver_collector"
    YOUTUBE_COLLECTOR    = "youtube_collector"
    NAVER_ADS_COLLECTOR  = "naver_ads_collector"
    META_ADS_COLLECTOR   = "meta_ads_collector"

    # === preprocessing_agent (15) ===
    # 텍스트 클렌징 8단계
    TEXT_PREPROCESSOR        = "text_preprocessor"
    EMOJI_HANDLER            = "emoji_handler"
    REPEAT_CHAR_NORMALIZER   = "repeat_char_normalizer"    # 신규
    HTML_URL_STRIPPER        = "html_url_stripper"          # 신규
    SPONSORED_DETECTOR       = "sponsored_detector"         # 신규
    LENGTH_FILTER            = "length_filter"              # 신규
    DUPLICATE_DETECTOR       = "duplicate_detector"         # 신규
    LANGUAGE_DETECTOR        = "language_detector"          # 신규
    SPELL_NORMALIZER         = "spell_normalizer"           # 신규 (배치 적용)
    # 데이터 전처리
    FORMAT_NORMALIZER        = "format_normalizer"
    KPI_FORMAT_PARSER        = "kpi_format_parser"
    KPI_CALCULATOR           = "kpi_calculator"             # 신규
    TEXT_TOKENIZER           = "text_tokenizer"
    PII_MASKER               = "pii_masker"                 # 신규

    # === analysis_agent (10) ===
    KEYWORD_EXTRACTOR        = "keyword_extractor"
    TREND_DETECTOR           = "trend_detector"
    SENTIMENT_ANALYZER       = "sentiment_analyzer"
    INSIGHT_EXTRACTOR        = "insight_extractor"
    ML_ANALYSIS_REPORTER     = "ml_analysis_reporter"
    # POC 시나리오용 (잠정 명칭 — 카탈로그 확정 시 변경 가능)
    KPI_ANOMALY_DETECTOR     = "kpi_anomaly_detector"       # POC-01
    FREQUENCY_ANALYZER       = "frequency_analyzer"         # POC-02
    CTR_TREND_ANALYZER       = "ctr_trend_analyzer"         # POC-02
    AB_TEST_RUNNER           = "ab_test_runner"             # POC-03
    KEYWORD_FILTER           = "keyword_filter"             # POC-04
    CAUSE_ESTIMATOR          = "cause_estimator"            # POC-04
    CREATIVE_QUALITY_SCORER  = "creative_quality_scorer"    # POC-05 (Vision LLM)
    MOVING_AVERAGE_FORECASTER = "moving_average_forecaster" # POC-06
    KPI_INSIGHT_GENERATOR    = "kpi_insight_generator"      # POC-01~08 공통
    SUMMARY_GENERATOR        = "summary_generator"          # POC-01~08 공통

    # === report_agent (4) ===
    INSIGHT_SYNTHESIZER      = "insight_synthesizer"
    REPORT_WRITER            = "report_writer"
    REPORT_SECTION_PLANNER   = "report_section_planner"
    # summary_generator는 analysis_agent에서 정의, report_agent도 공유 사용

    # === pdf_agent (3) ===
    CHART_GENERATOR          = "chart_generator"
    TEMPLATE_SELECTOR        = "template_selector"
    PDF_CONVERTER            = "pdf_converter"              # ← data_analysis에서 이동

    # === image_creation_agent (3) ===
    AD_PROMPT_GENERATOR  = "ad_prompt_generator"
    AD_IMAGE_GENERATOR   = "ad_image_generator"
    SLOGAN_GENERATOR     = "slogan_generator"

    # === video_creation_agent (1) ===
    STORYBOARD_PLANNER   = "storyboard_planner"

    # === 공유 Tool (5) ===
    IMAGE_RESIZER             = "image_resizer"
    THUMBNAIL_CREATOR         = "thumbnail_creator"
    FORMAT_CONVERTER          = "format_converter"
    BRAND_GUIDELINE_ANALYZER  = "brand_guideline_analyzer"
    BRAND_SAFETY_CHECKER      = "brand_safety_checker"
```

### 2.3 Tool 그룹 매핑

```python
TOOL_GROUP: Dict[str, str] = {
    # collection_agent
    "naver_collector": "수집", "youtube_collector": "수집",
    "naver_ads_collector": "성과수집", "meta_ads_collector": "성과수집",
    # preprocessing_agent — 텍스트 클렌징
    "text_preprocessor": "전처리", "emoji_handler": "전처리",
    "repeat_char_normalizer": "전처리", "html_url_stripper": "전처리",
    "sponsored_detector": "전처리", "length_filter": "전처리",
    "duplicate_detector": "전처리", "language_detector": "전처리",
    "spell_normalizer": "전처리",
    # preprocessing_agent — 데이터 전처리
    "format_normalizer": "전처리", "kpi_format_parser": "전처리",
    "kpi_calculator": "전처리", "text_tokenizer": "전처리",
    "pii_masker": "전처리",
    # analysis_agent
    "keyword_extractor": "ML", "trend_detector": "ML",
    "sentiment_analyzer": "ML",
    "insight_extractor": "LLM", "ml_analysis_reporter": "LLM",
    "kpi_anomaly_detector": "분석", "frequency_analyzer": "분석",
    "ctr_trend_analyzer": "분석", "ab_test_runner": "분석",
    "keyword_filter": "분석", "cause_estimator": "분석",
    "creative_quality_scorer": "분석", "moving_average_forecaster": "분석",
    "kpi_insight_generator": "분석", "summary_generator": "분석",
    # report_agent
    "insight_synthesizer": "보고서", "report_writer": "보고서",
    "report_section_planner": "보고서",
    # pdf_agent
    "chart_generator": "PDF", "template_selector": "PDF",
    "pdf_converter": "PDF",
    # image_creation_agent
    "ad_prompt_generator": "이미지", "ad_image_generator": "이미지",
    "slogan_generator": "슬로건",
    # video_creation_agent
    "storyboard_planner": "영상",
    # 공유
    "image_resizer": "공유", "thumbnail_creator": "공유",
    "format_converter": "공유", "brand_guideline_analyzer": "공유",
    "brand_safety_checker": "공유",
}

AGENT_TOOLS: Dict[str, List[str]] = {
    "collection_agent": [
        "naver_collector", "youtube_collector",
        "naver_ads_collector", "meta_ads_collector",
        # 2차 추가: tiktok_collector, oliveyoung_collector, brief_parser
    ],
    "preprocessing_agent": [
        # 텍스트 클렌징 8단계
        "text_preprocessor", "emoji_handler",
        "repeat_char_normalizer", "html_url_stripper",
        "sponsored_detector", "length_filter",
        "duplicate_detector", "language_detector",
        "spell_normalizer",
        # 데이터 전처리
        "format_normalizer", "kpi_format_parser", "kpi_calculator",
        "text_tokenizer", "pii_masker",
    ],
    "analysis_agent": [
        "keyword_extractor", "trend_detector",
        "sentiment_analyzer",
        "insight_extractor", "ml_analysis_reporter",
        # POC 시나리오용 신규 Tool (잠정 명칭)
        "kpi_anomaly_detector",
        "frequency_analyzer", "ctr_trend_analyzer",
        "ab_test_runner",
        "keyword_filter", "cause_estimator",
        "creative_quality_scorer",        # Vision LLM
        "moving_average_forecaster",
        "kpi_insight_generator",
        "summary_generator",
    ],
    "report_agent": [
        "insight_synthesizer",
        "report_writer",
        "report_section_planner",
        "summary_generator",
    ],
    "pdf_agent": [
        "chart_generator",
        "template_selector",
        "pdf_converter",
    ],
    "image_creation_agent": [
        "ad_prompt_generator", "ad_image_generator", "slogan_generator",
    ],
    "video_creation_agent": [
        "storyboard_planner",
    ],
    "shared": [
        "image_resizer", "thumbnail_creator", "format_converter",
        "brand_guideline_analyzer", "brand_safety_checker",
    ],
}
```

### 2.4 Tool 유형

```python
class ToolType(str, Enum):
    """Tool 실행 유형"""
    TOOL      = "tool"        # 단순 함수 호출
    SUBGRAPH  = "subgraph"    # LangGraph 서브그래프 (내부 상태 보유)

TOOL_TYPE_MAP: Dict[str, str] = {
    # collection_agent — 외부 API 연동이므로 subgraph
    "naver_collector": "subgraph", "youtube_collector": "subgraph",
    "naver_ads_collector": "subgraph", "meta_ads_collector": "subgraph",
    # 공유 — 브랜드 분석은 subgraph
    "brand_guideline_analyzer": "subgraph", "brand_safety_checker": "subgraph",
    # 나머지 전부 "tool" (preprocessing, analysis, report, pdf, image, video)
}
```

### 2.5 Layer

```python
class Layer(str, Enum):
    """4-Layer 아키텍처"""
    COGNITIVE  = "cognitive"
    PLANNING   = "planning"
    EXECUTION  = "execution"
    RESPONSE   = "response"
```

### 2.6 ExecutionStrategy — POC

```python
class ExecutionStrategy(str, Enum):
    """실행 전략 — Orchestrator가 Todo의 depends_on 기반으로 자동 판단"""
    SINGLE      = "single"       # Todo 1개만 실행
    SEQUENTIAL  = "sequential"   # 순차 실행 (모든 Todo에 직렬 의존성)
    PARALLEL    = "parallel"     # 병렬 실행 (의존성 없는 Todo들 동시 실행)
```

**Orchestrator 실행 전략 판단:**

```python
def determine_strategy(todos: List[TodoItem]) -> ExecutionStrategy:
    """Todo의 depends_on을 분석하여 실행 전략을 자동 결정"""
    if len(todos) <= 1:
        return ExecutionStrategy.SINGLE
    independent = [t for t in todos if not t.depends_on]
    if len(independent) >= 2:
        return ExecutionStrategy.PARALLEL
    return ExecutionStrategy.SEQUENTIAL
```

**병렬 실행 흐름:**

```
Orchestrator는 매 Step마다 Plan.get_ready_todos()를 호출하여
의존성이 충족된 Todo를 모두 가져와 동시에 실행한다.

예시:
  Step 1: todo_001(naver) + todo_002(youtube) 동시 실행  ← depends_on: []
  Step 2: todo_003(전처리) 실행                          ← depends_on: [001, 002] 완료 확인
  Step 3: todo_004(키워드) 실행                          ← depends_on: [003]
  Step 4: todo_005(인사이트) 실행                        ← depends_on: [004]
```

### 2.7 TodoStatus

```python
class TodoStatus(str, Enum):
    """POC: 재시도 없음 — failed는 즉시 final"""
    PENDING         = "pending"
    IN_PROGRESS     = "in_progress"
    COMPLETED       = "completed"
    FAILED          = "failed"           # final — 재시도 없음
    BLOCKED         = "blocked"
    SKIPPED         = "skipped"
    NEEDS_APPROVAL  = "needs_approval"
    CANCELLED       = "cancelled"
```

### 2.8 PlanStatus

```python
class PlanStatus(str, Enum):
    DRAFT            = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED         = "approved"
    EXECUTING        = "executing"
    PAUSED           = "paused"      # 사용자 pause 시
    COMPLETED        = "completed"
    FAILED           = "failed"
    CANCELLED        = "cancelled"
```

### 2.9 SessionStatus

```python
class SessionStatus(str, Enum):
    CREATED      = "created"
    RUNNING      = "running"
    PAUSED       = "paused"          # 사용자가 pause 버튼으로 중단
    COMPLETED    = "completed"
    FAILED       = "failed"
    CANCELLED    = "cancelled"
```

### 2.10 HITLRequestType

```python
class HITLRequestType(str, Enum):
    """HITL 요청 유형 — 시스템 요청 4종 + 사용자 중단 1종"""
    # 시스템 → 사용자 (Tool이 사용자 개입 요청)
    PLAN_REVIEW    = "plan_review"
    APPROVAL       = "approval"
    CLARIFICATION  = "clarification"
    INPUT          = "input"
    # 사용자 → 시스템 (AE가 직접 중단)
    USER_PAUSE     = "user_pause"    # pause 버튼 → 작업 중단, 중간 결과 확인
```

> **HITL 트리거 2가지:**
> - **시스템 트리거** (plan_review, approval, clarification, input): Tool이 사용자 확인 필요하다고 판단
> - **사용자 트리거** (user_pause): AE가 언제든 pause 버튼으로 작업 중단 가능

> **에이전트별 HITL 범위:**
> | 에이전트 | 시스템 트리거 (tool → 사용자) | 사용자 트리거 (user_pause) | POC 포함 |
> |---------|---------------------------|------------------------|---------|
> | 실행 에이전트 | O | O | O |
> | 모니터링 에이전트 | O | O | X |

### 2.11 HITLPriority

```python
class HITLPriority(str, Enum):
    """HITL 우선순위 — 멀티세션 큐잉 정렬 기준"""
    URGENT = "urgent"
    HIGH   = "high"
    MEDIUM = "medium"
    LOW    = "low"

PRIORITY_ORDER: Dict[str, int] = {
    "urgent": 0, "high": 1, "medium": 2, "low": 3,
}
```

---

## 3. Agent & Tool 정의

### 3.1 Tool 명세

```python
from pydantic import BaseModel, Field, ConfigDict, computed_field, field_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, timedelta

class ToolSpec(BaseModel):
    """POC Tool 명세"""
    name: str                    # PocTool Enum 값
    agent: str                   # PocAgent Enum 값
    tool_type: str               # "tool" | "subgraph"
    group: str                   # "수집" | "전처리" | "ML" | "LLM" | "보고서" | "이미지" | "슬로건" | "영상" | "공유"
    description: str
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    timeout_sec: int = 300
```

### 3.2 Tool → 결과 모델 매핑

```python
# models/tool_registry.py
from typing import Literal

PocToolLiteral = Literal[
    "naver_collector", "youtube_collector", "naver_ads_collector", "meta_ads_collector",
    "text_preprocessor", "emoji_handler", "format_normalizer", "kpi_format_parser",
    "text_tokenizer", "keyword_extractor", "trend_detector",
    "insight_extractor", "ml_analysis_reporter", "pdf_converter",
    "ad_prompt_generator", "ad_image_generator", "slogan_generator",
    "storyboard_planner",
    "image_resizer", "thumbnail_creator", "format_converter",
    "brand_guideline_analyzer", "brand_safety_checker",
]
```

---

## 4. Chat Session & Memory Models

### 4.1 ChatSession

```python
import uuid
from datetime import datetime, timedelta

class ChatSession(BaseModel):
    """채팅 세션 — AE당 N개 생성 가능

    ERD: chat_sessions 테이블 매핑.
    각 채팅방은 독립적인 대화 컨텍스트를 가진다.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str            # ERD: client_id uuid
    user_id: str              # ERD: user_id uuid — AE 식별
    title: str = ""           # 채팅방 제목 (자동 생성 또는 사용자 지정)
    status: SessionStatus = SessionStatus.CREATED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active_at: datetime = Field(default_factory=datetime.utcnow)
```

### 4.2 ChatMessage

```python
class ChatMessage(BaseModel):
    """채팅 메시지 — ERD: chat_messages 테이블 매핑"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str      # FK: chat_sessions.id
    role: str                 # "user" | "assistant" | "system"
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)  # step_preview 참조 등
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 4.3 SessionMemory — 단기 메모리

```python
class SessionMemory(BaseModel):
    """세션별 단기 메모리 — 실행 중 컨텍스트 유지

    각 채팅 세션의 대화 히스토리, 중간 결과, 사용자 선호를 저장한다.
    세션이 COMPLETED되면 LongTermMemory로 압축 저장된다.
    """
    session_id: str
    messages: List[Dict[str, Any]] = Field(default_factory=list)  # 대화 히스토리 (최근 N개)
    context: Dict[str, Any] = Field(default_factory=dict)          # 현재 작업 컨텍스트
    intermediate_results: Dict[str, Any] = Field(default_factory=dict)  # Tool 중간 결과
    max_messages: int = 50    # 단기 메모리 최대 메시지 수
```

### 4.4 LongTermMemory — 장기 기억

```python
class LongTermMemory(BaseModel):
    """장기 기억 — 세션 완료 후 압축 저장

    ERD: long_term_memories 테이블 (신규 추가 필요)
    LLM으로 대화 내용을 요약하여 핵심 인사이트만 보존한다.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str              # AE 식별
    client_id: str            # 광고주
    source_session_id: str    # 원본 채팅 세션 ID
    summary: str              # LLM이 생성한 대화 요약
    key_insights: List[str] = Field(default_factory=list)  # 핵심 인사이트 목록
    tools_used: List[str] = Field(default_factory=list)    # 사용된 Tool 목록
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

### 4.5 메모리 압축 흐름

```
세션 실행 중:
  SessionMemory에 대화/중간결과 누적

세션 COMPLETED:
  1. SessionMemory.messages + intermediate_results를 LLM에 전달
  2. LLM이 요약(summary) + 핵심 인사이트(key_insights) 생성
  3. LongTermMemory로 저장
  4. SessionMemory는 유지 (재방문 시 참조 가능)

다음 세션에서:
  1. 같은 client_id의 LongTermMemory를 조회
  2. Cognitive Layer 프롬프트에 장기 기억 주입
  3. "이전에 이 광고주에 대해 이런 분석을 했었다" 컨텍스트 활용

메모리 압축 실패 시:
  1. WS stream 채널로 error 이벤트 전송:
     { type: "error", session_id, data: { code: "MEMORY_COMPRESSION_FAILED", message: "..." } }
  2. LongTermMemory는 생성되지 않음 — 다음 세션에서 장기 기억 없이 진행
  3. SessionMemory는 유지되므로 같은 채팅방 재방문 시 단기 메모리 참조 가능
  4. 워크플로우 자체는 이미 COMPLETED이므로 실패가 결과에 영향 없음
```

---

## 5. Intent Models

### 5.1 Intent — POC

```python
class Intent(BaseModel):
    """POC 의도 분류 — 에이전트 라우팅에 사용"""
    agent: PocAgent              # 어떤 에이전트가 처리할지
    task_description: str        # 작업 설명 (LLM이 생성)
    confidence: float = Field(ge=0.0, le=1.0)
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    raw_input: str = ""
    language: str = "ko"

    model_config = {"frozen": True}
```

### 5.2 CognitiveOutput — POC

```python
class CognitiveOutput(BaseModel):
    """Cognitive Layer 출력"""
    intent: Intent
    requires_clarification: bool = False
    clarification_question: Optional[str] = None
    suggested_tools: List[str] = Field(default_factory=list)  # PocTool 값
    long_term_context: Optional[str] = None  # 장기 기억에서 가져온 관련 컨텍스트
```

---

## 6. Todo Models

### 6.1 TodoItem — POC

```python
class TodoItem(BaseModel, frozen=True):
    """Todo 아이템 — POC: 재시도 없음, 즉시 failed

    retry_count/max_retries 필드 제거 — POC에서 재시도 미지원.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    plan_id: Optional[str] = None

    task: str
    description: Optional[str] = None

    tool: PocTool                # PocTool Enum — 23종
    tool_params: Dict[str, Any] = Field(default_factory=dict)

    status: TodoStatus = TodoStatus.PENDING
    priority: int = Field(default=5, ge=0, le=10)  # 낮은 숫자 = 높은 우선순위

    depends_on: List[str] = Field(default_factory=list)

    timeout_sec: int = 300

    requires_approval: bool = False

    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    version: int = 1

    def with_status(self, new_status: str, **kwargs) -> "TodoItem":
        """상태 변경 — POC: 재시도 없음, failed는 즉시 final"""
        allowed = VALID_TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise ValueError(f"Invalid transition: {self.status} → {new_status}")

        now = datetime.utcnow()
        auto_fields: Dict[str, Any] = {}
        if new_status == "in_progress" and self.started_at is None:
            auto_fields["started_at"] = now
        if new_status in ("completed", "failed", "skipped", "cancelled"):
            auto_fields["completed_at"] = now

        return self.model_copy(
            update={"status": new_status, "version": self.version + 1,
                    **auto_fields, **kwargs},
            validate=True,
        )
```

### 6.2 상태 전환 규칙 — POC

```python
VALID_TRANSITIONS: dict[str, list[str]] = {
    "pending":         ["in_progress", "blocked", "needs_approval", "cancelled", "skipped"],
    "blocked":         ["pending", "cancelled"],
    "needs_approval":  ["pending", "cancelled", "skipped"],
    "in_progress":     ["completed", "failed"],  # POC: failed 즉시 전환, 재시도 없음
    "completed":       [],  # final
    "failed":          [],  # final — POC: 재시도 미지원
    "skipped":         [],  # final
    "cancelled":       [],  # final
}
```

---

## 7. Plan Models

### 7.1 Plan — POC

```python
class Plan(BaseModel):
    """실행 계획 — POC: SEQUENTIAL/PARALLEL 지원, pause 지원"""
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str        # 어떤 채팅방에서 생성된 Plan인지
    version: int = 1
    status: PlanStatus = PlanStatus.DRAFT

    todos: List[TodoItem] = Field(default_factory=list)
    strategy: ExecutionStrategy = ExecutionStrategy.SEQUENTIAL

    estimated_duration_sec: int = 0

    created_at: datetime = Field(default_factory=datetime.utcnow)

    @computed_field
    @property
    def dependency_graph(self) -> Dict[str, List[str]]:
        return {t.id: list(t.depends_on) for t in self.todos}

    def get_ready_todos(self) -> List[TodoItem]:
        satisfied = {t.id for t in self.todos if t.status in ("completed", "skipped")}
        return [
            t for t in self.todos
            if t.status == "pending"
            and all(dep in satisfied for dep in t.depends_on)
        ]

    def get_progress_percentage(self) -> float:
        if not self.todos:
            return 0.0
        final = {"completed", "failed", "skipped", "cancelled"}
        done = sum(1 for t in self.todos if t.status in final)
        return (done / len(self.todos)) * 100
```

---

## 8. Execution Models

### 8.1 ExecutionResult — POC

```python
class ExecutionResult(BaseModel):
    """Tool 실행 결과"""
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

    todo_id: str
    tool: PocTool
    started_at: datetime
    completed_at: datetime
    execution_time_ms: float = 0.0

    # 중간 미리보기용 요약
    preview_data: Optional[Dict[str, Any]] = None  # FE에 보여줄 결과 일부
```

### 8.2 ExecutionContext — POC

```python
class ExecutionContext(BaseModel):
    """Tool 실행 시 전달되는 컨텍스트"""
    session_id: str
    plan_id: str
    client_id: str
    user_id: str
    language: str = "ko"
    previous_results: Dict[str, Any] = Field(default_factory=dict)
    session_memory: Optional[Dict[str, Any]] = None  # SessionMemory 참조
```

---

## 9. Step Preview Models

### 9.1 StepPreview

```python
class StepPreview(BaseModel):
    """단계별 중간 미리보기 — 각 Tool 완료 시 FE에 전송

    Tool이 완료될 때마다 결과의 일부를 FE에 보여준다.
    예: naver_collector 완료 → 수집된 데이터 건수 + 샘플 3건
    예: keyword_extractor 완료 → 추출된 상위 키워드 10개
    예: ad_image_generator 완료 → 생성된 이미지 URL
    """
    todo_id: str
    tool: str                    # PocTool 값
    group: str                   # Tool 그룹 ("수집", "전처리", "ML" 등)
    step_index: int              # 전체 Plan에서 몇 번째 단계인지 (0-based)
    total_steps: int             # 전체 단계 수

    preview_type: str            # "data_sample" | "statistics" | "image" | "text" | "chart"
    title: str                   # 미리보기 제목 ("네이버 데이터 수집 완료")
    summary: str                 # 한 줄 요약 ("142건 수집, 최근 30일")
    data: Dict[str, Any] = Field(default_factory=dict)  # 미리보기 데이터

    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 9.2 Tool별 미리보기 데이터 규격

| Tool | preview_type | data 구조 |
|------|-------------|-----------|
| `naver_collector` | `data_sample` | `{ count: 142, sample: [{title, url, date}...], period: "30d" }` |
| `youtube_collector` | `data_sample` | `{ count: 89, sample: [{title, channel, views}...] }` |
| `naver_ads_collector` | `statistics` | `{ campaigns: 5, total_spend: 4200000, avg_cpc: 580 }` |
| `meta_ads_collector` | `statistics` | `{ campaigns: 3, total_spend: 2100000, avg_ctr: 0.038 }` |
| `keyword_extractor` | `text` | `{ keywords: ["CPC", "전환율", ...], count: 15 }` |
| `trend_detector` | `chart` | `{ trends: [{keyword, direction, score}...] }` |
| `insight_extractor` | `text` | `{ insights: ["CPC 급등 원인은...", ...], count: 3 }` |
| `ml_analysis_reporter` | `text` | `{ report_summary: "...", sections: 4 }` |
| `pdf_converter` | `text` | `{ file_url: "/api/v1/files/...", file_size_kb: 1240 }` |
| `ad_prompt_generator` | `text` | `{ prompts: ["여름 쿨링 제품...", ...], count: 3 }` |
| `ad_image_generator` | `image` | `{ images: [{url, width, height}...], count: 2 }` |
| `slogan_generator` | `text` | `{ slogans: ["시원한 여름, 쿨링펫", ...], count: 5 }` |
| `storyboard_planner` | `text` | `{ scenes: [{scene_num, description, duration}...] }` |

---

## 10. Response Models

### 10.1 ResponsePayload — POC

```python
class ResponsePayload(BaseModel):
    """최종 응답"""
    format: str = "text"        # "text" | "image" | "pdf" | "mixed"
    text: str
    summary: str = ""
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    step_previews: List[str] = Field(default_factory=list)  # StepPreview ID 목록 (FE 참조용)
```

---

## 11. HITL Models

### 11.1 HITLRequest — POC

```python
class HITLRequest(BaseModel):
    """HITL 요청 — POC: budget_review 제거, severity 기반 큐잉

    멀티세션 환경에서 여러 세션의 HITL 요청이 동시에 발생할 수 있다.
    priority 기반으로 큐잉하여 urgent가 먼저 AE에게 표시된다.

    ⚠ 직렬화: model_dump(by_alias=True) 필수
    """
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        serialization_alias="request_id",
    )
    client_id: str
    session_id: str        # 어떤 채팅방에서 발생했는지
    user_id: str                # AE 식별
    type: HITLRequestType
    priority: HITLPriority = HITLPriority.MEDIUM
    status: str = "pending"

    title: str
    description: str = ""

    data: Dict[str, Any] = Field(default_factory=dict)
    options: List[str] = Field(default_factory=list)

    wait_minutes: int = Field(default=5, ge=1, le=30)
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

    @computed_field
    @property
    def timeout_at(self) -> datetime:
        return self.requested_at + timedelta(minutes=self.wait_minutes)
```

### 11.2 HITL 멀티세션 큐잉 규칙

```
AE가 채팅 3개를 동시에 실행 중:
  채팅 A: plan_review (priority=medium)
  채팅 B: approval (priority=urgent) — 비용 관련
  채팅 C: clarification (priority=low)

큐잉 순서: B(urgent) → A(medium) → C(low)
FE에서 HITL 모달은 priority 순으로 표시.
같은 priority면 requested_at 순 (먼저 요청된 것 우선).
```

### 11.3 HITLResponse — POC

```python
class HITLResponse(BaseModel):
    hitl_request_id: str
    session_id: str
    action: Literal["approve", "reject", "skip", "modify"]
    value: Optional[Any] = None
    comment: Optional[str] = None
    responded_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## 12. AgentState — POC

> Graph State 명세서(v1.0) 기준. client_id는 State에 포함하지 않음.

```python
from typing import TypedDict, Annotated, Optional

class AgentState(TypedDict, total=False):
    """POC AgentState — 멀티세션 환경

    각 채팅 세션마다 독립적인 AgentState가 생성된다.
    client_id/user_id는 ExecutionContext로 주입.
    """

    # ─── Session ───
    session_id: str              # 채팅방 UUID (chat_sessions.id)
    user_input: str
    language: str                # "ko" | "en" | "ja"

    # ─── Layer Results ───
    cognitive_result: dict       # CognitiveOutput.model_dump()
    planning_result: dict
    execution_results: Annotated[dict, results_reducer]
    response_result: dict

    # ─── Plan & Todos ───
    plan: dict
    todos: Annotated[list, todo_reducer]

    # ─── Control ───
    error: Optional[str]         # 시스템 에러 전용

    # ─── HITL ───
    hitl_pending: Optional[dict]

    # ─── Trace ───
    trace: Annotated[list, trace_reducer]

    # ─── Memory (POC 추가) ───
    memory_context: Optional[dict]  # SessionMemory에서 주입된 컨텍스트
```

### 12.1 hitl_pending 최소 구조

```python
# Agent 트리거
{
    "hitl_type": "agent_trigger",
    "request_id": "hitl_uuid_001",   # DB 조회 키
    "todo_id": "todo_005",
    "trigger": "plan_review",
    "question": "실행 계획을 검토해주세요",
    "options": ["approve", "modify", "reject"],
}
```

---

## 13. Reducers — POC

```python
def todo_reducer(existing: list, updates: list) -> list:
    """Todo 병합 — POC: failed도 final"""
    existing_map = {t["id"]: t for t in existing}
    final_statuses = {"completed", "failed", "skipped", "cancelled"}

    for update in updates:
        todo_id = update["id"]
        if todo_id in existing_map:
            if existing_map[todo_id].get("status") not in final_statuses:
                existing_map[todo_id] = update
        else:
            existing_map[todo_id] = update

    result = list(existing_map.values())
    result.sort(key=lambda t: t.get("priority", 5))
    return result


def _deep_merge(base: dict, override: dict) -> dict:
    result = {**base}
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def results_reducer(existing: dict, new: dict) -> dict:
    """실행 결과 병합 — 재귀적 딕셔너리 병합"""
    return _deep_merge(existing, new)


MAX_TRACE_ENTRIES = 200  # POC: 500 → 200으로 축소

def trace_reducer(existing: list, new: list) -> list:
    combined = existing + new
    if len(combined) > MAX_TRACE_ENTRIES:
        combined = combined[-MAX_TRACE_ENTRIES:]
    return combined
```

---

## 14. Validation Rules

### 14.1 비즈니스 규칙

| 규칙 | 값 | 카운트 기준 | 에러 코드 |
|------|---|-------------|----------|
| **AE당 채팅방 최대 개수** | **10개** | `chat_sessions` 테이블에서 해당 user_id의 **삭제되지 않은 모든 행** (status 무관 — created/running/paused/completed/failed/cancelled 전부 포함) | `CHAT_SESSION_LIMIT_EXCEEDED` |
| 메시지 길이 | 1~10,000자 | — | `VALIDATION_INVALID_INPUT` |
| HITL 타임아웃 | 1~30분 | — | `HITL_TIMEOUT` |

> **채팅방 제한 정책 (POC):**
> - 11번째 채팅방 생성 요청 시 즉시 거부 (자동 삭제 없음 — LRU 미적용)
> - 사용자가 기존 채팅방을 명시적으로 DELETE한 후 새로 생성해야 함
> - 동시 생성 race condition 방지: DB 트랜잭션 내에서 SELECT FOR UPDATE 또는
>   `UNIQUE (user_id, slot_index)` 제약으로 atomic하게 처리

### 14.2 Pydantic 검증

```python
class AgentRunRequestSchema(BaseModel):
    """POC API 요청 검증"""
    message: str
    session_id: str         # 어떤 채팅방에서 실행하는지
    language: str = "ko"

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("message cannot be empty")
        if len(v) > 10000:
            raise ValueError("message exceeds 10000 characters")
        return v

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        v = v.strip().lower()
        if not v:
            raise ValueError("session_id cannot be empty")
        import re
        pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        if not re.match(pattern, v):
            raise ValueError("session_id must be UUID format")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if v not in ("ko", "en", "ja"):
            raise ValueError("language must be 'ko', 'en', or 'ja'")
        return v
```

---

## ERD 추가 필요 테이블

```sql
-- 장기 기억 테이블 (신규)
Table long_term_memories {
  id uuid [pk]
  user_id uuid [ref: > users.id]
  client_id uuid [ref: > clients.id]
  source_session_id uuid [ref: > chat_sessions.id]
  summary text
  key_insights jsonb
  tools_used jsonb
  created_at timestamp
  metadata jsonb
}
```

---

## datetime 규칙

> 본 문서의 코드 예시에서 `datetime.utcnow()`를 사용하고 있으나,
> Python 3.12+에서 deprecated이므로 실제 구현 시 `datetime.now(timezone.utc)`를 사용한다.
> ```python
> from datetime import datetime, timezone
> # ❌ datetime.utcnow()          — deprecated
> # ✅ datetime.now(timezone.utc)  — 권장
> ```

---

## Related Documents

- [DATA_MODELS.md](DATA_MODELS.md) — Full 스펙 (v3.2)
- [INTERFACE_CONTRACT_poc.md](INTERFACE_CONTRACT_poc.md) — POC API 계약
- [WEBSOCKET_PROTOCOL_poc.md](WEBSOCKET_PROTOCOL_poc.md) — POC WebSocket 프로토콜
- [Graph State 명세서](../main_gratph_state_명세서_260401.md) — AgentState 기준
- [ERD v2](../ADALLPIN_ERD_v2.md) — DB 스키마
- [MOCK_DATA_SPEC_poc.md](MOCK_DATA_SPEC_poc.md) — POC Mock 데이터 스키마 (블루밤글로우 4채널 RAW, 정규화 매핑, KPI 공식 등)

---

*Last Updated: 2026-04-10 | Version 1.1 — Agent 7종 재편 (data_analysis → collection/preprocessing/analysis 분리, report/pdf 분리), Tool 34종 확장, mock 데이터 스키마 참조 추가*
