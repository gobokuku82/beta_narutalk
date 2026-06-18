# Sprint 14 A3 — POC 1차 결산 문서 (초안)

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-04-27 |
| 작성자 | Claude (사용자 검토 대기) |
| 마지막 커밋 | `d6cd6b8` (compact 직전 종합 점검) + 본 세션 R-8/R-16 검증 (커밋 미반영) |
| 검증 범위 | R-1~R-8 (구조화 편집 + 회귀) + R-16 (NL 삭제 fatal) |
| 본 문서 위치 | `docs/reports/sprint14_a3_poc1_settlement.md` |
| 자매 문서 | `sprint14_a3_poc1_deliverables.md` (산출물 정의 계획서, 작성 예정) |

---

## 0. 본 문서의 역할

**과거 시점 정리** — POC 1차에서 무엇이 됐고, 무엇이 안 됐고, 왜 그런지를 객관적 사실 위주로 정리.

**이 문서가 다루지 않는 것**:
- 미래 계획 / Sprint 14.5/15 구체 계획 → `sprint14_a3_poc1_deliverables.md`
- 코드 변경 작업 / ADR 본문 작성 → 위 문서 결정 후
- 의견·해석 (필요 시 명시 표기 — "**해석:**" 으로 분리)

본 문서는 산출물 계획서의 **사실적 토대**.

---

## 1. 검증 결과 매트릭스

### 1.1 회귀 (R-1 ~ R-4)

| ID | 시나리오 | 결과 | 비고 |
|----|---------|------|------|
| R-1 | 쿼리 → hitl → 승인 → 출력 | ✅ PASS | 정상 |
| R-2 | 쿼리 → hitl → 거부 → 중단 | ✅ PASS | 정상 |
| R-3 | 쿼리 → pause → 모달 → 중단/재개 | ✅ PASS | 정상 |
| R-4 | 연속 pause/resume 반복 | ✅ PASS | 정상 |

### 1.2 Phase 5 핵심 (R-5 ~ R-8)

| ID | 시나리오 | 결과 | 핵심 발견 |
|----|---------|------|---------|
| R-5 | Plan review 편집 (🗑) → 승인 | ✅ 핵심 PASS | ISSUE-001 발견 후 fix |
| R-6 | Cascade 무효화 시각화 (downstream 3+) | ✅ PASS | ISSUE-005 / 006 발견 후 fix / Level A 해결 |
| R-7 | Todo 추가 (➕) | ✅ PASS (재재재검증) | ISSUE-007 / 008 / 009 발견 |
| R-8 | Diamond DAG cascade | 🟡 부분 PASS | 백엔드 ✅ / UI ❌ (ISSUE-014) |

### 1.3 NL 편집 (R-16 ~ R-18)

| ID | 시나리오 | 결과 | 핵심 발견 |
|----|---------|------|---------|
| R-16 | NL 삭제 ("4번 삭제") | ❌ **FATAL** | **ISSUE-016** Plan dict ↔ Pydantic schema 불일치 |
| R-17 | NL 순서 변경 | ⏳ 미진행 | R-16 fatal 로 동일 경로 차단 |
| R-18 | NL 파싱 실패 UX | ⏳ 미진행 | 동일 |

**해석**: R-16/17/18 모두 `_handle_todo_edit_nl` 의 `Plan.model_validate(progress.plan)` 변환 지점에서 차단. 동일 fix 로 3 시나리오 모두 풀림.

### 1.4 자동 테스트 상태

- Group A~H **239 passed + 2 skipped** (변경 후 유지)
- DC-5 통과, DC-4 잔여 10건 (모두 pre-existing 구버전 archived)

### 1.5 End-to-end 성공 케이스

| 시점 | 쿼리 | 결과 |
|------|------|------|
| R-8 첫 시도 | `"리뷰 수집한 후 ..."` | ❌ EXECUTION_ALL_FAILED (`KeyError: 'brand'`) |
| R-8 재시도 | `"블루밍글로우 네이버 리뷰 ..."` | ✅ end-to-end 성공 (`phases=7 todos=8 attachments=1`) |
| R-6 통합 시도 | brand 명시 + 중간 todo 삭제 | ✅ 7 todos 정상 실행 + PDF |

