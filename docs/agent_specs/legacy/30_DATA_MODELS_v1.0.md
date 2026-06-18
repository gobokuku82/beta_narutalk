# Data Models Specification (Sprint 13+)

| 항목 | 내용 |
|------|------|
| 담당자 | 도윤 |
| 분류 | 개발 - 데이터 모델 |
| 진행상태 | **Active** (POC 격상 + Sprint 10~13 반영) |
| 버전 | **v1.0** |
| 최종 수정일 | 2026-04-21 |
| 이전 버전 | `POC_legacy/DATA_MODELS_poc.md` (v1.1, 2026-04-10) |
| 관련 명세 | `20_INTERFACE_CONTRACT_v1.1.md`, `21_WEBSOCKET_PROTOCOL_v1.2.md`, `11_main_graph_state_v1.5.md` |

> **진실 소스 (Source of Truth)**: 이 문서는 **설계 참조**이다. 실제 모델의 진실 소스는 **코드** (`backend/app/dream_agent/schemas/*.py`). 문서와 코드 간 차이가 있으면 **코드가 우선**.

---

## 0. 개요

OctorAD Dream Agent V2의 **Pydantic / dataclass 모델** 전체 카탈로그.

주요 카테고리:
1. **Session 식별**: user_id / conversation_id / turn_id (Sprint 13 — main_graph_state 참조)
2. **Core Enums**: TaskType, TodoStatus 등
3. **StructuredQuery** (Cognitive 산출)
4. **Plan + Todo** (Planning 산출)
5. **ExecutionResult** (Execution 산출)
6. **ExecutionProgress** (HITL pause/resume 영속화, Sprint 12)
7. **ResponsePayload** (Response 산출)
8. **HITLRequest / HITLResponse** (Sprint 12 HITL PM)

---

## 1. Session 식별 (Sprint 13 I6)

`11_main_graph_state_v1.5.md §2.0-a` 참조. `AgentState` TypedDict에 포함:

```python
class AgentState(TypedDict, total=False):
    # Sprint 13 I6
    user_id: str                         # Settings fallback "demo"
    conversation_id: str                 # 클라 UUID
    turn_id: str                         # 클라 UUID per query
    session_id: str                      # deprecated — turn_id alias
    conversation_history: list[dict]     # Cognitive 주입용
    history_limit: int
    ...
```

---

## 2. Core Enums

### 2.1 TaskType (Cognitive 출력)

Cognitive가 생성하는 tasks 타입 (17종, `structured_query.py`):

```python
class TaskType(str, Enum):
    data_collection = "data_collection"
    sentiment_analysis = "sentiment_analysis"
    keyword_extraction = "keyword_extraction"
    insight_extraction = "insight_extraction"
    report_generation = "report_generation"
    pdf_rendering = "pdf_rendering"
    image_creation = "image_creation"
    video_creation = "video_creation"
    storyboard_creation = "storyboard_creation"
    slogan_writing = "slogan_writing"
    copy_generation = "copy_generation"
    summary_generation = "summary_generation"
    preprocessing = "preprocessing"
    format_normalization = "format_normalization"
    text_preprocessing = "text_preprocessing"
    ambiguity_resolution = "ambiguity_resolution"
    factual_answer = "factual_answer"
```

### 2.2 GoalType / Depth / OutputFormat

```python
class GoalType(str, Enum):
    analysis = "analysis"          # 분석
    generation = "generation"      # 생성 (이미지, 카피 등)
    factual = "factual"            # 사실 질의응답
    mixed = "mixed"                # 분석 + 생성 복합

class Depth(str, Enum):
    brief = "brief"                # 간단
    standard = "standard"          # 보통
    detailed = "detailed"          # 상세

class OutputFormat(str, Enum):
    text = "text"
    markdown = "markdown"
    pdf = "pdf"
    image = "image"
    video = "video"
```

### 2.3 Source / Period

Cognitive가 **data source** / **period** 를 추출:

```python
class Source(str, Enum):
    naver = "naver"
    google = "google"
    instagram = "instagram"
    youtube = "youtube"
    internal = "internal"
    unknown = "unknown"            # Cognitive가 unknown 낙관적 배정

class Period(BaseModel):
    start: Optional[date] = None
    end: Optional[date] = None
    raw: str = ""                  # 원본 표현 ("최근 30일" 등)
```

### 2.4 TodoStatus (Execution 단계)

```python
class TodoStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    success = "success"            # 호환 alias
    failed = "failed"              # final — 재시도 불가
    skipped = "skipped"
    cancelled = "cancelled"
```

### 2.5 HITLRequestType / HITLPriority (Sprint 12)

```python
class HITLRequestType(str, Enum):
    PLAN_REVIEW = "plan_review"
    APPROVAL = "approval"              # Execution pause 시
    CLARIFICATION = "clarification"    # Sprint 14+
    USER_INPUT = "user_input"          # Sprint 14+

class HITLPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
```

---

## 3. StructuredQuery (Cognitive 산출)

코드: `backend/app/dream_agent/schemas/structured_query.py`

