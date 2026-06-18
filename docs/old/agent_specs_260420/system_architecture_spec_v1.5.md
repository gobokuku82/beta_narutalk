# Dream Agent V2 시스템 구조 명세서

| 항목 | 내용 |
|------|------|
| 담당자 | 도윤 |
| 분류 | 개발 - AI 에이전트 |
| 진행상태 | **검증 완료** (POC E2E + HITL PM 구조, Sprint 0~12) |
| 버전 | **v1.6** |
| 최종 수정일 | 2026-04-19 |
| 이전 버전 | v1.5 (2026-04-17) |

---

## 0. v1.6 요약 (What's New)

v1.5 → v1.6은 **Sprint 10~12의 Checkpointer 연결 + HITL PM 구조 확정**을 반영하고, **Sprint 13~15 로드맵**을 공식화.

### v1.6 핵심 변경 (Sprint 10~12)

| 영역 | v1.5 | v1.6 |
|---|---|---|
| **Checkpointer** | 미연결 (POC) | **AsyncPostgresSaver 연결 완료** (Sprint 11) |
| **HITL Manager** | 스텁 | **PM/HITL Layer로 승격** (Sprint 12) — Plan 승인, Execution Pause/Resume, Todo 수정/삭제, Cascade 무효화 |
| **Execution 구조** | execute_plan 단일 호출 | **`hitl.should_continue()` + `executor.execute_phase()` 루프** (LangGraph 노드 재실행에 안전) |
| **Progress 영속화** | 없음 | **`AgentState.execution_progress` + Checkpoint** — 서버 재시작 시 복구 |
| **interrupt() 분기** | plan_review 단일 | **`plan_review` / `execution_pause`** 2종 (자동 승인 우회 포함) |
| **Cascade 무효화** | 없음 | **`todo_manager.calculate_cascade()`** — Todo 수정 시 downstream BFS 무효화 |
| **WebSocket 이중화** | `/ws/stream` 단일 | **`/ws/agent` (이벤트) + `/ws/hitl` (제어 명령)** |

### v1.6 로드맵 추가 (Sprint 13~15 계획)

| 항목 | 범위 | 예상 |
|---|---|---|
| Sprint 13 | **Session/Thread 재설계** — `user_id`/`conversation_id`/`turn_id` 분리, `thread_id = f"{conv}_{turn}"`, `conversation_history` 슬롯 | ~6h |
| Sprint 14 | **HITL 고도화** — A1 자연어 Todo 수정(plan_editor LLM), A2 부분 재시작, A3 `requires_approval` Tool, A4 복합 쿼리 재계획 | ~13h |
| Sprint 15 | **Memory (채팅 저장/불러오기)** — `conversations`/`turns` 테이블, MemoryManager, Cognitive context 주입, 대화 목록 UI | ~15h |

> Feedback/Learning Manager는 본 로드맵 범위 밖 (POC+ 추후 검토).

### v1.5 핵심 변경 (Sprint 9, 참조)

v1.4.1 → v1.5는 **Sprint 9의 모델 전환 + 3계층 프롬프트 도입**을 반영.

#### v1.5 변경 표 (Sprint 9)

| 영역 | v1.4.1 | v1.5 |
|---|---|---|
| **LLM 모델** | gpt-4o 단일 | **레이어별 분기**: cognitive/planning/execution=`gpt-5.4-mini`, response=`gpt-5.4-nano` |
| **Planning 프롬프트** | 단일 프롬프트 13KB (카탈로그 통째 주입) | **3계층 분리** (Stage 1 팀→Stage 2 Agent→Stage 3 Todo, 각 1~5KB) |
| **비용** | ~$0.078/쿼리 | **~$0.018/쿼리 (77%↓)** |
| **속도** | 평균 16.3초 | **평균 12.7초 (22%↑)** |
| **복잡 쿼리 통과율** | 4/5 | **5/5 (100%)** |

### v1.4 핵심 변경 (Sprint 0~8, 참조)

v1.3 → v1.4는 **구현 검증을 통해 확정된 설계를 공식 문서화**한 버전. Sprint 0~6을 거쳐 자연어 → PDF/이미지 첨부 응답까지의 4-Layer 파이프라인이 E2E로 작동함을 증명.

### 핵심 변경점

| 영역 | v1.3 | v1.4 |
|---|---|---|
| **Cognitive 출력** | `Intent` (3-depth 분류) | **`StructuredQuery`** (4 블록: targets/goal/tasks/meta) |
| **Task 어휘** | `subcategory` 자유 문자열 | **`TaskType` enum 17종** (유한 집합) |
| **요청 깊이** | `plan_hint` 문자열 | **`goal.depth` enum** (brief/standard/detailed) |
| **Tool 계층** | 평면 (Agent → Tool) | **3-Level 계층** (Team → Agent → Tool) |
| **Agent 초기화** | 요청 시 | **Eager Init** (서버 부팅 시 AgentPool) |
| **Planning 단계** | 3-Step | **4-Step** (drafter → team_selector → todo_builder → validator) |
| **실행 전략** | `ExecutionStrategy` enum 명시 | **DAG 분석 자동 추론** (enum 제거) |
| **Scheduler 레이어** | 고려 | **도입 안 함** (책임 3개 레이어 분산) |
| **구현 노드** | 4 (1 레이어 = 1 노드) | **14 개념 / 4 실제 LangGraph 노드** |
| **학습 데이터** | 언급 없음 | **명시** (`(raw_input, structured_query)` 페어 누적) |
| **레이어 파일 구조 (v1.4.1, Sprint 8)** | 노드 함수가 `system_graph/builder.py`에 집약 | **각 레이어 폴더에 `{layer}_stage.py` 분산** (`cognitive/cognitive_stage.py` 등) — 독립 관리 |

### 추가된 섹션

- §0. v1.4 요약 (본 섹션)
- §2.2.5 StructuredQuery 스키마
- §2.3.5 3-Level Team → Agent → Tool 계층
- §7.4 Tool 스케일링 3-Tier 전략
- §7.5 AgentPool Eager Init

---

## 1. 시스템 개요

### 1.1 Dream Agent란

Dream Agent는 광고대행사 퍼포먼스 마케터를 위한 **4-Layer + Manager 아키텍처** 기반의 AI 에이전트 시스템이다.

사용자의 자연어 입력을 **이해(Cognitive) → 계획(Planning) → 실행(Execution) → 시각화(Response)** 파이프라인으로 처리한다. 각 레이어는 **번역기**로서 사용자 언어 ↔ 기계 언어 변환의 연쇄를 이룬다.

### 1.2 핵심 설계 원칙

