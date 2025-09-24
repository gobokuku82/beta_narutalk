"""
Test Runner for Text2SQL
Runs all test suites and provides summary
"""

import subprocess
import sys
import os
from datetime import datetime


def run_test_suite(test_file, description):
    """
    Run a specific test suite

    Args:
        test_file: Test file to run
        description: Description of the test suite

    Returns:
        True if tests passed, False otherwise
    """
    print(f"\n{'='*60}")
    print(f" {description} ".center(60))
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)

        return result.returncode == 0

    except Exception as e:
        print(f"❌ Failed to run {test_file}: {e}")
        return False


def run_simple_tests():
    """Run simple tests without pytest"""
    print("\n" + "="*60)
    print(" Running Simple Tests (No pytest required) ".center(60))
    print("="*60)

    # Import and test directly
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    try:
        from backend.service.tools import SQLGenerator, SQLExecutor
        from backend.service.tools.query_clarifier import QueryClarifier

        results = []

        # Test 1: Name extraction
        print("\n[Test 1: Name Extraction]")
        generator = SQLGenerator()
        generator.use_llm = False  # Use rule-based

        test_cases = [
            ("김철수의 실적", "김철수"),
            ("이영희씨 3월 매출", "이영희"),
            ("최수아 11월 실적", "최수아"),
        ]

        for query, expected_name in test_cases:
            parsed = generator.parse_query(query)
            clean_name = parsed.get("person_name") or parsed.get("name", "").rstrip("의").rstrip("씨").rstrip("님")
            success = clean_name == expected_name
            results.append(success)
            symbol = "PASS" if success else "FAIL"
            print(f"  [{symbol}] '{query}' → {clean_name} (expected: {expected_name})")

        # Test 2: SQL Validation
        print("\n[Test 2: SQL Validation]")
        dangerous_sqls = [
            "DROP TABLE sales_performance",
            "DELETE FROM sales_performance",
            "UPDATE sales_performance SET amount = 0",
        ]

        for sql in dangerous_sqls:
            is_safe = generator.validate_sql(sql)
            success = not is_safe  # Should be blocked
            results.append(success)
            symbol = "PASS" if success else "FAIL"
            print(f"  [{symbol}] Blocked dangerous SQL: {sql[:30]}...")

        # Test 3: Query Clarification
        print("\n[Test 3: Query Clarification]")
        clarifier = QueryClarifier()

        ambiguous_queries = [
            "어제 실적",
            "오늘 매출",
            "최근 실적"
        ]

        for query in ambiguous_queries:
            entities = {"time_expression": None}
            for expr in clarifier.ambiguous_time_expressions:
                if expr in query:
                    entities["time_expression"] = expr
                    break

            result = clarifier.check_ambiguity(query, entities)
            success = result["needs_clarification"] == True
            results.append(success)
            symbol = "PASS" if success else "FAIL"
            print(f"  [{symbol}] '{query}' needs clarification: {result['needs_clarification']}")

        # Test 4: Error Messages
        print("\n[Test 4: Context-aware Error Messages]")
        executor = SQLExecutor()

        contexts = [
            ({"person_name": "홍길동"}, "등록되어 있지 않습니다"),
            ({"future_date": True}, "가용 기간"),
            ({"team": "영업1팀"}, "지원되지 않습니다"),
        ]

        for context, expected_text in contexts:
            message = executor.format_results([], context=context)
            success = expected_text in message
            results.append(success)
            symbol = "PASS" if success else "FAIL"
            print(f"  [{symbol}] Context {list(context.keys())[0]}: '{expected_text}' in message")

        # Summary
        passed = sum(results)
        total = len(results)
        print(f"\n[Results: {passed}/{total} tests passed]")

        return passed == total

    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        print("Make sure all required modules are installed")
        return False
    except Exception as e:
        print(f"[ERROR] Test error: {e}")
        return False


def main():
    """Main test runner"""
    print("\n" + "="*70)
    print(" Text2SQL Test Suite Runner ".center(70))
    print(f" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ".center(70))
    print("="*70)

    all_passed = True

    # Check if pytest is available
    try:
        import pytest
        has_pytest = True
    except ImportError:
        has_pytest = False
        print("\n[WARNING] pytest not installed. Running simple tests only.")

    if has_pytest:
        # Run pytest test suites
        test_suites = [
            ("tests/test_text2sql_unit.py", "Unit Tests"),
            # Add more test files here as needed
        ]

        for test_file, description in test_suites:
            if os.path.exists(test_file):
                passed = run_test_suite(test_file, description)
                all_passed = all_passed and passed
            else:
                print(f"\n[WARNING] Test file not found: {test_file}")
    else:
        # Run simple tests without pytest
        passed = run_simple_tests()
        all_passed = all_passed and passed

    # Final summary
    print("\n" + "="*70)
    if all_passed:
        print(" ALL TESTS PASSED! ".center(70))
    else:
        print(" SOME TESTS FAILED ".center(70))
    print("="*70)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())