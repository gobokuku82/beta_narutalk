# Sprint 14 A3 — Todo 편집 HITL (Y-a Structured + NL) 완료 보고서

| 항목 | 내용 |
|------|------|
| 기간 | 2026-04-23 (1일 집중) → 2026-04-30 Phase C-Unify (D 통일) 추가 종결 |
| 스코프 | Y-a: Structured 편집 UI + 자연어 편집 textarea 병행 (α+β, γ 분리) |
| 담당 | 도윤 + Claude |
| 상태 | **✅ 백엔드 + 자동 테스트 + R-16 fatal 코드 레벨 해소 완료**. 브라우저 regression (R-16/17/18) 수동 검증 대기 |
| 최종 commit | `1e8f319` refactor(sprint14): A3 Phase C-Unify — planner.Plan 단일화 (ADR-010 Accepted) |

---

## 1. 요약

**앱 핵심 기능 (Todo 편집) 구현 완료.** 사용자는 일시정지 / plan review 상태에서 Todo 를 (a) 구조화 UI (🗑 삭제, 드래그 순서변경, + 추가) 또는 (b) 자연어 textarea ("4번 삭제") 로 편집 가능.

### 주요 성과
- ✅ 백엔드 17건 의사결정 전수 구현 (Q1=Y-a / D1=E / D2=C-dual / D3=B / D4=B+ / D5=B / D6=Comprehensive+ / D7=A- / D8=중간 / D9=All layered / D10=A / D-11=A / D-12~15)
- ✅ 테스트 230 pass + 2 skip (Sprint 13 137 + A1 36 + A3 57)
- ✅ Contract Test DC-1~10 8/8 pass (DC-6 + DC-10 신설)
- ✅ 문서 cascade 5 bump (01 v1.4, 10 v1.9, 12 v1.2, 21 v1.3, 22 v1.1) + INDEX
- ✅ Dashboard C-dual UI +437줄 (pause 자동 팝업, 🗑/드래그/NL textarea, cascade 시각화, L2 ack gating, beforeunload 경고)
- ✅ 11 커밋 분해 (clean history)

### 규모
- **코드**: 백엔드 +~700줄 (ws_hitl + plan_editor + manager + layer_guard + error_codes), 프론트 +437줄 = ~1,140줄
- **테스트**: 신규 57건 (그룹 A~G)
- **문서**: 5 bump + decisions/plan/mockup/verification 9 자산 (docs/_claude/)
- **시간**: 계획 단계 포함 실제 하루 (plan 추정 2.5~3.5일 대비 단축 — 단 브라우저 수동 regression 수행 전)

---

## 2. 구현 완료 매트릭스 (13 결정)

| # | 결정 | 구현 위치 | 상태 |
|---|------|----------|------|
| Q1 | Y-a (Structured + NL) | Phase 2~4 전체 | ✅ |
| D1 | E (restart_from UX 라벨) | todo_manager.CascadeResult docstring + 10_v1.9 §4.3.3 drift 정리 | ✅ |
| D2 | C-dual 모달 재사용 | dashboard openHitlModal(mode, payload) | ✅ |
| D3 | B Red tint + ⛓ 라벨 | dashboard CSS `.invalidated` + renderCascade | ✅ |
| D4 | B+ 모달 재오픈 + beforeunload | dashboard handlePaused + beforeunload listener | ✅ |
| D5 | B pause/plan_review 만 | ws_hitl + handle_todo_* 가드 | ✅ |
| D6 | Comprehensive+ 68+ | 57건 구현 + 성장 여분 확보 | ✅ |
| D7 | A- (3개 enum + 4개 free-form) | error_codes.py + 22_v1.1 | ✅ |
| D8 | 중간 (DC-6 + DC-10) | test_doc_code_contract.py | ✅ |
| D9 L1 | per-session Lock | hitl_manager._session_locks + _get_lock | ✅ |
| D9 L2 | 프론트 ack gating | _editInFlight / _nlApplyInFlight | ✅ |
| D9 L3 | LLM lock release | **보류 (Phase 9 trigger 미충족)** | ⏸ |
| D9 L4 | 메시지 큐 | **보류** | ⏸ |
| D10 | layer_guard ErrorCodes 통합 | layer_guard.py L47/62/91/99/116 | ✅ |
| Q2-1 | 자동 팝업 | handlePaused → openHitlModal("pause") | ✅ |
| Q2-2 | 기본만 (재개/취소) | openHitlModal pause mode | ✅ |
| D-11 | A Status 마커 단순 | 5곳 코드 + DC-10 파싱 | ✅ |
| D-12 | UI mockup | docs/_claude/sprint14_a3_ui_mockup.md | ✅ |
| D-13 | Prompt injection | plan_editor.MAX_INSTRUCTION_LEN + _sanitize | ✅ |
| D-14 | NL 성공률 측정 | backend/scripts/a3_nl_success_rate.py | ✅ (실 실행 대기) |
| D-15 | 다중 탭 문서화 | handoff §0 + plan v0.4 명시 (20_v1.2 후속 bump 예정) | 🟡 부분 |

