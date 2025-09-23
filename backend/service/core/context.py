"""
Context schema for LangGraph Context API
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class BaseContext:
    """
    Base context for all agents - immutable runtime context
    Contains metadata that doesn't change during workflow execution
    """
    user_id: str
    session_id: str
    timestamp: str
    request_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize optional fields"""
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

        if self.metadata is None:
            self.metadata = {}

        if self.request_id is None:
            import uuid
            self.request_id = str(uuid.uuid4())


@dataclass
class AgentContext(BaseContext):
    """
    Extended context for individual agents
    Can be customized per agent if needed
    """
    agent_name: Optional[str] = None
    timeout: Optional[int] = 30
    retry_count: Optional[int] = 0
    max_retries: Optional[int] = 3

    # Error tracking (separate from State)
    error_logs: Optional[List[str]] = None

    def __post_init__(self):
        """Initialize fields"""
        super().__post_init__()
        if self.error_logs is None:
            self.error_logs = []

    def add_error(self, error: str):
        """Add error to context"""
        if self.error_logs is None:
            self.error_logs = []
        self.error_logs.append(f"[{datetime.now().isoformat()}] {error}")

    def clear_errors(self):
        """Clear all errors"""
        self.error_logs = []


@dataclass
class OrchestratorContext(BaseContext):
    """
    Context for the main orchestrator
    Contains high-level execution metadata
    """
    execution_mode: str = "sequential"  # sequential, parallel
    total_timeout: int = 60
    enable_checkpointing: bool = True
    enable_retry: bool = True

    # Tracking
    executed_agents: Optional[List[str]] = None
    execution_times: Optional[Dict[str, float]] = None

    def __post_init__(self):
        """Initialize tracking fields"""
        super().__post_init__()
        if self.executed_agents is None:
            self.executed_agents = []
        if self.execution_times is None:
            self.execution_times = {}


def create_context(
    user_id: str,
    session_id: str,
    context_type: str = "base",
    **kwargs
) -> BaseContext:
    """
    Factory function to create appropriate context

    Args:
        user_id: User identifier
        session_id: Session identifier
        context_type: Type of context (base, agent, orchestrator)
        **kwargs: Additional context parameters

    Returns:
        Appropriate context instance
    """
    base_params = {
        "user_id": user_id,
        "session_id": session_id,
        "timestamp": datetime.now().isoformat(),
        **kwargs
    }

    if context_type == "agent":
        return AgentContext(**base_params)
    elif context_type == "orchestrator":
        return OrchestratorContext(**base_params)
    else:
        return BaseContext(**base_params)