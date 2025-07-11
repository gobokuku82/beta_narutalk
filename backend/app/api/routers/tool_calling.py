"""
Tool Calling 기반 채팅 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
from ...services.tool_calling_router import ToolCallingRouter

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# 전역 라우터 인스턴스
tool_calling_router = ToolCallingRouter()

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    
class ChatResponse(BaseModel):
    response: str
    tool_calls: List[Dict[str, Any]]
    router_type: str
    session_id: Optional[str] = None
    error: Optional[str] = None

@router.post("/chat", response_model=ChatResponse)
async def tool_calling_chat(request: ChatMessage):
    """
    Tool calling 방식으로 메시지를 처리합니다.
    """
    try:
        logger.info(f"Tool calling chat request: {request.message}")
        
        # 라우터를 통해 메시지 처리
        result = await tool_calling_router.route_message(
            message=request.message,
            session_id=request.session_id
        )
        
        logger.info(f"Tool calling chat response: {result}")
        
        return ChatResponse(
            response=result["response"],
            tool_calls=result.get("tool_calls", []),
            router_type=result["router_type"],
            session_id=request.session_id,
            error=result.get("error")
        )
        
    except Exception as e:
        logger.error(f"Tool calling chat error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Tool calling chat failed: {str(e)}"
        )

@router.get("/tools")
async def get_available_tools():
    """
    사용 가능한 도구들의 목록을 반환합니다.
    """
    try:
        tools_info = []
        for tool in tool_calling_router.tools:
            tools_info.append({
                "name": tool["function"]["name"],
                "description": tool["function"]["description"],
                "parameters": tool["function"]["parameters"]
            })
        
        return {
            "tools": tools_info,
            "count": len(tools_info)
        }
        
    except Exception as e:
        logger.error(f"Get tools error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get tools: {str(e)}"
        )

@router.post("/test-tool")
async def test_tool(tool_name: str, tool_args: Dict[str, Any]):
    """
    개별 도구를 테스트합니다.
    """
    try:
        logger.info(f"Testing tool: {tool_name} with args: {tool_args}")
        
        result = await tool_calling_router._execute_tool(tool_name, tool_args)
        
        return {
            "tool_name": tool_name,
            "args": tool_args,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Test tool error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Tool test failed: {str(e)}"
        ) 