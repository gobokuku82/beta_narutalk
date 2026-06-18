# Dream Agent V2 - 다음 작업 계획서

**작성일**: 2026-02-09 (업데이트)
**현재 상태**: Option A 완료, 테스트 통과율 100% (57/57)

---

## 1. 현재 완료 상태

### 1.1 구현 완료 (Phase 1-5)

| Phase | 내용 | 상태 |
|-------|------|------|
| Phase 1 | Foundation (디렉토리, State, Models, Graph) | ✅ 완료 |
| Phase 2 | Layer 구현 (Cognitive, Planning, Execution, Response) | ✅ 완료 |
| Phase 3 | HITL (interrupt, Pause/Resume, Plan Editor) | ✅ 완료 |
| Phase 4 | Learning (TraceLogger, FeedbackCollector, Export) | ✅ 완료 |
| Phase 5 | Production (Session, Error Handling, Health) | ✅ 완료 |

### 1.2 Option A 완료 (테스트 우선 접근) - 2026-02-09

| 작업 | 상태 | 비고 |
|------|------|------|
| Integration 테스트 작성 | ✅ 완료 | 21개 테스트 |
| LLM 연동 테스트 | ✅ 완료 | OpenAI GPT-4o |
| PostgreSQL 연결 테스트 | ✅ 완료 | Checkpointer 연동 |

### 1.3 테스트 현황

| 구분 | 통과 | 실패 | 통과율 |
|------|------|------|--------|
| Unit Tests | 36 | 0 | 100% |
| Integration Tests | 21 | 0 | 100% |
| **전체** | **57** | **0** | **100%** |

---

## 2. 다음 작업 후보 (선택 사항)

### 2.1 추가 테스트 (선택)

| 작업 | 설명 | 우선순위 |
|------|------|----------|
| E2E 시나리오 테스트 확장 | 더 많은 시나리오 커버 | Low |
| API 테스트 | FastAPI 엔드포인트 테스트 | Medium |
| WebSocket 테스트 | 실시간 통신 테스트 | Medium |
| 부하 테스트 | 동시 요청 처리 | Low |

### 2.2 실제 연동 (완료됨)

| 작업 | 요구사항 | 상태 |
|------|----------|------|
| LLM 연동 | API 키 설정 (OpenAI) | ✅ 완료 |
| PostgreSQL 연동 | DB 서버 실행 | ✅ 완료 |
| Redis 연동 | Redis 서버 실행 (선택) | ⬜ 미진행 |

**필요 설정**:
```bash
# .env 파일
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
DATABASE_URL=postgresql://user:pass@localhost:5432/dream_agent
```

### 2.3 Tool 정의 추가

| 작업 | 설명 | 우선순위 |
|------|------|----------|
| YAML Tool 정의 | `tools/definitions/*.yaml` 파일 작성 | Medium |
| Prompt 템플릿 | `llm_manager/prompts/*.yaml` 파일 작성 | Medium |

**예시 파일**:
```yaml
# tools/definitions/collector.yaml
name: collector
description: "데이터 수집"
category: data
executor: "executors.data_executor.DataExecutor"
parameters:
  - name: source
    type: string
    required: true
```

### 2.4 Layer 실제 구현

| Layer | 현재 상태 | 필요 작업 |
|-------|----------|-----------|
| Cognitive | 뼈대 구현 | LLM 기반 의도 분류 구현 |
| Planning | 뼈대 구현 | LLM 기반 Plan 생성 구현 |
| Execution | 뼈대 구현 | Send API 병렬 실행 구현 |
| Response | 뼈대 구현 | 멀티포맷 출력 구현 |

### 2.5 미구현 컴포넌트

| 컴포넌트 | 파일 | 우선순위 |
|----------|------|----------|
| Resource Estimator | `planning/estimator.py` | Low |
| Tool Discovery | `tools/discovery.py` | Medium |
| 세션 라우트 | `api/routes/session.py` | Medium |

---

## 3. 권장 작업 순서

### Option A: 테스트 우선 접근

```
1. Integration 테스트 작성
2. E2E 테스트 작성
3. LLM 연동 테스트
4. Layer 실제 구현
```

### Option B: 기능 우선 접근

```
1. Tool YAML 정의 작성
2. Layer 실제 구현 (LLM 연동)
3. Integration 테스트 작성
4. E2E 테스트 작성
```

### Option C: 인프라 우선 접근

```
1. PostgreSQL 연결 설정
2. LLM API 키 설정
3. 실제 연동 테스트
4. 부하 테스트
```

---

## 4. 의존성 관계

```
┌─────────────────────────────────────────────────────────┐
│                    현재 완료                              │
│  Phase 1-5: 구조, 모델, API, Workflow Managers           │
└─────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │ Tool YAML   │ │ LLM API 키  │ │ PostgreSQL  │
    │ 정의 작성    │ │ 설정        │ │ 연결        │
    └─────────────┘ └─────────────┘ └─────────────┘
           │               │               │
           └───────────────┼───────────────┘
                           ▼
              ┌───────────────────────┐
              │ Layer 실제 구현        │
              │ (Cognitive, Planning,  │
              │  Execution, Response)  │
              └───────────────────────┘
                           │
                           ▼
              ┌───────────────────────┐
              │ Integration 테스트     │
              │ E2E 테스트             │
              └───────────────────────┘
                           │
                           ▼
              ┌───────────────────────┐
              │ Production 배포 준비   │
              └───────────────────────┘
```

---

## 5. 예상 리소스

### 5.1 외부 서비스

| 서비스 | 용도 | 필수 여부 |
|--------|------|-----------|
| OpenAI API | LLM 호출 | 필수 (또는 Anthropic) |
| PostgreSQL | 세션/체크포인트 저장 | 필수 |
| Redis | 캐시 (선택) | 선택 |

### 5.2 환경 변수

```bash
# 필수
OPENAI_API_KEY=
DATABASE_URL=

# 선택
ANTHROPIC_API_KEY=
REDIS_URL=
LOG_LEVEL=INFO
```

---

## 6. 다음 액션

**사용자 결정 필요:**

1. 위 Option A/B/C 중 어떤 접근 방식을 선택할 것인가?
2. LLM API 키가 준비되어 있는가?
3. PostgreSQL 서버 사용이 가능한가?
4. 특정 기능에 우선순위를 두고 싶은가?

---

## 7. 참조 문서

| 문서 | 위치 |
|------|------|
| 아키텍처 설계서 | `reports_mind_dream/version_2/v2_architecture_260205.md` |
| 테스트 결과 보고서 | `docs/TEST_RESULTS.md` |
| 프로젝트 컨텍스트 | `.claude/CLAUDE.md` |
| Plan 파일 | `~/.claude/plans/humming-puzzling-wigderson.md` |
