"""
LangGraph 라우터 채팅 API 엔드포인트

LangGraph 기반 라우터 시스템을 사용하는 채팅 API입니다.
기존 커스텀 라우터를 완전히 대체하는 새로운 시스템입니다.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import logging

from ...services.langgraph_router import LangGraphRouter
from ...core.dependencies import get_current_user, get_database_service, get_openai_service, get_embedding_service

logger = logging.getLogger(__name__)

router = APIRouter()

# 전역 LangGraph 라우터
langgraph_router = None

class LangGraphChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_preferences: Optional[Dict[str, Any]] = None
    conversation_history: Optional[List[Dict[str, str]]] = None

class LangGraphChatResponse(BaseModel):
    response: str
    agent_type: str
    confidence: float
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    workflow_visualization: Optional[str] = None

@router.on_event("startup")
async def initialize_langgraph_system():
    """LangGraph 라우터 시스템 초기화"""
    global langgraph_router
    try:
        langgraph_router = LangGraphRouter()
        
        # 서비스 의존성 설정 (실제 환경에서는 의존성 주입 사용)
        services = {
            # 'database_service': get_database_service(),
            # 'openai_service': get_openai_service(), 
            # 'embedding_service': get_embedding_service()
        }
        
        langgraph_router.set_agent_services(**services)
        logger.info("LangGraph 라우터 시스템 초기화 완료")
        
    except Exception as e:
        logger.error(f"LangGraph 라우터 시스템 초기화 실패: {str(e)}")
        raise

@router.post("/langgraph/chat", response_model=LangGraphChatResponse)
async def chat_with_langgraph_router(
    request: LangGraphChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    LangGraph 라우터와 채팅
    
    질문을 LangGraph 워크플로우를 통해 분석하여 적절한 전문 에이전트로 라우팅합니다:
    - 문서검색 에이전트: 내부/외부 문서 검색
    - 업무문서 초안작성 에이전트: 문서 자동 생성  
    - 실적분석 에이전트: 성과 데이터 분석
    - 거래처분석 에이전트: 고객/파트너 분석
    
    LangGraph의 장점:
    - TypedDict 기반 강력한 상태 관리
    - 조건부 엣지로 복잡한 라우팅 가능
    - 시각적 워크플로우 표현
    - 확장성과 유지보수성 확보
    """
    try:
        if not langgraph_router:
            raise HTTPException(status_code=500, detail="LangGraph 라우터 시스템이 초기화되지 않았습니다.")
        
        user_id = current_user.get("id", "anonymous")
        session_id = request.session_id or f"langgraph_session_{user_id}"
        
        # LangGraph 워크플로우 실행
        result = await langgraph_router.process_message(
            message=request.message,
            user_id=user_id,
            session_id=session_id,
            conversation_history=request.conversation_history,
            user_preferences=request.user_preferences
        )
        
        # 응답 반환
        return LangGraphChatResponse(
            response=result["response"],
            agent_type=result["agent_type"],
            confidence=result["confidence"],
            sources=result["sources"],
            metadata=result["metadata"],
            workflow_visualization=langgraph_router.get_workflow_visualization()
        )
        
    except Exception as e:
        logger.error(f"LangGraph 채팅 처리 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"채팅 처리 실패: {str(e)}")

@router.get("/langgraph/status")
async def get_langgraph_status():
    """LangGraph 라우터 시스템 상태 확인"""
    try:
        if not langgraph_router:
            return {"status": "not_initialized", "error": "라우터가 초기화되지 않았습니다."}
        
        stats = langgraph_router.get_router_statistics()
        return {
            "status": "healthy",
            "router_type": "LangGraph",
            "statistics": stats,
            "workflow_info": langgraph_router.get_workflow_visualization()
        }
        
    except Exception as e:
        logger.error(f"LangGraph 상태 확인 실패: {str(e)}")
        return {"status": "error", "error": str(e)}

@router.get("/langgraph/workflow")
async def get_workflow_structure():
    """LangGraph 워크플로우 구조 정보"""
    try:
        if not langgraph_router:
            raise HTTPException(status_code=500, detail="라우터가 초기화되지 않았습니다.")
        
        return {
            "workflow_structure": langgraph_router.get_workflow_visualization(),
            "statistics": langgraph_router.get_router_statistics(),
            "description": "LangGraph 기반 4개 전문 에이전트 라우터 시스템"
        }
        
    except Exception as e:
        logger.error(f"워크플로우 구조 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/langgraph/test")
async def test_langgraph_router(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """LangGraph 라우터 테스트"""
    try:
        if not langgraph_router:
            raise HTTPException(status_code=500, detail="라우터가 초기화되지 않았습니다.")
        
        # 각 에이전트별 테스트 메시지
        test_messages = [
            "문서를 찾아주세요",           # document_search
            "보고서를 작성해주세요",        # document_draft  
            "매출 실적을 분석해주세요",     # performance_analysis
            "거래처 정보를 분석해주세요"    # client_analysis
        ]
        
        results = []
        user_id = current_user.get("id", "test_user")
        
        for i, message in enumerate(test_messages):
            result = await langgraph_router.process_message(
                message=message,
                user_id=user_id,
                session_id=f"test_session_{i}"
            )
            results.append({
                "test_message": message,
                "selected_agent": result["agent_type"],
                "confidence": result["confidence"],
                "workflow_history": result["metadata"].get("workflow_history", [])
            })
        
        return {
            "test_status": "completed",
            "test_results": results,
            "router_statistics": langgraph_router.get_router_statistics()
        }
        
    except Exception as e:
        logger.error(f"LangGraph 라우터 테스트 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 