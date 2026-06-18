# Sprint 14 A3 종결 + Sprint 15 (POC 2차) — 마스터 구현 계획서 (Overview)

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-04-28 (마스터) / 6 세부 문서 분리 |
| 작성자 | Claude (사용자 5 항목 권고 lock 기반) |
| 역할 | **Overview / TOC / 결정 lock 박제** — 세부 작업은 6 세부 문서로 분리 |
| 자매 문서 | [`agent_specs/00_vision_and_intent.md`](../agent_specs/00_vision_and_intent.md) (north star) / [`agent_specs/35_DB_SCHEMA_v1.0.md`](../agent_specs/35_DB_SCHEMA_v1.0.md) (DB ERD + schema 정식 spec) / [`sprint14_a3_poc1_settlement.md`](./sprint14_a3_poc1_settlement.md) (결산) / [`sprint14_a3_poc1_deliverables.md`](./sprint14_a3_poc1_deliverables.md) (산출물 계획) / [`sprint14_a3_research_q1_plan_schema.md`](./sprint14_a3_research_q1_plan_schema.md) (Q1) / [`sprint14_a3_research_q3_memory.md`](./sprint14_a3_research_q3_memory.md) (Q3) |
| 세부 작업계획서 | §0.1 6 세부 문서 표 참조 |
| 위치 | `docs/reports/sprint15_implementation_plan.md` |
| 범위 | Phase C (Sprint 14 A3 종결) + Phase D (Sprint 15 ADR 본문) + Phase E (Sprint 15 구현) |

---

## 0. 본 문서의 역할

**Overview / 카탈로그 / 결정 lock 박제**.

세부 작업 (코드 골격 / 단위 테스트 / 시간 추정 / acceptance) 은 6 세부 문서로 분리됨.

본 문서가 다루는 것:
- 사용자 결정 lock (5 항목 정책 / Sprint 명명 등)
- Phase 별 의존성 그래프 + 시간 추정 합산
- 6 세부 문서 카탈로그
- Sprint 15 종결 시 Vision 진척 매핑

본 문서가 다루지 않는 것:
- Phase 별 세부 작업 (→ `sprint15_phase_*.md` 6 문서)
- 의도 / 비전 (→ `agent_specs/00_vision_and_intent.md`)
- 옵션 비교 / 트레이드오프 (→ research 문서들)
- 검증 결과 (→ `sprint14_a3_test_log.md` / `sprint15_test_log.md`)

### 0.1 6 세부 작업계획서 카탈로그

| Phase | 문서 | 핵심 작업 | 시간 |
|-------|------|---------|------|
| **C** | [`sprint15_phase_c_nl_fix.md`](./sprint15_phase_c_nl_fix.md) | NL fix B 어댑터 + R-16/17/18 + ADR-010 본문 + Sprint 14 A3 종결 | ~3h |
| **D** | [`sprint15_phase_d_adr.md`](./sprint15_phase_d_adr.md) | ADR-015 본문 (메모리 + Clarification 통합) + ADR-010 v2 (Sprint 15 D 단일화) | ~3.5h |
| **E1** | [`sprint15_phase_e1_memory_infrastructure.md`](./sprint15_phase_e1_memory_infrastructure.md) | DB 마이그레이션 + Pydantic models + MemoryManager 7 메서드 + API + UI | ~6h |
| **E2** | [`sprint15_phase_e2_chat_memory.md`](./sprint15_phase_e2_chat_memory.md) | persist_turn + 채팅창 로드 + Cognitive cascade + 토큰 cap + **Conversation sidebar (E2-5 신규)** | ~7h |
| **E3** | [`sprint15_phase_e3_clarification.md`](./sprint15_phase_e3_clarification.md) | StructuredQuery 확장 + Validator + Clarification 모달 + H0 자동 해결 ⭐ | ~4.5h |
| **E4** | [`sprint15_phase_e4_nl_v2.md`](./sprint15_phase_e4_nl_v2.md) | Catalog grounding + plan_editor 확장 + ISSUE-009/011 자연 해소 | ~6h |

**총 작업량**: ~30.5h = **9~11 세션** (E2-5 추가로 +3h).

작업 시작 시 → 해당 phase 의 세부 문서 따라가기. 본 문서는 overview / 결정 lock 만.

