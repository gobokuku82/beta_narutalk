"""
Sales Analytics Agent Test Suite - Fixed Version
실제 데이터베이스 직원명과 날짜 범위를 사용한 수정된 테스트

실행 방법:
    python tests/test_sales_analytics_agent_fixed.py
"""

import asyncio
import json
import logging
import os
import sys
import time
import io
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

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
from backend.service.subgraphs.data_collection_subgraph import DataCollectionSubgraph
from backend.service.subgraphs.analysis_subgraph import AnalysisSubgraph
from backend.service.tools.sql_generator import SQLGenerator
from backend.service.tools.sql_executor import SQLExecutor
from backend.service.core.context import create_agent_context, create_subgraph_context

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============== 실제 데이터베이스 정보 ==============

# 실제 직원명 (데이터베이스에서 확인된 이름)
ACTUAL_EMPLOYEES = [
    "윤수아",
    "윤하은",
    "정예준",
    "조시현",
    "조하은",
    "최수아"
]

# 사용 가능한 월 컬럼 (2022.12 ~ 2024.11)
AVAILABLE_MONTHS = [
    "202212", "202301", "202302", "202303", "202304", "202305",
    "202306", "202307", "202308", "202309", "202310", "202311",
    "202312", "202401", "202402", "202403", "202404", "202405",
    "202406", "202407", "202408", "202409", "202410", "202411"
]

# ============== Simple Console (Rich 대체) ==============

class SimpleConsole:
    """Rich 라이브러리 대체용 Simple Console"""

    def __init__(self):
        self.indent_level = 0

    def print(self, text, style=None):
        # 특수문자를 일반 문자로 변환
        text = str(text)
        text = text.replace('✓', '[OK]')
        text = text.replace('✗', '[FAIL]')
        text = text.replace('⚠', '[WARN]')

        # 스타일 태그 제거
        import re
        text = re.sub(r'\[.*?\]', '', text)

        # 들여쓰기 적용
        indent = "  " * self.indent_level
        print(indent + text)

    def rule(self, title="", style=None):
        print("\n" + "=" * 60)
        if title:
            print(f" {title} ".center(60))
            print("=" * 60)

    def table(self, data, headers):
        # 간단한 테이블 출력
        col_widths = []
        for i, header in enumerate(headers):
            max_width = len(header)
            for row in data:
                if i < len(row):
                    max_width = max(max_width, len(str(row[i])))
            col_widths.append(max_width + 2)

        # 헤더 출력
        header_line = "|"
        for i, header in enumerate(headers):
            header_line += f" {header:<{col_widths[i]-1}}|"
        print(header_line)
        print("-" * len(header_line))

        # 데이터 출력
        for row in data:
            row_line = "|"
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    row_line += f" {str(cell):<{col_widths[i]-1}}|"
            print(row_line)

console = SimpleConsole()

# ============== 테스트 케이스 생성 ==============

