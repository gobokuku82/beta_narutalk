# Orchestrator 완전 상세 문서

## 개요
Orchestrator는 LangGraph 0.6.7을 사용하여 전체 워크플로우를 관리하는 핵심 컴포넌트입니다. 메인 오케스트레이터와 5개의 서브그래프로 구성되어 있습니다.

---

## 1. Main Orchestrator

### 파일: `backend/service/orchestrator/orchestrator.py`

#### 파일 목적
전체 워크플로우를 조정하는 메인 오케스트레이터. 모든 서브그래프를 통합하고 실행 흐름을 제어합니다.

#### Imports 및 Dependencies
```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from typing import TypedDict, List, Dict, Any, Optional
from enum import Enum
import logging
from datetime import datetime
import uuid

# 서브그래프 임포트
from .intent_analysis import IntentAnalysisSubGraph
from .planning import PlanningSubGraph
from .agent_execution import AgentExecutionSubGraph
from .result_evaluation import ResultEvaluationSubGraph
from .response_generation import ResponseGenerationSubGraph
```

#### 로깅 설정
```python
logger = logging.getLogger(__name__)
```

---

### State 정의

#### MainState(TypedDict)
```python
class MainState(TypedDict):
    # ===== 기본 정보 =====
    user_id: str                           # 사용자 식별자
    session_id: str                        # 세션 식별자
    user_query: str                        # 사용자의 원본 쿼리
    timestamp: str                         # 요청 타임스탬프

    # ===== 의도 및 계획 =====
    intents: List[Dict[str, Any]]          # 분류된 의도들
    execution_plan: Dict[str, Any]         # 실행 계획
    priority_level: str                    # 우선순위 (high, medium, low)

    # ===== 실행 관련 =====
    active_agents: List[str]               # 활성화된 에이전트 목록
    agent_results: Dict[str, Any]          # 에이전트 실행 결과
    parallel_execution: bool               # 병렬 실행 여부

    # ===== 결과 및 검증 =====
    raw_results: Dict[str, Any]            # 원본 결과
    validated_results: Dict[str, Any]      # 검증된 결과
    compliance_status: Dict[str, Any]      # 컴플라이언스 상태

    # ===== 응답 =====
    final_response: str                    # 최종 응답 텍스트
    response_format: str                   # 응답 포맷 (text, table, chart, document)
    confidence_score: float                # 응답 신뢰도 점수

    # ===== 메타데이터 =====
    error_logs: List[str]                  # 에러 로그
    execution_time: float                  # 전체 실행 시간
    tokens_used: int                       # 사용된 토큰 수
    need_human_review: bool                # 사람 검토 필요 여부
    conversation_history: List[Dict]       # 대화 히스토리
```

---

### MainOrchestrator 클래스

#### 클래스 초기화
```python
class MainOrchestrator:
    def __init__(self, use_checkpointer: bool = False):
        """
        메인 오케스트레이터 초기화

        Args:
            use_checkpointer: 체크포인터 사용 여부 (상태 저장)
        """
        # 메인 워크플로우 생성
        self.workflow = StateGraph(MainState)

        # 서브그래프 초기화
        self.intent_analyzer = IntentAnalysisSubGraph()
        self.planner = PlanningSubGraph()
        self.agent_executor = AgentExecutionSubGraph()
        self.result_evaluator = ResultEvaluationSubGraph()
        self.response_generator = ResponseGenerationSubGraph()

        # 체크포인터 설정 (옵션)
        self.checkpointer = None
        if use_checkpointer:
            self.checkpointer = AsyncSqliteSaver.from_path("checkpoints.db")

        # 그래프 구성
        self._build_graph()

        logger.info(f"MainOrchestrator initialized (checkpointer: {use_checkpointer})")
```

#### 그래프 구성 (_build_graph)
```python
def _build_graph(self):
    """메인 워크플로우 그래프 구성"""

    # ===== 노드 추가 =====
    # 기본 노드
    self.workflow.add_node("authenticate", self.authenticate_user)
    self.workflow.add_node("store_memory", self.store_conversation)

    # 서브그래프 노드
    self.workflow.add_node("analyze_intent", self.analyze_intent_subgraph)
    self.workflow.add_node("create_plan", self.planning_subgraph)
    self.workflow.add_node("execute_agents", self.agent_execution_subgraph)
    self.workflow.add_node("evaluate_results", self.evaluation_subgraph)
    self.workflow.add_node("generate_response", self.response_generation_subgraph)

    # ===== 엣지 추가 =====
    # 시작 -> 인증
    self.workflow.add_edge(START, "authenticate")

    # 인증 -> 의도 분석
    self.workflow.add_edge("authenticate", "analyze_intent")

    # 의도 분석 -> 계획 수립
    self.workflow.add_edge("analyze_intent", "create_plan")

    # 계획 검증 조건부 라우팅
    self.workflow.add_conditional_edges(
        "create_plan",
        self.check_plan_validity,
        {
            "valid": "execute_agents",
            "need_clarification": "generate_response",
            "invalid": END
        }
    )

    # 실행 상태 조건부 라우팅
    self.workflow.add_conditional_edges(
        "execute_agents",
        self.check_execution_status,
        {
            "success": "evaluate_results",
            "partial_success": "evaluate_results",
            "retry": "execute_agents",
            "failure": "generate_response"
        }
    )

    # 평가 결과 조건부 라우팅
    self.workflow.add_conditional_edges(
        "evaluate_results",
        self.check_evaluation,
        {
            "approved": "generate_response",
            "need_revision": "execute_agents",
            "compliance_issue": "generate_response"
        }
    )

    # 응답 생성 -> 메모리 저장
    self.workflow.add_edge("generate_response", "store_memory")

    # 메모리 저장 -> 종료
    self.workflow.add_edge("store_memory", END)

    # 워크플로우 컴파일
    self.app = self.workflow.compile(checkpointer=self.checkpointer)

    logger.info("Main workflow graph built and compiled")
```

---

### 노드 함수 상세

#### 1. authenticate_user(self, state: MainState)
```python
def authenticate_user(self, state: MainState):
    """
    사용자 인증 및 세션 초기화

    - 사용자 ID 검증
    - 세션 생성
    - 초기 메타데이터 설정
    """
    user_id = state.get("user_id", "")

    # 사용자 ID가 없으면 생성
    if not user_id:
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        state["user_id"] = user_id

    # 세션 ID가 없으면 생성
    if not state.get("session_id"):
        state["session_id"] = f"session_{uuid.uuid4().hex[:8]}"

    # 타임스탬프 설정
    if not state.get("timestamp"):
        state["timestamp"] = datetime.now().isoformat()

    # 초기 메타데이터 설정
    state["error_logs"] = []
    state["execution_time"] = 0.0
    state["tokens_used"] = 0
    state["need_human_review"] = False

    # 대화 히스토리 초기화
    if "conversation_history" not in state:
        state["conversation_history"] = []

    # 현재 쿼리를 히스토리에 추가
    state["conversation_history"].append({
        "role": "user",
        "content": state.get("user_query", ""),
        "timestamp": state["timestamp"]
    })

    logger.info(f"User authenticated: {user_id}, Session: {state['session_id']}")

    return state
```

#### 2. analyze_intent_subgraph(self, state: MainState)
```python
def analyze_intent_subgraph(self, state: MainState):
    """
    의도 분석 서브그래프 실행

    IntentAnalysisSubGraph를 실행하여 사용자 쿼리의 의도를 분석
    """
    try:
        # 서브그래프 입력 준비
        intent_input = {
            "user_query": state["user_query"],
            "tokens": [],
            "entities": [],
            "intents": [],
            "confidence_scores": {},
            "ambiguous": False
        }

        # 서브그래프 실행
        intent_result = self.intent_analyzer.app.invoke(intent_input)

        # 결과를 메인 state에 통합
        state["intents"] = intent_result.get("intents", [])

        # 신뢰도 점수 저장
        if intent_result.get("confidence_scores"):
            max_confidence = max(intent_result["confidence_scores"].values())
            state["confidence_score"] = max_confidence
        else:
            state["confidence_score"] = 0.0

        # 모호성 플래그
        if intent_result.get("ambiguous"):
            state["need_human_review"] = True
            logger.warning("Ambiguous intent detected, may need human review")

        logger.info(f"Intent analysis complete: {len(state['intents'])} intents identified")

    except Exception as e:
        logger.error(f"Intent analysis failed: {e}")
        state["error_logs"].append(f"Intent analysis error: {str(e)}")
        state["intents"] = []

    return state
```

#### 3. planning_subgraph(self, state: MainState)
```python
def planning_subgraph(self, state: MainState):
    """
    실행 계획 서브그래프 실행

    PlanningSubGraph를 실행하여 에이전트 실행 계획 수립
    """
    try:
        # 서브그래프 입력 준비
        planning_input = {
            "intents": state.get("intents", []),
            "execution_steps": [],
            "agent_sequence": [],
            "dependencies": {},
            "parallel_groups": [],
            "estimated_time": 0.0
        }

        # 서브그래프 실행
        planning_result = self.planner.app.invoke(planning_input)

        # 실행 계획 저장
        state["execution_plan"] = {
            "steps": planning_result.get("execution_steps", []),
            "agent_sequence": planning_result.get("agent_sequence", []),
            "dependencies": planning_result.get("dependencies", {}),
            "parallel_groups": planning_result.get("parallel_groups", []),
            "estimated_time": planning_result.get("estimated_time", 0.0)
        }

        # 활성 에이전트 목록 설정
        state["active_agents"] = planning_result.get("agent_sequence", [])

        # 병렬 실행 가능 여부
        state["parallel_execution"] = len(planning_result.get("parallel_groups", [])) > 0

        # 우선순위 설정
        if len(state["active_agents"]) > 3:
            state["priority_level"] = "high"
        elif len(state["active_agents"]) > 1:
            state["priority_level"] = "medium"
        else:
            state["priority_level"] = "low"

        logger.info(f"Planning complete: {len(state['active_agents'])} agents planned")

    except Exception as e:
        logger.error(f"Planning failed: {e}")
        state["error_logs"].append(f"Planning error: {str(e)}")
        state["execution_plan"] = {}

    return state
```

