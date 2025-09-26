"""
Text2SQL Tool
공유 가능한 자연어-SQL 변환 도구
모든 Agent와 Subgraph에서 사용 가능
"""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import json

from .sql_generator import SQLGenerator
from .schema_context import SchemaContext

logger = logging.getLogger(__name__)


class Text2SQLTool:
    """
    Text2SQL conversion tool that can be shared across all components
    Provides a unified interface for natural language to SQL conversion
    """

    def __init__(self):
        """Initialize Text2SQL Tool"""
        self.sql_generator = SQLGenerator()
        self.schema_context = SchemaContext()
        self.logger = logger

        # Check LLM availability
        self.use_llm = self.sql_generator.use_llm

        if self.use_llm:
            self.logger.info("Text2SQL Tool initialized with LLM support")
        else:
            self.logger.info("Text2SQL Tool initialized (rule-based mode)")

    async def generate_sql(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Convert natural language query to SQL

        Args:
            query: Natural language query in Korean/English
            context: Optional context with user info, session info, etc.

        Returns:
            Dictionary containing:
            - sql: Generated SQL query
            - explanation: Human-readable explanation
            - database: Target database name
            - confidence: Confidence score (0-1)
            - parsed: Parsed query components
            - timestamp: Generation timestamp
            - method: "llm" or "rule-based"
        """
        try:
            self.logger.info(f"Generating SQL for query: {query[:100]}...")

            # 1. Parse the query
            parsed = self.sql_generator.parse_query(query)
            self.logger.debug(f"Parsed query: {parsed}")

            # 2. Generate SQL (LLM or rule-based)
            if self.use_llm:
                try:
                    # Try LLM generation
                    sql, explanation = await self.sql_generator.generate_sql_with_llm(
                        query=query,
                        parsed=parsed,
                        intent=context.get("intent") if context else None
                    )
                    method = "llm"
                    confidence = 0.9  # High confidence for LLM

                except Exception as e:
                    self.logger.warning(f"LLM generation failed: {e}, falling back to rule-based")
                    sql, explanation = self.sql_generator.generate_sql(parsed)
                    method = "rule-based"
                    confidence = 0.7  # Lower confidence for fallback
            else:
                # Use rule-based generation
                sql, explanation = self.sql_generator.generate_sql(parsed)
                method = "rule-based"
                confidence = 0.7

            # 3. Validate SQL
            is_valid = self.sql_generator.validate_sql(sql)
            if not is_valid:
                self.logger.warning("Generated SQL failed validation")
                confidence *= 0.5  # Reduce confidence for invalid SQL

            # 4. Determine target database
            database = self._determine_database(sql, parsed)

            # 5. Build response
            result = {
                "sql": sql,
                "explanation": explanation,
                "database": database,
                "confidence": confidence,
                "parsed": parsed,
                "timestamp": datetime.now().isoformat(),
                "method": method,
                "is_valid": is_valid
            }

            self.logger.info(f"SQL generated successfully using {method} method")
            return result

        except Exception as e:
            self.logger.error(f"Error generating SQL: {e}")
            return {
                "sql": None,
                "explanation": f"SQL 생성 실패: {str(e)}",
                "database": "sales_performance",
                "confidence": 0.0,
                "parsed": {},
                "timestamp": datetime.now().isoformat(),
                "method": "error",
                "is_valid": False,
                "error": str(e)
            }

    def _determine_database(self, sql: str, parsed: Dict[str, Any]) -> str:
        """
        Determine which database to use based on SQL and parsed query

        Args:
            sql: Generated SQL query
            parsed: Parsed query components

        Returns:
            Database name
        """
        if not sql:
            return "sales_performance"

        sql_lower = sql.lower()

        # Check for specific table names
        if "지점별목표" in sql or "sales_target" in sql_lower:
            return "sales_target"
        elif "거래처자료" in sql or "clients" in sql_lower:
            return "clients"
        elif "인사자료" in sql or "hr_data" in sql_lower:
            return "hr_data"
        else:
            # Default to sales_performance
            return "sales_performance"

    async def generate_multiple_sqls(
        self,
        queries: list[str],
        context: Optional[Dict[str, Any]] = None
    ) -> list[Dict[str, Any]]:
        """
        Generate SQL for multiple queries (batch processing)

        Args:
            queries: List of natural language queries
            context: Optional shared context

        Returns:
            List of SQL generation results
        """
        results = []

        for query in queries:
            result = await self.generate_sql(query, context)
            results.append(result)

        return results

    def get_schema_info(self, database: Optional[str] = None) -> Dict[str, Any]:
        """
        Get schema information for a database

        Args:
            database: Database name (optional, returns all if not specified)

        Returns:
            Schema information dictionary
        """
        if database:
            return {
                "database": database,
                "tables": self.schema_context.get_table_columns(database),
                "sample_queries": self.schema_context.get_example_queries()
            }
        else:
            # Return all schemas
            return {
                "databases": self.schema_context.available_tables,
                "columns": self.schema_context.get_all_schemas(),
                "sample_queries": self.schema_context.get_example_queries()
            }

    def validate_sql(self, sql: str) -> bool:
        """
        Validate SQL query for safety and correctness

        Args:
            sql: SQL query to validate

        Returns:
            True if valid and safe, False otherwise
        """
        return self.sql_generator.validate_sql(sql)


# Singleton pattern for shared instance
_text2sql_instance = None


def get_text2sql_tool() -> Text2SQLTool:
    """
    Get singleton instance of Text2SQL Tool

    Returns:
        Shared Text2SQLTool instance
    """
    global _text2sql_instance
    if _text2sql_instance is None:
        _text2sql_instance = Text2SQLTool()
    return _text2sql_instance