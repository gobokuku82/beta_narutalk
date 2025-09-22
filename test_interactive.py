"""
대화형 챗봇 테스트
실제 사용자 질문에 대한 응답 테스트
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import os

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 환경 변수 로드
load_dotenv()

# 색상 코드
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RED = '\033[91m'
    ENDC = '\033[0m'

async def chat_with_bot():
    """챗봇과 대화"""
    from backend.service.orchestrator.orchestrator import MainOrchestrator

    print(f"{Colors.GREEN}=" * 60)
    print("NaruTalk 챗봇 대화 모드")
    print(f"=" * 60 + Colors.ENDC)
    print(f"{Colors.BLUE}[INFO] 종료하려면 'exit' 또는 '종료' 입력{Colors.ENDC}\n")

    # 오케스트레이터 초기화
    orchestrator = MainOrchestrator()
    app = orchestrator.workflow.compile()

    session_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    user_id = "user_001"
    conversation_history = []

    print(f"{Colors.GREEN}챗봇 준비 완료!{Colors.ENDC}\n")
    print("예시 질문:")
    print("- 지난달 서울 지역 매출 분석해줘")
    print("- 김영희 사원의 정보를 찾아줘")
    print("- 리베이트 관련 규정 확인해줘")
    print("- 올해 실적 보고서 작성해줘\n")

    while True:
        # 사용자 입력
        user_input = input(f"{Colors.YELLOW}질문> {Colors.ENDC}").strip()

        if user_input.lower() in ['exit', '종료', 'quit']:
            print(f"{Colors.BLUE}대화를 종료합니다. 감사합니다!{Colors.ENDC}")
            break

        if not user_input:
            continue

        # 입력 상태 준비
        state = {
            "user_id": user_id,
            "session_id": session_id,
            "user_query": user_input,
            "timestamp": datetime.now().isoformat(),
            "conversation_history": conversation_history
        }

        print(f"{Colors.BLUE}[처리중...]{Colors.ENDC}")

        try:
            # 오케스트레이터 실행 (타임아웃 30초)
            result = await asyncio.wait_for(
                app.ainvoke(state),
                timeout=30.0
            )

            # 응답 출력
            response = result.get("final_response", "죄송합니다. 응답을 생성할 수 없습니다.")

            print(f"\n{Colors.GREEN}답변> {Colors.ENDC}{response}\n")

            # 추가 정보 표시 (옵션)
            if result.get("intents"):
                intents = [i.get('type', 'unknown') for i in result['intents']]
                print(f"{Colors.BLUE}[의도: {', '.join(intents)}]{Colors.ENDC}")

            if result.get("agent_results"):
                agents = list(result['agent_results'].keys())
                if agents:
                    print(f"{Colors.BLUE}[사용된 에이전트: {', '.join(agents)}]{Colors.ENDC}")

            if result.get("error_logs"):
                print(f"{Colors.RED}[오류: {', '.join(result['error_logs'][:2])}]{Colors.ENDC}")

            # 대화 기록 저장
            conversation_history.append({
                "user": user_input,
                "assistant": response,
                "timestamp": datetime.now().isoformat()
            })

            print("-" * 60)

        except asyncio.TimeoutError:
            print(f"{Colors.RED}[ERROR] 응답 시간 초과 (30초){Colors.ENDC}\n")
        except Exception as e:
            print(f"{Colors.RED}[ERROR] 오류 발생: {e}{Colors.ENDC}\n")

    # 대화 요약
    print(f"\n{Colors.GREEN}대화 요약:{Colors.ENDC}")
    print(f"총 {len(conversation_history)}개 대화")

async def test_specific_queries():
    """특정 쿼리 테스트"""
    from backend.service.orchestrator.orchestrator import MainOrchestrator

    print(f"{Colors.GREEN}=" * 60)
    print("특정 쿼리 테스트")
    print(f"=" * 60 + Colors.ENDC)

    orchestrator = MainOrchestrator()
    app = orchestrator.workflow.compile()

    # 테스트할 쿼리들
    test_queries = [
        "지난달 서울 지역 총 매출액은?",
        "이번 분기 실적 분석 보고서 작성해줘",
        "리베이트 규정 위반 사항 확인해줘",
        "김영희 사원의 연락처 알려줘"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{Colors.YELLOW}테스트 {i}: {query}{Colors.ENDC}")

        state = {
            "user_id": "test_user",
            "session_id": f"test_{i}",
            "user_query": query,
            "timestamp": datetime.now().isoformat()
        }

        try:
            result = await asyncio.wait_for(
                app.ainvoke(state),
                timeout=20.0
            )

            response = result.get("final_response", "응답 없음")
            print(f"{Colors.GREEN}응답:{Colors.ENDC} {response[:200]}...")

            if result.get("intents"):
                intents = [i.get('type', 'unknown') for i in result['intents']]
                print(f"{Colors.BLUE}의도: {intents}{Colors.ENDC}")

        except Exception as e:
            print(f"{Colors.RED}오류: {e}{Colors.ENDC}")

def check_database_status():
    """데이터베이스 연결 상태 확인"""
    print(f"\n{Colors.GREEN}=" * 60)
    print("데이터베이스 상태 확인")
    print(f"=" * 60 + Colors.ENDC)

    import os
    from pathlib import Path

    # 데이터베이스 경로들
    db_paths = {
        "HR DB": os.getenv("HR_DB_PATH", "./database/storage/hr_information/hr_data.db"),
        "Clients DB": os.getenv("CLIENTS_DB_PATH", "./database/storage/sales_performance/clients_db.db"),
        "Sales Performance": os.getenv("SALES_PERFORMANCE_PATH", "./database/storage/sales_performance/sales_performance_db.db"),
        "Sales Target": os.getenv("SALES_TARGET_PATH", "./database/storage/sales_performance/sales_target_db.db"),
    }

    print("\n데이터베이스 파일 상태:")
    for name, path in db_paths.items():
        if Path(path).exists():
            size = Path(path).stat().st_size / 1024  # KB
            print(f"  ✓ {name}: {path} ({size:.1f} KB)")
        else:
            print(f"  ✗ {name}: {path} (파일 없음)")

    # ChromaDB 경로
    chroma_paths = {
        "HR Rules": os.getenv("HR_RULES_CHROMA_PATH", "./database/storage/hr_rules/chromadb"),
        "Compliance": os.getenv("COMPLIANCE_CHROMA_PATH", "./database/storage/rules_compliance/chroma_db")
    }

    print("\nChromaDB 상태:")
    for name, path in chroma_paths.items():
        if Path(path).exists():
            print(f"  ✓ {name}: {path}")
        else:
            print(f"  ✗ {name}: {path} (디렉토리 없음)")

async def main():
    """메인 메뉴"""
    # Windows 콘솔 색상 활성화
    if sys.platform == "win32":
        os.system("color")

    while True:
        print(f"\n{Colors.GREEN}=" * 60)
        print("NaruTalk 대화형 테스트")
        print(f"=" * 60 + Colors.ENDC)
        print("\n1. 챗봇과 대화하기")
        print("2. 특정 쿼리 테스트")
        print("3. 데이터베이스 상태 확인")
        print("0. 종료")

        choice = input(f"\n{Colors.YELLOW}선택> {Colors.ENDC}").strip()

        if choice == "0":
            break
        elif choice == "1":
            await chat_with_bot()
        elif choice == "2":
            await test_specific_queries()
        elif choice == "3":
            check_database_status()
        else:
            print(f"{Colors.RED}잘못된 선택{Colors.ENDC}")

    print(f"\n{Colors.GREEN}프로그램을 종료합니다.{Colors.ENDC}")

if __name__ == "__main__":
    asyncio.run(main())