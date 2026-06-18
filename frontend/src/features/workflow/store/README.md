# store/ — 편집 임시 상태

**책임**: 편집 중 사용자 UI 임시 상태 (선택 노드 / 컨텍스트 메뉴 위치 / 속성 패널 열림 등). 서버 진실 캐시 (`useExecution.plan`) 와 분리.

**의존**: zustand 만.

**예정 파일** (Stage 2):
- `editingStore.ts` — `selectedNodeId / propertyPanelOpen / contextMenu / applyMode`

**왜 별도 store 인가**:
- `useExecution.plan` = 백엔드가 emit 한 plan 의 캐시. 진실 소스.
- `editingStore` = 사용자가 *지금 무엇을 선택했는지* 같은 UI 임시 상태. turn 끝나면 reset.
- 두 책임을 한 store 에 섞으면 *서버 상태* vs *UI 상태* 가 혼동되어 reset 정책이 복잡해짐.

상세: [ADR-012](../../../../docs/agent_specs/adr/ADR-012_workflow_canvas_w2_structure.md) §1.3 §3 — Alt D 기각 근거.
