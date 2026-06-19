# Requirements Specification (POC / Sprint 13~14)

| 항목 | 내용 |
|------|------|
| 담당자 | 도윤 |
| 분류 | 요구사항 정의 (Requirements) |
| 진행상태 | **Active** — POC / Sprint 13 완료 + Sprint 14 A1 완료 + A3 Phase 5 편집 경로 통합 완료 (브라우저 수동 대기) |
| 버전 | **v1.6** |
| 최종 수정일 | 2026-04-24 |
| 관련 명세 | `10_system_architecture_v1.9.md`, `12_manager_layer_v1.4.md`, `13_lifecycle_v1.3.md`, `21_WEBSOCKET_PROTOCOL_v1.5.md`, `22_error_codes_v1.1.md`, `24_sequence_diagrams_v1.3.md` |

> 이 문서는 "무엇을 만들고 있는가 / 왜 이 범위인가"의 단일 기준.  
> **기능 세부는 설계 문서(10~30번대) 참조.** 여긴 "요구사항" 수준만.

---

## 1. 비즈니스 목표

**DreamAgent V2** — 도메인 작업 자동화 AI 에이전트 프레임워크.

- **핵심 가치**: 사용자가 자연어로 쿼리하면, Agent 가 의도 분석 → 계획 수립 → 승인 후 실행 → 결과 요약. **계획은 사용자가 자연어 또는 UI 로 수정 가능** (Todo 편집 = 앱의 핵심 상호작용).
- **POC 목표 (~Sprint 17)**: LLM 기반 4-Layer 파이프라인 + HITL + Checkpoint 복원 + Todo 편집 (구조화 + NL) 검증. 단일 도메인 운영에 국한.
- **MVP 기준**: Sprint 17+ — 인증 / 멀티 테넌트 / 실시간 대시보드 / PII.

## 2. 이해관계자 / 페르소나

| 역할 | 설명 | 주 사용 기능 |
|------|------|--------------|
| **운영자(Operator)** | 도메인 작업 실무자. 자연어로 쿼리 입력 | 쿼리 입력, Plan 승인/거부, 실행 중 pause, **Todo 편집 (NL)** |
| **PM(Project Manager)** | 플랜 검토 / 실행 감시 | Plan 승인, **Todo 편집 (구조화 UI + NL, Sprint 14 A3)**, Pause/Resume |
| **개발팀** | 프롬프트 / 규칙 / Agent 튜닝 | `logs/layer_guard.jsonl`, Checkpoint 조회 |

POC 단계에서 위 3역할은 사실상 **동일 사용자** (개발자 본인).

## 3. 기능 요구사항 (FR)

