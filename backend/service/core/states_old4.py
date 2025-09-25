"""
State definitions for LangGraph 0.6.x with proper reducer patterns
Following Context API best practices - State contains ONLY workflow data
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from operator import add
from langgraph.graph.message import add_messages
from datetime import datetime


# ============ Custom Reducer Functions ============

def merge_dicts(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two dictionaries, b overwrites a"""
    if a is None:
        return b
    if b is None:
        return a
    return {**a, **b}


def append_unique(a: List[Any], b: List[Any]) -> List[Any]:
    """Append only unique items"""
    if a is None:
        a = []
    if b is None:
        return a
    result = a.copy()
    for item in b:
        if item not in result:
            result.append(item)
    return result


def update_timestamp(a: Any, b: Any) -> Any:
    """Always return latest value with timestamp"""
    return b


# ============ Sales State Definition ============

class SalesState(TypedDict):
    """
    Sales Analytics Agent State
    ONLY workflow data, NO metadata (metadata goes in Context)
    """
    
    # === Status Fields (Overwrite) ===
    status: str  # pending, processing, completed, failed
    execution_step: str  # Current workflow step
    
    # === Input Fields (Set once, Overwrite) ===
    query: str  # Original user query
    employee_name: Optional[str]
    period: Optional[str]  # daily, weekly, monthly, yearly
    metrics_type: Optional[str]  # performance, revenue, targets
    
    # === LLM Planning (Overwrite) ===
    execution_plan: Optional[Dict[str, Any]]  # LLM generated plan
    
    # === SQL Processing (Overwrite each update) ===
    parsed_query: Dict[str, Any]  # Parsed query components
    generated_sql: Optional[str]  # Generated SQL query
    
    # === Data Collection (Accumulate with reducers) ===
    sql_result: Annotated[List[Dict[str, Any]], add]  # SQL query results
    collected_data: Annotated[Dict[str, Any], merge_dicts]  # Data from subgraphs
    execution_results: Annotated[Dict[str, Any], merge_dicts]  # Execution outcomes
    
    # === Analysis Results (Merge) ===
    aggregated_data: Annotated[Dict[str, Any], merge_dicts]  # Aggregated metrics
    statistics: Annotated[Dict[str, float], merge_dicts]  # Statistical summaries
    insights: Annotated[List[str], append_unique]  # Unique insights
    
    # === Output Fields (Overwrite when complete) ===
    formatted_result: Optional[str]  # Human-readable result
    final_report: Optional[Dict[str, Any]]  # Complete report
    
    # === Error Tracking (Accumulate) ===
    errors: Annotated[List[str], add]  # Error messages


# ============ Context Definitions ============

class AgentContext(TypedDict):
    """
    Runtime context for agents (passed via runtime.context)
    Contains ONLY metadata and configuration, NO workflow data
    """
    
    # === Required Fields (Always present) ===
    user_id: str  # User identifier
    session_id: str  # Session identifier
    
    # === Optional Fields (May be None) ===
    request_id: Optional[str]  # Request tracking ID
    original_query: Optional[str]  # Original user input
    
    # === Authentication ===
    api_keys: Optional[Dict[str, str]]  # Service API keys
    
    # === Configuration ===
    language: Optional[str]  # User language preference
    timeout: Optional[int]  # Operation timeout
    debug_mode: Optional[bool]  # Debug logging enabled
    
    # === Database Connections ===
    db_paths: Optional[Dict[str, str]]  # Database file paths
    db_connections: Optional[Dict[str, str]]  # Connection strings
    
    # === Feature Flags ===
    feature_flags: Optional[Dict[str, bool]]  # Feature toggles
    
    # === From Supervisor/Orchestrator ===
    intent_result: Optional[Dict[str, Any]]  # Intent analysis from supervisor
    supervisor_context: Optional[Dict[str, Any]]  # Additional supervisor data
    
    # === Subgraph Hints ===
    suggested_tools: Optional[List[str]]  # Tool suggestions for subgraphs
    analysis_depth: Optional[str]  # shallow, normal, deep


