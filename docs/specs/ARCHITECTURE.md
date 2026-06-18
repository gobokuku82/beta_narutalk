# Dream Agent V2 - System Architecture

**Version**: 2.0 | **Date**: 2026-02-06 | **Status**: Draft

---

## 1. Overview

Dream Agent V2는 4-Layer Hand-off 아키텍처 기반의 기업용 AI 에이전트 시스템입니다. LangGraph 1.0.5의 최신 패턴(Command, Send, interrupt)을 활용하여 설계되었습니다.

### 1.1 Design Principles

| 원칙 | 설명 |
|------|------|
| **Clean State** | AgentState를 핵심 필드만으로 축소 |
| **Strict Contracts** | Layer 간 I/O는 Pydantic v2 스키마로 정의 |
| **3 Primitives** | Command(순차), Send(병렬), interrupt(HITL) 활용 |
| **Immutable Todos** | TodoItem은 불변, 수정 시 새 버전 생성 |
| **Two-Level Orchestration** | Graph 조립 + Execution 스케줄링 분리 |
| **Config-Driven** | Tools, Prompts 모두 YAML 기반 |

### 1.2 System Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Frontend (Next.js)                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │   Chat UI    │  │ Plan Viewer  │  │  Todo List   │  │ HITL Controls  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └───────┬────────┘  │
│         └─────────────────┴─────────────────┴──────────────────┘           │
│                                     │                                       │
│                         WebSocket + REST API                                │
└─────────────────────────────────────┼───────────────────────────────────────┘
                                      │
┌─────────────────────────────────────┼───────────────────────────────────────┐
│                            Backend (FastAPI)                                 │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                       api/ (Interface Layer)                           │ │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────────┐  │ │
│  │  │  routes/  │  │ websocket/│  │  schemas/ │  │    Middleware     │  │ │
│  │  └─────┬─────┘  └─────┬─────┘  └───────────┘  └───────────────────┘  │ │
│  └────────┼──────────────┼──────────────────────────────────────────────┘ │
│           │              │                                                 │
│  ┌────────┴──────────────┴─────────────────────────────────────────────┐  │
│  │               app/dream_agent/ (Application Layer)                   │  │
│  │                                                                      │  │
│  │  ┌────────────────────────────────────────────────────────────────┐ │  │
│  │  │              orchestrator/ (Level 1: LangGraph)                 │ │  │
│  │  │                                                                 │ │  │
│  │  │    ┌───────────┐        ┌───────────┐        ┌───────────┐     │ │  │
│  │  │    │ Cognitive │─Command─│ Planning  │─Command─│ Execution │    │ │  │
│  │  │    │   Node    │        │   Node    │        │   Node    │     │ │  │
│  │  │    └───────────┘        └─────┬─────┘        └─────┬─────┘     │ │  │
│  │  │          │                    │                    │           │ │  │
│  │  │     interrupt()          interrupt()          Send API         │ │  │
│  │  │     (질문/명확화)        (Plan 승인)         (병렬 실행)        │ │  │
│  │  │                                                    │           │ │  │
│  │  │                                                    ▼           │ │  │
│  │  │    ┌───────────┐                          ┌───────────────┐    │ │  │
│  │  │    │ Response  │◄────────Command──────────│ execute_todo  │    │ │  │
│  │  │    │   Node    │                          │   (N개 병렬)  │    │ │  │
│  │  │    └───────────┘                          └───────────────┘    │ │  │
│  │  │          │                                                     │ │  │
│  │  │       goto=END                                                 │ │  │
│  │  └────────────────────────────────────────────────────────────────┘ │  │
│  │                                                                      │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────────┐  │  │
│  │  │ workflow_        │  │ llm_manager/     │  │ tools/            │  │  │
│  │  │ managers/        │  │                  │  │                   │  │  │
│  │  │ • hitl_manager   │  │ • prompts/       │  │ • registry.py     │  │  │
│  │  │ • todo_manager   │  │ • client.py      │  │ • definitions/    │  │  │
│  │  │ • callback_mgr   │  │                  │  │                   │  │  │
│  │  └──────────────────┘  └──────────────────┘  └───────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
                                      │