| ID | 요구사항 | Sprint | 상태 |
|----|---------|--------|------|
| FR-1 | 사용자 자연어 쿼리 입력 가능 (WebSocket) | 13 | ✅ |
| FR-2 | 과거 대화 이력 참조한 의도 재해석 (Cognitive) | 13 | ✅ |
| FR-3 | 팀/Todo 구조의 실행 계획 자동 수립 (Planning) | 13 | ✅ |
| FR-4 | Plan 승인/거부/수정 HITL | 13 | ✅ (수정은 Sprint 14 A3 에서 확장) |
| FR-5 | Todo DAG 병렬 실행 (Execution) | 13 | ✅ |
| FR-6 | 실행 중 사용자 Pause/Resume | 13 | ✅ (phase 경계) |
| FR-7 | 마크다운 형식 응답 생성 (Response) | 13 | ✅ |
| FR-8 | Layer 품질 가드 (빈 쿼리/빈 플랜/전부 실패 등) | 13 | ✅ |
| FR-9 | 서버 재시작 시 중단 Turn 복원 (Checkpoint) | 13 | ✅ (R-9 live 검증 2026-04-21) |
| FR-10 | 사용자당 동시 Turn 개수 제한 (default 3) | 13 | ✅ |
| FR-11 | 같은 user 다중 탭 브로드캐스트 (fan-out) | 13 | ✅ |
| **FR-12** | **Todo 편집 HITL (구조화 + 자연어 병행)** | **14 A3** | **🟡 백엔드·자동 완료, 브라우저 수동 대기** |
| FR-12a | 구조화: Todo **수정** (task/priority/depends_on/tool_params 변경) | 14 A3 | 🟡 백엔드 ✅ + UI ✅ (편집 모달 생략, inline text/NL 로 대체), 브라우저 R-5 대기 |
| FR-12b | 구조화: Todo **삭제** (행 🗑 버튼 + cascade 무효화) | 14 A3 | 🟡 전수 구현, 브라우저 R-5/R-6 대기 |
| FR-12c | 구조화: Todo **추가** ("+ 추가" 버튼 + `after_todo_id` 지정) | 14 A3 | 🟡 전수 구현 (agent/task prompt), 브라우저 R-7 대기 |
| FR-12d | 구조화: Todo **순서 변경** (드래그 앤 드롭 + `reorder` action) | 14 A3 | 🟡 plan_editor reorder 신구현 + UI HTML5 drag&drop, 브라우저 R-17 대기 |
| FR-12e | 자연어: `todo_edit_nl` 메시지 (LLM 단회 파싱 → apply) | 14 A3 | 🟡 `_handle_todo_edit_nl` + plan_editor Pydantic↔dict 변환 + D-13 injection 방어, 브라우저 R-16/18 대기 |
| FR-12f | **편집은 `progress.status == "paused"` 조건만** (Phase 5 단순화 — plan_review 시 ws_agent 가 임시 progress `status="paused"` 생성) | 14 A3 | ✅ 백엔드 가드 + UI 연동 |
| FR-12g | 편집 후 **cascade 계산** (invalidated/preserved/restart_from) → UX 라벨 노출 | 14 A3 | ✅ `calculate_cascade` + renderCascade (🔴 tint + ⛓ 라벨 + 통계) |
| FR-12h | 다단계 자연어 대화 (clarification) — **Out of scope**, Sprint 15+ 또는 A5 | — | ❌ (Y-a 결정에서 γ 분리) |
| FR-13 | **HITL 응답 타임아웃 (pause/plan_review 공유)** | 14 A1 | ✅ (2026-04-22) |
| FR-13a | timeout 시 `complete(aborted, reason=hitl_timeout)` emit + slot 해제 | 14 A1 | ✅ (2026-04-22, HTL-01/02 실 Checkpoint 종결 증명) |
| FR-13b | timeout 이후 동일 turn_id 의 pause/resume/cancel/hitl_response 4종은 `turn_not_active` 로 거부 | 14 A1 | ✅ (2026-04-22, Round 17 hitl_response 포함) |
| **FR-13c** | **동일 가드가 `todo_modify/delete/add/edit_nl` 4종에도 적용 (A3 에서 확장)** | **14 A3** | **✅** (2026-04-23, `_check_turn_active` 헬퍼 DRY 적용. A1 4종 + A3 4종 = 8종 핸들러) |
| FR-14 | 대화 세션 저장/불러오기 (Memory) | 15 | ⏳ |

### FR-12 부연 설명 — Y-a 정책

**Y-a** 방침 (Sprint 14 A3 scope 결정, 2026-04-23):
- 구조화 편집 UI (FR-12a~d) 와 자연어 편집 (FR-12e) 을 **병행** 제공
- 같은 편집 대상에 대해 사용자가 방식 선택 (빠른 1클릭 삭제는 구조화, 복합 수정은 자연어)
- 자연어는 **단회 LLM 호출** 만 (parse → apply). 다단계 대화 (FR-12h) 는 out of scope

## 3.5 UX 요구사항 (UX)

사용자 경험 측면에서 만족해야 하는 기준. 코드 레벨 기능(FR)과 달리 대시보드·알림·상태 표시 등 **프런트/상호작용** 관점.

