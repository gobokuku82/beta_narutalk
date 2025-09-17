"""
Enhanced Intent Analyzer with Context Engineering
컨텍스트 기반 의도 분석기
"""

from typing import Dict, Any, List, Optional, Tuple
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import asyncio
import logging
from datetime import datetime

from .context_manager import ContextManager, MedicalContext
from .state import IntentAnalysisState, MedicalSupervisorState

logger = logging.getLogger(__name__)


class IntentClassification(BaseModel):
    """의도 분류 결과"""
    
    primary_intent: str = Field(description="주요 의도")
    confidence: float = Field(description="신뢰도 (0.0-1.0)")
    secondary_intents: List[Dict[str, float]] = Field(
        description="보조 의도들",
        default_factory=list
    )
    
class EntityExtraction(BaseModel):
    """엔티티 추출 결과"""
    
    entities: List[Dict[str, Any]] = Field(
        description="추출된 엔티티들",
        default_factory=list
    )
    time_expressions: List[str] = Field(
        description="시간 관련 표현",
        default_factory=list
    )
    target_names: List[str] = Field(
        description="대상 이름들 (병원, 거래처 등)",
        default_factory=list
    )

class QueryComplexity(BaseModel):
    """쿼리 복잡도 평가"""
    
    complexity_score: float = Field(description="복잡도 점수 (0.0-1.0)")
    factors: Dict[str, float] = Field(
        description="복잡도 요소별 점수",
        default_factory=dict
    )
    estimated_steps: int = Field(description="예상 처리 단계")
    recommended_approach: str = Field(
        description="권장 처리 방식",
        default="single_agent"
    )


