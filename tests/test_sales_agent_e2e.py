"""
Sales Analytics Agent End-to-End Integration Test
실제 agent.run() 호출로 전체 플로우 테스트
Text2SQL, Subgraph, SQL Execution 통합 검증

실행 방법:
    python tests/test_sales_agent_e2e.py
    python tests/test_sales_agent_e2e.py --flow text2sql
    python tests/test_sales_agent_e2e.py --flow subgraph
    python tests/test_sales_agent_e2e.py --benchmark
    python tests/test_sales_agent_e2e.py --verbose
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import argparse
from dataclasses import dataclass
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.service.agents.sales_analytics_agent import SalesAnalyticsAgent
from backend.service.core.context import create_agent_context
from backend.service.core.config import Config

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """테스트 케이스"""
    name: str
    query: str
    expected_flow: List[str]
    verify: List[str]
    description: str = ""


@dataclass
class TestResult:
    """테스트 결과"""
    test_case: TestCase
    success: bool
    execution_time: float
    result: Dict[str, Any]
    error: Optional[str] = None
    verified_items: Dict[str, bool] = None


class SalesAgentE2ETester:
    """Sales Analytics Agent E2E 테스터"""

    def __init__(self, verbose: bool = False):
        """초기화"""
        self.verbose = verbose
        self.agent = SalesAnalyticsAgent()
        self.test_results: List[TestResult] = []

        # 실제 데이터베이스의 테스트 데이터
        self.test_data = {
            "employees": ["윤수아", "윤하은", "정예준", "조시현", "조하은", "최수아"],
            "branches": ["서부팀"],
            "clients": ["파라곤이비인후과", "박영호내과의원", "현대파라곤정형외과"],
            "months": ["202409", "202410", "202411"]
        }

    def get_test_cases(self, flow_type: str = "all") -> List[TestCase]:
        """테스트 케이스 반환"""
        all_cases = []

        # Text2SQL 플로우 테스트
        text2sql_cases = [
            TestCase(
                name="Simple Employee Query",
                query=f"{self.test_data['employees'][0]}의 2024년 11월 판매 실적 조회해줘",
                expected_flow=["plan_execution", "text2sql", "execute_plan", "format_results"],
                verify=["generated_sql", "sql_result", "formatted_result"],
                description="단순 담당자 실적 조회 - Text2SQL 기본 동작"
            ),
            TestCase(
                name="Complex Multi-Column Query",
                query=f"{self.test_data['employees'][1]}의 최근 3개월 매출 추이 분석",
                expected_flow=["plan_execution", "text2sql", "execute_plan", "format_results"],
                verify=["generated_sql", "sql_result", "statistics"],
                description="다중 월 컬럼 조회 - 시계열 데이터 처리"
            ),
            TestCase(
                name="Client-based Query",
                query=f"{self.test_data['clients'][0]} 거래처의 월별 매출 현황",
                expected_flow=["plan_execution", "text2sql", "execute_plan"],
                verify=["generated_sql", "target_database"],
                description="거래처 기반 조회 - JOIN 쿼리 생성"
            ),
            TestCase(
                name="Comparison Query",
                query=f"{self.test_data['employees'][0]}와 {self.test_data['employees'][2]}의 실적 비교",
                expected_flow=["plan_execution", "text2sql", "execute_plan"],
                verify=["generated_sql", "sql_result"],
                description="비교 분석 - 복수 조건 SQL"
            ),
            TestCase(
                name="Aggregate Query",
                query="전체 영업팀의 2024년 11월 총 매출",
                expected_flow=["plan_execution", "text2sql", "execute_plan"],
                verify=["generated_sql", "sql_result"],
                description="집계 쿼리 - SUM/GROUP BY"
            )
        ]

        # Subgraph 플로우 테스트
        subgraph_cases = [
            TestCase(
                name="Data Collection Subgraph",
                query=f"{self.test_data['branches'][0]} 전체 실적 데이터 수집하고 분석해줘",
                expected_flow=["plan_execution", "data_collection_subgraph", "analysis_subgraph"],
                verify=["execution_results", "collected_data", "insights"],
                description="데이터 수집 서브그래프 호출"
            ),
            TestCase(
                name="Analysis Subgraph",
                query="수집된 판매 데이터로 트렌드 분석 실행",
                expected_flow=["plan_execution", "analysis_subgraph"],
                verify=["execution_results", "analysis_result", "insights"],
                description="분석 서브그래프 호출"
            ),
            TestCase(
                name="Complex Analysis with Subgraphs",
                query=f"{self.test_data['employees'][2]} 담당자의 거래처별 방문횟수와 매출 상관관계 분석",
                expected_flow=["plan_execution", "text2sql", "data_collection", "analysis"],
                verify=["execution_plan", "execution_results", "insights"],
                description="복합 분석 - 다중 서브그래프"
            )
        ]

        # 통합 플로우 테스트
        integration_cases = [
            TestCase(
                name="Full Pipeline Test",
                query="모든 영업사원의 목표 대비 달성률을 계산하고 상위 3명을 추출해줘",
                expected_flow=["plan_execution", "execute_plan", "format_results"],
                verify=["execution_plan", "sql_result", "statistics", "formatted_result"],
                description="전체 파이프라인 테스트"
            ),
            TestCase(
                name="Real User Scenario",
                query=f"{self.test_data['employees'][3]}의 이번달 실적이 목표 대비 어떤지 분석해줘",
                expected_flow=["plan_execution", "text2sql", "execute_plan", "format_results"],
                verify=["generated_sql", "statistics", "insights", "formatted_result"],
                description="실제 사용자 시나리오"
            )
        ]

        # 플로우 타입별 케이스 선택
        if flow_type == "text2sql":
            all_cases = text2sql_cases
        elif flow_type == "subgraph":
            all_cases = subgraph_cases
        elif flow_type == "integration":
            all_cases = integration_cases
        else:  # all
            all_cases = text2sql_cases + subgraph_cases + integration_cases

        return all_cases

    async def run_test_case(self, test_case: TestCase) -> TestResult:
        """단일 테스트 케이스 실행"""
        start_time = time.time()

        try:
            if self.verbose:
                logger.info(f"\n{'='*60}")
                logger.info(f"테스트: {test_case.name}")
                logger.info(f"쿼리: {test_case.query}")
                logger.info(f"설명: {test_case.description}")

            # Agent 실행
            result = await self.agent.run(
                query=test_case.query,
                user_id="test_user",
                session_id=f"test_session_{int(time.time())}"
            )

            # 결과 검증
            verified_items = {}
            for item in test_case.verify:
                if item == "generated_sql":
                    verified_items[item] = result.get("generated_sql") is not None
                elif item == "sql_result":
                    verified_items[item] = result.get("sql_result") is not None
                elif item == "formatted_result":
                    verified_items[item] = result.get("formatted_result") is not None
                elif item == "execution_results":
                    verified_items[item] = result.get("execution_results") is not None
                elif item == "collected_data":
                    verified_items[item] = result.get("collected_data") is not None or \
                                         result.get("data_collection_result") is not None
                elif item == "insights":
                    verified_items[item] = result.get("insights") is not None and \
                                         len(result.get("insights", [])) > 0
                elif item == "statistics":
                    verified_items[item] = result.get("statistics") is not None
                elif item == "execution_plan":
                    verified_items[item] = result.get("execution_plan") is not None
                elif item == "analysis_result":
                    verified_items[item] = result.get("analysis_result") is not None
                elif item == "target_database":
                    verified_items[item] = result.get("target_database") is not None
                else:
                    verified_items[item] = result.get(item) is not None

            # 전체 성공 여부
            success = all(verified_items.values()) and result.get("status") in ["completed", "success"]

            execution_time = time.time() - start_time

            if self.verbose:
                logger.info(f"실행 시간: {execution_time:.2f}초")
                logger.info(f"상태: {result.get('status')}")
                logger.info(f"검증 결과: {verified_items}")

                if result.get("generated_sql"):
                    logger.info(f"생성된 SQL:\n{result['generated_sql']}")

                if result.get("formatted_result"):
                    logger.info(f"포맷된 결과:\n{result['formatted_result'][:500]}...")

            return TestResult(
                test_case=test_case,
                success=success,
                execution_time=execution_time,
                result=result,
                verified_items=verified_items
            )

        except Exception as e:
            logger.error(f"테스트 실행 중 에러: {e}")
            return TestResult(
                test_case=test_case,
                success=False,
                execution_time=time.time() - start_time,
                result={},
                error=str(e)
            )

    async def run_benchmark(self, test_cases: List[TestCase]):
        """벤치마크 실행"""
        logger.info("\n=== 벤치마크 모드 ===")

        total_start = time.time()
        execution_times = []

        for test_case in test_cases[:3]:  # 벤치마크는 3개만
            times = []
            for i in range(3):  # 3회 반복
                result = await self.run_test_case(test_case)
                times.append(result.execution_time)

            avg_time = sum(times) / len(times)
            execution_times.append(avg_time)
            logger.info(f"{test_case.name}: 평균 {avg_time:.2f}초")

        total_time = time.time() - total_start
        logger.info(f"\n총 실행 시간: {total_time:.2f}초")
        logger.info(f"평균 실행 시간: {sum(execution_times)/len(execution_times):.2f}초")

    async def run_all_tests(self, flow_type: str = "all", benchmark: bool = False):
        """모든 테스트 실행"""
        test_cases = self.get_test_cases(flow_type)

        if benchmark:
            await self.run_benchmark(test_cases)
            return

        logger.info(f"\n=== Sales Agent E2E 테스트 시작 ===")
        logger.info(f"테스트 케이스 수: {len(test_cases)}")
        logger.info(f"플로우 타입: {flow_type}")

        # 테스트 실행
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"\n[{i}/{len(test_cases)}] {test_case.name} 실행 중...")
            result = await self.run_test_case(test_case)
            self.test_results.append(result)

            if result.success:
                logger.info(f"✅ 성공 ({result.execution_time:.2f}초)")
            else:
                logger.error(f"❌ 실패: {result.error or '검증 실패'}")

        # 결과 요약
        self.print_summary()

        # 결과 저장
        self.save_results()

    def print_summary(self):
        """테스트 결과 요약 출력"""
        total = len(self.test_results)
        success = sum(1 for r in self.test_results if r.success)
        failed = total - success

        logger.info(f"\n{'='*60}")
        logger.info(f"테스트 결과 요약")
        logger.info(f"{'='*60}")
        logger.info(f"총 테스트: {total}")
        logger.info(f"성공: {success} ({success/total*100:.1f}%)")
        logger.info(f"실패: {failed}")

        if failed > 0:
            logger.info(f"\n실패한 테스트:")
            for result in self.test_results:
                if not result.success:
                    logger.info(f"  - {result.test_case.name}: {result.error or '검증 실패'}")
                    if result.verified_items:
                        failed_items = [k for k, v in result.verified_items.items() if not v]
                        if failed_items:
                            logger.info(f"    실패 항목: {', '.join(failed_items)}")

        # 실행 시간 통계
        execution_times = [r.execution_time for r in self.test_results]
        if execution_times:
            logger.info(f"\n실행 시간 통계:")
            logger.info(f"  평균: {sum(execution_times)/len(execution_times):.2f}초")
            logger.info(f"  최소: {min(execution_times):.2f}초")
            logger.info(f"  최대: {max(execution_times):.2f}초")

    def save_results(self):
        """테스트 결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tests/test_results_e2e_{timestamp}.json"

        results_data = {
            "timestamp": timestamp,
            "summary": {
                "total": len(self.test_results),
                "success": sum(1 for r in self.test_results if r.success),
                "failed": sum(1 for r in self.test_results if not r.success)
            },
            "test_results": [
                {
                    "name": r.test_case.name,
                    "query": r.test_case.query,
                    "success": r.success,
                    "execution_time": r.execution_time,
                    "verified_items": r.verified_items,
                    "error": r.error
                }
                for r in self.test_results
            ]
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)

        logger.info(f"\n테스트 결과 저장: {filename}")


async def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='Sales Agent E2E Test')
    parser.add_argument('--flow', choices=['all', 'text2sql', 'subgraph', 'integration'],
                       default='all', help='테스트할 플로우 타입')
    parser.add_argument('--verbose', action='store_true', help='상세 출력')
    parser.add_argument('--benchmark', action='store_true', help='벤치마크 모드')

    args = parser.parse_args()

    # 테스터 생성 및 실행
    tester = SalesAgentE2ETester(verbose=args.verbose)
    await tester.run_all_tests(flow_type=args.flow, benchmark=args.benchmark)


if __name__ == "__main__":
    asyncio.run(main())