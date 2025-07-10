"""
일반 대화 라우터

일반적인 대화, 인사, 잡담 등을 처리하는 라우터입니다.
OpenAI GPT-4o를 사용하여 자연스러운 대화를 제공합니다.
"""

from typing import List, Dict, Any
import logging
from .base_router import BaseRouter, RouterContext, RouterResult, RouterAction

logger = logging.getLogger(__name__)

class GeneralChatRouter(BaseRouter):
    """일반 대화 라우터"""
    
    def __init__(self):
        super().__init__("general_chat_router")
    
    def get_description(self) -> str:
        return "일반적인 대화, 인사, 잡담을 처리합니다. 사용자와 자연스러운 대화를 나누며 친근한 분위기를 조성합니다."
    
    def get_keywords(self) -> List[str]:
        return [
            "안녕", "hi", "hello", "좋은", "나쁜", "기분", "날씨", "오늘", "어떻게", "지내",
            "고마워", "감사", "미안", "죄송", "반가워", "처음", "만나서", "인사", "대화",
            "채팅", "이야기", "chat", "talk", "conversation", "잡담", "수다", "심심",
            "도움말", "help", "도움", "설명서", "가이드", "사용법", "기능", "뭐해"
        ]
    
    def get_priority(self) -> int:
        return 3  # 낮은 우선순위 (다른 라우터가 처리할 수 없을 때)
    
    async def can_handle(self, context: RouterContext) -> float:
        """일반 대화 라우터가 메시지를 처리할 수 있는지 확인"""
        message = context.current_message.lower()
        
        confidence = 0.0
        
        # 인사말 패턴
        greeting_patterns = ["안녕", "hi", "hello", "좋은", "반가워", "처음"]
        for pattern in greeting_patterns:
            if pattern in message:
                confidence += 0.3
        
        # 감정 표현
        emotion_patterns = ["기분", "좋아", "나빠", "행복", "슬프", "화나", "심심"]
        for pattern in emotion_patterns:
            if pattern in message:
                confidence += 0.2
        
        # 키워드 매칭
        keyword_matches = sum(1 for keyword in self.keywords if keyword in message)
        confidence += min(keyword_matches * 0.1, 0.4)
        
        # 매우 짧은 메시지는 일반 대화일 가능성이 높음
        if len(message) < 10:
            confidence += 0.2
        
        # 기본 신뢰도 (다른 라우터가 처리할 수 없을 때의 fallback)
        confidence = max(confidence, 0.1)
        
        return min(confidence, 1.0)
    
    async def process(self, context: RouterContext) -> RouterResult:
        """일반 대화 처리 로직"""
        try:
            # 다른 라우터로 전환 확인
            next_router = await self.should_switch_router(context)
            if next_router:
                return RouterResult(
                    response=f"{next_router.replace('_', ' ').title()}로 전환합니다. 어떤 도움이 필요하시나요?",
                    action=RouterAction.SWITCH,
                    next_router=next_router,
                    confidence=0.9
                )
            
            # 특별한 패턴 확인
            message = context.current_message.lower()
            
            # 도움말 요청
            if any(word in message for word in ["도움말", "help", "도움", "기능", "사용법"]):
                response = await self._generate_help_response(context)
            # 인사말
            elif any(word in message for word in ["안녕", "hi", "hello", "반가워"]):
                response = await self._generate_greeting_response(context)
            # 감사 인사
            elif any(word in message for word in ["고마워", "감사", "thank"]):
                response = await self._generate_thanks_response(context)
            # 사과
            elif any(word in message for word in ["미안", "죄송", "sorry"]):
                response = await self._generate_apology_response(context)
            # 일반 대화
            else:
                response = await self._generate_general_response(context)
            
            # 결과 반환
            result = RouterResult(
                response=response,
                action=RouterAction.COMPLETE,
                confidence=0.7,
                sources=[],
                metadata={
                    "router_type": "general_chat",
                    "conversation_turn": len(context.conversation_history)
                }
            )
            
            await self.log_interaction(context, result)
            return result
            
        except Exception as e:
            logger.error(f"일반 대화 처리 실패: {str(e)}")
            return RouterResult(
                response="죄송합니다. 대화 처리 중 오류가 발생했습니다. 다시 시도해 주세요.",
                action=RouterAction.ERROR,
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    async def _generate_help_response(self, context: RouterContext) -> str:
        """도움말 응답 생성"""
        prompt = f"""
사용자가 도움말을 요청했습니다. NaruTalk AI Assistant의 주요 기능들을 친근하게 소개해주세요.

주요 기능:
1. 질문답변 - 문서 기반 질문에 답변
2. 문서 검색 - 관련 문서 찾기
3. 직원 정보 조회 - 직원 정보 검색
4. 분석 기능 - 데이터 분석 및 통계
5. 보고서 생성 - 자동 보고서 작성
6. 일반 대화 - 자연스러운 대화

각 기능을 어떻게 사용할 수 있는지 예시와 함께 설명해주세요.
"""
        return await self.generate_openai_response(prompt, context)
    
    async def _generate_greeting_response(self, context: RouterContext) -> str:
        """인사말 응답 생성"""
        prompt = f"""
사용자가 인사를 했습니다. NaruTalk AI Assistant로서 친근하고 따뜻한 인사를 반갑게 해주세요.
사용자의 메시지: {context.current_message}

어떤 도움이 필요한지 물어보고, 간단한 기능 소개도 포함해주세요.
"""
        return await self.generate_openai_response(prompt, context)
    
    async def _generate_thanks_response(self, context: RouterContext) -> str:
        """감사 인사 응답 생성"""
        prompt = f"""
사용자가 감사 인사를 했습니다. 겸손하고 친근하게 답변해주세요.
사용자의 메시지: {context.current_message}

추가로 도움이 필요한 것이 있는지 물어보세요.
"""
        return await self.generate_openai_response(prompt, context)
    
    async def _generate_apology_response(self, context: RouterContext) -> str:
        """사과 응답 생성"""
        prompt = f"""
사용자가 사과를 했습니다. 따뜻하고 이해심 있게 답변해주세요.
사용자의 메시지: {context.current_message}

사과할 필요가 없다는 것을 자연스럽게 전달하고, 도움이 필요하면 언제든 말하라고 하세요.
"""
        return await self.generate_openai_response(prompt, context)
    
    async def _generate_general_response(self, context: RouterContext) -> str:
        """일반 대화 응답 생성"""
        prompt = f"""
사용자와 자연스러운 일반 대화를 나누세요. 
사용자의 메시지: {context.current_message}

친근하고 도움이 되는 AI 어시스턴트로서 대화하되, 
필요시 다른 기능들(질문답변, 문서검색, 직원정보 등)을 활용할 수 있음을 자연스럽게 언급해주세요.
"""
        return await self.generate_openai_response(prompt, context) 