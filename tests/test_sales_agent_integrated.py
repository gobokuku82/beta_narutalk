"""
Sales Analytics Agent 통합 테스트
모든 테스트를 agent.run()을 통해 실행하여 실제 사용 시나리오 테스트

실행 방법:
    python tests/test_sales_agent_integrated.py [--interactive]

옵션:
    --interactive: 대화형 모드로 직접 쿼리 입력
"""

import asyncio
import json
import logging
import os
import sys
import time
import io
from datetime import datetime
from typing import Dict, Any, List, Optional
import argparse

# Windows 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding='utf-8',
        errors='replace'
    )

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.service.agents.sales_analytics_agent import SalesAnalyticsAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============== 실제 데이터베이스 기반 테스트 쿼리 ==============

# 실제 직원명 (데이터베이스 확인)
ACTUAL_EMPLOYEES = ["윤수아", "윤하은", "정예준", "조시현", "조하은", "최수아"]

# 1. Text2SQL 테스트 쿼리 (50개)
TEXT2SQL_QUERIES = [
    # 기본 개인 실적 조회 (15개)
    "윤수아 실적",
    "윤수아 3월 실적",
    "윤수아 2024년 3월 매출",
    "윤하은 작년 실적",
    "윤하은 2023년 전체 실적",
    "정예준 최근 실적",
    "정예준 이번달 매출",
    "조시현 4월 실적 조회",
    "조시현 2024년 1분기 실적",
    "조하은 상반기 매출",
    "조하은 2024년 상반기 실적",
    "최수아 하반기 실적",
    "윤수아씨의 성과",
    "정예준님 판매 실적",
    "조시현 담당자 실적 확인",

    # 집계 및 통계 (10개)
    "전체 직원 평균 실적",
    "이번달 총 매출",
    "3월 전체 매출 합계",
    "직원별 평균 실적",
    "월별 매출 총액",
    "2024년 총 매출",
    "상반기 평균 실적",
    "최고 실적 금액",
    "최저 매출 금액",
    "전체 실적 통계",

    # 비교 분석 (10개)
    "윤수아 전월 대비 실적",
    "정예준 작년 대비 성장률",
    "윤하은 목표 대비 달성률",
    "1분기 대비 2분기 실적",
    "상반기 대비 하반기 매출",
    "윤수아와 윤하은 실적 비교",
    "정예준과 조시현 매출 비교",
    "작년 동기 대비 성장",
    "전년 대비 실적 변화",
    "월별 성장 추이",

    # 순위 및 랭킹 (5개)
    "이번달 실적 TOP 3",
    "3월 매출 상위 5명",
    "실적 하위 3명",
    "올해 최고 실적자",
    "전체 직원 실적 순위",

    # 복잡한 조건 (10개)
    "윤수아 3월 실적과 목표 달성률",
    "정예준 상반기 실적 및 성장률",
    "실적 100만원 이상 직원",
    "목표 초과 달성 직원",
    "최근 3개월 실적 상승세",
    "2024년 각 분기별 실적",
    "월평균 실적 500만원 이상",
    "작년보다 실적 향상된 직원",
    "3개월 연속 목표 달성자",
    "실적 변동성이 큰 직원",
]

# 2. Data Collection 중심 쿼리 (10개)
DATA_COLLECTION_QUERIES = [
    "윤수아 전체 거래처별 실적",
    "정예준 담당 거래처 현황",
    "모든 직원의 3월 실적 데이터",
    "2024년 1분기 전체 데이터",
    "윤하은 월별 실적 추이",
    "전 직원 연간 실적 집계",
    "거래처별 매출 현황",
    "품목별 판매 실적",
    "지역별 매출 데이터",
    "신규 거래처 실적 현황",
]

# 3. Analysis 중심 쿼리 (20개)
ANALYSIS_QUERIES = [
    "윤수아 실적 트렌드 분석",
    "정예준 성과 평가",
    "전체 직원 실적 분포 분석",
    "매출 성장 패턴 분석",
    "목표 달성률 추이 분석",
    "실적 하락 원인 분석",
    "상위 실적자 공통점 분석",
    "월별 실적 변동 분석",
    "분기별 성과 비교 분석",
    "개인별 성장 잠재력 평가",
    "팀 전체 효율성 분석",
    "매출 예측 분석",
    "시장 점유율 분석",
    "경쟁력 평가",
    "리스크 요인 분석",
    "기회 요인 도출",
    "강점 약점 분석",
    "개선 방향 제안",
    "전략적 인사이트 도출",
    "종합 성과 리포트",
]

