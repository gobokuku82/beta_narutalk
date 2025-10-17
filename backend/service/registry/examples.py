"""
Registry Examples
레지스트리 사용 예제
"""

import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')

from .tool_registry import tool_registry, register_tool, tool_function
from .agent_registry import agent_registry, register_agent, register_subgraph, AgentType
from .registry_manager import get_registry_manager
from .auto_register import initialize_registries

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============== Example 1: Register Tool with Decorator ==============

@register_tool(name="example_calculator", category="calculation", description="Example calculator tool")
class ExampleCalculator:
    """Simple calculator for demonstration"""

    def add(self, a: float, b: float) -> float:
        return a + b

    def subtract(self, a: float, b: float) -> float:
        return a - b


# ============== Example 2: Register Function as Tool ==============

@tool_function(name="example_multiply", category="calculation")
def multiply_numbers(a: float, b: float) -> float:
    """Multiply two numbers"""
    return a * b


# ============== Example 3: Register Agent with Decorator ==============

@register_agent(
    name="example_worker",
    agent_type=AgentType.WORKER,
    capabilities=["data_processing", "calculation"],
    dependencies=["example_calculator"]
)
class ExampleWorkerAgent:
    """Example worker agent"""

    def __init__(self):
        self.name = "ExampleWorker"

    def process(self, data):
        return f"Processed: {data}"


# ============== Example 4: Manual Registration ==============

def example_manual_registration():
    """Example: Manually register tools and agents"""
    print("\n=== Example 1: Manual Registration ===\n")

    # Register a tool manually
    class MyCustomTool:
        def execute(self, input_data):
            return f"Executed with {input_data}"

    tool_registry.register_tool(
        name="my_custom_tool",
        tool_class=MyCustomTool,
        category="custom",
        description="My custom tool",
        version="1.0.0"
    )

    print(f"Registered tools: {tool_registry.list_all()}")


# ============== Example 5: Using Tools from Registry ==============

def example_using_tools():
    """Example: Create and use tools from registry"""
    print("\n=== Example 2: Using Tools from Registry ===\n")

    # Create tool instance from registry
    calculator = tool_registry.create_tool("example_calculator")
    result = calculator.add(10, 20)
    print(f"Calculator result: 10 + 20 = {result}")

    # Get tool information
    info = tool_registry.get_tool_info("example_calculator")
    print(f"Tool info: {info}")


# ============== Example 6: Using Agents from Registry ==============

def example_using_agents():
    """Example: Create and use agents from registry"""
    print("\n=== Example 3: Using Agents from Registry ===\n")

    # Create agent instance
    worker = agent_registry.create_agent("example_worker")
    result = worker.process("test data")
    print(f"Worker result: {result}")

    # Check dependencies
    deps = agent_registry.get_dependencies("example_worker")
    print(f"Worker dependencies: {deps}")

    # Validate dependencies
    is_valid, missing = agent_registry.validate_dependencies("example_worker")
    print(f"Dependencies valid: {is_valid}, Missing: {missing}")


# ============== Example 7: Using Registry Manager ==============

def example_registry_manager():
    """Example: Use registry manager to manage all registries"""
    print("\n=== Example 4: Using Registry Manager ===\n")

    manager = get_registry_manager()

    # Get statistics
    stats = manager.get_statistics()
    print("Registry Statistics:")
    print(f"  Tools: {stats['tools']['total']}")
    print(f"  Agents: {stats['agents']['total']}")

    # Search across registries
    search_results = manager.search("example")
    print(f"\nSearch results for 'example':")
    print(f"  Tools: {search_results['tools']}")
    print(f"  Agents: {search_results['agents']}")

    # Get info about any item
    info = manager.get_info("example_calculator")
    if info:
        print(f"\nInfo for 'example_calculator':")
        print(f"  Registry: {info['registry']}")
        print(f"  Version: {info['version']}")


# ============== Example 8: Dependency Resolution ==============

def example_dependency_resolution():
    """Example: Resolve agent dependencies"""
    print("\n=== Example 5: Dependency Resolution ===\n")

    manager = get_registry_manager()

    # Get dependency tree
    tree = agent_registry.get_dependency_tree("example_worker")
    print(f"Dependency tree: {tree}")

    # Resolve all dependencies
    try:
        resolved = manager.resolve_dependencies("example_worker")
        print(f"Resolved dependencies: {list(resolved.keys())}")
    except Exception as e:
        print(f"Error resolving dependencies: {e}")


# ============== Example 9: List and Filter ==============

def example_list_and_filter():
    """Example: List and filter registered items"""
    print("\n=== Example 6: List and Filter ===\n")

    # List tools by category
    calc_tools = tool_registry.list_by_category("calculation")
    print(f"Calculation tools: {calc_tools}")

    # List agents by type
    workers = agent_registry.list_by_type(AgentType.WORKER)
    print(f"Worker agents: {workers}")

    # Find agents by capability
    data_processors = agent_registry.find_by_capability("data_processing")
    print(f"Agents with 'data_processing' capability: {data_processors}")


# ============== Example 10: Auto-Registration ==============

def example_auto_registration():
    """Example: Auto-register existing tools and agents"""
    print("\n=== Example 7: Auto-Registration ===\n")

    # Initialize registries (auto-register existing components)
    initialize_registries()

    manager = get_registry_manager()

    # Show what was registered
    print("Auto-registered components:")
    print(f"  Tools: {manager.list_tools()}")
    print(f"  Agents: {manager.list_agents()}")

    # Print summary
    manager.print_summary()


# ============== Example 11: Using with Orchestrator ==============

async def example_with_orchestrator():
    """Example: Use registry with orchestrator"""
    print("\n=== Example 8: Using Registry with Orchestrator ===\n")

    # Initialize registries first
    initialize_registries()

    # Import registry-based orchestrator
    from ..orchestrator.registry_based_orchestrator import (
        RegistryBasedOrchestrator,
        create_registry_based_workflow
    )

    # Create orchestrator that uses registry
    orchestrator = RegistryBasedOrchestrator(use_registry=True)

    # Get registry info
    registry_info = orchestrator.get_registry_info()
    print(f"Orchestrator using registry: {registry_info['using_registry']}")
    print(f"Supervisor registered: {registry_info['supervisor_registered']}")
    print(f"Subgraphs registered: {registry_info['subgraphs_registered']}")

    # Build graph
    graph = orchestrator.build_graph()
    print(f"Graph built successfully with registry-loaded components")


# ============== Example 12: Export Registry State ==============

def example_export_registry():
    """Example: Export registry state"""
    print("\n=== Example 9: Export Registry State ===\n")

    manager = get_registry_manager()

    # Export all registries
    state = manager.export_all()
    print(f"Exported {len(state['tool_registry']['items'])} tools")
    print(f"Exported {len(state['agent_registry']['items'])} agents")

    # Could save to file
    # manager.save_to_file(Path("registry_state.json"))


# ============== Run All Examples ==============

async def run_all_examples():
    """Run all examples"""
    print("=" * 60)
    print("Registry Examples")
    print("=" * 60)

    example_manual_registration()
    example_using_tools()
    example_using_agents()
    example_registry_manager()
    example_dependency_resolution()
    example_list_and_filter()
    example_auto_registration()
    await example_with_orchestrator()
    example_export_registry()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Run all examples
    asyncio.run(run_all_examples())
