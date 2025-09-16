"""
Supervisor Agent Implementation
Based on LangGraph 0.6.7 and langgraph-supervisor 0.0.29
"""

from typing import Dict, Any, List, Literal, Optional, Union
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolExecutor, ToolInvocation
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.tools import Tool
import asyncio
from datetime import datetime
import logging

from .state import (
    GlobalSessionState,
    QueryAnalyzerState,
    PlanningState,
    ExecutionManagerState,
    determine_next_phase,
    initialize_global_state
)

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """Main supervisor agent that orchestrates all sub-agents"""

    def __init__(self, llm_provider: str = "openai"):
        """Initialize supervisor with LLM provider"""
        if llm_provider == "openai":
            self.llm = ChatOpenAI(model="gpt-4o", temperature=0)  # Using GPT-4o
        elif llm_provider == "anthropic":
            self.llm = ChatAnthropic(model="claude-3-opus-20240229", temperature=0)
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_provider}")

        self.tools = self._create_tools()
        self.tool_executor = ToolExecutor(self.tools)

    def _create_tools(self) -> List[Tool]:
        """Create tools for supervisor to delegate to agents"""
        tools = [
            Tool(
                name="query_analyzer",
                description="Analyze user query to understand intent and requirements",
                func=self._delegate_to_query_analyzer
            ),
            Tool(
                name="planner",
                description="Create execution plan based on analyzed query",
                func=self._delegate_to_planner
            ),
            Tool(
                name="data_analysis",
                description="Perform data analysis and SQL queries",
                func=self._delegate_to_data_analysis
            ),
            Tool(
                name="info_retrieval",
                description="Search and retrieve information from various sources",
                func=self._delegate_to_info_retrieval
            ),
            Tool(
                name="doc_generation",
                description="Generate documents and reports",
                func=self._delegate_to_doc_generation
            ),
            Tool(
                name="compliance",
                description="Validate compliance and check regulations",
                func=self._delegate_to_compliance
            ),
            Tool(
                name="storage",
                description="Determine storage strategy and save data",
                func=self._delegate_to_storage
            )
        ]
        return tools

    async def supervisor_node(self, state: GlobalSessionState) -> Dict[str, Any]:
        """Main supervisor node that decides next action"""
        current_phase = state["current_phase"]
        messages = state["messages"]

        # Create system prompt for supervisor
        system_prompt = self._create_supervisor_prompt(state)

        # Get supervisor decision
        supervisor_messages = [
            SystemMessage(content=system_prompt),
            *messages
        ]

        response = await self.llm.ainvoke(supervisor_messages)

        # Parse response and determine next action
        next_action = self._parse_supervisor_response(response, state)

        # Update state with supervisor decision
        state["audit_trail"].append({
            "timestamp": datetime.now().isoformat(),
            "agent": "supervisor",
            "action": "decision",
            "next_action": next_action,
            "phase": current_phase
        })

        return {"next_action": next_action, "current_agent": next_action}

    def _create_supervisor_prompt(self, state: GlobalSessionState) -> str:
        """Create prompt for supervisor based on current state"""
        phase = state["current_phase"]
        progress = state["progress_percentage"]

        prompt = f"""You are a supervisor agent orchestrating a multi-agent system.
Current phase: {phase}
Progress: {progress:.1f}%

Available agents:
- query_analyzer: Analyze user queries
- planner: Create execution plans
- data_analysis: Perform data analysis
- info_retrieval: Search information
- doc_generation: Generate documents
- compliance: Check compliance
- storage: Store data

Based on the conversation and current state, decide which agent to invoke next.
Consider dependencies and parallel execution opportunities.
"""

        # Add phase-specific instructions
        if phase == "analyzing":
            prompt += "\nStart by analyzing the user's query with query_analyzer."
        elif phase == "planning":
            prompt += "\nCreate an execution plan with planner based on analysis."
        elif phase == "executing":
            prompt += "\nExecute the plan by delegating to appropriate agents."

        return prompt

    def _parse_supervisor_response(self, response: AIMessage, state: GlobalSessionState) -> str:
        """Parse supervisor response to determine next action"""
        content = response.content.lower()

        # Map keywords to actions
        action_mapping = {
            "query_analyzer": "query_analyzer",
            "analyze": "query_analyzer",
            "planner": "planner",
            "plan": "planner",
            "data": "data_analysis",
            "sql": "data_analysis",
            "search": "info_retrieval",
            "retrieve": "info_retrieval",
            "document": "doc_generation",
            "generate": "doc_generation",
            "compliance": "compliance",
            "validate": "compliance",
            "store": "storage",
            "save": "storage"
        }

        for keyword, action in action_mapping.items():
            if keyword in content:
                return action

        # Default based on phase
        if state["current_phase"] == "analyzing":
            return "query_analyzer"
        elif state["current_phase"] == "planning":
            return "planner"
        else:
            return "data_analysis"

    async def _delegate_to_query_analyzer(self, query: str) -> Dict[str, Any]:
        """Delegate to query analyzer agent"""
        from .query_analyzer import QueryAnalyzerAgent
        agent = QueryAnalyzerAgent()
        return await agent.analyze(query)

    async def _delegate_to_planner(self, analyzed_query: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to planning agent"""
        from .planner import PlanningAgent
        agent = PlanningAgent()
        return await agent.create_plan(analyzed_query)

    async def _delegate_to_data_analysis(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to data analysis agent"""
        from .data_analysis import DataAnalysisAgent
        agent = DataAnalysisAgent()
        return await agent.execute(task)

    async def _delegate_to_info_retrieval(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to information retrieval agent"""
        from .information_retrieval import InformationRetrievalAgent
        agent = InformationRetrievalAgent()
        return await agent.execute(task)

    async def _delegate_to_doc_generation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to document generation agent"""
        from .document_generation import DocumentGenerationAgent
        agent = DocumentGenerationAgent()
        return await agent.execute(task)

    async def _delegate_to_compliance(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to compliance validation agent"""
        from .compliance import ComplianceValidationAgent
        agent = ComplianceValidationAgent()
        return await agent.execute(task)

    async def _delegate_to_storage(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Delegate to storage decision agent"""
        from .storage import StorageDecisionAgent
        agent = StorageDecisionAgent()
        return await agent.execute(task)


def create_supervisor_graph() -> StateGraph:
    """Create the main supervisor graph"""
    # Initialize graph with global state
    graph = StateGraph(GlobalSessionState)

    # Create supervisor instance
    supervisor = SupervisorAgent()

    # Add nodes
    graph.add_node("supervisor", supervisor.supervisor_node)

    # Add agent nodes (these will be imported from their respective modules)
    graph.add_node("query_analyzer", query_analyzer_node)
    graph.add_node("planner", planner_node)
    graph.add_node("data_analysis", data_analysis_node)
    graph.add_node("info_retrieval", info_retrieval_node)
    graph.add_node("doc_generation", doc_generation_node)
    graph.add_node("compliance", compliance_node)
    graph.add_node("storage", storage_node)

    # Add edges
    graph.add_edge(START, "supervisor")

    # Conditional edges from supervisor
    graph.add_conditional_edges(
        "supervisor",
        lambda x: x["current_agent"],
        {
            "query_analyzer": "query_analyzer",
            "planner": "planner",
            "data_analysis": "data_analysis",
            "info_retrieval": "info_retrieval",
            "doc_generation": "doc_generation",
            "compliance": "compliance",
            "storage": "storage",
            END: END
        }
    )

    # Add edges back to supervisor from each agent
    for agent in ["query_analyzer", "planner", "data_analysis", "info_retrieval",
                  "doc_generation", "compliance", "storage"]:
        graph.add_edge(agent, "supervisor")

    return graph


# Placeholder node functions (will be implemented in respective agent modules)
async def query_analyzer_node(state: GlobalSessionState) -> Dict[str, Any]:
    """Query analyzer node"""
    from .query_analyzer import QueryAnalyzerAgent
    agent = QueryAnalyzerAgent()
    result = await agent.analyze_query_node(state)
    state["query_analyzer_state"] = result
    return state


async def planner_node(state: GlobalSessionState) -> Dict[str, Any]:
    """Planner node"""
    from .planner import PlanningAgent
    agent = PlanningAgent()
    result = await agent.create_plan_node(state)
    state["planning_state"] = result
    return state


async def data_analysis_node(state: GlobalSessionState) -> Dict[str, Any]:
    """Data analysis node"""
    from .data_analysis import DataAnalysisAgent
    agent = DataAnalysisAgent()
    return await agent.execute_node(state)


async def info_retrieval_node(state: GlobalSessionState) -> Dict[str, Any]:
    """Information retrieval node"""
    from .information_retrieval import InformationRetrievalAgent
    agent = InformationRetrievalAgent()
    return await agent.execute_node(state)


async def doc_generation_node(state: GlobalSessionState) -> Dict[str, Any]:
    """Document generation node"""
    from .document_generation import DocumentGenerationAgent
    agent = DocumentGenerationAgent()
    return await agent.execute_node(state)


async def compliance_node(state: GlobalSessionState) -> Dict[str, Any]:
    """Compliance validation node"""
    from .compliance import ComplianceValidationAgent
    agent = ComplianceValidationAgent()
    return await agent.execute_node(state)


async def storage_node(state: GlobalSessionState) -> Dict[str, Any]:
    """Storage decision node"""
    from .storage import StorageDecisionAgent
    agent = StorageDecisionAgent()
    return await agent.execute_node(state)


async def compile_supervisor_graph():
    """Compile the supervisor graph with checkpointing"""
    graph = create_supervisor_graph()

    # Add checkpointing
    checkpointer = await AsyncSqliteSaver.from_conn_string("checkpoints.db")

    # Compile graph
    compiled_graph = graph.compile(checkpointer=checkpointer)

    return compiled_graph