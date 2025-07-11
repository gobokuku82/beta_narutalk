"""
고도화된 라우터 에이전트 - OpenAI GPT-4o 기반 지능형 라우팅
포트: 8001
"""
import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import httpx
from dotenv import load_dotenv
import openai

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="Enhanced Router Agent",
    description="OpenAI GPT-4o 기반 지능형 라우팅 에이전트",
    version="2.0.0"
)

# 요청/응답 모델
class AnalyzeRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None

class AnalyzeResponse(BaseModel):
    intent: str
    confidence: float
    service: str
    function_call: Dict[str, Any]
    timestamp: str
    reasoning: str
    details: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str
    openai_status: str
    details: Optional[Dict[str, Any]] = None


# OpenAI Tool 정의
AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": "좋은제약 내부 문서, 정책, 규정, 윤리강령, 복리후생 등을 검색합니다. 문서 관련 질문이나 회사 정책에 대한 문의, 규정 확인이 필요할 때 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string", 
                        "description": "검색할 키워드나 질문 (예: 윤리강령, 복리후생, 행동강령)"
                    },
                    "top_k": {
                        "type": "integer", 
                        "description": "검색 결과 개수", 
                        "default": 5
                    },
                    "filters": {
                        "type": "object",
                        "description": "검색 필터 (문서 타입 등)"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "analyze_employee_data",
            "description": "직원 정보, 성과 분석, 출근 현황, 부서별 통계, 인사 데이터 등을 분석합니다. 인사 관련 질문이나 직원 데이터 분석, 성과 평가, 출근 통계가 필요할 때 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {
                        "type": "string", 
                        "description": "특정 직원 ID (선택적, 전체 분석시 null)"
                    },
                    "analysis_type": {
                        "type": "string", 
                        "enum": ["general", "performance", "attendance", "department"],
                        "description": "분석 유형: 일반정보, 성과분석, 출근현황, 부서통계"
                    },
                    "filters": {
                        "type": "object",
                        "description": "분석 필터 (부서, 기간 등)"
                    }
                },
                "required": ["analysis_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_client_information", 
            "description": "고객사 정보, 거래 내역, 계약 현황, 매출 분석, 비즈니스 관계 등을 조회합니다. 고객 관련 문의나 영업 데이터 분석, 거래처 정보 확인이 필요할 때 사용합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "client_id": {
                        "type": "string", 
                        "description": "특정 고객 ID (선택적, 전체 조회시 null)"
                    },
                    "info_type": {
                        "type": "string", 
                        "enum": ["basic", "transactions", "contracts", "analytics"],
                        "description": "정보 유형: 기본정보, 거래내역, 계약현황, 분석데이터"
                    },
                    "filters": {
                        "type": "object",
                        "description": "조회 필터 (기간, 거래유형 등)"
                    }
                },
                "required": ["info_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "general_conversation",
            "description": "일반적인 대화, 인사말, 간단한 질문 답변, 회사 소개를 처리합니다. 위의 전문 영역(문서검색, 직원분석, 고객정보)에 해당하지 않는 일반적인 대화나 질문시 사용합니다.",
            "parameters": {
                "type": "object", 
                "properties": {
                    "message": {
                        "type": "string", 
                        "description": "사용자 메시지"
                    },
                    "context": {
                        "type": "object",
                        "description": "대화 맥락 정보 (선택적)"
                    },
                    "conversation_id": {
                        "type": "string",
                        "description": "대화 ID (선택적)"
                    }
                },
                "required": ["message"]
            }
        }
    }
]


