"""
Integrated Flow Test
전체 시스템 플로우 통합 테스트
Query → LLM → Agent → Graph → Subgraph → Tool → Result
"""

import asyncio
import logging
import sys
import os
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from colorama import init, Fore, Back, Style

# Initialize colorama for Windows
init(autoreset=True)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all components
from backend.service.utils.llm_manager import get_llm_manager
from backend.service.agents import (
    SearchAgent,
    SalesAnalyticsAgent,
    ComplianceCheckAgent,
    DocumentGenerationAgent
)
from backend.service.core.states import (
    SearchState,
    SalesState,
    ComplianceState,
    DocumentState
)
from backend.service.core.context import create_context
from backend.service.subgraphs import (
    create_data_collection_graph,
    create_analysis_graph
)
from backend.service.tools.calculation_tool import get_calculation_tool
from backend.service.tools.trend_analysis_tool import get_trend_analysis_tool
from backend.service.tools.cross_db_analysis_tool import get_cross_db_analysis_tool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IntegratedFlowTester:
    """
    통합 플로우 테스터
    전체 시스템의 데이터 흐름을 테스트하고 시각화
    """

    def __init__(self):
        """Initialize all components"""
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}Initializing Integrated Flow Tester...")
        print(f"{Fore.CYAN}{'='*80}\n")

        # Initialize LLM Manager
        print(f"{Fore.YELLOW}[1/6] Initializing LLM Manager...")
        self.llm_manager = get_llm_manager()
        print(f"{Fore.GREEN}[OK] LLM Manager initialized")

        # Initialize Agents
        print(f"{Fore.YELLOW}[2/6] Initializing Agents...")
        self.agents = {
            "search_agent": SearchAgent(),
            "sales_analytics": SalesAnalyticsAgent(),
            "compliance_check": ComplianceCheckAgent(),
            "document_generation": DocumentGenerationAgent()
        }
        print(f"{Fore.GREEN}[OK] 4 Agents initialized")

        # Initialize Subgraphs
        print(f"{Fore.YELLOW}[3/6] Initializing Subgraphs...")
        self.data_collection_graph = create_data_collection_graph()
        self.analysis_graph = create_analysis_graph()
        print(f"{Fore.GREEN}[OK] 2 Subgraphs initialized")

        # Initialize Tools
        print(f"{Fore.YELLOW}[4/6] Initializing Tools...")
        self.calculation_tool = get_calculation_tool()
        self.trend_tool = get_trend_analysis_tool()
        self.cross_db_tool = get_cross_db_analysis_tool()
        print(f"{Fore.GREEN}[OK] 3 Tools initialized")

        # Flow tracking
        print(f"{Fore.YELLOW}[5/6] Setting up flow tracking...")
        self.flow_log = []
        self.execution_times = {}
        print(f"{Fore.GREEN}[OK] Flow tracking ready")

        # Test queries
        print(f"{Fore.YELLOW}[6/6] Loading test queries...")
        self.test_queries = self._load_test_queries()
        print(f"{Fore.GREEN}[OK] {len(self.test_queries)} test queries loaded")

        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.GREEN}[OK] All components initialized successfully!")
        print(f"{Fore.CYAN}{'='*80}\n")

    def _load_test_queries(self) -> List[Dict[str, str]]:
        """Load predefined test queries"""
        return [
            {
                "id": "search_1",
                "query": "김영희 직원 정보 찾기",
                "expected_agent": "search_agent",
                "description": "Simple employee search"
            },
            {
                "id": "sales_1",
                "query": "3월 매출 실적 분석해줘",
                "expected_agent": "sales_analytics",
                "description": "Monthly sales analysis"
            },
            {
                "id": "sales_2",
                "query": "김영희의 실적 통계와 달성률 계산",
                "expected_agent": "sales_analytics",
                "description": "Personal performance with calculations"
            },
            {
                "id": "complex_1",
                "query": "영업팀 전체 실적을 분석하고 보고서 작성해줘",
                "expected_agents": ["sales_analytics", "document_generation"],
                "description": "Complex multi-agent task"
            },
            {
                "id": "trend_1",
                "query": "최근 6개월 매출 트렌드 분석",
                "expected_agent": "sales_analytics",
                "description": "Trend analysis task"
            },
            {
                "id": "compliance_1",
                "query": "영업 정책 위반 사항 확인",
                "expected_agent": "compliance_check",
                "description": "Compliance check task"
            },
            {
                "id": "cross_db_1",
                "query": "모든 영업 직원의 목표 대비 실적 비교 분석",
                "expected_agent": "sales_analytics",
                "description": "Cross-database analysis"
            }
        ]

    def _log_flow(self, step: str, details: Any, duration: float = 0):
        """Log flow step with timing"""
        self.flow_log.append({
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "details": details,
            "duration": duration
        })

    def _print_step_header(self, step_num: int, total: int, title: str):
        """Print formatted step header"""
        print(f"\n{Fore.CYAN}{'─'*60}")
        print(f"{Fore.YELLOW}[Step {step_num}/{total}] {title}")
        print(f"{Fore.CYAN}{'─'*60}")

    def _print_result_box(self, title: str, content: Any):
        """Print formatted result box"""
        print(f"\n{Fore.GREEN}┌{'─' * 58}┐")
        print(f"{Fore.GREEN}│ {title:<56} │")
        print(f"{Fore.GREEN}├{'─' * 58}┤")

        if isinstance(content, dict):
            for key, value in content.items():
                if isinstance(value, list) and len(value) > 3:
                    print(f"{Fore.GREEN}│ {key}: {value[:3]}... ({len(value)} items) │")
                else:
                    line = f"{key}: {value}"
                    if len(line) > 56:
                        line = line[:53] + "..."
                    print(f"{Fore.GREEN}│ {line:<56} │")
        else:
            lines = str(content).split('\n')
            for line in lines[:5]:  # Show first 5 lines
                if len(line) > 56:
                    line = line[:53] + "..."
                print(f"{Fore.GREEN}│ {line:<56} │")

        print(f"{Fore.GREEN}└{'─' * 58}┘")

    async def test_single_query(self, query: str, query_id: str = None) -> Dict[str, Any]:
        """
        Test a single query through the entire flow

        Args:
            query: User query to test
            query_id: Optional ID for the query

        Returns:
            Complete flow result
        """
        print(f"\n{Fore.MAGENTA}{'='*80}")
        print(f"{Fore.MAGENTA}Testing Query: {query}")
        print(f"{Fore.MAGENTA}{'='*80}")

        results = {
            "query": query,
            "query_id": query_id,
            "flow_steps": [],
            "final_result": None,
            "total_time": 0
        }

        total_start = time.time()

        try:
            # Step 1: LLM Intent Analysis
            self._print_step_header(1, 6, "LLM Intent Analysis")
            step_start = time.time()

            intent_result = await self.llm_manager.analyze_intent(query)
            step_time = time.time() - step_start

            self._log_flow("intent_analysis", intent_result, step_time)
            results["flow_steps"].append({
                "step": "intent_analysis",
                "result": intent_result,
                "time": step_time
            })

            print(f"Intent: {Fore.WHITE}{intent_result.get('intent', 'unknown')}")
            print(f"Agents: {Fore.WHITE}{intent_result.get('agents', [])}")
            print(f"Confidence: {Fore.WHITE}{intent_result.get('confidence', 0):.2%}")
            print(f"Entities: {Fore.WHITE}{intent_result.get('entities', {})}")
            print(f"Reasoning: {Fore.WHITE}{intent_result.get('reasoning', 'N/A')}")
            print(f"Time: {Fore.YELLOW}{step_time:.2f}s")

            # Step 2: Agent Routing Decision
            self._print_step_header(2, 6, "Agent Routing Decision")
            step_start = time.time()

            selected_agents = intent_result.get("agents", [])
            if not selected_agents:
                print(f"{Fore.RED}⚠ No agents selected, using fallback")
                selected_agents = ["search_agent"]

            print(f"Selected Agents: {Fore.WHITE}{', '.join(selected_agents)}")

            routing_time = time.time() - step_start
            results["flow_steps"].append({
                "step": "routing",
                "selected_agents": selected_agents,
                "time": routing_time
            })

            # Step 3: Agent Execution (Simulated Main Graph)
            self._print_step_header(3, 6, "Agent Execution")
            agent_results = {}

            for agent_name in selected_agents:
                if agent_name not in self.agents:
                    print(f"{Fore.RED}⚠ Agent {agent_name} not found, skipping")
                    continue

                print(f"\n{Fore.CYAN}Executing {agent_name}...")
                step_start = time.time()

                # Create appropriate state for agent
                agent_state = self._create_agent_state(agent_name, query, intent_result)

                # Simulate agent execution
                try:
                    if agent_name == "search_agent":
                        # Simulate search
                        agent_results[agent_name] = {
                            "status": "success",
                            "results": [
                                {"type": "employee", "name": "김영희", "department": "영업팀"}
                            ],
                            "count": 1
                        }
                    elif agent_name == "sales_analytics":
                        # Simulate sales analysis
                        agent_results[agent_name] = {
                            "status": "success",
                            "metrics": {
                                "total_sales": 15000000,
                                "achievement_rate": 95.5,
                                "growth_rate": 12.3
                            }
                        }
                    elif agent_name == "compliance_check":
                        # Simulate compliance check
                        agent_results[agent_name] = {
                            "status": "success",
                            "violations": [],
                            "compliant": True
                        }
                    elif agent_name == "document_generation":
                        # Simulate document generation
                        agent_results[agent_name] = {
                            "status": "success",
                            "document": "Generated report content...",
                            "format": "markdown"
                        }

                    agent_time = time.time() - step_start
                    print(f"{Fore.GREEN}[OK] {agent_name} completed in {agent_time:.2f}s")

                except Exception as e:
                    agent_results[agent_name] = {
                        "status": "error",
                        "error": str(e)
                    }
                    print(f"{Fore.RED}[ERROR] {agent_name} failed: {e}")

            results["flow_steps"].append({
                "step": "agent_execution",
                "results": agent_results,
                "time": time.time() - step_start
            })

            # Step 4: Subgraph Processing (if needed)
            if "sales_analytics" in selected_agents:
                self._print_step_header(4, 6, "Subgraph Processing")
                step_start = time.time()

                print(f"{Fore.CYAN}Invoking data_collection_subgraph...")

                # Simulate subgraph execution
                collection_state = {
                    "query_params": intent_result.get("entities", {}),
                    "performance_data": [],
                    "target_data": [],
                    "client_data": [],
                    "errors": []
                }

                # Simulate data collection
                collection_result = {
                    "performance_data": [{"month": "202403", "sales": 5000000}],
                    "target_data": [{"month": "202403", "target": 5500000}],
                    "client_data": [{"id": "H001", "name": "서울병원"}],
                    "collection_status": "completed"
                }

                print(f"{Fore.GREEN}[OK] Data collection completed")

                print(f"{Fore.CYAN}Invoking analysis_subgraph...")

                # Simulate analysis
                analysis_result = {
                    "basic_metrics": {
                        "total_performance": 15000000,
                        "average_achievement": 95.5
                    },
                    "trend_analysis": {
                        "trend_direction": "increasing",
                        "trend_strength": 0.75
                    },
                    "insights": [
                        "매출이 상승 추세입니다",
                        "목표 달성률이 우수합니다"
                    ]
                }

                print(f"{Fore.GREEN}[OK] Analysis completed")

                subgraph_time = time.time() - step_start
                results["flow_steps"].append({
                    "step": "subgraph_processing",
                    "collection": collection_result,
                    "analysis": analysis_result,
                    "time": subgraph_time
                })

            # Step 5: Tool Usage
            if any(a in selected_agents for a in ["sales_analytics"]):
                self._print_step_header(5, 6, "Tool Usage")
                step_start = time.time()

                tool_results = {}

                # Calculation tool
                print(f"{Fore.CYAN}Using calculation_tool...")
                achievement = self.calculation_tool.calculate_achievement_rate(15000000, 16000000)
                growth = self.calculation_tool.calculate_growth_rate(15000000, 13000000)
                tool_results["calculations"] = {
                    "achievement_rate": achievement,
                    "growth_rate": growth
                }
                print(f"  Achievement Rate: {achievement}%")
                print(f"  Growth Rate: {growth}%")

                # Trend tool
                print(f"{Fore.CYAN}Using trend_analysis_tool...")
                trend = self.trend_tool.analyze_historical_trend(
                    [12000000, 13000000, 14000000, 15000000]
                )
                tool_results["trend"] = {
                    "direction": trend.get("trend_direction"),
                    "strength": trend.get("trend_strength")
                }
                print(f"  Trend: {trend.get('trend_direction')}")

                tool_time = time.time() - step_start
                results["flow_steps"].append({
                    "step": "tool_usage",
                    "results": tool_results,
                    "time": tool_time
                })

            # Step 6: Generate Final Response
            self._print_step_header(6, 6, "Generate Final Response")
            step_start = time.time()

            # Combine all results
            combined_results = {
                "agents": agent_results,
                "subgraphs": results["flow_steps"][-2] if len(results["flow_steps"]) > 2 else {},
                "tools": results["flow_steps"][-1] if len(results["flow_steps"]) > 1 else {}
            }

            # Generate response using LLM
            final_response = await self.llm_manager.generate_response(
                query,
                combined_results,
                response_type="general"
            )

            response_time = time.time() - step_start
            results["final_result"] = final_response
            results["flow_steps"].append({
                "step": "final_response",
                "response": final_response,
                "time": response_time
            })

            self._print_result_box("Final Response", final_response[:200] + "..." if len(final_response) > 200 else final_response)

        except Exception as e:
            print(f"{Fore.RED}[ERROR] Error during flow execution: {e}")
            results["error"] = str(e)
            import traceback
            traceback.print_exc()

        # Calculate total time
        results["total_time"] = time.time() - total_start

        # Print flow summary
        self._print_flow_summary(results)

        return results

    def _create_agent_state(self, agent_name: str, query: str, intent_result: Dict) -> Dict[str, Any]:
        """Create appropriate state for each agent type"""
        base_state = {
            "query": query,
            "timestamp": datetime.now().isoformat()
        }

        if agent_name == "search_agent":
            return SearchState(
                **base_state,
                search_params=intent_result.get("entities", {}),
                results=[],
                search_status="pending",
                errors=[]
            )
        elif agent_name == "sales_analytics":
            return SalesState(
                **base_state,
                metrics={},
                analysis_type="comprehensive",
                filters=intent_result.get("entities", {}),
                results={},
                errors=[]
            )
        elif agent_name == "compliance_check":
            return ComplianceState(
                **base_state,
                check_type="policy",
                violations=[],
                compliance_status="pending",
                errors=[]
            )
        elif agent_name == "document_generation":
            return DocumentState(
                **base_state,
                document_type="report",
                template="default",
                content="",
                metadata={},
                errors=[]
            )

        return base_state

    def _print_flow_summary(self, results: Dict[str, Any]):
        """Print flow execution summary"""
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}Flow Execution Summary")
        print(f"{Fore.CYAN}{'='*80}")

        print(f"\n{Fore.YELLOW}Query: {Fore.WHITE}{results['query']}")
        print(f"{Fore.YELLOW}Total Time: {Fore.WHITE}{results['total_time']:.2f}s")

        print(f"\n{Fore.YELLOW}Step Breakdown:")
        for step in results["flow_steps"]:
            step_name = step["step"].replace("_", " ").title()
            step_time = step.get("time", 0)
            percentage = (step_time / results["total_time"] * 100) if results["total_time"] > 0 else 0

            # Create a simple bar chart
            bar_length = int(percentage / 2)
            bar = "█" * bar_length + "░" * (50 - bar_length)

            print(f"  {step_name:<25} {step_time:>6.2f}s  [{bar}] {percentage:>5.1f}%")

        if "error" in results:
            print(f"\n{Fore.RED}⚠ Error: {results['error']}")
        else:
            print(f"\n{Fore.GREEN}[OK] Flow completed successfully")

    async def test_all_queries(self):
        """Test all predefined queries"""
        print(f"\n{Fore.MAGENTA}{'='*80}")
        print(f"{Fore.MAGENTA}Running All Test Queries")
        print(f"{Fore.MAGENTA}{'='*80}")

        results = []
        for test_case in self.test_queries:
            print(f"\n{Fore.CYAN}Test Case: {test_case['id']} - {test_case['description']}")
            result = await self.test_single_query(test_case["query"], test_case["id"])
            results.append({
                "test_case": test_case,
                "result": result
            })
            print(f"\n{Fore.CYAN}{'─'*80}")

        # Print overall summary
        self._print_overall_summary(results)

        return results

    def _print_overall_summary(self, results: List[Dict]):
        """Print overall test summary"""
        print(f"\n{Fore.MAGENTA}{'='*80}")
        print(f"{Fore.MAGENTA}Overall Test Summary")
        print(f"{Fore.MAGENTA}{'='*80}")

        total_tests = len(results)
        successful = sum(1 for r in results if "error" not in r["result"])
        failed = total_tests - successful

        print(f"\n{Fore.YELLOW}Total Tests: {Fore.WHITE}{total_tests}")
        print(f"{Fore.GREEN}Successful: {successful}")
        print(f"{Fore.RED}Failed: {failed}")

        # Calculate average times
        total_time = sum(r["result"]["total_time"] for r in results)
        avg_time = total_time / total_tests if total_tests > 0 else 0

        print(f"\n{Fore.YELLOW}Total Execution Time: {Fore.WHITE}{total_time:.2f}s")
        print(f"{Fore.YELLOW}Average Time per Query: {Fore.WHITE}{avg_time:.2f}s")

        # Agent usage statistics
        agent_usage = {}
        for r in results:
            for step in r["result"]["flow_steps"]:
                if step["step"] == "routing":
                    for agent in step.get("selected_agents", []):
                        agent_usage[agent] = agent_usage.get(agent, 0) + 1

        print(f"\n{Fore.YELLOW}Agent Usage:")
        for agent, count in sorted(agent_usage.items(), key=lambda x: x[1], reverse=True):
            print(f"  {agent}: {count} times")

        # Success rate by expected agent
        print(f"\n{Fore.YELLOW}Success Rate by Expected Agent:")
        for test_case_result in results:
            test_case = test_case_result["test_case"]
            result = test_case_result["result"]

            expected = test_case.get("expected_agent") or test_case.get("expected_agents", [])
            if isinstance(expected, str):
                expected = [expected]

            actual = []
            for step in result["flow_steps"]:
                if step["step"] == "routing":
                    actual = step.get("selected_agents", [])
                    break

            match = any(a in actual for a in expected) if expected else True
            status = f"{Fore.GREEN}[OK]" if match else f"{Fore.RED}[FAIL]"
            print(f"  {test_case['id']}: {status} (Expected: {expected}, Got: {actual})")

    def visualize_flow(self, result: Dict[str, Any]):
        """Visualize the flow as ASCII art"""
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}Flow Visualization")
        print(f"{Fore.CYAN}{'='*80}\n")

        # Create flow diagram
        print(f"{Fore.WHITE}┌─────────────┐")
        print(f"{Fore.WHITE}│    Query    │ {result['query'][:40]}...")
        print(f"{Fore.WHITE}└──────┬──────┘")
        print(f"{Fore.WHITE}       │")
        print(f"{Fore.WHITE}       ▼")

        # Intent analysis
        intent_step = next((s for s in result["flow_steps"] if s["step"] == "intent_analysis"), None)
        if intent_step:
            intent = intent_step["result"].get("intent", "unknown")
            print(f"{Fore.YELLOW}┌─────────────┐")
            print(f"{Fore.YELLOW}│ LLM Intent  │ {intent}")
            print(f"{Fore.YELLOW}└──────┬──────┘")
            print(f"{Fore.YELLOW}       │")
            print(f"{Fore.YELLOW}       ▼")

        # Agent routing
        routing_step = next((s for s in result["flow_steps"] if s["step"] == "routing"), None)
        if routing_step:
            agents = routing_step.get("selected_agents", [])
            if len(agents) == 1:
                print(f"{Fore.GREEN}┌─────────────┐")
                print(f"{Fore.GREEN}│   {agents[0]:^9}   │")
                print(f"{Fore.GREEN}└──────┬──────┘")
            else:
                # Multiple agents
                for i, agent in enumerate(agents):
                    if i == 0:
                        print(f"{Fore.GREEN}       ├──→ [{agent}]")
                    elif i == len(agents) - 1:
                        print(f"{Fore.GREEN}       └──→ [{agent}]")
                    else:
                        print(f"{Fore.GREEN}       ├──→ [{agent}]")
            print(f"{Fore.GREEN}       │")
            print(f"{Fore.GREEN}       ▼")

        # Subgraphs
        subgraph_step = next((s for s in result["flow_steps"] if s["step"] == "subgraph_processing"), None)
        if subgraph_step:
            print(f"{Fore.MAGENTA}┌─────────────┐")
            print(f"{Fore.MAGENTA}│  Subgraphs  │")
            print(f"{Fore.MAGENTA}├─────────────┤")
            print(f"{Fore.MAGENTA}│ • Collect   │")
            print(f"{Fore.MAGENTA}│ • Analyze   │")
            print(f"{Fore.MAGENTA}└──────┬──────┘")
            print(f"{Fore.MAGENTA}       │")
            print(f"{Fore.MAGENTA}       ▼")

        # Tools
        tool_step = next((s for s in result["flow_steps"] if s["step"] == "tool_usage"), None)
        if tool_step:
            print(f"{Fore.BLUE}┌─────────────┐")
            print(f"{Fore.BLUE}│    Tools    │")
            print(f"{Fore.BLUE}├─────────────┤")
            print(f"{Fore.BLUE}│ • Calculate │")
            print(f"{Fore.BLUE}│ • Trend     │")
            print(f"{Fore.BLUE}│ • CrossDB   │")
            print(f"{Fore.BLUE}└──────┬──────┘")
            print(f"{Fore.BLUE}       │")
            print(f"{Fore.BLUE}       ▼")

        # Final result
        print(f"{Fore.WHITE}┌─────────────┐")
        print(f"{Fore.WHITE}│   Result    │")
        print(f"{Fore.WHITE}└─────────────┘")

        print(f"\n{Fore.CYAN}Total Time: {result['total_time']:.2f}s")


