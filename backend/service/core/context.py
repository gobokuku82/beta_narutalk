"""
Context Definitions for LangGraph 0.6.x
Runtime metadata passed through the context parameter
Cleaned version - removed unused code
"""

from typing import TypedDict, Optional, Dict, List, Any
import os
from datetime import datetime
import uuid


# ============ Agent Context (Active) ============

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

    # ========== Authentication ==========
    api_keys: Optional[Dict[str, str]]  # Service API keys (runtime injection)

    # ========== User Settings ==========
    language: Optional[str]     # User language (ko, en, etc.)

    # ========== Runtime Configuration ==========
    timeout_overrides: Optional[Dict[str, int]]  # Override timeouts

    # ========== Execution Control ==========
    debug_mode: Optional[bool]  # Enable debug logging
    dry_run: Optional[bool]     # Simulation mode
    strict_mode: Optional[bool]  # Strict error handling
    max_retries: Optional[int]  # Override retry count


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
        "language": kwargs.get("language", "ko"),
        "timeout_overrides": kwargs.get("timeout_overrides", {}),
        "debug_mode": kwargs.get("debug_mode", False),
        "dry_run": kwargs.get("dry_run", False),
        "strict_mode": kwargs.get("strict_mode", True),
        "max_retries": kwargs.get("max_retries"),
    })

    # Remove None values for cleaner context
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

    # Only add used timeouts
    for key in ["agent", "llm"]:
        if key not in context["timeout_overrides"]:
            context["timeout_overrides"][key] = Config.TIMEOUTS.get(key, 30)

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
    ]

    for key in key_patterns:
        value = os.getenv(key)
        if value:
            # Convert to lowercase key for consistency
            api_keys[key.lower()] = value

    return api_keys