#### 4. agent_execution_subgraph(self, state: MainState)
```python
def agent_execution_subgraph(self, state: MainState):
    """
    에이전트 실행 서브그래프 실행

    AgentExecutionSubGraph를 실행하여 계획된 에이전트들 실행
    """
    import time
    start_time = time.time()

    try:
        # 서브그래프 입력 준비
        execution_input = {
            "execution_plan": state.get("execution_plan", {}),
            "active_agents": state.get("active_agents", []),
            "agent_inputs": {"query": state["user_query"]},  # 기본 입력
            "agent_results": {},
            "parallel_groups": state["execution_plan"].get("parallel_groups", []),
            "execution_status": "started",
            "error_logs": [],
            "retry_count": 0,
            "start_time": start_time,
            "end_time": None
        }

        # 서브그래프 실행
        execution_result = self.agent_executor.app.invoke(execution_input)

        # 결과 저장
        state["agent_results"] = execution_result.get("agent_results", {})
        state["raw_results"] = execution_result.get("agent_results", {})

        # 에러 로그 추가
        if execution_result.get("error_logs"):
            state["error_logs"].extend(execution_result["error_logs"])

        # 실행 시간 계산
        execution_time = time.time() - start_time
        state["execution_time"] += execution_time

        # 실행 상태 저장
        state["_execution_status"] = execution_result.get("execution_status", "unknown")

        logger.info(f"Agent execution complete in {execution_time:.2f}s")

    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        state["error_logs"].append(f"Agent execution error: {str(e)}")
        state["agent_results"] = {}
        state["_execution_status"] = "failure"

    return state
```

#### 5. evaluation_subgraph(self, state: MainState)
```python
def evaluation_subgraph(self, state: MainState):
    """
    결과 평가 서브그래프 실행

    ResultEvaluationSubGraph를 실행하여 에이전트 실행 결과 평가
    """
    try:
        # 서브그래프 입력 준비
        evaluation_input = {
            "raw_results": state.get("raw_results", {}),
            "validation_rules": [],  # 기본 검증 규칙
            "quality_scores": {},
            "compliance_checks": {},
            "validated_results": {},
            "issues_found": [],
            "recommendations": []
        }

        # 서브그래프 실행
        evaluation_result = self.result_evaluator.app.invoke(evaluation_input)

        # 검증된 결과 저장
        state["validated_results"] = evaluation_result.get("validated_results", {})

        # 컴플라이언스 상태 저장
        state["compliance_status"] = evaluation_result.get("compliance_checks", {})

        # 품질 점수 반영
        quality_scores = evaluation_result.get("quality_scores", {})
        if quality_scores:
            avg_quality = sum(quality_scores.values()) / len(quality_scores)
            state["confidence_score"] = (state.get("confidence_score", 0) + avg_quality) / 2

        # 이슈 발견 시 휴먼 리뷰 플래그
        if evaluation_result.get("issues_found"):
            state["need_human_review"] = True
            logger.warning(f"Issues found during evaluation: {evaluation_result['issues_found']}")

        # 평가 상태 저장
        state["_evaluation_status"] = "approved"  # 기본값
        if evaluation_result.get("issues_found"):
            if any("compliance" in str(issue).lower() for issue in evaluation_result["issues_found"]):
                state["_evaluation_status"] = "compliance_issue"
            elif len(evaluation_result["issues_found"]) > 3:
                state["_evaluation_status"] = "need_revision"

        logger.info("Result evaluation complete")

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        state["error_logs"].append(f"Evaluation error: {str(e)}")
        state["validated_results"] = state.get("raw_results", {})
        state["_evaluation_status"] = "approved"  # 실패 시 진행

    return state
```

#### 6. response_generation_subgraph(self, state: MainState)
```python
def response_generation_subgraph(self, state: MainState):
    """
    응답 생성 서브그래프 실행

    ResponseGenerationSubGraph를 실행하여 최종 응답 생성
    """
    try:
        # 응답 포맷 결정 (결과 타입에 따라)
        if not state.get("response_format"):
            results = state.get("validated_results", {})
            if any("chart" in str(r) or "visualization" in str(r) for r in results.values()):
                state["response_format"] = "chart"
            elif any("table" in str(r) or "rows" in str(r) for r in results.values()):
                state["response_format"] = "table"
            elif any("document" in str(r) for r in results.values()):
                state["response_format"] = "document"
            else:
                state["response_format"] = "text"

        # 서브그래프 입력 준비
        response_input = {
            "response_format": state["response_format"],
            "raw_data": state.get("validated_results", {}),
            "formatted_response": "",
            "citations": [],
            "confidence_score": state.get("confidence_score", 0.5)
        }

        # 서브그래프 실행
        response_result = self.response_generator.app.invoke(response_input)

        # 최종 응답 저장
        state["final_response"] = response_result.get("formatted_response", "")

        # 인용 정보 추가
        if response_result.get("citations"):
            state["final_response"] += "\n\n### 참고 자료\n"
            for citation in response_result["citations"]:
                state["final_response"] += f"- {citation}\n"

        # 에러 처리
        if not state["final_response"] and state.get("error_logs"):
            state["final_response"] = "죄송합니다. 요청을 처리하는 중 오류가 발생했습니다.\n"
            state["final_response"] += f"오류: {state['error_logs'][0]}"

        logger.info(f"Response generated: {len(state['final_response'])} characters")

    except Exception as e:
        logger.error(f"Response generation failed: {e}")
        state["error_logs"].append(f"Response generation error: {str(e)}")
        state["final_response"] = "죄송합니다. 응답 생성 중 오류가 발생했습니다."

    return state
```

#### 7. store_conversation(self, state: MainState)
```python
def store_conversation(self, state: MainState):
    """
    대화 내역 저장

    현재 대화를 히스토리에 추가하고 메타데이터 업데이트
    """
    # 응답을 히스토리에 추가
    state["conversation_history"].append({
        "role": "assistant",
        "content": state.get("final_response", ""),
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "agents_used": state.get("active_agents", []),
            "execution_time": state.get("execution_time", 0),
            "confidence_score": state.get("confidence_score", 0),
            "tokens_used": state.get("tokens_used", 0)
        }
    })

    # 대화 히스토리 크기 제한 (최근 20개만 유지)
    if len(state["conversation_history"]) > 20:
        state["conversation_history"] = state["conversation_history"][-20:]

    # 토큰 사용량 추정 (간단한 추정)
    state["tokens_used"] += len(state.get("final_response", "").split()) * 2

    logger.info(f"Conversation stored. History size: {len(state['conversation_history'])}")

    return state
```

---

### 조건부 라우팅 함수

#### 1. check_plan_validity(self, state: MainState) -> str
```python
def check_plan_validity(self, state: MainState) -> str:
    """
    실행 계획의 유효성 검증

    Returns:
        "valid": 유효한 계획
        "need_clarification": 명확화 필요
        "invalid": 무효한 계획
    """
    plan = state.get("execution_plan", {})

    # 계획이 없으면 무효
    if not plan:
        logger.warning("No execution plan found")
        return "invalid"

    # 에이전트가 없으면 명확화 필요
    agents = plan.get("agent_sequence", [])
    if not agents:
        logger.warning("No agents in execution plan")
        return "need_clarification"

    # 의도가 불명확하면 명확화 필요
    if state.get("confidence_score", 0) < 0.3:
        logger.warning(f"Low confidence score: {state.get('confidence_score')}")
        return "need_clarification"

    # 너무 많은 에이전트(5개 초과)는 재검토 필요
    if len(agents) > 5:
        logger.warning(f"Too many agents planned: {len(agents)}")
        return "need_clarification"

    return "valid"
```

#### 2. check_execution_status(self, state: MainState) -> str
```python
def check_execution_status(self, state: MainState) -> str:
    """
    에이전트 실행 상태 확인

    Returns:
        "success": 성공
        "partial_success": 부분 성공
        "retry": 재시도 필요
        "failure": 실패
    """
    status = state.get("_execution_status", "unknown")
    results = state.get("agent_results", {})
    errors = state.get("error_logs", [])

    # 명시적 상태가 있으면 사용
    if status in ["success", "partial_success", "retry_needed", "failure"]:
        if status == "retry_needed":
            return "retry"
        return status

    # 결과로 상태 추론
    if results:
        success_count = sum(1 for r in results.values() if r.get("success", False))
        total_count = len(results)

        if success_count == total_count:
            return "success"
        elif success_count > 0:
            return "partial_success"
        else:
            return "failure"

    # 에러가 많으면 실패
    if len(errors) > 3:
        return "failure"

    # 기본값은 재시도
    return "retry"
```

