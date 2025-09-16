"""
Intent Analyzer - Step 1 of Supervisor Workflow
의도 분석 및 복잡도 평가
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
import asyncio
import logging
import os

from ..state import QueryAnalyzerState, GlobalSessionState

# Import config if available
try:
    from backend.core import settings
    OPENAI_MODEL = settings.OPENAI_MODEL
except ImportError:
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

logger = logging.getLogger(__name__)


class IntentAnalyzer:
    """사용자 의도를 분석하고 실행 요구사항을 파악하는 에이전트"""

    def __init__(self, llm_provider: str = "openai"):
        """Initialize with LLM provider"""
        if llm_provider == "openai":
            self.llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)  # Using GPT-4o from config
        elif llm_provider == "anthropic":
            self.llm = ChatAnthropic(model="claude-3-opus-20240229", temperature=0)
        else:
            self.llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)  # Default to GPT-4o

    async def analyze_intent(self, query: str, context: Dict[str, Any]) -> QueryAnalyzerState:
        """사용자 의도 분석 메인 메서드"""

        # 병렬로 여러 분석 수행
        analysis_tasks = [
            self._classify_intents(query),
            self._extract_entities(query),
            self._calculate_complexity(query),
            self._check_feasibility(query, context),
            self._identify_ambiguities(query)
        ]

        results = await asyncio.gather(*analysis_tasks)

        intents, entities, complexity, feasibility, ambiguities = results

        # 필요한 에이전트 결정
        suggested_agents = self._determine_required_agents(intents, entities, complexity)

        # 필요한 기능 결정
        required_capabilities = self._determine_capabilities(intents)

        # Context 요구사항 도출
        context_requirements = self._derive_context_requirements(intents, entities)

        # Create state as dictionary (not TypedDict instance)
        analyzer_result = {
            "raw_query": query,
            "query_timestamp": datetime.now().isoformat(),
            "user_context": context,
            "parsed_intents": intents,
            "required_capabilities": required_capabilities,
            "complexity_score": complexity,
            "suggested_agents": suggested_agents,
            "context_requirements": context_requirements,
            "extracted_entities": entities,
            "ambiguities": ambiguities,
            "clarification_needed": len(ambiguities) > 0,
            "feasibility_check": feasibility
        }

        logger.info(f"Intent analysis completed. Complexity: {complexity}, Agents: {suggested_agents}")

        return analyzer_result

    async def _classify_intents(self, query: str) -> List[Dict[str, Any]]:
        """Multi-label intent classification"""

        prompt = f"""사용자 질의를 분석하여 의도를 파악하세요.

사용자 질의: {query}

다음 의도들을 평가하고 각각의 신뢰도(0.0~1.0)를 부여하세요:
1. data_analysis: 데이터 분석, 통계, 실적 조회
2. information_retrieval: 정보 검색, 자료 찾기, 지식 조회
3. document_generation: 문서 작성, 보고서 생성, 양식 작성
4. compliance_check: 규정 검토, 위반 확인, 법규 검증
5. data_storage: 데이터 저장, 기록, 업데이트

JSON 형식으로 응답하세요:
[{{"intent": "의도명", "confidence": 신뢰도, "primary": true/false}}]
"""

        messages = [
            SystemMessage(content="You are an intent classification expert."),
            HumanMessage(content=prompt)
        ]

        response = await self.llm.ainvoke(messages)

        # Parse response and return intents
        try:
            import json
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            intents = json.loads(content)
            return intents
        except:
            # Fallback
            return [{"intent": "data_analysis", "confidence": 0.7, "primary": True}]

    async def _extract_entities(self, query: str) -> List[Dict[str, Any]]:
        """엔티티 추출 및 정규화"""

        prompt = f"""다음 질의에서 중요한 엔티티를 추출하고 정규화하세요.

질의: {query}

추출할 엔티티 타입:
- period: 시간, 기간 (예: 지난달, 이번 분기)
- location: 지역, 장소 (예: 서울, 강남지점)
- metric: 지표, 측정값 (예: 매출, 방문횟수)
- person: 사람, 직책 (예: 김대리, 영업팀장)
- product: 제품, 서비스 (예: 아스피린, MRI)
- department: 부서, 조직 (예: 영업팀, 마케팅부)

