"""
Workflow Orchestrator
슈퍼바이저와 서브그래프를 통합하여 전체 워크플로우 조율
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')

from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime

from ..supervisor.supervisor_state import SupervisorState, create_supervisor_initial_state
from ..supervisor.supervisor_agent import SupervisorAgent
from ..subgraphs.data_collection_subgraph import DataCollectionSubgraph
from ..subgraphs.analysis_subgraph import AnalysisSubgraph
from ..core.context import SubgraphContext

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """
    Workflow Orchestrator
    - 슈퍼바이저와 서브그래프를 통합
    - 전체 워크플로우 조율
    - 서브그래프 간 데이터 전달
    """

    def __init__(
        self,
        supervisor_model: str = "gpt-4o",
        supervisor_temperature: float = 0.2
    ):
        """
        Initialize workflow orchestrator

        Args:
            supervisor_model: LLM model for supervisor
            supervisor_temperature: Temperature for supervisor reasoning
        """
        self.logger = logger

        # Initialize components
        self.supervisor = SupervisorAgent(
            model=supervisor_model,
            temperature=supervisor_temperature
        )
        self.data_collector = DataCollectionSubgraph()
        self.analyzer = AnalysisSubgraph()

        self.logger.info("WorkflowOrchestrator initialized")

    # ============== Wrapper Nodes for Subgraphs ==============

    async def execute_data_collection(
        self,
        state: SupervisorState,
        runtime: Runtime[SubgraphContext]
    ) -> Dict[str, Any]:
        """
        Execute data collection subgraph

        Args:
            state: Current supervisor state
            runtime: Runtime context

        Returns:
            State update with data collection results
        """
        try:
            self.logger.info(f"Executing data collection for session {state['session_id']}")

            # Get input for data collection
            data_input = state.get("data_collection_input", {})

            if not data_input:
                self.logger.warning("No data collection input found")
                return {
                    "data_collection_output": {},
                    "errors": ["No data collection input provided"]
                }

            # Build data collection graph
            data_graph = self.data_collector.build_graph()

            # Prepare initial state for data collection subgraph
            from ..core.states import DataCollectionState
            data_state: DataCollectionState = {
                "query_params": data_input.get("query_params", {}),
                "target_databases": [],
                "performance_data": [],
                "target_data": [],
                "client_data": [],
                "aggregated_performance": {},
                "aggregated_target": {},
                "aggregated_client": {},
                "collection_status": "pending",
                "errors": []
            }

            # Compile and run subgraph
            compiled_graph = data_graph.compile()

            # Execute subgraph
            result_state = None
            async for chunk in compiled_graph.astream(
                data_state,
                context=runtime.context
            ):
                # Get the last state
                result_state = chunk

            # Extract results from final state
            if result_state:
                # The result_state is a dict with node names as keys
                # Get the actual state from the last node
                final_node_key = list(result_state.keys())[-1] if result_state else None
                final_state = result_state.get(final_node_key, {}) if final_node_key else {}

                data_output = {
                    "performance_data": final_state.get("performance_data", []),
                    "target_data": final_state.get("target_data", []),
                    "client_data": final_state.get("client_data", []),
                    "aggregated_performance": final_state.get("aggregated_performance", {}),
                    "aggregated_target": final_state.get("aggregated_target", {}),
                    "aggregated_client": final_state.get("aggregated_client", {}),
                    "collection_status": final_state.get("collection_status", "completed")
                }

                self.logger.info("Data collection completed successfully")

                return {
                    "data_collection_output": data_output,
                    "collected_data": data_output,
                    "execution_trace": [{
                        "step": "execute_data_collection",
                        "timestamp": datetime.now().isoformat(),
                        "status": "success",
                        "records": {
                            "performance": len(data_output.get("performance_data", [])),
                            "target": len(data_output.get("target_data", [])),
                            "client": len(data_output.get("client_data", []))
                        }
                    }]
                }
            else:
                self.logger.error("Data collection returned no results")
                return {
                    "data_collection_output": {},
                    "errors": ["Data collection subgraph returned no results"]
                }

        except Exception as e:
            self.logger.error(f"Error executing data collection: {e}", exc_info=True)
            return {
                "data_collection_output": {},
                "errors": [f"Data collection execution error: {str(e)}"]
            }

    async def execute_analysis(
        self,
        state: SupervisorState,
        runtime: Runtime[SubgraphContext]
    ) -> Dict[str, Any]:
        """
        Execute analysis subgraph

        Args:
            state: Current supervisor state
            runtime: Runtime context

        Returns:
            State update with analysis results
        """
        try:
            self.logger.info(f"Executing analysis for session {state['session_id']}")

            # Get input for analysis
            analysis_input = state.get("analysis_input", {})

            if not analysis_input:
                self.logger.warning("No analysis input found")
                return {
                    "analysis_output": {},
                    "errors": ["No analysis input provided"]
                }

            # Build analysis graph
            analysis_graph = self.analyzer.build_graph()

            # Prepare initial state for analysis subgraph
            from ..core.states import AnalysisState
            analysis_state: AnalysisState = {
                "performance_data": analysis_input.get("performance_data", []),
                "target_data": analysis_input.get("target_data", []),
                "client_data": analysis_input.get("client_data", []),
                "analysis_type": analysis_input.get("analysis_type", "comprehensive"),
                "analysis_params": analysis_input.get("analysis_params", {}),
                "basic_metrics": {},
                "trend_analysis": {},
                "comparative_analysis": {},
                "insights": [],
                "analysis_report": None,
                "analysis_status": "pending",
                "errors": []
            }

            # Add aggregated data to state
            if analysis_input.get("aggregated_performance"):
                analysis_state["performance_data"] = analysis_input.get("performance_data", [])
            if analysis_input.get("aggregated_target"):
                analysis_state["target_data"] = analysis_input.get("target_data", [])
            if analysis_input.get("aggregated_client"):
                analysis_state["client_data"] = analysis_input.get("client_data", [])

            # Store aggregated data in a custom field (not part of AnalysisState TypedDict)
            # We'll pass it through the state updates
            temp_state = dict(analysis_state)
            temp_state["aggregated_performance"] = analysis_input.get("aggregated_performance", {})
            temp_state["aggregated_target"] = analysis_input.get("aggregated_target", {})
            temp_state["aggregated_client"] = analysis_input.get("aggregated_client", {})

            # Compile and run subgraph
            compiled_graph = analysis_graph.compile()

            # Execute subgraph
            result_state = None
            async for chunk in compiled_graph.astream(
                temp_state,
                context=runtime.context
            ):
                # Get the last state
                result_state = chunk

            # Extract results from final state
            if result_state:
                # The result_state is a dict with node names as keys
                # Get the actual state from the last node
                final_node_key = list(result_state.keys())[-1] if result_state else None
                final_state = result_state.get(final_node_key, {}) if final_node_key else {}

                analysis_output = {
                    "basic_metrics": final_state.get("basic_metrics", {}),
                    "trend_analysis": final_state.get("trend_analysis", {}),
                    "comparative_analysis": final_state.get("comparative_analysis", {}),
                    "insights": final_state.get("insights", []),
                    "analysis_report": final_state.get("analysis_report"),
                    "analysis_status": final_state.get("analysis_status", "completed")
                }

                self.logger.info("Analysis completed successfully")

                return {
                    "analysis_output": analysis_output,
                    "analysis_results": {
                        "basic_metrics": analysis_output.get("basic_metrics", {}),
                        "trend_analysis": analysis_output.get("trend_analysis", {}),
                        "comparative_analysis": analysis_output.get("comparative_analysis", {})
                    },
                    "insights": analysis_output.get("insights", []),
                    "execution_trace": [{
                        "step": "execute_analysis",
                        "timestamp": datetime.now().isoformat(),
                        "status": "success",
                        "insights_count": len(analysis_output.get("insights", []))
                    }]
                }
            else:
                self.logger.error("Analysis returned no results")
                return {
                    "analysis_output": {},
                    "errors": ["Analysis subgraph returned no results"]
                }

        except Exception as e:
            self.logger.error(f"Error executing analysis: {e}", exc_info=True)
            return {
                "analysis_output": {},
                "errors": [f"Analysis execution error: {str(e)}"]
            }

    # ============== Conditional Routing ==============

    def route_next_action(self, state: SupervisorState) -> str:
        """
        Route to next action based on supervisor decision

        Args:
            state: Current supervisor state

        Returns:
            Next node name
        """
        next_action = state.get("next_action")

        self.logger.info(f"Routing decision: {next_action}")

        if next_action == "data_collection":
            return "data_collection"
        elif next_action == "analysis":
            return "analysis"
        elif next_action == "final_report":
            return "final_report"
        else:
            return END

    # ============== Graph Builder ==============

    def build_graph(self) -> StateGraph:
        """
        Build complete orchestrated workflow

        Returns:
            StateGraph for entire workflow
        """
        workflow = StateGraph(
            SupervisorState,
            context_schema=SubgraphContext
        )

        # Add supervisor nodes
        workflow.add_node("understand_query", self.supervisor.understand_query)
        workflow.add_node("decompose_tasks", self.supervisor.decompose_tasks)
        workflow.add_node("create_plan", self.supervisor.create_execution_plan)
        workflow.add_node("route", self.supervisor.route_to_subgraph)

        # Add subgraph execution nodes
        workflow.add_node("data_collection", self.execute_data_collection)
        workflow.add_node("analysis", self.execute_analysis)

        # Add aggregation and final report nodes
        workflow.add_node("aggregate", self.supervisor.aggregate_results)
        workflow.add_node("final_report", self.supervisor.generate_final_answer)

        # Build workflow
        # Start -> Supervisor Reasoning
        workflow.add_edge(START, "understand_query")
        workflow.add_edge("understand_query", "decompose_tasks")
        workflow.add_edge("decompose_tasks", "create_plan")
        workflow.add_edge("create_plan", "route")

        # Route -> Conditional routing to subgraphs
        workflow.add_conditional_edges(
            "route",
            self.route_next_action,
            {
                "data_collection": "data_collection",
                "analysis": "analysis",
                "final_report": "final_report",
                END: END
            }
        )

        # Data collection -> Route again (for next decision)
        workflow.add_edge("data_collection", "route")

        # Analysis -> Aggregate
        workflow.add_edge("analysis", "aggregate")

        # Aggregate -> Final report
        workflow.add_edge("aggregate", "final_report")

        # Final report -> END
        workflow.add_edge("final_report", END)

        return workflow


def create_orchestrated_workflow(
    supervisor_model: str = "gpt-4o",
    supervisor_temperature: float = 0.2
) -> StateGraph:
    """
    Factory function to create orchestrated workflow

    Args:
        supervisor_model: LLM model for supervisor
        supervisor_temperature: Temperature for supervisor

    Returns:
        Complete orchestrated workflow graph
    """
    orchestrator = WorkflowOrchestrator(
        supervisor_model=supervisor_model,
        supervisor_temperature=supervisor_temperature
    )
    return orchestrator.build_graph()
