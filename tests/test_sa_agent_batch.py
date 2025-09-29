"""
Sales Analytics Agent - Batch Test with Predefined Queries
판매 분석 에이전트 배치 테스트 (사전 정의된 쿼리)

50개의 미리 정의된 테스트 쿼리를 실행하여 에이전트의 성능과 정확성을 검증

사용법:
    python tests/test_sa_agent_batch.py [옵션]

옵션:
    --category [all|basic|employee|period|complex|trend]: 테스트 카테고리 선택
    --parallel: 병렬 실행 (더 빠른 테스트)
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
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
import traceback

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.service.agents.sales_analytics_agent import SalesAnalyticsAgent
from backend.service.core.config import Config

# Create logs directory if it doesn't exist
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f'batch_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Rich console
console = Console()


@dataclass
class TestQuery:
    """Test query definition"""
    category: str
    query: str
    expected_elements: List[str]  # Elements expected in the result
    description: str


@dataclass
class TestResult:
    """Test result container"""
    query: TestQuery
    status: str
    execution_time: float
    has_result: bool
    has_sql: bool
    has_insights: bool
    errors: List[str]
    raw_result: Optional[Dict[str, Any]] = None


class BatchTester:
    """Batch tester for Sales Analytics Agent"""

    def __init__(self, verbose: bool = False, save_report: bool = False):
        """
        Initialize batch tester

        Args:
            verbose: Show verbose output
            save_report: Save test report
        """
        self.verbose = verbose
        self.save_report = save_report
        self.config = Config()
        self.agent = None
        self.test_queries = self._define_test_queries()
        self.results: List[TestResult] = []
        self.session_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Initialize agent
        self._init_agent()

        if self.save_report:
            self.report_file = Path(f"test_reports/batch_{self.session_id}.json")
            self.report_file.parent.mkdir(exist_ok=True)

    def _init_agent(self):
        """Initialize the Sales Analytics Agent"""
        try:
            self.agent = SalesAnalyticsAgent(self.config)
            console.print("[green]✓[/green] Sales Analytics Agent 초기화 완료")
        except Exception as e:
            console.print(f"[red]✗[/red] Agent 초기화 실패: {str(e)}")
            raise

    def _define_test_queries(self) -> List[TestQuery]:
        """Define 50 test queries across different categories"""
        queries = []

        # Category 1: Basic Sales Performance (10 queries)
        basic_queries = [
            TestQuery("basic", "이번달 전체 매출 현황", ["매출", "금액"], "월별 전체 매출"),
            TestQuery("basic", "오늘 판매 실적", ["오늘", "실적"], "일별 판매 실적"),
            TestQuery("basic", "이번주 판매 현황", ["주", "판매"], "주간 판매 현황"),
            TestQuery("basic", "지난달 매출액", ["지난달", "매출"], "이전 월 매출"),
            TestQuery("basic", "올해 총 매출", ["올해", "총"], "연간 총 매출"),
            TestQuery("basic", "이번 분기 실적", ["분기", "실적"], "분기별 실적"),
            TestQuery("basic", "어제 판매량", ["어제", "판매"], "전일 판매량"),
            TestQuery("basic", "최근 판매 현황", ["최근", "현황"], "최근 판매 동향"),
            TestQuery("basic", "전체 영업 실적", ["전체", "영업"], "전체 영업 성과"),
            TestQuery("basic", "현재까지 매출", ["현재", "매출"], "누적 매출"),
        ]

        # Category 2: Employee-specific Queries (10 queries)
        # Using actual employee names: 윤수아, 윤하은, 정예준, 조시현, 조하은, 최수아
        employee_queries = [
            TestQuery("employee", "윤수아의 이번달 실적", ["윤수아"], "특정 직원 월 실적"),
            TestQuery("employee", "정예준 판매 현황", ["정예준"], "특정 직원 판매 현황"),
            TestQuery("employee", "조시현의 올해 실적", ["조시현"], "특정 직원 연간 실적"),
            TestQuery("employee", "조하은 목표 달성률", ["조하은", "목표"], "특정 직원 목표 달성"),
            TestQuery("employee", "최수아의 분기 성과", ["최수아", "분기"], "특정 직원 분기 성과"),
            TestQuery("employee", "윤하은 매출 분석", ["윤하은", "매출"], "팀장 매출 분석"),
            TestQuery("employee", "윤수아 실적 현황", ["윤수아"], "직원 실적"),
            TestQuery("employee", "정예준 팀 실적", ["정예준"], "팀별 실적"),
            TestQuery("employee", "조시현 담당 고객", ["조시현", "고객"], "직원별 고객 정보"),
            TestQuery("employee", "최수아 월별 실적 추이", ["최수아", "월별"], "직원 월별 추이"),
        ]

        # Category 3: Period-based Analysis (10 queries)
        period_queries = [
            TestQuery("period", "1월 매출 현황", ["1월"], "특정 월 매출"),
            TestQuery("period", "상반기 실적", ["상반기"], "반기 실적"),
            TestQuery("period", "하반기 목표 대비 실적", ["하반기", "목표"], "반기 목표 대비"),
            TestQuery("period", "3분기 판매 분석", ["3분기"], "분기 판매 분석"),
            TestQuery("period", "작년 대비 올해 실적", ["작년", "올해"], "연간 비교"),
            TestQuery("period", "월요일 평균 매출", ["월요일", "평균"], "요일별 평균"),
            TestQuery("period", "주말 판매 현황", ["주말"], "주말 판매"),
            TestQuery("period", "휴일 매출 분석", ["휴일"], "휴일 매출"),
            TestQuery("period", "분기별 성장률", ["분기", "성장"], "분기별 성장"),
            TestQuery("period", "연초 대비 현재", ["연초", "현재"], "연초 대비 현황"),
        ]

        # Category 4: Complex Multi-dimensional Queries (10 queries)
        complex_queries = [
            TestQuery("complex", "윤수아의 이번달 목표 달성률과 작년 동기 대비", ["윤수아", "목표", "작년"], "복합 분석"),
            TestQuery("complex", "상위 5명 영업사원 실적 비교", ["상위", "5명", "비교"], "순위 비교"),
            TestQuery("complex", "제품별 판매량과 매출 분석", ["제품", "판매량", "매출"], "제품 분석"),
            TestQuery("complex", "지역별 영업 성과 분석", ["지역", "성과"], "지역 분석"),
            TestQuery("complex", "신규 고객 대비 기존 고객 매출", ["신규", "기존", "고객"], "고객 유형 분석"),
            TestQuery("complex", "팀별 평균 실적과 개인 편차", ["팀별", "평균", "편차"], "팀 분석"),
            TestQuery("complex", "목표 초과 달성 직원 명단", ["목표", "초과", "직원"], "성과 우수자"),
            TestQuery("complex", "매출 하위 10% 원인 분석", ["하위", "10%", "원인"], "하위 성과 분석"),
            TestQuery("complex", "고객사별 매출 기여도", ["고객사", "기여도"], "고객사 분석"),
            TestQuery("complex", "채널별 판매 효율성", ["채널", "효율성"], "채널 분석"),
        ]

        # Category 5: Trend and Comparison Queries (10 queries)
        trend_queries = [
            TestQuery("trend", "최근 6개월 매출 트렌드", ["6개월", "트렌드"], "중기 트렌드"),
            TestQuery("trend", "월별 성장률 추이", ["월별", "성장률"], "성장률 추이"),
            TestQuery("trend", "판매량 증감 분석", ["증감", "분석"], "증감 분석"),
            TestQuery("trend", "계절별 매출 패턴", ["계절", "패턴"], "계절 패턴"),
            TestQuery("trend", "전년 동기 대비 성장", ["전년", "동기"], "전년 대비"),
            TestQuery("trend", "주간 실적 변동 추이", ["주간", "변동"], "주간 변동"),
            TestQuery("trend", "매출 예측 분석", ["예측"], "매출 예측"),
            TestQuery("trend", "성과 개선 추세", ["개선", "추세"], "개선 추세"),
            TestQuery("trend", "시장 점유율 변화", ["시장", "점유율"], "시장 점유율"),
            TestQuery("trend", "판매 속도 분석", ["판매", "속도"], "판매 속도"),
        ]

        # Combine all queries
        queries.extend(basic_queries)
        queries.extend(employee_queries)
        queries.extend(period_queries)
        queries.extend(complex_queries)
        queries.extend(trend_queries)

        return queries

    async def run_single_test(self, test_query: TestQuery) -> TestResult:
        """
        Run a single test query

        Args:
            test_query: Test query to run

        Returns:
            Test result
        """
        start_time = time.time()

        try:
            # Run the agent
            result = await self.agent.run(
                query=test_query.query,
                user_id="test_user",
                session_id=self.session_id,
                language="ko"
            )

            # Calculate execution time
            execution_time = time.time() - start_time

            # Analyze result
            status = result.get('status', 'unknown')
            has_result = bool(result.get('formatted_result') or result.get('final_report'))
            has_sql = bool(result.get('generated_sql'))
            has_insights = bool(result.get('insights'))
            errors = result.get('errors', [])

            # Check for expected elements in the result
            formatted_result = result.get('formatted_result', '')
            found_elements = []
            for element in test_query.expected_elements:
                if element.lower() in formatted_result.lower():
                    found_elements.append(element)

            # Determine test status
            test_status = 'passed' if status == 'completed' and has_result else 'failed'

            return TestResult(
                query=test_query,
                status=test_status,
                execution_time=execution_time,
                has_result=has_result,
                has_sql=has_sql,
                has_insights=has_insights,
                errors=errors,
                raw_result=result if self.verbose else None
            )

        except Exception as e:
            logger.error(f"Test failed for query '{test_query.query}': {e}")
            if self.verbose:
                traceback.print_exc()

            return TestResult(
                query=test_query,
                status='error',
                execution_time=time.time() - start_time,
                has_result=False,
                has_sql=False,
                has_insights=False,
                errors=[str(e)]
            )

    async def run_tests(self, category: str = "all", parallel: bool = False):
        """
        Run batch tests

        Args:
            category: Category to test (all, basic, employee, period, complex, trend)
            parallel: Whether to run tests in parallel
        """
        # Filter queries by category
        if category == "all":
            queries_to_test = self.test_queries
        else:
            queries_to_test = [q for q in self.test_queries if q.category == category]

        console.print(f"\n[bold cyan]Running {len(queries_to_test)} test queries...[/bold cyan]")

        # Progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task(
                f"Testing queries ({category})",
                total=len(queries_to_test)
            )

            if parallel:
                # Run tests in parallel
                tasks = []
                for query in queries_to_test:
                    tasks.append(self.run_single_test(query))

                results = await asyncio.gather(*tasks)
                self.results.extend(results)
                progress.update(task, advance=len(results))
            else:
                # Run tests sequentially
                for query in queries_to_test:
                    result = await self.run_single_test(query)
                    self.results.append(result)
                    progress.update(task, advance=1)

                    # Show immediate feedback
                    if self.verbose:
                        status_icon = "✓" if result.status == "passed" else "✗"
                        status_color = "green" if result.status == "passed" else "red"
                        console.print(
                            f"  [{status_color}]{status_icon}[/{status_color}] "
                            f"{query.query[:50]}... ({result.execution_time:.2f}s)"
                        )

    def generate_report(self) -> Dict[str, Any]:
        """
        Generate test report

        Returns:
            Test report dictionary
        """
        if not self.results:
            return {}

        # Calculate statistics by category
        categories = {}
        for result in self.results:
            cat = result.query.category
            if cat not in categories:
                categories[cat] = {
                    'total': 0,
                    'passed': 0,
                    'failed': 0,
                    'errors': 0,
                    'total_time': 0,
                    'has_sql': 0,
                    'has_insights': 0
                }

            categories[cat]['total'] += 1
            if result.status == 'passed':
                categories[cat]['passed'] += 1
            elif result.status == 'failed':
                categories[cat]['failed'] += 1
            else:
                categories[cat]['errors'] += 1

            categories[cat]['total_time'] += result.execution_time
            if result.has_sql:
                categories[cat]['has_sql'] += 1
            if result.has_insights:
                categories[cat]['has_insights'] += 1

        # Overall statistics
        total_queries = len(self.results)
        passed_queries = sum(1 for r in self.results if r.status == 'passed')
        failed_queries = sum(1 for r in self.results if r.status == 'failed')
        error_queries = sum(1 for r in self.results if r.status == 'error')
        total_time = sum(r.execution_time for r in self.results)
        avg_time = total_time / total_queries if total_queries > 0 else 0

        # Failed query details
        failed_details = []
        for result in self.results:
            if result.status != 'passed':
                failed_details.append({
                    'query': result.query.query,
                    'category': result.query.category,
                    'status': result.status,
                    'errors': result.errors
                })

        report = {
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_queries': total_queries,
                'passed': passed_queries,
                'failed': failed_queries,
                'errors': error_queries,
                'success_rate': (passed_queries / total_queries * 100) if total_queries > 0 else 0,
                'total_time': total_time,
                'average_time': avg_time
            },
            'by_category': categories,
            'failed_queries': failed_details
        }

        return report

    def display_report(self, report: Dict[str, Any]):
        """
        Display test report in formatted output

        Args:
            report: Test report
        """
        summary = report['summary']

        # Display summary panel
        console.print()
        console.print(Panel(
            f"[bold]Test Results Summary[/bold]\n\n"
            f"Total Queries: {summary['total_queries']}\n"
            f"Passed: [green]{summary['passed']}[/green]\n"
            f"Failed: [red]{summary['failed']}[/red]\n"
            f"Errors: [yellow]{summary['errors']}[/yellow]\n"
            f"Success Rate: [{'green' if summary['success_rate'] > 80 else 'yellow' if summary['success_rate'] > 60 else 'red'}]"
            f"{summary['success_rate']:.1f}%[/]\n"
            f"Total Time: {summary['total_time']:.2f}s\n"
            f"Average Time: {summary['average_time']:.2f}s",
            title="Summary",
            border_style="cyan"
        ))

        # Display category breakdown
        console.print("\n[bold cyan]Results by Category:[/bold cyan]")

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Category", style="white", width=15)
        table.add_column("Total", style="white", width=8)
        table.add_column("Passed", style="green", width=8)
        table.add_column("Failed", style="red", width=8)
        table.add_column("Success %", style="cyan", width=10)
        table.add_column("Avg Time", style="yellow", width=10)
        table.add_column("Has SQL", style="magenta", width=8)
        table.add_column("Insights", style="blue", width=8)

        for cat_name, cat_data in report['by_category'].items():
            success_rate = (cat_data['passed'] / cat_data['total'] * 100) if cat_data['total'] > 0 else 0
            avg_time = cat_data['total_time'] / cat_data['total'] if cat_data['total'] > 0 else 0

            table.add_row(
                cat_name.capitalize(),
                str(cat_data['total']),
                str(cat_data['passed']),
                str(cat_data['failed']),
                f"{success_rate:.1f}%",
                f"{avg_time:.2f}s",
                str(cat_data['has_sql']),
                str(cat_data['has_insights'])
            )

        console.print(table)

        # Display failed queries if any
        if report['failed_queries']:
            console.print("\n[bold red]Failed Queries:[/bold red]")
            for failed in report['failed_queries'][:10]:  # Show first 10
                console.print(f"  ✗ [{failed['category']}] {failed['query'][:60]}...")
                if failed['errors']:
                    console.print(f"    Error: {failed['errors'][0]}", style="dim red")

            if len(report['failed_queries']) > 10:
                console.print(f"  ... and {len(report['failed_queries']) - 10} more")

    def save_report(self, report: Dict[str, Any]):
        """
        Save test report to file

        Args:
            report: Test report
        """
        if not self.save_report:
            return

        # Save detailed results
        detailed_report = {
            **report,
            'detailed_results': [
                {
                    'query': r.query.query,
                    'category': r.query.category,
                    'description': r.query.description,
                    'status': r.status,
                    'execution_time': r.execution_time,
                    'has_result': r.has_result,
                    'has_sql': r.has_sql,
                    'has_insights': r.has_insights,
                    'errors': r.errors
                }
                for r in self.results
            ]
        }

        with open(self.report_file, 'w', encoding='utf-8') as f:
            json.dump(detailed_report, f, ensure_ascii=False, indent=2)

        console.print(f"\n[green]Report saved to: {self.report_file}[/green]")


async def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Batch Test for Sales Analytics Agent')
    parser.add_argument(
        '--category',
        choices=['all', 'basic', 'employee', 'period', 'complex', 'trend'],
        default='all',
        help='Test category to run'
    )
    parser.add_argument('--parallel', action='store_true', help='Run tests in parallel')
    parser.add_argument('--verbose', action='store_true', help='Show verbose output')
    parser.add_argument('--save-report', action='store_true', help='Save test report')

    args = parser.parse_args()

    try:
        tester = BatchTester(
            verbose=args.verbose,
            save_report=args.save_report
        )

        # Run tests
        await tester.run_tests(
            category=args.category,
            parallel=args.parallel
        )

        # Generate and display report
        report = tester.generate_report()
        tester.display_report(report)

        # Save report if requested
        if args.save_report:
            tester.save_report(report)

        # Exit with appropriate code
        success_rate = report['summary']['success_rate']
        if success_rate >= 90:
            sys.exit(0)  # Excellent
        elif success_rate >= 70:
            sys.exit(1)  # Good but needs improvement
        else:
            sys.exit(2)  # Poor performance

    except Exception as e:
        console.print(f"[red]Fatal error: {str(e)}[/red]")
        if args.verbose:
            traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    asyncio.run(main())