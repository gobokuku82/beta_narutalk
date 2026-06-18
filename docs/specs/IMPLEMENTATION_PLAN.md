# Dream Agent V2 - Implementation Plan

**Version**: 2.0 | **Date**: 2026-02-06 | **Status**: Active

---

## Overview

V2 구현을 5개 Phase로 나누어 진행합니다. 각 Phase는 독립적으로 검증 가능하며, 이전 Phase 완료 후 다음으로 진행합니다.

### Phase Summary

| Phase | 목표 | 예상 파일 수 | 검증 |
|-------|------|-------------|------|
| **Phase 1** | Foundation | ~25개 | pytest unit |
| **Phase 2** | Layer Implementation | ~20개 | pytest integration |
| **Phase 3** | HITL Completion | ~10개 | E2E scenario |
| **Phase 4** | Learning Infrastructure | ~8개 | 로깅 확인 |
| **Phase 5** | Production Ready | ~10개 | 서버 기동 |

---

## Phase 1: Foundation

**목표**: 깨끗한 시작점 + 4-Layer 기본 동작 (Mock 반환)

### 1.1 State 정의

| 파일 | 설명 | 참조 |
|------|------|------|
| `states/agent_state.py` | AgentState (TypedDict) 정의 | [DATA_MODELS.md#AgentState](DATA_MODELS.md) |
| `states/reducers.py` | 커스텀 리듀서 (todo_reducer, results_reducer) | [ARCHITECTURE.md#State](ARCHITECTURE.md) |

```python
# states/agent_state.py 핵심 구조
class AgentState(TypedDict, total=False):
    session_id: str
    user_input: str
    language: str
    cognitive_result: dict
    planning_result: dict
    execution_results: Annotated[dict, results_reducer]
    response_result: dict
    plan: dict
    todos: Annotated[list, todo_reducer]
    error: Optional[str]
    hitl_action: Optional[dict]
    trace: Annotated[list, lambda a, b: a + b]
```

### 1.2 Pydantic Models

| 파일 | 클래스 | 참조 |
|------|--------|------|
| `models/intent.py` | `Intent`, `Entity`, `IntentDomain` | [DATA_MODELS.md#Intent](DATA_MODELS.md) |
| `models/plan.py` | `Plan`, `PlanStatus` | [DATA_MODELS.md#Plan](DATA_MODELS.md) |
| `models/todo.py` | `TodoItem` (frozen=True) | [DATA_MODELS.md#TodoItem](DATA_MODELS.md) |
| `models/execution.py` | `ExecutionResult`, `ExecutionContext` | [DATA_MODELS.md#Execution](DATA_MODELS.md) |
| `models/response.py` | `ResponsePayload`, `Attachment` | [DATA_MODELS.md#Response](DATA_MODELS.md) |

### 1.3 Layer I/O Schemas

| 파일 | Input/Output | 참조 |
|------|--------------|------|
| `schemas/cognitive.py` | `CognitiveInput`, `CognitiveOutput` | [DATA_MODELS.md#LayerSchemas](DATA_MODELS.md) |
| `schemas/planning.py` | `PlanningInput`, `PlanningOutput` | [DATA_MODELS.md#LayerSchemas](DATA_MODELS.md) |
| `schemas/execution.py` | `ExecutionInput`, `ExecutionOutput` | [DATA_MODELS.md#LayerSchemas](DATA_MODELS.md) |
| `schemas/response.py` | `ResponseInput`, `ResponseOutput` | [DATA_MODELS.md#LayerSchemas](DATA_MODELS.md) |

### 1.4 Orchestrator (Graph 빌드)

| 파일 | 설명 | 참조 |
|------|------|------|
| `orchestrator/builder.py` | StateGraph 빌드 함수 | [ARCHITECTURE.md#Graph](ARCHITECTURE.md) |
| `orchestrator/checkpointer.py` | AsyncPostgresSaver 설정 | [DB_SCHEMA.md#Checkpointer](DB_SCHEMA.md) |
| `orchestrator/router.py` | 조건부 라우팅 함수 | [ARCHITECTURE.md#Routing](ARCHITECTURE.md) |
| `orchestrator/config.py` | interrupt_before 등 설정 | [HITL_SPEC.md](HITL_SPEC.md) |

```python
# orchestrator/builder.py 핵심 구조
def build_graph() -> StateGraph:
    g = StateGraph(AgentState)
    g.add_node("cognitive", cognitive_node)
    g.add_node("planning", planning_node)
    g.add_node("execution", execution_node)
    g.add_node("response", response_node)
    g.add_edge(START, "cognitive")
    # Command(goto=)로 라우팅
    return g
```

### 1.5 Mock Layer Nodes

| 파일 | 함수 | 반환 |
|------|------|------|
| `cognitive/cognitive_node.py` | `cognitive_node()` | `Command(update={...}, goto="planning")` |
| `planning/planning_node.py` | `planning_node()` | `Command(update={...}, goto="execution")` |
| `execution/execution_node.py` | `execution_node()` | `Command(update={...}, goto="response")` |
| `response/response_node.py` | `response_node()` | `Command(update={...}, goto=END)` |

### 1.6 Basic API

| 파일 | 엔드포인트 | 참조 |
|------|-----------|------|
| `api/main.py` | FastAPI app + lifespan | - |
| `api/routes/agent.py` | `POST /agent/run` (동기) | [API_SPEC.md#agent-run](API_SPEC.md) |
| `api/routes/health.py` | `GET /health` | [API_SPEC.md#health](API_SPEC.md) |
| `api/schemas/request.py` | `AgentRunRequest` | [API_SPEC.md#schemas](API_SPEC.md) |
| `api/schemas/response.py` | `AgentRunResponse` | [API_SPEC.md#schemas](API_SPEC.md) |

### 1.7 Core Infrastructure

| 파일 | 설명 | 참조 |
|------|------|------|
| `core/config.py` | Settings (pydantic-settings) | - |
| `core/logging.py` | 구조화 로깅 설정 | - |
| `core/errors.py` | 에러 코드 정의 | [ERROR_CODES.md](ERROR_CODES.md) |

### Phase 1 검증

```bash
# 1. Unit tests
pytest tests/unit/models/ -v
pytest tests/unit/states/ -v

# 2. Graph 빌드 테스트
pytest tests/unit/orchestrator/ -v

# 3. API 기동 테스트
python run_server.py
curl http://localhost:8000/health
```

---

## Phase 2: Layer Implementation

**목표**: 4-Layer 실제 LLM 연동 구현

### 2.1 LLM Manager

| 파일 | 설명 | 참조 |
|------|------|------|
| `llm_manager/client.py` | LLM 클라이언트 (provider-agnostic) | - |
| `llm_manager/config.py` | LLM 설정 | - |
| `llm_manager/prompts/cognitive.yaml` | Cognitive 프롬프트 | - |
| `llm_manager/prompts/planning.yaml` | Planning 프롬프트 | - |
| `llm_manager/prompts/execution.yaml` | Execution 프롬프트 | - |
| `llm_manager/prompts/response.yaml` | Response 프롬프트 | - |

### 2.2 Cognitive Layer (실제 구현)

| 파일 | 클래스/함수 | 설명 |
|------|------------|------|
| `cognitive/cognitive_node.py` | `cognitive_node()` | LangGraph 노드 함수 |
| `cognitive/classifier.py` | `IntentClassifier` | LLM 기반 의도 분류 |
| `cognitive/extractor.py` | `EntityExtractor` | 엔티티 추출 |
| `cognitive/clarifier.py` | `AmbiguityDetector` | 모호성 탐지 + 질문 생성 |

```python
# cognitive/cognitive_node.py 핵심 로직
async def cognitive_node(state: AgentState) -> Command:
    classifier = IntentClassifier()
    extractor = EntityExtractor()

    intent = await classifier.classify(state["user_input"])
    entities = await extractor.extract(state["user_input"])

    if intent.confidence < 0.7:
        return interrupt({"type": "clarification", "question": "..."})

    return Command(
        update={"cognitive_result": CognitiveOutput(...).model_dump()},
        goto="planning"
    )
```

### 2.3 Planning Layer (실제 구현)

| 파일 | 클래스/함수 | 설명 |
|------|------------|------|
| `planning/planning_node.py` | `planning_node()` | LangGraph 노드 함수 |
| `planning/planner.py` | `PlanGenerator` | LLM + Tool Catalog → Plan 생성 |
| `planning/dependency.py` | `DependencyResolver` | DAG 빌드 + 위상 정렬 |

### 2.4 Execution Layer (Send API)

| 파일 | 클래스/함수 | 설명 |
|------|------------|------|
| `execution/execution_node.py` | `execution_dispatcher()` | Send API로 병렬 실행 |
| `execution/executor_node.py` | `execute_todo()` | 개별 Todo 실행 노드 |
| `execution/strategy.py` | `ExecutionStrategy` | 실행 전략 결정 |
| `execution/supervisor.py` | `ExecutionSupervisor` | Tool → Executor 매핑 |
| `execution/executor_base.py` | `BaseExecutor` | ABC |
| `execution/executors/data_executor.py` | `DataExecutor` | 데이터 관련 실행 |

```python
# execution/execution_node.py 핵심 로직
async def execution_dispatcher(state: AgentState) -> list[Send] | Command:
    todos = state["todos"]
    ready = [t for t in todos if all_deps_complete(t, state)]

    if not ready:
        if all_complete(todos, state):
            return Command(goto="response")
        return Command()  # 대기

    return [Send("execute_todo", {"todo": t}) for t in ready]
```

### 2.5 Response Layer

| 파일 | 클래스/함수 | 설명 |
|------|------------|------|
| `response/response_node.py` | `response_node()` | LangGraph 노드 함수 |
| `response/formatter.py` | `ResponseFormatter` | 포맷별 생성 |
| `response/aggregator.py` | `ResultAggregator` | 결과 집계 |

### 2.6 Tool Registry

| 파일 | 설명 | 참조 |
|------|------|------|
| `tools/registry.py` | ToolRegistry (YAML 로드) | - |
| `tools/discovery.py` | ToolDiscovery (런타임) | - |
| `tools/base_tool.py` | BaseTool ABC | - |
| `tools/definitions/*.yaml` | Tool YAML 정의 | V1 참조 |

### Phase 2 검증

```bash
# 1. Layer 단위 테스트
pytest tests/unit/cognitive/ -v
pytest tests/unit/planning/ -v
pytest tests/unit/execution/ -v
pytest tests/unit/response/ -v

# 2. Integration 테스트
pytest tests/integration/graph/ -v

# 3. E2E 테스트 (Mock LLM)
pytest tests/e2e/ -v --mock-llm
```

---

## Phase 3: HITL Completion

**목표**: Human-in-the-Loop 완전 구현

### 3.1 HITL Manager

| 파일 | 클래스/함수 | 참조 |
|------|------------|------|
| `workflow_managers/hitl_manager/manager.py` | `HITLManager` | [HITL_SPEC.md](HITL_SPEC.md) |
| `workflow_managers/hitl_manager/plan_editor.py` | `PlanEditor` | 자연어 Plan 수정 |
| `workflow_managers/hitl_manager/approval.py` | `ApprovalHandler` | 승인 워크플로우 |
| `workflow_managers/hitl_manager/pause.py` | `PauseController` | Pause/Resume |

### 3.2 WebSocket Handler

| 파일 | 설명 | 참조 |
|------|------|------|
| `api/websocket/handler.py` | WebSocket 연결 핸들러 | [WEBSOCKET_PROTOCOL.md](WEBSOCKET_PROTOCOL.md) |
| `api/websocket/protocol.py` | 메시지 프로토콜 | [WEBSOCKET_PROTOCOL.md](WEBSOCKET_PROTOCOL.md) |
| `api/websocket/manager.py` | 연결 관리자 | - |

### 3.3 Async API

| 파일 | 엔드포인트 | 참조 |
|------|-----------|------|
| `api/routes/agent.py` | `POST /agent/run-async` | [API_SPEC.md](API_SPEC.md) |
| `api/routes/hitl.py` | `/hitl/*` 엔드포인트 | [API_SPEC.md#hitl](API_SPEC.md) |

### 3.4 interrupt() 통합

| 위치 | 트리거 | 참조 |
|------|--------|------|
| `cognitive_node` | 모호한 의도 | [HITL_SPEC.md#clarification](HITL_SPEC.md) |
| `planning_node` | Plan 생성 완료 | [HITL_SPEC.md#approval](HITL_SPEC.md) |
| `execution_node` | 사용자 Pause 요청 | [HITL_SPEC.md#pause](HITL_SPEC.md) |

### Phase 3 검증

```bash
# 1. WebSocket 연결 테스트
pytest tests/integration/websocket/ -v

# 2. HITL 시나리오 테스트
pytest tests/e2e/hitl/ -v

# 3. 수동 테스트
# - Plan 승인/수정/거부
# - Pause → 검증 → Resume
# - 자연어 Todo 수정
```

---

## Phase 4: Learning Infrastructure

**목표**: 학습 데이터 수집 파이프라인 (수집만, 학습은 별도)

### 4.1 Trace Logger

| 파일 | 설명 |
|------|------|
| `workflow_managers/learning_manager/trace_logger.py` | 실행 트레이스 로깅 |
| `workflow_managers/learning_manager/models.py` | `TraceLog`, `FeedbackRecord` |

### 4.2 Decorators

| 파일 | 데코레이터 |
|------|-----------|
| `core/decorators.py` | `@trace_log(layer, action)` |

```python
# 사용 예
@trace_log(layer="cognitive", action="classify_intent")
async def classify_intent(user_input: str) -> Intent:
    ...
```

### 4.3 Feedback Collector

| 파일 | 설명 |
|------|------|
| `workflow_managers/feedback_manager/collector.py` | 사용자 피드백 수집 |
| `api/routes/feedback.py` | `POST /feedback` |

### 4.4 Export

| 파일 | 설명 |
|------|------|
| `workflow_managers/learning_manager/export.py` | JSONL 학습 데이터 export |

### Phase 4 검증

```bash
# 1. 로깅 확인
pytest tests/unit/learning/ -v

# 2. 실행 후 로그 확인
python run_server.py
# → PostgreSQL trace_logs 테이블 확인
# → JSONL export 확인
```

---

## Phase 5: Production Ready

**목표**: 프로덕션 배포 준비

### 5.1 Session Management

| 파일 | 설명 | 참조 |
|------|------|------|
| `workflow_managers/session_manager/manager.py` | 세션 관리 | [SESSION_SPEC.md](SESSION_SPEC.md) |
| `api/routes/session.py` | 세션 CRUD API | [API_SPEC.md#session](API_SPEC.md) |

### 5.2 Error Handling

| 파일 | 설명 | 참조 |
|------|------|------|
| `core/errors.py` | 에러 코드 체계 | [ERROR_CODES.md](ERROR_CODES.md) |
| `core/exceptions.py` | 커스텀 예외 클래스 | - |
| `api/middleware/error_handler.py` | 전역 에러 핸들러 | - |

### 5.3 Database

| 작업 | 설명 | 참조 |
|------|------|------|
| SQL 스크립트 실행 | sessions, session_messages 테이블 | [DB_SCHEMA.md](DB_SCHEMA.md) |
| Checkpointer setup | `await checkpointer.setup()` | [DB_SCHEMA.md#Checkpointer](DB_SCHEMA.md) |

### 5.4 Health & Monitoring

| 파일 | 설명 |
|------|------|
| `api/routes/health.py` | `/health`, `/health/ready`, `/health/live` |
| `core/metrics.py` | Prometheus 메트릭 (선택) |

### 5.5 Configuration

| 파일 | 설명 |
|------|------|
| `.env.example` | 환경 변수 템플릿 |
| `docker-compose.yml` | 개발 환경 |
| `Dockerfile` | 프로덕션 이미지 |

### Phase 5 검증

```bash
# 1. 전체 테스트
pytest tests/ -v

# 2. 서버 기동
python run_server.py

# 3. Health check
curl http://localhost:8000/health/ready

# 4. E2E 시나리오
# - 세션 생성 → 에이전트 실행 → 응답 확인
# - 에러 발생 → 에러 코드 확인
# - 세션 만료 → 정리 확인
```

---

## File Creation Order

### Phase 1 (순서대로)

```
1. core/config.py
2. core/logging.py
3. core/errors.py

4. states/reducers.py
5. states/agent_state.py

6. models/intent.py
7. models/plan.py
8. models/todo.py
9. models/execution.py
10. models/response.py

11. schemas/cognitive.py
12. schemas/planning.py
13. schemas/execution.py
14. schemas/response.py

15. orchestrator/config.py
16. orchestrator/checkpointer.py
17. orchestrator/router.py
18. orchestrator/builder.py

19. cognitive/cognitive_node.py (mock)
20. planning/planning_node.py (mock)
21. execution/execution_node.py (mock)
22. response/response_node.py (mock)

23. api/schemas/request.py
24. api/schemas/response.py
25. api/routes/health.py
26. api/routes/agent.py
27. api/main.py
```

---

## Reference Documents

| Document | 용도 |
|----------|------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 전체 아키텍처 참조 |
| [DATA_MODELS.md](DATA_MODELS.md) | Pydantic 모델 스키마 |
| [API_SPEC.md](API_SPEC.md) | REST API 명세 |
| [WEBSOCKET_PROTOCOL.md](WEBSOCKET_PROTOCOL.md) | WebSocket 프로토콜 |
| [HITL_SPEC.md](HITL_SPEC.md) | HITL 시스템 명세 |
| [SESSION_SPEC.md](SESSION_SPEC.md) | 세션 관리 명세 |
| [DB_SCHEMA.md](DB_SCHEMA.md) | 데이터베이스 스키마 |
| [ERROR_CODES.md](ERROR_CODES.md) | 에러 코드 체계 |

### V1 Legacy Reference

| 폴더 | 용도 |
|------|------|
| `backend/_old/` | V1 전체 코드 참조 |
| `backend/_domains/` | 검증된 Agent/Tool 참조 |

---

*Last Updated: 2026-02-06*