class EnhancedRouterAgent:
    """OpenAI GPT-4o 기반 고도화된 라우터 에이전트"""
    
    def __init__(self):
        # OpenAI 클라이언트 초기화
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.warning("OPENAI_API_KEY not found. Using fallback routing.")
            self.openai_client = None
        else:
            self.openai_client = openai.OpenAI(api_key=api_key)
            logger.info("OpenAI 클라이언트 초기화 완료")
        
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o')
        self.tools = AGENT_TOOLS
        
        # 서비스 URL 매핑
        self.service_urls = {
            "search_documents": "http://localhost:8002",
            "analyze_employee_data": "http://localhost:8003", 
            "get_client_information": "http://localhost:8004",
            "general_conversation": "http://localhost:8005"
        }
    
    async def route_with_gpt4o(self, user_message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """GPT-4o를 사용한 지능형 라우팅"""
        
        if not self.openai_client:
            # OpenAI API가 없으면 폴백 라우팅 사용
            return self._fallback_routing(user_message)
        
        try:
            # 시스템 프롬프트 구성
            system_prompt = """
            당신은 좋은제약 AI 어시스턴트의 지능형 라우터입니다. 
            사용자의 질문을 정확히 분석하여 가장 적절한 전문 에이전트에게 라우팅해야 합니다.

            4개의 전문 에이전트와 역할:
            
            1. **문서검색 에이전트** (search_documents)
               - 회사 정책, 규정, 윤리강령, 행동강령, 복리후생 등 내부 문서 검색
               - 키워드: 문서, 정책, 규정, 윤리, 강령, 복리후생, 자료, 찾아줘
            
            2. **직원분석 에이전트** (analyze_employee_data)  
               - 직원 정보, 성과 분석, 출근 현황, 부서 통계, 인사 데이터
               - 키워드: 직원, 사원, 성과, 출근, 부서, 통계, 분석, 인사
               
            3. **고객정보 에이전트** (get_client_information)
               - 고객사 정보, 거래 내역, 계약 현황, 매출 분석, 영업 데이터
               - 키워드: 고객, 거래처, 클라이언트, 매출, 계약, 거래, 영업
               
            4. **일반대화 에이전트** (general_conversation)
               - 인사말, 일반 질문, 회사 소개, 기타 대화
               - 위 3개 영역에 해당하지 않는 모든 대화

            사용자 질문을 분석하여 가장 적합한 function을 호출하고, 
            적절한 parameters를 설정하세요.
            """
            
            # 대화 맥락 포함
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # 컨텍스트가 있으면 추가
            if context and context.get('previous_messages'):
                messages = context['previous_messages'] + messages[-1:]
            
            # OpenAI API 호출
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                temperature=0.1  # 일관성을 위해 낮은 temperature
            )
            
            # 응답 처리
            message = response.choices[0].message
            
            if message.tool_calls:
                tool_call = message.tool_calls[0]
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # 신뢰도 계산 (간단한 휴리스틱)
                confidence = self._calculate_confidence(user_message, function_name)
                
                return {
                    "intent": function_name,
                    "confidence": confidence,
                    "service": self._get_service_name(function_name),
                    "function_call": {
                        "name": function_name,
                        "arguments": function_args
                    },
                    "reasoning": message.content or "GPT-4o 분석 결과",
                    "openai_response": response.model_dump()
                }
            else:
                # Tool Call이 없으면 일반 대화로 라우팅
                return {
                    "intent": "general_conversation",
                    "confidence": 0.8,
                    "service": "general_agent",
                    "function_call": {
                        "name": "general_conversation",
                        "arguments": {"message": user_message}
                    },
                    "reasoning": "일반 대화로 분류됨",
                    "openai_response": response.model_dump()
                }
                
        except Exception as e:
            logger.error(f"OpenAI API 호출 실패: {str(e)}")
            return self._fallback_routing(user_message)
    
    def _fallback_routing(self, message: str) -> Dict[str, Any]:
        """OpenAI API 사용 불가시 폴백 라우팅"""
        message_lower = message.lower()
        
        # 간단한 키워드 기반 분류
        if any(keyword in message_lower for keyword in ['문서', '정책', '규정', '윤리', '강령', '복리후생']):
            return {
                "intent": "search_documents",
                "confidence": 0.7,
                "service": "document_agent",
                "function_call": {
                    "name": "search_documents",
                    "arguments": {"query": message}
                },
                "reasoning": "키워드 기반 문서 검색 분류"
            }
        elif any(keyword in message_lower for keyword in ['직원', '사원', '성과', '출근', '부서']):
            return {
                "intent": "analyze_employee_data",
                "confidence": 0.7,
                "service": "employee_agent", 
                "function_call": {
                    "name": "analyze_employee_data",
                    "arguments": {"analysis_type": "general"}
                },
                "reasoning": "키워드 기반 직원 분석 분류"
            }
        elif any(keyword in message_lower for keyword in ['고객', '거래처', '매출', '계약']):
            return {
                "intent": "get_client_information",
                "confidence": 0.7,
                "service": "client_agent",
                "function_call": {
                    "name": "get_client_information", 
                    "arguments": {"info_type": "basic"}
                },
                "reasoning": "키워드 기반 고객 정보 분류"
            }
        else:
            return {
                "intent": "general_conversation",
                "confidence": 0.6,
                "service": "general_agent",
                "function_call": {
                    "name": "general_conversation",
                    "arguments": {"message": message}
                },
                "reasoning": "기본 일반 대화 분류"
            }
    
    def _calculate_confidence(self, message: str, function_name: str) -> float:
        """신뢰도 계산"""
        # 간단한 키워드 매칭 기반 신뢰도
        keyword_mapping = {
            "search_documents": ['문서', '정책', '규정', '윤리', '강령', '복리후생'],
            "analyze_employee_data": ['직원', '사원', '성과', '출근', '부서'],
            "get_client_information": ['고객', '거래처', '매출', '계약'],
            "general_conversation": ['안녕', '반갑', '좋은', '회사']
        }
        
        keywords = keyword_mapping.get(function_name, [])
        message_lower = message.lower()
        
        matches = sum(1 for keyword in keywords if keyword in message_lower)
        base_confidence = 0.9  # GPT-4o 사용시 높은 기본 신뢰도
        
        return min(base_confidence + (matches * 0.05), 0.99)
    
    def _get_service_name(self, function_name: str) -> str:
        """함수 이름을 서비스 이름으로 변환"""
        mapping = {
            "search_documents": "document_agent",
            "analyze_employee_data": "employee_agent",
            "get_client_information": "client_agent", 
            "general_conversation": "general_agent"
        }
        return mapping.get(function_name, "general_agent")


