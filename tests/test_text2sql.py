"""
Test Text2SQL functionality in SalesAnalyticsAgent
"""

import asyncio
from backend.service.agents import SalesAnalyticsAgent

async def test_queries():
    """Test various queries"""
    agent = SalesAnalyticsAgent()

    test_cases = [
        "김철수 3월 실적",
        "최시우 4월 매출",
        "이영희 작년 12월 실적",
        "영업팀 평균 실적",
        "이번달 전체 매출"
    ]

    for query in test_cases:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)

        # Prepare input
        input_data = {
            "user_id": "test_user",
            "session_id": f"test_{query[:5]}",
            "original_query": query,
            "intent_result": {},
            "employee_name": "",  # Will be extracted from query
            "period": "monthly"
        }

        # Execute agent
        try:
            result = await agent.execute(input_data)

            if result["status"] == "success":
                data = result.get("data", {})
                print(f"\nStatus: {data.get('status')}")
                print(f"SQL: {data.get('generated_sql', 'N/A')}")
                print(f"\nResult:\n{data.get('formatted_result', 'No result')}")
            else:
                print(f"Error: {result.get('error')}")

        except Exception as e:
            print(f"Exception: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "="*70)
    print(" Text2SQL Testing ".center(70))
    print("="*70)

    asyncio.run(test_queries())