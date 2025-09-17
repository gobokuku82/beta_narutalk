"""
State definitions for Medical Supervisor
의료/제약 도메인 특화 상태 정의
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal, Annotated
from langgraph.graph import add_messages
from datetime import datetime
import operator


# Custom Reducers
def merge_data_sources(current: List[str], update: List[str]) -> List[str]:
    """데이터 소스 병합 (중복 제거)"""
    if not current:
        current = []
    if not update:
        return current
    return list(set(current + update))


def update_execution_status(current: Dict, update: Dict) -> Dict:
    """실행 상태 업데이트"""
    if not current:
        current = {"status": "pending", "progress": 0}
    
    # 상태 전이 규칙
    status_priority = {
        "pending": 0,
        "running": 1,
        "completed": 2,
        "failed": 3
    }
    
    current_priority = status_priority.get(current.get("status", "pending"), 0)
    update_priority = status_priority.get(update.get("status", "pending"), 0)
    
    if update_priority >= current_priority:
        return update
    return current


def append_agent_results(current: List[Dict], update: List[Dict]) -> List[Dict]:
    """에이전트 결과 추가 (최대 100개 유지)"""
    if not current:
        current = []
    if not update:
        return current
    
    combined = current + update
    return combined[-100:] if len(combined) > 100 else combined


class MedicalSupervisorState(TypedDict):
    """
    의료 Supervisor 전체 상태
    """
    
    # 기본 정보
    session_id: str
    user_id: str
    timestamp: str
    
    # 대화 관리
    messages: Annotated[List[Any], add_messages]
    
    # 컨텍스트 (Context Engineering)
    context: Dict[str, Any]
    optimized_context: Optional[Dict[str, Any]]
    agent_specific_contexts: Dict[str, Dict[str, Any]]
    
    # 워크플로우 상태
    current_phase: Literal["intent", "planning", "agent_selection", "execution", "completed"]
    workflow_status: Annotated[Dict[str, Any], update_execution_status]
    
    # 의도 분석 결과
    intent_analysis: Optional[Dict[str, Any]]
    domain_type: Optional[Literal["실적분석", "정보검색", "문서생성", "규정검토"]]
    complexity_score: float
    
    # 실행 계획
    execution_plan: Optional[List[Dict[str, Any]]]
    selected_agents: List[str]
    agent_dependencies: Dict[str, List[str]]
    parallel_groups: List[List[str]]
    
    # 에이전트 실행 상태
    agent_states: Dict[str, Dict[str, Any]]
    agent_results: Annotated[List[Dict[str, Any]], append_agent_results]
    active_agents: List[str]
    completed_agents: List[str]
    failed_agents: List[str]
    
    # 데이터 관련
    data_sources: Annotated[List[str], merge_data_sources]
    query_results: Dict[str, Any]
    generated_documents: List[Dict[str, Any]]
    
    # 규정 준수
    compliance_status: Literal["pending", "reviewing", "approved", "rejected"]
    compliance_issues: List[Dict[str, Any]]
    applicable_regulations: List[str]
    
    # 성능 메트릭
    execution_time: float
    token_usage: Dict[str, int]
    api_calls: Dict[str, int]
    
    # 에러 및 경고
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    
    # 최종 결과
    final_response: Optional[str]
    response_metadata: Dict[str, Any]


class IntentAnalysisState(TypedDict):
    """의도 분석 상태"""
    
    raw_query: str
    analyzed_intents: List[Dict[str, float]]  # {"intent": "실적분석", "confidence": 0.9}
    entities: List[Dict[str, Any]]
    time_range: Optional[Dict[str, str]]
    target_entities: List[str]
    required_capabilities: List[str]
    ambiguities: List[Dict[str, Any]]
    clarification_needed: bool


class PlanningState(TypedDict):
    """계획 수립 상태"""
    
    execution_steps: List[Dict[str, Any]]
    agent_assignments: Dict[str, List[str]]  # {agent: [tasks]}
    estimated_time: float
    resource_requirements: Dict[str, Any]
    parallel_opportunities: List[List[str]]
    fallback_plans: List[Dict[str, Any]]
    optimization_applied: bool


class AgentSelectionState(TypedDict):
    """에이전트 선택 상태"""
    
    available_agents: List[str]
    selected_agents: List[str]
    selection_criteria: Dict[str, Any]
    agent_capabilities: Dict[str, List[str]]
    workload_distribution: Dict[str, float]
    selection_reasoning: str


class ExecutionState(TypedDict):
    """실행 상태"""
    
    current_step: int
    total_steps: int
    execution_progress: float
    active_tasks: List[Dict[str, Any]]
    completed_tasks: List[Dict[str, Any]]
    pending_tasks: List[Dict[str, Any]]
    task_results: Dict[str, Any]
    execution_errors: List[Dict[str, Any]]
    retry_attempts: Dict[str, int]


def initialize_medical_state(
    session_id: str,
    user_id: str,
    initial_query: str
) -> MedicalSupervisorState:
    """
    초기 상태 생성
    """
    
    return MedicalSupervisorState(
        session_id=session_id,
        user_id=user_id,
        timestamp=datetime.now().isoformat(),
        messages=[],
        context={},
        optimized_context=None,
        agent_specific_contexts={},
        current_phase="intent",
        workflow_status={"status": "pending", "progress": 0},
        intent_analysis=None,
        domain_type=None,
        complexity_score=0.0,
        execution_plan=None,
        selected_agents=[],
        agent_dependencies={},
        parallel_groups=[],
        agent_states={},
        agent_results=[],
        active_agents=[],
        completed_agents=[],
        failed_agents=[],
        data_sources=[],
        query_results={},
        generated_documents=[],
        compliance_status="pending",
        compliance_issues=[],
        applicable_regulations=[],
        execution_time=0.0,
        token_usage={},
        api_calls={},
        errors=[],
        warnings=[],
        final_response=None,
        response_metadata={}
    )


def update_state_phase(
    state: MedicalSupervisorState,
    new_phase: str
) -> MedicalSupervisorState:
    """
    상태 단계 업데이트
    """
    
    state["current_phase"] = new_phase
    state["workflow_status"]["status"] = "running"
    
    # 단계별 진행률 계산
    phase_progress = {
        "intent": 0.2,
        "planning": 0.4,
        "agent_selection": 0.6,
        "execution": 0.8,
        "completed": 1.0
    }
    
    state["workflow_status"]["progress"] = phase_progress.get(new_phase, 0.0)
    
    return state


def merge_agent_state(
    global_state: MedicalSupervisorState,
    agent_name: str,
    agent_result: Dict[str, Any]
) -> MedicalSupervisorState:
    """
    에이전트 실행 결과를 전체 상태에 병합
    """
    
    # 에이전트 상태 업데이트
    global_state["agent_states"][agent_name] = agent_result
    
    # 결과 추가
    global_state["agent_results"].append({
        "agent": agent_name,
        "timestamp": datetime.now().isoformat(),
        "result": agent_result.get("result"),
        "status": agent_result.get("status", "completed")
    })
    
    # 완료/실패 리스트 업데이트
    if agent_result.get("status") == "completed":
        if agent_name not in global_state["completed_agents"]:
            global_state["completed_agents"].append(agent_name)
        if agent_name in global_state["active_agents"]:
            global_state["active_agents"].remove(agent_name)
    elif agent_result.get("status") == "failed":
        if agent_name not in global_state["failed_agents"]:
            global_state["failed_agents"].append(agent_name)
        if agent_name in global_state["active_agents"]:
            global_state["active_agents"].remove(agent_name)
    
    # 데이터 소스 업데이트
    if "data_sources" in agent_result:
        global_state["data_sources"].extend(agent_result["data_sources"])
    
    # 생성된 문서 추가
    if "generated_document" in agent_result:
        global_state["generated_documents"].append(agent_result["generated_document"])
    
    # 규정 이슈 추가
    if "compliance_issues" in agent_result:
        global_state["compliance_issues"].extend(agent_result["compliance_issues"])
    
    return global_state


class StateValidator:
    """
    상태 유효성 검증
    """
    
    @staticmethod
    def validate_intent_state(state: IntentAnalysisState) -> bool:
        """의도 분석 상태 검증"""
        
        if not state.get("raw_query"):
            return False
        
        if not state.get("analyzed_intents"):
            return False
        
        # 신뢰도 합이 1.0을 초과하지 않는지 확인
        total_confidence = sum(
            intent.get("confidence", 0)
            for intent in state.get("analyzed_intents", [])
        )
        
        if total_confidence > 1.1:  # 약간의 오차 허용
            return False
        
        return True
    
    @staticmethod
    def validate_execution_state(state: ExecutionState) -> bool:
        """실행 상태 검증"""
        
        if state.get("current_step", 0) > state.get("total_steps", 0):
            return False
        
        if state.get("execution_progress", 0) > 1.0:
            return False
        
        # 완료된 작업이 전체 작업을 초과하지 않는지 확인
        total_tasks = (
            len(state.get("active_tasks", [])) +
            len(state.get("completed_tasks", [])) +
            len(state.get("pending_tasks", []))
        )
        
        if len(state.get("completed_tasks", [])) > total_tasks:
            return False
        
        return True
    
    @staticmethod
    def validate_global_state(state: MedicalSupervisorState) -> bool:
        """전체 상태 검증"""
        
        # 필수 필드 확인
        required_fields = ["session_id", "user_id", "timestamp"]
        for field in required_fields:
            if field not in state or not state[field]:
                return False
        
        # 단계 유효성
        valid_phases = ["intent", "planning", "agent_selection", "execution", "completed"]
        if state.get("current_phase") not in valid_phases:
            return False
        
        # 진행률 유효성
        progress = state.get("workflow_status", {}).get("progress", 0)
        if progress < 0 or progress > 1:
            return False
        
        return True


class StateTransitions:
    """
    상태 전이 관리
    """
    
    @staticmethod
    def can_transition(
        current_phase: str,
        target_phase: str
    ) -> bool:
        """
        상태 전이 가능 여부 확인
        """
        
        valid_transitions = {
            "intent": ["planning", "completed"],  # 간단한 쿼리는 바로 완료 가능
            "planning": ["agent_selection", "completed"],
            "agent_selection": ["execution", "planning"],  # 재계획 가능
            "execution": ["completed", "planning"],  # 재계획 가능
            "completed": []  # 종료 상태
        }
        
        return target_phase in valid_transitions.get(current_phase, [])
    
    @staticmethod
    def get_next_phase(current_phase: str) -> str:
        """
        다음 단계 결정
        """
        
        next_phase_map = {
            "intent": "planning",
            "planning": "agent_selection",
            "agent_selection": "execution",
            "execution": "completed",
            "completed": "completed"
        }
        
        return next_phase_map.get(current_phase, "completed")
