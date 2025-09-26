"""
Full Orchestrator 테스트
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 환경 변수 로드
load_dotenv()

async def test_full_orchestrator():
    """전체 오케스트레이터 테스트"""
    print("=" * 60)
    print("Full Orchestrator Test")
    print("=" * 60)

    try:
        from backend.service.orchestrator.orchestrator import MainOrchestrator

        print("[INFO] Initializing MainOrchestrator...")
        orchestrator = MainOrchestrator()
        print("[OK] MainOrchestrator initialized")

        # 워크플로우 컴파일 (checkpointer 없이)
        print("[INFO] Compiling workflow...")
        app = orchestrator.workflow.compile()
        print("[OK] Workflow compiled")

        # 테스트 입력
        test_input = {
            "user_id": "test_user_001",
            "session_id": f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "user_query": "지난 분기 서울 지역 매출 분석해줘",
            "timestamp": datetime.now().isoformat()
        }

        print(f"\n[INFO] Test Input:")
        print(f"  User: {test_input['user_id']}")
        print(f"  Query: {test_input['user_query']}")
        print(f"  Session: {test_input['session_id']}")

        # 실행
        print("\n[INFO] Executing workflow...")
        try:
            # Checkpointer 없이 실행
            result = await asyncio.wait_for(
                app.ainvoke(test_input),
                timeout=30.0
            )

            print("\n[OK] Workflow executed successfully")

            # 결과 출력
            print("\n[INFO] Results:")
            print(f"  Intents: {result.get('intents', [])}")
            print(f"  Execution Plan: {bool(result.get('execution_plan'))}")
            print(f"  Agent Results: {bool(result.get('agent_results'))}")
            print(f"  Validated Results: {bool(result.get('validated_results'))}")
            print(f"  Final Response: {result.get('final_response', 'N/A')[:100]}...")

            if result.get("error_logs"):
                print(f"\n[WARNING] Errors occurred:")
                for error in result["error_logs"]:
                    print(f"  - {error}")

            return True

        except asyncio.TimeoutError:
            print("[ERROR] Workflow execution timeout (30s)")
            return False

    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    success = await test_full_orchestrator()

    print("\n" + "=" * 60)
    if success:
        print("[SUCCESS] Full Orchestrator test PASSED")
    else:
        print("[FAIL] Full Orchestrator test FAILED")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())