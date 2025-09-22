"""
LLM Integration 테스트 스크립트
실제 OpenAI API 호출을 통한 end-to-end 테스트
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 환경 변수 로드
load_dotenv()

# 색상 코드 (Windows 콘솔용)
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{'='*60}")
    print(f"{text}")
    print(f"{'='*60}{Colors.ENDC}")

def print_success(text):
    print(f"{Colors.GREEN}[OK] {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.RED}[ERROR] {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.BLUE}[INFO] {text}{Colors.ENDC}")

async def test_llm_manager():
    """LLM Manager 테스트"""
    print_header("1. LLM Manager 테스트")

    try:
        from backend.service.utils import LLMManager

        llm = LLMManager()
        print_success("LLM Manager 초기화 성공")

        # 간단한 테스트 쿼리
        response = await llm.generate(
            prompt="안녕하세요. 테스트입니다.",
            model="openai_mini",
            category="test"
        )

        if response and 'content' in response:
            print_success(f"LLM 응답: {response['content'][:50]}...")
            print_info(f"사용 토큰: {response['usage']['total_tokens']}")
        else:
            print_error("LLM 응답 실패")

        return True

    except Exception as e:
        print_error(f"LLM Manager 테스트 실패: {e}")
        return False

async def test_intent_analysis():
    """의도 분석 테스트"""
    print_header("2. Intent Analysis 테스트")

    try:
        from backend.service.orchestrator.intent_analysis import IntentAnalysisSubGraph

        analyzer = IntentAnalysisSubGraph()
        print_success("Intent Analyzer 초기화 성공")

        # 테스트 쿼리
        test_queries = [
            "지난 분기 서울 지역 매출 실적을 보여줘",
            "김영희 사원의 정보를 찾아줘",
            "리베이트 관련 규정을 확인해줘",
            "월간 실적 보고서를 작성해줘"
        ]

        for query in test_queries:
            print(f"\n테스트 쿼리: '{query}'")

            state = {
                "user_query": query,
                "tokens": [],
                "entities": [],
                "intents": [],
                "confidence_scores": {},
                "ambiguous": False
            }

            # classify_intent 메서드 직접 호출
            result = await analyzer.classify_intent(state)

            if result.get("intents"):
                for intent in result["intents"]:
                    print_success(f"  의도: {intent.get('type')} (신뢰도: {intent.get('confidence', 0):.2f})")
            else:
                print_info("  의도를 분류할 수 없음")

        return True

    except Exception as e:
        print_error(f"Intent Analysis 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_sales_analytics():
    """Sales Analytics Agent 테스트"""
    print_header("3. Sales Analytics Agent 테스트")

    try:
        from backend.service.agents.sales_analytics_agent import SalesAnalyticsAgent

        agent = SalesAnalyticsAgent()
        print_success("Sales Analytics Agent 초기화 성공")

        # 테스트 쿼리
        test_query = "지난달 서울 지역의 총 매출액을 알려줘"
        print(f"\n테스트 쿼리: '{test_query}'")

        # Text2SQL 테스트
        state = {
            "query": test_query,
            "sql_query": "",
            "query_results": [],
            "analysis": {},
            "visualization": {}
        }

        # parse_query 실행
        state = await agent.parse_sales_query(state)
        print_info(f"  추출된 기간: {state.get('period', 'N/A')}")
        print_info(f"  추출된 지역: {state.get('region', 'N/A')}")

        # text_to_sql 실행
        state = await agent.text_to_sql(state)
        if state.get("sql_query"):
            print_success(f"  생성된 SQL:\n    {state['sql_query'][:200]}...")
        else:
            print_error("  SQL 생성 실패")

        return True

    except Exception as e:
        print_error(f"Sales Analytics 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_full_orchestrator():
    """전체 오케스트레이터 테스트"""
    print_header("4. Full Orchestrator 테스트")

    try:
        from backend.service.orchestrator.orchestrator import MainOrchestrator

        orchestrator = MainOrchestrator()
        print_success("Main Orchestrator 초기화 성공")

        # 워크플로우 컴파일
        app = orchestrator.workflow.compile(
            checkpointer=orchestrator.checkpointer
        )
        print_success("워크플로우 컴파일 성공")

        # 테스트 입력
        test_input = {
            "user_id": "test_user_001",
            "session_id": f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "user_query": "지난 분기 서울 지역 거래처별 매출 실적을 분석해줘",
            "timestamp": datetime.now().isoformat()
        }

        print(f"\n테스트 입력:")
        print(f"  사용자: {test_input['user_id']}")
        print(f"  질의: {test_input['user_query']}")

        # 실행 (타임아웃 설정)
        try:
            result = await asyncio.wait_for(
                app.ainvoke(test_input),
                timeout=30.0
            )

            if result.get("final_response"):
                print_success(f"최종 응답: {result['final_response'][:100]}...")
            else:
                print_info("응답 생성 중...")

        except asyncio.TimeoutError:
            print_error("실행 타임아웃 (30초)")

        return True

    except Exception as e:
        print_error(f"Orchestrator 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_token_tracking():
    """토큰 추적 테스트"""
    print_header("5. Token Tracking 테스트")

    try:
        from backend.service.utils import TokenTracker

        tracker = TokenTracker()
        print_success("Token Tracker 초기화 성공")

        # 테스트 추적
        tracker.track(
            model="gpt-4o",
            prompt_tokens=100,
            completion_tokens=50,
            category="test",
            user_id="test_user"
        )

        stats = tracker.get_current_stats()
        print_info(f"총 토큰 사용: {stats['tokens']['total']}")
        print_info(f"예상 비용: ${stats['cost']['total_usd']:.4f}")

        return True

    except Exception as e:
        print_error(f"Token Tracking 테스트 실패: {e}")
        return False

async def interactive_test():
    """대화형 테스트 모드"""
    print_header("대화형 테스트 모드")
    print("종료하려면 'exit' 입력\n")

    from backend.service.utils import LLMManager, TokenTracker

    llm = LLMManager()
    tracker = TokenTracker()

    while True:
        query = input(f"{Colors.YELLOW}질의 입력: {Colors.ENDC}").strip()

        if query.lower() == 'exit':
            break

        try:
            # LLM 호출
            response = await llm.generate(
                prompt=query,
                model="openai_mini",
                category="interactive_test"
            )

            print(f"{Colors.GREEN}응답:{Colors.ENDC} {response['content']}")
            print(f"{Colors.BLUE}토큰:{Colors.ENDC} {response['usage']['total_tokens']}")

            # 토큰 추적
            tracker.track(
                model="gpt-4o-mini",
                prompt_tokens=response['usage']['prompt_tokens'],
                completion_tokens=response['usage']['completion_tokens'],
                category="interactive"
            )

        except Exception as e:
            print_error(f"오류: {e}")

    # 최종 통계
    stats = tracker.get_current_stats()
    print_header("세션 통계")
    print(f"총 요청: {len(tracker.usage_history)}")
    print(f"총 토큰: {stats['tokens']['total']}")
    print(f"예상 비용: ${stats['cost']['total_usd']:.4f}")

async def main():
    """메인 테스트 실행"""
    print_header("NaruTalk LLM Integration Test Suite")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # API Key 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print_error("OPENAI_API_KEY not found!")
        return

    print_success(f"API Key found: ...{api_key[-8:]}")

    # 메뉴 표시
    while True:
        print_header("Test Menu")
        print("1. LLM Manager Test")
        print("2. Intent Analysis Test")
        print("3. Sales Analytics Test")
        print("4. Full Orchestrator Test")
        print("5. Token Tracking Test")
        print("6. Interactive Test Mode")
        print("7. Run All Tests")
        print("0. Exit")

        choice = input(f"\n{Colors.YELLOW}Select: {Colors.ENDC}").strip()

        if choice == "0":
            break
        elif choice == "1":
            await test_llm_manager()
        elif choice == "2":
            await test_intent_analysis()
        elif choice == "3":
            await test_sales_analytics()
        elif choice == "4":
            await test_full_orchestrator()
        elif choice == "5":
            await test_token_tracking()
        elif choice == "6":
            await interactive_test()
        elif choice == "7":
            # 전체 테스트
            results = []
            results.append(("LLM Manager", await test_llm_manager()))
            results.append(("Intent Analysis", await test_intent_analysis()))
            results.append(("Sales Analytics", await test_sales_analytics()))
            results.append(("Full Orchestrator", await test_full_orchestrator()))
            results.append(("Token Tracking", await test_token_tracking()))

            print_header("Test Results Summary")
            for name, success in results:
                if success:
                    print_success(f"{name}: PASS")
                else:
                    print_error(f"{name}: FAIL")
        else:
            print_error("Invalid selection")

        input(f"\n{Colors.BLUE}Press Enter to continue...{Colors.ENDC}")

    print_header("Test Complete")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    # Windows 콘솔 색상 활성화
    if sys.platform == "win32":
        os.system("color")

    # 비동기 실행
    asyncio.run(main())