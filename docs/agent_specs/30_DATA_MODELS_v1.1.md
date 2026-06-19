# Data Models Specification (Sprint 14+ 검증 정정판)

| 항목 | 내용 |
|------|------|
| 담당자 | 도윤 |
| 분류 | 개발 - 데이터 모델 |
| 진행상태 | **Active** (코드 직독 기반 정정판) |
| 버전 | **v1.1** |
| 최종 수정일 | 2026-05-15 |
| 관련 명세 | `20_INTERFACE_CONTRACT_v1.1.md`, `21_WEBSOCKET_PROTOCOL_v1.5.md`, `22_error_codes_v1.1.md` |

> **진실 소스 (Source of Truth)**: **코드** (`backend/app/dream_agent/schemas/*.py`, `planner.py`, `agent_state.py`, `models/*.py`). 본 문서는 코드를 읽어 정리한 참조 — 코드와 다르면 코드가 우선, 문서를 고친다.

---

## 0. 개요

DreamAgent V2 의 **Pydantic / dataclass / TypedDict** 모델 카탈로그.

---

## 1. 모델 분류

| 카테고리 | 모델 | 위치 |
|---------|------|------|
| **레이어 산출물** | `StructuredQuery`, `Plan`+`PlannedTodo`, `ExecutionResult`+`TodoResult`, `ResponsePayload` | `schemas/`, `planning/planner.py` |
| **전역 상태** | `AgentState` (TypedDict) | `states/agent_state.py` |
| **실행 컨텍스트** | `ExecutionContext` | `models/execution.py` |
| **HITL 진행 상태** | `ExecutionProgress` (dataclass) | `workflow_managers/hitl_manager/manager.py` |
| ~~HITL 요청/응답~~ | ~~`HITLRequest`, `HITLResponse`~~ — **폐기(2026-06-11**, Sprint 12 event 트랙 잔재**)** | — |
| **Tool 메타** | `ToolSpec`, `ToolParameter` | `models/tool.py` |
| **Enums** | `ToolCategory`, `ToolParameterType` + `schemas/`내부 enum (`TodoStatus`, `GoalType` 등). ~~`HITLRequestType`~~ 폐기(2026-06-11) | `models/enums.py`, 각 schemas 내부 |
| ~~도메인 모델 (Tool I/O)~~ | ~~`models/domain.py`~~ — **폐기(2026-06-12)**, 현행은 `app/data_layer/schemas/outputs` 의 `*Output` | — |

> ✅ **이름 충돌 해소됨 (2026-05-15 models/ cleanup A1~A7)**:
> - `Plan`: **`planning/planner.py::Plan` 만 존재** (1곳). 옛 `models/plan.py::Plan` 삭제됨.
> - `ExecutionResult`: **`schemas/execution_result.py::ExecutionResult` 만 존재** (1곳). 옛 `models/execution.py::ExecutionResult` (단일 Tool wrapper) 삭제됨.
> - `TodoStatus`: **`schemas/execution_result.py::TodoStatus` (5값) 만 존재**. 옛 `models/enums.py::TodoStatus` (8값) 삭제됨.
>
> `from app.dream_agent.models import Plan` / `Intent` / `TodoItem` / `ExecutionResult` 는 이제 **ImportError**.

---

## 2. 레이어 산출물 (Pipeline 의 핵심)

### 2.1 StructuredQuery — Cognitive 산출

코드: `backend/app/dream_agent/schemas/structured_query.py`

