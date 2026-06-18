# Sprint 15 — Compact 이후 복원 가이드

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-04-29 (3차 점검) → **2026-04-30 D 통일 완료 갱신** |
| 마지막 커밋 | (D 통일 commit — 본 update 와 함께) |
| 마지막 큰 작업 | Phase C-Unify ⭐ — 어댑터 (B) 시도 후 D `planner.Plan` 단일화 직진. ADR-010 Accepted |
| Working tree | (D 통일 commit 직전) |
| 다음 즉시 작업 | **Phase C-2 브라우저 검증** (R-16/17/18) → C-5 완료 보고서 → Phase D / E |
| Sprint | **Sprint 14 A3 종결** (브라우저 검증만 남음) → Sprint 15 (POC 2차) 진입 대기 |
| 자동 테스트 | **239 passed + 2 skipped** (D 통일 후, 어댑터 5 TC 삭제 / 회귀 0) |
| 코드 변경 | plan_editor rewrite + ws_hitl 어댑터 제거 + scripts + 테스트 fixture + models deprecated |

---

## 0. Compact 이후 첫 행동

```
1. 본 문서 읽고 현 상황 파악 (5분)
2. 사용자에게 "Phase C-1 즉시 진입할까요?" 확인
3. 사용자 OK 시: sprint15_phase_c_nl_fix.md §3 따라 NL fix 코드 작성
4. 사용자가 다른 의도 있으면: 본 문서 §6 "다음 우선순위" 참조
```

---

## 1. 진짜 north star — 절대 잊지 말 것

🌟 **사용자 vision** ([`agent_specs/00_vision_and_intent.md`](../agent_specs/00_vision_and_intent.md)):

> 사용자와 에이전트의 파트너쉽을 통한 생동형 AI. 클로드/제미나이처럼 사용자와 LLM 이 브레인스토밍 + 토론으로 더 좋은 계획. todo plan 만들고 수정/삭제/보완. **각 기업의 암묵지 패턴화 → 맞춤형 에이전트**.

🌟 **사용자 통찰 1** — 도메인 지식 가정 X:
> 사용자가 시스템 도메인 지식 (DAG / schema / tool catalog) 가져야만 직접 편집 안전 = 비현실적

🌟 **사용자 통찰 2** ⭐ — 확장/변경 용이성 (2026-04-29):
> "쓰다보면 UX 변경 多. 지금 결정은 가설. 확장/변경 쉬운 구조 우선"

→ schema 자체보다 **schema 진화 비용 결정 구조** 가 본질. [`35_DB_SCHEMA §0.1`](../agent_specs/35_DB_SCHEMA_v1.0.md) 5 원칙 참조.

---

## 2. 이번 세션 (2026-04-28~29) 진행 요약

### 2.1 새 커밋 16개 (시간순, 최종)