┌─────────────────────────────────────┼───────────────────────────────────────┐
│                              Data Layer                                      │
│  ┌──────────────────────┐  ┌───────────────────┐  ┌─────────────────────┐  │
│  │     PostgreSQL       │  │       Redis       │  │    File Storage     │  │
│  │  • checkpoints       │  │  • session cache  │  │  • reports/         │  │
│  │  • sessions          │  │  • rate limit     │  │  • exports/         │  │
│  │  • plans/todos       │  │  • exec cache     │  │  • uploads/         │  │
│  │  • learning_logs     │  │                   │  │                     │  │
│  └──────────────────────┘  └───────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 4-Layer Hand-off Architecture

### 2.1 Layer Overview

```
User Input
    │
    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  LAYER 1: COGNITIVE                                                         │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────────────────────────┐ │
│  │    Intent     │  │    Entity     │  │         Ambiguity               │ │
│  │   Classifier  │─►│   Extractor   │─►│         Detector                │ │
│  └───────────────┘  └───────────────┘  └─────────────────────────────────┘ │
│                                                                             │
│  Output: CognitiveOutput { intent, entities, plan_hint, requires_clarify } │
│                                                                             │
│  Interrupt Point: 모호성 발견 시 → 사용자에게 질문                           │
└────────────────────────────────────────────────────────────────────────────┘
                                │
                           Command(goto="planning")
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  LAYER 2: PLANNING                                                          │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────────────────────────┐ │
│  │     Todo      │  │  Dependency   │  │         Resource                │ │
│  │   Generator   │─►│   Calculator  │─►│         Estimator               │ │
│  └───────────────┘  └───────────────┘  └─────────────────────────────────┘ │
│                                                                             │
│  Output: PlanningOutput { plan, todos, dependency_graph, mermaid }         │
│                                                                             │
│  Interrupt Point (interrupt_before): Plan 생성 후 사용자 승인 대기           │
└────────────────────────────────────────────────────────────────────────────┘
                                │
                           Command(goto="execution")
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  LAYER 3: EXECUTION                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Execution Dispatcher                              │   │
│  │            (전략 결정 + Send API 병렬 실행)                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│           │              │              │              │                    │
│           ▼              ▼              ▼              ▼                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐             │
│  │    Data     │ │   Insight   │ │   Content   │ │    Ops    │             │
│  │  Executor   │ │  Executor   │ │  Executor   │ │  Executor │             │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘             │
│                                                                             │
│  Output: execution_results { todo_id → ExecutionResult }                   │
│                                                                             │
│  Send API: 독립적인 Todo들 병렬 실행                                         │
│  Interrupt Point: Pause 요청 또는 에러 발생 시                               │
└────────────────────────────────────────────────────────────────────────────┘
                                │
                           Command(goto="response")
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  LAYER 4: RESPONSE                                                          │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────────────────────────┐ │
│  │    Result     │  │    Format     │  │         Response                │ │
│  │   Aggregator  │─►│   Decider     │─►│         Generator               │ │
│  └───────────────┘  └───────────────┘  └─────────────────────────────────┘ │
│                                                                             │
│  Output: ResponseOutput { format, text, attachments, next_actions }        │
│                                                                             │
│  Formats: text | image | pdf | video | mixed                               │
└────────────────────────────────────────────────────────────────────────────┘
                                │
                           Command(goto=END)
                                │
                                ▼
                          User Output
```

### 2.2 Layer Details

#### Layer 1: Cognitive

**역할**: 사용자 의도를 **구체적으로** 평가하고, 어떤 계획이 필요한지 판단

```python
# layers/cognitive/node.py
async def cognitive_node(state: AgentState) -> Command:
    """
    1. IntentClassifier: 3-depth 의도 분류 (domain → category → subcategory)
    2. EntityExtractor: 엔티티 추출 + 신뢰도
    3. AmbiguityDetector: 모호성 탐지
       - 모호하면 → interrupt()로 사용자에게 질문 (HITL)
       - 명확하면 → planning으로 hand-off
    4. TraceLogger: cognitive 단계 로깅

    Returns:
        Command(update={"cognitive_result": output}, goto="planning")
        또는 interrupt()로 사용자 질문
    """
```

**Components**:

| Component | 역할 |
|-----------|------|
| `IntentClassifier` | 3-depth 계층적 의도 분류 (domain/category/subcategory) |
| `EntityExtractor` | 엔티티 추출 (brand, product, date_range, platform 등) |
| `AmbiguityDetector` | 모호성 탐지 + 명확화 질문 생성 |

