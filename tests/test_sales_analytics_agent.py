"""
Sales Analytics Agent Comprehensive Test Suite
영업 분석 에이전트 종합 테스트 스위트

테스트 카테고리:
1. Text2SQL 테스트 (50개)
2. Data Collection Subgraph 테스트 (10개)
3. Analysis Subgraph 테스트 (20개)
4. 복합/단일 질의 처리 테스트 (20개)
5. 사용자 메시지 E2E 테스트

실행 방법:
    python tests/test_sales_analytics_agent.py [옵션]

옵션:
    --category [text2sql|data_collection|analysis|query|e2e|all]
    --verbose: 상세 출력
    --save-report: 결과 리포트 저장
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import argparse
from dataclasses import dataclass, asdict
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich import print as rprint

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

# Rich console for pretty output
console = Console()

# ============== Test Data Classes ==============

@dataclass
class TestCase:
    """테스트 케이스 데이터 클래스"""
    id: str
    category: str
    name: str
    input_data: Dict[str, Any]
    expected_output: Optional[Dict[str, Any]] = None
    description: str = ""

@dataclass
class TestResult:
    """테스트 결과 데이터 클래스"""
    test_case: TestCase
    status: str  # passed, failed, error
    execution_time: float
    actual_output: Dict[str, Any]
    error_message: Optional[str] = None

class TestCategory(Enum):
    """테스트 카테고리"""
    TEXT2SQL = "text2sql"
    DATA_COLLECTION = "data_collection"
    ANALYSIS = "analysis"
    QUERY = "query"
    E2E = "e2e"
    ALL = "all"

# ============== Test Cases Definition ==============

class TestCaseGenerator:
    """테스트 케이스 생성기"""

    @staticmethod
    def generate_text2sql_cases() -> List[TestCase]:
        """Text2SQL 테스트 케이스 50개 생성"""
        cases = []

        # 1. 기본 조회 (15개)
        basic_queries = [
            ("김철수 실적", "김철수의 현재 실적 조회"),
            ("이영희 3월 매출", "이영희의 3월 매출 조회"),
            ("박민수 작년 실적", "박민수의 작년 실적 조회"),
            ("최시우 2024년 1분기 실적", "최시우의 2024년 1분기 실적"),
            ("정수진 어제 매출", "정수진의 어제 매출 조회"),
            ("김영호 이번주 실적", "김영호의 이번주 실적"),
            ("이미경 지난달 매출", "이미경의 지난달 매출"),
            ("박준서 10월 실적", "박준서의 10월 실적"),
            ("홍길동님의 성과", "홍길동의 성과 조회"),
            ("김 대리 실적 확인", "김 대리의 실적 확인"),
            ("이번달 김철수씨 판매액", "이번달 김철수의 판매액"),
            ("작년 12월 박영희 실적", "작년 12월 박영희 실적"),
            ("2023년 상반기 최민수 매출", "2023년 상반기 최민수 매출"),
            ("올해 1월부터 3월까지 이철수 실적", "2024년 1-3월 이철수 실적"),
            ("김철수 최근 3개월 실적", "김철수 최근 3개월 실적"),
        ]

        for i, (query, desc) in enumerate(basic_queries, 1):
            cases.append(TestCase(
                id=f"text2sql_basic_{i:02d}",
                category="text2sql",
                name=f"기본조회_{i}",
                input_data={"query": query},
                description=desc
            ))

        # 2. 집계/통계 (10개)
        aggregation_queries = [
            ("전체 직원 평균 실적", "전체 직원의 평균 실적 계산"),
            ("영업팀 총 매출", "영업팀의 총 매출 집계"),
            ("이번달 최고 실적", "이번달 최고 실적 조회"),
            ("3월 최저 매출", "3월 최저 매출 조회"),
            ("팀별 평균 실적", "팀별 평균 실적 계산"),
            ("전체 매출 합계", "전체 매출 합계 계산"),
            ("상위 10% 직원 평균", "상위 10% 직원의 평균 실적"),
            ("부서별 실적 통계", "부서별 실적 통계"),
            ("월별 매출 총액", "월별 매출 총액 집계"),
            ("분기별 평균 실적", "분기별 평균 실적 계산"),
        ]

        for i, (query, desc) in enumerate(aggregation_queries, 1):
            cases.append(TestCase(
                id=f"text2sql_agg_{i:02d}",
                category="text2sql",
                name=f"집계통계_{i}",
                input_data={"query": query},
                description=desc
            ))

        # 3. 비교 분석 (10개)
        comparison_queries = [
            ("김철수 전년 대비 성장률", "김철수의 전년 대비 성장률"),
            ("이영희 전월 대비 실적", "이영희의 전월 대비 실적"),
            ("작년 대비 올해 매출 증가율", "YoY 매출 증가율"),
            ("1분기 대비 2분기 실적", "분기 대비 실적"),
            ("목표 대비 달성률", "목표 대비 달성률 계산"),
            ("팀간 실적 비교", "팀간 실적 비교 분석"),
            ("김철수와 이영희 실적 비교", "두 직원 실적 비교"),
            ("상반기 vs 하반기 매출", "반기별 매출 비교"),
            ("작년 동기 대비 성장", "작년 동기 대비 성장률"),
            ("월별 성장 추이", "월별 성장 추이 분석"),
        ]

        for i, (query, desc) in enumerate(comparison_queries, 1):
            cases.append(TestCase(
                id=f"text2sql_comp_{i:02d}",
                category="text2sql",
                name=f"비교분석_{i}",
                input_data={"query": query},
                description=desc
            ))

        # 4. 순위/랭킹 (5개)
        ranking_queries = [
            ("이번달 실적 TOP 5", "이번달 실적 상위 5명"),
            ("3월 매출 하위 3명", "3월 매출 하위 3명"),
            ("올해 최고 실적자", "올해 최고 실적자 조회"),
            ("팀별 실적 순위", "팀별 실적 순위"),
            ("전체 직원 실적 랭킹", "전체 직원 실적 순위"),
        ]

        for i, (query, desc) in enumerate(ranking_queries, 1):
            cases.append(TestCase(
                id=f"text2sql_rank_{i:02d}",
                category="text2sql",
                name=f"순위랭킹_{i}",
                input_data={"query": query},
                description=desc
            ))

        # 5. 복잡한 조건 (10개)
        complex_queries = [
            ("김철수 3월 실적과 목표 대비 달성률", "실적과 달성률 동시 조회"),
            ("영업1팀 상반기 실적 및 전년 대비 성장률", "팀 실적과 성장률"),
            ("실적 100만원 이상 직원 명단", "조건부 직원 조회"),
            ("목표 초과 달성 직원들의 평균 초과율", "복합 조건 계산"),
            ("최근 3개월 실적 상승 직원", "추세 기반 조회"),
            ("거래처별 매출 상위 10개", "거래처별 매출 순위"),
            ("품목별 판매 실적 분석", "품목별 실적 분석"),
            ("지역별 매출 현황", "지역별 매출 집계"),
            ("신규 거래처 매출 기여도", "신규 거래처 분석"),
            ("주요 거래처 의존도 분석", "거래처 의존도 계산"),
        ]

        for i, (query, desc) in enumerate(complex_queries, 1):
            cases.append(TestCase(
                id=f"text2sql_complex_{i:02d}",
                category="text2sql",
                name=f"복잡조건_{i}",
                input_data={"query": query},
                description=desc
            ))

        return cases

    @staticmethod
    def generate_data_collection_cases() -> List[TestCase]:
        """Data Collection Subgraph 테스트 케이스 10개 생성"""
        cases = []

        test_scenarios = [
            {
                "name": "단일DB_성능데이터",
                "input": {
                    "query_params": {"person_name": "김철수", "month": "03"},
                    "target_databases": ["performance"]
                },
                "desc": "단일 DB에서 성능 데이터 수집"
            },
            {
                "name": "다중DB_조인",
                "input": {
                    "query_params": {"person_name": "이영희"},
                    "target_databases": ["performance", "target", "clients"]
                },
                "desc": "다중 DB 조인 데이터 수집"
            },
            {
                "name": "목표데이터_수집",
                "input": {
                    "query_params": {"month": "202403"},
                    "target_databases": ["target"]
                },
                "desc": "목표 데이터만 수집"
            },
            {
                "name": "고객데이터_수집",
                "input": {
                    "query_params": {"client_id": "CL001"},
                    "target_databases": ["clients"]
                },
                "desc": "특정 고객 데이터 수집"
            },
            {
                "name": "팀별_집계",
                "input": {
                    "query_params": {"team": "영업1팀"},
                    "target_databases": ["performance", "target"]
                },
                "desc": "팀별 데이터 집계"
            },
            {
                "name": "기간범위_수집",
                "input": {
                    "query_params": {"start_month": "202401", "end_month": "202403"},
                    "target_databases": ["performance"]
                },
                "desc": "기간 범위 데이터 수집"
            },
            {
                "name": "필터링_적용",
                "input": {
                    "query_params": {"min_amount": 1000000},
                    "target_databases": ["performance"]
                },
                "desc": "조건 필터링 적용"
            },
            {
                "name": "에러처리_테스트",
                "input": {
                    "query_params": {"invalid_field": "test"},
                    "target_databases": ["invalid_db"]
                },
                "desc": "에러 처리 검증"
            },
            {
                "name": "대용량_처리",
                "input": {
                    "query_params": {"limit": 10000},
                    "target_databases": ["performance"]
                },
                "desc": "대용량 데이터 처리"
            },
            {
                "name": "복합조건_수집",
                "input": {
                    "query_params": {
                        "person_name": "박민수",
                        "month": "202403",
                        "client_id": "CL001"
                    },
                    "target_databases": ["performance", "target", "clients"]
                },
                "desc": "복합 조건 데이터 수집"
            }
        ]

        for i, scenario in enumerate(test_scenarios, 1):
            cases.append(TestCase(
                id=f"data_collection_{i:02d}",
                category="data_collection",
                name=scenario["name"],
                input_data=scenario["input"],
                description=scenario["desc"]
            ))

        return cases

    @staticmethod
    def generate_analysis_cases() -> List[TestCase]:
        """Analysis Subgraph 테스트 케이스 20개 생성"""
        cases = []

        # Sample collected data for analysis
        sample_data = {
            "performance_data": [
                {"담당자": "김철수", "202403": 1500000, "202402": 1200000},
                {"담당자": "이영희", "202403": 1800000, "202402": 1600000}
            ],
            "target_data": [
                {"담당자": "김철수", "목표_202403": 2000000},
                {"담당자": "이영희", "목표_202403": 1700000}
            ],
            "client_data": [
                {"거래처ID": "CL001", "병원": "서울대병원", "지역": "서울"}
            ]
        }

        analysis_scenarios = [
            ("기본메트릭_계산", "basic", "기본 메트릭 계산"),
            ("달성률_분석", "achievement", "목표 달성률 분석"),
            ("추세_분석", "trend", "시계열 추세 분석"),
            ("비교_분석", "comparison", "비교 분석 수행"),
            ("인사이트_생성", "insights", "비즈니스 인사이트 생성"),
            ("상관관계_분석", "correlation", "데이터 상관관계 분석"),
            ("예측_분석", "forecast", "미래 실적 예측"),
            ("이상치_탐지", "anomaly", "이상치 탐지 분석"),
            ("성과_평가", "performance", "개인 성과 평가"),
            ("팀_분석", "team", "팀 단위 분석"),
            ("거래처_분석", "client", "거래처별 분석"),
            ("품목_분석", "product", "품목별 분석"),
            ("지역_분석", "region", "지역별 분석"),
            ("시장점유율", "market_share", "시장 점유율 분석"),
            ("경쟁력_분석", "competitiveness", "경쟁력 분석"),
            ("리스크_평가", "risk", "리스크 평가"),
            ("기회_분석", "opportunity", "기회 요인 분석"),
            ("효율성_분석", "efficiency", "업무 효율성 분석"),
            ("수익성_분석", "profitability", "수익성 분석"),
            ("종합_리포트", "comprehensive", "종합 분석 리포트"),
        ]

        for i, (name, analysis_type, desc) in enumerate(analysis_scenarios, 1):
            input_data = sample_data.copy()
            input_data["analysis_type"] = analysis_type
            input_data["analysis_params"] = {}

            cases.append(TestCase(
                id=f"analysis_{i:02d}",
                category="analysis",
                name=name,
                input_data=input_data,
                description=desc
            ))

        return cases

    @staticmethod
    def generate_query_processing_cases() -> List[TestCase]:
        """복합/단일 질의 처리 테스트 케이스 20개 생성"""
        cases = []

        query_scenarios = [
            # 단순 질의 (5개)
            ("김철수 실적?", "simple", "간단한 질의"),
            ("이번달 매출", "simple", "시간 표현 질의"),
            ("최고 실적자", "simple", "순위 질의"),
            ("평균 실적", "simple", "통계 질의"),
            ("목표 달성률", "simple", "계산 질의"),

            # 복합 질의 (10개)
            ("김철수 3월 실적과 목표 대비 달성률 그리고 전월 대비 성장률", "complex", "다중 작업 질의"),
            ("영업팀 전체 실적 분석하고 개인별 순위도 보여줘", "complex", "분석과 순위"),
            ("작년 대비 올해 성장률이 높은 직원 5명과 그들의 주요 거래처", "complex", "비교와 연관 정보"),
            ("이번 분기 실적과 작년 동기 대비 그리고 목표 달성 현황", "complex", "시점 비교"),
            ("팀별 평균 실적과 최고/최저 실적자 그리고 달성률", "complex", "팀 분석"),
            ("김철수와 이영희 실적 비교하고 둘의 주요 거래처도 분석", "complex", "개인 비교"),
            ("상위 10% 직원들의 공통점 분석", "complex", "패턴 분석"),
            ("실적 하락 직원들의 원인 분석", "complex", "원인 분석"),
            ("신규 거래처 개발 현황과 기여도", "complex", "신규 분석"),
            ("지역별 실적과 성장 가능성 분석", "complex", "지역 분석"),

            # 모호한/불명확한 질의 (5개)
            ("김 대리", "ambiguous", "불완전한 이름"),
            ("작년에 잘한 사람", "ambiguous", "모호한 기준"),
            ("실적 괜찮은 직원들", "ambiguous", "불명확한 조건"),
            ("요즘 어때?", "ambiguous", "구체적이지 않은 질문"),
            ("분석해줘", "ambiguous", "대상 불명확"),
        ]

        for i, (query, query_type, desc) in enumerate(query_scenarios, 1):
            cases.append(TestCase(
                id=f"query_{i:02d}",
                category="query",
                name=f"{query_type}_{i}",
                input_data={
                    "query": query,
                    "query_type": query_type
                },
                description=desc
            ))

        return cases

    @staticmethod
    def generate_e2e_cases() -> List[TestCase]:
        """E2E 사용자 시나리오 테스트 케이스"""
        cases = []

        scenarios = [
            {
                "name": "일일보고_시나리오",
                "messages": [
                    "오늘 영업팀 전체 실적 요약해줘",
                    "어제 대비 변화량도 보여줘",
                    "특이사항이나 주목할 점은?"
                ],
                "desc": "일일 보고 시나리오"
            },
            {
                "name": "월간평가_시나리오",
                "messages": [
                    "이번달 김철수 실적 평가해줘",
                    "목표 달성률은 어떻게 되나요?",
                    "작년 동월 대비는요?",
                    "개선점이나 제안사항 있나요?"
                ],
                "desc": "월간 평가 시나리오"
            },
            {
                "name": "팀분석_시나리오",
                "messages": [
                    "영업1팀 실적 현황",
                    "팀원별 기여도 분석",
                    "타 팀과 비교하면?",
                    "팀 성과 향상 방안은?"
                ],
                "desc": "팀 분석 시나리오"
            },
            {
                "name": "전략수립_시나리오",
                "messages": [
                    "올해 상반기 실적 종합 분석",
                    "성장 추세와 예측",
                    "주요 성공 요인은?",
                    "하반기 전략 제안"
                ],
                "desc": "전략 수립 시나리오"
            },
            {
                "name": "문제해결_시나리오",
                "messages": [
                    "실적이 떨어진 직원들 리스트",
                    "하락 원인 분석해줘",
                    "개선 가능성 평가",
                    "지원 방안 제시"
                ],
                "desc": "문제 해결 시나리오"
            }
        ]

        for i, scenario in enumerate(scenarios, 1):
            cases.append(TestCase(
                id=f"e2e_{i:02d}",
                category="e2e",
                name=scenario["name"],
                input_data={
                    "messages": scenario["messages"],
                    "scenario_type": "conversation"
                },
                description=scenario["desc"]
            ))

        return cases

# ============== Test Runner ==============

class SalesAgentTestRunner:
    """Sales Agent 테스트 실행기"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.agent = None
        self.sql_generator = SQLGenerator()
        self.sql_executor = SQLExecutor()
        self.results: List[TestResult] = []
        self.start_time = None
        self.end_time = None

    async def initialize(self):
        """테스트 환경 초기화"""
        console.print("[bold green]Initializing test environment...[/bold green]")
        self.agent = SalesAnalyticsAgent()
        console.print("[bold green]✓[/bold green] Sales Analytics Agent initialized")

    async def run_text2sql_test(self, test_case: TestCase) -> TestResult:
        """Text2SQL 테스트 실행"""
        start_time = time.time()

        try:
            query = test_case.input_data["query"]

            # Parse query
            parsed = self.sql_generator.parse_query(query)

            # Generate SQL
            if self.sql_generator.use_llm:
                sql, explanation = await self.sql_generator.generate_sql_with_llm(query, parsed)
            else:
                sql, explanation = self.sql_generator.generate_sql(parsed)

            # Validate SQL
            is_valid = self.sql_generator.validate_sql(sql)

            # Execute if valid
            if is_valid:
                results, error = self.sql_executor.execute_query(sql)

                output = {
                    "sql": sql,
                    "explanation": explanation,
                    "valid": is_valid,
                    "result_count": len(results) if not error else 0,
                    "error": error
                }

                status = "passed" if not error else "failed"
                error_msg = error
            else:
                output = {
                    "sql": sql,
                    "explanation": explanation,
                    "valid": False,
                    "validation_error": "SQL validation failed"
                }
                status = "failed"
                error_msg = "SQL validation failed"

            execution_time = time.time() - start_time

            return TestResult(
                test_case=test_case,
                status=status,
                execution_time=execution_time,
                actual_output=output,
                error_message=error_msg
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                test_case=test_case,
                status="error",
                execution_time=execution_time,
                actual_output={},
                error_message=str(e)
            )

    async def run_data_collection_test(self, test_case: TestCase) -> TestResult:
        """Data Collection Subgraph 테스트 실행"""
        start_time = time.time()

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
                "query_params": test_case.input_data.get("query_params", {}),
                "target_databases": test_case.input_data.get("target_databases", []),
                "performance_data": [],
                "target_data": [],
                "client_data": [],
                "aggregated_performance": {},
                "aggregated_target": {},
                "aggregated_client": {},
                "collection_status": "pending",
                "errors": []
            }

            # Execute subgraph
            result = await app.ainvoke(state, context=context)

            execution_time = time.time() - start_time

            # Check results
            has_data = bool(
                result.get("performance_data") or
                result.get("target_data") or
                result.get("client_data")
            )

            status = "passed" if has_data or test_case.name == "에러처리_테스트" else "failed"

            return TestResult(
                test_case=test_case,
                status=status,
                execution_time=execution_time,
                actual_output={
                    "collection_status": result.get("collection_status"),
                    "data_collected": has_data,
                    "errors": result.get("errors", [])
                },
                error_message=None if status == "passed" else "No data collected"
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                test_case=test_case,
                status="error",
                execution_time=execution_time,
                actual_output={},
                error_message=str(e)
            )

    async def run_analysis_test(self, test_case: TestCase) -> TestResult:
        """Analysis Subgraph 테스트 실행"""
        start_time = time.time()

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

            # Prepare state with input data
            state = {
                "performance_data": test_case.input_data.get("performance_data", []),
                "target_data": test_case.input_data.get("target_data", []),
                "client_data": test_case.input_data.get("client_data", []),
                "analysis_type": test_case.input_data.get("analysis_type", "basic"),
                "analysis_params": test_case.input_data.get("analysis_params", {}),
                "basic_metrics": {},
                "trend_analysis": {},
                "comparative_analysis": {},
                "insights": [],
                "analysis_report": {},
                "analysis_status": "pending",
                "errors": []
            }

            # Execute subgraph
            result = await app.ainvoke(state, context=context)

            execution_time = time.time() - start_time

            # Check results
            has_analysis = bool(
                result.get("basic_metrics") or
                result.get("insights") or
                result.get("analysis_report")
            )

            status = "passed" if has_analysis else "failed"

            return TestResult(
                test_case=test_case,
                status=status,
                execution_time=execution_time,
                actual_output={
                    "analysis_status": result.get("analysis_status"),
                    "has_metrics": bool(result.get("basic_metrics")),
                    "insights_count": len(result.get("insights", [])),
                    "has_report": bool(result.get("analysis_report"))
                },
                error_message=None if status == "passed" else "No analysis generated"
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                test_case=test_case,
                status="error",
                execution_time=execution_time,
                actual_output={},
                error_message=str(e)
            )

    async def run_query_processing_test(self, test_case: TestCase) -> TestResult:
        """복합/단일 질의 처리 테스트 실행"""
        start_time = time.time()

        try:
            # Run agent with query
            result = await self.agent.run(
                query=test_case.input_data["query"],
                user_id="test_user",
                session_id=f"test_{test_case.id}",
                language="ko"
            )

            execution_time = time.time() - start_time

            # Check results based on query type
            query_type = test_case.input_data.get("query_type", "simple")

            if query_type == "complex":
                # Complex queries should have execution plan
                has_plan = bool(result.get("execution_plan"))
                has_results = bool(result.get("execution_results"))
                status = "passed" if has_plan and has_results else "failed"
            elif query_type == "ambiguous":
                # Ambiguous queries should be handled gracefully
                status = "passed" if result.get("status") in ["completed", "failed"] else "failed"
            else:
                # Simple queries should complete successfully
                status = "passed" if result.get("status") == "completed" else "failed"

            return TestResult(
                test_case=test_case,
                status=status,
                execution_time=execution_time,
                actual_output={
                    "status": result.get("status"),
                    "has_plan": bool(result.get("execution_plan")),
                    "has_results": bool(result.get("formatted_result")),
                    "execution_step": result.get("execution_step")
                },
                error_message=None if status == "passed" else f"Query processing failed: {result.get('errors')}"
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                test_case=test_case,
                status="error",
                execution_time=execution_time,
                actual_output={},
                error_message=str(e)
            )

    async def run_e2e_test(self, test_case: TestCase) -> TestResult:
        """E2E 사용자 시나리오 테스트 실행"""
        start_time = time.time()

        try:
            messages = test_case.input_data["messages"]
            conversation_results = []

            for i, message in enumerate(messages):
                # Run agent for each message
                result = await self.agent.run(
                    query=message,
                    user_id="test_user",
                    session_id=f"test_{test_case.id}",
                    language="ko"
                )

                conversation_results.append({
                    "message": message,
                    "response": result.get("formatted_result", "No response"),
                    "status": result.get("status")
                })

                # Small delay between messages
                await asyncio.sleep(0.5)

            execution_time = time.time() - start_time

            # Check if all messages were processed
            all_success = all(r["status"] == "completed" for r in conversation_results)

            return TestResult(
                test_case=test_case,
                status="passed" if all_success else "failed",
                execution_time=execution_time,
                actual_output={
                    "conversation_length": len(conversation_results),
                    "all_completed": all_success,
                    "results": conversation_results[:2] if self.verbose else []  # Show first 2 for brevity
                },
                error_message=None if all_success else "Some messages failed to process"
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return TestResult(
                test_case=test_case,
                status="error",
                execution_time=execution_time,
                actual_output={},
                error_message=str(e)
            )

    async def run_test_category(self, category: TestCategory) -> List[TestResult]:
        """특정 카테고리의 테스트 실행"""
        # Generate test cases
        if category == TestCategory.TEXT2SQL:
            test_cases = TestCaseGenerator.generate_text2sql_cases()
            runner_func = self.run_text2sql_test
        elif category == TestCategory.DATA_COLLECTION:
            test_cases = TestCaseGenerator.generate_data_collection_cases()
            runner_func = self.run_data_collection_test
        elif category == TestCategory.ANALYSIS:
            test_cases = TestCaseGenerator.generate_analysis_cases()
            runner_func = self.run_analysis_test
        elif category == TestCategory.QUERY:
            test_cases = TestCaseGenerator.generate_query_processing_cases()
            runner_func = self.run_query_processing_test
        elif category == TestCategory.E2E:
            test_cases = TestCaseGenerator.generate_e2e_cases()
            runner_func = self.run_e2e_test
        else:
            return []

        results = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task(
                f"[cyan]Running {category.value} tests...",
                total=len(test_cases)
            )

            for test_case in test_cases:
                if self.verbose:
                    console.print(f"\n[dim]Running: {test_case.name} - {test_case.description}[/dim]")

                result = await runner_func(test_case)
                results.append(result)

                # Update progress
                progress.update(task, advance=1)

                # Show result
                if result.status == "passed":
                    status_icon = "[green]✓[/green]"
                elif result.status == "failed":
                    status_icon = "[yellow]⚠[/yellow]"
                else:
                    status_icon = "[red]✗[/red]"

                if self.verbose or result.status != "passed":
                    console.print(f"{status_icon} {test_case.name}: {result.status} ({result.execution_time:.2f}s)")
                    if result.error_message and self.verbose:
                        console.print(f"  [red]{result.error_message}[/red]")

        return results

    async def run_all_tests(self):
        """모든 테스트 실행"""
        self.start_time = time.time()

        console.print("\n[bold cyan]Starting comprehensive test suite...[/bold cyan]\n")

        categories = [
            TestCategory.TEXT2SQL,
            TestCategory.DATA_COLLECTION,
            TestCategory.ANALYSIS,
            TestCategory.QUERY,
            TestCategory.E2E
        ]

        for category in categories:
            console.print(f"\n[bold]{category.value.upper()} Tests[/bold]")
            console.print("="*50)

            results = await self.run_test_category(category)
            self.results.extend(results)

            # Show category summary
            passed = sum(1 for r in results if r.status == "passed")
            failed = sum(1 for r in results if r.status == "failed")
            errors = sum(1 for r in results if r.status == "error")

            console.print(f"\nCategory Results: [green]{passed} passed[/green], "
                         f"[yellow]{failed} failed[/yellow], [red]{errors} errors[/red]")

        self.end_time = time.time()

    def generate_report(self) -> Dict[str, Any]:
        """테스트 결과 리포트 생성"""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.status == "passed")
        failed_tests = sum(1 for r in self.results if r.status == "failed")
        error_tests = sum(1 for r in self.results if r.status == "error")

        # Calculate statistics by category
        category_stats = {}
        for category in ["text2sql", "data_collection", "analysis", "query", "e2e"]:
            category_results = [r for r in self.results if r.test_case.category == category]
            if category_results:
                category_stats[category] = {
                    "total": len(category_results),
                    "passed": sum(1 for r in category_results if r.status == "passed"),
                    "failed": sum(1 for r in category_results if r.status == "failed"),
                    "errors": sum(1 for r in category_results if r.status == "error"),
                    "avg_time": sum(r.execution_time for r in category_results) / len(category_results),
                    "success_rate": sum(1 for r in category_results if r.status == "passed") / len(category_results) * 100
                }

        # Find slowest tests
        slowest_tests = sorted(self.results, key=lambda r: r.execution_time, reverse=True)[:5]

        # Find failed tests
        failed_tests_detail = [r for r in self.results if r.status in ["failed", "error"]]

        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "errors": error_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "total_time": self.end_time - self.start_time if self.end_time else 0,
                "timestamp": datetime.now().isoformat()
            },
            "category_statistics": category_stats,
            "slowest_tests": [
                {
                    "name": t.test_case.name,
                    "category": t.test_case.category,
                    "time": t.execution_time
                } for t in slowest_tests
            ],
            "failed_tests": [
                {
                    "name": t.test_case.name,
                    "category": t.test_case.category,
                    "error": t.error_message
                } for t in failed_tests_detail[:10]  # Limit to 10 for readability
            ]
        }

        return report

    def display_report(self, report: Dict[str, Any]):
        """리포트를 콘솔에 표시"""
        # Summary Panel
        summary = report["summary"]
        summary_content = f"""
[bold]Test Execution Summary[/bold]
───────────────────────
Total Tests: {summary['total_tests']}
Passed: [green]{summary['passed']}[/green]
Failed: [yellow]{summary['failed']}[/yellow]
Errors: [red]{summary['errors']}[/red]
Success Rate: [{'green' if summary['success_rate'] > 80 else 'yellow'}]{summary['success_rate']:.1f}%[/{'green' if summary['success_rate'] > 80 else 'yellow'}]
Total Time: {summary['total_time']:.2f}s
        """

        console.print(Panel(summary_content, title="Test Results", border_style="cyan"))

        # Category Statistics Table
        table = Table(title="Category Statistics", show_header=True, header_style="bold magenta")
        table.add_column("Category", style="cyan")
        table.add_column("Total", justify="right")
        table.add_column("Passed", justify="right", style="green")
        table.add_column("Failed", justify="right", style="yellow")
        table.add_column("Errors", justify="right", style="red")
        table.add_column("Success Rate", justify="right")
        table.add_column("Avg Time", justify="right")

        for category, stats in report["category_statistics"].items():
            table.add_row(
                category.upper(),
                str(stats["total"]),
                str(stats["passed"]),
                str(stats["failed"]),
                str(stats["errors"]),
                f"{stats['success_rate']:.1f}%",
                f"{stats['avg_time']:.2f}s"
            )

        console.print(table)

        # Slowest Tests
        if report["slowest_tests"]:
            console.print("\n[bold]Slowest Tests:[/bold]")
            for test in report["slowest_tests"]:
                console.print(f"  • {test['name']} ({test['category']}): {test['time']:.2f}s")

        # Failed Tests
        if report["failed_tests"]:
            console.print("\n[bold red]Failed Tests:[/bold red]")
            for test in report["failed_tests"]:
                console.print(f"  • {test['name']} ({test['category']})")
                if test['error']:
                    console.print(f"    [dim]{test['error'][:100]}...[/dim]")

    def save_report(self, report: Dict[str, Any], filepath: str = "test_report.json"):
        """리포트를 파일로 저장"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        console.print(f"\n[green]Report saved to {filepath}[/green]")

# ============== Interactive Test Mode ==============

class InteractiveTestMode:
    """대화형 테스트 모드"""

    def __init__(self):
        self.agent = SalesAnalyticsAgent()
        self.session_id = f"interactive_{datetime.now().timestamp()}"

    async def run(self):
        """대화형 모드 실행"""
        console.print("\n[bold cyan]Sales Analytics Agent Interactive Test Mode[/bold cyan]")
        console.print("Type 'exit' to quit, 'help' for commands\n")

        while True:
            try:
                # Get user input
                query = console.input("[bold green]Query>[/bold green] ")

                if query.lower() == 'exit':
                    break
                elif query.lower() == 'help':
                    self.show_help()
                    continue
                elif not query.strip():
                    continue

                # Process query
                console.print("[dim]Processing...[/dim]")

                start_time = time.time()
                result = await self.agent.run(
                    query=query,
                    user_id="interactive_user",
                    session_id=self.session_id,
                    language="ko"
                )
                execution_time = time.time() - start_time

                # Display results
                console.print(f"\n[bold]Status:[/bold] {result.get('status')}")
                console.print(f"[bold]Execution Time:[/bold] {execution_time:.2f}s")

                if result.get("execution_plan"):
                    console.print("\n[bold]Execution Plan:[/bold]")
                    console.print(Syntax(
                        json.dumps(result["execution_plan"], indent=2, ensure_ascii=False),
                        "json"
                    ))

                if result.get("formatted_result"):
                    console.print("\n[bold]Result:[/bold]")
                    console.print(Panel(result["formatted_result"], border_style="green"))

                if result.get("errors"):
                    console.print("\n[bold red]Errors:[/bold red]")
                    for error in result["errors"]:
                        console.print(f"  • {error}")

                console.print("\n" + "="*60 + "\n")

            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

    def show_help(self):
        """도움말 표시"""
        help_text = """
