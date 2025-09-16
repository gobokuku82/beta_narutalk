# LangGraph 0.6.7 고도화 코딩 규칙 (ADVANCED_RULES.md)

## 🎯 목적
LangGraph 0.6.7 최신 버전을 활용한 엔터프라이즈급 멀티 에이전트 챗봇 개발 시 준수해야 할 고급 코딩 규칙과 베스트 프랙티스를 정의합니다.

---

## 📋 핵심 원칙

### PRINCIPLE 1: Type Safety First
모든 코드는 타입 안전성을 최우선으로 고려하여 작성합니다.

### PRINCIPLE 2: Context Over Config
config['configurable'] 대신 Context API를 사용합니다.

### PRINCIPLE 3: Async by Default
모든 I/O 작업은 비동기로 구현합니다.

### PRINCIPLE 4: Error Recovery
모든 에러는 복구 가능하도록 설계합니다.

### PRINCIPLE 5: Observable
모든 중요 작업은 추적 가능해야 합니다.

---

## 🏗️ 아키텍처 규칙

### RULE A1: 모듈 구조

#### A1.1 에이전트 모듈 구조
```python
# ✅ GOOD: 명확한 책임 분리
agents/
├── supervisor/
│   ├── __init__.py
│   ├── orchestrator.py      # 오케스트레이션 로직
│   ├── query_analyzer.py    # 질의 분석
│   ├── plan_processor.py    # 계획 수립
│   └── error_recovery.py    # 에러 복구
├── analysis/
│   ├── __init__.py
│   ├── agent.py            # 에이전트 로직
│   └── tools.py            # 도구 구현

# ❌ BAD: 모든 로직을 한 파일에
agents/
├── supervisor.py           # 1000+ 라인의 거대한 파일
```

#### A1.2 임포트 순서
```python
# ✅ GOOD: 체계적인 임포트
# 1. 표준 라이브러리
import asyncio
import json
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

# 2. 서드파티 - LangChain/LangGraph
from langchain_core.messages import AnyMessage
from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime
from langgraph.types import Send, Command, interrupt

# 3. 서드파티 - 기타
import numpy as np
import pandas as pd
from sqlalchemy import create_engine

# 4. 로컬 모듈
from core.context import AdvancedContext
from core.state import AdvancedState
from tools.sql_tools import SQLQueryTool
```

### RULE A2: 네이밍 컨벤션

#### A2.1 클래스명
```python
# ✅ GOOD: 명확하고 설명적인 이름
class AdvancedQueryAnalyzer:
class ParallelExecutionOrchestrator:
class ComplianceValidationAgent:

# ❌ BAD: 모호하거나 축약된 이름
class QA:  # 무엇의 약자?
class Analyzer:  # 무엇을 분석?
class Agent:  # 어떤 에이전트?
```

#### A2.2 함수/메서드명
```python
# ✅ GOOD: 동사로 시작하는 명확한 이름
async def analyze_query_complexity(query: str) -> float:
def build_dependency_graph(agents: List[str]) -> Dict[str, List[str]]:
async def execute_with_retry(func: callable, max_attempts: int) -> Any:

# ❌ BAD: 명사형 또는 모호한 이름
def complexity(query):  # 복잡도를 어떻게?
def graph(agents):  # 그래프를 어떻게?
def retry(func):  # 무엇을 재시도?
```

---

## 🔧 Context API 고급 규칙

### RULE C1: Context 설계 패턴

#### C1.1 계층적 Context 구조
```python
# ✅ GOOD: 관심사별로 분리된 Context
@dataclass
class BaseContext:
    """기본 컨텍스트"""
    user_id: str
    session_id: str
    trace_id: str

@dataclass
class SecurityContext:
    """보안 관련 컨텍스트"""
    user_role: str
    permissions: List[str]
    approval_required: Dict[str, bool]

@dataclass
class ExecutionContext:
    """실행 관련 컨텍스트"""
    model_provider: str
    model_name: str
    max_parallel_agents: int
    enable_caching: bool

@dataclass
class AdvancedContext(BaseContext, SecurityContext, ExecutionContext):
    """통합 컨텍스트"""
    pass

# ❌ BAD: 하나의 거대한 Context
@dataclass
class GiantContext:
    # 100개 이상의 필드...
    pass
```

