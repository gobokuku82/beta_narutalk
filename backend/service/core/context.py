"""
Context definitions for all agents and orchestrator
Following LangGraph 0.6.x Context API patterns
"""

from typing import TypedDict, Optional, Dict, List, Any


class AgentContext(TypedDict):
    """
    Runtime context for all agents (required and optional fields)
    This is passed to agents via the context parameter in invoke/stream
    
    Required fields: Must always be present
    Optional fields: May be None or omitted
    """
    
    # ========== Required Fields ==========
    # These MUST be provided by supervisor/orchestrator
    user_id: str  # User identifier
    session_id: str  # Session identifier for conversation continuity
    
    # ========== Optional Fields ==========
    # These can be None or omitted
    request_id: Optional[str]  # Unique request identifier
    original_query: Optional[str]  # Original user query text
    
    # Authentication & API Keys
    api_keys: Optional[Dict[str, str]]  # API keys for various services
    
    # User permissions and settings
    permissions: Optional[List[str]]  # User permissions list
    language: Optional[str]  # User's preferred language (default: 'ko')
    timezone: Optional[str]  # User's timezone
    
    # Database and storage
    db_connections: Optional[Dict[str, str]]  # Database connection strings
    db_paths: Optional[Dict[str, str]]  # File-based database paths
    
    # Runtime configuration
    timeout: Optional[int]  # Operation timeout in seconds
    max_retries: Optional[int]  # Maximum retry attempts
    debug_mode: Optional[bool]  # Enable debug logging
    
    # Feature flags
    feature_flags: Optional[Dict[str, bool]]  # Feature toggles
    
    # Intent and planning (from supervisor/orchestrator)
    intent_result: Optional[Dict[str, Any]]  # Intent analysis result
    supervisor_context: Optional[Dict[str, Any]]  # Additional context from supervisor
    
    # Execution hints (for subgraphs)
    suggested_tools: Optional[List[str]]  # Tool usage hints
    analysis_depth: Optional[str]  # Analysis depth: shallow, normal, deep
    
    # Async execution
    parallel_execution: Optional[bool]  # Enable parallel processing
    
    # Error handling
    error_handling_mode: Optional[str]  # strict, lenient, fallback
    
    # Caching
    cache_enabled: Optional[bool]  # Enable caching
    cache_ttl: Optional[int]  # Cache time-to-live in seconds


class SubgraphContext(TypedDict):
    """
    Context specifically for subgraphs
    Inherits from parent agent's context but may have additional fields
    """
    
    # Required (inherited from parent)
    user_id: str
    session_id: str
    
    # Optional (inherited from parent)
    request_id: Optional[str]
    language: Optional[str]
    timeout: Optional[int]
    debug_mode: Optional[bool]
    
    # Subgraph-specific
    parent_agent: Optional[str]  # Name of parent agent
    subgraph_name: Optional[str]  # Name of current subgraph
    iteration: Optional[int]  # Iteration number if in loop
    
    # Data paths (for data collection subgraphs)
    db_paths: Optional[Dict[str, str]]
    
    # Analysis parameters (for analysis subgraphs)
    analysis_depth: Optional[str]
    include_predictions: Optional[bool]
    suggested_tools: Optional[List[str]]
    
    # Execution control
    parallel_execution: Optional[bool]
    max_workers: Optional[int]