#### 3. check_evaluation(self, state: MainState) -> str
```python
def check_evaluation(self, state: MainState) -> str:
    """
    평가 결과 확인

    Returns:
        "approved": 승인됨
        "need_revision": 수정 필요
        "compliance_issue": 컴플라이언스 문제
    """
    eval_status = state.get("_evaluation_status", "approved")

    # 명시적 상태 반환
    if eval_status in ["approved", "need_revision", "compliance_issue"]:
        return eval_status

    # 컴플라이언스 체크
    compliance = state.get("compliance_status", {})
    if compliance.get("violations"):
        return "compliance_issue"

    # 품질 점수 체크
    validated_results = state.get("validated_results", {})
    if not validated_results:
        return "need_revision"

    return "approved"
```

---

## 2. Intent Analysis SubGraph

### 파일: `backend/service/orchestrator/intent_analysis.py`

#### 파일 목적
사용자 쿼리의 의도를 분석하고 다중 의도를 분류하는 서브그래프

#### Imports 및 Dependencies
```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict, Any, Optional
import json
import logging
from ..utils import LLMManager, PromptTemplates
```

---

### State 정의

#### IntentAnalysisState(TypedDict)
```python
class IntentAnalysisState(TypedDict):
    user_query: str                     # 사용자 쿼리
    tokens: List[str]                   # 토큰화된 쿼리
    entities: List[Dict]                # 추출된 엔티티
    intents: List[Dict]                 # 분류된 의도들
    confidence_scores: Dict[str, float] # 의도별 신뢰도 점수
    ambiguous: bool                     # 모호성 플래그
```

---

### IntentAnalysisSubGraph 클래스

#### 클래스 초기화
```python
class IntentAnalysisSubGraph:
    def __init__(self):
        # 워크플로우 생성
        self.workflow = StateGraph(IntentAnalysisState)

        # LLM 매니저 초기화
        self.llm = LLMManager()

        # 프롬프트 템플릿 초기화
        self.prompts = PromptTemplates()

        # 그래프 구성
        self._build_graph()

        logger.info("IntentAnalysisSubGraph initialized")
```

#### 그래프 구성 (_build_graph)
```python
def _build_graph(self):
    """의도 분석 워크플로우 구성"""

    # 노드 추가
    self.workflow.add_node("tokenize", self.tokenize_query)
    self.workflow.add_node("extract_entities", self.extract_entities)
    self.workflow.add_node("classify_intent", self.classify_intent)
    self.workflow.add_node("validate_intent", self.validate_intent)
    self.workflow.add_node("resolve_ambiguity", self.resolve_ambiguity)

    # 엣지 추가
    self.workflow.add_edge(START, "tokenize")
    self.workflow.add_edge("tokenize", "extract_entities")
    self.workflow.add_edge("extract_entities", "classify_intent")
    self.workflow.add_edge("classify_intent", "validate_intent")

    # 조건부 엣지: 모호성 체크
    self.workflow.add_conditional_edges(
        "validate_intent",
        self.check_ambiguity,
        {
            "clear": END,
            "ambiguous": "resolve_ambiguity"
        }
    )

    self.workflow.add_edge("resolve_ambiguity", END)

    # 워크플로우 컴파일
    self.app = self.workflow.compile()
```

---

### 노드 함수 상세

#### 1. tokenize_query(self, state: IntentAnalysisState)
```python
def tokenize_query(self, state: IntentAnalysisState):
    """쿼리 토큰화"""
    query = state["user_query"]

    # 간단한 토큰화 (공백 기반)
    tokens = query.split()

    # 특수 문자 처리
    special_chars = ["?", "!", ".", ",", ";", ":", "(", ")", "[", "]"]
    processed_tokens = []

    for token in tokens:
        # 특수 문자 분리
        for char in special_chars:
            token = token.replace(char, f" {char} ")

        # 공백으로 다시 분리
        sub_tokens = token.split()
        processed_tokens.extend(sub_tokens)

    state["tokens"] = processed_tokens
    logger.debug(f"Tokenized query: {len(processed_tokens)} tokens")

    return state
```

#### 2. extract_entities(self, state: IntentAnalysisState)
```python
def extract_entities(self, state: IntentAnalysisState):
    """엔티티 추출 (규칙 기반)"""
    query = state["user_query"]
    entities = []

    # 기간 엔티티 추출
    period_patterns = {
        "지난달": {"type": "period", "value": "last_month", "normalized": "M-1"},
        "이번달": {"type": "period", "value": "this_month", "normalized": "M0"},
        "지난 분기": {"type": "period", "value": "last_quarter", "normalized": "Q-1"},
        "이번 분기": {"type": "period", "value": "this_quarter", "normalized": "Q0"},
        "작년": {"type": "period", "value": "last_year", "normalized": "Y-1"},
        "올해": {"type": "period", "value": "this_year", "normalized": "Y0"},
        "어제": {"type": "period", "value": "yesterday", "normalized": "D-1"},
        "오늘": {"type": "period", "value": "today", "normalized": "D0"},
        "내일": {"type": "period", "value": "tomorrow", "normalized": "D+1"}
    }

    for pattern, entity_info in period_patterns.items():
        if pattern in query:
            entity = entity_info.copy()
            entity["text"] = pattern
            entity["position"] = query.index(pattern)
            entities.append(entity)

    # 지역 엔티티 추출
    regions = {
        "서울": "seoul",
        "경기": "gyeonggi",
        "부산": "busan",
        "대구": "daegu",
        "인천": "incheon",
        "광주": "gwangju",
        "대전": "daejeon",
        "울산": "ulsan",
        "세종": "sejong",
        "강원": "gangwon",
        "충북": "chungbuk",
        "충남": "chungnam",
        "전북": "jeonbuk",
        "전남": "jeonnam",
        "경북": "gyeongbuk",
        "경남": "gyeongnam",
        "제주": "jeju"
    }

    for korean, english in regions.items():
        if korean in query:
            entities.append({
                "type": "region",
                "value": english,
                "text": korean,
                "position": query.index(korean)
            })

    # 숫자 엔티티 추출
    import re
    number_pattern = r'\d+(?:,\d{3})*(?:\.\d+)?'
    for match in re.finditer(number_pattern, query):
        entities.append({
            "type": "number",
            "value": float(match.group().replace(",", "")),
            "text": match.group(),
            "position": match.start()
        })

    # 퍼센트 엔티티 추출
    percent_pattern = r'\d+(?:\.\d+)?%'
    for match in re.finditer(percent_pattern, query):
        entities.append({
            "type": "percentage",
            "value": float(match.group()[:-1]) / 100,
            "text": match.group(),
            "position": match.start()
        })

    # 위치 기준 정렬
    entities.sort(key=lambda x: x.get("position", 0))

    state["entities"] = entities
    logger.info(f"Extracted {len(entities)} entities")

    return state
```

#### 3. classify_intent(self, state: IntentAnalysisState)
```python
def classify_intent(self, state: IntentAnalysisState):
    """LLM을 사용한 의도 분류"""
    query = state["user_query"]
    entities = state.get("entities", [])

    # 프롬프트 생성
    prompt = self.prompts.get_prompt(
        category="intent_analysis",
        version="v1",
        query=query,
        entities=json.dumps(entities, ensure_ascii=False)
    )

    # LLM 호출
    response = self.llm.generate(
        prompt=prompt,
        model="openai_mini",  # 빠른 응답을 위해 mini 모델 사용
        temperature=0.3,      # 일관성 있는 분류를 위해 낮은 temperature
        category="intent_classification"
    )

    try:
        # JSON 응답 파싱
        result = json.loads(response["content"])
        intents = result.get("intents", [])
        confidence_scores = result.get("confidence_scores", {})

    except json.JSONDecodeError:
        # JSON 파싱 실패 시 fallback
        logger.warning("Failed to parse LLM response as JSON, using fallback")
        intents = self._fallback_intent_classification(query)
        confidence_scores = {intent["name"]: 0.5 for intent in intents}

    # 의도 정규화 및 검증
    normalized_intents = []
    valid_intents = [
        "sales_analysis",      # 매출 분석
        "client_analysis",     # 거래처 분석
        "hr_search",          # HR 정보 검색
        "rule_search",        # 규정 검색
        "doc_generation",     # 문서 생성
        "compliance_check",   # 컴플라이언스 체크
        "general_query"       # 일반 질의
    ]

    for intent in intents:
        if isinstance(intent, dict) and "name" in intent:
            if intent["name"] in valid_intents:
                normalized_intents.append(intent)
        elif isinstance(intent, str) and intent in valid_intents:
            normalized_intents.append({
                "name": intent,
                "confidence": confidence_scores.get(intent, 0.5)
            })

    state["intents"] = normalized_intents
    state["confidence_scores"] = confidence_scores

    logger.info(f"Classified {len(normalized_intents)} intents")

    return state
```

#### 4. validate_intent(self, state: IntentAnalysisState)
```python
def validate_intent(self, state: IntentAnalysisState):
    """의도 검증 및 정제"""
    intents = state.get("intents", [])
    confidence_scores = state.get("confidence_scores", {})

    # 신뢰도 임계값
    CONFIDENCE_THRESHOLD = 0.3

    # 저신뢰도 의도 필터링
    validated_intents = []
    for intent in intents:
        intent_name = intent.get("name") if isinstance(intent, dict) else intent
        confidence = confidence_scores.get(intent_name, 0.5)

        if confidence >= CONFIDENCE_THRESHOLD:
            validated_intent = {
                "name": intent_name,
                "confidence": confidence,
                "primary": len(validated_intents) == 0  # 첫 번째가 주요 의도
            }
            validated_intents.append(validated_intent)

    # 의도가 없으면 일반 질의로 설정
    if not validated_intents:
        validated_intents = [{
            "name": "general_query",
            "confidence": 0.5,
            "primary": True
        }]
        state["ambiguous"] = True
    else:
        # 다중 의도이고 신뢰도가 비슷하면 모호함
        if len(validated_intents) > 1:
            confidences = [i["confidence"] for i in validated_intents]
            max_diff = max(confidences) - min(confidences)
            if max_diff < 0.2:  # 신뢰도 차이가 작으면 모호함
                state["ambiguous"] = True
            else:
                state["ambiguous"] = False
        else:
            state["ambiguous"] = False

    state["intents"] = validated_intents

    logger.info(f"Validated intents: {[i['name'] for i in validated_intents]}")

    return state
```