#### C1.2 Context 유효성 검증
```python
# ✅ GOOD: 생성 시 유효성 검증
@dataclass
class ValidatedContext:
    user_id: str
    model_name: str
    temperature: float
    
    def __post_init__(self):
        if not self.user_id:
            raise ValueError("user_id is required")
        
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("temperature must be between 0 and 2")
        
        valid_models = ["gpt-4o", "claude-3-opus", "gemini-pro"]
        if self.model_name not in valid_models:
            raise ValueError(f"Invalid model: {self.model_name}")
```

### RULE C2: Runtime 사용 패턴

#### C2.1 Runtime 타입 명시
```python
# ✅ GOOD: 항상 타입 파라미터 명시
async def process_node(
    state: AdvancedState,
    runtime: Runtime[AdvancedContext]  # 타입 파라미터 필수
) -> Dict[str, Any]:
    context = runtime.context  # 타입 안전
    store = runtime.store
    
# ❌ BAD: 타입 파라미터 누락
async def process_node(
    state: AdvancedState,
    runtime: Runtime  # 타입 정보 없음
):
    pass
```

#### C2.2 Store 접근 패턴
```python
# ✅ GOOD: None 체크 후 접근
async def access_store(runtime: Runtime[AdvancedContext]):
    if runtime.store:
        # namespace 사용
        user_data = await runtime.store.get(("users", runtime.context.user_id))
        
        # 존재 여부 확인
        if user_data:
            return user_data
        else:
            return await fetch_from_database(runtime.context.user_id)
    
    # Store 없을 때 폴백
    return get_default_user_data()

# ❌ BAD: 직접 접근
async def bad_store_access(runtime):
    return runtime.store.get(("key",))  # Store가 None일 수 있음
```

---

## 🤖 에이전트 구현 규칙

### RULE E1: 에이전트 클래스 구조

#### E1.1 표준 에이전트 템플릿
```python
# ✅ GOOD: 표준화된 에이전트 구조
from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """모든 에이전트의 기본 클래스"""
    
    def __init__(self, name: str):
        self.name = name
        self.tools = []
        self.metrics = AgentMetrics(name)
    
    @abstractmethod
    async def process(
        self,
        state: AdvancedState,
        runtime: Runtime[AdvancedContext]
    ) -> Dict[str, Any]:
        """에이전트 처리 로직"""
        pass
    
    async def execute(
        self,
        state: AdvancedState,
        runtime: Runtime[AdvancedContext]
    ) -> Dict[str, Any]:
        """표준 실행 패턴"""
        # 사전 처리
        await self._pre_process(state, runtime)
        
        # 메트릭 시작
        with self.metrics.track_execution():
            try:
                # 메인 처리
                result = await self.process(state, runtime)
                
                # 사후 처리
                result = await self._post_process(result, runtime)
                
                return result
                
            except Exception as e:
                # 에러 처리
                return await self._handle_error(e, state, runtime)

class AnalysisAgent(BaseAgent):
    """분석 에이전트 구현"""
    
    def __init__(self):
        super().__init__("analysis")
        self.tools = [SQLQueryTool(), DataAnalyzer()]
    
    async def process(
        self,
        state: AdvancedState,
        runtime: Runtime[AdvancedContext]
    ) -> Dict[str, Any]:
        # 구체적인 분석 로직
        pass
```

### RULE E2: 도구 관리

#### E2.1 동적 도구 선택
```python
# ✅ GOOD: 컨텍스트 기반 동적 도구 선택
class DynamicToolSelector:
    def select_tools(
        self,
        agent_name: str,
        runtime: Runtime[AdvancedContext]
    ) -> List[Tool]:
        """컨텍스트에 따른 도구 선택"""
        
        # 기본 도구
        tools = self._get_base_tools(agent_name)
        
        # 권한 기반 필터링
        tools = self._filter_by_permissions(
            tools,
            runtime.context.permissions
        )
        
        # 활성화된 도구만 선택
        tools = [
            tool for tool in tools
            if tool.name in runtime.context.enabled_tools
        ]
        
        # 언어별 도구 추가
        if runtime.context.language == "ko":
            tools.extend(self._get_korean_tools())
        
        return tools

# ❌ BAD: 정적 도구 할당
def get_tools(agent_name):
    return ALL_TOOLS  # 모든 도구를 항상 사용
```