class SupervisorContext(TypedDict):
    """
    Context for the main supervisor/orchestrator
    Contains global settings and coordination data
    """
    
    # Required fields
    user_id: str
    session_id: str
    conversation_id: str  # Long-term conversation identifier
    
    # Optional fields
    request_id: Optional[str]
    original_query: Optional[str]
    
    # User profile and settings
    user_profile: Optional[Dict[str, Any]]  # User profile data
    user_preferences: Optional[Dict[str, Any]]  # User preferences
    
    # Organization and team
    organization_id: Optional[str]
    team_id: Optional[str]
    department: Optional[str]
    
    # Global configuration
    api_keys: Optional[Dict[str, str]]
    feature_flags: Optional[Dict[str, bool]]
    
    # Coordination data
    active_agents: Optional[List[str]]  # Currently active agents
    agent_dependencies: Optional[Dict[str, List[str]]]  # Agent dependencies
    execution_order: Optional[List[str]]  # Execution sequence
    
    # Resource limits
    max_execution_time: Optional[int]  # Maximum total execution time
    max_parallel_agents: Optional[int]  # Maximum parallel agents
    
    # Monitoring and logging
    enable_monitoring: Optional[bool]
    log_level: Optional[str]  # debug, info, warning, error
    trace_id: Optional[str]  # Distributed tracing ID


# ========== Helper Functions ==========

def create_agent_context(
    user_id: str,
    session_id: str,
    **kwargs
) -> AgentContext:
    """
    Create an AgentContext with required fields and optional kwargs
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        **kwargs: Optional context fields
        
    Returns:
        AgentContext with all fields properly set
    """
    context = AgentContext(
        user_id=user_id,
        session_id=session_id,
        request_id=kwargs.get('request_id'),
        original_query=kwargs.get('original_query'),
        api_keys=kwargs.get('api_keys'),
        permissions=kwargs.get('permissions'),
        language=kwargs.get('language', 'ko'),
        timezone=kwargs.get('timezone'),
        db_connections=kwargs.get('db_connections'),
        db_paths=kwargs.get('db_paths'),
        timeout=kwargs.get('timeout', 30),
        max_retries=kwargs.get('max_retries', 3),
        debug_mode=kwargs.get('debug_mode', False),
        feature_flags=kwargs.get('feature_flags', {}),
        intent_result=kwargs.get('intent_result'),
        supervisor_context=kwargs.get('supervisor_context'),
        suggested_tools=kwargs.get('suggested_tools'),
        analysis_depth=kwargs.get('analysis_depth', 'normal'),
        parallel_execution=kwargs.get('parallel_execution', False),
        error_handling_mode=kwargs.get('error_handling_mode', 'strict'),
        cache_enabled=kwargs.get('cache_enabled', True),
        cache_ttl=kwargs.get('cache_ttl', 300)
    )
    return context


def inherit_context(
    parent_context: AgentContext,
    **overrides
) -> AgentContext:
    """
    Create a new context inheriting from parent with overrides
    
    Args:
        parent_context: Parent agent's context
        **overrides: Fields to override or add
        
    Returns:
        New AgentContext with inherited and overridden values
    """
    # Start with parent context
    new_context = dict(parent_context)
    
    # Apply overrides
    new_context.update(overrides)
    
    return AgentContext(**new_context)


def create_subgraph_context(
    parent_context: AgentContext,
    subgraph_name: str,
    **kwargs
) -> SubgraphContext:
    """
    Create a SubgraphContext from parent agent's context
    
    Args:
        parent_context: Parent agent's context
        subgraph_name: Name of the subgraph
        **kwargs: Additional subgraph-specific fields
        
    Returns:
        SubgraphContext for the subgraph
    """
    context = SubgraphContext(
        user_id=parent_context['user_id'],
        session_id=parent_context['session_id'],
        request_id=parent_context.get('request_id'),
        language=parent_context.get('language'),
        timeout=parent_context.get('timeout'),
        debug_mode=parent_context.get('debug_mode'),
        parent_agent=kwargs.get('parent_agent'),
        subgraph_name=subgraph_name,
        iteration=kwargs.get('iteration'),
        db_paths=kwargs.get('db_paths') or parent_context.get('db_paths'),
        analysis_depth=kwargs.get('analysis_depth') or parent_context.get('analysis_depth'),
        include_predictions=kwargs.get('include_predictions'),
        suggested_tools=kwargs.get('suggested_tools') or parent_context.get('suggested_tools'),
        parallel_execution=kwargs.get('parallel_execution') or parent_context.get('parallel_execution'),
        max_workers=kwargs.get('max_workers')
    )
    return context