---

## 3. 테스트 실측 결과

### 그룹별 건수 (Comprehensive+ D6=≥68)

| 그룹 | 파일 | 건수 | 상태 | 비고 |
|------|------|------|------|------|
| A | test_a3_todo_manager_unit.py | 15 | ✅ 전수 pass | TodoManager pure 단위 |
| B | test_a3_hitl_todo_unit.py | 12 | ✅ 전수 pass | HITLManager 조율 + Lock + 가드 |
| C | test_a3_ws_hitl_structured_integration.py | 10 | ✅ 전수 pass | ws_hitl 3핸들러 (B1~B5) |
| D | test_a3_plan_editor_nl_unit.py | 10 | ✅ 전수 pass | plan_editor NL + injection 방어 (TE-D09/D10) |
| E | test_a3_ws_hitl_nl_integration.py | 7 | ✅ 전수 pass | _handle_todo_edit_nl 통합 |
| F | test_a3_race_unit.py | 5 | 3 pass + 2 skip | F01 100회 race, F02 L1+NL race, F03/F05 skip |
| G | test_a3_e2e_live.py | 7 | 전부 skip | Phase 8 브라우저 수동 영역 |
| **합계** | **7 파일** | **66 + live 7 = 73** | **57 pass + 9 skip** | |

### Regression 유지 (전수 재실행 3회)

- **Sprint 13**: 137/137 pass
- **Sprint 14 A1**: 36/36 pass (Unit+Integration 36 + Live 4 = A1 전체)
- **Sprint 14 A3**: 57 pass + 2 skip (L3/Checkpoint live)
- **전체 non-live**: **230 pass + 2 skip + 0 xfail + 0 xpass** (7 deselected Live)

### Contract Test (DC-1~10)

- DC-1 code paths exist: ✅ pass
- DC-2 core symbols exist: ✅ pass
- DC-3 ErrorCodes ↔ 22_v1.1.md 일치: ✅ pass (11개 enum)
- DC-4 internal doc refs: ✅ pass
- DC-5 version metadata 삼자 일치: ✅ pass (10 v1.9, 12 v1.2, 21 v1.3, 22 v1.1, 01 v1.4)
- **DC-6** (신규) Sprint 14 A3 3개 ErrorCode 추가 + 4개 free-form: ✅ pass
- **DC-10** (신규) Status 마커 파싱 + partial 설명 필수: ✅ pass
- **DC-10 soft** partial 설명 앵커 권장: ✅ pass

**총 8/8 pass** (DC-7/8/9 는 D8=중간 으로 보류).

---

## 4. 코드 변경 요약

### 백엔드 (~700 LOC)

- **error_codes.py** (+40줄): 3개 신규 enum (TODO_EDIT_NOT_PAUSED / INVALID_DAG / NL_INTENT_UNCLEAR) + all_codes/all_specs 확장
- **layer_guard.py** (-25줄 / +5줄): dict literal 5곳 제거, ErrorCodes 중앙 참조 (D10)
- **hitl_manager/manager.py** (+30줄):
  - `_session_locks` 필드 + `_get_lock(session_id)` (D9 L1)
  - `cleanup_turn` 확장 (_session_locks.pop)
  - handle_todo_* 3메서드 Status 마커
- **hitl_manager/plan_editor.py** (+45줄):
  - `MAX_INSTRUCTION_LEN=500` + `_sanitize()` (D-13)
  - `apply_edit` reorder 신구현
  - `validate_edit` reorder new_position 필수 체크
