# LangGraph 0.6.7 State 관리 아키텍처

## 🎯 개요
3계층 메타 에이전트 구조를 기반으로 한 State 관리 체계 정의

---

## 🔴 Level 1: 메타 관리 Agent States

### 1.1 QueryAnalyzerState
```python
from typing import TypedDict, List, Dict, Any, Optional, Literal
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages

class QueryAnalyzerState(TypedDict):
    """질의 분석 에이전트 상태"""
    # 입력 데이터
    raw_query: str
    query_timestamp: str
    user_context: Dict[str, Any]
    
    # 분석 결과
    parsed_intents: List[Dict[str, Any]]  # [{'intent': 'analysis', 'confidence': 0.9}]
    required_capabilities: List[str]  # ['sql_query', 'data_visualization']
    complexity_score: float  # 0.0 ~ 1.0
    suggested_agents: List[str]  # ['DataAnalysisAgent', 'DocumentAgent']
    context_requirements: Dict[str, Any]  # {'need_auth': True, 'data_scope': 'company'}
    
    # 엔티티 추출
    extracted_entities: List[Dict[str, Any]]
    """
    [
        {'type': 'period', 'value': '지난달', 'normalized': '2024-12'},
        {'type': 'location', 'value': '서울', 'code': 'SEL'},
        {'type': 'metric', 'value': '매출', 'column': 'sales_amount'}
    ]
    """
    
    # 모호성 처리
    ambiguities: List[Dict[str, Any]]  # 명확히 해야 할 부분
    clarification_needed: bool
    
    # 실행 가능성
    feasibility_check: Dict[str, Any]
    """
    {
        'data_available': True,
        'permission_granted': True,
        'estimated_time': 30,
        'resource_status': 'available'
    }
    """
```

### 1.2 PlanningState
```python
class PlanningState(TypedDict):
    """계획 수립 에이전트 상태"""
    # 입력 (QueryAnalyzer로부터)
    analyzed_query: Dict[str, Any]
    
    # 실행 계획
    execution_plan: List[Dict[str, Any]]
    """
    [
        {
            'step_id': 'step_1',
            'agents': ['DataAnalysisAgent', 'InformationRetrievalAgent'],
            'parallel': True,
            'timeout': 30,
            'retry_count': 3,
            'dependencies': [],
            'checkpoint': True
        },
        {
            'step_id': 'step_2',
            'agents': ['DocumentGenerationAgent'],
            'parallel': False,
            'timeout': 20,
            'dependencies': ['step_1'],
            'checkpoint': True
        }
    ]
    """
    
    # 의존성 관리
    task_dependencies: Dict[str, List[str]]
    dependency_graph: Dict[str, Any]
    
    # 리소스 계획
    resource_requirements: Dict[str, Any]
    """
    {
        'cpu_cores': 2,
        'memory_gb': 4,
        'api_calls': {'naver': 10, 'google': 5},
        'db_connections': 3
    }
    """
    
    # 실행 전략
    estimated_steps: int
    priority_order: List[str]
    parallel_opportunities: List[List[str]]
    
    # 대체 계획
    fallback_plans: List[Dict[str, Any]]
    contingency_triggers: Dict[str, Any]
```

### 1.3 ExecutionManagerState
```python
class ExecutionManagerState(TypedDict):
    """실행 관리 에이전트 상태"""
    # 계획 관리
    current_plan: Dict[str, Any]
    active_step: str
    
    # 실행 상태
    execution_status: Literal['initializing', 'running', 'paused', 'completed', 'failed']
    execution_progress: float  # 0.0 ~ 1.0
    
    # 태스크 추적
    completed_tasks: List[Dict[str, Any]]
    """
    [
        {
            'task_id': 'task_001',
            'agent': 'DataAnalysisAgent',
            'result': {...},
            'execution_time': 5.2,
            'quality_score': 0.95
        }
    ]
    """
    pending_tasks: List[Dict[str, Any]]
    failed_tasks: List[Dict[str, Any]]
    
    # 품질 관리
    quality_scores: Dict[str, float]
    validation_results: Dict[str, Any]
    
    # 재계획 관리
    need_replan: bool
    replan_reason: Optional[str]
    replan_attempts: int
    
    # 최종 결과
    final_results: Optional[Dict[str, Any]]
    aggregation_method: Optional[str]
```

