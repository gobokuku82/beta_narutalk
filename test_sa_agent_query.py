"""
Sales Analytics Agent 직접 쿼리 테스트
Supervisor 없이 SalesAnalyticsAgent를 직접 실행하여 테스트

사용법:
    # 대화형 모드
    python test_sa_agent_query.py

    # 단일 쿼리 실행
    python test_sa_agent_query.py "윤수아 실적"

    # 도움말
    python test_sa_agent_query.py --help
"""

import asyncio
import sys
import os
import time
import argparse
from datetime import datetime
from typing import Dict, Any, Optional
import json

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Windows 인코딩 설정
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding='utf-8',
        errors='replace'
    )

from backend.service.agents.sales_analytics_agent import SalesAnalyticsAgent

# 색상 코드 (터미널 출력용)
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# 샘플 쿼리
SAMPLE_QUERIES = {
    "기본 조회": [
        "윤수아 실적",
        "정예준 3월 매출",
        "조시현 작년 실적",
        "최수아 이번달 실적",
    ],
    "통계 분석": [
        "전체 직원 평균 실적",
        "이번달 실적 TOP 3",
        "작년 대비 성장률",
        "목표 대비 달성률",
    ],
    "비교 분석": [
        "윤수아 전월 대비",
        "1분기 vs 2분기",
        "윤수아와 윤하은 실적 비교",
        "상반기 대비 하반기 매출",
    ],
    "복합 쿼리": [
        "윤수아 3월 실적과 목표 달성률",
        "전체 현황 분석 및 개선 제안",
        "정예준 실적 트렌드 분석",
        "팀 전체 효율성 분석",
    ]
}

