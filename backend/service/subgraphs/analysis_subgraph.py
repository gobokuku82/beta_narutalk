"""
Analysis Subgraph
데이터 분석을 수행하는 서브그래프
LangGraph 0.6.x Context API 준수
"""

import logging
from typing import TypedDict, Dict, Any, List, Optional, Annotated
from datetime import datetime
import json

from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime
from operator import add

# Import calculation tools
from ..tools.calculation_tool import get_calculation_tool
from ..tools.trend_analysis_tool import get_trend_analysis_tool
from ..tools.cross_db_analysis_tool import get_cross_db_analysis_tool

logger = logging.getLogger(__name__)


# ============== State Definitions ==============

class AnalysisState(TypedDict):
    """State for analysis workflow"""
    # Input data
    performance_data: List[Dict[str, Any]]
    target_data: List[Dict[str, Any]]
    client_data: List[Dict[str, Any]]

    # Aggregated input data (from data collection)
    aggregated_performance: Dict[str, Any]
    aggregated_target: Dict[str, Any]
    aggregated_client: Dict[str, Any]

    # Analysis parameters
    analysis_type: str  # "basic", "trend", "comparative", "comprehensive"
    analysis_params: Dict[str, Any]

    # Analysis results
    basic_metrics: Dict[str, Any]
    trend_analysis: Dict[str, Any]
    comparative_analysis: Dict[str, Any]
    predictions: Dict[str, Any]
    insights: List[str]

    # Final report
    analysis_report: Dict[str, Any]

    # Metadata
    analysis_status: str
    errors: Annotated[List[str], add]
    execution_time: float


class AnalysisContext(TypedDict):
    """Context for analysis (immutable)"""
    user_id: str
    session_id: str
    request_id: str
    analysis_depth: str  # "shallow", "normal", "deep"
    include_predictions: bool
    language: str  # "ko", "en"
    timeout: int


# ============== Node Implementations ==============

