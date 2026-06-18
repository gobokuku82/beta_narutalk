# Sprint 15 시작 — Phase D 세부 작업계획서 (ADR-010 v2 + ADR-015 본문)

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-04-28 |
| Phase | D — Sprint 15 시작 (ADR 본문 결정) |
| 마스터 | [`sprint15_implementation_plan.md`](./sprint15_implementation_plan.md) |
| 의존 | Phase C ✅ (Sprint 14 A3 종결) |
| 다음 | [`sprint15_phase_e1_memory_infrastructure.md`](./sprint15_phase_e1_memory_infrastructure.md) |
| 예상 작업량 | ~3.5시간 (1~2세션) |
| Acceptance | ADR-010 v2 + ADR-015 본문 + ADR INDEX 갱신 |

---

## 0. 본 문서의 역할

Phase D 의 **ADR 본문 작성 작업 카탈로그**. 코드 변경 X, 결정 박제만.

본 문서가 다루지 않는 것:
- 코드 구현 (→ Phase E)
- 옵션 비교 (→ Q1/Q3 자료)

---

## 1. Phase D 의 의도

### 1.1 왜 ADR 본문이 코드 구현 전에?

POC 1차 학습 = "결정 박제 안 하면 또 헷갈림". Phase B 사전 조사로 결정 root 가 잡혔으니, ADR 로 박제 후 구현.

### 1.2 작성 원칙

- **결정만 박제** — 옵션 비교는 Q1/Q3 자료가 이미 했음
- **사용자 lock 결정 그대로** — 이번 세션 모든 lock 반영
- **간결** — 1 ADR ≈ 1~2 페이지

---

## 2. 작업 분해

```
D-1  ADR-015 본문 (메모리 + Clarification 통합 architecture)
        ↓
D-2  ADR-010 v2 본문 (Sprint 15 D 단일화 정식 결정)
        ↓
D-3  ADR INDEX 갱신
```

### 시간 추정

| Sub-phase | 시간 | 누적 |
|-----------|------|------|
| D-1 ADR-015 본문 | 1.5h | 1.5h |
| D-2 ADR-010 v2 | 1h | 2.5h |
| D-3 INDEX 갱신 | 30min | 3h |
| 검토 + 정정 | 30min | **3.5h** |

---

## 3. D-1: ADR-015 본문 작성 (~1.5시간)

### 3.1 파일 생성

**경로**: `docs/agent_specs/adr/ADR-015_memory_intent_communication.md`

### 3.2 본문 구조 (Michael Nygard 표준)

#### 3.2.1 Status

```markdown
## Status

Accepted (2026-04-XX)

- 메모리 부분: Q3 자료 9 영역 lock 기반 정식 결정
- Clarification 부분: 메커니즘 lock (LLM hybrid + max 2회) / UX 세부 = Sprint 15 P1 구현 중 결정
```

#### 3.2.2 Context

```markdown
## Context

Vision (`agent_specs/00_vision_and_intent.md`) 의 H0 의도 모호성 + H2 학습 가설 + 자유 대화 파트너쉽을
구현하려면 다음이 필요:

1. **메모리 시스템** — 사용자 ↔ AI 대화 누적 = 학습 데이터 인프라
2. **Clarification HITL** — 모호한 쿼리 시 시스템 ← 사용자 보완 요청 (양방향 의도 흐름)
3. **메모리 ↔ Clarification 연결** — 같은 모호도 반복 시 메모리에서 자동 답 (H0 자동 해결)

POC 1차 검증 (R-8 첫 시도 brand 누락 fatal) 으로 H0 입증 + 자동 해결 메커니즘 부재 측정.

상세 설계: [`docs/reports/sprint14_a3_research_q3_memory.md`](../../reports/sprint14_a3_research_q3_memory.md)
사용자 5 항목 정책: [`docs/reports/sprint15_implementation_plan.md`](../../reports/sprint15_implementation_plan.md) §1.1
```

#### 3.2.3 Decision — 메모리 부분 (Q3 §3, §7)

