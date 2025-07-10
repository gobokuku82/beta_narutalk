"""
문서 검색 라우터

문서 검색 기능을 전담하는 라우터입니다.
임베딩 검색을 통해 관련 문서를 찾고 결과를 제공합니다.
"""

from typing import List, Dict, Any
import logging
from .base_router import BaseRouter, RouterContext, RouterResult, RouterAction

logger = logging.getLogger(__name__)

class DocumentSearchRouter(BaseRouter):
    """문서 검색 라우터"""
    
    def __init__(self):
        super().__init__("document_search_router")
    
    def get_description(self) -> str:
        return "문서 검색 기능을 제공합니다. 키워드나 내용을 기반으로 관련 문서를 찾아서 제공합니다."
    
    def get_keywords(self) -> List[str]:
        return [
            "검색", "찾아", "문서", "자료", "파일", "search", "find", "document", "file",
            "데이터", "정보", "내용", "자료실", "문서함", "아카이브", "기록", "문헌",
            "참고", "레퍼런스", "reference", "lookup", "조회", "확인", "리서치"
        ]
    
    def get_priority(self) -> int:
        return 7  # 높은 우선순위
    
    async def can_handle(self, context: RouterContext) -> float:
        """문서 검색 라우터가 메시지를 처리할 수 있는지 확인"""
        message = context.current_message.lower()
        
        confidence = 0.0
        
        # 검색 관련 키워드 확인
        search_patterns = ["검색", "찾아", "find", "search", "lookup", "조회"]
        for pattern in search_patterns:
            if pattern in message:
                confidence += 0.3
        
        # 문서 관련 키워드 확인
        document_patterns = ["문서", "자료", "파일", "document", "file", "데이터"]
        for pattern in document_patterns:
            if pattern in message:
                confidence += 0.2
        
        # 키워드 매칭
        keyword_matches = sum(1 for keyword in self.keywords if keyword in message)
        confidence += min(keyword_matches * 0.1, 0.4)
        
        return min(confidence, 1.0)
    
    async def process(self, context: RouterContext) -> RouterResult:
        """문서 검색 처리 로직"""
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
            
            # 문서 검색 실행
            sources = []
            if self.embedding_service:
                try:
                    search_results = await self.embedding_service.search_similar_documents(
                        context.current_message, limit=5
                    )
                    sources = search_results
                    logger.info(f"문서 검색 완료: {len(search_results)}개 결과")
                except Exception as e:
                    logger.error(f"문서 검색 실패: {str(e)}")
            
            # 검색 결과 요약 생성
            if sources:
                prompt = f"""
문서 검색 결과를 사용자에게 친근하게 제공해주세요.

검색 키워드: {context.current_message}
검색 결과 개수: {len(sources)}개

각 문서의 주요 내용을 간략히 요약하고, 사용자가 원하는 정보와 관련성을 설명해주세요.
사용자가 더 자세한 정보를 원한다면 질문답변 기능을 사용할 수 있음을 안내해주세요.
"""
                response = await self.generate_openai_response(prompt, context)
            else:
                response = "검색 결과가 없습니다. 다른 키워드로 검색해보시거나, 더 구체적인 검색어를 사용해보세요."
            
            # 결과 반환
            result = RouterResult(
                response=response,
                action=RouterAction.COMPLETE,
                confidence=0.9,
                sources=sources,
                metadata={
                    "documents_found": len(sources),
                    "router_type": "document_search",
                    "search_query": context.current_message
                }
            )
            
            await self.log_interaction(context, result)
            return result
            
        except Exception as e:
            logger.error(f"문서 검색 처리 실패: {str(e)}")
            return RouterResult(
                response="죄송합니다. 문서 검색 중 오류가 발생했습니다. 다시 시도해 주세요.",
                action=RouterAction.ERROR,
                confidence=0.0,
                metadata={"error": str(e)}
            ) 