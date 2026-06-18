# Dream Agent V2 테스트 계획서

**작성일**: 2026-02-07
**버전**: 2.0.0
**상태**: Draft

---

## 1. 개요

### 1.1 목적

Dream Agent V2 구현의 품질 보증을 위한 테스트 전략 및 계획 수립.

### 1.2 테스트 범위

| 구분 | 범위 | 비고 |
|------|------|------|
| Unit Test | 모델, 스키마, 개별 컴포넌트 | pytest |
| Integration Test | 레이어 간 통합, 그래프 플로우 | pytest-asyncio |
| E2E Test | 전체 파이프라인, API 호출 | pytest + httpx |
| Load Test | 성능, 동시성 | locust (선택) |

### 1.3 테스트 환경

```
Python: 3.11+
pytest: 8.0+
pytest-asyncio: 0.23+
pytest-cov: 4.0+
httpx: 0.27+ (async HTTP client)
```

---

## 2. 테스트 구조

```
tests/
├── conftest.py              # 공통 fixture (V2용 업데이트 필요)
├── __init__.py
│
├── unit/                    # 단위 테스트
│   ├── __init__.py
│   ├── core/               # 코어 인프라
│   │   ├── test_config.py
│   │   ├── test_errors.py
│   │   └── test_decorators.py
│   │
│   ├── models/             # Pydantic 모델 (V2 업데이트 필요)
│   │   ├── test_intent.py
│   │   ├── test_todo.py
│   │   ├── test_plan.py
│   │   ├── test_execution.py
│   │   ├── test_response.py
│   │   └── test_hitl.py
│   │
│   ├── schemas/            # Layer I/O 스키마
│   │   ├── test_cognitive.py
│   │   ├── test_planning.py
│   │   ├── test_execution.py
│   │   └── test_response.py
│   │
│   ├── states/             # AgentState, Reducers
│   │   ├── test_agent_state.py
│   │   └── test_reducers.py
│   │
│   ├── cognitive/          # Cognitive Layer
│   │   ├── test_classifier.py
│   │   ├── test_extractor.py
│   │   └── test_clarifier.py
│   │
│   ├── planning/           # Planning Layer
│   │   ├── test_planner.py
│   │   └── test_dependency.py
│   │
│   ├── execution/          # Execution Layer
│   │   ├── test_strategy.py
│   │   └── test_supervisor.py
│   │
│   ├── response/           # Response Layer
│   │   ├── test_formatter.py
│   │   └── test_aggregator.py
│   │
│   ├── tools/              # Tool Registry
│   │   ├── test_registry.py
│   │   └── test_base_tool.py
│   │
│   └── workflow_managers/  # 횡단 관심사
│       ├── test_hitl_manager.py
│       ├── test_session_manager.py
│       └── test_learning_manager.py
│
├── integration/            # 통합 테스트
│   ├── __init__.py
│   ├── graph/             # 그래프 플로우
│   │   ├── test_graph_build.py
│   │   ├── test_layer_flow.py
│   │   └── test_hitl_interrupt.py
│   │
│   ├── api/               # API 통합
│   │   ├── test_agent_api.py
│   │   ├── test_hitl_api.py
│   │   └── test_health_api.py
│   │
│   └── websocket/         # WebSocket 통합
│       └── test_websocket.py
│
└── e2e/                   # E2E 테스트
    ├── __init__.py
    ├── test_full_pipeline.py
    ├── test_hitl_scenario.py
    └── test_error_recovery.py
```

---

## 3. Unit Tests

### 3.1 Core Infrastructure

#### test_config.py

```python
class TestSettings:
    """설정 테스트"""

    def test_default_values():
        """기본값 확인"""

    def test_env_override():
        """환경변수 오버라이드"""

    def test_validation():
        """유효성 검증"""
```

#### test_errors.py