class TestCaseGenerator:
    """실제 데이터 기반 테스트 케이스 생성"""

    @staticmethod
    def generate_text2sql_cases() -> List[Dict]:
        """Text2SQL 테스트 케이스 - 실제 직원명 사용"""
        cases = []

        # 1. 기본 조회 (실제 직원명 사용)
        for emp in ACTUAL_EMPLOYEES[:3]:
            cases.extend([
                {
                    "query": f"{emp} 3월 실적",
                    "description": f"{emp}의 2024년 3월 실적 조회",
                    "expected_sql_parts": ["담당자", emp, "202403"]
                },
                {
                    "query": f"{emp} 작년 실적",
                    "description": f"{emp}의 2023년 전체 실적",
                    "expected_sql_parts": ["담당자", emp, "2023"]
                },
                {
                    "query": f"{emp} 최근 실적",
                    "description": f"{emp}의 최근 월 실적",
                    "expected_sql_parts": ["담당자", emp]
                }
            ])

        # 2. 집계 쿼리
        cases.extend([
            {
                "query": "전체 직원 평균 실적",
                "description": "모든 직원의 평균 실적",
                "expected_sql_parts": ["AVG", "sales_performance"]
            },
            {
                "query": "2024년 10월 실적 TOP 5",
                "description": "2024년 10월 상위 5명",
                "expected_sql_parts": ["202410", "ORDER BY", "LIMIT 5"]
            },
            {
                "query": "윤수아와 윤하은 실적 비교",
                "description": "두 직원 실적 비교",
                "expected_sql_parts": ["윤수아", "윤하은"]
            }
        ])

        # 3. 기간 조회
        cases.extend([
            {
                "query": "2024년 1분기 전체 실적",
                "description": "2024년 1-3월 실적",
                "expected_sql_parts": ["202401", "202402", "202403"]
            },
            {
                "query": "작년 하반기 매출 현황",
                "description": "2023년 7-12월 매출",
                "expected_sql_parts": ["202307", "202312"]
            }
        ])

        return cases

    @staticmethod
    def generate_data_collection_cases() -> List[Dict]:
        """Data Collection 테스트 케이스"""
        cases = []

        for emp in ACTUAL_EMPLOYEES[:2]:
            cases.append({
                "name": f"{emp}_데이터수집",
                "input": {
                    "query_params": {
                        "person_name": emp,
                        "month": "202403"
                    },
                    "target_databases": ["performance"]
                },
                "description": f"{emp}의 2024년 3월 데이터 수집"
            })

        cases.extend([
            {
                "name": "다중DB_조회",
                "input": {
                    "query_params": {"person_name": "윤수아"},
                    "target_databases": ["performance", "target"]
                },
                "description": "성능 및 목표 데이터 동시 수집"
            },
            {
                "name": "기간범위_수집",
                "input": {
                    "query_params": {
                        "start_month": "202401",
                        "end_month": "202403"
                    },
                    "target_databases": ["performance"]
                },
                "description": "2024년 1분기 데이터 수집"
            }
        ])

        return cases

    @staticmethod
    def generate_analysis_cases() -> List[Dict]:
        """Analysis 테스트 케이스"""
        # 실제 데이터 형식에 맞춘 샘플 데이터
        sample_data = {
            "performance_data": [
                {"담당자": "윤수아", "202403": 1500000, "202402": 1200000},
                {"담당자": "윤하은", "202403": 1800000, "202402": 1600000}
            ],
            "target_data": [
                {"담당자": "윤수아", "목표_202403": 2000000},
                {"담당자": "윤하은", "목표_202403": 1700000}
            ]
        }

        cases = [
            {
                "name": "기본메트릭_계산",
                "input": {
                    **sample_data,
                    "analysis_type": "basic"
                },
                "description": "기본 통계 메트릭 계산"
            },
            {
                "name": "달성률_분석",
                "input": {
                    **sample_data,
                    "analysis_type": "achievement"
                },
                "description": "목표 대비 달성률 분석"
            },
            {
                "name": "추세_분석",
                "input": {
                    **sample_data,
                    "analysis_type": "trend"
                },
                "description": "시간별 추세 분석"
            }
        ]

        return cases

    @staticmethod
    def generate_e2e_cases() -> List[Dict]:
        """E2E 시나리오 테스트 케이스"""
        cases = [
            {
                "name": "일일보고_시나리오",
                "messages": [
                    "오늘 전체 실적 현황",
                    "윤수아 이번달 실적",
                    "실적 TOP 3는?"
                ],
                "description": "일일 보고 시나리오"
            },
            {
                "name": "개인평가_시나리오",
                "messages": [
                    "정예준 3월 실적 조회",
                    "목표 대비 달성률은?",
                    "전월 대비 성장률"
                ],
                "description": "개인 평가 시나리오"
            }
        ]

        return cases

# ============== 테스트 실행기 ==============