→ **brand 명시 시 cognitive→planning→execution→response 전 layer 통과 확인** (POC 1차 첫 end-to-end 성공).

---

## 2. 발견 ISSUE 매트릭스 (16 항목)

### 2.1 정식 등록 (known_issues.md, 9건)

| # | 증상 | 발견시점 | 상태 | 처리 |
|---|------|--------|------|------|
| 001 | UI stale (메인 카드) | R-5 | ✅ 해결 | `9126315` — 사용자 인사이트 옵션 D (renderTodoList 1줄) |
| 002 | Cognitive LLM enum validation 실패 | R-5 사전 | 🟡 보류 | NL 2차 또는 ADR-009 묶음 |
| 003 | Memory drift (eager → lazy) | walkthrough | ✅ 해결 | 메모리 정정 |
| 004 | 모달 헤더 메시지 stale | R-6 | 🟡 보류 | 마무리 시점 일괄 |
| 005 | handle_todo_delete restart_from 누락 | R-6 | ✅ 해결 | `05045a1` — 1줄 fix |
| 006 | 도메인 의미적 검증 부재 | R-6 | 🟡 Level A 해결 | confirm 메시지 강화 / B/C 후속 |
| 007 | handleHitlAckTodo todo_add 미갱신 | R-7 | ✅ 해결 | `4dfa84d` — 책임 분리 |
| 008 | add_todo task_type 누락 → fatal | R-7 재검 | ✅ 해결 | `d3b5776` — setdefault 1줄 |
| 009 | tool 미지정 todo execution skip | R-7 재재재검 | 🟡 보류 | NL 2차 LLM Tool Routing 본질 해결 |

### 2.2 본 세션 신규 발견 (7건, 정식 등록 대기)

| # | 증상 | 발견시점 | 상태 | 본질 |
|---|------|--------|------|------|
| **010** | `plan_editor.modify` 가 `tool_params` 미지원 (`task/tool/priority` 만) | R-8 brand 추가 시도 | 🆕 미등록 | schema 충돌 — TodoItem vs 사용자 의도 |
| **011** | `pdf_renderer` hallucination (catalog 부재) | R-8 plan 분석 | 🆕 미등록 | LLM grounding 부재 |
| **012** | Cognitive 출력에 parallelism 정보 없음 (planning stage3 가 implicit grouping 으로 부분 보완) | R-8 plan 구조 분석 | 🆕 미등록 | Cognitive 출력 schema 빈약 |
| **013** | `HITL request not found` warning + ack `accepted=false` (동작은 정상) | R-8 / R-6 통합 | 🆕 미등록 | progress 기반 처리 일관성 |
| **014** | Plan review UI list-only — DAG 시각화 0 | R-8 | 🆕 미등록 | UI 표현력 한계 |
| **015** | modify approve 시 planning 3-stage 전체 재실행 (3 LLM 호출) | R-8/R-6 통합 로그 | 🆕 미등록 | LLM 호출 효율 결함 |
| **016** | NL path 가 또 다른 Plan model 기대 (`session_id`, `task` 필수) | R-16 | 🆕 **fatal**, 미등록 | **3개 Plan 클래스 공존** |

### 2.3 신규 — 누락 Capability (사용자 요구사항 추가, 2026-04-28)

ISSUE 와 다른 카테고리: **버그가 아니라 시스템 자체에 부재한 기능**.

| # | 항목 | 본질 | 의존성 | 처리 시점 |
|---|------|------|------|---------|
| **CAP-001** | Clarification HITL trigger 부재 — 쿼리 모호성 / 필수 정보 누락 시 사용자에게 보완 요청 못 함 | Cognitive 가 ambiguity 감지 시 interrupt 메커니즘 X. 신규 HITL 트리거 type 필요 | **메모리 시스템** (사용자 brand 선호·default·최근 컨텍스트 활용) — Sprint 15+ FR-14 의존 | Sprint 15 (POC 2차) — 메모리 ADR 과 함께 |

**사용자 사례 (2026-04-28)**:
- "리뷰를 찾아줘" — brand + channel + 기간 모두 누락
- "네이버에서 리뷰를 찾아줘" — brand 누락
- "블루밍글로우 리뷰 찾아줘" — channel default 가능 여부 confirm 필요
- "아모레 글로우 네이버 리뷰 찾아줘" — entity ambiguity (1개 brand vs 2개)

