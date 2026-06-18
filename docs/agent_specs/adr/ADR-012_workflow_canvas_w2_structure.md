# ADR-012: Workflow Canvas W2 — 확장형 폴더 구조 + paused 게이트

## Status

**Accepted** (2026-05-16) — 8 Stage TDD 모두 통과. spec 62 v1.1 정식 + main 누적 8 commit.

이전 이력:
- Proposed (2026-05-16) — Stage 0~6 작업 중.

## Context

### W1 완료, W2 진입 시점

- W1 (read-only 시각화) — Sprint 15 P0 완료. React Flow + dagre 자동 레이아웃 + 5 노드 타입 + MiniMap/Controls.
- W2 (시각적 편집) 는 spec 62 §7 일정 = Sprint 15 P1.
- 기존 `features/workflow/` 폴더 = 평탄 3 파일 (`WorkflowPage.tsx`, `WorkflowCanvas.tsx`, `NodeComponent.tsx`).

### 문제 (W2 진입 시 발생)

W2 가 도입할 신규 컴포넌트:
- 우클릭 컨텍스트 메뉴 (`ContextMenu`)
- 속성 패널 (`PropertyPanel`)
- 편집 toolbar (`EditToolbar`)
- 미적용 변경 badge / 빈 상태 안내 / 카스케이드 시각화 등 보조 컴포넌트
- 편집 임시 상태 store (`editingStore`)
- 편집 hook (`useWorkflowEditing`)

평탄 폴더에 7~10 신규 파일 추가 → **컴포넌트 sprawl**. 또한 W3 (Save/Library) / W4 (노드 팔레트) 진입 시 더 큰 폴더 정리 필요. POC 단계에 한 번 정리하는 비용 < 매 Phase 마다 분류 비용.

### 백엔드 게이트 제약

[`ws_hitl.py::_handle_todo_modify/delete/add`](../../../backend/api_v2/ws_hitl.py) — Sprint 14 A3 Phase 5 (2026-04-24) 완료 시점에 *paused 상태에서만 편집 허용* 정책 채택:

```python
if not progress or progress.status != "paused":
    return hitl_ack(accepted=False, code="TODO_EDIT_NOT_PAUSED", ...)
```

→ 프론트가 paused 가 아닌 상태에서 `sendTodoModify` 등을 보내면 **모두 거부**. UI 가 이를 사전 차단해야 함.

### 사용자 요구사항 (계획서 검토 시)

[`docs/_claude/workflow_w2_plan_2026-05-16.md`](../../_claude/workflow_w2_plan_2026-05-16.md) Q1~Q8 모두 권장 그대로 확정:

| Q | 답 |
|---|---|
| Q1 폴더 구조 | 4 layer (canvas / editing / library / palette) |
| Q2 변경 적용 모드 | `immediate` (단순 시작) |
| Q3 ContextMenu 항목 | 삭제 + 수정 2개 |
| Q4 PropertyPanel 필드 | rationale / agent / tool / tool_params |
| Q5 EditToolbar 버튼 | + 단계 추가 / 선택 삭제 (변경 적용은 batched 후속) |
| Q6 드래그 위치 | W2 후속 |
| Q7 Stage 분해 | 8 Stage TDD |
| Q8 spec 62 bump | Stage 7 일괄 |

## Decision

### 1. 폴더 4 layer 분리

```
features/workflow/
├── WorkflowPage.tsx              ← 라우트 진입 (얇음, 조립만)
├── canvas/                       ← 시각화 layer (편집 모름)
│   ├── WorkflowCanvas.tsx
│   ├── NodeComponent.tsx
│   └── nodeTypes.ts
├── editing/                      ← 편집 layer (W2 핵심)
│   ├── ContextMenu.tsx
│   ├── PropertyPanel.tsx
│   ├── EditToolbar.tsx
│   └── useWorkflowEditing.ts
├── store/                        ← 편집 임시 상태
│   └── editingStore.ts
├── library/                      ← (W3 예정) Save/Library
│   └── README.md
├── palette/                      ← (W4 예정) 노드 팔레트
│   └── README.md
└── README.md                     ← layer 가이드 + 의존 규칙
```

**layer 의존 규칙** (단방향):
- `canvas/` 는 *시각화만* — `useExecution.plan` (read-only) + 부모 콜백. 편집 모름.
- `editing/` → `canvas/` 의존 OK. 역방향 금지.
- `store/editingStore` 는 *편집 임시 상태* 전담 — `useExecution.plan` (서버 진실 캐시) 와 분리.

### 2. paused 게이트 정합

프론트 `useExecution.isPaused === true` 일 때만 편집 활성. 그렇지 않으면 read-only + 안내.

```ts
// useExecution 의 derive
const canEdit = isPaused && !!turnId;
```

paused 상태 도달 경로:
1. **plan_review** (검토 ON) — 백엔드 spec 21 v1.4 Phase 5 가 자동 progress paused 생성
2. **execution_pause** — 사용자 [⏸ 중지]

비-paused 상태 진입 시 = empty state + "편집은 일시정지 상태에서 가능" 안내.

### 3. 편집 결과 반영 = 자연 동기화 (변경 0)

`useExecution.handleWSMessage('hitl_ack')` (P1-4 에서 이미 구현) 가 `ack.plan` 받으면 `setPlan` 호출 → React Flow re-render 자연 발생. **별도 갱신 로직 X**.

### 4. applyMode = immediate (W2 진입 시 단순)

