"""
Session Management Routes
세션 관리 관련 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import logging

from backend.api.models.session import (
    SessionInfo,
    SessionHistory,
    SessionListResponse,
    ServiceStatistics
)
from backend.api.core.dependencies import get_supervisor_service
from backend.api.services.supervisor_service import SupervisorService

logger = logging.getLogger(__name__)

# Router 생성
router = APIRouter(tags=["Sessions"])


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    user_id: Optional[str] = Query(None, description="특정 사용자의 세션만 필터링"),
    supervisor: SupervisorService = Depends(get_supervisor_service)
):
    """
    활성 세션 목록 조회

    현재 활성화된 모든 세션의 목록을 반환합니다.
    """
    try:
        sessions = supervisor.list_active_sessions()

        # 사용자 ID로 필터링
        if user_id:
            sessions = [s for s in sessions if s.get("user_id") == user_id]

        # SessionInfo 모델로 변환
        session_infos = []
        for s in sessions:
            session_infos.append(
                SessionInfo(
                    session_id=s["session_id"],
                    user_id=s.get("user_id", "unknown"),
                    created_at=s.get("created_at", s["last_activity"]),
                    last_activity=s["last_activity"],
                    history_count=s["history_count"],
                    is_active=True
                )
            )

        # 통계 계산
        active_count = len(session_infos)

        return SessionListResponse(
            sessions=session_infos,
            total_count=len(session_infos),
            active_count=active_count,
            filtered_by=f"user_id={user_id}" if user_id else None
        )

    except Exception as e:
        logger.error(f"List sessions error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}", response_model=SessionInfo)
async def get_session(
    session_id: str,
    supervisor: SupervisorService = Depends(get_supervisor_service)
):
    """
    특정 세션 정보 조회

    세션 ID로 특정 세션의 상세 정보를 조회합니다.
    """
    try:
        session = supervisor.get_session_info(session_id)

        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        return SessionInfo(
            session_id=session["session_id"],
            user_id=session["user_context"].get("user_id", "unknown"),
            created_at=session.get("created_at", session["last_activity"]),
            last_activity=session["last_activity"],
            history_count=session["history_count"],
            user_context=session["user_context"],
            is_active=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get session error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/history", response_model=SessionHistory)
async def get_session_history(
    session_id: str,
    limit: int = Query(20, ge=1, le=100, description="히스토리 항목 수"),
    supervisor: SupervisorService = Depends(get_supervisor_service)
):
    """
    세션 대화 히스토리 조회

    특정 세션의 대화 히스토리를 조회합니다.
    """
    try:
        # 세션 확인
        session = supervisor.get_session_info(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        # 히스토리 가져오기
        history = supervisor._get_conversation_history(session_id)

        # 제한 적용
        total_count = len(history)
        if len(history) > limit:
            history = history[-limit:]

        return SessionHistory(
            session_id=session_id,
            user_id=session["user_context"].get("user_id", "unknown"),
            history=history,
            total_count=total_count,
            retrieved_count=len(history)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get history error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    supervisor: SupervisorService = Depends(get_supervisor_service)
):
    """
    세션 삭제

    특정 세션을 종료하고 삭제합니다.
    """
    try:
        # 세션 확인
        session = supervisor.get_session_info(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        # 세션 삭제
        if session_id in supervisor.active_sessions:
            del supervisor.active_sessions[session_id]
            logger.info(f"Session {session_id} deleted")

        return {
            "message": "Session deleted successfully",
            "session_id": session_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete session error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary", response_model=ServiceStatistics)
async def get_statistics(
    supervisor: SupervisorService = Depends(get_supervisor_service)
):
    """
    서비스 통계 조회

    서비스 전체 통계 및 성능 메트릭을 조회합니다.
    """
    try:
        stats = supervisor.get_statistics()

        return ServiceStatistics(
            service_stats=stats["service_stats"],
            cache_stats=stats["cache_stats"],
            active_sessions=stats["active_sessions"],
            checkpoint_path=stats["checkpoint_path"]
        )

    except Exception as e:
        logger.error(f"Get stats error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))