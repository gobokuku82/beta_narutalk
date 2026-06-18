# Dream Agent V2 구현 완료 보고서

**작성일**: 2026-02-07
**버전**: 2.0.0
**작성자**: Claude Opus 4.5

---

## 1. 개요

### 1.1 프로젝트 목표

V1의 혼합된 Phase 코드를 정리하고, LangGraph 1.0.5의 최신 패턴(Command, Send, interrupt)을 활용하여 **4-Layer Hand-off 아키텍처** 기반의 AI 에이전트 시스템을 재설계.

### 1.2 구현 범위

| 항목 | 상태 | 비고 |
|------|------|------|
| Core Infrastructure | ✅ 완료 | Config, Logging, Errors |
| State & Models | ✅ 완료 | AgentState, Pydantic 모델 |
| Orchestrator | ✅ 완료 | LangGraph StateGraph |
| 4-Layer Nodes | ✅ 완료 | Cognitive, Planning, Execution, Response |
| HITL System | ✅ 완료 | Approval, PlanEditor, Pause/Resume |
| WebSocket | ✅ 완료 | 실시간 통신 |
| Learning Infrastructure | ✅ 완료 | Trace, Query, Feedback 로깅 |
| Session Management | ✅ 완료 | Memory/Redis 지원 |
| API Endpoints | ✅ 완료 | REST + WebSocket |

### 1.3 구현 일정

| Phase | 커밋 | 설명 |
|-------|------|------|
| Phase 1 | `82466c5` | Foundation - 기반 구조 |
| Phase 2 | `bd1a5d8` | Layer Implementation - LLM 통합 |
| Phase 3 | `b5ba6cf` | HITL Completion - 인터럽트 시스템 |
| Phase 4 | `f19fea1` | Learning Infrastructure - 데이터 수집 |
| Phase 5 | `aabde92` | Production Ready - 세션, 에러 처리 |

---

## 2. 아키텍처

### 2.1 시스템 구조

```
User Input
    ↓
┌─────────────────────────────────────────────────────────────────┐
│              orchestrator/ (LangGraph StateGraph)               │
│                                                                 │
│  [Cognitive] ──Command──→ [Planning] ──Command──→ [Execution]  │
│       ↑                      ↑              │                   │
│   interrupt()            interrupt()        │ Send (병렬)       │
│   (질문/명확화)          (Plan 승인)        ↓                   │
│                                       execute_todo x N          │
│                                              │                   │
│                                       ──Command──→ [Response]   │
│                                                        │        │
│                                                     goto=END    │
└─────────────────────────────────────────────────────────────────┘
    ↓
User Output (text / image / pdf / video / mixed)
```

### 2.2 레이어 역할

| Layer | 역할 | 주요 컴포넌트 |
|-------|------|--------------|
| **Cognitive** | 의도 분류, 엔티티 추출, 모호성 탐지 | IntentClassifier, EntityExtractor, Clarifier |
| **Planning** | Plan 생성, 의존성 분석, 비용 추정 | PlanGenerator, DependencyResolver |
| **Execution** | 전략 결정, Todo 병렬/순차 실행 | StrategyDecider, ExecutionSupervisor |
| **Response** | 포맷 결정, 결과 집계, 응답 생성 | FormatDecider, ResultAggregator, ResponseFormatter |

### 2.3 LangGraph Primitives

| Primitive | 용도 | 사용처 |
|-----------|------|--------|
| **Command** | 순차 hand-off | 레이어 간 전환 |
| **Send** | 병렬 실행 | Execution 내 Todo 병렬 처리 |
| **interrupt()** | HITL 중단점 | Plan 승인, 질문, Pause |

---

## 3. 디렉토리 구조