class SubgraphContext(TypedDict):
    """
    Context for subgraphs - minimal subset of AgentContext
    """
    
    # === Required (from parent) ===
    user_id: str
    session_id: str
    
    # === Optional (from parent) ===
    request_id: Optional[str]
    language: Optional[str]
    timeout: Optional[int]
    
    # === Subgraph Specific ===
    parent_agent: Optional[str]  # Parent agent name
    db_paths: Optional[Dict[str, str]]  # Required databases
    suggested_tools: Optional[List[str]]  # Tool hints
    analysis_depth: Optional[str]  # Analysis level
    parallel_execution: Optional[bool]  # Enable parallelism


# ============ Helper Functions ============

def create_sales_initial_state(query: str = "", **kwargs) -> Dict[str, Any]:
    """
    Create initial SalesState with proper defaults
    
    Args:
        query: User query
        **kwargs: Optional initial values
        
    Returns:
        Initial state dictionary
    """
    return {
        # Status
        "status": "pending",
        "execution_step": "initializing",
        
        # Input
        "query": query,
        "employee_name": kwargs.get("employee_name"),
        "period": kwargs.get("period", "monthly"),
        "metrics_type": kwargs.get("metrics_type", "performance"),
        
        # Planning
        "execution_plan": None,
        
        # SQL
        "parsed_query": {},
        "generated_sql": None,
        
        # Data (empty lists/dicts for reducers)
        "sql_result": [],
        "collected_data": {},
        "execution_results": {},
        
        # Analysis
        "aggregated_data": {},
        "statistics": {},
        "insights": [],
        
        # Output
        "formatted_result": None,
        "final_report": None,
        
        # Errors
        "errors": []
    }


def create_agent_context(
    user_id: str,
    session_id: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Create AgentContext with required fields and optional values
    
    Args:
        user_id: User identifier (required)
        session_id: Session identifier (required)
        **kwargs: Optional context fields
        
    Returns:
        Context dictionary
    """
    return {
        # Required
        "user_id": user_id,
        "session_id": session_id,
        
        # Optional with defaults
        "request_id": kwargs.get("request_id"),
        "original_query": kwargs.get("original_query"),
        "api_keys": kwargs.get("api_keys", {}),
        "language": kwargs.get("language", "ko"),
        "timeout": kwargs.get("timeout", 30),
        "debug_mode": kwargs.get("debug_mode", False),
        "db_paths": kwargs.get("db_paths"),
        "db_connections": kwargs.get("db_connections"),
        "feature_flags": kwargs.get("feature_flags", {}),
        "intent_result": kwargs.get("intent_result"),
        "supervisor_context": kwargs.get("supervisor_context"),
        "suggested_tools": kwargs.get("suggested_tools"),
        "analysis_depth": kwargs.get("analysis_depth", "normal")
    }


def filter_context_for_subgraph(
    parent_context: Dict[str, Any],
    parent_agent: str
) -> Dict[str, Any]:
    """
    Filter parent context for subgraph (minimal necessary info)
    
    Args:
        parent_context: Parent agent's context
        parent_agent: Parent agent name
        
    Returns:
        Filtered context for subgraph
    """
    return {
        # Required
        "user_id": parent_context["user_id"],
        "session_id": parent_context["session_id"],
        
        # Optional
        "request_id": parent_context.get("request_id"),
        "language": parent_context.get("language"),
        "timeout": parent_context.get("timeout"),
        
        # Subgraph specific
        "parent_agent": parent_agent,
        "db_paths": parent_context.get("db_paths"),
        "suggested_tools": parent_context.get("suggested_tools"),
        "analysis_depth": parent_context.get("analysis_depth"),
        "parallel_execution": parent_context.get("parallel_execution", False)
    }