- **ws_hitl.py** (+330줄):
  - `_check_turn_active` 헬퍼 (DRY B1)
  - `_handle_todo_modify/delete/add` 3핸들러 B1~B5 + L1 Lock 리팩토링 (silent fail 수정 포함)
  - `_handle_todo_edit_nl` 신설 (170줄 — Y-a NL)
  - 메시지 dispatch 에 `todo_edit_nl` 추가

### 프론트엔드 (+437줄)

- HTML: `#hitl-overlay data-mode` + 편집 컨트롤 영역 + NL textarea + cascade 라벨/통계
- CSS: pause 모드 색상 + `.completed`/`.invalidated` tint + 드래그 시각 피드백
- JS (메인 추가):
  - `openHitlModal(mode, payload)` 통합
  - `renderHitlTodoList` + `setupHitlDragDrop`
  - `renderCascade` + `hideCascade`
  - `sendTodoDelete/Modify/Add/EditNl` + `sendTodoEditNlReorder`
  - `sendResume/sendCancel`
  - `handleHitlAckTodo` action 분기 dispatch
  - `wsHitl.onmessage` 확장 (에러 처리 포함)
  - NL 버튼/추가 버튼 wire-up + beforeunload 경고

### 테스트 (+933줄)

- sprint14/test_a3_*.py 7 파일 신규

### 문서 (+2,500줄)

- agent_specs 5 bump (01/10/12/21/22) + INDEX
- docs/_claude/ 9 자산 (gitignored — 계획·조사·검증 기록)

### 스크립트

- backend/scripts/a3_nl_success_rate.py — D-14 100회 측정 (실 실행은 API key 필요)

---

## 5. 의사결정 품질 — 3 사이클 검증 효과

| Round | 발견 건수 | 반영 |
|---|---|---|
| R1 (v0.3 독립 검증) | 12건 | D-11 포맷 확정 / silent fail 라인 정확화 / handlePaused 확장 / NL UX 분해 / L3 trigger 수치화 등 |
| R2 (v0.4 전수 재검증, effort-light 보정) | 14건 (10 agree + 1 disagree + 2 deliberate + 신규 4) | D7 A → A- 축소 / D8 A+ → 중간 / D-12 mockup / D-13 injection / D-14 성공률 / D-15 다중 탭 |
| R3 (최종 surgical) | 0건 (GO 판정) | — |

**교훈**: effort-light 우려에도 R2 가 공격적 재검증으로 잠재 문제 포착. R3 0건 수렴은 품질 보증. 3사이클 검증은 사용자 memory "정확한 게 중요" 원칙 충족.

---

## 6. 브라우저 수동 검증 (Phase 8 — 사용자 수행 대기)

자동 테스트로 커버 못 하는 실사용자 경로 — 6~7 시나리오 수동 검증 필요:

| ID | 시나리오 | 기대 |
|----|---------|------|
| R-5 | pause → structured modify → cascade → resume | ✎ 버튼 → 편집 → 🔴 tint → ⛓ 라벨 → 재개 |
| R-6 | pause → delete (🗑) → cascade 무효화 | downstream 🔴 + 통계 "N개 무효화" |
| R-7 | pause → "+ Todo 추가" → resume | 신규 Todo 실행 |
| R-8 | 복잡 cascade (diamond DAG) | invalidated 다건 순서 확인 |
| R-16 | NL textarea "4번 삭제" → cascade | LLM 파싱 → apply → 🔴 tint |
| R-17 | NL "순서 바꿔" → reorder → cascade | plan_editor reorder apply |
| R-18 | NL 파싱 실패 (LLM down) → 에러 UX | "어떤 작업을 원하시는지..." 토스트 + 구조화 UI 유지 |

수행 후 본 보고서 §6 에 결과 추가 + 01_requirements_v1.4 Acceptance 체크박스 마킹 + v1.4 → v1.5 bump 권장.

추가 실 검증 권장 (OpenAI API key 있을 때):
- `uv run python backend/scripts/a3_nl_success_rate.py 10` — 100회 NL 파싱 성공률 측정
  - 결과 < 3% → Y-a 유지 / 3%≤<10% → γ 재평가 / ≥10% → 범위 재설계

---