---

## 1. 사용자 결정 lock (2026-04-28)

### 1.1 6 항목 메모리 정책 (사용자 권고대로 lock — #6 추가)

| # | 항목 | 결정 |
|---|------|------|
| 1 | **PostgreSQL 대화기록 / 로드 / 삭제** | Q3 권고 — `memory_entries` 테이블 (Hybrid schema) + `MemoryManager` 7 메서드 |
| 2 | **채팅창 열 때 로드 개수 (turn)** | **최근 20 turn + Load More 버튼** |
| 3 | **이전 대화 LLM 참고 개수** | **마지막 5 turn + 토큰 budget cap (~1500 tokens)** |
| 4 | **대화 길어질 시 처리** | **잘라내기 (drop oldest)** — POC. 요약 LLM 은 Sprint 16+ |
| 5 | **Clarification (연속턴)** | **LLM `clarifications_needed` + required field validator (Hybrid)** + max 2회 + UX = "기존 todo 유지 + 부족분 요청" (구현 중 결정) |
| **6** | **Conversation list sidebar (신규 — 사용자 요구 2026-04-28)** | **좌측 sidebar / 최근 5개 conversation + Load More / 새 채팅 버튼 / 삭제 (turn 만, preference 보존) / 클릭 시 최근 5 turn 로드** |

### 1.2 ADR / Sprint 명명

- **Sprint 14 A3** = NL fatal fix 만 종결
- **Sprint 15 = POC 2차** = 메모리 + Clarification + NL 2차

### 1.3 Schema (Q1 권고)

- **Sprint 14 A3**: B 어댑터 (throwaway, ~140 LoC)
- **Sprint 15**: D planner.Plan 통일 (lifecycle metadata 폐기)

---

## 2. 의존성 그래프

```
[Sprint 14 A3 종결]                                    → sprint15_phase_c_nl_fix.md
   Phase C-1  NL fix B 어댑터 (~140 LoC)
        ↓
   Phase C-2  R-16/17/18 검증
        ↓
   Phase C-3  spec 점진 update (12 v1.4)
        ↓
   Phase C-4  ADR-010 본문
        ↓
   Phase C-5  Sprint 14 A3 완료 보고서
   ─────────────────────────────────────
[Sprint 15 시작 — POC 2차]                              → sprint15_phase_d_adr.md
   Phase D-1  ADR-015 본문 (메모리 + Clarification)
        ↓
   Phase D-2  ADR-010 v2 (Sprint 15 D 단일화)
   ─────────────────────────────────────
[Sprint 15 구현]
   Phase E-1  메모리 인프라                              → sprint15_phase_e1_memory_infrastructure.md
        ↓
   Phase E-2  채팅 메모리 통합                           → sprint15_phase_e2_chat_memory.md
        ↓
   Phase E-3  Clarification HITL (H0 자동 해결 ⭐)        → sprint15_phase_e3_clarification.md
        ↓
   Phase E-4  NL 2차 (LLM Tool Routing)                 → sprint15_phase_e4_nl_v2.md
        ↓
   Phase E-5  자연 v? bump (변경 누적)
```

---

## 3. Phase 별 핵심 (각 phase 의 세부 문서 link)

각 phase 의 **모든 세부 작업** (파일 / LoC / 코드 골격 / 단위 테스트 / acceptance / risk) 은 해당 phase 의 세부 문서에. 본 § 는 한눈 보기용 요약만.

### 3.1 Phase C — Sprint 14 A3 종결

📄 **[sprint15_phase_c_nl_fix.md](./sprint15_phase_c_nl_fix.md)** (~3h)

- NL 편집 ("4번 삭제") fatal 해소
- 5 sub-phase: 어댑터 코드 → R-16/17/18 검증 → spec bump → ADR-010 본문 → 완료 보고서
- Acceptance: R-16/17/18 PASS + 자동 테스트 244+

### 3.2 Phase D — Sprint 15 ADR 본문

📄 **[sprint15_phase_d_adr.md](./sprint15_phase_d_adr.md)** (~3.5h)

- ADR 결정 박제만, 코드 X
- 3 sub-phase: ADR-015 (메모리 + Clarification) → ADR-010 v2 (D 단일화) → INDEX
- Acceptance: 2 ADR + INDEX 갱신

