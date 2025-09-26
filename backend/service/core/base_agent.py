"""
BaseAgent class with full LangGraph 0.6.x Context API support
Following the official Context API manual and rules
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type, Callable
from langgraph.graph import StateGraph
from langgraph.runtime import Runtime
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import logging
import asyncio
from pathlib import Path
from datetime import datetime

from .context import AgentContext, create_agent_context


logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all agents with full Context API support
    Implements LangGraph 0.6.x patterns with Runtime
    """

    def __init__(self, agent_name: str, checkpoint_dir: Optional[str] = None):
        """
        Initialize base agent

        Args:
            agent_name: Name of the agent
            checkpoint_dir: Directory for checkpoints
        """
        self.agent_name = agent_name
        self.logger = logging.getLogger(f"agent.{agent_name}")

        # Set checkpoint directory
        if checkpoint_dir is None:
            checkpoint_dir = f"checkpoints/{agent_name}"

        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Initialize checkpointer (will be created in execute)
        self.checkpointer_path = self.checkpoint_dir / f"{self.agent_name}.db"

        # Initialize workflow with context schema
        self.workflow = None
        self._build_graph()

        self.logger.info(f"{agent_name} initialized with Context API support")

    @abstractmethod
    def _get_state_schema(self) -> Type:
        """
        Get the state schema for this agent

        Returns:
            State schema type (TypedDict)
        """
        pass

    @abstractmethod
    def _build_graph(self):
        """
        Build the LangGraph workflow with context_schema
        Must call StateGraph with both state_schema and context_schema
        """
        pass

    @abstractmethod
    async def _validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data before processing

        Args:
            input_data: Input data to validate

        Returns:
            True if valid, False otherwise
        """
        pass

    def _create_initial_state(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create initial state from input data
        Only includes workflow-specific fields (not context fields)

        Args:
            input_data: Input data from user

        Returns:
            Initial state dictionary with workflow fields only
        """
        # Basic state fields - subclasses should override to add specific fields
        return {
            "status": "pending",
            "execution_step": "starting",
            **{k: v for k, v in input_data.items()
               if k not in ["user_id", "session_id", "metadata", "original_query", "intent_result"]}  # Exclude context fields
        }

    def _create_context(self, input_data: Dict[str, Any]) -> AgentContext:
        """
        Create context from input data
        Context contains metadata that doesn't change during execution

        Args:
            input_data: Input data containing context information

        Returns:
            AgentContext instance
        """
        return create_agent_context(
            user_id=input_data.get("user_id", "default"),
            session_id=input_data.get("session_id", "default"),
            context_type="agent",
            agent_name=self.agent_name,
            original_query=input_data.get("original_query", ""),
            intent_result=input_data.get("intent_result", {}),
            metadata=input_data.get("metadata", {}),
            request_id=input_data.get("request_id")
        )

    def _wrap_node_with_runtime(self, node_func: Callable) -> Callable:
        """
        Wrap a node function to properly handle Runtime parameter
        This ensures nodes receive Runtime even if not explicitly passed

        Args:
            node_func: Original node function

        Returns:
            Wrapped function that handles Runtime
        """
        async def wrapped(state: Dict[str, Any], runtime: Optional[Runtime] = None) -> Dict[str, Any]:
            # If the node expects runtime, pass it
            import inspect
            sig = inspect.signature(node_func)

            if "runtime" in sig.parameters:
                if runtime is None:
                    # Create a mock runtime if needed (shouldn't happen in practice)
                    self.logger.warning(f"Runtime not provided to {node_func.__name__}, using default")
                    return await node_func(state, runtime)
                return await node_func(state, runtime)
            else:
                # Old-style node without runtime
                self.logger.warning(f"Node {node_func.__name__} doesn't use Runtime - consider updating")
                return await node_func(state)

        return wrapped

    async def execute(
        self,
        input_data: Dict[str, Any],
        config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Execute the agent workflow with Context API

        Args:
            input_data: Input data for the agent
            config: Optional configuration for execution

        Returns:
            Dict containing execution results
        """
        try:
            # Validate input
            if not await self._validate_input(input_data):
                return {
                    "status": "error",
                    "error": "Invalid input data",
                    "agent": self.agent_name
                }

            # Create initial state (workflow data only)
            initial_state = self._create_initial_state(input_data)

            # Create context (metadata)
            context = self._create_context(input_data)

            # Prepare config
            if config is None:
                config = {}

            # Add default config
            config.setdefault("recursion_limit", 25)
            config.setdefault("configurable", {})

            # Use context's session_id for thread_id (context is a dict)
            config["configurable"]["thread_id"] = context.get("session_id", "default")

            # Compile workflow with checkpointer
            if self.workflow is None:
                self.logger.error("Workflow not initialized")
                return {
                    "status": "error",
                    "error": "Workflow not initialized",
                    "agent": self.agent_name
                }

            # Create checkpointer and compile
            async with AsyncSqliteSaver.from_conn_string(str(self.checkpointer_path)) as checkpointer:
                app = self.workflow.compile(checkpointer=checkpointer)

                # Execute with timeout
                timeout = config.get("timeout", 30)  # Default 30 seconds

                try:
                    # Execute with context following LangGraph 0.6.x pattern
                    result = await asyncio.wait_for(
                        app.ainvoke(
                            initial_state,
                            config=config,
                            context=context  # context is already a dict
                        ),
                        timeout=timeout
                    )

                    self.logger.info(f"{self.agent_name} execution completed successfully")

                    # Check if there were any errors logged in context
                    if isinstance(context, dict) and "error_logs" in context:
                        self.logger.warning(f"Execution completed with errors: {context['error_logs']}")

                    return {
                        "status": "success",
                        "data": result,
                        "agent": self.agent_name,
                        "context": {
                            "user_id": context.get("user_id", "unknown"),
                            "session_id": context.get("session_id", "unknown"),
                            "request_id": context.get("request_id", "unknown")
                        }
                    }

                except asyncio.TimeoutError:
                    self.logger.error(f"{self.agent_name} execution timed out after {timeout}s")

                    # Log timeout in context if possible
                    if isinstance(context, dict) and "add_error" in context:
                        context["add_error"](f"Execution timed out after {timeout} seconds")

                    return {
                        "status": "error",
                        "error": f"Execution timed out after {timeout} seconds",
                        "agent": self.agent_name
                    }

        except Exception as e:
            self.logger.error(f"{self.agent_name} execution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "error": str(e),
                "agent": self.agent_name
            }

    async def get_state(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current state for a thread

        Args:
            thread_id: Thread ID to get state for

        Returns:
            Current state or None
        """
        try:
            async with AsyncSqliteSaver.from_conn_string(str(self.checkpointer_path)) as checkpointer:
                app = self.workflow.compile(checkpointer=checkpointer)
                config = {"configurable": {"thread_id": thread_id}}
                state = await app.aget_state(config)
                return state.values if state else None
        except Exception as e:
            self.logger.error(f"Failed to get state: {e}")
            return None

    async def update_state(
        self,
        thread_id: str,
        state_update: Dict[str, Any],
        context: Optional[AgentContext] = None
    ) -> bool:
        """
        Update the state for a thread

        Args:
            thread_id: Thread ID to update
            state_update: State updates to apply (partial update)
            context: Optional context for the update

        Returns:
            True if successful, False otherwise
        """
        try:
            async with AsyncSqliteSaver.from_conn_string(str(self.checkpointer_path)) as checkpointer:
                app = self.workflow.compile(checkpointer=checkpointer)
                config = {"configurable": {"thread_id": thread_id}}

                # Update only the specified fields (following Context API pattern)
                await app.aupdate_state(config, state_update)

                self.logger.info(f"State updated for thread {thread_id}: {list(state_update.keys())}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to update state: {e}")
            return False

    # Helper method for nodes to properly return partial updates
    @staticmethod
    def create_partial_update(**kwargs) -> Dict[str, Any]:
        """
        Helper to create partial state updates for nodes

        Usage in node:
            return self.create_partial_update(
                field1=new_value1,
                field2=new_value2
            )
        """
        return kwargs