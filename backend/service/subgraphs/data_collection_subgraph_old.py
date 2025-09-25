"""
Data Collection Subgraph
여러 DB에서 데이터를 수집하는 서브그래프
LangGraph 0.6.x Context API 준수
"""

import logging
from typing import TypedDict, Dict, Any, List, Annotated
from datetime import datetime
import sqlite3
from pathlib import Path

from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime
from operator import add

logger = logging.getLogger(__name__)


# ============== State Definitions ==============

class DataCollectionState(TypedDict):
    """State for data collection workflow"""
    # Input
    query_params: Dict[str, Any]  # Contains person_name, period, client_id, etc.

    # Collection results
    performance_data: List[Dict[str, Any]]
    target_data: List[Dict[str, Any]]
    client_data: List[Dict[str, Any]]

    # Aggregated data
    aggregated_performance: Dict[str, Any]
    aggregated_target: Dict[str, Any]
    aggregated_client: Dict[str, Any]

    # Metadata
    collection_status: str
    errors: Annotated[List[str], add]
    execution_time: float


class DataCollectionContext(TypedDict):
    """Context for data collection (immutable)"""
    user_id: str
    session_id: str
    request_id: str
    db_paths: Dict[str, str]
    timeout: int
    parallel_execution: bool


# ============== Node Implementations ==============

