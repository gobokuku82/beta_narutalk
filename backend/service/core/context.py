"""
Context Definitions for LangGraph 0.6.x
Runtime metadata passed through the context parameter
"""

from typing import TypedDict, Optional, Dict, List, Any
import os
from datetime import datetime
import uuid


# ============ Context Definitions ============

class AgentContext(TypedDict):
    """
    Runtime context for agents
    Contains metadata and configuration passed at execution time
    This is READ-ONLY during execution
    """
    
    # ========== Required Fields ==========
    user_id: str                # User identifier
    session_id: str             # Session identifier
    
    # ========== Optional Runtime Info ==========
    request_id: Optional[str]   # Unique request ID
    timestamp: Optional[str]    # Request timestamp
    original_query: Optional[str]  # Original user input
    
    # ========== Authentication & Security ==========
    api_keys: Optional[Dict[str, str]]  # Service API keys (runtime injection)
    auth_token: Optional[str]   # Authentication token
    permissions: Optional[List[str]]  # User permissions
    
    # ========== User Settings ==========
    language: Optional[str]     # User language (ko, en, etc.)
    timezone: Optional[str]     # User timezone
    preferences: Optional[Dict[str, Any]]  # User preferences
    
    # ========== Runtime Configuration ==========
    # These can override Config defaults
    model_overrides: Optional[Dict[str, str]]  # Override default models
    timeout_overrides: Optional[Dict[str, int]]  # Override timeouts
    feature_flags: Optional[Dict[str, bool]]  # User-specific features
    
    # ========== Execution Control ==========
    debug_mode: Optional[bool]  # Enable debug logging
    dry_run: Optional[bool]     # Simulation mode
    strict_mode: Optional[bool]  # Strict error handling
    max_retries: Optional[int]  # Override retry count
    
    # ========== Orchestration Data ==========
    # From supervisor/orchestrator
    intent_result: Optional[Dict[str, Any]]  # Intent analysis
    supervisor_hints: Optional[Dict[str, Any]]  # Execution hints
    parent_context: Optional[Dict[str, Any]]  # Parent agent context
    
    # ========== Database Connections ==========
    # Runtime database connections (if not using file-based)
    db_connections: Optional[Dict[str, str]]  # Connection strings
    db_credentials: Optional[Dict[str, Dict[str, str]]]  # DB credentials


class SubgraphContext(TypedDict):
    """
    Minimal context for subgraphs
    Filtered subset of AgentContext
    """
    
    # ========== Required (inherited) ==========
    user_id: str
    session_id: str
    
    # ========== Optional (filtered) ==========
    request_id: Optional[str]
    language: Optional[str]
    debug_mode: Optional[bool]
    
    # ========== Subgraph Specific ==========
    parent_agent: Optional[str]  # Parent agent name
    subgraph_name: Optional[str]  # Current subgraph
    iteration: Optional[int]     # Loop iteration
    
    # ========== Execution Hints ==========
    suggested_tools: Optional[List[str]]  # Tool hints
    analysis_depth: Optional[str]  # shallow, normal, deep
    parallel_execution: Optional[bool]  # Enable parallelism
    max_workers: Optional[int]   # Worker limit


class SupervisorContext(TypedDict):
    """
    Context for main supervisor/orchestrator
    Contains global coordination data
    """
    
    # ========== Required ==========
    user_id: str
    session_id: str
    conversation_id: str  # Long-term conversation ID
    
    # ========== Optional ==========
    request_id: Optional[str]
    timestamp: Optional[str]
    original_query: Optional[str]
    
    # ========== User Profile ==========
    user_profile: Optional[Dict[str, Any]]
    user_role: Optional[str]
    organization_id: Optional[str]
    department: Optional[str]
    
    # ========== Global Settings ==========
    api_keys: Optional[Dict[str, str]]
    global_features: Optional[Dict[str, bool]]
    global_limits: Optional[Dict[str, int]]
    
    # ========== Orchestration Control ==========
    execution_mode: Optional[str]  # sequential, parallel, adaptive
    priority_agents: Optional[List[str]]  # High priority agents
    excluded_agents: Optional[List[str]]  # Disabled agents
    
    # ========== Monitoring ==========
    trace_id: Optional[str]  # Distributed tracing
    monitoring_level: Optional[str]  # off, basic, detailed
    collect_metrics: Optional[bool]


# ============ Context Factory Functions ============