| 원칙 | 설명 | 이유 |
|------|------|------|
| **번역의 연쇄** | 각 레이어는 한 형태의 표현을 다른 형태로 변환. Cognitive(자연어→기계)와 Response(기계→사용자)가 쌍 | 책임 단순화, 검증 가능성 |
| **Layer Separation** | 각 레이어는 독립적 책임. 레이어 간 통신은 State를 통해서만 | 교체/수정 시 파급 0 |
| **Hand-off** | 각 레이어는 자기 일만 하고, 결과를 State에 쓰고, 다음으로 넘긴다 | 단방향 디버깅 |
| **Planning ≠ Execution** | Planning = "무엇을/누가/어떤 순서로" / Execution = "실제 실행 + 병렬/직렬 전략" | 계획 변경 시 실행 코드 무관 |
| **개념 레이어와 구현 노드 분리** | 4-Layer는 개념, 구현 노드는 필요한 만큼 자유 (현재 14 개념) | 내부 확장성 |
| **Manager Pattern** | 횡단 관심사(HITL, 메모리, 콜백)는 Manager 모듈 | 레이어가 비즈니스 로직에 집중 |
| **Hybrid State** | AgentState = TypedDict / I/O·도메인 = Pydantic | 성능 + 안전성 |
| **학습 데이터 축적** | 매 레이어 전후 페어를 학습 데이터로 저장 (MVP 이후 활용) | 도메인 특화 fine-tuning 기반 |
| **Breaking 시 계획서** | 기존 코드 교체는 계획서 → 검증 → 실행 순 | 리스크 관리 |

### 1.3 LLM 모델 배치 (v1.5, Sprint 9)

레이어별 모델 분기로 비용 77% 절감 + 품질 유지:

| Layer | 모델 | 용도 | 비용/1M input |
|-------|------|------|--------------|
| Cognitive | `gpt-5.4-mini` | 의도 분류 + StructuredQuery (복잡 쿼리 대응) | $0.75 |
| Planning (3계층) | `gpt-5.4-mini` | 팀/Agent/Tool 매핑 + DAG | $0.75 |
| Execution | `gpt-5.4-mini` | insight_extractor, report_writer 등 | $0.75 |
| Response | `gpt-5.4-nano` | 포맷팅 + 요약 (단순 태스크) | $0.20 |

> 설정 파일: `backend/app/dream_agent/llm_manager/config.py` LAYER_CONFIGS
> GPT-5+ 모델은 `max_tokens` 대신 `max_completion_tokens` 사용 (client.py 자동 분기)

### 1.4 LangGraph 도입 범위

| Layer | 구현 방식 | 이유 |
|-------|----------|------|
| Cognitive | 순수 Python (LangGraph 노드 1개) | 번역. LangGraph 내부 분기 불필요 |
| Planning | 순수 Python (LangGraph 노드 1개) | Todo 문서 생성 |
| **Execution** | **순수 Python + LangGraph 노드 1개** | DAG Phase 병렬 (asyncio.gather, 향후 Send API). HITL interrupt, Checkpoint |
| Response | 순수 Python (LangGraph 노드 1개) | 포맷팅 |
| **레이어 간 배선** | **LangGraph Command** | 각 노드가 Command(goto=...)로 다음 노드 지정 |

### 1.4 전체 아키텍처 다이어그램

```
User Input (자연어)
    │
    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Main Graph (LangGraph StateGraph)                    │
│                                                                              │
│  ┌───────────┐ Command ┌──────────┐ Command ┌───────────┐ Command ┌───────┐│
│  │ Cognitive  │───────→│ Planning │───────→│ Execution │───────→│Response││
│  │  (번역)    │        │  (매핑)  │        │  (실행)   │        │(역번역)││
│  │ StructQry  │        │Todo[]+DAG│        │ExecResult │        │Payload ││
│  └─────┬─────┘        └────┬─────┘        └─────┬─────┘        └───┬────┘│
│        │                   │                     │                  │     │
│   goto="response"     skip if empty         DAG Phase          goto=END  │
│   (모호/factual)      tasks               병렬 실행                         │
│        │                                                                    │
│        └──────────────────────┐                                            │
│                               │                                            │
├───────────────────────────────┼────────────────────────────────────────────┤
│                         Manager System (횡단 관심사)                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │ HITL Manager │ │ Todo Manager │ │ Memory Mgr   │ │ Callback Mgr │      │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                        │
│  │ Session Mgr  │ │ Learning Mgr │ │ Feedback Mgr │                        │
│  └──────────────┘ └──────────────┘ └──────────────┘                        │
└──────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
User Output (text / image / pdf / video / mixed)
```

### 1.5 AgentPool (v1.4 신규)

서버 부팅 시 `AgentPool` 싱글톤에 **모든 Agent 인스턴스를 Eager Init**. 요청 시 cold start 0ms.

```
AgentPool (Eager Init, 서버 lifespan 1회)
├── analysis_team (5 Agent)
│   ├── collection_agent
│   ├── preprocessing_agent
│   ├── analysis_agent
│   ├── report_agent
│   └── pdf_agent
├── creative_team (4 Agent)
│   ├── image_agent
│   ├── video_agent
│   ├── copy_agent
│   └── material_agent
└── operations_team (MVP+)
```

Tool의 무거운 리소스(ML 모델, DB 커넥션)는 **Lazy Load** (첫 호출 시).

---

## 2. 4-Layer 아키텍처

### 2.1 Layer 요약

| Layer | 역할 | 핵심 질문 | 입력 | 출력 | 구현 |
|-------|------|-----------|------|------|------|
| **Cognitive** | 번역 | 자연어에서 무엇을 추출하고 어떻게 조합? | `user_input` | **`StructuredQuery`** | 순수 Python |
| **Planning** | 매핑 | SQ와 AgentPool로 누가/무엇을/어떤 순서로? | SQ + 카탈로그 | **`Todo[] + DAG` (`Plan`)** | 순수 Python |
| **Execution** | 실행 | DAG 병렬/직렬 결정 + 실패/HITL? | Plan | **`ExecutionResult`** | Python + asyncio + LangGraph |
| **Response** | 역번역 | goal.output_format에 맞춰 사용자 언어로? | ExecResult + SQ.goal | **`ResponsePayload`** | 순수 Python |

### 2.2 Cognitive Layer — 번역

**책임**: 자연어 입력을 **StructuredQuery(기계 언어)**로 번역.

#### 2.2.1 하는 것

- 오타 교정 / 간접 표현 해석 / 업계 은어·비유 정규화
- 퍼포먼스 마케팅 도메인 용어 인식 (ROAS, CTR 등)
- 대상(targets) 추출 + 정규화 (브랜드/소스/기간 등)
- 목적(goal) 판정 (type/output_format/depth/audience)
- 작업(tasks) 분해 — `TaskType` 유한 enum 안에서
- 모호성 탐지 → `meta.missing` + `meta.ambiguity`

#### 2.2.2 하지 않는 것

- Tool/Agent 선택 (→ Planning)
- 실행 전략 (→ Execution)

#### 2.2.3 처리 흐름

```
user_input
    │
    ▼ ① input_normalizer (silent, 프롬프트 내부)
    │   오타 교정, 은어/비유 → 표준 표현
    │
    ▼ ② intent_classifier
    │   goal.type + original_domain 판정
    │
    ▼ ③ entity_extractor
    │   targets.brand/product/source/period/keywords 추출
    │
    ▼ ④ query_completer  ← v1.4 핵심
    │   goal.depth, tasks[], output_format 확정
    │
    ▼ ⑤ cognitive_validator (Pydantic)
    │   confidence ≥ 0.5, 필수 엔티티, enum 일관성
    │
    ▼
StructuredQuery
```

실제 구현에서는 ①~⑤가 **단일 LLM 호출로 통합** (프롬프트에 단계 지시 + few-shot). 개념적으로 5 단계지만 구현은 1 노드.

