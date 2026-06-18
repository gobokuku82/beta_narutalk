# ADR-013: Workflow Canvas W2' — 엣지 / 드래그 / batched 모드 + 시각 편집 gap 보강

## Status

**Accepted** (2026-05-17) — Stage 0~7 통과. 회귀 vitest 56/56 + backend 191/191. spec 62 v1.2 발효.

## Context

### W2 (ADR-012) 완료 후 사용자 발견 사항

ADR-012 완료 후 사용자 실사용 검증에서 다음 발견:

1. **노드끼리 선 잇는 작업 미구현** — 사용자 명시 요구.
   - `WorkflowCanvas` 의 `nodesConnectable={false}` `nodesDraggable={false}` 강제 read-only.
   - spec 62 §5.1 에 "노드 드래그 (순서 변경)" / "엣지 클릭 → 끊기" 명시되어 있으나 W2 범위에 포함 안 됨.
2. **동기화 모델 검토** — 현재 *immediate* (편집 즉시 ws 송신 → 채팅창 ChatTodoCard 자동 갱신).
   - 사용자 제안: *batched* (편집 누적 후 "완료" 클릭 시 일괄 송신) 도 가능해야.
   - 가치 = 실험적 편집 (여러 노드 옮기고/추가/삭제 후 한꺼번에 적용 또는 취소).
3. **3 워크플로우 고려사항** (사용자 명시):
   - ① 단순하고 쉽게 구성 가능
   - ② 사용자 맞춤형 복잡 구성 가능
   - ③ 각 작업의 의존성 명확

### Audit (2026-05-17 정정)

이전 audit 에서 백엔드 plan_editor 가 modify 의 일부 필드만 처리한다고 보고, "백엔드 변경 ~80 줄" 추정했음. **정정**:

| 경로 | 처리 위치 | 처리 범위 |
|------|---------|---------|
| **시각 편집** (todo_modify/delete/add) | `HITLManager → TodoManager.modify_todo` | **모든 키 통과** (`for key, value in changes.items(): todo[key] = value`) + `_rebuild_dag` 자동 |
| **NL 편집** (todo_edit_nl) | `HITLManager → plan_editor.apply_edit` (LLM 파싱) | task/rationale/tool/priority/agent 만 |

→ 시각 편집의 백엔드 변경 = **0**. depends_on / position / tool_params / task_type / node_type **모두 이미 처리됨**. ADR-012 의 "백엔드 변경 0" 정확.

### W2' 추가 점검 (audit 부산물)

| 항목 | 내용 |
|------|------|
| **issues UX** | `TodoManager.validate` 가 `_detect_cycle` 등으로 `issues: list[str]` 반환 → `hitl_ack.data.issues` 로 emit. 현 프론트는 무시 — cycle 만들어도 사용자 안내 0. |
| **tool_params merge vs replace** | `TodoManager.modify_todo` 는 `tool_params` 만 *merge* (덮어쓰기, 키 삭제 불가). PropertyPanel 의 "전체 교체" 의도와 경계 불일치. |
| **position cascade** | position 변경은 DAG 무관 → `calculate_cascade` 결과 빈 배열이어야. 단위 테스트로 검증 필요. |

### 사용자 핵심 4 질문 확정 (계획서 §9, 2026-05-17)