class SalesAgentQueryTester:
    """Sales Analytics Agent 쿼리 테스터"""

    def __init__(self):
        self.agent = None
        self.session_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.query_count = 0

    async def initialize(self):
        """에이전트 초기화"""
        print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER} Sales Analytics Agent 초기화 중...{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")

        try:
            self.agent = SalesAnalyticsAgent()
            print(f"{Colors.OKGREEN}✓ 에이전트 초기화 완료{Colors.ENDC}\n")
            return True
        except Exception as e:
            print(f"{Colors.FAIL}✗ 에이전트 초기화 실패: {e}{Colors.ENDC}")
            return False

    async def execute_query(self, query: str) -> Dict[str, Any]:
        """단일 쿼리 실행"""
        self.query_count += 1

        print(f"{Colors.OKCYAN}[Query #{self.query_count}] {query}{Colors.ENDC}")
        print(f"{Colors.OKBLUE}{'-'*60}{Colors.ENDC}")

        start_time = time.time()

        try:
            # 에이전트 실행
            result = await self.agent.run(
                query=query,
                user_id="test_user",
                session_id=self.session_id,
                language="ko"
            )

            execution_time = time.time() - start_time

            # 결과 처리
            self._display_result(result, execution_time)

            return result

        except Exception as e:
            print(f"{Colors.FAIL}✗ 실행 오류: {e}{Colors.ENDC}")
            return {"status": "error", "error": str(e)}

    def _display_result(self, result: Dict[str, Any], execution_time: float):
        """결과 표시"""
        status = result.get("status", "unknown")

        # 상태 표시
        if status == "completed":
            status_color = Colors.OKGREEN
            status_icon = "✓"
        else:
            status_color = Colors.WARNING
            status_icon = "⚠"

        print(f"{status_color}{status_icon} Status: {status}{Colors.ENDC}")
        print(f"⏱  실행 시간: {execution_time:.2f}초")

        # 실행 계획 표시
        if result.get("execution_plan"):
            plan = result["execution_plan"]
            print(f"\n📋 실행 계획:")
            print(f"  - SQL 사용: {plan.get('use_sql', False)}")
            print(f"  - Subgraph 사용: {plan.get('use_subgraphs', False)}")

        # 디버그: SQL 쿼리 표시
        if result.get("sql_query"):
            print(f"\n🔍 생성된 SQL:")
            print(f"{Colors.OKCYAN}{result.get('sql_query')[:500]}{Colors.ENDC}")

        # 디버그: Raw 결과 확인
        if result.get("sql_result"):
            print(f"\n🔍 SQL 실행 결과 (raw):")
            sql_result = result.get("sql_result")
            if isinstance(sql_result, list) and len(sql_result) > 0:
                print(f"  - 행 수: {len(sql_result)}")
                print(f"  - 첫 행: {sql_result[0] if sql_result else 'None'}")
            else:
                print(f"  - 결과: {sql_result}")

        # 결과 표시
        if result.get("formatted_result"):
            print(f"\n{Colors.BOLD}📊 결과:{Colors.ENDC}")
            print(f"{Colors.OKGREEN}{'-'*60}{Colors.ENDC}")
            formatted = result["formatted_result"]
            # 너무 긴 결과는 잘라서 표시
            if len(formatted) > 1000:
                print(formatted[:1000])
                print(f"\n... (총 {len(formatted)} 자, 일부만 표시)")
            else:
                print(formatted)
            print(f"{Colors.OKGREEN}{'-'*60}{Colors.ENDC}")
        else:
            # 포맷된 결과가 없을 때 state 전체 확인
            print(f"\n{Colors.WARNING}⚠ formatted_result가 비어있음{Colors.ENDC}")
            print(f"전체 결과 키: {list(result.keys())}")

        # 에러 표시
        if result.get("errors"):
            print(f"\n{Colors.FAIL}⚠ 오류:{Colors.ENDC}")
            for error in result["errors"]:
                print(f"  - {error}")

        print()  # 줄바꿈

    async def interactive_mode(self):
        """대화형 모드"""
        if not await self.initialize():
            return

        print(f"{Colors.BOLD}대화형 모드 시작{Colors.ENDC}")
        print(f"  • 'help' - 샘플 쿼리 보기")
        print(f"  • 'exit' - 종료")
        print(f"  • 'clear' - 화면 지우기")
        print(f"  • 쿼리 입력 - 실행\n")

        while True:
            try:
                # 프롬프트
                query = input(f"{Colors.BOLD}Query> {Colors.ENDC}").strip()

                # 명령 처리
                if query.lower() == 'exit':
                    print(f"\n{Colors.WARNING}종료합니다...{Colors.ENDC}")
                    break
                elif query.lower() == 'help':
                    self._show_samples()
                    continue
                elif query.lower() == 'clear':
                    os.system('cls' if os.name == 'nt' else 'clear')
                    continue
                elif not query:
                    continue

                # 쿼리 실행
                print()  # 줄바꿈
                await self.execute_query(query)

            except KeyboardInterrupt:
                print(f"\n\n{Colors.WARNING}중단됨{Colors.ENDC}")
                break
            except Exception as e:
                print(f"{Colors.FAIL}오류: {e}{Colors.ENDC}\n")

    async def single_query_mode(self, query: str):
        """단일 쿼리 모드"""
        if not await self.initialize():
            return

        await self.execute_query(query)

        # 요약 표시
        print(f"\n{Colors.BOLD}실행 완료{Colors.ENDC}")
        print(f"세션 ID: {self.session_id}")

    async def batch_mode(self):
        """배치 테스트 모드"""
        if not await self.initialize():
            return

        print(f"{Colors.BOLD}배치 테스트 시작{Colors.ENDC}\n")

        results = []
        for category, queries in SAMPLE_QUERIES.items():
            print(f"\n{Colors.HEADER}[{category}]{Colors.ENDC}")
            for query in queries[:2]:  # 각 카테고리에서 2개씩만
                result = await self.execute_query(query)
                results.append({
                    "query": query,
                    "category": category,
                    "status": result.get("status"),
                    "has_result": bool(result.get("formatted_result"))
                })
                await asyncio.sleep(0.5)  # 과부하 방지

        # 통계 표시
        self._show_statistics(results)

    def _show_samples(self):
        """샘플 쿼리 표시"""
        print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER} 샘플 쿼리{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")

        print(f"{Colors.BOLD}실제 직원명:{Colors.ENDC}")
        print("  윤수아, 윤하은, 정예준, 조시현, 조하은, 최수아\n")

        for category, queries in SAMPLE_QUERIES.items():
            print(f"{Colors.OKCYAN}[{category}]{Colors.ENDC}")
            for query in queries:
                print(f"  • {query}")
            print()

    def _show_statistics(self, results: list):
        """통계 표시"""
        total = len(results)
        successful = sum(1 for r in results if r.get("status") == "completed")

        print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER} 테스트 통계{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")

        print(f"총 쿼리: {total}")
        print(f"성공: {successful}")
        print(f"실패: {total - successful}")
        print(f"성공률: {(successful/total*100):.1f}%")

        # 카테고리별 통계
        categories = {}
        for r in results:
            cat = r["category"]
            if cat not in categories:
                categories[cat] = {"total": 0, "success": 0}
            categories[cat]["total"] += 1
            if r["status"] == "completed":
                categories[cat]["success"] += 1

        print(f"\n{Colors.BOLD}카테고리별 통계:{Colors.ENDC}")
        for cat, stats in categories.items():
            rate = (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"  {cat}: {stats['success']}/{stats['total']} ({rate:.0f}%)")

async def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='Sales Analytics Agent Query Tester',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  # 대화형 모드
  python test_sa_agent_query.py

  # 단일 쿼리
  python test_sa_agent_query.py "윤수아 실적"

  # 배치 테스트
  python test_sa_agent_query.py --batch
        """
    )

    parser.add_argument(
        'query',
        nargs='?',
        help='실행할 쿼리 (생략시 대화형 모드)'
    )

    parser.add_argument(
        '--batch',
        action='store_true',
        help='배치 테스트 모드'
    )

    args = parser.parse_args()

    tester = SalesAgentQueryTester()

    if args.batch:
        # 배치 모드
        await tester.batch_mode()
    elif args.query:
        # 단일 쿼리 모드
        await tester.single_query_mode(args.query)
    else:
        # 대화형 모드
        await tester.interactive_mode()

if __name__ == "__main__":
    # Windows에서 asyncio 이벤트 루프 정책 설정
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # 실행
    asyncio.run(main())