```python
# ── Enums ──
# ⚠️ TaskType / Source 는 이제 OPEN-VOCAB (자유 문자열) — 닫힌 enum 아님.
#    아래는 *예시* 값 (도메인 무관 일반 작업). 실제 값은 카탈로그/도메인에 따라 자유.
class TaskType(str, Enum):  # 예시 — Planning 의 Tool 매핑 키 (open-vocab)
    DATA_COLLECTION       = "data_collection"
    METRIC_CALCULATION    = "metric_calculation"
    ANALYSIS              = "analysis"
    COMPARISON            = "comparison"
    INSIGHT_GENERATION    = "insight_generation"
    SUMMARY_GENERATION    = "summary_generation"
    REPORT_GENERATION     = "report_generation"
    RECOMMENDATION        = "recommendation"
    FACTUAL_LOOKUP        = "factual_lookup"
    # ... (자유 확장 — 닫힌 enum 아님)

class GoalType(str, Enum):
    ANSWER, METRIC, INSIGHT, REPORT, CREATIVE, MIXED    # = "answer"/"metric"/...

class OutputFormat(str, Enum):
    TEXT, PDF, IMAGE, CHART, VIDEO, MIXED               # ⚠️ "markdown" 없음

class Depth(str, Enum):
    BRIEF, STANDARD, DETAILED

class Source(str, Enum):  # 예시 — open-vocab (자유 문자열), 도메인별 source 식별자
    SOURCE_A, SOURCE_B, MULTI, UNKNOWN

# ── Sub-structures ──
class Period(BaseModel):
    raw: str                         # 원문 ("지난 3개월")
    start, end, window: str | None   # ISO date / "3months" 정규화

class Targets(BaseModel):
    entity:       str | None
    sub_entity:   str | None
    related:      list[str]
    source:       Source = Source.UNKNOWN
    period:       Period | None
    keywords:     list[str]
    extra_filters: dict

class Goal(BaseModel):
    type:          GoalType
    output_format: OutputFormat
    depth:         Depth = Depth.STANDARD
    audience:      str | None

class Task(BaseModel):
    id:              TaskType
    priority:        int = 1
    params_override: dict             # ⚠️ "rationale" 아님

class Ambiguity(BaseModel):
    is_ambiguous:         bool = False
    severity:             str = "none"   # none|low|medium|high
    reasons:              list[str]
    clarification_question: str | None

class QueryMeta(BaseModel):
    confidence:      float           # 0.0~1.0
    ambiguity:       Ambiguity
    missing:         list[str]       # 비어있는 필수 필드 ID
    raw_input:       str
    language:        str = "ko"
    original_domain: str | None      # legacy 호환

# ── Root ──
class StructuredQuery(BaseModel):
    targets: Targets
    goal:    Goal
    tasks:   list[Task]
    meta:    QueryMeta
```

> ⚠️ `entity` 는 **`targets.entity` 중첩** — `structured_query["entity"]` 최상위 접근 아님. `layer_guard.py::inspect_layer_output` 의 `sq.get("entity")` 는 항상 None 반환 (별도 트랙).

**Writer**: `cognitive_stage` (LLM 기반, `llm_manager/prompts/cognitive.yaml`).
**JSON dump**: `sq.model_dump(mode="json")` → `AgentState["structured_query"]`.

### 2.2 Plan / PlannedTodo — Planning 산출

코드: `backend/app/dream_agent/planning/planner.py` (⚠️ `models/plan.py` 아님 — 그쪽은 deprecated)

```python
class PlannedTodo(BaseModel):
    id:          str                # "todo_001"
    task_type:   str                # TaskType.value
    team:        str | None         # "<team>" 등 — team_catalog 키
    agent:       str | None         # "<agent>" 등 — team_catalog 키
    tool:        str | None         # "<tool>" 등 — team_catalog 키
    tool_params: dict               # Tool 에 넘길 인자
    depends_on:  list[str]          # DAG 의존성
    priority:    int = 1
    rationale:   str = ""

class Plan(BaseModel):
    teams_selected: list[str]       # Stage 1 LLM 산출 — 선택된 팀
    todos:          list[PlannedTodo]
    dag:            dict[str, list[str]]   # todo_id → depends_on_ids (위상정렬용)
    plan_notes:     str = ""
```

**Writer**: `Planner.plan()` — 3 Stage LLM (team_selector → agent_selector → todo_builder).
**유효성 검증**: `validate_dag(plan)` — 미정의 의존 / 순환 검출.
**JSON dump**: `plan.model_dump(mode="json")` → `AgentState["plan"]`.

> 이전 v1.0 의 `plan_id`/`intent_summary`/`mermaid_diagram`/`visualization`/`strategy`/`estimated_duration_sec` 필드는 **실재하지 않는다** — 모두 정정.

### 2.3 ExecutionResult / TodoResult — Execution 산출

코드: `backend/app/dream_agent/schemas/execution_result.py` (⚠️ `models/execution.py::ExecutionResult` 아님)