### 3.3 Phase E-1 — 메모리 인프라

📄 **[sprint15_phase_e1_memory_infrastructure.md](./sprint15_phase_e1_memory_infrastructure.md)** (~6h)

- 5 항목 정책 #1 — PostgreSQL CRUD 인프라
- 5 sub-phase: DB 마이그레이션 → Pydantic models → MemoryManager → API → UI
- Acceptance: 자동 테스트 254+ + 사용자 메모리 관리 UI 작동

### 3.4 Phase E-2 — 채팅 메모리 통합

📄 **[sprint15_phase_e2_chat_memory.md](./sprint15_phase_e2_chat_memory.md)** (~7h)

- 6 항목 정책 #2 / #3 / #4 / **#6 (신규 sidebar)** — 채팅 ↔ 메모리 통합
- 5 sub-phase: persist_turn (+ conversation_meta) → 채팅창 로드 → Cognitive cascade → 토큰 cap → **Conversation sidebar (E2-5 신규)**
- Acceptance: 자동 테스트 269+ + E2E 시나리오 (1차 turn → 2차 turn 컨텍스트 자동) + sidebar 작동

### 3.5 Phase E-3 — Clarification HITL ⭐

📄 **[sprint15_phase_e3_clarification.md](./sprint15_phase_e3_clarification.md)** (~4.5h)

- 5 항목 정책 #5 + CAP-001 — 양방향 의도 통신
- 6 sub-phase: schema 확장 → Validator → Cognitive 통합 → ws_hitl → 모달 → E2E (R-19~22)
- ⭐ **H0 자동 해결 메커니즘**: 같은 모호도 반복 시 메모리에서 자동 답
- Acceptance: 자동 테스트 271+ + R-20 (자동 해결) PASS

### 3.6 Phase E-4 — NL 2차 LLM Tool Routing

📄 **[sprint15_phase_e4_nl_v2.md](./sprint15_phase_e4_nl_v2.md)** (~6h)

- ADR-002 §2차 — 사용자 도메인 지식 가정 X
- 5 sub-phase: catalog grounding → plan_editor 확장 → NL 2차 prompt → ISSUE 회귀 → E2E (R-23~25)
- ISSUE-009 / 011 자연 해소
- Acceptance: 자동 테스트 279+ + 복잡 NL 시나리오

### 3.7 Phase E-5 — 자연 v? bump

(별도 문서 없음 — 누적 변경 정리)

- 작성 시점: Phase E-4 완료 후
- 작업: 변경된 spec / INDEX / ADR INDEX 일괄 점검
- 시간: ~30min

---

## 4. 검증 / 테스트 전략

### 4.1 자동 테스트 (Phase 별 누적)

| Phase 종료 시점 | 누적 passed |
|---------------|------------|
| Phase C 종료 | 244+ (group A~H + plan_adapter 5) |
| Phase E-1 종료 | 254+ (+ group I Memory 10) |
| Phase E-2 종료 | 269+ (+ persist_turn / utils 9 + conversation list 6) |
| Phase E-3 종료 | 277+ (+ group J Clarification 8) |
| Phase E-4 종료 | 285+ (+ catalog / plan_editor v2 8) |

### 4.2 브라우저 검증

각 phase 별 시나리오는 해당 세부 문서 §검증.

| Phase | 시나리오 |
|-------|---------|
| C | R-16/17/18 (NL 편집) |
| E-1 | 메모리 CRUD UI |
| E-2 | 채팅창 로드 + 컨텍스트 + **conversation sidebar (5개 + 새 채팅 + 삭제)** |
| E-3 | R-19/20/21/22 (Clarification + 자동 해결) |
| E-4 | R-23/24/25 (복잡 NL + Tool routing) |

### 4.3 E2E 통합 시나리오 (Vision 검증)

1. 사용자 첫 turn: `"블루밍글로우 네이버 리뷰 분석"` → clarification (필요 시) → 메모리 저장
2. 사용자 두 번째 turn: `"리뷰 분석"` → 메모리 자동 brand → clarification skip
3. = **H0 자동 해결 회귀 테스트**

---

## 5. 작업량 추정 (합산)

