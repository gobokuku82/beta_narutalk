# Layer 간 계약 (Contracts)

> **상태**: Phase 0.5 완료 반영
> **최종 수정**: 2026-02-05
> **중요도**: 높음 - 이 문서가 타입 정의의 기준
> **Contract Version**: 2.0

---

## 개요

Dream Agent의 4-Layer 간 데이터 교환 규약을 정의합니다.
각 노드는 `Command(update={...}, goto="next_node")` 패턴으로 상태를 업데이트하고 다음 노드를 지정합니다.

```
사용자 입력
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Cognitive                                          │
│  - 입력: user_input (str)                                    │
│  - 출력: intent, current_context (Contract 1)                │
│  - goto: "planning"                                          │
└─────────────────────────────────────────────────────────────┘
    │ Contract 1
    ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Planning                                           │
│  - 입력: intent                                              │
│  - 출력: plan, todos, plan_obj, resource_plan (Contract 2)   │
│  - goto: "execution" | "response"                            │
└─────────────────────────────────────────────────────────────┘
    │ Contract 2
    ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Execution                                          │
│  - 입력: todos                                               │
│  - 출력: updated todos, ml_result/biz_result (Contract 3)    │
│  - goto: "execution" | "response"                            │
└─────────────────────────────────────────────────────────────┘
    │ Contract 3
    ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: Response                                           │
│  - 입력: ml_result, biz_result, user_input                   │
│  - 출력: response (str) (Contract 4)                         │
│  - goto: END                                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Contract 1: Cognitive → Planning

**파일**: `cognitive/cognitive_node.py`
**함수**: `async def cognitive_node(state) -> Command`
**라우팅**: 항상 `goto="planning"`

### 출력 필드

| 필드 | 타입 | 필수 | AgentState 채널 | 설명 |
|------|------|------|-----------------|------|
| `intent` | `dict` | O | `intent` | 의도 분석 결과 |
| `current_context` | `str` | O | `current_context` | 대화 맥락 요약 |
| `dialogue_context` | `dict` | X | - | DialogueManager 상태 (멀티턴) |
| `hierarchical_intent` | `dict` | X | - | HierarchicalIntent dict (Phase 1) |
| `extracted_entities` | `dict` | X | - | 추출된 엔티티 |

### intent 구조

```python
{
    "intent_type": "analysis",           # str: 의도 유형
    "confidence": 0.94,                  # float: 0.0~1.0
    "requires_ml": True,                 # bool: ML 실행 필요
    "requires_biz": True,               # bool: Biz 실행 필요
    "requires_data_collection": False,   # bool: 데이터 수집 필요
    "requires_preprocessing": False,     # bool: 전처리 필요
    "summary": "K-Beauty 트렌드 분석",   # str: 의도 요약
    "extracted_entities": {},            # dict: 추출 엔티티
    "hierarchical": {                    # HierarchicalIntent 직렬화
        "domain": "analytics",
        "category": "trend_analysis",
        "subcategory": "kbeauty_global_trend",
        "domain_confidence": 0.94,
        "category_confidence": 0.92,
        "overall_confidence": 0.94,
        "method": "llm_based"
    }
}
```

### HierarchicalIntent 모델 (SSOT: `models/intent.py`)

```python
class HierarchicalIntent(BaseModel):
    domain: IntentDomain              # 6개: data_science, marketing, sales, operations, analytics, general
    category: IntentCategory          # 19개: data_collection, trend_analysis, ...
    subcategory: Optional[IntentSubcategory]  # 57개
    domain_confidence: float          # 0.0~1.0
    category_confidence: float        # 0.0~1.0
    subcategory_confidence: float     # 0.0~1.0
    overall_confidence: float         # 0.0~1.0
    method: str                       # "llm_based" | "rule_based" | "unknown"
    requires_ml: bool
    requires_biz: bool
    requires_data_collection: bool
    requires_preprocessing: bool