```python
class TestErrorCode:
    """에러 코드 테스트"""

    def test_error_code_format():
        """에러 코드 형식 (E1xxx, E2xxx, ...)"""

    def test_agent_error_creation():
        """AgentError 생성"""

    def test_error_to_detail():
        """ErrorDetail 변환"""
```

#### test_decorators.py

```python
class TestTraceLog:
    """@trace_log 데코레이터 테스트"""

    async def test_async_function_logging():
        """비동기 함수 로깅"""

    def test_sync_function_logging():
        """동기 함수 로깅"""

    async def test_error_logging():
        """에러 발생 시 로깅"""

    async def test_input_output_capture():
        """입출력 캡처"""
```

### 3.2 Models (V2 기준)

#### test_intent.py

```python
class TestEntity:
    """Entity 모델 테스트"""

    def test_create_entity():
        """엔티티 생성"""
        entity = Entity(
            type="brand",
            value="라네즈",
            confidence=0.95
        )
        assert entity.type == "brand"
        assert entity.value == "라네즈"

    def test_frozen_immutability():
        """불변성 검증 (frozen=True)"""

class TestIntent:
    """Intent 모델 테스트"""

    def test_create_intent():
        """의도 생성"""
        intent = Intent(
            domain=IntentDomain.ANALYSIS,
            category="sentiment",
            confidence=0.85,
            summary="감성 분석 요청"
        )

    def test_domain_enum_values():
        """도메인 Enum 값 검증"""
        # ANALYSIS, CONTENT, OPERATION, INQUIRY

    def test_with_entities():
        """엔티티 포함 의도"""
```

#### test_todo.py (V2 업데이트)

```python
class TestTodoItem:
    """TodoItem 테스트 (V2 - frozen=True)"""

    def test_create_minimal():
        """최소 필드 생성"""
        todo = TodoItem(
            task="데이터 수집",
            tool="collector",
            plan_id="plan-001"
        )
        assert todo.status == TodoStatus.PENDING
        assert todo.id is not None

    def test_frozen_immutability():
        """불변성 - 직접 수정 불가"""
        todo = TodoItem(task="테스트", tool="test", plan_id="p1")
        with pytest.raises(ValidationError):
            todo.status = TodoStatus.COMPLETED

    def test_with_status():
        """상태 변경 메서드"""
        todo = TodoItem(task="테스트", tool="test", plan_id="p1")
        updated = todo.with_status(TodoStatus.IN_PROGRESS)

        assert todo.status == TodoStatus.PENDING  # 원본 불변
        assert updated.status == TodoStatus.IN_PROGRESS

    def test_with_result():
        """결과 설정 메서드"""
        todo = TodoItem(task="테스트", tool="test", plan_id="p1")
        updated = todo.with_result({"data": "result"})

        assert updated.result == {"data": "result"}
        assert updated.status == TodoStatus.COMPLETED

    def test_with_error():
        """에러 설정 메서드"""
        todo = TodoItem(task="테스트", tool="test", plan_id="p1")
        updated = todo.with_error("실패 사유")

        assert updated.error == "실패 사유"
        assert updated.status == TodoStatus.FAILED

    def test_depends_on():
        """의존성 설정"""
        todo = TodoItem(
            task="전처리",
            tool="preprocessor",
            plan_id="p1",
            depends_on=["todo-001", "todo-002"]
        )
        assert len(todo.depends_on) == 2
```

#### test_plan.py (V2 업데이트)