**Intent Classification Hierarchy**:

| Domain | Category Examples | Subcategory Examples |
|--------|-------------------|---------------------|
| ANALYSIS | sentiment, keyword, trend | review_analysis, brand_perception |
| CONTENT | report, video, ad | trend_report, promotional_video |
| OPERATION | sales, inventory, dashboard | sales_material, kpi_dashboard |
| INQUIRY | general | faq, how_to |

#### Layer 2: Planning

**역할**: "무엇을 할지" 결정 - Todo 목록 생성 (실행 전략은 Execution에서)

```python
# layers/planning/node.py
async def planning_node(state: AgentState) -> Command:
    """
    1. ToolRegistry 조회: 사용 가능한 도구 목록
    2. LLM에게 도구 목록 + 의도 → Plan 생성 요청
    3. Plan 검증: 의존성 순환 검사, 위상 정렬
    4. interrupt() → 사용자에게 Plan 승인 요청 (HITL)
    5. 승인 후 → execution으로 hand-off

    Returns:
        Command(update={"plan": plan, "todos": todos}, goto="execution")
    """
```

**Components**:

| Component | 역할 |
|-----------|------|
| `TodoGenerator` | Intent + Tool Catalog → Todo 목록 생성 |
| `DependencyCalculator` | 순환 의존성 탐지, 위상 정렬 |
| `ResourceEstimator` | 비용/시간 추정 |
| `MermaidRenderer` | 실행 그래프 시각화 |

#### Layer 3: Execution

**역할**: "어떻게 할지" 결정 + Todo 실행 오케스트레이션

```python
# layers/execution/node.py
async def execution_dispatcher(state: AgentState) -> list[Send] | Command:
    """
    1. ExecutionStrategy 결정 (SINGLE, SEQUENTIAL, PARALLEL, SWARM, CYCLIC)
    2. 독립적인 (의존성 없는) todo들 → Send API로 병렬 실행
    3. 의존성 있는 todo → 선행 작업 완료 후 다시 dispatcher로
    4. 모든 todo 완료 → Command(goto="response")

    Returns:
        list[Send] | Command
    """

async def execute_todo(state: dict) -> Command:
    """
    개별 Todo 실행 노드 (Send에 의해 호출됨)

    1. Supervisor가 tool → executor 매핑
    2. Executor 실행
    3. 결과 → execution_results에 병합

    Returns:
        Command(update={"execution_results": {todo_id: result}, "todos": [updated]})
    """
```

**Execution Strategies**:

| Strategy | 설명 | 사용 조건 |
|----------|------|----------|
| `SINGLE` | 단일 Todo 직접 실행 | Todo가 1개일 때 |
| `SEQUENTIAL` | 순차 실행 (모든 Todo가 의존성 있음) | 완전 순차 의존 |
| `PARALLEL` | Send API로 병렬 실행 | 독립 Todo 존재 |
| `SWARM` | 다중 에이전트 협업 | 복잡한 분석 작업 |
| `CYCLIC` | 반복 실행 (조건 충족까지) | 품질 개선 루프 |

**Execution Graph**:

```
                    ┌──────────────────┐
                    │ execution_       │
        ┌──────────│ dispatcher       │──────────┐
        │          └──────────────────┘          │
        │ Send([todo1, todo2])    │ Send([todo3])│
        ▼                        ▼              ▼
  ┌───────────┐          ┌───────────┐   ┌───────────┐
  │execute_   │          │execute_   │   │execute_   │
  │todo       │          │todo       │   │todo       │
  └─────┬─────┘          └─────┬─────┘   └─────┬─────┘
        │                      │               │
        └──────────┬───────────┘───────────────┘
                   │ (results_reducer로 병합)
                   ▼
            ┌──────────────┐
            │ execution_   │  ← 남은 todo 있으면 다시 dispatcher로
            │ collector    │  ← 전부 완료면 response로
            └──────────────┘
```

**Domain Executors**:

| Executor | Tools | 역할 |
|----------|-------|------|
| `DataExecutor` | collector, preprocessor, trends | 데이터 수집/처리 |
| `InsightExecutor` | sentiment, keyword, competitor | 분석/인사이트 |
| `ContentExecutor` | report, video, ad_creative | 콘텐츠 생성 |
| `OpsExecutor` | sales_material, inventory | 운영 작업 |