```
backend/
├── api/                           # Interface Layer
│   ├── main.py                    # FastAPI 앱 엔트리포인트
│   ├── middleware/                # 미들웨어
│   │   ├── __init__.py
│   │   └── error_handler.py       # 전역 에러 핸들러
│   ├── routes/                    # API 라우트
│   │   ├── __init__.py
│   │   ├── agent.py               # /api/agent/* (run, run-async, ws)
│   │   ├── health.py              # /health/* (health, ready, live, metrics)
│   │   └── hitl.py                # /api/hitl/* (approve, reject, modify, pause)
│   ├── websocket/                 # WebSocket
│   │   ├── __init__.py
│   │   ├── handler.py             # WebSocket 핸들러
│   │   ├── manager.py             # 연결 관리자
│   │   └── protocol.py            # 메시지 프로토콜
│   └── schemas/                   # API 스키마
│       ├── request.py
│       └── response.py
│
└── app/
    ├── core/                      # 공통 인프라
    │   ├── config.py              # pydantic-settings 설정
    │   ├── logging.py             # structlog 기반 로깅
    │   ├── errors.py              # 에러 코드 체계
    │   └── decorators.py          # @trace_log 등 데코레이터
    │
    └── dream_agent/               # Application Layer
        ├── orchestrator/          # LangGraph 그래프 조립
        │   ├── __init__.py
        │   ├── builder.py         # build_graph(), create_agent()
        │   ├── checkpointer.py    # AsyncPostgresSaver / MemorySaver
        │   ├── config.py          # OrchestratorConfig
        │   └── router.py          # 라우팅 함수
        │
        ├── states/                # 상태 정의
        │   ├── agent_state.py     # AgentState (TypedDict)
        │   └── reducers.py        # 커스텀 리듀서
        │
        ├── models/                # Pydantic 도메인 모델
        │   ├── __init__.py
        │   ├── enums.py           # IntentDomain, TodoStatus 등
        │   ├── intent.py          # Intent, Entity
        │   ├── todo.py            # TodoItem (frozen=True)
        │   ├── plan.py            # Plan, PlanChange
        │   ├── execution.py       # ExecutionResult, ExecutionContext
        │   ├── response.py        # ResponsePayload, Attachment
        │   ├── hitl.py            # HITLRequest, HITLResponse
        │   └── tool.py            # ToolSpec, ToolParameter
        │
        ├── schemas/               # Layer I/O 계약
        │   ├── cognitive.py       # CognitiveInput/Output
        │   ├── planning.py        # PlanningInput/Output
        │   ├── execution.py       # ExecutionInput/Output
        │   └── response.py        # ResponseInput/Output
        │
        ├── cognitive/             # Layer 1
        │   ├── cognitive_node.py  # 메인 노드 함수
        │   ├── classifier.py      # IntentClassifier
        │   ├── extractor.py       # EntityExtractor
        │   └── clarifier.py       # AmbiguityDetector, Clarifier
        │
        ├── planning/              # Layer 2
        │   ├── planning_node.py   # 메인 노드 함수
        │   ├── planner.py         # PlanGenerator
        │   └── dependency.py      # DependencyResolver
        │
        ├── execution/             # Layer 3
        │   ├── execution_node.py  # 메인 노드 함수
        │   ├── strategy.py        # StrategyDecider, ExecutionCoordinator
        │   ├── supervisor.py      # ExecutionSupervisor
        │   └── executor_base.py   # BaseExecutor ABC
        │
        ├── response/              # Layer 4
        │   ├── response_node.py   # 메인 노드 함수
        │   ├── formatter.py       # ResponseFormatter, FormatDecider
        │   └── aggregator.py      # ResultAggregator
        │
        ├── tools/                 # Tool Registry
        │   ├── registry.py        # ToolRegistry (YAML 로드)
        │   ├── base_tool.py       # BaseTool ABC
        │   └── definitions/       # YAML tool 정의
        │
        ├── llm_manager/           # LLM 추상화
        │   ├── __init__.py
        │   ├── client.py          # LLMClient (OpenAI/Anthropic)
        │   ├── config.py          # LLMConfig, PromptConfig
        │   └── prompts/           # YAML 프롬프트 템플릿
        │
        └── workflow_managers/     # 횡단 관심사
            ├── hitl_manager/      # HITL 관리
            │   ├── __init__.py
            │   ├── manager.py     # HITLManager
            │   ├── approval.py    # ApprovalHandler
            │   ├── plan_editor.py # PlanEditor (자연어 수정)
            │   └── pause.py       # PauseController
            │
            ├── learning_manager/  # 학습 인프라
            │   ├── __init__.py
            │   ├── trace_logger.py    # TraceLogger
            │   ├── query_logger.py    # QueryLogger
            │   ├── feedback_collector.py # FeedbackCollector
            │   └── export.py          # LearningDataExporter
            │
            └── session_manager/   # 세션 관리
                ├── __init__.py
                └── session.py     # SessionManager (Memory/Redis)
```

