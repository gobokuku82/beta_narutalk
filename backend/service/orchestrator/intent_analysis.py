from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict

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
        prompt = f"""
        사용자 질의: {state['user_query']}
        추출된 엔티티: {state['entities']}
        
        가능한 의도:
        1. sales_analysis - 실적/매출 분석
        2. client_analysis - 거래처 분석
        3. hr_search - 인사정보 검색
        4. rule_search - 내부규정 검색
        5. doc_generation - 문서 생성
        6. compliance_check - 규정 위반 검토
        
        의도를 분류하고 신뢰도를 평가하세요.
        """
        # LLM 호출 로직
        state["intents"] = []
        state["confidence_scores"] = {}
        return state

    async def tokenize_query(self, state: IntentAnalysisState) -> IntentAnalysisState:
        """쿼리 토큰화"""
        state["tokens"] = state.get("user_query", "").split()
        return state

    async def extract_entities(self, state: IntentAnalysisState) -> IntentAnalysisState:
        """엔티티 추출"""
        state["entities"] = []
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