| Q | 결정 |
|---|------|
| (1) Phase 진행 | 4 Phase 전부, 순서 W2' → W5 → W3 → W4 |
| (2) 동기화 default | 사용자 토글 default=immediate |
| (3) W4 branch/join | W4 후속 분리 |
| (4) ADR 분리 | Phase 별 (ADR-013 W2' / 014 W3 / 015 W4 / 016 W5 옵션) |

## Decision

### 1. W2 의 read-only 강제 해제

`WorkflowCanvas`:
- `nodesConnectable={editable}` (paused 시 true)
- `nodesDraggable={editable}`

### 2. 엣지 연결 / 끊기 / 노드 드래그 → 기존 endpoint 재활용

| 동작 | ws 메시지 | 백엔드 처리 |
|------|---------|----------|
| 엣지 연결 (source → target Handle drag) | `todo_modify(target, {depends_on: [...existing, source]})` | TodoManager.modify_todo 통과 |
| 엣지 끊기 (엣지 클릭 → 확인) | `todo_modify(target, {depends_on: existing.filter(!=source)})` | 동일 |
| 노드 드래그 종료 | `todo_modify(id, {position: {x, y}})` (debounce 300ms) | 동일 |

→ **백엔드 변경 0**.

### 3. Cycle 사전 차단

프론트가 *드래그 중* DFS 로 cycle 검증 → drop 시점에 cycle 이면 빨간 X 표시 + drop 거부. 백엔드 fall-back 으로 `issues` 받아 토스트.

### 4. issues UX 추가

`useHitl.handleWSMessage('hitl_ack')` 에 `if ack.issues?.length` 시 `sonner` 토스트 표시 — "DAG 검증 오류: ...". 변경 자체는 적용되지만 (TodoManager 이미 처리) 사용자에게 *경고* 알림.

### 5. tool_params 정책 = merge 유지 (POC)

PropertyPanel 의 JSON 편집은 현재 *전체 교체* 의도지만, 백엔드 merge 한계로 *키 삭제 불가*. POC 단계 정책:
- 사용자 메시지: "키 삭제는 빈 문자열로 변경하세요" (PropertyPanel 안내).
- 향후 replace 필요 시 별도 ADR (정책 변경).

(대안: TodoManager 1줄 변경 — `todo["tool_params"] = value` 로 replace. 단 기존 NL 편집 케이스에 영향 검증 필요. **W2' 에서는 보수적 merge 유지**.)

### 6. batched 모드 = 사용자 토글 default=immediate

editingStore.applyMode 의 토글 (`'immediate' | 'batched'`).
- **immediate** (default): 우클릭 삭제 즉시 송신 (현 동작).
- **batched**: pendingOps 누적 → "완료" 클릭 시 클라가 N 회 ws 송신 (백엔드 batch endpoint 신설 X — POC 단계).
- 로컬 시각화: 변경 노드 ✏ / 삭제 예정 회색+점선 / 신규 + 배지.
- 모드 전환 시점: EditToolbar 우측 toggle.
- batched 중 turn timeout 또는 PauseBox 자연어 편집 발생 → editingStore.reset + 안내.

### 7. 폴더 위치

W2' 의 신규 모듈은 ADR-012 §1 의 4 layer 그대로:
- 엣지/드래그 핸들러 → `canvas/WorkflowCanvas.tsx` (이벤트 위임만)
- cycle 검증 → `editing/cycleGuard.ts` (신규)
- batched UI → `editing/BatchedToolbar.tsx` (신규) + `editingStore.pendingOps` 확장

## Consequences

### Positive

1. **사용자 명시 요구 해소** — 엣지 연결 가능.
2. **3 고려사항 직접 답** — ① 단순 (immediate 단순 유지) / ② 맞춤 (batched + 엣지 자유) / ③ 의존성 (엣지 시각 편집 + cycle 검증).
3. **백엔드 변경 0** — TodoManager 가 이미 통과. ADR-012 의 정합 유지.
4. **issues UX 추가로 사용자 신뢰** — 침묵 실패 제거.
5. **batched 모드로 실험적 편집** — 잘못된 변경 일괄 취소 가능.

### Negative

1. **프론트 분량 ~420 줄** — 엣지/드래그 핸들러 + cycle DFS + batched UI + 단위 테스트.
2. **batched 의 atomicity 약함** — 클라 N 회 송신 중 중간 fail 가능. 대응: 첫 ack 거부 시 멈춤 + 안내.
3. **tool_params merge 한계** — 키 삭제 불가. POC OK.

### Risk Mitigation

- Stage 별 4종 회귀 (typecheck / build / vitest / sprint13+15) — ADR-012 패턴 그대로.
- 매 Stage atomic commit.
- batched 모드는 *별도 Stage* 로 분리 — 엣지/드래그 (필수) 가 먼저 안정 후 도입.
- main 직접 작업 정책 그대로.

## Alternatives Considered

### Alt A: 엣지/드래그 만 (batched 제외)

- 사용자 가치 작아짐. 사용자가 *명시적으로 동기화 모델 검토* 요청.
- 기각.

### Alt B: 백엔드 batch endpoint 신설 (`todo_batch_apply`)

- atomicity 보장. 단 백엔드 핸들러 + 테스트 신규 ~80 줄.
- POC 단계 → 기각. 향후 atomicity 본질 요구사항 되면 별도 ADR.

### Alt C: tool_params replace 즉시 변경

- TodoManager 1줄. 단 NL 편집 (plan_editor) 의 modify 케이스에 영향 검증 필요 — `params["tool"]` 외 tool_params 도 받는 케이스? 회귀 위험.
- W2' 에서는 보수적 merge 유지, 별도 ADR 로 정책 변경.

### Alt D: cycle 검증 백엔드만

- 백엔드 `validate` 이미 cycle 감지. 그러나 사용자 드래그 중 *즉시 피드백* 없음 → UX 나쁨.
- 기각 — 프론트 사전 차단 + 백엔드 fall-back 권장.

## Verification Plan (Stage 별)

구체 계획 = [`docs/_claude/workflow_advanced_plan_2026-05-16.md`](../../_claude/workflow_advanced_plan_2026-05-16.md) §3.1 (W2' FR/UX/NFR). 8 Stage TDD:

| Stage | 내용 |
|-------|------|
| 0 | ADR-013 + spec 62 v1.2 초안 + sed + INDEX |
| 1 | 엣지 연결/끊기 핸들러 (`onConnect` / `onEdgeClick`) + ws 송신 매핑 |
| 2 | cycle 사전 차단 (`editing/cycleGuard.ts` + DFS) + 단위 테스트 |
| 3 | 노드 드래그 (`onNodeDragStop` + debounce 300ms + position 송신) |
| 4 | issues UX (useHitl.hitl_ack 분기 + sonner 토스트) |
| 5 | editingStore.pendingOps 확장 + applyMode 토글 |
| 6 | batched UI — BatchedToolbar + 로컬 시각화 (✏/회색/+ 배지) + apply/cancel |
| 7 | spec 62 v1.2 정식 + ADR Accepted + E2E |

W2' 통과 시 ADR-013 Status: Proposed → Accepted, 다음 = W5.

## 관련 명세 / 결정

- spec 62 v1.2 (`62_workflow_canvas_design_v1.2.md`) — W2′ 본문 박제
- ADR-012 — W2 기반 (Accepted). 본 ADR-013 은 *후속 보강*.
- ADR-002 NL 편집 — *직교*. NL 1차 (plan_editor) 와 시각 편집 (TodoManager) 의 책임 분리 정확.

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-05-17 | 초안 (Stage 0) — Proposed. main 8 Stage TDD 진입 준비 |
| 2026-05-17 | **Accepted** — Stage 1~3 (엣지/cycle/드래그) + Stage 4 (issues UX) + Stage 5 (pendingOps + applyMode 분기) + Stage 6 (BatchedToolbar + 배지 시각화 + turn 종료 reset) + Stage 7 (spec 62 v1.2 + 본 문서). 회귀 vitest 40 → 56 (+16), backend 191/191. 백엔드 변경 0 (audit 정정 — TodoManager 가 이미 모든 필드 통과). |
