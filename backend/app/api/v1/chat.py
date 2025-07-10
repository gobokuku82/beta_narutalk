"""
채팅 API 엔드포인트

기존의 라우터 시스템과 새로운 4개 전문 에이전트 시스템을 모두 지원합니다.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging

from ...services.agent_router_manager import AgentRouterManager

logger = logging.getLogger(__name__)

router = APIRouter()

# 전역 에이전트 라우터 매니저
agent_router = None

# 더미 의존성 함수들 (임시)
def get_current_user():
    return {"id": "default_user", "name": "Test User"}

def get_database_service():
    return None

def get_openai_service():
    return None

def get_embedding_service():
    return None

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_preferences: Optional[Dict[str, Any]] = None
    conversation_history: Optional[List[Dict[str, str]]] = None

class ChatResponse(BaseModel):
    agent_id: str
    agent_name: str
    confidence: float
    response: str
    action: str
    metadata: Dict[str, Any]
    sources: List[Dict[str, Any]]
    error: Optional[str] = None
    suggestions: Optional[List[str]] = None

@router.on_event("startup")
async def initialize_agent_system():
    """4개 전문 에이전트 시스템 초기화"""
    global agent_router
    try:
        agent_router = AgentRouterManager()
        
        # 서비스 의존성 - 실제 환경에서는 의존성 주입 사용
        services = {
            # 'database_service': get_database_service(),
            # 'openai_service': get_openai_service(), 
            # 'embedding_service': get_embedding_service()
        }
        
        agent_router.initialize_agents(**services)
        logger.info("4개 전문 에이전트 시스템 초기화 완료")
        
    except Exception as e:
        logger.error(f"에이전트 시스템 초기화 실패: {str(e)}")
        raise

@router.post("/chat", response_model=ChatResponse)
async def chat_with_agents(request: ChatRequest):
    """
    4개 전문 에이전트와 채팅
    
    질문을 분석하여 적절한 전문 에이전트로 라우팅합니다:
    - 문서검색 에이전트: 내부/외부 문서 검색
    - 업무문서 초안작성 에이전트: 문서 자동 생성  
    - 실적분석 에이전트: 성과 데이터 분석
    - 거래처분석 에이전트: 고객/파트너 분석
    """
    try:
        if not agent_router:
            raise HTTPException(status_code=500, detail="에이전트 시스템이 초기화되지 않았습니다.")
        
        current_user = get_current_user()
        user_id = current_user.get("id", "anonymous")
        session_id = request.session_id or f"session_{user_id}"
        
        # 메시지 라우팅 및 처리
        result = await agent_router.route_message(
            message=request.message,
            user_id=user_id,
            session_id=session_id,
            conversation_history=request.conversation_history,
            user_preferences=request.user_preferences
        )
        
        # 응답 변환
        if "error" in result:
            return ChatResponse(
                agent_id="system",
                agent_name="시스템",
                confidence=0.0,
                response="",
                action="error",
                metadata={},
                sources=[],
                error=result["error"],
                suggestions=result.get("suggestions", [])
            )
        
        return ChatResponse(
            agent_id=result.get("agent_id", "unknown"),
            agent_name=result.get("agent_name", "알 수 없음"),
            confidence=result.get("confidence", 0.0),
            response=result.get("response", "응답을 생성할 수 없습니다."),
            action=result.get("action", "complete"),
            metadata=result.get("metadata", {}),
            sources=result.get("sources", [])
        )
        
    except Exception as e:
        logger.error(f"채팅 처리 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"채팅 처리 실패: {str(e)}")

@router.get("/health")
async def health_check():
    """에이전트 시스템 상태 확인"""
    try:
        if not agent_router:
            return {"status": "not_initialized", "error": "에이전트 라우터가 초기화되지 않았습니다."}
        
        health_status = await agent_router.health_check()
        return health_status
        
    except Exception as e:
        logger.error(f"헬스 체크 실패: {str(e)}")
        return {"status": "error", "error": str(e)}

@router.get("/agents")
async def get_available_agents():
    """사용 가능한 에이전트 목록"""
    try:
        if not agent_router:
            return {"agents": [], "error": "에이전트 라우터가 초기화되지 않았습니다."}
        
        agents_info = []
        for agent_id, agent in agent_router.agents.items():
            agents_info.append(agent.get_agent_info())
        
        return {"agents": agents_info}
        
    except Exception as e:
        logger.error(f"에이전트 목록 조회 실패: {str(e)}")
        return {"agents": [], "error": str(e)} 