```

### 예외 처리

| 상황 | 처리 |
|------|------|
| LLM 호출 실패 | fallback intent (domain=GENERAL, confidence=0.5) |
| Phase 1 미사용 | Legacy 모드 fallback (rule-based 분류) |

---

## Contract 2: Planning → Execution

**파일**: `planning/planning_node.py`
**함수**: `async def planning_node(state) -> Command`
**라우팅**: ready todos 있으면 `"execution"`, 없으면 `"response"`

### 출력 필드

| 필드 | 타입 | 필수 | AgentState 채널 | 설명 |
|------|------|------|-----------------|------|
| `plan` | `dict` | O | `plan` | Plan 설명 텍스트 |
| `todos` | `List[TodoItem]` | O | `todos` (reducer) | 생성된 Todo 리스트 |
| `target_context` | `str` | O | `target_context` | plan_description 복사 |
| `plan_obj` | `Plan` | O | `plan_obj` | 완전한 Plan 객체 |
| `plan_id` | `str` | O | `plan_id` | UUID |
| `resource_plan` | `ResourcePlan` | O | `resource_plan` | 리소스 할당 |
| `execution_graph` | `ExecutionGraph` | O | `execution_graph` | 실행 그래프 |
| `cost_estimate` | `dict` | O | `cost_estimate` | 비용 추정 |
| `langgraph_commands` | `list` | O | `langgraph_commands` | 실행 명령어 |
| `mermaid_diagram` | `str` | O | `mermaid_diagram` | Mermaid 다이어그램 |

### plan 구조

```python
{
    "plan_description": "K-Beauty 트렌드 분석을 위해...",
    "total_steps": 4,
    "estimated_complexity": "moderate",
    "workflow_type": "ml_pipeline"
}
```

### TodoItem 모델 (SSOT: `models/todo.py`)

```python
class TodoItem(BaseModel):
    id: str                    # UUID
    task: str                  # 작업 설명
    task_type: str             # "ml" | "biz" | "data" | ...
    status: TodoStatus         # pending, in_progress, completed, failed, blocked, skipped
    layer: str                 # "ml_execution" | "biz_execution"
    priority: int              # 0~10 (10이 최고)
    metadata: TodoMetadata     # execution_config, data_config, dependency_config, progress, approval
```

### 라우팅 로직

```python
def _determine_next_node_after_planning(todos, intent):
    # 1. ready todos가 있으면 → "execution"
    # 2. intent.requires_ml 또는 intent.requires_biz → "execution"
    # 3. 그 외 (단순 질문) → "response"