#### 2.2.4 출력 검증

| 검증 항목 | 기준 | 실패 시 |
|----------|------|--------|
| Pydantic parse | 스키마 일치 | 에러 → END |
| confidence | ≥ 0.5 | 재분류 (최대 2회) |
| 필수 엔티티 | tasks별 required_any_of | `meta.missing` 기록 |
| 모호성 | is_ambiguous 판정 | tasks=[] 상태 → Planning skip |

#### 2.2.5 StructuredQuery 스키마 (v1.4 핵심 계약)

```python
class StructuredQuery(BaseModel):
    # 대상 - "무엇에 대해"
    targets: Targets
        brand: str | None
        product: str | None
        competitors: list[str]          # 비교 쿼리 대응
        source: Source                  # enum: naver|youtube|coupang|oliveyoung|tiktok|amazon|google|multi|unknown
        period: Period | None           # {raw, start, end, window}
        keywords: list[str]
        extra_filters: dict             # 채널/타겟/예산 등 유연 dict

    # 목적 - "왜 / 어떤 결과"
    goal: Goal
        type: GoalType                  # enum: answer|metric|insight|report|creative|mixed
        output_format: OutputFormat     # enum: text|pdf|image|chart|video|mixed
        depth: Depth                    # enum: brief|standard|detailed  ← v1.3 대비 신규 1등급 필드
        audience: str | None

    # 작업 - "어떤 sub-intent"
    tasks: list[Task]
        id: TaskType                    # 17종 enum (§2.2.6)
        priority: int
        params_override: dict

    # 메타 - "이 쿼리 얼마나 믿을 수 있나"
    meta: QueryMeta
        confidence: float (0.0~1.0)
        ambiguity: Ambiguity            # {is_ambiguous, severity, reasons, clarification_question}
        missing: list[str]              # 비어있는 필수 필드
        raw_input: str
        language: str
        original_domain: str | None     # legacy 호환 (analysis/content/operation/inquiry)
```

#### 2.2.6 TaskType Vocabulary (17종 유한 enum)

```
# 데이터
DATA_COLLECTION, DATA_PREPROCESSING

# 분석
SENTIMENT_ANALYSIS, KEYWORD_EXTRACTION, TREND_ANALYSIS,
COMPETITOR_COMPARISON, CAUSAL_ANALYSIS

# 산출물
INSIGHT_GENERATION, REPORT_GENERATION, SUMMARY_GENERATION

# 크리에이티브
IMAGE_GENERATION, IMAGE_EDITING, VIDEO_STORYBOARD,
COPY_GENERATION, MATERIAL_VARIATION

# 운영
BUDGET_OPTIMIZATION

# 조회형
FACTUAL_LOOKUP
```

#### 2.2.7 State I/O

| 방향 | 필드 | 설명 |
|------|------|------|
| Read | `user_input`, `language`, `session_id` | 입력 |
| Write | `structured_query` | StructuredQuery.model_dump() |
| Write | `error` | 에러 시 |

#### 2.2.8 라우팅

| 조건 | goto |
|------|------|
| error 존재 | `__end__` |
| tasks 비어있음 (ambiguity/factual) | `response` (planning skip) |
| 정상 | `planning` |

---

### 2.3 Planning Layer — 매핑

**책임**: `StructuredQuery` + `AgentPool 카탈로그`를 매핑하여 **누가(Team/Agent), 무엇을(Tool), 어떤 순서로(DAG)** 할지 결정.

#### 2.3.1 하는 것

- Team → Agent → Tool 3-level 매핑
- 암묵적 선행(collection/preprocessing) 자동 삽입
- `depends_on` DAG 생성
- Tool params 구성 (targets에서 자동 주입)
- goal.depth에 따른 체인 길이 차등
- 구조/DAG/논리 검증

#### 2.3.2 하지 않는 것

- 실행 전략(병렬/직렬) 결정 → Execution
- Tool 직접 호출 → Execution

#### 2.3.3 내부 3계층 프롬프트 (v1.5, Sprint 9 확정)

v1.4의 개념 4단계를 **실제 3개의 독립 LLM 호출로 분리** — 각 단계가 관련 정보만 보므로 집중도·정확도 향상.

```
StructuredQuery
    │
    ▼ Stage 1: team_selector (LLM 호출 1, ~1KB 프롬프트)
    │   "어느 팀?" — tasks[].id → Team 매핑
    │   입력: StructuredQuery + 팀 요약 (2~3줄 × 2팀)
    │   출력: teams_selected: ["analysis_team"]
    │   프롬프트: planning_stage1_team.yaml
    │
    ▼ Stage 2: agent_selector (LLM 호출 2, ~3KB 프롬프트)
    │   "팀 내 어떤 Agent?" — depth 기반 Agent 수 조절
    │   입력: StructuredQuery + 선택 팀의 Agent 목록만
    │   출력: agents_selected: ["collection_agent", "preprocessing_agent", "analysis_agent"]
    │   프롬프트: planning_stage2_agent.yaml
    │
    ▼ Stage 3: todo_builder (LLM 호출 3, ~5KB 프롬프트)
    │   "Agent의 Tool로 Todo + DAG" — 실제 Plan 생성
    │   입력: StructuredQuery + 선택 Agent의 Tool 상세만
    │   출력: todos[] + dag + plan_notes
    │   ★ preprocessing 체인: format_normalizer → text_preprocessor 필수
    │   프롬프트: planning_stage3_todo.yaml
    │
    ▼ validate_dag (코드 검증, LLM 아님)
    │   구조 검증 (id/tool/params), DAG 순환, 논리 순서
    │
    ▼
Plan { teams_selected, todos, dag, plan_notes }
```

**v1.4 대비 변화**:
- 단일 13KB 프롬프트 → 3개 분리 (1+3+5 = 9KB 분산, 각 단계 집중)
- LLM 호출 1→3회 (Planning 실질 시간은 비슷 — 각 호출이 짧음)
- 복잡 쿼리 통과율 4/5 → **5/5 (100%)** 개선
- 각 단계 학습 데이터 수집 가능 (3페어/쿼리)
- 프롬프트 파일: `llm_manager/prompts/planning_stage{1,2,3}_*.yaml`
- 기존 단일 프롬프트: `planning_legacy.yaml`로 보존 (롤백용)

#### 2.3.4 Plan 출력 포맷

```python
class PlannedTodo(BaseModel, frozen=True-like):
    id: str                         # "todo_001"
    task_type: str                  # TaskType
    team: str | None                # "analysis_team"
    agent: str | None               # "collection_agent"
    tool: str | None                # "naver_collector"
    tool_params: dict
    depends_on: list[str]
    priority: int
    rationale: str                  # LLM 설명 (디버깅/학습용)

class Plan(BaseModel):
    teams_selected: list[str]       # ["analysis_team", "creative_team"]
    todos: list[PlannedTodo]
    dag: dict[str, list[str]]       # todo_id → depends_on (중복 표현, Execution 편의)
    plan_notes: str                 # LLM 요약 (1~2문장)
```

#### 2.3.5 3-Level Team → Agent → Tool 계층 (v1.4 핵심)

**계층 구조**:
```
Team (팀)           — Planning 첫 번째 선택 단위
  └── Agent (전문가) — Planning 두 번째 선택 단위
        └── Tool (도구) — Agent에 바인딩 (선택 불필요)
```