```python
class TodoStatus(str, Enum):           # ⚠️ 5개 (≠ models/enums.py::TodoStatus 8개)
    PENDING     = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED   = "completed"           # ⚠️ "success" 아님
    FAILED      = "failed"
    SKIPPED     = "skipped"

class TodoResult(BaseModel):
    todo_id:    str
    task_type:  str
    tool:       str | None
    agent:      str | None
    status:     TodoStatus
    data:       dict                   # ★ Tool 의 실제 출력 (dict)
    error:      str | None
    is_mock:    bool = False           # stub Tool → mock_result() 여부
    started_at: float                  # unix ts
    ended_at:   float
    duration_ms: float

class ExecutionResult(BaseModel):
    plan_id:           str = ""
    todos:             dict[str, TodoResult]   # 🔴 dict (todo_id → result) — list 아님
    phase_timings:     list[dict]              # [{phase, todos[], duration_ms}]
    total_duration_ms: float = 0.0
    overall_status:    TodoStatus = TodoStatus.COMPLETED   # 보통 COMPLETED / FAILED
    halted_at:         str | None              # 실패한 todo_id
    halt_reason:       str | None
```

**Writer**: `execution_stage._build_execution_result()` — `hitl_manager.completed_todos` 에서 조합.

### 2.4 ResponsePayload — Response 산출

코드: `backend/app/dream_agent/schemas/response_payload.py`

```python
class ResponseFormat(str, Enum):
    TEXT, PDF, IMAGE, CHART, VIDEO, MIXED, ERROR   # ⚠️ "markdown" 없음

class Attachment(BaseModel):
    kind:    str                       # "pdf"|"image"|"chart"|"video"|"link"
    path:    str | None
    url:     str | None
    caption: str | None
    meta:    dict

class ResponsePayload(BaseModel):
    format:       ResponseFormat
    text:         str                  # 메인 텍스트 응답 (항상 존재)
    summary:      str | None           # 1~2 문장 핵심 요약
    next_actions: list[str]            # 추천 후속 작업
    attachments:  list[Attachment]
    meta:         dict                 # 처리 시간, 완료 Todo 수 등
    error:        str | None           # format == ERROR 일 때
```

**Writer**: `Responder.respond(sq, exec_result)` — LLM 기반 자연어 생성 + 첨부 구성.

---

## 3. 전역 상태 — AgentState

코드: `backend/app/dream_agent/states/agent_state.py` — **TypedDict** (Pydantic 아님)

```python
class AgentState(TypedDict, total=False):     # 모든 필드 Optional
    # ── 식별 (Sprint 13 I6) ──
    user_id:              str
    conversation_id:      str
    turn_id:              str
    session_id:           str        # = turn_id alias (deprecated)
    # ── 대화 컨텍스트 ──
    conversation_history: list[dict[str, Any]]
    history_limit:        int
    # ── 입력 ──
    user_input:           str
    language:             str
    # ── 레이어 산출 (각 레이어가 자기 칸을 채움) ──
    structured_query:     dict        # StructuredQuery.model_dump
    plan:                 dict        # Plan.model_dump
    execution_result:     dict        # ExecutionResult.model_dump
    execution_progress:   dict        # ExecutionProgress (HITL pause 영속화)
    response:             dict        # ResponsePayload.model_dump
    # ── 횡단 ──
    error:                str | None
    trace:                list[dict[str, Any]]
    hitl_pending:         dict | None
```

**초기화 헬퍼**: `init_agent_state(user_input, conversation_id, turn_id, user_id=None, language="ko", conversation_history=None, history_limit=None)` — Settings fallback 일관화.

**Reader/Writer 매트릭스** (`docs/agent_specs/20_INTERFACE_CONTRACT_v1.1.md §4` 참조):
- `cognitive_stage`: read `user_input/language/conversation_history/history_limit` → write `structured_query`
- `planning_stage`: read `structured_query` → write `plan`
- `execution_stage`: read `plan` → write `execution_result`, `execution_progress`
- `response_stage`: read `structured_query, execution_result` → write `response`

**LangGraph 그래프 hand-off**: 각 stage 가 `Command(update={...}, goto="다음노드")` 반환 → `update` dict 가 AgentState 에 머지됨.

---

## 4. ExecutionContext — Tool 에 전달되는 컨텍스트

코드: `backend/app/dream_agent/models/execution.py`

```python
class ExecutionContext(BaseModel):
    # === Identity ===
    session_id:        str
    plan_id:           str
    client_id:         str | None
    user_id:           str | None
    # === Locale ===
    language:          str = "ko"
    # === Context ===
    previous_results:  dict             # ★ Todo 간 데이터 체인 — 이전 Phase 출력
    session_memory:    dict
    # === 공유 데이터 ===
    collected_data:    dict | None
    preprocessed_data: dict | None
    # === Metadata ===
    metadata:          dict
```

