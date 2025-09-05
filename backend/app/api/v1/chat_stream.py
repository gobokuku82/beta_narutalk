"""
실시간 진행 상황 스트리밍 API
SSE (Server-Sent Events)를 사용한 실시간 업데이트
"""

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator, Dict, Any, Optional
import asyncio
import json
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

# 전역 진행 상황 저장소 (실제 환경에서는 Redis 등 사용 권장)
progress_store: Dict[str, Dict[str, Any]] = {}

# 활성 SSE 연결 추적
active_connections: Dict[str, bool] = {}


def update_progress(session_id: str, data: Dict[str, Any]):
    """진행 상황 업데이트"""
    if session_id not in progress_store:
        progress_store[session_id] = {
            "current_step": 0,
            "total_steps": 0,
            "agents": [],
            "active_agent": None,
            "message": "",
            "status": "initializing",
            "history": [],
            "last_updated": datetime.now().isoformat()
        }
    
    progress_store[session_id].update(data)
    progress_store[session_id]["last_updated"] = datetime.now().isoformat()
    progress_store[session_id]["history"].append({
        "timestamp": datetime.now().isoformat(),
        "update": data
    })
    
    # 히스토리 크기 제한 (메모리 관리)
    if len(progress_store[session_id]["history"]) > 100:
        progress_store[session_id]["history"] = progress_store[session_id]["history"][-50:]
    
    logger.debug(f"Progress update for session {session_id}: {data}")


def get_progress(session_id: str) -> Optional[Dict[str, Any]]:
    """진행 상황 조회"""
    return progress_store.get(session_id)


def clear_progress(session_id: str):
    """진행 상황 초기화"""
    if session_id in progress_store:
        del progress_store[session_id]
    if session_id in active_connections:
        del active_connections[session_id]
    logger.info(f"Cleared progress for session {session_id}")


async def event_generator(session_id: str) -> AsyncGenerator[str, None]:
    """SSE 이벤트 생성기"""
    logger.info(f"Starting SSE stream for session {session_id}")
    
    # 연결 활성화 표시
    active_connections[session_id] = True
    
    # 초기 연결 메시지
    yield f"data: {json.dumps({'type': 'connection', 'message': 'Connected to progress stream', 'session_id': session_id})}\n\n"
    
    last_update = None
    last_update_time = datetime.now()
    retry_count = 0
    max_retries = 600  # 최대 10분 (1초 * 600)
    heartbeat_interval = 15  # 15초마다 하트비트
    
    while retry_count < max_retries and active_connections.get(session_id, False):
        try:
            # 진행 상황 확인
            progress = get_progress(session_id)
            current_time = datetime.now()
            
            if progress:
                # 변경 사항이 있을 때만 전송 (더 세밀한 비교)
                progress_changed = (
                    not last_update or 
                    progress.get("current_step") != last_update.get("current_step") or
                    progress.get("active_agent") != last_update.get("active_agent") or
                    progress.get("status") != last_update.get("status") or
                    progress.get("message") != last_update.get("message")
                )
                
                if progress_changed:
                    event_data = {
                        "type": "progress",
                        "session_id": session_id,
                        "current_step": progress.get("current_step", 0),
                        "total_steps": progress.get("total_steps", 0),
                        "agents": progress.get("agents", []),
                        "active_agent": progress.get("active_agent"),
                        "message": progress.get("message", ""),
                        "status": progress.get("status", "processing"),
                        "timestamp": current_time.isoformat()
                    }
                    
                    yield f"data: {json.dumps(event_data)}\n\n"
                    last_update = progress.copy()
                    last_update_time = current_time
                    
                    # 완료 상태면 잠시 대기 후 스트림 종료
                    if progress.get("status") == "completed":
                        yield f"data: {json.dumps({'type': 'completed', 'message': 'Processing completed', 'timestamp': current_time.isoformat()})}\n\n"
                        await asyncio.sleep(0.5)  # 마지막 메시지가 전달되도록 대기
                        break
                    elif progress.get("status") == "error":
                        yield f"data: {json.dumps({'type': 'error', 'message': progress.get('error_message', 'An error occurred'), 'timestamp': current_time.isoformat()})}\n\n"
                        await asyncio.sleep(0.5)
                        break
            
            # 하트비트 (연결 유지)
            if retry_count % heartbeat_interval == 0:
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': current_time.isoformat(), 'retry_count': retry_count})}\n\n"
            
            # 더 짧은 폴링 간격으로 반응성 개선
            await asyncio.sleep(0.5)
            retry_count += 1
            
        except asyncio.CancelledError:
            logger.info(f"SSE stream cancelled for session {session_id}")
            active_connections[session_id] = False
            break
        except Exception as e:
            logger.error(f"Error in SSE stream for session {session_id}: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e), 'timestamp': datetime.now().isoformat()})}\n\n"
            active_connections[session_id] = False
            break
    
    # 타임아웃
    if retry_count >= max_retries:
        yield f"data: {json.dumps({'type': 'timeout', 'message': 'Stream timeout', 'timestamp': datetime.now().isoformat()})}\n\n"
    
    # 연결 비활성화
    active_connections[session_id] = False
    
    # 완료 상태인 경우에만 진행 상황 정리 (에러나 진행 중인 경우 유지)
    progress = get_progress(session_id)
    if progress and progress.get("status") in ["completed", "error"]:
        # 잠시 유지 후 정리 (클라이언트가 재연결할 수 있도록)
        await asyncio.sleep(5)
        if not active_connections.get(session_id, False):
            clear_progress(session_id)
    
    logger.info(f"SSE stream ended for session {session_id}")


@router.get("/stream/{session_id}")
async def stream_progress(session_id: str, request: Request):
    """
    SSE를 통한 실시간 진행 상황 스트리밍
    
    클라이언트는 EventSource API를 사용하여 연결:
    ```javascript
    const eventSource = new EventSource(`/api/v1/chat/stream/${sessionId}`);
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        // 진행 상황 업데이트 처리
    };
    ```
    """
    async def generate():
        async for event in event_generator(session_id):
            if await request.is_disconnected():
                break
            yield event
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Nginx 버퍼링 비활성화
        }
    )


@router.post("/progress/{session_id}")
async def update_session_progress(
    session_id: str,
    progress_data: Dict[str, Any]
):
    """
    진행 상황 수동 업데이트 (디버깅용)
    """
    update_progress(session_id, progress_data)
    return {"status": "updated", "session_id": session_id}


@router.get("/progress/{session_id}")
async def get_session_progress(session_id: str):
    """
    현재 진행 상황 조회
    """
    progress = get_progress(session_id)
    if progress:
        return progress
    return {"error": "No progress data found for this session"}


@router.get("/debug/all-progress")
async def debug_all_progress():
    """
    디버깅용: 모든 진행 상황 조회
    """
    return {
        "active_connections": list(active_connections.keys()),
        "progress_sessions": list(progress_store.keys()),
        "details": {
            session_id: {
                "status": data.get("status"),
                "current_step": data.get("current_step"),
                "total_steps": data.get("total_steps"),
                "active_agent": data.get("active_agent"),
                "last_updated": data.get("last_updated"),
                "message": data.get("message")
            }
            for session_id, data in progress_store.items()
        }
    }


@router.delete("/progress/{session_id}")
async def delete_session_progress(session_id: str):
    """
    디버깅용: 특정 세션 진행 상황 삭제
    """
    clear_progress(session_id)
    return {"status": "cleared", "session_id": session_id}


# Export functions for supervisor
__all__ = ['update_progress', 'get_progress', 'clear_progress']