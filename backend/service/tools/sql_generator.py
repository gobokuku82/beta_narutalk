"""
SQL Generator Tool
Enhanced with LLM-based SQL generation for complex queries
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, timedelta
import json
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from .schema_context import SchemaContext

logger = logging.getLogger(__name__)


class SQLGenerator:
    """Generate SQL queries from natural language using LLM and rule-based hybrid approach"""

    def __init__(self):
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month

        # Initialize schema context
        self.schema_context = SchemaContext()

        # Available columns from schema context
        self.available_columns = self.schema_context.available_months

        # Initialize LLM client for SQL generation
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.1,  # Low temperature for deterministic SQL
                api_key=api_key,
                max_retries=2
            )
            self.use_llm = True
            logger.info("LLM initialized for SQL generation")
        else:
            self.llm = None
            self.use_llm = False
            logger.warning("No OpenAI API key found, falling back to rule-based SQL generation")

        # Month mapping for rule-based fallback
        self.month_map = {
            "1월": "01", "2월": "02", "3월": "03", "4월": "04",
            "5월": "05", "6월": "06", "7월": "07", "8월": "08",
            "9월": "09", "10월": "10", "11월": "11", "12월": "12",
            "일월": "01", "이월": "02", "삼월": "03", "사월": "04",
            "오월": "05", "유월": "06", "칠월": "07", "팔월": "08",
            "구월": "09", "시월": "10", "십일월": "11", "십이월": "12"
        }

    async def extract_entities_with_llm(self, query: str) -> Dict[str, Any]:
        """
        Extract entities from query using LLM for better accuracy

        Args:
            query: Natural language query in Korean

        Returns:
            Extracted entities dictionary
        """
        if not self.use_llm:
            return self.parse_query(query)

        try:
            prompt = f"""
한국어 쿼리에서 엔티티를 정확하게 추출하세요.

쿼리: {query}

다음 형식으로 JSON 반환:
{{
    "person_name": "조사를 제외한 순수 이름 (없으면 null)",
    "month": "월 (01-12 형식, 없으면 null)",
    "year": "연도 (4자리, 없으면 null)",
    "team": "팀명 (없으면 null)",
    "time_expression": "시간 표현 (이번달, 작년, 어제 등, 없으면 null)",
    "action_type": "조회 의도 (sales, average, ranking 등)"
}}