#### Layer 4: Response

**역할**: 결과를 어떤 **포맷**으로 출력할지 결정하고 생성

```python
# layers/response/node.py
async def response_node(state: AgentState) -> Command:
    """
    1. Aggregator: 모든 execution_results 집계
    2. FormatDecider: 의도 + 결과 기반으로 출력 포맷 결정
    3. Formatter: 포맷별 생성기 실행
    4. TraceLogger: response 단계 로깅

    Returns:
        Command(update={"response_result": output}, goto=END)
    """
```

**Output Formats**:

| Format | 설명 | 사용 조건 |
|--------|------|----------|
| `text` | 자연어 응답 | 기본 응답 |
| `image` | 차트/그래프 | 시각화 요청 |
| `pdf` | 보고서 PDF | 리포트 요청 |
| `video` | 영상 콘텐츠 | 영상 생성 요청 |
| `mixed` | 복합 포맷 (텍스트 + 첨부) | 분석 + 시각화 |

---

## 3. Two-Level Orchestration

V2는 오케스트레이션을 두 개 레벨로 분리합니다.

### 3.1 Level 1: Graph Orchestration (`orchestrator/`)

LangGraph StateGraph를 통한 4-Layer 조율

```python
# orchestrator/graph.py
from langgraph.graph import StateGraph, START, END

def build_graph() -> StateGraph:
    g = StateGraph(AgentState)

    # Layer 노드 등록
    g.add_node("cognitive", cognitive_node)
    g.add_node("planning", planning_node)
    g.add_node("execution_dispatcher", execution_dispatcher)
    g.add_node("execute_todo", execute_todo)
    g.add_node("execution_collector", execution_collector)
    g.add_node("response", response_node)

    # 진입점
    g.add_edge(START, "cognitive")

    # Layer 간 hand-off는 Command(goto=)로 결정

    return g

def create_agent(checkpointer):
    graph = build_graph()
    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["planning"],  # Plan 생성 후 승인 대기
    )
```

### 3.2 Level 2: Execution Orchestration (`execution/`)

Todo 실행 스케줄링 + 전략 결정

```python
# execution/strategy.py
from enum import Enum

class ExecutionStrategy(str, Enum):
    SINGLE = "single"           # 단일 Todo 직접 실행
    SEQUENTIAL = "sequential"   # 순차 실행
    PARALLEL = "parallel"       # Send API 병렬 실행
    SWARM = "swarm"            # 다중 에이전트 협업
    CYCLIC = "cyclic"          # 반복 실행

def determine_strategy(todos: List[TodoItem]) -> ExecutionStrategy:
    """Todo 의존성 분석 → 최적 전략 결정"""
    if len(todos) == 1:
        return ExecutionStrategy.SINGLE

    independent_todos = [t for t in todos if not t.depends_on]
    if len(independent_todos) > 1:
        return ExecutionStrategy.PARALLEL

    return ExecutionStrategy.SEQUENTIAL
```

### 3.3 Orchestration Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Level 1: Graph Orchestration                          │
│                        (orchestrator/graph.py)                           │
│                                                                          │
│  START ─► cognitive ─Command─► planning ─Command─► execution_dispatcher │
│                                    │                        │            │
│                               interrupt()              Send API          │
│                              (Plan 승인)               (Level 2)         │
│                                                            │            │
│                                                            ▼            │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │            Level 2: Execution Orchestration                       │   │
│  │                  (execution/strategy.py)                          │   │
│  │                                                                   │   │
│  │   ┌──────────────────┐                                           │   │
│  │   │  Strategy Decider │ → SINGLE / SEQUENTIAL / PARALLEL / ...   │   │
│  │   └─────────┬────────┘                                           │   │
│  │             │                                                     │   │
│  │             ▼                                                     │   │
│  │   ┌────────────────────────────────────────────────────────┐     │   │
│  │   │  PARALLEL Strategy                                      │     │   │
│  │   │                                                         │     │   │
│  │   │  Send("execute_todo", {todo: todo1}) ──┐               │     │   │
│  │   │  Send("execute_todo", {todo: todo2}) ──┼──► 병렬 실행   │     │   │
│  │   │  Send("execute_todo", {todo: todo3}) ──┘               │     │   │
│  │   └────────────────────────────────────────────────────────┘     │   │
│  │             │                                                     │   │
│  │             ▼                                                     │   │
│  │   execution_collector ───► 남은 todo? ─Yes─► execution_dispatcher│   │
│  │                              │                                    │   │
│  │                              No                                   │   │
│  │                              │                                    │   │
│  └──────────────────────────────┼────────────────────────────────────┘   │
│                                 │                                        │
│                            Command(goto="response")                      │
│                                 │                                        │
│                                 ▼                                        │
│  response ─────────────────► END                                         │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 4. LangGraph Primitives

