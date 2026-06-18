# Sprint 14 A3 → Sprint 15 — 산출물 정의 계획서 (초안)

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-04-28 |
| 작성자 | Claude (사용자 검토 대기 — Q1~Q6 결정 입력 받음) |
| 자매 문서 | [`sprint14_a3_poc1_settlement.md`](./sprint14_a3_poc1_settlement.md) (결산 — 사실 토대) |
| 본 문서 위치 | `docs/reports/sprint14_a3_poc1_deliverables.md` |
| 채택된 흐름 | **Feature-driven Iterative** (대규모 v2.0 rewrite 폐기) |

---

## 0. 본 문서의 역할

**미래 시점 정리** — POC 1차 결산을 토대로 어떤 문서·코드·테스트가 어느 순서로 어떻게 갱신되는지 정의.

**이 문서가 다루지 않는 것**:
- 검증 결과 / ISSUE 본문 → 결산 문서 (사실)
- ADR 본문 → 별도 ADR 파일 (결정 박제)

본 문서는 **Step 1~6 의 작업 카탈로그 + 각 Step 의 산출물 + Q1~Q6 결정 entry-point**.

---

## 1. 채택된 흐름 (결산 §8 lock + 2026-04-28 갱신 + Q4 SKIP)

```
Phase B  사전 조사 (의도 + 큰 그림 결정)
            ├─ B-0  의도 문서 v1.0 ✅ lock
            ├─ B-Q1 Plan schema 자료 ✅ (B 어댑터 → Sprint 15 D 단일화 권고)
            ├─ B-Q3 메모리 설계 v1.0 ✅ lock (9 영역 권고대로)
            └─ B-Q4 Clarification UX 자료 ❌ SKIP (UX 세부는 구현 중 결정)
            ↓
Phase C  Sprint 14 A3 종결 (POC 1차 Minimum Viable Completion)
  Step 1   NL fix (B 어댑터 — throwaway, Q1 권고)
  Step 2   spec 점진 update + R-16/17/18 검증
            ↓
Phase D  Sprint 15 시작 — ADR 결정 + 구현 진입
  Step 3   ADR-010 본문 (Q1 권고: B 어댑터 → Sprint 15 D planner.Plan 통일)
  Step 4   ADR-015 본문 (메모리 부분 = Q3 §3/§7 그대로 / Clarification UX 부분 = placeholder, 구현 중 결정)
            ↓
Phase E  Sprint 15 — POC 2차 구현 (UX 는 코드 작성 중 결정)
  Step 5   메모리 시스템 P0 구현 (Q3 권고 기반)
            ├─ Hybrid schema (memory_entries 테이블)
            ├─ MemoryEntry / MemoryContext / Pattern Pydantic
            ├─ MemoryManager 7 메서드 (P0)
            └─ Cognitive 직전 cascade + Clarification 통합
  Step 6   Clarification HITL 구현 (UX 점진 결정 — 구현 중 모달/inline/통합 선택)
  Step 7   NL 2차 (LLM Tool Routing — ADR-002 §2차)
  Step 8   자연 v? bump (변경 누적 결과)
```

각 Step 의 산출물 정의는 §3 참조.

---

## 2. 결정해야 할 Q (Q1~Q6)

본 계획서가 답해야 할 6 질문. 각 Q 의 옵션 매트릭스 + 제 추천 + 사용자 결정 lock 칸.

### Q1 — ADR-010 schema 통합 옵션 선택 (Step 1)

**문제**: 3 Plan 클래스 + 2 Todo 클래스 공존. NL 경로 fatal.

| 옵션 | 내용 | 장점 | 단점 | 추천 |
|------|------|------|------|------|
| A. **단일 Plan 모델** (Pydantic) | `models/plan.py::Plan` 만 유지, `planner.Plan` 폐기. PlannedTodo → TodoItem 통합 | 가장 깔끔. 타입 안전성 ↑ | 큰 마이그레이션 (planner / executor / ws_hitl 모두) | Sprint 15 P0 |
| B. **dict + 어댑터 layer** | progress.plan = dict 유지. `_handle_todo_edit_nl` 만 변환 함수 (`planner_dict_to_pydantic`) 추가 | 작은 변경 (1~2시간). NL 경로만 fix | 변환 부담 영구. 두 schema 동거 | **Sprint 14 A3 적합** |
| C. **단계적 마이그레이션** | B 로 시작 → 단계별 A | 위험 분산 | 일정 길어짐 | 중기 |

