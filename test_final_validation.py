"""Final validation test with all fixes"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.service.agents.sales_analytics_agent import SalesAnalyticsAgent
from backend.service.core.config import Config

async def test_final_validation():
    """Test final validation with all fixes"""

    # Initialize agent
    config = Config()
    agent = SalesAnalyticsAgent(config)

    test_cases = [
        # Test 1: Valid employees
        ("윤수아의 2024년 3월 실적", "Valid employee with valid date"),
        ("조시현 판매 현황", "Valid employee"),

        # Test 2: Invalid employees (should show validation message)
        ("김철수의 실적 조회", "Invalid employee - should show validation"),
        ("박영희씨 판매 현황", "Invalid employee - should show validation"),
        ("이민수 2024년 실적", "Invalid employee - should show validation"),

        # Test 3: Valid dates
        ("2024년 10월 실적", "Valid date range"),
        ("2023년 실적 분석", "Valid year"),

        # Test 4: Invalid dates (should show validation message)
        ("2025년 12월 실적", "Future date - should show validation"),
        ("2026년 판매 계획", "Future year - should show validation"),
        ("2025년 1월 실적", "Future date - should show validation"),
    ]

    success_count = 0
    fail_count = 0

    for query, description in test_cases:
        print(f"\n{'='*60}")
        print(f"Test: {description}")
        print(f"Query: {query}")
        print("-"*40)

        try:
            result = await agent.run(
                query=query,
                user_id="test_user",
                session_id="final_test",
                language="ko"
            )

            # Check if it's a validation case
            is_validation_case = "Invalid" in description or "Future" in description

            if result.get('status') == 'completed':
                formatted_result = result.get('formatted_result', '')

                # Check if it contains validation messages
                has_validation_msg = ('찾을 수 없습니다' in formatted_result or
                                     '데이터는 없습니다' in formatted_result or
                                     '등록된 직원' in formatted_result or
                                     '가용 기간' in formatted_result)

                if is_validation_case:
                    if has_validation_msg or '조회 결과가 없습니다' in formatted_result:
                        print("O PASS - Validation message shown correctly")
                        success_count += 1
                    else:
                        print("X FAIL - Expected validation message but got results")
                        fail_count += 1
                else:
                    if has_validation_msg:
                        print("X FAIL - Unexpected validation message for valid query")
                        fail_count += 1
                    else:
                        print("O PASS - Query executed successfully")
                        success_count += 1

                # Show partial result
                if formatted_result:
                    preview = formatted_result[:150].replace('\n', ' ')
                    if len(formatted_result) > 150:
                        preview += "..."
                    print(f"Result preview: {preview}")

            else:
                print(f"X Query failed with status: {result.get('status')}")
                fail_count += 1

        except Exception as e:
            print(f"X Exception: {str(e)}")
            fail_count += 1

    print(f"\n{'='*60}")
    print(f"FINAL TEST RESULTS:")
    print(f"  Success: {success_count}")
    print(f"  Failed: {fail_count}")
    print(f"  Total: {success_count + fail_count}")
    print(f"  Pass Rate: {success_count / (success_count + fail_count) * 100:.1f}%")

if __name__ == "__main__":
    print("Running final validation test")
    print("="*60)
    asyncio.run(test_final_validation())