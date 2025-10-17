"""
Registry-Based Workflow Orchestrator
레지스트리를 사용하여 약한 결합으로 에이전트와 툴을 관리하는 오케스트레이터
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

from ..supervisor.supervisor_state import SupervisorState
from ..core.context import SubgraphContext
from ..registry import get_registry_manager, AgentType


logger = logging.getLogger(__name__)


class RegistryBasedOrchestrator:
    """
    Registry-Based Orchestrator
    레지스트리를 통해 에이전트와 툴을 동적으로 로드하고 실행
    """

    def __init__(
        self,
        supervisor_model: str = "gpt-4o",
        supervisor_temperature: float = 0.2,
        use_registry: bool = True
    ):
        """
        Initialize registry-based orchestrator

        Args:
            supervisor_model: LLM model for supervisor
            supervisor_temperature: Temperature for supervisor reasoning
            use_registry: Whether to use registry (vs direct instantiation)
        """
        self.logger = logger
        self.use_registry = use_registry
        self.registry_manager = get_registry_manager()

        # Initialize components from registry if available
        if use_registry:
            self._init_from_registry(supervisor_model, supervisor_temperature)
        else:
            self._init_directly(supervisor_model, supervisor_temperature)

        self.logger.info("RegistryBasedOrchestrator initialized")

    def _init_from_registry(self, model: str, temperature: float) -> None:
        """Initialize components from registry"""
        try:
            # Get supervisor from registry
            if self.registry_manager.agent_registry.has("supervisor"):
                SupervisorClass = self.registry_manager.get_agent("supervisor")
                self.supervisor = SupervisorClass(model=model, temperature=temperature)
                self.logger.info("Loaded supervisor from registry")
            else:
                self.logger.warning("Supervisor not in registry, loading directly")
                self._init_directly(model, temperature)
                return

            # Get subgraphs from registry
            if self.registry_manager.agent_registry.has("data_collection_subgraph"):
                DataCollectorClass = self.registry_manager.get_agent("data_collection_subgraph")
                self.data_collector = DataCollectorClass()
                self.logger.info("Loaded data collection subgraph from registry")
            else:
                self.logger.warning("Data collection subgraph not in registry")
                from ..subgraphs.data_collection_subgraph import DataCollectionSubgraph
                self.data_collector = DataCollectionSubgraph()

            if self.registry_manager.agent_registry.has("analysis_subgraph"):
                AnalyzerClass = self.registry_manager.get_agent("analysis_subgraph")
                self.analyzer = AnalyzerClass()
                self.logger.info("Loaded analysis subgraph from registry")
            else:
                self.logger.warning("Analysis subgraph not in registry")
                from ..subgraphs.analysis_subgraph import AnalysisSubgraph
                self.analyzer = AnalysisSubgraph()

        except Exception as e:
            self.logger.error(f"Error loading from registry: {e}")
            self.logger.info("Falling back to direct initialization")
            self._init_directly(model, temperature)

    def _init_directly(self, model: str, temperature: float) -> None:
        """Initialize components directly (fallback)"""
        from ..supervisor.supervisor_agent import SupervisorAgent
        from ..subgraphs.data_collection_subgraph import DataCollectionSubgraph
        from ..subgraphs.analysis_subgraph import AnalysisSubgraph

        self.supervisor = SupervisorAgent(model=model, temperature=temperature)
        self.data_collector = DataCollectionSubgraph()
        self.analyzer = AnalysisSubgraph()

    # ============== Wrapper Nodes for Subgraphs ==============

    async def execute_data_collection(
        self,
        state: SupervisorState,
        runtime: Runtime[SubgraphContext]
    ) -> Dict[str, Any]:
        """Execute data collection subgraph"""
        try:
            self.logger.info(f"Executing data collection for session {state['session_id']}")

            data_input = state.get("data_collection_input", {})
            if not data_input:
                return {
                    "data_collection_output": {},
                    "errors": ["No data collection input provided"]
                }

            # Build and execute subgraph
            data_graph = self.data_collector.build_graph()
            compiled_graph = data_graph.compile()

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

            result_state = None
            async for chunk in compiled_graph.astream(data_state, context=runtime.context):
                result_state = chunk

            if result_state:
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

                return {
                    "data_collection_output": data_output,
                    "collected_data": data_output,
                    "execution_trace": [{
                        "step": "execute_data_collection",
                        "timestamp": datetime.now().isoformat(),
                        "status": "success",
                        "registry_used": self.use_registry
                    }]
                }

            return {
                "data_collection_output": {},
                "errors": ["Data collection returned no results"]
            }

        except Exception as e:
            self.logger.error(f"Error executing data collection: {e}", exc_info=True)
            return {
                "data_collection_output": {},
                "errors": [f"Data collection error: {str(e)}"]
            }

    async def execute_analysis(
        self,
        state: SupervisorState,
        runtime: Runtime[SubgraphContext]
    ) -> Dict[str, Any]:
        """Execute analysis subgraph"""
        try:
            self.logger.info(f"Executing analysis for session {state['session_id']}")

            analysis_input = state.get("analysis_input", {})
            if not analysis_input:
                return {
                    "analysis_output": {},
                    "errors": ["No analysis input provided"]
                }

            # Build and execute subgraph
            analysis_graph = self.analyzer.build_graph()
            compiled_graph = analysis_graph.compile()

            from ..core.states import AnalysisState
            temp_state = {
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
                "errors": [],
                "aggregated_performance": analysis_input.get("aggregated_performance", {}),
                "aggregated_target": analysis_input.get("aggregated_target", {}),
                "aggregated_client": analysis_input.get("aggregated_client", {})
            }

            result_state = None
            async for chunk in compiled_graph.astream(temp_state, context=runtime.context):
                result_state = chunk

            if result_state:
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
                        "registry_used": self.use_registry
                    }]
                }

            return {
                "analysis_output": {},
                "errors": ["Analysis returned no results"]
            }

        except Exception as e:
            self.logger.error(f"Error executing analysis: {e}", exc_info=True)
            return {
                "analysis_output": {},
                "errors": [f"Analysis error: {str(e)}"]
            }

    # ============== Conditional Routing ==============

    def route_next_action(self, state: SupervisorState) -> str:
        """Route to next action based on supervisor decision"""
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
        """Build complete orchestrated workflow"""
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

        # Build workflow edges
        workflow.add_edge(START, "understand_query")
        workflow.add_edge("understand_query", "decompose_tasks")
        workflow.add_edge("decompose_tasks", "create_plan")
        workflow.add_edge("create_plan", "route")

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

        workflow.add_edge("data_collection", "route")
        workflow.add_edge("analysis", "aggregate")
        workflow.add_edge("aggregate", "final_report")
        workflow.add_edge("final_report", END)

        return workflow

    def get_registry_info(self) -> Dict[str, Any]:
        """Get registry information"""
        return {
            "using_registry": self.use_registry,
            "statistics": self.registry_manager.get_statistics(),
            "supervisor_registered": self.registry_manager.agent_registry.has("supervisor"),
            "subgraphs_registered": {
                "data_collection": self.registry_manager.agent_registry.has("data_collection_subgraph"),
                "analysis": self.registry_manager.agent_registry.has("analysis_subgraph")
            }
        }


def create_registry_based_workflow(
    supervisor_model: str = "gpt-4o",
    supervisor_temperature: float = 0.2,
    use_registry: bool = True
) -> StateGraph:
    """
    Factory function to create registry-based workflow

    Args:
        supervisor_model: LLM model for supervisor
        supervisor_temperature: Temperature for supervisor
        use_registry: Whether to use registry

    Returns:
        Complete orchestrated workflow graph
    """
    orchestrator = RegistryBasedOrchestrator(
        supervisor_model=supervisor_model,
        supervisor_temperature=supervisor_temperature,
        use_registry=use_registry
    )
    return orchestrator.build_graph()
