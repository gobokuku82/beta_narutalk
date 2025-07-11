"""
간단한 채팅 API 엔드포인트
- 복잡한 LangGraph 대신 단순한 라우터 사용
- 빠르고 관리하기 쉬운 구조
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import time
import logging

from ...services.simple_router import simple_router
from ...core.dependencies import get_vector_db_service, get_rdb_service, get_llm_service

logger = logging.getLogger(__name__)

router = APIRouter()

class SimpleChatRequest(BaseModel):
    """간단한 채팅 요청"""
    message: str
    user_id: str
    session_id: str
    conversation_history: Optional[List[Dict[str, str]]] = None
    user_preferences: Optional[Dict[str, Any]] = None

class SimpleChatResponse(BaseModel):
    """간단한 채팅 응답"""
    response: str
    agent_type: str
    confidence: float
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    processing_time_ms: int

@router.post("/simple/chat", response_model=SimpleChatResponse)
async def simple_chat(
    request: SimpleChatRequest,
    vector_db_service = Depends(get_vector_db_service),
    rdb_service = Depends(get_rdb_service), 
    llm_service = Depends(get_llm_service)
):
    """간단한 채팅 처리"""
    start_time = time.time()
    
    try:
        # 라우터에 서비스 설정
        simple_router.set_agent_services(
            vector_db_service=vector_db_service,
            rdb_service=rdb_service,
            llm_service=llm_service
        )
        
        # 메시지 처리
        result = await simple_router.process_message(
            message=request.message,
            user_id=request.user_id,
            session_id=request.session_id,
            conversation_history=request.conversation_history,
            user_preferences=request.user_preferences
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return SimpleChatResponse(
            response=result.response,
            agent_type=result.agent_type,
            confidence=result.confidence,
            sources=result.sources or [],
            metadata=result.metadata or {},
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"채팅 처리 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"채팅 처리 실패: {str(e)}")

@router.get("/simple/info")
async def get_simple_router_info():
    """간단한 라우터 정보"""
    return simple_router.get_router_info()

@router.get("/simple/agents")
async def get_available_agents():
    """사용 가능한 에이전트 목록"""
    return {
        "agents": simple_router.get_available_agents(),
        "total": len(simple_router.get_available_agents())
    } 