**1팀: 분석팀 (Analysis Team) — 순차 파이프라인**
| Agent | 담당 TaskType | Tools |
|---|---|---|
| collection_agent | data_collection | naver_collector / youtube / coupang / oliveyoung |
| preprocessing_agent | data_preprocessing | format_normalizer → text_preprocessor (**필수 2단계**) |
| analysis_agent | sentiment/keyword/trend/competitor/causal | sentiment_analyzer / keyword_extractor / trend_analyzer / competitor_comparator |
| report_agent | insight/report/summary | report_writer / insight_extractor / summary_generator |
| pdf_agent | report(pdf) | pdf_renderer / chart_generator |

**2팀: 크리에이티브팀 (Creative Team) — 병렬/분기**
| Agent | 담당 TaskType | Tools |
|---|---|---|
| image_agent | image_generation/editing | image_generator / image_resizer / thumbnail_creator |
| video_agent | video_storyboard | storyboard_creator / video_image_generator |
| copy_agent | copy_generation | slogan_writer / copy_generator |
| material_agent | material_variation | material_modifier / variation_generator |

**3팀: 운영팀 (Operations Team) — MVP+**
| Agent | 담당 TaskType |
|---|---|
| budget_agent | budget_optimization |
| targeting_agent | (MVP에서 정의) |
| scheduling_agent | (MVP에서 정의) |

**⚠ preprocessing 체인 필수 규칙 (Sprint 6)**:
- 분석 계열 task가 있으면 `format_normalizer → text_preprocessor` 2단계 Tool을 **반드시 순서대로** 포함
- `text_preprocessor`는 `format_normalizer.produces[normalized_reviews]`를 입력으로 받음
- format_normalizer가 빠지면 데이터 체인 단절 → `text_preprocessor input=0`

#### 2.3.6 Tool 스케일링 3-Tier 전략

| Tier | 시점 | 방식 | Tool 수 |
|---|---|---|---|
| Tier 1 (POC) | 현재 | Task enum → Team/Agent 매핑 (hardcode), 카탈로그 전체 LLM 주입 | 8~15 |
| Tier 2 (MVP) | 예정 | Team 단위 Agent 분리 + AgentPool Eager Init. 투입 팀만 프롬프트 주입 | 15~30 |
| Tier 3 (자동화) | 예정 | Vector RAG (Tool description embedding) 2차 필터 | 30~60 |

#### 2.3.7 State I/O

| 방향 | 필드 | 설명 |
|------|------|------|
| Read | `structured_query` | Cognitive 출력 |
| Write | `plan` | Plan.model_dump() |
| Write | `error` | 에러 시 |

#### 2.3.8 라우팅

| 조건 | goto |
|------|------|
| tasks 비어있음 (SQ가 이미 ambiguity/factual) | `response` (skip) |
| Plan 생성 실패 | `__end__` |
| 정상 | `execution` |

---

### 2.4 Execution Layer — 실행 (Orchestrator)

**책임**: Plan의 Todo + DAG를 받아 **병렬/직렬 전략을 자동 결정**하고 실행.

#### 2.4.1 하는 것

- DAG 분석 → 독립 Todo 그룹화 (Phase)
- Phase 내부 asyncio.gather 병렬 실행
- 실재 Tool (ToolRegistry) or stub Tool (mock_result) 호출
- 선행 결과 `previous_results`로 전달
- Todo 상태 전이 (pending → in_progress → completed/failed)
- HITL interrupt 처리 (MVP+)
- 실패 시 즉시 halt (spec v1.3 §2.4 방침 유지)

#### 2.4.2 하지 않는 것

- Todo 생성/변경 → Planning
- Tool 로직 구현 → Agent 내부

#### 2.4.3 내부 3단계

```
Plan
    │
    ▼ ⑩ dag_analyzer (build_phases)
    │   DAG에서 depends_on 전부 완료된 todo를 Phase로 그룹
    │   예: Phase 1: [todo_001], Phase 2: [todo_002], Phase 3: [todo_003, todo_004]
    │
    ▼ ⑪ runner
    │   Phase별로 asyncio.gather(*[_run_single_todo(t) for t in phase])
    │   (향후 Send API로 전환)
    │
    ▼ ⑫ result_collector
    │   TodoResult 집계, 상태 전이, 루프 판정 (quality_loop 시)
    │
    ▼
ExecutionResult
```

#### 2.4.4 실행 전략 (v1.3 enum 제거, 자동 추론)

| 전략 (자동) | DAG 특성 | POC |
|------|------|-----|
| 단일 | Todo 1개 | ✅ |
| 직렬 | depends_on 체인 | ✅ |
| 병렬 | 독립 Todo 그룹 (같은 Phase) | ✅ |
| fan-out | 같은 Tool을 N번 | ✅ (params_override.count) |
| 루프 | Plan.quality_loop 있을 때 | ❌ MVP+ |
| swarm | 의사결정 실험 (실행 아님) | ❌ (제거 예정) |

#### 2.4.5 Tool 실행 방식

**실재 Tool (status=implemented, 8개)**:
- `naver_collector`, `format_normalizer`, `text_preprocessor`
- `sentiment_analyzer`, `keyword_extractor`, `insight_extractor`
- `report_writer`, `summary_generator`
→ ToolRegistry로 import, 실제 데이터 처리

**Stub Tool (status=stub, 19개)**:
- `youtube_collector`, `pdf_renderer`, `image_generator` 등
→ `mock_tools.mock_result(tool_name, params)` 반환 (체인 통과용)

**Tool 결과 주입**:
```python
# previous_results의 모든 키를 다음 Tool params에 자동 병합
for r in previous_results.values():
    for k, v in r.data.items():
        merged.setdefault(k, v)
```

#### 2.4.6 에러 처리 (v1.3 방침 유지)

- Todo 실패 → 재시도 없이 즉시 failed → 전체 halt
- Todo status: in_progress → failed (final)
- `error` 필드에 실패 위치 + 원인 기록
- goto=`__end__`

#### 2.4.7 State I/O

| 방향 | 필드 | 설명 |
|------|------|------|
| Read | `plan` | Planning 출력 |
| Write | `execution_result` | ExecutionResult.model_dump() |
| Write | `error` | 에러 시 |

---

### 2.5 Response Layer — 역번역

**책임**: Execution 결과를 **`goal.output_format`에 맞춰 사용자 언어로 역번역**.

#### 2.5.1 하는 것

- 여러 Agent 결과 todo_id별 집계
- LLM 기반 자연어 요약 생성
- format 라우팅: text / pdf / image / chart / video / mixed / error
- 첨부(attachments) 구성
- 후속 작업 추천(next_actions)

#### 2.5.2 처리 흐름

```
ExecutionResult + StructuredQuery.goal
    │
    ▼ ⑬ result_aggregator (_build_execution_summary)
    │   todo_id별 TodoResult 요약 (data 핵심 키만 추출, 크기 제한)
    │
    ▼ ⑭ response_formatter (LLM)
    │   goal.output_format별 스타일 (프롬프트 few-shot):
    │     text (brief) → 1~3문장
    │     pdf → 본문 + 첨부 안내
    │     image → 개수/컨셉 + 첨부
    │     error → 실패 사유 + 재시도 제안
    │
    ▼
ResponsePayload
```

