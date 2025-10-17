"""
Registry Module
에이전트와 툴을 등록하고 관리하는 레지스트리 시스템
약한 결합(Loose Coupling)을 위한 패턴 구현
"""

from .base_registry import BaseRegistry, RegistryError
from .tool_registry import ToolRegistry, tool_registry, register_tool
from .agent_registry import AgentRegistry, agent_registry, register_agent, register_subgraph
from .registry_manager import RegistryManager, get_registry_manager

__all__ = [
    # Base
    "BaseRegistry",
    "RegistryError",

    # Tool Registry
    "ToolRegistry",
    "tool_registry",
    "register_tool",

    # Agent Registry
    "AgentRegistry",
    "agent_registry",
    "register_agent",
    "register_subgraph",

    # Manager
    "RegistryManager",
    "get_registry_manager"
]
