"""
라우터 에이전트 - 사용자 의도 분석 및 라우팅 결정
포트: 8001
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="Router Agent",
    description="사용자 의도 분석 및 라우팅 결정 에이전트",
    version="1.0.0"
)

# 요청/응답 모델
class AnalyzeRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

class AnalyzeResponse(BaseModel):
    intent: str
    confidence: float
    service: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None


# 간단한 의도 분석 로직 (실제로는 더 복잡한 모델 사용)
def analyze_intent(message: str) -> Dict[str, Any]:
    """의도 분석 함수"""
    message_lower = message.lower()
    
    # 키워드 기반 의도 분류
    if any(keyword in message_lower for keyword in ['문서', '검색', '찾아', '정보', '자료']):
        return {
            'intent': 'document_search',
            'confidence': 0.8,
            'service': 'document_agent',
            'keywords': ['문서', '검색']
        }
    
    elif any(keyword in message_lower for keyword in ['직원', '사원', '근무', '출근', '실적', '성과']):
        return {
            'intent': 'employee_analysis',
            'confidence': 0.85,
            'service': 'employee_agent',
            'keywords': ['직원', '분석']
        }
    
    elif any(keyword in message_lower for keyword in ['고객', '거래처', '클라이언트', '계약', '매출']):
        return {
            'intent': 'client_info',
            'confidence': 0.75,
            'service': 'client_agent',
            'keywords': ['고객', '정보']
        }
    
    else:
        return {
            'intent': 'general_chat',
            'confidence': 0.6,
            'service': 'general_agent',
            'keywords': ['일반', '대화']
        }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_message(request: AnalyzeRequest):
    """메시지 의도 분석"""
    try:
        logger.info(f"Analyzing message: {request.message}")
        
        # 의도 분석
        analysis = analyze_intent(request.message)
        
        response = AnalyzeResponse(
            intent=analysis['intent'],
            confidence=analysis['confidence'],
            service=analysis['service'],
            timestamp=datetime.now().isoformat(),
            details=analysis
        )
        
        logger.info(f"Analysis result: {response}")
        return response
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스 체크"""
    return HealthResponse(
        status="healthy",
        service="router_agent",
        timestamp=datetime.now().isoformat(),
        details={
            "port": 8001,
            "version": "1.0.0",
            "capabilities": ["intent_analysis", "routing_decision"]
        }
    )


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "router_agent",
        "description": "사용자 의도 분석 및 라우팅 결정 에이전트",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "/analyze",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001) 