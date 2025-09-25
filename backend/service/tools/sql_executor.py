"""
SQL Executor Tool
Enhanced with safety checks, monitoring, and better error handling
"""

import sqlite3
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import time
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class SQLExecutor:
    """Execute SQL queries on SQLite databases with enhanced safety and monitoring"""

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

        # Execution limits
        self.max_execution_time = 30  # seconds
        self.max_result_rows = 10000  # maximum rows to return
        self.max_retries = 3  # retry count for transient errors

    @contextmanager
    def _get_db_connection(self, db_path: Path, timeout: int = 10):
        """
        Context manager for database connections with timeout

        Args:
            db_path: Path to database file
            timeout: Connection timeout in seconds

        Yields:
            Database connection
        """
        conn = None
        try:
            conn = sqlite3.connect(str(db_path), timeout=timeout)
            conn.row_factory = sqlite3.Row
            # Set pragmas for performance and safety
            conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
            conn.execute("PRAGMA synchronous=NORMAL")  # Balance safety/speed
            conn.execute("PRAGMA temp_store=MEMORY")  # Use memory for temp tables
            yield conn
        finally:
            if conn:
                conn.close()

    def execute(
        self,
        query: str,
        params: Optional[Tuple] = None,
        database: str = None
    ) -> List[Dict[str, Any]]:
        """
        Execute SQL query (simplified interface for subgraphs)

        Args:
            query: SQL query to execute
            params: Query parameters
            database: Database name

        Returns:
            List of result dictionaries
        """
        results, error = self.execute_query(query, database, params)
        if error:
            logger.error(f"SQL execution error: {error}")
            return []
        return results

    def execute_query(
        self,
        sql: str,
        db_name: str = None,
        params: Optional[Tuple] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Execute SQL query with enhanced safety and monitoring

        Args:
            sql: SQL query to execute
            db_name: Database name (default: sales_performance)
            params: Query parameters for prepared statements

        Returns:
            Tuple of (results list, error message if any)
        """
        if not db_name:
            db_name = self.default_db

        # Validate database
        if db_name not in self.db_paths:
            return [], f"알 수 없는 데이터베이스: {db_name}"

        db_path = self.db_paths[db_name]
        if not db_path.exists():
            return [], f"데이터베이스 파일을 찾을 수 없습니다: {db_path}"

        # Pre-execution validation
        validation_error = self._validate_query_safety(sql)
        if validation_error:
            return [], validation_error

        # Execute with retry logic
        last_error = None
        for attempt in range(self.max_retries):
            try:
                return self._execute_with_timeout(sql, db_path, params)
            except sqlite3.OperationalError as e:
                # Handle locked database or other operational errors
                last_error = str(e)
                if "locked" in last_error.lower() and attempt < self.max_retries - 1:
                    logger.warning(f"Database locked, retrying... (attempt {attempt + 1})")
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                else:
                    break
            except Exception as e:
                last_error = str(e)
                break

        # All retries failed
        error_msg = f"쿼리 실행 실패: {last_error}"
        logger.error(error_msg)
        return [], error_msg

    def _validate_query_safety(self, sql: str) -> Optional[str]:
        """
        Validate query safety before execution

        Args:
            sql: SQL query to validate

        Returns:
            Error message if unsafe, None if safe
        """
        sql_upper = sql.upper().strip()

        # Check for write operations
        write_operations = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER"]
        for op in write_operations:
            if sql_upper.startswith(op):
                return f"쓰기 작업은 허용되지 않습니다: {op}"

        # Check for multiple statements
        if ";" in sql and sql.strip()[-1] != ";":
            return "복수의 SQL 문장은 허용되지 않습니다"

        return None

    def _execute_with_timeout(
        self,
        sql: str,
        db_path: Path,
        params: Optional[Tuple] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Execute query with timeout protection

        Args:
            sql: SQL query
            db_path: Database file path
            params: Query parameters

        Returns:
            Query results or error
        """
        results = []
        error = None
        execution_complete = threading.Event()

        def execute_query():
            nonlocal results, error
            try:
                with self._get_db_connection(db_path) as conn:
                    cursor = conn.cursor()

                    # Log execution plan for complex queries
                    if "JOIN" in sql.upper() or "GROUP BY" in sql.upper():
                        try:
                            plan = cursor.execute(f"EXPLAIN QUERY PLAN {sql}").fetchall()
                            logger.debug(f"Query plan: {[dict(row) for row in plan]}")
                        except:
                            pass  # Ignore explain errors

                    # Execute query
                    start_time = time.time()
                    if params:
                        cursor.execute(sql, params)
                    else:
                        cursor.execute(sql)

                    # Fetch results with row limit
                    rows = cursor.fetchmany(self.max_result_rows)
                    execution_time = time.time() - start_time

                    # Convert to list of dicts
                    results = [dict(row) for row in rows]

                    # Check if more rows exist
                    if len(results) == self.max_result_rows:
                        logger.warning(f"Result truncated at {self.max_result_rows} rows")

                    logger.info(f"Query executed in {execution_time:.2f}s, returned {len(results)} rows")

            except Exception as e:
                error = f"실행 오류: {str(e)}"
                logger.error(error)
            finally:
                execution_complete.set()

        # Start execution in thread
        thread = threading.Thread(target=execute_query)
        thread.start()

        # Wait for completion or timeout
        if not execution_complete.wait(timeout=self.max_execution_time):
            error = f"쿼리 실행 시간 초과 ({self.max_execution_time}초)"
            logger.error(error)
            return [], error

        return results, error

    def format_results(self, results: List[Dict[str, Any]], max_rows: int = 10, context: Optional[Dict] = None) -> str:
        """
        Format query results for display with improved formatting

        Args:
            results: Query results
            max_rows: Maximum number of rows to display
            context: Optional context for better error messages

        Returns:
            Formatted string
        """
        if not results:
            # Provide context-aware messages for empty results
            if context:
                if context.get("person_name"):
                    return f"'{context['person_name']}'님의 정보가 시스템에 등록되어 있지 않습니다.\n💡 실제 직원명으로 다시 검색해주세요."
                elif context.get("team"):
                    return f"'{context['team']}' 정보를 찾을 수 없습니다.\n💡 팀별 조회는 현재 지원되지 않습니다."
                elif context.get("future_date"):
                    return f"요청하신 기간의 데이터가 없습니다.\n📅 가용 기간: 2022년 12월 ~ 2024년 11월"
            return "조회 결과가 없습니다."

        # Get column names
        columns = list(results[0].keys())

        # Build formatted output
        output = []
        output.append(f"✅ 총 {len(results)}건 조회됨")
        output.append("=" * 60)

        # Analyze result structure for better formatting
        has_ranking = any('ranking' in col.lower() or 'rank' in col.lower() for col in columns)
        has_sales = any('sales' in col.lower() or '매출' in col or col.startswith('20') for col in columns)

        # Show first max_rows
        for i, row in enumerate(results[:max_rows], 1):
            output.append(f"\n📊 [{i}]")

            # Format each column based on type and name
            for col in columns:
                value = row.get(col)

                # Skip null values
                if value is None:
                    continue

                # Format based on column type
                if col.lower() in ['ranking', 'rank', '순위']:
                    output.append(f"  🏆 {col}: {value}위")
                elif col in ['담당자', '성명', 'name']:
                    output.append(f"  👤 {col}: {value}")
                elif col in ['팀명칭', '부서', '지점']:
                    output.append(f"  🏢 {col}: {value}")
                elif isinstance(value, (int, float)):
                    # Format numeric values
                    if col.startswith('20') or '매출' in col or 'sales' in col.lower():
                        # Sales/revenue formatting
                        if value >= 100000000:  # 1억 이상
                            output.append(f"  💰 {col}: {value/100000000:,.1f}억원")
                        elif value >= 10000:  # 1만 이상
                            output.append(f"  💰 {col}: {value/10000:,.0f}만원")
                        else:
                            output.append(f"  💰 {col}: {value:,.0f}원")
                    elif 'rate' in col.lower() or '률' in col:
                        # Percentage formatting
                        output.append(f"  📈 {col}: {value:.1f}%")
                    elif 'count' in col.lower() or '건수' in col:
                        # Count formatting
                        output.append(f"  📋 {col}: {value:,.0f}건")
                    else:
                        # General number formatting
                        output.append(f"  📊 {col}: {value:,.0f}")
                else:
                    # Text values
                    output.append(f"  ℹ️ {col}: {value}")

        if len(results) > max_rows:
            output.append(f"\n... 외 {len(results) - max_rows}건 더 있음")

        # Add summary statistics if applicable
        if has_sales and len(results) > 1:
            output.append("\n" + "=" * 60)
            output.append("📈 요약 통계:")

            # Calculate summary for numeric columns
            for col in columns:
                if col.startswith('20') or '매출' in col or 'sales' in col.lower():
                    values = [r.get(col, 0) for r in results if isinstance(r.get(col), (int, float))]
                    if values:
                        total = sum(values)
                        avg = total / len(values) if values else 0
                        if total >= 100000000:
                            output.append(f"  • {col} 합계: {total/100000000:,.1f}억원")
                        elif total >= 10000:
                            output.append(f"  • {col} 합계: {total/10000:,.0f}만원")
                        output.append(f"  • {col} 평균: {avg/10000:,.0f}만원")

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