**전달 경로**: `execution_stage` → `executor._run_single_todo(todo, context, previous_results)` → `tool.execute(params, context)`.

**`previous_results` 머지 패턴** (`executor._inject_prev_outputs`):
- 이전 `TodoResult.data` 의 키(`raw_records`, `cleaned_text` 등)가 다음 Todo 의 `tool_params` 에 자동 머지됨 (key 가 `_` 로 시작하지 않으면). 같은 키 충돌 시 기존 `tool_params` 우선 (`setdefault`).

**`client_id` 의 Sprint 16 의미** (ADR-022 박제):
- frontend TopBar 드롭다운 → Zustand store → API `?client=` param → ExecutionContext.client_id → `DataSource.get(client_id, source_id)` 까지 *일관 흐름*.
- tool 코드는 client 무관. client 추가 = `data/{new_client}/raw/` 디렉토리 + dropdown entry 만.
- Default fallback = `"default"` (POC).

---

## 5. HITL 모델

### 5.1 ExecutionProgress (dataclass)

코드: `backend/app/dream_agent/workflow_managers/hitl_manager/manager.py:20`

```python
@dataclass
class ExecutionProgress:
    session_id:        str                            # = turn_id
    plan:              dict                           # 현재 유효 Plan (편집 시 mutate)
    phases:            list[list[str]]                # [["t1"], ["t2","t3"]]
    current_phase:     int = 0
    completed_todos:   dict[str, dict]                # todo_id → TodoResult dict
    status:            str = "running"                # running|paused|completed|cancelled
    paused_at_phase:   int | None
```

**소유자**: `HITLManager` (싱글톤). `_progress: dict[turn_id, ExecutionProgress]`.

**영속화**: `get_progress_snapshot()` → JSON 직렬화 가능 dict → interrupt payload 로 LangGraph Checkpoint 에 저장 → 서버 재시작 시 `restore_progress()` 로 복원.

### 5.2 ~~HITLRequest / HITLResponse~~ — **폐기 (2026-06-11)**

~~코드: `models/hitl.py`~~ → **삭제됨** (HITLRequest/HITLResponse + HITLRequestType enum, Sprint 12 event 트랙 전용 모델).

폐기 사유: legacy `_run_agent` 폐기(05-31) 후 생성 경로 0 — 잔존 호출(submit_response)이 빈 장부 조회로 `hitl_ack.accepted` 항상-false 거짓 신호를 만들던 버그의 원인이라 짝 단위 일괄 철거. Sprint 13 신경로(`run_turn`)는 `hitl.signal_resume(turn_id, action_dict)` / `wait_for_resume(turn_id)` 로 dict 직접 전달. 외부 계약(WS `hitl_request` 이벤트)은 `21_WEBSOCKET_PROTOCOL_v1.5.md §2.2` 의 평탄 envelope 사용. 복원은 git 히스토리(b75df88).

---

## 6. Tool 모델

### 6.1 ToolSpec / ToolParameter

코드: `backend/app/dream_agent/models/tool.py`

`BaseTool` 의 인스턴스화 시 주입되는 메타. `ToolRegistry` 가 관리.

```python
class ToolParameterType(str, Enum):
    STRING, INTEGER, FLOAT, BOOLEAN, ARRAY, OBJECT

class ToolParameter(BaseModel):
    name:        str
    type:        ToolParameterType
    required:    bool
    default:     Any | None
    description: str

class ToolSpec(BaseModel):
    name:        str
    category:    ToolCategory      # collection|normalization|cleaning|preprocessing|metrics|comparison|analysis|report
    description: str
    parameters:  list[ToolParameter]
    # ... + 부가 메타
```

### 6.2 BaseTool 계약

코드: `backend/app/dream_agent/tools/base_tool.py`

```python
class BaseTool(ABC):
    def __init__(self, spec: ToolSpec): ...

    @abstractmethod
    async def execute(
        self,
        params: dict[str, Any],
        context: ExecutionContext,
    ) -> dict[str, Any]:
        """ Tool 의 단일 계약. 반환 dict = TodoResult.data 가 됨. """

    def validate_params(self, params) -> (bool, list[str]): ...
    def get_default_params(self) -> dict: ...
    def merge_params(self, params) -> dict: ...
```

