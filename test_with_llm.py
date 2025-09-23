"""
Test agents with LLM integration
LLM을 통한 의도분석과 에이전트 라우팅 테스트
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List
from backend.service.agents import (
    SearchAgent,
    SalesAnalyticsAgent,
    ComplianceCheckAgent,
    DocumentGenerationAgent
)
from backend.service.utils import get_llm_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleOrchestrator:
    """Simple orchestrator with LLM integration for testing"""

    def __init__(self):
        self.llm_manager = get_llm_manager()
        self.agents = {
            "search_agent": SearchAgent(),
            "sales_analytics": SalesAnalyticsAgent(),
            "compliance_check": ComplianceCheckAgent(),
            "document_generation": DocumentGenerationAgent()
        }
        logger.info("SimpleOrchestrator initialized with LLM support")

    async def process_query(self, query: str, user_id: str = "test_user") -> Dict[str, Any]:
        """
        Process user query with LLM intent analysis and agent routing

        Args:
            query: User query in Korean
            user_id: User identifier

        Returns:
            Processing result
        """
        session_id = f"session_{datetime.now().timestamp()}"

        print(f"\n[Processing Query]")
        print(f"Query: {query}")
        print(f"Session: {session_id}")

        # Step 1: Analyze intent with LLM
        print("\n[Step 1: Intent Analysis]")
        intent_result = await self.llm_manager.analyze_intent(query)

        print(f"Intent: {intent_result.get('intent')}")
        print(f"Agents: {intent_result.get('agents')}")
        print(f"Confidence: {intent_result.get('confidence')}")
        print(f"Entities: {intent_result.get('entities')}")
        print(f"Keywords: {intent_result.get('keywords')}")

        # Step 2: Create execution plan with LLM
        print("\n[Step 2: Execution Planning]")
        plan = await self.llm_manager.create_execution_plan(intent_result)

        if "steps" in plan:
            print(f"Plan Steps: {len(plan.get('steps', []))}")
            for step in plan.get("steps", []):
                print(f"  {step['order']}. {step['agent']}: {step['action']}")
        else:
            print("No execution plan generated")

        # Step 3: Execute agents
        print("\n[Step 3: Agent Execution]")
        results = {}

        for step in plan.get("steps", []):
            agent_name = step.get("agent")
            if agent_name in self.agents:
                print(f"\nExecuting {agent_name}...")

                # Prepare input for agent
                agent_input = self._prepare_agent_input(
                    agent_name,
                    query,
                    intent_result,
                    step,
                    user_id,
                    session_id
                )

                # Execute agent
                agent = self.agents[agent_name]
                result = await agent.execute(agent_input)

                if result["status"] == "success":
                    results[agent_name] = result.get("data", {})
                    print(f"{agent_name} execution successful")
                else:
                    print(f"{agent_name} execution failed: {result.get('error')}")
                    results[agent_name] = {"error": result.get("error")}

        # Step 4: Generate response with LLM
        print("\n[Step 4: Response Generation]")
        response = await self.llm_manager.generate_response(query, results)

        return {
            "query": query,
            "intent": intent_result,
            "plan": plan,
            "results": results,
            "response": response
        }

    def _prepare_agent_input(
        self,
        agent_name: str,
        query: str,
        intent_result: Dict,
        step: Dict,
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Prepare input for specific agent"""
        base_input = {
            "user_id": user_id,
            "session_id": session_id,
            "original_query": query,  # Add original query
            "intent_result": intent_result  # Add intent analysis result
        }

        entities = intent_result.get("entities", {})

        if agent_name == "search_agent":
            return {
                **base_input,
                "query": query,
                "search_type": "both"  # or determine from intent
            }

        elif agent_name == "sales_analytics":
            return {
                **base_input,
                "employee_name": entities.get("person", "최시우"),
                "period": entities.get("period", "monthly")
            }

        elif agent_name == "compliance_check":
            return {
                **base_input,
                "check_type": entities.get("type", "general"),
                "check_target": entities.get("target", query)
            }

        elif agent_name == "document_generation":
            # Get data from previous agent results if available
            doc_data = {}
            if "sales_analytics" in self.results:
                sales_data = self.results["sales_analytics"]
                if "final_report" in sales_data:
                    doc_data = sales_data["final_report"]

            return {
                **base_input,
                "doc_type": entities.get("doc_type", "general"),
                "title": f"Report for: {query}",
                "data": doc_data
            }

        return base_input