---

## 4. API 명세

### 4.1 REST Endpoints

| Method | Path | 설명 |
|--------|------|------|
| `POST` | `/api/agent/run` | 동기 에이전트 실행 |
| `POST` | `/api/agent/run-async` | 비동기 에이전트 실행 (WebSocket) |
| `GET` | `/api/agent/status/{sid}` | 세션 상태 조회 |
| `POST` | `/api/agent/stop/{sid}` | 실행 중지 |
| `POST` | `/api/hitl/approve/{sid}` | Plan 승인 |
| `POST` | `/api/hitl/reject/{sid}` | Plan 거부 |
| `POST` | `/api/hitl/modify/{sid}` | Plan 수정 (자연어) |
| `POST` | `/api/hitl/input/{sid}` | 사용자 입력 제공 |
| `POST` | `/api/hitl/pause/{sid}` | 일시정지 |
| `POST` | `/api/hitl/resume/{sid}` | 재개 |
| `GET` | `/api/hitl/status/{sid}` | HITL 상태 조회 |
| `GET` | `/health` | 기본 헬스체크 |
| `GET` | `/health/ready` | Readiness 체크 |
| `GET` | `/health/live` | Liveness 체크 |
| `GET` | `/health/metrics` | 메트릭 조회 |

### 4.2 WebSocket

| Path | 설명 |
|------|------|
| `WS /api/agent/ws/{session_id}` | 실시간 통신 |

**Server → Client 메시지**:
- `layer_start` / `layer_complete`: 레이어 진행 상태
- `todo_update`: Todo 상태 변경
- `execution_progress`: 실행 진행률
- `hitl_request`: HITL 요청 (사용자 입력 필요)
- `complete`: 최종 완료
- `error`: 에러 발생

**Client → Server 메시지**:
- `approve` / `reject` / `modify`: Plan 응답
- `input`: 사용자 입력
- `pause` / `resume` / `cancel`: 제어
- `ping`: 하트비트

---

## 5. 데이터 모델

### 5.1 AgentState (TypedDict)

```python
class AgentState(TypedDict, total=False):
    # Input
    session_id: str
    user_input: str
    language: str

    # Layer Results
    cognitive_result: dict
    planning_result: dict
    execution_results: Annotated[dict, results_reducer]
    response_result: dict

    # Plan & Todos
    plan: dict
    todos: Annotated[list, todo_reducer]

    # Control
    error: Optional[str]
    hitl_action: Optional[dict]

    # Learning
    trace: Annotated[list, trace_reducer]
```

### 5.2 핵심 Pydantic 모델

| 모델 | 용도 | 특징 |
|------|------|------|
| `Intent` | 의도 분류 결과 | frozen=True |
| `TodoItem` | 실행 단위 | frozen=True, with_status() |
| `Plan` | 실행 계획 | 의존성 검증, 사이클 탐지 |
| `ExecutionResult` | 실행 결과 | 성공/실패 상태 |
| `ResponsePayload` | 최종 응답 | 다중 포맷 지원 |

---

## 6. 주요 컴포넌트 상세

### 6.1 Orchestrator

```python
# builder.py
def build_graph() -> StateGraph:
    """LangGraph StateGraph 빌드"""
    graph = StateGraph(AgentState)

    # 노드 등록
    graph.add_node("cognitive", cognitive_node)
    graph.add_node("planning", planning_node)
    graph.add_node("execution", execution_node)
    graph.add_node("response", response_node)

    # 진입점
    graph.add_edge(START, "cognitive")

    # 조건부 라우팅
    graph.add_conditional_edges("cognitive", route_after_cognitive)
    graph.add_conditional_edges("planning", route_after_planning)
    graph.add_conditional_edges("execution", route_after_execution)
    graph.add_edge("response", END)

    return graph
```

### 6.2 HITL Manager

```python
# manager.py
class HITLManager:
    """HITL 요청/응답 관리"""

    def create_request(session_id, request_type, message, ...) -> HITLRequest
    async def wait_for_response(request_id, timeout) -> Optional[HITLResponse]
    def submit_response(request_id, action, value, comment) -> bool

# plan_editor.py
class PlanEditor:
    """자연어 기반 Plan 수정"""

    async def parse_instruction(instruction, plan) -> dict
    async def apply_edit(plan, parsed, user_instruction) -> tuple[Plan, PlanChange]
```

