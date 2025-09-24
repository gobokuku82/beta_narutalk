"""
Test Sales Analytics Agent with Real LLM Planning
실제 LLM 계획 수립과 함께 SalesAnalyticsAgent 테스트
"""

import asyncio
import logging
import sys
import os
import time
from typing import Dict, Any
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.service.agents.sales_analytics_agent import SalesAnalyticsAgent
from backend.service.core.context import create_context

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestSalesAgentReal:
    """Test SalesAnalyticsAgent with real execution"""

    def __init__(self):
        """Initialize the agent"""
        print("\n" + "="*80)
        print("Initializing Sales Analytics Agent Test")
        print("="*80)

        self.agent = SalesAnalyticsAgent()

        # Test queries
        self.test_queries = [
            {
                "id": "simple",
                "query": "김영희 실적 조회",
                "description": "Simple performance query"
            },
            {
                "id": "achievement",
                "query": "김철수 3월 달성률 계산",
                "description": "Achievement rate calculation"
            },
            {
                "id": "trend",
                "query": "최근 6개월 매출 트렌드 분석",
                "description": "Trend analysis"
            },
            {
                "id": "complex",
                "query": "전체 영업팀 실적 분석 및 목표 대비 달성률",
                "description": "Complex team analysis"
            }
        ]

    async def test_agent_execution(self, query: str) -> Dict[str, Any]:
        """Test actual agent execution with LLM planning"""

        print(f"\n{'='*60}")
        print(f"Testing Agent Execution")
        print(f"Query: {query}")
        print(f"{'='*60}")

        try:
            # Create initial input with context info
            input_data = {
                "query": query,
                "user_id": "test_user",
                "session_id": f"test_{datetime.now().timestamp()}",
                "original_query": query
            }

            # Execute agent (it creates context internally)
            start_time = time.time()
            result = await self.agent.execute(input_data)
            execution_time = time.time() - start_time

            print(f"\n[Execution Result]")
            print(f"Status: {result.get('status', 'unknown')}")
            print(f"Execution Step: {result.get('execution_step', 'unknown')}")
            print(f"Time taken: {execution_time:.2f}s")

            # Check if LLM planning was used
            if "execution_plan" in result:
                plan = result["execution_plan"]
                print(f"\n[LLM Plan Used]")
                print(f"Subgraphs: {plan.get('use_subgraphs', [])}")
                print(f"Tools: {plan.get('use_tools', [])}")
                print(f"SQL: {plan.get('use_sql', False)}")
                print(f"Reasoning: {plan.get('reasoning', 'N/A')[:200]}...")

            # Check execution results
            if "execution_results" in result:
                exec_results = result["execution_results"]
                print(f"\n[Execution Details]")

                if "collected_data" in exec_results:
                    data = exec_results["collected_data"]
                    print(f"Data Collection: {data.get('collection_status', 'N/A')}")

                if "tool_results" in exec_results:
                    tools = exec_results["tool_results"]
                    print(f"Tools Used: {list(tools.keys())}")

                if "analysis_result" in exec_results:
                    analysis = exec_results["analysis_result"]
                    print(f"Analysis: {analysis.get('analysis_status', 'N/A')}")

            # Show formatted result
            if "formatted_result" in result:
                print(f"\n[Formatted Output]")
                output = result["formatted_result"]
                print(output[:500] + "..." if len(output) > 500 else output)

            return {
                "success": True,
                "execution_time": execution_time,
                "result": result
            }

        except Exception as e:
            logger.error(f"Error during agent execution: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }

    async def run_all_tests(self):
        """Run all test queries"""
        print(f"\n{'='*80}")
        print("Running All Test Queries")
        print(f"{'='*80}")

        results = []
        for test_case in self.test_queries:
            print(f"\n[Test: {test_case['id']}] {test_case['description']}")
            result = await self.test_agent_execution(test_case["query"])
            results.append({
                "test_case": test_case,
                "result": result
            })
            await asyncio.sleep(1)  # Small delay between tests

        # Summary
        print(f"\n{'='*80}")
        print("Test Summary")
        print(f"{'='*80}")

        successful = sum(1 for r in results if r["result"]["success"])
        failed = len(results) - successful

        print(f"\nTotal Tests: {len(results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")

        # Performance summary
        total_time = sum(r["result"].get("execution_time", 0) for r in results if r["result"]["success"])
        if successful > 0:
            print(f"\nAverage Execution Time: {total_time/successful:.2f}s")

        # Check if LLM planning was used
        llm_used = sum(1 for r in results if "execution_plan" in r["result"].get("result", {}))
        print(f"LLM Planning Used: {llm_used}/{len(results)}")

        return results

    async def test_single_interactive(self):
        """Interactive single query test"""
        query = input("\nEnter query: ").strip()
        if query:
            await self.test_agent_execution(query)
        else:
            print("Empty query")


async def main():
    """Main test runner"""
    tester = TestSalesAgentReal()

    while True:
        print(f"\n{'='*60}")
        print("Sales Agent Real Execution Test")
        print(f"{'='*60}")
        print("1. Run all tests")
        print("2. Test single query (interactive)")
        print("3. Check LLM planning status")
        print("0. Exit")
        print("-"*60)

        choice = input("Select option: ").strip()

        if choice == "0":
            break

        elif choice == "1":
            await tester.run_all_tests()

        elif choice == "2":
            await tester.test_single_interactive()

        elif choice == "3":
            # Check if LLM planning is enabled
            if tester.agent.use_llm_planning:
                print("\n[OK] LLM Planning is ENABLED")
                print(f"Model: {tester.agent.planner_llm.model_name if tester.agent.planner_llm else 'N/A'}")
            else:
                print("\n[X] LLM Planning is DISABLED")
                print("Set OPENAI_API_KEY environment variable to enable")

        else:
            print("Invalid choice")

        if choice != "0":
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    print("Starting Sales Agent Real Execution Test...")
    asyncio.run(main())