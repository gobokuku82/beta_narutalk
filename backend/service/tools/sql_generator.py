"""
SQL Generator Tool - FIXED VERSION
Enhanced with LLM-based SQL generation for complex queries
주요 수정: parse_query 메서드에서 시간 표현을 먼저 처리하여 "지난달"을 이름으로 인식하는 문제 해결
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

        # Table name mapping (English -> Korean)
        self.table_mapping = {
            'sales_performance': 'sales_performance',  # Already matches
            'sales_target': '지점별목표',
            'sales_target_db': '지점별목표',  # Alias
            'clients': '거래처자료',
            'clients_db': '거래처자료',  # Alias
            'hr_data': '인사자료',
            'hr_info': '인사자료',  # Alias
        }

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
        
        # Time-related words to skip during name extraction
        self.time_words = ["지난달", "이번달", "작년", "올해", "내년", "전월", "당월", "지난", "이번", "다음"]

        # Keywords that shouldn't be treated as names
        self.skip_words = ["실적", "매출", "판매", "목표", "달성", "평균", "합계", "순위", "현황", "분석", "조회", "데이터"]

        # Valid employees list (from actual database - only 6 employees have sales data)
        self.valid_employees = [
            '윤수아', '윤하은', '정예준', '조시현', '조하은', '최수아'
        ]

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

    def validate_query_entities(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate entities in the query (employees, dates, etc.)

        Args:
            parsed: Parsed query components

        Returns:
            Validation result with warnings
        """
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'suggestions': []
        }

        # Check if parsed name is a valid employee
        if parsed.get('person_name'):
            clean_name = parsed['person_name']
            if clean_name not in self.valid_employees:
                validation_result['warnings'].append(
                    f"'{clean_name}'님의 데이터를 찾을 수 없습니다."
                )
                validation_result['suggestions'].append(
                    f"등록된 직원: {', '.join(self.valid_employees)}"
                )
                validation_result['is_valid'] = False

        # Check for multiple names
        if parsed.get('names'):
            invalid_names = []
            for name in parsed['names']:
                if name not in self.valid_employees:
                    invalid_names.append(name)

            if invalid_names:
                validation_result['warnings'].append(
                    f"다음 직원의 데이터를 찾을 수 없습니다: {', '.join(invalid_names)}"
                )
                validation_result['is_valid'] = False

        # Check if requested date is within available range
        if parsed.get('year') and parsed.get('month'):
            month_col = f"{parsed['year']}{parsed['month']}"
            if month_col not in self.available_columns:
                validation_result['warnings'].append(
                    f"{parsed['year']}년 {int(parsed['month'])}월 데이터는 없습니다. (가용 기간: 2022년 12월 ~ 2024년 11월)"
                )
                validation_result['is_valid'] = False
        elif parsed.get('year') and parsed['year'] > 2024:
            validation_result['warnings'].append(
                f"{parsed['year']}년 데이터는 없습니다. (가용 기간: 2022년 12월 ~ 2024년 11월)"
            )
            validation_result['is_valid'] = False

        return validation_result

    def parse_query(self, query: str) -> Dict[str, Any]:
        """
        Parse Korean query into structured components (FIXED VERSION)
        시간 표현을 먼저 처리하여 "지난달"을 이름으로 오인식하는 문제 해결

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
            "person_name": None,  # Clean name without particles
            "comparison_type": None
        }
        
        current_date = datetime.now()

        # STEP 1: Check for relative time expressions FIRST (before name extraction)
        if "이번달" in query or "이번 달" in query:
            parsed["month"] = f"{self.current_month:02d}"
            parsed["year"] = self.current_year
        elif "지난달" in query or "지난 달" in query or "전월" in query:
            last_month = current_date - timedelta(days=30)
            parsed["month"] = f"{last_month.month:02d}"
            parsed["year"] = last_month.year
        elif "작년" in query:
            parsed["year"] = self.current_year - 1
            
        # STEP 2: Extract specific month references
        for month_kr, month_num in self.month_map.items():
            if month_kr in query:
                parsed["month"] = month_num
                break

        # STEP 3: Extract year if mentioned
        year_pattern = r'(\d{4})년'
        year_match = re.search(year_pattern, query)
        if year_match:
            parsed["year"] = int(year_match.group(1))
        elif parsed["month"] and not parsed["year"]:
            # Default to current year if month is specified but year is not
            parsed["year"] = self.current_year

        # STEP 4: Handle comparisons (대비)
        if "대비" in query:
            parsed["action"] = "compare"
            if "지난달" in query and ("이번달" in query or "이번 달" in query):
                parsed["comparison_type"] = "mom"  # Month-over-Month
            elif "작년" in query:
                parsed["comparison_type"] = "yoy"  # Year-over-Year

        # STEP 5: Extract names (AFTER handling time expressions)
        # Pattern for Korean names (2-4 characters) with optional titles/particles
        # Updated to better capture names with particles
        name_pattern = r'([가-힣]{2,4})(?:의|씨|님|대리|과장|부장|차장|팀장)?'

        # Also check for names with possessive particle '의'
        possessive_pattern = r'([가-힣]{2,4})의'
        possessive_match = re.search(possessive_pattern, query)
        if possessive_match:
            potential_name = possessive_match.group(1)
            if (potential_name not in self.time_words and
                potential_name not in self.month_map and
                potential_name not in self.skip_words):
                parsed["name"] = potential_name
                parsed["person_name"] = potential_name
                # Skip the general pattern matching below
                name_pattern = None

        # Check for multiple names (와, 과, 및, 그리고, comma)
        if name_pattern and any(separator in query for separator in ["와", "과", ",", "및", "그리고"]):
            names = []
            # Split by various separators
            parts = query
            for sep in ["와", "과", ",", "및", "그리고"]:
                parts = parts.replace(sep, "|")

            for part in parts.split("|"):
                part = part.strip()
                # Find potential names in each part
                matches = re.findall(name_pattern, part)
                for match in matches:
                    # Skip time-related words and month names
                    if match not in self.time_words and match not in self.month_map and "달" not in match:
                        clean_name = match.rstrip('의').rstrip('씨').rstrip('님')
                        if clean_name and clean_name not in names:
                            names.append(clean_name)

            if len(names) > 1:
                parsed["names"] = names
                parsed["name"] = names[0]
                parsed["person_name"] = names[0]
        elif name_pattern and not parsed.get("name"):
            # Single name extraction (only if not already found with possessive particle)
            matches = re.findall(name_pattern, query)
            for match in matches:
                # Skip time-related words, month names, and keywords
                if (match not in self.time_words and
                    match not in self.month_map and
                    match not in self.skip_words and
                    "달" not in match):
                    clean_name = match.rstrip('의').rstrip('씨').rstrip('님')
                    parsed["name"] = match  # Keep original for backward compatibility
                    parsed["person_name"] = clean_name  # Clean version
                    break

        # STEP 6: Extract team
        team_pattern = r'([가-힣]+팀|[가-힣]+부서|[가-힣]+부)'
        team_match = re.search(team_pattern, query)
        if team_match:
            parsed["team"] = team_match.group(1)

        # STEP 7: Determine action type (if not already set)
        if not parsed["action"]:
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
            elif "순위" in query or "TOP" in query.upper() or "랭킹" in query:
                parsed["action"] = "ranking"
            elif "추이" in query or "트렌드" in query:
                parsed["action"] = "trend"
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
            if parsed.get("names"):
                # Multiple names to query
                names_str = ", ".join(f"'{name}'" for name in parsed["names"])
                prompt += f"\n특정 직원 조회: {', '.join(parsed['names'])} (WHERE 담당자 IN ({names_str}))"
            elif parsed.get("name"):
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

            # Map table names to Korean
            sql = self._map_table_names(sql)

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

    def _map_table_names(self, sql: str) -> str:
        """Map English table names to Korean table names in SQL"""
        # Replace table names in SQL
        for eng_name, kor_name in self.table_mapping.items():
            # Replace table names with word boundaries to avoid partial replacements
            # Handle both direct references and JOIN clauses
            sql = re.sub(rf'\b{eng_name}\b', kor_name, sql, flags=re.IGNORECASE)

        return sql

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
        FIXED: Better handling of None values in month/year

        Args:
            parsed: Parsed query components

        Returns:
            Tuple of (SQL query, explanation)
        """
        # First validate the query entities
        validation = self.validate_query_entities(parsed)

        # If validation fails, return special SQL with validation message
        if not validation['is_valid']:
            error_msg = ' '.join(validation['warnings'])
            if validation['suggestions']:
                error_msg += ' ' + ' '.join(validation['suggestions'])

            # Return a SQL that will produce empty results
            sql = f"SELECT '' as result WHERE 1=0"
            explanation = error_msg
            return sql, explanation

        names = parsed.get("names")  # Multiple names
        name = parsed.get("name") if not names else None  # Single name
        month = parsed.get("month")
        year = parsed.get("year", self.current_year)
        team = parsed.get("team")
        action = parsed.get("action", "sales")

        # Construct column name for month with better None handling
        if month and year:
            column_name = f"{year}{month}"
        elif month and not year:
            column_name = f"{self.current_year}{month}"
        elif not month and year:
            # Use last available month for that year
            if year == 2024:
                column_name = "202411"  # November 2024 is the last available
            elif year == 2023:
                column_name = "202312"
            else:
                column_name = f"{year}12"
        else:
            # Default to last available month (202411)
            column_name = "202411"

        # Validate column exists in database
        if column_name not in self.available_columns:
            # Fall back to the most recent available month
            if self.available_columns:
                column_name = self.available_columns[-1]  # Use last available month (202411)
                logger.warning(f"Requested column {column_name} not available, using {self.available_columns[-1]}")

        # Build SQL based on action and filters
        if action == "sales":
            if names:
                # Multiple individuals - compare their sales
                names_str = ", ".join(f"'{n}'" for n in names)
                sql = f"""
                SELECT `담당자`, `{column_name}` as sales_amount
                FROM sales_performance
                WHERE `담당자` IN ({names_str})
                  AND `{column_name}` IS NOT NULL
                  AND `{column_name}` > 0
                ORDER BY `{column_name}` DESC
                """
                explanation = f"{', '.join(names)}의 {year}년 {int(month) if month else ''}월 실적 비교"
            elif name:
                # Individual sales
                sql = f"""
                SELECT *, `{column_name}` as target_month
                FROM sales_performance
                WHERE `담당자` = '{name}'
                  AND `{column_name}` IS NOT NULL
                  AND `{column_name}` > 0
                LIMIT 100
                """
                explanation = f"{name}의 {year}년 {int(month) if month else ''}월 실적 조회"
            elif team:
                # Team sales
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
                SELECT `담당자`, `{column_name}` as sales_amount
                FROM sales_performance
                WHERE `{column_name}` IS NOT NULL AND `{column_name}` > 0
                ORDER BY `{column_name}` DESC
                LIMIT 10
                """
                explanation = f"{year}년 {int(month) if month else ''}월 상위 10명 실적 조회"

        elif action == "compare":
            # Month-over-month or year-over-year comparison
            if parsed.get("comparison_type") == "mom":
                # Get previous month
                if column_name in self.available_columns:
                    idx = self.available_columns.index(column_name)
                    if idx > 0:
                        prev_column = self.available_columns[idx - 1]
                        sql = f"""
                        SELECT `담당자`,
                               `{prev_column}` as last_month,
                               `{column_name}` as this_month,
                               (`{column_name}` - `{prev_column}`) as difference,
                               ROUND(((`{column_name}` - `{prev_column}`) * 100.0 / `{prev_column}`), 2) as growth_rate
                        FROM sales_performance
                        WHERE `{prev_column}` IS NOT NULL AND `{column_name}` IS NOT NULL
                        ORDER BY growth_rate DESC
                        LIMIT 20
                        """
                        explanation = "지난달 대비 이번달 실적 비교"
                    else:
                        sql = f"SELECT * FROM sales_performance WHERE `{column_name}` IS NOT NULL LIMIT 10"
                        explanation = "비교할 이전 데이터가 없습니다"
                else:
                    sql = f"SELECT * FROM sales_performance LIMIT 10"
                    explanation = "기본 조회"
            else:
                sql = f"SELECT * FROM sales_performance WHERE `{column_name}` IS NOT NULL LIMIT 10"
                explanation = f"{year}년 {int(month) if month else ''}월 실적 조회"

        elif action == "ranking":
            # Top N ranking
            sql = f"""
            SELECT 
                ROW_NUMBER() OVER (ORDER BY `{column_name}` DESC) as ranking,
                `담당자`,
                `{column_name}` as sales_amount
            FROM sales_performance
            WHERE `{column_name}` IS NOT NULL AND `{column_name}` > 0
            ORDER BY ranking
            LIMIT 10
            """
            explanation = f"{year}년 {int(month) if month else ''}월 TOP 10 순위"

        else:
            # Default: simple query
            sql = f"SELECT * FROM sales_performance WHERE `{column_name}` IS NOT NULL LIMIT 5"
            explanation = "기본 조회"

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

        # Check for system tables access
        system_tables = ["SQLITE_MASTER", "SQLITE_SEQUENCE", "SQLITE_STAT"]
        for table in system_tables:
            if table in sql_upper:
                logger.warning(f"Access to system table {table} not allowed")
                return False

        logger.debug("SQL validation passed")
        return True

    # ... (나머지 advanced SQL generation 메서드들은 그대로 유지)