#### 2.5.3 ResponsePayload 스키마

```python
class ResponsePayload(BaseModel):
    format: ResponseFormat              # enum: text|pdf|image|chart|video|mixed|error
    text: str                           # 메인 응답 (항상 존재)
    summary: str | None                 # 1~2문장 핵심
    next_actions: list[str]             # 추천 후속 작업
    attachments: list[Attachment]       # [{kind, path, url, caption, meta}]
    meta: dict                          # tools_used, completed_todos, total_duration_ms
    error: str | None                   # format=error일 때
```

#### 2.5.4 정직성 원칙 (v1.4 신규)

Response는 Execution 데이터 품질 이슈를 **사용자에게 솔직히 전달**:
- Tool 실행은 성공했으나 데이터가 비어있음 → "데이터가 수집되지 않아 분석 불가"
- 일부 todo만 completed → 부분 결과 + 어느 Tool이 실패했는지 명시
- 숨기거나 가짜 데이터 생성 금지

#### 2.5.5 State I/O

| 방향 | 필드 | 설명 |
|------|------|------|
| Read | `structured_query`, `execution_result`, `language` | 모두 |
| Write | `response` | ResponsePayload.model_dump() |
| Write | `error` | 에러 시 |

---

### 2.6 Layer 추가 규칙

새 Layer 추가 시 확인:

1. 기존 Layer와 책임 경계 겹치지 않는가
2. Hand-off 흐름 어디에 삽입되는가
3. State에 새 필드 필요한가 → State 명세서 업데이트
4. 라우팅 규칙 변경되는가 → system_graph/builder 수정
5. 관련 명세서(AgentState, Schemas) 업데이트

**현 시점 (v1.4)**: Scheduler 레이어 추가 검토 → 기각 (§3.4 참조).

---

## 3. System Graph

### 3.1 그래프 구조 (v1.4.1 파일 배치 반영)

```python
# 실제 LangGraph 노드 4개 (내부에 개념 14단계).
# 각 stage 함수는 해당 레이어 폴더의 {layer}_stage.py에 정의됨 (Sprint 8).

from app.dream_agent.cognitive.cognitive_stage  import cognitive_stage    # 내부: ①②③④⑤
from app.dream_agent.planning.planning_stage    import planning_stage     # 내부: ⑥⑦⑧⑨
from app.dream_agent.execution.execution_stage  import execution_stage    # 내부: ⑩⑪⑫
from app.dream_agent.response.response_stage    import response_stage     # 내부: ⑬⑭

graph.add_node("cognitive", cognitive_stage)   # 노드 이름 문자열 유지 (대시보드 호환)
graph.add_node("planning",  planning_stage)
graph.add_node("execution", execution_stage)
graph.add_node("response",  response_stage)

# 엣지
START → cognitive
cognitive →[Command]→ planning | response | __end__
planning  →[Command]→ execution | response | __end__   # tasks=[] skip
execution →[Command]→ response | __end__
response  →[Command]→ __end__
```

**2-계층 분리 원칙** (Sprint 8 확정):
- `{layer}_stage.py` = 파이프라인 단계 (LangGraph Command 인터페이스, state ↔ Command 변환)
- `{layer}/planner.py`, `executor.py`, `responder.py` = 비즈니스 로직 서비스 클래스 (LLM 호출, Pydantic 변환, 도메인 로직)
- `system_graph/builder.py` = 4 stage import + StateGraph 조립 (~40줄)

### 3.2 LangGraph Primitives

| Primitive | 사용처 | v1.6 상태 |
|-----------|--------|-----------|
| **Command** | 모든 레이어 간 hand-off | ✅ 전면 사용 |
| **Send** | Execution 병렬 | ❌ 현재 asyncio.gather (MVP+에서 전환) |
| **interrupt()** | HITL 중단점 (Plan 승인, Execution Pause) | ✅ Sprint 12 완료 — `plan_review`/`execution_pause` 분기 |
| **Checkpoint** | 상태 저장 + interrupt resume | ✅ AsyncPostgresSaver 연결 (Sprint 11) — `thread_id` per query |

### 3.3 설정

```python
# Sprint 11 이후: AsyncPostgresSaver 연결
checkpointer = await AsyncPostgresSaver.from_conn_string(POSTGRES_DSN)
agent = builder.compile(checkpointer=checkpointer)

# 호출 시 thread_id (현재는 session_id, Sprint 13에서 conversation_id_turn_id로 분리)
config = {"configurable": {"thread_id": session_id}}
async for chunk in agent.astream(initial_state, config=config):
    ...
```

**interrupt resume 흐름**:
```python
# 1) Plan 승인 모달
async for chunk in agent.astream(initial_state, config=config):
    if "__interrupt__" in chunk:
        # ws_agent → 대시보드 모달
        graph_state = await agent.aget_state(config)
        intr_type = graph_state.tasks[0].interrupts[0].value.get("type")
        # plan_review | execution_pause 분기

# 2) 사용자 응답 후 resume
async for chunk in agent.astream(LGCommand(resume={"action": "approve"}), config=config):
    ...
```

### 3.4 Scheduler 레이어 미도입 결정 (v1.4)

Planning과 Execution 사이에 **Scheduler 레이어**를 추가 검토했으나 **기각**:

| Scheduler가 담당할 일 | 실제 배치 |
|---|---|
| 실행 전략 결정 (seq/parallel/fan-out) | Execution `dag_analyzer` 자동 추론 |
| HITL 포인트 삽입 | Tool 정의의 `requires_approval` + Planning 고정 interrupt |
| Timeout / 병렬도 상한 | Tool 정의 `timeout_sec` + Execution 설정 |
| depth → Tool 수 | Planning의 Tool 선택 단계 |
| 루프 판정 | Execution 내부 |

→ Scheduler 고유 책임 없음. 기존 3레이어에 흡수.

---

## 4. Manager 시스템

### 4.1 개요

Manager는 **4-Layer에 직교하는 횡단 관심사**를 담당. v1.4 현재 대부분 스텁 — **POC 범위 외, MVP+ 본격 구현**.

### 4.2 Manager 목록 (v1.6 갱신)

| Manager | 역할 | v1.6 상태 |
|---------|------|-----------|
| **HITL Manager** | **PM/HITL Layer** — Plan 승인, Execution Pause/Resume, Todo 수정/삭제/추가, Cascade 무효화, Phase 통제 | ✅ **Sprint 12 완료** |
| **Todo Manager** | Todo 상태 전이, DAG cascade 계산, Phase 빌드 | ✅ **Sprint 12 완료** (`calculate_cascade`, `_build_phases_from_plan`) |
| **Callback Manager** | WebSocket 이벤트, 진행률 알림 | ✅ 구현 (api_v2/ws_agent + ws_hitl) |
| Memory Manager | 대화 저장/불러오기 (conversations/turns), Cognitive context 주입 | ⏳ **Sprint 15 예정** (~15h) |
| Session Manager | 세션 CRUD, 대화 이력 | (Memory Manager로 흡수 — Sprint 13/15) |
| Learning Manager | `(raw, structured_query)` 페어 로깅 | 보류 (POC 범위 외) |
| Feedback Manager | 사용자 피드백, 품질 평가 | 보류 (POC 범위 외) |

