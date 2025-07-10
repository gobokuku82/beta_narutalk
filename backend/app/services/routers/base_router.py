"""
기본 라우터 클래스

모든 라우터가 상속받아야 하는 기본 클래스입니다.
라우터 간 이동, 상태 관리, 공통 기능을 제공합니다.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class RouterAction(Enum):
    """라우터 액션 타입"""
    CONTINUE = "continue"
    SWITCH = "switch"
    COMPLETE = "complete"
    ERROR = "error"

@dataclass
class RouterResult:
    """라우터 처리 결과"""
    response: str
    action: RouterAction
    next_router: Optional[str] = None
    confidence: float = 0.0
    sources: List[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.sources is None:
            self.sources = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class RouterContext:
    """라우터 컨텍스트 정보"""
    current_message: str
    user_id: str
    session_id: str
    conversation_history: List[Dict[str, str]]
    current_router: str
    router_switches: int
    user_preferences: Dict[str, Any]
    
    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []
        if self.user_preferences is None:
            self.user_preferences = {}

class BaseRouter(ABC):
    """기본 라우터 클래스"""
    
    def __init__(self, router_name: str):
        self.router_name = router_name
        self.description = self.get_description()
        self.keywords = self.get_keywords()
        self.priority = self.get_priority()
        self.openai_client = None
        self.embedding_service = None
        self.database_service = None
        logger.info(f"라우터 초기화 완료: {self.router_name}")
    
    @abstractmethod
    def get_description(self) -> str:
        """라우터 설명을 반환합니다."""
        pass
    
    @abstractmethod
    def get_keywords(self) -> List[str]:
        """라우터가 반응할 키워드들을 반환합니다."""
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """라우터 우선순위를 반환합니다. (높을수록 우선)"""
        pass
    
    @abstractmethod
    async def can_handle(self, context: RouterContext) -> float:
        """
        이 라우터가 현재 메시지를 처리할 수 있는지 신뢰도를 반환합니다.
        
        Args:
            context: 라우터 컨텍스트
            
        Returns:
            float: 0.0 ~ 1.0 사이의 신뢰도
        """
        pass
    
    @abstractmethod
    async def process(self, context: RouterContext) -> RouterResult:
        """
        메시지를 처리하고 결과를 반환합니다.
        
        Args:
            context: 라우터 컨텍스트
            
        Returns:
            RouterResult: 처리 결과
        """
        pass
    
    def set_services(self, openai_client=None, embedding_service=None, database_service=None):
        """외부 서비스들을 설정합니다."""
        self.openai_client = openai_client
        self.embedding_service = embedding_service
        self.database_service = database_service
    
    async def should_switch_router(self, context: RouterContext) -> Optional[str]:
        """
        다른 라우터로 전환해야 하는지 확인합니다.
        
        Args:
            context: 라우터 컨텍스트
            
        Returns:
            Optional[str]: 전환할 라우터 이름 또는 None
        """
        message = context.current_message.lower()
        
        # 명시적인 라우터 전환 요청 확인
        switch_patterns = {
            "qa_router": ["질문", "답변", "알려줘", "설명"],
            "document_search_router": ["검색", "찾아", "문서", "자료"],
            "employee_info_router": ["직원", "사원", "동료", "부서"],
            "analysis_router": ["분석", "통계", "리포트", "데이터"],
            "report_generator_router": ["보고서", "리포트", "문서 생성"],
            "general_chat_router": ["대화", "채팅", "안녕", "도움말"]
        }
        
        for router_name, patterns in switch_patterns.items():
            if router_name != self.router_name:
                if any(pattern in message for pattern in patterns):
                    return router_name
        
        return None
    
    async def generate_openai_response(self, prompt: str, context: RouterContext) -> str:
        """OpenAI GPT-4o를 사용하여 응답을 생성합니다."""
        if not self.openai_client:
            return "OpenAI 클라이언트가 설정되지 않았습니다."
        
        try:
            # 컨텍스트 정보를 포함한 프롬프트 생성
            full_prompt = f"""
당신은 NaruTalk AI Assistant입니다. 사용자의 질문에 한국어로 친근하고 도움이 되는 답변을 제공하세요.

현재 라우터: {self.router_name}
사용자 메시지: {context.current_message}

{prompt}

답변은 명확하고 정확하며 도움이 되도록 작성하세요.
"""
            
            response = await self.openai_client.chat.completions.acreate(
                model="gpt-4o",
                messages=[{"role": "user", "content": full_prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI 응답 생성 실패: {str(e)}")
            return f"응답 생성 중 오류가 발생했습니다: {str(e)}"
    
    async def log_interaction(self, context: RouterContext, result: RouterResult):
        """라우터 상호작용을 로깅합니다."""
        logger.info(f"""
라우터 처리 완료:
- 라우터: {self.router_name}
- 사용자: {context.user_id}
- 세션: {context.session_id}
- 메시지: {context.current_message[:100]}...
- 액션: {result.action}
- 신뢰도: {result.confidence}
- 다음 라우터: {result.next_router}
        """)
    
    def __str__(self) -> str:
        return f"Router({self.router_name})"
    
    def __repr__(self) -> str:
        return f"Router(name='{self.router_name}', priority={self.priority})" 