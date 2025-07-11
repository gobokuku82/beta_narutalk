"""
일반 대화 에이전트 - 일반적인 질문과 대화 처리
포트: 8005
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="General Agent",
    description="일반적인 질문과 대화 처리 에이전트",
    version="1.0.0"
)

# 요청/응답 모델
class ChatRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    context: Optional[Dict[str, Any]] = None
    conversation_id: str
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None


# 간단한 대화 규칙 (실제로는 LLM 사용)
CHAT_RESPONSES = {
    "인사": [
        "안녕하세요! 좋은제약 AI 어시스턴트입니다. 무엇을 도와드릴까요?",
        "반갑습니다! 궁금한 것이 있으시면 언제든 물어보세요.",
        "안녕하세요! 어떤 도움이 필요하신가요?"
    ],
    "감사": [
        "도움이 되었다니 기쁩니다!",
        "천만에요! 언제든 도와드리겠습니다.",
        "좋은 하루 보내세요!"
    ],
    "회사": [
        "좋은제약은 국내 최고의 제약회사로, 건강한 사회를 만들어가는 것을 목표로 합니다.",
        "저희 회사는 윤리적 경영과 사회적 책임을 다하는 제약회사입니다.",
        "좋은제약에 대해 더 자세히 알고 싶으시면 문서 검색을 이용해보세요."
    ],
    "업무": [
        "구체적인 업무 관련 질문이 있으시면 해당 분야의 전문 에이전트를 이용해보세요.",
        "직원 관련 문의는 직원 분석 시스템을, 고객 관련 문의는 고객 정보 시스템을 이용하시면 됩니다.",
        "문서나 자료가 필요하시면 문서 검색 시스템을 활용해보세요."
    ],
    "기본": [
        "죄송합니다. 정확히 이해하지 못했습니다. 다시 한 번 말씀해주시겠어요?",
        "더 구체적으로 설명해주시면 더 정확한 답변을 드릴 수 있습니다.",
        "특정 분야의 질문이시라면 전문 에이전트를 이용하시는 것이 좋습니다."
    ]
}


def classify_message(message: str) -> str:
    """메시지 분류 함수"""
    message_lower = message.lower()
    
    if any(keyword in message_lower for keyword in ['안녕', '하이', '반갑', '처음', '시작']):
        return "인사"
    elif any(keyword in message_lower for keyword in ['감사', '고마워', '좋아', '훌륭', '잘']):
        return "감사"
    elif any(keyword in message_lower for keyword in ['회사', '좋은제약', '제약회사', '기업']):
        return "회사"
    elif any(keyword in message_lower for keyword in ['업무', '일', '작업', '프로젝트']):
        return "업무"
    else:
        return "기본"


def generate_response(message: str, context: Optional[Dict[str, Any]] = None) -> str:
    """응답 생성 함수"""
    category = classify_message(message)
    
    # 컨텍스트 기반 응답 조정
    if context and context.get('previous_category'):
        if context['previous_category'] == "인사" and category == "기본":
            return "어떤 도움이 필요하신지 구체적으로 말씀해주세요."
    
    # 카테고리별 응답 선택
    responses = CHAT_RESPONSES.get(category, CHAT_RESPONSES["기본"])
    
    # 간단한 로테이션 (실제로는 더 복잡한 로직 사용)
    import random
    return random.choice(responses)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """일반 대화 처리"""
    try:
        logger.info(f"Processing chat message: {request.message}")
        
        # 대화 ID 생성 (없으면 새로 생성)
        conversation_id = request.conversation_id or f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 응답 생성
        response_text = generate_response(request.message, request.context)
        
        # 새로운 컨텍스트 생성
        new_context = {
            "previous_message": request.message,
            "previous_category": classify_message(request.message),
            "conversation_length": (request.context.get('conversation_length', 0) + 1) if request.context else 1
        }
        
        response = ChatResponse(
            response=response_text,
            context=new_context,
            conversation_id=conversation_id,
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"Chat response generated: {response.response[:50]}...")
        return response
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """대화 기록 조회 (모의 구현)"""
    return {
        "conversation_id": conversation_id,
        "messages": [
            {
                "role": "user",
                "message": "안녕하세요",
                "timestamp": "2024-01-01T10:00:00Z"
            },
            {
                "role": "assistant",
                "message": "안녕하세요! 좋은제약 AI 어시스턴트입니다.",
                "timestamp": "2024-01-01T10:00:01Z"
            }
        ],
        "timestamp": datetime.now().isoformat()
    }


@app.get("/categories")
async def get_categories():
    """대화 카테고리 조회"""
    return {
        "categories": list(CHAT_RESPONSES.keys()),
        "descriptions": {
            "인사": "인사말 및 시작 대화",
            "감사": "감사 표현 및 긍정적 피드백",
            "회사": "회사 관련 일반적인 질문",
            "업무": "업무 관련 일반적인 안내",
            "기본": "기타 일반적인 대화"
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/stats")
async def get_stats():
    """통계 조회"""
    return {
        "total_categories": len(CHAT_RESPONSES),
        "total_responses": sum(len(responses) for responses in CHAT_RESPONSES.values()),
        "capabilities": ["general_chat", "context_awareness", "conversation_tracking"],
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스 체크"""
    return HealthResponse(
        status="healthy",
        service="general_agent",
        timestamp=datetime.now().isoformat(),
        details={
            "port": 8005,
            "version": "1.0.0",
            "capabilities": ["general_chat", "context_awareness", "conversation_tracking"],
            "response_categories": len(CHAT_RESPONSES)
        }
    )


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "general_agent",
        "description": "일반적인 질문과 대화 처리 에이전트",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/chat",
            "conversation": "/conversation/{conversation_id}",
            "categories": "/categories",
            "stats": "/stats",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005) 