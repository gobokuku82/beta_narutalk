"""
Sales Analytics Agent - Sales performance analysis
Fully compliant with LangGraph 0.6.x Context API
"""

from typing import Dict, Any, List, Type
from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime
import sqlite3
import asyncio
from pathlib import Path
import logging
from datetime import datetime, timedelta
import json

from ..core.base_agent import BaseAgent
from ..core.states import SalesState
from ..core.context import AgentContext
from ..core.config import Config


logger = logging.getLogger(__name__)


class SalesAnalyticsAgent(BaseAgent):
    """Agent for analyzing sales performance with Runtime support"""

    def __init__(self):
        super().__init__("sales_analytics_agent")
        self.sales_db_path = Config.get_database_path("sales")

    def _get_state_schema(self) -> Type:
        """Get the state schema for this agent"""
        return SalesState

    def _build_graph(self):
        """Build the sales analytics workflow with context support"""
        # StateGraph with context_schema following LangGraph 0.6.x pattern
        self.workflow = StateGraph(SalesState, context_schema=AgentContext)

        # Add nodes - all nodes will receive Runtime parameter
        self.workflow.add_node("validate_request", self.validate_request)
        self.workflow.add_node("fetch_data", self.fetch_sales_data)
        self.workflow.add_node("calculate_metrics", self.calculate_metrics)
        self.workflow.add_node("generate_insights", self.generate_insights)
        self.workflow.add_node("format_report", self.format_report)

        # Add edges
        self.workflow.add_edge(START, "validate_request")
        self.workflow.add_edge("validate_request", "fetch_data")
        self.workflow.add_edge("fetch_data", "calculate_metrics")
        self.workflow.add_edge("calculate_metrics", "generate_insights")
        self.workflow.add_edge("generate_insights", "format_report")
        self.workflow.add_edge("format_report", END)

    async def _validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data"""
        required_fields = ["employee_name"]
        for field in required_fields:
            if field not in input_data:
                self.logger.error(f"Missing required field: {field}")
                return False
        return True

    def _create_initial_state(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create initial SalesState from input data
        Only workflow data, no context fields
        """
        return {
            # Workflow status fields
            "status": "pending",
            "execution_step": "starting",

            # SalesState specific fields
            "employee_name": input_data.get("employee_name", ""),
            "period": input_data.get("period", "monthly"),
            "metrics_type": input_data.get("metrics_type", "performance"),
            "raw_data": [],
            "statistics": {},
            "aggregated_data": {},
            "charts_data": [],
            "insights": [],
            "final_report": {}
        }

    # ==================== Node Functions with Runtime ====================
    # All nodes now receive Runtime[AgentContext] and return partial updates

    async def validate_request(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Validate and prepare the analytics request

        Args:
            state: Current workflow state
            runtime: Runtime with context access

        Returns:
            Partial state update (only changed fields)
        """
        try:
            # Access context through runtime
            user_id = getattr(runtime.context, "user_id", "unknown")
            self.logger.info(f"Validating request for user: {user_id}")

            # Set default period if not specified
            period = state.get("period", "monthly")

            # Set default metrics type if not specified
            metrics_type = state.get("metrics_type", "performance")

            employee_name = state.get("employee_name", "")
            self.logger.info(f"Analytics request validated - Employee: {employee_name}, Period: {period}")

            # Return ONLY changed fields (Context API pattern)
            return {
                "status": "processing",
                "execution_step": "request_validated",
                "period": period,
                "metrics_type": metrics_type
            }

        except Exception as e:
            self.logger.error(f"Error validating request: {e}")

            # Log error in context if possible
            if hasattr(runtime.context, 'add_error'):
                runtime.context.add_error(f"Request validation failed: {str(e)}")

            # Return failure status
            return {
                "status": "failed",
                "execution_step": "validation_failed"
            }

    async def fetch_sales_data(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Fetch sales data from database

        Args:
            state: Current workflow state
            runtime: Runtime with context access

        Returns:
            Partial state update
        """
        try:
            # Access context
            session_id = getattr(runtime.context, "session_id", "unknown")
            self.logger.info(f"Fetching sales data for session: {session_id}")

            employee_name = state.get("employee_name", "")
            period = state.get("period", "monthly")

            # For now, generate mock data
            # TODO: Connect to real sales database later
            mock_data = self._generate_mock_sales_data(employee_name, period)

            self.logger.info(f"Fetched {len(mock_data)} sales records")

            # Return partial update
            return {
                "execution_step": "data_fetched",
                "raw_data": mock_data
            }

        except Exception as e:
            self.logger.error(f"Error fetching sales data: {e}")

            # Log error in context
            if hasattr(runtime.context, 'add_error'):
                runtime.context.add_error(f"Data fetch failed: {str(e)}")

            return {
                "execution_step": "data_fetch_failed",
                "raw_data": []
            }

    async def calculate_metrics(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Calculate sales metrics

        Args:
            state: Current workflow state
            runtime: Runtime with context access

        Returns:
            Partial state update
        """
        try:
            # Access context for logging
            user_id = getattr(runtime.context, "user_id", "unknown")
            self.logger.info(f"Calculating metrics for user: {user_id}")

            raw_data = state.get("raw_data", [])

            if not raw_data:
                return {
                    "execution_step": "metrics_calculated",
                    "statistics": {},
                    "aggregated_data": {},
                    "charts_data": []
                }

            # Calculate basic statistics
            total_sales = sum(d.get("amount", 0) for d in raw_data)
            avg_sales = total_sales / len(raw_data) if raw_data else 0
            max_sale = max((d.get("amount", 0) for d in raw_data), default=0)
            min_sale = min((d.get("amount", 0) for d in raw_data), default=0)

            statistics = {
                "total_sales": total_sales,
                "average_sale": avg_sales,
                "max_sale": max_sale,
                "min_sale": min_sale,
                "transaction_count": len(raw_data)
            }

            # Aggregate by period
            aggregated = {}
            for record in raw_data:
                period_key = record.get("date", "").split("T")[0][:7]  # YYYY-MM
                if period_key not in aggregated:
                    aggregated[period_key] = {"count": 0, "amount": 0}
                aggregated[period_key]["count"] += 1
                aggregated[period_key]["amount"] += record.get("amount", 0)

            # Prepare chart data
            charts_data = [
                {
                    "type": "line",
                    "title": "Sales Trend",
                    "data": [
                        {"x": k, "y": v["amount"]}
                        for k, v in sorted(aggregated.items())
                    ]
                }
            ]

            self.logger.info("Metrics calculated successfully")

            # Return partial update
            return {
                "execution_step": "metrics_calculated",
                "statistics": statistics,
                "aggregated_data": aggregated,
                "charts_data": charts_data
            }

        except Exception as e:
            self.logger.error(f"Error calculating metrics: {e}")

            # Log error in context
            if hasattr(runtime.context, 'add_error'):
                runtime.context.add_error(f"Metrics calculation failed: {str(e)}")

            return {
                "execution_step": "metrics_calculation_failed",
                "statistics": {},
                "aggregated_data": {},
                "charts_data": []
            }

    async def generate_insights(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Generate insights from the metrics

        Args:
            state: Current workflow state
            runtime: Runtime with context access

        Returns:
            Partial state update
        """
        try:
            # Access context
            session_id = getattr(runtime.context, "session_id", "unknown")
            self.logger.info(f"Generating insights for session: {session_id}")

            statistics = state.get("statistics", {})
            aggregated = state.get("aggregated_data", {})

            insights = []

            # Generate basic insights
            if statistics.get("total_sales", 0) > 0:
                insights.append(f"총 매출: {statistics['total_sales']:,.0f}원")
                insights.append(f"평균 거래액: {statistics.get('average_sale', 0):,.0f}원")
                insights.append(f"총 거래 건수: {statistics.get('transaction_count', 0)}건")

            # Trend analysis
            if len(aggregated) > 1:
                periods = sorted(aggregated.keys())
                latest = aggregated[periods[-1]]["amount"]
                previous = aggregated[periods[-2]]["amount"] if len(periods) > 1 else 0

                if previous > 0:
                    change = ((latest - previous) / previous) * 100
                    trend = "증가" if change > 0 else "감소"
                    insights.append(f"전월 대비 {abs(change):.1f}% {trend}")

            self.logger.info(f"Generated {len(insights)} insights")

            # Return partial update
            return {
                "execution_step": "insights_generated",
                "insights": insights
            }

        except Exception as e:
            self.logger.error(f"Error generating insights: {e}")

            # Log error in context
            if hasattr(runtime.context, 'add_error'):
                runtime.context.add_error(f"Insight generation failed: {str(e)}")

            return {
                "execution_step": "insight_generation_failed",
                "insights": []
            }

    async def format_report(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Format the final analytics report

        Args:
            state: Current workflow state
            runtime: Runtime with context access

        Returns:
            Partial state update with final report
        """
        try:
            # Access context
            user_id = getattr(runtime.context, "user_id", "unknown")
            self.logger.info(f"Formatting report for user: {user_id}")

            final_report = {
                "status": "success",
                "employee": state.get("employee_name", ""),
                "period": state.get("period", ""),
                "statistics": state.get("statistics", {}),
                "insights": state.get("insights", []),
                "charts": state.get("charts_data", []),
                "aggregated_data": state.get("aggregated_data", {}),
                "generated_at": datetime.now().isoformat()
            }

            self.logger.info("Sales analytics report generated successfully")

            # Return partial update
            return {
                "status": "completed",
                "execution_step": "report_formatted",
                "final_report": final_report
            }

        except Exception as e:
            self.logger.error(f"Error formatting report: {e}")

            # Log error in context
            if hasattr(runtime.context, 'add_error'):
                runtime.context.add_error(f"Report formatting failed: {str(e)}")

            return {
                "status": "failed",
                "execution_step": "report_formatting_failed",
                "final_report": {
                    "status": "error",
                    "error": str(e)
                }
            }

    # ==================== Helper Methods ====================

    def _generate_mock_sales_data(self, employee_name: str, period: str) -> List[Dict[str, Any]]:
        """Generate mock sales data for testing"""
        import random

        data = []
        base_date = datetime.now()

        # Determine number of records based on period
        if period == "daily":
            days = 30
        elif period == "weekly":
            days = 7 * 12  # 12 weeks
        elif period == "yearly":
            days = 365
        else:  # monthly
            days = 30 * 6  # 6 months

        for i in range(min(days, 100)):  # Limit to 100 records
            date = base_date - timedelta(days=i)
            data.append({
                "date": date.isoformat(),
                "employee": employee_name,
                "amount": random.randint(100000, 1000000),
                "product": random.choice(["Product A", "Product B", "Product C"]),
                "customer": f"Customer_{random.randint(1, 50)}"
            })

        return data