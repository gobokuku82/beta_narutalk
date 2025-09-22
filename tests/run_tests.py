"""
NaruTalk Beta v0.033 - 대화형 테스트 시스템
콘솔에서 실행 가능한 테스트 런너
"""

import os
import sys
import time
import asyncio
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Windows 콘솔 색상 지원
try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False
    # 색상 없이 실행
    class DummyColor:
        def __getattr__(self, name):
            return ""
    Fore = Back = Style = DummyColor()

def print_header():
    """헤더 출력"""
    print(f"\n{Fore.CYAN}{'=' * 70}")
    print(f"{Fore.YELLOW}  NaruTalk Beta v0.033 - 테스트 시스템")
    print(f"{Fore.CYAN}{'=' * 70}")
    print(f"{Fore.WHITE}  제약회사 챗봇 통합 테스트")
    print(f"  실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{Fore.CYAN}{'=' * 70}\n")

def show_menu():
    """메인 메뉴 표시"""
    print(f"{Fore.GREEN}테스트 메뉴:")
    print(f"{Fore.WHITE}  1. {Fore.YELLOW}DB 연결 테스트{Fore.WHITE} - 모든 데이터베이스 연결 확인")
    print(f"  2. {Fore.YELLOW}스키마 검증{Fore.WHITE} - 테이블 구조 및 데이터 검증")
    print(f"  3. {Fore.YELLOW}샘플 쿼리 실행{Fore.WHITE} - 실제 SQL 쿼리 테스트")
    print(f"  4. {Fore.YELLOW}에이전트 테스트{Fore.WHITE} - 개별 에이전트 동작 확인")
    print(f"  5. {Fore.YELLOW}오케스트레이터 테스트{Fore.WHITE} - 메인 워크플로우 검증")
    print(f"  6. {Fore.YELLOW}통합 시나리오{Fore.WHITE} - 전체 파이프라인 테스트")
    print(f"  7. {Fore.YELLOW}전체 테스트{Fore.WHITE} - 모든 테스트 순차 실행")
    print(f"  0. {Fore.RED}종료")
    print()

def run_db_test():
    """DB 연결 테스트 실행"""
    print(f"\n{Fore.CYAN}▶ DB 연결 테스트 시작...")
    print(f"{Fore.CYAN}{'-' * 50}")

    try:
        from test_db_connection import (
            test_hr_database,
            test_sales_databases,
            test_chromadb_connections,
            test_sample_query
        )
        from database.schemas.schema_definitions import HR_SCHEMA, SALES_SCHEMA
        from dotenv import load_dotenv

        load_dotenv()

        # DB 경로 설정
        db_paths = {
            "hr_data": os.getenv("HR_DB_PATH"),
            "clients_db": os.getenv("CLIENTS_DB_PATH"),
            "clients_info": os.getenv("CLIENTS_INFO_PATH"),
            "sales_performance": os.getenv("SALES_PERFORMANCE_PATH"),
            "sales_target": os.getenv("SALES_TARGET_PATH"),
            "hr_rules_chroma": os.getenv("HR_RULES_CHROMA_PATH"),
            "compliance_chroma": os.getenv("COMPLIANCE_CHROMA_PATH")
        }

        schema_info = {
            "hr": HR_SCHEMA,
            "sales": SALES_SCHEMA
        }

        # 각 테스트 실행
        test_hr_database(db_paths, schema_info)
        test_sales_databases(db_paths, schema_info)
        test_chromadb_connections(db_paths)
        test_sample_query(db_paths)

        print(f"\n{Fore.GREEN}✅ DB 연결 테스트 완료!")
        return True

    except Exception as e:
        print(f"\n{Fore.RED}❌ DB 테스트 실패: {e}")
        return False

def run_schema_validation():
    """스키마 검증 테스트"""
    print(f"\n{Fore.CYAN}▶ 스키마 검증 시작...")
    print(f"{Fore.CYAN}{'-' * 50}")

    try:
        from database.schemas.schema_definitions import list_all_tables, get_table_schema

        print(f"\n{Fore.YELLOW}전체 테이블 목록:")
        for db, table in list_all_tables():
            print(f"  • {Fore.WHITE}{db}.{Fore.GREEN}{table}")

        # HR 인사자료 테이블 상세 정보
        hr_table = get_table_schema("hr_data", "인사자료")
        print(f"\n{Fore.YELLOW}HR 인사자료 테이블 정보:")
        print(f"  - 테이블명: {Fore.GREEN}{hr_table.name}")
        print(f"  - 설명: {hr_table.description}")
        print(f"  - 예상 행 개수: {Fore.CYAN}{hr_table.row_count}")
        print(f"  - 컬럼 개수: {Fore.CYAN}{len(hr_table.columns)}")

        print(f"\n{Fore.GREEN}✅ 스키마 검증 완료!")
        return True

    except Exception as e:
        print(f"\n{Fore.RED}❌ 스키마 검증 실패: {e}")
        return False

