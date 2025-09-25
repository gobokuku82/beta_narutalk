"""
State Definitions for LangGraph 0.6.x
Workflow data that changes during execution with reducer patterns
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from operator import add
from langgraph.graph.message import add_messages
from datetime import datetime


# ============ Custom Reducer Functions ============

def merge_dicts(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Merge dictionaries, b overwrites a"""
    if not a:
        return b or {}
    if not b:
        return a
    return {**a, **b}


def append_unique(a: List[Any], b: List[Any]) -> List[Any]:
    """Append only unique items to list"""
    if not a:
        a = []
    if not b:
        return a
    result = a.copy()
    for item in b:
        if item not in result:
            result.append(item)
    return result


def append_with_timestamp(a: List[Dict], b: List[Dict]) -> List[Dict]:
    """Append items with timestamp added"""
    result = a.copy() if a else []
    for item in (b or []):
        if isinstance(item, dict):
            item["timestamp"] = datetime.now().isoformat()
        result.append(item)
    return result


def keep_max(a: float, b: float) -> float:
    """Keep maximum value"""
    if a is None:
        return b
    if b is None:
        return a
    return max(a, b)


def keep_min(a: float, b: float) -> float:
    """Keep minimum value"""
    if a is None:
        return b
    if b is None:
        return a
    return min(a, b)


def increment_counter(a: int, b: int) -> int:
    """Increment counter"""
    return (a or 0) + (b or 1)


# ============ Base State ============

class BaseState(TypedDict):
    """Base state for all workflows"""
    
    # Status tracking (overwrite)
    status: str  # pending, processing, completed, failed
    execution_step: str  # Current step in workflow
    
    # Error tracking (accumulate)
    errors: Annotated[List[str], add]  # Error messages
    
    # Timing (overwrite)
    start_time: Optional[str]
    end_time: Optional[str]


# ============ Sales State ============

class SalesState(BaseState):
    """
    Sales Analytics Agent State
    Workflow data that changes during execution
    """
    
    # === Input (overwrite) ===
    query: str  # User query
    employee_name: Optional[str]
    period: Optional[str]  # daily, weekly, monthly, yearly
    metrics_type: Optional[str]  # performance, revenue, targets
    
    # === Planning (overwrite) ===
    execution_plan: Optional[Dict[str, Any]]  # LLM generated plan
    
    # === Query Processing (overwrite) ===
    parsed_query: Dict[str, Any]  # Parsed components
    generated_sql: Optional[str]  # Generated SQL
    
    # === Data Collection (accumulate) ===
    sql_result: Annotated[List[Dict[str, Any]], add]  # Query results
    raw_data: Annotated[List[Dict[str, Any]], add]  # Raw collected data
    
    # === Aggregation (merge) ===
    collected_data: Annotated[Dict[str, Any], merge_dicts]  # From subgraphs
    execution_results: Annotated[Dict[str, Any], merge_dicts]  # Execution outcomes
    aggregated_data: Annotated[Dict[str, Any], merge_dicts]  # Aggregated metrics
    statistics: Annotated[Dict[str, float], merge_dicts]  # Statistical summaries
    
    # === Analysis (unique accumulate) ===
    insights: Annotated[List[str], append_unique]  # Unique insights
    recommendations: Annotated[List[str], append_unique]  # Unique recommendations
    
    # === Output (overwrite) ===
    formatted_result: Optional[str]  # Human-readable result
    final_report: Optional[Dict[str, Any]]  # Complete report
    
    # === Metrics (special reducers) ===
    max_value: Annotated[Optional[float], keep_max]  # Track maximum
    min_value: Annotated[Optional[float], keep_min]  # Track minimum
    total_processed: Annotated[int, increment_counter]  # Count items


# ============ Search State ============

class SearchState(BaseState):
    """Search Agent State"""
    
    # Input (overwrite)
    search_query: str
    search_type: str  # hr_info, hr_rules, both
    filters: Dict[str, Any]
    
    # Processing (accumulate)
    keywords: Annotated[List[str], append_unique]
    search_results: Annotated[List[Dict[str, Any]], add]
    
    # Scoring (merge)
    relevance_scores: Annotated[Dict[str, float], merge_dicts]
    
    # Output (overwrite)
    ranked_results: Optional[List[Dict[str, Any]]]
    final_answer: Optional[str]


# ============ Orchestrator State ============

class OrchestratorState(BaseState):
    """Main Orchestrator State"""
    
    # Input (overwrite)
    user_query: str
    conversation_id: str
    
    # Conversation (message reducer)
    messages: Annotated[List[Dict], add_messages]
    
    # Intent Analysis (overwrite)
    intent: Optional[str]
    entities: Optional[List[Dict[str, Any]]]
    confidence_score: Optional[float]
    
    # Planning (accumulate)
    reasoning_steps: Annotated[List[str], add]
    required_agents: Annotated[List[str], append_unique]
    
    # Execution (merge)
    agent_inputs: Annotated[Dict[str, Any], merge_dicts]
    agent_results: Annotated[Dict[str, Any], merge_dicts]
    
    # Response (overwrite)
    final_response: Optional[str]
    response_metadata: Optional[Dict[str, Any]]


