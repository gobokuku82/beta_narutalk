# 함수 참조 문서 (Function Reference)
> 모든 주요 함수의 입력/출력 명세 및 사용 예시

## 목차
1. [Backend API Functions](#backend-api-functions)
2. [Supervisor Functions](#supervisor-functions)
3. [Worker Agent Functions](#worker-agent-functions)
4. [Database Functions](#database-functions)
5. [Utility Functions](#utility-functions)

---

## Backend API Functions

### Main Application (backend/api/main.py)

#### lifespan
```python
@asynccontextmanager
async def lifespan(app: FastAPI)
```
- **용도**: 애플리케이션 생명주기 관리
- **입력**:
  - `app`: FastAPI - FastAPI 애플리케이션 인스턴스
- **출력**: AsyncGenerator
- **동작**:
  - Startup: 설정 검증, Supervisor 초기화
  - Shutdown: 리소스 정리
- **예외**: `StartupError`, `ShutdownError`

#### root
```python
@app.get("/")
async def root() -> Dict[str, Any]
```
- **용도**: API 루트 엔드포인트
- **입력**: None
- **출력**:
  ```python
  {
    "service": str,      # 서비스 이름
    "version": str,      # 버전
    "status": str,       # "running"
    "docs": str,         # "/docs"
    "health": str        # "/api/v1/health"
  }
  ```

### Chat Routes (backend/api/routes/chat.py)

#### chat
```python
@router.post("/chat")
async def chat(
    request: ChatRequest,
    supervisor: SupervisorService = Depends(get_supervisor_service),
    cache: SQLiteMemoryCache = Depends(get_cache_manager)
) -> ChatResponse
```
- **용도**: 메인 대화 처리 엔드포인트
- **입력**:
  ```python
  ChatRequest:
    query: str                    # 사용자 질문
    user_id: Optional[str]        # 사용자 ID
    session_id: Optional[str]     # 세션 ID
    context: Optional[Dict]       # 추가 컨텍스트
    use_cache: bool = True        # 캐시 사용 여부
  ```
- **출력**:
  ```python
  ChatResponse:
    status: str                   # "success" | "error"
    result: Dict[str, Any]        # 처리 결과
    session_id: str               # 세션 ID
    metadata: Dict[str, Any]      # 메타데이터
    error: Optional[str]          # 에러 메시지
  ```
- **예외**: `ProcessingError`, `TimeoutError`

#### chat_stream
```python
@router.get("/chat/stream")
async def chat_stream(
    query: str = Query(...),
    user_id: Optional[str] = Query(None),
    session_id: Optional[str] = Query(None)
) -> StreamingResponse
```
- **용도**: SSE 기반 스트리밍 응답
- **입력**: Query parameters (query, user_id, session_id)
- **출력**: Server-Sent Events 스트림
  ```
  event: progress
  data: {"type": "progress", "step": 1, "total": 5}

  event: token
  data: {"type": "token", "content": "답변"}

  event: result
  data: {"type": "result", "content": {...}}
  ```

### Session Routes (backend/api/routes/sessions.py)

#### list_sessions
```python
@router.get("/")
async def list_sessions(
    user_id: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    supervisor: SupervisorService = Depends(get_supervisor_service)
) -> SessionListResponse
```
- **용도**: 활성 세션 목록 조회
- **입력**:
  - `user_id`: Optional[str] - 특정 사용자 필터
  - `limit`: int - 최대 결과 수 (기본 100, 최대 1000)
- **출력**:
  ```python
  SessionListResponse:
    sessions: List[SessionInfo]
    total: int
  ```

#### get_session_history
```python
@router.get("/{session_id}/history")
async def get_session_history(
    session_id: str,
    limit: int = Query(50, le=500),
    supervisor: SupervisorService = Depends(get_supervisor_service)
) -> SessionHistory
```
- **용도**: 세션 대화 이력 조회
- **입력**:
  - `session_id`: str - 세션 식별자
  - `limit`: int - 메시지 수 제한
- **출력**:
  ```python
  SessionHistory:
    session_id: str
    messages: List[Message]
    metadata: Dict[str, Any]
  ```

### Service Layer (backend/api/services/)

#### SupervisorService.process_chat
```python
async def process_chat(
    self,
    query: str,
    user_context: Optional[Dict] = None,
    use_cache: bool = True
) -> Dict[str, Any]
```
- **용도**: 대화 처리 핵심 로직
- **입력**:
  - `query`: str - 사용자 쿼리
  - `user_context`: Dict - 사용자 컨텍스트
  - `use_cache`: bool - 캐시 사용 여부
- **출력**:
  ```python
  {
    "response": str,           # AI 응답
    "metadata": {
      "intent": str,          # 분석된 의도
      "confidence": float,    # 신뢰도
      "processing_time": float,
      "agents_used": List[str]
    },
    "session_id": str
  }
  ```

#### SQLiteMemoryCache.get
```python
async def get(self, key: str) -> Optional[Any]
```
- **용도**: 캐시에서 값 조회
- **입력**: `key`: str - 캐시 키
- **출력**: Optional[Any] - 캐시된 값 또는 None
- **동작**:
  1. 만료 시간 확인
  2. 히트 카운트 증가
  3. 값 역직렬화

#### SQLiteMemoryCache.set
```python
async def set(
    self,
    key: str,
    value: Any,
    ttl: Optional[int] = None
) -> bool
```
- **용도**: 캐시에 값 저장
- **입력**:
  - `key`: str - 캐시 키
  - `value`: Any - 저장할 값
  - `ttl`: Optional[int] - Time To Live (초)
- **출력**: bool - 성공 여부
- **동작**:
  1. 값 직렬화 (pickle)
  2. 만료 시간 설정
  3. LRU 정책 적용

---

## Supervisor Functions

### Main Supervisor (backend/service/supervisor/main_supervisor_v2.py)

#### MedicalSupervisorV2.execute_with_context
```python
async def execute_with_context(
    self,
    query: str,
    user_context: Dict[str, Any],
    session_id: Optional[str] = None
) -> Dict[str, Any]
```
- **용도**: 컨텍스트 기반 쿼리 실행
- **입력**:
  - `query`: str - 사용자 쿼리
  - `user_context`: Dict - 사용자 컨텍스트
  - `session_id`: str - 세션 ID
- **출력**:
  ```python
  {
    "response": str,
    "status": str,
    "metadata": {
      "execution_time": float,
      "tokens_used": int,
      "agents_executed": List[str],
      "confidence_score": float
    }
  }
  ```
- **프로세스**:
  1. 의도 분석
  2. 실행 계획 수립
  3. 에이전트 선택 및 실행
  4. 결과 집계

#### MedicalSupervisorV2._create_sql_query_tool
```python
def _create_sql_query_tool(self) -> Tool
```
- **용도**: SQL 실행 도구 생성
- **입력**: None (self 참조)
- **출력**: Tool - LangChain Tool 인스턴스
- **도구 시그니처**:
  ```python
  async def execute_sql(query: str) -> str
  ```
- **데이터베이스 선택 로직**:
  - HR 키워드 → hr_data.db
  - 매출/성과 → sales_performance_db.db
  - 규정 → rules.db

### Intent Analyzer (backend/service/supervisor/intent_analyzer.py)

#### EnhancedIntentAnalyzer.analyze
```python
async def analyze(
    self,
    query: str,
    context: Optional[Dict] = None
) -> IntentAnalysisResult
```
- **용도**: 사용자 의도 분석
- **입력**:
  - `query`: str - 분석할 쿼리
  - `context`: Dict - 추가 컨텍스트
- **출력**:
  ```python
  IntentAnalysisResult:
    intent: IntentClassification
      category: str           # "data_analysis" | "information_retrieval" | ...
      confidence: float       # 0.0 ~ 1.0
      sub_intents: List[str]
    entities: EntityExtraction
      medical_terms: List[str]
      time_ranges: List[DateRange]
      numeric_values: List[NumericValue]
    complexity: QueryComplexity
      level: str              # "simple" | "moderate" | "complex"
      estimated_time: float   # 예상 처리 시간 (초)
    ambiguity: AmbiguityDetection
      is_ambiguous: bool
      clarification_needed: List[str]
  ```

### Planner (backend/service/supervisor/planner.py)

#### SmartPlanner.create_plan
```python
def create_plan(
    self,
    intent_analysis: IntentAnalysisResult,
    available_agents: List[str],
    constraints: Optional[PlanConstraints] = None
) -> ExecutionPlan
```
- **용도**: 실행 계획 수립
- **입력**:
  - `intent_analysis`: IntentAnalysisResult - 의도 분석 결과
  - `available_agents`: List[str] - 사용 가능한 에이전트
  - `constraints`: PlanConstraints - 제약 조건
- **출력**:
  ```python
  ExecutionPlan:
    tasks: List[TaskNode]
      id: str
      name: str
      agent_type: str
      dependencies: List[str]
      priority: int
      estimated_time: float
    execution_strategy: str    # "sequential" | "parallel" | "mixed"
    dependency_graph: nx.DiGraph
    estimated_total_time: float
  ```

### Agent Selector (backend/service/supervisor/agent_selector.py)

#### DynamicAgentSelector.select_agents
```python
def select_agents(
    self,
    tasks: List[TaskNode],
    available_agents: Dict[str, AgentProfile],
    selection_criteria: Optional[SelectionCriteria] = None
) -> Dict[str, str]
```
- **용도**: 작업에 적합한 에이전트 선택
- **입력**:
  - `tasks`: List[TaskNode] - 실행할 작업 목록
  - `available_agents`: Dict[str, AgentProfile] - 에이전트 프로필
  - `selection_criteria`: SelectionCriteria - 선택 기준
- **출력**:
  ```python
  Dict[str, str]  # {task_id: agent_name}
  ```
- **점수 계산**:
  ```python
  score = (
    capability_match * 0.4 +
    (1 - current_load) * 0.2 +
    success_rate * 0.2 +
    (1 - avg_response_time) * 0.1 +
    domain_expertise * 0.1
  )
  ```

### Execution Manager (backend/service/supervisor/execution_manager.py)

#### ParallelExecutionManager.execute
```python
async def execute(
    self,
    plan: ExecutionPlan,
    agent_assignments: Dict[str, str],
    state: MedicalSupervisorState,
    max_parallel: int = 5
) -> ExecutionResult
```
- **용도**: 실행 계획 처리
- **입력**:
  - `plan`: ExecutionPlan - 실행 계획
  - `agent_assignments`: Dict - 에이전트 할당
  - `state`: MedicalSupervisorState - 현재 상태
  - `max_parallel`: int - 최대 병렬 수
- **출력**:
  ```python
  ExecutionResult:
    status: str               # "success" | "partial" | "failed"
    results: Dict[str, Any]   # {task_id: result}
    errors: List[TaskError]
    metrics: ExecutionMetrics
      total_time: float
      task_times: Dict[str, float]
      parallel_efficiency: float
  ```

---

## Worker Agent Functions

### SQL Analysis Agent (backend/service/worker_agents/sql_analysis_agent.py)

#### SQLAnalysisAgent.analyze
```python
async def analyze(
    self,
    query: str,
    context: Dict[str, Any],
    database: str = "hr"
) -> SQLAnalysisResult
```
- **용도**: SQL 기반 데이터 분석
- **입력**:
  - `query`: str - 자연어 쿼리
  - `context`: Dict - 분석 컨텍스트
  - `database`: str - 대상 데이터베이스
- **출력**:
  ```python
  SQLAnalysisResult:
    sql_query: str            # 생성된 SQL
    results: List[Dict]       # 쿼리 결과
    analysis: Dict            # 분석 결과
      summary: str
      insights: List[str]
      statistics: Dict
    visualization: Optional[Dict]  # 차트 데이터
  ```
- **프로세스**:
  1. Text2SQL 변환
  2. 쿼리 검증 및 실행
  3. 결과 분석
  4. 인사이트 생성

### Information Retrieval Agent (backend/service/worker_agents/information_retrieval_agent.py)

#### InformationRetrievalAgent.search
```python
async def search(
    self,
    query: str,
    sources: List[str] = ["all"],
    filters: Optional[SearchFilters] = None,
    limit: int = 10
) -> SearchResult
```
- **용도**: 멀티소스 정보 검색
- **입력**:
  - `query`: str - 검색 쿼리
  - `sources`: List[str] - 검색 소스
  - `filters`: SearchFilters - 필터 조건
  - `limit`: int - 결과 수 제한
- **출력**:
  ```python
  SearchResult:
    total_results: int
    results: List[SearchItem]
      source: str
      title: str
      content: str
      relevance_score: float
      metadata: Dict
    aggregated_summary: str
  ```

### Document Generation Agent (backend/service/worker_agents/document_generation_agent.py)

#### DocumentGenerationAgent.generate
```python
async def generate(
    self,
    doc_type: str,
    data: Dict[str, Any],
    template: Optional[str] = None,
    format: str = "pdf"
) -> GeneratedDocument
```
- **용도**: 문서 생성
- **입력**:
  - `doc_type`: str - 문서 유형
  - `data`: Dict - 문서 데이터
  - `template`: str - 템플릿 이름
  - `format`: str - 출력 형식
- **출력**:
  ```python
  GeneratedDocument:
    document_id: str
    type: str
    format: str
    content: Union[str, bytes]
    metadata: Dict
      created_at: datetime
      size: int
      pages: int
  ```

### Compliance Validation Agent (backend/service/worker_agents/compliance_validation_agent.py)

#### ComplianceValidationAgent.validate
```python
async def validate(
    self,
    document: Union[str, Dict],
    rules: List[str] = ["all"],
    strict_mode: bool = False
) -> ValidationResult
```
- **용도**: 규정 준수 검증
- **입력**:
  - `document`: Union[str, Dict] - 검증할 문서
  - `rules`: List[str] - 적용할 규칙
  - `strict_mode`: bool - 엄격 모드
- **출력**:
  ```python
  ValidationResult:
    is_compliant: bool
    compliance_score: float    # 0.0 ~ 1.0
    violations: List[Violation]
      rule_id: str
      severity: str           # "critical" | "major" | "minor"
      description: str
      location: str
    recommendations: List[str]
  ```

---

## Database Functions

### CRUD Operations (database/system/crud.py)

#### create_conversation
```python
async def create_conversation(
    db: AsyncSession,
    conversation: ConversationCreate
) -> Conversation
```
- **용도**: 새 대화 생성
- **입력**:
  ```python
  ConversationCreate:
    user_id: str
    title: Optional[str]
    metadata: Optional[Dict]
  ```
- **출력**: Conversation 모델 인스턴스
- **SQL**:
  ```sql
  INSERT INTO conversations (id, user_id, title, created_at, metadata)
  VALUES (?, ?, ?, ?, ?)
  ```

#### create_message
```python
async def create_message(
    db: AsyncSession,
    message: MessageCreate
) -> Message
```
- **용도**: 메시지 생성 with 자동 시퀀싱
- **입력**:
  ```python
  MessageCreate:
    conversation_id: str
    role: MessageRole        # "user" | "assistant" | "system"
    content: str
    metadata: Optional[Dict]
  ```
- **출력**: Message 모델 인스턴스
- **특징**: 시퀀스 번호 자동 할당

#### create_or_update_agent_state
```python
async def create_or_update_agent_state(
    db: AsyncSession,
    state: AgentStateCreate
) -> AgentState
```
- **용도**: 에이전트 상태 Upsert
- **입력**:
  ```python
  AgentStateCreate:
    conversation_id: str
    agent_type: AgentType
    state_data: Dict
    execution_status: ExecutionStatus
  ```
- **출력**: AgentState 모델 인스턴스
- **동작**: 존재하면 업데이트, 없으면 생성

### Database Manager (database/system/db_manager.py)

#### DatabaseManager.execute_query
```python
async def execute_query(
    self,
    db_name: str,
    query: str,
    params: Optional[Dict] = None,
    timeout: int = 30
) -> List[Dict[str, Any]]
```
- **용도**: 데이터베이스 쿼리 실행
- **입력**:
  - `db_name`: str - 데이터베이스 이름
  - `query`: str - SQL 쿼리
  - `params`: Dict - 쿼리 파라미터
  - `timeout`: int - 타임아웃 (초)
- **출력**: List[Dict] - 쿼리 결과
- **예외**: `TimeoutError`, `DatabaseError`

#### DatabaseManager.get_table_schema
```python
def get_table_schema(
    self,
    db_name: str,
    table_name: str
) -> TableSchema
```
- **용도**: 테이블 스키마 조회
- **입력**:
  - `db_name`: str - 데이터베이스 이름
  - `table_name`: str - 테이블 이름
- **출력**:
  ```python
  TableSchema:
    table_name: str
    columns: List[ColumnInfo]
      name: str
      type: str
      nullable: bool
      primary_key: bool
      default: Any
    indexes: List[IndexInfo]
  ```

---

## Utility Functions

### Korean SQL Utils (backend/common/korean_sql_utils.py)

#### translate_korean_columns
```python
def translate_korean_columns(
    sql_query: str,
    schema_mapping: Dict[str, Dict[str, str]]
) -> str
```
- **용도**: 한글 컬럼명을 영문으로 변환
- **입력**:
  - `sql_query`: str - 한글 포함 SQL
  - `schema_mapping`: Dict - 매핑 정보
- **출력**: str - 영문 변환된 SQL
- **예시**:
  ```python
  # 입력: "SELECT 이름, 부서 FROM 직원"
  # 출력: "SELECT name, department FROM employees"
  ```

#### format_korean_output
```python
def format_korean_output(
    results: List[Dict],
    display_mapping: Dict[str, str]
) -> List[Dict]
```
- **용도**: 영문 결과를 한글로 포맷팅
- **입력**:
  - `results`: List[Dict] - 쿼리 결과
  - `display_mapping`: Dict - 표시 매핑
- **출력**: List[Dict] - 한글 포맷된 결과

### Cache Key Generation

#### generate_cache_key
```python
def generate_cache_key(
    query: str,
    context: Optional[Dict] = None,
    version: str = "v1"
) -> str
```
- **용도**: 캐시 키 생성
- **입력**:
  - `query`: str - 쿼리
  - `context`: Dict - 컨텍스트
  - `version`: str - 캐시 버전
- **출력**: str - 해시된 캐시 키
- **알고리즘**:
  ```python
  data = f"{version}:{query}:{json.dumps(context, sort_keys=True)}"
  return hashlib.sha256(data.encode()).hexdigest()[:16]
  ```

### Error Handling

#### handle_api_error
```python
def handle_api_error(
    error: Exception,
    context: Optional[Dict] = None
) -> JSONResponse
```
- **용도**: API 에러 처리 및 응답
- **입력**:
  - `error`: Exception - 발생한 예외
  - `context`: Dict - 에러 컨텍스트
- **출력**: JSONResponse with 적절한 상태 코드
- **매핑**:
  - `ValidationError` → 400
  - `NotFoundError` → 404
  - `TimeoutError` → 408
  - `Exception` → 500

### Performance Monitoring

#### measure_performance
```python
@contextmanager
def measure_performance(
    operation: str,
    metrics_collector: Optional[MetricsCollector] = None
)
```
- **용도**: 성능 측정 컨텍스트 매니저
- **입력**:
  - `operation`: str - 작업 이름
  - `metrics_collector`: MetricsCollector - 메트릭 수집기
- **사용법**:
  ```python
  with measure_performance("database_query"):
      result = await execute_query(...)
  # 자동으로 실행 시간 측정 및 기록
  ```

---

## 에러 처리 패턴

### Retry with Exponential Backoff
```python
async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
) -> Any
```
- **용도**: 지수 백오프를 이용한 재시도
- **입력**:
  - `func`: Callable - 실행할 함수
  - `max_retries`: int - 최대 재시도 횟수
  - `initial_delay`: float - 초기 지연 시간
  - `max_delay`: float - 최대 지연 시간
  - `exponential_base`: float - 지수 베이스
- **출력**: 함수 실행 결과
- **예시**:
  ```python
  result = await retry_with_backoff(
      lambda: api_client.request(),
      max_retries=5
  )
  ```

---

## 테스트 헬퍼 함수

### create_test_conversation
```python
def create_test_conversation(
    user_id: str = "test_user",
    **kwargs
) -> ConversationCreate
```
- **용도**: 테스트용 대화 생성
- **입력**: 대화 속성
- **출력**: ConversationCreate 인스턴스

### mock_llm_response
```python
def mock_llm_response(
    query: str,
    response_type: str = "default"
) -> str
```
- **용도**: LLM 응답 모킹
- **입력**:
  - `query`: str - 입력 쿼리
  - `response_type`: str - 응답 타입
- **출력**: str - 모킹된 응답

---

## 결론

이 함수 참조 문서는 NaruTalk 시스템의 모든 주요 함수에 대한 상세한 입력/출력 명세와 사용 예시를 제공합니다. 각 함수는 명확한 용도와 타입 안정성을 가지며, 체계적인 에러 처리와 성능 모니터링을 지원합니다. 이 문서는 개발자들이 시스템을 이해하고 효과적으로 사용할 수 있도록 돕는 중요한 참조 자료입니다.