| # | SHA | 제목 | 카테고리 |
|---|-----|------|---------|
| 1 | `a6966c2` | POC 1차 결산 + Sprint 15 vision/메모리/구현 계획 | 토대 |
| 2 | `2f8f0de` | Phase C 세부 작업계획서 — NL fix | Phase 분리 |
| 3 | `c9c88c0` | Phase D 세부 작업계획서 — ADR-010 v2 + ADR-015 | Phase 분리 |
| 4 | `ec6fc29` | Phase E1 세부 작업계획서 — 메모리 인프라 | Phase 분리 |
| 5 | `3c5b5c4` | Phase E2 세부 작업계획서 — 채팅 메모리 통합 | Phase 분리 |
| 6 | `ce602d9` | Phase E3 세부 작업계획서 — Clarification HITL | Phase 분리 |
| 7 | `ff97197` | Phase E4 세부 작업계획서 — NL 2차 LLM Tool Routing | Phase 분리 |
| 8 | `1830a86` | 마스터 계획서 overview 화 — 6 세부 문서 카탈로그 | Master |
| 9 | `51d6f6a` | Conversation list sidebar (#6) 신규 추가 | UI 추가 |
| 10 | `b4b3cce` | 35_DB_SCHEMA spec 신규 — ERD + 테이블 | DB spec |
| 11 | `c51b4e4` | ERD 시각화 파일 신규 — Mermaid 7 view | 시각화 |
| 12 | `1bae6d1` | 설계 원칙 ⭐ 박제 — 확장/변경 용이성 | 원칙 박제 |
| 13 | `7ae29dd` | Compact 복원 가이드 | 본 문서 |
| 14 | `3759d3c` | 점검 누락 정정 — 자동 테스트 + ERD § | 1차 점검 |
| 15 | `42b56a8` | 점검 누락 정정 2 — ADR INDEX + 산출물 §7.2 | 2차 점검 |
| **16** | **(본 갱신)** | **3차 점검 — Recovery SHA / Prompt 정밀화** | **3차 점검** |

### 2.2 코드 변경 = 0

이번 세션 = **계획서 / 자료 / 의도 박제만**. 코드 변경 안 됨.

다음 세션 부터 코드 작업 진입 (Phase C-1).

### 2.3 자동 테스트 상태

- 239 passed + 2 skipped (변경 X — Phase C-1 진입 시 244+ 가 목표)

---

## 3. 결정 lock 매트릭스

### 3.1 의도 / Sprint 명명

| 항목 | 결정 |
|------|------|
| Vision (north star) | [`00_vision_and_intent.md`](../agent_specs/00_vision_and_intent.md) v1.0 lock |
| 가설 H0~H4 | H0 의도 모호성 (전제) → H1 발견 → H2 학습 → H3 패턴 → H4 맞춤 |
| Sprint 14 A3 | NL fatal fix (B 어댑터) 만 종결 |
| Sprint 15 | POC 2차 = 메모리 + Clarification + NL 2차 |

### 3.2 6 항목 메모리 정책 (사용자 권고대로 lock)

| # | 항목 | 결정 |
|---|------|------|
| 1 | PostgreSQL CRUD | Q3 권고 — `memory_entries` Hybrid schema |
| 2 | 채팅 turn 로드 | 최근 20 + Load More |
| 3 | LLM 히스토리 | 마지막 5 turn + 1500 token cap |
| 4 | 길어질 시 | drop oldest (POC). 요약 = Sprint 16+ |
| 5 | Clarification | LLM hybrid + max 2회 + UX = "기존 todo 유지 + 부족분 요청" |
| **6** | **Conversation sidebar** | **좌측 / 최근 5 + Load More / 새 채팅 / 삭제 (turn 만, preference 보존)** |

### 3.3 Schema 결정 (Q1 권고 → D 직진으로 수렴)

- Sprint 14 A3: ~~B 어댑터~~ → **D `planner.Plan` 단일화 직진** (2026-04-30, ADR-010 Accepted)
- 이유: 사용자 통찰 "v1/v2 섞임 금지" + 통일 비용 ~3~4h = 1 day 미만 + 부채 0
- 어댑터 시도 commit `e767845` 의 어댑터 파일은 D 통일 commit 에서 삭제됨

### 3.4 설계 원칙 ⭐ (2026-04-29 사용자 통찰 lock)

[`35_DB_SCHEMA §0.1`](../agent_specs/35_DB_SCHEMA_v1.0.md) — 5 원칙:
1. JSONB content (정형 컬럼 최소화)
2. schema_version 필드 in content
3. Pydantic Optional 위주
4. String + validator (enum 신중)
5. Append-only message log

→ **모든 미래 변경 결정의 기준점**.

### 3.5 v1 schema (의도적 단순)

`memory_entries.content` (type=conversation) 의 v1 형식:
```json
{
  "schema_version": "v1",
  "conversation_id": "...",
  "session_id": "...",
  "messages": [{"role", "content", "ts", ...}],   // append-only
  "summary": "...",
  "metadata": {"plan", "result_data", "completed_at"}
}
```

**의도적 미정** (쓰면서 결정):
- message `type` 정확한 분류
- summary 생성 방법
- attachments 위치

---

## 4. 핵심 문서 위치 맵

### 4.1 의도 / 결산 (north star)

| 문서 | 역할 |
|------|------|
| [`agent_specs/00_vision_and_intent.md`](../agent_specs/00_vision_and_intent.md) | 🌟 **north star — 비전 / H0~H4 / 비기능 / 우선순위** |
| [`reports/sprint14_a3_poc1_settlement.md`](./sprint14_a3_poc1_settlement.md) | POC 1차 결산 (사실) |
| [`reports/sprint14_a3_poc1_deliverables.md`](./sprint14_a3_poc1_deliverables.md) | 산출물 정의 + Phase 흐름 |

### 4.2 사전 조사

| 문서 | 역할 |
|------|------|
| [`reports/sprint14_a3_research_q1_plan_schema.md`](./sprint14_a3_research_q1_plan_schema.md) | Plan/Todo schema 충돌 분석 (B → D 권고) |
| [`reports/sprint14_a3_research_q3_memory.md`](./sprint14_a3_research_q3_memory.md) | 메모리 architecture 9 영역 lock |

### 4.3 정식 spec (agent_specs)

| 문서 | 역할 |
|------|------|
| [`agent_specs/INDEX.md`](../agent_specs/INDEX.md) | spec 카탈로그 |
| [`agent_specs/35_DB_SCHEMA_v1.0.md`](../agent_specs/35_DB_SCHEMA_v1.0.md) | **DB Schema + ⭐ 설계 원칙 §0.1** |
| [`agent_specs/erd_database.md`](../agent_specs/erd_database.md) | ERD 시각화 8 view |
| [`agent_specs/30_DATA_MODELS_v1.0.md`](../agent_specs/30_DATA_MODELS_v1.0.md) | Pydantic 모델 (짝) |

### 4.4 구현 계획 (sprint15_phase_*)

| 문서 | 역할 | 시간 |
|------|------|------|
| [`reports/sprint15_implementation_plan.md`](./sprint15_implementation_plan.md) | **마스터 overview** (~272줄) | — |
| [`reports/sprint15_phase_c_nl_fix.md`](./sprint15_phase_c_nl_fix.md) | **Phase C — Sprint 14 A3 종결** ⭐ 다음 작업 | ~3h |
| [`reports/sprint15_phase_d_adr.md`](./sprint15_phase_d_adr.md) | Phase D — ADR-010 v2 + ADR-015 본문 | ~3.5h |
| [`reports/sprint15_phase_e1_memory_infrastructure.md`](./sprint15_phase_e1_memory_infrastructure.md) | Phase E1 — 메모리 인프라 | ~6h |
| [`reports/sprint15_phase_e2_chat_memory.md`](./sprint15_phase_e2_chat_memory.md) | Phase E2 — 채팅 메모리 + Sidebar (#6) | ~7h |
| [`reports/sprint15_phase_e3_clarification.md`](./sprint15_phase_e3_clarification.md) | Phase E3 — Clarification HITL ⭐ H0 자동 해결 | ~4.5h |
| [`reports/sprint15_phase_e4_nl_v2.md`](./sprint15_phase_e4_nl_v2.md) | Phase E4 — NL 2차 LLM Tool Routing | ~6h |

**총**: ~30.5h = 9~11 세션.

### 4.5 ADR 폴더

| ADR | 상태 | 비고 |
|-----|------|------|
| 000~007 | Accepted | 이전 세션까지 |
| 010 | 미작성 (Phase C-4 / D-2) | Sprint 14 A3 어댑터 + Sprint 15 D 단일화 |
| 015 | 미작성 (Phase D-1) | 메모리 + Clarification 통합 |

---

## 5. 다음 세션 진입 — Phase C-1 즉시 시작

### 5.1 작업 카탈로그

[`sprint15_phase_c_nl_fix.md`](./sprint15_phase_c_nl_fix.md) §3 따라:

**C-1 코드 변경** (~1시간):
- 신규: `backend/app/dream_agent/workflow_managers/hitl_manager/plan_adapter.py` (~80 LoC)
- 수정: `backend/api_v2/ws_hitl.py` 3 변경 (import + L507 + L591)
- 신규 테스트: `backend/tests/sprint14/test_a3_plan_adapter_unit.py` (5 TC)

**C-2 브라우저 검증** (~30분, 사용자 협조):
- R-16 ("4번 삭제") / R-17 ("3-4 순서 바꿔") / R-18 ("asdf xyz")

**C-3 spec 갱신** (~30분):
- 12_manager_layer v1.4 / INDEX / known_issues

**C-4 ADR-010 본문** (~30분):
- Sprint 14 A3 어댑터 + Sprint 15 D 단일화 결정 박제

**C-5 완료 보고서** (~15분):
- Sprint 14 A3 종결 선언

### 5.2 진입 prompt 권장

```
sprint15_phase_c_nl_fix.md 따라 Phase C-1 (NL fix B 어댑터) 진입해.
plan_adapter.py 코드 작성 + ws_hitl 수정 + 단위 테스트 5 TC.
```

### 5.3 완료 시점

R-16/17/18 모두 PASS 확인 + 자동 테스트 244+ → **Sprint 14 A3 종결**.

---

## 6. 다음 우선순위 (Phase C 외 옵션)

사용자가 다른 의도 가질 수 있음. 옵션:

| 옵션 | 설명 |
|------|------|
| **A. Phase C-1 진입** ⭐ 추천 | NL fix 즉시 — 1~2시간으로 Sprint 14 A3 종결 |
| B. Phase D ADR 본문 먼저 | 코드 전 ADR 박제. 단 Phase C 가 logical 선행 |
| C. 다른 누락 점검 | UI/UX / 다른 spec 보충 |
| D. 휴식 / 검토 | 사용자가 자료 자세히 검토 |

---

## 7. 잊지 말아야 할 사용자 통찰 박제

### 7.1 도메인 지식 가정 X

> 사용자가 시스템 schema (tool / DAG) 알아야 안전 = 비현실적

→ ADR-002 NL 2차 진입 정당성. Sprint 15 Phase E-4.

### 7.2 메모리는 자유 대화 / 학습의 인프라

> 메모리 + Clarification 묶음. 메모리 없이 clarification 만 만들면 부채.

→ ADR-015 = 메모리 + Clarification 통합 architecture.

### 7.3 확장/변경 용이성 ⭐ (2026-04-29)

> "쓰다보면 UX 변경 多. 지금 결정은 가설."

→ 35 §0.1 5 원칙 박제. 모든 schema 결정의 기준.

### 7.4 ChatGPT/Claude 같은 sidebar UI

> 좌측 conversation list / 최근 5개 / 새 채팅 / 삭제

→ 5 항목 → 6 항목 (#6 신규). Phase E2-5.

---

## 8. 잠재 리스크 / 모호 항목

### 8.1 어댑터 throwaway 비용

Phase C-1 어댑터 = Sprint 15 D 단일화 시 폐기. **의도된 throwaway**. ADR-010 본문에 명시.

### 8.2 Clarification UX 세부 미정

모달 vs inline vs 통합 = 구현 중 결정 (Q4 SKIP). 사용자 의도 lock = "기존 todo 유지 + 부족분 요청".

### 8.3 message type 정확한 분류 미정

35 §0.1 의도적 단순. 쓰면서 정의.

### 8.4 docs/walkthroughs/ 미커밋

사용자 검토 중. compact 후에도 그대로 untracked.

---

## 9. Compact 이후 — 사용자 prompt 옵션 + Claude 첫 응답 가이드

### 9.1 사용자가 입력할 prompt — 4 옵션

#### 🟢 옵션 A (표준, 권장) — 안전한 시작

```
sprint15_compact_recovery.md 읽고 현 상황 파악 후 다음 단계 안내해줘.
```

→ Claude 가 본 문서 읽고 §9.2 형식의 status report → 사용자 결정 대기.
→ **가장 안전. 자동 진입 X.**

#### 🟡 옵션 B — Phase C-1 즉시 진입

```
sprint15_compact_recovery.md 읽고 sprint15_phase_c_nl_fix.md §3 따라
Phase C-1 (NL fix B 어댑터) 코드 작성 즉시 진입해. plan_adapter.py 신규 +
ws_hitl 수정 + 단위 테스트 5 TC.
```

→ Claude 가 본 문서 빠르게 읽고 즉시 코드 작업.
→ **사용자가 작업 흐름 확실할 때.**

#### 🟡 옵션 C — Phase D ADR 본문 우선

```
sprint15_compact_recovery.md 읽고 sprint15_phase_d_adr.md 따라
ADR-015 (메모리 + Clarification) 본문 작성 진입해. Q3 §3, §7 그대로 + UX placeholder.
```

→ 코드 전 결정 박제 우선. Phase C 보다 D 먼저 가는 흐름.

#### 🟢 옵션 D — 검토 / 다른 누락 점검

```
sprint15_compact_recovery.md 읽고 결정 lock + 설계 원칙 + 6 항목 정책 다시 점검해줘.
의심되는 일관성 / 누락 있으면 보고.
```

→ 작업 시작 전 한 번 더 검토.

### 9.2 Claude 첫 응답 — 표준 status report (옵션 A 응답 형식)

본 문서 읽고 다음 형식으로 응답:

```markdown
## 복원 완료

| 항목 | 값 |
|------|-----|
| 마지막 커밋 | `42b56a8` (점검 누락 정정 2) |
| 이번 세션 누적 | 16 커밋 (POC 1차 결산 / 6 Phase 세부 / 설계 원칙 / DB spec / ERD / Compact recovery / 3차 점검) |
| 코드 변경 | 0 (모두 계획서 + 박제) |
| 자동 테스트 | 239 passed + 2 skipped (변경 X) |
| Sprint 상태 | Sprint 14 A3 종결 직전 — Sprint 15 (POC 2차) 진입 대기 |

## 사용자 통찰 4가지 박제 (절대 잊지 말 것)

1. 🌟 도메인 지식 가정 X (R-5~R-7 입증)
2. 🌟 메모리 = 자유 대화 / 학습 인프라 (ADR-015)
3. 🌟 확장/변경 용이성 (35 §0.1, 2026-04-29) ⭐ 최신
4. 🌟 ChatGPT 스타일 sidebar (#6 정책)

## 결정 lock 매트릭스 (요약)

- 6 항목 메모리 정책 lock (1~6)
- 5 설계 원칙 (JSONB / schema_version / Optional / String validator / append-only)
- Schema: B 어댑터 → Sprint 15 D 단일화
- ADR-010 / ADR-015 본문 작성 대기

## 다음 단계 — 4 옵션

| 옵션 | 작업 | 시간 | 추천도 |
|------|------|------|------|
| A | Phase C-1 (NL fix B 어댑터) | ~1시간 | ⭐ 추천 (logical 선행) |
| B | Phase D ADR 본문 (010/015) | ~3.5시간 | 코드 전 박제 우선 시 |
| C | 다른 누락 점검 | 가변 | 의심 영역 있을 시 |
| D | 휴식 / 검토 | 가변 | 자료 자세히 검토 |

어느 옵션으로 진입하시겠습니까?
```

### 9.3 검증 체크리스트 — 사용자가 받는 응답이 맞는지

Claude 가 위 응답을 줬을 때 사용자가 다음 항목 확인:

- [ ] 마지막 커밋 SHA = `42b56a8` (정확)
- [ ] 누적 커밋 수 = **16** (정확)
- [ ] 사용자 통찰 4가지 모두 언급
- [ ] 6 항목 정책 + 5 설계 원칙 모두 lock 표기
- [ ] 다음 단계 4 옵션 제시 + Phase C-1 추천

**틀린 항목 있으면**: Claude 가 본 문서 제대로 안 읽음. "다시 읽고 정확히 보고해" 요청.

### 9.4 작업 진입 후 Claude 동작 가이드 (옵션 B 진입 시)

옵션 B 진입 시 Claude 는:

1. `sprint15_phase_c_nl_fix.md` §3 읽기
2. **C-1 작업 1.1**: `plan_adapter.py` 신규 작성 (~80 LoC, Q1 §6 권고대로)
3. **C-1 작업 1.2**: `ws_hitl.py` 3 변경 (import + L507 + L591)
4. **C-1 작업 1.3**: 단위 테스트 신규 (`test_a3_plan_adapter_unit.py` 5 TC)
5. 자동 테스트 실행 — 244+ passed 확인
6. **C-2 진입 안내** — 사용자에게 R-16/17/18 브라우저 검증 요청

각 step 완료 시 사용자에게 보고. 사용자 검증 후 다음 step 진입.

### 9.5 막혔을 때 trouble-shooting prompt

#### Claude 가 헷갈릴 때
```
sprint15_compact_recovery.md 다시 읽고 결정 lock + 설계 원칙 정확히 정리해.
이전 세션의 모든 결정이 이 문서 안에 있음.
```

#### 어떤 문서 봐야 할지 모를 때
```
sprint15_implementation_plan.md §0.1 의 6 세부 문서 카탈로그 확인해줘.
현재 작업이 어느 phase 인지 식별 후 해당 phase 세부 문서 따라가.
```

#### 사용자 의도 모를 때
```
agent_specs/00_vision_and_intent.md §1 vision + §2 가설 H0~H4 다시 읽어.
모든 결정의 north star.
```

#### 구체 작업이 막혔을 때
```
sprint15_phase_<현재phase>.md §완료 체크리스트 확인해서 어디서 막혔는지 파악해.
```

---

## 10. 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-29 | 초안 — Sprint 15 진입 직전 compact 준비. 11 커밋 / 결정 lock / 설계 원칙 / 다음 작업 (Phase C-1). 사용자 통찰 4가지 박제 |
| 2026-04-29 | **3차 점검 + Prompt 정밀화** — 마지막 커밋 SHA 갱신 (1bae6d1 → 42b56a8). 커밋 표 11개 → 16개. §9 Compact 이후 prompt 4 옵션 (A 표준 / B Phase C-1 즉시 / C ADR 우선 / D 검토). §9.2 Claude 표준 응답 형식. §9.3 검증 체크리스트. §9.4 작업 진입 가이드. §9.5 trouble-shooting prompt 4 종 |