```python
class Targets(BaseModel):
    brand: Optional[str] = None           # "블루밍글로우"
    product: Optional[str] = None
    domain: Optional[str] = None          # "뷰티 리뷰" 등
    additional: dict[str, Any] = {}       # 유연 슬롯

class Goal(BaseModel):
    type: GoalType                        # analysis/generation/factual/mixed
    depth: Depth                          # brief/standard/detailed
    output_format: OutputFormat = OutputFormat.text

class Task(BaseModel):
    id: TaskType                          # TaskType enum
    priority: int = 1                     # 낮을수록 우선
    rationale: Optional[str] = None

class Ambiguity(BaseModel):
    field: str                            # 모호한 필드명
    question: str                         # 사용자에게 물을 질문

class QueryMeta(BaseModel):
    sources: list[Source] = []
    period: Optional[Period] = None
    language: str = "ko"
    ambiguities: list[Ambiguity] = []

class StructuredQuery(BaseModel):
    targets: Targets
    goal: Goal
    tasks: list[Task]
    meta: QueryMeta = QueryMeta()
```

**Writer**: `cognitive_stage` (Sprint 9: 3계층 프롬프트 기반 LLM 생성).
**JSON dump**: `sq.model_dump(mode="json")` → `AgentState["structured_query"]`.

---

## 4. Plan + Todo (Planning 산출)

코드: `backend/app/dream_agent/planning/planner.py`

### 4.1 PlannedTodo

```python
class PlannedTodo(BaseModel):
    id: str                               # "todo_001"
    task_type: str                        # TaskType value
    team: str                             # "analysis_team" 등
    agent: str                            # "collection_agent" 등
    tool: str                             # "naver_collector" 등
    tool_params: dict[str, Any] = {}
    depends_on: list[str] = []            # DAG 의존성
    priority: int = 1
    rationale: Optional[str] = None
    requires_approval: bool = False       # Sprint 14 예정
```

### 4.2 Plan

```python
class Plan(BaseModel):
    plan_id: str                          # 보통 turn_id
    intent_summary: str                   # 한 줄 요약
    todos: list[PlannedTodo]
    dag: dict[str, list[str]]             # todo_id → depends_on_ids
    dependency_graph: dict[str, list[str]]  # alias of dag (v1.1 호환)
    teams_selected: list[str] = []        # Stage 1 산출
    strategy: Optional[str] = None        # "sequential"|"parallel"|...
    estimated_duration_sec: int = 0
    mermaid_diagram: str = ""
    visualization: dict = {}               # v1.1 시각화용
    plan_notes: Optional[str] = None
```

**Writer**: `planning_stage` (Sprint 9: 3-Step macro→team→todo).

---

## 5. ExecutionResult (Execution 산출)

코드: `backend/app/dream_agent/schemas/execution_result.py`

```python
class TodoResult(BaseModel):
    todo_id: str
    task_type: str
    tool: str
    agent: str
    status: TodoStatus
    data: dict[str, Any] = {}
    error: Optional[str] = None
    is_mock: bool = False
    started_at: float
    ended_at: float
    duration_ms: float

class ExecutionResult(BaseModel):
    plan_id: str
    todos: dict[str, TodoResult]          # 🔴 dict (not list) — todo_id keyed
    phase_timings: list[dict]             # [{"phase": int, "todos": [...], "duration_ms": float}]
    total_duration_ms: float
    overall_status: str                   # "success"|"failed"|"partial"
    halted_at: Optional[str] = None
    halt_reason: Optional[str] = None
```

**주의**: `todos`는 **dict** (id → result) — list 아님. I11-a layer guard에서 이 구조 반영 (dict/list 둘 다 지원).

**Writer**: `execution_stage` (Sprint 12: `executor.execute_phase()` 루프).

---

## 6. ExecutionProgress (Sprint 12 HITL 영속화)

코드: `backend/app/dream_agent/workflow_managers/hitl_manager/manager.py:20` (별도 파일 아닌 `manager.py` 내부 dataclass)

**dataclass** (Pydantic 아님 — 내부용):

```python
@dataclass
class ExecutionProgress:
    session_id: str                       # = turn_id
    plan: dict                            # 현재 유효한 Plan (수정 반영)
    phases: list[list[str]]               # [["t1"], ["t2","t3"], ["t4"]]
    current_phase: int = 0
    completed_todos: dict[str, dict]      # todo_id → result
    status: str = "running"               # running | paused | cancelled
    paused_at_phase: Optional[int] = None
```

**영속화**: `AgentState["execution_progress"]` (Pydantic dump 아닌 `asdict()`) → Checkpoint.
**복원**: `hitl.restore_progress(turn_id, snapshot)` (Sprint 13 I11-a에서 run_turn에 포팅).

**Writer**: `hitl_manager` (PM/HITL Layer, Sprint 12).
**Reader**: `execution_stage` (phase 결과 `report_phase_complete`로 보고).

---

## 7. ResponsePayload (Response 산출)

코드: `backend/app/dream_agent/schemas/response_payload.py`