**제 추천**: **B (어댑터)** — Sprint 14 A3 종결 목표가 "Minimum Viable Completion" 이므로 작은 fix. A 단일화는 Sprint 15 P0 ADR-010 본문에서 정식 결정.

**사용자 결정**: `____` (B 권고 / A / C / 다른 안)

### Q2 — Step 2 spec 점진 update 범위

**문제**: NL fix 후 어떤 spec 을 minor bump 할지.

| 문서 | 현 버전 | 권고 bump | 변경 내용 |
|------|---------|--------|---------|
| `12_manager_layer` | v1.3 | **v1.4** | `_handle_todo_edit_nl` 의 어댑터 변환 함수 명시. dict ↔ Pydantic 경계 |
| `21_WEBSOCKET_PROTOCOL` | v1.4 | **v1.5** | `todo_edit_nl` 의 schema 변환 ack 형식 (변경 없으면 skip) |
| `22_error_codes` | v1.1 | **v1.2** | NL 변환 실패 신규 코드 (`PLAN_SCHEMA_MISMATCH` 등) — 발생 시점만 추가 |
| `30_DATA_MODELS` | v1.0 | **건드리지 않음** | ADR-010 정식 결정은 Sprint 15 — 임시 어댑터는 minor 차원 X |
| `INDEX.md` | — | 갱신 | 위 v bump 표시만 |

**제 추천**:
- 12 v1.4 = 필수 (가장 큰 변경 — 어댑터 함수가 manager layer 의 책임)
- 22 v1.2 = 필수 (신규 error code)
- 21 v1.5 / 30 v1.0 = skip 또는 minor 표기만
- INDEX 갱신 필수

**사용자 결정**: `____` (권고대로 / 더 / 덜)

### Q3 — ADR-015 architecture 큰 그림 (Step 3)

**문제**: 메모리 + HITL 트리거 + clarification 통합 architecture 의 큰 그림.

이 Q 는 **별도 ADR 본문에서 결정** — 본 계획서는 결정해야 할 sub-Q 만 식별.

#### ADR-015 sub-Q (Step 3 ADR 작성 시 답할 것)

- **Q3.1** 메모리 layer 위치 — Cognitive 입력? Planning 입력? 별도 layer (5번째)?
- **Q3.2** 메모리 저장 시점 — Response 후? clarification 답변 시? 둘 다?
- **Q3.3** 메모리 schema — Key-Value? Document? Graph?
- **Q3.4** Clarification trigger — Cognitive 자체가 감지? 별도 validation node?
- **Q3.5** Clarification 응답 흐름 — StructuredQuery augment 후 cognitive 재실행? planning 직진?
- **Q3.6** 메모리 ↔ Clarification 연결 — 답변 즉시 메모리 저장? 다음 쿼리 메모리 조회?
- **Q3.7** Manager 책임 분담 — `MemoryManager` 신규? `HITLManager` 확장? `ClarificationManager` 신규?

→ **본 계획서에선 Step 3 의 인풋만 정의. Sub-Q 결정은 ADR-015 본문에서.**

**사용자 결정**: `____` (Step 3 진입 시 ADR-015 작성 — 동의?)

### Q4 — Clarification UX 옵션

**문제**: 사용자에게 모호도 보완 요청을 어떤 UI 로?

| 옵션 | UI | 장점 | 단점 | 추천 모호도 |
|------|----|------|------|----------|
| A. 전용 모달 | 신규 "💬 정보 보완 요청" 모달 | 의도 명확. plan_review 와 분리 | HITL trigger 4번째 type | (a) Missing field, (b) Default confirm, (c) Ambiguity |
| B. 채팅 inline | 메인 응답 영역에 질문 메시지 | 가장 자연스러운 대화 | 채팅 흐름 관리. 신규 message type | 자유 대화 (3차) |
| C. Plan review 통합 | plan_review 모달에 ⚠️ 배너 + 보완 입력 | 기존 모달 재사용 | 가정 plan 만든 후 변경 = ISSUE-015 악화 | (b) Default confirm 만 |

**제 추천**:
- **A 채택 (전용 모달)** — 모든 모호도 유형 통일된 입구. 3 유형별로 모달 안 UI 만 변경 (input / radio / radio with default)
- B 는 Sprint 16+ NL 3차 진입 시 고려
- C 는 ISSUE-015 의 LLM 비용 누적 문제 — 비추

