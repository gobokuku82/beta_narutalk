"""
Base agent class for all agents
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import logging
import asyncio
from pathlib import Path


logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all agents"""

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

        # Initialize checkpointer
        self.checkpointer = None
        self._init_checkpointer()

        # Initialize workflow
        self.workflow = None
        self._build_graph()

        self.logger.info(f"{agent_name} initialized")

    def _init_checkpointer(self):
        """Initialize async SQLite checkpointer"""
        checkpoint_path = self.checkpoint_dir / f"{self.agent_name}.db"
        self.checkpointer = AsyncSqliteSaver.from_conn_string(str(checkpoint_path))
        self.logger.debug(f"Checkpointer initialized at {checkpoint_path}")

    @abstractmethod
    def _build_graph(self):
        """Build the LangGraph workflow - must be implemented by subclasses"""
        pass

    @abstractmethod
    async def _validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data - must be implemented by subclasses"""
        pass

    async def execute(self, input_data: Dict[str, Any], config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute the agent workflow

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

            # Prepare config
            if config is None:
                config = {}

            # Add default config
            config.setdefault("recursion_limit", 25)
            config.setdefault("configurable", {})
            config["configurable"]["thread_id"] = input_data.get("session_id", "default")

            # Compile workflow with checkpointer
            if self.workflow is None:
                self.logger.error("Workflow not initialized")
                return {
                    "status": "error",
                    "error": "Workflow not initialized",
                    "agent": self.agent_name
                }

            app = self.workflow.compile(checkpointer=self.checkpointer)

            # Execute with timeout
            timeout = config.get("timeout", 30)  # Default 30 seconds

            try:
                result = await asyncio.wait_for(
                    app.ainvoke(input_data, config=config),
                    timeout=timeout
                )

                self.logger.info(f"{self.agent_name} execution completed successfully")
                return {
                    "status": "success",
                    "data": result,
                    "agent": self.agent_name
                }

            except asyncio.TimeoutError:
                self.logger.error(f"{self.agent_name} execution timed out after {timeout}s")
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
            app = self.workflow.compile(checkpointer=self.checkpointer)
            config = {"configurable": {"thread_id": thread_id}}
            state = await app.aget_state(config)
            return state.values if state else None
        except Exception as e:
            self.logger.error(f"Failed to get state: {e}")
            return None

    async def update_state(self, thread_id: str, state_update: Dict[str, Any]) -> bool:
        """
        Update the state for a thread

        Args:
            thread_id: Thread ID to update
            state_update: State updates to apply

        Returns:
            True if successful, False otherwise
        """
        try:
            app = self.workflow.compile(checkpointer=self.checkpointer)
            config = {"configurable": {"thread_id": thread_id}}
            await app.aupdate_state(config, state_update)
            return True
        except Exception as e:
            self.logger.error(f"Failed to update state: {e}")
            return False