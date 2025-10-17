"""
Registry Manager
모든 레지스트리를 통합 관리하는 매니저
"""

import logging
from typing import Dict, Any, Optional, List, Type
from pathlib import Path
import json

from .tool_registry import ToolRegistry, tool_registry
from .agent_registry import AgentRegistry, agent_registry, AgentType
from .base_registry import RegistryError


logger = logging.getLogger(__name__)


class RegistryManager:
    """
    Registry Manager
    툴과 에이전트 레지스트리를 통합 관리
    """

    def __init__(
        self,
        tool_registry_instance: Optional[ToolRegistry] = None,
        agent_registry_instance: Optional[AgentRegistry] = None
    ):
        """
        Initialize registry manager

        Args:
            tool_registry_instance: Tool registry (uses global if None)
            agent_registry_instance: Agent registry (uses global if None)
        """
        self.tool_registry = tool_registry_instance or tool_registry
        self.agent_registry = agent_registry_instance or agent_registry
        self._logger = logging.getLogger(__name__)
        self._logger.info("Registry Manager initialized")

    # ============== Tool Management ==============

    def register_tool(self, name: str, tool_class: Type[Any], **kwargs) -> None:
        """Register a tool"""
        self.tool_registry.register_tool(name=name, tool_class=tool_class, **kwargs)

    def get_tool(self, name: str) -> Optional[Type[Any]]:
        """Get a tool class"""
        return self.tool_registry.get_tool(name)

    def create_tool(self, name: str, *args, **kwargs) -> Any:
        """Create a tool instance"""
        return self.tool_registry.create_tool(name, *args, **kwargs)

    def list_tools(self, category: Optional[str] = None) -> List[str]:
        """
        List tools

        Args:
            category: Optional category filter

        Returns:
            List of tool names
        """
        if category:
            return self.tool_registry.list_by_category(category)
        return self.tool_registry.list_all()

    # ============== Agent Management ==============

    def register_agent(self, name: str, agent_class: Type[Any], **kwargs) -> None:
        """Register an agent"""
        self.agent_registry.register_agent(name=name, agent_class=agent_class, **kwargs)

    def register_subgraph(self, name: str, subgraph_class: Type[Any], **kwargs) -> None:
        """Register a subgraph"""
        self.agent_registry.register_subgraph(name=name, subgraph_class=subgraph_class, **kwargs)

    def get_agent(self, name: str) -> Optional[Type[Any]]:
        """Get an agent class"""
        return self.agent_registry.get_agent(name)

    def create_agent(self, name: str, *args, **kwargs) -> Any:
        """Create an agent instance"""
        return self.agent_registry.create_agent(name, *args, **kwargs)

    def list_agents(self, agent_type: Optional[AgentType] = None) -> List[str]:
        """
        List agents

        Args:
            agent_type: Optional type filter

        Returns:
            List of agent names
        """
        if agent_type:
            return self.agent_registry.list_by_type(agent_type)
        return self.agent_registry.list_all()

    # ============== Dependency Management ==============

    def validate_agent_dependencies(self, agent_name: str) -> tuple[bool, List[str]]:
        """
        Validate agent dependencies

        Args:
            agent_name: Agent name to validate

        Returns:
            Tuple of (is_valid, missing_dependencies)
        """
        is_valid, missing = self.agent_registry.validate_dependencies(agent_name)

        # Also check if dependencies are tools
        dependencies = self.agent_registry.get_dependencies(agent_name)
        for dep in dependencies:
            # Check if it's a tool
            if not self.agent_registry.has(dep) and not self.tool_registry.has(dep):
                if dep not in missing:
                    missing.append(dep)
                is_valid = False

        return is_valid, missing

    def resolve_dependencies(self, agent_name: str) -> Dict[str, Any]:
        """
        Resolve and create all dependencies for an agent

        Args:
            agent_name: Agent name

        Returns:
            Dictionary of dependency instances

        Raises:
            RegistryError: If dependencies cannot be resolved
        """
        is_valid, missing = self.validate_agent_dependencies(agent_name)
        if not is_valid:
            raise RegistryError(
                f"Cannot resolve dependencies for '{agent_name}'. Missing: {missing}"
            )

        dependencies = self.agent_registry.get_dependencies(agent_name)
        resolved = {}

        for dep_name in dependencies:
            # Try to get from agent registry first
            if self.agent_registry.has(dep_name):
                resolved[dep_name] = self.agent_registry.create_agent(dep_name)
            # Then try tool registry
            elif self.tool_registry.has(dep_name):
                resolved[dep_name] = self.tool_registry.create_tool(dep_name)
            else:
                self._logger.warning(f"Dependency '{dep_name}' not found")

        return resolved

    # ============== Search and Discovery ==============

    def search(self, query: str) -> Dict[str, List[str]]:
        """
        Search across all registries

        Args:
            query: Search query

        Returns:
            Dictionary with 'tools' and 'agents' lists
        """
        return {
            "tools": self.tool_registry.search(query),
            "agents": self.agent_registry.search(query)
        }

    def find_by_capability(self, capability: str) -> List[str]:
        """
        Find agents by capability

        Args:
            capability: Capability to search for

        Returns:
            List of agent names
        """
        return self.agent_registry.find_by_capability(capability)

    def get_tool_categories(self) -> List[str]:
        """Get all tool categories"""
        return self.tool_registry.list_categories()

    def get_agent_types(self) -> List[str]:
        """Get all agent types"""
        return [at.value for at in AgentType]

    # ============== Statistics ==============

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get registry statistics

        Returns:
            Statistics dictionary
        """
        return {
            "tools": {
                "total": self.tool_registry.count(),
                "categories": {
                    cat: len(self.tool_registry.list_by_category(cat))
                    for cat in self.tool_registry.list_categories()
                }
            },
            "agents": {
                "total": self.agent_registry.count(),
                "by_type": {
                    at.value: len(self.agent_registry.list_by_type(at))
                    for at in AgentType
                }
            }
        }

    def get_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a tool or agent

        Args:
            name: Tool or agent name

        Returns:
            Information dictionary or None
        """
        # Try tool registry first
        info = self.tool_registry.get_tool_info(name)
        if info:
            info["registry"] = "tool"
            return info

        # Try agent registry
        info = self.agent_registry.get_agent_info(name)
        if info:
            info["registry"] = "agent"
            return info

        return None

    # ============== Export/Import ==============

    def export_all(self) -> Dict[str, Any]:
        """
        Export all registries

        Returns:
            Complete registry state
        """
        return {
            "tool_registry": self.tool_registry.export(),
            "agent_registry": self.agent_registry.export()
        }

    def save_to_file(self, file_path: Path) -> None:
        """
        Save registry state to file

        Args:
            file_path: Path to save to
        """
        data = self.export_all()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        self._logger.info(f"Saved registry state to {file_path}")

    def load_from_file(self, file_path: Path) -> None:
        """
        Load registry state from file

        Args:
            file_path: Path to load from
        """
        # TODO: Implement loading
        # This would require re-registering classes from module paths
        self._logger.warning("Loading from file not yet implemented")

    # ============== Validation ==============

    def validate_all(self) -> Dict[str, Any]:
        """
        Validate all registries

        Returns:
            Validation results
        """
        results = {
            "valid": True,
            "issues": []
        }

        # Validate all agents
        for agent_name in self.agent_registry.list_all():
            is_valid, missing = self.validate_agent_dependencies(agent_name)
            if not is_valid:
                results["valid"] = False
                results["issues"].append({
                    "type": "missing_dependencies",
                    "agent": agent_name,
                    "missing": missing
                })

        return results

    # ============== Display ==============

    def print_summary(self) -> None:
        """Print a summary of all registries"""
        stats = self.get_statistics()

        print("\n" + "=" * 60)
        print("Registry Summary")
        print("=" * 60)

        print(f"\nTools: {stats['tools']['total']}")
        for category, count in stats['tools']['categories'].items():
            print(f"  - {category}: {count}")

        print(f"\nAgents: {stats['agents']['total']}")
        for agent_type, count in stats['agents']['by_type'].items():
            print(f"  - {agent_type}: {count}")

        print("\n" + "=" * 60)


# Global registry manager instance
_registry_manager: Optional[RegistryManager] = None


def get_registry_manager() -> RegistryManager:
    """
    Get global registry manager instance

    Returns:
        RegistryManager instance
    """
    global _registry_manager
    if _registry_manager is None:
        _registry_manager = RegistryManager()
    return _registry_manager


def reset_registry_manager() -> None:
    """Reset global registry manager (useful for testing)"""
    global _registry_manager
    _registry_manager = None