**3가지 모호도 유형**:
- (a) Missing required field — 명백히 비어있음
- (b) Default 가능 — 시스템이 default 줘도 OK 인지 confirm
- (c) Entity ambiguity — 토큰 분리 자체가 모호 (LLM 재해석 + 다중 후보)

**핵심 통찰** (사용자, 2026-04-28):
> "이건 메모리 설계와 같이 가는 파트. 메모리 구현도 하면서 고려해야 할 사항"

→ Clarification 단발 fix 아님. 메모리 + clarification = **묶음 설계**. 별도로 만들면 메모리 도입 시 재설계 (부채).

---

## 3. 도메인별 분류 (4축)

### 3.1 UX 차원

| ISSUE | 본질 |
|------|------|
| 001 ✅ | 모달 ↔ 메인 카드 동기화 |
| 004 🟡 | 부분 갱신 누락 (헤더) |
| 006 🟡 | 도메인 지식 안내 부재 (Level A 해결) |
| 014 🆕 | DAG 시각화 부재 — 사용자가 시스템 구조를 못 봄 |

**공통 패턴**: **표시 영역 일관성 + 시스템 구조의 가시성**.

### 3.2 User Flow 차원

| Flow | 결과 | 본질 |
|------|------|------|
| 🗑 직접 삭제 | ✅ 작동 | dict 직접 조작 OK |
| ➕ Todo 추가 | 🟡 작동하나 SKIP (009) | 사용자가 tool catalog 알아야 함 |
| 🗣 NL 편집 | ❌ fatal (016) | schema 불일치로 통째로 차단 |
| 새 쿼리 정공법 | ✅ 작동 | LLM 매개 의도 해석 |

**공통 패턴**: **직접 편집 = 사용자 부담 / NL = 차단됨 → POC 1차 핵심 가치 미달성**.

### 3.3 System 차원

| ISSUE | 위치 | 본질 |
|------|------|------|
| 008 ✅ | todo_manager.add_todo | TodoItem vs PlannedTodo schema 충돌 |
| 010 🆕 | plan_editor.modify | tool_params 편집 미지원 |
| 011 🆕 | LLM stage3 출력 | catalog grounding 부재 |
| 012 🆕 | Cognitive output schema | parallelism 표현 X |
| 013 🆕 | ws_hitl response | progress ↔ pending_request 이중 처리 |
| 015 🆕 | planning_stage modify | LLM 재호출 비효율 |
| 016 🆕 | ws_hitl._handle_todo_edit_nl L507 | **3 Plan 클래스 공존** |

**공통 패턴**: **모델 다중·스키마 충돌·LLM 호출 비효율 — 시스템 응집성 결함**.

### 3.4 Domain 차원 (메모리 박제됨)

> "사용자가 시스템 도메인 지식 (DAG / schema / tool catalog) 가져야만 직접 편집이 안전 — 비현실적"

[`project_no_user_domain_assumption.md`](C:/Users/gobok/.claude/projects/c--kdy-Projects-octormate-beta-v001/memory/project_no_user_domain_assumption.md) 박제 완료.

**해당 ISSUE**: 006 / 008 / 009 / 010 / 011 / 014 / 016 — 모두 같은 근본.

---

## 4. 본질 패턴 4가지

POC 1차 검증으로 측정된 **시스템·UX·사용자 간 마찰의 4가지 패턴**.

### 4.1 패턴 A — 의도 흐름 부재 (Intent Flow Gap, 양방향)

**정의 (2026-04-28 갱신)**: 시스템 ↔ 사용자 사이의 의도 흐름이 양방향 모두 결함.

#### 4.1.a 시스템 → 사용자 방향 — 도메인 지식 강요

사용자가 시스템 내부 schema/DAG/catalog 를 알아야만 안전한 작업이 가능한 상태.

**해당 ISSUE**: 006, 008, 009, 010, 011, 014, 016

**대표 사례**:
- ISSUE-006: format_normalizer 삭제 시 downstream 빈 입력 (DAG 의존성 모름)
- ISSUE-009: ➕ Todo 추가 시 tool 미지정 → SKIP (catalog 모름)
- ISSUE-016: NL 편집이 task vs task_type 필드 불일치로 fatal (schema 모름 — 시스템 내부 문제)