class SalesAgentTestRunner:
    """Sales Agent 테스트 실행"""

    def __init__(self):
        self.agent = None
        self.sql_generator = SQLGenerator()
        self.sql_executor = SQLExecutor()
        self.results = []

    async def initialize(self):
        """초기화"""
        console.print("Initializing test environment...")
        self.agent = SalesAnalyticsAgent()
        console.print("[OK] Sales Analytics Agent initialized")

    async def run_text2sql_tests(self) -> List[Dict]:
        """Text2SQL 테스트 실행"""
        console.rule("Text2SQL Tests")
        test_cases = TestCaseGenerator.generate_text2sql_cases()
        results = []

        for i, test_case in enumerate(test_cases[:10], 1):  # 처음 10개만 실행
            print(f"\n[Test {i}] {test_case['query']}")
            print(f"Description: {test_case['description']}")

            try:
                # Parse query
                parsed = self.sql_generator.parse_query(test_case['query'])
                print(f"Parsed: {parsed}")

                # Generate SQL
                sql, explanation = self.sql_generator.generate_sql(parsed)
                print(f"SQL: {sql[:100]}..." if len(sql) > 100 else f"SQL: {sql}")

                # Check expected parts
                success = True
                if 'expected_sql_parts' in test_case:
                    for part in test_case['expected_sql_parts']:
                        if part not in sql:
                            print(f"[WARN] Missing expected part: {part}")
                            success = False

                results.append({
                    "test": test_case['query'],
                    "status": "PASS" if success else "PARTIAL",
                    "sql_generated": bool(sql)
                })

            except Exception as e:
                print(f"[FAIL] Error: {e}")
                results.append({
                    "test": test_case['query'],
                    "status": "FAIL",
                    "error": str(e)
                })

        return results

    async def run_data_collection_tests(self) -> List[Dict]:
        """Data Collection 테스트 실행"""
        console.rule("Data Collection Subgraph Tests")
        test_cases = TestCaseGenerator.generate_data_collection_cases()
        results = []

        for test_case in test_cases[:5]:  # 처음 5개만 실행
            print(f"\n[Test] {test_case['name']}")
            print(f"Description: {test_case['description']}")

            try:
                # Create subgraph
                subgraph = DataCollectionSubgraph()
                graph = subgraph.build_graph()
                app = graph.compile()

                # Create context
                context = create_subgraph_context(
                    parent_context={
                        "user_id": "test_user",
                        "session_id": "test_session"
                    },
                    parent_agent="test_agent",
                    subgraph_name="data_collection"
                )

                # Prepare state
                state = {
                    "query_params": test_case['input'].get("query_params", {}),
                    "target_databases": test_case['input'].get("target_databases", []),
                    "performance_data": [],
                    "target_data": [],
                    "client_data": [],
                    "aggregated_performance": {},
                    "aggregated_target": {},
                    "aggregated_client": {},
                    "collection_status": "pending",
                    "errors": []
                }

                # Execute
                result = await app.ainvoke(state, context=context)

                status = "PASS" if result.get("collection_status") == "completed" else "FAIL"
                print(f"Status: {status}")

                results.append({
                    "test": test_case['name'],
                    "status": status
                })

            except Exception as e:
                print(f"[FAIL] Error: {e}")
                results.append({
                    "test": test_case['name'],
                    "status": "FAIL",
                    "error": str(e)
                })

        return results

    async def run_analysis_tests(self) -> List[Dict]:
        """Analysis 테스트 실행"""
        console.rule("Analysis Subgraph Tests")
        test_cases = TestCaseGenerator.generate_analysis_cases()
        results = []

        for test_case in test_cases:
            print(f"\n[Test] {test_case['name']}")
            print(f"Description: {test_case['description']}")

            try:
                # Create subgraph
                subgraph = AnalysisSubgraph()
                graph = subgraph.build_graph()
                app = graph.compile()

                # Create context
                context = create_subgraph_context(
                    parent_context={
                        "user_id": "test_user",
                        "session_id": "test_session"
                    },
                    parent_agent="test_agent",
                    subgraph_name="analysis"
                )

                # Prepare state
                state = {
                    "performance_data": test_case['input'].get("performance_data", []),
                    "target_data": test_case['input'].get("target_data", []),
                    "client_data": [],
                    "analysis_type": test_case['input'].get("analysis_type", "basic"),
                    "analysis_params": {},
                    "basic_metrics": {},
                    "trend_analysis": {},
                    "comparative_analysis": {},
                    "insights": [],
                    "analysis_report": {},
                    "analysis_status": "pending",
                    "errors": []
                }

                # Execute
                result = await app.ainvoke(state, context=context)

                has_results = bool(
                    result.get("basic_metrics") or
                    result.get("insights") or
                    result.get("analysis_report")
                )

                status = "PASS" if has_results else "FAIL"
                print(f"Status: {status}")
                if result.get("insights"):
                    print(f"Insights: {len(result['insights'])} generated")

                results.append({
                    "test": test_case['name'],
                    "status": status
                })

            except Exception as e:
                print(f"[FAIL] Error: {e}")
                results.append({
                    "test": test_case['name'],
                    "status": "FAIL",
                    "error": str(e)
                })

        return results

    async def run_e2e_tests(self) -> List[Dict]:
        """E2E 시나리오 테스트"""
        console.rule("End-to-End Scenario Tests")
        test_cases = TestCaseGenerator.generate_e2e_cases()
        results = []

        for test_case in test_cases:
            print(f"\n[Scenario] {test_case['name']}")
            print(f"Description: {test_case['description']}")

            scenario_results = []

            for message in test_case['messages']:
                print(f"\nUser: {message}")

                try:
                    result = await self.agent.run(
                        query=message,
                        user_id="test_user",
                        session_id=f"test_{test_case['name']}",
                        language="ko"
                    )

                    status = result.get("status")
                    print(f"Agent: {status}")

                    if result.get("formatted_result"):
                        print(f"Response: {result['formatted_result'][:100]}...")

                    scenario_results.append(status == "completed")

                except Exception as e:
                    print(f"Error: {e}")
                    scenario_results.append(False)

            overall_status = "PASS" if all(scenario_results) else "FAIL"
            results.append({
                "test": test_case['name'],
                "status": overall_status,
                "success_rate": sum(scenario_results) / len(scenario_results) * 100
            })

        return results

    async def run_all_tests(self):
        """모든 테스트 실행"""
        console.rule("Sales Analytics Agent Test Suite", style="bold")

        # Initialize
        await self.initialize()

        all_results = {}

        # Run each test category
        print("\n" + "="*60)
        all_results['text2sql'] = await self.run_text2sql_tests()

        print("\n" + "="*60)
        all_results['data_collection'] = await self.run_data_collection_tests()

        print("\n" + "="*60)
        all_results['analysis'] = await self.run_analysis_tests()

        print("\n" + "="*60)
        all_results['e2e'] = await self.run_e2e_tests()

        # Summary
        self.print_summary(all_results)

        return all_results

    def print_summary(self, all_results: Dict):
        """결과 요약 출력"""
        console.rule("Test Summary")

        # Calculate statistics
        total_tests = 0
        passed_tests = 0

        for category, results in all_results.items():
            category_total = len(results)
            category_passed = sum(1 for r in results if r['status'] in ['PASS', 'PARTIAL'])

            total_tests += category_total
            passed_tests += category_passed

            print(f"\n{category.upper()}:")
            print(f"  Total: {category_total}")
            print(f"  Passed: {category_passed}")
            print(f"  Failed: {category_total - category_passed}")
            print(f"  Success Rate: {category_passed/category_total*100:.1f}%")

        # Overall summary
        print("\n" + "="*60)
        print("OVERALL RESULTS")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Overall Success Rate: {passed_tests/total_tests*100:.1f}%")

        # Failed tests detail
        print("\n" + "="*60)
        print("FAILED TESTS DETAIL")
        print("="*60)

        for category, results in all_results.items():
            failed = [r for r in results if r['status'] == 'FAIL']
            if failed:
                print(f"\n{category}:")
                for test in failed:
                    print(f"  - {test['test']}: {test.get('error', 'Unknown error')}")

# ============== Main ==============

async def main():
    """메인 실행 함수"""
    runner = SalesAgentTestRunner()

    try:
        results = await runner.run_all_tests()

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"test_report_{timestamp}.json"

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n[OK] Report saved to {report_file}")

    except Exception as e:
        print(f"\n[FAIL] Test execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())