V2는 LangGraph 1.0.5의 세 가지 핵심 패턴을 활용합니다.

### 4.1 Command (Sequential Hand-off)

레이어 간 순차 전환에 사용

```python
from langgraph.types import Command

async def cognitive_node(state: AgentState) -> Command:
    # 의도 분류 로직
    output = await classify_intent(state["user_input"])

    return Command(
        update={"cognitive_result": output.model_dump()},
        goto="planning"  # 다음 레이어로 hand-off
    )
```

**사용처**:
- `cognitive → planning`
- `planning → execution`
- `execution → response`
- `response → END`

### 4.2 Send (Parallel Execution)

Execution 레이어 내 병렬 Todo 실행에 사용

```python
from langgraph.types import Send

async def execution_dispatcher(state: AgentState) -> list[Send]:
    # 독립적인 Todo 추출
    ready_todos = get_ready_todos(state["todos"])

    # 각 Todo를 병렬로 실행
    return [
        Send("execute_todo", {"todo": todo, "context": get_context(state)})
        for todo in ready_todos
    ]
```

**사용처**:
- `execution_dispatcher → execute_todo` (N개 병렬)

### 4.3 interrupt() (Human-in-the-Loop)

사용자 입력이 필요한 중단점에 사용

```python
from langgraph.types import interrupt

async def planning_node(state: AgentState) -> Command:
    plan = await generate_plan(state)

    if plan.requires_approval:
        # 사용자 승인 대기
        user_response = interrupt({
            "type": "plan_approval",
            "plan": plan.model_dump(),
            "message": "생성된 계획을 검토해주세요."
        })

        if not user_response.get("approved"):
            # 수정된 계획으로 재생성
            plan = await modify_plan(plan, user_response)

    return Command(
        update={"plan": plan.model_dump(), "todos": [t.model_dump() for t in plan.todos]},
        goto="execution"
    )
```

**Interrupt Points**:

| 지점 | 트리거 | 사용자 액션 |
|------|--------|------------|
| Cognitive | 모호한 의도 | 질문 답변 / 명확화 |
| Planning (interrupt_before) | Plan 생성 완료 | 승인 / 수정 / 거부 |
| Execution | Pause 요청 | 현재 작업 검증 / 수정 / 삭제 |
| Any Layer | 에러 발생 | 재시도 / 건너뛰기 / 중단 |

---

## 5. State Management

### 5.1 Hybrid Type Strategy

| 용도 | 타입 시스템 | 이유 |
|------|-----------|------|
| `AgentState` | **TypedDict** | 성능, 부분 업데이트, Reducer 호환 |
| Layer I/O | **Pydantic BaseModel** | 런타임 검증, 직렬화 |
| Domain Models | **Pydantic BaseModel** | 검증, 불변성 (frozen=True) |
| API Schemas | **Pydantic BaseModel** | FastAPI 자동 문서화 |

### 5.2 AgentState (TypedDict)

```python
from typing import Annotated, TypedDict, Optional

class AgentState(TypedDict, total=False):
    """V2 Agent State - 최소한의 핵심 필드만"""

    # ─── Input ───
    session_id: str
    user_input: str
    language: str  # "ko", "en", "ja"

    # ─── Layer Results ───
    cognitive_result: dict      # CognitiveOutput.model_dump()
    planning_result: dict       # PlanningOutput.model_dump()
    execution_results: Annotated[dict, results_reducer]  # todo_id → result
    response_result: dict       # ResponseOutput.model_dump()

    # ─── Plan & Todos ───
    plan: dict                  # Plan.model_dump()
    todos: Annotated[list, todo_reducer]  # TodoItem 리스트

    # ─── Control ───
    error: Optional[str]

    # ─── HITL ───
    hitl_action: Optional[dict]

    # ─── Learning ───
    trace: Annotated[list, lambda a, b: a + b]  # append-only
```

### 5.3 Custom Reducers