#### 5. resolve_ambiguity(self, state: IntentAnalysisState)
```python
def resolve_ambiguity(self, state: IntentAnalysisState):
    """모호성 해결 시도"""
    query = state["user_query"]
    intents = state.get("intents", [])
    entities = state.get("entities", [])

    # 컨텍스트 기반 모호성 해결
    context_clues = {
        "sales_analysis": ["매출", "실적", "판매", "revenue", "성과"],
        "client_analysis": ["거래처", "고객", "클라이언트", "customer"],
        "hr_search": ["직원", "사원", "팀", "부서", "연락처"],
        "rule_search": ["규정", "규칙", "정책", "가이드라인"],
        "doc_generation": ["문서", "보고서", "작성", "생성"],
        "compliance_check": ["컴플라이언스", "준수", "위반", "규정검토"]
    }

    # 각 의도에 대한 추가 점수 계산
    for intent in intents:
        intent_name = intent["name"]
        if intent_name in context_clues:
            clue_words = context_clues[intent_name]
            # 쿼리에 단서 단어가 있으면 신뢰도 증가
            for word in clue_words:
                if word in query.lower():
                    intent["confidence"] = min(1.0, intent["confidence"] + 0.1)

    # 신뢰도 재정렬
    intents.sort(key=lambda x: x["confidence"], reverse=True)

    # 상위 2개만 유지
    state["intents"] = intents[:2]

    # 여전히 모호하면 플래그 유지
    if len(intents) >= 2 and abs(intents[0]["confidence"] - intents[1]["confidence"]) < 0.15:
        state["ambiguous"] = True
        logger.warning("Ambiguity remains after resolution attempt")
    else:
        state["ambiguous"] = False
        logger.info("Ambiguity resolved")

    return state
```

---

### 조건부 라우팅 함수

#### check_ambiguity(self, state: IntentAnalysisState) -> str
```python
def check_ambiguity(self, state: IntentAnalysisState) -> str:
    """모호성 체크"""
    if state.get("ambiguous", False):
        return "ambiguous"
    return "clear"
```

---

### 보조 메서드

#### _fallback_intent_classification(self, query: str) -> List[Dict]
```python
def _fallback_intent_classification(self, query: str) -> List[Dict]:
    """LLM 실패 시 규칙 기반 의도 분류"""
    intents = []
    query_lower = query.lower()

    # 키워드 기반 분류
    if any(word in query_lower for word in ["매출", "실적", "판매", "revenue"]):
        intents.append({"name": "sales_analysis", "confidence": 0.7})

    if any(word in query_lower for word in ["거래처", "고객", "클라이언트"]):
        intents.append({"name": "client_analysis", "confidence": 0.7})

    if any(word in query_lower for word in ["직원", "사원", "팀", "부서"]):
        intents.append({"name": "hr_search", "confidence": 0.7})

    if any(word in query_lower for word in ["규정", "규칙", "정책"]):
        intents.append({"name": "rule_search", "confidence": 0.7})

    if any(word in query_lower for word in ["문서", "보고서", "작성"]):
        intents.append({"name": "doc_generation", "confidence": 0.7})

    if any(word in query_lower for word in ["컴플라이언스", "준수", "위반"]):
        intents.append({"name": "compliance_check", "confidence": 0.7})

    # 의도가 없으면 일반 질의
    if not intents:
        intents.append({"name": "general_query", "confidence": 0.5})

    return intents
```

---

## 3. Planning SubGraph

### 파일: `backend/service/orchestrator/planning.py`

#### 파일 목적
의도 분석 결과를 바탕으로 최적의 실행 계획을 수립하는 서브그래프

#### Imports 및 Dependencies
```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict
import logging
```

---

### State 정의

#### PlanningState(TypedDict)
```python
class PlanningState(TypedDict):
    intents: List[Dict]                 # 의도 목록
    execution_steps: List[Dict]         # 실행 단계
    agent_sequence: List[str]           # 에이전트 실행 순서
    dependencies: Dict[str, List[str]]  # 에이전트 간 의존성
    parallel_groups: List[List[str]]    # 병렬 실행 그룹
    estimated_time: float                # 예상 실행 시간
```

---

### PlanningSubGraph 클래스

#### 클래스 초기화
```python
class PlanningSubGraph:
    def __init__(self):
        # 워크플로우 생성
        self.workflow = StateGraph(PlanningState)

        # 그래프 구성
        self._build_graph()

        logger.info("PlanningSubGraph initialized")
```

#### 그래프 구성 (_build_graph)
```python
def _build_graph(self):
    """계획 수립 워크플로우 구성"""

    # 노드 추가
    self.workflow.add_node("analyze_dependencies", self.analyze_dependencies)
    self.workflow.add_node("optimize_sequence", self.optimize_execution_sequence)
    self.workflow.add_node("allocate_resources", self.allocate_resources)
    self.workflow.add_node("create_execution_plan", self.create_execution_plan)

    # 엣지 추가
    self.workflow.add_edge(START, "analyze_dependencies")
    self.workflow.add_edge("analyze_dependencies", "optimize_sequence")
    self.workflow.add_edge("optimize_sequence", "allocate_resources")
    self.workflow.add_edge("allocate_resources", "create_execution_plan")
    self.workflow.add_edge("create_execution_plan", END)

    # 워크플로우 컴파일
    self.app = self.workflow.compile()
```

---

### 노드 함수 상세

#### 1. analyze_dependencies(self, state: PlanningState)
```python
def analyze_dependencies(self, state: PlanningState):
    """에이전트 간 의존성 분석"""
    intents = state.get("intents", [])

    # 의도별 에이전트 매핑
    intent_to_agents = {
        "sales_analysis": ["sales_analytics_agent"],
        "client_analysis": ["sales_analytics_agent", "search_agent"],
        "hr_search": ["search_agent"],
        "rule_search": ["search_agent"],
        "doc_generation": ["document_generation_agent"],
        "compliance_check": ["compliance_check_agent"],
        "general_query": ["search_agent"]
    }

    # 필요한 에이전트 수집
    required_agents = set()
    for intent in intents:
        intent_name = intent.get("name") if isinstance(intent, dict) else intent
        agents = intent_to_agents.get(intent_name, [])
        required_agents.update(agents)

    # 의존성 정의
    dependencies = {
        "document_generation_agent": ["sales_analytics_agent", "search_agent"],  # 문서 생성은 데이터가 필요
        "compliance_check_agent": ["sales_analytics_agent"],  # 컴플라이언스는 매출 데이터가 필요할 수 있음
    }

    # 실제 의존성 필터링
    actual_dependencies = {}
    for agent in required_agents:
        if agent in dependencies:
            deps = [dep for dep in dependencies[agent] if dep in required_agents]
            if deps:
                actual_dependencies[agent] = deps

    state["agent_sequence"] = list(required_agents)
    state["dependencies"] = actual_dependencies

    logger.info(f"Analyzed dependencies for {len(required_agents)} agents")

    return state
```

#### 2. optimize_execution_sequence(self, state: PlanningState)
```python
def optimize_execution_sequence(self, state: PlanningState):
    """실행 순서 최적화 (토폴로지 정렬)"""
    agents = state.get("agent_sequence", [])
    dependencies = state.get("dependencies", {})

    # 의존성이 없으면 모두 병렬 실행 가능
    if not dependencies:
        state["parallel_groups"] = [agents] if agents else []
        logger.info("No dependencies, all agents can run in parallel")
        return state

    # 토폴로지 정렬을 위한 진입 차수 계산
    in_degree = {agent: 0 for agent in agents}
    for deps in dependencies.values():
        for dep in deps:
            if dep in in_degree:
                in_degree[dep] += 1

    # 레벨별 그룹화 (병렬 실행 가능한 그룹)
    parallel_groups = []
    processed = set()

    while len(processed) < len(agents):
        # 현재 실행 가능한 에이전트들 (진입 차수가 0)
        current_group = []
        for agent in agents:
            if agent not in processed and in_degree.get(agent, 0) == 0:
                current_group.append(agent)
                processed.add(agent)

        if not current_group:
            # 순환 의존성이 있는 경우
            logger.warning("Circular dependency detected")
            # 남은 에이전트를 순차적으로 추가
            for agent in agents:
                if agent not in processed:
                    parallel_groups.append([agent])
                    processed.add(agent)
            break

        parallel_groups.append(current_group)

        # 의존성 업데이트
        for agent in current_group:
            for dependent, deps in dependencies.items():
                if agent in deps:
                    in_degree[dependent] -= 1

    # 최적화된 순서 생성
    optimized_sequence = []
    for group in parallel_groups:
        optimized_sequence.extend(group)

    state["agent_sequence"] = optimized_sequence
    state["parallel_groups"] = parallel_groups

    logger.info(f"Optimized into {len(parallel_groups)} parallel groups")

    return state
```

