"""
Korean SQL Column Name Processing Utilities
한글 컬럼명 및 SQL 처리 유틸리티 (중앙 집중화)
LangGraph 0.6.x 최적화
"""

import re
from typing import Set, List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class KoreanSQLProcessor:
    """
    한글 SQL 처리 유틸리티
    - 한글 컬럼명 자동 인용 처리
    - 월별 컬럼 자동 처리
    - SQL 쿼리 정규화
    """

    # 한글 컬럼명 집합 (모든 데이터베이스 통합)
    KOREAN_COLUMNS: Set[str] = {
        # HR 데이터베이스 컬럼
        "사번", "성명", "본부", "직급", "부서", "지점", "연락처",
        "월평균사용예산", "최근 평가", "기본급(₩)", "성과급(₩)", "책임업무",

        # 지점 연락처 관련
        "지점 연락처", "담당자", "지점연락처", "지점별목표",

        # 거래처 및 매출 관련
        "거래처ID", "품목", "거래처자료", "거래처정보",
        "월방문횟수", "사용 예산", "총환자수", "월", "매출",

        # 병원 관련
        "원장명", "지역구", "병원연락처",

        # 기타
        "인사자료"
    }

    # 테이블명 집합
    KOREAN_TABLES: Set[str] = {
        "인사자료", "지점연락처", "거래처정보", "지점별목표"
    }

    # 월별 컬럼 패턴 (고정 범위: 202312 ~ 202411)
    MONTHLY_COLUMNS: List[str] = (
        ["202312"] + [f"2024{month:02d}" for month in range(1, 12)]
    )

    # SQL 키워드 (대소문자 변환용)
    SQL_KEYWORDS: Set[str] = {
        "SELECT", "FROM", "WHERE", "JOIN", "LEFT", "RIGHT", "INNER", "OUTER",
        "ON", "AS", "AND", "OR", "NOT", "IN", "EXISTS", "LIKE", "BETWEEN",
        "GROUP", "BY", "HAVING", "ORDER", "ASC", "DESC", "LIMIT", "OFFSET",
        "INSERT", "INTO", "VALUES", "UPDATE", "SET", "DELETE", "CREATE",
        "DROP", "ALTER", "TABLE", "INDEX", "VIEW", "DISTINCT", "COUNT",
        "SUM", "AVG", "MAX", "MIN", "CASE", "WHEN", "THEN", "ELSE", "END"
    }

    @classmethod
    def auto_quote_sql(cls, sql: str) -> str:
        """
        SQL 쿼리에서 한글 컬럼명과 테이블명을 자동으로 인용 처리

        Args:
            sql: 원본 SQL 쿼리

        Returns:
            처리된 SQL 쿼리
        """
        processed = sql

        # 1. 한글 컬럼명 처리
        for column in cls.KOREAN_COLUMNS:
            processed = cls._quote_identifier(processed, column)

        # 2. 한글 테이블명 처리
        for table in cls.KOREAN_TABLES:
            processed = cls._quote_identifier(processed, table)

        # 3. 월별 컬럼 처리
        for month in cls.MONTHLY_COLUMNS:
            processed = cls._quote_month_column(processed, month)

        # 4. SQL 키워드 대문자 변환 (선택적)
        processed = cls._normalize_sql_keywords(processed)

        return processed

    @classmethod
    def _quote_identifier(cls, sql: str, identifier: str) -> str:
        """
        식별자(컬럼/테이블)를 큰따옴표로 감싸기

        Args:
            sql: SQL 쿼리
            identifier: 처리할 식별자

        Returns:
            처리된 SQL
        """
        # 이미 따옴표가 있는지 확인
        if f'"{identifier}"' in sql or f"'{identifier}'" in sql or f"`{identifier}`" in sql:
            return sql

        # 정규표현식으로 단어 경계 확인하여 정확한 매칭
        # (?<!["\w]) : 앞에 따옴표나 문자가 없어야 함
        # (?!["\w]) : 뒤에 따옴표나 문자가 없어야 함
        pattern = r'(?<!["\w])' + re.escape(identifier) + r'(?!["\w])'
        replacement = f'"{identifier}"'

        return re.sub(pattern, replacement, sql)

    @classmethod
    def _quote_month_column(cls, sql: str, month: str) -> str:
        """
        월별 컬럼명을 큰따옴표로 감싸기

        Args:
            sql: SQL 쿼리
            month: 월별 컬럼 (예: 202312, 202401)

        Returns:
            처리된 SQL
        """
        # 이미 따옴표가 있는지 확인
        if f'"{month}"' in sql or f"'{month}'" in sql:
            return sql

        # 숫자로만 이루어진 컬럼명 처리
        # SELECT 202401 → SELECT "202401"
        pattern = r'\b' + month + r'\b'
        replacement = f'"{month}"'

        return re.sub(pattern, replacement, sql)

    @classmethod
    def _normalize_sql_keywords(cls, sql: str) -> str:
        """
        SQL 키워드를 대문자로 변환 (선택적)

        Args:
            sql: SQL 쿼리

        Returns:
            정규화된 SQL
        """
        # 문자열 리터럴 보호 (따옴표 안의 내용은 변경하지 않음)
        protected_parts = []
        pattern = r'(["\'])(?:(?=(\\?))\2.)*?\1'

        # 문자열 리터럴 임시 저장
        def protect_string(match):
            protected_parts.append(match.group(0))
            return f"__PROTECTED_{len(protected_parts) - 1}__"

        protected_sql = re.sub(pattern, protect_string, sql)

        # SQL 키워드 대문자 변환
        for keyword in cls.SQL_KEYWORDS:
            pattern = r'\b' + keyword + r'\b'
            protected_sql = re.sub(pattern, keyword, protected_sql, flags=re.IGNORECASE)

        # 보호된 문자열 복원
        for i, protected in enumerate(protected_parts):
            protected_sql = protected_sql.replace(f"__PROTECTED_{i}__", protected)

        return protected_sql

    @classmethod
    def validate_korean_columns(cls, columns: List[str]) -> Dict[str, bool]:
        """
        컬럼 목록이 한글 컬럼인지 확인

        Args:
            columns: 확인할 컬럼 목록

        Returns:
            각 컬럼의 한글 여부
        """
        result = {}
        for column in columns:
            # 따옴표 제거
            clean_column = column.strip('"').strip("'").strip("`")
            result[column] = clean_column in cls.KOREAN_COLUMNS

        return result

    @classmethod
    def extract_columns_from_sql(cls, sql: str) -> List[str]:
        """
        SQL 쿼리에서 컬럼명 추출

        Args:
            sql: SQL 쿼리

        Returns:
            추출된 컬럼 목록
        """
        columns = []

        # SELECT 절에서 컬럼 추출
        select_pattern = r'SELECT\s+(.*?)\s+FROM'
        select_match = re.search(select_pattern, sql, re.IGNORECASE | re.DOTALL)

        if select_match:
            select_clause = select_match.group(1)

            # 컬럼 파싱 (쉼표로 분리, 별칭 처리)
            column_parts = select_clause.split(',')
            for part in column_parts:
                # 별칭 제거 (AS 처리)
                part = re.sub(r'\s+AS\s+\w+', '', part, flags=re.IGNORECASE)
                # 함수 호출 제거
                part = re.sub(r'\w+\([^)]*\)', '', part)
                # 공백 제거 및 따옴표 정리
                part = part.strip().strip('"').strip("'")

                if part and part != '*':
                    columns.append(part)

        return columns

    @classmethod
    def generate_column_alias(cls, column: str) -> str:
        """
        한글 컬럼명에 대한 영문 별칭 생성

        Args:
            column: 원본 컬럼명

        Returns:
            영문 별칭
        """
        alias_map = {
            "사번": "employee_id",
            "성명": "name",
            "본부": "headquarters",
            "직급": "position",
            "부서": "department",
            "지점": "branch",
            "연락처": "contact",
            "월평균사용예산": "monthly_avg_budget",
            "최근 평가": "recent_evaluation",
            "기본급(₩)": "base_salary",
            "성과급(₩)": "performance_pay",
            "책임업무": "responsibility",
            "담당자": "manager",
            "거래처ID": "client_id",
            "품목": "item",
            "월방문횟수": "monthly_visits",
            "사용 예산": "used_budget",
            "총환자수": "total_patients",
            "월": "month",
            "매출": "sales",
            "원장명": "director_name",
            "지역구": "district",
            "병원연락처": "hospital_contact"
        }

        return alias_map.get(column, f"col_{abs(hash(column)) % 10000}")

    @classmethod
    def add_column_aliases(cls, sql: str) -> str:
        """
        한글 컬럼에 영문 별칭 자동 추가

        Args:
            sql: 원본 SQL

        Returns:
            별칭이 추가된 SQL
        """
        # SELECT 절 찾기
        select_pattern = r'(SELECT\s+)(.*?)(\s+FROM)'
        match = re.search(select_pattern, sql, re.IGNORECASE | re.DOTALL)

        if not match:
            return sql

        select_keyword = match.group(1)
        select_clause = match.group(2)
        from_keyword = match.group(3)

        # 컬럼 파싱 및 별칭 추가
        columns = select_clause.split(',')
        aliased_columns = []

        for column in columns:
            column = column.strip()

            # 이미 별칭이 있는지 확인
            if ' AS ' in column.upper():
                aliased_columns.append(column)
                continue

            # 한글 컬럼인지 확인
            clean_column = column.strip('"').strip("'")
            if clean_column in cls.KOREAN_COLUMNS:
                alias = cls.generate_column_alias(clean_column)
                aliased_columns.append(f'{column} AS {alias}')
            else:
                aliased_columns.append(column)

        # 새로운 SELECT 절 구성
        new_select_clause = ', '.join(aliased_columns)
        new_sql = select_keyword + new_select_clause + from_keyword + sql[match.end(3):]

        return new_sql

    @classmethod
    def format_sql(cls, sql: str, indent: int = 2) -> str:
        """
        SQL 쿼리 포맷팅 (가독성 향상)

        Args:
            sql: 원본 SQL
            indent: 들여쓰기 공백 수

        Returns:
            포맷팅된 SQL
        """
        # 주요 키워드에서 줄바꿈
        keywords = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING', 'JOIN', 'LEFT JOIN', 'RIGHT JOIN']

        formatted = sql
        indent_str = ' ' * indent

        for keyword in keywords:
            pattern = r'\b' + keyword + r'\b'
            replacement = '\n' + keyword
            formatted = re.sub(pattern, replacement, formatted, flags=re.IGNORECASE)

        # 첫 줄바꿈 제거
        formatted = formatted.strip()

        # 쉼표 뒤 줄바꿈 (SELECT 절)
        if 'SELECT' in formatted.upper():
            lines = formatted.split('\n')
            new_lines = []
            for line in lines:
                if line.strip().upper().startswith('SELECT'):
                    # SELECT 절의 컬럼들을 줄바꿈
                    parts = line.split(',')
                    if len(parts) > 1:
                        new_lines.append(parts[0])
                        for part in parts[1:]:
                            new_lines.append(indent_str + ',' + part.strip())
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            formatted = '\n'.join(new_lines)

        return formatted


# 전역 인스턴스 (싱글톤 패턴)
_processor = KoreanSQLProcessor()


# 편의 함수들
def auto_quote_sql(sql: str) -> str:
    """SQL 쿼리에서 한글 컬럼명 자동 인용 처리"""
    return _processor.auto_quote_sql(sql)


def validate_korean_columns(columns: List[str]) -> Dict[str, bool]:
    """컬럼 목록의 한글 여부 확인"""
    return _processor.validate_korean_columns(columns)


def add_column_aliases(sql: str) -> str:
    """한글 컬럼에 영문 별칭 자동 추가"""
    return _processor.add_column_aliases(sql)


def format_sql(sql: str, indent: int = 2) -> str:
    """SQL 쿼리 포맷팅"""
    return _processor.format_sql(sql, indent)