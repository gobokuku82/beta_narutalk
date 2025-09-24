"""
Text2SQL Unit Tests
Tests for SQL generation, entity extraction, and query clarification
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.service.tools import SQLGenerator, SQLExecutor, SchemaContext
from backend.service.tools.query_clarifier import QueryClarifier


class TestEntityExtraction:
    """Test entity extraction from Korean queries"""

    @pytest.fixture
    def sql_generator(self):
        """Create SQLGenerator instance"""
        generator = SQLGenerator()
        generator.use_llm = False  # Use rule-based for testing
        return generator

    @pytest.mark.parametrize("query,expected_name", [
        ("김철수의 실적", "김철수"),
        ("이영희씨 3월 매출", "이영희"),
        ("박 대리님의 성과", "박"),
        ("최수아의 11월 실적", "최수아"),
        ("윤하은 실적 분석", "윤하은"),
    ])
    def test_name_extraction_with_particles(self, sql_generator, query, expected_name):
        """Test that Korean particles are properly removed from names"""
        parsed = sql_generator.parse_query(query)
        # Check clean name field
        assert parsed.get("person_name") == expected_name or parsed.get("name") == expected_name
        print(f"✅ '{query}' → name: {expected_name}")

    @pytest.mark.parametrize("query,expected_month", [
        ("3월 실적", "03"),
        ("11월 매출", "11"),
        ("이번달 실적", None),  # Should be handled as current month
        ("지난달 성과", None),  # Should be handled as last month
    ])
    def test_month_extraction(self, sql_generator, query, expected_month):
        """Test month extraction from queries"""
        parsed = sql_generator.parse_query(query)
        if expected_month:
            assert parsed.get("month") == expected_month
        print(f"✅ '{query}' → month: {parsed.get('month')}")

    @pytest.mark.asyncio
    @patch('backend.service.tools.sql_generator.ChatOpenAI')
    async def test_llm_entity_extraction(self, mock_llm):
        """Test LLM-based entity extraction"""
        # Mock LLM response
        mock_response = AsyncMock()
        mock_response.content = '{"person_name": "김철수", "action_type": "sales", "month": null, "year": null, "team": null, "time_expression": null}'

        mock_llm_instance = AsyncMock()
        mock_llm_instance.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm.return_value = mock_llm_instance

        generator = SQLGenerator()
        generator.llm = mock_llm_instance
        generator.use_llm = True

        entities = await generator.extract_entities_with_llm("김철수의 실적")

        assert entities.get("person_name") == "김철수"
        assert entities.get("action_type") == "sales"
        print("✅ LLM entity extraction working correctly")


class TestQueryClarification:
    """Test query clarification for ambiguous inputs"""

    @pytest.fixture
    def clarifier(self):
        """Create QueryClarifier instance"""
        return QueryClarifier()

    @pytest.mark.parametrize("query,should_clarify", [
        ("어제 실적", True),  # Daily data not supported
        ("오늘 매출", True),  # Daily data not supported
        ("2024년 3월 실적", False),  # Clear query
        ("최근 실적", True),  # Vague time period
        ("최수아 11월 실적", False),  # Clear query
    ])
    def test_ambiguity_detection(self, clarifier, query, should_clarify):
        """Test detection of ambiguous queries"""
        entities = {"time_expression": None}

        # Extract time expressions
        for expr in clarifier.ambiguous_time_expressions:
            if expr in query:
                entities["time_expression"] = expr
                break

        result = clarifier.check_ambiguity(query, entities)
        assert result["needs_clarification"] == should_clarify

        if should_clarify:
            print(f"⚠️ '{query}' needs clarification: {result['message']}")
        else:
            print(f"✅ '{query}' is clear")

    def test_clarification_suggestions(self, clarifier):
        """Test that clarification provides helpful suggestions"""
        result = clarifier._create_clarification_response("어제", "daily")

        assert result["needs_clarification"] == True
        assert len(result["suggestions"]) > 0
        assert "월 단위" in result["message"]
        print(f"✅ Clarification provides {len(result['suggestions'])} suggestions")

    def test_error_suggestions(self, clarifier):
        """Test suggestions for error cases"""
        suggestions = clarifier.suggest_alternatives(
            "홍길동의 실적",
            "해당 직원이 시스템에 등록되어 있지 않습니다"
        )

        assert len(suggestions["suggestions"]) > 0
        assert "실제 직원명" in suggestions["suggestions"][0]
        print("✅ Error suggestions provided")


class TestSQLValidation:
    """Test SQL validation and safety checks"""

    @pytest.fixture
    def sql_generator(self):
        """Create SQLGenerator instance"""
        return SQLGenerator()

    @pytest.mark.parametrize("sql,is_safe", [
        ("SELECT * FROM sales_performance", True),
        ("DROP TABLE sales_performance", False),
        ("SELECT * FROM sales; DROP TABLE users", False),
        ("UPDATE sales_performance SET amount = 0", False),
        ("SELECT `담당자`, `202403` FROM sales_performance", True),
    ])
    def test_sql_validation(self, sql_generator, sql, is_safe):
        """Test SQL injection prevention"""
        result = sql_generator.validate_sql(sql)
        assert result == is_safe

        if is_safe:
            print(f"✅ Safe SQL: {sql[:50]}...")
        else:
            print(f"⛔ Unsafe SQL blocked: {sql[:50]}...")


class TestErrorMessages:
    """Test context-aware error messages"""

    @pytest.fixture
    def sql_executor(self):
        """Create SQLExecutor instance"""
        return SQLExecutor()

    def test_nonexistent_employee_message(self, sql_executor):
        """Test error message for non-existent employee"""
        context = {"person_name": "홍길동"}
        message = sql_executor.format_results([], context=context)

        assert "홍길동" in message
        assert "등록되어 있지 않습니다" in message
        print(f"✅ Proper error message for non-existent employee")

    def test_future_date_message(self, sql_executor):
        """Test error message for future dates"""
        context = {"future_date": True}
        message = sql_executor.format_results([], context=context)

        assert "가용 기간" in message
        assert "2024년 11월" in message
        print(f"✅ Proper error message for future dates")

    def test_team_not_supported_message(self, sql_executor):
        """Test error message for team queries"""
        context = {"team": "영업1팀"}
        message = sql_executor.format_results([], context=context)

        assert "영업1팀" in message
        assert "지원되지 않습니다" in message
        print(f"✅ Proper error message for unsupported team queries")


class TestIntegrationScenarios:
    """Integration tests for complete workflows"""

    @pytest.fixture
    def setup(self):
        """Setup test components"""
        return {
            "generator": SQLGenerator(),
            "executor": SQLExecutor(),
            "clarifier": QueryClarifier(),
            "schema": SchemaContext()
        }

    @pytest.mark.asyncio
    async def test_complete_workflow(self, setup):
        """Test complete workflow from query to result"""
        generator = setup["generator"]
        executor = setup["executor"]

        # Parse query
        query = "최수아 3월 실적"
        parsed = generator.parse_query(query)

        # Generate SQL
        sql, explanation = generator.generate_sql(parsed)

        # Validate SQL
        is_safe = generator.validate_sql(sql)
        assert is_safe == True

        print(f"✅ Complete workflow test passed")

    def test_schema_context_generation(self, setup):
        """Test schema context for LLM"""
        schema = setup["schema"]
        context = schema.get_llm_context()

        assert "sales_performance" in context
        assert "202212" in context
        assert "202411" in context
        print("✅ Schema context generated correctly")


def run_tests():
    """Run all tests with pytest"""
    import subprocess

    # Run pytest with verbose output
    result = subprocess.run(
        ["pytest", __file__, "-v", "--tb=short"],
        capture_output=True,
        text=True
    )

    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)

    return result.returncode == 0


if __name__ == "__main__":
    # Run tests
    print("=" * 70)
    print(" Running Text2SQL Tests ".center(70))
    print("=" * 70)

    success = run_tests()

    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")

    sys.exit(0 if success else 1)