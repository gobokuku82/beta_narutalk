"""
Sales Analytics Agent Interactive Flow Test
직접 쿼리를 입력하고 각 실행 단계를 추적하는 인터랙티브 테스트

실행 방법:
    python tests/test_interactive_flow.py
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
from functools import wraps
from dotenv import load_dotenv
import traceback

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.service.agents.sales_analytics_agent import SalesAnalyticsAgent
from backend.service.tools.text2sql_tool import get_text2sql_tool
from backend.service.tools.sql_executor import SQLExecutor
from backend.service.core.config import Config

# Rich 라이브러리 (없으면 기본 print 사용)
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.syntax import Syntax
    from rich.progress import track
    from rich import print as rprint
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None
    rprint = print

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # 기본은 WARNING으로 설정
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FlowTracker:
    """플로우 추적 클래스"""

    def __init__(self, verbose: bool = False):
        self.steps = []
        self.current_step = 0
        self.verbose = verbose

    def add_step(self, name: str, input_data: Any, output_data: Any, duration: float):
        """단계 추가"""
        self.steps.append({
            "step": self.current_step + 1,
            "name": name,
            "input": input_data,
            "output": output_data,
            "duration": duration
        })
        self.current_step += 1

    def display_step(self, step: Dict[str, Any], mode: str = "simple"):
        """단계 표시"""
        if RICH_AVAILABLE:
            panel = Panel(
                f"[bold cyan]{step['name']}[/bold cyan]\n"
                f"실행 시간: {step['duration']:.2f}초",
                title=f"[yellow]STEP {step['step']}[/yellow]",
                expand=False
            )
            console.print(panel)

            if mode == "detailed":
                if step['input']:
                    console.print("[dim]입력:[/dim]")
                    if isinstance(step['input'], str):
                        console.print(f"  {step['input']}")
                    else:
                        console.print(json.dumps(step['input'], ensure_ascii=False, indent=2))

                if step['output']:
                    console.print("[dim]출력:[/dim]")
                    if isinstance(step['output'], dict):
                        output_str = json.dumps(step['output'], ensure_ascii=False, indent=2)
                        if len(output_str) > 500:
                            output_str = output_str[:500] + "..."
                        console.print(output_str)
                    else:
                        console.print(f"  {step['output']}")
        else:
            print(f"\n{'='*50}")
            print(f"STEP {step['step']}: {step['name']}")
            print(f"실행 시간: {step['duration']:.2f}초")
            print('='*50)

            if mode == "detailed" and self.verbose:
                if step['input']:
                    print("입력:", step['input'])
                if step['output']:
                    print("출력:", step['output'])


class InteractiveTester:
    """인터랙티브 테스터"""

    def __init__(self):
        self.agent = SalesAnalyticsAgent()
        self.text2sql_tool = get_text2sql_tool()
        self.sql_executor = SQLExecutor()
        self.flow_tracker = FlowTracker()

        # 예제 쿼리
        self.example_queries = [
            # 기본 SQL 쿼리
            "윤수아의 2024년 11월 판매 실적 조회",
            "정예준 담당자의 최근 3개월 매출 추이",
            "파라곤이비인후과 거래처의 월별 매출 현황",
            "상위 5명의 영업사원 실적 비교",

            # Data Collection Subgraph 호출 쿼리
            "모든 영업사원의 실적 데이터를 수집하고 종합해줘",
            "서부팀 전체의 실적 데이터를 수집해줘",
            "전체 거래처 데이터를 수집하고 정리해줘",

            # Analysis Subgraph 호출 쿼리
            "윤하은과 최수아의 실적을 비교 분석해줘",
            "2024년 3분기 전체 매출을 분석해줘",
            "거래처별 방문 횟수와 매출 상관관계를 분석해줘",

            # 복합 쿼리 (Data Collection + Analysis)
            "서부팀 전체 실적을 수집하고 목표 대비 달성률을 분석해줘",
            "모든 데이터를 수집하고 트렌드 분석을 실행해줘",
            "전체 영업팀 데이터를 수집하고 개선점을 제시해줘"
        ]

        # 실행 히스토리
        self.history = []

    def display_welcome(self):
        """환영 메시지"""
        if RICH_AVAILABLE:
            panel = Panel(
                "[bold cyan]Sales Analytics Agent Interactive Test[/bold cyan]\n\n"
                "직접 쿼리를 입력하여 전체 실행 플로우를 확인할 수 있습니다.\n"
                "각 단계별로 어떻게 처리되는지 실시간으로 추적합니다.",
                title="[bold green]Welcome[/bold green]",
                expand=False
            )
            console.print(panel)
        else:
            print("\n" + "="*60)
            print("Sales Analytics Agent Interactive Test")
            print("="*60)
            print("직접 쿼리를 입력하여 전체 실행 플로우를 확인할 수 있습니다.")
            print("각 단계별로 어떻게 처리되는지 실시간으로 추적합니다.\n")

    def get_query_input(self) -> Optional[str]:
        """쿼리 입력 받기"""
        if RICH_AVAILABLE:
            console.print("\n[bold yellow]쿼리 입력 방법 선택:[/bold yellow]")
            console.print("[1] 직접 입력")
            console.print("[2] 예제 쿼리 선택")
            console.print("[3] 히스토리에서 선택")
            console.print("[4] 종료")
        else:
            print("\n쿼리 입력 방법 선택:")
            print("[1] 직접 입력")
            print("[2] 예제 쿼리 선택")
            print("[3] 히스토리에서 선택")
            print("[4] 종료")

        choice = input("\n선택: ").strip()

        if choice == "1":
            return input("\n쿼리를 입력하세요: ").strip()

        elif choice == "2":
            if RICH_AVAILABLE:
                console.print("\n[bold cyan]예제 쿼리:[/bold cyan]")
            else:
                print("\n예제 쿼리:")

            for i, query in enumerate(self.example_queries, 1):
                print(f"[{i}] {query}")

            try:
                idx = int(input("\n번호 선택: ")) - 1
                if 0 <= idx < len(self.example_queries):
                    return self.example_queries[idx]
            except:
                pass

        elif choice == "3":
            if not self.history:
                print("히스토리가 없습니다.")
                return None

            if RICH_AVAILABLE:
                console.print("\n[bold cyan]히스토리:[/bold cyan]")
            else:
                print("\n히스토리:")

            for i, item in enumerate(self.history[-10:], 1):  # 최근 10개만
                print(f"[{i}] {item['query']} ({item['time']})")

            try:
                idx = int(input("\n번호 선택: ")) - 1
                if 0 <= idx < min(10, len(self.history)):
                    return self.history[-(10-idx)]['query']
            except:
                pass

        elif choice == "4":
            return None

        return None

    def get_execution_mode(self) -> str:
        """실행 모드 선택"""
        if RICH_AVAILABLE:
            console.print("\n[bold yellow]실행 모드:[/bold yellow]")
            console.print("[1] 전체 실행 (빠르게)")
            console.print("[2] 단계별 실행 (각 단계 확인)")
            console.print("[3] 상세 모드 (디버깅)")
        else:
            print("\n실행 모드:")
            print("[1] 전체 실행 (빠르게)")
            print("[2] 단계별 실행 (각 단계 확인)")
            print("[3] 상세 모드 (디버깅)")

        choice = input("\n선택 (기본값: 2): ").strip() or "2"

        mode_map = {
            "1": "fast",
            "2": "step",
            "3": "debug"
        }

        return mode_map.get(choice, "step")

    async def execute_with_tracking(self, query: str, mode: str = "step"):
        """플로우 추적하며 실행"""
        self.flow_tracker = FlowTracker(verbose=(mode == "debug"))

        try:
            # Step 1: Query Parsing
            if mode != "fast":
                print("\n" + "━"*50)

            start = time.time()

            # Text2SQL tool로 파싱 및 SQL 생성
            if mode != "fast":
                if RICH_AVAILABLE:
                    console.print("[bold cyan]Step 1: Query Parsing & SQL Generation[/bold cyan]")
                else:
                    print("Step 1: Query Parsing & SQL Generation")

            sql_result = await self.text2sql_tool.generate_sql(query)

            self.flow_tracker.add_step(
                "Query Parsing & SQL Generation",
                query,
                {
                    "sql": sql_result.get("sql"),
                    "database": sql_result.get("database"),
                    "method": sql_result.get("method"),
                    "confidence": sql_result.get("confidence")
                },
                time.time() - start
            )

            if mode != "fast":
                self.flow_tracker.display_step(self.flow_tracker.steps[-1],
                                              "detailed" if mode == "debug" else "simple")
                if mode == "step":
                    input("\n[Enter를 눌러 다음 단계로...]")

            # Step 2: Agent Execution
            if mode != "fast":
                if RICH_AVAILABLE:
                    console.print("\n[bold cyan]Step 2: Agent Execution (Full Pipeline)[/bold cyan]")
                else:
                    print("\nStep 2: Agent Execution (Full Pipeline)")

            start = time.time()

            # Agent 실행
            result = await self.agent.run(
                query=query,
                user_id="interactive_user",
                session_id=f"interactive_{int(time.time())}"
            )

            self.flow_tracker.add_step(
                "Agent Execution",
                {"query": query},
                {
                    "status": result.get("status"),
                    "execution_step": result.get("execution_step"),
                    "has_sql_result": result.get("sql_result") is not None,
                    "has_insights": result.get("insights") is not None,
                    "has_formatted_result": result.get("formatted_result") is not None
                },
                time.time() - start
            )

            if mode != "fast":
                self.flow_tracker.display_step(self.flow_tracker.steps[-1],
                                              "detailed" if mode == "debug" else "simple")

            # Step 2-1: Execution Plan 표시
            if result.get("execution_plan") and mode != "fast":
                if RICH_AVAILABLE:
                    console.print("\n[bold yellow]실행 계획:[/bold yellow]")
                else:
                    print("\n실행 계획:")

                plan = result["execution_plan"]
                if plan.get("use_sql"):
                    print("  ✓ SQL 쿼리 사용")
                if plan.get("use_subgraphs"):
                    for subgraph in plan["use_subgraphs"]:
                        print(f"  ✓ {subgraph} subgraph 호출")

                if mode == "step":
                    input("\n[Enter를 눌러 계속...]")

            # Step 2-2: Subgraph 실행 결과 표시
            if result.get("execution_results") and mode != "fast":
                exec_results = result["execution_results"]

                # Data Collection Subgraph 결과
                if exec_results.get("collection"):
                    if RICH_AVAILABLE:
                        console.print("\n[bold magenta]📊 Data Collection Subgraph 실행됨[/bold magenta]")
                    else:
                        print("\n📊 Data Collection Subgraph 실행됨")

                    collection = exec_results["collection"]
                    if collection.get("status") == "completed":
                        print("  상태: ✅ 완료")
                        if result.get("collected_data"):
                            data = result["collected_data"]
                            if data.get("performance"):
                                print(f"  - 실적 데이터 수집 완료")
                            if data.get("target"):
                                print(f"  - 목표 데이터 수집 완료")
                            if data.get("client"):
                                print(f"  - 거래처 데이터 수집 완료")

                    if mode == "step":
                        input("\n[Enter를 눌러 계속...]")

                # Analysis Subgraph 결과
                if exec_results.get("analysis"):
                    if RICH_AVAILABLE:
                        console.print("\n[bold magenta]🔍 Analysis Subgraph 실행됨[/bold magenta]")
                    else:
                        print("\n🔍 Analysis Subgraph 실행됨")

                    analysis = exec_results["analysis"]
                    if analysis.get("status") == "completed":
                        print("  상태: ✅ 완료")
                        if result.get("analysis_result"):
                            analysis_data = result["analysis_result"]
                            if analysis_data.get("basic_metrics"):
                                print("  - 기본 통계 계산 완료")
                            if analysis_data.get("trend_analysis"):
                                print("  - 트렌드 분석 완료")
                            if analysis_data.get("insights"):
                                print(f"  - {len(analysis_data['insights'])}개 인사이트 생성")

                    if mode == "step":
                        input("\n[Enter를 눌러 계속...]")

            # Step 3: 중간 결과 표시 (있는 경우)
            if result.get("generated_sql") and mode != "fast":
                if RICH_AVAILABLE:
                    console.print("\n[dim]생성된 SQL:[/dim]")
                    syntax = Syntax(result["generated_sql"], "sql", theme="monokai")
                    console.print(syntax)
                else:
                    print("\n생성된 SQL:")
                    print(result["generated_sql"])

                if mode == "step":
                    input("\n[Enter를 눌러 계속...]")

            # Step 4: SQL 실행 결과 표시
            if result.get("sql_result") and mode != "fast":
                if RICH_AVAILABLE:
                    console.print("\n[dim]SQL 실행 결과:[/dim]")

                    # 테이블로 표시
                    if isinstance(result["sql_result"], list) and result["sql_result"]:
                        table = Table()

                        # 컬럼 추가
                        first_row = result["sql_result"][0]
                        for col in first_row.keys():
                            table.add_column(str(col))

                        # 데이터 추가 (최대 5행)
                        for row in result["sql_result"][:5]:
                            table.add_row(*[str(v) for v in row.values()])

                        console.print(table)

                        if len(result["sql_result"]) > 5:
                            console.print(f"... 총 {len(result['sql_result'])}개 행")
                else:
                    print("\nSQL 실행 결과:")
                    if isinstance(result["sql_result"], list) and result["sql_result"]:
                        for row in result["sql_result"][:3]:
                            print(row)
                        if len(result["sql_result"]) > 3:
                            print(f"... 총 {len(result['sql_result'])}개 행")

                if mode == "step":
                    input("\n[Enter를 눌러 계속...]")

            # Step 5: Insights 표시
            if result.get("insights") and mode != "fast":
                if RICH_AVAILABLE:
                    console.print("\n[dim]분석 인사이트:[/dim]")
                    for insight in result["insights"]:
                        console.print(f"  • {insight}")
                else:
                    print("\n분석 인사이트:")
                    for insight in result["insights"]:
                        print(f"  • {insight}")

                if mode == "step":
                    input("\n[Enter를 눌러 계속...]")

            # Step 6: 최종 결과
            if RICH_AVAILABLE:
                console.print("\n[bold green]최종 결과:[/bold green]")

                if result.get("formatted_result"):
                    panel = Panel(
                        result["formatted_result"],
                        title="[cyan]Analysis Result[/cyan]",
                        expand=False
                    )
                    console.print(panel)
                else:
                    console.print("[red]포맷된 결과가 없습니다.[/red]")
            else:
                print("\n" + "="*50)
                print("최종 결과:")
                print("="*50)
                if result.get("formatted_result"):
                    print(result["formatted_result"])
                else:
                    print("포맷된 결과가 없습니다.")

            # 히스토리에 추가
            self.history.append({
                "query": query,
                "time": datetime.now().strftime("%H:%M:%S"),
                "success": result.get("status") == "completed"
            })

            # 결과 저장 옵션
            save = input("\n\n결과를 파일로 저장하시겠습니까? (y/n): ").strip().lower()
            if save == 'y':
                self.save_results(query, result)

            return result

        except Exception as e:
            logger.error(f"실행 중 오류: {e}")
            if RICH_AVAILABLE:
                console.print(f"[red]오류 발생: {e}[/red]")
                if mode == "debug":
                    console.print("[dim]" + traceback.format_exc() + "[/dim]")
            else:
                print(f"\n오류 발생: {e}")
                if mode == "debug":
                    print(traceback.format_exc())
            return None

    def save_results(self, query: str, result: Dict[str, Any]):
        """결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tests/interactive_result_{timestamp}.json"

        data = {
            "timestamp": timestamp,
            "query": query,
            "result": result,
            "flow_steps": self.flow_tracker.steps
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"결과가 {filename}에 저장되었습니다.")

    async def run(self):
        """메인 실행 루프"""
        self.display_welcome()

        while True:
            query = self.get_query_input()

            if query is None:
                print("\n종료합니다.")
                break

            if not query:
                print("올바른 쿼리를 입력해주세요.")
                continue

            mode = self.get_execution_mode()

            await self.execute_with_tracking(query, mode)

            # 계속 여부
            cont = input("\n\n다른 쿼리를 실행하시겠습니까? (y/n): ").strip().lower()
            if cont != 'y':
                break

        print("\n테스트를 종료합니다. 감사합니다!")


async def main():
    """메인 함수"""
    tester = InteractiveTester()
    await tester.run()


if __name__ == "__main__":
    asyncio.run(main())