"""
Factory Functions for Orchestrator
오케스트레이터 초기화 및 생성을 위한 팩토리 함수들
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .workflow_orchestrator import WorkflowOrchestrator, create_orchestrated_workflow
from ..supervisor.supervisor_state import create_supervisor_initial_state
from ..core.context import SubgraphContext

logger = logging.getLogger(__name__)


def create_workflow_instance(
    supervisor_model: str = "gpt-4o",
    supervisor_temperature: float = 0.2,
    config: Optional[Dict[str, Any]] = None
) -> WorkflowOrchestrator:
    """
    Create a workflow orchestrator instance

    Args:
        supervisor_model: LLM model for supervisor
        supervisor_temperature: Temperature for supervisor reasoning
        config: Additional configuration

    Returns:
        WorkflowOrchestrator instance
    """
    logger.info(f"Creating workflow instance with model={supervisor_model}, temp={supervisor_temperature}")

    orchestrator = WorkflowOrchestrator(
        supervisor_model=supervisor_model,
        supervisor_temperature=supervisor_temperature
    )

    if config:
        logger.info(f"Applying additional config: {config}")
        # Apply any additional configuration if needed
        # This can be extended in the future

    return orchestrator


def create_workflow_with_config(config_path: Optional[Path] = None) -> WorkflowOrchestrator:
    """
    Create workflow orchestrator from config file

    Args:
        config_path: Path to configuration file (JSON or YAML)

    Returns:
        WorkflowOrchestrator instance
    """
    if config_path and config_path.exists():
        logger.info(f"Loading configuration from {config_path}")
        # TODO: Implement config file loading
        # For now, use defaults
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        return create_workflow_instance(
            supervisor_model=config.get("supervisor_model", "gpt-4o"),
            supervisor_temperature=config.get("supervisor_temperature", 0.2),
            config=config.get("additional_config")
        )
    else:
        logger.info("No config file provided, using defaults")
        return create_workflow_instance()


async def run_workflow(
    user_query: str,
    session_id: str,
    user_id: Optional[str] = None,
    orchestrator: Optional[WorkflowOrchestrator] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Run complete workflow from query to answer

    Args:
        user_query: User's query
        session_id: Session identifier
        user_id: User identifier
        orchestrator: Optional pre-created orchestrator instance
        **kwargs: Additional metadata

    Returns:
        Final workflow result
    """
    try:
        logger.info(f"Starting workflow for session {session_id}")

        # Create orchestrator if not provided
        if orchestrator is None:
            orchestrator = create_workflow_instance()

        # Build and compile graph
        graph = orchestrator.build_graph()
        compiled_graph = graph.compile()

        # Create initial state
        initial_state = create_supervisor_initial_state(
            user_query=user_query,
            session_id=session_id,
            user_id=user_id,
            **kwargs
        )

        # Create context
        context = SubgraphContext(
            session_id=session_id,
            user_id=user_id or "anonymous",
            request_metadata=kwargs
        )

        # Run workflow
        logger.info("Executing workflow...")
        final_state = None

        async for chunk in compiled_graph.astream(
            initial_state,
            context=context
        ):
            # Track progress
            final_state = chunk
            logger.debug(f"Workflow chunk: {list(chunk.keys())}")

        # Extract final result
        if final_state:
            # Get the last node's state
            final_node_key = list(final_state.keys())[-1] if final_state else None
            result_state = final_state.get(final_node_key, {}) if final_node_key else {}

            logger.info("Workflow completed successfully")

            return {
                "success": True,
                "session_id": session_id,
                "query": user_query,
                "answer": result_state.get("final_answer"),
                "report": result_state.get("final_report"),
                "status": result_state.get("status"),
                "execution_trace": result_state.get("execution_trace", []),
                "errors": result_state.get("errors", [])
            }
        else:
            logger.error("Workflow returned no results")
            return {
                "success": False,
                "session_id": session_id,
                "query": user_query,
                "error": "Workflow returned no results"
            }

    except Exception as e:
        logger.error(f"Error running workflow: {e}", exc_info=True)
        return {
            "success": False,
            "session_id": session_id,
            "query": user_query,
            "error": str(e)
        }


def create_streaming_workflow(
    user_query: str,
    session_id: str,
    user_id: Optional[str] = None,
    orchestrator: Optional[WorkflowOrchestrator] = None,
    **kwargs
):
    """
    Create a streaming workflow (async generator)

    Args:
        user_query: User's query
        session_id: Session identifier
        user_id: User identifier
        orchestrator: Optional pre-created orchestrator instance
        **kwargs: Additional metadata

    Yields:
        Workflow state updates
    """
    async def stream():
        try:
            logger.info(f"Starting streaming workflow for session {session_id}")

            # Create orchestrator if not provided
            if orchestrator is None:
                _orchestrator = create_workflow_instance()
            else:
                _orchestrator = orchestrator

            # Build and compile graph
            graph = _orchestrator.build_graph()
            compiled_graph = graph.compile()

            # Create initial state
            initial_state = create_supervisor_initial_state(
                user_query=user_query,
                session_id=session_id,
                user_id=user_id,
                **kwargs
            )

            # Create context
            context = SubgraphContext(
                session_id=session_id,
                user_id=user_id or "anonymous",
                request_metadata=kwargs
            )

            # Stream workflow
            async for chunk in compiled_graph.astream(
                initial_state,
                context=context
            ):
                # Yield each state update
                yield {
                    "type": "state_update",
                    "data": chunk,
                    "session_id": session_id
                }

            logger.info("Streaming workflow completed")

        except Exception as e:
            logger.error(f"Error in streaming workflow: {e}", exc_info=True)
            yield {
                "type": "error",
                "error": str(e),
                "session_id": session_id
            }

    return stream()


# Convenience functions

def quick_run(user_query: str, **kwargs) -> Dict[str, Any]:
    """
    Quick synchronous run (for testing)

    Args:
        user_query: User's query
        **kwargs: Additional parameters

    Returns:
        Workflow result
    """
    import asyncio
    import uuid

    session_id = kwargs.pop("session_id", str(uuid.uuid4()))

    return asyncio.run(run_workflow(
        user_query=user_query,
        session_id=session_id,
        **kwargs
    ))