#### 4.1.b 시스템 ← 사용자 방향 — 의도 확인 부재

시스템이 모호 / 부족한 사용자 의도를 **되묻지 못함**. 가정으로 진행 → fail or 잘못된 결과.

**해당 항목**: CAP-001 (Clarification HITL trigger 부재)

**대표 사례** (2026-04-28):
- "리뷰를 찾아줘" → cognitive 가 brand=None 으로 진행 → naver_collector KeyError fatal (실제 R-8 첫 시도에서 발생)
- "아모레 글로우" → entity 다중 해석 가능 → 시스템이 추측, 사용자 의도 확인 없음

#### 본질 (양방향 통합)

**시스템 ↔ 사용자 의도 통신 부재**. 한쪽은 사용자가 시스템 내부를 알아야 하고, 다른 한쪽은 시스템이 사용자에게 묻지 못함. **LLM 매개 + 메모리 기반 양방향 의도 흐름** 이 본질 해결.

**상태**:
- 4.1.a → 메모리 박제됨, ADR-002 NL 2/3차 진입 정당성
- 4.1.b → CAP-001, 메모리 ADR + ADR-015 (HITL 트리거 정책) 통합 설계 (Sprint 15)

### 4.2 패턴 B — Schema 충돌 (Schema Coexistence)

**정의**: 같은 개념 (Plan / Todo) 에 대해 여러 Pydantic 모델이 공존하며 단계별 변환 누락 시 fatal.

**해당 코드** (3 Plan 클래스):
1. `backend/app/dream_agent/models/plan.py::Plan` — `session_id`, `todos: list[TodoItem]` (TodoItem 은 `task` 필수)
2. `backend/app/dream_agent/planning/planner.py::Plan` — `teams_selected`, `todos: list[PlannedTodo]` (PlannedTodo 는 `task_type` 필수, `task` 없음)
3. (추가) `backend/app/dream_agent/models/todo.py::TodoItem` — Sprint 12 형식

**해당 ISSUE**: 008 (✅), 010 (🆕), 016 (🆕 fatal)

**현재 dict ↔ Pydantic 변환 지점**:
- ✅ 작동: TodoManager (line 97 `dag = plan.get("dag", plan.get("dependency_graph", {}))` — 두 필드명 fallback)
- ❌ 차단: `_handle_todo_edit_nl` L507 `Plan.model_validate(progress.plan)` — fallback 없음

**본질**: schema 단일화 또는 명시적 어댑터 layer.

**상태**: ADR-010 후보 — 본 결산 후 정식 결정.

### 4.3 패턴 C — UI 표현력 한계 (UI Representation Gap)

**정의**: 백엔드가 정상 처리한 구조 (DAG 병렬 / phase grouping) 가 UI 에서 표현 안 됨.

**대표**: ISSUE-014 — `phases=7 / todos=8` 인 Plan 도 UI 는 list 1~8 로만 표시. Diamond 분기 / 병렬 그룹 / cascade 영향 화살표 등 표현 0.

**부수 효과**: 패턴 A 강화 — 사용자가 DAG 모름 → 안전한 편집 불가 → 패턴 A 의 표면 원인 일부.

**본질**: dagre/mermaid 같은 DAG 시각화 도입 또는 phase grouping 의 indent/box 표현.

**상태**: ADR-011 후보.

### 4.4 패턴 D — LLM 호출 비효율 (LLM Cost Pattern)

**정의**: 시스템 비효율로 LLM 이 불필요하게 여러 번 호출됨.

**대표**:
- ISSUE-015: modify approve 시 planning 3-stage 재실행 (~10초 + 3 token cost)
- ISSUE-002: cognitive LLM enum 실패 시 재시도 안 됨 (사용자 정공법 = 새 쿼리)
- (참조) ADR-009 후보: LLM client timeout 무한 대기 가능

**본질**: LLM 호출 정책 (timeout / retry / cache / 분기 skip 조건) 통합 결정.

**상태**: ADR-009 (timeout) + 신규 LLM 효율 ADR 후보.

---

## 5. ADR 매핑

### 5.1 작성 완료 (5건)

