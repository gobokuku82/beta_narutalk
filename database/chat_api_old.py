"""
Chat API Endpoints
사용자와 Supervisor 간의 대화를 처리하는 FastAPI 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging
import json

from supervisor_service import get_supervisor_service, SupervisorService

logger = logging.getLogger(__name__)

# Router 생성
router = APIRouter(prefix="/api/v1", tags=["Chat API"])


# ===== Request/Response Models =====

class ChatRequest(BaseModel):
    """대화 요청 모델"""
    query: str = Field(..., description="사용자 질의")
    user_id: str = Field(..., description="사용자 ID")
    session_id: Optional[str] = Field(None, description="세션 ID")
    context: Dict[str, Any] = Field(default_factory=dict, description="추가 컨텍스트")
    use_cache: bool = Field(True, description="캐시 사용 여부")


class ChatResponse(BaseModel):
    """대화 응답 모델"""
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    session_id: str
    cached: bool = False
    response_time: float
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class SessionInfo(BaseModel):
    """세션 정보 모델"""
    session_id: str
    user_id: Optional[str]
    last_activity: str
    history_count: int


class ServiceStats(BaseModel):
    """서비스 통계 모델"""
    service_stats: Dict[str, Any]
    cache_stats: Dict[str, Any]
    active_sessions: int
    checkpoint_path: str


class FeedbackRequest(BaseModel):
    """피드백 요청 모델"""
    session_id: str
    message_id: Optional[str] = None
    rating: int = Field(..., ge=1, le=5, description="1-5 평점")
    feedback: Optional[str] = None


# ===== Chat Endpoints =====

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    supervisor: SupervisorService = Depends(get_supervisor_service)
):
    """
    대화 요청 처리

    사용자의 자연어 질의를 받아 Supervisor를 통해 처리하고 결과를 반환합니다.

    Request Body:
    - query: 사용자 질의
    - user_id: 사용자 ID
    - session_id: 세션 ID (선택)
    - context: 추가 컨텍스트 정보
    - use_cache: 캐시 사용 여부

    Returns:
    - ChatResponse: 처리 결과
    """
    try:
        # 사용자 컨텍스트 구성
        user_context = {
            "user_id": request.user_id,
            "session_id": request.session_id or f"session_{request.user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            **request.context
        }

        logger.info(f"Processing chat request for user {request.user_id}: {request.query[:100]}...")

        # Supervisor 실행
        result = await supervisor.process_chat(
            query=request.query,
            user_context=user_context,
            use_cache=request.use_cache
        )

        # 응답 생성
        if result["status"] == "success":
            return ChatResponse(
                status="success",
                result=result.get("result"),
                session_id=result["session_id"],
                cached=result.get("cached", False),
                response_time=result["response_time"]
            )
        else:
            return ChatResponse(
                status="error",
                error=result.get("error", "Processing failed"),
                session_id=result["session_id"],
                cached=False,
                response_time=result["response_time"]
            )

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/stream")
async def chat_stream(
    query: str = Query(..., description="사용자 질의"),
    user_id: str = Query(..., description="사용자 ID"),
    session_id: Optional[str] = Query(None, description="세션 ID"),
    supervisor: SupervisorService = Depends(get_supervisor_service)
):
    """
    스트리밍 대화 응답

    Server-Sent Events (SSE)를 사용하여 실시간으로 응답을 스트리밍합니다.

    Query Parameters:
    - query: 사용자 질의
    - user_id: 사용자 ID
    - session_id: 세션 ID (선택)

    Returns:
    - StreamingResponse: SSE 스트림
    """
    try:
        # 사용자 컨텍스트 구성
        user_context = {
            "user_id": user_id,
            "session_id": session_id or f"session_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }

        logger.info(f"Starting stream for user {user_id}: {query[:100]}...")

        # 스트리밍 응답 생성
        return StreamingResponse(
            supervisor.stream_response(query, user_context),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except Exception as e:
        logger.error(f"Stream endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ===== Session Management Endpoints =====

@router.get("/sessions", response_model=List[SessionInfo])
async def list_sessions(
    user_id: Optional[str] = Query(None, description="특정 사용자의 세션만 필터링"),
    supervisor: SupervisorService = Depends(get_supervisor_service)
):
    """
    활성 세션 목록 조회

    현재 활성화된 모든 세션의 목록을 반환합니다.

    Query Parameters:
    - user_id: 특정 사용자의 세션만 필터링 (선택)

    Returns:
    - List[SessionInfo]: 세션 목록
    """
    try:
        sessions = supervisor.list_active_sessions()

        # 사용자 ID로 필터링
        if user_id:
            sessions = [s for s in sessions if s.get("user_id") == user_id]

        return [
            SessionInfo(
                session_id=s["session_id"],
                user_id=s.get("user_id"),
                last_activity=s["last_activity"],
                history_count=s["history_count"]
            )
            for s in sessions
        ]

    except Exception as e:
        logger.error(f"List sessions error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session(
    session_id: str,
    supervisor: SupervisorService = Depends(get_supervisor_service)
):
    """
    특정 세션 정보 조회

    Path Parameters:
    - session_id: 세션 ID

    Returns:
    - SessionInfo: 세션 정보
    """
    try:
        session = supervisor.get_session_info(session_id)

        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        return SessionInfo(
            session_id=session["session_id"],
            user_id=session["user_context"].get("user_id"),
            last_activity=session["last_activity"],
            history_count=session["history_count"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get session error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/history")
async def get_session_history(
    session_id: str,
    limit: int = Query(20, ge=1, le=100, description="히스토리 항목 수"),
    supervisor: SupervisorService = Depends(get_supervisor_service)
):
    """
    세션 대화 히스토리 조회

    Path Parameters:
    - session_id: 세션 ID

    Query Parameters:
    - limit: 반환할 히스토리 항목 수 (기본 20, 최대 100)

    Returns:
    - 대화 히스토리
    """
    try:
        session = supervisor.get_session_info(session_id)

        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        # 히스토리 가져오기
        history = supervisor._get_conversation_history(session_id)

        # 제한 적용
        if len(history) > limit:
            history = history[-limit:]

        return {
            "session_id": session_id,
            "history": history,
            "total_count": len(history)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get history error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ===== Statistics & Management Endpoints =====

@router.get("/stats", response_model=ServiceStats)
async def get_statistics(
    supervisor: SupervisorService = Depends(get_supervisor_service)
):
    """
    서비스 통계 조회

    Returns:
    - ServiceStats: 서비스 및 캐시 통계
    """
    try:
        stats = supervisor.get_statistics()
        return ServiceStats(**stats)

    except Exception as e:
        logger.error(f"Get stats error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_cache(
    supervisor: SupervisorService = Depends(get_supervisor_service)
):
    """
    캐시 전체 초기화

    Returns:
    - 성공 메시지
    """
    try:
        await supervisor.clear_cache()
        return {"message": "Cache cleared successfully"}

    except Exception as e:
        logger.error(f"Clear cache error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/invalidate")
async def invalidate_cache(
    pattern: str = Query(..., description="캐시 키 패턴 (SQL LIKE 형식)"),
    supervisor: SupervisorService = Depends(get_supervisor_service)
):
    """
    패턴별 캐시 무효화

    Query Parameters:
    - pattern: 캐시 키 패턴 (예: 'chat:%')

    Returns:
    - 무효화된 항목 수
    """
    try:
        count = await supervisor.invalidate_cache(pattern)
        return {
            "message": f"Invalidated {count} cache entries",
            "pattern": pattern,
            "count": count
        }

    except Exception as e:
        logger.error(f"Invalidate cache error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ===== Feedback Endpoint =====

@router.post("/feedback")
async def submit_feedback(
    feedback: FeedbackRequest
):
    """
    사용자 피드백 제출

    Request Body:
    - session_id: 세션 ID
    - message_id: 메시지 ID (선택)
    - rating: 1-5 평점
    - feedback: 피드백 텍스트 (선택)

    Returns:
    - 피드백 제출 결과
    """
    try:
        # TODO: 피드백 저장 로직 구현
        # 현재는 로깅만 수행
        logger.info(f"Feedback received - Session: {feedback.session_id}, Rating: {feedback.rating}")

        return {
            "message": "Feedback submitted successfully",
            "session_id": feedback.session_id,
            "rating": feedback.rating,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Feedback error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ===== Health Check =====

@router.get("/chat/health")
async def health_check(
    supervisor: SupervisorService = Depends(get_supervisor_service)
):
    """
    Chat API 상태 확인

    Returns:
    - 서비스 상태 정보
    """
    try:
        stats = supervisor.get_statistics()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "active_sessions": stats["active_sessions"],
            "cache_enabled": supervisor.enable_cache,
            "total_requests": stats["service_stats"]["total_requests"]
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }