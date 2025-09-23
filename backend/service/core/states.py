"""
State definitions for all agents and orchestrator
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


class BaseState(TypedDict):
    """Base state shared by all components"""
    user_id: str
    session_id: str
    timestamp: str
    status: str  # ProcessingStatus value
    error_logs: List[str]
    metadata: Dict[str, Any]


class AgentState(BaseState):
    """Base state for all agents"""
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    execution_time: float
    retry_count: int


# ============= Agent-specific States =============

class SearchState(AgentState):
    """Search agent state"""
    query: str
    search_type: str  # hr_info, hr_rules, both
    filters: Dict[str, Any]
    keywords: List[str]
    hr_results: List[Dict[str, Any]]
    rules_results: List[Dict[str, Any]]
    relevance_scores: Dict[str, float]
    sources: List[str]
    final_results: Dict[str, Any]


class SalesState(AgentState):
    """Sales analytics agent state"""
    employee_name: str
    period: str  # daily, weekly, monthly, yearly
    metrics_type: str  # performance, revenue, targets
    raw_data: List[Dict[str, Any]]
    aggregated_data: Dict[str, Any]
    statistics: Dict[str, float]
    charts_data: List[Dict[str, Any]]
    insights: List[str]
    final_report: Dict[str, Any]


class ComplianceState(AgentState):
    """Compliance check agent state"""
    check_type: str  # policy, regulation, audit
    target_action: str
    context: Dict[str, Any]
    rules_checked: List[Dict[str, Any]]
    violations: List[Dict[str, Any]]
    recommendations: List[str]
    compliance_score: float
    is_compliant: bool
    compliance_report: Dict[str, Any]


class DocumentState(AgentState):
    """Document generation agent state"""
    document_type: str  # report, memo, presentation, email
    template_name: str
    input_content: Dict[str, Any]
    formatting_rules: Dict[str, Any]
    sections: List[Dict[str, Any]]
    generated_content: str
    document_format: str  # text, html, markdown, pdf
    final_document: Dict[str, Any]


# ============= Orchestrator States =============

class OrchestratorState(BaseState):
    """Main orchestrator state"""
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
    execution_status: Dict[str, str]

    # Response generation
    raw_results: Dict[str, Any]
    formatted_response: str
    response_format: str  # text, table, chart, mixed
    citations: List[Dict[str, Any]]

    # Final output
    final_response: str
    success: bool
    total_execution_time: float