### 4.3 HITL Manager — PM/HITL Layer 상세 (v1.6 신규)

Sprint 12 확정 — hitl_manager가 Execution을 **지시(PM)**, Executor는 **단순 실행자**로 분리.

#### 4.3.1 책임 분리

| 책임 | 담당 |
|---|---|
| Plan을 Phase로 분해 | hitl_manager (`_build_phases_from_plan`) |
| 다음 Phase 진행 여부 결정 | hitl_manager (`should_continue`) |
| Phase 단위 실행 | executor (`execute_phase`) |
| 결과 누적 (`completed_todos`) | hitl_manager (`report_phase_complete`) |
| Pause/Resume 신호 | hitl_manager (싱글톤, ws_hitl이 호출) |
| Todo 수정/삭제/추가 + cascade | hitl_manager (`handle_todo_edit/delete/add`) |
| 최종 ExecutionResult 조립 | hitl_manager (`get_execution_result`) |

#### 4.3.2 ExecutionProgress (Checkpoint 영속화)

```python
@dataclass
class ExecutionProgress:
    session_id: str
    plan: dict                            # 원본 또는 수정된 Plan
    phases: list[list[str]]              # [[t1], [t2,t3], [t4]]
    current_phase: int = 0
    completed_todos: dict[str, dict]     # todo_id → result
    status: str = "running"              # running | paused | cancelled
    paused_at_phase: Optional[int] = None
```

→ `AgentState.execution_progress`로 직렬화되어 Checkpoint에 저장. 서버 재시작 시 `restore_progress()`로 복원.

#### 4.3.3 Cascade 무효화

Todo 수정/삭제 시 downstream BFS로 영향받는 Todo 식별:

```python
@dataclass
class CascadeResult:
    invalidated_todos: list[str]    # 결과 폐기 대상
    preserved_todos: list[str]      # 유지 대상
    restart_from: str               # 재실행 시작점
```

Plan 수정 → cascade 계산 → `completed_todos`에서 `invalidated` 제거 → phases 재구성 → 사용자 승인 → 재개.

#### 4.3.4 interrupt 분기

| `intr_type` | 발생 시점 | UI 동작 |
|---|---|---|
| `plan_review` | Planning 종료 후 | 승인/거부 모달 (Plan 표시) |
| `execution_pause` | Phase 사이 (사용자 Pause 요청 시) | 재개/취소 모달 (Todo 수정 가능) |

**자동 우회**: 사용자가 cognitive/planning 중 pause 누르면 `plan_review`는 자동 approve → 다음 Phase 직전 `execution_pause`로 멈춤.

### 4.4 Manager 공통 패턴

```python
class BaseManager:
    async def initialize(self): ...
    async def ready(self) -> bool: ...
    async def shutdown(self): ...
```

ManagerRegistry로 의존성 기반 초기화 순서 관리.

### 4.5 WebSocket 이중 채널 (v1.6)

| 채널 | 방향 | 용도 |
|---|---|---|
| `/ws/agent` | Server → Client (주) | layer events, interrupt 알림, complete |
| `/ws/hitl` | 양방향 | hitl_response (approve/reject), pause/resume, todo_edit/delete/add, todo_edit_nl (Sprint 14 예정) |

> 단일 채널로 합치지 않은 이유: 이벤트 스트림과 사용자 명령의 backpressure/생명주기 분리. Pause 중에도 명령은 계속 받기 위함.

---

## 5. State 관리

### 5.1 Hybrid State 전략

| 용도 | 타입 시스템 | 이유 |
|------|-----------|------|
| `AgentState` (그래프 상태) | TypedDict | 성능, 부분 업데이트, Reducer 호환 |
| Layer I/O (StructuredQuery 등) | Pydantic BaseModel | 런타임 검증, 직렬화 |
| 도메인 모델 (Plan, TodoResult 등) | Pydantic BaseModel | 검증, 불변성, 직렬화 |

### 5.2 AgentState (v1.6)

```python
class AgentState(TypedDict, total=False):
    # 입력 (v1.6 — Sprint 13에서 conversation_id/turn_id로 분리 예정)
    user_input: str
    language: str
    session_id: str                     # = turn_id alias (Sprint 13에서 deprecated)

    # ── Sprint 13 예정 (Session/Thread 재설계) ──
    # user_id: str                      # 사용자 식별
    # conversation_id: str              # 대화 단위 (UI 채팅방 1개)
    # turn_id: str                      # 쿼리 단위 (대화 안의 1턴)
    # conversation_history: list[dict]  # Cognitive 주입용 최근 N턴 요약

    # Cognitive 산출
    structured_query: dict              # StructuredQuery.model_dump()

    # Planning 산출
    plan: dict                          # Plan.model_dump()

    # Execution 산출
    execution_result: dict              # ExecutionResult.model_dump()
    execution_progress: dict            # ✅ Sprint 12 신규 — ExecutionProgress (Pause/Resume용)

    # Response 산출
    response: dict                      # ResponsePayload.model_dump()

    # 횡단
    error: str | None
    trace: list[dict]
    hitl_pending: dict | None
```

#### 5.2.1 execution_progress 구조 (Sprint 12 신규)

```python
{
    "session_id": "sess_xxx",
    "plan": {...},                      # 현재 유효한 Plan (수정 반영)
    "phases": [["t1"], ["t2","t3"], ["t4"]],
    "current_phase": 1,
    "completed_todos": {"t1": {...}, "t2": {...}},
    "status": "paused",                 # running | paused | cancelled
    "paused_at_phase": 2,
}
```

→ Checkpoint와 함께 영속화. 서버 재시작 시 ws_agent가 interrupt payload + restore_progress로 복원.

### 5.3 직렬화 경계

```
쓰는 노드                      AgentState                      읽는 노드
PydanticModel ──.model_dump()──→ dict ──→ .model_validate() ──→ PydanticModel
```

### 5.4 Reducer

v1.4 현재 기본 덮어쓰기 (update dict 병합). v1.3의 `todo_reducer`/`results_reducer`/`trace_reducer`는 MVP+에서 재도입.

---

## 6. 도메인 모델

### 6.1 모델 관계도 (v1.4)

```
StructuredQuery (Cognitive 산출) — 핵심 계약
  ├── targets: Targets
  ├── goal: Goal
  ├── tasks: list[Task]
  └── meta: QueryMeta
         │
         ↓
Plan (Planning 산출)
  ├── teams_selected: list[str]
  ├── todos: list[PlannedTodo]
  │     ├── id, task_type, team, agent, tool
  │     ├── tool_params, depends_on
  │     └── rationale
  ├── dag: dict[str, list[str]]
  └── plan_notes: str
         │
         ↓
ExecutionResult (Execution 산출)
  ├── plan_id: str
  ├── todos: dict[str, TodoResult]
  │     ├── status, data, error
  │     ├── is_mock, duration_ms
  │     └── started_at, ended_at
  ├── phase_timings: list[dict]
  ├── total_duration_ms: float
  ├── overall_status: TodoStatus
  └── halted_at, halt_reason
         │
         ↓
ResponsePayload (Response 산출)
  ├── format: ResponseFormat
  ├── text, summary, next_actions
  ├── attachments: list[Attachment]
  └── meta, error
```