async def test_llm_intent_analysis():
    """Test LLM intent analysis only"""
    print("\n" + "="*60)
    print("Testing LLM Intent Analysis")
    print("="*60)

    llm_manager = get_llm_manager()

    test_queries = [
        "최시우 실적 분석해줘",
        "김철수 인사정보 찾아줘",
        "연차 사용 규정 확인해줘",
        "3월 실적 보고서 작성해줘",
        "경비 처리 규정 준수 확인",
        "최시우 3월 실적 보고서 만들어줘"
    ]

    for query in test_queries:
        print(f"\n[Query]: {query}")

        # Analyze intent
        intent = await llm_manager.analyze_intent(query)

        print(f"Intent: {intent.get('intent')}")
        print(f"Agents: {intent.get('agents')}")
        print(f"Confidence: {intent.get('confidence', 0):.2f}")

        if intent.get("entities"):
            print(f"Entities: {intent.get('entities')}")

        # Create plan
        plan = await llm_manager.create_execution_plan(intent)
        if "steps" in plan:
            print(f"Steps: {len(plan.get('steps', []))}")


async def test_end_to_end_with_llm():
    """Test end-to-end flow with LLM"""
    print("\n" + "="*60)
    print("Testing End-to-End with LLM Integration")
    print("="*60)

    orchestrator = SimpleOrchestrator()

    test_queries = [
        {
            "query": "최시우 실적 분석해줘",
            "expected_agent": "sales_analytics"
        },
        {
            "query": "김철수 직원 정보 찾아줘",
            "expected_agent": "search_agent"
        },
        {
            "query": "휴가 사용 규정 확인해줘",
            "expected_agent": "compliance_check"
        },
        {
            "query": "최시우 3월 실적 보고서 만들어줘",
            "expected_agent": "document_generation"
        }
    ]

    for test in test_queries:
        print(f"\n{'='*50}")
        print(f"Test Query: {test['query']}")
        print(f"Expected Agent: {test['expected_agent']}")
        print("="*50)

        try:
            result = await orchestrator.process_query(test["query"])

            # Check if expected agent was used
            if test["expected_agent"] in result.get("results", {}):
                print(f"\n[SUCCESS] Expected agent {test['expected_agent']} was used")
            else:
                print(f"\n[WARNING] Expected agent {test['expected_agent']} was not used")

            # Show response
            print(f"\n[Final Response]")
            print(result.get("response", "No response generated"))

        except Exception as e:
            print(f"\n[ERROR] Test failed: {e}")
            logger.error(f"Test failed for query: {test['query']}", exc_info=True)


async def test_complex_workflow():
    """Test complex multi-agent workflow"""
    print("\n" + "="*60)
    print("Testing Complex Multi-Agent Workflow")
    print("="*60)

    orchestrator = SimpleOrchestrator()

    # Complex query requiring multiple agents
    complex_query = "최시우 실적 분석하고 규정 위반 확인 후 보고서 작성해줘"

    print(f"Complex Query: {complex_query}")

    result = await orchestrator.process_query(complex_query)

    # Check how many agents were involved
    agents_used = list(result.get("results", {}).keys())
    print(f"\nAgents Used: {agents_used}")
    print(f"Total Agents: {len(agents_used)}")

    # Show plan steps
    if "plan" in result and "steps" in result["plan"]:
        print("\nExecution Plan:")
        for step in result["plan"]["steps"]:
            print(f"  {step['order']}. {step['agent']}: {step['action']}")

    # Show final response
    print(f"\n[Final Response]")
    print(result.get("response", "No response generated"))


async def main():
    """Run all LLM integration tests"""
    print("\n" + "="*70)
    print(" LLM Integration Testing ".center(70))
    print("="*70)
    print(f"Started at: {datetime.now().isoformat()}")

    try:
        # Test 1: Intent Analysis Only
        print("\n[Test 1/3] Testing Intent Analysis...")
        await test_llm_intent_analysis()
        print("[PASS] Intent Analysis Test")

    except Exception as e:
        print(f"[FAIL] Intent Analysis Test: {e}")

    try:
        # Test 2: End-to-End with Single Agents
        print("\n[Test 2/3] Testing End-to-End Flows...")
        await test_end_to_end_with_llm()
        print("[PASS] End-to-End Test")

    except Exception as e:
        print(f"[FAIL] End-to-End Test: {e}")

    try:
        # Test 3: Complex Multi-Agent Workflow
        print("\n[Test 3/3] Testing Complex Workflow...")
        await test_complex_workflow()
        print("[PASS] Complex Workflow Test")

    except Exception as e:
        print(f"[FAIL] Complex Workflow Test: {e}")

    print("\n" + "="*70)
    print(" Test Complete ".center(70))
    print("="*70)
    print(f"Completed at: {datetime.now().isoformat()}")


if __name__ == "__main__":
    asyncio.run(main())