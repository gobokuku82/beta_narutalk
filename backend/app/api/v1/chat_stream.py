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
            "history": []
        }
    
    progress_store[session_id].update(data)
    progress_store[session_id]["history"].append({
        "timestamp": datetime.now().isoformat(),
        "update": data
    })
    
    logger.info(f"Progress update for session {session_id}: {data}")


def get_progress(session_id: str) -> Optional[Dict[str, Any]]:
    """진행 상황 조회"""
    return progress_store.get(session_id)


def clear_progress(session_id: str):
    """진행 상황 초기화"""
    if session_id in progress_store:
        del progress_store[session_id]


async def event_generator(session_id: str) -> AsyncGenerator[str, None]:
    """SSE 이벤트 생성기"""
    logger.info(f"Starting SSE stream for session {session_id}")
    
    # 초기 연결 메시지
    yield f"data: {json.dumps({'type': 'connection', 'message': 'Connected to progress stream'})}\n\n"
    
    last_update = None
    retry_count = 0
    max_retries = 300  # 최대 5분 (1초 * 300)
    
    while retry_count < max_retries:
        try:
            # 진행 상황 확인
            progress = get_progress(session_id)
            
            if progress:
                # 변경 사항이 있을 때만 전송
                if progress != last_update:
                    event_data = {
                        "type": "progress",
                        "session_id": session_id,
                        "current_step": progress.get("current_step", 0),
                        "total_steps": progress.get("total_steps", 0),
                        "agents": progress.get("agents", []),
                        "active_agent": progress.get("active_agent"),
                        "message": progress.get("message", ""),
                        "status": progress.get("status", "processing"),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    yield f"data: {json.dumps(event_data)}\n\n"
                    last_update = progress.copy()
                    
                    # 완료 상태면 스트림 종료
                    if progress.get("status") == "completed":
                        yield f"data: {json.dumps({'type': 'completed', 'message': 'Processing completed'})}\n\n"
                        break
                    elif progress.get("status") == "error":
                        yield f"data: {json.dumps({'type': 'error', 'message': progress.get('error_message', 'An error occurred')})}\n\n"
                        break
            
            # 하트비트 (연결 유지)
            if retry_count % 30 == 0:  # 30초마다
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"
            
            await asyncio.sleep(1)
            retry_count += 1
            
        except asyncio.CancelledError:
            logger.info(f"SSE stream cancelled for session {session_id}")
            break
        except Exception as e:
            logger.error(f"Error in SSE stream for session {session_id}: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            break
    
    # 타임아웃
    if retry_count >= max_retries:
        yield f"data: {json.dumps({'type': 'timeout', 'message': 'Stream timeout'})}\n\n"
    
    # 진행 상황 정리
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


# Export functions for supervisor
__all__ = ['update_progress', 'get_progress', 'clear_progress']