| Phase | 시간 | 누적 |
|-------|------|------|
| C Sprint 14 A3 종결 | 3h | 3h |
| D ADR 본문 | 3.5h | 6.5h |
| E-1 메모리 인프라 | 6h | 12.5h |
| E-2 채팅 메모리 (E2-5 sidebar 포함) | 7h | 19.5h |
| E-3 Clarification | 4.5h | 24h |
| E-4 NL 2차 | 6h | 30h |
| E-5 v bump | 0.5h | **30.5h** |

**총**: **~30~31시간 = 9~11 세션** (E2-5 Conversation sidebar 추가로 +3h).

---

## 6. Risk + 완화 (전체)

(각 phase 별 세부 risk 는 해당 세부 문서 §Risk 참조)

| 큰 그림 Risk | 완화 |
|---------|------|
| 어댑터 fix → Sprint 15 단일화 시 throwaway | 의도된 throwaway. ADR-010 명시 |
| 메모리 cascade DB 부하 | turn 단위 in-memory cache (Phase E-2 통합) |
| Clarification UX 결정 변경 | UX = 구현 중 결정 (사용자 의도 lock = "기존 todo 유지 + 부족분 요청") |
| LLM 토큰 비용 폭증 | 5 turn + 1500 cap + trim_to_token_budget |
| Clarification 무한 loop | max 2회 attempts |
| 메모리 schema 진화 (POC → MVP) | content JSONB + version 필드 |
| 사용자 ↔ 시스템 메모리 충돌 | source 라벨 우선순위 (explicit > implicit > extracted) |
| ISSUE-011 hallucination | catalog grounding (Phase E-4) |
| ISSUE-009 tool 미지정 SKIP | LLM Tool Routing (Phase E-4) |

---

## 7. 사용자 ↔ Claude 협업 지점

| Phase | 사용자 협조 |
|-------|---------|
| C-2 R-16/17/18 검증 | 브라우저 테스트 (~30분) |
| D 검토 | ADR-015 / ADR-010 v2 본문 검토 |
| E-1 | DB 마이그레이션 결과 확인 |
| E-2 검증 | 채팅창 로드 + 컨텍스트 작동 확인 |
| E-3 검증 | R-19~22 시나리오 직접 시도 (사용자 사례 4가지 — 의도 문서 §1.1) |
| E-3 UX 결정 | 모달 디자인 검토 (구현 중) |
| E-4 검증 | R-23~25 + 자유 대화 시도 |

---

## 8. Sprint 15 종결 시 Vision 진척

(의도 문서 §2 가설 H0~H4 매핑)

| 가설 | Sprint 15 진척 | 다음 |
|------|------|------|
| H0 의도 모호성 | ✅ **자동 해결 작동** (Phase E-3 + 메모리 cascade) | 운영 검증 |
| H1 발견 | ✅ NL 1차 ✅ + 2차 ✅ (Phase E-4) | NL 3차 = Sprint 18+ |
| H2 학습 데이터 누적 | ✅ 메모리 인프라 작동 (Phase E-1/2) | 패턴 추출 = Sprint 17 |
| H3 패턴화 | ⏳ Sprint 17+ | 메모리 누적 후 |
| H4 맞춤화 | ⏳ Sprint 18+ | MVP 이후 |

**Sprint 15 종결 = "자유 대화 양방향 통신 + 학습 인프라" 완성**.

---

## 9. 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-28 | 초안 — Phase C (Sprint 14 A3 종결) + Phase D (ADR 본문) + Phase E (Sprint 15 구현). 5 항목 정책 lock. ~27h / 8~10 세션 추정 |
| 2026-04-28 | **Overview 화** — 6 세부 문서 분리 + 본 문서는 overview/결정 lock/카탈로그. 세부 작업은 sprint15_phase_*.md 참조. Vision 진척 매핑 (H0~H4) 추가 |
| 2026-04-28 | **5 항목 → 6 항목** — Conversation list sidebar (#6) 신규 추가 (사용자 요구). Phase E-2 4 → 5 sub-phase, +3h, 27.5h → 30.5h. memory type 에 conversation_meta 추가 (Phase E-1). 좌측 sidebar / 최근 5개 / 새 채팅 / 삭제 정책 (turn 만, preference 보존) |
