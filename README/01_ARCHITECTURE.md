# 01. 전체 아키텍처

## 프로젝트 구조

```
mind_dream/beta_v001/
│
├── backend/                          # FastAPI 백엔드
│   ├── api/                         # REST API & WebSocket
│   │   ├── main.py                  # FastAPI 진입점
│   │   ├── middleware/              # CORS 미들웨어
│   │   ├── routes/
│   │   │   ├── agent.py            # /api/agent 엔드포인트
│   │   │   ├── websocket.py        # /ws/{session_id}
│   │   │   └── health.py           # 헬스체크
│   │   └── schemas/                # Pydantic 스키마
│   │
│   └── app/                        # 핵심 애플리케이션
│       ├── core/
│       │   ├── config.py           # 설정 (API 키, DB URI)
│       │   ├── logging.py          # 로깅 설정
│       │   └── file_storage.py     # 파일 I/O
│       │
│       └── dream_agent/            # 4-Layer 에이전트
│           ├── cognitive/          # Layer 1: 의도 파악
│           ├── planning/           # Layer 2: 계획 수립
│           ├── execution/          # Layer 3: 실행
│           ├── response/           # Layer 4: 응답 생성
│           ├── states/             # 상태 관리
│           ├── orchestrator/       # LangGraph 워크플로우
│           ├── workflow_manager/   # 계획/리소스 관리
│           ├── tools/              # 도구 모음
│           └── llm_manager/        # LLM 관리
│
├── dashboard/                       # HTML 테스트 대시보드
│   ├── templates/
│   │   └── index.html              # 메인 UI
│   └── static/
│       ├── css/style.css           # 스타일링
│       └── js/app.js               # WebSocket 클라이언트
│
├── data/                            # 데이터 저장소
│   ├── mock/                       # Mock 테스트 데이터
│   ├── collected/                  # 수집된 원본 데이터
│   ├── processed/                  # 처리된 데이터
│   ├── cache/                      # 실행 캐시
│   ├── sessions/                   # 세션 데이터
│   ├── reports/                    # 생성된 리포트
│   └── result_trend/               # 최종 트렌드 분석 결과
│
├── tests/                          # 테스트 코드
│
└── README/                         # 개발 문서
```

---

## 4-Layer 에이전트 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER REQUEST                              │
│                    "K-Beauty 트렌드 분석해줘"                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: COGNITIVE (의도 파악)                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Intent    │  │   Entity    │  │  Dialogue   │             │
│  │ Classifier  │  │  Extractor  │  │  Manager    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  Output: intent (domain/category/subcategory), entities, context │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 2: PLANNING (작업 계획)                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │    Plan     │  │    Todo     │  │  Resource   │             │
│  │  Generator  │  │   Manager   │  │   Planner   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  Output: Plan, TodoList (with dependencies), ExecutionGraph      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 3: EXECUTION (실행)                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  ExecutionSupervisor                      │    │
│  └─────────────────────────────────────────────────────────┘    │
│           │              │              │              │         │
│           ▼              ▼              ▼              ▼         │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │   Data     │ │  Insight   │ │  Content   │ │   Ops      │   │
│  │ Executor   │ │  Executor  │ │  Executor  │ │ Executor   │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
│                                                                  │
│  Output: ml_result, biz_result (실시간 WebSocket 업데이트)        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 4: RESPONSE (응답 생성)                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Result    │  │  Markdown   │  │   Report    │             │
│  │ Aggregator  │  │  Formatter  │  │   Saver     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  Output: response (마크다운 형식), saved report                   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        FINAL RESPONSE                            │
│         K-Beauty 글로벌 트렌드 분석 리포트 (마크다운)              │
└─────────────────────────────────────────────────────────────────┘
```

---

## LangGraph 워크플로우

```python
# backend/app/dream_agent/orchestrator/builder.py

START
  ↓
cognitive_node          # Layer 1: 의도 파악
  ↓
