"""
Data Collection Subgraph
여러 DB에서 데이터를 수집하는 서브그래프
LangGraph 0.6.x Context API 준수
"""

import logging
from typing import TypedDict, Dict, Any, List, Annotated, Optional
from datetime import datetime
import sqlite3
from pathlib import Path
import json
from dotenv import load_dotenv

# Load environment variables from project root
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')

from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime
from operator import add
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Import tools
from ..tools.sql_executor import SQLExecutor
from ..tools.sql_generator import SQLGenerator
from ..core.states import DataCollectionState
from ..core.context import SubgraphContext

logger = logging.getLogger(__name__)


# State and Context are now imported from core modules


# ============== Node Implementations ==============

class DataCollectionSubgraph:
    """Subgraph for collecting data from multiple databases with LLM-based tool selection"""

    def __init__(self):
        """Initialize data collection subgraph"""
        self.logger = logger
        # Use absolute paths from project root
        base_path = Path(__file__).parent.parent.parent.parent  # backend/service/subgraphs -> project root
        self.db_paths = {
            "performance": base_path / "database" / "storage" / "sales_performance" / "sales_performance_db.db",
            "target": base_path / "database" / "storage" / "sales_performance" / "sales_target_db.db",
            "clients": base_path / "database" / "storage" / "sales_performance" / "clients_db.db"
        }

        # Initialize tools
        self.sql_executor = SQLExecutor()
        self.sql_generator = SQLGenerator()

        # Initialize LLM for tool selection (api_key from environment)
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            max_tokens=500
        )

        self.logger.info("DataCollectionSubgraph initialized with LLM and tools")

    # ============== Node Functions ==============

    async def select_databases(
        self,
        state: DataCollectionState,
        runtime: Runtime[SubgraphContext]
    ) -> Dict[str, Any]:
        """
        Use LLM to select which databases to query based on user query

        Args:
            state: Current state
            runtime: Runtime with context

        Returns:
            State update with selected databases
        """
        try:
            query_params = state.get("query_params", {})
            original_query = query_params.get("original_query", "")

            # Create prompt for database selection
            prompt = f"""
            Based on the user query, determine which databases need to be queried.

            Available databases:
            1. sales_performance_db: Contains sales performance data (담당자, 거래처ID, 품목, monthly sales)
            2. sales_target_db: Contains sales targets (담당자, monthly targets)
            3. clients_db: Contains client information (거래처ID, 병원, 지역, 외래 환자, 직원수)

            User query: {original_query}

            Return ONLY a valid JSON object (no markdown, no extra text):
            {{
                "databases": [list of database names to query],
                "reason": "brief explanation"
            }}

            Example: {{"databases": ["sales_performance_db", "sales_target_db"], "reason": "Need sales and target data"}}
            """

            messages = [
                SystemMessage(content="You are a database selection expert. Select only the necessary databases."),
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

            self.logger.info(f"Selected databases: {selection['databases']}")

            return {
                "target_databases": selection["databases"]
                # Don't update collection_status here - let aggregate do it
            }

        except Exception as e:
            self.logger.error(f"Error selecting databases: {e}")
            # Default to all databases on error
            return {
                "target_databases": ["sales_performance_db", "sales_target_db", "clients_db"],
                "errors": [f"Database selection error: {str(e)}"]
            }

    async def collect_performance_data(
        self,
        state: DataCollectionState,
        runtime: Runtime[SubgraphContext]
    ) -> Dict[str, Any]:
        """
        Collect sales performance data using SQL Generator with LLM

        Args:
            state: Current state
            runtime: Runtime with context

        Returns:
            Partial state update
        """
        try:
            # Check if performance database is selected
            target_dbs = state.get("target_databases", [])
            if "sales_performance_db" not in target_dbs:
                return {"performance_data": []}

            self.logger.info(f"Collecting performance data for session {runtime.context['session_id']}")

            # Get original query from state
            original_query = state.get("query_params", {}).get("original_query", "")

            # Use SQLGenerator to generate SQL with LLM
            if original_query and self.sql_generator.use_llm:
                try:
                    # Parse query first
                    parsed = self.sql_generator.parse_query(original_query)

                    # Generate SQL using LLM
                    sql, explanation = await self.sql_generator.generate_sql_with_llm(
                        query=original_query,
                        parsed=parsed
                    )

                    self.logger.info(f"Generated SQL with LLM: {sql[:200]}...")
                    self.logger.info(f"Explanation: {explanation}")

                    # Execute the generated SQL
                    data, error = self.sql_executor.execute_query(
                        sql=sql,
                        db_name="sales_performance"
                    )

                    if error:
                        self.logger.error(f"SQL execution error: {error}")
                        # Fall back to rule-based approach
                        data = self._fallback_data_collection(state)

                except Exception as e:
                    self.logger.warning(f"LLM SQL generation failed: {e}, falling back to rule-based")
                    data = self._fallback_data_collection(state)
            else:
                # Use rule-based approach if no query or LLM not available
                data = self._fallback_data_collection(state)

            # Filter by period if specified
            if period and data:
                filtered_data = []
                for row in data:
                    if self._matches_period(row, period):
                        filtered_data.append(row)
                data = filtered_data

            self.logger.info(f"Collected {len(data)} performance records")

            # Return partial update (LangGraph 0.6.x pattern)
            return {
                "performance_data": data
                # Don't update collection_status here - let aggregate do it
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
        runtime: Runtime[SubgraphContext]
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
            # Check if target database is selected
            target_dbs = state.get("target_databases", [])
            if "sales_target_db" not in target_dbs:
                return {"target_data": []}

            self.logger.info(f"Collecting target data for session {runtime.context['session_id']}")

            params = state["query_params"]
            person_name = params.get("person_name")

            if person_name:
                query = """
                SELECT * FROM 지점별목표
                WHERE 담당자 = ?
                """
                query_params = (person_name,)
            else:
                query = """
                SELECT * FROM 지점별목표
                """
                query_params = ()

            # Use SQLExecutor tool
            data = self.sql_executor.execute(
                query=query,
                params=query_params,
                database="sales_target"
            )

            self.logger.info(f"Collected {len(data)} target records")

            # Return partial update
            return {
                "target_data": data
                # Don't update collection_status here - let aggregate do it
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
        runtime: Runtime[SubgraphContext]
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
            # Check if clients database is selected
            target_dbs = state.get("target_databases", [])
            if "clients_db" not in target_dbs:
                return {"client_data": []}

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

            # Use SQLExecutor tool
            data = self.sql_executor.execute(
                query=query,
                params=query_params,
                database="clients"
            )

            self.logger.info(f"Collected {len(data)} client records")

            # Return partial update
            return {
                "client_data": data
                # Don't update collection_status here - let aggregate do it
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
        runtime: Runtime[SubgraphContext]
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

            # Return partial update
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
            StateGraph configured with Context API
        """
        # Create graph with context_schema (LangGraph 0.6.x pattern)
        workflow = StateGraph(
            DataCollectionState,
            context_schema=SubgraphContext
        )

        # Add nodes
        workflow.add_node("select_databases", self.select_databases)
        workflow.add_node("collect_performance", self.collect_performance_data)
        workflow.add_node("collect_target", self.collect_target_data)
        workflow.add_node("collect_client", self.collect_client_data)
        workflow.add_node("aggregate", self.aggregate_data)

        # Add edges - LLM selects databases first
        workflow.add_edge(START, "select_databases")
        workflow.add_edge("select_databases", "collect_performance")
        workflow.add_edge("select_databases", "collect_target")
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