### 6.3 Learning Infrastructure

```python
# decorators.py
@trace_log(layer="cognitive", action="classify_intent")
async def classify_intent(user_input: str) -> Intent:
    ...

# trace_logger.py
class TraceLogger:
    def log(layer, action, input_data, output_data, duration_ms, success, error)
    def flush()  # 파일에 JSONL로 저장
    def get_layer_stats() -> dict[str, dict]

# export.py
class LearningDataExporter:
    def export_traces(config) -> Path
    def export_training_pairs(config) -> Path  # SFT/RLHF용
```

---

## 7. 설정

### 7.1 환경 변수 (.env)

```env
# App
APP_NAME=Dream Agent V2
APP_VERSION=2.0.0
DEBUG=false
ENVIRONMENT=development

# Server
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/dream_agent

# Redis (Optional)
REDIS_URL=redis://localhost:6379/0

# LLM
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-4o

# Session
SESSION_TIMEOUT_SEC=3600

# HITL
HITL_TIMEOUT_SEC=300

# Execution
EXECUTION_MAX_PARALLEL=5
```

---

## 8. 검증 계획

### 8.1 검증 순서

```bash
# 1. 서버 기동 테스트
python run_server.py

# 2. 헬스체크
curl http://localhost:8000/health
curl http://localhost:8000/health/ready

# 3. 동기 실행 테스트
curl -X POST http://localhost:8000/api/agent/run \
  -H "Content-Type: application/json" \
  -d '{"message": "테스트 쿼리", "language": "ko"}'

# 4. WebSocket 테스트 (wscat)
wscat -c ws://localhost:8000/api/agent/ws/test-session

# 5. HITL 테스트
curl -X POST http://localhost:8000/api/hitl/pause/test-session
curl -X POST http://localhost:8000/api/hitl/resume/test-session
```

### 8.2 Unit Test 대상

| 모듈 | 테스트 항목 |
|------|------------|
| `models/` | Pydantic 직렬화/역직렬화, 유효성 검증 |
| `states/` | 리듀서 동작 (todo_reducer, results_reducer) |
| `schemas/` | Layer I/O 계약 검증 |
| `cognitive/` | IntentClassifier, EntityExtractor |
| `planning/` | DependencyResolver, 사이클 탐지 |
| `execution/` | StrategyDecider, ExecutionCoordinator |

---

## 9. 향후 작업

### 9.1 즉시 필요

| 항목 | 우선순위 | 설명 |
|------|---------|------|
| Unit Tests 작성 | High | `tests/unit/` 폴더 |
| Integration Tests | High | `tests/integration/` 폴더 |
| Tool Executors 구현 | High | `execution/executors/` 도메인별 Executor |

### 9.2 개선 사항

| 항목 | 우선순위 | 설명 |
|------|---------|------|
| Prompt 템플릿 최적화 | Medium | `llm_manager/prompts/*.yaml` |
| 에러 복구 로직 | Medium | 재시도, 폴백 전략 |
| 메트릭 대시보드 | Low | Prometheus/Grafana 연동 |
| 프론트엔드 연동 | Low | React/Next.js 클라이언트 |

---

## 10. 참고 문서

| 문서 | 경로 |
|------|------|
| V2 아키텍처 설계서 | `reports_mind_dream/version_2/v2_architecture_260205.md` |
| 구현 계획서 | `docs/IMPLEMENTATION_PLAN.md` |
| API 스펙 | `docs/specs/API_SPEC.md` |
| HITL 스펙 | `docs/specs/HITL_SPEC.md` |
| WebSocket 스펙 | `docs/specs/WEBSOCKET_SPEC.md` |

---

## 11. 결론

Dream Agent V2의 핵심 구현이 완료되었습니다. 5개 Phase를 통해:

1. **Foundation**: 견고한 기반 구조 (State, Models, Schemas)
2. **Layer Implementation**: LLM 통합 4-Layer 아키텍처
3. **HITL Completion**: 사용자 개입 시스템 (승인, 수정, 일시정지)
4. **Learning Infrastructure**: 비침습적 데이터 수집 체계
5. **Production Ready**: 세션 관리, 에러 핸들링

다음 단계는 **검증 및 테스트**입니다.
