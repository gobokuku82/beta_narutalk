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
from ..tools import SQLGenerator, SQLExecutor


logger = logging.getLogger(__name__)


class SalesAnalyticsAgent(BaseAgent):
    """Agent for analyzing sales performance with Runtime support"""

    def __init__(self):
        super().__init__("sales_analytics_agent")
        self.sales_db_path = Config.get_database_path("sales")
        self.sql_generator = SQLGenerator()
        self.sql_executor = SQLExecutor()

    def _get_state_schema(self) -> Type:
        """Get the state schema for this agent"""
        return SalesState

    def _build_graph(self):
        """Build the sales analytics workflow with Text2SQL support"""
        # StateGraph with context_schema following LangGraph 0.6.x pattern
        self.workflow = StateGraph(SalesState, context_schema=AgentContext)

        # Add nodes - Text2SQL workflow
        self.workflow.add_node("parse_query", self.parse_query)
        self.workflow.add_node("generate_sql", self.generate_sql)
        self.workflow.add_node("execute_sql", self.execute_sql)
        self.workflow.add_node("format_result", self.format_result)

        # Add edges
        self.workflow.add_edge(START, "parse_query")
        self.workflow.add_edge("parse_query", "generate_sql")
        self.workflow.add_edge("generate_sql", "execute_sql")
        self.workflow.add_edge("execute_sql", "format_result")
        self.workflow.add_edge("format_result", END)

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

            # SQL/Text2SQL fields
            "parsed_query": {},
            "generated_sql": "",
            "sql_result": [],
            "formatted_result": "",

            # Legacy fields (kept for compatibility)
            "raw_data": [],
            "statistics": {},
            "aggregated_data": {},
            "charts_data": [],
            "insights": [],
            "final_report": {}
        }

    # ==================== Text2SQL Node Functions ====================
    # All nodes now receive Runtime[AgentContext] and return partial updates

    async def parse_query(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Parse the user query to extract key information

        Args:
            state: Current workflow state
            runtime: Runtime with context access

        Returns:
            Partial state update with parsed query
        """
        try:
            # Access original query from context
            original_query = getattr(runtime.context, "original_query", "")
            user_id = getattr(runtime.context, "user_id", "unknown")
            self.logger.info(f"Parsing query for user {user_id}: {original_query}")

            # Use the SQL generator to parse the query
            parsed = self.sql_generator.parse_query(original_query)

            self.logger.info(f"Parsed query components: {parsed}")

            # Return parsed information
            return {
                "status": "processing",
                "execution_step": "query_parsed",
                "parsed_query": parsed
            }

        except Exception as e:
            self.logger.error(f"Error parsing query: {e}")

            if hasattr(runtime.context, 'add_error'):
                runtime.context.add_error(f"Query parsing failed: {str(e)}")

            return {
                "status": "failed",
                "execution_step": "parsing_failed",
                "parsed_query": {}
            }

    async def generate_sql(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Generate SQL query from parsed components using LLM or rule-based approach

        Args:
            state: Current workflow state
            runtime: Runtime with context access

        Returns:
            Partial state update with generated SQL
        """
        try:
            session_id = getattr(runtime.context, "session_id", "unknown")
            original_query = getattr(runtime.context, "original_query", "")
            self.logger.info(f"Generating SQL for session: {session_id}")

            parsed_query = state.get("parsed_query", {})

            # Try LLM-based SQL generation first if available
            if self.sql_generator.use_llm:
                try:
                    # Get intent result if available from context
                    intent_result = getattr(runtime.context, "intent_result", None)

                    # Use LLM to generate SQL
                    sql, explanation = await self.sql_generator.generate_sql_with_llm(
                        original_query,
                        parsed_query,
                        intent_result
                    )

                    self.logger.info("Using LLM-generated SQL")
                except Exception as llm_error:
                    self.logger.warning(f"LLM SQL generation failed, falling back to rule-based: {llm_error}")
                    # Fall back to rule-based
                    sql, explanation = self.sql_generator.generate_sql(parsed_query)
            else:
                # Use rule-based SQL generation
                sql, explanation = self.sql_generator.generate_sql(parsed_query)

            # Validate SQL for safety
            if not self.sql_generator.validate_sql(sql):
                return {
                    "status": "failed",
                    "execution_step": "sql_validation_failed",
                    "generated_sql": sql
                }

            self.logger.info(f"Generated SQL: {sql}")
            self.logger.info(f"Explanation: {explanation}")

            return {
                "execution_step": "sql_generated",
                "generated_sql": sql
            }

        except Exception as e:
            self.logger.error(f"Error generating SQL: {e}")

            if hasattr(runtime.context, 'add_error'):
                runtime.context.add_error(f"SQL generation failed: {str(e)}")

            return {
                "execution_step": "sql_generation_failed",
                "generated_sql": ""
            }

    async def execute_sql(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Execute SQL query against the database

        Args:
            state: Current workflow state
            runtime: Runtime with context access

        Returns:
            Partial state update with query results
        """
        try:
            user_id = getattr(runtime.context, "user_id", "unknown")
            self.logger.info(f"Executing SQL for user: {user_id}")

            generated_sql = state.get("generated_sql", "")

            if not generated_sql:
                return {
                    "status": "failed",
                    "execution_step": "no_sql_to_execute",
                    "sql_result": []
                }

            # Execute SQL using the executor tool
            results, error = self.sql_executor.execute_query(generated_sql)

            if error:
                self.logger.error(f"SQL execution error: {error}")
                return {
                    "status": "failed",
                    "execution_step": "sql_execution_failed",
                    "sql_result": [],
                    "formatted_result": f"SQL 실행 오류: {error}"
                }

            self.logger.info(f"SQL executed successfully, got {len(results)} rows")

            return {
                "execution_step": "sql_executed",
                "sql_result": results
            }

        except Exception as e:
            self.logger.error(f"Error executing SQL: {e}")

            if hasattr(runtime.context, 'add_error'):
                runtime.context.add_error(f"SQL execution failed: {str(e)}")

            return {
                "status": "failed",
                "execution_step": "sql_execution_error",
                "sql_result": []
            }

    async def format_result(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Format SQL results for user presentation

        Args:
            state: Current workflow state
            runtime: Runtime with context access

        Returns:
            Partial state update with formatted result
        """
        try:
            session_id = getattr(runtime.context, "session_id", "unknown")
            original_query = getattr(runtime.context, "original_query", "")
            self.logger.info(f"Formatting results for session: {session_id}")

            sql_result = state.get("sql_result", [])
            parsed_query = state.get("parsed_query", {})

            # Use the executor's format method
            formatted = self.sql_executor.format_results(sql_result)

            # Add context from the original query
            if parsed_query.get("name"):
                name = parsed_query["name"]
                formatted = f"{name}님의 조회 결과:\n\n{formatted}"

            # Create final report structure for compatibility
            final_report = {
                "status": "success",
                "query": original_query,
                "parsed": parsed_query,
                "results_count": len(sql_result),
                "formatted_output": formatted,
                "raw_results": sql_result[:5] if sql_result else []  # First 5 for preview
            }

            self.logger.info("Results formatted successfully")

            return {
                "status": "completed",
                "execution_step": "result_formatted",
                "formatted_result": formatted,
                "final_report": final_report
            }

        except Exception as e:
            self.logger.error(f"Error formatting result: {e}")

            if hasattr(runtime.context, 'add_error'):
                runtime.context.add_error(f"Result formatting failed: {str(e)}")

            return {
                "status": "failed",
                "execution_step": "formatting_failed",
                "formatted_result": "결과 포맷팅 실패",
                "final_report": {"status": "error", "error": str(e)}
            }

    # ==================== Legacy Helper Methods (will be removed in Phase 2) ====================

    def _generate_mock_sales_data(self, employee_name: str, period: str) -> List[Dict[str, Any]]:
        """Generate mock sales data for testing - DEPRECATED"""
        # This method is kept for backward compatibility but will be removed
        return []