def create_agent_context(
    user_id: str,
    session_id: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Create AgentContext with required fields and optional values
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        **kwargs: Optional context fields
        
    Returns:
        Context dictionary ready for LangGraph
    """
    # Start with required fields
    context = {
        "user_id": user_id,
        "session_id": session_id,
        "request_id": kwargs.get("request_id") or f"req_{uuid.uuid4().hex[:8]}",
        "timestamp": kwargs.get("timestamp") or datetime.now().isoformat(),
    }
    
    # Add optional fields with defaults
    context.update({
        "original_query": kwargs.get("original_query"),
        "api_keys": kwargs.get("api_keys", {}),
        "auth_token": kwargs.get("auth_token"),
        "permissions": kwargs.get("permissions", []),
        "language": kwargs.get("language", "ko"),
        "timezone": kwargs.get("timezone", "Asia/Seoul"),
        "preferences": kwargs.get("preferences", {}),
        "model_overrides": kwargs.get("model_overrides", {}),
        "timeout_overrides": kwargs.get("timeout_overrides", {}),
        "feature_flags": kwargs.get("feature_flags", {}),
        "debug_mode": kwargs.get("debug_mode", False),
        "dry_run": kwargs.get("dry_run", False),
        "strict_mode": kwargs.get("strict_mode", True),
        "max_retries": kwargs.get("max_retries"),
        "intent_result": kwargs.get("intent_result"),
        "supervisor_hints": kwargs.get("supervisor_hints"),
        "parent_context": kwargs.get("parent_context"),
        "db_connections": kwargs.get("db_connections"),
        "db_credentials": kwargs.get("db_credentials")
    })
    
    # Remove None values for cleaner context
    return {k: v for k, v in context.items() if v is not None}


def create_subgraph_context(
    parent_context: Dict[str, Any],
    parent_agent: str,
    subgraph_name: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Create SubgraphContext from parent agent context
    
    Args:
        parent_context: Parent agent's context
        parent_agent: Parent agent name
        subgraph_name: Subgraph name
        **kwargs: Additional subgraph-specific fields
        
    Returns:
        Filtered context for subgraph
    """
    # Extract only necessary fields from parent
    context = {
        # Required
        "user_id": parent_context["user_id"],
        "session_id": parent_context["session_id"],
        
        # Optional from parent
        "request_id": parent_context.get("request_id"),
        "language": parent_context.get("language"),
        "debug_mode": parent_context.get("debug_mode"),
        
        # Subgraph specific
        "parent_agent": parent_agent,
        "subgraph_name": subgraph_name,
        "iteration": kwargs.get("iteration"),
        
        # Execution hints
        "suggested_tools": kwargs.get("suggested_tools"),
        "analysis_depth": kwargs.get("analysis_depth"),
        "parallel_execution": kwargs.get("parallel_execution", False),
        "max_workers": kwargs.get("max_workers")
    }
    
    # Remove None values
    return {k: v for k, v in context.items() if v is not None}


def create_supervisor_context(
    user_id: str,
    session_id: str,
    conversation_id: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Create SupervisorContext for orchestrator
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        conversation_id: Long-term conversation ID
        **kwargs: Additional supervisor fields
        
    Returns:
        Supervisor context dictionary
    """
    context = {
        # Required
        "user_id": user_id,
        "session_id": session_id,
        "conversation_id": conversation_id,
        "request_id": kwargs.get("request_id") or f"req_{uuid.uuid4().hex[:8]}",
        "timestamp": kwargs.get("timestamp") or datetime.now().isoformat(),
        
        # Optional
        "original_query": kwargs.get("original_query"),
        "user_profile": kwargs.get("user_profile"),
        "user_role": kwargs.get("user_role"),
        "organization_id": kwargs.get("organization_id"),
        "department": kwargs.get("department"),
        "api_keys": kwargs.get("api_keys", {}),
        "global_features": kwargs.get("global_features", {}),
        "global_limits": kwargs.get("global_limits", {}),
        "execution_mode": kwargs.get("execution_mode", "adaptive"),
        "priority_agents": kwargs.get("priority_agents", []),
        "excluded_agents": kwargs.get("excluded_agents", []),
        "trace_id": kwargs.get("trace_id") or f"trace_{uuid.uuid4().hex[:12]}",
        "monitoring_level": kwargs.get("monitoring_level", "basic"),
        "collect_metrics": kwargs.get("collect_metrics", True)
    }
    
    return {k: v for k, v in context.items() if v is not None}


def merge_with_config_defaults(
    context: Dict[str, Any],
    config: Any
) -> Dict[str, Any]:
    """
    Merge context with config defaults
    Context values take precedence
    
    Args:
        context: Runtime context
        config: Config instance
        
    Returns:
        Merged context with defaults
    """
    from .config import Config
    
    # Apply timeout defaults if not overridden
    if "timeout_overrides" not in context:
        context["timeout_overrides"] = {}
    
    for key, value in Config.TIMEOUTS.items():
        if key not in context["timeout_overrides"]:
            context["timeout_overrides"][key] = value
    
    # Apply model defaults if not overridden
    if "model_overrides" not in context:
        context["model_overrides"] = {}
    
    for key, value in Config.DEFAULT_MODELS.items():
        if key not in context["model_overrides"]:
            context["model_overrides"][key] = value
    
    # Apply feature flags
    if "feature_flags" not in context:
        context["feature_flags"] = {}
    
    for key, value in Config.FEATURES.items():
        if key not in context["feature_flags"]:
            context["feature_flags"][key] = value
    
    return context


def extract_api_keys_from_env() -> Dict[str, str]:
    """
    Extract API keys from environment variables
    
    Returns:
        Dictionary of API keys
    """
    api_keys = {}
    
    # Common API key patterns
    key_patterns = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY",
        "AZURE_API_KEY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY"
    ]
    
    for key in key_patterns:
        value = os.getenv(key)
        if value:
            # Convert to lowercase key for consistency
            api_keys[key.lower()] = value
    
    return api_keys
