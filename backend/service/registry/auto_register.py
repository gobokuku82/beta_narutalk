"""
Auto Registration
기존 툴과 에이전트를 자동으로 레지스트리에 등록
"""

import logging
from typing import Optional
from pathlib import Path

from .tool_registry import tool_registry
from .agent_registry import agent_registry, AgentType


logger = logging.getLogger(__name__)


def auto_register_tools() -> int:
    """
    Auto-register all existing tools

    Returns:
        Number of tools registered
    """
    count = 0

    # Import and register SQL tools
    try:
        from ..tools.sql_executor import SQLExecutor
        tool_registry.register_tool(
            name="sql_executor",
            tool_class=SQLExecutor,
            category="database",
            description="Execute SQL queries on databases",
            version="1.0.0"
        )
        count += 1
    except Exception as e:
        logger.warning(f"Could not register SQLExecutor: {e}")

    try:
        from ..tools.sql_generator import SQLGenerator
        tool_registry.register_tool(
            name="sql_generator",
            tool_class=SQLGenerator,
            category="database",
            description="Generate SQL queries using LLM",
            version="1.0.0"
        )
        count += 1
    except Exception as e:
        logger.warning(f"Could not register SQLGenerator: {e}")

    # Register calculation tools
    try:
        from ..tools.calculation_tool import CalculationTool
        tool_registry.register_tool(
            name="calculation_tool",
            tool_class=CalculationTool,
            category="calculation",
            description="Basic mathematical calculations",
            version="1.0.0"
        )
        count += 1
    except Exception as e:
        logger.warning(f"Could not register CalculationTool: {e}")

    # Register trend analysis tool
    try:
        from ..tools.trend_analysis_tool import TrendAnalysisTool
        tool_registry.register_tool(
            name="trend_analysis_tool",
            tool_class=TrendAnalysisTool,
            category="analysis",
            description="Time series trend analysis",
            version="1.0.0"
        )
        count += 1
    except Exception as e:
        logger.warning(f"Could not register TrendAnalysisTool: {e}")

    # Register cross-db analysis tool
    try:
        from ..tools.cross_db_analysis_tool import CrossDBAnalysisTool
        tool_registry.register_tool(
            name="cross_db_analysis_tool",
            tool_class=CrossDBAnalysisTool,
            category="analysis",
            description="Cross-database analysis and comparison",
            version="1.0.0"
        )
        count += 1
    except Exception as e:
        logger.warning(f"Could not register CrossDBAnalysisTool: {e}")

    logger.info(f"Auto-registered {count} tools")
    return count


def auto_register_agents() -> int:
    """
    Auto-register all existing agents and subgraphs

    Returns:
        Number of agents registered
    """
    count = 0

    # Register supervisor
    try:
        from ..supervisor.supervisor_agent import SupervisorAgent
        from ..supervisor.supervisor_state import SupervisorState

        agent_registry.register_agent(
            name="supervisor",
            agent_class=SupervisorAgent,
            agent_type=AgentType.SUPERVISOR,
            description="Main supervisor agent for reasoning and execution control",
            capabilities=["reasoning", "planning", "routing", "aggregation"],
            version="1.0.0"
        )
        count += 1
    except Exception as e:
        logger.warning(f"Could not register SupervisorAgent: {e}")

    # Register data collection subgraph
    try:
        from ..subgraphs.data_collection_subgraph import DataCollectionSubgraph
        from ..core.states import DataCollectionState

        agent_registry.register_subgraph(
            name="data_collection_subgraph",
            subgraph_class=DataCollectionSubgraph,
            description="Collect data from multiple databases",
            input_state=DataCollectionState,
            output_state=DataCollectionState,
            dependencies=["sql_executor", "sql_generator"],
            version="1.0.0"
        )
        count += 1
    except Exception as e:
        logger.warning(f"Could not register DataCollectionSubgraph: {e}")

    # Register analysis subgraph
    try:
        from ..subgraphs.analysis_subgraph import AnalysisSubgraph
        from ..core.states import AnalysisState

        agent_registry.register_subgraph(
            name="analysis_subgraph",
            subgraph_class=AnalysisSubgraph,
            description="Perform data analysis with multiple tools",
            input_state=AnalysisState,
            output_state=AnalysisState,
            dependencies=["calculation_tool", "trend_analysis_tool", "cross_db_analysis_tool"],
            version="1.0.0"
        )
        count += 1
    except Exception as e:
        logger.warning(f"Could not register AnalysisSubgraph: {e}")

    logger.info(f"Auto-registered {count} agents")
    return count


def auto_register_all() -> dict[str, int]:
    """
    Auto-register all tools and agents

    Returns:
        Dictionary with counts
    """
    tools_count = auto_register_tools()
    agents_count = auto_register_agents()

    logger.info(f"Auto-registration complete: {tools_count} tools, {agents_count} agents")

    return {
        "tools": tools_count,
        "agents": agents_count,
        "total": tools_count + agents_count
    }


def initialize_registries() -> None:
    """
    Initialize and populate registries
    This should be called at application startup
    """
    logger.info("Initializing registries...")

    counts = auto_register_all()

    logger.info(
        f"Registries initialized: "
        f"{counts['tools']} tools, "
        f"{counts['agents']} agents"
    )


# Auto-initialize when module is imported
# Comment this out if you want manual initialization
# initialize_registries()