```markdown
## Decision

### A. 메모리 부분

#### A.1 Schema (Q3 §2)
**Hybrid** — 핵심 metadata 정규화 컬럼 + content JSONB.

```sql
CREATE TABLE memory_entries (
    id UUID PRIMARY KEY,
    type VARCHAR(32),           -- preference / conversation / plan / pattern / knowledge / session / tool_cache
    scope_type VARCHAR(16),     -- global / org / user / session
    scope_id VARCHAR(255),
    key VARCHAR(255),
    content JSONB,
    source VARCHAR(16),         -- explicit / implicit / extracted
    confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    expires_at TIMESTAMP
);
CREATE INDEX idx_memory_scope ON memory_entries(scope_type, scope_id, type);
CREATE INDEX idx_memory_content ON memory_entries USING GIN (content);
CREATE UNIQUE INDEX idx_memory_unique_key ON memory_entries(scope_type, scope_id, type, key);
```

#### A.2 Granularity (Q3 §3)
**5 tier** — Global / Org / User / Session / Turn (Turn 만 in-memory).
**Sprint 15 P0 범위** = Session + User. Org + Global = Sprint 16+.

#### A.3 Read 시점 (Q3 §4) ⭐ H0 자동 해결 핵심
- Cognitive 직전 — `memory.get_context(session, user)` cascade
- Clarification 판단 시 — `memory.find_clarification_answer(field)` (답 있으면 묻기 skip)

#### A.4 Write 시점 (Q3 §5)
- Clarification 답변 직후 (explicit, user-scope 자동 promote)
- Response 성공 후 (implicit, persist_turn)
- 사용자 명시 action — Sprint 15 P1
- 자동 패턴 추출 — Sprint 17+

#### A.5 Lifecycle (Q3 §6) — Type 별 정책
- preference / plan / knowledge: TTL 무한
- conversation: 90일 (POC = 무한)
- session: 24h
- tool_cache: 1~7일 (Sprint 16+)

#### A.6 Manager API (Q3 §7) — 11 메서드 / P0 = 7
- get / set / delete (CRUD)
- get_context (cascade)
- search
- store_clarification / find_clarification_answer
- (Sprint 15 P1) persist_turn
- (Sprint 17+) extract_patterns

#### A.7 Checkpointer 분리 (Q3 §8)
LangGraph Checkpointer (PostgreSQL native) 와 Memory 는 **다른 테이블, 같은 DB**.
- checkpoints / checkpoint_writes — LangGraph 자동
- memory_entries — 본 시스템

#### A.8 Data Model (Q3 §9)
- `MemoryEntry` (Pydantic) — DB row 매핑
- `MemoryContext` — cascade 결과
- `Pattern` — Sprint 17+ 추출

#### A.9 사용자 5 항목 정책 (계획서 §1.1)
- #1 PostgreSQL CRUD — A.1 + A.6
- #2 채팅창 로드 = 최근 20 turn + Load More
- #3 LLM 히스토리 = 마지막 5 turn + 1500 token cap
- #4 긴 대화 = 잘라내기 (drop oldest) — POC. 요약 = Sprint 16+
```

#### 3.2.4 Decision — Clarification 부분

```markdown
### B. Clarification HITL 부분

#### B.1 Trigger 메커니즘 — Hybrid
- LLM 자체 감지: `StructuredQuery.clarifications_needed: list[ClarificationRequest]`
- Required field validator: brand / channel 등 비어있으면 자동 추가 (LLM 누락 시 backup)

#### B.2 모호도 3 유형
- (a) **Missing field** — 필수 정보 누락 (brand 등)
- (b) **Default confirm** — 시스템이 default 줘도 OK 인지 confirm
- (c) **Ambiguity** — entity 다중 해석 (예: "아모레 글로우")

#### B.3 Loop 방지
**max 2 회 attempts**. 이후 직진 + warning 로그.

#### B.4 응답 흐름
```
Cognitive 출력 (clarifications_needed 있음)
   ↓
[메모리 cascade] memory.find_clarification_answer(field)
   ↓ 답 있음 → augment + skip
   ↓ 답 없음 → interrupt(type="clarification")
   ↓ 사용자 답변
   memory.store_clarification(field, value)  # 즉시 저장
   ↓
Cognitive 재실행 (augmented input) — attempts < 2 일 때
   ↓