[bold]Available Commands:[/bold]
  exit  - Quit interactive mode
  help  - Show this help message

[bold]Example Queries:[/bold]
  • 김철수 실적
  • 이번달 매출 TOP 5
  • 영업팀 평균 실적과 목표 달성률
  • 작년 대비 올해 성장률
  • 최근 3개월 실적 추이
        """
        console.print(Panel(help_text, title="Help", border_style="blue"))

# ============== Main Entry Point ==============

async def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="Sales Analytics Agent Test Suite")
    parser.add_argument(
        "--category",
        type=str,
        choices=["text2sql", "data_collection", "analysis", "query", "e2e", "all"],
        default="all",
        help="Test category to run"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--save-report",
        action="store_true",
        help="Save test report to file"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )

    args = parser.parse_args()

    if args.interactive:
        # Run interactive mode
        interactive = InteractiveTestMode()
        await interactive.run()
    else:
        # Run test suite
        runner = SalesAgentTestRunner(verbose=args.verbose)

        # Initialize
        await runner.initialize()

        # Run tests
        if args.category == "all":
            await runner.run_all_tests()
        else:
            category = TestCategory(args.category)
            results = await runner.run_test_category(category)
            runner.results = results
            runner.start_time = time.time()
            runner.end_time = time.time()

        # Generate and display report
        report = runner.generate_report()
        runner.display_report(report)

        # Save report if requested
        if args.save_report:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.json"
            runner.save_report(report, filename)

if __name__ == "__main__":
    asyncio.run(main())