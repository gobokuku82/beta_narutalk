from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict, Any, Optional
import json
import logging
from ..utils import LLMManager, PromptTemplates

logger = logging.getLogger(__name__)

class IntentAnalysisState(TypedDict):
    user_query: str
    tokens: List[str]
    entities: List[Dict]
    intents: List[Dict]
    confidence_scores: Dict[str, float]
    ambiguous: bool

class IntentAnalysisSubGraph:
    def __init__(self):
        self.workflow = StateGraph(IntentAnalysisState)
        self.llm_manager = LLMManager()
        self.prompt_templates = PromptTemplates()
        self._build_graph()
    
    def _build_graph(self):
        # 노드 추가
        self.workflow.add_node("tokenize", self.tokenize_query)
        self.workflow.add_node("extract_entities", self.extract_entities)
        self.workflow.add_node("classify_intent", self.classify_intent)
        self.workflow.add_node("validate_intent", self.validate_intent)
        self.workflow.add_node("resolve_ambiguity", self.resolve_ambiguity)
        
        # 엔트리 포인트 정의 (LangGraph 0.6.7 방식)
        self.workflow.add_edge(START, "tokenize")
        self.workflow.add_edge("tokenize", "extract_entities")
        self.workflow.add_edge("extract_entities", "classify_intent")
        self.workflow.add_edge("classify_intent", "validate_intent")
        
        self.workflow.add_conditional_edges(
            "validate_intent",
            self.check_ambiguity,
            {
                "clear": END,
                "ambiguous": "resolve_ambiguity"
            }
        )
        self.workflow.add_edge("resolve_ambiguity", END)
    
    async def classify_intent(self, state: IntentAnalysisState):
        """다중 의도 분류 가능"""
        try:
            # 프롬프트 생성
            prompt = self.prompt_templates.get_prompt(
                category="intent_analysis",
                version="v1",
                user_query=state['user_query']
            )

            # LLM 호출
            response = await self.llm_manager.generate(
                prompt=prompt,
                model="openai_mini",  # 빠른 응답을 위해 mini 모델 사용
                category="intent_analysis",
                temperature=0.3  # 일관된 분류를 위해 낮은 temperature
            )

            # 응답 파싱
            try:
                result = json.loads(response['content'])
                state["intents"] = result.get("intents", [])
                state["ambiguous"] = result.get("ambiguous", False)

                # 신뢰도 점수 추출
                confidence_scores = {}
                for intent in state["intents"]:
                    confidence_scores[intent["type"]] = intent.get("confidence", 0.0)
                state["confidence_scores"] = confidence_scores

                # 엔티티 업데이트
                if "entities" in result:
                    state["entities"] = result["entities"]

                logger.info(f"Classified intents: {[i['type'] for i in state['intents']]}")

            except json.JSONDecodeError:
                # JSON 파싱 실패 시 기본값
                logger.error("Failed to parse LLM response as JSON")
                state["intents"] = [{
                    "type": "general_query",
                    "confidence": 0.5
                }]
                state["confidence_scores"] = {"general_query": 0.5}
                state["ambiguous"] = True

        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            # 에러 발생 시 기본 의도 설정
            state["intents"] = [{
                "type": "error",
                "confidence": 0.0,
                "error": str(e)
            }]
            state["confidence_scores"] = {}
            state["ambiguous"] = True

        return state

    async def tokenize_query(self, state: IntentAnalysisState) -> IntentAnalysisState:
        """쿼리 토큰화"""
        state["tokens"] = state.get("user_query", "").split()
        return state

    async def extract_entities(self, state: IntentAnalysisState) -> IntentAnalysisState:
        """엔티티 추출"""
        # 간단한 규칙 기반 엔티티 추출 (LLM은 classify_intent에서 처리)
        entities = []
        query = state.get("user_query", "").lower()

        # 기간 엔티티
        period_keywords = {
            "지난달": "last_month",
            "이번달": "this_month",
            "지난 분기": "last_quarter",
            "이번 분기": "this_quarter",
            "작년": "last_year",
            "올해": "this_year"
        }

        for keyword, value in period_keywords.items():
            if keyword in query:
                entities.append({"type": "period", "value": value})

        # 지역 엔티티
        regions = ["서울", "경기", "부산", "대구", "인천", "광주", "대전", "울산"]
        for region in regions:
            if region in query:
                entities.append({"type": "region", "value": region})

        state["entities"] = entities
        return state

    async def validate_intent(self, state: IntentAnalysisState) -> IntentAnalysisState:
        """의도 검증"""
        state["ambiguous"] = False
        return state

    async def resolve_ambiguity(self, state: IntentAnalysisState) -> IntentAnalysisState:
        """모호성 해결"""
        return state

    def check_ambiguity(self, state: IntentAnalysisState) -> str:
        """모호성 체크"""
        if state.get("ambiguous"):
            return "ambiguous"
        return "clear"