| ID | 요구사항 | Sprint | 상태 |
|----|---------|--------|------|
| UX-1 | 실행 상태 버튼 전이: idle → waiting → pause_available → resume_available | 13 | ✅ |
| UX-2 | 서버 재시작 후 재접속 시 미완료 Turn 자동 resume_query (last_turn_id 기반) | 13 | ✅ |
| UX-3 | auto-approve (plan_review 자동 승인) 경로에서도 Todo 리스트 렌더 | 13 | ✅ (R-10) |
| UX-4 | HITL timeout 발생 시 대시보드에 시스템 메시지 표시 ("자동 종료됨") + plan_review 모달 자동 close | 14 A1 | ✅ (2026-04-22, R-13 live) |
| UX-5 | timeout 이후 늦은 HITL 요청 시 토스트 + idle 복귀 (turn_not_active ack 처리) | 14 A1 | ✅ (2026-04-22, R-14 live) |
| UX-6 | (Sprint 15) 대화 사이드바에서 종료/중단 Turn 이어하기 — Memory 범위 | 15 | ⏳ |
| **UX-7** | **Pause interrupt 수신 시 편집 모달 자동 팝업** (Plan review 와 동일 패턴) | **14 A3** | **🟡** `handlePaused` → `openHitlModal("pause", data)` 구현 ✅, 브라우저 수동 대기 |
| **UX-8** | **Plan review 모달 과 Pause 모달은 같은 DOM 재사용** (`data-mode="plan_review|pause"`). 헤더·버튼 라벨만 차등 ("승인/거부" ↔ "재개/취소") | **14 A3** | **🟡** 구현 ✅ (데이터 속성 + CSS 차별화), 브라우저 수동 대기 |
| **UX-9** | **Todo 행 편집 컨트롤**: 🗑 삭제 버튼 + ≡ 드래그 핸들 (순수 HTML5 Drag&Drop) + 행 클릭 → 상세 편집 모달 | **14 A3** | **🟡** 🗑 + 드래그 구현 ✅ (상세 편집 모달은 NL textarea 로 대체), 브라우저 수동 대기 |
| **UX-10** | **자연어 편집 textarea** (모달 하단, 재개/취소 버튼 위). 적용 중 로딩 indicator (LLM 호출 ~1~2s). 실패 시 토스트 + textarea 내용 보존 | **14 A3** | **🟡** 구현 ✅ (로딩 spinner + 5종 에러 분기), 브라우저 R-16~18 대기 |
| **UX-11** | **Cascade 무효화 시각화** — invalidated Todo 행 🔴 tint (배경색 `#450a0a`) + "⛓ restart_from: Todo X 부터 재실행" 라벨 모달 상단에 표시 | **14 A3** | **🟡** 구현 ✅ (renderCascade + 통계 바), 브라우저 수동 대기 |
| **UX-12** | **NL 파싱 실패 UX** — 의도 불명확 (`NL_INTENT_UNCLEAR`) 시 "어떤 작업을 원하시는지 구조화 UI 로 시도해보세요" 안내 토스트 + 구조화 UI 유지 | **14 A3** | **🟡** 5종 분기 (12a NL_INTENT_UNCLEAR / 12b LLM 실패 / 12c 타임아웃 / 12d 컨텍스트 초과 / 12e REORDER 실패) 구현 ✅, 브라우저 R-18 대기 |

## 4. 비기능 요구사항 (NFR)