**사용자 결정**: `____` (A / B / C / 조합)

### Q5 — ISSUE-002 / 004 / 011 / 013 / 015 처리 시점

**문제**: 미해결 ISSUE 5건을 어느 Step 에 묶을지.

| ISSUE | 본질 | 권고 처리 시점 |
|------|------|------------|
| 002 Cognitive enum 실패 | LLM 안정성 | **Step 1 또는 Step 2** (작은 fix — prompt + fallback) |
| 004 모달 헤더 stale | UX 부분 갱신 | **Step 4 묶음** (다른 UI 갱신과 함께 minor) |
| 011 pdf_renderer hallucination | LLM grounding | **Step 5** (NL 2차 LLM Tool Routing 의 부수 — catalog grounding 강화) |
| 013 HITL request not found | progress 일관성 | **Step 4 묶음** (메모리 + HITL 정리 시 함께) |
| 015 modify approve LLM 재호출 | LLM 비용 | **Step 4 묶음** (HITL 트리거 정책 안에서 — modify path 정리) |

**제 추천**:
- 002 → Step 2 묶음 (NL fix 와 함께 cognitive 안정성)
- 004 / 013 / 015 → Step 4 묶음 (메모리 + HITL 통합 시)
- 011 → Step 5 묶음 (NL 2차 LLM grounding)

**사용자 결정**: `____` (권고대로 / 다른 묶음)

### Q6 — Legacy 백업 정책

**문제**: 문서 v bump 시 옛 버전 처리.

| 변경 규모 | 패턴 | 적용 |
|---------|------|------|
| Minor bump (v1.x → v1.x+1) | **inline** — 동일 폴더에 두 파일 공존 | Sprint 14 A3: 12 / 22 등 |
| Major rewrite (v1.x → v2.x, schema 깨짐) | **legacy 이동** — `docs/agent_specs/_legacy/` | 현재 적용 대상 없음 (v2.0 rewrite 폐기됨) |
| 단일 파일 schema 깨짐 | **inline + Status 마커** — 옛 파일에 `Status: superseded by vN.M` 추가 | Sprint 15 ADR-010 정식 결정 시 30_DATA_MODELS |

**제 추천**:
- **현재**: legacy 폴더 도입 **불필요** — v2.0 rewrite 폐기로 major rewrite 없음
- **Sprint 15 진입 시**: ADR-010 정식 통합 시점에 30_DATA_MODELS 가 v2.0 될 가능성 → 그때 `_legacy/` 도입 검토
- **현재 안전책**: minor bump 시 inline + INDEX.md 의 changelog 강화

**사용자 결정**: `____` (지금 도입 / Sprint 15 진입 시 / 도입 안 함)

---

## 3. Step 별 산출물 정의

### Step 0.5 — Phase B 사전 조사 (2026-04-28 추가)

**입력**: 결산 §9 lock + Q1/Q3/Q4 보류 결정

**산출물 — 3 자료 문서**:

#### 자료 1: Plan/Todo schema 현황 매핑 (Q1)

**파일**: `docs/reports/sprint14_a3_research_q1_plan_schema.md` (가칭)

**내용**:
- 3 Plan 클래스 사용 위치 전수 조사 (grep + 호출 그래프)
- TodoItem vs PlannedTodo 사용 빈도 / 위치 / 의존성
- dict ↔ Pydantic 변환 지점 매핑
- 옵션 A/B/C 별 마이그레이션 cost 추정 (파일 수, 라인 수, breaking changes)
- 각 옵션의 Sprint 14 A3 어댑터 ↔ Sprint 15 본격 마이그레이션 path

#### 자료 2: 메모리 architecture 후보 (Q3)

**파일**: `docs/reports/sprint14_a3_research_q3_memory.md` (가칭)

**내용**:
- 기존 `memory_manager/` 폴더 placeholder 확인 ✅ (비어있음)
- PostgreSQL Checkpointer 기존 사용 분석 (Sprint 12 도입)
- 메모리 schema 후보:
  - Key-Value (단순, fast)
  - Document (JSONB, flexible)
  - Hybrid (key + JSON content)