| ADR | 제목 | Sprint 14 A3 와의 관계 |
|-----|------|---------------------|
| 000 | ADR 도입 자체 | 메타 |
| 001 | hitl/pause 통합 | Phase 5 핵심 결정 |
| 002 | NL 편집 1·2·3차 + R-7 보강 | 본 결산의 패턴 A 직결 |
| 005 | Sprint 12 legacy `_run_agent` 정책 | Phase 5 정리 |
| 007 | session_id ↔ turn_id 네이밍 | Phase 5 fix 결과 |

### 5.2 본 결산이 식별한 ADR 후보 (10건)

| 후보 | 본질 패턴 | 우선순위 | 의존 ISSUE |
|------|---------|---------|---------|
| **003** Manager 5 책임 분리 | C (구조) | 중 | (전체 코드 명료화) |
| **004** WebSocket 2채널 분리 이유 | C (구조) | 중 | — |
| **006** Walkthrough-First 패턴 | 메타 | 중 | — |
| **008** Error 처리 통일 + ws_hitl error 코드 분리 | C (구조) | 중 | sprint14_post_a3_cleanup_plan 작성됨 |
| **009** LLM client timeout | D (비용) | 높 | 002 |
| **010** Plan/Todo schema 통합 | B (schema) | **최고 (R-16 fatal)** | 008, 010, 016 |
| **011** UI DAG 시각화 정책 | C (UI) | 중 | 014 |
| **012** Cognitive 출력 schema 강화 | A (도메인) | 중 | 012 |
| **013** ws_hitl ack 일관성 (progress 기반) | C (구조) | 낮 | 013 |
| **014** LLM tool catalog grounding | A/D | 중 | 011 |
| **015** **메모리 기반 양방향 의도 통신 architecture** (메모리 + HITL 트리거 + clarification 통합) | A 양방향 | **최고 (Sprint 15 P0)** | CAP-001, FR-14, ADR-002 NL 2차 |

### 5.3 ADR-010 의 위치 (가장 큰 부채)

**범위**: 3 Plan 클래스 + 2 Todo 클래스 통합/명시.

**옵션** (본 결산 단계에선 비교만, 결정은 산출물 계획서 + 별도 ADR-010 본문):

| Option | 내용 | 장점 | 단점 |
|--------|------|------|------|
| A. 단일 Plan 모델 | `models/plan.py` 만 유지, planner.Plan 폐기 | 가장 깔끔 | 큰 마이그레이션 |
| B. 어댑터 layer | dict ↔ 두 모델 변환 함수 명시 | 점진 가능 | 변환 부담 영구 |
| C. 단계적 마이그레이션 | A 를 단계별 (planner → executor → ws_hitl 순) | 위험 분산 | 일정 길어짐 |

각 옵션의 trade-off, migration cost, backwards-compat 정책은 **ADR-010 본문에서 결정**.

---

## 6. 사용자 5항목 요구사항 진척

| 요구사항 | 구현 | 검증 | 상태 |
|---------|------|------|------|
| §1 ws_agent + ws_hitl 2채널, pause=hitl=interrupt | ✅ | ✅ R-5 PASS | ✅ 완료 |
| §2 hitl_manager 가 hitl/pause 관리 | ✅ Phase 5 임시 progress | ✅ R-5/6/7 PASS | ✅ 완료 |
| §3 todo_manager 가 todo 관리 명확 | 🟡 모델 충돌 (ISSUE-008/010/016) | 🟡 ADR-010 의존 | 🟡 schema 통합 후 완전 |
| §4 hitl=pause 같은 개념, NL 가능, 단순 작업 간단, UI 완벽 | 🟡 NL 1차 fatal (016) | ❌ R-16 차단 | ❌ 본질 fix 필요 |
| §5 gap 작음, 타이밍·구조·연결 | ✅ Phase 5 통합 + R-7 fix | ✅ | ✅ 완료 |

**핵심**:
- §1 / §2 / §5 = 완료 (Phase 5 핵심 산출물)
- §3 = schema 충돌로 부분 완성 (ADR-010 후 완료)
- §4 = NL fatal 로 미완성 (ADR-010 fix 후 R-16/17/18 검증 가능)

§4 의 "단순 작업 간단" 의 한계가 R-5~R-7 검증으로 명확히 측정됨 (패턴 A 박제).

### 6.1 신규 사용자 요구사항 (2026-04-28, POC 1차 범위 외)