#### E2.2 도구 레지스트리
```python
# ✅ GOOD: 중앙 집중식 도구 관리
class ToolRegistry:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
        return cls._instance
    
    def register(self, tool: Tool, categories: List[str]):
        """도구 등록"""
        for category in categories:
            if category not in self._tools:
                self._tools[category] = []
            self._tools[category].append(tool)
    
    def get_tools(
        self,
        categories: List[str],
        context: AdvancedContext
    ) -> List[Tool]:
        """카테고리별 도구 조회"""
        tools = []
        for category in categories:
            tools.extend(self._tools.get(category, []))
        
        # 컨텍스트 필터링
        return [
            tool for tool in tools
            if self._is_tool_allowed(tool, context)
        ]
```

---

## 🔄 워크플로우 규칙

### RULE W1: 그래프 구성

#### W1.1 그래프 빌더 패턴
```python
# ✅ GOOD: 체계적인 그래프 구성
class GraphBuilder:
    def build_graph(self) -> CompiledGraph:
        """그래프 구성 및 컴파일"""
        
        # 1. 빌더 초기화
        builder = StateGraph(
            state_schema=AdvancedState,
            context_schema=AdvancedContext
        )
        
        # 2. 노드 추가 (그룹별)
        self._add_supervisor_nodes(builder)
        self._add_agent_nodes(builder)
        self._add_utility_nodes(builder)
        
        # 3. 엣지 연결
        self._connect_edges(builder)
        
        # 4. 조건부 라우팅
        self._add_conditional_routing(builder)
        
        # 5. 컴파일 (durability 설정)
        return builder.compile(
            checkpointer=self._get_checkpointer(),
            store=self._get_store(),
            durability="async"  # 프로덕션: "sync"
        )
    
    def _add_supervisor_nodes(self, builder: StateGraph):
        """Supervisor 노드 추가"""
        builder.add_node("analyze_query", analyze_query_node)
        builder.add_node("create_plan", create_plan_node)
        builder.add_node("route_agents", route_agents_node)

# ❌ BAD: 무계획적 그래프 구성
builder = StateGraph(State)
builder.add_node("node1", func1)
builder.add_edge("node1", "node2")
# ... 수백 줄의 반복적인 코드
```

#### W1.2 조건부 라우팅
```python
# ✅ GOOD: 명확한 라우팅 로직
def intelligent_router(state: AdvancedState) -> str:
    """지능형 라우팅 결정"""
    
    # 에러 상태 체크
    if state["errors"]:
        return "error_recovery"
    
    # 인터럽트 체크
    if state["interrupt_data"]:
        return "handle_interrupt"
    
    # 완료 체크
    if all_agents_completed(state):
        return "aggregate_results"
    
    # 다음 에이전트 결정
    next_agent = get_next_agent(state)
    return f"{next_agent}_agent"

builder.add_conditional_edges(
    "route_agents",
    intelligent_router,
    {
        "error_recovery": "error_recovery_node",
        "handle_interrupt": "interrupt_handler",
        "aggregate_results": "result_aggregator",
        "analysis_agent": "analysis_node",
        "search_agent": "search_node"
    }
)
```

### RULE W2: 병렬 실행

#### W2.1 Send API 사용
```python
# ✅ GOOD: Send를 통한 병렬 실행
async def parallel_execution_node(
    state: AdvancedState,
    runtime: Runtime[AdvancedContext]
) -> List[Send]:
    """병렬 에이전트 실행"""
    
    sends = []
    parallel_tasks = identify_parallel_tasks(state)
    
    for task in parallel_tasks:
        # 각 태스크별 Send 생성
        sends.append(
            Send(
                task["target_node"],
                {
                    "task_id": task["id"],
                    "task_data": task["data"],
                    "parent_state": state,
                    "timeout": calculate_timeout(task)
                }
            )
        )
    
    return sends

# ❌ BAD: 순차 실행으로 병렬 작업 처리
for agent in agents:
    result = await execute_agent(agent)  # 하나씩 순차 실행
```

