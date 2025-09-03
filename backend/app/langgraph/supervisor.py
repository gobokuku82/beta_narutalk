"""
Supervisor Agent - LangGraph 0.6.6
모든 에이전트를 조정하는 중앙 관리자
"""

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from loguru import logger

from app.langgraph.state import AgentState, initialize_state
from app.langgraph.agents.doc_generation import DocGenerationAgent
from app.langgraph.agents.compliance import ComplianceAgent
from app.langgraph.agents.analytics import AnalyticsAgent
from app.core.config import settings

# HuggingFace 사용 여부에 따라 다른 Agent 임포트
if settings.USE_HUGGINGFACE:
    from app.langgraph.agents.info_retrieval_hf import InfoRetrievalAgentHF as InfoRetrievalAgent
else:
    from app.langgraph.agents.info_retrieval import InfoRetrievalAgent


class SupervisorAgent:
    """Supervisor 에이전트 - Command Pattern으로 라우팅"""
    
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
        
        # 각 전문 에이전트 초기화
        self.agents = {
            "info_retrieval": InfoRetrievalAgent(),
            "doc_generation": DocGenerationAgent(),
            "compliance": ComplianceAgent(),
            "analytics": AnalyticsAgent()
        }
        
        # Command 매핑
        self.command_map = {
            "search": "info_retrieval",
            "retrieve": "info_retrieval",
            "find": "info_retrieval",
            "조회": "info_retrieval",
            "검색": "info_retrieval",
            
            "create": "doc_generation",
            "generate": "doc_generation",
            "write": "doc_generation",
            "작성": "doc_generation",
            "생성": "doc_generation",
            
            "check": "compliance",
            "verify": "compliance",
            "validate": "compliance",
            "검사": "compliance",
            "확인": "compliance",
            
            "analyze": "analytics",
            "report": "analytics",
            "statistics": "analytics",
            "분석": "analytics",
            "통계": "analytics"
        }
    
    async def route(self, state: AgentState) -> str:
        """사용자 의도를 분석하여 적절한 에이전트 선택"""
        
        # 최신 메시지 확인
        if not state.get("messages"):
            return "END"
        
        last_message = state["messages"][-1]
        user_input = last_message.get("content", "")
        
        # 의도 분석 프롬프트
        prompt = f"""
        사용자 요청: {user_input}
        
        다음 중 어떤 작업에 해당하는지 선택하세요:
        1. info_retrieval: 의약품 정보, 학술자료, 제품 정보 검색
        2. doc_generation: 문서 작성, 제안서 생성, 보고서 작성
        3. compliance: 규정 확인, 리스크 검사, 컴플라이언스 체크
        4. analytics: 데이터 분석, 실적 조회, 통계 생성
        5. END: 작업 완료 또는 인사
        
        하나만 선택하여 답하세요:
        """
        
        # LLM으로 라우팅 결정
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
            return "END"
    
    async def process(self, state: AgentState) -> Dict[str, Any]:
        """Supervisor 노드 실행"""
        logger.info(f"Supervisor 처리 중: 세션 {state.get('session_id')}")
        
        # 반복 횟수 체크
        if state.get("iteration_count", 0) >= settings.MAX_ITERATIONS:
            return {
                "messages": [{"role": "assistant", "content": "최대 처리 횟수를 초과했습니다."}],
                "should_end": True
            }
        
        # 라우팅 결정
        next_agent = await self.route(state)
        
        if next_agent == "END":
            return {"should_end": True}
        
        return {
            "next_agent": next_agent,
            "iteration_count": state.get("iteration_count", 0) + 1
        }


def create_supervisor_graph():
    """Supervisor 기반 워크플로우 그래프 생성"""
    
    # StateGraph 초기화 (0.6.6 문법)
    workflow = StateGraph(AgentState)
    
    # Supervisor 인스턴스
    supervisor = SupervisorAgent()
    
    # 노드 추가
    workflow.add_node("supervisor", supervisor.process)
    workflow.add_node("info_retrieval", supervisor.agents["info_retrieval"].process)
    workflow.add_node("doc_generation", supervisor.agents["doc_generation"].process)
    workflow.add_node("compliance", supervisor.agents["compliance"].process)
    workflow.add_node("analytics", supervisor.agents["analytics"].process)
    
    # 엣지 추가
    workflow.add_edge(START, "supervisor")
    
    # 조건부 엣지 - Supervisor의 라우팅 결정에 따라
    def route_decision(state: AgentState) -> str:
        """라우팅 결정 함수"""
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
    
    # 각 에이전트에서 다시 Supervisor로
    for agent in ["info_retrieval", "doc_generation", "compliance", "analytics"]:
        workflow.add_edge(agent, "supervisor")
    
    # 그래프 컴파일 (0.6.6 문법)
    app = workflow.compile()
    
    logger.info("✅ Supervisor 그래프 생성 완료")
    return app


# 그래프 실행 헬퍼 함수
async def run_supervisor(user_input: str, session_id: str, user_id: str = None):
    """Supervisor 그래프 실행"""
    
    # 그래프 생성
    app = create_supervisor_graph()
    
    # 초기 State 생성
    initial_state = initialize_state(session_id, user_id)
    initial_state["messages"] = [{"role": "user", "content": user_input}]
    
    # 그래프 실행
    try:
        result = await app.ainvoke(initial_state)
        return result
    except Exception as e:
        logger.error(f"Supervisor 실행 오류: {e}")
        return {
            "error": str(e),
            "messages": [{"role": "assistant", "content": f"처리 중 오류가 발생했습니다: {str(e)}"}]
        }