| ID | 항목 | 목표 | 현재 |
|----|------|------|------|
| NFR-1 | 동시성 | user당 최대 3 Turn | `MAX_CONCURRENT_TURNS_PER_USER=3` |
| NFR-2 | WS 연결 | user당 최대 5 탭 | `MAX_WS_CONNECTIONS_PER_USER=5` |
| NFR-3 | 의도 해석 지연 | P95 < 5s (LLM 단독) | 미측정 (Sprint 16) |
| NFR-4 | Plan 승인 응답 | interrupt 후 즉시 (Queue 기반) | ✅ (I7) |
| NFR-5 | Pause 응답 한계 | phase 경계에서만 (부분 제약) | 문서화됨 (`13_lifecycle`) |
| NFR-6 | 신뢰성 | 서버 재시작 후 Turn 복원 | AsyncPostgresSaver |
| NFR-7 | 관찰성 (POC) | layer guard JSONL | `logs/layer_guard.jsonl` |
| NFR-8 | 확장성 | Sprint 17+ K8s 배포 준비 | out of scope (POC) |
| NFR-9 | HITL 응답 대기 기본값 | 30분 (1800s) | `settings.HITL_RESUME_TIMEOUT_SEC` ✅ (Sprint 14 A1 완료) |
| NFR-10 | HITL 타임아웃 설정 방식 | `.env HITL_RESUME_TIMEOUT_SEC=<초>` override | ✅ pydantic `Field(ge=1)` validator (Sprint 14 A1 완료) |
| **NFR-11** | **NL 편집 LLM 응답 지연** | **P95 < 3s** (plan_editor.parse_instruction 단회 호출) | 미측정, Sprint 14 A3 측정 대상 |
| **NFR-12** | **NL 편집 파싱 결정성** | 동일 입력 → 동일 action JSON (temperature=0, seed 고정 권장) | 테스트 그룹 F race 2건 검증 예정 |
| **NFR-13** | **Todo 드래그 앤 드롭 프레임워크** | 순수 HTML5 Drag & Drop API (SortableJS 3KB 옵션). **Next.js 전환 불필요** | ⏳ (Sprint 14 A3 결정) |
| **NFR-14** | **Cascade 계산 복잡도** | O(V+E) BFS (`calculate_cascade`). Todo ≤ 50 전제 | ✅ 코드 구현됨 |

## 5. 제약 / 범위

### In Scope (Sprint 13)
- 단일 도메인 고정
- 단일 사용자 (`demo`)
- 로컬 PostgreSQL Checkpointer
- Plan 승인/거부 + Execution Pause/Resume 만
- 대시보드 (개발자용 HTML)

### In Scope (Sprint 14 확장)
- ✅ **A1 HITL 타임아웃 완료** (FR-13/13a/13b, NFR-9/10, UX-4/5) — 2026-04-22
- ⏳ A2 phase 내 pause 세밀화 (`should_continue` Todo 단위)
- ⏳ **A3 Todo 편집 HITL** (FR-12 전체, Y-a: structured + NL 단회, D1=E / D2=C-dual / D3=B) — 2026-04-23 착수
- ⏳ A4 `team_catalog.yaml` `requires_approval` 확장
- ⏳ agent_specs 문서 확장 (Glossary / Runbook / Event Catalog 등)
- 🔒 **AgentState Reducer — 보류** (Tool 확장 이후 재평가. Plan 수립 중 writer 전수 조사 결과 실 다중 writer race 부재.)

### Out of Scope (Sprint 13~14)
- 인증/인가, PII, 멀티 테넌트
- Prometheus/Grafana observability
- Memory / 대화 이력 DB 저장 (Sprint 15)
- timeout 이후 재개 UI — **Sprint 15 Memory 범위** (UX-6)
- **다단계 자연어 편집 대화 (clarification)** — A5 또는 Sprint 15+ (FR-12h)
- **자연어 편집의 Cognitive layer 재진입** — 현재는 plan_editor 단회 호출만
- 운영 배포, CI/CD, 로그 로테이션

## 6. 성공 기준 (Acceptance)

Sprint 13 기준:
- ✅ 비-live 테스트 **137/137 pass × 3회 안정** (R-9 resume_only 대응 RO-01~13, WQ-09~11 추가)
- ✅ Live 테스트 6/6 개별 pass (WL-01~06)
- ✅ 브라우저 수동 regression 전 항목 pass:
  - R-1 plan 승인 / R-2 reject / R-3 pause / R-4 resume (Sprint 12 기존)
  - **R-9 서버 재시작 복원** (2026-04-21 성공 — resume_query + Checkpoint 복원)
  - **R-10 plan_review auto-bypass** (2026-04-22 성공 — cognitive/planning 중 pause → auto-approve → paused 이벤트에서 Todo 리스트 복원 렌더)
  - **R-11 연속 pause/resume 3회 토글** (2026-04-22 성공 — CallbackManager dedup 검증)
  - **R-12 progress 유지** (R-9 restore_progress 로그 확인)

