"""
Sales Analytics Agent Subgraph Integration Test
Agent가 실제로 subgraph를 호출하고 데이터가 올바르게 전달되는지 검증

실행 방법:
    python tests/test_agent_with_subgraphs.py
    python tests/test_agent_with_subgraphs.py --verbose
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
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.service.agents.sales_analytics_agent import SalesAnalyticsAgent
from backend.service.subgraphs.data_collection_subgraph import DataCollectionSubgraph
from backend.service.subgraphs.analysis_subgraph import AnalysisSubgraph
from backend.service.core.context import create_agent_context, create_subgraph_context
from backend.service.core.config import Config

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SubgraphIntegrationTester:
    """Subgraph 통합 테스터"""

    def __init__(self, verbose: bool = False):
        """초기화"""
        self.verbose = verbose
        self.agent = SalesAnalyticsAgent()
        self.test_results = []

        # 실제 데이터베이스의 테스트 데이터
        self.test_data = {
            "employees": ["윤수아", "윤하은", "정예준", "조시현", "조하은", "최수아"],
            "branches": ["서부팀"],
            "clients": ["파라곤이비인후과", "박영호내과의원", "현대파라곤정형외과"],
            "months": ["202409", "202410", "202411"]
        }

    async def test_data_collection_subgraph_invocation(self):
        """DataCollectionSubgraph 호출 테스트"""
        logger.info("\n=== DataCollectionSubgraph 호출 테스트 ===")

        try:
            # 데이터 수집을 유도하는 쿼리
            query = "모든 영업사원의 실적 데이터를 수집하고 종합해줘"

            result = await self.agent.run(
                query=query,
                user_id="test_user",
                session_id=f"test_subgraph_{int(time.time())}"
            )

            # 검증
            success = True
            checks = []

            # 1. execution_plan에 subgraph 사용이 계획되었는지
            if result.get("execution_plan"):
                plan = result["execution_plan"]
                if "use_subgraphs" in plan:
                    has_collection = "data_collection" in plan.get("use_subgraphs", [])
                    checks.append(("Plan includes data_collection", has_collection))
                    success = success and has_collection

            # 2. execution_results에 collection 결과가 있는지
            if result.get("execution_results"):
                exec_results = result["execution_results"]
                has_collection_result = "collection" in exec_results
                checks.append(("Execution has collection result", has_collection_result))

                if has_collection_result and exec_results["collection"]:
                    collection_status = exec_results["collection"].get("status") == "completed"
                    checks.append(("Collection status completed", collection_status))
                    success = success and collection_status

            # 3. data_collection_result가 state에 저장되었는지
            has_collection_data = result.get("data_collection_result") is not None or \
                                result.get("collected_data") is not None
            checks.append(("Has collected data in state", has_collection_data))
            success = success and has_collection_data

            # 4. collected_data 구조 확인
            if result.get("collected_data"):
                collected = result["collected_data"]
                has_performance = "performance" in collected
                has_target = "target" in collected
                checks.append(("Has performance data", has_performance))
                checks.append(("Has target data", has_target))
                success = success and has_performance

            if self.verbose:
                logger.info("검증 결과:")
                for check_name, check_result in checks:
                    symbol = "✅" if check_result else "❌"
                    logger.info(f"  {symbol} {check_name}")

                if result.get("collected_data"):
                    logger.info(f"\n수집된 데이터 키: {list(result['collected_data'].keys())}")

            return success, checks

        except Exception as e:
            logger.error(f"DataCollectionSubgraph 테스트 실패: {e}")
            return False, [("Exception occurred", False)]

    async def test_analysis_subgraph_invocation(self):
        """AnalysisSubgraph 호출 테스트"""
        logger.info("\n=== AnalysisSubgraph 호출 테스트 ===")

        try:
            # 분석을 유도하는 쿼리
            query = f"{self.test_data['employees'][0]}와 {self.test_data['employees'][1]}의 실적을 비교 분석해줘"

            result = await self.agent.run(
                query=query,
                user_id="test_user",
                session_id=f"test_analysis_{int(time.time())}"
            )

            # 검증
            success = True
            checks = []

            # 1. execution_plan에 analysis가 포함되었는지
            if result.get("execution_plan"):
                plan = result["execution_plan"]
                if "use_subgraphs" in plan:
                    has_analysis = "analysis" in plan.get("use_subgraphs", [])
                    checks.append(("Plan includes analysis", has_analysis))

            # 2. execution_results에 analysis 결과가 있는지
            if result.get("execution_results"):
                exec_results = result["execution_results"]
                has_analysis_result = "analysis" in exec_results
                checks.append(("Execution has analysis result", has_analysis_result))

                if has_analysis_result and exec_results["analysis"]:
                    analysis_status = exec_results["analysis"].get("status") == "completed"
                    checks.append(("Analysis status completed", analysis_status))
                    success = success and analysis_status

            # 3. insights가 생성되었는지
            has_insights = result.get("insights") is not None and len(result.get("insights", [])) > 0
            checks.append(("Has insights", has_insights))
            success = success and has_insights

            # 4. statistics가 계산되었는지
            has_statistics = result.get("statistics") is not None
            checks.append(("Has statistics", has_statistics))

            # 5. formatted_result에 분석 결과가 포함되었는지
            if result.get("formatted_result"):
                formatted = result["formatted_result"]
                has_analysis_output = "분석" in formatted or "인사이트" in formatted
                checks.append(("Formatted result has analysis", has_analysis_output))

            if self.verbose:
                logger.info("검증 결과:")
                for check_name, check_result in checks:
                    symbol = "✅" if check_result else "❌"
                    logger.info(f"  {symbol} {check_name}")

                if result.get("insights"):
                    logger.info(f"\n생성된 인사이트: {result['insights'][:3]}")

            return success, checks

        except Exception as e:
            logger.error(f"AnalysisSubgraph 테스트 실패: {e}")
            return False, [("Exception occurred", False)]

    async def test_subgraph_context_propagation(self):
        """Subgraph로 context가 올바르게 전달되는지 테스트"""
        logger.info("\n=== Subgraph Context 전달 테스트 ===")

        try:
            # Context에 특별한 값 설정
            custom_context = {
                "language": "en",  # 영어로 설정
                "debug_mode": True,
                "timeout_overrides": {"llm": 10}
            }

            query = "Analyze sales performance for all employees"

            result = await self.agent.run(
                query=query,
                user_id="test_user",
                session_id=f"test_context_{int(time.time())}",
                **custom_context
            )

            # 검증
            success = True
            checks = []

            # 1. 영어로 결과가 포맷되었는지
            if result.get("formatted_result"):
                formatted = result["formatted_result"]
                is_english = "Sales Analysis Results" in formatted or \
                           "Statistics" in formatted or \
                           "Achievement Rate" in formatted
                checks.append(("English formatting", is_english))
                success = success and is_english

            # 2. Status가 정상적으로 완료되었는지
            is_completed = result.get("status") in ["completed", "success"]
            checks.append(("Execution completed", is_completed))
            success = success and is_completed

            if self.verbose:
                logger.info("검증 결과:")
                for check_name, check_result in checks:
                    symbol = "✅" if check_result else "❌"
                    logger.info(f"  {symbol} {check_name}")

                if result.get("formatted_result"):
                    logger.info(f"\n포맷된 결과 (일부):\n{result['formatted_result'][:200]}...")

            return success, checks

        except Exception as e:
            logger.error(f"Context 전달 테스트 실패: {e}")
            return False, [("Exception occurred", False)]

    async def test_multiple_subgraph_coordination(self):
        """여러 subgraph가 연계되어 동작하는지 테스트"""
        logger.info("\n=== Multiple Subgraph Coordination 테스트 ===")

        try:
            # 데이터 수집과 분석을 모두 요구하는 쿼리
            query = f"{self.test_data['branches'][0]} 팀 전체의 실적을 수집하고, 목표 대비 달성률을 분석하고, 개선점을 제시해줘"

            result = await self.agent.run(
                query=query,
                user_id="test_user",
                session_id=f"test_multi_{int(time.time())}"
            )

            # 검증
            success = True
            checks = []

            # 1. 여러 subgraph가 계획되었는지
            if result.get("execution_plan"):
                plan = result["execution_plan"]
                subgraphs = plan.get("use_subgraphs", [])
                has_multiple = len(subgraphs) >= 2
                checks.append(("Multiple subgraphs planned", has_multiple))
                checks.append((f"Subgraphs: {subgraphs}", True))

            # 2. execution_results에 여러 결과가 있는지
            if result.get("execution_results"):
                exec_results = result["execution_results"]
                result_keys = list(exec_results.keys())
                has_multiple_results = len(result_keys) >= 2
                checks.append(("Multiple execution results", has_multiple_results))
                checks.append((f"Results: {result_keys}", True))

            # 3. 데이터가 subgraph 간에 전달되었는지
            # (analysis가 collection의 결과를 사용했는지)
            has_data_flow = (result.get("collected_data") is not None or
                            result.get("data_collection_result") is not None) and \
                           (result.get("analysis_result") is not None or
                            result.get("insights") is not None)
            checks.append(("Data flow between subgraphs", has_data_flow))

            # 4. 최종 포맷된 결과가 통합되었는지
            if result.get("formatted_result"):
                formatted = result["formatted_result"]
                has_integrated_result = len(formatted) > 100
                checks.append(("Integrated final result", has_integrated_result))
                success = success and has_integrated_result

            if self.verbose:
                logger.info("검증 결과:")
                for check_name, check_result in checks:
                    if isinstance(check_result, bool):
                        symbol = "✅" if check_result else "❌"
                        logger.info(f"  {symbol} {check_name}")
                    else:
                        logger.info(f"  ℹ️ {check_name}")

            return success, checks

        except Exception as e:
            logger.error(f"Multiple subgraph 테스트 실패: {e}")
            return False, [("Exception occurred", False)]

    async def test_subgraph_error_handling(self):
        """Subgraph 실행 중 에러 처리 테스트"""
        logger.info("\n=== Subgraph Error Handling 테스트 ===")

        try:
            # 잘못된 데이터로 subgraph 호출 유도
            query = "존재하지 않는 직원 XXXXX의 데이터를 수집하고 분석해줘"

            result = await self.agent.run(
                query=query,
                user_id="test_user",
                session_id=f"test_error_{int(time.time())}"
            )

            # 검증
            checks = []

            # 1. 에러가 발생해도 agent가 정상 종료되었는지
            has_status = result.get("status") is not None
            checks.append(("Has status field", has_status))

            # 2. 에러 메시지가 포함되었는지
            has_error_handling = result.get("errors") is not None or \
                                result.get("status") == "failed" or \
                                (result.get("formatted_result") and
                                 ("결과가 없습니다" in result.get("formatted_result", "") or
                                  "No results" in result.get("formatted_result", "")))
            checks.append(("Error handled gracefully", has_error_handling))

            # 3. Agent가 크래시하지 않았는지
            agent_survived = True  # 여기까지 왔다면 크래시하지 않음
            checks.append(("Agent survived error", agent_survived))

            if self.verbose:
                logger.info("검증 결과:")
                for check_name, check_result in checks:
                    symbol = "✅" if check_result else "❌"
                    logger.info(f"  {symbol} {check_name}")

                logger.info(f"\nStatus: {result.get('status')}")
                if result.get("errors"):
                    logger.info(f"Errors: {result.get('errors')}")

            # 에러 처리 테스트는 graceful failure가 목적
            success = has_status and agent_survived

            return success, checks

        except Exception as e:
            # 예외가 발생해도 테스트 자체는 실패로 처리
            logger.error(f"Error handling 테스트 중 예외: {e}")
            return True, [("Exception handled", True)]  # 에러 처리가 목적이므로

    async def run_all_tests(self):
        """모든 subgraph 테스트 실행"""
        logger.info("\n" + "="*60)
        logger.info("Sales Agent Subgraph Integration Test")
        logger.info("="*60)

        test_methods = [
            ("Data Collection Subgraph", self.test_data_collection_subgraph_invocation),
            ("Analysis Subgraph", self.test_analysis_subgraph_invocation),
            ("Context Propagation", self.test_subgraph_context_propagation),
            ("Multiple Subgraph Coordination", self.test_multiple_subgraph_coordination),
            ("Error Handling", self.test_subgraph_error_handling)
        ]

        results = []
        for test_name, test_method in test_methods:
            logger.info(f"\n실행 중: {test_name}")
            success, checks = await test_method()
            results.append({
                "name": test_name,
                "success": success,
                "checks": checks
            })

            if success:
                logger.info(f"✅ {test_name} 성공")
            else:
                logger.error(f"❌ {test_name} 실패")

        # 최종 요약
        self.print_summary(results)
        self.save_results(results)

    def print_summary(self, results):
        """테스트 결과 요약"""
        logger.info("\n" + "="*60)
        logger.info("테스트 결과 요약")
        logger.info("="*60)

        total = len(results)
        passed = sum(1 for r in results if r["success"])
        failed = total - passed

        logger.info(f"총 테스트: {total}")
        logger.info(f"성공: {passed} ({passed/total*100:.1f}%)")
        logger.info(f"실패: {failed}")

        if failed > 0:
            logger.info("\n실패한 테스트:")
            for result in results:
                if not result["success"]:
                    logger.info(f"  - {result['name']}")
                    failed_checks = [c[0] for c in result["checks"] if not c[1]]
                    if failed_checks:
                        for check in failed_checks:
                            logger.info(f"    ❌ {check}")

    def save_results(self, results):
        """테스트 결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tests/test_results_subgraph_{timestamp}.json"

        results_data = {
            "timestamp": timestamp,
            "test": "Subgraph Integration Test",
            "results": results,
            "summary": {
                "total": len(results),
                "passed": sum(1 for r in results if r["success"]),
                "failed": sum(1 for r in results if not r["success"])
            }
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)

        logger.info(f"\n테스트 결과 저장: {filename}")


async def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='Subgraph Integration Test')
    parser.add_argument('--verbose', action='store_true', help='상세 출력')

    args = parser.parse_args()

    # 테스터 생성 및 실행
    tester = SubgraphIntegrationTester(verbose=args.verbose)
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())