§4 의 "NL 가능" 을 양방향으로 확장 — Clarification HITL 추가 (CAP-001).

| 신규 요구 | 본질 | 처리 시점 |
|---------|------|---------|
| 쿼리 모호성 시 시스템이 사용자에게 보완 요청 | §4 의 양방향 확장 | Sprint 15 (메모리 + clarification 묶음) |

→ POC 1차 범위 외. 메모리 시스템 구현과 동시 설계 필요.

---

## 7. POC 1차의 진짜 산출물

기존 정의: "Plan 편집 기능 작동" — 부분 미충족 (NL fatal)

**재정의**: **"한계 측정 + NL 2차 진입 trigger 식별 + 시스템 응집성 부채 가시화"**

이 재정의에 따르면 POC 1차는 ✅ **완료**.

### 7.0 Minimum Viable Completion (사용자 결정, 2026-04-28)

순수 "한계 측정" 으로 끝내면 NL fatal 이 부정적 출발점. **NL fix 만 추가** 해서 "기능 작동 + 한계 측정" 으로 마무리.

**범위**:
- ADR-010 작은 결정 (어댑터 vs 단일화 선택만)
- `_handle_todo_edit_nl` 의 plan dict ↔ Pydantic 변환 어댑터 작성
- R-16/17/18 검증 PASS

**범위 외**:
- 다른 ISSUE (002/004/011/013/015) — Sprint 15 ADR 묶음
- 메모리 / clarification — Sprint 15 본격
- 7-domain v2.0 rewrite — **불필요** (점진 update 안 채택)

### 7.1 측정된 한계 3가지

1. **단순 작업의 경계** (사용자 §4) — 마지막 todo 삭제 / 단순 NL 만 안전. 중간 todo 삭제·NL 다단계 = 위험
2. **사용자 도메인 지식 가정의 비현실성** — 8 tool 도 어려움, 10~20 tool 비현실
3. **schema 다중·LLM 비용 부채** — 시스템 응집성 부채로 치환 가능

### 7.2 식별된 trigger

- ADR-002 NL 2차 진입 정당성 — 본 결산으로 입증
- ADR-010 schema 통합 정당성 — R-16 fatal 로 즉시성 강화
- ADR-011 UI DAG 시각화 — ISSUE-014 발견

### 7.3 가시화된 부채

3개 Plan 클래스 + 다중 LLM 비효율 + UI 표현력 한계 — 본 결산 §3.3 / §4.2 / §4.3 / §4.4 에 정리.

---

## 8. Sprint 진입 — Feature-driven Iterative (사용자 결정, 2026-04-28)

**큰 결정 (2026-04-28)**: 7-domain v2.0 rewrite 안 채택. **점진 업데이트 + 구현 동행** 채택.

### 8.1 채택된 흐름

```
[Step 0]  결산 문서 갱신 ✅ (본 문서)
            ↓
[Step 1]  ADR-010 작은 결정 (어댑터 vs 단일화)
            ↓
[Step 2]  NL fix (R-16/17/18 작동) + 관련 spec 점진 update
           (12_manager / 21_websocket / 22_error_codes minor bump)
            ↓
[Step 3]  **ADR-015** 메모리 + HITL 트리거 + clarification 통합 architecture (큰 결정)
            ↓
[Step 4]  메모리 + Clarification HITL 구현 + spec 점진 update
           (10_system / 30_data_models 갱신, StructuredQuery 확장,
            신규 message type, 신규 메모리 spec, 모달 추가)
            ↓
[Step 5]  NL 2차 (LLM Tool Routing) — ADR-002 §2차 진입
            ↓
[Step 6]  자연 v? bump (변경 누적 결과)
```

**원칙**:
- 각 Step 끝에 **변경된 spec 만 minor bump**. 안 변한 건 그대로
- v2.0 같은 통째로 rewrite 없음
- ADR 은 **결정 박제** 용 — 1 ADR ≈ 1 페이지 (가벼움)

### 8.2 폐기된 옵션

| 옵션 | 폐기 이유 |
|------|---------|
| 7-domain v2.0 rewrite | oversprint, 코드 ↔ 문서 drift 위험, POC 단계 부적합 |
| Sprint 14.5 신설 | 14.5 vs 15 경계 모호. 단일 "Sprint 15 = POC 2차" 로 통합 |
| 사실만 정리 후 종결 | NL fatal 미해소 = 부정적 출발점. Step 2 로 minimum viable completion |

