"""
Supervisor Agent
추론(Reasoning)과 실행 통제(Execution Control)를 담당하는 슈퍼바이저
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')

from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from .supervisor_state import SupervisorState, create_supervisor_initial_state
from ..core.context import SubgraphContext

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """
    Supervisor Agent
    - 사용자 질의 이해 및 분석
    - 작업 분해 및 실행 계획 수립
    - 서브그래프 선택 및 실행 통제
    - 결과 통합 및 최종 응답 생성
    """

    def __init__(self, model: str = "gpt-4o", temperature: float = 0.2):
        """
        Initialize supervisor agent

        Args:
            model: LLM model name
            temperature: Temperature for reasoning
        """
        self.logger = logger
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=2000
        )
        self.logger.info(f"SupervisorAgent initialized with {model}")

    # ============== Reasoning Nodes ==============

    async def understand_query(
        self,
        state: SupervisorState,
        runtime: Runtime[SubgraphContext]
    ) -> Dict[str, Any]:
        """
        Understand user query and extract intent

        Args:
            state: Current state
            runtime: Runtime context

        Returns:
            State update with query understanding
        """
        try:
            user_query = state["user_query"]
            self.logger.info(f"Understanding query: {user_query[:100]}...")

            prompt = f"""
            Analyze the user's query and extract key information.

            User query: {user_query}

            Extract and return ONLY a valid JSON object with:
            {{
                "intent": "data_retrieval" | "analysis" | "comparison" | "report_generation" | "mixed",
                "entities": {{
                    "person_name": "extracted person name or null",
                    "client_id": "extracted client ID or null",
                    "client_name": "extracted client name or null",
                    "period": "extracted time period or null",
                    "product": "extracted product name or null"
                }},
                "required_data": ["list of required data sources"],
                "analysis_type": "basic" | "trend" | "comparative" | "comprehensive",
                "complexity": "simple" | "moderate" | "complex"
            }}

            Example: {{"intent": "analysis", "entities": {{"person_name": "김철수", "period": "2024"}}, "required_data": ["sales_performance", "sales_target"], "analysis_type": "comprehensive", "complexity": "moderate"}}
            """

            messages = [
                SystemMessage(content="You are an expert query analyzer. Extract structured information from user queries."),
                HumanMessage(content=prompt)
            ]

            response = await self.llm.ainvoke(messages)
            content = self._clean_json_response(response.content)
            understanding = json.loads(content)

            self.logger.info(f"Query understanding: {understanding}")

            return {
                "query_understanding": understanding,
                "current_step": "query_understood",
                "execution_trace": [{
                    "step": "understand_query",
                    "timestamp": datetime.now().isoformat(),
                    "result": "success"
                }]
            }

        except Exception as e:
            self.logger.error(f"Error understanding query: {e}")
            return {
                "errors": [f"Query understanding error: {str(e)}"],
                "status": "failed"
            }

    async def decompose_tasks(
        self,
        state: SupervisorState,
        runtime: Runtime[SubgraphContext]
    ) -> Dict[str, Any]:
        """
        Decompose query into executable tasks

        Args:
            state: Current state
            runtime: Runtime context

        Returns:
            State update with task decomposition
        """
        try:
            understanding = state["query_understanding"]
            self.logger.info("Decomposing tasks based on query understanding")

            prompt = f"""
            Based on the query understanding, decompose this into specific tasks.

            Query understanding:
            {json.dumps(understanding, ensure_ascii=False, indent=2)}

            Return ONLY a valid JSON array of tasks:
            [
                {{
                    "task_id": "unique_id",
                    "task_type": "data_collection" | "analysis" | "report_generation",
                    "description": "what this task does",
                    "dependencies": ["list of task_ids this depends on"],
                    "required_subgraph": "data_collection" | "analysis" | "none",
                    "priority": 1-10
                }}
            ]

            Example: [{{"task_id": "collect_sales", "task_type": "data_collection", "description": "Collect sales performance data", "dependencies": [], "required_subgraph": "data_collection", "priority": 10}}]
            """

            messages = [
                SystemMessage(content="You are a task planning expert. Break down complex queries into executable tasks."),
                HumanMessage(content=prompt)
            ]

            response = await self.llm.ainvoke(messages)
            content = self._clean_json_response(response.content)
            tasks = json.loads(content)

            self.logger.info(f"Decomposed into {len(tasks)} tasks")

            return {
                "task_decomposition": tasks,
                "current_step": "tasks_decomposed",
                "execution_trace": [{
                    "step": "decompose_tasks",
                    "timestamp": datetime.now().isoformat(),
                    "tasks_count": len(tasks)
                }]
            }

        except Exception as e:
            self.logger.error(f"Error decomposing tasks: {e}")
            return {
                "errors": [f"Task decomposition error: {str(e)}"],
                "status": "failed"
            }

    async def create_execution_plan(
        self,
        state: SupervisorState,
        runtime: Runtime[SubgraphContext]
    ) -> Dict[str, Any]:
        """
        Create execution plan from decomposed tasks

        Args:
            state: Current state
            runtime: Runtime context

        Returns:
            State update with execution plan
        """
        try:
            tasks = state["task_decomposition"]
            self.logger.info("Creating execution plan")

            # Sort tasks by priority and dependencies
            sorted_tasks = sorted(tasks, key=lambda x: (-x["priority"], len(x["dependencies"])))

            # Determine subgraphs to execute
            subgraphs = set()
            for task in sorted_tasks:
                if task["required_subgraph"] != "none":
                    subgraphs.add(task["required_subgraph"])

            execution_plan = {
                "execution_order": [task["task_id"] for task in sorted_tasks],
                "subgraphs_required": list(subgraphs),
                "parallel_execution": self._identify_parallel_tasks(sorted_tasks),
                "estimated_steps": len(sorted_tasks) + len(subgraphs) + 2  # +2 for routing and final report
            }

            self.logger.info(f"Execution plan: {execution_plan}")

            return {
                "execution_plan": execution_plan,
                "subgraph_selection": list(subgraphs),
                "current_step": "plan_created",
                "status": "executing",
                "execution_trace": [{
                    "step": "create_execution_plan",
                    "timestamp": datetime.now().isoformat(),
                    "subgraphs": list(subgraphs)
                }]
            }

        except Exception as e:
            self.logger.error(f"Error creating execution plan: {e}")
            return {
                "errors": [f"Execution plan error: {str(e)}"],
                "status": "failed"
            }

    # ============== Execution Control Nodes ==============

    async def route_to_subgraph(
        self,
        state: SupervisorState,
        runtime: Runtime[SubgraphContext]
    ) -> Dict[str, Any]:
        """
        Determine next action and route to appropriate subgraph

        Args:
            state: Current state
            runtime: Runtime context

        Returns:
            State update with routing decision
        """
        try:
            plan = state.get("execution_plan", {})
            subgraphs = plan.get("subgraphs_required", [])

            # Check what has been executed
            has_data = bool(state.get("data_collection_output"))
            has_analysis = bool(state.get("analysis_output"))

            # Determine next action
            if "data_collection" in subgraphs and not has_data:
                next_action = "data_collection"
                # Prepare input for data collection
                understanding = state.get("query_understanding", {})
                entities = understanding.get("entities", {})

                data_collection_input = {
                    "query_params": {
                        "original_query": state["user_query"],
                        "person_name": entities.get("person_name"),
                        "client_id": entities.get("client_id"),
                        "client_name": entities.get("client_name"),
                        "period": entities.get("period"),
                        "product": entities.get("product")
                    }
                }

                self.logger.info("Routing to data_collection subgraph")

                return {
                    "next_action": next_action,
                    "data_collection_input": data_collection_input,
                    "current_step": "routing_to_data_collection",
                    "execution_trace": [{
                        "step": "route_to_subgraph",
                        "timestamp": datetime.now().isoformat(),
                        "action": next_action
                    }]
                }

            elif "analysis" in subgraphs and not has_analysis and has_data:
                next_action = "analysis"
                # Prepare input for analysis
                understanding = state.get("query_understanding", {})
                data_output = state.get("data_collection_output", {})

                analysis_input = {
                    "performance_data": data_output.get("performance_data", []),
                    "target_data": data_output.get("target_data", []),
                    "client_data": data_output.get("client_data", []),
                    "aggregated_performance": data_output.get("aggregated_performance", {}),
                    "aggregated_target": data_output.get("aggregated_target", {}),
                    "aggregated_client": data_output.get("aggregated_client", {}),
                    "analysis_type": understanding.get("analysis_type", "comprehensive"),
                    "analysis_params": {}
                }

                self.logger.info("Routing to analysis subgraph")

                return {
                    "next_action": next_action,
                    "analysis_input": analysis_input,
                    "current_step": "routing_to_analysis",
                    "execution_trace": [{
                        "step": "route_to_subgraph",
                        "timestamp": datetime.now().isoformat(),
                        "action": next_action
                    }]
                }

            else:
                # All subgraphs executed, go to final report
                next_action = "final_report"
                self.logger.info("Routing to final report generation")

                return {
                    "next_action": next_action,
                    "current_step": "routing_to_final_report",
                    "execution_trace": [{
                        "step": "route_to_subgraph",
                        "timestamp": datetime.now().isoformat(),
                        "action": next_action
                    }]
                }

        except Exception as e:
            self.logger.error(f"Error routing to subgraph: {e}")
            return {
                "errors": [f"Routing error: {str(e)}"],
                "status": "failed"
            }

    async def aggregate_results(
        self,
        state: SupervisorState,
        runtime: Runtime[SubgraphContext]
    ) -> Dict[str, Any]:
        """
        Aggregate results from subgraphs

        Args:
            state: Current state
            runtime: Runtime context

        Returns:
            State update with aggregated results
        """
        try:
            self.logger.info("Aggregating results from subgraphs")

            collected_data = {}
            analysis_results = {}
            insights = []

            # Aggregate data collection results
            if state.get("data_collection_output"):
                data_output = state["data_collection_output"]
                collected_data = {
                    "performance_data": data_output.get("performance_data", []),
                    "target_data": data_output.get("target_data", []),
                    "client_data": data_output.get("client_data", []),
                    "aggregated_performance": data_output.get("aggregated_performance", {}),
                    "aggregated_target": data_output.get("aggregated_target", {}),
                    "aggregated_client": data_output.get("aggregated_client", {}),
                }

            # Aggregate analysis results
            if state.get("analysis_output"):
                analysis_output = state["analysis_output"]
                analysis_results = {
                    "basic_metrics": analysis_output.get("basic_metrics", {}),
                    "trend_analysis": analysis_output.get("trend_analysis", {}),
                    "comparative_analysis": analysis_output.get("comparative_analysis", {}),
                }
                insights = analysis_output.get("insights", [])

            return {
                "collected_data": collected_data,
                "analysis_results": analysis_results,
                "insights": insights,
                "current_step": "results_aggregated",
                "execution_trace": [{
                    "step": "aggregate_results",
                    "timestamp": datetime.now().isoformat(),
                    "data_sources": len(collected_data),
                    "analysis_types": len(analysis_results)
                }]
            }

        except Exception as e:
            self.logger.error(f"Error aggregating results: {e}")
            return {
                "errors": [f"Aggregation error: {str(e)}"],
                "status": "failed"
            }

    async def generate_final_answer(
        self,
        state: SupervisorState,
        runtime: Runtime[SubgraphContext]
    ) -> Dict[str, Any]:
        """
        Generate final answer and report

        Args:
            state: Current state
            runtime: Runtime context

        Returns:
            State update with final answer
        """
        try:
            self.logger.info("Generating final answer")

            user_query = state["user_query"]
            collected_data = state.get("collected_data", {})
            analysis_results = state.get("analysis_results", {})
            insights = state.get("insights", [])

            # Prepare context for LLM
            context = {
                "query": user_query,
                "data_summary": self._summarize_data(collected_data),
                "analysis_summary": self._summarize_analysis(analysis_results),
                "insights": insights
            }

            prompt = f"""
            Based on the collected data and analysis results, generate a comprehensive answer to the user's query.

            User query: {user_query}

            Available data:
            {json.dumps(context["data_summary"], ensure_ascii=False, indent=2)}

            Analysis results:
            {json.dumps(context["analysis_summary"], ensure_ascii=False, indent=2)}

            Insights:
            {json.dumps(insights, ensure_ascii=False, indent=2)}

            Generate a clear, concise answer in Korean that:
            1. Directly answers the user's question
            2. Highlights key findings and metrics
            3. Provides actionable insights
            4. Uses specific numbers and data points
            """

            messages = [
                SystemMessage(content="You are a helpful business analyst. Provide clear, data-driven answers in Korean."),
                HumanMessage(content=prompt)
            ]

            response = await self.llm.ainvoke(messages)
            final_answer = response.content.strip()

            # Create final report
            final_report = {
                "query": user_query,
                "answer": final_answer,
                "data": collected_data,
                "analysis": analysis_results,
                "insights": insights,
                "session_id": state["session_id"],
                "timestamp": datetime.now().isoformat()
            }

            self.logger.info("Final answer generated successfully")

            return {
                "final_answer": final_answer,
                "final_report": final_report,
                "status": "completed",
                "current_step": "completed",
                "end_time": datetime.now().isoformat(),
                "execution_trace": [{
                    "step": "generate_final_answer",
                    "timestamp": datetime.now().isoformat(),
                    "result": "success"
                }]
            }

        except Exception as e:
            self.logger.error(f"Error generating final answer: {e}")
            return {
                "errors": [f"Final answer generation error: {str(e)}"],
                "status": "failed",
                "end_time": datetime.now().isoformat()
            }

    # ============== Helper Methods ==============

    def _clean_json_response(self, content: str) -> str:
        """Clean JSON response from LLM (remove markdown formatting)"""
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])
            if content.startswith("json"):
                content = content[4:].strip()
        return content

    def _identify_parallel_tasks(self, tasks: List[Dict[str, Any]]) -> List[List[str]]:
        """Identify tasks that can be executed in parallel"""
        parallel_groups = []
        current_group = []

        for task in tasks:
            if not task["dependencies"]:
                current_group.append(task["task_id"])
            else:
                if current_group:
                    parallel_groups.append(current_group)
                    current_group = []

        if current_group:
            parallel_groups.append(current_group)

        return parallel_groups

    def _summarize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize collected data"""
        summary = {}

        if data.get("performance_data"):
            summary["performance_records"] = len(data["performance_data"])

        if data.get("target_data"):
            summary["target_records"] = len(data["target_data"])

        if data.get("client_data"):
            summary["client_records"] = len(data["client_data"])

        if data.get("aggregated_performance"):
            agg_perf = data["aggregated_performance"]
            summary["total_performance"] = sum(agg_perf.get("monthly_totals", {}).values())

        if data.get("aggregated_target"):
            agg_target = data["aggregated_target"]
            summary["total_target"] = sum(agg_target.get("monthly_targets", {}).values())

        return summary

    def _summarize_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize analysis results"""
        summary = {}

        if analysis.get("basic_metrics"):
            metrics = analysis["basic_metrics"]
            summary["key_metrics"] = {
                "total_performance": metrics.get("total_performance"),
                "average_achievement": metrics.get("average_achievement"),
                "total_clients": metrics.get("total_clients")
            }

        if analysis.get("trend_analysis"):
            trends = analysis["trend_analysis"]
            summary["trend_type"] = trends.get("performance_trend", {}).get("trend_type")

        if analysis.get("comparative_analysis"):
            comps = analysis["comparative_analysis"]
            summary["comparisons_count"] = len(comps)

        return summary

    # ============== Conditional Routing ==============

    def should_continue(self, state: SupervisorState) -> str:
        """
        Determine if workflow should continue or end

        Args:
            state: Current state

        Returns:
            Next node name or END
        """
        next_action = state.get("next_action")

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
        Build supervisor graph

        Returns:
            StateGraph for supervisor
        """
        workflow = StateGraph(
            SupervisorState,
            context_schema=SubgraphContext
        )

        # Add reasoning nodes
        workflow.add_node("understand_query", self.understand_query)
        workflow.add_node("decompose_tasks", self.decompose_tasks)
        workflow.add_node("create_plan", self.create_execution_plan)

        # Add execution control nodes
        workflow.add_node("route", self.route_to_subgraph)
        workflow.add_node("aggregate", self.aggregate_results)
        workflow.add_node("final_report", self.generate_final_answer)

        # Add edges for reasoning flow
        workflow.add_edge(START, "understand_query")
        workflow.add_edge("understand_query", "decompose_tasks")
        workflow.add_edge("decompose_tasks", "create_plan")
        workflow.add_edge("create_plan", "route")

        # Note: Conditional routing and subgraph integration will be handled by orchestrator
        # For now, route -> aggregate -> final_report
        workflow.add_edge("route", "aggregate")
        workflow.add_edge("aggregate", "final_report")
        workflow.add_edge("final_report", END)

        return workflow


def create_supervisor_graph() -> StateGraph:
    """
    Factory function to create supervisor graph

    Returns:
        Supervisor graph
    """
    supervisor = SupervisorAgent()
    return supervisor.build_graph()
