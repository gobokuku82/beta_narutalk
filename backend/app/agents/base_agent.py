"""
베이스 에이전트 클래스

모든 전문 에이전트가 상속받는 기본 클래스입니다.
벡터DB, 정형DB, 비정형DB와의 연동을 제공합니다.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class AgentAction(Enum):
    """에이전트 액션 타입"""
    COMPLETE = "complete"       # 처리 완료
    SWITCH = "switch"          # 다른 에이전트로 전환
    CONTINUE = "continue"      # 계속 처리
    ERROR = "error"           # 오류 발생

@dataclass
class AgentContext:
    """에이전트 처리 컨텍스트"""
    current_message: str
    user_id: str
    session_id: str
    conversation_history: List[Dict[str, str]]
    current_agent: str
    agent_switches: int
    user_preferences: Dict[str, Any]
    task_type: str = ""        # 작업 유형 (검색, 작성, 분석 등)
    target_data: str = ""      # 대상 데이터 (내부문서, 외부문서, 실적데이터 등)

@dataclass 
class AgentResult:
    """에이전트 처리 결과"""
    response: str
    action: AgentAction = AgentAction.COMPLETE
    confidence: float = 0.0
    sources: List[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    next_agent: Optional[str] = None
    
    def __post_init__(self):
        if self.sources is None:
            self.sources = []
        if self.metadata is None:
            self.metadata = {}

class BaseAgent(ABC):
    """모든 전문 에이전트의 기본 클래스"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.agent_id = agent_name
        
        # 서비스 인스턴스들 (의존성 주입)
        self.openai_client = None
        self.embedding_service = None
        self.database_service = None
        self.vector_db = None
        self.structured_db = None
        self.unstructured_db = None
        
        logger.info(f"{self.agent_name} 에이전트 초기화")
    
    def set_services(self, **services):
        """서비스 의존성 주입"""
        self.openai_client = services.get('openai_client')
        self.embedding_service = services.get('embedding_service')
        self.database_service = services.get('database_service')
        self.vector_db = services.get('vector_db')
        self.structured_db = services.get('structured_db')
        self.unstructured_db = services.get('unstructured_db')
        
        logger.info(f"{self.agent_name} 에이전트 서비스 설정 완료")
    
    @property
    @abstractmethod
    def description(self) -> str:
        """에이전트 설명"""
        pass
    
    @property
    @abstractmethod
    def keywords(self) -> List[str]:
        """에이전트 키워드"""
        pass
    
    @property
    @abstractmethod
    def priority(self) -> int:
        """에이전트 우선순위 (1-10, 높을수록 우선)"""
        pass
    
    @property
    @abstractmethod
    def supported_tasks(self) -> List[str]:
        """지원하는 작업 유형들"""
        pass
    
    @abstractmethod
    async def can_handle(self, context: AgentContext) -> float:
        """
        메시지를 처리할 수 있는지 신뢰도 반환 (0.0~1.0)
        
        Args:
            context: 에이전트 컨텍스트
            
        Returns:
            신뢰도 점수
        """
        pass
    
    @abstractmethod
    async def process(self, context: AgentContext) -> AgentResult:
        """
        메시지 처리 메인 로직
        
        Args:
            context: 에이전트 컨텍스트
            
        Returns:
            처리 결과
        """
        pass
    
    async def should_switch_agent(self, context: AgentContext) -> Optional[str]:
        """다른 에이전트로 전환해야 하는지 확인"""
        message = context.current_message.lower()
        
        # 다른 에이전트 키워드 확인
        agent_keywords = {
            "document_search_agent": ["검색", "찾아", "조회", "문서", "자료"],
            "document_draft_agent": ["작성", "초안", "문서", "보고서", "계획서"],
            "performance_analysis_agent": ["실적", "성과", "분석", "매출", "수익"],
            "client_analysis_agent": ["거래처", "고객", "파트너", "클라이언트", "업체"]
        }
        
        for agent_name, keywords_list in agent_keywords.items():
            if agent_name != self.agent_name:
                for keyword in keywords_list:
                    if keyword in message:
                        return agent_name
        
        return None
    
    async def search_vector_db(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """벡터 데이터베이스 검색"""
        try:
            if self.embedding_service:
                # 문서 목록 가져오기
                documents = await self.get_searchable_documents()
                if documents:
                    results = await self.embedding_service.search_similar_documents(
                        query, documents, limit
                    )
                    return results
            return []
        except Exception as e:
            logger.error(f"벡터DB 검색 실패: {str(e)}")
            return []
    
    async def search_structured_db(self, query: str, table: str = None) -> List[Dict[str, Any]]:
        """정형 데이터베이스 검색"""
        try:
            if self.database_service:
                # 테이블별 검색 로직 구현
                if table == "employees":
                    result = await self.database_service.search_employee_info(query)
                    if result:
                        return [{"data": result, "source": "employees_db"}]
                elif table == "performance":
                    # 실적 데이터 검색 (향후 구현)
                    return [{"data": f"실적 데이터: {query}", "source": "performance_db"}]
                elif table == "clients":
                    # 거래처 데이터 검색 (향후 구현)
                    return [{"data": f"거래처 데이터: {query}", "source": "clients_db"}]
            return []
        except Exception as e:
            logger.error(f"정형DB 검색 실패: {str(e)}")
            return []
    
    async def search_unstructured_db(self, query: str, data_type: str = None) -> List[Dict[str, Any]]:
        """비정형 데이터베이스 검색"""
        try:
            if self.database_service:
                # 비정형 데이터 검색 (문서, 이미지, 음성 등)
                documents = await self.database_service.get_company_documents()
                filtered_docs = []
                
                for doc in documents:
                    if query.lower() in doc.lower():
                        filtered_docs.append({
                            "content": doc,
                            "source": "unstructured_db",
                            "type": data_type or "document"
                        })
                
                return filtered_docs[:5]  # 최대 5개
            return []
        except Exception as e:
            logger.error(f"비정형DB 검색 실패: {str(e)}")
            return []
    
    async def get_searchable_documents(self) -> List[str]:
        """검색 가능한 문서 목록 가져오기"""
        try:
            if self.database_service:
                return await self.database_service.get_company_documents()
            return []
        except Exception as e:
            logger.error(f"문서 목록 조회 실패: {str(e)}")
            return []
    
    async def generate_openai_response(self, prompt: str, context: AgentContext) -> str:
        """OpenAI를 사용한 응답 생성"""
        try:
            if not self.openai_client:
                return f"OpenAI 서비스가 설정되지 않았습니다. {self.agent_name}가 기본 응답을 제공합니다."
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"당신은 {self.description}입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI 응답 생성 실패: {str(e)}")
            return f"죄송합니다. {self.agent_name} 처리 중 오류가 발생했습니다."
    
    async def log_interaction(self, context: AgentContext, result: AgentResult):
        """상호작용 로그 기록"""
        try:
            log_data = {
                "agent": self.agent_name,
                "user_id": context.user_id,
                "session_id": context.session_id,
                "message": context.current_message,
                "response": result.response,
                "confidence": result.confidence,
                "action": result.action.value
            }
            logger.info(f"에이전트 상호작용 로그: {log_data}")
        except Exception as e:
            logger.error(f"상호작용 로그 기록 실패: {str(e)}")
    
    def get_agent_info(self) -> Dict[str, Any]:
        """에이전트 정보 반환"""
        return {
            "name": self.agent_name,
            "description": self.description,
            "keywords": self.keywords,
            "priority": self.priority,
            "supported_tasks": self.supported_tasks,
            "services_available": {
                "openai": bool(self.openai_client),
                "embedding": bool(self.embedding_service),
                "database": bool(self.database_service)
            }
        } 