"""
Simple Agent Routing Test
4개 에이전트 테스트 및 State 전달 검증
나중에 서브그래프로 전환을 고려한 구조
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import agents and core components
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
from backend.service.core.context import AgentContext, create_context
from backend.service.utils import get_llm_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleAgentRouter:
    """
    Simple router for testing agents with proper state management
    This will later become subgraphs in the orchestrator
    """

    def __init__(self):
        """Initialize router with agents and LLM manager"""
        self.llm_manager = get_llm_manager()

        # Initialize agents
        self.agents = {
            "search_agent": SearchAgent(),
            "sales_analytics": SalesAnalyticsAgent(),
            "compliance_check": ComplianceCheckAgent(),
            "document_generation": DocumentGenerationAgent()
        }

        logger.info("SimpleAgentRouter initialized")

    async def route_query(self, query: str, user_id: str = "test_user", session_id: str = None) -> Dict[str, Any]:
        """
        Route query to appropriate agents with proper state management

        Args:
            query: User query
            user_id: User ID
            session_id: Session ID

        Returns:
            Results from agent execution
        """
        if not session_id:
            session_id = f"session_{datetime.now().timestamp()}"

        logger.info(f"Routing query: {query}")

        # Step 1: Analyze intent using LLM manager
        intent_result = await self.llm_manager.analyze_intent(query)
        logger.info(f"Intent analysis: {intent_result}")

        selected_agents = intent_result.get("agents", [])

        # Check if routing failed
        if not selected_agents:
            logger.error(f"No agents selected for query: {query}")
            error_msg = intent_result.get("error", "Agent routing failed")

            return {
                "query": query,
                "intent": intent_result,
                "agent_results": {},
                "error": error_msg,
                "response": f"요청을 처리할 수 없습니다. ({error_msg})",
                "timestamp": datetime.now().isoformat()
            }

        # Step 2: Execute each selected agent with proper state
        results = {}

        for agent_name in selected_agents:
            if agent_name not in self.agents:
                logger.warning(f"Unknown agent: {agent_name}")
                continue

            try:
                # Create appropriate state and context for each agent
                state = self._create_agent_state(agent_name, query, intent_result)
                context = self._create_agent_context(
                    agent_name, user_id, session_id, query, intent_result
                )

                logger.info(f"Executing {agent_name} with state keys: {list(state.keys())}")

                # Execute agent
                agent = self.agents[agent_name]

                # Prepare input format expected by agent
                agent_input = {
                    **state,  # Include state fields
                    "context": context.__dict__ if hasattr(context, '__dict__') else context,
                    "user_id": user_id,
                    "session_id": session_id,
                    "query": query,  # Add the original query directly
                    "original_query": query  # Also add as original_query for compatibility
                }

                result = await agent.execute(agent_input)
                results[agent_name] = {
                    "status": result.get("status", "unknown"),
                    "data": result.get("data", {}),
                    "state_used": list(state.keys()),
                    "execution_time": result.get("execution_time", 0)
                }

                logger.info(f"{agent_name} completed: {result.get('status')}")

            except Exception as e:
                logger.error(f"Error executing {agent_name}: {e}")
                results[agent_name] = {
                    "status": "error",
                    "error": str(e),
                    "state_used": []
                }

        # Step 3: Generate final response
        final_response = await self._generate_response(query, results, intent_result)

        return {
            "query": query,
            "intent": intent_result,
            "agent_results": results,
            "response": final_response,
            "timestamp": datetime.now().isoformat()
        }

    def _create_agent_state(self, agent_name: str, query: str, intent_result: Dict) -> Dict[str, Any]:
        """
        Create appropriate state for each agent type
        This ensures proper state structure for future subgraph conversion
        """
        entities = intent_result.get("entities", {})

        if agent_name == "search_agent":
            # SearchState
            return {
                "status": "pending",
                "execution_step": "init",
                "query": query,
                "search_type": "both",  # hr_info and hr_rules
                "filters": {},
                "keywords": intent_result.get("keywords", []),
                "hr_results": [],
                "rules_results": [],
                "relevance_scores": {},
                "sources": [],
                "final_results": {}
            }

        elif agent_name == "sales_analytics":
            # SalesState with Text2SQL fields
            return {
                "status": "pending",
                "execution_step": "init",
                "employee_name": entities.get("person", ""),
                "period": entities.get("period", "monthly"),
                "metrics_type": "performance",
                # Text2SQL specific fields
                "parsed_query": {},
                "generated_sql": "",
                "sql_result": [],
                "formatted_result": "",
                # Legacy fields (kept for compatibility)
                "raw_data": [],
                "aggregated_data": {},
                "statistics": {},
                "charts_data": [],
                "insights": [],
                "final_report": {}
            }

        elif agent_name == "compliance_check":
            # ComplianceState
            return {
                "status": "pending",
                "execution_step": "init",
                "check_type": entities.get("check_type", "policy"),
                "target_action": query,
                "action_context": {"query": query, "entities": entities},
                "rules_checked": [],
                "violations": [],
                "recommendations": [],
                "compliance_score": 0.0,
                "is_compliant": False,
                "compliance_report": {}
            }

        elif agent_name == "document_generation":
            # DocumentState
            return {
                "status": "pending",
                "execution_step": "init",
                "document_type": entities.get("doc_type", "report"),
                "template_name": "",
                "input_content": {"query": query, "entities": entities},
                "formatting_rules": {},
                "sections": [],
                "generated_content": "",
                "document_format": "text",
                "final_document": {}
            }

        else:
            # Default state
            return {
                "status": "pending",
                "execution_step": "init",
                "query": query
            }

    def _create_agent_context(
        self,
        agent_name: str,
        user_id: str,
        session_id: str,
        query: str,
        intent_result: Dict
    ) -> AgentContext:
        """
        Create context for agent execution
        Separated from state as per Context API pattern
        """
        return create_context(
            user_id=user_id,
            session_id=session_id,
            context_type="agent",
            agent_name=agent_name,
            original_query=query,
            intent_result=intent_result,
            timeout=30,
            max_retries=3
        )

    async def _generate_response(
        self,
        query: str,
        results: Dict[str, Any],
        intent_result: Dict
    ) -> str:
        """Generate final response from agent results"""
        try:
            # Use LLM manager to generate response
            response = await self.llm_manager.generate_response(query, results)
            return response
        except Exception as e:
            logger.error(f"Error generating response: {e}")

            # Fallback response
            successful_agents = [
                name for name, result in results.items()
                if result.get("status") == "success"
            ]

            if successful_agents:
                return f"처리 완료. 실행된 에이전트: {', '.join(successful_agents)}"
            else:
                return "요청을 처리하는 중 오류가 발생했습니다."


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

async def test_single_agent():
    """Test single agent routing and state management"""
    print("\n" + "="*70)
    print(" Test 1: Single Agent (Search) ")
    print("="*70)

    router = SimpleAgentRouter()

    query = "김철수 직원의 정보를 찾아줘"
    result = await router.route_query(query, user_id="test_001")

    print(f"\n📝 Query: {query}")
    print(f"🎯 Intent: {result['intent'].get('intent', 'unknown')}")
    print(f"🤖 Selected Agents: {result['intent'].get('agents', [])}")

    for agent_name, agent_result in result['agent_results'].items():
        print(f"\n[{agent_name}]")
        print(f"  Status: {agent_result['status']}")
        print(f"  State fields used: {', '.join(agent_result['state_used'])}")

    print(f"\n💬 Response: {result['response']}")


async def test_sales_agent():
    """Test sales agent with Text2SQL state"""
    print("\n" + "="*70)
    print(" Test 2: Sales Analytics Agent ")
    print("="*70)

    router = SimpleAgentRouter()

    query = "최시우의 3월 실적 분석해줘"
    result = await router.route_query(query, user_id="test_002")

    print(f"\n📝 Query: {query}")
    print(f"🎯 Intent: {result['intent'].get('intent', 'unknown')}")
    print(f"🤖 Selected Agents: {result['intent'].get('agents', [])}")

    # Check if SalesState fields were properly used
    if "sales_analytics" in result['agent_results']:
        sales_result = result['agent_results']['sales_analytics']
        print(f"\n[Sales Analytics State Check]")
        print(f"  Status: {sales_result['status']}")
        print(f"  State fields: {sales_result.get('state_used', [])}")

        # Verify Text2SQL fields are present
        expected_fields = ['parsed_query', 'generated_sql', 'sql_result', 'formatted_result']
        present_fields = [f for f in expected_fields if f in sales_result.get('state_used', [])]
        print(f"  Text2SQL fields present: {present_fields}")

    print(f"\n💬 Response: {result['response']}")


async def test_multi_agent():
    """Test multiple agents with state propagation"""
    print("\n" + "="*70)
    print(" Test 3: Multi-Agent Routing ")
    print("="*70)

    router = SimpleAgentRouter()

    query = "3월 실적을 분석하고 규정 위반 사항을 확인한 후 보고서를 작성해줘"
    result = await router.route_query(query, user_id="test_003")

    print(f"\n📝 Query: {query}")
    print(f"🎯 Intent: {result['intent'].get('intent', 'unknown')}")
    print(f"🤖 Selected Agents: {result['intent'].get('agents', [])}")

    print("\n[Agent Execution Results]")
    for agent_name, agent_result in result['agent_results'].items():
        print(f"\n  {agent_name}:")
        print(f"    Status: {agent_result['status']}")
        print(f"    State fields: {len(agent_result.get('state_used', []))} fields")
        if agent_result['status'] == 'error':
            print(f"    Error: {agent_result.get('error', 'Unknown error')}")

    print(f"\n💬 Response: {result['response']}")


async def test_state_integrity():
    """Test that state is properly maintained for each agent"""
    print("\n" + "="*70)
    print(" Test 4: State Integrity Check ")
    print("="*70)

    router = SimpleAgentRouter()

    # Test each agent type
    test_queries = {
        "search_agent": "휴가 규정을 찾아줘",
        "sales_analytics": "이번달 매출 통계 보여줘",
        "compliance_check": "경비 처리가 규정에 맞는지 확인해줘",
        "document_generation": "월간 실적 보고서 템플릿 만들어줘"
    }

    for expected_agent, query in test_queries.items():
        print(f"\n[Testing {expected_agent}]")
        print(f"Query: {query}")

        result = await router.route_query(query, user_id=f"test_{expected_agent}")

        # Verify the correct agent was selected
        selected = result['intent'].get('agents', [])
        if expected_agent in selected:
            print(f"✅ Correct agent selected")

            # Check state structure
            if expected_agent in result['agent_results']:
                agent_result = result['agent_results'][expected_agent]
                state_fields = agent_result.get('state_used', [])

                # Define expected fields for each agent
                expected_fields = {
                    "search_agent": ["query", "search_type", "keywords"],
                    "sales_analytics": ["parsed_query", "generated_sql", "employee_name"],
                    "compliance_check": ["check_type", "target_action", "rules_checked"],
                    "document_generation": ["document_type", "template_name", "sections"]
                }

                agent_expected = expected_fields.get(expected_agent, [])
                present = [f for f in agent_expected if f in state_fields]

                print(f"  Expected fields present: {len(present)}/{len(agent_expected)}")
                if len(present) < len(agent_expected):
                    missing = [f for f in agent_expected if f not in state_fields]
                    print(f"  ⚠️ Missing fields: {missing}")
        else:
            print(f"❌ Agent not selected. Got: {selected}")


async def interactive_test():
    """Interactive testing mode"""
    print("\n" + "="*70)
    print(" Interactive Agent Routing Test ")
    print("="*70)
    print("종료하려면 'exit' 입력\n")

    router = SimpleAgentRouter()

    while True:
        query = input("\n💬 질문: ").strip()

        if query.lower() in ['exit', 'quit', '종료']:
            break

        if not query:
            continue

        try:
            result = await router.route_query(query)

            print(f"\n🎯 Intent: {result['intent'].get('intent', 'unknown')}")
            print(f"🤖 Agents: {', '.join(result['intent'].get('agents', []))}")

            # Show agent results
            for agent_name, agent_result in result['agent_results'].items():
                status_icon = "✅" if agent_result['status'] == 'success' else "❌"
                print(f"  {status_icon} {agent_name}: {agent_result['status']}")

            print(f"\n💬 응답: {result['response']}")

        except Exception as e:
            print(f"❌ Error: {e}")


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Main test runner"""
    while True:
        print("\n" + "="*70)
        print(" Agent Routing Test (Simple) ")
        print("="*70)
        print("\n테스트 옵션:")
        print("1. Single Agent Test (Search)")
        print("2. Sales Analytics Test (Text2SQL)")
        print("3. Multi-Agent Test")
        print("4. State Integrity Check")
        print("5. Interactive Test")
        print("0. Exit")

        choice = input("\n선택 (0-5): ").strip()

        if choice == "1":
            await test_single_agent()
        elif choice == "2":
            await test_sales_agent()
        elif choice == "3":
            await test_multi_agent()
        elif choice == "4":
            await test_state_integrity()
        elif choice == "5":
            await interactive_test()
        elif choice == "0":
            print("테스트 종료")
            break
        else:
            print("잘못된 선택")


if __name__ == "__main__":
    asyncio.run(main())