# 4. 복합/단일 질의 (20개)
COMPLEX_QUERIES = [
    # 단순 질의 (5개)
    "윤수아 실적",
    "이번달 매출",
    "평균 실적",
    "최고 실적",
    "전체 매출",

    # 복합 질의 (10개)
    "윤수아 3월 실적과 목표 달성률 그리고 전월 대비 성장률 보여줘",
    "정예준 상반기 실적 분석하고 하반기 예측해줘",
    "전체 직원 실적 순위와 평균 그리고 최고/최저 보여줘",
    "윤하은 작년 대비 올해 성장률과 주요 성장 요인 분석",
    "이번 분기 실적과 작년 동기 대비 그리고 목표 달성 현황",
    "상위 3명의 실적과 그들의 주요 거래처 분석",
    "실적 하락 직원들과 원인 그리고 개선 방안",
    "월별 매출 추이와 성장률 그리고 예측",
    "거래처별 매출과 담당자 그리고 성장 가능성",
    "전체 현황 종합 분석 및 제안사항",

    # 모호한 질의 (5개)
    "윤수아 어때?",
    "실적 좋은 사람",
    "요즘 매출",
    "작년이랑 비교하면?",
    "분석 좀 해줘",
]

# 5. 사용자 시나리오 쿼리
E2E_SCENARIOS = [
    {
        "name": "일일 보고",
        "queries": [
            "오늘 전체 실적 현황",
            "어제 대비 변화",
            "주목할 만한 성과",
        ]
    },
    {
        "name": "월간 평가",
        "queries": [
            "윤수아 이번달 실적",
            "목표 달성률",
            "작년 동월 대비",
            "개선 제안",
        ]
    },
    {
        "name": "분기 리뷰",
        "queries": [
            "1분기 전체 실적",
            "직원별 성과",
            "목표 달성 현황",
            "2분기 전망",
        ]
    },
]

# ============== 테스트 실행 클래스 ==============

