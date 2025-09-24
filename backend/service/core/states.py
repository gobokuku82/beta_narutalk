"""
State definitions for all agents and orchestrator
Simplified to contain only workflow-related data (Context API handles metadata)
"""

from typing import TypedDict, List, Dict, Any, Optional
from enum import Enum


class ProcessingStatus(Enum):
    """Processing status enum"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


# Note: With Context API, metadata like user_id, session_id, error_logs
# are moved to Context. State now only contains workflow data.

class BaseState(TypedDict):
    """Base workflow state - simplified"""
    status: str  # ProcessingStatus value
    execution_step: str  # Current step in workflow


# ============= Agent-specific States (Simplified) =============

class SearchState(TypedDict):
    """Search agent workflow state"""
    status: str
    execution_step: str
    # Search-specific workflow data
    query: str
    search_type: str  # hr_info, hr_rules, both
    filters: Dict[str, Any]
    keywords: List[str]
    hr_results: List[Dict[str, Any]]
    rules_results: List[Dict[str, Any]]
    relevance_scores: Dict[str, float]
    sources: List[str]
    final_results: Dict[str, Any]


class SalesState(TypedDict):
    """Sales analytics workflow state"""
    status: str
    execution_step: str
    # Sales-specific workflow data
    employee_name: str
    period: str  # daily, weekly, monthly, yearly
    metrics_type: str  # performance, revenue, targets

    # SQL/Text2SQL related fields
    parsed_query: Dict[str, Any]  # Parsed query information {name, month, action, etc}
    generated_sql: str  # Generated SQL query
    sql_result: List[Dict[str, Any]]  # SQL execution results
    formatted_result: str  # Formatted result for user

    # Legacy fields (will be phased out gradually)
    raw_data: List[Dict[str, Any]]
    aggregated_data: Dict[str, Any]
    statistics: Dict[str, float]
    charts_data: List[Dict[str, Any]]
    insights: List[str]
    final_report: Dict[str, Any]


class ComplianceState(TypedDict):
    """Compliance check workflow state"""
    status: str
    execution_step: str
    # Compliance-specific workflow data
    check_type: str  # policy, regulation, audit
    target_action: str
    action_context: Dict[str, Any]  # Renamed from 'context' to avoid confusion
    rules_checked: List[Dict[str, Any]]
    violations: List[Dict[str, Any]]
    recommendations: List[str]
    compliance_score: float
    is_compliant: bool
    compliance_report: Dict[str, Any]


class DocumentState(TypedDict):
    """Document generation workflow state"""
    status: str
    execution_step: str
    # Document-specific workflow data
    document_type: str  # report, memo, presentation, email
    template_name: str
    input_content: Dict[str, Any]
    formatting_rules: Dict[str, Any]
    sections: List[Dict[str, Any]]
    generated_content: str
    document_format: str  # text, html, markdown, pdf
    final_document: Dict[str, Any]


# ============= Orchestrator States =============

class OrchestratorState(TypedDict):
    """Main orchestrator workflow state"""
    status: str
    execution_step: str

    # User input
    user_query: str
    conversation_history: List[Dict[str, Any]]

    # Intent analysis
    intents: List[Dict[str, Any]]
    entities: List[Dict[str, Any]]
    query_type: str
    confidence_score: float

    # Planning (with reasoning)
    reasoning_steps: List[str]
    insights: Dict[str, Any]
    execution_plan: List[Dict[str, Any]]
    required_agents: List[str]
    dependencies: Dict[str, List[str]]
    parallel_groups: List[List[str]]

    # Execution
    active_agents: List[str]
    agent_inputs: Dict[str, Any]
    agent_results: Dict[str, Any]

    # Response generation
    raw_results: Dict[str, Any]
    formatted_response: str
    response_format: str  # text, table, chart, mixed
    citations: List[Dict[str, Any]]

    # Final output
    final_response: str
    success: bool