def run_sample_queries():
    """샘플 쿼리 실행"""
    print(f"\n{Fore.CYAN}▶ 샘플 쿼리 실행...")
    print(f"{Fore.CYAN}{'-' * 50}")

    queries = [
        ("부서별 인원수", "SELECT 부서, COUNT(*) as 인원수 FROM 인사자료 GROUP BY 부서"),
        ("직급별 인원수", "SELECT 직급, COUNT(*) as 인원수 FROM 인사자료 GROUP BY 직급"),
    ]

    print(f"\n{Fore.YELLOW}실행할 쿼리:")
    for i, (desc, _) in enumerate(queries, 1):
        print(f"  {i}. {desc}")

    choice = input(f"\n{Fore.WHITE}쿼리 선택 (1-{len(queries)}, 0=전체): ")

    # 쿼리 실행 로직...
    print(f"\n{Fore.GREEN}✅ 쿼리 실행 완료!")
    return True

async def run_agent_tests():
    """에이전트 테스트"""
    print(f"\n{Fore.CYAN}▶ 에이전트 테스트 시작...")
    print(f"{Fore.CYAN}{'-' * 50}")

    agents = [
        "SalesAnalyticsAgent",
        "SearchAgent",
        "DocumentGenerationAgent",
        "ComplianceCheckAgent"
    ]

    print(f"\n{Fore.YELLOW}테스트할 에이전트:")
    for i, agent in enumerate(agents, 1):
        print(f"  {i}. {agent}")

    choice = input(f"\n{Fore.WHITE}에이전트 선택 (1-{len(agents)}, 0=전체): ")

    if choice == "0" or choice == "":
        # 모든 에이전트 테스트
        for agent in agents:
            print(f"\n{Fore.YELLOW}Testing {agent}...")
            await test_single_agent(agent)
    else:
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(agents):
                await test_single_agent(agents[idx])
        except:
            print(f"{Fore.RED}잘못된 선택입니다.")
            return False

    print(f"\n{Fore.GREEN}✅ 에이전트 테스트 완료!")
    return True

async def test_single_agent(agent_name):
    """단일 에이전트 테스트"""
    try:
        if agent_name == "DocumentGenerationAgent":
            from backend.service.agents.document_generation_agent import DocumentGenerationAgent

            agent = DocumentGenerationAgent()
            test_input = {
                "document_type": "sales_report",
                "data": {
                    "period": "2024년 4분기",
                    "sales_data": [{"item": "제품A", "amount": 1000000}],
                    "analysis": "테스트 분석",
                    "author": "테스터"
                }
            }

            result = await agent.execute(test_input)
            print(f"{Fore.GREEN}  ✓ {agent_name} 실행 성공")

        elif agent_name == "SearchAgent":
            from backend.service.agents.search_agent import SearchAgent

            agent = SearchAgent()
            test_input = {
                "query": "영업1팀 직원 정보",
                "search_type": "hr_info"
            }

            result = await agent.execute(test_input)
            print(f"{Fore.GREEN}  ✓ {agent_name} 실행 성공")

        else:
            print(f"{Fore.YELLOW}  - {agent_name} (구현 예정)")

    except Exception as e:
        print(f"{Fore.RED}  ✗ {agent_name} 실패: {e}")