class AnalysisSubgraph:
    """Subgraph for performing data analysis"""

    def __init__(self):
        """Initialize analysis subgraph"""
        self.logger = logger
        self.calculation_tool = get_calculation_tool()
        self.trend_tool = get_trend_analysis_tool()
        self.cross_db_tool = get_cross_db_analysis_tool()
        self.logger.info("AnalysisSubgraph initialized")

    # ============== Node Functions ==============

    async def calculate_basic_metrics(
        self,
        state: AnalysisState,
        runtime: Runtime[AnalysisContext]
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
                "basic_metrics": metrics,
                "analysis_status": "basic_completed"
            }

        except Exception as e:
            self.logger.error(f"Error calculating basic metrics: {e}")
            return {
                "basic_metrics": {},
                "errors": [f"Basic metrics error: {str(e)}"]
            }

    async def analyze_trends(
        self,
        state: AnalysisState,
        runtime: Runtime[AnalysisContext]
    ) -> Dict[str, Any]:
        """
        Analyze trends in the data

        Args:
            state: Current state
            runtime: Runtime with context

        Returns:
            Partial state update with trend analysis
        """
        try:
            self.logger.info(f"Analyzing trends for session {runtime.context['session_id']}")

            trend_results = {}

            # Analyze performance trends
            if state.get("aggregated_performance"):
                perf_data = state["aggregated_performance"]

                if "monthly_totals" in perf_data:
                    # Historical trend
                    monthly_values = list(perf_data["monthly_totals"].values())
                    monthly_labels = list(perf_data["monthly_totals"].keys())

                    trend_results["performance_trend"] = self.trend_tool.analyze_historical_trend(
                        monthly_values,
                        monthly_labels
                    )

                    # Moving average
                    trend_results["moving_average"] = self.trend_tool.calculate_moving_average(
                        monthly_values,
                        window=3
                    )

                    # Seasonality detection
                    trend_results["seasonality"] = self.trend_tool.detect_seasonality(
                        perf_data["monthly_totals"]
                    )

                    # Anomaly detection
                    trend_results["anomalies"] = self.trend_tool.detect_anomalies(
                        monthly_values
                    )

            # Growth analysis
            if state.get("aggregated_performance"):
                perf_data = state["aggregated_performance"]

                if "monthly_totals" in perf_data:
                    # MoM growth
                    trend_results["mom_growth"] = self.calculation_tool.calculate_mom_growth(
                        perf_data["monthly_totals"]
                    )

            self.logger.info(f"Completed trend analysis with {len(trend_results)} results")

            return {
                "trend_analysis": trend_results,
                "analysis_status": "trend_completed"
            }

        except Exception as e:
            self.logger.error(f"Error analyzing trends: {e}")
            return {
                "trend_analysis": {},
                "errors": [f"Trend analysis error: {str(e)}"]
            }

    async def perform_comparative_analysis(
        self,
        state: AnalysisState,
        runtime: Runtime[AnalysisContext]
    ) -> Dict[str, Any]:
        """
        Perform comparative analysis

        Args:
            state: Current state
            runtime: Runtime with context

        Returns:
            Partial state update with comparative analysis
        """
        try:
            self.logger.info(f"Performing comparative analysis for session {runtime.context['session_id']}")

            comparative_results = {}

            # Compare employees
            if state.get("aggregated_performance"):
                perf_data = state["aggregated_performance"]

                if "employee_totals" in perf_data:
                    employee_data = perf_data["employee_totals"]

                    if len(employee_data) > 1:
                        # Calculate market share for each employee
                        total = sum(employee_data.values())
                        employee_shares = {}

                        for emp, value in employee_data.items():
                            share = self.calculation_tool.calculate_market_share(value, total)
                            employee_shares[emp] = {
                                "value": value,
                                "share": share,
                                "rank": 0  # Will be set below
                            }

                        # Add rankings
                        sorted_employees = sorted(
                            employee_shares.items(),
                            key=lambda x: x[1]["value"],
                            reverse=True
                        )

                        for rank, (emp, data) in enumerate(sorted_employees, 1):
                            employee_shares[emp]["rank"] = rank

                        comparative_results["employee_comparison"] = employee_shares

            # Compare products
            if state.get("aggregated_performance"):
                perf_data = state["aggregated_performance"]

                if "product_totals" in perf_data:
                    product_data = perf_data["product_totals"]

                    if len(product_data) > 1:
                        # Calculate market share for each product
                        total = sum(product_data.values())
                        product_shares = {}

                        for prod, value in product_data.items():
                            share = self.calculation_tool.calculate_market_share(value, total)
                            product_shares[prod] = {
                                "value": value,
                                "share": share
                            }

                        comparative_results["product_comparison"] = product_shares

            # Achievement comparison
            if state.get("basic_metrics"):
                basic_metrics = state["basic_metrics"]

                if "achievement_rates" in basic_metrics:
                    achievement_data = basic_metrics["achievement_rates"]

                    # Find best and worst performing months
                    if achievement_data:
                        best_month = max(achievement_data, key=achievement_data.get)
                        worst_month = min(achievement_data, key=achievement_data.get)

                        comparative_results["achievement_comparison"] = {
                            "best_month": {
                                "period": best_month,
                                "rate": achievement_data[best_month]
                            },
                            "worst_month": {
                                "period": worst_month,
                                "rate": achievement_data[worst_month]
                            },
                            "variance": self.calculation_tool.calculate_variance(
                                list(achievement_data.values())
                            )
                        }

            self.logger.info(f"Completed comparative analysis with {len(comparative_results)} comparisons")

            return {
                "comparative_analysis": comparative_results,
                "analysis_status": "comparative_completed"
            }

        except Exception as e:
            self.logger.error(f"Error in comparative analysis: {e}")
            return {
                "comparative_analysis": {},
                "errors": [f"Comparative analysis error: {str(e)}"]
            }

    async def generate_predictions(
        self,
        state: AnalysisState,
        runtime: Runtime[AnalysisContext]
    ) -> Dict[str, Any]:
        """
        Generate predictions based on historical data

        Args:
            state: Current state
            runtime: Runtime with context

        Returns:
            Partial state update with predictions
        """
        try:
            if not runtime.context.get("include_predictions", True):
                self.logger.info("Predictions skipped per context settings")
                return {"predictions": {}, "analysis_status": "predictions_skipped"}

            self.logger.info(f"Generating predictions for session {runtime.context['session_id']}")

            prediction_results = {}

            # Performance predictions
            if state.get("aggregated_performance"):
                perf_data = state["aggregated_performance"]

                if "monthly_totals" in perf_data:
                    monthly_data = perf_data["monthly_totals"]

                    # Simple trend prediction
                    monthly_values = list(monthly_data.values())
                    if len(monthly_values) >= 3:
                        prediction_results["simple_forecast"] = self.trend_tool.predict_future_trend(
                            monthly_values,
                            periods_ahead=3
                        )

                    # Seasonal prediction
                    if len(monthly_data) >= 12:
                        prediction_results["seasonal_forecast"] = self.trend_tool.predict_with_seasonality(
                            monthly_data,
                            months_ahead=3
                        )

            # Pattern-based predictions
            if state.get("trend_analysis"):
                trend_data = state["trend_analysis"]

                if "performance_trend" in trend_data:
                    trend_info = trend_data["performance_trend"]

                    # Predict based on trend direction
                    if trend_info.get("trend_direction") == "increasing":
                        prediction_results["outlook"] = "positive"
                        prediction_results["confidence"] = trend_info.get("trend_strength", 0) * 100
                    elif trend_info.get("trend_direction") == "decreasing":
                        prediction_results["outlook"] = "negative"
                        prediction_results["confidence"] = trend_info.get("trend_strength", 0) * 100
                    else:
                        prediction_results["outlook"] = "stable"
                        prediction_results["confidence"] = 50

            self.logger.info(f"Generated {len(prediction_results)} predictions")

            return {
                "predictions": prediction_results,
                "analysis_status": "predictions_completed"
            }

        except Exception as e:
            self.logger.error(f"Error generating predictions: {e}")
            return {
                "predictions": {},
                "errors": [f"Prediction error: {str(e)}"]
            }

    async def generate_insights(
        self,
        state: AnalysisState,
        runtime: Runtime[AnalysisContext]
    ) -> Dict[str, Any]:
        """
        Generate actionable insights from analysis

        Args:
            state: Current state
            runtime: Runtime with context

        Returns:
            Partial state update with insights
        """
        try:
            self.logger.info(f"Generating insights for session {runtime.context['session_id']}")

            insights = []
            language = runtime.context.get("language", "ko")

            # Basic metrics insights
            if state.get("basic_metrics"):
                metrics = state["basic_metrics"]

                # Achievement insights
                if "average_achievement" in metrics:
                    avg_achievement = metrics["average_achievement"]
                    if avg_achievement >= 100:
                        if language == "ko":
                            insights.append(f"목표 달성률이 {avg_achievement:.1f}%로 우수합니다.")
                        else:
                            insights.append(f"Target achievement rate is excellent at {avg_achievement:.1f}%")
                    elif avg_achievement < 80:
                        if language == "ko":
                            insights.append(f"목표 달성률이 {avg_achievement:.1f}%로 개선이 필요합니다.")
                        else:
                            insights.append(f"Target achievement rate needs improvement at {avg_achievement:.1f}%")

                # Top performer insights
                if "top_employees" in metrics and metrics["top_employees"]:
                    top_emp = metrics["top_employees"][0]
                    if language == "ko":
                        insights.append(f"최고 성과자는 {top_emp[0]}입니다.")
                    else:
                        insights.append(f"Top performer is {top_emp[0]}")

                # Product insights
                if "top_products" in metrics and metrics["top_products"]:
                    top_prod = metrics["top_products"][0]
                    if language == "ko":
                        insights.append(f"주력 제품은 {top_prod[0]}입니다.")
                    else:
                        insights.append(f"Main product is {top_prod[0]}")

            # Trend insights
            if state.get("trend_analysis"):
                trend_data = state["trend_analysis"]

                # Performance trend insights
                if "performance_trend" in trend_data:
                    trend = trend_data["performance_trend"]
                    if trend.get("trend_direction") == "increasing":
                        if language == "ko":
                            insights.append("매출이 상승 추세를 보이고 있습니다.")
                        else:
                            insights.append("Sales showing upward trend")
                    elif trend.get("trend_direction") == "decreasing":
                        if language == "ko":
                            insights.append("매출 하락 추세에 주의가 필요합니다.")
                        else:
                            insights.append("Sales decline needs attention")

                # Seasonality insights
                if "seasonality" in trend_data:
                    seasonality = trend_data["seasonality"]
                    if seasonality.get("has_seasonality"):
                        peak = seasonality.get("peak_season")
                        if language == "ko":
                            insights.append(f"계절성 패턴 발견: 성수기는 {peak}입니다.")
                        else:
                            insights.append(f"Seasonal pattern detected: Peak season is {peak}")

                # Anomaly insights
                if "anomalies" in trend_data:
                    anomaly_data = trend_data["anomalies"]
                    if anomaly_data.get("anomaly_count", 0) > 0:
                        count = anomaly_data["anomaly_count"]
                        if language == "ko":
                            insights.append(f"{count}개의 이상치가 발견되어 검토가 필요합니다.")
                        else:
                            insights.append(f"{count} anomalies detected requiring review")

            # Comparative insights
            if state.get("comparative_analysis"):
                comp_data = state["comparative_analysis"]

                if "employee_comparison" in comp_data:
                    emp_comp = comp_data["employee_comparison"]
                    # Find largest gap
                    if len(emp_comp) > 1:
                        shares = [d["share"] for d in emp_comp.values()]
                        gap = max(shares) - min(shares)
                        if gap > 30:
                            if language == "ko":
                                insights.append(f"직원간 성과 격차가 {gap:.1f}%로 큽니다.")
                            else:
                                insights.append(f"Performance gap between employees is large at {gap:.1f}%")

            # Prediction insights
            if state.get("predictions"):
                pred_data = state["predictions"]

                if "outlook" in pred_data:
                    outlook = pred_data["outlook"]
                    confidence = pred_data.get("confidence", 0)

                    if outlook == "positive" and confidence > 70:
                        if language == "ko":
                            insights.append("향후 전망이 긍정적입니다.")
                        else:
                            insights.append("Future outlook is positive")
                    elif outlook == "negative" and confidence > 70:
                        if language == "ko":
                            insights.append("매출 감소에 대한 대비가 필요합니다.")
                        else:
                            insights.append("Preparation needed for sales decline")

            self.logger.info(f"Generated {len(insights)} insights")

            return {
                "insights": insights,
                "analysis_status": "insights_generated"
            }

        except Exception as e:
            self.logger.error(f"Error generating insights: {e}")
            return {
                "insights": [],
                "errors": [f"Insights generation error: {str(e)}"]
            }

    async def compile_report(
        self,
        state: AnalysisState,
        runtime: Runtime[AnalysisContext]
    ) -> Dict[str, Any]:
        """
        Compile final analysis report

        Args:
            state: Current state
            runtime: Runtime with context

        Returns:
            Partial state update with final report
        """
        try:
            self.logger.info(f"Compiling final report for session {runtime.context['session_id']}")

            report = {
                "report_id": runtime.context["request_id"],
                "timestamp": datetime.now().isoformat(),
                "analysis_type": state.get("analysis_type", "comprehensive"),
                "summary": {},
                "details": {},
                "recommendations": []
            }

            # Summary section
            if state.get("basic_metrics"):
                metrics = state["basic_metrics"]
                report["summary"] = {
                    "total_performance": metrics.get("total_performance", 0),
                    "average_achievement": metrics.get("average_achievement", 0),
                    "total_clients": metrics.get("total_clients", 0)
                }

            # Details section
            report["details"] = {
                "basic_metrics": state.get("basic_metrics", {}),
                "trend_analysis": state.get("trend_analysis", {}),
                "comparative_analysis": state.get("comparative_analysis", {}),
                "predictions": state.get("predictions", {})
            }

            # Insights and recommendations
            report["insights"] = state.get("insights", [])

            # Generate recommendations based on insights
            recommendations = []

            # Based on achievement rate
            if state.get("basic_metrics", {}).get("average_achievement", 0) < 80:
                recommendations.append({
                    "priority": "high",
                    "action": "목표 달성률 개선을 위한 전략 수립 필요",
                    "details": "현재 달성률이 목표 대비 낮으므로 영업 전략 재검토 필요"
                })

            # Based on trend
            if state.get("trend_analysis", {}).get("performance_trend", {}).get("trend_direction") == "decreasing":
                recommendations.append({
                    "priority": "high",
                    "action": "매출 하락 원인 분석 및 대응 방안 마련",
                    "details": "하락 추세를 반전시킬 수 있는 즉각적인 조치 필요"
                })

            # Based on seasonality
            if state.get("trend_analysis", {}).get("seasonality", {}).get("has_seasonality"):
                recommendations.append({
                    "priority": "medium",
                    "action": "계절성을 고려한 영업 계획 수립",
                    "details": "성수기와 비수기에 맞는 차별화된 전략 필요"
                })

            report["recommendations"] = recommendations

            # Add execution metadata
            report["metadata"] = {
                "analysis_depth": runtime.context.get("analysis_depth", "normal"),
                "errors": state.get("errors", []),
                "execution_time": state.get("execution_time", 0)
            }

            self.logger.info("Analysis report compiled successfully")

            return {
                "analysis_report": report,
                "analysis_status": "completed"
            }

        except Exception as e:
            self.logger.error(f"Error compiling report: {e}")
            return {
                "analysis_report": {},
                "analysis_status": "failed",
                "errors": [f"Report compilation error: {str(e)}"]
            }

    # ============== Graph Builder ==============

    def build_graph(self) -> StateGraph:
        """
        Build the analysis subgraph

        Returns:
            Compiled StateGraph
        """
        # Create graph with context schema
        workflow = StateGraph(
            state_schema=AnalysisState,
            context_schema=AnalysisContext
        )

        # Add nodes
        workflow.add_node("calculate_basic", self.calculate_basic_metrics)
        workflow.add_node("analyze_trends", self.analyze_trends)
        workflow.add_node("comparative_analysis", self.perform_comparative_analysis)
        workflow.add_node("generate_predictions", self.generate_predictions)
        workflow.add_node("generate_insights", self.generate_insights)
        workflow.add_node("compile_report", self.compile_report)

        # Add conditional routing based on analysis type
        def route_analysis(state: AnalysisState) -> str:
            analysis_type = state.get("analysis_type", "comprehensive")
            if analysis_type == "basic":
                return "compile_report"
            elif analysis_type == "trend":
                return "analyze_trends"
            else:  # comprehensive or comparative
                return "analyze_trends"

        # Add edges
        workflow.add_edge(START, "calculate_basic")
        workflow.add_conditional_edges(
            "calculate_basic",
            route_analysis,
            {
                "compile_report": "compile_report",
                "analyze_trends": "analyze_trends"
            }
        )

        # Parallel analysis paths
        workflow.add_edge("analyze_trends", "comparative_analysis")
        workflow.add_edge("analyze_trends", "generate_predictions")

        # All paths lead to insights
        workflow.add_edge("comparative_analysis", "generate_insights")
        workflow.add_edge("generate_predictions", "generate_insights")

        # Insights lead to final report
        workflow.add_edge("generate_insights", "compile_report")

        # End
        workflow.add_edge("compile_report", END)

        return workflow


def create_analysis_graph() -> StateGraph:
    """
    Factory function to create analysis graph

    Returns:
        Compiled analysis graph
    """
    analyzer = AnalysisSubgraph()
    return analyzer.build_graph()