사용자 우클릭 삭제 → 즉시 `sendTodoDelete`. `batched` (변경 적용 버튼) 는 W2 후속.

## Consequences

### Positive

1. **수정 위치 명확** — 새 편집 동작 (예: 엣지 끊기) → `editing/` 1 컴포넌트 + 1 송신 함수. 새 시각화 (예: 분기 노드) → `canvas/nodeTypes.ts` + 1 컴포넌트. 사용자 요구사항 "어디를 수정해야 되는지 명확하면 문제 X" 정합.
2. **W3/W4 진입 시 sprawl 회피** — 자리 (library/, palette/) 이미 마련.
3. **백엔드 변경 0** — 모든 endpoint Sprint 14 A3 에 준비됨.
4. **자연 동기화** — hitl_ack 흐름 재활용. 새 데이터 갱신 코드 X.

### Negative

1. **Stage 1 폴더 리팩 = ~100 줄 이동** — git mv + import 경로 수정. typecheck 일시적 broken 가능 → Stage 1 의 commit 시점에 typecheck/build 통과 보장.
2. **paused 가 아닌 사용자에게 UI 비활성** — UX 미묘. 안내 메시지 명확화로 완화.
3. **main 직접 작업** = 중간 fail 시 main broken 위험 → Stage 별 4종 회귀 정책 (typecheck + build + vitest + sprint13/15) 으로 완화.

### Risk Mitigation

- 각 Stage 끝마다 4종 회귀 — 통과 전 다음 Stage 진입 금지.
- atomic commit (Stage 1 = 1 commit 원칙).
- Stage 6 끝 + Stage 7 끝 시점에 사용자 브라우저 검증.

## Alternatives Considered

### Alt A: 별도 브랜치 `workflow_w2`

- 사용자 검토 시 main 선택. 본 ADR 의 작업 분량 (~6.5시간, 8 Stage) 이 multi-day 가 아닌 *한 작업 묶음* 으로 분류 가능.
- 기각 — 사용자 결정.

### Alt B: 폴더 평탄 유지 (W3/W4 시점에 한꺼번에 리팩)

- W3/W4 진입 시 변경 분량이 더 큼 (Total ~20 파일 한 번에 이동 vs 본 Decision 의 단계적 진화).
- 기각 — 사용자 메모리 [`feedback_no_mixed_codebases`](.) 의 "점진 추가 후 전환 Sprint" 원칙은 *코드베이스 마이그레이션* 컨텍스트. 본 건은 *폴더 구조 진화* 라 평탄 유지보다 layer 명시가 정합.

### Alt C: paused 게이트 무시 (UI 항상 활성)

- 편집 시도 → 백엔드 모두 거부 → 모든 ack 가 reason=TODO_EDIT_NOT_PAUSED. UX 최악.
- 기각.

### Alt D: 편집 임시 상태를 useExecution 에 통합 (별도 editingStore X)

- `useExecution.plan` (서버 진실 캐시) 와 *편집 임시 상태* (선택 노드 등) 가 같은 store 에 섞임 → 책임 혼동.
- 기각 — 단일 책임 원칙.

## Verification Plan (Stage 별)

본 ADR 의 *implementation* 은 [`docs/_claude/workflow_w2_plan_2026-05-16.md`](../../_claude/workflow_w2_plan_2026-05-16.md) §4 의 8 Stage TDD 로 수행. 통과 시 본 ADR 의 Status 를 Accepted 로 갱신.

| Stage | 검증 |
|-------|------|
| 0 | ADR-012 + spec 62 v1.1 초안 + shadcn 의존 확인 |
| 1 | 폴더 리팩 — read-only 동작 그대로 (typecheck/build/E2E) |
| 2 | editingStore + Canvas 이벤트 인터페이스 (vitest) |
| 3 | ws.ts 송신 3개 + useWorkflowEditing hook (vitest) |
| 4 | ContextMenu — 우클릭 삭제/수정 |
| 5 | PropertyPanel — 더블클릭 속성 편집 |
| 6 | EditToolbar + cascade 시각화 + 비-paused 안내 |
| 7 | spec 62 v1.1 + ADR Accepted + E2E 시나리오 3종 |

## 관련 명세 / 결정

- spec 62 v1.0 → v1.1 (`62_workflow_canvas_design_v1.1.md`) §2/§5/§7 갱신
- spec 21 v1.5 — 변경 없음 (todo_modify/delete/add 이미 명세됨)
- spec 22 v1.1 — 변경 없음 (TODO_EDIT_NOT_PAUSED 이미 카탈로그됨)
- ADR-002 (NL 편집 1·2·3차 로드맵) — W2 시각적 편집은 NL 편집과 *공존*, ADR-002 와 직교
- ADR-010 (Plan/Todo schema 통합) — `planner.Plan` 단일화 기반 위 W2 진행

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-05-16 | 초안 (Stage 0) — Proposed. ws_contract 머지 직후 main 에서 8 Stage TDD 진입 준비 |
| 2026-05-16 | 8 Stage TDD 모두 통과 (Stage 1 폴더 리팩 / 2 editingStore + Canvas 인터페이스 / 3 ws 송신 + hook / 4 ContextMenu / 5 PropertyPanel / 6 EditToolbar + cascade + empty-state / 7 spec 62 v1.1 정식). 매 Stage 4종 회귀 (typecheck + build + vitest 22/22 + sprint13/15 191/191). Accepted |