---

## 🔵 Level 2: 실행 Agent States

### 2.1 BaseAgentState (공통 기반)
```python
class BaseAgentState(TypedDict):
    """모든 실행 에이전트의 기본 상태"""
    # 태스크 정보
    task_id: str
    assigned_task: Dict[str, Any]
    execution_context: Dict[str, Any]
    
    # 실행 결과
    result: Optional[Any]
    confidence_score: float
    execution_time: float
    
    # 에러 처리
    error_message: Optional[str]
    error_type: Optional[str]
    recovery_attempted: bool
    
    # 메타데이터
    start_time: str
    end_time: Optional[str]
    resource_usage: Dict[str, Any]
```

### 2.2 DataAnalysisAgentState
```python
class DataAnalysisAgentState(BaseAgentState):
    """데이터 분석 에이전트 상태"""
    # SQL 관련
    generated_queries: List[str]
    query_execution_plans: List[Dict[str, Any]]
    
    # 분석 결과
    raw_data: List[Dict[str, Any]]
    processed_data: Dict[str, Any]
    statistics: Dict[str, Any]
    
    # 시각화
    visualizations: List[Dict[str, Any]]
    """
    [
        {
            'type': 'bar_chart',
            'data': {...},
            'config': {...},
            'image_url': 'base64...'
        }
    ]
    """
    
    # 캐싱
    cache_key: Optional[str]
    cache_hit: bool
```

### 2.3 InformationRetrievalAgentState
```python
class InformationRetrievalAgentState(BaseAgentState):
    """정보 검색 에이전트 상태"""
    # 검색 설정
    search_queries: List[str]
    search_sources: List[str]  # ['internal_db', 'vector_db', 'web']
    
    # 검색 결과
    search_results: Dict[str, List[Dict[str, Any]]]
    """
    {
        'internal_db': [...],
        'vector_db': [...],
        'web': [...]
    }
    """
    
    # 관련성 평가
    relevance_scores: Dict[str, float]
    filtered_results: List[Dict[str, Any]]
    
    # 출처 추적
    sources: List[Dict[str, Any]]
    citations: List[str]
```

### 2.4 DocumentGenerationAgentState
```python
class DocumentGenerationAgentState(BaseAgentState):
    """문서 생성 에이전트 상태"""
    # 문서 타입
    document_type: str  # 'visit_report', 'seminar_request', etc.
    template_id: str
    
    # 입력 데이터
    form_data: Dict[str, Any]
    source_data: List[Dict[str, Any]]
    
    # 생성 과정
    draft_versions: List[Dict[str, Any]]
    current_version: int
    
    # 최종 문서
    generated_document: Dict[str, Any]
    """
    {
        'content': '...',
        'format': 'pdf',
        'metadata': {...},
        'file_path': '/path/to/doc.pdf'
    }
    """
    
    # 저장 정보
    document_id: str
    storage_location: str
    document_url: Optional[str]
```

### 2.5 ComplianceValidationAgentState
```python
class ComplianceValidationAgentState(BaseAgentState):
    """규정 검증 에이전트 상태"""
    # 검증 대상
    validation_target: Dict[str, Any]
    validation_type: str  # 'document', 'action', 'data'
    
    # 규정 체크
    applied_rules: List[str]
    """
    ['medical_law', 'rebate_law', 'fair_trade', 'internal_compliance']
    """
    
    # 검증 결과
    validation_results: List[Dict[str, Any]]
    """
    [
        {
            'rule': 'medical_law_article_23',
            'status': 'pass',
            'confidence': 0.95,
            'details': '...'
        }
    ]
    """
    
    # 위반 사항
    violations: List[Dict[str, Any]]
    risk_level: Literal['low', 'medium', 'high', 'critical']
    
    # 권고사항
    recommendations: List[str]
    required_modifications: List[Dict[str, Any]]
```

