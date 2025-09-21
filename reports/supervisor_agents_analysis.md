# Supervisor & Agents 분석 보고서
> LangGraph 기반 Multi-Agent 시스템 상세 분석

## 목차
1. [시스템 개요](#시스템-개요)
2. [Main Supervisor](#main-supervisor)
3. [Supervisor 컴포넌트](#supervisor-컴포넌트)
4. [Worker Agents](#worker-agents)
5. [워크플로우 분석](#워크플로우-분석)
6. [상태 관리](#상태-관리)

---

## 시스템 개요

### Multi-Agent 아키텍처
NaruTalk는 LangGraph 0.6.x 기반의 Supervisor-Worker 패턴을 구현한 Multi-Agent 시스템입니다.

```
사용자 쿼리
    ↓
Main Supervisor (조정자)
    ↓
┌──────────────────────────────────────┐
│  1. Intent Analyzer (의도 분석)       │
│  2. Planner (실행 계획 수립)          │
│  3. Agent Selector (에이전트 선택)    │
│  4. Execution Manager (실행 관리)     │
│  5. Context Manager (컨텍스트 최적화) │
└──────────────────────────────────────┘
    ↓
Worker Agents (실행)
    ↓
결과 집계 및 응답
```

---

## Main Supervisor

### **backend/service/supervisor/main_supervisor_v2.py**

#### MedicalSupervisorV2 클래스

##### 주요 속성
| 속성 | 타입 | 설명 |
|------|------|------|
| llm | BaseChatModel | LLM 인스턴스 |
| embeddings | Embeddings | 임베딩 모델 |
| agents | Dict[str, Agent] | Worker 에이전트 맵 |
| workflow | CompiledGraph | LangGraph 워크플로우 |
| checkpointer_pool | CheckpointerPool | 체크포인트 관리 |

##### 핵심 메소드

###### 1. 에이전트 초기화
```python
def _initialize_agents(self) -> Dict[str, Any]
```
- **SQL Analysis Agent**: Text2SQL 및 데이터 분석
- **Information Retrieval Agent**: 멀티소스 정보 검색
- **Document Generation Agent**: 문서 생성
- **Compliance Validation Agent**: 규정 검증

###### 2. 워크플로우 구성
```python
def build_supervisor_workflow(self) -> CompiledGraph
```
- **HandoffTools**: 에이전트 간 핸드오프
- **StateGraph**: 상태 기반 워크플로우
- **Checkpointing**: 실행 상태 저장

###### 3. 실행 메소드
```python
async def execute_with_context(
    query: str,
    user_context: Dict,
    session_id: str
) -> Dict
```
- **입력**: 쿼리, 컨텍스트, 세션 ID
- **처리**: 의도 분석 → 계획 → 실행 → 결과
- **출력**: 처리 결과 및 메타데이터

#### Database API 통합 도구

##### SQL 쿼리 도구
```python
def _create_sql_query_tool(self) -> Tool
```
- **데이터베이스 선택 로직**:
  - HR 관련 → hr_data.db
  - 매출/성과 → sales_performance_db.db
  - 규정/컴플라이언스 → rules.db, hr_rules.db

##### 스키마 조회 도구
```python
def _create_schema_retrieval_tool(self) -> Tool
```
- 테이블 구조 조회
- 컬럼 정보 및 타입
- 인덱스 정보

##### 정보 검색 도구
```python
def _create_search_tools(self) -> List[Tool]
```
- HR 정보 검색
- 규정 검색
- 논문 검색 (Mock)
- HIRA 데이터 검색 (Mock)

---

## Supervisor 컴포넌트

### **1. Intent Analyzer (intent_analyzer.py)**

#### EnhancedIntentAnalyzer 클래스

##### 분석 프로세스
```python
async def analyze(query: str, context: Dict) -> IntentAnalysisResult
```

###### 병렬 분석 작업
1. **의도 분류** (Intent Classification)
   - 카테고리: data_analysis, information_retrieval, document_generation, compliance_check
   - 신뢰도 점수 (0-1)

2. **엔티티 추출** (Entity Extraction)
   - 의료/제약 도메인 엔티티
   - 시간 범위 파싱
   - 수치 데이터 추출

3. **복잡도 평가** (Complexity Assessment)
   - Simple / Moderate / Complex
   - 예상 처리 시간
   - 필요 리소스 추정

4. **모호성 감지** (Ambiguity Detection)
   - 불명확한 부분 식별
   - 명확화 제안 생성

##### 컨텍스트 엔지니어링
```python
def _create_enhanced_prompt(query: str, domain_context: Dict) -> str
```
- 도메인 특화 프롬프트 생성
- 컨텍스트 정보 주입
- Few-shot 예시 포함

### **2. Smart Planner (planner.py)**

#### SmartPlanner 클래스

##### 계획 수립 프로세스
```python
def create_plan(
    intent_analysis: IntentAnalysisResult,
    available_agents: List[str]
) -> ExecutionPlan
```

###### 계획 단계
1. **작업 식별** (Task Identification)
   ```python
   def _identify_required_tasks(intent, agents) -> List[TaskNode]
   ```
   - 필요 작업 목록 생성
   - 우선순위 설정

2. **의존성 분석** (Dependency Analysis)
   ```python
   def _build_dependency_graph(tasks) -> nx.DiGraph
   ```
   - NetworkX 기반 그래프 구성
   - 순환 의존성 감지

3. **병렬 처리 최적화** (Parallel Optimization)
   ```python
   def _identify_parallel_opportunities(graph) -> List[List[TaskNode]]
   ```
   - 독립 작업 그룹 식별
   - 병렬 실행 계획

4. **리소스 할당** (Resource Allocation)
   ```python
   def _allocate_resources(tasks, constraints) -> Dict
   ```
   - 메모리/CPU 할당
   - 타임아웃 설정

### **3. Agent Selector (agent_selector.py)**

#### DynamicAgentSelector 클래스

##### 선택 알고리즘
```python
def select_agents(
    tasks: List[TaskNode],
    available_agents: Dict[str, AgentProfile]
) -> Dict[str, str]
```

###### 점수 계산 요소
| 요소 | 가중치 | 설명 |
|------|--------|------|
| Capability Match | 0.4 | 작업-능력 일치도 |
| Current Load | 0.2 | 현재 작업 부하 |
| Success Rate | 0.2 | 과거 성공률 |
| Response Time | 0.1 | 평균 응답 시간 |
| Domain Expertise | 0.1 | 도메인 전문성 |

##### 로드 밸런싱
```python
def _distribute_workload(
    agents: List[str],
    tasks: List[TaskNode]
) -> Dict
```
- Round-robin 기본 전략
- 가중치 기반 분배
- 동적 재할당

### **4. Execution Manager (execution_manager.py)**

#### ParallelExecutionManager 클래스

##### 실행 전략
```python
async def execute(
    plan: ExecutionPlan,
    agent_assignments: Dict,
    state: MedicalSupervisorState
) -> ExecutionResult
```

###### 실행 단계
1. **초기화 단계**
   - 실행 큐 생성
   - 리소스 풀 초기화

2. **병렬 실행**
   ```python
   async def _execute_parallel(tasks, max_workers=5)
   ```
   - asyncio.gather() 활용
   - 동시 실행 제한

3. **순차 실행**
   ```python
   async def _execute_sequential(tasks)
   ```
   - 의존성 순서 보장
   - 결과 전파

4. **에러 처리**
   ```python
   async def _handle_task_failure(task, error, retry_count)
   ```
   - 재시도 로직 (최대 3회)
   - Fallback 전략
   - Circuit Breaker 패턴

### **5. Context Manager (context_manager.py)**

#### ContextManager 클래스

##### 컨텍스트 최적화
```python
def optimize_context(
    query: str,
    user_context: Dict,
    agent_type: str
) -> MedicalContext
```

###### 최적화 전략
1. **관련성 필터링**
   - 에이전트별 필요 정보 선별
   - 노이즈 제거

2. **압축 및 요약**
   - 긴 텍스트 요약
   - 중복 정보 제거

3. **구조화**
   - JSON 스키마 적용
   - 타입 검증

4. **캐싱**
   - 자주 사용되는 컨텍스트 캐싱
   - TTL 기반 만료

---

## Worker Agents

### **1. SQL Analysis Agent**

#### 주요 기능
```python
class SQLAnalysisAgent:
    async def analyze(
        query: str,
        context: Dict,
        database: str
    ) -> SQLAnalysisResult
```

##### 처리 프로세스
1. **Text2SQL 변환**
   - LLM 기반 SQL 생성
   - 스키마 인식 쿼리 생성

2. **쿼리 실행**
   - 안전성 검증
   - 타임아웃 관리

3. **결과 분석**
   - 통계 분석
   - 트렌드 파악
   - 인사이트 생성

##### 지원 분석 유형
| 유형 | 설명 | 예시 |
|------|------|------|
| Aggregate | 집계 분석 | SUM, AVG, COUNT |
| Trend | 추세 분석 | 시계열 패턴 |
| Comparison | 비교 분석 | 부서별, 기간별 |
| Complex | 복합 분석 | JOIN, 서브쿼리 |

### **2. Information Retrieval Agent**

#### 주요 기능
```python
class InformationRetrievalAgent:
    async def search(
        query: str,
        sources: List[str],
        filters: Dict
    ) -> SearchResult
```

##### 검색 소스
1. **내부 데이터베이스**
   - HR 정보
   - 규정 문서
   - 업무 매뉴얼

2. **외부 API**
   - 논문 검색
   - HIRA 데이터
   - 규제 정보

##### 검색 최적화
- **쿼리 확장**: 동의어, 관련어 추가
- **결과 재순위**: LLM 기반 관련성 평가
- **중복 제거**: 유사도 기반 필터링

### **3. Document Generation Agent**

#### 주요 기능
```python
class DocumentGenerationAgent:
    async def generate(
        doc_type: str,
        data: Dict,
        template: Optional[str]
    ) -> Document
```

##### 지원 문서 유형
| 유형 | 형식 | 템플릿 |
|------|------|---------|
| 보고서 | PDF/DOCX | 사용자 정의 |
| 증명서 | PDF | 표준 양식 |
| 분석 리포트 | HTML/PDF | 데이터 기반 |
| 이메일 | TEXT/HTML | 템플릿 기반 |

##### 생성 프로세스
1. **데이터 추출**: 자연어에서 필드 추출
2. **템플릿 적용**: 문서 구조 생성
3. **포맷팅**: 스타일 적용
4. **검증**: 필수 항목 확인

### **4. Compliance Validation Agent**

#### 주요 기능
```python
class ComplianceValidationAgent:
    async def validate(
        document: str,
        rules: List[str],
        context: Dict
    ) -> ValidationResult
```

##### 검증 레벨
1. **기본 검증**
   - 필수 항목 확인
   - 형식 검증

2. **규정 준수**
   - 법규 위반 체크
   - 내부 규정 확인

3. **LLM 검증**
   - 의미론적 검증
   - 일관성 확인

##### 검증 결과
```python
class ValidationResult:
    is_compliant: bool
    violations: List[Violation]
    suggestions: List[str]
    confidence_score: float
```

---

## 워크플로우 분석

### LangGraph 워크플로우 구조

#### 노드 정의
```python
workflow = StateGraph(MedicalSupervisorState)

# 노드 추가
workflow.add_node("intent_analysis", intent_analyzer)
workflow.add_node("planning", planner)
workflow.add_node("agent_selection", selector)
workflow.add_node("execution", executor)
workflow.add_node("result_aggregation", aggregator)
```

#### 엣지 정의
```python
# 조건부 엣지
workflow.add_conditional_edges(
    "intent_analysis",
    lambda x: x["intent"]["category"],
    {
        "data_analysis": "sql_agent",
        "information_retrieval": "search_agent",
        "document_generation": "doc_agent",
        "compliance_check": "compliance_agent"
    }
)
```

#### 실행 흐름
```
START
  ↓
Intent Analysis
  ↓
Planning
  ↓
Agent Selection
  ↓
Parallel Execution ──→ [Agent 1] [Agent 2] [Agent 3]
  ↓
Result Aggregation
  ↓
END
```

---

## 상태 관리

### **State Definition (state.py)**

#### MedicalSupervisorState
```python
class MedicalSupervisorState(TypedDict):
    # 기본 정보
    session_id: str
    query: str
    user_context: Dict

    # 분석 결과
    intent_analysis: IntentAnalysisResult
    execution_plan: ExecutionPlan

    # 실행 상태
    current_step: str
    agent_results: Dict[str, Any]

    # 메타데이터
    timestamps: Dict[str, datetime]
    performance_metrics: Dict
    error_log: List[Dict]
```

#### State Reducers
```python
def merge_agent_results(current: Dict, new: Dict) -> Dict:
    """에이전트 결과 병합"""
    return {**current, **new}

def append_to_history(current: List, new: Any) -> List:
    """히스토리 추가"""
    return current + [new]
```

### Checkpointing

#### CheckpointerPool 클래스
```python
class CheckpointerPool:
    def __init__(self, max_size: int = 100):
        self.pool = {}
        self.checkpointer = SqliteSaver.from_conn_string(":memory:")

    async def save(self, session_id: str, state: Dict):
        """상태 저장"""

    async def load(self, session_id: str) -> Optional[Dict]:
        """상태 복원"""
```

---

## 성능 모니터링

### PerformanceMonitor 클래스

#### 수집 메트릭
| 메트릭 | 단위 | 설명 |
|--------|------|------|
| agent_execution_time | ms | 에이전트별 실행 시간 |
| memory_usage | MB | 메모리 사용량 |
| token_usage | count | LLM 토큰 사용량 |
| cache_hit_rate | % | 캐시 적중률 |
| error_rate | % | 에러 발생률 |

#### 모니터링 대시보드
```python
def get_dashboard_metrics() -> Dict:
    return {
        "real_time": get_realtime_metrics(),
        "aggregated": get_aggregated_metrics(),
        "alerts": get_active_alerts()
    }
```

---

## 에러 처리 및 복구

### 에러 처리 전략

#### 1. 재시도 메커니즘
```python
@retry(max_attempts=3, backoff=exponential)
async def execute_with_retry(task):
    """지수 백오프를 이용한 재시도"""
```

#### 2. Fallback 전략
```python
fallback_chain = [
    primary_agent,
    secondary_agent,
    default_response
]
```

#### 3. Circuit Breaker
```python
class CircuitBreaker:
    def __init__(self, failure_threshold=5):
        self.failure_count = 0
        self.is_open = False
```

---

## 최적화 기법

### 1. 병렬 처리 최적화
- **작업 배치**: 유사 작업 그룹화
- **리소스 풀링**: 연결 재사용
- **비동기 처리**: Non-blocking I/O

### 2. 컨텍스트 최적화
- **선택적 로딩**: 필요한 정보만 로드
- **압축**: 대용량 컨텍스트 압축
- **캐싱**: 자주 사용되는 컨텍스트 캐싱

### 3. LLM 최적화
- **프롬프트 캐싱**: 반복 프롬프트 재사용
- **토큰 관리**: 토큰 사용량 최적화
- **모델 선택**: 작업별 적절한 모델 선택

---

## 결론

Supervisor & Agents 시스템은 LangGraph를 활용한 정교한 Multi-Agent 아키텍처를 구현하고 있습니다. 의도 분석, 지능형 계획 수립, 동적 에이전트 선택, 병렬 실행 관리 등의 고급 기능을 통해 복잡한 의료/제약 도메인 쿼리를 효과적으로 처리합니다. 특히 컨텍스트 최적화, 성능 모니터링, 강력한 에러 처리 메커니즘을 통해 안정적이고 확장 가능한 시스템을 제공합니다.