#### W2.2 Map-Reduce 패턴
```python
# ✅ GOOD: Map-Reduce 구현
class MapReduceOrchestrator:
    async def map_phase(
        self,
        state: AdvancedState,
        runtime: Runtime[AdvancedContext]
    ) -> List[Send]:
        """Map 단계: 작업 분산"""
        
        data_chunks = self._split_data(state["data"])
        
        return [
            Send(
                "worker_node",
                {
                    "chunk_id": i,
                    "chunk_data": chunk,
                    "operation": state["map_operation"]
                }
            )
            for i, chunk in enumerate(data_chunks)
        ]
    
    async def reduce_phase(
        self,
        state: AdvancedState,
        runtime: Runtime[AdvancedContext]
    ) -> Dict[str, Any]:
        """Reduce 단계: 결과 집계"""
        
        results = state["agent_results"]
        
        # 결과 검증
        validated_results = self._validate_results(results)
        
        # 집계
        aggregated = self._aggregate(
            validated_results,
            state["reduce_operation"]
        )
        
        return {"final_result": aggregated}
```

---

## 🚨 에러 처리 규칙

### RULE R1: 에러 복구 전략

#### R1.1 계층적 에러 처리
```python
# ✅ GOOD: 다층 방어 전략
class LayeredErrorHandler:
    async def handle_with_recovery(
        self,
        operation: callable,
        state: AdvancedState,
        runtime: Runtime[AdvancedContext]
    ) -> Any:
        """계층적 에러 처리"""
        
        # Layer 1: 기본 재시도
        try:
            return await operation()
        except RecoverableError as e:
            # Layer 2: 복구 가능한 에러
            return await self._recover_from_error(e, state)
        except TimeoutError:
            # Layer 3: 타임아웃 처리
            return await self._handle_timeout(state, runtime)
        except ValidationError as e:
            # Layer 4: 검증 실패
            return await self._fix_validation(e, state)
        except Exception as e:
            # Layer 5: 최종 폴백
            return await self._final_fallback(e, state, runtime)
    
    async def _recover_from_error(
        self,
        error: RecoverableError,
        state: AdvancedState
    ) -> Any:
        """에러별 복구 전략"""
        
        strategies = {
            "missing_data": self._fetch_alternative_data,
            "api_failure": self._use_cached_response,
            "model_error": self._switch_model
        }
        
        strategy = strategies.get(
            error.error_type,
            self._default_recovery
        )
        
        return await strategy(error, state)
```

#### R1.2 Circuit Breaker 패턴
```python
# ✅ GOOD: Circuit Breaker 구현
class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = {}
        self.last_failure_time = {}
    
    async def call(
        self,
        service_name: str,
        operation: callable
    ) -> Any:
        """Circuit Breaker로 보호된 호출"""
        
        # 회로 차단 상태 확인
        if self._is_open(service_name):
            if not self._should_attempt_reset(service_name):
                raise CircuitOpenError(f"{service_name} is unavailable")
        
        try:
            # 작업 실행
            result = await operation()
            
            # 성공 시 카운터 리셋
            self._on_success(service_name)
            
            return result
            
        except Exception as e:
            # 실패 기록
            self._on_failure(service_name)
            
            # 임계값 도달 시 회로 차단
            if self.failures[service_name] >= self.failure_threshold:
                self._open_circuit(service_name)
            
            raise
```

---

## 🔄 Human-in-the-Loop 규칙

### RULE H1: Interrupt 패턴

