"""
State definitions for LangGraph agents
Based on LangGraph 0.6.7 patterns with optimized reducers
"""

from typing import TypedDict, List, Dict, Any, Optional, Literal, Annotated, Callable
from langgraph.graph import add_messages
from datetime import datetime
import operator


# Custom Reducer Functions
def merge_dicts(current: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """Merge dictionaries, adding numeric values"""
    result = current.copy() if current else {}
    for key, value in (update or {}).items():
        if key in result and isinstance(result[key], (int, float)) and isinstance(value, (int, float)):
            result[key] += value
        else:
            result[key] = value
    return result


def append_with_limit(limit: int = 100) -> Callable:
    """Create a reducer that limits list size"""
    def reducer(current: List, update: List) -> List:
        if not isinstance(current, list):
            current = []
        if not isinstance(update, list):
            update = [update] if update is not None else []
        combined = current + update
        return combined[-limit:] if len(combined) > limit else combined
    return reducer


def merge_agent_states(current: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """Merge agent states dictionaries"""
    result = current.copy() if current else {}
    result.update(update or {})
    return result


class BaseAgentState(TypedDict):
    """Base state for all execution agents"""
    task_id: str
    assigned_task: Dict[str, Any]
    execution_context: Dict[str, Any]
    result: Optional[Any]
    confidence_score: float
    execution_time: float
    error_message: Optional[str]
    error_type: Optional[str]
    recovery_attempted: bool
    start_time: str
    end_time: Optional[str]
    resource_usage: Dict[str, Any]


class QueryAnalyzerState(TypedDict):
    """Query analyzer agent state"""
    raw_query: str
    query_timestamp: str
    user_context: Dict[str, Any]
    parsed_intents: List[Dict[str, Any]]
    required_capabilities: List[str]
    complexity_score: float
    suggested_agents: List[str]
    context_requirements: Dict[str, Any]
    extracted_entities: List[Dict[str, Any]]
    ambiguities: List[Dict[str, Any]]
    clarification_needed: bool
    feasibility_check: Dict[str, Any]


class PlanningState(TypedDict):
    """Planning agent state"""
    analyzed_query: Dict[str, Any]
    execution_plan: List[Dict[str, Any]]
    task_dependencies: Dict[str, List[str]]
    dependency_graph: Dict[str, Any]
    resource_requirements: Dict[str, Any]
    estimated_steps: int
    priority_order: List[str]
    parallel_opportunities: List[List[str]]
    fallback_plans: List[Dict[str, Any]]
    contingency_triggers: Dict[str, Any]


class ExecutionManagerState(TypedDict):
    """Execution manager state"""
    current_plan: Dict[str, Any]
    active_step: Optional[str]
    execution_status: Literal['initializing', 'running', 'paused', 'completed', 'failed']
    execution_progress: float
    completed_tasks: List[Dict[str, Any]]
    pending_tasks: List[Dict[str, Any]]
    failed_tasks: List[Dict[str, Any]]
    quality_scores: Dict[str, float]
    validation_results: Dict[str, Any]
    need_replan: bool
    replan_reason: Optional[str]
    replan_attempts: int
    final_results: Optional[Dict[str, Any]]
    aggregation_method: Optional[str]


class DataAnalysisAgentState(BaseAgentState):
    """Data analysis agent state"""
    generated_queries: List[str]
    query_execution_plans: List[Dict[str, Any]]
    raw_data: List[Dict[str, Any]]
    processed_data: Dict[str, Any]
    statistics: Dict[str, Any]
    visualizations: List[Dict[str, Any]]
    cache_key: Optional[str]
    cache_hit: bool


class InformationRetrievalAgentState(BaseAgentState):
    """Information retrieval agent state"""
    search_queries: List[str]
    search_sources: List[str]
    search_results: Dict[str, List[Dict[str, Any]]]
    relevance_scores: Dict[str, float]
    filtered_results: List[Dict[str, Any]]
    sources: List[Dict[str, Any]]
    citations: List[str]


class DocumentGenerationAgentState(BaseAgentState):
    """Document generation agent state"""
    document_type: str
    template_id: str
    form_data: Dict[str, Any]
    source_data: List[Dict[str, Any]]
    draft_versions: List[Dict[str, Any]]
    current_version: int
    generated_document: Dict[str, Any]
    document_id: str
    storage_location: str
    document_url: Optional[str]


class ComplianceValidationAgentState(BaseAgentState):
    """Compliance validation agent state"""
    validation_target: Dict[str, Any]
    validation_type: str
    applied_rules: List[str]
    validation_results: List[Dict[str, Any]]
    violations: List[Dict[str, Any]]
    risk_level: Literal['low', 'medium', 'high', 'critical']
    recommendations: List[str]
    required_modifications: List[Dict[str, Any]]


class StorageDecisionAgentState(BaseAgentState):
    """Storage decision agent state"""
    data_to_store: Dict[str, Any]
    data_type: str
    data_size: int
    storage_decision: Literal['structured_db', 'vector_db', 'unstructured_db', 'hybrid']
    decision_reasoning: str
    schema_mapping: Dict[str, Any]
    storage_status: Literal['pending', 'in_progress', 'completed', 'failed']
    stored_location: Optional[str]
    storage_metadata: Dict[str, Any]


class GlobalSessionState(TypedDict):
    """Global session state for the entire workflow with optimized reducers"""
    # Session identification
    session_id: str
    user_id: str
    company_id: str

    # Conversation management with auto-merge
    messages: Annotated[List[Any], add_messages]
    conversation_history: Annotated[List[Dict[str, Any]], append_with_limit(50)]

    # Workflow state
    current_phase: Literal['analyzing', 'planning', 'executing', 'completed']
    current_agent: Optional[str]
    workflow_status: Dict[str, Any]

    # Progress tracking with auto-increment
    iteration_count: Annotated[int, operator.add]
    execution_steps: Annotated[List[Dict[str, Any]], append_with_limit(100)]
    progress_percentage: float

    # Resource tracking with auto-sum
    total_tokens_used: Annotated[int, operator.add]
    api_calls_made: Annotated[Dict[str, int], merge_dicts]
    db_queries_executed: Annotated[int, operator.add]

    # Meta agent states
    query_analyzer_state: Optional[QueryAnalyzerState]
    planning_state: Optional[PlanningState]
    execution_manager_state: Optional[ExecutionManagerState]

    # Execution agent states with merge
    agent_states: Annotated[Dict[str, BaseAgentState], merge_agent_states]

    # Final results
    final_response: Optional[str]
    response_metadata: Dict[str, Any]

    # Errors and warnings with auto-append
    errors: Annotated[List[Dict[str, Any]], operator.add]
    warnings: Annotated[List[Dict[str, Any]], operator.add]

    # Audit trail with size limit
    audit_trail: Annotated[List[Dict[str, Any]], append_with_limit(200)]


def initialize_global_state(session_id: str, user_id: str, company_id: str = "") -> GlobalSessionState:
    """Initialize a new global session state"""
    return GlobalSessionState(
        session_id=session_id,
        user_id=user_id,
        company_id=company_id,
        messages=[],
        conversation_history=[],
        current_phase="analyzing",
        current_agent=None,
        workflow_status={},
        iteration_count=0,
        execution_steps=[],
        progress_percentage=0.0,
        total_tokens_used=0,
        api_calls_made={},
        db_queries_executed=0,
        query_analyzer_state=None,
        planning_state=None,
        execution_manager_state=None,
        agent_states={},
        final_response=None,
        response_metadata={},
        errors=[],
        warnings=[],
        audit_trail=[]
    )


def determine_next_phase(state: GlobalSessionState) -> str:
    """Determine the next phase based on current state"""
    current = state["current_phase"]

    if current == "analyzing":
        if state["query_analyzer_state"] and state["query_analyzer_state"]["clarification_needed"]:
            return "clarifying"
        return "planning"

    elif current == "planning":
        if state["planning_state"] and not state["planning_state"]["execution_plan"]:
            return "analyzing"
        return "executing"

    elif current == "executing":
        if state["execution_manager_state"]:
            if state["execution_manager_state"]["need_replan"]:
                return "planning"
            if state["execution_manager_state"]["execution_status"] == "completed":
                return "completed"
        return "executing"

    return "completed"


def merge_agent_results(
    global_state: GlobalSessionState,
    agent_state: BaseAgentState,
    agent_name: str
) -> GlobalSessionState:
    """Merge agent execution results into global state"""
    # Store agent state
    global_state["agent_states"][agent_name] = agent_state

    # Update execution manager state if exists
    if global_state["execution_manager_state"]:
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

        # Update progress
        if global_state["planning_state"]:
            total_tasks = len(global_state["planning_state"]["execution_plan"])
            if total_tasks > 0:
                completed = len(global_state["execution_manager_state"]["completed_tasks"])
                global_state["progress_percentage"] = (completed / total_tasks) * 100

    # Add to audit trail
    global_state["audit_trail"].append({
        "timestamp": datetime.now().isoformat(),
        "agent": agent_name,
        "action": "completed" if not agent_state["error_message"] else "failed",
        "task_id": agent_state["task_id"],
        "execution_time": agent_state["execution_time"]
    })

    return global_state