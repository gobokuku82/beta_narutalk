"""
Analysis Subgraph
데이터 분석을 수행하는 서브그래프
LangGraph 0.6.x Context API 준수
"""

import logging
from typing import TypedDict, Dict, Any, List, Optional, Annotated, Union
from datetime import datetime
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from project root
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')

from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime
from operator import add
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Import calculation tools
from ..tools.calculation_tool import CalculationTool
from ..tools.trend_analysis_tool import TrendAnalysisTool
from ..tools.cross_db_analysis_tool import CrossDBAnalysisTool as CrossDbAnalysisTool

# Import states and context from core
from ..core.states import AnalysisState
from ..core.context import SubgraphContext

logger = logging.getLogger(__name__)


# ============== Node Implementations ==============

class AnalysisSubgraph:
    """Subgraph for performing data analysis with LLM-based tool selection"""

    def __init__(self):
        """Initialize analysis subgraph"""
        self.logger = logger

        # Initialize tools
        self.calculation_tool = CalculationTool()
        self.trend_tool = TrendAnalysisTool()
        self.cross_db_tool = CrossDbAnalysisTool()

        # Initialize LLM for tool selection
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            max_tokens=500
        )

        self.logger.info("AnalysisSubgraph initialized with LLM-based tool selection")

    # ============== Node Functions ==============

    async def select_analysis_tools(
        self,
        state: AnalysisState,
        runtime: Runtime[SubgraphContext]
    ) -> Dict[str, Any]:
        """
        Use LLM to select which analysis tools to use

        Args:
            state: Current state
            runtime: Runtime with context

        Returns:
            State update with selected tools
        """
        try:
            # Get context about the data
            has_performance = bool(state.get("aggregated_performance"))
            has_target = bool(state.get("aggregated_target"))
            has_client = bool(state.get("aggregated_client"))
            analysis_type = state.get("analysis_type", "comprehensive")

            prompt = f"""
            Based on the available data and analysis requirements, select the appropriate analysis tools.

            Available data:
            - Performance data: {has_performance}
            - Target data: {has_target}
            - Client data: {has_client}
            - Analysis type requested: {analysis_type}

            Available tools:
            1. CalculationTool: Basic metrics (sum, average, min/max, achievement rates)
            2. TrendAnalysisTool: Time series analysis, trends, patterns
            3. CrossDbAnalysisTool: Cross-database analysis, correlations

            Return ONLY a valid JSON object (no markdown, no extra text):
            {{
                "tools": [list of tool names to use],
                "analysis_depth": "shallow" | "normal" | "deep",
                "reason": "brief explanation"
            }}

            Example: {{"tools": ["CalculationTool", "TrendAnalysisTool"], "analysis_depth": "normal", "reason": "Need basic metrics and trends"}}
            """

            messages = [
                SystemMessage(content="You are an analysis tool selector. Choose only necessary tools."),
                HumanMessage(content=prompt)
            ]

            response = await self.llm.ainvoke(messages)
            # Extract JSON from response - handle potential markdown formatting
            content = response.content.strip()
            if content.startswith("```"):
                # Remove markdown code blocks
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            selection = json.loads(content)

            self.logger.info(f"Selected analysis tools: {selection['tools']}")

            return {
                "analysis_params": {
                    "selected_tools": selection["tools"],
                    "analysis_depth": selection.get("analysis_depth", "normal")
                }
                # Don't update analysis_status here - let final report do it
            }

        except Exception as e:
            self.logger.error(f"Error selecting analysis tools: {e}")
            # Default to basic tools on error
            return {
                "analysis_params": {
                    "selected_tools": ["CalculationTool", "TrendAnalysisTool"],
                    "analysis_depth": "normal"
                },
                "errors": [f"Tool selection error: {str(e)}"]
            }

    async def calculate_basic_metrics(
        self,
        state: AnalysisState,
        runtime: Runtime[SubgraphContext]
    ) -> Dict[str, Any]:
        """
        Calculate basic business metrics

        Args:
            state: Current state
            runtime: Runtime with context

        Returns:
            Partial state update with basic metrics
        """
        try:
            # Check if calculation tool is selected
            selected_tools = state.get("analysis_params", {}).get("selected_tools", [])
            if "CalculationTool" not in selected_tools:
                return {"basic_metrics": {}}

            self.logger.info(f"Calculating basic metrics for session {runtime.context['session_id']}")

            metrics = {}

            # Performance metrics
            if state.get("aggregated_performance"):
                perf_data = state["aggregated_performance"]

                # Calculate total performance
                if "monthly_totals" in perf_data:
                    monthly_values = list(perf_data["monthly_totals"].values())
                    metrics["total_performance"] = self.calculation_tool.calculate_sum(monthly_values)
                    metrics["average_monthly_performance"] = self.calculation_tool.calculate_average(monthly_values)
                    metrics["performance_range"] = self.calculation_tool.calculate_min_max(monthly_values)

                # Product performance
                if "product_totals" in perf_data:
                    metrics["top_products"] = sorted(
                        perf_data["product_totals"].items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:5]

                # Employee performance
                if "employee_totals" in perf_data:
                    metrics["top_employees"] = sorted(
                        perf_data["employee_totals"].items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:5]

            # Target achievement metrics
            if state.get("aggregated_target") and state.get("aggregated_performance"):
                target_data = state["aggregated_target"]
                perf_data = state["aggregated_performance"]

                # Calculate achievement rates
                achievement_rates = {}
                if "monthly_targets" in target_data and "monthly_totals" in perf_data:
                    for month in target_data["monthly_targets"]:
                        if month in perf_data["monthly_totals"]:
                            rate = self.calculation_tool.calculate_achievement_rate(
                                perf_data["monthly_totals"][month],
                                target_data["monthly_targets"][month]
                            )
                            achievement_rates[month] = rate

                    metrics["achievement_rates"] = achievement_rates
                    metrics["average_achievement"] = self.calculation_tool.calculate_average(
                        list(achievement_rates.values())
                    ) if achievement_rates else 0

            # Client metrics
            if state.get("aggregated_client"):
                client_data = state["aggregated_client"]
                metrics["total_clients"] = client_data.get("total_clients", 0)
                metrics["region_distribution"] = client_data.get("region_distribution", {})
                metrics["total_patients"] = client_data.get("total_patients", 0)

            self.logger.info(f"Calculated {len(metrics)} basic metrics")

            return {
                "basic_metrics": metrics
                # Don't update analysis_status here
            }

        except Exception as e:
            self.logger.error(f"Error calculating basic metrics: {e}")
            return {
                "basic_metrics": {},
                "errors": [f"Basic metrics error: {str(e)}"]
            }

    async def perform_trend_analysis(
        self,
        state: AnalysisState,
        runtime: Runtime[SubgraphContext]
    ) -> Dict[str, Any]:
        """
        Perform trend analysis on time series data

        Args:
            state: Current state
            runtime: Runtime with context

        Returns:
            Partial state update with trend analysis
        """
        try:
            # Check if trend tool is selected
            selected_tools = state.get("analysis_params", {}).get("selected_tools", [])
            if "TrendAnalysisTool" not in selected_tools:
                return {"trend_analysis": {}}

            self.logger.info(f"Performing trend analysis for session {runtime.context['session_id']}")

            trends = {}

            # Performance trends
            if state.get("aggregated_performance", {}).get("monthly_totals"):
                monthly_data = state["aggregated_performance"]["monthly_totals"]

                # Analyze monthly trends
                time_series = sorted(monthly_data.items())
                values = [v for _, v in time_series]

                if len(values) >= 3:  # Need at least 3 points for trend
                    trends["performance_trend"] = self.trend_tool.analyze_trend(values)
                    trends["moving_average"] = self.trend_tool.calculate_moving_average(values, window=3)
                    trends["growth_rates"] = self.trend_tool.calculate_growth_rates(values)
                    trends["seasonality"] = self.trend_tool.detect_seasonality(values)

            # Achievement trends
            if state.get("basic_metrics", {}).get("achievement_rates"):
                achievement_data = state["basic_metrics"]["achievement_rates"]
                time_series = sorted(achievement_data.items())
                values = [v for _, v in time_series]

                if len(values) >= 3:
                    trends["achievement_trend"] = self.trend_tool.analyze_trend(values)
                    trends["achievement_stability"] = self.trend_tool.calculate_volatility(values)

            self.logger.info(f"Identified {len(trends)} trend patterns")

            return {
                "trend_analysis": trends
                # Don't update analysis_status here
            }

        except Exception as e:
            self.logger.error(f"Error performing trend analysis: {e}")
            return {
                "trend_analysis": {},
                "errors": [f"Trend analysis error: {str(e)}"]
            }

    async def perform_comparative_analysis(
        self,
        state: AnalysisState,
        runtime: Runtime[SubgraphContext]
    ) -> Dict[str, Any]:
        """
        Perform comparative analysis across different dimensions

        Args:
            state: Current state
            runtime: Runtime with context

        Returns:
            Partial state update with comparative analysis
        """
        try:
            # Check if cross-db tool is selected
            selected_tools = state.get("analysis_params", {}).get("selected_tools", [])
            if "CrossDbAnalysisTool" not in selected_tools:
                return {"comparative_analysis": {}}

            self.logger.info(f"Performing comparative analysis for session {runtime.context['session_id']}")

            comparisons = {}

            # Compare performance across employees
            if state.get("aggregated_performance", {}).get("employee_totals"):
                employee_data = state["aggregated_performance"]["employee_totals"]
                if len(employee_data) > 1:
                    comparisons["employee_comparison"] = self.cross_db_tool.compare_entities(
                        employee_data,
                        entity_type="employee"
                    )

            # Compare performance across products
            if state.get("aggregated_performance", {}).get("product_totals"):
                product_data = state["aggregated_performance"]["product_totals"]
                if len(product_data) > 1:
                    comparisons["product_comparison"] = self.cross_db_tool.compare_entities(
                        product_data,
                        entity_type="product"
                    )

            # Compare regions
            if state.get("aggregated_client", {}).get("region_distribution"):
                region_data = state["aggregated_client"]["region_distribution"]
                if len(region_data) > 1:
                    comparisons["region_comparison"] = self.cross_db_tool.compare_entities(
                        region_data,
                        entity_type="region"
                    )

            # Performance vs Target comparison
            if state.get("aggregated_performance") and state.get("aggregated_target"):
                comparisons["target_gap_analysis"] = self.cross_db_tool.analyze_gap(
                    state["aggregated_performance"],
                    state["aggregated_target"]
                )

            self.logger.info(f"Completed {len(comparisons)} comparative analyses")

            return {
                "comparative_analysis": comparisons
                # Don't update analysis_status here
            }

        except Exception as e:
            self.logger.error(f"Error performing comparative analysis: {e}")
            return {
                "comparative_analysis": {},
                "errors": [f"Comparative analysis error: {str(e)}"]
            }

    async def generate_insights(
        self,
        state: AnalysisState,
        runtime: Runtime[SubgraphContext]
    ) -> Dict[str, Any]:
        """
        Generate insights from all analyses

        Args:
            state: Current state
            runtime: Runtime with context

        Returns:
            Partial state update with insights
        """
        try:
            self.logger.info(f"Generating insights for session {runtime.context['session_id']}")

            insights = []

            # Basic metrics insights
            if state.get("basic_metrics"):
                metrics = state["basic_metrics"]

                # Performance insights
                if "total_performance" in metrics:
                    insights.append(f"총 실적: {metrics['total_performance']:,.0f}")

                if "average_achievement" in metrics:
                    avg_achievement = metrics["average_achievement"]
                    if avg_achievement >= 100:
                        insights.append(f"목표 달성률이 {avg_achievement:.1f}%로 우수합니다")
                    elif avg_achievement < 80:
                        insights.append(f"목표 달성률이 {avg_achievement:.1f}%로 개선이 필요합니다")

                # Top performers
                if "top_employees" in metrics and metrics["top_employees"]:
                    top_employee = metrics["top_employees"][0]
                    insights.append(f"최고 실적자: {top_employee[0]} ({top_employee[1]:,.0f})")

            # Trend insights
            if state.get("trend_analysis"):
                trends = state["trend_analysis"]

                if "performance_trend" in trends:
                    trend_type = trends["performance_trend"].get("trend_type", "")
                    if trend_type == "increasing":
                        insights.append("실적이 상승 추세를 보이고 있습니다")
                    elif trend_type == "decreasing":
                        insights.append("실적이 하락 추세를 보이고 있어 주의가 필요합니다")

                if "seasonality" in trends and trends["seasonality"]:
                    insights.append("계절성 패턴이 감지되었습니다")

            # Comparative insights
            if state.get("comparative_analysis"):
                comparisons = state["comparative_analysis"]

                if "target_gap_analysis" in comparisons:
                    gap_data = comparisons["target_gap_analysis"]
                    if gap_data.get("overall_gap_percentage"):
                        gap = gap_data["overall_gap_percentage"]
                        if gap > 0:
                            insights.append(f"목표 대비 {gap:.1f}% 초과 달성했습니다")
                        else:
                            insights.append(f"목표 대비 {abs(gap):.1f}% 미달입니다")

            self.logger.info(f"Generated {len(insights)} insights")

            return {
                "insights": insights
                # Don't update analysis_status here
            }

        except Exception as e:
            self.logger.error(f"Error generating insights: {e}")
            return {
                "insights": [],
                "errors": [f"Insight generation error: {str(e)}"]
            }

    async def create_final_report(
        self,
        state: AnalysisState,
        runtime: Runtime[SubgraphContext]
    ) -> Dict[str, Any]:
        """
        Create final analysis report

        Args:
            state: Current state
            runtime: Runtime with context

        Returns:
            Partial state update with final report
        """
        try:
            self.logger.info(f"Creating final report for session {runtime.context['session_id']}")

            report = {
                "summary": {
                    "analysis_type": state.get("analysis_type", "comprehensive"),
                    "data_sources": [],
                    "tools_used": state.get("analysis_params", {}).get("selected_tools", []),
                    "analysis_depth": state.get("analysis_params", {}).get("analysis_depth", "normal")
                },
                "metrics": state.get("basic_metrics", {}),
                "trends": state.get("trend_analysis", {}),
                "comparisons": state.get("comparative_analysis", {}),
                "insights": state.get("insights", []),
                "timestamp": datetime.now().isoformat(),
                "status": "completed"
            }

            # Add data source info
            if state.get("performance_data"):
                report["summary"]["data_sources"].append("performance")
            if state.get("target_data"):
                report["summary"]["data_sources"].append("target")
            if state.get("client_data"):
                report["summary"]["data_sources"].append("client")

            self.logger.info("Final report created successfully")

            return {
                "analysis_report": report,
                "analysis_status": "completed"
            }

        except Exception as e:
            self.logger.error(f"Error creating final report: {e}")
            return {
                "analysis_report": {},
                "errors": [f"Report creation error: {str(e)}"],
                "analysis_status": "failed"
            }

    # ============== Graph Builder ==============

    def build_graph(self) -> StateGraph:
        """
        Build the analysis subgraph

        Returns:
            StateGraph configured with Context API
        """
        # Create graph with context_schema (LangGraph 0.6.x pattern)
        workflow = StateGraph(
            AnalysisState,
            context_schema=SubgraphContext
        )

        # Add nodes
        workflow.add_node("select_tools", self.select_analysis_tools)
        workflow.add_node("basic_metrics", self.calculate_basic_metrics)
        workflow.add_node("trend_analysis", self.perform_trend_analysis)
        workflow.add_node("comparative", self.perform_comparative_analysis)
        workflow.add_node("generate_insights", self.generate_insights)
        workflow.add_node("create_report", self.create_final_report)

        # Add edges - LLM selects tools first, then parallel analysis
        workflow.add_edge(START, "select_tools")
        workflow.add_edge("select_tools", "basic_metrics")
        workflow.add_edge("select_tools", "trend_analysis")
        workflow.add_edge("select_tools", "comparative")
        workflow.add_edge("basic_metrics", "generate_insights")
        workflow.add_edge("trend_analysis", "generate_insights")
        workflow.add_edge("comparative", "generate_insights")
        workflow.add_edge("generate_insights", "create_report")
        workflow.add_edge("create_report", END)

        return workflow


def create_analysis_graph() -> StateGraph:
    """
    Factory function to create analysis graph

    Returns:
        Compiled analysis graph
    """
    analyzer = AnalysisSubgraph()
    return analyzer.build_graph()