```python
class TestPlan:
    """Plan 테스트 (V2)"""

    def test_create_plan():
        """Plan 생성"""
        plan = Plan(
            session_id="session-001",
            intent_summary="감성 분석",
            todos=[]
        )
        assert plan.status == PlanStatus.DRAFT
        assert plan.version == 1

    def test_dependency_graph():
        """의존성 그래프"""
        todos = [
            TodoItem(id="t1", task="수집", tool="collector", plan_id="p1"),
            TodoItem(id="t2", task="전처리", tool="preprocessor", plan_id="p1", depends_on=["t1"]),
            TodoItem(id="t3", task="분석", tool="analyzer", plan_id="p1", depends_on=["t2"]),
        ]
        plan = Plan(session_id="s1", todos=todos)

        graph = plan.build_dependency_graph()
        assert graph["t2"] == ["t1"]
        assert graph["t3"] == ["t2"]

    def test_cycle_detection():
        """순환 의존성 탐지"""
        todos = [
            TodoItem(id="t1", task="A", tool="x", plan_id="p1", depends_on=["t2"]),
            TodoItem(id="t2", task="B", tool="x", plan_id="p1", depends_on=["t1"]),
        ]
        plan = Plan(session_id="s1", todos=todos)

        with pytest.raises(ValueError, match="cycle"):
            plan.validate_dependencies()

    def test_get_ready_todos():
        """실행 가능한 Todo 조회"""
        todos = [
            TodoItem(id="t1", task="A", tool="x", plan_id="p1", status=TodoStatus.COMPLETED),
            TodoItem(id="t2", task="B", tool="x", plan_id="p1", depends_on=["t1"]),
            TodoItem(id="t3", task="C", tool="x", plan_id="p1", depends_on=["t2"]),
        ]
        plan = Plan(session_id="s1", todos=todos)

        ready = plan.get_ready_todos()
        assert len(ready) == 1
        assert ready[0].id == "t2"  # t1 완료 → t2 실행 가능

    def test_topological_sort():
        """위상 정렬"""
        todos = [
            TodoItem(id="t3", task="C", tool="x", plan_id="p1", depends_on=["t1", "t2"]),
            TodoItem(id="t1", task="A", tool="x", plan_id="p1"),
            TodoItem(id="t2", task="B", tool="x", plan_id="p1", depends_on=["t1"]),
        ]
        plan = Plan(session_id="s1", todos=todos)

        sorted_ids = plan.topological_sort()
        assert sorted_ids.index("t1") < sorted_ids.index("t2")
        assert sorted_ids.index("t2") < sorted_ids.index("t3")
```

### 3.3 Schemas

#### test_cognitive.py

```python
class TestCognitiveSchemas:
    """Cognitive Layer 스키마 테스트"""

    def test_cognitive_input():
        """CognitiveInput 검증"""
        input_data = CognitiveInput(
            user_input="라네즈 리뷰 분석해줘",
            session_id="s1",
            language="ko"
        )
        assert input_data.user_input == "라네즈 리뷰 분석해줘"

    def test_cognitive_output():
        """CognitiveOutput 검증"""
        output = CognitiveOutput(
            intent=Intent(...),
            entities=[Entity(...)],
            requires_clarification=False,
            context_summary="브랜드 감성 분석 요청"
        )

    def test_output_serialization():
        """직렬화/역직렬화"""
```

### 3.4 States & Reducers

#### test_reducers.py

```python
class TestTodoReducer:
    """todo_reducer 테스트"""

    def test_merge_todos():
        """Todo 병합 (ID 기반)"""
        existing = [
            {"id": "t1", "status": "pending"},
            {"id": "t2", "status": "pending"},
        ]
        new = [
            {"id": "t1", "status": "completed"},  # 업데이트
            {"id": "t3", "status": "pending"},    # 추가
        ]

        result = todo_reducer(existing, new)

        assert len(result) == 3
        assert result[0]["status"] == "completed"  # t1 업데이트됨

class TestResultsReducer:
    """results_reducer 테스트"""

    def test_merge_results():
        """결과 병합"""
        existing = {"t1": {"data": "a"}}
        new = {"t2": {"data": "b"}}

        result = results_reducer(existing, new)

        assert "t1" in result
        assert "t2" in result
```

### 3.5 Cognitive Layer

#### test_classifier.py

