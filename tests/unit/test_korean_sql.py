"""
한글 SQL 처리 유틸리티 단위 테스트
Phase 1: Korean SQL Utils
"""

import pytest
import sys
from pathlib import Path

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.common.korean_sql_utils import KoreanSQLProcessor


class TestKoreanSQLProcessor:
    """한글 SQL 처리 테스트"""

    @pytest.fixture
    def processor(self):
        """KoreanSQLProcessor 인스턴스"""
        return KoreanSQLProcessor()

    def test_detect_korean_columns(self, processor):
        """한글 컬럼명 감지 테스트"""
        # 한글 컬럼 검증
        columns_with_korean = ["사번", "성명"]
        result = processor.validate_korean_columns(columns_with_korean)
        assert all(result.values()) is True

        # 한글 미포함 컬럼
        columns_without_korean = ["id", "name"]
        result = processor.validate_korean_columns(columns_without_korean)
        assert all(result.values()) is False

        # 혼합 컬럼
        mixed_columns = ["id", "성명", "department"]
        result = processor.validate_korean_columns(mixed_columns)
        assert result["성명"] is True
        assert result["id"] is False

    def test_auto_quote_sql(self, processor):
        """한글 컬럼명 자동 인용 테스트"""
        # 기본 인용
        query = "SELECT 사번, 성명 FROM employees"
        quoted = processor.auto_quote_sql(query)
        assert '"사번"' in quoted
        assert '"성명"' in quoted

        # WHERE 절의 한글
        where_query = "SELECT * FROM employees WHERE 부서 = 'IT'"
        quoted_where = processor.auto_quote_sql(where_query)
        assert '"부서"' in quoted_where

    def test_format_sql(self, processor):
        """SQL 포맷팅 테스트"""
        # 대소문자 혼합
        mixed_case = "select 사번 from employees"
        formatted = processor.format_sql(mixed_case)
        assert "SELECT" in formatted or "select" in formatted
        assert "FROM" in formatted or "from" in formatted

        # 여러 컬럼 포맷팅
        multi_column = "SELECT 사번, 성명, 부서 FROM employees"
        formatted_multi = processor.format_sql(multi_column)
        # 포맷팅 후 가독성 향상
        assert "\n" in formatted_multi  # 줄바꿈이 있어야 함

    def test_column_alias_generation(self, processor):
        """컬럼 별칭 생성 테스트"""
        # 알려진 한글 컬럼의 별칭
        assert processor.generate_column_alias("사번") == "employee_id"
        assert processor.generate_column_alias("성명") == "name"
        assert processor.generate_column_alias("부서") == "department"

        # 별칭 자동 추가
        query = "SELECT 사번, 성명 FROM employees"
        aliased = processor.add_column_aliases(query)
        assert "AS employee_id" in aliased or "AS name" in aliased

    def test_extract_columns_from_sql(self, processor):
        """SQL에서 컬럼명 추출 테스트"""
        query = "SELECT 사번, 성명, id FROM employees WHERE 부서 = 'IT'"
        columns = processor.extract_columns_from_sql(query)

        assert "사번" in columns
        assert "성명" in columns
        assert "id" in columns

    def test_add_column_aliases(self, processor):
        """컬럼 별칭 추가 테스트"""
        query = "SELECT 사번, 성명 FROM employees"
        aliased = processor.add_column_aliases(query)

        # 별칭이 추가되어야 함
        assert "AS" in aliased
        # 원본 한글 컬럼은 유지되고 별칭만 추가
        assert "사번" in aliased or '"사번"' in aliased
        assert "성명" in aliased or '"성명"' in aliased

    def test_complex_korean_query(self, processor):
        """복잡한 한글 쿼리 처리 테스트"""
        complex_query = "SELECT 사번, 성명, 부서 FROM 인사자료 WHERE 직급 = '과장'"

        # 자동 인용 처리
        quoted = processor.auto_quote_sql(complex_query)
        assert '"사번"' in quoted
        assert '"성명"' in quoted
        assert '"부서"' in quoted
        assert '"인사자료"' in quoted  # 테이블명도 처리
        assert '"직급"' in quoted

    def test_monthly_columns(self, processor):
        """월별 컬럼 처리 테스트"""
        # 월별 컬럼 포함 쿼리
        monthly_query = "SELECT 사번, 202401, 202402 FROM sales"
        quoted = processor.auto_quote_sql(monthly_query)

        # 월별 컬럼도 인용되어야 함
        assert '"202401"' in quoted
        assert '"202402"' in quoted

    @pytest.mark.parametrize("column,expected", [
        ("사번", True),
        ("employee_id", False),
        ("성명", True),
        ("부서", True),
        ("ID123", False)
    ])
    def test_validate_single_column(self, processor, column, expected):
        """개별 컬럼명 한글 여부 테스트"""
        result = processor.validate_korean_columns([column])
        assert result[column] == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])