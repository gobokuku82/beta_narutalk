"""
Test file for agents with Context API
"""

import asyncio
import logging
from datetime import datetime
from backend.service.agents import SearchAgent
from backend.service.core import create_context

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_search_agent():
    """Test SearchAgent with Context API"""
    print("\n" + "="*50)
    print("Testing SearchAgent with Context API")
    print("="*50)

    try:
        # Initialize agent
        agent = SearchAgent()
        print("[OK] SearchAgent initialized")

        # Prepare test input
        test_input = {
            "query": "최시우 실적 분석",
            "user_id": "test_user_001",
            "session_id": "test_session_001",
            "metadata": {
                "request_source": "test",
                "priority": "high"
            }
        }

        print(f"\n[Test Input]")
        print(f"  - Query: {test_input['query']}")
        print(f"  - User ID: {test_input['user_id']}")
        print(f"  - Session ID: {test_input['session_id']}")

        # Execute agent
        print(f"\n[Executing agent...]")
        result = await agent.execute(test_input)

        # Check result
        if result["status"] == "success":
            print(f"\n[SUCCESS] Agent execution successful!")

            # Get the state data
            state_data = result.get("data", {})

            print(f"\n[Results]")
            print(f"  - Status: {state_data.get('status', 'N/A')}")
            print(f"  - Execution Step: {state_data.get('execution_step', 'N/A')}")

            # Check final results
            final_results = state_data.get("final_results", {})
            if final_results:
                print(f"  - Total Results: {final_results.get('total_results', 0)}")
                print(f"  - Sources: {final_results.get('sources', [])}")

                # Show sample results
                results = final_results.get("results", [])
                if results:
                    print(f"\n  Sample Results (first 2):")
                    for i, res in enumerate(results[:2], 1):
                        print(f"    {i}. Type: {res.get('type', 'N/A')}, Score: {res.get('relevance_score', 0)}")
        else:
            print(f"\n[FAILED] Agent execution failed!")
            print(f"  Error: {result.get('error', 'Unknown error')}")

        return result

    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        logger.error(f"Test failed: {e}", exc_info=True)
        return None


async def test_context_creation():
    """Test Context creation and usage"""
    print("\n" + "="*50)
    print("Testing Context Creation")
    print("="*50)

    # Create different types of contexts
    base_context = create_context(
        user_id="user_001",
        session_id="session_001",
        context_type="base"
    )
    print(f"[OK] Base Context created: {base_context.request_id}")

    agent_context = create_context(
        user_id="user_002",
        session_id="session_002",
        context_type="agent",
        agent_name="SearchAgent",
        timeout=20
    )
    print(f"[OK] Agent Context created: {agent_context.agent_name} with timeout {agent_context.timeout}s")

    orchestrator_context = create_context(
        user_id="user_003",
        session_id="session_003",
        context_type="orchestrator",
        execution_mode="parallel",
        total_timeout=60
    )
    print(f"[OK] Orchestrator Context created: mode={orchestrator_context.execution_mode}")

    # Test error tracking
    agent_context.add_error("Test error 1")
    agent_context.add_error("Test error 2")
    print(f"\n[OK] Error tracking: {len(agent_context.error_logs)} errors logged")
    for error in agent_context.error_logs:
        print(f"  - {error}")


async def main():
    """Main test function"""
    print("\n" + "="*60)
    print(" Agent Testing with Context API ".center(60))
    print("="*60)
    print(f"Started at: {datetime.now().isoformat()}")

    # Test Context creation
    await test_context_creation()

    # Test SearchAgent
    result = await test_search_agent()

    print("\n" + "="*60)
    print(" Test Complete ".center(60))
    print("="*60)

    # Summary
    if result and result["status"] == "success":
        print("\n[SUCCESS] All tests passed!")
    else:
        print("\n[WARNING] Some tests failed. Check the logs above.")


if __name__ == "__main__":
    asyncio.run(main())