- 저장 단위 후보: session / conversation / user / global
- 조회 시점 후보: cognitive 입력 / planning 입력 / execution 시점 / 다중
- 저장 시점 후보: response 후 / clarification 답변 시 / explicit memory action
- FR-14 기존 spec 검토 (`01_requirements` 의 메모리 항목)
- 다른 시스템 참고 (LangGraph Memory, OpenAI Memory 등 — 가벼운 비교)

#### 자료 3: Clarification UX 흐름 비교 (Q4)

**파일**: `docs/reports/sprint14_a3_research_q4_clarification_ux.md` (가칭)

**내용**:
- (α) memory 보관 + 추가 질문 안: 흐름 다이어그램 + 코드 영향 + 메모리 의존
- (β) interrupt 후 보완 안: 흐름 다이어그램 + 코드 영향 + 메모리 무관
- (γ) 혼합 안 (사용자 인사이트 — cognitive 직후 ask + plan_review 보완): 흐름 + 영향
- 각 안의 LLM 비용 / latency / UX 자연스러움 / 메모리 의존도 비교 표
- 모호도 3 유형 (a/b/c) 별 적합한 안 매핑

**작업량**: 1~2세션 (Q1 = 0.5세션, Q2/Q3 각 0.5~1세션)

**검증**: 사용자 검토 → Phase C (NL fix) 진입 결정 + Phase D 결정 입력 확정

### Step 1 — NL fix (Sprint 14 A3, 어댑터 임시)

**입력**: Phase B 자료 1 의 어댑터 형태 권고 (Q1 lock 없이 throwaway 의도)

**산출물 — 코드 + 테스트**:

### Step 2 — NL fix + spec 점진 update (Sprint 14 A3)

**입력**: Step 1 ADR + Q2 / Q5 답

**산출물**:

#### 2.1 코드
- [ ] `backend/api_v2/ws_hitl.py::_handle_todo_edit_nl` 어댑터 함수 추가
  - 신규 함수: `_planner_dict_to_pydantic(plan_dict: dict) -> Plan`
  - 변환: `task_type` → `task` (또는 양쪽 모두 보존), `session_id` 채움, etc.
- [ ] (Q5) ISSUE-002 fix — cognitive prompt 강화 + enum fallback
- [ ] R-16/17/18 검증

#### 2.2 자동 테스트
- [ ] `backend/tests/sprint14/test_a3_ws_hitl_nl_integration.py` — 어댑터 회귀 테스트 추가

#### 2.3 문서
- [ ] **`12_manager_layer_v1.4.md`** — 어댑터 함수 명시
- [ ] **`22_error_codes_v1.2.md`** — `PLAN_SCHEMA_MISMATCH` 등 신규 코드
- [ ] (선택) `21_WEBSOCKET_PROTOCOL_v1.5.md` — 변경 없으면 skip
- [ ] **`INDEX.md`** — bump 반영
- [ ] **`sprint14_a3_known_issues.md`** — ISSUE-016 해결 표기, ISSUE-002 fix 표기
- [ ] **`sprint14_a3_test_log.md`** — 세션 #2 R-16/17/18 결과 추가

**작업량**: 2~3시간 (1세션)

**검증**:
- 자동 테스트 239+ 유지
- 브라우저 R-16/17/18 PASS
- 사용자 검증

**완료 시점**: Sprint 14 A3 종결.

### Step 3 — ADR-015 architecture 본문 (Sprint 15 시작)

**입력**: Q3 (계획서 통과) + Q4 (UX 옵션)

**산출물**:
- [ ] **ADR-015** 본문 작성 (`docs/agent_specs/adr/ADR-015_memory_intent_communication.md`)
  - 메모리 layer 위치 결정 (Q3.1)
  - 저장/조회 시점 (Q3.2)
  - Schema 결정 (Q3.3)
  - Clarification trigger 메커니즘 (Q3.4~3.5)
  - 메모리 ↔ Clarification 연결 (Q3.6)
  - Manager 책임 분담 (Q3.7)
- [ ] **ADR INDEX** 갱신

**작업량**: 1~2세션 (큰 결정)

**검증**: 사용자 검토 → Step 4 진입 결정

### Step 4 — 메모리 + Clarification 구현 (Sprint 15 본격)

**입력**: ADR-015 본문 + Q5 묶음 (004 / 013 / 015)

**산출물**:

#### 4.1 코드
- [ ] **MemoryManager** (신규) — ADR-015 결정대로
- [ ] **HITLManager** 확장 — clarification trigger
- [ ] **Cognitive 출력 schema** 확장 — `clarifications_needed: list[ClarificationRequest]`
- [ ] **ws_hitl 신규 message type** — `clarification_request` / `clarification_response`
- [ ] **dashboard** — 신규 clarification 모달 (Q4 결정 따라)
- [ ] (Q5) ISSUE-004 fix — 모달 헤더 갱신
- [ ] (Q5) ISSUE-013 fix — ack accepted 일관성
- [ ] (Q5) ISSUE-015 fix — modify approve LLM 재호출 skip

#### 4.2 자동 테스트
- [ ] 신규 group I (Memory)
- [ ] 신규 group J (Clarification)

#### 4.3 문서
- [ ] **`10_system_architecture` 갱신** — 5번째 layer 또는 cross-cutting Memory
- [ ] **`30_DATA_MODELS` 갱신** — `ClarificationRequest`, MemorySchema 등
- [ ] **`12_manager_layer` 갱신** — MemoryManager 추가
- [ ] **`21_WEBSOCKET_PROTOCOL` 갱신** — 신규 message type
- [ ] **신규 spec** `33_memory_system_v1.0.md` (가칭)
- [ ] **신규 spec** `34_clarification_hitl_v1.0.md` (가칭)
- [ ] **`INDEX.md`** 갱신

**작업량**: 3~4세션

**검증**: 신규 시나리오 (R-19~ Memory / R-20~ Clarification) + 자동 테스트

### Step 5 — NL 2차 (LLM Tool Routing)

**입력**: Step 4 완료

**산출물**:
- [ ] `plan_editor` 확장 — multi-step + clarification 통합
- [ ] (Q5) ISSUE-011 fix — pdf_renderer hallucination = LLM tool catalog grounding
- [ ] **ADR-002** §2차 완료 표기
- [ ] **`02_nl_edit_phase2_v1.0.md`** (가칭) 또는 ADR-002 본문 갱신
- [ ] R-21~R-25 신규 시나리오 (복잡 NL)

**작업량**: 2~3세션

### Step 6 — 자연 v? bump

**입력**: Step 5 완료

**산출물**:
- 누적 변경 결과로 자연스럽게 v 카운트 증가 — **의도적 rewrite 아님**
- INDEX.md 한 번 정리

**작업량**: 30분

---

## 4. Legacy 백업 정책 (Q6 답 따라)

기본: minor bump 시 inline 공존 (`*_v1.4.md`, `*_v1.5.md` 둘 다 폴더에 둠)

ADR-010 정식 통합 (Sprint 15) 시점에 `30_DATA_MODELS` v2.0 가능성 — 그때 `_legacy/` 도입 검토.

**현재 (Sprint 14 A3)**: legacy 폴더 도입 안 함.

---

## 5. 검증 / 테스트 전략

### 5.1 자동 테스트
- 각 Step 끝에 group A~H 모두 통과 + 신규 group 추가
- DC-* 검증 통과 (DC-4 잔여 archived 는 그대로)

### 5.2 브라우저 검증
- Step 2 끝: R-16/17/18 PASS
- Step 4 끝: R-19~ (Memory) + R-20~ (Clarification) 신규 시나리오
- Step 5 끝: R-21~R-25 (복잡 NL)

### 5.3 문서 검증
- 각 Step 끝에 INDEX 일관성 + 변경된 spec ↔ 코드 ↔ ADR 3자 일치
- DC-* 자동 검증으로 link 무결성

---

## 6. Risk + 완화

| Risk | 완화 |
|------|------|
| Sprint 14 A3 어댑터 fix 가 Sprint 15 단일화 시 throw-away | ADR-010 본문에 migration path 명시. 어댑터는 의도된 임시 |
| Sprint 15 oversprint (Step 3+4 묶음) | Step 3 (ADR) → Step 4 (구현) 분리. 사용자 검토 gate 통과 후 진입 |
| Step 4 의 신규 spec 2개 (33 / 34) 동시 작성 부담 | 점진 — 코드와 함께. 한 번에 v2.0 X |
| Clarification UX 결정 (Q4) 후 추후 변경 시 dashboard 큰 rewrite | Q4 답 lock 시 ADR-015 에 박제. UX 변경 = 별도 ADR |
| ISSUE 5건 묶음 시점 누락 | Q5 답 lock 시 본 계획서에 박제 (§ 2 표) |