#### 3. allocate_resources(self, state: PlanningState)
```python
def allocate_resources(self, state: PlanningState):
    """리소스 할당 및 예상 시간 계산"""
    agents = state.get("agent_sequence", [])
    parallel_groups = state.get("parallel_groups", [])

    # 에이전트별 예상 실행 시간 (초)
    agent_times = {
        "sales_analytics_agent": 3.0,
        "search_agent": 2.0,
        "document_generation_agent": 2.5,
        "compliance_check_agent": 4.0
    }

    # 전체 예상 시간 계산 (병렬 그룹 고려)
    total_time = 0.0
    for group in parallel_groups:
        # 병렬 그룹은 가장 오래 걸리는 에이전트 시간
        group_time = max(agent_times.get(agent, 1.0) for agent in group)
        total_time += group_time

    # 실행 단계 생성
    execution_steps = []
    step_number = 1

    for group_idx, group in enumerate(parallel_groups):
        step = {
            "step_number": step_number,
            "type": "parallel" if len(group) > 1 else "sequential",
            "agents": group,
            "estimated_time": max(agent_times.get(agent, 1.0) for agent in group),
            "description": f"{'병렬' if len(group) > 1 else '순차'} 실행: {', '.join(group)}"
        }
        execution_steps.append(step)
        step_number += 1

    state["execution_steps"] = execution_steps
    state["estimated_time"] = total_time

    logger.info(f"Allocated resources: {len(execution_steps)} steps, {total_time:.1f}s estimated")

    return state
```

#### 4. create_execution_plan(self, state: PlanningState)
```python
def create_execution_plan(self, state: PlanningState):
    """최종 실행 계획 생성"""
    steps = state.get("execution_steps", [])
    agents = state.get("agent_sequence", [])
    dependencies = state.get("dependencies", {})
    parallel_groups = state.get("parallel_groups", [])
    estimated_time = state.get("estimated_time", 0.0)

    # 실행 계획 요약
    plan_summary = {
        "total_agents": len(agents),
        "total_steps": len(steps),
        "parallel_groups": len([g for g in parallel_groups if len(g) > 1]),
        "sequential_steps": len([g for g in parallel_groups if len(g) == 1]),
        "has_dependencies": len(dependencies) > 0,
        "estimated_time": estimated_time
    }

    # 상세 계획
    detailed_plan = {
        "summary": plan_summary,
        "steps": steps,
        "agents": agents,
        "dependencies": dependencies,
        "parallel_groups": parallel_groups,
        "execution_notes": []
    }

    # 실행 참고사항 추가
    if estimated_time > 10:
        detailed_plan["execution_notes"].append("장시간 실행이 예상됩니다.")

    if len(agents) > 3:
        detailed_plan["execution_notes"].append("복잡한 요청으로 여러 에이전트가 필요합니다.")

    if dependencies:
        detailed_plan["execution_notes"].append("일부 에이전트는 순차적으로 실행됩니다.")

    # 계획 검증
    if not agents:
        logger.warning("Empty execution plan created")
        detailed_plan["execution_notes"].append("경고: 실행할 에이전트가 없습니다.")

    # State에 상세 계획 저장 (구조 유지를 위해 기존 필드 업데이트)
    state["execution_steps"] = steps

    logger.info(f"Execution plan created: {plan_summary}")

    return state
```

---

## 4. Agent Execution SubGraph

### 파일: `backend/service/orchestrator/agent_execution.py`

#### 파일 목적
계획된 에이전트들을 실제로 실행하고 조정하는 서브그래프

#### Imports 및 Dependencies
```python
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
import asyncio
from datetime import datetime
import logging
import importlib
import time
```

---

### State 정의

#### AgentExecutionState(TypedDict)
```python
class AgentExecutionState(TypedDict):
    execution_plan: Dict[str, Any]      # 실행 계획
    active_agents: List[str]            # 활성 에이전트
    agent_inputs: Dict[str, Any]        # 에이전트 입력 데이터
    agent_results: Dict[str, Any]       # 에이전트 결과
    parallel_groups: List[List[str]]    # 병렬 실행 그룹
    execution_status: str                # 실행 상태
    error_logs: List[str]                # 에러 로그
    retry_count: int                     # 재시도 횟수
    start_time: float                    # 시작 시간
    end_time: Optional[float]            # 종료 시간
```

---

### AgentExecutionSubGraph 클래스

#### 클래스 초기화
```python
class AgentExecutionSubGraph:
    def __init__(self):
        # 워크플로우 생성
        self.workflow = StateGraph(AgentExecutionState)

        # 에이전트 레지스트리
        self.agent_registry = {
            "sales_analytics_agent": "service.agents.sales_analytics_agent.SalesAnalyticsAgent",
            "search_agent": "service.agents.search_agent.SearchAgent",
            "document_generation_agent": "service.agents.document_generation_agent.DocumentGenerationAgent",
            "compliance_check_agent": "service.agents.compliance_check_agent.ComplianceCheckAgent"
        }

        # 설정
        self.max_retries = 3
        self.timeout_seconds = 30

        # 그래프 구성
        self._build_graph()

        logger.info("AgentExecutionSubGraph initialized")
```

#### 그래프 구성 (_build_graph)
```python
def _build_graph(self):
    """에이전트 실행 워크플로우 구성"""

    # 노드 추가
    self.workflow.add_node("prepare_execution", self.prepare_agent_execution)
    self.workflow.add_node("execute_parallel", self.execute_parallel_agents)
    self.workflow.add_node("execute_sequential", self.execute_sequential_agents)
    self.workflow.add_node("merge_results", self.merge_agent_results)
    self.workflow.add_node("validate_results", self.validate_execution_results)
    self.workflow.add_node("handle_failures", self.handle_execution_failures)

    # 시작 엣지
    self.workflow.add_edge(START, "prepare_execution")

    # 실행 전략에 따른 조건부 라우팅
    self.workflow.add_conditional_edges(
        "prepare_execution",
        self.determine_execution_strategy,
        {
            "parallel": "execute_parallel",
            "sequential": "execute_sequential",
            "mixed": "execute_parallel"  # mixed는 parallel부터 시작
        }
    )

    # 실행 후 병합
    self.workflow.add_edge("execute_parallel", "merge_results")
    self.workflow.add_edge("execute_sequential", "merge_results")

    # 결과 검증
    self.workflow.add_edge("merge_results", "validate_results")

    # 검증 결과에 따른 라우팅
    self.workflow.add_conditional_edges(
        "validate_results",
        self.check_validation_status,
        {
            "success": END,
            "partial_success": END,
            "retry_needed": "handle_failures",
            "failure": "handle_failures"
        }
    )

    # 실패 처리 후 재시도 또는 종료
    self.workflow.add_conditional_edges(
        "handle_failures",
        self.decide_retry,
        {
            "retry": "prepare_execution",
            "abort": END
        }
    )

    # 워크플로우 컴파일
    self.app = self.workflow.compile()
```

---

### 노드 함수 상세

#### 1. prepare_agent_execution(self, state: AgentExecutionState)
```python
def prepare_agent_execution(self, state: AgentExecutionState):
    """에이전트 실행 준비"""
    plan = state.get("execution_plan", {})
    active_agents = state.get("active_agents", [])

    # 입력 데이터 준비
    if not state.get("agent_inputs"):
        state["agent_inputs"] = {}

    # 각 에이전트별 입력 데이터 설정
    for agent in active_agents:
        if agent not in state["agent_inputs"]:
            # 기본 입력 데이터
            state["agent_inputs"][agent] = {
                "query": state.get("user_query", ""),
                "context": {}
            }

            # 에이전트별 특화 입력
            if agent == "sales_analytics_agent":
                state["agent_inputs"][agent]["database"] = "sales_performance"

            elif agent == "search_agent":
                state["agent_inputs"][agent]["search_type"] = "both"

            elif agent == "document_generation_agent":
                state["agent_inputs"][agent]["document_type"] = "report"

            elif agent == "compliance_check_agent":
                state["agent_inputs"][agent]["check_type"] = "general"

    # 실행 상태 초기화
    if state.get("retry_count", 0) == 0:
        state["execution_status"] = "prepared"
        state["error_logs"] = []
        state["agent_results"] = {}

    logger.info(f"Execution prepared for {len(active_agents)} agents")

    return state
```

#### 2. execute_parallel_agents(self, state: AgentExecutionState)
```python
async def execute_parallel_agents_async(self, agents: List[str], inputs: Dict[str, Any]) -> Dict[str, Any]:
    """비동기 병렬 실행"""
    tasks = []
    for agent_name in agents:
        input_data = inputs.get(agent_name, {})
        task = asyncio.create_task(self._execute_agent_async(agent_name, input_data))
        tasks.append((agent_name, task))

    results = {}
    for agent_name, task in tasks:
        try:
            result = await asyncio.wait_for(task, timeout=self.timeout_seconds)
            results[agent_name] = result
        except asyncio.TimeoutError:
            results[agent_name] = {
                "success": False,
                "error": f"Timeout after {self.timeout_seconds} seconds"
            }
        except Exception as e:
            results[agent_name] = {
                "success": False,
                "error": str(e)
            }

    return results

def execute_parallel_agents(self, state: AgentExecutionState):
    """병렬 에이전트 실행"""
    parallel_groups = state.get("parallel_groups", [])
    agent_inputs = state.get("agent_inputs", {})
    all_results = state.get("agent_results", {})

    for group_idx, group in enumerate(parallel_groups):
        if len(group) > 1:
            logger.info(f"Executing parallel group {group_idx + 1}: {group}")

            # 병렬 실행
            try:
                # 이벤트 루프 처리
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                group_results = loop.run_until_complete(
                    self.execute_parallel_agents_async(group, agent_inputs)
                )

                all_results.update(group_results)

            except Exception as e:
                logger.error(f"Parallel execution failed: {e}")
                state["error_logs"].append(f"Parallel group {group_idx + 1} failed: {str(e)}")

                # 실패한 에이전트들에 대한 기본 결과
                for agent in group:
                    if agent not in all_results:
                        all_results[agent] = {
                            "success": False,
                            "error": str(e)
                        }

        else:
            # 단일 에이전트는 순차 실행으로 처리
            if group:
                agent = group[0]
                logger.info(f"Executing single agent: {agent}")
                result = self._execute_single_agent(agent, agent_inputs.get(agent, {}))
                all_results[agent] = result

    state["agent_results"] = all_results
    state["execution_status"] = "parallel_complete"

    return state
```