예시:
- "김철수의 실적" → {{"person_name": "김철수", "action_type": "sales"}}
- "이영희씨 3월 매출" → {{"person_name": "이영희", "month": "03", "action_type": "sales"}}
- "박 대리님의 성과" → {{"person_name": "박", "action_type": "sales"}}
"""

            messages = [
                SystemMessage(content="당신은 한국어 엔티티 추출 전문가입니다."),
                HumanMessage(content=prompt)
            ]

            response = await self.llm.ainvoke(messages)
            entities = json.loads(response.content)

            # Add original query
            entities["original_query"] = query

            logger.info(f"LLM extracted entities: {entities}")
            return entities

        except Exception as e:
            logger.warning(f"LLM entity extraction failed, falling back to rule-based: {e}")
            return self.parse_query(query)

    def parse_query(self, query: str) -> Dict[str, Any]:
        """
        Parse Korean query into structured components (rule-based fallback)

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
            "period_type": None,
            "person_name": None  # Clean name without particles
        }

        # Extract name (assuming Korean names are 2-4 characters)
        name_pattern = r'([가-힣]{2,4})(?:의|씨|님|대리|과장|부장|차장|팀장)?(?:\s|$)'
        name_match = re.search(name_pattern, query)
        if name_match:
            potential_name = name_match.group(1)
            # Check if it's not a month name or other keyword
            if potential_name not in self.month_map and "월" not in potential_name:
                # Clean name - remove particles
                clean_name = potential_name.rstrip('의').rstrip('씨').rstrip('님')
                parsed["name"] = potential_name  # Keep original for backward compatibility
                parsed["person_name"] = clean_name  # Clean version for queries

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

    async def generate_sql_with_llm(
        self,
        query: str,
        parsed: Dict[str, Any],
        intent: Optional[Dict] = None
    ) -> Tuple[str, str]:
        """
        Generate SQL using LLM based on natural language query

        Args:
            query: Original user query
            parsed: Parsed query components
            intent: Optional intent analysis result

        Returns:
            Tuple of (SQL query, explanation)
        """
        try:
            # Build comprehensive prompt with schema context
            prompt = self.schema_context.format_for_prompt(query, intent)

            # Add specific requirements based on parsed components
            if parsed.get("name"):
                prompt += f"\n특정 직원 조회: {parsed['name']}"
            if parsed.get("month") and parsed.get("year"):
                month_col = f"{parsed['year']}{parsed['month']}"
                prompt += f"\n조회 기간: {month_col} 컬럼 사용"

            # Call LLM for SQL generation
            messages = [
                SystemMessage(content="당신은 SQLite SQL 전문가입니다. 안전하고 정확한 SELECT 쿼리만 생성하세요."),
                HumanMessage(content=prompt)
            ]

            response = await self.llm.ainvoke(messages)
            sql_content = response.content

            # Extract SQL from response
            sql = self._extract_sql_from_response(sql_content)

            # Validate generated SQL
            if not self.validate_sql(sql):
                logger.warning("LLM generated unsafe SQL, falling back to rule-based")
                return self.generate_sql(parsed)

            # Generate explanation
            explanation = self._generate_explanation(query, parsed, sql)

            logger.info(f"LLM generated SQL: {sql}")
            return sql, explanation

        except Exception as e:
            logger.error(f"LLM SQL generation failed: {e}, falling back to rule-based")
            return self.generate_sql(parsed)

    def _extract_sql_from_response(self, response: str) -> str:
        """Extract SQL query from LLM response"""
        # Look for SQL in code blocks
        if "```sql" in response.lower():
            start = response.lower().find("```sql") + 6
            end = response.find("```", start)
            if end > start:
                return response[start:end].strip()

        # Look for SELECT statement
        lines = response.split('\n')
        sql_lines = []
        in_sql = False

        for line in lines:
            if line.strip().upper().startswith("SELECT"):
                in_sql = True
            if in_sql:
                sql_lines.append(line)
                if ";" in line:
                    break

        if sql_lines:
            return " ".join(sql_lines).strip()

        # If no clear SQL found, return the whole response (might be SQL)
        return response.strip()

    def _generate_explanation(self, query: str, parsed: Dict[str, Any], sql: str) -> str:
        """Generate Korean explanation for the SQL query"""
        explanation_parts = []

        # Basic explanation based on parsed components
        if parsed.get("name"):
            explanation_parts.append(f"{parsed['name']}님의")

        if parsed.get("year") and parsed.get("month"):
            explanation_parts.append(f"{parsed['year']}년 {int(parsed['month'])}월")
        elif parsed.get("month"):
            explanation_parts.append(f"{int(parsed['month'])}월")

        # Analyze SQL for more details
        sql_upper = sql.upper()
        if "SUM(" in sql_upper:
            explanation_parts.append("합계")
        elif "AVG(" in sql_upper:
            explanation_parts.append("평균")
        elif "COUNT(" in sql_upper:
            explanation_parts.append("건수")
        else:
            explanation_parts.append("실적")

        if "GROUP BY" in sql_upper:
            explanation_parts.append("집계")
        if "ORDER BY" in sql_upper:
            if "DESC" in sql_upper:
                explanation_parts.append("(내림차순 정렬)")
            else:
                explanation_parts.append("(오름차순 정렬)")

        explanation_parts.append("조회")

        return " ".join(explanation_parts)

    def generate_sql(self, parsed: Dict[str, Any]) -> Tuple[str, str]:
        """
        Generate SQL from parsed query components (rule-based fallback)

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
        Validate SQL for safety with enhanced checks

        Args:
            sql: SQL query to validate

        Returns:
            True if safe, False otherwise
        """
        if not sql:
            logger.warning("Empty SQL query")
            return False

        sql_upper = sql.upper().strip()

        # Must be SELECT query
        if not sql_upper.startswith("SELECT"):
            logger.warning("Only SELECT queries are allowed")
            return False

        # Check for dangerous keywords
        dangerous_keywords = [
            "DROP", "DELETE", "UPDATE", "INSERT", "CREATE", "ALTER",
            "TRUNCATE", "EXEC", "EXECUTE", "ATTACH", "DETACH"
        ]

        for keyword in dangerous_keywords:
            if re.search(r'\b' + keyword + r'\b', sql_upper):
                logger.warning(f"Dangerous SQL keyword detected: {keyword}")
                return False

        # Check for SQL injection patterns
        injection_patterns = [
            r";\s*DROP",  # Statement termination followed by DROP
            r";\s*DELETE",  # Statement termination followed by DELETE
            r"--\s*$",  # SQL comment at end
            r"/\*.*\*/",  # Block comments
            r"UNION\s+ALL\s+SELECT",  # UNION injection
            r"OR\s+1\s*=\s*1",  # Classic injection
            r"OR\s+'[^']*'\s*=\s*'[^']*'"  # String comparison injection
        ]

        for pattern in injection_patterns:
            if re.search(pattern, sql_upper):
                logger.warning(f"Potential SQL injection pattern detected: {pattern}")
                return False

        # Additional safety checks
        # Limit number of statements (should be single SELECT)
        if sql.count(';') > 1:
            logger.warning("Multiple SQL statements not allowed")
            return False

        # Check for system tables access
        system_tables = ["SQLITE_MASTER", "SQLITE_SEQUENCE", "SQLITE_STAT"]
        for table in system_tables:
            if table in sql_upper:
                logger.warning(f"Access to system table {table} not allowed")
                return False

        logger.debug("SQL validation passed")
        return True

    async def generate_advanced_sql(
        self,
        query: str,
        query_type: str,
        entities: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        Generate advanced SQL queries with complex features

        Args:
            query: Original user query
            query_type: Type of query (trend, comparison, ranking, etc.)
            entities: Extracted entities from query

        Returns:
            Tuple of (SQL query, explanation)
        """
        sql = ""
        explanation = ""

        if query_type == "trend":
            # Time series trend analysis
            sql = self._generate_trend_sql(entities)
            explanation = "시계열 추이 분석"

        elif query_type == "comparison":
            # YoY or MoM comparison
            sql = self._generate_comparison_sql(entities)
            explanation = "기간 비교 분석"

        elif query_type == "ranking":
            # Top N ranking with window functions
            sql = self._generate_ranking_sql(entities)
            explanation = "순위 분석"

        elif query_type == "aggregation":
            # Multi-level aggregation
            sql = self._generate_aggregation_sql(entities)
            explanation = "다차원 집계 분석"

        else:
            # Default to LLM generation for complex queries
            return await self.generate_sql_with_llm(query, entities)

        return sql, explanation

    def _generate_trend_sql(self, entities: Dict[str, Any]) -> str:
        """Generate SQL for trend analysis"""
        name = entities.get("name", "")
        start_month = entities.get("start_month", "202401")
        end_month = entities.get("end_month", "202411")

        # Get months in range
        months_in_range = [m for m in self.available_columns if start_month <= m <= end_month]

        if name:
            # Individual trend
            columns = ", ".join([f"`{m}`" for m in months_in_range])
            sql = f"""
            SELECT `담당자`, {columns}
            FROM sales_performance
            WHERE `담당자` = '{name}'
            """
        else:
            # Overall trend
            sums = ", ".join([f"SUM(`{m}`) as `{m}`" for m in months_in_range])
            sql = f"""
            SELECT 'Total' as category, {sums}
            FROM sales_performance
            WHERE {" OR ".join([f"`{m}` IS NOT NULL" for m in months_in_range])}
            """

        return sql.strip()

    def _generate_comparison_sql(self, entities: Dict[str, Any]) -> str:
        """Generate SQL for period comparison (YoY, MoM)"""
        comparison_type = entities.get("comparison_type", "yoy")
        current_period = entities.get("current_period", "202403")

        if comparison_type == "yoy":
            # Year-over-year comparison
            current_year = int(current_period[:4])
            month = current_period[4:]
            previous_period = f"{current_year - 1}{month}"

            sql = f"""
            SELECT
                `담당자`,
                `{previous_period}` as last_year,
                `{current_period}` as this_year,
                `{current_period}` - `{previous_period}` as difference,
                ROUND(((`{current_period}` - `{previous_period}`) * 100.0 / `{previous_period}`), 2) as growth_rate
            FROM sales_performance
            WHERE `{previous_period}` IS NOT NULL AND `{current_period}` IS NOT NULL
            ORDER BY growth_rate DESC
            LIMIT 20
            """
        else:
            # Month-over-month comparison
            # Find previous month column
            current_idx = self.available_columns.index(current_period)
            if current_idx > 0:
                previous_period = self.available_columns[current_idx - 1]
                sql = f"""
                SELECT
                    `담당자`,
                    `{previous_period}` as last_month,
                    `{current_period}` as this_month,
                    `{current_period}` - `{previous_period}` as difference,
                    ROUND(((`{current_period}` - `{previous_period}`) * 100.0 / `{previous_period}`), 2) as growth_rate
                FROM sales_performance
                WHERE `{previous_period}` IS NOT NULL AND `{current_period}` IS NOT NULL
                ORDER BY growth_rate DESC
                LIMIT 20
                """
            else:
                sql = f"SELECT * FROM sales_performance WHERE `{current_period}` IS NOT NULL LIMIT 10"

        return sql.strip()

    def _generate_ranking_sql(self, entities: Dict[str, Any]) -> str:
        """Generate SQL for ranking queries"""
        month = entities.get("month", "202411")
        category = entities.get("category", "individual")  # individual, team, product

        if category == "team":
            # Team ranking
            sql = f"""
            WITH team_sales AS (
                SELECT
                    `팀명칭`,
                    SUM(`{month}`) as total_sales,
                    COUNT(*) as member_count,
                    AVG(`{month}`) as avg_sales
                FROM sales_performance
                WHERE `{month}` IS NOT NULL
                GROUP BY `팀명칭`
            )
            SELECT
                ROW_NUMBER() OVER (ORDER BY total_sales DESC) as ranking,
                `팀명칭`,
                total_sales,
                member_count,
                ROUND(avg_sales, 0) as avg_sales
            FROM team_sales
            ORDER BY ranking
            """
        else:
            # Individual ranking
            sql = f"""
            SELECT
                ROW_NUMBER() OVER (ORDER BY `{month}` DESC) as ranking,
                `담당자`,
                `{month}` as sales_amount
            FROM sales_performance
            WHERE `{month}` IS NOT NULL AND `{month}` > 0
            ORDER BY ranking
            LIMIT 30
            """

        return sql.strip()

    def _generate_aggregation_sql(self, entities: Dict[str, Any]) -> str:
        """Generate SQL for multi-level aggregation"""
        month = entities.get("month", "202411")
        group_by = entities.get("group_by", ["팀명칭"])

        if isinstance(group_by, str):
            group_by = [group_by]

        group_columns = ", ".join([f"`{col}`" for col in group_by])

        sql = f"""
        SELECT
            {group_columns},
            COUNT(*) as count,
            SUM(`{month}`) as total_sales,
            AVG(`{month}`) as avg_sales,
            MAX(`{month}`) as max_sales,
            MIN(`{month}`) as min_sales
        FROM sales_performance
        WHERE `{month}` IS NOT NULL
        GROUP BY {group_columns}
        ORDER BY total_sales DESC
        """

        return sql.strip()