class DataCollectionSubgraph:
    """Subgraph for collecting data from multiple databases"""

    def __init__(self):
        """Initialize data collection subgraph"""
        self.logger = logger
        self.db_paths = {
            "performance": Path("database/storage/sales_performance/sales_performance_db.db"),
            "target": Path("database/storage/sales_performance/sales_target_db.db"),
            "clients": Path("database/storage/sales_performance/clients_db.db")
        }
        self.logger.info("DataCollectionSubgraph initialized")

    # ============== Node Functions ==============

    async def collect_performance_data(
        self,
        state: DataCollectionState,
        runtime: Runtime[DataCollectionContext]
    ) -> Dict[str, Any]:
        """
        Collect sales performance data

        Args:
            state: Current state
            runtime: Runtime with context

        Returns:
            Partial state update
        """
        try:
            self.logger.info(f"Collecting performance data for session {runtime.context['session_id']}")

            params = state["query_params"]
            person_name = params.get("person_name")
            period = params.get("period")
            client_id = params.get("client_id")

            # Build query based on parameters
            if person_name:
                query = """
                SELECT * FROM sales_performance
                WHERE 담당자 = ?
                """
                query_params = (person_name,)
            elif client_id:
                query = """
                SELECT * FROM sales_performance
                WHERE 거래처ID = ?
                """
                query_params = (client_id,)
            else:
                # Get all data (limited for performance)
                query = """
                SELECT * FROM sales_performance
                LIMIT 100
                """
                query_params = ()

            # Execute query
            data = self._query_database("performance", query, query_params)

            # Filter by period if specified
            if period and data:
                filtered_data = []
                for row in data:
                    if self._matches_period(row, period):
                        filtered_data.append(row)
                data = filtered_data

            self.logger.info(f"Collected {len(data)} performance records")

            return {
                "performance_data": data,
                "collection_status": "performance_collected"
            }

        except Exception as e:
            self.logger.error(f"Error collecting performance data: {e}")
            return {
                "performance_data": [],
                "errors": [f"Performance collection error: {str(e)}"]
            }

    async def collect_target_data(
        self,
        state: DataCollectionState,
        runtime: Runtime[DataCollectionContext]
    ) -> Dict[str, Any]:
        """
        Collect sales target data

        Args:
            state: Current state
            runtime: Runtime with context

        Returns:
            Partial state update
        """
        try:
            self.logger.info(f"Collecting target data for session {runtime.context['session_id']}")

            params = state["query_params"]
            person_name = params.get("person_name")

            if person_name:
                query = """
                SELECT * FROM 영업목표
                WHERE 담당자 = ?
                """
                query_params = (person_name,)
            else:
                query = """
                SELECT * FROM 영업목표
                """
                query_params = ()

            data = self._query_database("target", query, query_params)

            self.logger.info(f"Collected {len(data)} target records")

            return {
                "target_data": data,
                "collection_status": "target_collected"
            }

        except Exception as e:
            self.logger.error(f"Error collecting target data: {e}")
            return {
                "target_data": [],
                "errors": [f"Target collection error: {str(e)}"]
            }

    async def collect_client_data(
        self,
        state: DataCollectionState,
        runtime: Runtime[DataCollectionContext]
    ) -> Dict[str, Any]:
        """
        Collect client data

        Args:
            state: Current state
            runtime: Runtime with context

        Returns:
            Partial state update
        """
        try:
            self.logger.info(f"Collecting client data for session {runtime.context['session_id']}")

            params = state["query_params"]
            client_id = params.get("client_id")
            client_name = params.get("client_name")

            if client_id:
                query = """
                SELECT * FROM 거래처자료
                WHERE 거래처ID = ?
                """
                query_params = (client_id,)
            elif client_name:
                query = """
                SELECT * FROM 거래처자료
                WHERE 병원 LIKE ?
                """
                query_params = (f"%{client_name}%",)
            else:
                # Get client IDs from performance data if available
                if state.get("performance_data"):
                    client_ids = set()
                    for row in state["performance_data"]:
                        if "거래처ID" in row:
                            client_ids.add(row["거래처ID"])

                    if client_ids:
                        placeholders = ",".join(["?"] * len(client_ids))
                        query = f"""
                        SELECT * FROM 거래처자료
                        WHERE 거래처ID IN ({placeholders})
                        """
                        query_params = tuple(client_ids)
                    else:
                        return {"client_data": []}
                else:
                    return {"client_data": []}

            data = self._query_database("clients", query, query_params)

            self.logger.info(f"Collected {len(data)} client records")

            return {
                "client_data": data,
                "collection_status": "client_collected"
            }

        except Exception as e:
            self.logger.error(f"Error collecting client data: {e}")
            return {
                "client_data": [],
                "errors": [f"Client collection error: {str(e)}"]
            }

    async def aggregate_data(
        self,
        state: DataCollectionState,
        runtime: Runtime[DataCollectionContext]
    ) -> Dict[str, Any]:
        """
        Aggregate collected data

        Args:
            state: Current state
            runtime: Runtime with context

        Returns:
            Partial state update with aggregated data
        """
        try:
            self.logger.info("Aggregating collected data")

            # Aggregate performance data
            aggregated_perf = self._aggregate_performance(state.get("performance_data", []))

            # Aggregate target data
            aggregated_target = self._aggregate_target(state.get("target_data", []))

            # Aggregate client data
            aggregated_client = self._aggregate_client(state.get("client_data", []))

            return {
                "aggregated_performance": aggregated_perf,
                "aggregated_target": aggregated_target,
                "aggregated_client": aggregated_client,
                "collection_status": "completed"
            }

        except Exception as e:
            self.logger.error(f"Error aggregating data: {e}")
            return {
                "errors": [f"Aggregation error: {str(e)}"],
                "collection_status": "failed"
            }

    # ============== Helper Methods ==============

    def _query_database(
        self,
        db_name: str,
        query: str,
        params: tuple = ()
    ) -> List[Dict[str, Any]]:
        """Execute database query"""
        db_path = self.db_paths.get(db_name)
        if not db_path or not db_path.exists():
            self.logger.error(f"Database not found: {db_name}")
            return []

        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return results
        except Exception as e:
            self.logger.error(f"Database query error: {e}")
            return []

    def _matches_period(self, row: Dict[str, Any], period: str) -> bool:
        """Check if row matches the specified period"""
        if len(period) == 4:  # Year
            # Check if any column matches the year
            for key in row:
                if key.startswith(period) and len(key) == 6:
                    return True
        elif len(period) == 6:  # Specific month
            # Check if the specific month column exists
            return period in row
        return False

    def _aggregate_performance(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate performance data"""
        if not data:
            return {}

        monthly_totals = {}
        product_totals = {}
        employee_totals = {}

        for row in data:
            # Aggregate by month
            for key, value in row.items():
                if key.startswith("20") and len(key) == 6:  # Month column
                    if value:
                        monthly_totals[key] = monthly_totals.get(key, 0) + value

            # Aggregate by product
            product = row.get("품목")
            if product:
                product_totals[product] = product_totals.get(product, 0) + sum(
                    v for k, v in row.items()
                    if k.startswith("20") and v
                )

            # Aggregate by employee
            employee = row.get("담당자")
            if employee:
                employee_totals[employee] = employee_totals.get(employee, 0) + sum(
                    v for k, v in row.items()
                    if k.startswith("20") and v
                )

        return {
            "monthly_totals": monthly_totals,
            "product_totals": product_totals,
            "employee_totals": employee_totals,
            "total_records": len(data)
        }

    def _aggregate_target(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate target data"""
        if not data:
            return {}

        monthly_targets = {}
        employee_targets = {}

        for row in data:
            # Aggregate monthly targets
            for key, value in row.items():
                if key.startswith("20") and len(key) == 6:  # Month column
                    if value:
                        monthly_targets[key] = monthly_targets.get(key, 0) + value

            # Aggregate by employee
            employee = row.get("담당자")
            if employee:
                employee_targets[employee] = sum(
                    v for k, v in row.items()
                    if k.startswith("20") and v
                )

        return {
            "monthly_targets": monthly_targets,
            "employee_targets": employee_targets,
            "total_records": len(data)
        }

    def _aggregate_client(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate client data"""
        if not data:
            return {}

        region_counts = {}
        total_patients = 0
        total_employees = 0

        for row in data:
            # Count by region
            region = row.get("지역")
            if region:
                region_counts[region] = region_counts.get(region, 0) + 1

            # Sum patients and employees
            patients = row.get("외래 환자", 0)
            employees = row.get("직원수", 0)
            total_patients += patients if patients else 0
            total_employees += employees if employees else 0

        return {
            "region_distribution": region_counts,
            "total_patients": total_patients,
            "total_employees": total_employees,
            "total_clients": len(data)
        }

    # ============== Graph Builder ==============

    def build_graph(self) -> StateGraph:
        """
        Build the data collection subgraph

        Returns:
            Compiled StateGraph
        """
        # Create graph with context schema
        workflow = StateGraph(
            state_schema=DataCollectionState,
            context_schema=DataCollectionContext
        )

        # Add nodes
        workflow.add_node("collect_performance", self.collect_performance_data)
        workflow.add_node("collect_target", self.collect_target_data)
        workflow.add_node("collect_client", self.collect_client_data)
        workflow.add_node("aggregate", self.aggregate_data)

        # Add edges for parallel collection
        workflow.add_edge(START, "collect_performance")
        workflow.add_edge(START, "collect_target")
        workflow.add_edge("collect_performance", "collect_client")  # Client depends on performance
        workflow.add_edge("collect_performance", "aggregate")
        workflow.add_edge("collect_target", "aggregate")
        workflow.add_edge("collect_client", "aggregate")
        workflow.add_edge("aggregate", END)

        return workflow


def create_data_collection_graph() -> StateGraph:
    """
    Factory function to create data collection graph

    Returns:
        Compiled data collection graph
    """
    collector = DataCollectionSubgraph()
    return collector.build_graph()