#### 3. execute_sequential_agents(self, state: AgentExecutionState)
```python
def execute_sequential_agents(self, state: AgentExecutionState):
    """순차 에이전트 실행"""
    agents = state.get("active_agents", [])
    agent_inputs = state.get("agent_inputs", {})
    results = state.get("agent_results", {})

    for agent_name in agents:
        if agent_name in results:
            # 이미 실행된 에이전트는 스킵
            continue

        logger.info(f"Executing sequential agent: {agent_name}")

        # 이전 결과를 컨텍스트로 전달
        input_data = agent_inputs.get(agent_name, {}).copy()
        input_data["previous_results"] = results

        # 에이전트 실행
        result = self._execute_single_agent(agent_name, input_data)
        results[agent_name] = result

        # 실패 시 중단 여부 결정
        if not result.get("success", False):
            logger.warning(f"Agent {agent_name} failed, continuing with next")

    state["agent_results"] = results
    state["execution_status"] = "sequential_complete"

    return state
```

#### 4. _execute_single_agent(self, agent_name: str, input_data: Dict) -> Dict
```python
def _execute_single_agent(self, agent_name: str, input_data: Dict) -> Dict:
    """단일 에이전트 실행"""
    try:
        # 에이전트 클래스 동적 로드
        if agent_name not in self.agent_registry:
            return {
                "success": False,
                "error": f"Unknown agent: {agent_name}"
            }

        module_path, class_name = self.agent_registry[agent_name].rsplit(".", 1)
        module = importlib.import_module(module_path)
        agent_class = getattr(module, class_name)

        # 에이전트 인스턴스 생성 및 실행
        agent = agent_class()
        result = agent.execute(input_data)

        # 성공 플래그 확인
        if "success" not in result:
            result["success"] = True

        result["agent"] = agent_name
        result["execution_time"] = time.time()

        logger.info(f"Agent {agent_name} executed successfully")
        return result

    except Exception as e:
        logger.error(f"Agent {agent_name} execution failed: {e}")
        return {
            "success": False,
            "agent": agent_name,
            "error": str(e),
            "execution_time": time.time()
        }
```

#### 5. _execute_agent_async(self, agent_name: str, input_data: Dict) -> Dict
```python
async def _execute_agent_async(self, agent_name: str, input_data: Dict) -> Dict:
    """비동기 에이전트 실행 래퍼"""
    # 동기 함수를 비동기로 실행
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, self._execute_single_agent, agent_name, input_data)
```

#### 6. merge_agent_results(self, state: AgentExecutionState)
```python
def merge_agent_results(self, state: AgentExecutionState):
    """에이전트 결과 병합"""
    results = state.get("agent_results", {})

    # 결과 요약
    success_count = sum(1 for r in results.values() if r.get("success", False))
    total_count = len(results)

    # 병합된 데이터 생성
    merged_data = {
        "total_agents": total_count,
        "successful_agents": success_count,
        "failed_agents": total_count - success_count,
        "success_rate": success_count / total_count if total_count > 0 else 0,
        "individual_results": results,
        "aggregated_data": {}
    }

    # 에이전트별 주요 데이터 추출
    for agent_name, result in results.items():
        if result.get("success"):
            # 각 에이전트의 주요 결과 추출
            if agent_name == "sales_analytics_agent":
                merged_data["aggregated_data"]["sales_analysis"] = result.get("analysis", {})

            elif agent_name == "search_agent":
                merged_data["aggregated_data"]["search_results"] = result.get("final_results", {})

            elif agent_name == "document_generation_agent":
                merged_data["aggregated_data"]["generated_document"] = result.get("document", {})

            elif agent_name == "compliance_check_agent":
                merged_data["aggregated_data"]["compliance_report"] = result.get("report", "")

    state["agent_results"] = merged_data
    state["execution_status"] = "merged"

    logger.info(f"Results merged: {success_count}/{total_count} successful")

    return state
```

#### 7. validate_execution_results(self, state: AgentExecutionState)
```python
def validate_execution_results(self, state: AgentExecutionState):
    """실행 결과 검증"""
    results = state.get("agent_results", {})

    # 검증 기준
    validation_criteria = {
        "has_results": len(results) > 0,
        "has_successful": results.get("successful_agents", 0) > 0,
        "critical_agents_succeeded": True,  # 중요 에이전트 성공 여부
        "data_integrity": True               # 데이터 무결성
    }

    # 중요 에이전트 체크
    critical_agents = []  # 정의된 중요 에이전트가 있다면 여기에 추가
    for agent in critical_agents:
        if agent in results.get("individual_results", {}):
            if not results["individual_results"][agent].get("success"):
                validation_criteria["critical_agents_succeeded"] = False

    # 데이터 무결성 체크
    individual_results = results.get("individual_results", {})
    for agent_name, result in individual_results.items():
        # 기본 구조 체크
        if not isinstance(result, dict):
            validation_criteria["data_integrity"] = False
            break

        # 필수 필드 체크
        if "success" not in result:
            validation_criteria["data_integrity"] = False
            break

    # 전체 검증 상태 결정
    if all(validation_criteria.values()):
        state["_validation_status"] = "success"
    elif validation_criteria["has_successful"]:
        state["_validation_status"] = "partial_success"
    elif state.get("retry_count", 0) < self.max_retries:
        state["_validation_status"] = "retry_needed"
    else:
        state["_validation_status"] = "failure"

    logger.info(f"Validation complete: {state['_validation_status']}")

    return state
```

#### 8. handle_execution_failures(self, state: AgentExecutionState)
```python
def handle_execution_failures(self, state: AgentExecutionState):
    """실행 실패 처리"""
    results = state.get("agent_results", {})
    error_logs = state.get("error_logs", [])
    retry_count = state.get("retry_count", 0)

    # 실패한 에이전트 식별
    failed_agents = []
    individual_results = results.get("individual_results", {})

    for agent_name, result in individual_results.items():
        if not result.get("success", False):
            failed_agents.append(agent_name)
            error_msg = f"Agent {agent_name} failed: {result.get('error', 'Unknown error')}"
            error_logs.append(error_msg)
            logger.error(error_msg)

    # 재시도 전략 결정
    if retry_count < self.max_retries:
        # 실패한 에이전트만 재시도
        state["active_agents"] = failed_agents
        state["retry_count"] = retry_count + 1
        state["_retry_decision"] = "retry"
        logger.info(f"Retrying {len(failed_agents)} failed agents (attempt {retry_count + 1}/{self.max_retries})")
    else:
        state["_retry_decision"] = "abort"
        state["execution_status"] = "failed"
        logger.error(f"Max retries ({self.max_retries}) exceeded, aborting")

    state["error_logs"] = error_logs

    return state
```

---

### 조건부 라우팅 함수

#### 1. determine_execution_strategy(self, state: AgentExecutionState) -> str
```python
def determine_execution_strategy(self, state: AgentExecutionState) -> str:
    """실행 전략 결정"""
    parallel_groups = state.get("parallel_groups", [])

    if not parallel_groups:
        return "sequential"

    # 모든 그룹이 단일 에이전트면 순차
    if all(len(group) <= 1 for group in parallel_groups):
        return "sequential"

    # 모든 그룹이 다중 에이전트면 병렬
    if all(len(group) > 1 for group in parallel_groups):
        return "parallel"

    # 혼합
    return "mixed"
```

#### 2. check_validation_status(self, state: AgentExecutionState) -> str
```python
def check_validation_status(self, state: AgentExecutionState) -> str:
    """검증 상태 확인"""
    return state.get("_validation_status", "failure")
```

#### 3. decide_retry(self, state: AgentExecutionState) -> str
```python
def decide_retry(self, state: AgentExecutionState) -> str:
    """재시도 결정"""
    return state.get("_retry_decision", "abort")
```

---

## 5. Result Evaluation SubGraph

### 파일: `backend/service/orchestrator/result_evaluation.py`

#### 파일 목적
에이전트 실행 결과를 평가하고 품질을 검증하는 서브그래프

#### Imports 및 Dependencies
```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict, Any
import logging
```

---

### State 정의

#### EvaluationState(TypedDict)
```python
class EvaluationState(TypedDict):
    raw_results: Dict[str, Any]         # 원본 결과
    validation_rules: List[Dict]        # 검증 규칙
    quality_scores: Dict[str, float]    # 품질 점수
    compliance_checks: Dict[str, Any]   # 컴플라이언스 체크
    validated_results: Dict[str, Any]   # 검증된 결과
    issues_found: List[str]             # 발견된 문제
    recommendations: List[str]          # 개선 권고사항
```

---

### ResultEvaluationSubGraph 클래스

