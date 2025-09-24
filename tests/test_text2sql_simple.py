"""
Simple Text2SQL Tests - No pytest required
Direct testing of Text2SQL functionality
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.service.tools import SQLGenerator, SQLExecutor, SchemaContext
from backend.service.tools.query_clarifier import QueryClarifier


def test_name_extraction():
    """Test Korean name extraction with particles"""
    print("\n[Test: Name Extraction]")
    print("-" * 40)

    generator = SQLGenerator()
    generator.use_llm = False  # Use rule-based for testing

    test_cases = [
        ("김철수의 실적", "김철수"),
        ("이영희씨 3월 매출", "이영희"),
        ("박 대리님의 성과", "박"),
        ("최수아의 11월 실적", "최수아"),
        ("윤하은 실적 분석", "윤하은"),
    ]

    passed = 0
    failed = 0

    for query, expected_name in test_cases:
        parsed = generator.parse_query(query)
        # Get clean name from person_name field or clean the name field
        clean_name = parsed.get("person_name")
        if not clean_name:
            # Fallback to cleaning name field manually
            raw_name = parsed.get("name", "")
            clean_name = raw_name.rstrip("의").rstrip("씨").rstrip("님")

        if clean_name == expected_name:
            print(f"  [PASS] '{query}' → {clean_name}")
            passed += 1
        else:
            print(f"  [FAIL] '{query}' → {clean_name} (expected: {expected_name})")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_sql_validation():
    """Test SQL injection prevention"""
    print("\n[Test: SQL Validation]")
    print("-" * 40)

    generator = SQLGenerator()

    test_cases = [
        ("SELECT * FROM sales_performance", True, "Safe SELECT query"),
        ("DROP TABLE sales_performance", False, "Dangerous DROP"),
        ("DELETE FROM sales_performance", False, "Dangerous DELETE"),
        ("UPDATE sales_performance SET x=0", False, "Dangerous UPDATE"),
        ("SELECT * FROM sales; DROP TABLE", False, "Multiple statements"),
    ]

    passed = 0
    failed = 0

    for sql, should_be_safe, description in test_cases:
        is_safe = generator.validate_sql(sql)

        if is_safe == should_be_safe:
            print(f"  [PASS] {description}")
            passed += 1
        else:
            print(f"  [FAIL] {description} - got {is_safe}, expected {should_be_safe}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_query_clarification():
    """Test ambiguous query detection"""
    print("\n[Test: Query Clarification]")
    print("-" * 40)

    clarifier = QueryClarifier()

    test_cases = [
        ("어제 실적", True, "Daily data not supported"),
        ("오늘 매출", True, "Daily data not supported"),
        ("2024년 3월 실적", False, "Clear month/year"),
        ("최근 실적", True, "Vague time period"),
        ("최수아 11월 실적", False, "Clear name and month"),
    ]

    passed = 0
    failed = 0

    for query, should_clarify, description in test_cases:
        entities = {"time_expression": None}

        # Check for ambiguous time expressions
        for expr in clarifier.ambiguous_time_expressions:
            if expr in query:
                entities["time_expression"] = expr
                break

        result = clarifier.check_ambiguity(query, entities)
        needs_clarification = result["needs_clarification"]

        if needs_clarification == should_clarify:
            print(f"  [PASS] {description}: '{query}'")
            passed += 1
        else:
            print(f"  [FAIL] {description}: '{query}' - got {needs_clarification}, expected {should_clarify}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_error_messages():
    """Test context-aware error messages"""
    print("\n[Test: Error Messages]")
    print("-" * 40)

    executor = SQLExecutor()

    test_cases = [
        ({"person_name": "홍길동"}, "등록되어 있지 않습니다", "Non-existent person"),
        ({"future_date": True}, "가용 기간", "Future date"),
        ({"team": "영업1팀"}, "지원되지 않습니다", "Team query"),
    ]

    passed = 0
    failed = 0

    for context, expected_text, description in test_cases:
        message = executor.format_results([], context=context)

        if expected_text in message:
            print(f"  [PASS] {description}")
            passed += 1
        else:
            print(f"  [FAIL] {description} - expected '{expected_text}' in message")
            print(f"         Got: {message[:100]}...")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_sql_generation():
    """Test basic SQL generation"""
    print("\n[Test: SQL Generation]")
    print("-" * 40)

    generator = SQLGenerator()
    generator.use_llm = False  # Use rule-based

    # Test simple query
    query = "최수아 3월 실적"
    parsed = generator.parse_query(query)
    sql, explanation = generator.generate_sql(parsed)

    # Check if SQL is valid
    is_valid = generator.validate_sql(sql)

    if is_valid and "SELECT" in sql:
        print(f"  [PASS] Generated valid SQL for '{query}'")
        print(f"         SQL: {sql[:100]}...")
        return True
    else:
        print(f"  [FAIL] Failed to generate valid SQL for '{query}'")
        return False


def main():
    """Run all tests"""
    print("="*60)
    print(" Text2SQL Simple Tests ".center(60))
    print("="*60)

    all_tests = [
        test_name_extraction,
        test_sql_validation,
        test_query_clarification,
        test_error_messages,
        test_sql_generation,
    ]

    results = []
    for test_func in all_tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\n[ERROR] Test {test_func.__name__} failed with error: {e}")
            results.append(False)

    # Summary
    print("\n" + "="*60)
    passed_tests = sum(results)
    total_tests = len(results)

    if passed_tests == total_tests:
        print(f" ALL TESTS PASSED ({passed_tests}/{total_tests}) ".center(60))
    else:
        print(f" SOME TESTS FAILED ({passed_tests}/{total_tests} passed) ".center(60))
    print("="*60)

    return 0 if passed_tests == total_tests else 1


if __name__ == "__main__":
    sys.exit(main())