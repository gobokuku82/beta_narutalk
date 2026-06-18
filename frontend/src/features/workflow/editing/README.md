# editing/ — 편집 동작 layer

W2 (시각적 편집) 단계 — Stage 2~6 에서 채움.

**책임**: 사용자의 시각적 편집 동작 (우클릭 / 더블클릭 / toolbar) 을 받아 ws.ts 송신으로 변환. UI 컴포넌트 + ws 송신 hook.

**의존**: `useExecution.plan` (read-only), `useExecution.isPaused`, `editingStore`, `ws.ts`.

**규칙**: `editing/` → `canvas/` 의존 OK. 역방향 금지 (canvas 는 편집을 모름).

**예정 파일** (Stage 4~6):
- `ContextMenu.tsx` — 노드 우클릭 메뉴 (삭제 / 수정)
- `PropertyPanel.tsx` — 노드 더블클릭 속성 편집 sheet
- `EditToolbar.tsx` — 캔버스 toolbar (+ 단계 추가 / 선택 삭제)
- `useWorkflowEditing.ts` — 콜백 → ws 송신 hook

상세: [ADR-012](../../../../docs/agent_specs/adr/ADR-012_workflow_canvas_w2_structure.md).