```python
class TestIntentClassifier:
    """IntentClassifier 테스트"""

    @pytest.fixture
    def classifier(self):
        return IntentClassifier()

    async def test_classify_analysis_intent(self, classifier):
        """분석 의도 분류"""
        result = await classifier.classify("라네즈 리뷰 감성 분석해줘")
        assert result.domain == IntentDomain.ANALYSIS

    async def test_classify_content_intent(self, classifier):
        """콘텐츠 생성 의도 분류"""
        result = await classifier.classify("마케팅 보고서 작성해줘")
        assert result.domain == IntentDomain.CONTENT

    async def test_confidence_score(self, classifier):
        """신뢰도 점수"""
        result = await classifier.classify("명확한 요청")
        assert 0.0 <= result.confidence <= 1.0

    async def test_ambiguous_input(self, classifier):
        """모호한 입력"""
        result = await classifier.classify("해줘")
        assert result.confidence < 0.5
```

#### test_extractor.py

```python
class TestEntityExtractor:
    """EntityExtractor 테스트"""

    async def test_extract_brand(self, extractor):
        """브랜드 엔티티 추출"""
        entities = await extractor.extract("라네즈 리뷰 분석")
        brand = next((e for e in entities if e.type == "brand"), None)
        assert brand is not None
        assert brand.value == "라네즈"

    async def test_extract_date_range(self, extractor):
        """날짜 범위 추출"""
        entities = await extractor.extract("지난 달 데이터 분석")
        date = next((e for e in entities if e.type == "date_range"), None)
        assert date is not None

    async def test_normalize_entity(self, extractor):
        """엔티티 정규화"""
        # "라네즈" = "LANEIGE" 정규화 확인
```

### 3.6 Planning Layer

#### test_dependency.py

```python
class TestDependencyResolver:
    """DependencyResolver 테스트"""

    def test_build_dag(self, resolver):
        """DAG 빌드"""

    def test_topological_sort(self, resolver):
        """위상 정렬"""

    def test_detect_cycle(self, resolver):
        """사이클 탐지"""
        with pytest.raises(CycleDetectedError):
            resolver.validate(cyclic_graph)

    def test_get_execution_order(self, resolver):
        """실행 순서 결정"""
```

### 3.7 Execution Layer

#### test_strategy.py

```python
class TestStrategyDecider:
    """StrategyDecider 테스트"""

    def test_single_strategy(self, decider):
        """SINGLE 전략 - Todo 1개"""
        strategy = decider.decide([todo1])
        assert strategy == ExecutionStrategy.SINGLE

    def test_sequential_strategy(self, decider):
        """SEQUENTIAL 전략 - 의존성 체인"""
        strategy = decider.decide([todo1, todo2_depends_on_1])
        assert strategy == ExecutionStrategy.SEQUENTIAL

    def test_parallel_strategy(self, decider):
        """PARALLEL 전략 - 독립 Todo"""
        strategy = decider.decide([independent_todos])
        assert strategy == ExecutionStrategy.PARALLEL
```

### 3.8 Workflow Managers

#### test_hitl_manager.py

```python
class TestHITLManager:
    """HITLManager 테스트"""

    async def test_create_request(self, manager):
        """요청 생성"""
        request = manager.create_request(
            session_id="s1",
            request_type=HITLRequestType.APPROVAL,
            message="Plan 승인 요청"
        )
        assert request.request_id is not None

    async def test_wait_for_response_timeout(self, manager):
        """응답 대기 타임아웃"""
        request = manager.create_request(...)
        response = await manager.wait_for_response(
            request.request_id,
            timeout=0.1
        )
        assert response is None

    async def test_submit_response(self, manager):
        """응답 제출"""
        request = manager.create_request(...)

        # 별도 태스크에서 응답 제출
        asyncio.create_task(
            submit_after_delay(manager, request.request_id, "approve")
        )

        response = await manager.wait_for_response(request.request_id)
        assert response.action == "approve"

class TestPlanEditor:
    """PlanEditor 테스트"""

    async def test_parse_remove_instruction(self, editor):
        """삭제 명령 파싱"""
        parsed = await editor.parse_instruction(
            "2번 작업 삭제해줘",
            plan
        )
        assert parsed["action"] == "remove"

    async def test_apply_add_todo(self, editor):
        """Todo 추가 적용"""
        new_plan, change = await editor.apply_edit(
            plan,
            {"action": "add", "params": {"task": "새 작업", "tool": "test"}},
            "새 작업 추가"
        )
        assert len(new_plan.todos) == len(plan.todos) + 1
```

