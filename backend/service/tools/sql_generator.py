"""
SQL Generator Tool
Phase 1: Rule-based SQL generation from Korean queries
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SQLGenerator:
    """Generate SQL queries from natural language (Phase 1: Rule-based)"""

    def __init__(self):
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month

        # Available columns in the database (from 202212 to 202411)
        self.available_columns = [
            "202212", "202301", "202302", "202303", "202304", "202305",
            "202306", "202307", "202308", "202309", "202310", "202311",
            "202312", "202401", "202402", "202403", "202404", "202405",
            "202406", "202407", "202408", "202409", "202410", "202411"
        ]

        # Month mapping
        self.month_map = {
            "1월": "01", "2월": "02", "3월": "03", "4월": "04",
            "5월": "05", "6월": "06", "7월": "07", "8월": "08",
            "9월": "09", "10월": "10", "11월": "11", "12월": "12",
            "일월": "01", "이월": "02", "삼월": "03", "사월": "04",
            "오월": "05", "유월": "06", "칠월": "07", "팔월": "08",
            "구월": "09", "시월": "10", "십일월": "11", "십이월": "12"
        }

    def parse_query(self, query: str) -> Dict[str, Any]:
        """
        Parse Korean query into structured components

        Args:
            query: Natural language query in Korean

        Returns:
            Parsed components dictionary
        """
        parsed = {
            "original_query": query,
            "name": None,
            "month": None,
            "year": None,
            "team": None,
            "action": None,
            "period_type": None
        }

        # Extract name (assuming Korean names are 2-4 characters)
        name_pattern = r'([가-힣]{2,4})(?:의|씨|님)?(?:\s|$)'
        name_match = re.search(name_pattern, query)
        if name_match:
            potential_name = name_match.group(1)
            # Check if it's not a month name or other keyword
            if potential_name not in self.month_map and "월" not in potential_name:
                parsed["name"] = potential_name

        # Extract month
        for month_kr, month_num in self.month_map.items():
            if month_kr in query:
                parsed["month"] = month_num
                break

        # Check for relative time expressions
        if "이번달" in query or "이번 달" in query:
            parsed["month"] = f"{self.current_month:02d}"
            parsed["year"] = self.current_year
        elif "지난달" in query or "지난 달" in query or "전월" in query:
            last_month = datetime.now() - timedelta(days=30)
            parsed["month"] = f"{last_month.month:02d}"
            parsed["year"] = last_month.year
        elif "작년" in query:
            parsed["year"] = self.current_year - 1

        # Extract year if mentioned
        year_pattern = r'(\d{4})년'
        year_match = re.search(year_pattern, query)
        if year_match:
            parsed["year"] = int(year_match.group(1))
        elif parsed["month"] and not parsed["year"]:
            # Default to current year if month is specified but year is not
            parsed["year"] = self.current_year

        # Extract team
        team_pattern = r'([가-힣]+팀|[가-힣]+부서|[가-힣]+부)'
        team_match = re.search(team_pattern, query)
        if team_match:
            parsed["team"] = team_match.group(1)

        # Determine action type
        if "실적" in query or "매출" in query or "판매" in query:
            parsed["action"] = "sales"
        elif "목표" in query:
            parsed["action"] = "target"
        elif "달성률" in query or "달성율" in query:
            parsed["action"] = "achievement_rate"
        elif "평균" in query:
            parsed["action"] = "average"
        elif "합계" in query or "총" in query:
            parsed["action"] = "sum"
        elif "비교" in query:
            parsed["action"] = "compare"
        else:
            parsed["action"] = "sales"  # Default

        logger.info(f"Parsed query: {parsed}")
        return parsed

    def generate_sql(self, parsed: Dict[str, Any]) -> Tuple[str, str]:
        """
        Generate SQL from parsed query components

        Args:
            parsed: Parsed query components

        Returns:
            Tuple of (SQL query, explanation)
        """
        name = parsed.get("name")
        month = parsed.get("month")
        year = parsed.get("year", self.current_year)
        team = parsed.get("team")
        action = parsed.get("action", "sales")

        # Construct column name for month
        if month:
            column_name = f"{year}{month}"
        else:
            # Default to current month
            column_name = f"{self.current_year}{self.current_month:02d}"

        # Validate column exists in database
        if column_name not in self.available_columns:
            # Fall back to the most recent available month
            if self.available_columns:
                column_name = self.available_columns[-1]  # Use last available month (202411)
                logger.warning(f"Requested column {year}{month} not available, using {column_name}")

        # Build SQL based on action and filters
        # Note: Using column names directly since month columns work fine
        if action == "sales":
            if name:
                # Individual sales - show all columns including the specific month
                sql = f"""
                SELECT *, `{column_name}` as target_month
                FROM sales_performance
                WHERE `{column_name}` IS NOT NULL AND `{column_name}` > 0
                LIMIT 100
                """
                explanation = f"{name}의 {year}년 {int(month) if month else ''}월 실적 조회"

            elif team:
                # Team sales - aggregate by team
                sql = f"""
                SELECT SUM(`{column_name}`) as total_sales,
                       AVG(`{column_name}`) as avg_sales,
                       COUNT(*) as count
                FROM sales_performance
                WHERE `{column_name}` IS NOT NULL AND `{column_name}` > 0
                """
                explanation = f"{team}의 {year}년 {int(month) if month else ''}월 실적 조회"

            else:
                # All sales for the month - top performers
                sql = f"""
                SELECT *, `{column_name}` as sales_amount
                FROM sales_performance
                WHERE `{column_name}` IS NOT NULL AND `{column_name}` > 0
                ORDER BY `{column_name}` DESC
                LIMIT 10
                """
                explanation = f"{year}년 {int(month) if month else ''}월 상위 10명 실적 조회"

        elif action == "average":
            if team:
                sql = f"""
                SELECT `팀명칭`, AVG(`{column_name}`) as 평균매출액
                FROM sales_performance
                WHERE `팀명칭` = '{team}'
                GROUP BY `팀명칭`
                """
                explanation = f"{team}의 {year}년 {int(month)}월 평균 실적"
            else:
                sql = f"""
                SELECT AVG(`{column_name}`) as 전체평균매출액
                FROM sales_performance
                WHERE `{column_name}` IS NOT NULL AND `{column_name}` > 0
                """
                explanation = f"{year}년 {int(month)}월 전체 평균 실적"

        elif action == "sum":
            if team:
                sql = f"""
                SELECT `팀명칭`, SUM(`{column_name}`) as 총매출액
                FROM sales_performance
                WHERE `팀명칭` = '{team}'
                GROUP BY `팀명칭`
                """
                explanation = f"{team}의 {year}년 {int(month)}월 총 매출"
            else:
                sql = f"""
                SELECT SUM(`{column_name}`) as 전체매출액
                FROM sales_performance
                WHERE `{column_name}` IS NOT NULL AND `{column_name}` > 0
                """
                explanation = f"{year}년 {int(month)}월 전체 매출"

        else:
            # Default: simple query
            sql = f"""
            SELECT * FROM sales_performance LIMIT 5
            """
            explanation = "기본 조회 (상위 5건)"

        # Clean up SQL
        sql = " ".join(sql.split())

        logger.info(f"Generated SQL: {sql}")
        return sql, explanation

    def validate_sql(self, sql: str) -> bool:
        """
        Validate SQL for safety

        Args:
            sql: SQL query to validate

        Returns:
            True if safe, False otherwise
        """
        # Check for dangerous keywords
        dangerous_keywords = [
            "DROP", "DELETE", "UPDATE", "INSERT", "CREATE", "ALTER",
            "TRUNCATE", "EXEC", "EXECUTE", "--", "/*", "*/"
        ]

        sql_upper = sql.upper()
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                logger.warning(f"Dangerous SQL keyword detected: {keyword}")
                return False

        # Must be SELECT query
        if not sql_upper.strip().startswith("SELECT"):
            logger.warning("Only SELECT queries are allowed")
            return False

        return True