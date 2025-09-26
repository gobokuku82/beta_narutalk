"""
Simple test script for chatbot functionality
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import logging

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_query(query: str):
    """단일 쿼리 테스트"""
    from backend.service.orchestrator.orchestrator import MainOrchestrator

    print(f"\n테스트 쿼리: {query}")
    print("=" * 60)

    try:
        # 오케스트레이터 초기화
        orchestrator = MainOrchestrator()
        app = orchestrator.workflow.compile()

        # 입력 상태 준비
        state = {
            "user_id": "test_user",
            "session_id": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "user_query": query,
            "timestamp": datetime.now().isoformat()
        }

        print("처리 중...")

        # 오케스트레이터 실행
        result = await asyncio.wait_for(
            app.ainvoke(state),
            timeout=30.0
        )

        # 결과 출력
        print(f"\n결과:")
        print(f"- 의도: {result.get('intents', [])}")
        print(f"- 실행 계획: {result.get('execution_plan', {}).get('agents', [])}")
        print(f"- 에이전트 결과: {list(result.get('agent_results', {}).keys())}")
        print(f"- 응답: {result.get('final_response', '응답 없음')[:200]}")
        print(f"- 오류: {result.get('error_logs', [])}")

        return True

    except asyncio.TimeoutError:
        print("ERROR: 응답 시간 초과 (30초)")
        return False

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """메인 함수"""
    print("NaruTalk 챗봇 테스트")
    print("=" * 60)

    # 테스트 쿼리들
    test_queries = [
        "최시우 실적 분석해줘",
        # "지난달 서울 지역 매출 분석해줘",
        # "김영희 사원의 정보를 찾아줘"
    ]

    results = []
    for query in test_queries:
        success = await test_query(query)
        results.append((query, success))
        await asyncio.sleep(1)  # 요청 간 간격

    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약:")
    for query, success in results:
        status = "[성공]" if success else "[실패]"
        print(f"{status} {query}")

    success_count = sum(1 for _, s in results if s)
    print(f"\n전체: {success_count}/{len(results)} 성공")

if __name__ == "__main__":
    asyncio.run(main())