#### H1.1 조건부 Interrupt
```python
# ✅ GOOD: 컨텍스트 기반 조건부 인터럽트
async def conditional_interrupt_node(
    state: AdvancedState,
    runtime: Runtime[AdvancedContext]
) -> Dict[str, Any]:
    """조건부 인터럽트 처리"""
    
    operation = state["pending_operation"]
    
    # 인터럽트 필요 여부 판단
    should_interrupt = (
        runtime.context.interrupt_mode != "none" and
        operation["type"] in runtime.context.approval_required and
        runtime.context.approval_required[operation["type"]]
    )
    
    if should_interrupt:
        # 상세한 인터럽트 정보 제공
        interrupt_data = {
            "reason": f"Approval required for {operation['type']}",
            "operation": operation,
            "risk_assessment": assess_risk(operation),
            "recommendations": generate_recommendations(operation),
            "options": [
                {"value": "approve", "label": "승인"},
                {"value": "modify", "label": "수정"},
                {"value": "reject", "label": "거부"}
            ],
            "timeout": 300  # 5분 타임아웃
        }
        
        # 사용자 응답 대기
        user_response = interrupt(interrupt_data)
        
        # 응답 처리
        return process_user_response(user_response, operation)
    
    # 인터럽트 불필요 시 직접 실행
    return await execute_operation(operation)

# ❌ BAD: 무조건적 인터럽트
def bad_interrupt():
    interrupt("Continue?")  # 정보 부족
```

#### H1.2 Command 패턴
```python
# ✅ GOOD: Command를 통한 재개
async def resume_with_command(
    session_id: str,
    user_response: Dict[str, Any]
) -> None:
    """Command를 통한 워크플로우 재개"""
    
    # Command 생성
    command = Command(
        resume=user_response["value"],  # 사용자 선택
        update={
            "user_feedback": user_response.get("feedback"),
            "modified_params": user_response.get("modifications")
        },
        goto=determine_next_node(user_response)  # 다음 노드 결정
    )
    
    # 그래프 재개
    config = {
        "configurable": {
            "thread_id": session_id
        }
    }
    
    await graph.ainvoke(command, config)
```

---

## 📊 성능 최적화 규칙

### RULE P1: 캐싱 전략

#### P1.1 다층 캐싱
```python
# ✅ GOOD: 다층 캐싱 시스템
class MultiLayerCache:
    def __init__(self):
        # L1: 메모리 캐시 (빠름, 작음)
        self.l1_cache = LRUCache(maxsize=100)
        
        # L2: Redis 캐시 (중간, 중간)
        self.l2_cache = RedisCache(ttl=3600)
        
        # L3: 데이터베이스 캐시 (느림, 큼)
        self.l3_cache = DatabaseCache()
    
    async def get(self, key: str) -> Optional[Any]:
        """계층적 캐시 조회"""
        
        # L1 체크
        if value := self.l1_cache.get(key):
            return value
        
        # L2 체크
        if value := await self.l2_cache.get(key):
            # L1에 승급
            self.l1_cache.set(key, value)
            return value
        
        # L3 체크
        if value := await self.l3_cache.get(key):
            # L1, L2에 승급
            await self.l2_cache.set(key, value)
            self.l1_cache.set(key, value)
            return value
        
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """모든 레벨에 캐시 설정"""
        
        # 중요도에 따라 캐시 레벨 결정
        if is_hot_data(key):
            self.l1_cache.set(key, value)
        
        await self.l2_cache.set(key, value, ttl)
        
        if is_persistent_data(key):
            await self.l3_cache.set(key, value)
```

#### P1.2 스마트 캐시 무효화
```python
# ✅ GOOD: 지능형 캐시 무효화
class SmartCacheInvalidator:
    def __init__(self):
        self.dependency_graph = {}
        self.cache_metadata = {}
    
    async def invalidate_with_dependencies(
        self,
        key: str,
        cascade: bool = True
    ):
        """의존성 기반 캐시 무효화"""
        
        # 직접 무효화
        await self._invalidate_key(key)
        
        if cascade:
            # 의존 캐시도 무효화
            dependent_keys = self.dependency_graph.get(key, [])
            for dep_key in dependent_keys:
                await self._invalidate_key(dep_key)
        
        # 메타데이터 업데이트
        self.cache_metadata[key] = {
            "invalidated_at": datetime.now(),
            "reason": "manual_invalidation"
        }
```

### RULE P2: 리소스 관리