```python
class Attachment(BaseModel):
    kind: str                             # "pdf" | "image" | "chart" | ...
    caption: Optional[str] = None
    path: Optional[str] = None
    url: Optional[str] = None
    metadata: dict[str, Any] = {}

class ResponseFormat(str, Enum):
    text = "text"
    markdown = "markdown"

class ResponsePayload(BaseModel):
    text: str                             # 사용자 표시용
    format: ResponseFormat = ResponseFormat.text
    summary: Optional[str] = None
    attachments: list[Attachment] = []
    next_actions: list[str] = []
```

**Writer**: `response_stage`.

---

## 8. HITL 모델 (Sprint 12)

코드: `backend/app/dream_agent/models/hitl.py` (+ `models/enums.py`에 HITLRequestType/HITLPriority)

```python
class HITLRequest(BaseModel):
    request_id: str                       # uuid
    session_id: str                       # = turn_id (Sprint 13)
    type: HITLRequestType
    priority: HITLPriority = HITLPriority.NORMAL
    message: str                          # 사용자 표시용
    data: dict[str, Any] = {}             # Plan, progress snapshot 등
    options: list[str] = []               # ["approve", "reject", "modify"]
    timeout_sec: int = 300
    created_at: datetime

class HITLResponse(BaseModel):
    request_id: str
    action: str                           # "approve"|"reject"|"modify"|"continue"|"cancel"
    value: Any = None                     # modify 시 수정값
    user_id: Optional[str] = None
    timestamp: datetime
```

**주의**: Sprint 13 run_turn은 `hitl.signal_resume(turn_id, action_dict)` 를 사용 — `HITLRequest/Response` 모델은 Sprint 12 legacy `_run_agent` 전용.

---

## 9. Agent & Tool 카탈로그 (POC 범위)

`31_execution_agent_function_list_v0.6.md` 참조. 요약:

| Agent | 역할 | 주요 Tool |
|-------|------|----------|
| collection_agent | 외부 데이터 수집 | naver_collector, google_collector, instagram_collector, youtube_collector |
| preprocessing_agent | 텍스트 정제 | format_normalizer, text_preprocessor |
| analysis_agent | 분석 | sentiment_analyzer, keyword_extractor, insight_extractor |
| report_agent | 분석 종합 + 스토리 | report_writer, summary_generator |
| pdf_agent | PDF 렌더링 | pdf_renderer |
| image_creation_agent | 이미지 생성 (mock in POC) | image_generator, storyboard_creator |
| video_creation_agent | 영상 생성 (mock in POC) | video_generator |

카탈로그 YAML: `backend/app/dream_agent/planning/catalog/team_catalog.yaml`

---

## 10. 코드 참조 매핑 (단일 진실 소스)

| 모델 | 파일 |
|------|------|
| AgentState | `backend/app/dream_agent/states/agent_state.py` |
| StructuredQuery + subsidiary | `backend/app/dream_agent/schemas/structured_query.py` |
| Plan + PlannedTodo | `backend/app/dream_agent/planning/planner.py` |
| ExecutionResult + TodoResult | `backend/app/dream_agent/schemas/execution_result.py` |
| ResponsePayload + Attachment | `backend/app/dream_agent/schemas/response_payload.py` |
| ExecutionProgress | `backend/app/dream_agent/workflow_managers/hitl_manager/manager.py:20` (dataclass) |
| HITLRequest/Response | `backend/app/dream_agent/models/hitl.py` |
| HITLRequestType/HITLPriority | `backend/app/dream_agent/models/enums.py` |
| TaskType / TodoStatus / Enums | 각 모듈 내부 |
| Team 카탈로그 | `backend/app/dream_agent/planning/catalog/team_catalog.yaml` |

---

## 11. 변경점 (v1.0, POC 격상 시 반영된 Sprint 10~13 변화)

### Sprint 10~11 (Checkpointer)
- AsyncPostgresSaver 연결 — 모델 변경 없음. thread_id 체계만 영향.

### Sprint 12 (HITL PM)
- `ExecutionProgress` dataclass 신규
- `AgentState.execution_progress` 필드 추가
- HITLRequestType에 `APPROVAL` (execution_pause용) 추가

### Sprint 13 (Session/Thread 재설계)
- AgentState에 `user_id`/`conversation_id`/`turn_id`/`conversation_history`/`history_limit` 추가
- `session_id` deprecated alias 공식화

### Sprint 13 I11-a (이벤트 보강)
- WS event schema 통일 — `21_WEBSOCKET_PROTOCOL_v1.2.md` §6 참조
- Error 이벤트에 `severity`/`layer` 필드 추가
- Layer guard 5종 error code 카탈로그 추가 (`layer_guard.py`)

---

## 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-04-21 | **POC 격상** — `DATA_MODELS_poc.md` 기반으로 Sprint 10~13 반영. (1) Session 식별 필드 (Sprint 13) 추가 (2) ExecutionProgress dataclass 신규 (3) ExecutionResult.todos dict 구조 주의 표기 (4) HITLRequest.session_id = turn_id alias 명시 (5) 코드 참조 매핑 표 추가 — 진실 소스는 코드 |