```python
# states/reducers.py

def todo_reducer(existing: list, updates: list) -> list:
    """Todo ID 기반 병합 (최신 버전 우선)"""
    existing_map = {t["id"]: t for t in existing}
    for update in updates:
        existing_item = existing_map.get(update["id"])
        if existing_item is None or update.get("version", 1) > existing_item.get("version", 1):
            existing_map[update["id"]] = update
    return list(existing_map.values())

def results_reducer(existing: dict, new: dict) -> dict:
    """실행 결과 병합 (덮어쓰기)"""
    return {**existing, **new}
```

---

## 6. Directory Structure

```
backend/
├── _old/                          # V1 레거시 (참조용, import 안 됨)
├── _domains/                      # 도메인 참조 코드 라이브러리
│   ├── agents/                    # Agent 참조 구현
│   └── tools/                     # Tool 참조 구현
│
├── api/                           # Interface Layer (FastAPI)
│   ├── main.py                    # FastAPI 앱 생성 + lifespan
│   ├── routes/
│   │   ├── agent.py               # POST /agent/run, /agent/stream
│   │   ├── session.py             # 세션 관리 CRUD
│   │   ├── hitl.py                # HITL 엔드포인트
│   │   └── health.py              # 헬스체크
│   ├── websocket/
│   │   ├── handler.py             # WebSocket 핸들러
│   │   └── protocol.py            # 메시지 프로토콜
│   └── schemas/
│       ├── request.py             # API 요청 스키마
│       └── response.py            # API 응답 스키마
│
└── app/
    ├── core/                      # 공통 인프라
    │   ├── config.py              # Settings (pydantic-settings)
    │   ├── logging.py             # 구조화 로깅
    │   ├── errors.py              # 에러 코드 체계
    │   └── decorators.py          # 학습 훅, 로깅 데코레이터
    │
    └── dream_agent/               # Application Layer
        ├── orchestrator/          # Level 1: 그래프 조립
        │   ├── __init__.py
        │   ├── graph.py           # StateGraph 빌드
        │   ├── builder.py         # 그래프 빌더 헬퍼
        │   ├── router.py          # 라우팅 로직
        │   ├── checkpointer.py    # AsyncPostgresSaver
        │   └── config.py          # interrupt points 등
        │
        ├── states/                # AgentState (TypedDict)
        │   ├── __init__.py
        │   ├── agent_state.py     # AgentState 정의
        │   └── reducers.py        # 커스텀 리듀서
        │
        ├── models/                # Pydantic 도메인 모델
        │   ├── __init__.py
        │   ├── intent.py          # Intent, Entity
        │   ├── plan.py            # Plan
        │   ├── todo.py            # TodoItem (frozen=True)
        │   ├── execution.py       # ExecutionResult
        │   └── response.py        # ResponsePayload, Attachment
        │
        ├── schemas/               # Layer I/O 계약 (Pydantic)
        │   ├── __init__.py
        │   ├── cognitive.py       # CognitiveInput/Output
        │   ├── planning.py        # PlanningInput/Output
        │   ├── execution.py       # ExecutionInput/Output
        │   └── response.py        # ResponseInput/Output
        │
        ├── cognitive/             # Layer 1
        │   ├── __init__.py
        │   ├── node.py            # cognitive_node()
        │   ├── classifier.py      # IntentClassifier
        │   ├── extractor.py       # EntityExtractor
        │   └── clarifier.py       # AmbiguityDetector
        │
        ├── planning/              # Layer 2
        │   ├── __init__.py
        │   ├── node.py            # planning_node()
        │   ├── planner.py         # PlanGenerator
        │   ├── dependency.py      # DAG builder
        │   └── estimator.py       # Resource/Cost estimator
        │
        ├── execution/             # Layer 3
        │   ├── __init__.py
        │   ├── node.py            # execution_dispatcher(), execute_todo()
        │   ├── strategy.py        # ExecutionStrategy 결정
        │   ├── supervisor.py      # ExecutionSupervisor
        │   ├── executor_base.py   # BaseExecutor ABC
        │   └── executors/         # 도메인 Executor
        │       ├── __init__.py
        │       ├── data_executor.py
        │       ├── insight_executor.py
        │       ├── content_executor.py
        │       └── ops_executor.py
        │
        ├── response/              # Layer 4
        │   ├── __init__.py
        │   ├── node.py            # response_node()
        │   ├── formatter.py       # 포맷별 생성
        │   └── aggregator.py      # 결과 집계
        │
        ├── tools/                 # Tool Discovery & Registry
        │   ├── __init__.py
        │   ├── registry.py        # ToolRegistry
        │   ├── discovery.py       # ToolDiscovery
        │   ├── base_tool.py       # BaseTool ABC
        │   └── definitions/       # YAML tool 정의
        │       ├── collector.yaml
        │       ├── preprocessor.yaml
        │       └── ...
        │
        ├── llm_manager/           # LLM 추상화
        │   ├── __init__.py
        │   ├── client.py          # LLM 클라이언트
        │   └── prompts/           # YAML 프롬프트
        │       ├── cognitive.yaml
        │       ├── planning.yaml
        │       ├── execution.yaml
        │       └── response.yaml
        │
        └── workflow_managers/     # 횡단 관심사 Manager
            ├── hitl_manager/      # HITL 처리
            ├── todo_manager/      # Todo CRUD
            ├── feedback_manager/  # 피드백 수집
            ├── callback_manager/  # WebSocket 콜백
            ├── memory_manager/    # 대화 메모리
            └── learning_manager/  # 학습 데이터 수집
```

