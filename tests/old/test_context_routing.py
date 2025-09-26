"""
LangGraph 0.6.x Context API를 활용한 에이전트 라우팅 테스트
State, Config, Context가 정확하게 전달되는지 검증
"""

import asyncio
import logging
import sys
import os
from typing import TypedDict, Annotated, Dict, Any, List
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime
from langgraph.graph.message import add_messages, AnyMessage, HumanMessage, AIMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from operator import add

# Import our components
from backend.service.utils import get_llm_manager
from backend.service.agents import (
    SearchAgent,
    SalesAnalyticsAgent,
    ComplianceCheckAgent,
    DocumentGenerationAgent
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# SCHEMA DEFINITIONS (LangGraph 0.6.x Pattern)
# ============================================================================

class AgentState(TypedDict):
    """Main state that flows through the graph"""
    messages: Annotated[List[AnyMessage], add_messages]  # Auto-merge messages
    current_query: str
    intent_analysis: Dict[str, Any]
    selected_agents: List[str]
    agent_results: Dict[str, Any]  # Results from each agent
    execution_steps: Annotated[List[Dict], add]  # Track execution history
    final_response: str
    error_log: Annotated[List[str], add]  # Accumulate errors


class AppContext(TypedDict):
    """Runtime context - doesn't change during execution"""
    user_id: str
    session_id: str
    user_name: str
    department: str
    permissions: List[str]
    api_keys: Dict[str, str]
    feature_flags: Dict[str, bool]
    max_retries: int
    timeout_seconds: int


class UserInput(TypedDict):
    """Simple input schema for users"""
    query: str


class BotOutput(TypedDict):
    """Output schema - what users see"""
    response: str
    agents_used: List[str]
    execution_time: float
    confidence: float


# ============================================================================
# NODE IMPLEMENTATIONS (Context API Pattern)
# ============================================================================

async def analyze_intent_node(
    state: AgentState,
    runtime: Runtime[AppContext]
) -> Dict[str, Any]:
    """
    Analyze user intent using LLM and determine which agents to use
    Context API Pattern: runtime.context for accessing configuration
    """
    logger.info(f"[Intent Analysis] User: {runtime.context['user_id']}")

    # Get LLM manager
    llm_manager = get_llm_manager()

    # Analyze intent
    query = state.get("current_query") or state["messages"][-1].content
    intent_result = await llm_manager.analyze_intent(query)

    # Log for debugging
    execution_step = {
        "node": "analyze_intent",
        "timestamp": datetime.now().isoformat(),
        "user": runtime.context["user_id"],
        "input": query,
        "output": intent_result,
        "context_used": {
            "permissions": runtime.context["permissions"],
            "department": runtime.context["department"]
        }
    }

    # Return partial state update (not full state!)
    return {
        "current_query": query,
        "intent_analysis": intent_result,
        "selected_agents": intent_result.get("agents", ["search_agent"]),
        "execution_steps": [execution_step]
    }


async def route_to_agents_node(
    state: AgentState,
    runtime: Runtime[AppContext]
) -> Dict[str, Any]:
    """
    Route query to appropriate agents based on intent analysis
    Demonstrates parallel agent execution with context passing
    """
    logger.info(f"[Routing] Agents: {state['selected_agents']}")

    # Initialize agents
    agents = {
        "search_agent": SearchAgent(),
        "sales_analytics": SalesAnalyticsAgent(),
        "compliance_check": ComplianceCheckAgent(),
        "document_generation": DocumentGenerationAgent()
    }

    # Check permissions
    allowed_agents = []
    for agent_name in state["selected_agents"]:
        # Permission check using context
        if agent_name == "compliance_check" and "compliance_access" not in runtime.context["permissions"]:
            logger.warning(f"User {runtime.context['user_id']} lacks permission for {agent_name}")
            continue
        if agent_name == "sales_analytics" and "sales_data_access" not in runtime.context["permissions"]:
            logger.warning(f"User {runtime.context['user_id']} lacks permission for {agent_name}")
            continue
        allowed_agents.append(agent_name)

    if not allowed_agents:
        return {
            "error_log": ["권한이 없는 에이전트 접근 시도"],
            "agent_results": {"error": "접근 권한이 없습니다"}
        }

    # Execute agents with proper context
    agent_results = {}
    execution_steps = []

    for agent_name in allowed_agents:
        if agent_name not in agents:
            logger.error(f"Unknown agent: {agent_name}")
            continue

        agent = agents[agent_name]

        # Prepare agent input with context
        agent_input = {
            "query": state["current_query"],
            "user_id": runtime.context["user_id"],
            "session_id": runtime.context["session_id"],
            "intent": state["intent_analysis"],
            "context": {
                "department": runtime.context["department"],
                "user_name": runtime.context["user_name"],
                "feature_flags": runtime.context["feature_flags"]
            },
            "messages": [msg.content if hasattr(msg, 'content') else str(msg)
                        for msg in state["messages"]]
        }

        try:
            # Execute agent
            result = await agent.execute(agent_input)
            agent_results[agent_name] = result

            execution_steps.append({
                "node": f"agent_{agent_name}",
                "timestamp": datetime.now().isoformat(),
                "status": result.get("status", "unknown"),
                "summary": result.get("summary", "")
            })

            logger.info(f"[Agent] {agent_name} completed: {result.get('status')}")

        except Exception as e:
            logger.error(f"Agent {agent_name} failed: {e}")
            agent_results[agent_name] = {"error": str(e), "status": "error"}
            execution_steps.append({
                "node": f"agent_{agent_name}",
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            })

    return {
        "agent_results": agent_results,
        "execution_steps": execution_steps
    }


async def generate_response_node(
    state: AgentState,
    runtime: Runtime[AppContext]
) -> Dict[str, Any]:
    """
    Generate final response from agent results
    Uses context for personalization
    """
    logger.info(f"[Response Generation] for {runtime.context['user_name']}")

    llm_manager = get_llm_manager()

    # Check if we have valid results
    if not state.get("agent_results") or all(
        r.get("status") == "error" for r in state["agent_results"].values()
    ):
        return {
            "final_response": "죄송합니다. 요청을 처리하는 중 오류가 발생했습니다.",
            "messages": [AIMessage(content="처리 중 오류가 발생했습니다.")]
        }

    # Generate personalized response
    try:
        # Add user context for personalization
        query_with_context = f"""
사용자: {runtime.context['user_name']} ({runtime.context['department']})
질문: {state['current_query']}

에이전트 실행 결과:
{json.dumps(state['agent_results'], ensure_ascii=False, indent=2)}
"""

        response = await llm_manager.generate_response(
            query_with_context,
            state["agent_results"]
        )

        # Add personalization if feature flag is on
        if runtime.context["feature_flags"].get("personalized_response"):
            response = f"{runtime.context['user_name']}님, {response}"

        return {
            "final_response": response,
            "messages": [AIMessage(content=response)],
            "execution_steps": [{
                "node": "generate_response",
                "timestamp": datetime.now().isoformat(),
                "personalized": runtime.context["feature_flags"].get("personalized_response", False)
            }]
        }

    except Exception as e:
        logger.error(f"Response generation failed: {e}")
        return {
            "final_response": "응답 생성 중 오류가 발생했습니다.",
            "error_log": [f"Response generation error: {str(e)}"]
        }


# ============================================================================
# GRAPH CONSTRUCTION (LangGraph 0.6.x Pattern)
# ============================================================================

def create_agent_graph():
    """
    Create the agent routing graph with Context API
    """
    # Initialize graph with all schemas
    workflow = StateGraph(
        state_schema=AgentState,
        input_schema=UserInput,
        output_schema=BotOutput,
        context_schema=AppContext  # Critical for 0.6.x!
    )

    # Add nodes
    workflow.add_node("analyze_intent", analyze_intent_node)
    workflow.add_node("route_agents", route_to_agents_node)
    workflow.add_node("generate_response", generate_response_node)

    # Define edges
    workflow.add_edge(START, "analyze_intent")
    workflow.add_edge("analyze_intent", "route_agents")
    workflow.add_edge("route_agents", "generate_response")
    workflow.add_edge("generate_response", END)

    return workflow


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

async def test_single_agent_routing():
    """Test routing to a single agent with context"""
    print("\n" + "="*70)
    print(" TEST 1: Single Agent Routing ")
    print("="*70)

    # Create graph
    workflow = create_agent_graph()

    # Compile with checkpointer
    async with AsyncSqliteSaver.from_conn_string(":memory:") as checkpointer:
        app = workflow.compile(checkpointer=checkpointer)

        # Define context
        context = {
            "user_id": "test_user_001",
            "session_id": "session_" + str(datetime.now().timestamp()),
            "user_name": "김철수",
            "department": "영업1팀",
            "permissions": ["search_access", "sales_data_access", "compliance_access"],
            "api_keys": {
                "openai": os.getenv("OPENAI_API_KEY", "")
            },
            "feature_flags": {
                "personalized_response": True,
                "detailed_logging": True
            },
            "max_retries": 3,
            "timeout_seconds": 30
        }

        # Get user input
        print("\n예시: 최시우 직원의 정보를 찾아줘")
        test_query = input("쿼리 입력 (Enter로 예시 사용): ").strip()
        if not test_query:
            test_query = "최시우 직원의 정보를 찾아줘"

        # Invoke with context
        config = {"configurable": {"thread_id": "test_thread_001"}}

        result = await app.ainvoke(
            {"query": test_query},
            config=config,
            context=context  # Pass context!
        )

        print(f"\n📝 Query: {test_query}")
        print(f"👤 User: {context['user_name']} ({context['department']})")
        print(f"🤖 Agents Used: {result.get('agents_used', [])}")
        print(f"💬 Response: {result.get('response', 'No response')}")
        print(f"⏱️ Execution Time: {result.get('execution_time', 0):.2f}s")


async def test_multi_agent_routing():
    """Test routing to multiple agents with different permissions"""
    print("\n" + "="*70)
    print(" TEST 2: Multi-Agent Routing ")
    print("="*70)

    workflow = create_agent_graph()

    async with AsyncSqliteSaver.from_conn_string(":memory:") as checkpointer:
        app = workflow.compile(checkpointer=checkpointer)

        # Context with limited permissions
        context = {
            "user_id": "test_user_002",
            "session_id": "session_" + str(datetime.now().timestamp()),
            "user_name": "이영희",
            "department": "인사팀",
            "permissions": ["search_access"],  # Limited permissions
            "api_keys": {
                "openai": os.getenv("OPENAI_API_KEY", "")
            },
            "feature_flags": {
                "personalized_response": False,
                "detailed_logging": True
            },
            "max_retries": 3,
            "timeout_seconds": 30
        }

        # Get user input
        print("\n예시: 3월 매출 분석하고 규정 위반 사항 확인해줘")
        test_query = input("쿼리 입력 (Enter로 예시 사용): ").strip()
        if not test_query:
            test_query = "3월 매출 분석하고 규정 위반 사항 확인해줘"

        config = {"configurable": {"thread_id": "test_thread_002"}}

        result = await app.ainvoke(
            {"query": test_query},
            config=config,
            context=context
        )

        print(f"\n📝 Query: {test_query}")
        print(f"👤 User: {context['user_name']} (Permissions: {context['permissions']})")
        print(f"🤖 Response: {result.get('response', 'No response')}")
        print("⚠️ Note: Should show permission denied for sales/compliance")


async def test_context_propagation():
    """Test that context properly propagates through all nodes"""
    print("\n" + "="*70)
    print(" TEST 3: Context Propagation ")
    print("="*70)

    workflow = create_agent_graph()

    async with AsyncSqliteSaver.from_conn_string(":memory:") as checkpointer:
        app = workflow.compile(checkpointer=checkpointer)

        # Rich context
        context = {
            "user_id": "admin_user",
            "session_id": "admin_session",
            "user_name": "관리자",
            "department": "시스템관리팀",
            "permissions": ["search_access", "sales_data_access", "compliance_access", "admin"],
            "api_keys": {
                "openai": os.getenv("OPENAI_API_KEY", "")
            },
            "feature_flags": {
                "personalized_response": True,
                "detailed_logging": True,
                "admin_mode": True
            },
            "max_retries": 5,
            "timeout_seconds": 60
        }

        # Get user input
        print("\n예시: 2024년 3월 실적 보고서 작성해줘")
        test_query = input("쿼리 입력 (Enter로 예시 사용): ").strip()
        if not test_query:
            test_query = "2024년 3월 실적 보고서 작성해줘"

        config = {"configurable": {"thread_id": "admin_thread"}}

        # Stream to see intermediate steps
        print("\n🔄 Streaming execution steps:")
        async for chunk in app.astream(
            {"query": test_query},
            config=config,
            context=context,
            stream_mode="updates"
        ):
            for node, data in chunk.items():
                if "execution_steps" in data:
                    for step in data["execution_steps"]:
                        print(f"  ✓ {step.get('node', 'unknown')}: {step.get('status', 'processing')}")


async def interactive_test():
    """Interactive test with custom context"""
    print("\n" + "="*70)
    print(" Interactive Context Routing Test ")
    print("="*70)
    print("종료하려면 'exit' 입력\n")

    workflow = create_agent_graph()

    async with AsyncSqliteSaver.from_conn_string(":memory:") as checkpointer:
        app = workflow.compile(checkpointer=checkpointer)

        # Setup user context
        print("사용자 설정:")
        user_name = input("이름 (기본: 테스트): ").strip() or "테스트"
        department = input("부서 (기본: 영업팀): ").strip() or "영업팀"

        # Permission selection
        print("\n권한 설정 (쉼표로 구분하여 입력):")
        print("  1. search_access (HR/인사 검색)")
        print("  2. sales_data_access (매출 데이터 접근)")
        print("  3. compliance_access (규정 확인)")
        print("  4. admin (관리자)")
        permission_input = input("권한 번호 (기본: 1,2): ").strip() or "1,2"

        permission_map = {
            "1": "search_access",
            "2": "sales_data_access",
            "3": "compliance_access",
            "4": "admin"
        }

        permissions = []
        for p in permission_input.split(","):
            p = p.strip()
            if p in permission_map:
                permissions.append(permission_map[p])

        if not permissions:
            permissions = ["search_access", "sales_data_access"]

        # Feature flags
        print("\n기능 플래그 설정:")
        personalized = input("개인화된 응답 사용? (y/n, 기본: y): ").strip().lower() != 'n'
        detailed_log = input("상세 로깅 사용? (y/n, 기본: n): ").strip().lower() == 'y'

        context = {
            "user_id": f"user_{user_name}",
            "session_id": f"session_{datetime.now().timestamp()}",
            "user_name": user_name,
            "department": department,
            "permissions": permissions,
            "api_keys": {
                "openai": os.getenv("OPENAI_API_KEY", "")
            },
            "feature_flags": {
                "personalized_response": True,
                "detailed_logging": False
            },
            "max_retries": 3,
            "timeout_seconds": 30
        }

        thread_id = f"interactive_{datetime.now().timestamp()}"
        config = {"configurable": {"thread_id": thread_id}}

        print(f"\n✅ Context 설정 완료: {user_name}님 ({department})")
        print("-" * 40)

        while True:
            query = input("\n💬 질문: ").strip()

            if query.lower() in ['exit', 'quit', '종료']:
                break

            if not query:
                continue

            try:
                start_time = datetime.now()

                result = await app.ainvoke(
                    {"query": query},
                    config=config,
                    context=context
                )

                execution_time = (datetime.now() - start_time).total_seconds()

                print(f"\n🤖 응답: {result.get('response', 'No response')}")
                print(f"⏱️ 처리 시간: {execution_time:.2f}초")
                print(f"📊 사용된 에이전트: {', '.join(result.get('agents_used', []))}")

            except Exception as e:
                print(f"❌ 오류: {e}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

async def main():
    """Main test runner"""
    while True:
        print("\n" + "="*70)
        print(" LangGraph Context API Routing Test ")
        print("="*70)
        print("\n테스트 옵션:")
        print("1. Single Agent Routing Test")
        print("2. Multi-Agent with Permissions Test")
        print("3. Context Propagation Test")
        print("4. Interactive Test")
        print("0. 종료")

        choice = input("\n선택 (0-4): ").strip()

        if choice == "1":
            await test_single_agent_routing()
        elif choice == "2":
            await test_multi_agent_routing()
        elif choice == "3":
            await test_context_propagation()
        elif choice == "4":
            await interactive_test()
        elif choice == "0":
            print("테스트 종료")
            break
        else:
            print("잘못된 선택")


if __name__ == "__main__":
    asyncio.run(main())