---

## 7. ~~도메인 모델 (Tool I/O 공유 타입)~~ — **폐기 (2026-06-12 정리 전환 Sprint)**

~~코드: `models/domain.py` (구 backend/app/dream_agent/ 하위)~~ → **삭제됨** (구 POC 도메인 I/O 공유 타입 다수).

폐기 사유: 이 모델들의 계약 대상이던 POC tool 체인이 폐기된 뒤 **소비처 0** (전수 grep 재검증). 현행 tool I/O 는 `app/data_layer/schemas/outputs` 의 `*Output` 모델 사용. 복원은 git 히스토리.

→ Tool 의 `execute()` 반환 dict 는 보통 이 모델들의 list/dict 를 포함. 다음 Todo 가 `previous_results` 로 받아 사용.

### 7.5 DataSource ABC (Sprint 16, ADR-022)

코드: `backend/app/data_layer/data_sources/base.py`

```python
class DataSource(ABC):
    """Repository — tool 에 data 의 '어디서' 를 추상화."""
    @abstractmethod
    def get(self, client: str, source_id: str) -> pd.DataFrame | dict | list: ...
    @abstractmethod
    def list_sources(self, client: str) -> list[str]: ...
    @abstractmethod
    def has(self, client: str, source_id: str) -> bool: ...

class DataSourceError(Exception): ...
class DataSourceNotFound(DataSourceError): ...
```

**Adapter** (POC): `FileDataSource` — `data/{client}/raw/{filename}` (csv/json/jsonl/sql).
**Adapter** (MVP 예정): `PostgresDataSource` — 같은 ABC, default 교체. tool 변경 0.

**source_id 카탈로그** (`DEFAULT_MAPPING` — 도메인별 N종):

| source_id | filename |
|---|---|
| `source_a` | source_a.csv |
| `source_b` | source_b.csv |
| `records` | records.csv |
| `entities` | entities.csv |
| ... | (도메인별 N source — `file.py:DEFAULT_MAPPING`) |

→ tool 은 의미 단위 `source_id` 로 요청 (file 번호 X). client 변경 = `client` arg 만 변경.

### 7.6 WorkspaceBackend ABC (Sprint 16, ADR-022)

코드: `backend/app/data_layer/workspace/base.py`

```python
class WorkspaceBackend(ABC):
    """Tool 결과 산출물 영속화 — raw/cleaned/computed layer 별."""
    @abstractmethod
    def save(self, layer: str, key: str, data) -> Path: ...
    @abstractmethod
    def load(self, layer: str, key: str) -> dict | list: ...
    @abstractmethod
    def exists(self, layer: str, key: str) -> bool: ...
    @abstractmethod
    def list_keys(self, layer: str) -> list[str]: ...

# layer 매핑 (POC)
LAYER_DIR = {
    "raw":      "default/raw",
    "cleaned":  "default/cleaned",
    "computed": "default/computed",
}
```

**Adapter** (POC): `FileWorkspace` — `data/{LAYER_DIR[layer]}/{key}.json`.
**키 명명**: `count_total_2026-04.json`, `entity_total_2026-04.json` — client 이름 없음 (cache 자산 보존).

→ tool 의 결과 산출물 영속화. frontend 가 같은 Workspace 에서 cleaned/computed 직접 조회 (agent 우회 — 빠른 응답).

### 7.7 호환 layer (shim)

코드: `backend/app/dream_agent/tools/shared/storage.py`

```python
# 옛 import 호환 — 점진 마이그레이션
from app.data_layer.workspace import (
    get_default_workspace as get_storage,
    WorkspaceBackend as StorageBackend,
)
```

→ Sprint 13~15 tool 들이 import 하던 `get_storage()` 가 그대로 작동. 신규 tool 은 `get_default_workspace()` 사용 권장.

---

## 8. 기타 Enum (참조용) — 정리 후 (2026-05-15)

코드: `backend/app/dream_agent/models/enums.py` (2 enum)