Planning → Execution → Response
```

#### B.5 UX (placeholder, Sprint 15 P1 구현 중 결정)
사용자 의도 lock: **"기존 todo 유지 + 부족분 요청"**.
구체 UX (모달 / inline / 통합) = 코드 작성 시 결정.

#### B.6 Data model
```python
class ClarificationRequest(BaseModel):
    type: Literal["missing_field", "default_confirm", "ambiguity"]
    field: str
    question: str
    options: Optional[list[str]] = None   # ambiguity / default_confirm
    default_value: Optional[str] = None   # default_confirm
    reason: str
```
```

#### 3.2.5 Consequences

```markdown
## Consequences

### 좋은 점
- ✅ H0 자동 해결 메커니즘 확보 (Cognitive 직전 cascade + Clarification 메모리 조회)
- ✅ H2 학습 데이터 인프라 (메모리 = 누적 저장소)
- ✅ Sprint 17+ 패턴 추출의 entry-point
- ✅ Sprint 18+ 맞춤형 에이전트의 토대
- ✅ 양방향 의도 흐름 구현 (시스템 ← 사용자)

### 나쁜 점 / 비용
- DB 부하 — turn 마다 cascade 조회 → in-memory cache (turn 단위) 로 완화
- Schema 진화 비용 — content JSONB 가 변경 흡수, version 필드로 대비
- LLM 비용 (clarification = 추가 LLM 호출) — H0 자동 해결로 점진 감소

### 위험
- 메모리 ↔ 사용자 의도 충돌 → source 라벨 우선순위 (explicit > implicit > extracted)
- Clarification 무한 loop → max 2회로 차단
- Sprint 17 패턴 추출 의도 어긋남 → confidence 가중치 + 사용자 검증 step
```

#### 3.2.6 Alternatives Considered

```markdown
## Alternatives Considered

[Q3 §4 의 외부 시스템 비교 + 영역별 옵션 참조]

### Alt-1. 단일 store (LangGraph Store)
- 장점: LangGraph native, 빠른 도입
- 단점: 우리 Vision (자유 대화 + 패턴 추출 + 맞춤형) 의 미세 제어 어려움
- 불채택 — Sprint 16+ MemoryManager 가 BaseStore 호환 가능

### Alt-2. Checkpointer 활용 (별도 메모리 X)
- 장점: 추가 인프라 0
- 단점: thread 단위 → cross-thread 학습 불가능 (H2 가설 못 함)
- 불채택

### Alt-3. 단순 Key-Value (Redis 스타일)
- 장점: 빠름
- 단점: 검색 / 패턴 / lifecycle 모두 부족
- 불채택 — POC 단계에도 부족

### Alt-4. Clarification 없이 default 적용
- 장점: 단순
- 단점: 사용자 의도 와 충돌 시 silent fail. 학습 데이터 X
- 불채택
```

#### 3.2.7 Related

```markdown
## Related

- 사전 조사: `docs/reports/sprint14_a3_research_q3_memory.md`
- 의도 문서: `docs/agent_specs/00_vision_and_intent.md` (vision §1, 가설 H0~H4)
- POC 1차 결산: `docs/reports/sprint14_a3_poc1_settlement.md` (CAP-001)
- 구현 계획: `docs/reports/sprint15_phase_e1_memory_infrastructure.md` (Phase E-1)
- 관련 ADR:
  - ADR-002 NL 점진 고도화 (Clarification = NL 2차 일부)
  - ADR-010 Plan schema (Memory 와 schema 협업)
  - ADR-001 hitl/pause 통합 (Clarification = 신규 HITL trigger)
- 사용자 메모리:
  - `project_no_user_domain_assumption.md` (H0 양방향 통신의 전제)
```

#### 3.2.8 변경 이력

```markdown
## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-XX | 초안 + Accepted. 메모리 부분 = Q3 §3/§7 lock. Clarification 메커니즘 lock. UX 세부 = Sprint 15 P1 구현 중 결정 |
```

### 3.3 Acceptance — D-1

- [ ] `ADR-015_memory_intent_communication.md` 파일 생성
- [ ] 8 섹션 (Status / Context / Decision A 메모리 / Decision B Clarification / Consequences / Alternatives / Related / 변경 이력) 모두 작성
- [ ] Q3 §3, §7 정확히 반영
- [ ] 5 항목 정책 (계획서 §1.1) 반영
- [ ] 외부 참조 link 모두 valid