class EnhancedIntentAnalyzer:
    """
    향상된 의도 분석기
    - 컨텍스트 기반 분석
    - 병렬 처리
    - 정확한 도메인 매핑
    """
    
    def __init__(self, llm_provider: str = "openai", model_name: Optional[str] = None):
        """Initialize Intent Analyzer"""
        
        if llm_provider == "openai":
            self.llm = ChatOpenAI(
                model=model_name or "gpt-4o",
                temperature=0.1
            )
        elif llm_provider == "anthropic":
            self.llm = ChatAnthropic(
                model=model_name or "claude-3-opus-20240229",
                temperature=0.1
            )
        else:
            self.llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
        
        self.context_manager = ContextManager()
        
        # Output parsers
        self.intent_parser = PydanticOutputParser(pydantic_object=IntentClassification)
        self.entity_parser = PydanticOutputParser(pydantic_object=EntityExtraction)
        self.complexity_parser = PydanticOutputParser(pydantic_object=QueryComplexity)
    
    async def analyze(
        self,
        query: str,
        user_context: Dict[str, Any],
        conversation_history: Optional[List[Dict]] = None
    ) -> IntentAnalysisState:
        """
        메인 분석 메서드
        병렬로 여러 분석 수행
        """
        
        # 병렬 분석 작업
        analysis_tasks = [
            self._classify_intent_with_context(query, user_context),
            self._extract_entities_medical(query),
            self._evaluate_complexity(query, conversation_history),
            self._identify_required_capabilities(query),
            self._detect_ambiguities(query)
        ]
        
        results = await asyncio.gather(*analysis_tasks)
        
        (
            intent_result,
            entity_result,
            complexity_result,
            capabilities,
            ambiguities
        ) = results
        
        # 시간 범위 정규화
        time_range = self._normalize_time_range(entity_result.time_expressions)
        
        # 결과 조합
        analysis_state = IntentAnalysisState(
            raw_query=query,
            analyzed_intents=self._format_intents(intent_result),
            entities=entity_result.entities,
            time_range=time_range,
            target_entities=entity_result.target_names,
            required_capabilities=capabilities,
            ambiguities=ambiguities,
            clarification_needed=len(ambiguities) > 0,
            complexity_score=complexity_result.complexity_score,
            domain_type=self._determine_domain(intent_result.primary_intent)
        )
        
        logger.info(
            f"Intent analysis complete: {intent_result.primary_intent} "
            f"(confidence: {intent_result.confidence:.2f}, "
            f"complexity: {complexity_result.complexity_score:.2f})"
        )
        
        return analysis_state
    
    async def _classify_intent_with_context(
        self,
        query: str,
        user_context: Dict[str, Any]
    ) -> IntentClassification:
        """
        컨텍스트를 활용한 의도 분류
        """
        
        system_prompt = """당신은 의료/제약 도메인 쿼리 분석 전문가입니다.
        
        사용자 쿼리를 분석하여 다음 의도 중 하나 이상을 식별하세요:
        
        1. 실적분석 - 직원 실적, 거래처 트렌드, 매출 분석
        2. 정보검색 - 인사정보, 규정, 웹정보, 논문, HiRA 데이터
        3. 문서생성 - 보고서 작성, 신청서 작성, DB 저장
        4. 규정검토 - 법규 위반 확인, 규정 준수 검증
        
        사용자 역할과 부서를 고려하여 의도를 파악하세요.
        
        {format_instructions}
        """
        
        user_prompt = f"""
        사용자 정보:
        - 역할: {user_context.get('role', '영업사원')}
        - 부서: {user_context.get('department', '미지정')}
        - 지역: {user_context.get('region', '전국')}
        
        쿼리: {query}
        """
        
        messages = [
            SystemMessage(content=system_prompt.format(
                format_instructions=self.intent_parser.get_format_instructions()
            )),
            HumanMessage(content=user_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            return self.intent_parser.parse(response.content)
        except:
            # Fallback
            return IntentClassification(
                primary_intent="정보검색",
                confidence=0.5,
                secondary_intents=[]
            )
    
    async def _extract_entities_medical(self, query: str) -> EntityExtraction:
        """
        의료 도메인 특화 엔티티 추출
        """
        
        system_prompt = """의료/제약 도메인 엔티티를 추출하세요.
        
        추출할 엔티티 타입:
        - hospital: 병원, 의원, 클리닉
        - pharmacy: 약국
        - product: 의약품, 제품
        - person: 직원, 담당자
        - department: 부서, 팀
        - date: 날짜, 기간
        - regulation: 법규, 규정
        - metric: 지표, 수치
        
        {format_instructions}
        """
        
        messages = [
            SystemMessage(content=system_prompt.format(
                format_instructions=self.entity_parser.get_format_instructions()
            )),
            HumanMessage(content=f"쿼리: {query}")
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            return self.entity_parser.parse(response.content)
        except:
            return EntityExtraction(entities=[], time_expressions=[], target_names=[])
    
    async def _evaluate_complexity(
        self,
        query: str,
        conversation_history: Optional[List[Dict]]
    ) -> QueryComplexity:
        """
        쿼리 복잡도 평가
        """
        
        system_prompt = """쿼리의 복잡도를 평가하세요.
        
        복잡도 요소:
        1. 데이터 요구사항 (0.0-0.3): 필요한 데이터 소스 수
        2. 처리 단계 (0.0-0.3): 필요한 처리 단계 수
        3. 규정 검토 (0.0-0.2): 규정 확인 필요 여부
        4. 통합 요구사항 (0.0-0.2): 여러 결과 통합 필요
        
        권장 처리 방식:
        - single_agent: 단일 에이전트로 충분 (복잡도 < 0.3)
        - sequential: 순차적 멀티 에이전트 (0.3 <= 복잡도 < 0.7)
        - parallel: 병렬 멀티 에이전트 (복잡도 >= 0.7)
        
        {format_instructions}
        """
        
        context = ""
        if conversation_history:
            context = f"\n이전 대화: {len(conversation_history)}개 메시지"
        
        messages = [
            SystemMessage(content=system_prompt.format(
                format_instructions=self.complexity_parser.get_format_instructions()
            )),
            HumanMessage(content=f"쿼리: {query}{context}")
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            return self.complexity_parser.parse(response.content)
        except:
            # 기본 복잡도 계산
            complexity = len(query) / 200  # 길이 기반
            return QueryComplexity(
                complexity_score=min(complexity, 1.0),
                factors={},
                estimated_steps=1,
                recommended_approach="single_agent"
            )
    
    async def _identify_required_capabilities(self, query: str) -> List[str]:
        """
        필요한 기능 식별
        """
        
        capabilities = []
        query_lower = query.lower()
        
        # 데이터 분석 기능
        if any(word in query_lower for word in ["실적", "매출", "트렌드", "분석", "통계"]):
            capabilities.extend(["sql_query", "data_aggregation", "trend_analysis"])
        
        # 정보 검색 기능
        if any(word in query_lower for word in ["검색", "찾", "조회", "확인"]):
            capabilities.extend(["search", "retrieval", "filtering"])
        
        # 문서 생성 기능
        if any(word in query_lower for word in ["작성", "생성", "만들", "보고서"]):
            capabilities.extend(["document_generation", "template_processing", "formatting"])
        
        # 규정 검토 기능
        if any(word in query_lower for word in ["규정", "위반", "법규", "검토"]):
            capabilities.extend(["compliance_check", "regulation_validation"])
        
        # DB 저장 기능
        if any(word in query_lower for word in ["저장", "기록", "업데이트"]):
            capabilities.extend(["data_storage", "db_write"])
        
        # 웹 검색 기능
        if any(word in query_lower for word in ["네이버", "구글", "웹", "온라인"]):
            capabilities.extend(["web_search", "api_integration"])
        
        return list(set(capabilities))  # 중복 제거
    
    async def _detect_ambiguities(self, query: str) -> List[Dict[str, Any]]:
        """
        모호성 감지
        """
        
        ambiguities = []
        
        # 모호한 시간 표현
        vague_time_terms = {
            "최근": "구체적인 기간을 명시해주세요 (예: 지난 1주일)",
            "얼마전": "정확한 날짜나 기간을 알려주세요",
            "예전": "대략적인 시기를 명시해주세요",
            "나중": "언제를 의미하는지 명확히 해주세요"
        }
        
        for term, suggestion in vague_time_terms.items():
            if term in query:
                ambiguities.append({
                    "type": "temporal",
                    "term": term,
                    "suggestion": suggestion,
                    "severity": "medium"
                })
        
        # 모호한 대상
        if "그것" in query or "그거" in query:
            ambiguities.append({
                "type": "reference",
                "term": "그것/그거",
                "suggestion": "구체적인 대상을 명시해주세요",
                "severity": "high"
            })
        
        # 모호한 수량
        vague_quantities = {
            "많은": "구체적인 수량이나 비율을 명시해주세요",
            "적은": "구체적인 수량이나 기준을 알려주세요",
            "몇몇": "정확한 개수를 명시해주세요"
        }
        
        for term, suggestion in vague_quantities.items():
            if term in query:
                ambiguities.append({
                    "type": "quantity",
                    "term": term,
                    "suggestion": suggestion,
                    "severity": "low"
                })
        
        return ambiguities
    
    def _format_intents(self, intent_result: IntentClassification) -> List[Dict[str, float]]:
        """
        의도 결과 포맷팅
        """
        
        intents = [{
            "intent": intent_result.primary_intent,
            "confidence": intent_result.confidence,
            "primary": True
        }]
        
        for secondary in intent_result.secondary_intents:
            intents.append({
                "intent": secondary.get("intent", "unknown"),
                "confidence": secondary.get("confidence", 0.0),
                "primary": False
            })
        
        return intents
    
    def _normalize_time_range(self, time_expressions: List[str]) -> Optional[Dict[str, str]]:
        """
        시간 표현 정규화
        """
        
        if not time_expressions:
            return None
        
        from datetime import datetime, timedelta
        import re
        
        today = datetime.now()
        
        for expr in time_expressions:
            expr_lower = expr.lower()
            
            # 상대적 시간 표현
            if "지난달" in expr_lower or "지난 달" in expr_lower:
                last_month = today.replace(day=1) - timedelta(days=1)
                return {
                    "start": last_month.replace(day=1).strftime("%Y-%m-%d"),
                    "end": last_month.strftime("%Y-%m-%d")
                }
            
            elif "이번달" in expr_lower or "이번 달" in expr_lower:
                return {
                    "start": today.replace(day=1).strftime("%Y-%m-%d"),
                    "end": today.strftime("%Y-%m-%d")
                }
            
            elif "올해" in expr_lower:
                return {
                    "start": f"{today.year}-01-01",
                    "end": today.strftime("%Y-%m-%d")
                }
            
            # 절대적 날짜 패턴
            date_pattern = r'(\d{4})[-.년](\d{1,2})[-.월](\d{1,2})'
            match = re.search(date_pattern, expr)
            if match:
                year, month, day = match.groups()
                return {
                    "start": f"{year}-{month:0>2}-{day:0>2}",
                    "end": f"{year}-{month:0>2}-{day:0>2}"
                }
        
        return None
    
    def _determine_domain(self, primary_intent: str) -> str:
        """
        주요 의도에서 도메인 타입 결정
        """
        
        intent_to_domain = {
            "실적분석": "실적분석",
            "정보검색": "정보검색",
            "문서생성": "문서생성",
            "규정검토": "규정검토",
            "데이터분석": "실적분석",
            "보고서작성": "문서생성",
            "규정확인": "규정검토"
        }
        
        return intent_to_domain.get(primary_intent, "정보검색")


async def intent_analyzer_node(state: MedicalSupervisorState) -> Dict[str, Any]:
    """
    Graph node for intent analysis
    """
    
    analyzer = EnhancedIntentAnalyzer()
    
    # 최신 메시지 추출
    if state["messages"]:
        last_message = state["messages"][-1]
        query = last_message.content if hasattr(last_message, 'content') else str(last_message)
    else:
        query = ""
    
    # 사용자 컨텍스트 구성
    user_context = {
        "user_id": state["user_id"],
        "session_id": state["session_id"],
        "role": state.get("context", {}).get("user_role", "영업사원"),
        "department": state.get("context", {}).get("department", "미지정"),
        "region": state.get("context", {}).get("region", "전국")
    }
    
    # 대화 히스토리
    conversation_history = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": msg.content}
        for i, msg in enumerate(state["messages"][:-1])
        if hasattr(msg, 'content')
    ]
    
    # 의도 분석 수행
    intent_state = await analyzer.analyze(query, user_context, conversation_history)
    
    # 상태 업데이트
    return {
        "intent_analysis": intent_state,
        "domain_type": intent_state["domain_type"],
        "complexity_score": intent_state["complexity_score"],
        "current_phase": "planning"
    }