JSON 형식으로 응답:
[{{"type": "타입", "value": "원본값", "normalized": "정규화값"}}]
"""

        messages = [
            SystemMessage(content="You are an entity extraction expert."),
            HumanMessage(content=prompt)
        ]

        response = await self.llm.ainvoke(messages)

        try:
            import json
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            entities = json.loads(content)
            return entities
        except:
            return []

    async def _calculate_complexity(self, query: str) -> float:
        """쿼리 복잡도 계산 (0.0 ~ 1.0)"""

        factors = {
            "length": len(query) / 500,  # 길이 기반
            "entities": 0,  # 엔티티 수
            "operations": 0,  # 연산 수
            "conditions": 0  # 조건 수
        }

        # 복잡도 키워드 체크
        complex_keywords = ["그리고", "또한", "비교", "분석", "예측", "추세", "상관관계"]
        for keyword in complex_keywords:
            if keyword in query:
                factors["operations"] += 0.1

        # 조건 키워드 체크
        condition_keywords = ["만약", "경우", "때", "이상", "이하", "사이"]
        for keyword in condition_keywords:
            if keyword in query:
                factors["conditions"] += 0.1

        # 전체 복잡도 계산
        complexity = min(1.0, sum(factors.values()) / len(factors))

        return round(complexity, 2)

    async def _check_feasibility(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """실행 가능성 체크"""

        feasibility = {
            "data_available": True,
            "permission_granted": True,
            "estimated_time": 10,  # seconds
            "resource_status": "available",
            "confidence": 0.9
        }

        # 데이터 가용성 체크
        data_keywords = ["데이터", "정보", "자료", "통계"]
        if any(keyword in query for keyword in data_keywords):
            feasibility["data_available"] = True

        # 권한 체크
        if context.get("user_role") in ["admin", "manager", "analyst"]:
            feasibility["permission_granted"] = True

        # 예상 시간 계산
        complexity = await self._calculate_complexity(query)
        feasibility["estimated_time"] = int(10 + complexity * 50)

        return feasibility

    async def _identify_ambiguities(self, query: str) -> List[Dict[str, Any]]:
        """모호한 부분 식별"""

        ambiguities = []

        # 모호한 시간 표현
        vague_time = ["최근", "얼마전", "예전", "나중"]
        for term in vague_time:
            if term in query:
                ambiguities.append({
                    "type": "temporal",
                    "term": term,
                    "suggestion": "구체적인 기간을 명시해주세요"
                })

        # 모호한 수량 표현
        vague_quantity = ["많은", "적은", "몇몇", "여러"]
        for term in vague_quantity:
            if term in query:
                ambiguities.append({
                    "type": "quantity",
                    "term": term,
                    "suggestion": "구체적인 수량을 명시해주세요"
                })

        return ambiguities

    def _determine_required_agents(
        self,
        intents: List[Dict],
        entities: List[Dict],
        complexity: float
    ) -> List[str]:
        """필요한 에이전트 결정"""

        agent_mapping = {
            "data_analysis": "DataAnalysisAgent",
            "information_retrieval": "InformationRetrievalAgent",
            "document_generation": "DocumentGenerationAgent",
            "compliance_check": "ComplianceValidationAgent",
            "data_storage": "StorageDecisionAgent"
        }

        required_agents = []

        # 의도 기반 매핑
        for intent in intents:
            if intent.get("confidence", 0) > 0.5:
                agent = agent_mapping.get(intent["intent"])
                if agent and agent not in required_agents:
                    required_agents.append(agent)

        # 복잡도 기반 추가
        if complexity > 0.7 and "DataAnalysisAgent" not in required_agents:
            required_agents.append("DataAnalysisAgent")

        # 엔티티 기반 추가
        if len(entities) > 3 and "InformationRetrievalAgent" not in required_agents:
            required_agents.append("InformationRetrievalAgent")

        return required_agents

    def _determine_capabilities(self, intents: List[Dict]) -> List[str]:
        """필요한 기능 결정"""

        capabilities = []

        capability_mapping = {
            "data_analysis": ["sql_query", "data_visualization", "statistics"],
            "information_retrieval": ["vector_search", "keyword_search", "web_search"],
            "document_generation": ["template_processing", "content_generation", "formatting"],
            "compliance_check": ["rule_validation", "risk_assessment"],
            "data_storage": ["schema_mapping", "data_validation"]
        }

        for intent in intents:
            if intent.get("confidence", 0) > 0.5:
                caps = capability_mapping.get(intent["intent"], [])
                for cap in caps:
                    if cap not in capabilities:
                        capabilities.append(cap)

        return capabilities

    def _derive_context_requirements(
        self,
        intents: List[Dict],
        entities: List[Dict]
    ) -> Dict[str, Any]:
        """컨텍스트 요구사항 도출"""

        requirements = {
            "need_auth": False,
            "data_scope": "personal",
            "time_range": None,
            "filters": []
        }

        # 인증 필요 여부
        if any(intent["intent"] in ["compliance_check", "data_storage"]
               for intent in intents if intent.get("confidence", 0) > 0.5):
            requirements["need_auth"] = True

        # 데이터 범위
        if any(entity["type"] == "department" for entity in entities):
            requirements["data_scope"] = "department"
        elif any(entity["type"] == "location" for entity in entities):
            requirements["data_scope"] = "company"

        # 시간 범위
        time_entities = [e for e in entities if e["type"] == "period"]
        if time_entities:
            requirements["time_range"] = time_entities[0].get("normalized")

        # 필터
        for entity in entities:
            if entity["type"] in ["location", "department", "product"]:
                requirements["filters"].append({
                    "field": entity["type"],
                    "value": entity.get("normalized", entity["value"])
                })

        return requirements


async def intent_analyzer_node(state: GlobalSessionState) -> Dict[str, Any]:
    """Intent analyzer node for graph"""

    analyzer = IntentAnalyzer()

    # Get latest message
    if state["messages"]:
        last_message = state["messages"][-1]
        query = last_message.content if hasattr(last_message, 'content') else str(last_message)
    else:
        query = state.get("raw_query", "")

    # Analyze intent
    analyzer_state = await analyzer.analyze_intent(
        query=query,
        context={
            "user_id": state["user_id"],
            "company_id": state["company_id"],
            "session_id": state["session_id"]
        }
    )

    # Return only changes (not entire state)
    return {
        "query_analyzer_state": analyzer_state,
        "current_phase": "planning",
        "audit_trail": [{
            "timestamp": datetime.now().isoformat(),
            "agent": "intent_analyzer",
            "action": "analyzed",
            "complexity": analyzer_state["complexity_score"],
            "suggested_agents": analyzer_state["suggested_agents"]
        }]  # Reducer will append this
    }

    logger.info(f"Intent analysis completed for session {state['session_id']}")