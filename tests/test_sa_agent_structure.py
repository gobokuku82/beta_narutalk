"""
Sales Analytics Agent - Structure and Import Validation Test
판매 분석 에이전트 구조 및 Import 검증 테스트

파일 구조, import, 설정, 의존성 등을 검증하는 테스트

사용법:
    python tests/test_sa_agent_structure.py [옵션]

옵션:
    --verbose: 상세 출력
    --fix: 자동으로 수정 가능한 문제 해결 시도
"""

import asyncio
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich import print as rprint
import importlib
import inspect

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create logs directory if it doesn't exist
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f'structure_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Rich console
console = Console()


@dataclass
class ValidationResult:
    """Validation result container"""
    category: str
    item: str
    status: str  # passed, failed, warning
    message: str
    details: Optional[Dict[str, Any]] = None


class StructureValidator:
    """Structure and import validator for Sales Analytics Agent"""

    def __init__(self, verbose: bool = False, auto_fix: bool = False):
        """
        Initialize validator

        Args:
            verbose: Show verbose output
            auto_fix: Attempt to auto-fix issues
        """
        self.verbose = verbose
        self.auto_fix = auto_fix
        self.results: List[ValidationResult] = []
        self.base_path = Path(__file__).parent.parent

        # Define expected structure
        self.expected_structure = self._define_expected_structure()

    def _define_expected_structure(self) -> Dict[str, Any]:
        """Define expected file and directory structure"""
        return {
            'backend': {
                'service': {
                    'agents': [
                        'sales_analytics_agent.py',
                        '__init__.py'
                    ],
                    'subgraphs': [
                        'data_collection_subgraph.py',
                        'analysis_subgraph.py',
                        '__init__.py'
                    ],
                    'tools': [
                        'sql_executor.py',
                        'sql_generator.py',
                        'text2sql_tool.py',
                        '__init__.py'
                    ],
                    'core': [
                        'config.py',
                        'context.py',
                        'states.py',
                        '__init__.py'
                    ]
                }
            },
            'database': {
                'storage': {
                    'sales_performance': [
                        'sales_performance_db.db',
                        'sales_target_db.db',
                        'clients_db.db'
                    ]
                }
            },
            'tests': [],
            'logs': [],
            'checkpoints': []
        }

    def validate_directory_structure(self) -> List[ValidationResult]:
        """Validate directory structure"""
        results = []

        def check_structure(expected: Dict, base: Path, prefix: str = ""):
            """Recursively check directory structure"""
            for name, content in expected.items():
                path = base / name
                full_name = f"{prefix}/{name}" if prefix else name

                if isinstance(content, dict):
                    # It's a directory
                    if path.exists() and path.is_dir():
                        results.append(ValidationResult(
                            category="structure",
                            item=full_name,
                            status="passed",
                            message=f"Directory exists: {path}"
                        ))
                        # Check subdirectories
                        check_structure(content, path, full_name)
                    else:
                        results.append(ValidationResult(
                            category="structure",
                            item=full_name,
                            status="failed",
                            message=f"Directory missing: {path}"
                        ))
                        # Try to create if auto_fix
                        if self.auto_fix:
                            try:
                                path.mkdir(parents=True, exist_ok=True)
                                results.append(ValidationResult(
                                    category="structure",
                                    item=full_name,
                                    status="warning",
                                    message=f"Directory created: {path}"
                                ))
                            except Exception as e:
                                logger.error(f"Failed to create directory: {e}")

                elif isinstance(content, list):
                    # It's a list of files
                    for file_name in content:
                        file_path = path / file_name
                        file_full_name = f"{full_name}/{file_name}"

                        if file_path.exists():
                            results.append(ValidationResult(
                                category="structure",
                                item=file_full_name,
                                status="passed",
                                message=f"File exists: {file_path}"
                            ))
                        else:
                            # Check if it's optional (like .db files)
                            if file_name.endswith('.db'):
                                results.append(ValidationResult(
                                    category="structure",
                                    item=file_full_name,
                                    status="warning",
                                    message=f"Database file missing (will be created on first use): {file_path}"
                                ))
                            else:
                                results.append(ValidationResult(
                                    category="structure",
                                    item=file_full_name,
                                    status="failed",
                                    message=f"File missing: {file_path}"
                                ))

        check_structure(self.expected_structure, self.base_path)
        return results

    def validate_imports(self) -> List[ValidationResult]:
        """Validate Python imports"""
        results = []

        # Core modules to import
        modules_to_check = [
            ('backend.service.agents.sales_analytics_agent', 'SalesAnalyticsAgent'),
            ('backend.service.core.config', 'Config'),
            ('backend.service.core.context', 'create_agent_context'),
            ('backend.service.core.states', 'SalesState'),
            ('backend.service.subgraphs.data_collection_subgraph', 'DataCollectionSubgraph'),
            ('backend.service.subgraphs.analysis_subgraph', 'AnalysisSubgraph'),
            ('backend.service.tools.sql_executor', 'SQLExecutor'),
            ('backend.service.tools.sql_generator', 'SQLGenerator'),
            ('backend.service.tools.text2sql_tool', 'get_text2sql_tool'),
        ]

        for module_name, class_name in modules_to_check:
            try:
                module = importlib.import_module(module_name)

                # Check if the expected class/function exists
                if hasattr(module, class_name):
                    results.append(ValidationResult(
                        category="import",
                        item=f"{module_name}.{class_name}",
                        status="passed",
                        message=f"Successfully imported {class_name} from {module_name}"
                    ))
                else:
                    results.append(ValidationResult(
                        category="import",
                        item=f"{module_name}.{class_name}",
                        status="failed",
                        message=f"Module {module_name} exists but {class_name} not found"
                    ))

            except ImportError as e:
                results.append(ValidationResult(
                    category="import",
                    item=f"{module_name}.{class_name}",
                    status="failed",
                    message=f"Failed to import {module_name}: {str(e)}"
                ))
            except Exception as e:
                results.append(ValidationResult(
                    category="import",
                    item=f"{module_name}.{class_name}",
                    status="failed",
                    message=f"Error checking {module_name}: {str(e)}"
                ))

        return results

    def validate_dependencies(self) -> List[ValidationResult]:
        """Validate external dependencies"""
        results = []

        # Required packages
        required_packages = [
            'langchain_core',
            'langchain_openai',
            'langgraph',
            'dotenv',
            'rich',
            'sqlite3',  # Built-in
            'asyncio',  # Built-in
        ]

        for package in required_packages:
            try:
                if package in ['sqlite3', 'asyncio']:
                    # Built-in modules
                    __import__(package)
                else:
                    # External packages
                    importlib.import_module(package)

                results.append(ValidationResult(
                    category="dependency",
                    item=package,
                    status="passed",
                    message=f"Package {package} is installed"
                ))

            except ImportError:
                results.append(ValidationResult(
                    category="dependency",
                    item=package,
                    status="failed",
                    message=f"Package {package} is not installed"
                ))

        return results

    def validate_environment(self) -> List[ValidationResult]:
        """Validate environment variables and configuration"""
        results = []

        # Check for .env file
        env_file = self.base_path / '.env'
        if env_file.exists():
            results.append(ValidationResult(
                category="environment",
                item=".env",
                status="passed",
                message=".env file exists"
            ))
        else:
            results.append(ValidationResult(
                category="environment",
                item=".env",
                status="warning",
                message=".env file not found (using environment variables)"
            ))

        # Check required environment variables
        required_env_vars = [
            'OPENAI_API_KEY',
        ]

        for var in required_env_vars:
            if os.getenv(var):
                results.append(ValidationResult(
                    category="environment",
                    item=var,
                    status="passed",
                    message=f"Environment variable {var} is set"
                ))
            else:
                results.append(ValidationResult(
                    category="environment",
                    item=var,
                    status="warning",
                    message=f"Environment variable {var} not set (agent may work without LLM features)"
                ))

        return results

    def validate_config(self) -> List[ValidationResult]:
        """Validate configuration"""
        results = []

        try:
            from backend.service.core.config import Config

            config = Config()

            # Check if config can be initialized
            results.append(ValidationResult(
                category="config",
                item="Config class",
                status="passed",
                message="Config class initialized successfully"
            ))

            # Validate config
            if config.validate():
                results.append(ValidationResult(
                    category="config",
                    item="Config validation",
                    status="passed",
                    message="Config validation passed"
                ))
            else:
                results.append(ValidationResult(
                    category="config",
                    item="Config validation",
                    status="failed",
                    message="Config validation failed"
                ))

            # Check critical paths
            critical_paths = ['BASE_DIR', 'DB_DIR', 'CHECKPOINT_DIR', 'LOG_DIR']
            for path_name in critical_paths:
                path_value = getattr(config, path_name, None)
                if path_value:
                    if Path(path_value).exists():
                        results.append(ValidationResult(
                            category="config",
                            item=f"Config.{path_name}",
                            status="passed",
                            message=f"{path_name}: {path_value}"
                        ))
                    else:
                        results.append(ValidationResult(
                            category="config",
                            item=f"Config.{path_name}",
                            status="warning",
                            message=f"{path_name} path does not exist: {path_value}"
                        ))
                else:
                    results.append(ValidationResult(
                        category="config",
                        item=f"Config.{path_name}",
                        status="failed",
                        message=f"{path_name} not defined in Config"
                    ))

        except Exception as e:
            results.append(ValidationResult(
                category="config",
                item="Config",
                status="failed",
                message=f"Failed to validate config: {str(e)}"
            ))

        return results

    def validate_agent_initialization(self) -> List[ValidationResult]:
        """Validate agent can be initialized"""
        results = []

        try:
            from backend.service.agents.sales_analytics_agent import SalesAnalyticsAgent
            from backend.service.core.config import Config

            config = Config()
            agent = SalesAnalyticsAgent(config)

            results.append(ValidationResult(
                category="agent",
                item="SalesAnalyticsAgent",
                status="passed",
                message="Agent initialized successfully"
            ))

            # Check agent components
            if hasattr(agent, 'workflow'):
                results.append(ValidationResult(
                    category="agent",
                    item="Agent workflow",
                    status="passed",
                    message="Agent workflow exists"
                ))
            else:
                results.append(ValidationResult(
                    category="agent",
                    item="Agent workflow",
                    status="failed",
                    message="Agent workflow not found"
                ))

            # Check if LLM is configured
            if hasattr(agent, 'use_llm_planning'):
                if agent.use_llm_planning:
                    results.append(ValidationResult(
                        category="agent",
                        item="LLM planning",
                        status="passed",
                        message="LLM planning enabled"
                    ))
                else:
                    results.append(ValidationResult(
                        category="agent",
                        item="LLM planning",
                        status="warning",
                        message="LLM planning disabled (will use rule-based planning)"
                    ))

        except Exception as e:
            results.append(ValidationResult(
                category="agent",
                item="SalesAnalyticsAgent",
                status="failed",
                message=f"Failed to initialize agent: {str(e)}",
                details={"error": str(e), "traceback": traceback.format_exc()}
            ))

        return results

    def validate_langgraph_compatibility(self) -> List[ValidationResult]:
        """Validate LangGraph compatibility"""
        results = []

        try:
            import langgraph
            from packaging import version

            # Get LangGraph version
            lg_version = getattr(langgraph, '__version__', 'unknown')

            results.append(ValidationResult(
                category="langgraph",
                item="Version",
                status="passed",
                message=f"LangGraph version: {lg_version}"
            ))

            # Check required LangGraph components
            required_components = [
                ('langgraph.graph', 'StateGraph'),
                ('langgraph.graph', 'START'),
                ('langgraph.graph', 'END'),
                ('langgraph.runtime', 'Runtime'),
                ('langgraph.checkpoint.sqlite.aio', 'AsyncSqliteSaver'),
            ]

            for module_path, component in required_components:
                try:
                    module = importlib.import_module(module_path)
                    if hasattr(module, component):
                        results.append(ValidationResult(
                            category="langgraph",
                            item=f"{module_path}.{component}",
                            status="passed",
                            message=f"Component available: {component}"
                        ))
                    else:
                        results.append(ValidationResult(
                            category="langgraph",
                            item=f"{module_path}.{component}",
                            status="failed",
                            message=f"Component not found: {component}"
                        ))
                except ImportError as e:
                    results.append(ValidationResult(
                        category="langgraph",
                        item=f"{module_path}.{component}",
                        status="failed",
                        message=f"Module not found: {module_path}"
                    ))

        except Exception as e:
            results.append(ValidationResult(
                category="langgraph",
                item="LangGraph",
                status="failed",
                message=f"Failed to validate LangGraph: {str(e)}"
            ))

        return results

    async def validate_async_functionality(self) -> List[ValidationResult]:
        """Validate async functionality"""
        results = []

        try:
            from backend.service.agents.sales_analytics_agent import SalesAnalyticsAgent
            from backend.service.core.config import Config

            config = Config()
            agent = SalesAnalyticsAgent(config)

            # Test async run
            test_result = await agent.run(
                query="테스트 쿼리",
                user_id="test_user",
                session_id="test_session",
                language="ko"
            )

            if test_result and 'status' in test_result:
                results.append(ValidationResult(
                    category="async",
                    item="Agent.run()",
                    status="passed",
                    message="Async run method works"
                ))
            else:
                results.append(ValidationResult(
                    category="async",
                    item="Agent.run()",
                    status="warning",
                    message="Async run executed but returned unexpected result"
                ))

        except Exception as e:
            results.append(ValidationResult(
                category="async",
                item="Agent.run()",
                status="failed",
                message=f"Async functionality test failed: {str(e)}"
            ))

        return results

    def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation tests"""
        console.print(Panel(
            "[bold cyan]Sales Analytics Agent Structure Validation[/bold cyan]\n"
            "파일 구조, Import, 설정 검증",
            title="Structure Validator",
            border_style="cyan"
        ))

        all_results = []

        # 1. Directory structure
        console.print("\n[bold yellow]1. Validating Directory Structure...[/bold yellow]")
        structure_results = self.validate_directory_structure()
        all_results.extend(structure_results)
        self._print_category_summary("Directory Structure", structure_results)

        # 2. Python imports
        console.print("\n[bold yellow]2. Validating Python Imports...[/bold yellow]")
        import_results = self.validate_imports()
        all_results.extend(import_results)
        self._print_category_summary("Python Imports", import_results)

        # 3. Dependencies
        console.print("\n[bold yellow]3. Validating Dependencies...[/bold yellow]")
        dependency_results = self.validate_dependencies()
        all_results.extend(dependency_results)
        self._print_category_summary("Dependencies", dependency_results)

        # 4. Environment
        console.print("\n[bold yellow]4. Validating Environment...[/bold yellow]")
        env_results = self.validate_environment()
        all_results.extend(env_results)
        self._print_category_summary("Environment", env_results)

        # 5. Configuration
        console.print("\n[bold yellow]5. Validating Configuration...[/bold yellow]")
        config_results = self.validate_config()
        all_results.extend(config_results)
        self._print_category_summary("Configuration", config_results)

        # 6. Agent initialization
        console.print("\n[bold yellow]6. Validating Agent Initialization...[/bold yellow]")
        agent_results = self.validate_agent_initialization()
        all_results.extend(agent_results)
        self._print_category_summary("Agent", agent_results)

        # 7. LangGraph compatibility
        console.print("\n[bold yellow]7. Validating LangGraph Compatibility...[/bold yellow]")
        langgraph_results = self.validate_langgraph_compatibility()
        all_results.extend(langgraph_results)
        self._print_category_summary("LangGraph", langgraph_results)

        self.results = all_results

        # Generate summary
        summary = self._generate_summary(all_results)
        return summary

    async def run_all_validations_async(self) -> Dict[str, Any]:
        """Run all validations including async tests"""
        # Run sync validations first
        summary = self.run_all_validations()

        # Add async validation
        console.print("\n[bold yellow]8. Validating Async Functionality...[/bold yellow]")
        async_results = await self.validate_async_functionality()
        self.results.extend(async_results)
        self._print_category_summary("Async", async_results)

        # Update summary
        summary = self._generate_summary(self.results)
        return summary

    def _print_category_summary(self, category: str, results: List[ValidationResult]):
        """Print summary for a category"""
        passed = sum(1 for r in results if r.status == "passed")
        failed = sum(1 for r in results if r.status == "failed")
        warnings = sum(1 for r in results if r.status == "warning")

        status_text = f"Passed: [green]{passed}[/green], Failed: [red]{failed}[/red], Warnings: [yellow]{warnings}[/yellow]"
        console.print(f"  {status_text}")

        if self.verbose:
            for result in results:
                if result.status == "failed":
                    console.print(f"    [red]X[/red] {result.item}: {result.message}")
                elif result.status == "warning":
                    console.print(f"    [yellow]![/yellow] {result.item}: {result.message}")
                elif self.verbose:
                    console.print(f"    [green]V[/green] {result.item}")

    def _generate_summary(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """Generate validation summary"""
        total = len(results)
        passed = sum(1 for r in results if r.status == "passed")
        failed = sum(1 for r in results if r.status == "failed")
        warnings = sum(1 for r in results if r.status == "warning")

        # Group by category
        by_category = {}
        for result in results:
            if result.category not in by_category:
                by_category[result.category] = {
                    'passed': 0,
                    'failed': 0,
                    'warning': 0,
                    'items': []
                }

            by_category[result.category][result.status] += 1
            if result.status != "passed" or self.verbose:
                by_category[result.category]['items'].append({
                    'item': result.item,
                    'status': result.status,
                    'message': result.message
                })

        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_checks': total,
            'passed': passed,
            'failed': failed,
            'warnings': warnings,
            'success_rate': (passed / total * 100) if total > 0 else 0,
            'by_category': by_category,
            'critical_issues': [r for r in results if r.status == "failed"]
        }

        # Display final summary
        console.print()
        console.print(Panel(
            f"[bold]Validation Summary[/bold]\n\n"
            f"Total Checks: {total}\n"
            f"Passed: [green]{passed}[/green]\n"
            f"Failed: [red]{failed}[/red]\n"
            f"Warnings: [yellow]{warnings}[/yellow]\n"
            f"Success Rate: [{'green' if summary['success_rate'] > 90 else 'yellow' if summary['success_rate'] > 70 else 'red'}]"
            f"{summary['success_rate']:.1f}%[/]",
            title="Summary",
            border_style="cyan"
        ))

        # Show critical issues
        if summary['critical_issues']:
            console.print("\n[bold red]Critical Issues:[/bold red]")
            for issue in summary['critical_issues'][:5]:
                console.print(f"  X [{issue.category}] {issue.item}: {issue.message}")

            if len(summary['critical_issues']) > 5:
                console.print(f"  ... and {len(summary['critical_issues']) - 5} more")

        # Overall status
        if failed == 0:
            console.print("\n[bold green]V All critical checks passed![/bold green]")
        else:
            console.print(f"\n[bold red]X {failed} critical issues found. Please fix them before running the agent.[/bold red]")

        return summary


async def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Structure Validation for Sales Analytics Agent')
    parser.add_argument('--verbose', action='store_true', help='Show verbose output')
    parser.add_argument('--fix', action='store_true', help='Attempt to auto-fix issues')

    args = parser.parse_args()

    try:
        validator = StructureValidator(
            verbose=args.verbose,
            auto_fix=args.fix
        )

        # Run validations
        summary = await validator.run_all_validations_async()

        # Exit with appropriate code
        if summary['failed'] == 0:
            sys.exit(0)  # All passed
        elif summary['failed'] < 5:
            sys.exit(1)  # Minor issues
        else:
            sys.exit(2)  # Major issues

    except Exception as e:
        console.print(f"[red]Fatal error: {str(e)}[/red]")
        if args.verbose:
            traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    asyncio.run(main())