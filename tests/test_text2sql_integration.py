"""
Text2SQL Tool Integration Test
Agent 내부에서 Text2SQL tool이 정확히 동작하는지 테스트
LLM 모드와 Rule-based 모드 모두 검증

실행 방법:
    python tests/test_text2sql_integration.py
    python tests/test_text2sql_integration.py --verbose
    python tests/test_text2sql_integration.py --mode llm
    python tests/test_text2sql_integration.py --mode rule
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import argparse
import sqlite3
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.service.agents.sales_analytics_agent import SalesAnalyticsAgent
from backend.service.tools.text2sql_tool import get_text2sql_tool
from backend.service.tools.sql_executor import SQLExecutor
from backend.service.core.config import Config

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Text2SQLIntegrationTester:
    """Text2SQL Integration 테스터"""

    def __init__(self, verbose: bool = False, mode: str = "both"):
        """
        초기화

        Args:
            verbose: 상세 출력 여부
            mode: 테스트 모드 (llm, rule, both)
        """
        self.verbose = verbose
        self.mode = mode
        self.agent = SalesAnalyticsAgent()
        self.text2sql_tool = get_text2sql_tool()
        self.sql_executor = SQLExecutor()

        # 실제 데이터베이스의 테스트 데이터
        self.test_data = {
            "employees": ["윤수아", "윤하은", "정예준", "조시현", "조하은", "최수아"],
            "branches": ["서부팀"],
            "clients": ["파라곤이비인후과", "박영호내과의원", "현대파라곤정형외과"],
            "months": ["202409", "202410", "202411"],
            "columns": ["사번", "담당자", "거래처ID", "품목"] +
                      [f"{year}{month:02d}" for year in [2022, 2023, 2024]
                       for month in range(1, 13) if f"{year}{month:02d}" <= "202411"]
        }

    def get_test_queries(self) -> List[Tuple[str, Dict[str, Any]]]:
        """테스트 쿼리 목록"""
        queries = [
            # 단순 조회
            (
                f"{self.test_data['employees'][0]}의 2024년 11월 매출 조회",
                {
                    "expected_keywords": ["SELECT", "담당자", "202411", "윤수아"],
                    "expected_database": "sales_performance",
                    "complexity": "simple"
                }
            ),
            # 시간 범위 조회
            (
                f"{self.test_data['employees'][1]}의 최근 3개월 매출 조회",
                {
                    "expected_keywords": ["SELECT", "담당자", "202409", "202410", "202411"],
                    "expected_database": "sales_performance",
                    "complexity": "medium"
                }
            ),
            # 거래처 기반 조회
            (
                f"{self.test_data['clients'][0]} 거래처의 월별 매출 현황",
                {
                    "expected_keywords": ["SELECT", "거래처ID", "파라곤이비인후과"],
                    "expected_database": "sales_performance",
                    "complexity": "medium"
                }
            ),
            # 집계 쿼리
            (
                "전체 영업팀의 2024년 11월 총 매출",
                {
                    "expected_keywords": ["SELECT", "SUM", "202411"],
                    "expected_database": "sales_performance",
                    "complexity": "medium"
                }
            ),
            # 비교 쿼리
            (
                f"{self.test_data['employees'][0]}와 {self.test_data['employees'][2]}의 실적 비교",
                {
                    "expected_keywords": ["SELECT", "담당자", "윤수아", "정예준"],
                    "expected_database": "sales_performance",
                    "complexity": "complex"
                }
            ),
            # 순위 쿼리
            (
                "2024년 10월 상위 5명 영업사원",
                {
                    "expected_keywords": ["SELECT", "202410", "ORDER BY", "LIMIT"],
                    "expected_database": "sales_performance",
                    "complexity": "complex"
                }
            ),
            # JOIN 쿼리
            (
                f"{self.test_data['employees'][3]}의 목표 대비 달성률",
                {
                    "expected_keywords": ["SELECT", "담당자", "조시현"],
                    "expected_database": "sales_performance",
                    "complexity": "complex"
                }
            ),
            # 품목별 분석
            (
                "품목별 매출 TOP 10",
                {
                    "expected_keywords": ["SELECT", "품목", "GROUP BY", "ORDER BY"],
                    "expected_database": "sales_performance",
                    "complexity": "complex"
                }
            ),
            # 트렌드 분석
            (
                f"{self.test_data['branches'][0]} 팀의 월별 매출 추이",
                {
                    "expected_keywords": ["SELECT", "서부팀"],
                    "expected_database": "sales_performance",
                    "complexity": "complex"
                }
            ),
            # 연도별 비교
            (
                "2023년과 2024년 매출 비교",
                {
                    "expected_keywords": ["SELECT", "2023", "2024"],
                    "expected_database": "sales_performance",
                    "complexity": "complex"
                }
            )
        ]

        return queries

    async def test_text2sql_in_agent_flow(self):
        """Agent 플로우 내에서 Text2SQL 테스트"""
        logger.info("\n=== Text2SQL in Agent Flow 테스트 ===")

        test_queries = self.get_test_queries()[:5]  # 처음 5개만
        results = []

        for i, (query, expected) in enumerate(test_queries, 1):
            logger.info(f"\n[{i}/{len(test_queries)}] 쿼리: {query}")

            try:
                # Agent 실행
                result = await self.agent.run(
                    query=query,
                    user_id="test_user",
                    session_id=f"test_text2sql_{int(time.time())}_{i}"
                )

                # SQL 생성 확인
                generated_sql = result.get("generated_sql")
                success = generated_sql is not None

                checks = {
                    "has_sql": generated_sql is not None,
                    "is_select": "SELECT" in generated_sql if generated_sql else False,
                    "has_target_db": result.get("target_database") is not None,
                    "correct_db": result.get("target_database") == expected["expected_database"]
                }

                # 예상 키워드 확인
                if generated_sql:
                    for keyword in expected["expected_keywords"]:
                        if keyword not in generated_sql:
                            checks[f"has_{keyword}"] = False
                            success = False

                # SQL 실행 결과 확인
                if result.get("sql_result"):
                    checks["has_result"] = True
                    checks["result_count"] = len(result.get("sql_result", []))

                results.append({
                    "query": query,
                    "success": success,
                    "sql": generated_sql,
                    "database": result.get("target_database"),
                    "checks": checks
                })

                if self.verbose:
                    logger.info(f"생성된 SQL:\n{generated_sql}")
                    logger.info(f"대상 DB: {result.get('target_database')}")
                    logger.info(f"검증: {checks}")

            except Exception as e:
                logger.error(f"에러: {e}")
                results.append({
                    "query": query,
                    "success": False,
                    "error": str(e)
                })

        # 요약
        success_count = sum(1 for r in results if r.get("success"))
        logger.info(f"\n결과: {success_count}/{len(results)} 성공")

        return results

    async def test_text2sql_direct_tool(self):
        """Text2SQL Tool 직접 호출 테스트"""
        logger.info("\n=== Text2SQL Tool Direct 테스트 ===")

        test_queries = self.get_test_queries()
        results = []

        for i, (query, expected) in enumerate(test_queries, 1):
            logger.info(f"\n[{i}/{len(test_queries)}] 쿼리: {query}")

            try:
                # Text2SQL Tool 직접 호출
                result = await self.text2sql_tool.generate_sql(
                    query=query,
                    context={
                        "user_id": "test",
                        "session_id": f"direct_{i}",
                        "language": "ko"
                    }
                )

                # 검증
                checks = {
                    "has_sql": result.get("sql") is not None,
                    "has_explanation": result.get("explanation") is not None,
                    "has_database": result.get("database") is not None,
                    "has_confidence": result.get("confidence") is not None,
                    "is_valid": result.get("is_valid", False),
                    "method": result.get("method")
                }

                # SQL 유효성 검증
                if result.get("sql"):
                    sql = result["sql"]

                    # 키워드 확인
                    for keyword in expected["expected_keywords"]:
                        checks[f"has_{keyword}"] = keyword in sql

                    # SQL 실행 테스트
                    if checks["is_valid"]:
                        exec_result, error = self.sql_executor.execute_query(
                            sql=sql,
                            db_name=result.get("database", "sales_performance")
                        )
                        checks["executable"] = error is None
                        if exec_result:
                            checks["row_count"] = len(exec_result)

                success = checks.get("has_sql") and checks.get("is_valid")

                results.append({
                    "query": query,
                    "success": success,
                    "result": result,
                    "checks": checks
                })

                if self.verbose:
                    logger.info(f"방법: {result.get('method')}")
                    logger.info(f"SQL: {result.get('sql')}")
                    logger.info(f"설명: {result.get('explanation')}")
                    logger.info(f"신뢰도: {result.get('confidence')}")

            except Exception as e:
                logger.error(f"에러: {e}")
                results.append({
                    "query": query,
                    "success": False,
                    "error": str(e)
                })

        # 요약
        success_count = sum(1 for r in results if r.get("success"))
        logger.info(f"\n결과: {success_count}/{len(results)} 성공")

        return results

    async def test_sql_validation_and_execution(self):
        """생성된 SQL의 유효성과 실행 가능성 테스트"""
        logger.info("\n=== SQL Validation and Execution 테스트 ===")

        test_cases = [
            {
                "query": f"{self.test_data['employees'][0]}의 모든 매출 데이터",
                "validate_only": False
            },
            {
                "query": "DELETE FROM sales_performance",  # 위험한 쿼리
                "validate_only": True
            },
            {
                "query": f"{self.test_data['employees'][1]}의 202411 매출",
                "validate_only": False
            }
        ]

        results = []

        for case in test_cases:
            logger.info(f"\n쿼리: {case['query']}")

            try:
                # Text2SQL 생성
                sql_result = await self.text2sql_tool.generate_sql(case["query"])
                sql = sql_result.get("sql")

                if not sql:
                    results.append({
                        "query": case["query"],
                        "success": False,
                        "reason": "No SQL generated"
                    })
                    continue

                # 유효성 검증
                is_valid = self.text2sql_tool.validate_sql(sql)
                logger.info(f"SQL 유효성: {is_valid}")

                # 실행 (안전한 쿼리만)
                if not case["validate_only"] and is_valid:
                    exec_result, error = self.sql_executor.execute_query(
                        sql=sql,
                        db_name=sql_result.get("database", "sales_performance")
                    )

                    results.append({
                        "query": case["query"],
                        "success": error is None,
                        "sql": sql,
                        "is_valid": is_valid,
                        "executable": error is None,
                        "row_count": len(exec_result) if exec_result else 0,
                        "error": error
                    })

                    if self.verbose and exec_result:
                        logger.info(f"실행 결과: {len(exec_result)} rows")
                        if exec_result:
                            logger.info(f"첫 번째 행: {exec_result[0]}")
                else:
                    results.append({
                        "query": case["query"],
                        "success": is_valid,
                        "sql": sql,
                        "is_valid": is_valid,
                        "validate_only": True
                    })

            except Exception as e:
                logger.error(f"에러: {e}")
                results.append({
                    "query": case["query"],
                    "success": False,
                    "error": str(e)
                })

        return results

    async def test_llm_vs_rule_based(self):
        """LLM 모드와 Rule-based 모드 비교"""
        logger.info("\n=== LLM vs Rule-based 비교 테스트 ===")

        if self.mode == "llm" and not os.getenv("OPENAI_API_KEY"):
            logger.warning("OpenAI API key가 없어 LLM 테스트 건너뜀")
            return []

        test_queries = [
            f"{self.test_data['employees'][0]}의 2024년 11월 실적",
            "상위 5명의 영업사원",
            f"{self.test_data['clients'][0]} 거래처 매출"
        ]

        results = []

        for query in test_queries:
            logger.info(f"\n쿼리: {query}")

            comparison = {"query": query}

            # LLM 모드 테스트
            if self.mode in ["llm", "both"] and os.getenv("OPENAI_API_KEY"):
                try:
                    # LLM 모드 강제
                    with_llm = await self.text2sql_tool.generate_sql(query)
                    if with_llm.get("method") == "llm":
                        comparison["llm"] = {
                            "sql": with_llm.get("sql"),
                            "confidence": with_llm.get("confidence"),
                            "valid": with_llm.get("is_valid")
                        }
                except Exception as e:
                    comparison["llm"] = {"error": str(e)}

            # Rule-based 모드 테스트
            if self.mode in ["rule", "both"]:
                try:
                    # Rule-based 강제 (LLM 비활성화)
                    original_use_llm = self.text2sql_tool.use_llm
                    self.text2sql_tool.use_llm = False

                    with_rule = await self.text2sql_tool.generate_sql(query)
                    comparison["rule"] = {
                        "sql": with_rule.get("sql"),
                        "confidence": with_rule.get("confidence"),
                        "valid": with_rule.get("is_valid")
                    }

                    # 복원
                    self.text2sql_tool.use_llm = original_use_llm

                except Exception as e:
                    comparison["rule"] = {"error": str(e)}

            results.append(comparison)

            if self.verbose:
                if "llm" in comparison:
                    logger.info(f"LLM SQL: {comparison['llm'].get('sql')}")
                if "rule" in comparison:
                    logger.info(f"Rule SQL: {comparison['rule'].get('sql')}")

        return results

    async def test_complex_queries(self):
        """복잡한 쿼리 처리 테스트"""
        logger.info("\n=== Complex Queries 테스트 ===")

        complex_queries = [
            {
                "query": f"{self.test_data['employees'][0]}와 {self.test_data['employees'][1]}의 " +
                        "최근 3개월 실적을 비교하고 차이를 계산해줘",
                "expected_features": ["JOIN", "GROUP BY", "calculation"]
            },
            {
                "query": f"{self.test_data['branches'][0]} 팀에서 목표 달성률이 가장 높은 " +
                        "상위 3명과 하위 3명의 실적 비교",
                "expected_features": ["subquery", "ORDER BY", "LIMIT"]
            },
            {
                "query": "2024년 분기별 매출 추이와 전년 동기 대비 성장률 계산",
                "expected_features": ["time_series", "calculation", "comparison"]
            }
        ]

        results = []

        for case in complex_queries:
            logger.info(f"\n복잡한 쿼리: {case['query']}")

            try:
                # Agent를 통한 처리
                agent_result = await self.agent.run(
                    query=case["query"],
                    user_id="test_user",
                    session_id=f"complex_{int(time.time())}"
                )

                # 결과 분석
                has_sql = agent_result.get("generated_sql") is not None
                has_plan = agent_result.get("execution_plan") is not None
                has_result = agent_result.get("formatted_result") is not None

                # 복잡도 확인
                complexity_score = 0
                if has_sql:
                    sql = agent_result["generated_sql"]
                    if "JOIN" in sql: complexity_score += 1
                    if "GROUP BY" in sql: complexity_score += 1
                    if "ORDER BY" in sql: complexity_score += 1
                    if "WHERE" in sql: complexity_score += 1
                    if "SUM" in sql or "COUNT" in sql: complexity_score += 1

                results.append({
                    "query": case["query"],
                    "success": has_sql and has_result,
                    "has_sql": has_sql,
                    "has_plan": has_plan,
                    "has_result": has_result,
                    "complexity_score": complexity_score,
                    "sql_length": len(agent_result.get("generated_sql", ""))
                })

                if self.verbose and has_sql:
                    logger.info(f"복잡도 점수: {complexity_score}")
                    logger.info(f"SQL 길이: {len(agent_result['generated_sql'])}")
                    logger.info(f"SQL:\n{agent_result['generated_sql'][:300]}...")

            except Exception as e:
                logger.error(f"에러: {e}")
                results.append({
                    "query": case["query"],
                    "success": False,
                    "error": str(e)
                })

        return results

    async def run_all_tests(self):
        """모든 테스트 실행"""
        logger.info("\n" + "="*60)
        logger.info("Text2SQL Integration Test")
        logger.info("="*60)

        all_results = {}

        # 1. Agent 플로우 테스트
        logger.info("\n[1/5] Agent Flow Test")
        all_results["agent_flow"] = await self.test_text2sql_in_agent_flow()

        # 2. Direct Tool 테스트
        logger.info("\n[2/5] Direct Tool Test")
        all_results["direct_tool"] = await self.test_text2sql_direct_tool()

        # 3. Validation & Execution 테스트
        logger.info("\n[3/5] Validation & Execution Test")
        all_results["validation"] = await self.test_sql_validation_and_execution()

        # 4. LLM vs Rule-based 비교
        if self.mode != "skip_comparison":
            logger.info("\n[4/5] LLM vs Rule-based Test")
            all_results["comparison"] = await self.test_llm_vs_rule_based()

        # 5. Complex Queries 테스트
        logger.info("\n[5/5] Complex Queries Test")
        all_results["complex"] = await self.test_complex_queries()

        # 결과 요약
        self.print_summary(all_results)
        self.save_results(all_results)

    def print_summary(self, all_results):
        """테스트 결과 요약"""
        logger.info("\n" + "="*60)
        logger.info("테스트 결과 요약")
        logger.info("="*60)

        for test_name, results in all_results.items():
            if results:
                success_count = sum(1 for r in results if r.get("success"))
                total = len(results)
                logger.info(f"\n{test_name}:")
                logger.info(f"  성공: {success_count}/{total} ({success_count/total*100:.1f}%)")

    def save_results(self, all_results):
        """테스트 결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tests/test_results_text2sql_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)

        logger.info(f"\n테스트 결과 저장: {filename}")


async def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='Text2SQL Integration Test')
    parser.add_argument('--verbose', action='store_true', help='상세 출력')
    parser.add_argument('--mode', choices=['llm', 'rule', 'both', 'skip_comparison'],
                       default='both', help='테스트 모드')

    args = parser.parse_args()

    # 테스터 생성 및 실행
    tester = Text2SQLIntegrationTester(verbose=args.verbose, mode=args.mode)
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())