"""Test validation logic for non-existent employees and dates"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.service.agents.sales_analytics_agent import SalesAnalyticsAgent
from backend.service.core.config import Config

async def test_validation():
    """Test validation for non-existent employees and invalid dates"""

    # Initialize agent
    config = Config()
    agent = SalesAnalyticsAgent(config)

    test_cases = [
        # Valid employee
        ("윤수아의 이번달 실적", "Valid employee - should work"),

        # Invalid employee
        ("김철수의 실적 조회", "Invalid employee - should show validation message"),
        ("박영희씨 판매 현황", "Invalid employee - should show validation message"),

        # Valid date
        ("2024년 3월 실적", "Valid date - should work"),

        # Invalid date (future)
        ("2025년 12월 실적", "Invalid future date - should show validation message"),
        ("2026년 실적 분석", "Invalid future year - should show validation message"),
    ]

    for query, description in test_cases:
        print(f"\n{'='*60}")
        print(f"Test: {description}")
        print(f"Query: {query}")
        print("-"*40)

        try:
            result = await agent.run(
                query=query,
                user_id="test_user",
                session_id="test_validation",
                language="ko"
            )

            # Check result
            if result.get('status') == 'completed':
                print("✓ Query executed successfully")
                if result.get('formatted_result'):
                    # Show first 200 chars of result
                    output = result['formatted_result'][:200]
                    if len(result['formatted_result']) > 200:
                        output += "..."
                    print(f"Result: {output}")
            elif result.get('status') == 'failed':
                print(f"✗ Query failed: {result.get('error', 'Unknown error')}")
                if result.get('formatted_result'):
                    print(f"Message: {result['formatted_result']}")
            else:
                print(f"? Unknown status: {result.get('status')}")

        except Exception as e:
            print(f"✗ Exception: {str(e)}")

if __name__ == "__main__":
    print("Testing validation logic for Sales Analytics Agent")
    print("="*60)
    asyncio.run(test_validation())