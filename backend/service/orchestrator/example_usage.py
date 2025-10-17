"""
Example Usage of Orchestrator
오케스트레이터 사용 예제
"""

import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')

from .factory import (
    create_workflow_instance,
    run_workflow,
    create_streaming_workflow,
    quick_run
)
from ..supervisor.supervisor_state import create_supervisor_initial_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_basic_usage():
    """
    Example: Basic workflow usage
    기본적인 워크플로우 사용 예제
    """
    print("\n=== Example 1: Basic Usage ===\n")

    # Simple query
    query = "김철수의 2024년 실적을 분석해주세요"
    session_id = "session_001"

    # Run workflow
    result = await run_workflow(
        user_query=query,
        session_id=session_id,
        user_id="user_123"
    )

    print(f"Query: {result['query']}")
    print(f"Status: {result['status']}")
    print(f"Answer: {result['answer']}")
    print(f"Execution trace: {len(result['execution_trace'])} steps")


async def example_streaming_usage():
    """
    Example: Streaming workflow
    스트리밍 방식 워크플로우 예제
    """
    print("\n=== Example 2: Streaming Usage ===\n")

    query = "전체 영업실적 추세를 분석해주세요"
    session_id = "session_002"

    # Create streaming workflow
    stream = create_streaming_workflow(
        user_query=query,
        session_id=session_id,
        user_id="user_456"
    )

    # Process stream
    async for update in stream:
        if update["type"] == "state_update":
            # Get node name from update
            node_names = list(update["data"].keys())
            if node_names:
                print(f"Processing: {node_names[-1]}")
        elif update["type"] == "error":
            print(f"Error: {update['error']}")


async def example_custom_orchestrator():
    """
    Example: Custom orchestrator configuration
    커스텀 오케스트레이터 설정 예제
    """
    print("\n=== Example 3: Custom Orchestrator ===\n")

    # Create custom orchestrator
    orchestrator = create_workflow_instance(
        supervisor_model="gpt-4o",
        supervisor_temperature=0.1,  # Lower temperature for more deterministic results
        config={
            "enable_caching": True,
            "max_retries": 3
        }
    )

    query = "거래처별 실적 비교 분석"
    session_id = "session_003"

    # Run with custom orchestrator
    result = await run_workflow(
        user_query=query,
        session_id=session_id,
        orchestrator=orchestrator
    )

    print(f"Answer: {result.get('answer', 'No answer')}")


def example_quick_run():
    """
    Example: Quick synchronous run (for testing)
    빠른 동기식 실행 예제 (테스트용)
    """
    print("\n=== Example 4: Quick Run ===\n")

    query = "이번달 목표 달성률은?"

    # Quick run (blocks until complete)
    result = quick_run(query)

    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Answer: {result.get('answer')}")
    else:
        print(f"Error: {result.get('error')}")


async def example_complex_query():
    """
    Example: Complex multi-step query
    복잡한 다단계 질의 예제
    """
    print("\n=== Example 5: Complex Query ===\n")

    query = """
    2024년 전체 영업실적을 분석하고, 다음을 포함해주세요:
    1. 월별 실적 추이
    2. 담당자별 성과 비교
    3. 목표 대비 달성률
    4. 주요 인사이트 및 개선점
    """
    session_id = "session_005"

    result = await run_workflow(
        user_query=query,
        session_id=session_id,
        user_id="manager_001",
        metadata={
            "department": "sales",
            "role": "manager"
        }
    )

    print(f"Query: {query[:50]}...")
    print(f"\nFinal Report:")
    if result.get('report'):
        report = result['report']
        print(f"- Data sources: {report.get('data', {}).keys()}")
        print(f"- Analysis types: {report.get('analysis', {}).keys()}")
        print(f"- Insights count: {len(report.get('insights', []))}")
        print(f"\nAnswer preview: {result['answer'][:200]}...")


async def example_with_error_handling():
    """
    Example: Error handling
    에러 처리 예제
    """
    print("\n=== Example 6: Error Handling ===\n")

    # Invalid query (empty)
    query = ""
    session_id = "session_006"

    try:
        result = await run_workflow(
            user_query=query,
            session_id=session_id
        )

        if not result['success']:
            print(f"Workflow failed: {result.get('error')}")
            print(f"Errors: {result.get('errors', [])}")
        else:
            print("Workflow succeeded (unexpected)")

    except Exception as e:
        print(f"Exception caught: {e}")


async def run_all_examples():
    """Run all examples"""
    print("=" * 60)
    print("Orchestrator Usage Examples")
    print("=" * 60)

    await example_basic_usage()
    await example_streaming_usage()
    await example_custom_orchestrator()
    example_quick_run()
    await example_complex_query()
    await example_with_error_handling()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Run all examples
    asyncio.run(run_all_examples())
