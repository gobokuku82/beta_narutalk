"""
Pydantic schemas for database API
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Message role enum"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class AgentType(str, Enum):
    """Agent type enum"""
    SUPERVISOR = "supervisor"
    QUERY_ANALYZER = "query_analyzer"
    PLANNER = "planner"
    EXECUTOR = "executor"
    DATA_ANALYSIS = "data_analysis"
    INFO_RETRIEVAL = "info_retrieval"
    DOC_GENERATION = "doc_generation"
    COMPLIANCE = "compliance"
    STORAGE = "storage"


class ExecutionStatus(str, Enum):
    """Execution status enum"""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


# Base schemas
class BaseSchema(BaseModel):
    """Base schema with common config"""
    model_config = ConfigDict(from_attributes=True)


# Conversation schemas
class ConversationBase(BaseSchema):
    """Base conversation schema"""
    user_id: str
    session_id: str
    company_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ConversationCreate(ConversationBase):
    """Schema for creating conversation"""
    pass


class ConversationResponse(ConversationBase):
    """Schema for conversation response"""
    id: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    status: ExecutionStatus = ExecutionStatus.INITIALIZING


# Message schemas
class MessageBase(BaseSchema):
    """Base message schema"""
    conversation_id: str
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MessageCreate(MessageBase):
    """Schema for creating message"""
    pass


class MessageResponse(MessageBase):
    """Schema for message response"""
    id: str
    created_at: datetime
    sequence_number: int


# Agent State schemas
class AgentStateBase(BaseSchema):
    """Base agent state schema"""
    conversation_id: str
    agent_name: AgentType
    state_data: Dict[str, Any]
    task_id: Optional[str] = None
    execution_status: ExecutionStatus = ExecutionStatus.INITIALIZING


class AgentStateCreate(AgentStateBase):
    """Schema for creating agent state"""
    pass


class AgentStateResponse(AgentStateBase):
    """Schema for agent state response"""
    id: str
    created_at: datetime
    updated_at: datetime
    execution_time: Optional[float] = None
    confidence_score: Optional[float] = None


# Analysis Result schemas
class AnalysisResultBase(BaseSchema):
    """Base analysis result schema"""
    conversation_id: str
    agent_name: AgentType
    result_type: str
    result_data: Dict[str, Any]
    query: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AnalysisResultCreate(AnalysisResultBase):
    """Schema for creating analysis result"""
    pass


class AnalysisResultResponse(AnalysisResultBase):
    """Schema for analysis result response"""
    id: str
    created_at: datetime
    confidence_score: Optional[float] = None


# Global Session State schema
class GlobalSessionState(BaseSchema):
    """Global session state for LangGraph"""
    session_id: str
    user_id: str
    company_id: Optional[str] = None

    # Conversation management
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)

    # Workflow state
    current_phase: str = "analyzing"
    current_agent: Optional[str] = None
    workflow_status: Dict[str, Any] = Field(default_factory=dict)

    # Progress tracking
    iteration_count: int = 0
    execution_steps: List[Dict[str, Any]] = Field(default_factory=list)
    progress_percentage: float = 0.0

    # Resource tracking
    total_tokens_used: int = 0
    api_calls_made: Dict[str, int] = Field(default_factory=dict)
    db_queries_executed: int = 0

    # Agent states
    query_analyzer_state: Optional[Dict[str, Any]] = None
    planning_state: Optional[Dict[str, Any]] = None
    execution_manager_state: Optional[Dict[str, Any]] = None
    agent_states: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    # Results
    final_response: Optional[str] = None
    response_metadata: Dict[str, Any] = Field(default_factory=dict)

    # Errors and warnings
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)

    # Audit trail
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list)


# Query Analyzer State schema
class QueryAnalyzerState(BaseSchema):
    """Query analyzer agent state"""
    raw_query: str
    query_timestamp: str
    user_context: Dict[str, Any] = Field(default_factory=dict)

    # Analysis results
    parsed_intents: List[Dict[str, Any]] = Field(default_factory=list)
    required_capabilities: List[str] = Field(default_factory=list)
    complexity_score: float = 0.0
    suggested_agents: List[str] = Field(default_factory=list)
    context_requirements: Dict[str, Any] = Field(default_factory=dict)

    # Entity extraction
    extracted_entities: List[Dict[str, Any]] = Field(default_factory=list)

    # Ambiguity handling
    ambiguities: List[Dict[str, Any]] = Field(default_factory=list)
    clarification_needed: bool = False

    # Feasibility
    feasibility_check: Dict[str, Any] = Field(default_factory=dict)


# Planning State schema
class PlanningState(BaseSchema):
    """Planning agent state"""
    analyzed_query: Dict[str, Any]

    # Execution plan
    execution_plan: List[Dict[str, Any]] = Field(default_factory=list)
    task_dependencies: Dict[str, List[str]] = Field(default_factory=dict)
    dependency_graph: Dict[str, Any] = Field(default_factory=dict)

    # Resource planning
    resource_requirements: Dict[str, Any] = Field(default_factory=dict)
    estimated_steps: int = 0
    priority_order: List[str] = Field(default_factory=list)
    parallel_opportunities: List[List[str]] = Field(default_factory=list)

    # Fallback plans
    fallback_plans: List[Dict[str, Any]] = Field(default_factory=list)
    contingency_triggers: Dict[str, Any] = Field(default_factory=dict)


# Execution Manager State schema
class ExecutionManagerState(BaseSchema):
    """Execution manager state"""
    current_plan: Dict[str, Any]
    active_step: Optional[str] = None

    # Execution status
    execution_status: ExecutionStatus = ExecutionStatus.INITIALIZING
    execution_progress: float = 0.0

    # Task tracking
    completed_tasks: List[Dict[str, Any]] = Field(default_factory=list)
    pending_tasks: List[Dict[str, Any]] = Field(default_factory=list)
    failed_tasks: List[Dict[str, Any]] = Field(default_factory=list)

    # Quality management
    quality_scores: Dict[str, float] = Field(default_factory=dict)
    validation_results: Dict[str, Any] = Field(default_factory=dict)

    # Replan management
    need_replan: bool = False
    replan_reason: Optional[str] = None
    replan_attempts: int = 0

    # Final results
    final_results: Optional[Dict[str, Any]] = None
    aggregation_method: Optional[str] = None


# Database statistics schema
class DatabaseStatistics(BaseSchema):
    """Database statistics"""
    total_conversations: int
    total_messages: int
    total_agent_states: int
    total_analysis_results: int
    active_conversations: int
    avg_messages_per_conversation: float
    most_active_agents: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]