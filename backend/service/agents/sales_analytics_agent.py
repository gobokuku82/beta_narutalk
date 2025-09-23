"""
Sales Analytics Agent - Sales performance analysis
"""

from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
import sqlite3
import asyncio
from pathlib import Path
import logging
from datetime import datetime, timedelta
import json

from ..core.base_agent import BaseAgent
from ..core.states import SalesState
from ..core.config import Config


logger = logging.getLogger(__name__)


class SalesAnalyticsAgent(BaseAgent):
    """Agent for analyzing sales performance"""

    def __init__(self):
        super().__init__("sales_analytics_agent")
        self.sales_db_path = Config.get_database_path("sales")

    def _build_graph(self):
        """Build the sales analytics workflow"""
        self.workflow = StateGraph(SalesState)

        # Add nodes
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

    async def validate_request(self, state: SalesState) -> SalesState:
        """Validate and prepare the analytics request"""
        try:
            state["status"] = "processing"

            # Set default period if not specified
            if not state.get("period"):
                state["period"] = "monthly"

            # Set default metrics type if not specified
            if not state.get("metrics_type"):
                state["metrics_type"] = "performance"

            self.logger.info(f"Analytics request validated - Employee: {state.get('employee_name')}, Period: {state.get('period')}")
            return state

        except Exception as e:
            self.logger.error(f"Error validating request: {e}")
            state["error_logs"] = state.get("error_logs", []) + [str(e)]
            state["status"] = "failed"
            return state

    async def fetch_sales_data(self, state: SalesState) -> SalesState:
        """Fetch sales data from database"""
        try:
            employee_name = state.get("employee_name", "")
            period = state.get("period", "monthly")

            # For now, generate mock data
            # TODO: Connect to real sales database later
            mock_data = self._generate_mock_sales_data(employee_name, period)

            state["raw_data"] = mock_data
            self.logger.info(f"Fetched {len(mock_data)} sales records")

        except Exception as e:
            self.logger.error(f"Error fetching sales data: {e}")
            state["error_logs"] = state.get("error_logs", []) + [str(e)]
            state["raw_data"] = []

        return state

    async def calculate_metrics(self, state: SalesState) -> SalesState:
        """Calculate sales metrics"""
        try:
            raw_data = state.get("raw_data", [])

            if not raw_data:
                state["statistics"] = {}
                state["aggregated_data"] = {}
                return state

            # Calculate basic statistics
            total_sales = sum(d.get("amount", 0) for d in raw_data)
            avg_sales = total_sales / len(raw_data) if raw_data else 0
            max_sale = max((d.get("amount", 0) for d in raw_data), default=0)
            min_sale = min((d.get("amount", 0) for d in raw_data), default=0)

            state["statistics"] = {
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

            state["aggregated_data"] = aggregated

            # Prepare chart data
            state["charts_data"] = [
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

        except Exception as e:
            self.logger.error(f"Error calculating metrics: {e}")
            state["error_logs"] = state.get("error_logs", []) + [str(e)]

        return state

    async def generate_insights(self, state: SalesState) -> SalesState:
        """Generate insights from the metrics"""
        try:
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

            state["insights"] = insights
            self.logger.info(f"Generated {len(insights)} insights")

        except Exception as e:
            self.logger.error(f"Error generating insights: {e}")
            state["error_logs"] = state.get("error_logs", []) + [str(e)]
            state["insights"] = []

        return state

    async def format_report(self, state: SalesState) -> SalesState:
        """Format the final analytics report"""
        try:
            state["final_report"] = {
                "status": "success",
                "employee": state.get("employee_name", ""),
                "period": state.get("period", ""),
                "statistics": state.get("statistics", {}),
                "insights": state.get("insights", []),
                "charts": state.get("charts_data", []),
                "aggregated_data": state.get("aggregated_data", {}),
                "generated_at": datetime.now().isoformat()
            }

            state["status"] = "completed"
            self.logger.info("Sales analytics report generated successfully")

        except Exception as e:
            self.logger.error(f"Error formatting report: {e}")
            state["error_logs"] = state.get("error_logs", []) + [str(e)]
            state["status"] = "failed"
            state["final_report"] = {
                "status": "error",
                "error": str(e)
            }

        return state

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