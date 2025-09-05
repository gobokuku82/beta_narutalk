"""
채팅 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from loguru import logger
import uuid

from app.langgraph.supervisor_graph import run_supervisor
from app.core.session import get_session, create_session

router = APIRouter()


class ChatRequest(BaseModel):
    """채팅 요청 모델"""
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    """채팅 응답 모델"""
    response: str
    session_id: str
    agent_used: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest
) -> ChatResponse:
    """
    메인 채팅 엔드포인트
    Supervisor를 통해 적절한 에이전트로 라우팅
    """
    try:
        # 세션 ID 생성 또는 확인
        session_id = request.session_id or str(uuid.uuid4())
        
        logger.info(f"채팅 요청: 세션={session_id}, 메시지={request.message[:50]}...")
        
        # Supervisor 실행
        result = await run_supervisor(
            user_input=request.message,
            session_id=session_id,
            user_id=request.user_id
        )
        
        # 응답 추출
        messages = result.get("messages", [])
        if messages:
            response_text = messages[-1].get("content", "처리할 수 없습니다.")
        else:
            response_text = "응답을 생성할 수 없습니다."
        
        # 사용된 에이전트 확인
        agent_used = result.get("current_agent", "unknown")
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            agent_used=agent_used,
            metadata={
                "iteration_count": result.get("iteration_count", 0),
                "error": result.get("error")
            }
        )
        
    except Exception as e:
        logger.error(f"채팅 처리 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    스트리밍 채팅 엔드포인트 (SSE)
    """
    # TODO: 스트리밍 구현
    pass


@router.get("/agents")
async def get_available_agents():
    """
    사용 가능한 에이전트 목록 조회
    """
    return {
        "agents": [
            {
                "name": "info_retrieval",
                "description": "의약품 정보 및 학술자료 검색",
                "capabilities": [
                    "제품 정보 검색",
                    "임상 데이터 조회",
                    "경쟁 제품 비교"
                ]
            },
            {
                "name": "doc_generation",
                "description": "문서 자동 생성",
                "capabilities": [
                    "제안서 작성",
                    "보고서 생성",
                    "이메일 작성"
                ]
            },
            {
                "name": "compliance",
                "description": "규정 검사 및 컴플라이언스",
                "capabilities": [
                    "KGSP 규정 확인",
                    "리베이트 위험도 평가",
                    "프로모션 자료 검토"
                ]
            },
            {
                "name": "analytics",
                "description": "데이터 분석 및 인사이트",
                "capabilities": [
                    "판매 실적 분석",
                    "거래처 프로파일링",
                    "트렌드 예측"
                ]
            }
        ]
    }