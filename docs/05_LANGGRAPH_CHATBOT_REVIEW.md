# LangGraph 0.6.7 기반 제약회사 챗봇 시스템 - 상세 코드리뷰 보고서

## 목차
1. [시스템 개요](#1-시스템-개요)
2. [전체 아키텍처](#2-전체-아키텍처)
3. [사용자 입력-출력 흐름 분석](#3-사용자-입력-출력-흐름-분석)
4. [LLM 통합 및 관리](#4-llm-통합-및-관리)
5. [서브그래프 상세 분석](#5-서브그래프-상세-분석)
6. [에이전트 구현 분석](#6-에이전트-구현-분석)
7. [데이터 계층 분석](#7-데이터-계층-분석)
8. [State 관리 메커니즘](#8-state-관리-메커니즘)
9. [개선 제안 및 권고사항](#9-개선-제안-및-권고사항)

---

## 1. 시스템 개요

### 1.1 프로젝트 구조
```
beta_narutalk/
├── backend/
│   ├── api/
│   │   └── models/
│   │       └── base.py              # 기본 모델 정의
│   └── service/
│       ├── orchestrator/
│       │   ├── orchestrator.py      # 메인 오케스트레이터
│       │   ├── intent_analysis.py   # 의도 분석 서브그래프
│       │   ├── planning.py          # 계획 수립 서브그래프
│       │   ├── agent_execution.py   # 에이전트 실행 서브그래프
│       │   ├── result_evaluation.py # 결과 평가 서브그래프
│       │   └── response_generation.py # 응답 생성 서브그래프
│       ├── agents/
│       │   ├── sales_analytics_agent.py    # 매출 분석 에이전트
│       │   ├── search_agent.py             # 검색 에이전트
│       │   ├── document_generation_agent.py # 문서 생성 에이전트
│       │   └── compliance_check_agent.py   # 규정 검토 에이전트
│       ├── utils/
│       │   ├── llm_manager.py      # LLM 관리자 (싱글톤)
│       │   ├── prompt_templates.py # 프롬프트 템플릿
│       │   └── token_tracker.py    # 토큰 추적
│       └── supervisor.py            # 시스템 진입점
├── database/
│   ├── schemas/
│   │   └── schema_definitions.py   # DB 스키마 정의
│   └── storage/
│       ├── hr_information/          # HR 데이터베이스
│       └── sales_performance/       # 영업 실적 데이터베이스
└── test files                       # 테스트 파일들
```

### 1.2 핵심 기술 스택
- **LangGraph 0.6.7**: 워크플로우 오케스트레이션
- **LangChain**: LLM 통합 프레임워크
- **OpenAI GPT-4o/GPT-4o-mini**: LLM 모델
- **SQLite**: 데이터 저장소
- **Pandas**: 데이터 분석
- **AsyncIO**: 비동기 처리

---

## 2. 전체 아키텍처

### 2.1 메인 오케스트레이터 구조

**파일**: `backend/service/orchestrator/orchestrator.py`

```python
class MainOrchestrator:
    def __init__(self):
        self.workflow = StateGraph(MainState)
        self.checkpointer = None  # AsyncSqliteSaver (선택적)

        # 5개 서브그래프 초기화
        self.intent_analyzer = IntentAnalysisSubGraph()
        self.planner = PlanningSubGraph()
        self.agent_executor = AgentExecutionSubGraph()
        self.evaluator = ResultEvaluationSubGraph()
        self.response_generator = ResponseGenerationSubGraph()
```

### 2.2 워크플로우 노드 구성

메인 워크플로우는 7개의 핵심 노드로 구성:

1. **authenticate** (`authenticate_user`): 사용자 인증 및 초기화
2. **analyze_intent** (`analyze_intent_subgraph`): 의도 분석 서브그래프 실행
3. **create_plan** (`planning_subgraph`): 실행 계획 수립
4. **execute_agents** (`agent_execution_subgraph`): 에이전트 병렬/순차 실행
5. **evaluate_results** (`evaluation_subgraph`): 결과 검증 및 평가
6. **generate_response** (`response_generation_subgraph`): 최종 응답 생성
7. **store_memory** (`store_conversation`): 대화 내용 저장

### 2.3 조건부 라우팅 로직

```python
# 계획 검증 분기
"create_plan" → check_plan_validity → {
    "valid": "execute_agents",
    "need_clarification": "generate_response",
    "invalid": END
}

# 실행 결과 분기
"execute_agents" → check_execution_status → {
    "success": "evaluate_results",
    "partial_success": "evaluate_results",
    "retry": "execute_agents",  # 재시도
    "failure": "generate_response"
}

# 평가 결과 분기
"evaluate_results" → check_evaluation → {
    "approved": "generate_response",
    "need_revision": "execute_agents",  # 재실행
    "compliance_issue": "generate_response"
}
```

---

## 3. 사용자 입력-출력 흐름 분석

### 3.1 시작점: supervisor.py

**파일**: `backend/service/supervisor.py`

```python
async def main():
    orchestrator = MainOrchestrator()
    app = orchestrator.workflow.compile(
        checkpointer=orchestrator.checkpointer
    )

    user_input = {
        "user_id": "pharm_user_001",
        "session_id": "session_123",
        "user_query": "지난 분기 서울 지역 거래처별 매출 실적을 분석하고...",
        "timestamp": datetime.now().isoformat()
    }

    # 스트리밍 실행
    async for event in app.astream(
        user_input,
        config={"configurable": {"thread_id": "thread_123"}},
        stream_mode="values"
    ):
        print(f"Current State: {event}")
```

### 3.2 MainState 구조

**파일**: `backend/service/orchestrator/orchestrator.py:17-49`

```python
class MainState(TypedDict):
    # 기본 정보
    user_id: str
    session_id: str
    user_query: str
    timestamp: str

    # 의도 및 계획
    intents: List[Dict[str, Any]]
    execution_plan: Dict[str, Any]
    priority_level: str  # high, medium, low

    # 실행 관련
    active_agents: List[str]
    agent_results: Dict[str, Any]
    parallel_execution: bool

    # 결과 및 검증
    raw_results: Dict[str, Any]
    validated_results: Dict[str, Any]
    compliance_status: Dict[str, Any]

    # 응답
    final_response: str
    response_format: str  # text, table, chart, document
    confidence_score: float

    # 메타데이터
    error_logs: List[str]
    execution_time: float
    tokens_used: int
    need_human_review: bool
    conversation_history: List[Dict]
```

### 3.3 실행 흐름 시퀀스

```
1. 사용자 입력 → supervisor.py
   ↓
2. MainOrchestrator 초기화
   ↓
3. authenticate_user
   - State 초기화
   - 필수 필드 설정
   ↓
4. analyze_intent_subgraph
   - IntentAnalysisSubGraph 실행
   - LLM 호출 (GPT-4o-mini)
   - 의도 분류 및 엔티티 추출
   ↓
5. planning_subgraph
   - PlanningSubGraph 실행
   - 의존성 분석
   - 병렬/순차 실행 계획
   ↓
6. agent_execution_subgraph
   - AgentExecutionSubGraph 실행
   - 동적 에이전트 임포트
   - 병렬/순차 실행
   ↓
7. evaluation_subgraph
   - ResultEvaluationSubGraph 실행
   - 품질 검증
   - 규정 준수 확인
   ↓
8. response_generation_subgraph
   - ResponseGenerationSubGraph 실행
   - 포맷 선택 (text/table/chart/document)
   - 최종 응답 생성
   ↓
9. store_conversation
   - 대화 내용 저장
   ↓
10. 최종 응답 반환
```

---

## 4. LLM 통합 및 관리

### 4.1 LLMManager 싱글톤 패턴

**파일**: `backend/service/utils/llm_manager.py`

```python
class LLMManager:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

### 4.2 모델별 용도 분류

```python
self.clients = {
    # 일반 대화용 (창의적)
    "openai": ChatOpenAI(
        model="gpt-4o",
        temperature=0.7,
        max_retries=3
    ),

    # SQL, 규정 검토용 (정확성)
    "openai_strict": ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        max_retries=3
    ),

    # 빠른 응답용 (의도분석, 간단한 작업)
    "openai_mini": ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        max_retries=3
    ),

    # 문서 생성용 (균형잡힌 창의성)
    "openai_doc": ChatOpenAI(
        model="gpt-4o",
        temperature=0.5,
        max_retries=3
    )
}
```

### 4.3 LLM 호출 프로세스

```python
async def generate(self, prompt, model="openai", system_prompt=None,
                  category=None, use_cache=True, **kwargs):
    # 1. 캐시 확인
    if use_cache:
        cache_key = self._get_cache_key(prompt, model, system_prompt)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

    # 2. LLM 호출
    client = self.clients.get(model)
    messages = [SystemMessage(system_prompt), HumanMessage(prompt)]
    response = await client.ainvoke(messages, **kwargs)

    # 3. 토큰 추적
    self._track_usage(usage, model, category)

    # 4. 캐시 저장
    if use_cache:
        self._save_to_cache(cache_key, result)

    return result
```

### 4.4 프롬프트 템플릿 시스템

**파일**: `backend/service/utils/prompt_templates.py`

주요 템플릿 카테고리:
- **intent_analysis**: 의도 분석용 프롬프트
- **text_to_sql**: SQL 쿼리 생성
- **planning**: 실행 계획 수립
- **document_generation**: 문서 생성
- **compliance_check**: 규정 검토
- **response_generation**: 응답 생성
- **search**: 검색 최적화

---

## 5. 서브그래프 상세 분석

### 5.1 IntentAnalysisSubGraph

**파일**: `backend/service/orchestrator/intent_analysis.py`

#### 노드 구성:
1. **tokenize** → 쿼리 토큰화
2. **extract_entities** → 엔티티 추출 (기간, 지역 등)
3. **classify_intent** → LLM 기반 의도 분류
4. **validate_intent** → 의도 검증
5. **resolve_ambiguity** → 모호성 해결

#### LLM 호출 부분:
```python
async def classify_intent(self, state):
    prompt = self.prompt_templates.get_prompt(
        category="intent_analysis",
        version="v1",
        user_query=state['user_query']
    )

    response = await self.llm_manager.generate(
        prompt=prompt,
        model="openai_mini",  # 빠른 응답
        category="intent_analysis",
        temperature=0.3  # 일관된 분류
    )

    # JSON 파싱 및 State 업데이트
    result = json.loads(response['content'])
    state["intents"] = result.get("intents", [])
    state["ambiguous"] = result.get("ambiguous", False)
```

### 5.2 PlanningSubGraph

**파일**: `backend/service/orchestrator/planning.py`

#### 노드 구성:
1. **analyze_dependencies** → 의존성 분석
2. **optimize_sequence** → 병렬/순차 최적화
3. **allocate_resources** → 리소스 할당
4. **create_execution_plan** → 실행 계획 생성

#### 병렬 실행 최적화:
```python
async def optimize_execution_sequence(self, state):
    parallel_groups = []
    sequential_tasks = []

    for intent in state['intents']:
        if intent['type'] in ['sales_analysis', 'client_analysis']:
            # 데이터 분석은 병렬 실행 가능
            parallel_groups.append(intent)
        elif intent['type'] == 'compliance_check':
            # 규정 검토는 순차 실행
            sequential_tasks.append(intent)

    state['parallel_groups'] = parallel_groups
```

### 5.3 AgentExecutionSubGraph

**파일**: `backend/service/orchestrator/agent_execution.py`

#### 노드 구성:
1. **prepare_execution** → 실행 준비
2. **execute_parallel** / **execute_sequential** → 실행 전략
3. **merge_results** → 결과 병합
4. **validate_results** → 결과 검증
5. **handle_failures** → 실패 처리

#### 동적 에이전트 임포트:
```python
async def _execute_single_agent(self, agent_name: str, input_data: Dict):
    if agent_name == "sales_analytics":
        from ..agents.sales_analytics_agent import SalesAnalyticsAgent
        agent = SalesAnalyticsAgent()
    elif agent_name == "internal_search":
        from ..agents.search_agent import SearchAgent
        agent = SearchAgent()
    # ... 기타 에이전트

    result = await agent.execute(input_data)
    return result
```

#### 병렬 실행 구현:
```python
async def execute_parallel_agents(self, state):
    tasks = []
    for agent_name in group:
        task = self._execute_single_agent(
            agent_name,
            state["agent_inputs"].get(agent_name, {})
        )
        tasks.append((agent_name, task))

    # asyncio.gather로 병렬 실행
    results = await asyncio.gather(
        *[task for _, task in tasks],
        return_exceptions=True
    )
```

### 5.4 ResultEvaluationSubGraph

**파일**: `backend/service/orchestrator/result_evaluation.py`

#### 노드 구성:
1. **check_completeness** → 완전성 확인
2. **validate_accuracy** → 정확성 검증
3. **check_compliance** → 규정 준수 확인
4. **calculate_quality** → 품질 점수 계산
5. **generate_recommendations** → 개선 권고사항

#### 품질 평가 로직:
```python
def check_quality_threshold(self, state) -> str:
    overall_score = state.get("quality_scores", {}).get("overall", 0)
    if overall_score >= 0.8:
        return "high_quality"
    elif overall_score >= 0.5:
        return "needs_improvement"
    else:
        return "low_quality"
```

### 5.5 ResponseGenerationSubGraph

**파일**: `backend/service/orchestrator/response_generation.py`

#### 노드 구성:
1. **format_selection** → 포맷 선택
2. **generate_text/table/chart/document** → 포맷별 생성
3. **add_citations** → 참조 추가
4. **final_review** → 최종 검토

#### 포맷 라우팅:
```python
def route_by_format(self, state) -> str:
    format_type = state.get("response_format", "text")
    if format_type in ["text", "table", "chart", "document"]:
        return format_type
    return "text"
```

---

## 6. 에이전트 구현 분석

### 6.1 SalesAnalyticsAgent

**파일**: `backend/service/agents/sales_analytics_agent.py`

#### 워크플로우 노드:
1. **parse_query** → 쿼리 파싱 (기간, 지역 추출)
2. **generate_sql** → Text2SQL 변환 (LLM 호출)
3. **execute_query** → SQL 실행
4. **analyze_data** → 데이터 분석
5. **visualize** → 시각화 설정

#### Text2SQL 구현:
```python
async def text_to_sql(self, state):
    # 스키마 정보 로드
    schema_info = await self.load_schema_info()

    system_prompt = f"""
    You are a SQL expert for pharmaceutical sales data analysis.
    Database Schema: {schema_info}
    Rules:
    1. Only generate SELECT queries
    2. Always use proper JOINs
    3. Include date filters
    4. Limit results to 1000 rows
    """

    response = await self.llm_manager.generate(
        prompt=prompt,
        system_prompt=system_prompt,
        model="openai_strict",  # 정확성 중요
        temperature=0
    )

    sql_query = response['content'].strip()

    # SQL 주입 방지 검증
    if not self._validate_sql(sql_query):
        sql_query = "SELECT 'Error: Invalid SQL generated' as error"
```

#### SQL 검증 로직:
```python
def _validate_sql(self, sql: str) -> bool:
    sql_upper = sql.upper()

    # 위험한 명령어 체크
    dangerous = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'CREATE', 'ALTER']
    for keyword in dangerous:
        if keyword in sql_upper:
            return False

    # SELECT 쿼리인지 확인
    if not sql_upper.strip().startswith('SELECT'):
        return False

    return True
```

#### 데이터베이스 연결:
```python
self.db_paths = {
    "clients": os.getenv("CLIENTS_DB_PATH", "./database/storage/sales_performance/clients_db.db"),
    "clients_info": os.getenv("CLIENTS_INFO_PATH", "./database/storage/sales_performance/clients_info.db"),
    "sales_performance": os.getenv("SALES_PERFORMANCE_PATH", "./database/storage/sales_performance/sales_performance_db.db"),
    "sales_target": os.getenv("SALES_TARGET_PATH", "./database/storage/sales_performance/sales_target_db.db")
}
```

### 6.2 기타 에이전트 (구현 예정)

- **SearchAgent**: 내부 검색 (HR, 규정)
- **DocumentGenerationAgent**: 보고서 생성
- **ComplianceCheckAgent**: 규정 준수 검토

---

## 7. 데이터 계층 분석

### 7.1 데이터베이스 구조

**파일**: `database/schemas/schema_definitions.py`

#### HR 데이터베이스:
```python
HR_SCHEMA = {
    "database": "hr_data.db",
    "tables": {
        "인사자료": TableInfo(
            columns=[
                "사번", "성명", "본부", "직급", "부서",
                "지점", "연락처", "월평균사용예산",
                "최근 평가", "기본급", "성과급", "책임업무"
            ]
        ),
        "지점연락처": TableInfo(
            columns=["본부", "부서", "지점", "지점 연락처"]
        )
    }
}
```

#### 영업 데이터베이스:
```python
SALES_SCHEMA = {
    "clients_db": {
        "거래처자료": TableInfo(
            columns=["거래처ID", "월", "매출", "월방문횟수",
                    "사용 예산", "총환자수", "담당자"]
        )
    },
    "sales_performance": {
        "sales_performance": TableInfo(
            columns=["사번", "담당자", "거래처ID", "품목",
                    "202212", "202301", ..., "202411"]  # 월별 실적
        )
    }
}
```

### 7.2 스키마 관리 함수

```python
def get_table_schema(database_name: str, table_name: str) -> TableInfo
def get_database_path(database_name: str) -> str
def list_all_tables() -> List[tuple]
```

---

## 8. State 관리 메커니즘

### 8.1 State 전파 방식

1. **메인 State → 서브그래프 State**:
```python
async def analyze_intent_subgraph(self, state: MainState):
    # 서브그래프용 State 준비
    intent_state = {
        "user_query": state.get("user_query", ""),
        "tokens": [],
        "entities": [],
        "intents": [],
        "confidence_scores": {},
        "ambiguous": False
    }

    # 서브그래프 실행
    app = self.intent_analyzer.workflow.compile()
    result = await app.ainvoke(intent_state)

    # 결과를 메인 State에 병합
    state["intents"] = result.get("intents", [])
    state["confidence_score"] = max(result.get("confidence_scores", {}).values(), default=0.0)
```

### 8.2 State 초기화 및 기본값

```python
async def authenticate_user(self, state: MainState):
    # 필수 필드 초기화
    if "error_logs" not in state:
        state["error_logs"] = []
    if "conversation_history" not in state:
        state["conversation_history"] = []
    if "tokens_used" not in state:
        state["tokens_used"] = 0
```

### 8.3 에러 State 관리

```python
except Exception as e:
    logger.error(f"Intent analysis failed: {e}")
    state["intents"] = []
    state["error_logs"] = state.get("error_logs", [])
    state["error_logs"].append(f"Intent analysis: {str(e)}")
```

---

## 9. 개선 제안 및 권고사항

### 9.1 구조적 개선점

#### 1. **Checkpointer 구현 필요**
```python
# 현재: self.checkpointer = None
# 개선안:
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
self.checkpointer = AsyncSqliteSaver.from_path("./database/checkpointer/checkpoints.db")
```

#### 2. **API 계층 구현 필요**
- FastAPI/Flask 엔드포인트 추가
- WebSocket 지원 (스트리밍 응답)
- 인증/권한 관리

#### 3. **에이전트 추상 클래스 도입**
```python
class BaseAgent(ABC):
    @abstractmethod
    async def execute(self, input_data: Dict) -> Dict:
        pass

    @abstractmethod
    def validate_input(self, input_data: Dict) -> bool:
        pass
```

### 9.2 에러 처리 강화

#### 1. **구체적인 에러 타입 정의**
```python
class IntentAnalysisError(Exception): pass
class SQLGenerationError(Exception): pass
class AgentExecutionError(Exception): pass
```

#### 2. **재시도 로직 개선**
```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def execute_with_retry(self, agent_name, input_data):
    return await self._execute_single_agent(agent_name, input_data)
```

### 9.3 성능 최적화

#### 1. **연결 풀링 구현**
```python
from sqlalchemy.pool import QueuePool
engine = create_engine('sqlite:///database.db',
                       poolclass=QueuePool,
                       pool_size=5)
```

#### 2. **배치 처리 최적화**
```python
async def execute_agents_batch(self, agents, batch_size=5):
    for i in range(0, len(agents), batch_size):
        batch = agents[i:i+batch_size]
        await asyncio.gather(*[self.execute(a) for a in batch])
```

### 9.4 모니터링 및 로깅

#### 1. **구조화된 로깅**
```python
import structlog
logger = structlog.get_logger()

logger.info("agent_execution",
           agent=agent_name,
           duration=execution_time,
           status="success",
           tokens_used=token_count)
```

#### 2. **메트릭 수집**
```python
from prometheus_client import Counter, Histogram

request_count = Counter('chatbot_requests_total', 'Total requests')
response_time = Histogram('chatbot_response_seconds', 'Response time')
```

### 9.5 테스트 커버리지

#### 1. **단위 테스트 추가**
```python
@pytest.mark.asyncio
async def test_intent_analysis():
    analyzer = IntentAnalysisSubGraph()
    state = {"user_query": "지난달 매출 분석"}
    result = await analyzer.workflow.compile().ainvoke(state)
    assert "intents" in result
    assert len(result["intents"]) > 0
```

#### 2. **통합 테스트 구현**
```python
async def test_end_to_end_flow():
    orchestrator = MainOrchestrator()
    result = await orchestrator.process_query(
        "서울 지역 거래처 매출 분석"
    )
    assert result["final_response"] is not None
```

### 9.6 보안 강화

#### 1. **입력 검증 강화**
```python
def sanitize_user_input(query: str) -> str:
    # XSS, SQL 인젝션 방지
    query = html.escape(query)
    query = query.replace("'", "''")
    return query[:1000]  # 길이 제한
```

#### 2. **API 키 관리**
```python
from cryptography.fernet import Fernet

def encrypt_api_key(key: str) -> bytes:
    cipher = Fernet(os.getenv("ENCRYPTION_KEY"))
    return cipher.encrypt(key.encode())
```

### 9.7 문서화 개선

#### 1. **API 문서 자동 생성**
```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="NaruTalk Chatbot API",
        version="1.0.0",
        description="제약회사 AI 챗봇 API",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema
```

---

## 결론

이 LangGraph 0.6.7 기반 챗봇 시스템은 다음과 같은 특징을 가지고 있습니다:

### 강점:
1. **모듈화된 구조**: 서브그래프로 분리된 명확한 책임
2. **병렬 처리 지원**: AsyncIO를 활용한 효율적인 실행
3. **유연한 LLM 관리**: 용도별 모델 분류 및 캐싱
4. **확장 가능한 에이전트 시스템**: 동적 임포트 및 실행

### 개선 필요 사항:
1. **API 계층 구현**
2. **에러 처리 및 재시도 로직 강화**
3. **테스트 커버리지 확대**
4. **모니터링 및 로깅 체계 구축**
5. **보안 강화 (입력 검증, 암호화)**

이 시스템은 제약회사의 복잡한 비즈니스 요구사항을 처리할 수 있는 견고한 기반을 제공하며,
위의 개선사항들을 적용하면 프로덕션 환경에서도 안정적으로 운영할 수 있을 것입니다.