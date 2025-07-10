"""
라우터 API 엔드포인트

새로운 모듈화된 라우터 시스템을 위한 API 엔드포인트들을 제공합니다.
서비스는 요청 시점에 초기화됩니다.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter()

# 서비스 의존성 함수들
def get_langgraph_service():
    """LangGraph 서비스 의존성"""
    try:
        from ...services.langgraph_service import LangGraphService
        return LangGraphService()
    except Exception as e:
        logger.error(f"LangGraph 서비스 초기화 실패: {str(e)}")
        return None

class ChatMessage(BaseModel):
    """채팅 메시지 모델"""
    message: str
    user_id: str = "default_user"
    session_id: str = "default_session"

class RouterInfo(BaseModel):
    """라우터 정보 모델"""
    name: str
    description: str
    keywords: List[str]
    priority: int

@router.post("/chat", response_model=Dict[str, Any])
async def chat(message: ChatMessage, service = Depends(get_langgraph_service)):
    """
    챗봇 대화 처리
    
    Args:
        message: 채팅 메시지
        service: LangGraph 서비스
        
    Returns:
        처리 결과
    """
    try:
        if service is None:
            return {
                "success": False,
                "error": "서비스를 초기화할 수 없습니다.",
                "data": {
                    "response": "죄송합니다. 현재 서비스를 사용할 수 없습니다. OpenAI API 키가 설정되어 있는지 확인해주세요.",
                    "router_type": "error",
                    "confidence": 0.0,
                    "sources": [],
                    "metadata": {"error": "service_unavailable"}
                }
            }
        
        result = await service.process_message(
            message.message, 
            message.user_id, 
            message.session_id
        )
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"채팅 처리 실패: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "response": f"죄송합니다. 채팅 처리 중 오류가 발생했습니다: {str(e)}",
                "router_type": "error",
                "confidence": 0.0,
                "sources": [],
                "metadata": {"error": str(e)}
            }
        }

@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str, service = Depends(get_langgraph_service)):
    """
    채팅 기록 조회
    
    Args:
        session_id: 세션 ID
        service: LangGraph 서비스
        
    Returns:
        채팅 기록
    """
    try:
        if service is None:
            return {
                "success": False,
                "error": "서비스를 초기화할 수 없습니다.",
                "data": {
                    "session_id": session_id,
                    "history": [],
                    "count": 0
                }
            }
        
        history = await service.get_chat_history(session_id)
        
        return {
            "success": True,
            "data": {
                "session_id": session_id,
                "history": history,
                "count": len(history)
            }
        }
        
    except Exception as e:
        logger.error(f"채팅 기록 조회 실패: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "session_id": session_id,
                "history": [],
                "count": 0
            }
        }

@router.get("/routers")
async def get_routers(service = Depends(get_langgraph_service)):
    """
    사용 가능한 라우터 목록 조회
    
    Returns:
        라우터 목록
    """
    try:
        if service is None:
            # 기본 라우터 목록 반환
            default_routers = [
                {
                    "name": "general_chat_router",
                    "description": "일반 대화 처리",
                    "keywords": ["안녕", "대화", "채팅"],
                    "priority": 3
                },
                {
                    "name": "qa_router",
                    "description": "질문답변 기능",
                    "keywords": ["질문", "답변", "알려줘"],
                    "priority": 8
                }
            ]
            return {
                "success": True,
                "data": {
                    "routers": default_routers,
                    "count": len(default_routers)
                }
            }
        
        routers = service.get_router_types()
        
        return {
            "success": True,
            "data": {
                "routers": routers,
                "count": len(routers)
            }
        }
        
    except Exception as e:
        logger.error(f"라우터 목록 조회 실패: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "routers": [],
                "count": 0
            }
        }

@router.get("/status")
async def get_service_status(service = Depends(get_langgraph_service)):
    """
    서비스 상태 조회
    
    Returns:
        서비스 상태 정보
    """
    try:
        if service is None:
            return {
                "success": True,
                "data": {
                    "status": "limited",
                    "embedding_service": "unavailable",
                    "database_service": "unavailable", 
                    "openai_client": "unavailable",
                    "message": "서비스가 제한 모드로 실행 중입니다."
                }
            }
        
        status = service.get_service_status()
        
        return {
            "success": True,
            "data": status
        }
        
    except Exception as e:
        logger.error(f"서비스 상태 조회 실패: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "status": "error",
                "message": str(e)
            }
        }

@router.get("/health")
async def health_check(service = Depends(get_langgraph_service)):
    """
    헬스 체크
    
    Returns:
        헬스 체크 결과
    """
    try:
        if service is None:
            return {
                "success": True,
                "data": {
                    "status": "limited",
                    "test_message_processed": False,
                    "router_count": 0,
                    "services": {
                        "embedding": False,
                        "database": False,
                        "openai": False
                    },
                    "message": "기본 기능만 사용 가능합니다."
                }
            }
        
        health = await service.health_check()
        
        return {
            "success": True,
            "data": health
        }
        
    except Exception as e:
        logger.error(f"헬스 체크 실패: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "status": "unhealthy",
                "message": str(e)
            }
        }

@router.post("/routers/{router_name}/remove")
async def remove_router(router_name: str, service = Depends(get_langgraph_service)):
    """
    라우터 제거
    
    Args:
        router_name: 제거할 라우터 이름
        service: LangGraph 서비스
        
    Returns:
        제거 결과
    """
    try:
        if service is None:
            raise HTTPException(
                status_code=500,
                detail="서비스를 초기화할 수 없어 라우터 제거를 수행할 수 없습니다."
            )
        
        # 필수 라우터는 제거할 수 없음
        protected_routers = ["general_chat_router", "qa_router"]
        if router_name in protected_routers:
            raise HTTPException(
                status_code=400,
                detail=f"필수 라우터 {router_name}는 제거할 수 없습니다."
            )
        
        service.remove_router(router_name)
        
        return {
            "success": True,
            "message": f"라우터 {router_name}가 성공적으로 제거되었습니다."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"라우터 제거 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"라우터 제거 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/demo")
async def demo_conversation(service = Depends(get_langgraph_service)):
    """
    데모 대화 실행
    
    Returns:
        데모 대화 결과
    """
    try:
        if service is None:
            return {
                "success": True,
                "data": {
                    "demo_results": [
                        {
                            "message": "안녕하세요",
                            "response": "안녕하세요! 기본 모드로 실행 중입니다.",
                            "router_type": "fallback",
                            "confidence": 0.5
                        }
                    ],
                    "message": "기본 데모가 실행되었습니다."
                }
            }
        
        demo_messages = [
            "안녕하세요",
            "도움말을 보여주세요", 
            "문서를 검색하고 싶습니다",
            "직원 정보를 찾고 있습니다"
        ]
        
        results = []
        for i, msg in enumerate(demo_messages):
            try:
                result = await service.process_message(
                    msg, 
                    "demo_user", 
                    f"demo_session_{i}"
                )
                results.append({
                    "message": msg,
                    "response": result["response"][:200] + "..." if len(result["response"]) > 200 else result["response"],
                    "router_type": result["router_type"],
                    "confidence": result["confidence"]
                })
            except Exception as e:
                results.append({
                    "message": msg,
                    "response": f"데모 처리 실패: {str(e)}",
                    "router_type": "error",
                    "confidence": 0.0
                })
        
        return {
            "success": True,
            "data": {
                "demo_results": results,
                "message": "다양한 라우터가 적절히 선택되어 처리되었습니다."
            }
        }
        
    except Exception as e:
        logger.error(f"데모 실행 실패: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "demo_results": [],
                "message": f"데모 실행 중 오류가 발생했습니다: {str(e)}"
            }
        }

@router.get("/statistics")
async def get_statistics(service = Depends(get_langgraph_service)):
    """
    라우터 통계 정보 조회
    
    Returns:
        통계 정보
    """
    try:
        if service is None:
            return {
                "success": False,
                "error": "서비스를 초기화할 수 없습니다.",
                "data": {
                    "message": "서비스가 제한 모드로 실행 중이므로 통계를 조회할 수 없습니다."
                }
            }
        
        stats = service.router_manager.get_router_statistics()
        
        return {
            "success": True,
            "data": stats
        }
        
    except Exception as e:
        logger.error(f"통계 조회 실패: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "message": str(e)
            }
        }

@router.get("/test")
async def test_basic():
    """
    기본 테스트 엔드포인트
    
    Returns:
        기본 테스트 결과
    """
    return {
        "success": True,
        "message": "API가 정상적으로 작동하고 있습니다.",
        "data": {
            "timestamp": "2024-01-01T00:00:00Z",
            "version": "1.0.0",
            "status": "healthy"
        }
    } 