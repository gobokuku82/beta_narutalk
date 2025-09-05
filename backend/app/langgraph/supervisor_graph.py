"""
Supervisor Agent - Subgraph Integration
LangGraph 0.6.6 기반 중앙 관리 에이전트 (Subgraph 통합 버전)
"""

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from loguru import logger

from app.langgraph.state import AgentState, initialize_state
from app.langgraph.agents.info_retrieval_graph import create_info_retrieval_subgraph
from app.langgraph.agents.doc_generation_graph import create_doc_generation_subgraph
from app.langgraph.agents.compliance_graph import create_compliance_subgraph
from app.langgraph.agents.analytics_graph import create_analytics_subgraph
from app.core.config import settings


class SupervisorAgent:
    """Supervisor 에이전트 - Subgraph 오케스트레이션"""
    
    def __init__(self):
        # LLM 초기화 (Claude 또는 GPT-4)
        if settings.ANTHROPIC_API_KEY:
            self.llm = ChatAnthropic(
                model="claude-3-opus-20240229",
                anthropic_api_key=settings.ANTHROPIC_API_KEY
            )
        else:
            self.llm = ChatOpenAI(
                model=settings.OPENAI_MODEL,  # gpt-4o
                openai_api_key=settings.OPENAI_API_KEY
            )
        
        # 각 전문 에이전트 Subgraph 초기화
        logger.info("Subgraph 에이전트 초기화 시작")
        self.agents = {
            "info_retrieval": create_info_retrieval_subgraph(),
            "doc_generation": create_doc_generation_subgraph(),
            "compliance": create_compliance_subgraph(),
            "analytics": create_analytics_subgraph()
        }
        logger.info(f"✅ {len(self.agents)}개 Subgraph 에이전트 초기화 완료")
        
        # Command 매핑 (빠른 라우팅용)
        self.command_map = {
            "search": "info_retrieval",
            "retrieve": "info_retrieval",
            "find": "info_retrieval",
            "조회": "info_retrieval",
            "검색": "info_retrieval",
            "찾": "info_retrieval",
            
            "create": "doc_generation",
            "generate": "doc_generation",
            "write": "doc_generation",
            "작성": "doc_generation",
            "생성": "doc_generation",
            "만들": "doc_generation",
            
            "check": "compliance",
            "verify": "compliance",
            "validate": "compliance",
            "검사": "compliance",
            "확인": "compliance",
            "규정": "compliance",
            "컴플라이언스": "compliance",
            
            "analyze": "analytics",
            "report": "analytics",
            "statistics": "analytics",
            "분석": "analytics",
            "통계": "analytics",
            "데이터": "analytics",
            "실적": "analytics"
        }
    
    async def route(self, state: AgentState) -> str:
        """사용자 의도를 분석하여 적절한 Subgraph 선택"""
        
        # 최신 메시지 확인
        if not state.get("messages"):
            return "END"
        
        last_message = state["messages"][-1]
        user_input = last_message.get("content", "")
        
        # 빠른 키워드 매칭
        user_input_lower = user_input.lower()
        for keyword, agent in self.command_map.items():
            if keyword in user_input_lower:
                logger.info(f"키워드 매칭: '{keyword}' -> {agent}")
                return agent
        
        # LLM 기반 의도 분석
        prompt = f"""
        사용자 요청: {user_input}
        
        다음 중 어떤 작업에 해당하는지 선택하세요:
        1. info_retrieval: 의약품 정보, 학술자료, 제품 정보 검색
        2. doc_generation: 문서 작성, 제안서 생성, 보고서 작성, 이메일 작성
        3. compliance: 규정 확인, 리스크 검사, 컴플라이언스 체크
        4. analytics: 데이터 분석, 실적 조회, 통계 생성
        5. END: 작업 완료 또는 인사말
        
        하나만 선택하여 답하세요 (예: info_retrieval):
        """
        
        try:
            response = await self.llm.ainvoke(prompt)
            decision = response.content.strip().lower()
            
            # 라우팅 결정
            if "info_retrieval" in decision:
                return "info_retrieval"
            elif "doc_generation" in decision:
                return "doc_generation"
            elif "compliance" in decision:
                return "compliance"
            elif "analytics" in decision:
                return "analytics"
            else:
                # 기본 처리: 일반적인 대화
                return "END"
        except Exception as e:
            logger.error(f"라우팅 결정 오류: {e}")
            return "END"
    
    async def process(self, state: AgentState) -> Dict[str, Any]:
        """Supervisor 노드 실행"""
        logger.info(f"Supervisor 처리 중: 세션 {state.get('session_id')}")
        
        # 반복 횟수 체크
        if state.get("iteration_count", 0) >= settings.MAX_ITERATIONS:
            logger.warning(f"최대 반복 횟수 초과: {settings.MAX_ITERATIONS}")
            return {
                "messages": [{"role": "assistant", "content": "최대 처리 횟수를 초과했습니다. 요청을 다시 시도해주세요."}],
                "should_end": True
            }
        
        # 라우팅 결정
        next_agent = await self.route(state)
        
        if next_agent == "END":
            # 일반적인 대화 처리
            last_message = state["messages"][-1]
            user_input = last_message.get("content", "")
            
            # 인사말 처리
            if any(greeting in user_input.lower() for greeting in ["안녕", "hello", "hi"]):
                response = "안녕하세요! 제약회사 영업사원 AI 어시스턴트입니다. 무엇을 도와드릴까요?"
            else:
                response = "죄송합니다. 요청하신 내용을 이해하지 못했습니다. 다시 한 번 설명해주시겠어요?"
            
            return {
                "messages": [{"role": "assistant", "content": response}],
                "should_end": True
            }
        
        logger.info(f"선택된 에이전트: {next_agent}")
        
        return {
            "next_agent": next_agent,
            "iteration_count": state.get("iteration_count", 0) + 1
        }