#### P2.1 커넥션 풀링
```python
# ✅ GOOD: 효율적인 커넥션 풀 관리
class ConnectionPoolManager:
    def __init__(self):
        self.pools = {}
        self.metrics = PoolMetrics()
    
    async def get_connection(
        self,
        service: str,
        runtime: Runtime[AdvancedContext]
    ):
        """커넥션 풀에서 연결 획득"""
        
        # 풀 생성 또는 조회
        if service not in self.pools:
            self.pools[service] = await self._create_pool(
                service,
                runtime.context
            )
        
        pool = self.pools[service]
        
        # 헬스 체크
        if not await pool.is_healthy():
            await pool.reconnect()
        
        # 커넥션 획득 (타임아웃 설정)
        async with asyncio.timeout(5.0):
            conn = await pool.acquire()
        
        # 메트릭 기록
        self.metrics.record_acquisition(service)
        
        return conn
    
    async def _create_pool(
        self,
        service: str,
        context: AdvancedContext
    ):
        """서비스별 최적화된 풀 생성"""
        
        pool_config = {
            "min_size": 2,
            "max_size": 10,
            "max_idle_time": 300,
            "validation_query": "SELECT 1"
        }
        
        # 서비스별 설정 조정
        if service == "structured_db":
            pool_config["max_size"] = 20
        elif service == "vector_db":
            pool_config["max_size"] = 5
        
        return await create_pool(**pool_config)
```

---

## 🔐 보안 규칙

### RULE S1: 데이터 보호

#### S1.1 민감 정보 마스킹
```python
# ✅ GOOD: 자동 마스킹 시스템
class DataMasker:
    SENSITIVE_FIELDS = [
        "password", "api_key", "token",
        "ssn", "credit_card", "phone"
    ]
    
    def mask_sensitive_data(
        self,
        data: Dict[str, Any],
        level: str = "partial"
    ) -> Dict[str, Any]:
        """민감 정보 마스킹"""
        
        masked = {}
        for key, value in data.items():
            if self._is_sensitive(key):
                masked[key] = self._mask_value(value, level)
            elif isinstance(value, dict):
                masked[key] = self.mask_sensitive_data(value, level)
            elif isinstance(value, list):
                masked[key] = [
                    self.mask_sensitive_data(item, level)
                    if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                masked[key] = value
        
        return masked
    
    def _mask_value(self, value: str, level: str) -> str:
        """값 마스킹"""
        
        if level == "full":
            return "***MASKED***"
        elif level == "partial":
            if len(value) > 4:
                return value[:2] + "*" * (len(value) - 4) + value[-2:]
            return "*" * len(value)
        
        return value
```

#### S1.2 감사 로깅
```python
# ✅ GOOD: 포괄적인 감사 로깅
class AuditLogger:
    def __init__(self):
        self.logger = setup_secure_logger()
        self.masker = DataMasker()
    
    async def log_operation(
        self,
        operation: str,
        runtime: Runtime[AdvancedContext],
        data: Dict[str, Any],
        result: Any = None,
        error: Exception = None
    ):
        """작업 감사 로깅"""
        
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "trace_id": runtime.context.trace_id,
            "user_id": runtime.context.user_id,
            "operation": operation,
            "data": self.masker.mask_sensitive_data(data),
            "status": "success" if not error else "failure"
        }
        
        if result:
            audit_entry["result_summary"] = self._summarize_result(result)
        
        if error:
            audit_entry["error"] = {
                "type": type(error).__name__,
                "message": str(error)
            }
        
        # 비동기 로깅 (메인 플로우 차단 방지)
        asyncio.create_task(
            self._async_log(audit_entry)
        )
```

---

## 🧪 테스트 규칙

### RULE T1: 테스트 구조