```python
# ❌ HITLRequestType — 2026-06-11 폐기 (Sprint 12 event 트랙: models/hitl.py
#    HITLRequest/HITLResponse + hitl_manager 장부 메서드와 동반 삭제. 거짓 accepted 버그 원인)

class ToolCategory(str, Enum):       # ToolSpec.category 의 타입 (11값 — 코드 참조)
    COLLECTION, NORMALIZATION, CLEANING, PREPROCESSING, METRICS,
    COMPARISON, ANALYSIS, REPORT, RENDERING, QA, DECISION

class ToolParameterType(str, Enum):  # ToolParameter.type 의 타입
    STRING, INTEGER, FLOAT, BOOLEAN, ARRAY, OBJECT
```

> **2026-05-15 정리** (models/ cleanup A5): `IntentDomain`/`IntentCategory`/`Layer`/`ExecutionStrategy`/`PlanStatus`/`TodoStatus`(8값)/`SessionStatus` 7개 enum 삭제 (활성 사용 0건 확인). `Intent`/`Entity` 도 함께 정리.

---

## 9. 코드 참조 매핑 (단일 진실 소스)

| 모델 | 파일 |
|------|------|
| `AgentState` | `backend/app/dream_agent/states/agent_state.py` |
| `StructuredQuery` + sub (Targets/Goal/Task/QueryMeta/Period/Ambiguity) | `backend/app/dream_agent/schemas/structured_query.py` |
| TaskType, GoalType, OutputFormat, Depth, Source enums | 동상 (위 파일 내부) |
| `Plan` + `PlannedTodo` | `backend/app/dream_agent/planning/planner.py` |
| `ExecutionResult` + `TodoResult` + `TodoStatus`(5값) | `backend/app/dream_agent/schemas/execution_result.py` |
| `ResponsePayload` + `Attachment` + `ResponseFormat` | `backend/app/dream_agent/schemas/response_payload.py` |
| `ExecutionProgress` (dataclass) | `backend/app/dream_agent/workflow_managers/hitl_manager/manager.py` |
| ~~`HITLRequest` / `HITLResponse` / `HITLRequestType`~~ | 폐기(2026-06-11) — 구 `models/hitl.py` + enums | 
| `ExecutionContext` | `backend/app/dream_agent/models/execution.py` |
| `ToolSpec` / `ToolParameter` | `backend/app/dream_agent/models/tool.py` |
| ~~도메인 모델~~ (폐기 2026-06-12) | ~~`models/domain.py`~~ → `app/data_layer/schemas/outputs` |
| Team/Agent/Tool 카탈로그 | `backend/app/dream_agent/planning/catalog/team_catalog.yaml` |
| **`DataSource` ABC + `FileDataSource`** (Sprint 16, ADR-022) | `backend/app/data_layer/data_sources/base.py` + `file.py` |
| **`WorkspaceBackend` ABC + `FileWorkspace`** (Sprint 16, ADR-022) | `backend/app/data_layer/workspace/base.py` + `file.py` |
| **호환 shim** (`get_storage`/`StorageBackend` alias) | `backend/app/dream_agent/tools/shared/storage.py` |

---

## 10. 데이터 흐름 — 모델 변환 체인

```
[입력]   user_input (str), language (str)
         ↓
[Cognitive] StructuredQuery               ─┐
            .model_dump(mode="json")       │
            → AgentState["structured_query"]│  Pydantic ↔ dict
            ← .model_validate(state[...])  ─┘
         ↓
[Planning] Plan (planner.Plan)             ─┐
           interrupt() → user approval     │
           .model_dump → AgentState["plan"]│
         ↓                                  │
[Execution] hitl.create_progress(plan)     │
            → ExecutionProgress (dataclass)│  dataclass 기반
            phase 루프:                     │  (Pydantic 아님 — Checkpoint 호환)
              executor.execute_phase(...)   │
              → list[TodoResult]            │
              → progress.completed_todos    │
            → ExecutionResult.model_dump   │
            → AgentState["execution_result"]│
         ↓                                  │
[Response] ResponsePayload                  │
           .model_dump → AgentState["response"]
         ↓                                  ─┘
[출력]   complete.data.response (WS)
```

**핵심 패턴**: 각 레이어는 Pydantic 모델 만들기 → `.model_dump(mode="json")` 로 dict 화 → `AgentState` 의 자기 칸에 저장 → 다음 레이어가 `.model_validate(state[...])` 로 복원. **양쪽이 같은 스키마 클래스를 봐야** 변환이 깨지지 않는다.

---

## 변경 이력

> 프레임워크 추출(2026-06-19) 이전(마케팅 도메인 시기)의 상세 변경 이력은 git 히스토리를 참조하세요.