### 8.3 Sprint 명명 (단순화)

- **Sprint 14 A3** = 종결 (본 결산 + Step 1~2 NL fix 까지)
- **Sprint 15 = POC 2차** = Step 3~7 (메모리 + HITL + clarification + NL 2차 + 점진 spec update)

### 8.4 산출물 계획서가 다룰 Q (축소)

- **Q1** ADR-010 옵션 (A 단일화 / B 어댑터) — Step 1
- **Q2** Step 2 의 spec 점진 update 범위 (12 / 21 / 22 어떻게?)
- **Q3** ADR-015 (메모리 + HITL 트리거 + clarification 통합) — Step 3 architecture 큰 그림
- **Q4** Clarification UX (모달 / 채팅 inline / Plan review 통합) 중 선택
- **Q5** ISSUE-002 / 004 / 011 / 013 / 015 처리 시점 — 어느 Step 묶음?
- **Q6** Legacy 백업 정책 — minor bump 만 하면 거의 불필요. 단일 파일이라도 major schema 변경 시 `_legacy/` 도입 여부

이전의 Q1~Q7 보다 좁아짐 — 채택된 흐름이 많은 결정을 이미 답함.

### 8.5 § 9 결정 lock (2026-04-28 사용자 답)

- **A/B/C/D/E/F/G** 모두 동의
- **H** 동의 + **ADR-015/016 통합** — 단일 ADR-015 "메모리 기반 양방향 의도 통신 architecture"

---

## 9. 결정 대기 항목 (산출물 계획서 입력)

본 결산을 사용자가 검토 후, **사실 정확성 + 갱신된 전략 동의 여부** 확인:

| # | 검토 포인트 | 동의 여부 |
|---|----------|---------|
| 1 | 검증 결과 매트릭스 (§1) | 사실 정확? 빠진 시나리오? |
| 2 | ISSUE 16건 + CAP-001 (§2) | 신규 7건 + 1 capability 등록 동의? |
| 3 | 4축 분류 + 패턴 A 양방향 (§3, §4.1) | 시스템 ↔ 사용자 양방향 통찰 동의? |
| 4 | 본질 패턴 4가지 (§4) | 더 있나? 빠진 건? |
| 5 | ADR 후보 12건 (§5.2 — 015/016 추가됨) | 우선순위 동의? 메모리 + HITL 묶음 동의? |
| 6 | POC 1차 = "Minimum Viable Completion" (§7.0) | NL fix 만 추가 후 종결 동의? |
| 7 | Feature-driven Iterative 채택 (§8) | 7-domain v2.0 rewrite 폐기 + 점진 update 동의? |
| 8 | Sprint 14 A3 종결 + Sprint 15 = POC 2차 (§8.3) | Sprint 명명 동의? |

검토 통과 후 → **`sprint14_a3_poc1_deliverables.md` 작성** (Phase A-3, Q1~Q6 결정).

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-27 | 초안 — Sprint 14 A3 + 본 세션 R-8/R-16 결과 통합. ISSUE 16건 (정식 9 + 신규 7) 분류. 4축 분류 + 본질 패턴 4가지. ADR 후보 10건 식별. POC 1차 산출물 재정의 |
| 2026-04-28 | §2.3 신규 Capability (CAP-001 Clarification HITL — 메모리 의존). §4.1 패턴 A 양방향 확장 (시스템→사용자 + 시스템←사용자). §5.2 ADR 후보 015/016 추가 (HITL 트리거 + 메모리 architecture). §6.1 신규 사용자 요구사항. §7.0 Minimum Viable Completion. §8 Feature-driven Iterative 채택 (7-domain v2.0 rewrite 폐기). §8 Q 축소. Sprint 명명 단순화 (Sprint 14 A3 종결 + Sprint 15 POC 2차) |
| 2026-04-28 | §9 사용자 답 lock — A/B/C/D/E/F/G 동의, H 동의 + ADR-015/016 통합. §5.2 ADR-015/016 → 단일 ADR-015 "메모리 기반 양방향 의도 통신 architecture". §8.1 흐름도 갱신 (Step 3~5 통합). §8.5 답 박제. Phase A-3 진입 |