def create_supervisor_graph():
    """Supervisor 기반 워크플로우 그래프 생성 (Subgraph 통합)"""
    
    # StateGraph 초기화
    workflow = StateGraph(AgentState)
    
    # Supervisor 인스턴스
    supervisor = SupervisorAgent()
    
    # 노드 추가
    # Supervisor 노드
    workflow.add_node("supervisor", supervisor.process)
    
    # 각 Subgraph를 노드로 추가
    # 각 Subgraph는 이미 컴파일된 그래프
    workflow.add_node("info_retrieval", supervisor.agents["info_retrieval"].process)
    workflow.add_node("doc_generation", supervisor.agents["doc_generation"].process)
    workflow.add_node("compliance", supervisor.agents["compliance"].process)
    workflow.add_node("analytics", supervisor.agents["analytics"].process)
    
    # 엣지 추가
    # 시작은 항상 Supervisor
    workflow.add_edge(START, "supervisor")
    
    # 조건부 엣지 - Supervisor의 라우팅 결정에 따라
    def route_decision(state: AgentState) -> str:
        """라우팅 결정 함수"""
        # should_end 플래그 확인
        if state.get("should_end", False):
            return "end"
        
        # next_agent 확인
        next_agent = state.get("next_agent")
        if next_agent and next_agent != "END":
            return next_agent
        
        return "end"
    
    workflow.add_conditional_edges(
        "supervisor",
        route_decision,
        {
            "info_retrieval": "info_retrieval",
            "doc_generation": "doc_generation",
            "compliance": "compliance",
            "analytics": "analytics",
            "end": END
        }
    )
    
    # 각 Subgraph에서 다시 Supervisor로
    # Subgraph는 처리 후 next_agent를 None으로 설정하므로 Supervisor로 돌아감
    for agent in ["info_retrieval", "doc_generation", "compliance", "analytics"]:
        workflow.add_edge(agent, "supervisor")
    
    # 그래프 컴파일
    app = workflow.compile()
    
    logger.info("✅ Supervisor 그래프 (Subgraph 통합) 생성 완료")
    logger.info(f"  - 통합된 Subgraph 수: {len(supervisor.agents)}")
    logger.info(f"  - 노드 구성: supervisor + {list(supervisor.agents.keys())}")
    
    return app


# 그래프 실행 헬퍼 함수
async def run_supervisor(user_input: str, session_id: str, user_id: str = None):
    """Supervisor 그래프 실행 (Subgraph 버전)"""
    
    logger.info(f"Supervisor 실행 시작 - 세션: {session_id}")
    
    # 그래프 생성
    app = create_supervisor_graph()
    
    # 초기 State 생성
    initial_state = initialize_state(session_id, user_id)
    initial_state["messages"] = [{"role": "user", "content": user_input}]
    
    # 그래프 실행
    try:
        logger.info("그래프 실행 중...")
        result = await app.ainvoke(initial_state)
        logger.info("그래프 실행 완료")
        
        # 결과 처리
        if result.get("messages"):
            # 마지막 assistant 메시지 찾기
            assistant_messages = [msg for msg in result["messages"] if msg.get("role") == "assistant"]
            if assistant_messages:
                final_message = assistant_messages[-1].get("content", "처리가 완료되었습니다.")
            else:
                final_message = "요청을 처리했습니다."
        else:
            final_message = "처리가 완료되었습니다."
        
        return {
            "success": True,
            "message": final_message,
            "session_id": session_id,
            "agent_outputs": result.get("agent_outputs", {}),
            "iteration_count": result.get("iteration_count", 0)
        }
        
    except Exception as e:
        logger.error(f"Supervisor 실행 오류: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": f"처리 중 오류가 발생했습니다: {str(e)}",
            "session_id": session_id
        }


# 테스트 함수
async def test_supervisor():
    """Supervisor와 Subgraph 통합 테스트"""
    import asyncio
    
    test_cases = [
        "아스피린에 대한 정보를 알려주세요",
        "영업 제안서를 작성해주세요",
        "GMP 규정을 확인해주세요",
        "이번 달 매출 데이터를 분석해주세요"
    ]
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n[테스트 {i}] {test_input}")
        result = await run_supervisor(test_input, f"test_session_{i}")
        print(f"결과: {result['message'][:200]}...")
        print(f"성공 여부: {result['success']}")
        if result.get('agent_outputs'):
            print(f"사용된 에이전트: {list(result['agent_outputs'].keys())}")
        print("-" * 50)


if __name__ == "__main__":
    # 테스트 실행
    import asyncio
    asyncio.run(test_supervisor())