---

## 4. D-2: ADR-010 v2 본문 갱신 (~1시간)

### 4.1 갱신 대상

**파일**: `docs/agent_specs/adr/ADR-010_plan_schema_unification.md` (Phase C-4 에서 신규 생성됨)

### 4.2 변경 내용

Phase C-4 의 ADR-010 은 "어댑터 임시 + Sprint 15 D 단일화 예정" 까지. **Phase D 에서 D 단일화 본격 결정 정식 박제**.

#### 4.2.1 Status 갱신

```markdown
## Status

Accepted (2026-04-XX) — Sprint 15 P0 D 단일화 정식 결정

이력:
- 2026-04-XX (Phase C-4): Sprint 14 A3 B 어댑터 임시 + Sprint 15 D 예정 표기
- 2026-04-XX (Phase D-2): Sprint 15 P0 D 단일화 본격 결정 + Migration plan 상세
```

#### 4.2.2 Decision 갱신 — Migration Plan 추가

```markdown
## Decision

### Sprint 15 P0 — Option D: planner.Plan 통일

#### D.1 폐기 대상
- `models/plan.py::Plan` (canonical)
- `models/todo.py::TodoItem`
- `models/__init__.py` 의 Plan / TodoItem export

#### D.2 유지 대상 (확장)
- `planning/planner.py::Plan`
- `planning/planner.py::PlannedTodo` — 필요 시 lifecycle 필드 추가:
  - `status: Literal[...]` (Sprint 16+)
  - `created_at / completed_at` (Sprint 16+)
  - `result / error_message` (Sprint 16+)

#### D.3 마이그레이션 작업
| 파일 | 변경 |
|------|------|
| `workflow_managers/hitl_manager/plan_editor.py` | import 변경 (planner.Plan + PlannedTodo). apply_edit add 분기 → PlannedTodo |
| `api_v2/ws_hitl.py` L464 import 변경. L507/L591 어댑터 호출 제거 (직접 사용) |
| `workflow_managers/hitl_manager/plan_adapter.py` | **삭제** (어댑터 throwaway) |
| `tests/sprint14/test_a3_plan_adapter_unit.py` | **삭제** |
| `tests/sprint14/test_a3_plan_editor_nl_unit.py` | import 변경 + assertion 갱신 |
| `tests/sprint14/test_a3_plan_review_edit_integration.py` | 동일 |
| `scripts/a3_nl_success_rate.py` | 동일 |

#### D.4 Migration 순서
1. PlannedTodo 가 lifecycle 필요 시 미리 확장 (Sprint 15 P0 진입 전)
2. plan_editor.py 변경 — 단위 테스트로 즉시 검증
3. ws_hitl.py 어댑터 제거 — 통합 테스트
4. 어댑터 파일 삭제
5. 회귀 테스트 (R-16/17/18 재검증)

#### D.5 LoC 추정
- 변경: ~150 LoC (5 파일)
- 삭제: ~130 LoC (어댑터 + 어댑터 테스트)
- 순 변화: +20 LoC
```

#### 4.2.3 Consequences 갱신

```markdown
## Consequences

### 좋은 점
- ✅ schema 단일 (Plan / Todo 모델 1쌍)
- ✅ 어댑터 변환 부담 0
- ✅ planner / executor / hitl 모두 같은 타입
- ✅ 정보 손실 0 (round-trip 매핑 불필요)

### 나쁜 점 / 비용
- 풀 lifecycle metadata 부재 (status / versions / changes / timestamps) — Sprint 16+ PlannedTodo 확장 필요
- 마이그레이션 ~150 LoC + 테스트 회귀 위험

### 위험
- PlannedTodo 확장 시 LLM prompt 변경 (status 등 추가) — Sprint 16+ 별도 ADR
- HITL history / replay / audit 기능 도입 시 PlannedTodo 추가 확장
```

### 4.3 Acceptance — D-2

- [ ] ADR-010 갱신 (Status / Decision / Consequences)
- [ ] D.3 마이그레이션 작업 표 (~7 파일)
- [ ] D.4 순서 5 단계
- [ ] D.5 LoC 추정