Sprint 14 A1 달성 (✅ 2026-04-22):
- [x] HITL timeout 유닛/통합 36건 pass (그룹 A~F)
- [x] Live 4건 pass (그룹 G HTL-01~04) — 실 Checkpoint 종결 증명
- [x] Sprint 13 regression 137/137 유지
- [x] Contract Test 5/5 pass
- [x] 브라우저 regression 3건 전수 pass:
  - **R-13** timeout 발생 → `complete(aborted, reason=hitl_timeout)` 수신 + 한글 시스템 메시지 + 모달 자동 close (UX-4)
  - **R-14** timeout 후 뒤늦은 HITL 요청 (pause/resume/cancel/hitl_response 4종) → `turn_not_active` ack + 토스트 (UX-5)
  - **R-15** timeout'd turn 에 resume_query 재진입 → `INVALID_MESSAGE` emit (G-10)

Sprint 14 A3 자동 달성 (✅ 2026-04-23):
- [x] **테스트 230 pass + 2 skip** (Sprint 13 137 + A1 36 + A3 57)
  - 그룹 A (TodoManager pure) 15건 / B (HITLManager + 가드 + Lock) 12건 / C (ws_hitl structured) 10건
  - 그룹 D (plan_editor NL + injection) 10건 / E (ws_hitl NL) 7건 / F (race) 3 pass + 2 skip
  - 그룹 G (Live E2E) 7건 — 브라우저 수동 R-5~R-18 로 대체
- [x] **Contract Test 8/8 pass** (DC-1~5 + DC-6 ErrorCodes 확장 + DC-10 Status 마커 파싱 2건)
- [x] **문서 5 bump** (01 v1.4→v1.5 / 10 v1.9 / 12 v1.2 / 21 v1.3 / 22 v1.1) + INDEX
- [x] **Dashboard +437줄** (C-dual 모달 + NL textarea + cascade + L2 ack gating + beforeunload)
- [x] **11 커밋 push**

Sprint 14 A3 브라우저 수동 검증 대기 (⏳ 2026-04-23~):

**실행 환경**:
```bash
uv run python run_server.py
# → http://localhost:8001/dashboard 접속
```

**R-5 ~ R-8 Structured 편집 (Sprint 12 정의, A3 live 최초 검증)**:

- [ ] **R-5 Todo 수정**: 쿼리 전송 → Plan review 승인 → execution 중 pause 클릭
  - ✅ 모달 자동 팝업 (주황 헤더 "⏸ 실행 일시정지됨")
  - 대기 Todo 행 🗑 버튼 클릭 → confirm → `todo_delete` 전송
  - ✅ `hitl_ack accepted:true` + 🔴 tint + ⛓ 라벨 표시
  - 재개 → 남은 Todo 실행 → complete(success)
  - (참고: R-5 이름이 "수정" 이지만 3유형 모두 이 테스트로 커버 — R-6 은 cascade, R-7 은 추가)

- [ ] **R-6 Cascade 무효화 시각화**: Plan 에 downstream 3+ 있는 Todo 선택 → pause → 삭제
  - ✅ invalidated 다건 🔴 tint
  - ✅ 통계 바 "N개 무효화 · X개 유지 · ⚠️ issues"
  - ✅ ⛓ "Todo X 부터 재실행됩니다" 라벨 (첫 invalidated = restart_from)

- [ ] **R-7 Todo 추가**: pause → "+ Todo 추가" 버튼 → prompt 에 agent/task 입력
  - ✅ `hitl_ack accepted:true` + 새 Todo 목록 끝에 추가 (depends_on 없음)
  - 재개 → 기존 남은 Todo + 신규 Todo 실행

- [ ] **R-8 Diamond DAG**: t1 → {t2,t3} → t4 구조 plan 에서 t2 만 삭제
  - ✅ invalidated = [t2, t4] (t4 가 t2 depends)
  - ✅ t3 은 preserved (t2 독립)

**R-16 ~ R-18 자연어 편집 (Sprint 14 A3 신규, Y-a)**:

- [ ] **R-16 NL 삭제**: pause → 🗣 textarea "4번 삭제" → [⚡ 적용]
  - ✅ 로딩 indicator (spinner + "⏳ 처리 중...") 1~3초
  - ✅ plan_editor LLM 호출 → action=remove 파싱
  - ✅ `hitl_ack accepted:true, nl_action:"remove"` + cascade 렌더
  - ✅ textarea 내용 초기화 + 피드백 "✓ remove 적용됨"

- [ ] **R-17 NL 순서 변경 (reorder)**: pause → 🗣 "3번과 4번 순서 바꿔" → 적용
  - ✅ plan_editor parse_instruction → action=reorder + target_todo_ids + new_position
  - ✅ apply_edit reorder 분기 실행 (Sprint 14 A3 Phase 3 신구현)
  - ✅ Todo 순서 변경 확인 + cascade (의존성 따라 invalidated)

- [ ] **R-18 NL 파싱 실패 UX**: pause → 🗣 "asdf xyz 123" (의미 불명) → 적용
  - ✅ `hitl_ack accepted:false, code:"NL_INTENT_UNCLEAR"` (D7=A- enum)
  - ✅ 한글 피드백 "⚠️ 어떤 작업을 원하시는지 이해하지 못했습니다. 버튼/드래그로 시도하거나 다시 입력해보세요"
  - ✅ textarea 내용 보존 (재시도 가능)
  - ✅ 모달 유지 (구조화 UI 로 fallback)

**추가 검증 (UX-7~12, 선택)**:

- [ ] **UX-7 Pause 모달 자동 팝업** (Q2-1=A): pause 버튼만 눌러도 모달 자동 open
- [ ] **UX-8 DOM 재사용** (D2=C-dual): 모달 DOM 이 plan_review / pause 동일 (`data-mode` 전환만)
- [ ] **UX-9 드래그 앤 드롭**: Todo 행 잡고 끌어 다른 위치로 drop → `todo_edit_nl` 로 reorder 전송
- [ ] **UX-10 NL 로딩**: 🗣 적용 중 textarea / 버튼 disabled + 로딩 텍스트
- [ ] **UX-11 Cascade 시각화**: 🔴 tint + ⛓ 라벨 + 통계 바 (3요소 확인)
- [ ] **UX-12a NL_INTENT_UNCLEAR** UX — R-18 과 동일
- [ ] **UX-12b~e** 나머지 NL 에러 — LLM API 실제 down 상황 재현 어려움, Phase 9 후속

**보호 기능 검증 (D4/D9/D-13/FR-13c)**:

- [ ] **D4=B+ beforeunload 경고**: pause 모달 open + textarea 에 내용 입력 → F5 → 브라우저 경고 팝업
- [ ] **D9 L2 ack gating**: 🗑 버튼 연타 → 첫 번째만 처리, 나머지 무시 (`_editInFlight` flag)
- [ ] **D9 L1 Lock**: 서버 로그에서 `_get_lock` 획득/해제 확인 (race 로그)
- [ ] **D-13 Prompt injection 방어**: 🗣 에 501자 입력 → action=unknown + "명령 길이 초과" reason
- [ ] **FR-13c 가드**: A1 timeout 발생 (30분 또는 .env 로 10초 단축) → 편집 시도 → "⚠️ 이 쿼리는 시간 초과로 종료되었습니다" 토스트

**추가 측정 (선택, OpenAI API key 필요)**:

- [ ] **D-14 NL 성공률 100회 측정** (측정 스크립트로 반복 실행)
  - 결과 파일: `logs/a3_nl_success_rate_<ts>.jsonl` + `.summary.json`
  - 판정:
    - 실패율 < 3%: ✅ Y-a 유지
    - 3% ≤ 실패율 < 10%: ⚠️ γ (multi-turn) 재평가 trigger → A5 sprint 검토
    - 실패율 ≥ 10%: 🔴 Y-a 범위 재설계 (Y-c structured only 축소)
  - NFR-11 (P95 < 3s) 자동 검증 포함
  - **R-18** NL 파싱 실패 (LLM API 에러 or 의도 불명) → 에러 UX + 구조화 UI 유지 (Sprint 14 A3 신규)

