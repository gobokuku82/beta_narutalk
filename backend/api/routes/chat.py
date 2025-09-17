"""
Chat API Routes
대화 처리 관련 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from datetime import datetime
import logging
import uuid

from backend.api.models.chat import (
    ChatRequest,
    ChatResponse,
    FeedbackRequest,
    FeedbackResponse
)
from backend.api.core.dependencies import get_supervisor_service
from backend.api.services.supervisor_service import SupervisorService

logger = logging.getLogger(__name__)

# Router 생성
router = APIRouter(tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    supervisor: SupervisorService = Depends(get_supervisor_service)
):
    """
    대화 요청 처리

    사용자의 자연어 질의를 받아 Supervisor를 통해 처리하고 결과를 반환합니다.
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
                response_time=result["response_time"],
                agents_used=result.get("result", {}).get("agents_used")
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


@router.get("/stream")
async def chat_stream(
    query: str = Query(..., description="사용자 질의"),
    user_id: str = Query(..., description="사용자 ID"),
    session_id: Optional[str] = Query(None, description="세션 ID"),
    supervisor: SupervisorService = Depends(get_supervisor_service)
):
    """
    스트리밍 대화 응답

    Server-Sent Events (SSE)를 사용하여 실시간으로 응답을 스트리밍합니다.
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


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: FeedbackRequest
):
    """
    사용자 피드백 제출

    대화에 대한 사용자 피드백을 수집합니다.
    """
    try:
        # TODO: 피드백 저장 로직 구현 (데이터베이스 저장)
        feedback_id = str(uuid.uuid4())

        logger.info(
            f"Feedback received - Session: {feedback.session_id}, "
            f"Rating: {feedback.rating}, Category: {feedback.category}"
        )

        return FeedbackResponse(
            message="Feedback submitted successfully",
            feedback_id=feedback_id,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Feedback error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))