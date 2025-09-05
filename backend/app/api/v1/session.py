"""
Session Management API
세션 관리 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging
logger = logging.getLogger(__name__)
import uuid
import json

router = APIRouter()

# In-memory session store (실제 환경에서는 Redis 사용)
sessions: Dict[str, Dict] = {}


class SessionCreate(BaseModel):
    """세션 생성 요청"""
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SessionResponse(BaseModel):
    """세션 응답"""
    session_id: str
    user_id: Optional[str]
    created_at: str
    last_activity: str
    metadata: Optional[Dict[str, Any]]
    message_count: int


class SessionUpdate(BaseModel):
    """세션 업데이트 요청"""
    metadata: Optional[Dict[str, Any]] = None
    append_message: Optional[Dict[str, Any]] = None


@router.post("/create", response_model=SessionResponse)
async def create_session(request: SessionCreate):
    """새 세션 생성"""
    try:
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        session_data = {
            "session_id": session_id,
            "user_id": request.user_id or f"guest_{uuid.uuid4().hex[:8]}",
            "created_at": now,
            "last_activity": now,
            "metadata": request.metadata or {},
            "messages": [],
            "message_count": 0
        }
        
        sessions[session_id] = session_data
        logger.info(f"Created session: {session_id}")
        
        return SessionResponse(**session_data)
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """세션 정보 조회"""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        session_data = sessions[session_id]
        return SessionResponse(**session_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(session_id: str, request: SessionUpdate):
    """세션 업데이트"""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        session_data = sessions[session_id]
        session_data["last_activity"] = datetime.now().isoformat()
        
        # Update metadata
        if request.metadata:
            session_data["metadata"].update(request.metadata)
        
        # Append message if provided
        if request.append_message:
            session_data["messages"].append({
                "timestamp": datetime.now().isoformat(),
                **request.append_message
            })
            session_data["message_count"] += 1
        
        sessions[session_id] = session_data
        logger.info(f"Updated session: {session_id}")
        
        return SessionResponse(**session_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """세션 삭제"""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        del sessions[session_id]
        logger.info(f"Deleted session: {session_id}")
        
        return {"success": True, "message": f"Session {session_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/messages")
async def get_session_messages(session_id: str, limit: int = 50):
    """세션 메시지 이력 조회"""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        messages = sessions[session_id].get("messages", [])
        
        # Return last N messages
        if limit > 0:
            messages = messages[-limit:]
        
        return {
            "session_id": session_id,
            "messages": messages,
            "total_count": len(sessions[session_id].get("messages", [])),
            "returned_count": len(messages)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/clear-messages")
async def clear_session_messages(session_id: str):
    """세션 메시지 초기화"""
    try:
        if session_id not in sessions:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        sessions[session_id]["messages"] = []
        sessions[session_id]["message_count"] = 0
        sessions[session_id]["last_activity"] = datetime.now().isoformat()
        
        logger.info(f"Cleared messages for session: {session_id}")
        
        return {"success": True, "message": f"Messages cleared for session {session_id}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/sessions")
async def get_user_sessions(user_id: str):
    """특정 사용자의 모든 세션 조회"""
    try:
        user_sessions = []
        
        for session_id, session_data in sessions.items():
            if session_data.get("user_id") == user_id:
                user_sessions.append({
                    "session_id": session_id,
                    "created_at": session_data.get("created_at"),
                    "last_activity": session_data.get("last_activity"),
                    "message_count": session_data.get("message_count", 0)
                })
        
        # Sort by last activity (most recent first)
        user_sessions.sort(key=lambda x: x["last_activity"], reverse=True)
        
        return {
            "user_id": user_id,
            "sessions": user_sessions,
            "total_sessions": len(user_sessions)
        }
    except Exception as e:
        logger.error(f"Error fetching user sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_old_sessions(hours: int = 24):
    """오래된 세션 정리"""
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours)
        deleted_count = 0
        
        sessions_to_delete = []
        for session_id, session_data in sessions.items():
            last_activity = datetime.fromisoformat(session_data.get("last_activity"))
            if last_activity < cutoff_time:
                sessions_to_delete.append(session_id)
        
        for session_id in sessions_to_delete:
            del sessions[session_id]
            deleted_count += 1
        
        logger.info(f"Cleaned up {deleted_count} old sessions")
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Deleted {deleted_count} sessions older than {hours} hours"
        }
    except Exception as e:
        logger.error(f"Error cleaning up sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_session_stats():
    """세션 통계"""
    try:
        total_sessions = len(sessions)
        active_sessions = 0
        total_messages = 0
        unique_users = set()
        
        now = datetime.now()
        
        for session_data in sessions.values():
            # Count active sessions (activity within last hour)
            last_activity = datetime.fromisoformat(session_data.get("last_activity"))
            if (now - last_activity).seconds < 3600:
                active_sessions += 1
            
            # Count messages
            total_messages += session_data.get("message_count", 0)
            
            # Count unique users
            user_id = session_data.get("user_id")
            if user_id:
                unique_users.add(user_id)
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_messages": total_messages,
            "unique_users": len(unique_users),
            "average_messages_per_session": round(total_messages / total_sessions, 2) if total_sessions > 0 else 0
        }
    except Exception as e:
        logger.error(f"Error getting session stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check
@router.get("/health")
async def session_health():
    """세션 서비스 상태 확인"""
    return {
        "status": "healthy",
        "service": "session_management",
        "session_count": len(sessions)
    }