#### 클래스 초기화 및 그래프 구성
```python
class ResultEvaluationSubGraph:
    def __init__(self):
        self.workflow = StateGraph(EvaluationState)
        self._build_graph()
        logger.info("ResultEvaluationSubGraph initialized")

    def _build_graph(self):
        """평가 워크플로우 구성"""
        # 노드 추가
        self.workflow.add_node("check_completeness", self.check_completeness)
        self.workflow.add_node("validate_accuracy", self.validate_accuracy)
        self.workflow.add_node("check_compliance", self.check_compliance)
        self.workflow.add_node("calculate_quality", self.calculate_quality_score)
        self.workflow.add_node("generate_recommendations", self.generate_recommendations)

        # 엣지 추가
        self.workflow.add_edge(START, "check_completeness")
        self.workflow.add_edge("check_completeness", "validate_accuracy")
        self.workflow.add_edge("validate_accuracy", "check_compliance")
        self.workflow.add_edge("check_compliance", "calculate_quality")

        # 조건부 엣지: 품질 점수에 따라
        self.workflow.add_conditional_edges(
            "calculate_quality",
            self.check_quality_threshold,
            {
                "high_quality": END,
                "needs_improvement": "generate_recommendations",
                "low_quality": "generate_recommendations"
            }
        )

        self.workflow.add_edge("generate_recommendations", END)
        self.app = self.workflow.compile()
```

---

### 노드 함수 상세

#### 1. check_completeness(self, state: EvaluationState)
```python
def check_completeness(self, state: EvaluationState):
    """결과 완성도 체크"""
    raw_results = state.get("raw_results", {})
    issues = state.get("issues_found", [])

    completeness_score = 1.0

    # 기본 구조 체크
    if not raw_results:
        issues.append("No results provided")
        completeness_score = 0.0
    else:
        # 개별 결과 체크
        individual_results = raw_results.get("individual_results", {})
        if not individual_results:
            issues.append("No individual agent results")
            completeness_score -= 0.3

        # 필수 필드 체크
        for agent_name, result in individual_results.items():
            if not isinstance(result, dict):
                issues.append(f"Invalid result format for {agent_name}")
                completeness_score -= 0.1

            if "success" not in result:
                issues.append(f"Missing success flag for {agent_name}")
                completeness_score -= 0.05

    completeness_score = max(0, completeness_score)
    state["quality_scores"] = state.get("quality_scores", {})
    state["quality_scores"]["completeness"] = completeness_score
    state["issues_found"] = issues

    logger.info(f"Completeness check: {completeness_score:.2f}")
    return state
```

#### 2. validate_accuracy(self, state: EvaluationState)
```python
def validate_accuracy(self, state: EvaluationState):
    """정확도 검증"""
    raw_results = state.get("raw_results", {})
    issues = state.get("issues_found", [])

    accuracy_score = 1.0

    # 데이터 타입 검증
    aggregated_data = raw_results.get("aggregated_data", {})

    # 매출 분석 데이터 검증
    if "sales_analysis" in aggregated_data:
        sales_data = aggregated_data["sales_analysis"]
        if isinstance(sales_data, dict):
            # 숫자 데이터 검증
            for key, value in sales_data.items():
                if "amount" in key.lower() or "total" in key.lower():
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        issues.append(f"Invalid numeric value in sales_analysis: {key}")
                        accuracy_score -= 0.1

    # 검색 결과 검증
    if "search_results" in aggregated_data:
        search_data = aggregated_data["search_results"]
        if isinstance(search_data, dict):
            if "total_results" in search_data:
                if search_data["total_results"] < 0:
                    issues.append("Invalid negative result count")
                    accuracy_score -= 0.15

    accuracy_score = max(0, accuracy_score)
    state["quality_scores"]["accuracy"] = accuracy_score

    logger.info(f"Accuracy validation: {accuracy_score:.2f}")
    return state
```

#### 3. check_compliance(self, state: EvaluationState)
```python
def check_compliance(self, state: EvaluationState):
    """컴플라이언스 체크"""
    raw_results = state.get("raw_results", {})
    compliance_checks = {}

    # 컴플라이언스 보고서 체크
    aggregated_data = raw_results.get("aggregated_data", {})
    if "compliance_report" in aggregated_data:
        report = aggregated_data["compliance_report"]
        if report:
            # 위반 사항 추출
            if "위반" in report or "violation" in report.lower():
                compliance_checks["has_violations"] = True
                compliance_checks["status"] = "review_required"
            else:
                compliance_checks["has_violations"] = False
                compliance_checks["status"] = "compliant"
        else:
            compliance_checks["status"] = "not_checked"
    else:
        compliance_checks["status"] = "not_applicable"

    state["compliance_checks"] = compliance_checks

    logger.info(f"Compliance check: {compliance_checks.get('status')}")
    return state
```

#### 4. calculate_quality_score(self, state: EvaluationState)
```python
def calculate_quality_score(self, state: EvaluationState):
    """전체 품질 점수 계산"""
    quality_scores = state.get("quality_scores", {})

    # 가중 평균 계산
    weights = {
        "completeness": 0.4,
        "accuracy": 0.6
    }

    total_score = 0.0
    total_weight = 0.0

    for metric, weight in weights.items():
        if metric in quality_scores:
            total_score += quality_scores[metric] * weight
            total_weight += weight

    overall_score = total_score / total_weight if total_weight > 0 else 0.0
    quality_scores["overall"] = overall_score

    # 품질 레벨 결정
    if overall_score >= 0.8:
        quality_level = "high"
    elif overall_score >= 0.5:
        quality_level = "medium"
    else:
        quality_level = "low"

    quality_scores["level"] = quality_level
    state["quality_scores"] = quality_scores

    # 검증된 결과 생성
    state["validated_results"] = state.get("raw_results", {})
    state["validated_results"]["quality_assessment"] = quality_scores

    logger.info(f"Quality score: {overall_score:.2f} ({quality_level})")
    return state
```

#### 5. generate_recommendations(self, state: EvaluationState)
```python
def generate_recommendations(self, state: EvaluationState):
    """개선 권고사항 생성"""
    issues = state.get("issues_found", [])
    quality_scores = state.get("quality_scores", {})
    recommendations = []

    # 완성도 관련 권고
    if quality_scores.get("completeness", 1.0) < 0.7:
        recommendations.append("일부 에이전트 실행이 누락되었습니다. 재실행을 고려하세요.")

    # 정확도 관련 권고
    if quality_scores.get("accuracy", 1.0) < 0.7:
        recommendations.append("데이터 검증에 문제가 있습니다. 입력 데이터를 확인하세요.")

    # 컴플라이언스 관련 권고
    compliance = state.get("compliance_checks", {})
    if compliance.get("has_violations"):
        recommendations.append("컴플라이언스 위반 사항이 발견되었습니다. 법무팀 검토가 필요합니다.")

    # 일반 권고
    if len(issues) > 5:
        recommendations.append("다수의 문제가 발견되었습니다. 전체적인 재검토가 필요합니다.")

    state["recommendations"] = recommendations

    logger.info(f"Generated {len(recommendations)} recommendations")
    return state
```

---

### 조건부 라우팅 함수

#### check_quality_threshold(self, state: EvaluationState) -> str
```python
def check_quality_threshold(self, state: EvaluationState) -> str:
    """품질 임계값 체크"""
    quality_level = state.get("quality_scores", {}).get("level", "low")

    if quality_level == "high":
        return "high_quality"
    elif quality_level == "medium":
        return "needs_improvement"
    else:
        return "low_quality"
```

---

## 6. Response Generation SubGraph

### 파일: `backend/service/orchestrator/response_generation.py`

#### 파일 목적
검증된 결과를 사용자 친화적인 응답으로 변환하는 서브그래프

#### Imports 및 Dependencies
```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict, Any
import json
import logging
```

---

### State 정의

#### ResponseState(TypedDict)
```python
class ResponseState(TypedDict):
    response_format: str                # 응답 포맷
    raw_data: Dict[str, Any]            # 원본 데이터
    formatted_response: str             # 포맷된 응답
    citations: List[str]                # 인용/참조
    confidence_score: float             # 신뢰도 점수
```

---

### ResponseGenerationSubGraph 클래스

#### 클래스 초기화 및 그래프 구성
```python
class ResponseGenerationSubGraph:
    def __init__(self):
        self.workflow = StateGraph(ResponseState)
        self._build_graph()
        logger.info("ResponseGenerationSubGraph initialized")

    def _build_graph(self):
        """응답 생성 워크플로우 구성"""
        # 노드 추가
        self.workflow.add_node("format_selection", self.select_format)
        self.workflow.add_node("generate_text", self.generate_text_response)
        self.workflow.add_node("generate_table", self.generate_table_response)
        self.workflow.add_node("generate_chart", self.generate_chart_response)
        self.workflow.add_node("generate_document", self.generate_document_response)
        self.workflow.add_node("add_citations", self.add_references)
        self.workflow.add_node("final_review", self.final_quality_check)

        # 포맷 선택
        self.workflow.add_edge(START, "format_selection")

        # 포맷별 라우팅
        self.workflow.add_conditional_edges(
            "format_selection",
            self.route_by_format,
            {
                "text": "generate_text",
                "table": "generate_table",
                "chart": "generate_chart",
                "document": "generate_document"
            }
        )

        # 모든 생성 노드는 인용 추가로
        self.workflow.add_edge("generate_text", "add_citations")
        self.workflow.add_edge("generate_table", "add_citations")
        self.workflow.add_edge("generate_chart", "add_citations")
        self.workflow.add_edge("generate_document", "add_citations")

        # 최종 검토
        self.workflow.add_edge("add_citations", "final_review")
        self.workflow.add_edge("final_review", END)

        self.app = self.workflow.compile()
```