planning_node           # Layer 2: 계획 수립
  ├→ execution_node     # Layer 3: 실행 (Todo 있는 경우)
  │     ↓
  │   [Todo Loop]       # 모든 Todo 완료까지 반복
  │     ↓
  │   response_node     # Layer 4: 응답 생성
  │     ↓
  │   END
  │
  └→ response_node      # Todo 없으면 바로 응답
       ↓
     END
```

---

## 실행 흐름 예시

### 요청: "라네즈 리뷰 분석해줘"

```
1. COGNITIVE
   ├─ Intent: domain=data_science, category=analysis
   ├─ Entities: brand=라네즈, data_sources=[reviews]
   └─ Language: ko

2. PLANNING
   ├─ Todo 1: 리뷰 데이터 수집 (collector)
   ├─ Todo 2: 데이터 전처리 (preprocessor) ← depends_on: Todo 1
   ├─ Todo 3: 감성 분석 (sentiment_analyzer) ← depends_on: Todo 2
   ├─ Todo 4: 키워드 추출 (keyword_extractor) ← depends_on: Todo 2
   └─ Todo 5: 인사이트 생성 (insight_generator) ← depends_on: Todo 3, 4

3. EXECUTION (WebSocket으로 실시간 업데이트)
   ├─ Todo 1: collector → completed (10 reviews)
   ├─ Todo 2: preprocessor → completed (8 cleaned)
   ├─ Todo 3: sentiment_analyzer → completed
   ├─ Todo 4: keyword_extractor → completed
   └─ Todo 5: insight_generator → completed

4. RESPONSE
   └─ 마크다운 형식의 분석 결과 반환
```

---

## 데이터 흐름

```
User Input
    │
    ▼
┌────────────────┐
│   WebSocket    │──────→ 실시간 진행상황 전송
│   Connection   │
└────────────────┘
    │
    ▼
┌────────────────┐
│   AgentState   │ ← Pydantic 기반 상태 관리
└────────────────┘
    │
    ├──→ cognitive_result (의도, 엔티티)
    ├──→ plan (계획 정보)
    ├──→ todos (작업 목록)
    ├──→ ml_result (분석 결과)
    ├──→ biz_result (비즈니스 결과)
    └──→ response (최종 응답)
```

---

## 핵심 컴포넌트

### 1. ExecutionSupervisor
```python
# backend/app/dream_agent/execution/supervisor.py

class ExecutionSupervisor:
    """실행 관리 감독자

    - Todo → Executor 라우팅
    - 의존성 해결
    - 캐싱 관리
    - 실행 이력 추적
    """

    async def execute_todo(self, todo, context) -> ExecutionResult:
        executor = self.get_executor_for_tool(todo.tool)
        return await executor.execute(todo, context)
```

### 2. Executor 매핑
```python
TOOL_TO_EXECUTOR = {
    # DataExecutor
    "collector": "data_executor",
    "preprocessor": "data_executor",
    "google_trends": "data_executor",

    # InsightExecutor
    "sentiment": "insight_executor",
    "keyword": "insight_executor",
    "keyword_extractor": "insight_executor",      # Alias
    "hashtag": "insight_executor",
    "problem": "insight_executor",
    "competitor": "insight_executor",
    "insight": "insight_executor",
    "insight_generator": "insight_executor",      # Alias
    "insight_with_trends": "insight_executor",    # K-Beauty RAG
    "absa_analyzer": "insight_executor",          # ABSA 감성 분석

    # ContentExecutor
    "report": "content_executor",
    "report_agent": "content_executor",           # Alias
    "video": "content_executor",
    "video_agent": "content_executor",            # Alias
    "ad_creative": "content_executor",
    "storyboard_agent": "content_executor",

    # OpsExecutor
    "sales": "ops_executor",
    "inventory": "ops_executor",
    "dashboard": "ops_executor",
}
```

### 3. TodoItem 구조
```python
class TodoItem(BaseModel):
    id: str
    task: str
    task_type: str
    layer: Literal["cognitive", "planning", "ml_execution", "biz_execution", "response"]
    status: Literal["pending", "in_progress", "completed", "failed", "blocked"]
    priority: int  # 0-10
    metadata: TodoMetadata  # execution, dependency, progress, approval
```