---

## 4. Integration Tests

### 4.1 Graph Flow

#### test_graph_build.py

```python
class TestGraphBuild:
    """그래프 빌드 테스트"""

    def test_build_graph():
        """StateGraph 빌드"""
        graph = build_graph()
        assert graph is not None

    async def test_create_agent():
        """Agent 생성"""
        agent = await create_agent()
        assert agent is not None

    def test_nodes_registered():
        """노드 등록 확인"""
        graph = build_graph()
        nodes = graph.nodes

        assert "cognitive" in nodes
        assert "planning" in nodes
        assert "execution" in nodes
        assert "response" in nodes
```

#### test_layer_flow.py

```python
class TestLayerFlow:
    """레이어 플로우 테스트"""

    async def test_cognitive_to_planning():
        """Cognitive → Planning 전환"""
        agent = await create_agent()
        initial_state = create_initial_state(
            session_id="test",
            user_input="감성 분석해줘"
        )

        # cognitive 노드까지만 실행
        result = await agent.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": "test"}}
        )

        assert "cognitive_result" in result

    async def test_full_flow_mock():
        """전체 플로우 (Mock Executor)"""
        # Mock으로 전체 플로우 테스트
```

#### test_hitl_interrupt.py

```python
class TestHITLInterrupt:
    """HITL Interrupt 테스트"""

    async def test_planning_interrupt():
        """Planning 단계 interrupt"""
        agent = await create_agent()
        config = {"configurable": {"thread_id": "test"}}

        # interrupt_before=["planning"] 설정으로
        # planning 전에 중단되는지 확인

    async def test_resume_after_approval():
        """승인 후 재개"""
        # interrupt 후 Command(resume=...) 테스트
```

### 4.2 API Integration

#### test_agent_api.py

```python
class TestAgentAPI:
    """Agent API 테스트"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_run_sync(self, client):
        """POST /api/agent/run"""
        response = client.post("/api/agent/run", json={
            "message": "테스트 쿼리",
            "language": "ko"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "session_id" in data

    def test_run_async(self, client):
        """POST /api/agent/run-async"""
        response = client.post("/api/agent/run-async", json={
            "message": "테스트",
            "language": "ko"
        })

        assert response.status_code == 200
        data = response.json()
        assert "websocket_url" in data

    def test_get_status(self, client):
        """GET /api/agent/status/{session_id}"""

    def test_stop_agent(self, client):
        """POST /api/agent/stop/{session_id}"""
```

#### test_health_api.py

```python
class TestHealthAPI:
    """Health API 테스트"""

    def test_health_check(self, client):
        """GET /health"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_readiness_check(self, client):
        """GET /health/ready"""
        response = client.get("/health/ready")
        data = response.json()
        assert "checks" in data

    def test_liveness_check(self, client):
        """GET /health/live"""

    def test_metrics(self, client):
        """GET /health/metrics"""
```

### 4.3 WebSocket

#### test_websocket.py

```python
class TestWebSocket:
    """WebSocket 테스트"""

    async def test_connect(self):
        """연결 성공"""
        async with websocket_connect("/api/agent/ws/test") as ws:
            msg = await ws.receive_json()
            assert msg["type"] == "connected"

    async def test_receive_layer_events(self):
        """레이어 이벤트 수신"""

    async def test_send_approve(self):
        """승인 메시지 전송"""

    async def test_send_pause_resume(self):
        """일시정지/재개"""
```