async def main():
    """Main function with interactive menu"""
    tester = IntegratedFlowTester()

    while True:
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{Fore.CYAN}Integrated Flow Test Menu")
        print(f"{Fore.CYAN}{'='*80}")
        print(f"{Fore.YELLOW}1. Test all predefined queries")
        print(f"{Fore.YELLOW}2. Test single predefined query")
        print(f"{Fore.YELLOW}3. Test custom query (interactive)")
        print(f"{Fore.YELLOW}4. Visualize last flow")
        print(f"{Fore.YELLOW}5. Show flow statistics")
        print(f"{Fore.YELLOW}0. Exit")
        print(f"{Fore.CYAN}{'─'*80}")

        choice = input(f"{Fore.WHITE}Select option (0-5): ").strip()

        if choice == "0":
            print(f"{Fore.GREEN}Exiting...")
            break

        elif choice == "1":
            # Test all queries
            results = await tester.test_all_queries()

        elif choice == "2":
            # Test single predefined query
            print(f"\n{Fore.YELLOW}Available test queries:")
            for i, test_case in enumerate(tester.test_queries, 1):
                print(f"{Fore.WHITE}{i}. [{test_case['id']}] {test_case['query']}")
                print(f"   {Fore.CYAN}{test_case['description']}")

            try:
                idx = int(input(f"\n{Fore.WHITE}Select query number: ")) - 1
                if 0 <= idx < len(tester.test_queries):
                    test_case = tester.test_queries[idx]
                    result = await tester.test_single_query(
                        test_case["query"],
                        test_case["id"]
                    )
                    tester.last_result = result
                else:
                    print(f"{Fore.RED}Invalid selection")
            except ValueError:
                print(f"{Fore.RED}Invalid input")

        elif choice == "3":
            # Test custom query
            print(f"\n{Fore.YELLOW}Enter your query (Korean or English):")
            custom_query = input(f"{Fore.WHITE}Query: ").strip()
            if custom_query:
                result = await tester.test_single_query(custom_query, "custom")
                tester.last_result = result
            else:
                print(f"{Fore.RED}Empty query")

        elif choice == "4":
            # Visualize last flow
            if hasattr(tester, 'last_result'):
                tester.visualize_flow(tester.last_result)
            else:
                print(f"{Fore.RED}No flow to visualize. Run a test first.")

        elif choice == "5":
            # Show statistics
            if tester.flow_log:
                print(f"\n{Fore.CYAN}Flow Statistics")
                print(f"{Fore.CYAN}{'─'*60}")

                # Count by step type
                step_counts = {}
                step_times = {}
                for entry in tester.flow_log:
                    step = entry["step"]
                    step_counts[step] = step_counts.get(step, 0) + 1
                    step_times[step] = step_times.get(step, 0) + entry.get("duration", 0)

                print(f"\n{Fore.YELLOW}Step Execution Counts:")
                for step, count in sorted(step_counts.items()):
                    avg_time = step_times[step] / count if count > 0 else 0
                    print(f"  {step}: {count} times (avg: {avg_time:.2f}s)")

                print(f"\n{Fore.YELLOW}Total Flows Executed: {len(set(e['timestamp'][:10] for e in tester.flow_log))}")
            else:
                print(f"{Fore.RED}No statistics available. Run some tests first.")

        else:
            print(f"{Fore.RED}Invalid choice")

        if choice != "0":
            input(f"\n{Fore.CYAN}Press Enter to continue...")


if __name__ == "__main__":
    print(f"{Fore.CYAN}Starting Integrated Flow Tester...")
    print(f"{Fore.YELLOW}This test shows the complete flow:")
    print(f"{Fore.WHITE}Query → LLM → Agent → Graph → Subgraph → Tool → Result\n")

    asyncio.run(main())