```

### 예외 처리

| 상황 | 처리 |
|------|------|
| LLM이 todos 생성 실패 | TodoValidator가 fallback todos 생성 |
| intent가 ML 필요하나 todos 없음 | 자동 fallback (키워드추출, 감성분석, 인사이트, 보고서) |

---

## Contract 3: Execution → Response

**파일**: `execution/execution_node.py`
**함수**: `async def execution_node(state) -> Command`
**라우팅**: 남은 ready todos 있으면 `"execution"` (루프), 없으면 `"response"`

### 출력 필드

| 필드 | 타입 | 필수 | AgentState 채널 | 설명 |
|------|------|------|-----------------|------|
| `todos` | `List[TodoItem]` | O | `todos` (reducer) | 상태 업데이트된 todos |
| `execution_result` | `dict` | O | ⚠️ **미등록** | 실행 결과 (현재 drop됨) |
| `ml_result` | `dict` | 조건 | `ml_result` (reducer) | ML 실행 결과 |
| `biz_result` | `dict` | 조건 | `biz_result` (reducer) | Biz 실행 결과 |

### ⚠️ 알려진 이슈

`execution_result` 필드가 `AgentState`에 정의되어 있지 않아 LangGraph가 이 업데이트를 무시합니다. 향후 `AgentState`에 `execution_result: dict` 필드 추가가 필요합니다.

### execution_result 구조 (의도된 형식)

```python
{
    "status": "completed",       # "completed" | "partial" | "no_todos" | "no_ready_todos"
    "results": {                 # todo_id → result_data 매핑
        "abc-123": {...}
    },
    "errors": [],                # 에러 리스트
    "statistics": {...}          # supervisor 통계
}
```

### 실행 모드

Execution 노드는 **한 번에 하나의 Todo만** 실행합니다 (WebSocket 실시간 업데이트를 위해).

| 노드 | 담당 도구 |
|------|-----------|
| `execution_node` | 범용 (모든 도구) |
| `data_execution_node` | collector, preprocessor, google_trends |
| `insight_execution_node` | sentiment, keyword, hashtag, problem, competitor, insight |
| `content_execution_node` | report, video, ad_creative |
| `ops_execution_node` | sales, inventory, dashboard |

### 예외 처리

| 상황 | 처리 |
|------|------|
| Todo 실행 실패 | todo.status = "failed", 에러 기록 |
| 전체 실패 | execution_result.status = "partial" |
| ready todos 없음 | 즉시 "response"로 라우팅 |

---

## Contract 4: Response → 사용자

**파일**: `response/response_node.py`
**함수**: `async def response_node(state) -> Command`
**라우팅**: 항상 `goto=END`

### 출력 필드

| 필드 | 타입 | 필수 | AgentState 채널 | 설명 |
|------|------|------|-----------------|------|
| `response` | `str` | O | `response` | 최종 응답 텍스트 |
| `saved_report_path` | `str` | X | - | 트렌드 리포트 저장 경로 |

### 응답 생성 규칙

- ml_result/biz_result가 10KB 초과 시 자동 요약
- 최대 토큰: 2500
- 언어: state.language에 따라 한국어/영어/일본어

### 예외 처리

| 상황 | 처리 |
|------|------|
| ML/Biz 결과 없음 | 사용자 입력에 대한 직접 응답 생성 |
| LLM 호출 실패 | 간단한 오류 메시지 반환 |

---

## AgentState 정의

**파일**: `states/base.py`

```python
class AgentState(TypedDict, total=False):
    # 사용자 입력
    user_input: str
    language: str

    # 컨텍스트
    current_context: str
    target_context: str

    # Todo 관리 (ID 기반 병합)
    todos: Annotated[list[TodoItem], todo_reducer]

    # 레이어별 결과
    intent: dict
    plan: dict
    ml_result: Annotated[dict, ml_result_reducer]
    biz_result: Annotated[dict, biz_result_reducer]
    response: str

    # 워크플로우 제어
    next_layer: Optional[str]
    requires_hitl: bool
    error: Optional[str]

    # Phase 2: Planning 고도화
    session_id: Optional[str]
    plan_obj: Optional[Plan]
    plan_id: Optional[str]
    resource_plan: Optional[ResourcePlan]
    execution_graph: Optional[ExecutionGraph]
    cost_estimate: Optional[dict]
    langgraph_commands: Optional[list]
    mermaid_diagram: Optional[str]

    # Phase 3: ML Executor
    intermediate_results: Optional[dict]

    # Phase 2: HITL 강화
    hitl_mode: Optional[str]
    hitl_requested_field: Optional[str]
    hitl_message: Optional[str]
    hitl_timestamp: Optional[str]
    hitl_pause_reason: Optional[str]
    hitl_pending_input: Optional[dict]
```

### Reducer 동작

| 채널 | Reducer | 동작 |
|------|---------|------|
| `todos` | `todo_reducer` | ID 기반 병합 (같은 ID면 덮어씀) |
| `ml_result` | `ml_result_reducer` | dict 머지 (기존 결과 보존) |
| `biz_result` | `biz_result_reducer` | dict 머지 (기존 결과 보존) |

---

## 스키마 정의 (참고용)

`schemas/` 폴더의 Pydantic 스키마는 **문서 겸 검증 목적**으로 존재합니다.
실제 노드 함수는 `Dict[str, Any]` 기반으로 동작합니다.

| 스키마 | 위치 | 역할 |
|--------|------|------|
| `CognitiveInput/Output` | `schemas/cognitive.py` | Cognitive Layer I/O 정의 |
| `PlanningInput/Output` | `schemas/planning.py` | Planning Layer I/O 정의 |
| `ExecutionInput/Output` | `schemas/execution.py` | Execution Layer I/O 정의 |
| `ResponseInput/Output` | `schemas/response.py` | Response Layer I/O 정의 |

---

## 변경 시 규칙

1. **AgentState 필드 추가**: `states/base.py`에 추가 + 이 문서 업데이트
2. **새 모델 추가**: `models/` 폴더에 정의 + `models/__init__.py` export
3. **필드 제거**: Deprecated 마킹 → 다음 Phase에서 제거
4. **타입 변경**: 하위 호환 유지 (Optional로 추가)

---

## 참고 문서

- `models/` — Pydantic 모델 정의 (SSOT)
- `schemas/` — Layer I/O 스키마
- `states/base.py` — AgentState TypedDict
- `states/reducers.py` — Reducer 함수

---

*이 문서는 코드 기반으로 2026-02-05에 업데이트되었습니다.*