---

## 5. E2E Tests

### 5.1 Full Pipeline

```python
class TestFullPipeline:
    """전체 파이프라인 E2E"""

    async def test_simple_query_flow():
        """단순 쿼리 → 응답"""
        # 1. POST /api/agent/run
        # 2. Cognitive → Planning → Execution → Response
        # 3. 응답 검증

    async def test_with_approval():
        """승인 포함 플로우"""
        # 1. POST /api/agent/run-async
        # 2. WebSocket 연결
        # 3. hitl_request 수신
        # 4. approve 전송
        # 5. complete 수신
```

### 5.2 HITL Scenarios

```python
class TestHITLScenarios:
    """HITL 시나리오 테스트"""

    async def test_approve_flow():
        """승인 시나리오"""

    async def test_reject_flow():
        """거부 시나리오"""

    async def test_modify_flow():
        """수정 시나리오"""
        # "2번 작업 삭제해줘" → Plan 수정 → 재개

    async def test_pause_resume():
        """일시정지 → 재개"""

    async def test_clarification():
        """명확화 질문 → 응답"""
```

### 5.3 Error Recovery

```python
class TestErrorRecovery:
    """에러 복구 테스트"""

    async def test_timeout_recovery():
        """타임아웃 복구"""

    async def test_llm_error_retry():
        """LLM 에러 재시도"""

    async def test_graceful_degradation():
        """우아한 저하"""
```

---

## 6. 테스트 Fixtures (conftest.py 업데이트)

```python
"""V2 테스트 설정 및 공통 fixture"""

import pytest
import asyncio
from datetime import datetime

# === Models ===

@pytest.fixture
def sample_entity():
    """샘플 Entity"""
    from app.dream_agent.models import Entity
    return Entity(type="brand", value="라네즈", confidence=0.95)

@pytest.fixture
def sample_intent(sample_entity):
    """샘플 Intent"""
    from app.dream_agent.models import Intent, IntentDomain
    return Intent(
        domain=IntentDomain.ANALYSIS,
        category="sentiment",
        confidence=0.85,
        entities=[sample_entity],
        summary="브랜드 감성 분석"
    )

@pytest.fixture
def sample_todo():
    """샘플 TodoItem"""
    from app.dream_agent.models import TodoItem
    return TodoItem(
        task="리뷰 데이터 수집",
        tool="collector",
        plan_id="plan-001",
        priority=5
    )

@pytest.fixture
def sample_todos():
    """샘플 TodoItem 리스트 (의존성 포함)"""
    from app.dream_agent.models import TodoItem
    return [
        TodoItem(id="t1", task="수집", tool="collector", plan_id="p1"),
        TodoItem(id="t2", task="전처리", tool="preprocessor", plan_id="p1", depends_on=["t1"]),
        TodoItem(id="t3", task="분석", tool="analyzer", plan_id="p1", depends_on=["t2"]),
    ]

@pytest.fixture
def sample_plan(sample_todos):
    """샘플 Plan"""
    from app.dream_agent.models import Plan
    return Plan(
        session_id="test-session",
        intent_summary="감성 분석",
        todos=sample_todos
    )

# === Schemas ===

@pytest.fixture
def sample_cognitive_input():
    """샘플 CognitiveInput"""
    from app.dream_agent.schemas import CognitiveInput
    return CognitiveInput(
        user_input="라네즈 리뷰 감성 분석해줘",
        session_id="test-session",
        language="ko"
    )

# === State ===

@pytest.fixture
def sample_initial_state():
    """샘플 초기 AgentState"""
    from app.dream_agent.states import create_initial_state
    return create_initial_state(
        session_id="test-session",
        user_input="테스트 쿼리",
        language="ko"
    )

# === API Client ===

@pytest.fixture
def client():
    """FastAPI TestClient"""
    from fastapi.testclient import TestClient
    from api.main import app
    return TestClient(app)

@pytest.fixture
async def async_client():
    """Async HTTP Client"""
    import httpx
    async with httpx.AsyncClient(base_url="http://test") as ac:
        yield ac

# === Mocks ===

@pytest.fixture
def mock_llm_client(mocker):
    """Mock LLM Client"""
    mock = mocker.patch("app.dream_agent.llm_manager.get_llm_client")
    mock.return_value.generate.return_value = "mocked response"
    mock.return_value.generate_json.return_value = {"result": "mocked"}
    return mock
```

