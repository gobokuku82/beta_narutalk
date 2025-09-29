"""
Sales Analytics Agent - Interactive Query Test
판매 분석 에이전트 대화형 쿼리 테스트

실시간으로 사용자가 쿼리를 입력하고 결과를 확인할 수 있는 테스트 도구

사용법:
    python tests/test_sa_agent_interactive.py [옵션]

옵션:
    --save: 결과를 파일로 저장
    --verbose: 상세 로그 출력
    --no-color: 컬러 출력 비활성화
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.syntax import Syntax
from rich import print as rprint
import traceback

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.service.agents.sales_analytics_agent import SalesAnalyticsAgent
from backend.service.core.config import Config
from backend.service.core.context import create_agent_context

# Create logs directory if it doesn't exist
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f'interactive_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Rich console
console = Console()


class InteractiveTester:
    """Interactive tester for Sales Analytics Agent"""

    def __init__(self, save_results: bool = False, verbose: bool = False):
        """
        Initialize the interactive tester

        Args:
            save_results: Whether to save results to file
            verbose: Whether to show verbose output
        """
        self.save_results = save_results
        self.verbose = verbose
        self.config = Config()
        self.agent = None
        self.session_id = f"interactive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.query_history = []
        self.results_history = []

        # Initialize agent
        self._init_agent()

        if self.save_results:
            self.results_file = Path(f"test_results/interactive_{self.session_id}.json")
            self.results_file.parent.mkdir(exist_ok=True)

    def _init_agent(self):
        """Initialize the Sales Analytics Agent"""
        try:
            self.agent = SalesAnalyticsAgent(self.config)
            console.print("[green]V[/green] Sales Analytics Agent 초기화 완료")
        except Exception as e:
            console.print(f"[red]✗[/red] Agent 초기화 실패: {str(e)}")
            raise

    async def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process a single query

        Args:
            query: User query

        Returns:
            Query result
        """
        start_time = datetime.now()

        try:
            # Show processing message
            with console.status(f"[cyan]처리 중...[/cyan] {query[:50]}...") as status:
                # Run the agent
                result = await self.agent.run(
                    query=query,
                    user_id="test_user",
                    session_id=self.session_id,
                    language="ko"
                )

                # Calculate execution time
                execution_time = (datetime.now() - start_time).total_seconds()

                # Add execution metadata
                result['execution_metadata'] = {
                    'query': query,
                    'execution_time': execution_time,
                    'timestamp': datetime.now().isoformat()
                }

                return result

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            if self.verbose:
                traceback.print_exc()

            return {
                'status': 'error',
                'error': str(e),
                'query': query,
                'execution_time': (datetime.now() - start_time).total_seconds()
            }

    def display_result(self, result: Dict[str, Any]):
        """
        Display query result in formatted output

        Args:
            result: Query result
        """
        # Extract metadata
        metadata = result.get('execution_metadata', {})
        query = metadata.get('query', 'Unknown')
        exec_time = metadata.get('execution_time', 0)

        # Status indicator
        status = result.get('status', 'unknown')
        status_icon = "✓" if status == 'completed' else "✗" if status == 'failed' else "?"
        status_color = "green" if status == 'completed' else "red" if status == 'failed' else "yellow"

        # Create result panel
        console.print()
        console.print(Panel(
            f"[{status_color}]{status_icon}[/{status_color}] Query: {query}\n"
            f"Status: {status} | Execution Time: {exec_time:.2f}s",
            title="Query Result",
            border_style="cyan"
        ))

        # Display formatted result if available
        if result.get('formatted_result'):
            console.print("\n[bold cyan]Formatted Output:[/bold cyan]")
            console.print(Panel(
                result['formatted_result'],
                border_style="blue"
            ))

        # Display SQL if generated
        if result.get('generated_sql'):
            console.print("\n[bold yellow]Generated SQL:[/bold yellow]")
            syntax = Syntax(
                result['generated_sql'],
                "sql",
                theme="monokai",
                line_numbers=True
            )
            console.print(syntax)

        # Display insights if available
        if result.get('insights'):
            console.print("\n[bold green]Insights:[/bold green]")
            for insight in result['insights']:
                console.print(f"  • {insight}")

        # Display statistics if available
        if result.get('statistics'):
            console.print("\n[bold magenta]Statistics:[/bold magenta]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white")

            for key, value in result['statistics'].items():
                if isinstance(value, float):
                    table.add_row(key, f"{value:,.2f}")
                else:
                    table.add_row(key, str(value))

            console.print(table)

        # Display errors if any
        if result.get('errors'):
            console.print("\n[bold red]Errors:[/bold red]")
            for error in result['errors']:
                console.print(f"  ✗ {error}", style="red")

        # Verbose output
        if self.verbose and result.get('execution_results'):
            console.print("\n[bold yellow]Execution Details:[/bold yellow]")
            console.print(json.dumps(result['execution_results'], indent=2, ensure_ascii=False))

    def save_session_results(self):
        """Save session results to file"""
        if not self.save_results or not self.results_history:
            return

        session_data = {
            'session_id': self.session_id,
            'timestamp': datetime.now().isoformat(),
            'total_queries': len(self.query_history),
            'queries': self.query_history,
            'results': self.results_history
        }

        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

        console.print(f"\n[green]Session results saved to: {self.results_file}[/green]")

    def show_help(self):
        """Show help message"""
        help_text = """
[bold cyan]Available Commands:[/bold cyan]
  • Enter any sales query in Korean
  • Type 'help' or '도움말' for this help
  • Type 'history' or '기록' to see query history
  • Type 'clear' or '지우기' to clear screen
  • Type 'exit', 'quit', '종료' to exit

[bold yellow]Example Queries:[/bold yellow]
  • 김철수의 이번달 판매 실적
  • 지난달 전체 매출 현황
  • 이번 분기 목표 달성률
  • 박영희 실적 분석
  • 올해 판매 트렌드 분석

[bold green]Tips:[/bold green]
  • Queries are processed by AI-powered agent
  • SQL is automatically generated when needed
  • Results include statistics and insights
        """
        console.print(Panel(help_text, title="Help", border_style="blue"))

    def show_history(self):
        """Show query history"""
        if not self.query_history:
            console.print("[yellow]No query history yet[/yellow]")
            return

        table = Table(title="Query History", show_header=True, header_style="bold cyan")
        table.add_column("#", style="dim", width=4)
        table.add_column("Query", style="white")
        table.add_column("Status", style="cyan", width=10)
        table.add_column("Time", style="green", width=10)

        for i, (query, result) in enumerate(zip(self.query_history, self.results_history), 1):
            status = result.get('status', 'unknown')
            exec_time = result.get('execution_metadata', {}).get('execution_time', 0)

            status_display = "✓" if status == 'completed' else "✗" if status == 'failed' else "?"
            table.add_row(
                str(i),
                query[:50] + "..." if len(query) > 50 else query,
                status_display,
                f"{exec_time:.2f}s"
            )

        console.print(table)

    async def run_interactive_session(self):
        """Run interactive query session"""
        console.clear()
        console.print(Panel(
            "[bold cyan]Sales Analytics Agent - Interactive Query Tester[/bold cyan]\n"
            "판매 분석 에이전트 대화형 쿼리 테스터\n\n"
            "Type 'help' for commands | 'exit' to quit",
            title="Welcome",
            border_style="cyan"
        ))

        self.show_help()

        while True:
            try:
                # Get user input
                console.print()
                query = Prompt.ask("[bold cyan]Query[/bold cyan]")

                # Check for commands
                if query.lower() in ['exit', 'quit', '종료']:
                    console.print("[yellow]Exiting...[/yellow]")
                    break

                if query.lower() in ['help', '도움말']:
                    self.show_help()
                    continue

                if query.lower() in ['history', '기록']:
                    self.show_history()
                    continue

                if query.lower() in ['clear', '지우기']:
                    console.clear()
                    continue

                if not query.strip():
                    continue

                # Process the query
                result = await self.process_query(query)

                # Store in history
                self.query_history.append(query)
                self.results_history.append(result)

                # Display result
                self.display_result(result)

                # Save if needed
                if self.save_results:
                    self.save_session_results()

            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted by user[/yellow]")
                break
            except Exception as e:
                console.print(f"\n[red]Error: {str(e)}[/red]")
                if self.verbose:
                    traceback.print_exc()

        # Final save
        if self.save_results and self.results_history:
            self.save_session_results()

        # Show summary
        self.show_summary()

    def show_summary(self):
        """Show session summary"""
        if not self.query_history:
            return

        total = len(self.query_history)
        completed = sum(1 for r in self.results_history if r.get('status') == 'completed')
        failed = sum(1 for r in self.results_history if r.get('status') == 'failed')
        avg_time = sum(r.get('execution_metadata', {}).get('execution_time', 0)
                      for r in self.results_history) / total if total > 0 else 0

        console.print()
        console.print(Panel(
            f"[bold]Session Summary[/bold]\n\n"
            f"Total Queries: {total}\n"
            f"Completed: [green]{completed}[/green]\n"
            f"Failed: [red]{failed}[/red]\n"
            f"Average Time: {avg_time:.2f}s\n"
            f"Session ID: {self.session_id}",
            title="Summary",
            border_style="cyan"
        ))


async def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Interactive Sales Analytics Agent Tester')
    parser.add_argument('--save', action='store_true', help='Save results to file')
    parser.add_argument('--verbose', action='store_true', help='Show verbose output')
    parser.add_argument('--no-color', action='store_true', help='Disable colored output')

    args = parser.parse_args()

    if args.no_color:
        console = Console(force_terminal=False, force_jupyter=False)

    try:
        tester = InteractiveTester(
            save_results=args.save,
            verbose=args.verbose
        )
        await tester.run_interactive_session()
    except Exception as e:
        console.print(f"[red]Fatal error: {str(e)}[/red]")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())