class SalesAgentIntegratedTester:
    """Sales Analytics Agent 통합 테스터"""

    def __init__(self):
        self.agent = None
        self.results = []
        self.total_queries = 0
        self.successful_queries = 0
        self.failed_queries = 0

    async def initialize(self):
        """에이전트 초기화"""
        print("\n" + "="*60)
        print("Sales Analytics Agent 초기화 중...")
        print("="*60)

        try:
            self.agent = SalesAnalyticsAgent()
            print("[OK] 에이전트 초기화 완료")
            return True
        except Exception as e:
            print(f"[ERROR] 에이전트 초기화 실패: {e}")
            return False

    async def test_query(self, query: str, category: str = "general") -> Dict[str, Any]:
        """단일 쿼리 테스트"""
        self.total_queries += 1

        print(f"\n[Query {self.total_queries}] {query}")
        print("-" * 50)

        start_time = time.time()

        try:
            # 에이전트 실행
            result = await self.agent.run(
                query=query,
                user_id="test_user",
                session_id=f"test_{self.total_queries}",
                language="ko"
            )

            execution_time = time.time() - start_time

            # 결과 분석
            status = result.get("status")
            has_result = bool(result.get("formatted_result"))
            has_plan = bool(result.get("execution_plan"))

            # 결과 출력
            print(f"Status: {status}")
            print(f"Execution Time: {execution_time:.2f}s")
            print(f"Has Plan: {has_plan}")
            print(f"Has Result: {has_result}")

            if has_result:
                formatted_result = result.get("formatted_result")
                print(f"\n[Result]")
                print(formatted_result[:500] if len(formatted_result) > 500 else formatted_result)

            if result.get("errors"):
                print(f"\n[Errors]")
                for error in result.get("errors", []):
                    print(f"  - {error}")

            # 성공/실패 판단
            if status == "completed" and has_result:
                self.successful_queries += 1
                test_status = "SUCCESS"
            else:
                self.failed_queries += 1
                test_status = "FAILED"

            # 결과 저장
            test_result = {
                "query": query,
                "category": category,
                "status": test_status,
                "execution_time": execution_time,
                "agent_status": status,
                "has_result": has_result,
                "has_plan": has_plan,
                "errors": result.get("errors", [])
            }

            self.results.append(test_result)

            print(f"\n[Test Result: {test_status}]")

            return test_result

        except Exception as e:
            self.failed_queries += 1
            print(f"[ERROR] {e}")

            test_result = {
                "query": query,
                "category": category,
                "status": "ERROR",
                "execution_time": time.time() - start_time,
                "error": str(e)
            }

            self.results.append(test_result)
            return test_result

    async def run_category_tests(self, queries: List[str], category: str):
        """카테고리별 테스트 실행"""
        print(f"\n{'='*60}")
        print(f" {category.upper()} TESTS ")
        print(f"{'='*60}")
        print(f"Total queries to test: {len(queries)}")

        category_results = []

        for i, query in enumerate(queries, 1):
            print(f"\n[{category} {i}/{len(queries)}]")
            result = await self.test_query(query, category)
            category_results.append(result)

            # 진행률 표시
            if i % 5 == 0:
                success_rate = (sum(1 for r in category_results if r['status'] == 'SUCCESS') / i) * 100
                print(f"\n>>> Progress: {i}/{len(queries)} completed, Success Rate: {success_rate:.1f}%")

        return category_results

    async def run_all_tests(self):
        """모든 테스트 실행"""
        print("\n" + "="*80)
        print(" SALES ANALYTICS AGENT INTEGRATED TEST SUITE ".center(80))
        print("="*80)

        # 초기화
        if not await self.initialize():
            return

        # 1. Text2SQL 테스트
        await self.run_category_tests(TEXT2SQL_QUERIES, "text2sql")

        # 2. Data Collection 테스트
        await self.run_category_tests(DATA_COLLECTION_QUERIES, "data_collection")

        # 3. Analysis 테스트
        await self.run_category_tests(ANALYSIS_QUERIES, "analysis")

        # 4. Complex Query 테스트
        await self.run_category_tests(COMPLEX_QUERIES, "complex")

        # 5. E2E 시나리오 테스트
        for scenario in E2E_SCENARIOS:
            print(f"\n{'='*60}")
            print(f" E2E SCENARIO: {scenario['name']} ")
            print(f"{'='*60}")

            for query in scenario['queries']:
                await self.test_query(query, f"e2e_{scenario['name']}")

        # 최종 요약
        self.print_summary()

        # 결과 저장
        self.save_results()

    def print_summary(self):
        """테스트 결과 요약"""
        print("\n" + "="*80)
        print(" TEST SUMMARY ".center(80))
        print("="*80)

        print(f"\nTotal Queries Tested: {self.total_queries}")
        print(f"Successful: {self.successful_queries}")
        print(f"Failed: {self.failed_queries}")
        print(f"Success Rate: {(self.successful_queries/self.total_queries*100):.1f}%")

        # 카테고리별 통계
        categories = {}
        for result in self.results:
            cat = result['category']
            if cat not in categories:
                categories[cat] = {'total': 0, 'success': 0}
            categories[cat]['total'] += 1
            if result['status'] == 'SUCCESS':
                categories[cat]['success'] += 1

        print("\nCategory Statistics:")
        print("-" * 40)
        for cat, stats in categories.items():
            success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"{cat:20s}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")

        # 실패한 쿼리 목록
        failed = [r for r in self.results if r['status'] != 'SUCCESS']
        if failed:
            print("\nFailed Queries:")
            print("-" * 40)
            for f in failed[:10]:  # 처음 10개만
                print(f"- {f['query'][:50]}...")
                if 'error' in f:
                    print(f"  Error: {f['error'][:100]}")
                elif f.get('errors'):
                    print(f"  Errors: {f['errors'][0] if f['errors'] else 'Unknown'}")

        # 실행 시간 통계
        exec_times = [r['execution_time'] for r in self.results]
        if exec_times:
            print(f"\nExecution Time Statistics:")
            print(f"  Average: {sum(exec_times)/len(exec_times):.2f}s")
            print(f"  Min: {min(exec_times):.2f}s")
            print(f"  Max: {max(exec_times):.2f}s")

    def save_results(self):
        """결과를 파일로 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_integrated_{timestamp}.json"

        report = {
            "timestamp": timestamp,
            "summary": {
                "total": self.total_queries,
                "successful": self.successful_queries,
                "failed": self.failed_queries,
                "success_rate": (self.successful_queries/self.total_queries*100) if self.total_queries > 0 else 0
            },
            "results": self.results
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n[Results saved to {filename}]")

# ============== 대화형 테스트 모드 ==============

class InteractiveTestMode:
    """대화형 테스트 모드"""

    def __init__(self):
        self.agent = None
        self.session_id = f"interactive_{datetime.now().timestamp()}"

    async def run(self):
        """대화형 모드 실행"""
        print("\n" + "="*60)
        print(" INTERACTIVE TEST MODE ".center(60))
        print("="*60)
        print("\nType 'exit' to quit")
        print("Type 'help' for sample queries\n")

        # 초기화
        self.agent = SalesAnalyticsAgent()
        print("[OK] Agent initialized\n")

        while True:
            try:
                # 사용자 입력
                query = input("\nQuery> ").strip()

                if query.lower() == 'exit':
                    break
                elif query.lower() == 'help':
                    self.show_help()
                    continue
                elif not query:
                    continue

                # 쿼리 실행
                print("\nProcessing...")
                start_time = time.time()

                result = await self.agent.run(
                    query=query,
                    user_id="interactive_user",
                    session_id=self.session_id,
                    language="ko"
                )

                execution_time = time.time() - start_time

                # 결과 출력
                print(f"\nStatus: {result.get('status')}")
                print(f"Execution Time: {execution_time:.2f}s")

                if result.get("execution_plan"):
                    print(f"\nExecution Plan:")
                    plan = result.get("execution_plan")
                    print(f"  - Use SQL: {plan.get('use_sql')}")
                    print(f"  - Use Subgraphs: {plan.get('use_subgraphs')}")
                    print(f"  - Reasoning: {plan.get('reasoning', 'N/A')[:200]}")

                if result.get("formatted_result"):
                    print(f"\n{'='*60}")
                    print(" RESULT ")
                    print('='*60)
                    print(result.get("formatted_result"))
                    print('='*60)

                if result.get("errors"):
                    print(f"\nErrors:")
                    for error in result.get("errors", []):
                        print(f"  - {error}")

            except KeyboardInterrupt:
                print("\nInterrupted")
                break
            except Exception as e:
                print(f"\nError: {e}")

    def show_help(self):
        """도움말 표시"""
        print("\n" + "="*60)
        print(" SAMPLE QUERIES ".center(60))
        print("="*60)
        print("\n실제 직원명: 윤수아, 윤하은, 정예준, 조시현, 조하은, 최수아")
        print("\n[기본 조회]")
        print("  - 윤수아 실적")
        print("  - 정예준 3월 매출")
        print("  - 조시현 작년 실적")
        print("\n[통계 분석]")
        print("  - 전체 직원 평균 실적")
        print("  - 이번달 실적 TOP 5")
        print("  - 목표 대비 달성률")
        print("\n[비교 분석]")
        print("  - 윤수아 전월 대비")
        print("  - 작년 대비 성장률")
        print("  - 1분기 vs 2분기")
        print("\n[복합 질의]")
        print("  - 윤하은 3월 실적과 목표 달성률 그리고 전월 대비")
        print("  - 전체 현황 분석 및 개선 제안")

# ============== Main ==============

async def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='Sales Analytics Agent Test')
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Run in interactive mode'
    )
    parser.add_argument(
        '--category',
        choices=['text2sql', 'data_collection', 'analysis', 'complex', 'e2e', 'all'],
        default='all',
        help='Test category to run'
    )

    args = parser.parse_args()

    if args.interactive:
        # 대화형 모드
        interactive = InteractiveTestMode()
        await interactive.run()
    else:
        # 자동 테스트 모드
        tester = SalesAgentIntegratedTester()

        if args.category == 'all':
            await tester.run_all_tests()
        elif args.category == 'text2sql':
            await tester.initialize()
            await tester.run_category_tests(TEXT2SQL_QUERIES, 'text2sql')
            tester.print_summary()
        elif args.category == 'data_collection':
            await tester.initialize()
            await tester.run_category_tests(DATA_COLLECTION_QUERIES, 'data_collection')
            tester.print_summary()
        elif args.category == 'analysis':
            await tester.initialize()
            await tester.run_category_tests(ANALYSIS_QUERIES, 'analysis')
            tester.print_summary()
        elif args.category == 'complex':
            await tester.initialize()
            await tester.run_category_tests(COMPLEX_QUERIES, 'complex')
            tester.print_summary()
        elif args.category == 'e2e':
            await tester.initialize()
            for scenario in E2E_SCENARIOS:
                for query in scenario['queries']:
                    await tester.test_query(query, f"e2e_{scenario['name']}")
            tester.print_summary()

        tester.save_results()

if __name__ == "__main__":
    asyncio.run(main())