---

## 5. D-3: ADR INDEX 갱신 (~30분)

### 5.1 변경

**파일**: `docs/agent_specs/adr/INDEX.md`

#### 5.1.1 ADR 표 업데이트

| ADR | 변경 |
|-----|------|
| 010 | Phase C-4 entry → Phase D-2 갱신 entry 추가. Sprint 14 A3 어댑터 + Sprint 15 D 통일 |
| **015** | 신규 entry — "메모리 + Clarification 통합 architecture (Q3 9 영역 + 5 항목 정책 lock)" |

#### 5.1.2 결정 누락 표 정리

| 변경 |
|------|
| ADR-015 (HITL 트리거 + 메모리) → 작성 완료, "결정 누락" 에서 제거 |
| ADR-010 → 갱신 완료, 상태 = Accepted (Sprint 15 P0) |

### 5.2 Acceptance — D-3

- [ ] INDEX 의 ADR 목록에 ADR-015 행 추가
- [ ] ADR-010 행 갱신 (Sprint 15 P0)
- [ ] "결정 누락" 표에서 ADR-015 / ADR-016 (메모리) 제거 (통합됨)
- [ ] 변경 이력 갱신

---

## 6. 검증 / 테스트 전략

### 6.1 ADR 본문 일관성

**자가 점검**:
- [ ] ADR-015 가 Q3 §3, §7 모두 반영
- [ ] ADR-015 가 5 항목 정책 (#1~#5) 모두 반영
- [ ] ADR-010 v2 가 Phase C 어댑터 → Sprint 15 D 흐름 일관
- [ ] 외부 참조 link 모두 valid (관련 spec / 자료)

### 6.2 사용자 검토

**검토 포인트**:
- ADR-015 §A.1 schema SQL 정확?
- ADR-015 §B 의 Clarification 메커니즘 의도 일치?
- ADR-010 v2 의 Migration plan 동의?

### 6.3 자동 검증 (DC)

```bash
pytest backend/tests/test_doc_contracts.py -v
```

**기대**: ADR INDEX ↔ ADR 파일 link 일치 확인.

---

## 7. Risk + 완화

| Risk | 완화 |
|------|------|
| ADR-015 너무 길어짐 (메모리 + Clarification 통합) | 8 섹션 구조로 분리. 세부는 Q3 자료 참조 |
| 사용자가 본문 본 후 변경 요청 | ADR 은 살아있는 문서 — Status update 로 대응 |
| Q3 자료 ↔ ADR-015 사이 중복 | ADR 은 결정 박제 / Q3 는 옵션 비교. 다른 책임 |
| ADR-010 v2 마이그레이션 plan 부정확 | Phase E-1 진입 시 재검토 |

---

## 8. 완료 체크리스트

### D-1 ADR-015 본문
- [ ] 파일 생성
- [ ] 8 섹션 모두 작성
- [ ] Q3 §3, §7 반영
- [ ] 5 항목 정책 반영

### D-2 ADR-010 v2
- [ ] Status 갱신
- [ ] Decision 의 D 단일화 정식 결정
- [ ] Migration plan (D.1~D.5)
- [ ] Consequences 갱신

### D-3 ADR INDEX
- [ ] ADR-015 행 추가
- [ ] ADR-010 행 갱신
- [ ] 결정 누락 표 정리

### Phase D 종합
- [ ] 사용자 검토
- [ ] 커밋 (`docs(sprint15): Phase D ADR-015 + ADR-010 v2 본문` 권장)
- [ ] 다음 [`sprint15_phase_e1_memory_infrastructure.md`](./sprint15_phase_e1_memory_infrastructure.md) 진입

---

## 9. 다음 Phase 연결

Phase D 완료 후 → **Phase E-1**: 메모리 인프라 구현

[`sprint15_phase_e1_memory_infrastructure.md`](./sprint15_phase_e1_memory_infrastructure.md) 참조.

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-28 | 초안 — Phase D 3 sub-phase. ADR-015 본문 골격 (메모리 + Clarification 통합) + ADR-010 v2 (D 단일화 정식) + INDEX 갱신 |
