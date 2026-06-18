# features/workflow/ — Workflow Canvas

OctorAD Dream Agent 의 시각적 워크플로우 편집기 (`/workflow` 라우트).

spec: [62](../../../../docs/agent_specs/62_workflow_canvas_design_v1.0.md) (디자인) / [ADR-012](../../../../docs/agent_specs/adr/ADR-012_workflow_canvas_w2_structure.md) (확장형 구조)

## Layer 구성

```
features/workflow/
├── WorkflowPage.tsx     ← 라우트 진입 (얇음, 조립만)
├── canvas/              ← 시각화 layer — 편집 모름
│   ├── WorkflowCanvas.tsx
│   ├── NodeComponent.tsx
│   └── nodeTypes.ts
├── editing/             ← 편집 동작 layer (W2)
├── store/               ← 편집 임시 상태 (selectedNodeId 등)
├── library/             ← Workflow Template Save/Load (W3 예정)
└── palette/             ← 노드 팔레트 (W4 예정)
```

## Layer 의존 규칙 (단방향)

```
editing/ ───→ canvas/    (✅ editing 이 canvas 사용 OK)
editing/ ←──╳ canvas/    (❌ canvas 가 editing 보면 안 됨)
editing/ ──→ store/      (editingStore 구독)
store/   = zustand only  (다른 layer 의존 X)
library/ ──→ memory API  (W3)
palette/ ──→ editing/store + ws.ts (W4)
```

**규칙 위배 방지**:
- `canvas/` 는 *시각화만*. 우클릭/더블클릭 등 이벤트는 *콜백으로 위로 emit*.
- `editing/` 이 콜백 받아 처리.
- `canvas/` 가 `editing/` 또는 `store/` 의 함수/상태를 직접 import 하면 안 됨.

## Phase 매핑 (spec 62 §7)

| Phase | 폴더 | 상태 |
|-------|------|------|
| W1 read-only 시각화 | `canvas/` | ✅ Sprint 15 P0 완료 |
| W2 시각적 편집 | `editing/` + `store/` | 🚧 Sprint 15 P1 진입 (ADR-012) |
| W3 Save / Library | `library/` | ⏳ Sprint 15 P1 또는 16 |
| W4 노드 팔레트 | `palette/` | ⏳ Sprint 16+ |

## 백엔드 의존

| 동작 | WS 메시지 | 백엔드 핸들러 |
|------|----------|---------------|
| 노드 삭제 | `todo_delete` | [`_handle_todo_delete`](../../../../backend/api_v2/ws_hitl.py) |
| 노드 속성 수정 | `todo_modify` | `_handle_todo_modify` |
| 노드 추가 | `todo_add` | `_handle_todo_add` |
| 자연어 편집 (PauseBox) | `todo_edit_nl` | `_handle_todo_edit_nl` |

**활성 조건**: 모두 `progress.status == "paused"` 시점에만 허용 (Sprint 14 A3 정책).
프론트는 `useExecution.isPaused === true` 일 때만 편집 UI 활성화.

## 다음 어디 봐야 하나

| 질문 | 위치 |
|------|------|
| 폴더 구조 결정 근거 | [ADR-012](../../../../docs/agent_specs/adr/ADR-012_workflow_canvas_w2_structure.md) |
| 시각적 편집 동작 매핑 | spec 62 §5.1 |
| W3 Save/Load schema | spec 62 §3.2 / §6 |
| 새 노드 타입 추가 | `canvas/nodeTypes.ts` |
| 새 편집 동작 추가 | `editing/` 새 컴포넌트 + `ws.ts` 송신 함수 |