#### T1.1 에이전트 테스트
```python
# ✅ GOOD: 포괄적인 에이전트 테스트
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
class TestAnalysisAgent:
    async def test_successful_analysis(self):
        """정상 분석 테스트"""
        # Given
        agent = AnalysisAgent()
        state = create_test_state()
        runtime = create_mock_runtime()
        
        # When
        result = await agent.execute(state, runtime)
        
        # Then
        assert result["status"] == "success"
        assert "analysis_results" in result
        assert len(result["analysis_results"]) > 0
    
    async def test_error_recovery(self):
        """에러 복구 테스트"""
        # Given
        agent = AnalysisAgent()
        state = create_test_state()
        runtime = create_mock_runtime()
        
        # 첫 번째 호출은 실패
        agent.tools[0].execute = AsyncMock(
            side_effect=[Exception("DB Error"), {"data": []}]
        )
        
        # When
        result = await agent.execute(state, runtime)
        
        # Then
        assert result["status"] == "recovered"
        assert agent.tools[0].execute.call_count == 2
    
    @pytest.mark.parametrize("context_type,expected_tools", [
        ("admin", ["sql_query", "admin_analytics"]),
        ("user", ["sql_query"]),
        ("readonly", [])
    ])
    async def test_dynamic_tool_selection(
        self,
        context_type,
        expected_tools
    ):
        """동적 도구 선택 테스트"""
        # Given
        runtime = create_runtime_with_role(context_type)
        tools = DynamicToolSelector().select_tools("analysis", runtime)
        
        # Then
        tool_names = [tool.name for tool in tools]
        assert set(tool_names) == set(expected_tools)
```

#### T1.2 통합 테스트
```python
# ✅ GOOD: End-to-End 통합 테스트
@pytest.mark.integration
class TestWorkflowIntegration:
    async def test_complete_workflow(self):
        """전체 워크플로우 테스트"""
        # Given
        graph = GraphBuilder().build_graph()
        input_state = {
            "messages": [HumanMessage(content="작년 실적 분석해줘")]
        }
        context = AdvancedContext(
            user_id="test_user",
            company_id="test_company",
            session_id="test_session"
        )
        
        # When
        result = await graph.ainvoke(
            input_state,
            context=context
        )
        
        # Then
        assert result["workflow_status"] == "completed"
        assert result["final_response"] is not None
        assert len(result["completed_steps"]) > 0
```

---

## ✅ 체크리스트

### 프로젝트 시작
- [ ] LangGraph 0.6.7 이상 설치
- [ ] Python 3.9 이상 확인
- [ ] 프로젝트 구조 설정
- [ ] Context/State 스키마 정의
- [ ] 기본 에이전트 템플릿 생성

### 개발 중
- [ ] 타입 힌트 100% 적용
- [ ] Runtime[Context] 타입 파라미터 명시
- [ ] 에러 처리 전략 구현
- [ ] 캐싱 전략 적용
- [ ] 보안 규칙 준수

### 배포 전
- [ ] 단위 테스트 커버리지 80% 이상
- [ ] 통합 테스트 완료
- [ ] 성능 테스트 통과
- [ ] 보안 감사 완료
- [ ] 문서화 완성

---

## 🚫 금지 사항

### 절대 하지 말아야 할 것들

1. **구조적 안티패턴**
   - `config['configurable']` 사용 (deprecated)
   - 타입 힌트 없는 함수
   - 1000줄 이상의 단일 파일
   - 순환 의존성

2. **보안 위반**
   - 민감 정보 하드코딩
   - 마스킹 없는 로깅
   - SQL Injection 가능한 쿼리
   - 권한 체크 없는 작업

3. **성능 안티패턴**
   - 동기 I/O in async 함수
   - 무한 재시도
   - 캐시 없는 반복 계산
   - 커넥션 풀 미사용

4. **유지보수 안티패턴**
   - 문서화 없는 복잡한 로직
   - 테스트 없는 중요 기능
   - 하드코딩된 설정값
   - 에러 무시 (except: pass)

---

## 📚 참고 자료

### 필수 문서
- [LangGraph 0.6.7 Documentation](https://langchain-ai.github.io/langgraph/)
- [Runtime API Reference](https://langchain-ai.github.io/langgraph/reference/runtime/)
- [Context API Guide](https://langchain-ai.github.io/langgraph/agents/context/)
- [Human-in-the-Loop Patterns](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/)

### 추가 학습 자료
- [LangGraph 1.0 Alpha Release Notes](https://github.com/langchain-ai/langgraph/releases)
- [LangChain Academy](https://academy.langchain.com/)
- [Community Forum](https://github.com/langchain-ai/langgraph/discussions)

---

**버전**: 2.0.0  
**최종 수정**: 2025-01-10  
**작성자**: LangGraph 0.6.7 고도화 구현팀

이 규칙은 지속적으로 업데이트되며, 팀의 피드백을 반영하여 개선됩니다.
