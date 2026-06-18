# palette/ — 노드 라이브러리 / 팔레트 (W4 예정)

**상태**: 자리만 잡음. W4 단계 (spec 62 §7) 에서 채움.

**책임**: 좌측 팔레트 → 사용자가 새 노드 (task / branch / join 등) 드래그-인. 자유 빌더.

**의존 (예정)**:
- `editingStore` — drag in 시작 상태
- `ws.ts::sendTodoAdd` — 드롭 시 todo_add 송신
- `canvas/nodeTypes.ts` — 신규 노드 타입 등록

**예정 파일** (W4):
- `NodePalette.tsx` — 좌측 사이드 패널
- `PaletteItem.tsx` — 드래그 가능 노드 아이템
- `useDragNewNode.ts` — drag handler

상세: spec 62 §7 W4 / §4.1 노드 타입.