### 2.6 StorageDecisionAgentState
```python
class StorageDecisionAgentState(BaseAgentState):
    """저장 결정 에이전트 상태"""
    # 데이터 분석
    data_to_store: Dict[str, Any]
    data_type: str
    data_size: int
    
    # 저장 결정
    storage_decision: Literal['structured_db', 'vector_db', 'unstructured_db', 'hybrid']
    decision_reasoning: str
    
    # 스키마 매핑
    schema_mapping: Dict[str, Any]
    """
    {
        'target_table': 'customer_info',
        'field_mappings': {...},
        'transformation_rules': [...]
    }
    """
    
    # 저장 실행
    storage_status: Literal['pending', 'in_progress', 'completed', 'failed']
    stored_location: Optional[str]
    storage_metadata: Dict[str, Any]
```

---

## 🟡 Global Session State

```python
from typing import Annotated

class GlobalSessionState(TypedDict):
    """전체 세션을 관리하는 글로벌 상태"""
    # 세션 식별
    session_id: str
    user_id: str
    company_id: str
    
    # 대화 관리
    messages: Annotated[List[AnyMessage], add_messages]
    conversation_history: List[Dict[str, Any]]
    
    # 워크플로우 상태
    current_phase: Literal['analyzing', 'planning', 'executing', 'completed']
    current_agent: Optional[str]
    workflow_status: Dict[str, Any]
    
    # 진행 상황
    iteration_count: int
    execution_steps: List[Dict[str, Any]]
    progress_percentage: float
    
    # 리소스 추적
    total_tokens_used: int
    api_calls_made: Dict[str, int]
    db_queries_executed: int
    
    # 메타 에이전트 상태 참조
    query_analyzer_state: Optional[QueryAnalyzerState]
    planning_state: Optional[PlanningState]
    execution_manager_state: Optional[ExecutionManagerState]
    
    # 실행 에이전트 상태 참조
    agent_states: Dict[str, BaseAgentState]
    
    # 최종 결과
    final_response: Optional[str]
    response_metadata: Dict[str, Any]
    
    # 에러 및 경고
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    
    # 감사 로그
    audit_trail: List[Dict[str, Any]]
```

---

## 🔄 State 전환 규칙

### Phase 전환
```python
def determine_next_phase(state: GlobalSessionState) -> str:
    """현재 상태를 기반으로 다음 단계 결정"""
    
    current = state["current_phase"]
    
    if current == "analyzing":
        if state["query_analyzer_state"]["clarification_needed"]:
            return "clarifying"  # 사용자 확인 필요
        return "planning"
    
    elif current == "planning":
        if not state["planning_state"]["execution_plan"]:
            return "analyzing"  # 재분석 필요
        return "executing"
    
    elif current == "executing":
        if state["execution_manager_state"]["need_replan"]:
            return "planning"  # 재계획
        if state["execution_manager_state"]["execution_status"] == "completed":
            return "completed"
        return "executing"  # 계속 실행
    
    return "completed"
```

### State 병합 규칙
```python
def merge_agent_results(
    global_state: GlobalSessionState,
    agent_state: BaseAgentState,
    agent_name: str
) -> GlobalSessionState:
    """에이전트 실행 결과를 글로벌 상태에 병합"""
    
    # 에이전트 상태 저장
    global_state["agent_states"][agent_name] = agent_state
    
    # 실행 관리자 상태 업데이트
    if agent_state["error_message"]:
        global_state["execution_manager_state"]["failed_tasks"].append({
            "agent": agent_name,
            "task_id": agent_state["task_id"],
            "error": agent_state["error_message"]
        })
    else:
        global_state["execution_manager_state"]["completed_tasks"].append({
            "agent": agent_name,
            "task_id": agent_state["task_id"],
            "result": agent_state["result"],
            "quality_score": agent_state["confidence_score"]
        })
    
    # 진행률 업데이트
    total_tasks = len(global_state["planning_state"]["execution_plan"])
    completed = len(global_state["execution_manager_state"]["completed_tasks"])
    global_state["progress_percentage"] = (completed / total_tasks) * 100
    
    return global_state
```

---

## 📊 State 모니터링