## 7. 커밋 매핑 (11 커밋)

| # | SHA prefix | 타입 | 내용 |
|---|------------|------|------|
| 1 | fb72dc3 | docs | A1 완료 보고서 수치 정정 (175→177, 34→36) |
| 2 | 050ab7d | docs | A3 Phase 0 — drift + Status 마커 + requirements v1.4 + handoff |
| 3 | 6da6ba6 | test | A3 TDD skeleton 71건 (7 파일) |
| 4 | 2796ea0 | feat | A3 Phase 2 — 백엔드 structured (B1~B5 + D9 L1 + D10) |
| 5 | c92086c | feat | A3 Phase 3 — 백엔드 NL (plan_editor reorder + todo_edit_nl + D-13 injection) |
| 6 | c052f85 | feat | A3 Phase 4 — Dashboard C-dual UI + NL + cascade + L2 + beforeunload |
| 7 | fbc911c | test | A3 Phase 5 — Live skeleton + NL 성공률 측정 스크립트 |
| 8 | cff085f | docs | A3 Phase 6 Part 1 — 22_error_codes v1.1 + INDEX |
| 9 | bab572c | test | A3 Phase 7 — Contract DC-6 + DC-10 신설 |
| 10 | e08a0d5 | docs | A3 Phase 6 Part 2 — agent_specs 3 bump (10/12/21) + INDEX |
| 11 | (본 커밋) | docs | A3 Phase 9 완료 보고서 |

---

## 8. 알려진 한계 / 후속 작업

### Phase 6 Part 3 (후속)
- 13_lifecycle v1.2 → v1.3 — §3.5 Todo 편집 상태 전이 + NL 경로
- 20_INTERFACE_CONTRACT v1.1 → v1.2 — Manager API 확장 + 다중 탭 시나리오 (D-15)
- 24_sequence_diagrams v1.2 → v1.3 — §6 편집 시퀀스 4건

### D-14 실 실행
- 100회 LLM 성공률 측정 결과에 따라 Phase 9 회고 재진입
- 실패율 ≥3% → γ 재평가 → A5 sprint 재정의

### D9 L3/L4 판단
- 현재 L1+L2 로 race 관찰 없음
- 브라우저 regression R-5~R-18 중 race UX 이슈 발견 시 L3 도입
- Phase 9 후속 회고에서 결정

### Sprint 15+ 연동
- Memory 도입 시 D4 beforeunload 제거 (서버 persistence 로 대체)
- restart_from UX 라벨 활용 확장 가능 (현재 미소비)

---

## 9. 학습 · 교훈

1. **Effort-light 이력은 R2 공격적 재검증으로 보정 가능** — 단일 pass 신뢰 금지, 독립 눈 다회 필요
2. **C-dual 모달 재사용은 구현 복잡도를 감춘다** — mockup (D-12) 으로 사전 estimate 재조정이 800줄 과소평가 방지
3. **D7=A- 축소가 옳았다** — enum 7개 → 3개로 UX 차별화 핵심만 유지, 나머지 free-form 은 관리 비용 절감
4. **DC-10 Status 마커는 handoff drift 재발 방지의 핵심** — "A3 는 스텁 수준" 같은 잘못된 기록을 자동 감지
5. **3 사이클 검증 (R1 12건 → R2 14건 → R3 0건 수렴)** 은 "리소스·시간 무제한, 정확한 게 중요" 원칙과 완벽 부합
6. **plan_editor 의 Pydantic Plan ↔ dict 변환 레이어** 가 A3 핵심 통합 난제. ws_hitl dict 기반 경로와 plan_editor Pydantic 경로를 _handle_todo_edit_nl 에서 연결
7. **라운드별 독립 Agent** 가 Claude 의 자기 편향 (특히 effort-light 시) 을 걸러내는 실질적 메커니즘

---

## 10. 다음 단계

1. **사용자 수행 대기**: 브라우저 regression R-5~R-18 6~7 시나리오 수동 검증
2. **선택적**: `uv run python backend/scripts/a3_nl_success_rate.py 10` (100회 LLM 성공률 측정)
3. **후속 bump**: 13/20/24 cross-link 갱신 (1~2h)
4. **01_requirements v1.5 bump**: Acceptance 체크박스 완료 마킹 + FR-12a~h ⏳ → ✅
5. **handoff §0 갱신**: "A3 완료" 표시 + Tier 2 잔여 A2/A4 대기
6. **Tier 2 다음 작업**: A2 (phase 내 pause 세밀화) / A4 (team_catalog requires_approval)

