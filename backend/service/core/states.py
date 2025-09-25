"""
State Definitions for LangGraph 0.6.x
Workflow data that changes during execution with reducer patterns
Cleaned version - removed unused code
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from operator import add
from datetime import datetime


# ============ Custom Reducer Functions (Used Only) ============

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


# ============ Sales State (Active) ============

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

    # === Aggregation (merge) ===
    collected_data: Annotated[Dict[str, Any], merge_dicts]  # From subgraphs
    execution_results: Annotated[Dict[str, Any], merge_dicts]  # Execution outcomes
    aggregated_data: Annotated[Dict[str, Any], merge_dicts]  # Aggregated metrics
    statistics: Annotated[Dict[str, float], merge_dicts]  # Statistical summaries

    # === Analysis (unique accumulate) ===
    insights: Annotated[List[str], append_unique]  # Unique insights

    # === Output (overwrite) ===
    formatted_result: Optional[str]  # Human-readable result
    final_report: Optional[Dict[str, Any]]  # Complete report


# ============ State Factory Functions ============

def create_sales_initial_state(**kwargs) -> Dict[str, Any]:
    """
    Create initial SalesState with defaults

    Args:
        **kwargs: Initial field values

    Returns:
        Initial state dictionary
    """
    return {
        # Status
        "status": "pending",
        "execution_step": "initializing",
        "errors": [],
        "start_time": datetime.now().isoformat(),

        # Input
        "query": kwargs.get("query", ""),
        "employee_name": kwargs.get("employee_name"),
        "period": kwargs.get("period", "monthly"),
        "metrics_type": kwargs.get("metrics_type", "performance"),

        # Planning
        "execution_plan": None,

        # Query Processing
        "parsed_query": {},
        "generated_sql": None,

        # Data Collection
        "sql_result": [],

        # Aggregation
        "collected_data": {},
        "execution_results": {},
        "aggregated_data": {},
        "statistics": {},

        # Analysis
        "insights": [],

        # Output
        "formatted_result": None,
        "final_report": None,
        "end_time": None
    }


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