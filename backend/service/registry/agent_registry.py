"""
Agent Registry
에이전트와 서브그래프를 등록하고 관리하는 레지스트리
"""

import logging
from typing import Type, Any, Callable, Optional, Dict, List
from enum import Enum

from .base_registry import BaseRegistry, RegistryError


logger = logging.getLogger(__name__)


class AgentType(Enum):
    """에이전트 타입"""
    SUPERVISOR = "supervisor"
    SUBGRAPH = "subgraph"
    WORKER = "worker"
    TOOL = "tool"
    CUSTOM = "custom"


class AgentRegistry(BaseRegistry):
    """
    Agent Registry
    에이전트와 서브그래프를 등록하고 조회하는 레지스트리
    """

    def __init__(self):
        super().__init__(name="AgentRegistry")
        self._agent_types: Dict[AgentType, List[str]] = {
            agent_type: [] for agent_type in AgentType
        }
        self._dependencies: Dict[str, List[str]] = {}

    def register_agent(
        self,
        name: str,
        agent_class: Type[Any],
        agent_type: AgentType = AgentType.CUSTOM,
        description: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        capabilities: Optional[List[str]] = None,
        version: str = "1.0.0",
        override: bool = False,
        **kwargs
    ) -> None:
        """
        Register an agent

        Args:
            name: Unique agent identifier
            agent_class: Agent class to register
            agent_type: Type of agent
            description: Agent description
            dependencies: List of required tool/agent names
            capabilities: List of capabilities
            version: Version string
            override: Whether to override existing agent
            **kwargs: Additional metadata
        """
        metadata = {
            "class_name": agent_class.__name__,
            "module": agent_class.__module__,
            "description": description or agent_class.__doc__,
            "agent_type": agent_type.value,
            "dependencies": dependencies or [],
            "capabilities": capabilities or [],
            **kwargs
        }

        tags = [agent_type.value]
        if capabilities:
            tags.extend(capabilities)

        self.register(
            name=name,
            item=agent_class,
            metadata=metadata,
            tags=tags,
            version=version,
            override=override
        )

        # Track by type
        if name not in self._agent_types[agent_type]:
            self._agent_types[agent_type].append(name)

        # Track dependencies
        if dependencies:
            self._dependencies[name] = dependencies

    def register_subgraph(
        self,
        name: str,
        subgraph_class: Type[Any],
        description: Optional[str] = None,
        input_state: Optional[Type[Any]] = None,
        output_state: Optional[Type[Any]] = None,
        dependencies: Optional[List[str]] = None,
        version: str = "1.0.0",
        override: bool = False,
        **kwargs
    ) -> None:
        """
        Register a subgraph

        Args:
            name: Unique subgraph identifier
            subgraph_class: Subgraph class
            description: Subgraph description
            input_state: Input state type
            output_state: Output state type
            dependencies: Required dependencies
            version: Version string
            override: Whether to override existing
            **kwargs: Additional metadata
        """
        additional_metadata = {
            "input_state": input_state.__name__ if input_state else None,
            "output_state": output_state.__name__ if output_state else None,
            **kwargs
        }

        self.register_agent(
            name=name,
            agent_class=subgraph_class,
            agent_type=AgentType.SUBGRAPH,
            description=description,
            dependencies=dependencies,
            version=version,
            override=override,
            **additional_metadata
        )

    def get_agent(self, name: str) -> Optional[Type[Any]]:
        """
        Get agent class by name

        Args:
            name: Agent name

        Returns:
            Agent class or None
        """
        return self.get(name)

    def create_agent(self, name: str, *args, **kwargs) -> Any:
        """
        Create agent instance

        Args:
            name: Agent name
            *args: Constructor arguments
            **kwargs: Constructor keyword arguments

        Returns:
            Agent instance

        Raises:
            RegistryError: If agent not found or dependencies missing
        """
        agent_class = self.get_agent(name)
        if agent_class is None:
            raise RegistryError(f"Agent '{name}' not found in registry")

        # Check dependencies
        dependencies = self._dependencies.get(name, [])
        if dependencies:
            self._logger.info(f"Agent '{name}' has dependencies: {dependencies}")
            # Could validate dependencies here

        try:
            instance = agent_class(*args, **kwargs)
            self._logger.info(f"Created instance of agent '{name}'")
            return instance
        except Exception as e:
            self._logger.error(f"Error creating agent '{name}': {e}")
            raise RegistryError(f"Failed to create agent '{name}': {str(e)}")

    def list_by_type(self, agent_type: AgentType) -> List[str]:
        """
        List agents by type

        Args:
            agent_type: Agent type to filter by

        Returns:
            List of agent names
        """
        return self._agent_types.get(agent_type, [])

    def list_supervisors(self) -> List[str]:
        """List all supervisor agents"""
        return self.list_by_type(AgentType.SUPERVISOR)

    def list_subgraphs(self) -> List[str]:
        """List all subgraph agents"""
        return self.list_by_type(AgentType.SUBGRAPH)

    def list_workers(self) -> List[str]:
        """List all worker agents"""
        return self.list_by_type(AgentType.WORKER)

    def get_dependencies(self, name: str) -> List[str]:
        """
        Get dependencies for an agent

        Args:
            name: Agent name

        Returns:
            List of dependency names
        """
        return self._dependencies.get(name, [])

    def get_agent_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed agent information

        Args:
            name: Agent name

        Returns:
            Agent information dictionary
        """
        info = self.get_info(name)
        if not info:
            return None

        agent_class = self.get_agent(name)
        if agent_class:
            # Add class information
            info["class"] = agent_class.__name__
            info["module"] = agent_class.__module__

            # Get methods
            methods = [
                method for method in dir(agent_class)
                if not method.startswith("_") and callable(getattr(agent_class, method))
            ]
            info["methods"] = methods

            # Add dependencies
            info["dependencies"] = self.get_dependencies(name)

        return info

    def get_dependency_tree(self, name: str, visited: Optional[set] = None) -> Dict[str, Any]:
        """
        Get dependency tree for an agent

        Args:
            name: Agent name
            visited: Set of visited agents (for cycle detection)

        Returns:
            Dependency tree as nested dictionary
        """
        if visited is None:
            visited = set()

        if name in visited:
            return {"name": name, "cyclic": True}

        if not self.has(name):
            return {"name": name, "missing": True}

        visited.add(name)
        dependencies = self.get_dependencies(name)

        tree = {
            "name": name,
            "dependencies": [
                self.get_dependency_tree(dep, visited.copy())
                for dep in dependencies
            ]
        }

        return tree

    def validate_dependencies(self, name: str) -> tuple[bool, List[str]]:
        """
        Validate that all dependencies are available

        Args:
            name: Agent name

        Returns:
            Tuple of (is_valid, missing_dependencies)
        """
        if not self.has(name):
            return False, [name]

        dependencies = self.get_dependencies(name)
        missing = []

        for dep in dependencies:
            if not self.has(dep):
                missing.append(dep)
            else:
                # Recursively check dependencies
                is_valid, sub_missing = self.validate_dependencies(dep)
                if not is_valid:
                    missing.extend(sub_missing)

        return len(missing) == 0, missing

    def find_by_capability(self, capability: str) -> List[str]:
        """
        Find agents by capability

        Args:
            capability: Capability to search for

        Returns:
            List of agent names with the capability
        """
        result = []
        for name in self.list_all():
            metadata = self.get_metadata(name)
            if metadata:
                capabilities = metadata.get("capabilities", [])
                if capability in capabilities:
                    result.append(name)
        return result


# Global agent registry instance
agent_registry = AgentRegistry()


def register_agent(
    name: Optional[str] = None,
    agent_type: AgentType = AgentType.CUSTOM,
    description: Optional[str] = None,
    dependencies: Optional[List[str]] = None,
    capabilities: Optional[List[str]] = None,
    version: str = "1.0.0",
    **kwargs
) -> Callable:
    """
    Decorator to register an agent class

    Args:
        name: Agent name (defaults to class name)
        agent_type: Type of agent
        description: Agent description
        dependencies: Required dependencies
        capabilities: Agent capabilities
        version: Version string
        **kwargs: Additional metadata

    Returns:
        Decorator function

    Example:
        @register_agent(
            name="data_collector",
            agent_type=AgentType.WORKER,
            capabilities=["data_collection", "sql_query"]
        )
        class DataCollectorAgent:
            pass
    """
    def decorator(cls: Type[Any]) -> Type[Any]:
        agent_name = name or cls.__name__
        agent_registry.register_agent(
            name=agent_name,
            agent_class=cls,
            agent_type=agent_type,
            description=description or cls.__doc__,
            dependencies=dependencies,
            capabilities=capabilities,
            version=version,
            **kwargs
        )
        return cls

    return decorator


def register_subgraph(
    name: Optional[str] = None,
    description: Optional[str] = None,
    input_state: Optional[Type[Any]] = None,
    output_state: Optional[Type[Any]] = None,
    dependencies: Optional[List[str]] = None,
    version: str = "1.0.0",
    **kwargs
) -> Callable:
    """
    Decorator to register a subgraph

    Args:
        name: Subgraph name
        description: Description
        input_state: Input state type
        output_state: Output state type
        dependencies: Required dependencies
        version: Version string
        **kwargs: Additional metadata

    Returns:
        Decorator function

    Example:
        @register_subgraph(
            name="data_collection",
            input_state=DataCollectionState,
            dependencies=["sql_executor", "sql_generator"]
        )
        class DataCollectionSubgraph:
            pass
    """
    def decorator(cls: Type[Any]) -> Type[Any]:
        subgraph_name = name or cls.__name__
        agent_registry.register_subgraph(
            name=subgraph_name,
            subgraph_class=cls,
            description=description or cls.__doc__,
            input_state=input_state,
            output_state=output_state,
            dependencies=dependencies,
            version=version,
            **kwargs
        )
        return cls

    return decorator
