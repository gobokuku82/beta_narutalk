"""
문서검색 에이전트

내부/외부 문서 검색을 전담하는 전문 에이전트입니다.
벡터DB, 정형DB, 비정형DB를 통합하여 최적의 검색 결과를 제공합니다.
"""

from typing import List, Dict, Any, Optional
import logging
from ..base_agent import BaseAgent, AgentContext, AgentResult, AgentAction
from .config import DocumentSearchConfig, default_config
from .database import DocumentSearchDatabase

logger = logging.getLogger(__name__)

class DocumentSearchAgent(BaseAgent):
    """문서검색 전문 에이전트"""
    
    def __init__(self, config: DocumentSearchConfig = None):
        super().__init__("document_search_agent")
        self.config = config or default_config
        self.database = DocumentSearchDatabase(self.config)
        
    def set_services(self, **services):
        """서비스 의존성 주입"""
        super().set_services(**services)
        self.database.set_services(**services)
    
    @property
    def description(self) -> str:
        return "내부/외부 문서 검색을 전담하는 전문 에이전트입니다. 벡터DB, 정형DB, 비정형DB를 통합하여 최적의 검색 결과를 제공합니다."
    
    @property
    def keywords(self) -> List[str]:
        return [
            # 한국어 키워드
            "검색", "찾아", "조회", "탐색", "찾기", "찾아서", "찾아봐", 
            "문서", "자료", "파일", "데이터", "정보", "내용", 
            "내부", "외부", "회사", "사내", "사외",
            "정책", "규정", "절차", "매뉴얼", "가이드", "지침",
            "보고서", "자료집", "문서함", "아카이브",
            
            # 영어 키워드  
            "search", "find", "lookup", "query", "explore",
            "document", "file", "data", "information", "content",
            "internal", "external", "company", "policy", "procedure",
            "manual", "guide", "report", "archive"
        ]
    
    @property
    def priority(self) -> int:
        return 8  # 높은 우선순위 (문서 검색은 핵심 기능)
    
    @property
    def supported_tasks(self) -> List[str]:
        return [
            "document_search",      # 문서 검색
            "internal_search",      # 내부 문서 검색
            "external_search",      # 외부 문서 검색
            "policy_lookup",        # 정책 조회
            "regulation_search",    # 규정 검색
            "manual_search",        # 매뉴얼 검색
            "report_search",        # 보고서 검색
            "archive_search"        # 아카이브 검색
        ]
    
    async def can_handle(self, context: AgentContext) -> float:
        """메시지를 처리할 수 있는지 신뢰도 반환"""
        message = context.current_message.lower()
        confidence = 0.0
        
        # 검색 의도 확인
        search_indicators = ["검색", "찾아", "조회", "search", "find", "lookup"]
        for indicator in search_indicators:
            if indicator in message:
                confidence += 0.4
                break
        
        # 문서 관련 키워드 확인
        document_indicators = ["문서", "자료", "파일", "document", "file", "data"]
        for indicator in document_indicators:
            if indicator in message:
                confidence += 0.3
                break
        
        # 키워드 매칭
        keyword_matches = sum(1 for keyword in self.keywords if keyword in message)
        confidence += min(keyword_matches * 0.05, 0.3)
        
        # 내부/외부 구분 키워드
        scope_indicators = ["내부", "외부", "사내", "사외", "internal", "external"]
        for indicator in scope_indicators:
            if indicator in message:
                confidence += 0.1
                break
        
        # 특정 문서 유형 키워드
        doc_type_indicators = ["정책", "규정", "매뉴얼", "보고서", "policy", "regulation", "manual", "report"]
        for indicator in doc_type_indicators:
            if indicator in message:
                confidence += 0.1
                break
        
        return min(confidence, 1.0)
    
    async def process(self, context: AgentContext) -> AgentResult:
        """문서검색 처리 메인 로직"""
        try:
            # 다른 에이전트로 전환 확인
            next_agent = await self.should_switch_agent(context)
            if next_agent:
                return AgentResult(
                    response=f"{next_agent.replace('_', ' ').title()}로 전환합니다.",
                    action=AgentAction.SWITCH,
                    next_agent=next_agent,
                    confidence=0.9
                )
            
            # 검색 유형 분석
            search_type = await self.analyze_search_type(context)
            search_scope = await self.analyze_search_scope(context)
            
            # 문서 검색 실행
            search_results = await self.execute_search(context, search_type, search_scope)
            
            # 검색 결과 요약 생성
            response = await self.generate_search_response(context, search_results, search_type, search_scope)
            
            # 결과 반환
            result = AgentResult(
                response=response,
                action=AgentAction.COMPLETE,
                confidence=0.9,
                sources=search_results,
                metadata={
                    "agent_type": "document_search",
                    "search_type": search_type,
                    "search_scope": search_scope,
                    "results_count": len(search_results),
                    "query": context.current_message
                }
            )
            
            await self.log_interaction(context, result)
            return result
            
        except Exception as e:
            logger.error(f"문서검색 처리 실패: {str(e)}")
            return AgentResult(
                response="죄송합니다. 문서 검색 중 오류가 발생했습니다. 다시 시도해 주세요.",
                action=AgentAction.ERROR,
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    async def analyze_search_type(self, context: AgentContext) -> str:
        """검색 유형 분석"""
        message = context.current_message.lower()
        
        # 문서 유형별 키워드 매핑
        type_keywords = {
            "policy": ["정책", "policy"],
            "regulation": ["규정", "규칙", "regulation", "rule"],  
            "manual": ["매뉴얼", "가이드", "지침", "manual", "guide"],
            "report": ["보고서", "리포트", "report"],
            "procedure": ["절차", "프로세스", "procedure", "process"],
            "general": ["문서", "자료", "파일", "document", "file"]
        }
        
        for doc_type, keywords in type_keywords.items():
            for keyword in keywords:
                if keyword in message:
                    return doc_type
        
        return "general"
    
    async def analyze_search_scope(self, context: AgentContext) -> str:
        """검색 범위 분석"""
        message = context.current_message.lower()
        
        # 내부 문서 키워드
        internal_keywords = ["내부", "사내", "회사", "internal", "company"]
        for keyword in internal_keywords:
            if keyword in message:
                return "internal"
        
        # 외부 문서 키워드
        external_keywords = ["외부", "사외", "external", "industry", "market"]
        for keyword in external_keywords:
            if keyword in message:
                return "external"
        
        return "all"  # 전체 검색
    
    async def execute_search(self, context: AgentContext, search_type: str, search_scope: str) -> List[Dict[str, Any]]:
        """실제 검색 실행"""
        try:
            query = context.current_message
            
            # 데이터베이스 통합 검색
            results = await self.database.search_all_sources(query, search_scope)
            
            # 검색 유형에 따른 필터링
            if search_type != "general":
                filtered_results = []
                for result in results:
                    metadata = result.get("metadata", {})
                    if (search_type in result.get("content", "").lower() or 
                        search_type in str(metadata).lower()):
                        filtered_results.append(result)
                return filtered_results
            
            return results
            
        except Exception as e:
            logger.error(f"검색 실행 실패: {str(e)}")
            return []
    
    async def generate_search_response(self, context: AgentContext, results: List[Dict[str, Any]], 
                                     search_type: str, search_scope: str) -> str:
        """검색 결과 응답 생성"""
        try:
            if not results:
                return f"'{context.current_message}'에 대한 검색 결과가 없습니다. 다른 키워드로 검색해보시거나, 더 구체적인 검색어를 사용해보세요."
            
            # OpenAI를 사용한 응답 생성
            if self.openai_client:
                prompt = f"""
사용자가 문서 검색을 요청했습니다.

검색 쿼리: {context.current_message}
검색 유형: {search_type}
검색 범위: {search_scope}
검색 결과 개수: {len(results)}개

검색 결과:
{self._format_results_for_prompt(results[:5])}

사용자에게 친근하고 유용한 검색 결과 요약을 제공해주세요. 
각 결과의 핵심 내용을 간략히 설명하고, 사용자가 원하는 정보와의 관련성을 설명해주세요.
추가로 필요한 정보가 있다면 더 구체적인 검색어를 제안해주세요.
"""
                return await self.generate_openai_response(prompt, context)
            
            # 기본 응답 생성
            response = f"'{context.current_message}'에 대한 {len(results)}개의 검색 결과를 찾았습니다.\n\n"
            
            for i, result in enumerate(results[:5], 1):
                content = result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", "")
                score = result.get("final_score", result.get("score", 0.0))
                source = result.get("source", "unknown")
                
                response += f"{i}. [{source}] (관련도: {score:.2f})\n"
                response += f"   {content}\n\n"
            
            if len(results) > 5:
                response += f"(총 {len(results)}개 결과 중 상위 5개를 표시했습니다.)\n"
            
            response += "\n더 구체적인 정보가 필요하시면 더 세부적인 검색어로 다시 검색해보세요."
            
            return response
            
        except Exception as e:
            logger.error(f"검색 응답 생성 실패: {str(e)}")
            return f"검색 결과를 처리하는 중 오류가 발생했습니다: {str(e)}"
    
    def _format_results_for_prompt(self, results: List[Dict[str, Any]]) -> str:
        """OpenAI 프롬프트용 검색 결과 포맷팅"""
        formatted = ""
        for i, result in enumerate(results, 1):
            content = result.get("content", "")[:300]
            score = result.get("final_score", result.get("score", 0.0))
            source = result.get("source", "unknown")
            
            formatted += f"{i}. 출처: {source} (점수: {score:.2f})\n"
            formatted += f"   내용: {content}\n\n"
        
        return formatted
    
    async def get_search_suggestions(self, context: AgentContext) -> List[str]:
        """검색 제안사항 생성"""
        suggestions = []
        
        # 기본 검색 제안
        base_suggestions = [
            "좋은제약 복리후생 정책 검색",
            "좋은제약 윤리강령 조회", 
            "좋은제약 행동강령 찾기",
            "회사 규정 문서 검색",
            "업무 매뉴얼 찾기"
        ]
        
        suggestions.extend(base_suggestions)
        return suggestions
    
    def get_agent_status(self) -> Dict[str, Any]:
        """에이전트 상태 정보"""
        return {
            **self.get_agent_info(),
            "config": {
                "max_results": self.config.max_search_results,
                "confidence_threshold": self.config.confidence_threshold,
                "search_weights": {
                    "vector": self.config.vector_search_weight,
                    "structured": self.config.structured_search_weight,
                    "unstructured": self.config.unstructured_search_weight
                }
            },
            "supported_document_types": self.config.supported_document_types,
            "internal_sources": self.config.internal_document_sources,
            "external_sources": self.config.external_document_sources
        } 