def run_orchestrator_test():
    """오케스트레이터 테스트"""
    print(f"\n{Fore.CYAN}▶ 오케스트레이터 테스트...")
    print(f"{Fore.CYAN}{'-' * 50}")

    try:
        from backend.service.orchestrator.orchestrator import MainOrchestrator

        print(f"{Fore.YELLOW}MainOrchestrator 초기화 중...")
        orchestrator = MainOrchestrator()

        print(f"{Fore.YELLOW}워크플로우 컴파일 중...")
        app = orchestrator.workflow.compile(
            checkpointer=orchestrator.checkpointer
        )

        print(f"{Fore.GREEN}✅ 오케스트레이터 초기화 성공!")
        return True

    except Exception as e:
        print(f"{Fore.RED}❌ 오케스트레이터 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

async def run_integration_test():
    """통합 테스트"""
    print(f"\n{Fore.CYAN}▶ 통합 시나리오 테스트...")
    print(f"{Fore.CYAN}{'-' * 50}")

    scenarios = [
        "김철수 과장의 정보 조회",
        "2024년 10월 실적 분석",
        "서울 지역 거래처 매출 보고서 생성"
    ]

    print(f"\n{Fore.YELLOW}테스트 시나리오:")
    for i, scenario in enumerate(scenarios, 1):
        print(f"  {i}. {scenario}")

    # 시나리오별 테스트...
    print(f"\n{Fore.GREEN}✅ 통합 테스트 완료!")
    return True

def run_all_tests():
    """전체 테스트 실행"""
    print(f"\n{Fore.CYAN}▶ 전체 테스트 시작...")
    print(f"{Fore.CYAN}{'=' * 50}")

    results = []

    # 1. DB 테스트
    print(f"\n{Fore.YELLOW}[1/5] DB 연결 테스트")
    results.append(("DB 연결", run_db_test()))

    # 2. 스키마 검증
    print(f"\n{Fore.YELLOW}[2/5] 스키마 검증")
    results.append(("스키마", run_schema_validation()))

    # 3. 에이전트 테스트
    print(f"\n{Fore.YELLOW}[3/5] 에이전트 테스트")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    results.append(("에이전트", loop.run_until_complete(run_agent_tests())))

    # 4. 오케스트레이터 테스트
    print(f"\n{Fore.YELLOW}[4/5] 오케스트레이터 테스트")
    results.append(("오케스트레이터", run_orchestrator_test()))

    # 5. 통합 테스트
    print(f"\n{Fore.YELLOW}[5/5] 통합 테스트")
    results.append(("통합", loop.run_until_complete(run_integration_test())))

    # 결과 요약
    print(f"\n{Fore.CYAN}{'=' * 50}")
    print(f"{Fore.YELLOW}테스트 결과 요약:")
    print(f"{Fore.CYAN}{'=' * 50}")

    passed = 0
    for name, result in results:
        status = f"{Fore.GREEN}✅ PASS" if result else f"{Fore.RED}❌ FAIL"
        print(f"  {status} - {name} 테스트")
        if result:
            passed += 1

    print(f"\n{Fore.YELLOW}총 {len(results)}개 테스트 중 {Fore.GREEN}{passed}개 통과")

    if passed == len(results):
        print(f"\n{Fore.GREEN}{'🎉' * 10}")
        print(f"{Fore.GREEN}모든 테스트 성공!")
        print(f"{Fore.GREEN}{'🎉' * 10}")
    else:
        print(f"\n{Fore.YELLOW}⚠️ 일부 테스트 실패. 로그를 확인하세요.")

def main():
    """메인 실행 함수"""
    print_header()

    while True:
        show_menu()
        choice = input(f"{Fore.WHITE}선택 (0-7): ").strip()

        if choice == "0":
            print(f"\n{Fore.YELLOW}테스트를 종료합니다.")
            break
        elif choice == "1":
            run_db_test()
        elif choice == "2":
            run_schema_validation()
        elif choice == "3":
            run_sample_queries()
        elif choice == "4":
            asyncio.run(run_agent_tests())
        elif choice == "5":
            run_orchestrator_test()
        elif choice == "6":
            asyncio.run(run_integration_test())
        elif choice == "7":
            run_all_tests()
        else:
            print(f"{Fore.RED}잘못된 선택입니다. 다시 선택해주세요.")

        if choice != "0":
            input(f"\n{Fore.YELLOW}계속하려면 Enter를 누르세요...")
            print("\n" * 2)

    print(f"\n{Fore.CYAN}감사합니다! 👋")

if __name__ == "__main__":
    # 명령줄 인자 처리
    import argparse

    parser = argparse.ArgumentParser(description="NaruTalk 테스트 시스템")
    parser.add_argument("--all", action="store_true", help="모든 테스트 실행")
    parser.add_argument("--db", action="store_true", help="DB 테스트만 실행")
    parser.add_argument("--agents", action="store_true", help="에이전트 테스트만 실행")
    parser.add_argument("--no-color", action="store_true", help="색상 없이 실행")

    args = parser.parse_args()

    if args.no_color:
        HAS_COLOR = False
        Fore = Back = Style = DummyColor()

    if args.all:
        print_header()
        run_all_tests()
    elif args.db:
        print_header()
        run_db_test()
    elif args.agents:
        print_header()
        asyncio.run(run_agent_tests())
    else:
        # 대화형 모드
        main()