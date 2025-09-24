"""
Debug test to find exactly where the timeout occurs
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_with_detailed_logging():
    from backend.service.orchestrator.orchestrator import MainOrchestrator
    import time

    orchestrator = MainOrchestrator()

    # 각 노드에 실행 시간 추적을 위한 래퍼 추가
    original_nodes = {}
    for node_name in orchestrator.workflow.nodes:
        original_nodes[node_name] = orchestrator.workflow.nodes[node_name]

    def create_logged_node(name, func):
        async def logged_func(state):
            print(f"\n>>> ENTERING NODE: {name}")
            start = time.time()
            try:
                result = await func(state)
                elapsed = time.time() - start
                print(f"<<< EXITING NODE: {name} (took {elapsed:.2f}s)")
                return result
            except Exception as e:
                print(f"!!! ERROR IN NODE: {name} - {e}")
                raise
        return logged_func

    # 모든 노드를 로깅 버전으로 교체
    for node_name, node_func in original_nodes.items():
        if callable(node_func):
            orchestrator.workflow.nodes[node_name] = create_logged_node(node_name, node_func)

    app = orchestrator.workflow.compile()

    state = {
        "user_id": "test",
        "session_id": "test",
        "user_query": "최시우 실적",
        "timestamp": "2024-01-01"
    }

    print("=" * 60)
    print("Starting workflow execution...")
    print("=" * 60)

    try:
        # 더 짧은 타임아웃으로 테스트
        result = await asyncio.wait_for(
            app.ainvoke(state),
            timeout=15.0
        )
        print("\n✅ SUCCESS!")
        return True
    except asyncio.TimeoutError:
        print(f"\n❌ TIMEOUT after 15s - Check which node was last entered")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_individual_subgraphs():
    """각 서브그래프를 개별적으로 테스트"""
    print("\n" + "=" * 60)
    print("Testing Individual Subgraphs")
    print("=" * 60)

    # 1. Intent Analysis 테스트
    print("\n1. Testing IntentAnalysisSubGraph...")
    try:
        from backend.service.orchestrator.intent_analysis import IntentAnalysisSubGraph
        intent_analyzer = IntentAnalysisSubGraph()
        app = intent_analyzer.workflow.compile()

        state = {
            "user_query": "최시우 실적",
            "tokens": [],
            "entities": [],
            "intents": []
        }

        result = await asyncio.wait_for(app.ainvoke(state), timeout=5.0)
        print(f"   ✅ IntentAnalysis completed: {result.get('intents', [])}")
    except asyncio.TimeoutError:
        print("   ❌ IntentAnalysis TIMEOUT")
    except Exception as e:
        print(f"   ❌ IntentAnalysis ERROR: {e}")

    # 2. Planning 테스트
    print("\n2. Testing PlanningSubGraph...")
    try:
        from backend.service.orchestrator.planning import PlanningSubGraph
        planner = PlanningSubGraph()
        app = planner.workflow.compile()

        state = {
            "intents": [{"type": "internal_search", "confidence": 0.5}],
            "execution_steps": [],
            "agent_sequence": []
        }

        result = await asyncio.wait_for(app.ainvoke(state), timeout=5.0)
        print(f"   ✅ Planning completed: {len(result.get('execution_steps', []))} steps")
    except asyncio.TimeoutError:
        print("   ❌ Planning TIMEOUT")
    except Exception as e:
        print(f"   ❌ Planning ERROR: {e}")

    # 3. Result Evaluation 테스트
    print("\n3. Testing ResultEvaluationSubGraph...")
    try:
        from backend.service.orchestrator.result_evaluation import ResultEvaluationSubGraph
        evaluator = ResultEvaluationSubGraph()
        app = evaluator.workflow.compile()

        state = {
            "raw_results": {"test": "data"},
            "quality_scores": {},
            "compliance_status": {}
        }

        result = await asyncio.wait_for(app.ainvoke(state), timeout=5.0)
        print(f"   ✅ Evaluation completed")
    except asyncio.TimeoutError:
        print("   ❌ Evaluation TIMEOUT")
    except Exception as e:
        print(f"   ❌ Evaluation ERROR: {e}")

    # 4. Response Generation 테스트
    print("\n4. Testing ResponseGenerationSubGraph...")
    try:
        from backend.service.orchestrator.response_generation import ResponseGenerationSubGraph
        generator = ResponseGenerationSubGraph()
        app = generator.workflow.compile()

        state = {
            "validated_results": {"test": "data"},
            "response_format": "text",
            "formatted_response": ""
        }

        result = await asyncio.wait_for(app.ainvoke(state), timeout=5.0)
        print(f"   ✅ Response generation completed")
    except asyncio.TimeoutError:
        print("   ❌ Response generation TIMEOUT")
    except Exception as e:
        print(f"   ❌ Response generation ERROR: {e}")

async def main():
    # 1. 전체 워크플로우 디버그
    print("Test 1: Full workflow with detailed logging")
    await test_with_detailed_logging()

    # 2. 개별 서브그래프 테스트
    print("\nTest 2: Individual subgraphs")
    await test_individual_subgraphs()

if __name__ == "__main__":
    asyncio.run(main())