---

## 7. 결정 lock 상태 (2026-04-28 최종)

| # | Q | 제 추천 | 사용자 답 (2026-04-28) |
|---|---|--------|---------|
| 1 | ADR-010 옵션 | B 어댑터 (Sprint 14 A3) → D planner.Plan 통일 (Sprint 15) | ✅ **lock** — Phase B-Q1 자료 §7 권고대로. Phase C 어댑터, Phase D 본문 |
| 2 | Step 2 spec bump 범위 | 12 v1.4 + 22 v1.2 + INDEX | ✅ lock |
| 3 | 메모리 architecture | Q3 자료 §3, §7 (Hybrid schema + 5 tier + Cognitive cascade 등) | ✅ **lock** — Phase B-Q3 9 영역 권고대로 |
| 4 | Clarification UX | 큰 그림 = Cognitive 직전 cascade + Clarification 판단 (Q3 영역 4) / 세부 UX = 구현 중 결정 | ✅ **lock** — Q4 자료 SKIP, Sprint 15 구현 중 결정 |
| 5 | ISSUE 5건 묶음 시점 | 002→Step2, 004/013/015→Step5, 011→Step7 | ✅ lock |
| 6 | Legacy 백업 정책 | rename 으로 버전업, legacy 폴더 X | ✅ lock |
| 7 | 의도 문서 (사용자 vision) | 신규 — `00_vision_and_intent.md` | ✅ **lock v1.0** (H0~H4 + 의존도 + 비기능 + 우선순위) |
| flow | 사전 조사 phase | 옵션 X | ✅ lock |

**lock 결과**: ✅ **모두 lock** — Phase C 진입 가능.

**작성된 사전 조사 자료**:
- [`sprint14_a3_research_q1_plan_schema.md`](sprint14_a3_research_q1_plan_schema.md) ✅ 완료
- [`sprint14_a3_research_q3_memory.md`](sprint14_a3_research_q3_memory.md) ✅ 완료
- ~~`sprint14_a3_research_q4_clarification_ux.md`~~ ❌ SKIP (사용자 결정)

### 7.1 신규 추가 (2026-04-28) — Conversation list sidebar

5 항목 정책 → 6 항목 정책 (사용자 요구로 #6 신규):
- **#6 Conversation list sidebar**: 좌측 sidebar / 최근 5개 + Load More / 새 채팅 / 삭제 (turn 만, preference 보존)
- Phase E-2 의 E2-5 sub-phase 로 추가 (+3h)
- 의존: memory_entries 의 `conversation_meta` type 추가 (Phase E-1 갱신)
- 상세: [`sprint15_phase_e2_chat_memory.md`](./sprint15_phase_e2_chat_memory.md) §6.5

### 7.2 추가 갱신 (2026-04-29) — 설계 원칙 + 시각화

- **설계 원칙 ⭐ 박제** (사용자 통찰): 35 spec §0.1 + 의도 문서 §5 + 5 phase 문서 일관 적용
- **35_DB_SCHEMA_v1.0** spec 신규 (정식 spec)
- **erd_database.md** 시각화 (Mermaid 8 view)
- **Compact 복원 가이드** (sprint15_compact_recovery.md)
- **ADR INDEX** 갱신 (010 / 015 메인 표 등재 + 결정 누락 표 ISSUE-010~016 / CAP-001 추가)
- 마스터 작업량 27.5h → 30.5h (E2-5 +3h)
- 자동 테스트 누적 갱신 (244 → 254 → 269 → 277 → 285)

---

## 8. 진행 흐름

```
[지금]   본 계획서 작성 ✅
            ↓
[다음]   사용자가 Q1~Q6 답 lock
            ↓
[Step 1] ADR-010 어댑터 본문 작성 (30~60분)
            ↓
[Step 2] NL fix + R-16/17/18 검증 + spec bump (1세션)
            ↓
[Sprint 14 A3 종결]
            ↓
[Step 3] ADR-015 본문 작성 (1~2세션)
            ↓
[Step 4~6] 구현 + 점진 spec update (3~4세션)
            ↓
[Sprint 15 POC 2차 종결]
```

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-28 | 초안 — 결산 §9 lock (A~G 동의 + H 통합) 반영. Q1~Q6 옵션 + 추천 + Step 1~6 산출물 정의. Risk + 검증 전략 |