### 6.2 정식 Pydantic 파일 위치

- `backend/app/dream_agent/schemas/structured_query.py`
- `backend/app/dream_agent/schemas/execution_result.py`
- `backend/app/dream_agent/schemas/response_payload.py`
- `backend/app/dream_agent/planning/planner.py` (Plan + PlannedTodo는 여기)

---

## 7. Tool 시스템

### 7.1 Tool 분류

| 분류 | 구현 | 설명 | 예시 |
|------|------|------|------|
| **tool** | Python 함수/클래스 | 단일 작업, 중간 상태 없음 | `sentiment_analyzer`, `keyword_extractor` |
| **subgraph** | LangGraph subgraph | 복합 파이프라인, 중간 상태 있음 | (MVP+ 도입) 매체 API 수집 체인 |

### 7.2 3-Level 계층 (v1.4 핵심)

```
Team (2~3개)
  └── Agent (각 3~5개)
        └── Tool (각 2~5개)
```

§2.3.5 참조.

### 7.3 ToolRegistry 인터페이스

> 코드 위치: `backend/app/dream_agent/tools/registry.py`
> 카탈로그 위치: `backend/app/dream_agent/tools/catalog/` (YAML 재귀 스캔)

```python
from app.dream_agent.tools.registry import get_registry
registry = get_registry()  # 싱글톤
```

| 메서드 | 반환 | 용도 |
|--------|------|------|
| `get_all()` | `list[ToolSpec]` | 전체 Tool (프롬프트 주입 — POC Tier 1) |
| `get(name)` | `ToolSpec \| None` | 이름으로 조회 |
| `get_by_category(category)` | `list[ToolSpec]` | 카테고리별 |
| `get_for_domain(domain)` | `list[ToolSpec]` | 도메인별 (Tier 2 기반) |
| `import_tool(name)` | `type` | Python 클래스 동적 import |
| `exists(name)` | `bool` | 존재 여부 |

### 7.4 Tool 스케일링 3-Tier 전략 (v1.4 공식화)

§2.3.6 참조. 요약:
- Tier 1 (현재): 카탈로그 전체 LLM 주입
- Tier 2 (MVP): Team 단위 필터 + Eager Init
- Tier 3 (자동화): Vector RAG

### 7.5 AgentPool (v1.4 신규)

> 코드 위치: `backend/app/dream_agent/execution/agent_pool.py`

**Eager Init**: 서버 부팅 시 `team_catalog.yaml` 읽어 Team/Agent 전부 인스턴스화.

```python
from app.dream_agent.execution.agent_pool import get_agent_pool
pool = get_agent_pool()
pool.list_teams()          # ["analysis_team", "creative_team"]
pool.list_agents()         # 9개 Agent 이름
pool.get_agent(name)       # AgentSpec
pool.is_tool_implemented(agent, tool)  # bool
pool.get_real_tool(tool_name)          # Lazy Load 인스턴스
```

**Lazy Load**:
- Tool의 무거운 리소스(ML 모델, DB 커넥션)는 첫 호출 시 로드 + 캐시
- 예: `sentiment_analyzer`의 MultilingualSentiment ML 모델은 첫 감성 분석 요청 시 로드

### 7.6 Stub Tool 처리 (v1.4 신규)

POC 단계에서 미구현 Tool(image_generator, pdf_renderer 등)은 `status: stub` 표시. Execution이 `mock_tools.mock_result()`로 더미 결과 반환.

**목적**: Plan 체인 구조 검증이 목적이지 Tool 구현이 목적 아님. Sprint 3에서 검증 완료.

---

## 8. 실행 흐름 예시 (v1.4 검증 케이스)

### 8.1 Brief: "블루밍글로우 리뷰 감성 어때?"

```
1. User Input
2. Cognitive:
   structured_query:
     targets: {brand: "블루밍글로우", source: "naver"}
     goal:    {type: "answer", format: "text", depth: "brief"}
     tasks:   [{id: "sentiment_analysis"}]
     meta:    {confidence: 0.92, missing: []}
3. Planning:
   teams: ["analysis_team"]
   todos: 4 — collection, format_normalizer, text_preprocessor, sentiment_analyzer
   dag: 선형 체인
4. Execution:
   Phase 1: naver_collector → 15 raw_reviews
   Phase 2: format_normalizer → 15 normalized_reviews
   Phase 3: text_preprocessor → 15 cleaned_texts
   Phase 4: sentiment_analyzer → pos 60%, neu 20%, neg 20%
   ~2초
5. Response:
   format: "text"
   text: "블루밍글로우 리뷰 감성 분석 결과 — 긍정 60%, 중립 20%, 부정 20%"
```

### 8.2 Detailed: "블루밍글로우 네이버 리뷰 감성 분석하고 상세 보고서 PDF로 만들어줘"

```
1. Cognitive:
   goal: {type: "report", format: "pdf", depth: "detailed"}
   tasks: [sentiment_analysis, report_generation]
2. Planning:
   todos: 8 — collection, format, text, sentiment, keyword, insight, report, pdf
3. Execution (7 phases, ~20초):
   감성 + 키워드 공유 선행(text_preprocessor) 후 병렬
4. Response:
   format: "pdf"
   text: "주요 발견 3가지: 긍정 72%, 핵심 키워드 수분/저자극/가성비, 부정 10% 향 이슈"
   attachments: [{kind: "pdf", path: "/mock/블루밍글로우_report.pdf"}]
```

### 8.3 Mixed: "블루밍글로우 리뷰 분석하고 그 결과로 광고 이미지도 만들어줘"

```
1. Cognitive:
   goal: {type: "mixed", format: "mixed", depth: "detailed"}
   tasks: [sentiment_analysis, insight_generation, image_generation]
2. Planning:
   teams: ["analysis_team", "creative_team"]
   todos: 6 — 분석팀 5 + 크리에이티브팀 1(image_generator)
   팀 간 의존성: image_generation → insight_generation
3. Execution (6 phases, ~15초):
   분석팀 순차 → insight 완료 → image_generator 실행
4. Response:
   format: "mixed"
   text: "긍정 60%, 피부 개선 효과/세럼 키워드 반영한 광고 이미지 생성"
   attachments: [pdf report + image]
```

### 8.4 모호: "분석해줘"

```
1. Cognitive:
   targets: {brand: null}
   tasks: []
   meta: {confidence: 0.40, ambiguity: {is_ambiguous: true, severity: "high"},
          missing: ["target", "task_spec"]}
2. Planning: SKIP (tasks 비어있음)
3. Execution: SKIP (empty plan)
4. Response:
   format: "text"
   text: "어떤 브랜드/제품을 어느 채널에서 분석할까요?"
   (clarification question)
```

### 8.5 Factual: "ROAS가 뭐야?"

```
1. Cognitive:
   tasks: [{id: "factual_lookup"}]
2. Planning: todos=0 (Tool 없이 Response가 직답)
3. Execution: SKIP
4. Response:
   format: "text"
   text: "ROAS (Return On Ad Spend)는 광고비 대비 매출 비율입니다. ..."
   (LLM 직답)
```

---

## 9. 단계별 로드맵 (POC → MVP → 자동화)

v1.3 §9 내용 유지.

### 9.1 단계 정의