# ============ Subgraph States ============

class DataCollectionState(TypedDict):
    """Data Collection Subgraph State"""
    
    # Status
    status: str
    
    # Input
    query_params: Dict[str, Any]
    
    # Collection (accumulate)
    performance_data: Annotated[List[Dict], add]
    target_data: Annotated[List[Dict], add]
    client_data: Annotated[List[Dict], add]
    
    # Aggregation (merge)
    aggregated_performance: Annotated[Dict, merge_dicts]
    aggregated_target: Annotated[Dict, merge_dicts]
    aggregated_client: Annotated[Dict, merge_dicts]
    
    # Errors
    errors: Annotated[List[str], add]


class AnalysisState(TypedDict):
    """Analysis Subgraph State"""
    
    # Status
    status: str
    
    # Input
    input_data: Dict[str, Any]
    analysis_params: Dict[str, Any]
    
    # Analysis Results (merge)
    basic_metrics: Annotated[Dict[str, float], merge_dicts]
    trend_analysis: Annotated[Dict, merge_dicts]
    predictions: Annotated[Dict, merge_dicts]
    
    # Insights (unique)
    insights: Annotated[List[str], append_unique]
    
    # Output
    analysis_report: Optional[Dict[str, Any]]
    
    # Errors
    errors: Annotated[List[str], add]


# ============ State Factory Functions ============

def create_initial_state(state_class: type, **kwargs) -> Dict[str, Any]:
    """
    Generic initial state creator
    
    Args:
        state_class: State class type
        **kwargs: Initial values
        
    Returns:
        Initial state dictionary with defaults
    """
    # Get annotations from class
    annotations = getattr(state_class, '__annotations__', {})
    
    initial = {
        "status": "pending",
        "execution_step": "initializing",
        "errors": [],
        "start_time": datetime.now().isoformat()
    }
    
    # Add defaults for each field type
    for field, field_type in annotations.items():
        if field in initial:
            continue
            
        # Check if it's Optional
        type_str = str(field_type)
        if 'Optional' in type_str or 'None' in type_str:
            initial[field] = kwargs.get(field)
        # Check for List
        elif 'List' in type_str or 'list' in type_str:
            initial[field] = kwargs.get(field, [])
        # Check for Dict
        elif 'Dict' in type_str or 'dict' in type_str:
            initial[field] = kwargs.get(field, {})
        # String fields
        elif field in ['query', 'search_query', 'user_query']:
            initial[field] = kwargs.get(field, "")
        # Default to None for unknown
        else:
            initial[field] = kwargs.get(field)
    
    # Override with provided kwargs
    initial.update(kwargs)
    
    return initial


def create_sales_initial_state(**kwargs) -> Dict[str, Any]:
    """Create initial SalesState"""
    return create_initial_state(SalesState, **kwargs)


def create_search_initial_state(**kwargs) -> Dict[str, Any]:
    """Create initial SearchState"""
    return create_initial_state(SearchState, **kwargs)


def create_orchestrator_initial_state(**kwargs) -> Dict[str, Any]:
    """Create initial OrchestratorState"""
    return create_initial_state(OrchestratorState, **kwargs)


def merge_state_updates(*updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple state updates
    
    Args:
        *updates: State update dictionaries
        
    Returns:
        Merged state update
    """
    result = {}
    for update in updates:
        for key, value in update.items():
            if value is not None:
                result[key] = value
    return result


def validate_state_transition(
    current_state: Dict[str, Any],
    next_state: Dict[str, Any]
) -> bool:
    """
    Validate state transition is valid
    
    Args:
        current_state: Current state
        next_state: Proposed next state
        
    Returns:
        True if transition is valid
    """
    # Status transition rules
    valid_transitions = {
        "pending": ["processing", "failed"],
        "processing": ["completed", "failed", "pending"],
        "completed": [],  # Terminal state
        "failed": ["pending"]  # Can retry
    }
    
    current_status = current_state.get("status", "pending")
    next_status = next_state.get("status", current_status)
    
    if next_status != current_status:
        allowed = valid_transitions.get(current_status, [])
        if next_status not in allowed:
            return False
    
    return True


def get_state_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get summary of current state
    
    Args:
        state: Current state
        
    Returns:
        Summary dictionary
    """
    return {
        "status": state.get("status"),
        "step": state.get("execution_step"),
        "errors_count": len(state.get("errors", [])),
        "has_results": bool(state.get("final_report") or state.get("formatted_result")),
        "data_collected": bool(state.get("collected_data") or state.get("sql_result")),
        "insights_count": len(state.get("insights", [])),
        "start_time": state.get("start_time"),
        "end_time": state.get("end_time")
    }
