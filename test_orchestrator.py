"""
오케스트레이터 임포트 테스트
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_orchestrator_import():
    """오케스트레이터 임포트 및 초기화 테스트"""

    print("=" * 60)
    print("오케스트레이터 테스트 시작")
    print("=" * 60)

    # 1. Import 테스트
    print("\n1. Import 테스트...")
    try:
        from backend.service.orchestrator.orchestrator import MainOrchestrator
        print("✓ MainOrchestrator import 성공")
    except ImportError as e:
        print(f"✗ MainOrchestrator import 실패: {e}")
        return False

    # 2. 초기화 테스트
    print("\n2. MainOrchestrator 초기화 테스트...")
    try:
        # checkpointer 디렉토리 생성
        checkpointer_dir = Path("database/checkpointer")
        checkpointer_dir.mkdir(parents=True, exist_ok=True)

        orchestrator = MainOrchestrator()
        print("✓ MainOrchestrator 초기화 성공")
    except Exception as e:
        print(f"✗ MainOrchestrator 초기화 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 3. 워크플로우 컴파일 테스트
    print("\n3. 워크플로우 컴파일 테스트...")
    try:
        app = orchestrator.workflow.compile(
            checkpointer=orchestrator.checkpointer
        )
        print("✓ 워크플로우 컴파일 성공")
    except Exception as e:
        print(f"✗ 워크플로우 컴파일 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 4. 그래프 구조 확인
    print("\n4. 그래프 구조 확인...")
    try:
        nodes = orchestrator.workflow.nodes
        print(f"✓ 노드 개수: {len(nodes)}")
        print("✓ 노드 목록:")
        for node in list(nodes.keys())[:10]:  # 처음 10개만 출력
            print(f"  - {node}")
    except Exception as e:
        print(f"✗ 그래프 구조 확인 실패: {e}")

    print("\n" + "=" * 60)
    print("✅ 오케스트레이터 테스트 완료!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    # 환경 변수 로드
    from dotenv import load_dotenv
    load_dotenv()

    success = test_orchestrator_import()
    if not success:
        sys.exit(1)