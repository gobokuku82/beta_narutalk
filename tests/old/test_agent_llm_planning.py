"""
Test LLM Planning in SalesAnalyticsAgent
Agent 내부 LLM 계획 수립 및 실행 테스트
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


class TestAgentLLMPlanning:
    """Test suite for LLM-based planning in agents"""

    def __init__(self):
        self.agent = SalesAnalyticsAgent()
        self.test_queries = [
            {
                "id": "simple_sql",
                "query": "김영희 3월 실적",
                "expected": "SQL query should be sufficient",
                "description": "Simple query requiring only SQL"
            },
            {
                "id": "with_calculation",
                "query": "김영희 달성률 계산",
                "expected": "Should use data_collection + calculation tool",
                "description": "Query requiring subgraph and tool"
            },
            {
                "id": "trend_analysis",
                "query": "최근 6개월 매출 트렌드 분석",
                "expected": "Should use data_collection + trend tool",
                "description": "Query requiring trend analysis"
            },
            {
                "id": "complex",
                "query": "모든 직원의 목표 대비 실적 비교 분석하고 인사이트 도출",
                "expected": "Should use multiple subgraphs and tools",
                "description": "Complex query requiring full pipeline"
            },
            {
                "id": "cross_db",
                "query": "영업팀 전체의 거래처별 실적과 목표 달성률",
                "expected": "Should use data_collection + cross_db tool",
                "description": "Cross-database analysis"
            }
        ]

    async def test_llm_planning(self, query: str) -> Dict[str, Any]:
        """Test LLM planning for a single query"""
        print(f"\n{'='*60}")
        print(f"Testing LLM Planning")
        print(f"Query: {query}")
        print(f"{'='*60}")

        try:
            # Create context for runtime (use agent context type)
            context = create_context(
                user_id="test_user",
                session_id=f"test_{datetime.now().timestamp()}",
                context_type="agent",
                request_id=f"req_{datetime.now().timestamp()}",
                original_query=query
            )

            # Create initial state
            initial_state = {
                "query": query,
                "status": "pending",
                "execution_step": "starting",
                "parsed_query": {},
                "generated_sql": "",
                "sql_result": [],
                "formatted_result": "",
                "raw_data": [],
                "statistics": {},
                "aggregated_data": {},
                "charts_data": [],
                "insights": [],
                "final_report": {}
            }

            # Mock runtime object
            class MockRuntime:
                def __init__(self, context):
                    self.context = context

            runtime = MockRuntime(context)

            # Test LLM planning
            start_time = time.time()
            planning_result = await self.agent.llm_planning(initial_state, runtime)
            planning_time = time.time() - start_time

            print(f"\n[Planning Result]")
            print(f"Time taken: {planning_time:.2f}s")

            if "execution_plan" in planning_result:
                plan = planning_result["execution_plan"]
                print(f"\nExecution Plan:")
                print(f"  Use Subgraphs: {plan.get('use_subgraphs', [])}")
                print(f"  Use Tools: {plan.get('use_tools', [])}")
                print(f"  Use SQL: {plan.get('use_sql', False)}")
                print(f"  Execution Order: {plan.get('execution_order', [])}")
                print(f"  Reasoning: {plan.get('reasoning', 'N/A')}")

                # Test execution
                print(f"\n[Executing Plan]")
                initial_state.update(planning_result)

                exec_start = time.time()
                execution_result = await self.agent.execute_plan(initial_state, runtime)
                exec_time = time.time() - exec_start

                print(f"Execution time: {exec_time:.2f}s")
                print(f"Execution status: {execution_result.get('execution_step')}")

                if "execution_results" in execution_result:
                    results = execution_result["execution_results"]
                    print(f"\nResults:")

                    if "collected_data" in results:
                        data = results["collected_data"]
                        print(f"  Data Collection: {data.get('collection_status', 'N/A')}")
                        if "aggregated_performance" in data:
                            print(f"    Performance records: {len(data.get('performance_data', []))}")
                            print(f"    Target records: {len(data.get('target_data', []))}")

                    if "tool_results" in results:
                        tools = results["tool_results"]
                        print(f"  Tools Used:")
                        for tool_name, tool_result in tools.items():
                            print(f"    - {tool_name}: {type(tool_result)}")
                            if isinstance(tool_result, dict) and "average_achievement" in tool_result:
                                print(f"      Average Achievement: {tool_result['average_achievement']:.1f}%")

                    if "sql_result" in results:
                        print(f"  SQL Results: {len(results['sql_result'])} rows")

                    if "analysis_result" in results:
                        analysis = results["analysis_result"]
                        print(f"  Analysis: {analysis.get('analysis_status', 'N/A')}")

                if "formatted_result" in execution_result:
                    print(f"\n[Formatted Result]")
                    print(execution_result["formatted_result"][:500])
                    if len(execution_result["formatted_result"]) > 500:
                        print("... (truncated)")

                return {
                    "success": True,
                    "planning_time": planning_time,
                    "execution_time": exec_time,
                    "total_time": planning_time + exec_time,
                    "plan": plan,
                    "results": execution_result
                }

            else:
                print(f"Error: No execution plan generated")
                return {
                    "success": False,
                    "error": "No execution plan"
                }

        except Exception as e:
            print(f"Error during test: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }

    async def test_all_queries(self):
        """Test all predefined queries"""
        print(f"\n{'='*80}")
        print("Testing All Queries with LLM Planning")
        print(f"{'='*80}")

        results = []
        for test_case in self.test_queries:
            print(f"\n[Test Case: {test_case['id']}]")
            print(f"Description: {test_case['description']}")
            print(f"Expected: {test_case['expected']}")

            result = await self.test_llm_planning(test_case["query"])
            result["test_case"] = test_case
            results.append(result)

            # Short delay between tests
            await asyncio.sleep(1)

        # Summary
        print(f"\n{'='*80}")
        print("Test Summary")
        print(f"{'='*80}")

        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful

        print(f"\nTotal Tests: {len(results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")

        # Performance metrics
        total_planning_time = sum(r.get("planning_time", 0) for r in results if r["success"])
        total_execution_time = sum(r.get("execution_time", 0) for r in results if r["success"])

        if successful > 0:
            print(f"\nAverage Planning Time: {total_planning_time/successful:.2f}s")
            print(f"Average Execution Time: {total_execution_time/successful:.2f}s")
            print(f"Average Total Time: {(total_planning_time + total_execution_time)/successful:.2f}s")

        # Plan analysis
        print(f"\nPlan Analysis:")
        for result in results:
            if result["success"] and "plan" in result:
                test_case = result["test_case"]
                plan = result["plan"]
                print(f"\n{test_case['id']}:")
                print(f"  Subgraphs: {plan.get('use_subgraphs', [])}")
                print(f"  Tools: {plan.get('use_tools', [])}")
                print(f"  SQL: {plan.get('use_sql', False)}")

        return results

    async def test_specific_scenario(self, scenario: str):
        """Test specific scenarios"""
        scenarios = {
            "simple": "김철수 실적",
            "achievement": "김영희 3월 달성률",
            "trend": "2024년 상반기 트렌드",
            "complex": "전체 영업팀 실적 분석 및 목표 대비 달성률 계산하고 향후 예측",
            "cross": "모든 거래처의 담당자별 실적"
        }

        if scenario in scenarios:
            query = scenarios[scenario]
            print(f"\nTesting scenario: {scenario}")
            return await self.test_llm_planning(query)
        else:
            print(f"Unknown scenario: {scenario}")
            print(f"Available: {list(scenarios.keys())}")
            return None


async def main():
    """Main test runner"""
    tester = TestAgentLLMPlanning()

    while True:
        print(f"\n{'='*60}")
        print("LLM Planning Test Menu")
        print(f"{'='*60}")
        print("1. Test all queries")
        print("2. Test single query (interactive)")
        print("3. Test specific scenario")
        print("4. Check execution logs")
        print("0. Exit")
        print("-"*60)

        choice = input("Select option: ").strip()

        if choice == "0":
            break

        elif choice == "1":
            await tester.test_all_queries()

        elif choice == "2":
            query = input("\nEnter query: ").strip()
            if query:
                await tester.test_llm_planning(query)
            else:
                print("Empty query")

        elif choice == "3":
            print("\nAvailable scenarios:")
            print("  simple - Simple query")
            print("  achievement - Achievement rate calculation")
            print("  trend - Trend analysis")
            print("  complex - Complex multi-step")
            print("  cross - Cross-database")

            scenario = input("\nSelect scenario: ").strip()
            await tester.test_specific_scenario(scenario)

        elif choice == "4":
            # Check execution logs
            try:
                with open("agent_execution_logs.jsonl", "r") as f:
                    lines = f.readlines()
                    print(f"\nExecution Logs ({len(lines)} entries)")

                    # Show last 5 entries
                    for line in lines[-5:]:
                        log = eval(line)
                        print(f"\nTimestamp: {log['timestamp']}")
                        print(f"Query: {log['query']}")
                        plan = log['plan']
                        print(f"Plan: Subgraphs={plan.get('use_subgraphs')}, Tools={plan.get('use_tools')}, SQL={plan.get('use_sql')}")
            except FileNotFoundError:
                print("No execution logs found")
            except Exception as e:
                print(f"Error reading logs: {e}")

        else:
            print("Invalid choice")

        if choice != "0":
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    print("Starting LLM Planning Tests...")
    print("This will test the new LLM-based planning in SalesAnalyticsAgent")
    asyncio.run(main())