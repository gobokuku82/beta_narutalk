"""
SQL Executor Tool
Execute SQL queries against the actual databases
"""

import sqlite3
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class SQLExecutor:
    """Execute SQL queries on SQLite databases"""

    def __init__(self):
        # Database paths
        self.db_paths = {
            "sales_performance": Path("database/storage/sales_performance/sales_performance_db.db"),
            "sales_target": Path("database/storage/sales_performance/sales_target_db.db"),
            "clients": Path("database/storage/sales_performance/clients_db.db"),
            "hr_data": Path("database/storage/hr_information/hr_data.db")
        }

        # Default database
        self.default_db = "sales_performance"

    def execute_query(
        self,
        sql: str,
        db_name: str = None,
        params: Optional[Tuple] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Execute SQL query and return results

        Args:
            sql: SQL query to execute
            db_name: Database name (default: sales_performance)
            params: Query parameters for prepared statements

        Returns:
            Tuple of (results list, error message if any)
        """
        if not db_name:
            db_name = self.default_db

        if db_name not in self.db_paths:
            return [], f"Unknown database: {db_name}"

        db_path = self.db_paths[db_name]
        if not db_path.exists():
            return [], f"Database file not found: {db_path}"

        try:
            # Connect to database
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()

            # Execute query
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)

            # Fetch results
            rows = cursor.fetchall()

            # Convert to list of dicts
            results = []
            for row in rows:
                results.append(dict(row))

            conn.close()

            logger.info(f"Executed query successfully, got {len(results)} rows")
            return results, None

        except sqlite3.Error as e:
            error_msg = f"SQL execution error: {str(e)}"
            logger.error(error_msg)
            return [], error_msg

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return [], error_msg

    def format_results(self, results: List[Dict[str, Any]], max_rows: int = 10) -> str:
        """
        Format query results for display

        Args:
            results: Query results
            max_rows: Maximum number of rows to display

        Returns:
            Formatted string
        """
        if not results:
            return "조회 결과가 없습니다."

        # Get column names
        if results:
            columns = list(results[0].keys())
        else:
            return "결과 없음"

        # Build formatted output
        output = []
        output.append(f"총 {len(results)}건 조회됨")
        output.append("-" * 50)

        # Show first max_rows
        for i, row in enumerate(results[:max_rows], 1):
            output.append(f"\n[{i}]")
            for col in columns:
                value = row.get(col)

                # Format numeric values
                if isinstance(value, (int, float)) and value is not None:
                    if col.startswith('20'):  # Month column (202403, etc)
                        output.append(f"  {col}: {value:,.0f}원")
                    else:
                        output.append(f"  {col}: {value:,.0f}")
                else:
                    output.append(f"  {col}: {value}")

        if len(results) > max_rows:
            output.append(f"\n... 외 {len(results) - max_rows}건")

        return "\n".join(output)

    def get_database_info(self, db_name: str = None) -> Dict[str, Any]:
        """
        Get database schema information

        Args:
            db_name: Database name

        Returns:
            Database info dictionary
        """
        if not db_name:
            db_name = self.default_db

        if db_name not in self.db_paths:
            return {"error": f"Unknown database: {db_name}"}

        db_path = self.db_paths[db_name]
        if not db_path.exists():
            return {"error": f"Database file not found: {db_path}"}

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Get tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            # Get table info for each table
            table_info = {}
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                table_info[table] = [
                    {
                        "name": col[1],
                        "type": col[2],
                        "notnull": bool(col[3]),
                        "primary_key": bool(col[5])
                    }
                    for col in columns
                ]

            conn.close()

            return {
                "database": db_name,
                "path": str(db_path),
                "tables": table_info
            }

        except Exception as e:
            return {"error": str(e)}

    def test_connection(self, db_name: str = None) -> bool:
        """
        Test database connection

        Args:
            db_name: Database name

        Returns:
            True if connection successful
        """
        if not db_name:
            db_name = self.default_db

        if db_name not in self.db_paths:
            logger.error(f"Unknown database: {db_name}")
            return False

        db_path = self.db_paths[db_name]
        if not db_path.exists():
            logger.error(f"Database file not found: {db_path}")
            return False

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            logger.info(f"Database connection successful: {db_name}")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False