---

## 7. Communication Patterns

### 7.1 REST API (Synchronous)

짧은 작업에 적합 (타임아웃: 300초)

```
Client ──[POST /agent/run]──► Server ──► Response (blocking)
```

### 7.2 WebSocket + REST (Asynchronous)

긴 작업 + 실시간 업데이트

```
1. Client ──[POST /agent/run-async]──► Server
   └── Response: { session_id, websocket_url }

2. Client ══[WS /ws/{session_id}]══► Server
   ├── Server ──[session_state]──► Client
   ├── Server ──[layer_start]──► Client
   ├── Server ──[todo_progress]──► Client
   ├── Server ──[hitl_request]──► Client
   │   └── Client ──[hitl_response]──► Server
   └── Server ──[complete]──► Client
```

### 7.3 HITL Interrupt Flow

```
Execution ──► interrupt() ──► WebSocket ──► Frontend
                                               │
Frontend: 사용자 결정 (approve/modify/reject)
                                               │
Frontend ──► WebSocket/REST ──► Command(resume) ──► Execution 재개
```

---

## 8. Error Handling

### 8.1 Error Categories

| Code Range | Category | Description |
|------------|----------|-------------|
| 1000-1999 | VALIDATION | 입력 검증 에러 |
| 2000-2999 | AUTH | 인증/권한 에러 |
| 3000-3999 | SESSION | 세션 관리 에러 |
| 4000-4999 | AGENT | 에이전트 실행 에러 |
| 5000-5999 | HITL | HITL 처리 에러 |
| 6000-6999 | TOOL | 도구 실행 에러 |
| 7000-7999 | LLM | LLM 호출 에러 |
| 8000-8999 | EXTERNAL | 외부 서비스 에러 |
| 9000-9999 | INTERNAL | 내부 시스템 에러 |

### 8.2 Error Propagation

```
Tool Error → Executor → ExecutionResult(success=False)
                              │
                              ▼
                    execution_results에 기록
                              │
                              ▼
                    ┌─────────────────────┐
                    │ Error Handler 결정   │
                    ├─────────────────────┤
                    │ • retry (재시도)     │
                    │ • skip (건너뛰기)    │
                    │ • fail (전체 실패)   │
                    │ • hitl (사용자 결정) │
                    └─────────────────────┘
```

---

## 9. Related Documents

| Document | Description |
|----------|-------------|
| [INDEX.md](INDEX.md) | 문서 목록 |
| [DATA_MODELS.md](DATA_MODELS.md) | Pydantic 데이터 모델 상세 |
| [WEBSOCKET_PROTOCOL.md](WEBSOCKET_PROTOCOL.md) | WebSocket 프로토콜 |
| [API_SPEC.md](API_SPEC.md) | REST API 명세 |
| [HITL_SPEC.md](HITL_SPEC.md) | Human-in-the-Loop 시스템 |
| [SESSION_SPEC.md](SESSION_SPEC.md) | 세션 관리 |
| [ERROR_CODES.md](ERROR_CODES.md) | 에러 코드 체계 |

---

*Last Updated: 2026-02-06*
