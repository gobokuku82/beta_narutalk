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
        # 한글 포함 쿼리
        query_with_korean = "SELECT 사번, 성명 FROM employees"
        assert processor.has_korean_columns(query_with_korean) is True

        # 한글 미포함 쿼리
        query_without_korean = "SELECT id, name FROM employees"
        assert processor.has_korean_columns(query_without_korean) is False

        # 혼합 쿼리
        mixed_query = "SELECT id, 성명, department FROM employees"
        assert processor.has_korean_columns(mixed_query) is True

    def test_escape_korean_columns(self, processor):
        """한글 컬럼명 이스케이프 테스트"""
        # 기본 이스케이프
        query = "SELECT 사번, 성명 FROM employees"
        escaped = processor.escape_korean_columns(query)
        assert '"사번"' in escaped or '[사번]' in escaped
        assert '"성명"' in escaped or '[성명]' in escaped

        # WHERE 절의 한글
        where_query = "SELECT * FROM employees WHERE 부서 = 'IT'"
        escaped_where = processor.escape_korean_columns(where_query)
        assert '"부서"' in escaped_where or '[부서]' in escaped_where

    def test_normalize_query(self, processor):
        """쿼리 정규화 테스트"""
        # 대소문자 혼합
        mixed_case = "SeLeCt 사번 FrOm EMPLOYEES"
        normalized = processor.normalize_query(mixed_case)
        assert "SELECT" in normalized.upper()
        assert "FROM" in normalized.upper()

        # 여러 공백
        multi_space = "SELECT     사번,     성명     FROM     employees"
        normalized_space = processor.normalize_query(multi_space)
        # 정규화 후 과도한 공백이 제거되어야 함
        assert "     " not in normalized_space

    def test_validate_korean_query(self, processor):
        """한글 쿼리 검증 테스트"""
        # 유효한 쿼리
        valid_query = "SELECT 사번, 성명 FROM employees"
        is_valid, message = processor.validate_korean_query(valid_query)
        assert is_valid is True

        # 위험한 쿼리 (DELETE)
        dangerous_query = "DELETE FROM employees WHERE 사번 = '1234'"
        is_valid, message = processor.validate_korean_query(dangerous_query)
        assert is_valid is False
        assert "DELETE" in message

        # 빈 쿼리
        empty_query = ""
        is_valid, message = processor.validate_korean_query(empty_query)
        assert is_valid is False

    def test_extract_korean_columns(self, processor):
        """한글 컬럼명 추출 테스트"""
        query = "SELECT 사번, 성명, id FROM employees WHERE 부서 = 'IT'"
        korean_columns = processor.extract_korean_columns(query)

        assert "사번" in korean_columns
        assert "성명" in korean_columns
        assert "부서" in korean_columns
        assert "id" not in korean_columns

    def test_replace_korean_with_alias(self, processor):
        """한글 컬럼명 별칭 치환 테스트"""
        query = "SELECT 사번, 성명 FROM employees"
        aliased, mapping = processor.replace_with_alias(query)

        # 별칭이 생성되어야 함
        assert "col_" in aliased
        assert "사번" not in aliased
        assert "성명" not in aliased

        # 매핑이 올바르게 생성되어야 함
        assert len(mapping) == 2
        assert any("사번" in v for v in mapping.values())

    def test_complex_korean_query(self, processor):
        """복잡한 한글 쿼리 처리 테스트"""
        complex_query = """
        SELECT e.사번, e.성명, d.부서명, s.급여
        FROM 직원 e
        JOIN 부서 d ON e.부서코드 = d.부서코드
        JOIN 급여 s ON e.사번 = s.사번
        WHERE e.입사일 >= '2024-01-01'
        ORDER BY s.급여 DESC
        """

        # 한글 컬럼 감지
        assert processor.has_korean_columns(complex_query) is True

        # 한글 컬럼 추출
        korean_columns = processor.extract_korean_columns(complex_query)
        assert len(korean_columns) > 0

        # 이스케이프 처리
        escaped = processor.escape_korean_columns(complex_query)
        assert escaped != complex_query  # 변경이 있어야 함

    def test_korean_column_in_functions(self, processor):
        """함수 내 한글 컬럼명 처리 테스트"""
        function_query = "SELECT COUNT(사번), AVG(급여), MAX(나이) FROM 직원"

        # 한글 컬럼 감지
        assert processor.has_korean_columns(function_query) is True

        # 이스케이프 처리
        escaped = processor.escape_korean_columns(function_query)
        # 함수 내부의 컬럼도 이스케이프되어야 함
        assert ("COUNT(\"사번\")" in escaped or "COUNT([사번])" in escaped)

    @pytest.mark.parametrize("column,expected", [
        ("사번", True),
        ("employee_id", False),
        ("직원_성명", True),
        ("dept_부서", True),
        ("ID123", False)
    ])
    def test_is_korean_column(self, processor, column, expected):
        """개별 컬럼명 한글 여부 테스트"""
        assert processor.is_korean_column(column) == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])