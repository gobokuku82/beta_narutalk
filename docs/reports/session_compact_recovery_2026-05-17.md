# 세션 Compact 복구 가이드 (2026-05-17) — 상세 100% 버전

> **다음 세션 진입 시 이 문서를 첫 번째로 읽고, §13 의 진입 액션부터 시작하세요.**
> 본 문서는 *압축 없이* 작성 — 특히 §6~§10 (Workflow 수정 관련) 은 작업 결과를 빠짐없이 박제.

---

## 0. 세션 한 줄 요약

`ws_contract` 머지 → mock data hotfix → ADR-012 Workflow W2 시각 편집 완료 → **ADR-013 W2' (엣지/드래그/batched) Stage 0~3 진행 중, Stage 4~7 남음**. 사용자 중간 검증 대기.

---

## 1. 현재 git 상태

| 항목 | 값 |
|------|------|
| 브랜치 | `main` |
| 최신 commit | `c43f57d` (W2' Stage 3 노드 드래그) |
| Working tree | (본 복구 문서 commit 후) clean |
| origin/main | 이번 세션 신규 25+ commit 누적, push 안 함 (사용자 결정) |
| ws_contract 브랜치 | 유지 (이미 머지됨, 삭제 안 함) |

## 2. 누적 commit 전수 (시간 순)

### 2.1 ws_contract 브랜치 (ADR-011 ConnectionManager 채널 분리)

| commit | 내용 |
|--------|------|
| `15b4c08` | docs(adr): ADR-011 ConnectionManager 채널 분리 — Stage 0 (Proposed) |
| `8ed6ce5` | docs(spec): spec 21 v1.5 초안 — Stage 0 (ADR-011 정합) |
| `7b72137` | test(connection_manager): Stage 1-1 RED — 채널 분리 단위 테스트 16건 신규 |
| `201f585` | test(integration): Stage 1-3 RED — 이중 채널 dedup 통합 테스트 4건 신규 |
| `3416c97` | test(contract): Stage 1-4 RED — spec 21 v1.5 §3.2 카탈로그 contract 4건 |
| `a7cfff2` | feat(connection_manager): Stage 2 GREEN — (user_id, channel) 채널 분리 구현 |
| `979e456` | feat(api_v2): Stage 3 호출부 점진 갱신 — channel 인자 추가 (ADR-011) |
| `817fb36` | docs(specs): Stage 4 — ADR-011 ConnectionManager 채널 분리 문서 정합 |
| `8df93e7` | fix(agent): SideChatPanel 순서 — ChatTodoCard 를 마지막 user 메시지 직후 inline |
| `5631e64` | docs(adr): ADR-011 Accepted — Stage 5 통과 + Stage 6 순서 fix 동반 |
| **`c9819f8`** | **Merge ws_contract: ADR-011 ConnectionManager 채널 분리 + Phase 1 UX 정정** (no-ff merge commit) |

### 2.2 main 직접 hotfix (mock data % suffix)

| commit | 내용 |
|--------|------|
| `b5950bd` | feat(mock-data): % suffix string → float 일관 변환 (CSV 비일관성 흡수) |
| `f41bedf` | refactor(schemas): mock ab-tests + funnel KPI = number 단일 (백엔드 변환과 정합) |

### 2.3 ADR-012 Workflow W2 (main 직접)

| commit | Stage | 내용 |
|--------|-------|------|
| `cd81755` | Stage 0 | docs(adr): ADR-012 Workflow Canvas W2 — Stage 0 (Proposed) |
| `cfa1dfb` | Stage 1 | refactor(workflow): W2 진입 전 layer 분리 (canvas/editing/library/palette) |
| `fa8ebf8` | Stage 2 | feat(workflow): editingStore + Canvas 이벤트 인터페이스 + computeCanEdit |
| `9189fd8` | Stage 3 | feat(workflow): ws 송신 3개 + useWorkflowEditing hook |
| `cf39f3c` | Stage 4 | feat(workflow): ContextMenu (우클릭 삭제/수정, W2 첫 인터랙션) |
| `1fc6876` | Stage 5 | feat(workflow): PropertyPanel (노드 더블클릭 속성 편집) |
| `217cb00` | Stage 6 | feat(workflow): EditToolbar + cascade tint + 비-paused 안내 |
| `d37b8af` | Stage 7 | docs(specs): spec 62 v1.1 정식 + ADR-012 Accepted |

### 2.4 ADR-013 Workflow W2' (main 직접, **진행 중 Stage 0~3 완료**)

| commit | Stage | 내용 | 상태 |
|--------|-------|------|------|
| `7fe211d` | Stage 0 | docs(adr): ADR-013 Workflow W2' 엣지/드래그/batched — Stage 0 (Proposed) | ✅ 완료 |
| `3eed7d1` | Stage 1 | feat(workflow): W2' Stage 1 — 엣지 연결/끊기 핸들러 + 송신 매핑 | ✅ 완료 |
| `c69059c` | Stage 2 | feat(workflow): W2' Stage 2 — cycle 사전 차단 (DFS) + sonner 안내 | ✅ 완료 |
| `c43f57d` | Stage 3 | feat(workflow): W2' Stage 3 — 노드 드래그 (position 변경 + debounce 300ms) | ✅ 완료 |
| (없음) | Stage 4 | issues UX (hitl_ack.issues → sonner) | ⏳ 다음 |
| (없음) | Stage 5 | editingStore.pendingOps + applyMode 토글 | ⏳ |
| (없음) | Stage 6 | batched UI (BatchedToolbar + 시각화 + apply/cancel) | ⏳ |
| (없음) | Stage 7 | spec 62 v1.2 정식 + ADR Accepted + E2E | ⏳ |

---

## 3. 사용자 명시 핵심 결정 사항 (잊으면 안 됨)

### 3.1 3 워크플로우 고려사항 (사용자 직접 명시)

> 1. **단순하고 쉽게 구성이 가능하다**
> 2. **사용자 맞춤형으로 복잡하게 구현 가능하다**
> 3. **각 작업의 의존성이 명확해야 한다**

### 3.2 계획서 §9 핵심 4 질문 (2026-05-17 확정, 사용자 권장 그대로)

| Q | 결정 |
|---|------|
| **(1)** Phase 진행 | **4 Phase 전부, 순서 W2' → W5 → W3 → W4** |
| **(2)** 동기화 default | **사용자 토글 default=immediate** (초보 단순 + 고급 시 batched 진입) |
| **(3)** W4 branch/join | **W4 후속 분리** (W4 진입 시는 팔레트 + task 노드 자유 추가까지만) |
| **(4)** ADR 분리 | **Phase 별** — ADR-013 (W2') / ADR-014 (W3) / ADR-015 (W4) / ADR-016 (W5, 옵션) |

### 3.3 batched 모드 사용자 의도

사용자가 묻기 시작한 시점 = W2 실사용 후. 가치 = *실험적 편집* (여러 노드 옮기고 / 추가하고 / 삭제하고 → "한꺼번에 적용 또는 취소"). 채팅창은 안정 상태 유지, 워크플로우는 디자이너 환경.

→ 채택 방향: 사용자 토글, default=immediate, batched 진입 시 EditToolbar 의 toggle. clas N 회 송신 (백엔드 batch endpoint 신설 X — POC 단계).

### 3.4 사용자 가능성 (엣지 잇기 미구현 발견)

사용자 W2 사용 중 *직접 발견* — 노드끼리 선 잇는 작업 미구현. → W2' (ADR-013) 핵심 동기.

---

## 4. ⚠️ 중요 audit 정정 (잊으면 안 됨)

이전 audit 에서 *틀린 가정* — 다음 세션에서 *같은 실수 방지*:

### 4.1 시각 편집 ↔ NL 편집 책임 분리

| 경로 | 처리 위치 | 처리 범위 |
|------|---------|---------|
| **시각 편집** (todo_modify/delete/add) | `HITLManager.handle_todo_edit/delete/add → TodoManager.modify_todo` | **모든 필드 통과** — `for key, value in changes.items(): todo[key] = value` + `_rebuild_dag` 자동 호출 |
| **NL 편집** (todo_edit_nl) | `HITLManager → plan_editor.apply_edit` (LLM 파싱) | `task/rationale/tool/priority/agent` **만** |

→ **시각 편집의 백엔드 변경 = 0**. depends_on / position / tool_params / task_type / node_type **모두 이미 처리**.

→ ADR-012 의 "백엔드 변경 0" 가정 = **정확**. (이전 audit 에서 "백엔드 plan_editor 가 depends_on 미처리" 라고 적은 건 *NL 편집 한정* 이었음).

### 4.2 W2' 의 추가 점검 3건 (audit 부산물)

1. **issues UX 누락** — `TodoManager.validate` 가 `_detect_cycle` 등으로 `issues: list[str]` 반환 → `hitl_ack.data.issues` 로 emit. 현 프론트는 *무시*. → Stage 4 에서 sonner 토스트 추가.
2. **tool_params merge 경계** — `TodoManager.modify_todo` 는 `tool_params` 만 *merge* (덮어쓰기, 키 삭제 불가). PropertyPanel 의 "전체 교체" 의도와 불일치. → POC 정책 = merge 유지 + 사용자 안내. 향후 별도 ADR.
3. **position cascade** — position 변경은 DAG 무관 → `calculate_cascade` 결과 빈 배열이어야. 단위 테스트로 검증 (Stage 3 후속).

### 4.3 W3/W4 백엔드 실제 미지원 (audit 정정 후도 유효)

| 동작 | 위치 | 현재 |
|------|------|------|
| `MemoryManager.save_workflow_template / load_workflow_template / apply_template_with_params` | 신규 | ❌ 메서드 자체 없음 (W3 진입 시 작성) |
| `memory_entries.type='workflow_template'` | DB CHECK constraint | ❌ enum 확장 마이그레이션 필요 (W3) |
| W4 branch/join 노드의 Execution routing | 신규 | ❌ (Q4 권장 = W4 후속 분리) |

---

## 5. 핵심 참조 파일 (다음 세션 자주 봄)

### 5.1 계획 / 결정 문서

| 파일 | 역할 | 상태 |
|------|------|------|
| [docs/_claude/workflow_advanced_plan_2026-05-16.md](docs/_claude/workflow_advanced_plan_2026-05-16.md) | W2'/W3/W4/W5 고도화 계획서 | gitignored, §9 4 질문 박제, audit 정정 |
| [docs/_claude/workflow_user_guide_2026-05-17.md](docs/_claude/workflow_user_guide_2026-05-17.md) | **사용자 가이드 + 검증 체크리스트** | gitignored, 30+ 체크리스트 (E-1~M-1), 3 고려사항 매트릭스, 코딩 정합 확인 |
| [docs/agent_specs/adr/ADR-013_workflow_w2_prime_edge_drag_batched.md](docs/agent_specs/adr/ADR-013_workflow_w2_prime_edge_drag_batched.md) | W2' 결정 — 8 Stage 분해 | Proposed |
| [docs/agent_specs/adr/ADR-012_workflow_canvas_w2_structure.md](docs/agent_specs/adr/ADR-012_workflow_canvas_w2_structure.md) | W2 결정 — 4 layer + paused 게이트 | Accepted |
| [docs/agent_specs/adr/ADR-011_connection_channel_separation.md](docs/agent_specs/adr/ADR-011_connection_channel_separation.md) | WS 채널 분리 | Accepted |
| [docs/agent_specs/62_workflow_canvas_design_v1.1.md](docs/agent_specs/62_workflow_canvas_design_v1.1.md) | spec 62 — W2 본문 정합 (W2' 본문은 Stage 7 에서 v1.2) | Active |
| [docs/agent_specs/21_WEBSOCKET_PROTOCOL_v1.5.md](docs/agent_specs/21_WEBSOCKET_PROTOCOL_v1.5.md) | spec 21 — 채널 분리 정합 | Active |
| [docs/agent_specs/15_end_to_end_flow_v1.0.md](docs/agent_specs/15_end_to_end_flow_v1.0.md) | spec 15 — 신규 입사자 first read | Active |
| [docs/agent_specs/INDEX.md](docs/agent_specs/INDEX.md) | spec 인덱스 | 갱신됨 |
| [docs/agent_specs/adr/INDEX.md](docs/agent_specs/adr/INDEX.md) | ADR 인덱스 | 갱신됨 |

### 5.2 W2/W2' 프론트 코드 (편집 가능 영역)

| 파일 | 역할 |
|------|------|
| `frontend/src/features/workflow/WorkflowPage.tsx` | 라우트 진입 + Canvas 콜백 조립 + cycle 사전 차단 + position debounce |
| `frontend/src/features/workflow/canvas/WorkflowCanvas.tsx` | React Flow 래퍼 — 6 콜백 (select/contextMenu/doubleClick/edgeConnect/edgeClick/dragEnd) |
| `frontend/src/features/workflow/canvas/NodeComponent.tsx` | 노드 카드 + cascade tint (🔴 + ⛓) |
| `frontend/src/features/workflow/canvas/nodeTypes.ts` | React Flow NodeTypes 매핑 (taskNode 만, W4 에서 확장) |
| `frontend/src/features/workflow/editing/ContextMenu.tsx` | 우클릭 메뉴 (수정/삭제 2 항목) |
| `frontend/src/features/workflow/editing/PropertyPanel.tsx` | shadcn Sheet (rationale/agent/tool/tool_params) |
| `frontend/src/features/workflow/editing/EditToolbar.tsx` | + 단계 추가 / 선택 삭제 |
| `frontend/src/features/workflow/editing/useWorkflowEditing.ts` | 편집 hook — 5 store 액션 + 5 ws 송신 함수 |
| `frontend/src/features/workflow/editing/cycleGuard.ts` | DFS cycle 검증 (Stage 2 신규) |
| `frontend/src/features/workflow/store/editingStore.ts` | zustand — selectedNodeId / propertyPanelOpen / contextMenu / applyMode |
| `frontend/src/features/workflow/README.md` | 4 layer 의존 규칙 가이드 |

### 5.3 백엔드 (audit 정합 — *변경 금지*, 참조만)

| 파일 | 역할 |
|------|------|
| `backend/api_v2/ws_hitl.py` | WS endpoint — `_handle_todo_modify/delete/add` (paused 가드 + Lock + ack) |
| `backend/app/dream_agent/workflow_managers/hitl_manager/manager.py:410-560` | HITLManager PM 역할 — `handle_todo_edit/delete/add` (TodoManager 위임) |
| `backend/app/dream_agent/workflow_managers/todo_manager/manager.py` | TodoManager 작업자 — `modify_todo/delete_todo/add_todo` (모든 필드 통과) / `calculate_cascade` / `validate (_detect_cycle)` / `_build_phases_from_plan` |
| `backend/app/dream_agent/workflow_managers/hitl_manager/plan_editor.py` | NL 편집 전용 (LLM 파싱, modify 시 일부 필드만) — 시각 편집 경로 X |
| `backend/api_v2/connection_manager.py` | ADR-011 — `(user_id, channel)` 자료구조 |
| `backend/api_v2/routes/mock_data.py` | mock data — `_coerce_percent` 헬퍼 추가됨 |

### 5.4 zod schema / ws 송신

| 파일 | 역할 |
|------|------|
| `frontend/src/api/schemas.ts` | WS message schema (spec 21 v1.4 → v1.5 정합) + mock row schema (% suffix 정정) |
| `frontend/src/api/ws.ts` | ws 클라이언트 + 5 송신 함수 (sendQuery / sendPause/Resume/Cancel/TodoEditNl + sendTodoModify/Delete/Add) |
| `frontend/src/api/hooks/useWebSocket.ts` | useWebSocket + fanout (agent + hitl) |
| `frontend/src/api/hooks/useMockData.ts` | 12 mock endpoint hook |

---

## 6. ⭐ Workflow 수정 작업 상세 (압축 X — 100%)

### 6.1 ADR-012 W2 (완료) — 폴더 구조 + 5 컴포넌트

**4 layer 폴더 구조** (`features/workflow/`):
```
canvas/   — 시각화만, 편집 모름
editing/  — 편집 동작 + ws 송신
store/    — 편집 임시 UI 상태 (selectedNodeId 등)
library/  — W3 자리 (Save/Load)
palette/  — W4 자리 (노드 빌더)
```

**의존 규칙** (단방향): editing → canvas (역방향 금지) / editing → store / canvas 는 콜백으로만 emit / store 는 zustand only

**5 컴포넌트** (Stage 4~6 완성):

#### ContextMenu (우클릭)
- 위치: editing/ContextMenu.tsx
- 트리거: 노드 우클릭 (editable 시)
- 항목: 수정 (`openPropertyPanel`) / 삭제 (`deleteTodo` → ws sendTodoDelete)
- 외부 클릭 / ESC 로 닫힘
- aria role=menu/menuitem

#### PropertyPanel (더블클릭)
- 위치: editing/PropertyPanel.tsx
- 트리거: 노드 더블클릭 또는 ContextMenu "수정"
- UI: shadcn Sheet 우측 슬라이드
- 필드: rationale (textarea) / agent (input) / tool (input) / tool_params (textarea JSON)
- 저장: 바뀐 필드만 changes dict → modifyTodo → ws sendTodoModify
- 변경 없으면 닫음만 (no-op)
- tool_params JSON 파싱 — 잘못된 형식 inline error
- 불변 필드 (id/task_type/depends_on/node_type) 는 readonly 표시

#### EditToolbar (캔버스 toolbar)
- 위치: editing/EditToolbar.tsx
- 위치 (DOM): canvas 우측 상단 absolute
- 버튼:
  - + 단계 추가 → addTodo({task_type:"custom", depends_on:[], ...})
  - 🗑 선택 삭제 → selectedNodeId 있을 때 deleteTodo
- editable=false 면 null 반환 (안 보임)

#### NodeComponent (cascade tint)
- 위치: canvas/NodeComponent.tsx
- isInvalidated=true 면 ring-destructive/60 + bg-destructive/5 + ⛓ "cascade" 배지

#### useWorkflowEditing (편집 hook)
- 위치: editing/useWorkflowEditing.ts
- store 액션 wrapping (선언적 콜백) + ws 송신
- 5 액션: openContextMenu / closeContextMenu / openPropertyPanel / closePropertyPanel / selectNode
- 5 송신: deleteTodo / modifyTodo / addTodo / **connectEdge** (Stage 1) / **disconnectEdge** (Stage 1)
- turnId 가드: 없으면 모두 no-op false

**paused 게이트**:
```ts
// useExecution/store.ts
export function computeCanEdit(isPaused: boolean, turnId: string | null): boolean {
  return isPaused && !!turnId;
}
```
WorkflowPage 가 `editable = computeCanEdit(isPaused, turnId)` → Canvas / EditToolbar 에 전달.

**cascade 시각화**:
- 백엔드 emit: `hitl_ack.data.invalidated = [downstream_ids]`
- 프론트: `useHitl.cascadeResult.invalidated` → WorkflowPage → `WorkflowCanvas.invalidatedIds` → `nodes.data.isInvalidated` → NodeComponent 🔴

**empty-state 안내**:
- hasPlan && !editable 일 때 헤더 아래 배너
- "편집은 일시정지 상태에서 가능합니다. 채팅창에서 [⏸ 중지] 를 눌러..."

### 6.2 ADR-013 W2' Stage 1 상세 — 엣지 연결/끊기

#### WorkflowCanvas Props 확장
```tsx
onEdgeConnect?: (source: string, target: string) => void
onEdgeClick?: (edge: Edge) => void
```

#### ReactFlow props
```tsx
nodesConnectable={editable}  // ← Stage 1 변경
onConnect={(c: Connection) => {
  if (!editable) return;
  if (!c.source || !c.target || c.source === c.target) return;  // self-loop 즉시 차단
  onEdgeConnect?.(c.source, c.target);
}}
onEdgeClick={(_e, edge: Edge) => {
  if (!editable) return;
  onEdgeClick?.(edge);
}}
```

#### useWorkflowEditing.connectEdge
```ts
connectEdge(source: string, target: string): boolean
  - turnId 없으면 false (no-op)
  - useExecution.plan 없으면 false
  - targetTodo lookup (없으면 false)
  - 이미 의존이면 no-op true (송신 X)
  - 새 의존이면 sendTodoModify(turnId, target, { depends_on: [...existing, source] })
```

#### useWorkflowEditing.disconnectEdge
```ts
disconnectEdge(source: string, target: string): boolean
  - turnId / plan / targetTodo 가드 동일
  - depends_on 에 source 없으면 no-op true
  - 있으면 sendTodoModify(turnId, target, { depends_on: existing.filter(!=source) })
```

#### WorkflowPage 통합
```tsx
onEdgeConnect={(source, target) => {
  // Stage 2 에서 cycle 사전 차단 추가됨 — 아래 §6.3 참조
  connectEdge(source, target);
}}
onEdgeClick={(edge) => {
  if (window.confirm(`의존성 끊기: ${edge.source} → ${edge.target} ?`)) {
    disconnectEdge(edge.source, edge.target);
  }
}}
```

#### 테스트 (useWorkflowEditing.test.ts 신규 6 케이스)
1. connectEdge — turnId 없으면 false
2. connectEdge — plan 없으면 false
3. connectEdge — 이미 존재면 no-op true
4. connectEdge — 새 의존이면 [기존, source] 송신
5. disconnectEdge — 정상 제거 후 송신
6. disconnectEdge — 의존 없으면 no-op true

SAMPLE_PLAN fixture 추가 (todo_001 → todo_002 사슬).

### 6.3 ADR-013 W2' Stage 2 상세 — Cycle 사전 차단

#### cycleGuard.ts 핵심 알고리즘

```ts
export function wouldAddEdgeCreateCycle(plan, source, target): boolean {
  if (source === target) return true; // self-loop
  const childrenMap = buildChildrenMap(plan.todos);
  // target 부터 descendants BFS — source 만나면 cycle
  const visited = new Set();
  const queue = [target];
  while (queue.length > 0) {
    const cur = queue.shift()!;
    if (visited.has(cur)) continue;
    visited.add(cur);
    const children = childrenMap.get(cur);
    if (!children) continue;
    for (const child of children) {
      if (child === source) return true;
      queue.push(child);
    }
  }
  return false;
}
```

**의미 모델 (핵심 — 잊으면 안 됨)**:
- 엣지 source → target = "source 실행 후 target 실행" (실행 흐름 방향)
- schemas 표현: `target.depends_on` 에 source 포함
- 새 엣지 추가 후 cycle 조건 = 기존 그래프에서 *target → ... → source* 경로 존재
- → target 부터 descendants 탐색 → source 도달하면 cycle

**알고리즘 정정 이력 (Stage 2 RED→GREEN)**:
- 첫 시도: "source 부터 descendants 탐색 → target 찾기" → 8 fail
- 정정: "target 부터 descendants 탐색 → source 찾기" → 12 pass

#### 테스트 12 케이스 (cycleGuard.test.ts)
- self-loop
- 빈 의존 그래프 A → B 안전
- 단순 사슬 A → B 존재, B → A 추가 = cycle
- 단순 사슬, A → B 다시 추가 = 안전 (중복)
- 긴 사슬 A→B→C, C → A 추가 = cycle (transitive)
- 긴 사슬, A → C 추가 = 안전 (shortcut)
- 병렬 분기 + D → A = 안전 (D 신규 root)
- 병렬 분기 + B → A = cycle
- Y 모양 C → A = cycle
- Y 모양 + 무관 노드 C → D = 안전
- Diamond D → A = cycle
- Diamond A → D = 안전 (shortcut)

#### WorkflowPage 의 사전 차단
```tsx
onEdgeConnect={(source, target) => {
  if (plan && wouldAddEdgeCreateCycle(plan, source, target)) {
    toast.error(`순환 의존 — ${source} → ${target} 연결 시 cycle 이 생깁니다.`);
    return;
  }
  connectEdge(source, target);
}}
```

### 6.4 ADR-013 W2' Stage 3 상세 — 노드 드래그 (position)

#### WorkflowCanvas
```tsx
onNodeDragEnd?: (nodeId: string, position: { x: number; y: number }) => void

// ReactFlow:
nodesDraggable={editable}  // Stage 1 보류 해제
onNodeDragStop={(_e, n: RFNode) => {
  if (!editable) return;
  onNodeDragEnd?.(n.id, { x: n.position.x, y: n.position.y });
}}
```

#### WorkflowPage debounce 패턴
```tsx
const dragTimersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

const handleNodeDragEnd = useCallback(
  (nodeId: string, position: { x: number; y: number }) => {
    const timers = dragTimersRef.current;
    const existing = timers.get(nodeId);
    if (existing) clearTimeout(existing);
    const t = setTimeout(() => {
      modifyTodo(nodeId, { position });
      timers.delete(nodeId);
    }, 300);
    timers.set(nodeId, t);
  },
  [modifyTodo],
);
```

같은 nodeId 의 연속 드래그는 마지막 위치만 송신.

#### 백엔드 (변경 0)
- TodoManager.modify_todo 가 changes 의 모든 key 통과 → `todo.position = {x, y}` plan dict 에 저장.
- dagre 의 planToFlow 가 todo.position 있으면 그것을 우선 ([lib/dagre.ts:44](frontend/src/lib/dagre.ts#L44)).

### 6.5 ⏳ Stage 4~7 남은 작업 상세

#### Stage 4 — issues UX (예상 ~50 줄 / 30분)

**파일**: `frontend/src/features/hitl/store.ts` 확장

```ts
// useHitl.handleWSMessage('hitl_ack') 분기:
case 'hitl_ack': {
  const ack = msg.data;
  set((s) => ({
    cascadeResult: ack,
    pending: ...,
  }));
  // 신규 — issues 있으면 사용자 안내
  if (Array.isArray(ack.issues) && ack.issues.length > 0) {
    import('sonner').then(({ toast }) => {
      ack.issues.forEach((msg) => toast.warning(msg));
    });
    // 또는 묶음: toast.warning(ack.issues.join(' / '));
  }
  break;
}
```

**테스트**: store.test.ts 에 케이스 추가 — issues 있을 때 mock toast 호출.

#### Stage 5 — editingStore.pendingOps + applyMode 토글 (~80 줄)

**파일**: `frontend/src/features/workflow/store/editingStore.ts` 확장

```ts
// 신규 타입:
export type PendingOp =
  | { kind: 'delete'; todoId: string }
  | { kind: 'modify'; todoId: string; changes: Record<string, unknown> }
  | { kind: 'add'; todo: PartialTodo };

// State 추가:
pendingOps: PendingOp[];
addPendingOp: (op: PendingOp) => void;
clearPendingOps: () => void;

// 동작:
- applyMode==='immediate' (default): 기존 동작 — useWorkflowEditing 이 즉시 ws 송신
- applyMode==='batched': useWorkflowEditing 이 pendingOps 에 push 만, ws 송신 X
- "변경 적용" → pendingOps 순회 N 회 ws 송신 + clearPendingOps
- "취소" → clearPendingOps + WorkflowCanvas 가 서버 plan 으로 자연 reset (이미 useExecution.plan 구독)
```

**useWorkflowEditing 변경**: deleteTodo/modifyTodo/addTodo 가 applyMode 확인 후 분기:
```ts
const deleteTodo = useCallback((todoId: string): boolean => {
  const turnId = useSession.getState().turnId;
  if (!turnId) return false;
  const applyMode = useEditingStore.getState().applyMode;
  if (applyMode === 'batched') {
    useEditingStore.getState().addPendingOp({ kind: 'delete', todoId });
    return true;
  }
  return sendTodoDelete(turnId, todoId);
}, []);
```

#### Stage 6 — batched UI (~170 줄)

**파일**: `frontend/src/features/workflow/editing/BatchedToolbar.tsx` 신규

- editingStore.pendingOps 카운트 표시 — "변경 N건"
- "변경 적용" 버튼 — applyAll 호출 → for-of pendingOps + sendTodoXxx
- "취소" 버튼 — clearPendingOps
- applyMode toggle (immediate ↔ batched)

**파일**: `WorkflowCanvas.tsx` 또는 NodeComponent — 로컬 시각화
- 변경 대기 노드: ✏ 배지 (modify)
- 삭제 대기 노드: 회색 + 점선 (delete)
- 신규 대기 노드: + 배지 (add)

**시나리오 — batched 중 turn 종료 / NL 편집 발생**:
- useExecution.handleWSMessage 의 complete / hitl_ack(nl_action='...') 분기에서 editingStore.reset() 호출 + 안내 토스트.

#### Stage 7 — 마무리 (~70 줄 + 문서)

1. `spec 62 v1.1` → `legacy/` 백업
2. `spec 62 v1.2` 신규 — §5.7 엣지/드래그 동작 매핑 + §5.8 batched 모드 + §5.9 cycle 사전 차단 본문
3. `ADR-013` Status: Proposed → Accepted
4. `adr/INDEX.md` 변경 이력
5. spec 62 stale 링크 sed (5 파일)
6. INDEX.md 변경 이력
7. 사용자 E2E 검증 시나리오 W2'-A~G + batched (S-B-01~05)

---

## 7. W2' 사용자 검증 시나리오 (다음 세션 첫 동작 — 결과 받기)

| # | 시나리오 | 절차 | 기대 |
|---|---------|------|------|
| **W2'-A** | 엣지 연결 | paused 상태에서 노드 source Handle (아래) → 다른 노드 target Handle (위) drag | 새 엣지 등장 + 백엔드 ack 후 ChatTodoCard 갱신 |
| **W2'-B** | 엣지 끊기 | 엣지 클릭 → confirm | 엣지 사라짐 |
| **W2'-C** | cycle 차단 | A → B 존재할 때 B → A drag | 빨간 sonner 토스트 "순환 의존" + 엣지 안 만들어짐 |
| **W2'-D** | self-loop | 같은 노드 Handle 내 drag | 차단 |
| **W2'-E** | 노드 드래그 | 노드 잡아 끌고 다른 위치에 drop | 300ms 후 ws 송신 → position 저장 |
| **W2'-F** | 빠른 연속 드래그 | 한 노드을 여러 번 빠르게 옮김 | 마지막 위치만 송신 (debounce) |
| **W2'-G** | 비-paused 모드 | 일시정지 아닌 상태에서 위 동작들 시도 | 모두 비활성 (firing 안 됨) |

## 8. 회귀 테스트 기준 (매 Stage 4종) — 다음 세션도 유지

| 종류 | 명령 | 현재 통과 수 |
|------|------|-----------|
| typecheck | `pnpm typecheck` | TS strict pass |
| build | `pnpm build` | noUncheckedIndexedAccess pass |
| vitest | `pnpm vitest run` | **40/40** |
| 백엔드 | `uv run pytest backend/tests/sprint13/ backend/tests/sprint15/` | **191/191** (6 deselected = live) |

각 Stage 끝마다 **4종 모두 통과** 후 commit.

### 현재 vitest 구성 (40)
- src/features/hitl/store.test.ts — 7
- src/features/workflow/store/editingStore.test.ts — 7
- src/features/workflow/editing/useWorkflowEditing.test.ts — 14 (기본 8 + Stage 1 신규 6)
- src/features/workflow/editing/cycleGuard.test.ts — 12

---

## 9. 환경 / 인프라

| 항목 | 상태 |
|------|------|
| 백엔드 (8001) | 사용자 직접 띄움 (이전 task `b8jqw13dw` 는 stopped) |
| 프론트 (5173) | 사용자 직접 띄움 (Vite HMR) |
| PostgreSQL | 로컬 localhost:5432, 정상 — `postgresql://postgres:root1234@localhost:5432/adal` |
| `.env` | OPENAI_API_KEY / CHECKPOINT_DB_URI / DATABASE_URL 모두 설정 |

다음 세션 진입 시 환경 재확인:
```bash
curl -s -m 3 -o /dev/null -w "8001=%{http_code} 5173=" http://localhost:8001/health
curl -s -m 3 -o /dev/null -w "%{http_code}\n" http://localhost:5173/
```

---

## 10. 사용자 작업 패턴 (잊으면 안 됨 — 동일 패턴 유지)

기존 memory + 본 세션 확인:

- **TDD 우선** — 단축/skip 제안 X. timeout 충분히. 변경 모듈 + 인접 모듈 회귀 검증 필수.
- **멀티 사이클 검증** — 코드 변경 전 ADR + spec 초안. 사용자 검증 후 진입.
- **Atomic commit** — Stage 1개 = commit 1개 원칙 (예외: ADR + spec 분리).
- **main 직접 작업 + 매 Stage 4종 회귀** — ADR-012 부터 채택. broken state 방지.
- **계획서 → ADR → spec → 코드 흐름**.
- **확장/변경 용이성이 schema 결정보다 우선** (memory).
- **UI = "AI 만든 티" 금지** — 액센트 1개. 색 결정 전 실제 제품 디자인 시스템 조사.

### 8 Stage TDD 패턴 (ADR-011/012/013 동일)
- Stage 0: ADR + spec 초안 + INDEX
- Stage 1~N: 코드 변경 (RED → GREEN 또는 점진 갱신)
- Stage N+1: spec 정식 + ADR Accepted + E2E

---

## 11. 시각 편집 ↔ NL 편집 흐름 도식 (잊지 말 것)

```
시각 편집 (W2/W2')                        NL 편집 (ADR-002 1차)
─────────────────                       ─────────────────
[프론트] ContextMenu / PropertyPanel    [프론트] PauseBox 자연어 textarea
        EditToolbar / drag / connect
  ↓                                       ↓
ws.sendTodoModify/Delete/Add            ws.sendTodoEditNl
  ↓ /ws/hitl                             ↓ /ws/hitl
ws_hitl._handle_todo_modify/...         ws_hitl._handle_todo_edit_nl
  ↓                                       ↓
HITLManager.handle_todo_edit/...        HITLManager → plan_editor
  (PM 조율자)                              (LLM 파싱)
  ↓                                       ↓
TodoManager.modify_todo/...             plan_editor.apply_edit
  ↓ 모든 필드 통과                          ↓ task/rationale/tool/priority/agent 만
  ↓ + _rebuild_dag 자동
  ↓
계산: calculate_cascade / validate (issues)
  ↓
hitl_ack { plan, invalidated, issues, ... }
  ↓
[프론트] useExecution.setPlan + useHitl.cascadeResult
```

**책임 분리 본질**:
- TodoManager = 데이터 변경 (deterministic, 모든 필드)
- plan_editor = LLM 해석 (probabilistic, 일부 필드)
- HITLManager = 조율 (가드 + Lock + 흐름)

---

## 12. ADR-014/015/016 진입 시 참조 사항 (W2' 끝나면 — 다음 다음 세션 가능)

| Phase | 작업 시점 | ADR | 주요 |
|-------|---------|-----|------|
| **W5** | W2' 다음 (Q1 결정) | ADR-016 (옵션) | 의존성 시각화 강화 — Phase 박스 / critical path / 실행 상태 색 / 타임라인 토글 |
| **W3** | W5 다음 | ADR-014 | Save / Load — MemoryManager + DB 마이그레이션 (workflow_template enum) + param_slots |
| **W4** (팔레트만) | W3 다음 | ADR-015 | 노드 팔레트 + drag-in (task 노드 자유 추가까지) |
| W4 (branch/join 후속) | W4 다음 | ADR-015 후속 또는 ADR-017 | Execution routing — 백엔드 변경 큼 |

각 진입 시 동일 8 Stage TDD 패턴. 계획서 (`docs/_claude/workflow_advanced_plan_2026-05-16.md`) §3 의 요구사항 참조.

---

## 13. ⭐ 다음 세션 진입 첫 동작

### 13-1. 사용자 응답 가능한 경우 분류

| 사용자 신호 | 다음 작업 |
|------|---------|
| (A) "W2' 검증 정상 / 통과" 또는 "Stage 4 진행" | **Stage 4** (issues UX) 진입 — §6.5 Stage 4 절차 따라감 |
| (B) "W2'-X 가 안 됨" 또는 정정 보고 | hotfix → 재검증 후 Stage 4 |
| (C) "Stage 5/6 (batched) 먼저" | Stage 4 건너뛰고 Stage 5/6 진입 (단 issues UX 는 W2' 마무리 전 후속 처리 명시) |
| (D) "W2' 마무리 / Stage 7" | Stage 7 진입 — 그런데 *Stage 4/5/6 미완* 상태로 Stage 7 진입은 비추. 권장: Stage 4 만 빠르게 마치고 Stage 7 (batched 는 후속 ADR-013.1 으로 분리) |

### 13-2. 첫 메시지 권장 (사용자에게)

> "ws_contract → main merge (ADR-011) + mock hotfix + ADR-012 W2 완료 + ADR-013 W2' Stage 0~3 진행 (엣지 연결/끊기/cycle/노드 드래그). main 최신 = c43f57d. 회귀 vitest 40 / 백엔드 191 통과. 브라우저 W2'-A~G 검증 결과 알려주시면 Stage 4 (issues UX) 또는 Stage 5/6 (batched) 진입."

### 13-3. 진입 후 확인 명령 모음

```bash
# 1. git 상태
cd c:/kdy/Projects/octormate/beta_v001 && git status && git log --oneline -5

# 2. 회귀
cd frontend && pnpm typecheck && pnpm vitest run
cd .. && uv run pytest backend/tests/sprint13/ backend/tests/sprint15/ --no-header --tb=no -q

# 3. 환경
curl -s -m 3 -o /dev/null -w "8001=%{http_code} 5173=" http://localhost:8001/health
curl -s -m 3 -o /dev/null -w "%{http_code}\n" http://localhost:5173/
```

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-05-17 | 초안 — ADR-013 Stage 0~3 완료 시점. 본 문서는 *압축 X 100%* 박제. 시각 편집 ↔ NL 편집 책임 분리 핵심 (§4.1 / §11). 다음 세션 첫 동작 = §13. |