---

### 노드 함수 상세

#### 1. select_format(self, state: ResponseState)
```python
def select_format(self, state: ResponseState):
    """응답 포맷 선택"""
    response_format = state.get("response_format", "")
    raw_data = state.get("raw_data", {})

    # 명시적 포맷이 없으면 데이터 기반 추론
    if not response_format:
        aggregated_data = raw_data.get("aggregated_data", {})

        # 차트 데이터가 있으면 차트
        if any("visualization" in str(v) for v in aggregated_data.values()):
            response_format = "chart"
        # 테이블 데이터가 있으면 테이블
        elif any("table" in str(v) or isinstance(v, list) for v in aggregated_data.values()):
            response_format = "table"
        # 문서가 있으면 문서
        elif "generated_document" in aggregated_data:
            response_format = "document"
        # 기본은 텍스트
        else:
            response_format = "text"

    state["response_format"] = response_format
    logger.info(f"Selected format: {response_format}")

    return state
```

#### 2. generate_text_response(self, state: ResponseState)
```python
def generate_text_response(self, state: ResponseState):
    """텍스트 응답 생성"""
    raw_data = state.get("raw_data", {})
    response = ""

    # 요약 정보
    if "total_agents" in raw_data:
        response += f"실행 요약:\n"
        response += f"- 총 {raw_data['total_agents']}개 에이전트 실행\n"
        response += f"- 성공: {raw_data.get('successful_agents', 0)}개\n"
        response += f"- 실패: {raw_data.get('failed_agents', 0)}개\n\n"

    # 주요 결과
    aggregated = raw_data.get("aggregated_data", {})

    # 매출 분석 결과
    if "sales_analysis" in aggregated:
        analysis = aggregated["sales_analysis"]
        response += "📊 매출 분석 결과:\n"
        if isinstance(analysis, dict):
            for key, value in analysis.items():
                if key != "raw_data":
                    response += f"- {key}: {value}\n"
        response += "\n"

    # 검색 결과
    if "search_results" in aggregated:
        search = aggregated["search_results"]
        if isinstance(search, dict):
            response += "🔍 검색 결과:\n"
            response += f"- 총 {search.get('total_results', 0)}개 결과\n"
            top_results = search.get("top_results", [])
            if top_results:
                response += "- 상위 결과:\n"
                for idx, result in enumerate(top_results[:3], 1):
                    if isinstance(result, dict):
                        response += f"  {idx}. {result.get('title', result.get('name', 'N/A'))}\n"
            response += "\n"

    # 컴플라이언스 결과
    if "compliance_report" in aggregated:
        report = aggregated["compliance_report"]
        if report:
            response += "✅ 컴플라이언스 검토:\n"
            # 보고서의 첫 200자만 표시
            response += report[:200]
            if len(report) > 200:
                response += "...\n"
            response += "\n"

    if not response:
        response = "요청을 처리했지만 표시할 결과가 없습니다."

    state["formatted_response"] = response
    logger.info(f"Generated text response: {len(response)} characters")

    return state
```

#### 3. generate_table_response(self, state: ResponseState)
```python
def generate_table_response(self, state: ResponseState):
    """테이블 응답 생성"""
    raw_data = state.get("raw_data", {})
    aggregated = raw_data.get("aggregated_data", {})

    table_html = "<table class='result-table'>\n"

    # 매출 데이터 테이블
    if "sales_analysis" in aggregated:
        analysis = aggregated["sales_analysis"]
        if "statistics" in analysis:
            stats = analysis["statistics"]
            table_html += "<thead><tr><th>항목</th><th>값</th></tr></thead>\n"
            table_html += "<tbody>\n"
            for col, values in stats.items():
                if isinstance(values, dict):
                    for stat, value in values.items():
                        table_html += f"<tr><td>{col} - {stat}</td><td>{value:,.2f}</td></tr>\n"
            table_html += "</tbody>\n"

    table_html += "</table>"

    # Markdown 테이블도 생성
    markdown_table = "\n| 항목 | 값 |\n|------|----|\n"
    if "sales_analysis" in aggregated:
        analysis = aggregated["sales_analysis"]
        if "statistics" in analysis:
            stats = analysis["statistics"]
            for col, values in stats.items():
                if isinstance(values, dict):
                    for stat, value in values.items():
                        markdown_table += f"| {col} - {stat} | {value:,.2f} |\n"

    state["formatted_response"] = f"### 데이터 테이블\n{markdown_table}"
    logger.info("Generated table response")

    return state
```

#### 4. generate_chart_response(self, state: ResponseState)
```python
def generate_chart_response(self, state: ResponseState):
    """차트 응답 생성"""
    raw_data = state.get("raw_data", {})
    aggregated = raw_data.get("aggregated_data", {})

    chart_config = {
        "type": "bar",
        "data": {},
        "options": {}
    }

    # 매출 데이터를 차트로
    if "sales_analysis" in aggregated:
        analysis = aggregated["sales_analysis"]
        if "top_5" in analysis:
            chart_config["data"] = {
                "labels": list(analysis["top_5"].keys()),
                "datasets": [{
                    "label": "매출액",
                    "data": list(analysis["top_5"].values())
                }]
            }

    # 차트 설정을 JSON으로
    chart_json = json.dumps(chart_config, ensure_ascii=False, indent=2)

    response = f"""### 📈 차트 데이터

아래 데이터를 차트로 시각화할 수 있습니다:

```json
{chart_json}
```

이 데이터를 Chart.js, D3.js 등의 라이브러리로 렌더링하세요.
"""

    state["formatted_response"] = response
    logger.info("Generated chart response configuration")

    return state
```

#### 5. generate_document_response(self, state: ResponseState)
```python
def generate_document_response(self, state: ResponseState):
    """문서 응답 생성"""
    raw_data = state.get("raw_data", {})
    aggregated = raw_data.get("aggregated_data", {})

    if "generated_document" in aggregated:
        document = aggregated["generated_document"]
        if isinstance(document, dict):
            content = document.get("content", "")
            metadata = document.get("metadata", {})

            response = f"""### 📄 생성된 문서

**문서 정보:**
- 문서 ID: {metadata.get('document_id', 'N/A')}
- 생성일: {metadata.get('created_at', 'N/A')}
- 포맷: {document.get('format', 'N/A')}

**문서 내용:**
{content[:1000]}  # 처음 1000자만 표시

{"... (문서가 계속됩니다)" if len(content) > 1000 else ""}
"""
        else:
            response = "문서가 생성되었지만 형식이 올바르지 않습니다."
    else:
        response = "문서를 생성할 수 없었습니다."

    state["formatted_response"] = response
    logger.info("Generated document response")

    return state
```

#### 6. add_references(self, state: ResponseState)
```python
def add_references(self, state: ResponseState):
    """참조/인용 추가"""
    raw_data = state.get("raw_data", {})
    citations = []

    # 사용된 데이터 소스 수집
    individual_results = raw_data.get("individual_results", {})

    for agent_name, result in individual_results.items():
        if result.get("success"):
            # 각 에이전트별 소스 추가
            if agent_name == "sales_analytics_agent":
                citations.append("매출 데이터베이스 (sales_performance_db)")
            elif agent_name == "search_agent":
                sources = result.get("sources_used", [])
                for source in sources:
                    citations.append(f"검색 소스: {source}")
            elif agent_name == "compliance_check_agent":
                citations.append("KPBMA 규정 데이터베이스")

    # 중복 제거
    citations = list(set(citations))

    if citations:
        citation_text = "\n\n---\n### 📚 참고 자료\n"
        for idx, citation in enumerate(citations, 1):
            citation_text += f"{idx}. {citation}\n"

        state["formatted_response"] += citation_text

    state["citations"] = citations
    logger.info(f"Added {len(citations)} citations")

    return state
```

#### 7. final_quality_check(self, state: ResponseState)
```python
def final_quality_check(self, state: ResponseState):
    """최종 품질 검토"""
    response = state.get("formatted_response", "")

    # 응답이 너무 짧으면 보강
    if len(response) < 50:
        response += "\n\n💡 추가 정보가 필요하시면 더 구체적인 질문을 해주세요."

    # 신뢰도 점수 추가
    confidence = state.get("confidence_score", 0.5)
    if confidence < 0.5:
        response += "\n\n⚠️ 주의: 이 응답의 신뢰도가 낮습니다. 결과를 검증해 주세요."

    # 응답 길이 제한 (너무 긴 경우)
    MAX_LENGTH = 5000
    if len(response) > MAX_LENGTH:
        response = response[:MAX_LENGTH] + "\n\n... (응답이 너무 길어 일부가 생략되었습니다)"

    state["formatted_response"] = response
    logger.info(f"Final response: {len(response)} characters")

    return state
```

---

### 조건부 라우팅 함수

#### route_by_format(self, state: ResponseState) -> str
```python
def route_by_format(self, state: ResponseState) -> str:
    """포맷별 라우팅"""
    format_type = state.get("response_format", "text")

    if format_type in ["text", "table", "chart", "document"]:
        return format_type
    else:
        logger.warning(f"Unknown format: {format_type}, defaulting to text")
        return "text"
```

---

이 문서는 Orchestrator의 모든 파일(메인 오케스트레이터 및 5개 서브그래프)에 대한 완전한 상세 문서입니다. 각 클래스, 메서드, 노드, state, 조건부 라우팅을 모두 포함하고 있습니다.