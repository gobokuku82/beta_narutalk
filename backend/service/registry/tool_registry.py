"""
Tool Registry
툴을 등록하고 관리하는 레지스트리
"""

import logging
from typing import Type, Any, Callable, Optional, Dict, List
from functools import wraps

from .base_registry import BaseRegistry, RegistryError


logger = logging.getLogger(__name__)


class ToolRegistry(BaseRegistry):
    """
    Tool Registry
    툴을 등록하고 조회하는 레지스트리
    """

    def __init__(self):
        super().__init__(name="ToolRegistry")
        self._tool_categories: Dict[str, List[str]] = {}

    def register_tool(
        self,
        name: str,
        tool_class: Type[Any],
        category: Optional[str] = None,
        description: Optional[str] = None,
        version: str = "1.0.0",
        override: bool = False,
        **kwargs
    ) -> None:
        """
        Register a tool class

        Args:
            name: Unique tool identifier
            tool_class: Tool class to register
            category: Tool category (e.g., "database", "analysis", "calculation")
            description: Tool description
            version: Version string
            override: Whether to override existing tool
            **kwargs: Additional metadata
        """
        metadata = {
            "class_name": tool_class.__name__,
            "module": tool_class.__module__,
            "description": description or tool_class.__doc__,
            "category": category,
            **kwargs
        }

        tags = []
        if category:
            tags.append(category)

        self.register(
            name=name,
            item=tool_class,
            metadata=metadata,
            tags=tags,
            version=version,
            override=override
        )

        # Track by category
        if category:
            if category not in self._tool_categories:
                self._tool_categories[category] = []
            if name not in self._tool_categories[category]:
                self._tool_categories[category].append(name)

    def get_tool(self, name: str) -> Optional[Type[Any]]:
        """
        Get tool class by name

        Args:
            name: Tool name

        Returns:
            Tool class or None
        """
        return self.get(name)

    def create_tool(self, name: str, *args, **kwargs) -> Any:
        """
        Create tool instance

        Args:
            name: Tool name
            *args: Constructor arguments
            **kwargs: Constructor keyword arguments

        Returns:
            Tool instance

        Raises:
            RegistryError: If tool not found
        """
        tool_class = self.get_tool(name)
        if tool_class is None:
            raise RegistryError(f"Tool '{name}' not found in registry")

        try:
            instance = tool_class(*args, **kwargs)
            self._logger.info(f"Created instance of tool '{name}'")
            return instance
        except Exception as e:
            self._logger.error(f"Error creating tool '{name}': {e}")
            raise RegistryError(f"Failed to create tool '{name}': {str(e)}")

    def list_by_category(self, category: str) -> List[str]:
        """
        List tools by category

        Args:
            category: Category name

        Returns:
            List of tool names in the category
        """
        return self._tool_categories.get(category, [])

    def list_categories(self) -> List[str]:
        """
        List all categories

        Returns:
            List of category names
        """
        return list(self._tool_categories.keys())

    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed tool information

        Args:
            name: Tool name

        Returns:
            Tool information dictionary
        """
        info = self.get_info(name)
        if not info:
            return None

        tool_class = self.get_tool(name)
        if tool_class:
            # Add class information
            info["class"] = tool_class.__name__
            info["module"] = tool_class.__module__

            # Get methods
            methods = [
                method for method in dir(tool_class)
                if not method.startswith("_") and callable(getattr(tool_class, method))
            ]
            info["methods"] = methods

        return info

    def discover_tools(self, module_path: str) -> int:
        """
        Auto-discover and register tools from a module

        Args:
            module_path: Module path to discover tools from

        Returns:
            Number of tools discovered
        """
        # TODO: Implement auto-discovery
        # This would scan a module for classes with specific attributes/decorators
        self._logger.info(f"Tool discovery from {module_path} not yet implemented")
        return 0


# Global tool registry instance
tool_registry = ToolRegistry()


def register_tool(
    name: Optional[str] = None,
    category: Optional[str] = None,
    description: Optional[str] = None,
    version: str = "1.0.0",
    **kwargs
) -> Callable:
    """
    Decorator to register a tool class

    Args:
        name: Tool name (defaults to class name)
        category: Tool category
        description: Tool description
        version: Version string
        **kwargs: Additional metadata

    Returns:
        Decorator function

    Example:
        @register_tool(name="sql_executor", category="database")
        class SQLExecutor:
            def execute(self, query):
                pass
    """
    def decorator(cls: Type[Any]) -> Type[Any]:
        tool_name = name or cls.__name__
        tool_registry.register_tool(
            name=tool_name,
            tool_class=cls,
            category=category,
            description=description or cls.__doc__,
            version=version,
            **kwargs
        )
        return cls

    return decorator


def tool_function(
    name: Optional[str] = None,
    category: Optional[str] = None,
    description: Optional[str] = None,
    **kwargs
) -> Callable:
    """
    Decorator to register a function as a tool

    Args:
        name: Tool name (defaults to function name)
        category: Tool category
        description: Tool description
        **kwargs: Additional metadata

    Returns:
        Decorator function

    Example:
        @tool_function(name="calculate_sum", category="calculation")
        def sum_numbers(a, b):
            return a + b
    """
    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__

        # Wrap function in a class
        class FunctionTool:
            """Auto-generated tool wrapper for function"""

            def __init__(self):
                self.func = func

            def __call__(self, *args, **kwargs):
                return self.func(*args, **kwargs)

            def execute(self, *args, **kwargs):
                return self.func(*args, **kwargs)

        FunctionTool.__name__ = f"{tool_name}_Tool"
        FunctionTool.__doc__ = description or func.__doc__

        tool_registry.register_tool(
            name=tool_name,
            tool_class=FunctionTool,
            category=category,
            description=description or func.__doc__,
            **kwargs
        )

        return func

    return decorator