---

## 7. 실행 방법

### 7.1 전체 테스트

```bash
# 전체 실행
pytest tests/ -v

# 커버리지 포함
pytest tests/ --cov=backend --cov-report=html
```

### 7.2 카테고리별 실행

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# E2E tests
pytest tests/e2e/ -v
```

### 7.3 특정 테스트

```bash
# 특정 파일
pytest tests/unit/models/test_todo.py -v

# 특정 클래스
pytest tests/unit/models/test_todo.py::TestTodoItem -v

# 특정 테스트
pytest tests/unit/models/test_todo.py::TestTodoItem::test_with_status -v
```

### 7.4 마커별 실행

```bash
# 느린 테스트 제외
pytest tests/ -v -m "not slow"

# 통합 테스트만
pytest tests/ -v -m integration
```

---

## 8. 우선순위

### 8.1 즉시 필요 (P0)

| 테스트 | 이유 |
|--------|------|
| `test_todo.py` (V2) | 핵심 모델, frozen 검증 |
| `test_plan.py` (V2) | 의존성/사이클 탐지 |
| `test_reducers.py` | 상태 병합 로직 |
| `test_graph_build.py` | 그래프 빌드 확인 |
| `test_health_api.py` | 서버 기동 확인 |

### 8.2 중요 (P1)

| 테스트 | 이유 |
|--------|------|
| `test_classifier.py` | 의도 분류 정확도 |
| `test_hitl_manager.py` | HITL 플로우 |
| `test_websocket.py` | 실시간 통신 |
| `test_layer_flow.py` | 레이어 전환 |

### 8.3 권장 (P2)

| 테스트 | 이유 |
|--------|------|
| `test_full_pipeline.py` | E2E 검증 |
| `test_error_recovery.py` | 안정성 |
| 나머지 Unit Tests | 커버리지 |

---

## 9. 체크리스트

### 9.1 테스트 작성 전

- [ ] conftest.py V2 fixture 업데이트
- [ ] 기존 V1 테스트 파일 정리/제거
- [ ] pytest 설정 (pytest.ini / pyproject.toml)

### 9.2 P0 테스트

- [ ] test_todo.py (V2 frozen 모델)
- [ ] test_plan.py (의존성, 사이클)
- [ ] test_reducers.py
- [ ] test_graph_build.py
- [ ] test_health_api.py

### 9.3 P1 테스트

- [ ] test_classifier.py
- [ ] test_hitl_manager.py
- [ ] test_websocket.py
- [ ] test_layer_flow.py

### 9.4 검증 완료 기준

- [ ] Unit Test 커버리지 > 80%
- [ ] Integration Test 통과
- [ ] E2E 주요 시나리오 통과
- [ ] 서버 기동 성공 (`python run_server.py`)
- [ ] Health Check 정상 (`/health/ready`)

---

## 10. 참고

| 문서 | 경로 |
|------|------|
| V2 구현 보고서 | `docs/V2_IMPLEMENTATION_REPORT.md` |
| V2 아키텍처 | `reports_mind_dream/version_2/v2_architecture_260205.md` |
| 기존 테스트 | `tests/unit/models/test_todo.py` (V1 기반, 업데이트 필요) |