Sprint 14 A2/A4 대기 (⏳):
- [ ] A2 phase 내 pause 세밀화
- [ ] A4 `requires_approval` Tool 확장

## 7. 이해 필요 용어 (요약)

| 용어 | 의미 |
|------|------|
| `conversation_id` | 대화 세션 (여러 Turn 묶음) |
| `turn_id` | 쿼리 1회 = 1 Turn. `thread_id = f"{conv}_{turn}"` |
| **Turn** | 쿼리→응답 1사이클 (복수 phase 실행 + HITL 포함 가능) |
| **Phase** | Plan DAG의 topological 단계. pause 는 phase 경계에서 감지 |
| `interrupt()` | LangGraph 원시 — state를 Checkpoint 저장 후 astream 중단 |
| `Command(resume=...)` | interrupt 값 주입하며 재개 |
| **fan-out** | 같은 user의 모든 WS 탭에 브로드캐스트 (`broadcast_to_user`) |
| **direct-WS** | 수신 WS 한 곳에만 전송 (`_safe_send`) |
| **turn_not_active** | HITL 핸들러 거부 사유 — timeout/완료 등으로 활성 리스트에서 제거된 turn_id (Sprint 14 A1) |
| **`plan_review`** | Planning 종료 후 interrupt 타입 — 사용자 승인/거부/편집 대기 |
| **`execution_pause`** | Execution 중 사용자 Pause 수신 후 interrupt 타입 — 재개/취소/편집 대기 |
| **`todo_edit_nl`** | WebSocket 메시지 — 자연어 Todo 편집 요청 (Sprint 14 A3 신설) |
| **`CascadeResult`** | Todo 편집 시 cascade 계산 결과. 필드: `invalidated_todos`, `preserved_results`, `restart_from`, `new_plan` |
| **`invalidated_todos`** | 편집으로 인해 결과가 폐기되는 Todo 목록 (BFS downstream) |
| **`restart_from`** | **UX 라벨 전용 metadata** — "Todo X 부터 재실행됩니다" 안내용 (D1=E, execution 활용은 Sprint 15+) |
| **`preserved_results`** | 편집 후에도 유지되는 완료 Todo 결과 dict (D1 drift 정리 대상 — 문서는 `preserved_todos: list` 였음) |
| **`plan_editor`** | `backend/app/dream_agent/workflow_managers/hitl_manager/plan_editor.py` — LLM 기반 자연어 편집 파서. `parse_instruction` + `apply_edit` + `validate_edit` 구성 |
| **C-dual** | D2 결정값 — Plan review 모달과 Pause 모달이 같은 DOM 재사용 (`data-mode` 플래그로 분기) |

(상세 Glossary = *(예정) 50_glossary_v1.0.md* — Sprint 14 범위)

## 8. 참조

- 시스템 구조 → `10_system_architecture_v1.9.md` (→ v1.9 A3 완료 시 CascadeResult drift 수정 + todo_edit_nl 흐름 추가)
- 라이프사이클 / 상태머신 → `13_lifecycle_v1.3.md` (Sprint 14 A3 Phase 5 링크 갱신, §3.5 Todo 편집 상태 전이는 별도 추가 예정)
- 시퀀스 다이어그램 → `24_sequence_diagrams_v1.3.md` (§8 Plan review 편집 시퀀스 신규 추가)
- API 계약 → `20_INTERFACE_CONTRACT_v1.1.md`, `21_WEBSOCKET_PROTOCOL_v1.5.md` (→ v1.3 A3 완료 시 todo_edit_nl 스키마)
- Error 카탈로그 → `22_error_codes_v1.1.md` (→ v1.1 A3 완료 시 TODO_* + NL_INTENT_UNCLEAR 추가)
- Manager API → `12_manager_layer_v1.4.md` (→ v1.2 A3 완료 시 handle_todo_* 상세)

## 변경 이력

> 프레임워크 추출(2026-06-19) 이전(마케팅 도메인 시기)의 상세 변경 이력은 git 히스토리를 참조하세요.