### 실시간 상태 추적
```python
class StateMonitor:
    """State 변화를 실시간으로 모니터링"""
    
    def track_state_changes(
        self,
        old_state: GlobalSessionState,
        new_state: GlobalSessionState
    ) -> Dict[str, Any]:
        """상태 변화 추적"""
        
        changes = {
            "timestamp": datetime.now().isoformat(),
            "phase_transition": None,
            "agent_changes": [],
            "progress_delta": 0,
            "new_errors": [],
            "completed_tasks": []
        }
        
        # Phase 전환 감지
        if old_state["current_phase"] != new_state["current_phase"]:
            changes["phase_transition"] = {
                "from": old_state["current_phase"],
                "to": new_state["current_phase"]
            }
        
        # 진행률 변화
        changes["progress_delta"] = (
            new_state["progress_percentage"] - 
            old_state["progress_percentage"]
        )
        
        # 새로운 에러
        old_errors = {e["id"] for e in old_state.get("errors", [])}
        new_errors = {e["id"] for e in new_state.get("errors", [])}
        changes["new_errors"] = list(new_errors - old_errors)
        
        return changes
```

---

## 💾 State 영속성

### Checkpoint 전략
```python
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

class StateCheckpointer:
    """State 체크포인트 관리"""
    
    def __init__(self):
        self.checkpointer = AsyncSqliteSaver.from_conn_string(
            "checkpoints.db"
        )
    
    async def save_checkpoint(
        self,
        state: GlobalSessionState,
        checkpoint_id: str
    ):
        """중요 시점에 상태 저장"""
        
        checkpoint_data = {
            "state": state,
            "timestamp": datetime.now().isoformat(),
            "phase": state["current_phase"],
            "progress": state["progress_percentage"]
        }
        
        await self.checkpointer.aput(
            config={"configurable": {"thread_id": state["session_id"]}},
            checkpoint=checkpoint_data,
            checkpoint_id=checkpoint_id
        )
    
    async def restore_from_checkpoint(
        self,
        session_id: str,
        checkpoint_id: Optional[str] = None
    ) -> GlobalSessionState:
        """체크포인트에서 상태 복원"""
        
        checkpoint = await self.checkpointer.aget(
            config={"configurable": {"thread_id": session_id}},
            checkpoint_id=checkpoint_id
        )
        
        return checkpoint["state"] if checkpoint else None
```

---

## 🔐 State 보안

### 민감 정보 처리
```python
class StateSecurityManager:
    """State 내 민감 정보 관리"""
    
    SENSITIVE_FIELDS = [
        "user_id", "api_keys", "passwords",
        "personal_info", "financial_data"
    ]
    
    def sanitize_state_for_logging(
        self,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """로깅용 State 정제"""
        
        sanitized = deepcopy(state)
        
        for field in self.SENSITIVE_FIELDS:
            if field in sanitized:
                sanitized[field] = "***REDACTED***"
        
        return sanitized
    
    def encrypt_sensitive_fields(
        self,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """민감 필드 암호화"""
        
        encrypted = deepcopy(state)
        
        for field in self.SENSITIVE_FIELDS:
            if field in encrypted:
                encrypted[field] = self.encrypt(encrypted[field])
        
        return encrypted
```

---

## 📈 성능 최적화

### State 크기 관리
```python
class StateOptimizer:
    """State 크기 및 성능 최적화"""
    
    MAX_MESSAGE_HISTORY = 50
    MAX_AGENT_RESULTS = 100
    
    def optimize_state(
        self,
        state: GlobalSessionState
    ) -> GlobalSessionState:
        """State 크기 최적화"""
        
        # 메시지 히스토리 제한
        if len(state["messages"]) > self.MAX_MESSAGE_HISTORY:
            state["messages"] = state["messages"][-self.MAX_MESSAGE_HISTORY:]
        
        # 오래된 에이전트 결과 정리
        if len(state["agent_states"]) > self.MAX_AGENT_RESULTS:
            # 가장 최근 N개만 유지
            recent_agents = sorted(
                state["agent_states"].items(),
                key=lambda x: x[1].get("end_time", ""),
                reverse=True
            )[:self.MAX_AGENT_RESULTS]
            state["agent_states"] = dict(recent_agents)
        
        return state
```

---

**버전**: 1.0.0  
**작성일**: 2025-01-10  
**기반**: LangGraph 0.6.7
