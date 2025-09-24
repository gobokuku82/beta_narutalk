"""
Schema Context Manager for LLM-based SQL Generation
Provides structured schema information for LLM to understand database structure
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SchemaContext:
    """Manages database schema context for LLM-based SQL generation"""

    def __init__(self):
        """Initialize schema context with database metadata"""
        self.base_path = Path("database")
        self.schemas_path = self.base_path / "schemas"

        # Load schema information
        self.table_descriptions = self._load_table_descriptions()
        self.relationships = self._load_relationships()

        # Available month columns (202212 ~ 202411)
        self.available_months = self._generate_month_columns()

        logger.info("SchemaContext initialized successfully")

    def _load_table_descriptions(self) -> Dict[str, Any]:
        """Load table descriptions from JSON file"""
        try:
            desc_file = self.schemas_path / "table_descriptions.json"
            if desc_file.exists():
                with open(desc_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"Table descriptions file not found: {desc_file}")
                return {}
        except Exception as e:
            logger.error(f"Error loading table descriptions: {e}")
            return {}

    def _load_relationships(self) -> Dict[str, Any]:
        """Load table relationships from JSON file"""
        try:
            rel_file = self.schemas_path / "relationships.json"
            if rel_file.exists():
                with open(rel_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"Relationships file not found: {rel_file}")
                return {}
        except Exception as e:
            logger.error(f"Error loading relationships: {e}")
            return {}

    def _generate_month_columns(self) -> List[str]:
        """Generate list of available month columns"""
        months = []
        # 2022년 12월부터 2024년 11월까지
        for year in [2022, 2023, 2024]:
            start_month = 12 if year == 2022 else 1
            end_month = 11 if year == 2024 else 12

            for month in range(start_month if year == 2022 else 1,
                              end_month + 1 if year == 2024 else 13):
                if year == 2022 and month < 12:
                    continue
                months.append(f"{year}{month:02d}")

        return months

    def get_llm_context(self, query_type: Optional[str] = None) -> str:
        """
        Get formatted schema context for LLM prompt

        Args:
            query_type: Optional query type to filter relevant schema info

        Returns:
            Formatted schema context string for LLM
        """
        context = []

        # Database overview
        context.append("=== 데이터베이스 구조 ===\n")
        context.append("사용 가능한 데이터베이스와 테이블:\n")

        # Sales Performance Database
        context.append("\n1. sales_performance_db.db:")
        context.append("   - sales_performance 테이블: 직원별 거래처별 품목별 월간 판매 실적")
        context.append("   주요 컬럼:")
        context.append("   - 사번, 담당자, 거래처ID, 품목")
        context.append(f"   - 월별 실적 컬럼: {', '.join(self.available_months[:5])} ... {self.available_months[-1]}")
        context.append("   - 각 월별 컬럼에는 해당 월의 매출액이 저장됨\n")

        # Sales Target Database
        context.append("2. sales_target_db.db:")
        context.append("   - 지점별목표 테이블: 지점별 월간 판매 목표")
        context.append("   주요 컬럼: 지점, 담당자, 월별 목표액 (202312~202411)\n")

        # Clients Database
        context.append("3. clients_db.db:")
        context.append("   - 거래처자료 테이블: 거래처별 월간 영업 실적")
        context.append("   주요 컬럼: 거래처ID, 월, 매출, 월방문횟수, 사용 예산, 총환자수, 담당자\n")

        # HR Database (if needed for joins)
        context.append("4. hr_data.db:")
        context.append("   - 인사자료 테이블: 직원 정보")
        context.append("   주요 컬럼: 사번, 성명, 본부, 직급, 부서, 지점, 기본급, 성과급\n")

        # Key relationships
        context.append("=== 주요 테이블 관계 ===")
        context.append("- 인사자료.사번 = sales_performance.사번")
        context.append("- sales_performance.거래처ID = 거래처자료.거래처ID")
        context.append("- 인사자료.지점 = 지점별목표.지점\n")

        # SQL generation guidelines
        context.append("=== SQL 생성 가이드라인 ===")
        context.append("1. 월별 데이터 조회 시 해당 월 컬럼을 직접 사용 (예: `202403`)")
        context.append("2. 컬럼명에 특수문자나 숫자로 시작하는 경우 백틱(`)으로 감싸기")
        context.append("3. 한글 컬럼명도 백틱(`)으로 감싸기")
        context.append("4. SQLite 문법 사용 (LIMIT, NOT NULL 등)")
        context.append("5. 집계 함수: SUM(), AVG(), COUNT(), MAX(), MIN()")
        context.append("6. NULL 값 처리: WHERE 절에서 IS NOT NULL 사용")

        return "\n".join(context)

    def get_table_columns(self, table_name: str, db_name: Optional[str] = None) -> List[str]:
        """
        Get column list for a specific table

        Args:
            table_name: Name of the table
            db_name: Optional database name

        Returns:
            List of column names
        """
        # Predefined column mappings based on our schema
        table_columns = {
            "sales_performance": ["사번", "담당자", "거래처ID", "품목"] + self.available_months,
            "지점별목표": ["지점", "담당자"] + [m for m in self.available_months if m >= "202312"],
            "거래처자료": ["거래처ID", "월", "매출", "월방문횟수", "사용 예산", "총환자수", "담당자"],
            "인사자료": ["사번", "성명", "본부", "직급", "부서", "지점", "연락처",
                      "월평균사용예산", "최근 평가", "기본급(₩)", "성과급(₩)", "책임업무"]
        }

        return table_columns.get(table_name, [])

    def validate_month_column(self, month: str) -> bool:
        """
        Validate if a month column exists

        Args:
            month: Month in YYYYMM format

        Returns:
            True if month column exists
        """
        return month in self.available_months

    def get_join_hints(self, tables: List[str]) -> List[Dict[str, str]]:
        """
        Get JOIN hints for given tables

        Args:
            tables: List of table names

        Returns:
            List of join hints
        """
        hints = []

        # Define common join patterns
        if "sales_performance" in tables and "인사자료" in tables:
            hints.append({
                "tables": ["sales_performance", "인사자료"],
                "condition": "sales_performance.사번 = 인사자료.사번",
                "type": "INNER JOIN"
            })

        if "sales_performance" in tables and "거래처자료" in tables:
            hints.append({
                "tables": ["sales_performance", "거래처자료"],
                "condition": "sales_performance.거래처ID = 거래처자료.거래처ID",
                "type": "LEFT JOIN"
            })

        if "인사자료" in tables and "지점별목표" in tables:
            hints.append({
                "tables": ["인사자료", "지점별목표"],
                "condition": "인사자료.지점 = 지점별목표.지점",
                "type": "LEFT JOIN"
            })

        return hints

    def get_example_queries(self) -> List[Dict[str, str]]:
        """
        Get example SQL queries for LLM reference

        Returns:
            List of example queries with descriptions
        """
        examples = [
            {
                "description": "특정 월 전체 실적 조회",
                "sql": "SELECT `담당자`, `202403` as sales FROM sales_performance WHERE `202403` IS NOT NULL ORDER BY `202403` DESC LIMIT 10"
            },
            {
                "description": "직원별 월간 실적 합계",
                "sql": "SELECT `담당자`, SUM(`202403`) as total_sales FROM sales_performance WHERE `202403` IS NOT NULL GROUP BY `담당자`"
            },
            {
                "description": "지점별 실적과 목표 비교",
                "sql": """
                SELECT sp.`지점`,
                       SUM(sp.`202403`) as actual_sales,
                       st.`202403` as target_sales,
                       ROUND(SUM(sp.`202403`) * 100.0 / st.`202403`, 2) as achievement_rate
                FROM sales_performance sp
                JOIN 지점별목표 st ON sp.`지점` = st.`지점`
                WHERE sp.`202403` IS NOT NULL
                GROUP BY sp.`지점`
                """
            },
            {
                "description": "월별 실적 추이 (시계열)",
                "sql": """
                SELECT `담당자`,
                       `202401`, `202402`, `202403`, `202404`
                FROM sales_performance
                WHERE `담당자` = '김철수'
                """
            },
            {
                "description": "전년 동월 대비 성장률",
                "sql": """
                SELECT `담당자`,
                       `202303` as last_year,
                       `202403` as this_year,
                       ROUND(((`202403` - `202303`) * 100.0 / `202303`), 2) as growth_rate
                FROM sales_performance
                WHERE `202303` IS NOT NULL AND `202403` IS NOT NULL
                ORDER BY growth_rate DESC
                """
            }
        ]

        return examples

    def format_for_prompt(self, user_query: str, intent: Optional[Dict] = None) -> str:
        """
        Format complete prompt for LLM SQL generation

        Args:
            user_query: Original user query
            intent: Optional intent analysis result

        Returns:
            Formatted prompt for LLM
        """
        prompt_parts = []

        # System context
        prompt_parts.append("당신은 SQLite 데이터베이스 전문가입니다.")
        prompt_parts.append("주어진 스키마 정보를 바탕으로 정확한 SQL 쿼리를 생성하세요.\n")

        # Schema context
        prompt_parts.append(self.get_llm_context())
        prompt_parts.append("")

        # Example queries
        prompt_parts.append("=== 참고 예시 SQL ===")
        for example in self.get_example_queries()[:3]:  # Show top 3 examples
            prompt_parts.append(f"// {example['description']}")
            prompt_parts.append(example['sql'])
            prompt_parts.append("")

        # User query
        prompt_parts.append("=== 사용자 요청 ===")
        prompt_parts.append(f"요청: {user_query}")

        # Intent information if available
        if intent:
            if intent.get("entities"):
                prompt_parts.append(f"추출된 정보: {intent['entities']}")

        prompt_parts.append("")
        prompt_parts.append("=== SQL 쿼리 생성 ===")
        prompt_parts.append("위 요청에 대한 SQL 쿼리를 생성하세요.")
        prompt_parts.append("주의사항:")
        prompt_parts.append("1. 실제 존재하는 테이블과 컬럼만 사용")
        prompt_parts.append("2. 월별 컬럼은 백틱(`)으로 감싸기")
        prompt_parts.append("3. 한글 컬럼명도 백틱(`)으로 감싸기")
        prompt_parts.append("4. SQLite 문법 준수")
        prompt_parts.append("5. 안전한 쿼리 (SELECT만 사용)")

        return "\n".join(prompt_parts)