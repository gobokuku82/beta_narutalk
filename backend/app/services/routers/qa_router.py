"""
QA 라우터

문서 기반 질문답변 기능을 담당하는 라우터입니다.
임베딩 검색과 OpenAI GPT-4o를 결합하여 정확한 답변을 제공합니다.
"""

from typing import List, Dict, Any
import logging
from .base_router import BaseRouter, RouterContext, RouterResult, RouterAction

logger = logging.getLogger(__name__)

class QARouter(BaseRouter):
    """질문답변 라우터"""
    
    def __init__(self):
        super().__init__("qa_router")
    
    def get_description(self) -> str:
        return "문서 기반 질문답변 기능을 제공합니다. 사용자의 질문에 대해 관련 문서를 검색하고 정확한 답변을 생성합니다."
    
    def get_keywords(self) -> List[str]:
        return [
            "질문", "답변", "알려줘", "설명", "뭐야", "어떻게", "왜", "무엇", "어디서", "언제",
            "what", "how", "why", "where", "when", "explain", "tell me", "문의", "궁금",
            "정보", "내용", "의미", "정의", "방법", "절차", "과정", "규정", "정책", "가이드"
        ]
    
    def get_priority(self) -> int:
        return 8  # 높은 우선순위
    
    async def can_handle(self, context: RouterContext) -> float:
        """QA 라우터가 메시지를 처리할 수 있는지 확인"""
        message = context.current_message.lower()
        
        # 질문 패턴 확인
        question_patterns = [
            "?", "？", "질문", "답변", "알려줘", "설명", "뭐야", "어떻게", "왜", "무엇", "어디서", "언제"
        ]
        
        confidence = 0.0
        
        # 질문 패턴 매칭
        for pattern in question_patterns:
            if pattern in message:
                confidence += 0.2
        
        # 키워드 매칭
        keyword_matches = sum(1 for keyword in self.keywords if keyword in message)
        confidence += min(keyword_matches * 0.1, 0.5)
        
        # 문장 길이 고려 (긴 문장은 질문일 가능성이 높음)
        if len(message) > 20:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    async def process(self, context: RouterContext) -> RouterResult:
        """QA 처리 로직"""
        try:
            # 다른 라우터로 전환 확인
            next_router = await self.should_switch_router(context)
            if next_router:
                return RouterResult(
                    response=f"{next_router.replace('_', ' ').title()}로 전환합니다.",
                    action=RouterAction.SWITCH,
                    next_router=next_router,
                    confidence=0.9
                )
            
            # 관련 문서 검색
            sources = []
            context_text = ""
            
            if self.embedding_service:
                try:
                    search_results = await self.embedding_service.search_similar_documents(
                        context.current_message, limit=3
                    )
                    
                    if search_results:
                        sources = search_results
                        context_text = "\n".join([result.get("document", "") for result in search_results])
                        logger.info(f"문서 검색 완료: {len(search_results)}개 결과")
                    else:
                        logger.warning("관련 문서를 찾을 수 없음")
                        
                except Exception as e:
                    logger.error(f"문서 검색 실패: {str(e)}")
            
            # OpenAI GPT-4o를 사용하여 답변 생성
            prompt = f"""
다음은 사용자의 질문에 답하기 위한 관련 문서입니다:

{context_text if context_text else "관련 문서가 없습니다."}

사용자 질문: {context.current_message}

위 문서를 바탕으로 사용자의 질문에 대해 정확하고 도움이 되는 답변을 제공하세요.
만약 관련 문서가 없거나 불충분하다면, 일반적인 지식을 바탕으로 도움이 되는 답변을 제공하세요.

답변 조건:
1. 한국어로 답변하세요
2. 명확하고 구체적으로 답변하세요
3. 가능한 경우 단계별로 설명하세요
4. 친근하고 도움이 되는 톤으로 답변하세요
"""
            
            response = await self.generate_openai_response(prompt, context)
            
            # 결과 반환
            result = RouterResult(
                response=response,
                action=RouterAction.COMPLETE,
                confidence=0.9,
                sources=sources,
                metadata={
                    "documents_found": len(sources),
                    "router_type": "qa",
                    "has_context": bool(context_text)
                }
            )
            
            await self.log_interaction(context, result)
            return result
            
        except Exception as e:
            logger.error(f"QA 처리 실패: {str(e)}")
            return RouterResult(
                response="죄송합니다. 질문 처리 중 오류가 발생했습니다. 다시 시도해 주세요.",
                action=RouterAction.ERROR,
                confidence=0.0,
                metadata={"error": str(e)}
            ) 