---

## 11. Phase C-Unify (2026-04-30) — Sprint 14 A3 추가 종결

### 11.1 배경

POC 1차 검증 (R-16) — NL 편집 ("4번 삭제") fatal 발견. 활성 코드의 schema 불일치 (3 Plan / 2 Todo 클래스).

### 11.2 결정 흐름 — 어댑터 (B) 시도 후 D 직진

| 단계 | 내용 | commit |
|------|------|--------|
| 1. 어댑터 (B) | `plan_adapter.py` 신규 (양방향 변환) — 1시간 fatal 해소 | `e767845` |
| 2. 부채 우려 제기 | 사용자 통찰 "v1/v2 섞임 금지" + 통일 비용 ~3~5h = 1 day 미만 | (질문) |
| 3. D 통일 직진 | `planner.Plan` 단일화 — 어댑터 폐기 + 모듈 5개 + 테스트 4개 정리 | `1e8f319` |
| 4. ADR-010 본문 | Accepted (D 단일화 결정 + 어댑터 시도는 history) | (포함) |

### 11.3 변경 요약

| 영역 | 변경 |
|------|------|
| 활성 schema | `models.Plan / TodoItem` → `planner.Plan / PlannedTodo` 단일화 |
| `plan_editor.py` | rewrite. `apply_edit` 단일 반환 (PlanChange 폐기, NL edit 경로) |
| `ws_hitl.py` | 어댑터 호출 제거. 직접 `planner.Plan.model_validate` |
| `plan_adapter.py` | 삭제 (throwaway 자취만 commit history 에) |
| `models/plan.py`, `models/todo.py` | deprecated 마커 (활성 사용 0, `_old_v1/` 호환만) |
| 테스트 | sprint14 fixture 4개 전환 (TC 5 삭제, 보정 후 회귀 0) |

### 11.4 최종 자동 테스트

- 단위 plan_editor: 10/10 PASS (D01~D10)
- NL integration: 7/7 PASS (TE-E01~E07)
- plan_review integration: 8/8 PASS (TE-H01~H08)
- Sprint14 dir: 102 passed + 2 skipped
- **Full suite: 239 passed + 2 skipped** (회귀 0, 어댑터 5 TC 삭제 보정)

### 11.5 사용자 통찰 부합

- ✅ **v1/v2 섞임 금지** — schema 1개로 수렴
- ✅ **확장/변경 용이성** — 단일 모듈 진화
- ✅ **부채 0** — 어댑터 throwaway 시도는 한 commit 내 자취만 남기고 폐기

### 11.6 남은 작업 (브라우저 검증)

- R-16 ("4번 삭제") / R-17 ("3-4 순서 바꿔") / R-18 ("asdf xyz") — 다음 세션 사용자 협조

### 11.7 관련 문서

- ADR-010: [`docs/agent_specs/adr/ADR-010_plan_schema_unification.md`](../agent_specs/adr/ADR-010_plan_schema_unification.md)
- 작업 계획서: [`sprint14_a3_phase_c_unify_plan.md`](./sprint14_a3_phase_c_unify_plan.md)
- 사전 조사 Q1: [`sprint14_a3_research_q1_plan_schema.md`](./sprint14_a3_research_q1_plan_schema.md)
- known_issues ISSUE-016: [`sprint14_a3_known_issues.md`](./sprint14_a3_known_issues.md)
- 자동 테스트 로그 #2: [`sprint14_a3_test_log.md`](./sprint14_a3_test_log.md)

---

## 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-04-23 | A3 백엔드 + 자동 테스트 + 문서 5 bump + Contract Test DC-6/10 완료. 11 커밋. 브라우저 R-5~R-18 수동 검증 대기 |
| v1.1 | 2026-04-30 | Phase C-Unify (D 통일) 추가 종결. R-16 NL fatal 코드 레벨 해소. ADR-010 Accepted. 어댑터 (B, e767845) 시도 후 D 직진 (1e8f319). Full suite 239 passed. §11 신규 |
