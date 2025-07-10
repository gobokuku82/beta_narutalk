"""
채팅 API 엔드포인트

기존의 라우터 시스템과 새로운 4개 전문 에이전트 시스템을 모두 지원합니다.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging

from ...services.agent_router_manager import AgentRouterManager
from ...core.dependencies import get_current_user, get_database_service, get_openai_service, get_embedding_service

logger = logging.getLogger(__name__)

router = APIRouter()

# 전역 에이전트 라우터 매니저
agent_router = None

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
    next_agent: Optional[str] = None
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
async def chat_with_agents(
    request: ChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
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
            agent_id=result["agent_id"],
            agent_name=result["agent_name"],
            confidence=result["confidence"],
            response=result["response"],
            action=result["action"],
            metadata=result["metadata"],
            sources=result["sources"],
            next_agent=result.get("next_agent")
        )
        
    except Exception as e:
        logger.error(f"채팅 처리 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"채팅 처리 중 오류가 발생했습니다: {str(e)}")

@router.get("/agents/capabilities")
async def get_agent_capabilities():
    """각 에이전트의 기능 소개"""
    try:
        if not agent_router:
            raise HTTPException(status_code=500, detail="에이전트 시스템이 초기화되지 않았습니다.")
        
        return agent_router.get_agent_capabilities()
        
    except Exception as e:
        logger.error(f"에이전트 기능 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/statistics")
async def get_routing_statistics():
    """라우팅 통계 정보"""
    try:
        if not agent_router:
            raise HTTPException(status_code=500, detail="에이전트 시스템이 초기화되지 않았습니다.")
        
        return agent_router.get_routing_statistics()
        
    except Exception as e:
        logger.error(f"통계 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/health")
async def check_agent_health():
    """에이전트 시스템 상태 확인"""
    try:
        if not agent_router:
            raise HTTPException(status_code=500, detail="에이전트 시스템이 초기화되지 않았습니다.")
        
        return await agent_router.health_check()
        
    except Exception as e:
        logger.error(f"상태 확인 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/overview")
async def get_system_overview():
    """시스템 전체 개요"""
    try:
        if not agent_router:
            raise HTTPException(status_code=500, detail="에이전트 시스템이 초기화되지 않았습니다.")
        
        return await agent_router.get_system_overview()
        
    except Exception as e:
        logger.error(f"시스템 개요 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents/suggestions")
async def get_usage_suggestions():
    """사용법 제안사항"""
    try:
        if not agent_router:
            raise HTTPException(status_code=500, detail="에이전트 시스템이 초기화되지 않았습니다.")
        
        suggestions = await agent_router.get_general_suggestions()
        
        return {
            "suggestions": suggestions,
            "examples": {
                "document_search": [
                    "좋은제약 복리후생 정책 찾아줘",
                    "회사 규정 문서 검색해줘",
                    "내부 매뉴얼 찾아줘"
                ],
                "document_draft": [
                    "월간 실적 보고서 작성해줘", 
                    "사업 제안서 초안 만들어줘",
                    "회의록 템플릿 보여줘"
                ],
                "performance_analysis": [
                    "올해 매출 분석해줘",
                    "수익률 트렌드 분석해줘",
                    "KPI 달성도 분석해줘"
                ],
                "client_analysis": [
                    "고객 세분화 분석해줘",
                    "거래처 성과 평가해줘",
                    "위험도 분석해줘"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"제안사항 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 