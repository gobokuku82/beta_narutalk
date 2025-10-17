"""
Routing Logic for Supervisor Decisions
슈퍼바이저의 의사결정에 따른 라우팅 로직
"""

import logging
from typing import Dict, Any, Literal
from ..supervisor.supervisor_state import SupervisorState

logger = logging.getLogger(__name__)


class Router:
    """
    Router for supervisor decisions
    슈퍼바이저의 결정에 따라 다음 노드로 라우팅
    """

    @staticmethod
    def route_from_planning(state: SupervisorState) -> Literal["route", "END"]:
        """
        Route after planning phase

        Args:
            state: Current supervisor state

        Returns:
            Next node: "route" or END
        """
        execution_plan = state.get("execution_plan")

        if not execution_plan:
            logger.warning("No execution plan found, ending workflow")
            return "END"

        subgraphs_required = execution_plan.get("subgraphs_required", [])

        if not subgraphs_required:
            logger.info("No subgraphs required, going to final report")
            return "route"  # Will route to final_report

        logger.info(f"Subgraphs required: {subgraphs_required}, proceeding to route")
        return "route"

    @staticmethod
    def route_to_subgraph(state: SupervisorState) -> Literal["data_collection", "analysis", "final_report", "END"]:
        """
        Route to appropriate subgraph based on next_action

        Args:
            state: Current supervisor state

        Returns:
            Next node name
        """
        next_action = state.get("next_action")

        logger.info(f"Next action determined: {next_action}")

        if next_action == "data_collection":
            return "data_collection"
        elif next_action == "analysis":
            return "analysis"
        elif next_action == "final_report":
            return "final_report"
        else:
            logger.warning(f"Unknown next action: {next_action}, ending workflow")
            return "END"

    @staticmethod
    def route_after_data_collection(state: SupervisorState) -> Literal["route", "analysis", "final_report"]:
        """
        Route after data collection completes

        Args:
            state: Current supervisor state

        Returns:
            Next node name
        """
        execution_plan = state.get("execution_plan", {})
        subgraphs_required = execution_plan.get("subgraphs_required", [])

        # Check if analysis is needed
        if "analysis" in subgraphs_required:
            analysis_done = bool(state.get("analysis_output"))
            if not analysis_done:
                logger.info("Analysis required, routing to analysis")
                return "route"  # Will route to analysis

        # No more subgraphs needed, go to final report
        logger.info("Data collection done, no more subgraphs needed")
        return "route"  # Will route to final_report

    @staticmethod
    def should_aggregate(state: SupervisorState) -> Literal["aggregate", "final_report"]:
        """
        Determine if aggregation is needed

        Args:
            state: Current supervisor state

        Returns:
            Next node name
        """
        has_data = bool(state.get("data_collection_output"))
        has_analysis = bool(state.get("analysis_output"))

        # If we have both data and analysis, aggregate them
        if has_data and has_analysis:
            logger.info("Both data and analysis available, aggregating")
            return "aggregate"

        # If we only have one, we can skip aggregation
        logger.info("Skipping aggregation, going to final report")
        return "final_report"


def create_routing_logic() -> Dict[str, Any]:
    """
    Create routing configuration for workflow

    Returns:
        Routing configuration
    """
    router = Router()

    return {
        "from_planning": router.route_from_planning,
        "to_subgraph": router.route_to_subgraph,
        "after_data_collection": router.route_after_data_collection,
        "should_aggregate": router.should_aggregate
    }


def get_execution_path(state: SupervisorState) -> Dict[str, Any]:
    """
    Analyze the execution path based on current state

    Args:
        state: Current supervisor state

    Returns:
        Execution path analysis
    """
    execution_plan = state.get("execution_plan", {})
    subgraphs_required = execution_plan.get("subgraphs_required", [])

    has_data_collection = "data_collection" in subgraphs_required
    has_analysis = "analysis" in subgraphs_required

    data_done = bool(state.get("data_collection_output"))
    analysis_done = bool(state.get("analysis_output"))

    path = {
        "total_steps": 0,
        "completed_steps": 0,
        "remaining_steps": [],
        "next_step": None
    }

    # Calculate steps
    if has_data_collection:
        path["total_steps"] += 1
        if data_done:
            path["completed_steps"] += 1
        else:
            path["remaining_steps"].append("data_collection")

    if has_analysis:
        path["total_steps"] += 1
        if analysis_done:
            path["completed_steps"] += 1
        else:
            path["remaining_steps"].append("analysis")

    # Always have final report
    path["total_steps"] += 1

    # Determine next step
    if path["remaining_steps"]:
        path["next_step"] = path["remaining_steps"][0]
    else:
        path["next_step"] = "final_report"

    return path