# 글로벌 라우터 인스턴스
enhanced_router = EnhancedRouterAgent()


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_message(request: AnalyzeRequest):
    """메시지 의도 분석 (GPT-4o 기반)"""
    try:
        logger.info(f"GPT-4o 기반 메시지 분석: {request.message}")
        
        # GPT-4o를 사용한 라우팅
        result = await enhanced_router.route_with_gpt4o(
            request.message, 
            request.context
        )
        
        response = AnalyzeResponse(
            intent=result['intent'],
            confidence=result['confidence'],
            service=result['service'],
            function_call=result['function_call'],
            timestamp=datetime.now().isoformat(),
            reasoning=result['reasoning'],
            details=result.get('openai_response')
        )
        
        logger.info(f"분석 완료: {result['intent']} (신뢰도: {result['confidence']})")
        return response
        
    except Exception as e:
        logger.error(f"분석 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스 체크"""
    openai_status = "available" if enhanced_router.openai_client else "unavailable"
    
    return HealthResponse(
        status="healthy",
        service="enhanced_router_agent",
        timestamp=datetime.now().isoformat(),
        openai_status=openai_status,
        details={
            "port": 8001,
            "version": "2.0.0",
            "model": enhanced_router.model,
            "capabilities": [
                "gpt4o_routing", 
                "tool_calling", 
                "fallback_routing",
                "intent_analysis"
            ],
            "tools_count": len(enhanced_router.tools)
        }
    )


@app.get("/tools")
async def get_tools():
    """사용 가능한 도구 목록 조회"""
    return {
        "tools": AGENT_TOOLS,
        "count": len(AGENT_TOOLS),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "enhanced_router_agent",
        "description": "OpenAI GPT-4o 기반 지능형 라우팅 에이전트",
        "version": "2.0.0",
        "model": enhanced_router.model,
        "endpoints": {
            "analyze": "/analyze",
            "health": "/health",
            "tools": "/tools"
        },
        "features": [
            "GPT-4o 기반 지능형 라우팅",
            "OpenAI Tool Calling",
            "폴백 라우팅 지원",
            "실시간 의도 분석"
        ]
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001) 