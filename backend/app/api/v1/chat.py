"""
채팅 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
logger = logging.getLogger(__name__)
import uuid

from app.langgraph.supervisor_multi_agent import run_multi_agent_supervisor
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


@router.options("/")
async def chat_options(request: Request):
    """OPTIONS 요청 처리 - 디버깅 로그 포함"""
    logger.info(f"OPTIONS request received: {request.url}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    return Response(
        content="",
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "3600",
        }
    )

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
        
        # Multi-Agent Supervisor 실행
        result = await run_multi_agent_supervisor(
            user_input=request.message,
            session_id=session_id,
            user_id=request.user_id
        )
        
        # 응답 추출
        if result.get("success"):
            response_text = result.get("message", "처리 완료")
        else:
            response_text = result.get("message", "처리 중 오류가 발생했습니다.")
        
        # 메타데이터 구성
        metadata = result.get("metadata", {})
        metadata.update({
            "agent_outputs": result.get("agent_outputs", {}),
            "execution_type": result.get("execution_type", "unknown"),
            "success": result.get("success", False)
        })
        
        # 사용된 에이전트 추출
        agents_used = list(result.get("agent_outputs", {}).keys())
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            agent_used=agents_used[0] if agents_used else None,
            metadata=metadata
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
                ],
                "tools": [
                    "drug_search", "customer_search", "vector_search", 
                    "literature_search", "web_search"
                ]
            },
            {
                "name": "doc_generation",
                "description": "문서 자동 생성",
                "capabilities": [
                    "제안서 작성",
                    "보고서 생성",
                    "이메일 작성"
                ],
                "tools": [
                    "document_generator", "report_builder", 
                    "template_manager", "data_formatter"
                ]
            },
            {
                "name": "compliance",
                "description": "규정 검사 및 컴플라이언스",
                "capabilities": [
                    "KGSP 규정 확인",
                    "리베이트 위험도 평가",
                    "프로모션 자료 검토"
                ],
                "tools": [
                    "compliance_check", "regulatory_search", 
                    "risk_assessment", "audit_trail"
                ]
            },
            {
                "name": "analytics",
                "description": "데이터 분석 및 인사이트",
                "capabilities": [
                    "판매 실적 분석",
                    "거래처 프로파일링",
                    "트렌드 예측"
                ],
                "tools": [
                    "data_analysis", "trend_analysis", 
                    "statistical_analysis", "comparative_analysis"
                ]
            }
        ]
    }


@router.get("/tools")
async def get_available_tools():
    """
    사용 가능한 도구 목록 조회
    """
    return {
        "tools": {
            "database": [
                {"name": "drug_search", "description": "의약품 정보 검색"},
                {"name": "customer_search", "description": "고객/병원 정보 검색"},
                {"name": "sales_analysis", "description": "매출 데이터 분석"}
            ],
            "search": [
                {"name": "vector_search", "description": "벡터 DB 검색"},
                {"name": "literature_search", "description": "학술 문헌 검색"},
                {"name": "web_search", "description": "웹 검색"}
            ],
            "document": [
                {"name": "document_generator", "description": "문서 생성"},
                {"name": "report_builder", "description": "보고서 작성"},
                {"name": "template_manager", "description": "템플릿 관리"}
            ],
            "compliance": [
                {"name": "compliance_check", "description": "규정 준수 확인"},
                {"name": "risk_assessment", "description": "리스크 평가"}
            ],
            "analysis": [
                {"name": "data_analysis", "description": "데이터 분석"},
                {"name": "trend_analysis", "description": "트렌드 분석"},
                {"name": "statistical_analysis", "description": "통계 분석"}
            ]
        }
    }


class ComplexQueryRequest(BaseModel):
    """복합 질의 요청 모델"""
    query: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    agents: Optional[List[str]] = None  # 특정 에이전트 지정


@router.options("/complex")
async def complex_options(request: Request):
    """OPTIONS 요청 처리 - 디버깅 로그 포함"""
    logger.info(f"OPTIONS request received for /complex: {request.url}")
    
    return Response(
        content="",
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "3600",
        }
    )

@router.post("/complex", response_model=ChatResponse)
async def complex_query(
    request: ComplexQueryRequest
) -> ChatResponse:
    """
    복합 질의 처리 엔드포인트
    여러 에이전트를 동시에 활용하여 복잡한 요청 처리
    """
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        # Multi-Agent Supervisor 실행
        result = await run_multi_agent_supervisor(
            user_input=request.query,
            session_id=session_id,
            user_id=request.user_id
        )
        
        # 복합 응답 처리
        if result.get("success"):
            response_text = result.get("message", "처리 완료")
        else:
            response_text = result.get("message", "처리 중 오류가 발생했습니다.")
        
        # 메타데이터 구성
        metadata = result.get("metadata", {})
        metadata.update({
            "agent_outputs": result.get("agent_outputs", {}),
            "execution_type": result.get("execution_type", "unknown"),
            "agents_used": list(result.get("agent_outputs", {}).keys()),
            "success": result.get("success", False)
        })
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            agent_used="multi_agent",
            metadata=metadata
        )
        
    except Exception as e:
        logger.error(f"복합 질의 처리 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))