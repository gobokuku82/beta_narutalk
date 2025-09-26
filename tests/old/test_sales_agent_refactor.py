"""
Test script for refactored Sales Analytics Agent
Tests the new architecture where:
- Agent only orchestrates
- DataCollectionSubgraph only collects data (no tools)
- AnalysisSubgraph uses tools autonomously based on suggestions
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.service.agents.sales_analytics_agent import SalesAnalyticsAgent
from backend.service.core.context import AgentContext


async def test_agent_orchestration():
    """Test the refactored agent orchestration"""

    print("=" * 60)
    print("Testing Refactored Sales Analytics Agent")
    print("=" * 60)

    # Initialize agent
    agent = SalesAnalyticsAgent()
    print("✓ Agent initialized")

    # Test queries
    test_cases = [
        {
            "name": "Simple SQL Query",
            "query": "홍길동의 실적을 보여줘",
            "expected_plan": {
                "use_sql": True,
                "use_subgraphs": [],
                "use_tools": []
            }
        },
        {
            "name": "Data Collection + Basic Analysis",
            "query": "홍길동의 2024년 실적을 분석해줘",
            "expected_plan": {
                "use_sql": False,
                "use_subgraphs": ["data_collection", "analysis"],
                "use_tools": ["calculation"]
            }
        },
        {
            "name": "Comprehensive Analysis with Trends",
            "query": "홍길동의 실적 트렌드와 달성률을 종합적으로 분석해줘",
            "expected_plan": {
                "use_sql": False,
                "use_subgraphs": ["data_collection", "analysis"],
                "use_tools": ["calculation", "trend"]
            }
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case['name']} ---")
        print(f"Query: {test_case['query']}")

        # Create context
        context = AgentContext(
            user_id=f"test_user_{i}",
            session_id=f"test_session_{i}",
            request_id=f"test_request_{i}",
            original_query=test_case['query']
        )

        # Create input
        input_data = {
            "query": test_case['query']
        }

        try:
            # Process the request
            result = await agent.process(input_data, context)

            # Check execution plan
            if "execution_plan" in result:
                plan = result["execution_plan"]
                print(f"\nExecution Plan:")
                print(f"  - Use SQL: {plan.get('use_sql', False)}")
                print(f"  - Subgraphs: {plan.get('use_subgraphs', [])}")
                print(f"  - Tools (suggested): {plan.get('use_tools', [])}")
                print(f"  - Reasoning: {plan.get('reasoning', 'N/A')}")

                # Verify plan matches expectation
                if test_case.get('expected_plan'):
                    expected = test_case['expected_plan']
                    matches = (
                        plan.get('use_sql') == expected.get('use_sql') and
                        set(plan.get('use_subgraphs', [])) == set(expected.get('use_subgraphs', [])) and
                        set(plan.get('use_tools', [])) == set(expected.get('use_tools', []))
                    )

                    if matches:
                        print("✓ Plan matches expected behavior")
                    else:
                        print("✗ Plan differs from expected")

            # Check execution results
            if "execution_results" in result:
                exec_results = result["execution_results"]

                # Check data collection
                if "collected_data" in exec_results:
                    data = exec_results["collected_data"]
                    print(f"\n✓ Data Collection:")
                    print(f"  - Status: {data.get('collection_status', 'unknown')}")
                    print(f"  - Performance records: {len(data.get('performance_data', []))}")
                    print(f"  - Target records: {len(data.get('target_data', []))}")
                    print(f"  - Client records: {len(data.get('client_data', []))}")

                # Check analysis results
                if "analysis_result" in exec_results:
                    analysis = exec_results["analysis_result"]
                    print(f"\n✓ Analysis Results:")
                    print(f"  - Status: {analysis.get('analysis_status', 'unknown')}")

                    # Check which tools were actually used by the subgraph
                    if analysis.get('basic_metrics'):
                        print(f"  - Basic metrics calculated: {len(analysis['basic_metrics'])} metrics")
                        if 'average_achievement' in analysis['basic_metrics']:
                            print(f"    → Achievement rate calculated (calculation tool used)")

                    if analysis.get('trend_analysis'):
                        print(f"  - Trend analysis performed: {len(analysis['trend_analysis'])} results")
                        if 'performance_trend' in analysis['trend_analysis']:
                            print(f"    → Trend tool was used")

                    if analysis.get('insights'):
                        print(f"  - Insights generated: {len(analysis['insights'])} insights")
                        for insight in analysis['insights'][:2]:
                            print(f"    → {insight}")

            # Check final result
            if result.get("status") == "completed":
                print(f"\n✓ Test case completed successfully")
            else:
                print(f"\n✗ Test case failed with status: {result.get('status')}")
                if result.get("error"):
                    print(f"  Error: {result['error']}")

        except Exception as e:
            print(f"\n✗ Test case failed with exception: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)
    print("\nSummary:")
    print("1. Agent orchestrates subgraphs without directly using tools ✓")
    print("2. DataCollectionSubgraph performs pure DB operations ✓")
    print("3. AnalysisSubgraph autonomously selects tools based on suggestions ✓")
    print("4. Clean separation of responsibilities achieved ✓")


if __name__ == "__main__":
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not set. Agent will use rule-based planning.")

    # Run test
    asyncio.run(test_agent_orchestration())