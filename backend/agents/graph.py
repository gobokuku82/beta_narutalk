"""
Main workflow graph configuration for LangGraph 0.6.7
Implements 6-step supervisor workflow with caching and optimization
"""

from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.cache import SimpleCache
import logging

from .state import GlobalSessionState, initialize_global_state
from .supervisor import (
    intent_analyzer_node,
    planner_node,
    agent_selector_node,
    execution_manager_node,
    evaluator_node,
    iteration_controller_node
)

logger = logging.getLogger(__name__)


class WorkflowGraph:
    """Main workflow graph implementation"""

    def __init__(self, checkpoint_path: str = "checkpoints.db"):
        self.checkpoint_path = checkpoint_path
        self.graph = None
        self.compiled_graph = None

    async def build_graph(self) -> StateGraph:
        """Build the main workflow graph"""

        # Initialize graph with GlobalSessionState
        graph = StateGraph(GlobalSessionState)

        # Add supervisor nodes (6-step workflow)
        graph.add_node("intent_analysis", intent_analyzer_node)
        graph.add_node("planning", planner_node)
        graph.add_node("agent_selection", agent_selector_node)
        graph.add_node("execution", execution_manager_node)
        graph.add_node("evaluation", evaluator_node)
        graph.add_node("iteration", iteration_controller_node)

        # Add worker nodes (will be imported when implemented)
        # graph.add_node("data_analysis", data_analysis_node)
        # graph.add_node("info_retrieval", info_retrieval_node)
        # graph.add_node("doc_generation", doc_generation_node)
        # graph.add_node("compliance", compliance_node)
        # graph.add_node("storage", storage_node)

        # Sequential flow for supervisor nodes
        graph.add_edge(START, "intent_analysis")
        graph.add_edge("intent_analysis", "planning")
        graph.add_edge("planning", "agent_selection")
        graph.add_edge("agent_selection", "execution")

        # Conditional routing from execution to workers
        graph.add_conditional_edges(
            "execution",
            self._route_to_workers,
            {
                # "data_analysis": "data_analysis",
                # "info_retrieval": "info_retrieval",
                # "doc_generation": "doc_generation",
                # "compliance": "compliance",
                # "storage": "storage",
                "evaluation": "evaluation",  # Default when all workers complete
                "error": END
            }
        )

        # Workers return to execution manager
        # for worker in ["data_analysis", "info_retrieval", "doc_generation", "compliance", "storage"]:
        #     graph.add_edge(worker, "execution")

        # Evaluation to iteration
        graph.add_edge("evaluation", "iteration")

        # Iteration decision: retry or complete
        graph.add_conditional_edges(
            "iteration",
            self._check_iteration,
            {
                "retry": "planning",  # Go back to planning
                "complete": END
            }
        )

        self.graph = graph
        return graph

    async def compile_graph(self) -> Any:
        """Compile the graph with checkpointing and caching"""

        if not self.graph:
            await self.build_graph()

        # Initialize checkpointer
        checkpointer = await AsyncSqliteSaver.from_conn_string(self.checkpoint_path)

        # Initialize cache
        cache = SimpleCache()

        # Define cache policy for expensive operations
        cache_policy = {
            "intent_analysis": {
                "ttl": 300,  # 5 minutes
                "key_func": lambda x: f"intent_{x.get('session_id')}_{x.get('messages', [''])[-1]}"
            },
            "planning": {
                "ttl": 300,  # 5 minutes
                "key_func": lambda x: f"plan_{x.get('session_id')}_{x.get('query_analyzer_state', {}).get('raw_query', '')}"
            },
            # "data_analysis": {
            #     "ttl": 600,  # 10 minutes for data results
            #     "key_func": lambda x: f"data_{x.get('task_id')}"
            # }
        }

        # Compile with optimizations
        self.compiled_graph = self.graph.compile(
            checkpointer=checkpointer,
            cache=cache,
            cache_policy=cache_policy,
            # Enable parallel execution
            parallel=True,
            # Set timeouts
            node_timeouts={
                "intent_analysis": 30,
                "planning": 30,
                "execution": 120,
                "evaluation": 20,
                "iteration": 10
            }
        )

        logger.info("Graph compiled with checkpointing and caching")
        return self.compiled_graph

    def _route_to_workers(self, state: GlobalSessionState) -> str:
        """Route from execution manager to appropriate workers or evaluation"""

        execution_state = state.get("execution_manager_state")
        if not execution_state:
            logger.error("No execution manager state found")
            return "error"

        # Check if there are pending tasks
        pending_tasks = execution_state.get("pending_tasks", [])
        if pending_tasks:
            # Route to the first pending task's agent
            next_task = pending_tasks[0]
            agent_name = next_task.get("agent")

            # Map agent names to node names
            agent_mapping = {
                "DataAnalysisAgent": "data_analysis",
                "InformationRetrievalAgent": "info_retrieval",
                "DocumentGenerationAgent": "doc_generation",
                "ComplianceValidationAgent": "compliance",
                "StorageDecisionAgent": "storage"
            }

            node_name = agent_mapping.get(agent_name)
            if node_name:
                logger.info(f"Routing to {node_name}")
                return node_name

        # All tasks completed, go to evaluation
        if execution_state.get("execution_status") == "completed":
            logger.info("All tasks completed, routing to evaluation")
            return "evaluation"

        # Error or unknown state
        logger.warning("Unknown execution state, ending workflow")
        return "error"

    def _check_iteration(self, state: GlobalSessionState) -> str:
        """Check if iteration is needed or workflow is complete"""

        iteration_state = state.get("iteration_state")
        if not iteration_state:
            # No iteration state, assume complete
            return "complete"

        # Check iteration count
        max_iterations = state.get("max_iterations", 3)
        current_iteration = state.get("iteration_count", 0)

        if current_iteration >= max_iterations:
            logger.info(f"Max iterations ({max_iterations}) reached, completing")
            return "complete"

        # Check if retry is needed
        need_retry = iteration_state.get("need_retry", False)
        if need_retry:
            logger.info(f"Retry needed, iteration {current_iteration + 1}")
            return "retry"

        # Check quality threshold
        quality_threshold = 0.8
        quality_score = iteration_state.get("quality_score", 1.0)
        if quality_score < quality_threshold:
            logger.info(f"Quality score {quality_score} below threshold {quality_threshold}, retrying")
            return "retry"

        # All checks passed, complete
        logger.info("Iteration checks passed, completing workflow")
        return "complete"

    async def execute(self, initial_state: GlobalSessionState, config: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute the compiled graph with initial state"""

        if not self.compiled_graph:
            await self.compile_graph()

        # Default config
        if not config:
            config = {
                "configurable": {
                    "thread_id": initial_state["session_id"]
                }
            }

        # Execute graph
        try:
            result = await self.compiled_graph.ainvoke(initial_state, config)
            logger.info(f"Workflow completed for session {initial_state['session_id']}")
            return result
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            raise

    async def stream(self, initial_state: GlobalSessionState, config: Optional[Dict] = None):
        """Stream execution results in real-time"""

        if not self.compiled_graph:
            await self.compile_graph()

        # Default config
        if not config:
            config = {
                "configurable": {
                    "thread_id": initial_state["session_id"]
                }
            }

        # Stream execution
        try:
            async for chunk in self.compiled_graph.astream(initial_state, config):
                yield chunk
        except Exception as e:
            logger.error(f"Workflow streaming failed: {e}")
            raise


# Singleton instance
workflow_graph = WorkflowGraph()


async def create_and_compile_graph():
    """Helper function to create and compile the graph"""
    graph = WorkflowGraph()
    await graph.compile_graph()
    return graph


async def execute_workflow(
    session_id: str,
    user_id: str,
    company_id: str,
    query: str
) -> Dict[str, Any]:
    """High-level function to execute a workflow"""

    # Initialize state
    initial_state = initialize_global_state(session_id, user_id, company_id)
    initial_state["messages"] = [{"role": "user", "content": query}]

    # Execute workflow
    result = await workflow_graph.execute(initial_state)

    return result