| 단계 | 명칭 | 핵심 목표 | 데이터 | 실행 방식 |
|------|------|----------|-------|----------|
| **1차** | POC | "이렇게 작동합니다" 시연 | mock (블루밍글로우) | 모든 화면 + 분석 로직 + 분석/생성 |
| **2차** | MVP | 진짜 성과 데이터로 분석 | 실제 매체 API 4개 | 실데이터 ML 정확도 향상 |
| **3차** | 자동화 | 분석 → 판단 → 집행 전 과정 | 외부 트렌드 + 요서 | 영상 제작 + 매체 자동 집행 |

### 9.2 v1.4 기준 현재 상태

- ✅ **POC E2E 파이프라인 작동** (자연어 → PDF/이미지 첨부)
- ✅ StructuredQuery 기반 계약 확정
- ✅ Team/Agent/Tool 3-level 계층
- ✅ AgentPool Eager Init
- ✅ 회귀 검증 (20 쿼리 90%)
- ⏳ MVP 진입 대기 (Tool 정합성 안정화 완료)

### 9.3 POC 핵심 원칙 유지

- 데이터: mock (블루밍글로우)
- 실행: 에이전트 채팅 베이스
- 자동화 범위: 분석·생성까지
- HITL: 모든 결과 마케터 확인
- 목표: 현업자에게 보여줄 프로토타입

### 9.4 단계별 핵심 변화

```
1차 (POC)                    2차 (MVP)                    3차 (자동화)
─────────                    ─────────                    ──────────────
mock 데이터                → 실제 API 4채널            → 외부 트렌드 + 요서
LLM 많이 + 규칙 거의 없음  → 규칙/ML 비중 증가          → 인과분석 본격 도입
스토리보드까지             → 영상 프레임 자동 생성      → 실제 영상 제작
PDF 1종 출력               → PPT/Excel 추가            → 인터랙티브 리포트
HITL 모든 결정 확인        → 패턴 학습으로 자동 추천    → 매체 자동 집행 + HITL 최소화
```

### 9.5 학습 데이터 누적 계획 (v1.4 신규)

| 단계 | 수집량 | 활용 |
|---|---|---|
| POC | ~20 쿼리 | Sprint 자동 테스트 평가 기준 |
| MVP | 1,000+ 쿼리 | Fine-tuning 데이터셋 초안 / 규칙 추출 |
| 자동화 | 10,000+ 쿼리 | Small model 자체 학습 (LLM 비용 절감) |

---

## 10. 관련 명세서

| 명세서 | 위치 | 설명 |
|--------|------|------|
| **시스템 아키텍처 (상세)** | `docs/_claude/4layer_system/system_architecture.md` | 14-노드 토폴로지 상세 |
| **완료 보고서** | `docs/_claude/4layer_system/report_01_completion_summary_260416.md` | Sprint 0~6 결과 |
| **v1 vs v2 비교** | `docs/_claude/4layer_system/report_02_v1_vs_v2_architecture_260416.md` | 변경점 상세 |
| **파일 매핑** | `docs/_claude/4layer_system/report_03_file_structure_mapping_260416.md` | 파일 이동/rename |
| **Sprint 실행 로그** | `docs/_claude/4layer_system/sprint_log.md` | 가설/검증/발견 |
| Pydantic 모델 | `backend/app/dream_agent/schemas/*.py` | StructuredQuery, ExecutionResult, ResponsePayload |
| Team 카탈로그 | `backend/app/dream_agent/planning/catalog/team_catalog.yaml` | 3-level 계층 정의 |
| LLM 프롬프트 | `backend/app/dream_agent/llm_manager/prompts/*.yaml` | cognitive/planning/response |
| *(예정)* 에이전트 기능 정의서 | `02_에이전트_기능_정의서/` | Agent별 상세 |
| *(예정)* 평가 기준서 | `08_에이전트_평가_기준서/` | 가설/합격 기준 |

---

## 11. 변경 이력

| 버전 | 날짜 | 변경자 | 변경 내용 |
|------|------|--------|----------|
| v1.0 | 2026-03-31 | 도윤 | 초기 작성. 4-Layer + Manager 전체 구조 |
| v1.02 | 2026-04-09 | 도윤 | data_analysis_agent 3분리 (collection/preprocessing/analysis) |
| v1.03 | 2026-04-09 | 도윤 | pdf_agent 신설(7 Agent), POC/MVP/자동화 로드맵 흡수 |
| v1.04 | 2026-04-10 | 도윤 | 논리 검증 전체 7 agent 순서, ToolRegistry 인터페이스 명세, SystemGraphConfig rename |
| v1.05 | 2026-04-13 | 도윤 | v1.3 최종. Intent 모델 기반 |
| v1.4 | 2026-04-16 | 도윤 + Sprint 0~6 | **대규모 업데이트 — v2 재설계 공식화**: StructuredQuery 도입, TaskType 17 enum, 3-Level Team/Agent/Tool 계층, AgentPool Eager Init, DAG 기반 병렬 실행 자동 추론, ExecutionStrategy enum 제거, Scheduler 레이어 미도입 결정, Planning 4-Step, Stub Tool mock 처리, 3-Tier 스케일링 전략, 정직성 원칙, 학습 데이터 축적 계획, preprocessing 체인 필수 규칙 (Sprint 6) |
| v1.4.1 | 2026-04-16 | 도윤 + Sprint 7~8 | Sprint 7: 50 쿼리 E2E 회귀 76% 통과. Sprint 8: stage 파일 분리 + builder 축약. |
| **v1.5** | **2026-04-17** | **도윤 + Sprint 9** | **Sprint 9-1**: LLM 모델 gpt-4o → GPT-5.4 mini/nano 레이어별 분기 (비용 77%↓, 속도 22%↑). 3모델 비교 테스트(gpt-5/5.4-mini/5.4-nano × 단순/복잡 10쿼리) 기반 선정. client.py에 `max_completion_tokens` GPT-5+ 호환 추가. <br>**Sprint 9-2**: Planning 3계층 프롬프트 도입 (단일 13KB → Stage1 팀/Stage2 Agent/Stage3 Todo 분리). 복잡 쿼리 통과율 4/5 → 5/5. 기존 planning.yaml → planning_legacy.yaml 보존. |
| **v1.6** | **2026-04-19** | **도윤 + Sprint 10~12** | **Sprint 10~11**: AsyncPostgresSaver 연결 — Checkpointer 정식 사용, `thread_id`로 interrupt resume. <br>**Sprint 12**: HITL Manager를 **PM/HITL Layer**로 승격. Executor는 Phase 단위 실행자(`execute_phase`)로 단순화. `hitl.should_continue()` 루프, `ExecutionProgress` Checkpoint 영속화, Cascade 무효화(`todo_manager.calculate_cascade`), interrupt 분기(plan_review/execution_pause), 자동 우회(cognitive/planning 중 pause → plan_review 자동 approve), WebSocket 이중 채널(/ws/agent + /ws/hitl). `AgentState.execution_progress` 추가. <br>**Sprint 13~15 로드맵 추가**: 13(Session/Thread 재설계 ~6h), 14(HITL 고도화 ~13h), 15(Memory 채팅 저장/불러오기 ~15h). Feedback/Learning은 범위 밖. |
