# 62. Workflow Canvas Design — React Flow 기반 vision H4 UI

| 항목 | 내용 |
|------|------|
| 버전 | **v1.1** |
| 작성일 | 2026-05-12 (v1.0) / 2026-05-16 (v1.1 — W2 구현 상세) |
| 상태 | **Active** (W1 완료 + W2 구현 완료 — Sprint 15 P1) |
| 영역 | 프론트엔드 (60대) — Workflow 시각화 / 편집 / 저장 |
| Vision 매핑 | [00_vision_and_intent.md](00_vision_and_intent.md) — H3 패턴화 / **H4 맞춤화** |
| 관련 spec | [30_DATA_MODELS](30_DATA_MODELS_v1.1.md) (PlannedTodo) / [35_DB_SCHEMA](35_DB_SCHEMA_v1.0.md) (memory_entries) / [21_WEBSOCKET](21_WEBSOCKET_PROTOCOL_v1.5.md) (NL edit 메시지) |
| 관련 ADR | [ADR-002](adr/ADR-002_nl_edit_phased_roadmap.md) NL 점진 / [ADR-010](adr/ADR-010_plan_schema_unification.md) planner.Plan 단일화 / **[ADR-012](adr/ADR-012_workflow_canvas_w2_structure.md) W2 확장형 구조 + paused 게이트** / [ADR-015](adr/) (예정) 메모리+Clarification 통합 |

---

## v1.1 (2026-05-16) 변경점 — W2 구현 완료

ADR-012 의 W2 (시각적 편집) 단계 구현. spec 본문에 다음을 박제:

- **§2.5 확장형 폴더 구조** — `features/workflow/` 의 4 layer (canvas/editing/library/palette) 신규 추가. 의존 규칙 단방향 (editing → canvas).
- **§5.4 paused 게이트** — 백엔드 `_handle_todo_modify/delete/add` 의 `progress.status == "paused"` 요구사항을 프론트가 `computeCanEdit(isPaused, turnId)` 로 사전 차단.
- **§5.5 W2 컴포넌트 카탈로그** — ContextMenu / PropertyPanel / EditToolbar 의 책임/항목/이벤트 매핑.
- **§5.6 자연 동기화** — 편집 결과 = `hitl_ack.plan` → `useExecution.setPlan` 자동 반영. 별도 데이터 갱신 코드 X.
- **§7 Phase 표** — W2 = ✅ 완료 (Sprint 15 P1, 8 Stage TDD).

**호환성**: 본 v1.1 은 *내용 추가만* — 기존 v1.0 의 모든 결정 (3-Panel 제거, NL+시각 편집 공존, param_slots 등) 그대로 유지.

---

## 0. 본 문서의 역할

OctorAD 의 핵심 vision (사용자 ↔ AI 파트너쉽 + 학습 + **맞춤형 에이전트**) 을 UI 로 구현하는 **Workflow Canvas** 의 정식 spec.

n8n / Zapier / Make 같은 노드-엣지 workflow 빌더의 **AI-first 진화 형태**:
- **시작**: 빈 캔버스 X. 사용자 자연어 → AI 자동 생성된 workflow 표시
- **편집**: 시각적 드래그/클릭 ↔ 자연어 명령 ("4번 삭제") 공존
- **저장**: 마음에 든 패턴을 template 으로 → 재사용 (파라미터 슬롯)
- **누적**: 사용 패턴 → 시스템이 학습 (Memory cascade, H3)
- **맞춤화**: 사용자별 자동 제안 (H4)

→ "**AI 가 초안 그려주는 n8n + 패턴 누적해 점점 똑똑해지는 캔버스**"

---

## 1. Vision 매핑 — 가설 H1~H4 의 UI 구체화

[`00_vision_and_intent.md`](00_vision_and_intent.md) 의 가설 사슬과 본 spec 의 대응:

| 가설 | 의미 | Workflow Canvas 의 역할 |
|------|------|------------------------|
| **H0** 의도 모호성 | 사용자가 정확한 의도 표현 어려움 | 자연어 입력 → 시각적 workflow → "이거 맞아?" 즉시 확인 |
| **H1** 발견 | AI 와 대화 중 의도 명확화 | 시각화로 누락 발견 + 시각적 편집 |
| **H2** 학습 | 사용자 패턴 누적 | save 기능 — 반복 작업 template 화 |
| **H3** 패턴화 | 시스템이 사용자 패턴 추출 | "이 사용자는 분석 시 항상 X 패턴" — 자동 제안 |
| **H4** **맞춤화** ⭐ | 사용자별 맞춤형 에이전트 | "신상품 launch" 한 마디로 저장된 패턴 자동 호출 |

→ **Workflow Canvas = H4 맞춤화의 핵심 manifestation**.

---

## 2. 핵심 결정 — 라이브러리 / 패턴

### 2.1 시각화 라이브러리

**선택: `@xyflow/react`** (구 React Flow)

**근거**:
- n8n / Zapier / Make / Flowise / Langflow / Dify — 모든 주요 AI workflow 빌더의 표준
- MIT OSS, 80K+ GitHub stars, 활발한 업데이트
- React 19 + TypeScript first
- 노드 / 엣지 완전 커스터마이즈 + 미니맵 / 줌 / 팬 / 자동 레이아웃 내장

**대안 (검토 후 폐기)**:
| 라이브러리 | 폐기 이유 |
|---|---|
| vis-network | 학술용, 거친 UX |
| Cytoscape.js | 학술 그래프, 편집 약함 |
| D3 + dagre 직접 | 인터랙션 직접 구현 비용 큼 |

### 2.2 자동 레이아웃 알고리즘

**선택: `dagre`** (POC), 향후 `elkjs` 검토

**근거**:
- React Flow 공식 예제에 dagre 통합 패턴 존재 → 학습 비용 낮음
- DAG 구조에 자연 최적화
- AI 가 자연어로 plan 생성 → 노드 위치 자동 배치 → 사용자가 드래그하면 그 위치 저장

### 2.3 레이아웃 — GlobalLayout 의 Outlet 안 (v1.1 정정)

> **변경 (2026-05-13 v1.1)**: 3-Panel 패턴 제거. v1 GlobalLayout 패턴 (TopBar + Sidebar + Outlet + SideChatPanel) 채택. Workflow Canvas 는 **`/workflow` 라우트의 Outlet 콘텐츠** 로 들어감. 자연어 편집은 우측 SideChatPanel 에서.

#### Workflow Canvas 페이지 (`/workflow`) 내부 구조

```
GlobalLayout 의 Outlet:
┌──────────────────────────────────────────────┐
│ Page Header                                   │
│   "워크플로우 ▾" + [💾 저장] [📂 호출] [↩ 자동배치] │
├──────────────────────────────────────────────┤
│                                              │
│  Workflow Canvas (React Flow) — 메인 영역    │
│   ┌─────┐    ┌─────┐    ┌─────┐              │
│   │ t1  │───▶│ t2  │───▶│ t3  │              │
│   └─────┘    └─────┘    └─────┘              │
│                                              │
│  ┌──────────┐                                │
│  │ MiniMap  │ ◀ 우하단                       │
│  └──────────┘                                │
└──────────────────────────────────────────────┘

선택된 노드 있을 때:
→ 우측 Sheet (shadcn) 로 PropertyPanel 슬라이드 인 (or 우상단 panel toggle)
```

→ Workflow Canvas 가 **메인 영역 전체** 차지. 우측 SideChatPanel 은 GlobalLayout 에서 전역.

#### 자연어 편집 위치

| 영역 | 자연어 편집 가능? | 비고 |
|------|:----------------:|------|
| 메인 워크플로우 캔버스 (`/workflow`) | ❌ 직접 X | 우측 SideChatPanel 호출 |
| **우측 SideChatPanel** (GlobalLayout 전역) | ✅ "4번 삭제" 등 NL 입력 | 현재 보는 워크플로우가 컨텍스트로 자동 전달 |
| 노드 우클릭 → 드롭다운 | ✅ 시각적 편집 | 삭제 / 수정 / 추가 |

### 2.4 시각화 vs 자연어 — 공존 UX (v1.1)

```
┌──────┬─────────────────────────────────────┬────────────────────┐
│ Side │  Outlet (= /workflow 페이지)         │ SideChatPanel      │
│ bar  │                                      │  - 메시지 누적     │
│      │  Workflow Canvas                     │  - "4번 삭제"      │
│ -대시│  ┌─────┐  ┌─────┐  ┌─────┐         │    ⚡ 적용         │
│ -소재│  │ t1  │─▶│ t2  │─▶│ t3  │         │  - ack 받으면      │
│ -채널│  └─────┘  └─────┘  └─────┘         │    Canvas 갱신     │
│ -..  │                                      │    (실시간)        │
│ -워크│  + 드래그 / 우클릭 = 시각적 편집     │                    │
│ -메모│                                      │                    │
└──────┴─────────────────────────────────────┴────────────────────┘
```

→ 두 입력 경로 (시각적 + NL) 가 **동시에 가능**. 같은 백엔드 호출 (`_handle_todo_*`).

- **두 입력 경로 모두 같은 백엔드 호출** — `ws_hitl._handle_todo_edit_nl` (자연어) / `_handle_todo_delete/modify/add` (시각적)
- 사용자가 그때그때 편한 방식 선택
- 백엔드 변경 최소화 (기존 메시지 그대로)

### 2.5 확장형 폴더 구조 (v1.1 — ADR-012)

W2 진입 시 평탄 폴더 sprawl 회피 + W3/W4 진입 자리 사전 확보:

```
frontend/src/features/workflow/
├── WorkflowPage.tsx              ← 라우트 진입 (얇음, 조립만)
├── canvas/                       ← 시각화 layer (편집 모름)
│   ├── WorkflowCanvas.tsx        ← React Flow 래퍼 + 이벤트 위임
│   ├── NodeComponent.tsx         ← 노드 카드 (cascade tint 포함)
│   └── nodeTypes.ts              ← React Flow NodeTypes 매핑
├── editing/                      ← 편집 layer (W2)
│   ├── ContextMenu.tsx           ← 노드 우클릭 메뉴
│   ├── PropertyPanel.tsx         ← 노드 더블클릭 속성 sheet
│   ├── EditToolbar.tsx           ← 캔버스 toolbar
│   └── useWorkflowEditing.ts     ← 콜백 → ws 송신 hook
├── store/
│   └── editingStore.ts           ← 편집 임시 UI 상태 (zustand)
├── library/                      ← (W3 예정) Save / Load
│   └── README.md
└── palette/                      ← (W4 예정) 노드 팔레트
    └── README.md
```

**의존 규칙 (단방향)**:
- `canvas/` 는 *순수 시각화* — `useExecution.plan` (read-only) + 부모 콜백만. 편집 모름.
- `editing/` → `canvas/` 의존 OK. 역방향 금지.
- `store/editingStore` 는 *편집 임시 UI 상태* 전담 — `useExecution.plan` (서버 진실 캐시) 와 분리.

**확장 시 수정 위치**:
| 신규 요구 | 추가 위치 |
|---------|--------|
| 새 노드 타입 시각 | `canvas/nodeTypes.ts` + 새 컴포넌트 1개 |
| 새 편집 동작 (예: 엣지 끊기) | `editing/` 새 컴포넌트 + `ws.ts` 송신 함수 |
| 새 시각화 metadata | `PlannedTodo.visualization_meta` (§3.1 — schema 변경 0) |
| Save/Load | `library/` 채움 |
| 노드 라이브러리 | `palette/` 채움 |

상세 의존 규칙: `frontend/src/features/workflow/README.md`.

---

## 3. Schema 확장 — Minimum (사용자 5 원칙 부합)

[35 §0.1 5 원칙](35_DB_SCHEMA_v1.0.md) 적용 — JSONB / Optional / 확장 용이.

### 3.1 PlannedTodo 확장 — 3 Optional 필드

```python
# backend/app/dream_agent/planning/planner.py
class PlannedTodo(BaseModel):
    # 기존 필드
    id: str
    task_type: str
    agent: str | None = None
    tool: str | None = None
    tool_params: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = Field(default_factory=list)
    priority: int = 1
    rationale: str = ""

    # === Workflow Canvas (Sprint 15+) 신규 ===
    position: dict[str, float] | None = None          # {"x": 100, "y": 200}
    node_type: str = "task"                            # task / branch / join / start / end
    visualization_meta: dict[str, Any] = Field(default_factory=dict)  # 자유 영역
```

**원칙 부합**:
- ✅ 모두 Optional → 기존 데이터 무손상
- ✅ String + default → enum 제약 X (새 node_type 추가 자유)
- ✅ JSONB content (visualization_meta) → 향후 시각화 metadata 자유 확장
- ✅ schema_version 영향 X — Pydantic Optional 추가만으로 v1 유지

**migration 영향**: 0 (기존 DB 데이터는 None / default 로 자연 채워짐).

### 3.2 memory_entries — type 확장

[35_DB_SCHEMA_v1.0.md](35_DB_SCHEMA_v1.0.md) 의 8 type 에 **`workflow_template` 추가** (9번째).

**content JSONB schema** (`type="workflow_template"`):

```json
{
  "schema_version": "v1",
  "name": "마케팅 분석 패턴",
  "description": "신상품 launch 후 review 분석",
  "todos": [
    {
      "id": "todo_001",
      "task_type": "data_collection",
      "agent": "collection_agent",
      "tool": "naver_collector",
      "tool_params": {"brand": "{{brand}}"},
      "depends_on": [],
      "priority": 1,
      "rationale": "네이버 리뷰 수집",
      "position": {"x": 100, "y": 100},
      "node_type": "task"
    }
  ],
  "dag": {"todo_002": ["todo_001"]},
  "param_slots": [
    {"name": "brand", "type": "string", "required": true, "description": "분석할 브랜드명"}
  ],
  "usage_count": 0,
  "last_used_at": null,
  "tags": ["analysis", "review"]
}
```

**핵심 — `param_slots`**:
- 다음 호출 시 채울 변수. `{{brand}}` placeholder.
- 사용자: "마케팅 분석 패턴 써줘, 브랜드는 블루밍글로우" → 시스템: template + slot 채움 → 즉시 실행 가능 plan 생성
- = **vision H4 맞춤화의 구체적 메커니즘**

### 3.3 백엔드 변경 영향 — 최소

| 영역 | 변경 |
|------|------|
| `planner.PlannedTodo` | Optional 3 필드 추가 (~10 LoC) |
| `memory_entries` | type CHECK constraint 확장 (`workflow_template` 추가, 1 마이그레이션) |
| `MemoryManager` | `save_workflow_template` / `load_workflow_template` / `apply_template_with_params` 메서드 (~50 LoC) |
| `ws_hitl` / `ws_agent` | **변경 X** — 기존 메시지 그대로 (NL edit / structured edit 둘 다 활용) |
| `plan_editor` | **변경 X** — Optional 필드는 자동 보존 |

→ **백엔드 변경 ~60 LoC**. 기존 메시지 / 흐름 / DB 구조 99% 유지.

---

## 4. 노드 / 엣지 디자인

### 4.1 노드 시각적 사양

| 요소 | 사양 |
|------|------|
| 모양 | 둥근 사각형 (radius 8px) |
| 크기 | 180×80px (POC) / 자동 (텍스트 길이) |
| 헤더 | 아이콘 (lucide-react) + task_type / agent |
| 본문 | rationale (1~2줄, ellipsis) |
| 푸터 | tool 명 (small text) |
| 상태별 색상 | task: 회색 / branch: 노랑 / start: 녹색 / end: 청색 / 실행중: 펄스 애니메이션 / 완료: 진녹색 / 실패: 빨강 |
| 무효화 (cascade) | 🔴 tint + ⛓ overlay (기존 패턴 유지) |
| 선택됨 | 파란 outline (2px) |
| 호버 | shadow + cursor pointer |

### 4.2 엣지 (depends_on)

| 요소 | 사양 |
|------|------|
| 모양 | Bezier curve (React Flow 기본) |
| 색상 | 회색 (기본) / 빨강 (cascade invalidated 영향) |
| 화살표 | 종점 |
| 라벨 (선택) | "depends" (W2+) |

### 4.3 노드 타입별 동작

```typescript
type NodeType = "task" | "branch" | "join" | "start" | "end";
```

| node_type | 의미 | 입출력 | POC |
|-----------|------|--------|:---:|
| `task` | 일반 실행 단위 (PlannedTodo) | depends_on[] → 1 출력 | ✅ |
| `start` | 워크플로우 시작점 (가상) | 0 입력 → 1 출력 | W3 |
| `end` | 결과 노드 (가상) | depends_on[] → 0 출력 | W3 |
| `branch` | 조건 분기 | 1 입력 → N 출력 (condition) | W4 |
| `join` | 병합 | N 입력 → 1 출력 | W4 |

→ POC (W1) = task 만. branch/join 은 W4 (사용자 피드백 후 결정).

---

## 5. 인터랙션 — NL 편집 ↔ 시각적 편집 공존

### 5.1 시각적 편집 동작 매핑

| 사용자 동작 | 백엔드 호출 | 기존 ws_hitl 메시지 |
|------------|------------|--------------------|
| 노드 우클릭 → "삭제" | `todo_delete` | ✅ 기존 |
| 노드 더블클릭 → 속성 패널 → 저장 | `todo_modify` | ✅ 기존 |
| 좌 팔레트에서 드래그 in (W4+) | `todo_add` | ✅ 기존 |
| 노드 드래그 (순서 변경) | `todo_modify` (position) | ⚠️ position 추가 |
| 엣지 클릭 → "끊기" | `todo_modify` (depends_on 제거) | ⚠️ depends_on 변경 |
| 캔버스 빈 곳 우클릭 → "노드 추가" | `todo_add` | ✅ 기존 |

→ **기존 백엔드 메시지 90% 재활용**. position 변경만 신규.

### 5.2 NL 편집 동작

[ADR-002](adr/ADR-002_nl_edit_phased_roadmap.md) 의 NL 1차~3차 그대로:
- 1차 (현재 ✅): "4번 삭제" / "3-4 순서 바꿔"
- 2차 (Sprint 15 E4): LLM Tool Routing
- 3차 (Sprint 16+): 메모리 / 패턴 기반

캔버스 위 별도 입력창 → ws_hitl `todo_edit_nl` 전송 → 결과가 시각적으로 즉시 반영 (애니메이션).

### 5.3 둘의 충돌 방지

- L1 per-session Lock (HITLManager) — 기존 그대로 작동
- 한 번에 하나의 편집만 진행 (NL 편집 중 시각적 편집 비활성화 — 로딩 indicator)

### 5.4 paused 게이트 (v1.1 — ADR-012)

백엔드 [`ws_hitl._handle_todo_modify/delete/add`](../../backend/api_v2/ws_hitl.py) 는 모두 `progress.status == "paused"` 시점에만 허용 (Sprint 14 A3 정책). 비-paused 상태에서 편집 요청 시 `hitl_ack accepted:false, code:"TODO_EDIT_NOT_PAUSED"` 거부.

→ 프론트는 **사전 차단** — `useExecution.computeCanEdit(isPaused, turnId)` 가 false 면 우클릭/더블클릭/toolbar 모두 비활성:

```ts
// frontend/src/features/execution/store.ts
export function computeCanEdit(isPaused: boolean, turnId: string | null): boolean {
  return isPaused && !!turnId;
}
```

paused 상태 도달 경로 (둘 다 W2 활성):
1. **plan_review** (검토 ON) — 백엔드 spec 21 v1.4 Phase 5 가 자동 progress paused 생성
2. **execution_pause** — 사용자 채팅창 [⏸ 중지]

비-paused 상태 → empty-state 안내 배너: "편집은 일시정지 상태에서 가능합니다."

### 5.5 W2 컴포넌트 카탈로그 (v1.1)

| 컴포넌트 | 트리거 | 동작 | ws 송신 |
|---------|--------|------|--------|
| **ContextMenu** | 노드 우클릭 (editable 시) | 메뉴 fixed 표시 — 수정/삭제 2 항목 | 삭제 시 `todo_delete` |
| **PropertyPanel** | 노드 더블클릭 / ContextMenu "수정" | shadcn Sheet 우측 슬라이드 — rationale/agent/tool/tool_params 폼 | 저장 시 변경 필드만 `todo_modify` |
| **EditToolbar** | 캔버스 우측 상단 absolute | "+ 단계 추가" / "🗑 선택 삭제" 2 버튼 | 추가 시 `todo_add` / 삭제 시 `todo_delete` |
| **cascade tint** | `hitl_ack.invalidated` 수신 | NodeComponent 가 🔴 ring + ⛓ "cascade" 배지 | (수신 전용) |

**applyMode = `immediate`** (W2 진입 단순) — 우클릭 삭제 즉시 송신. `batched` (변경 적용 누적) 는 W2 후속.

### 5.6 자연 동기화 (v1.1 — 변경 0)

편집 결과 반영 = `useExecution.handleWSMessage('hitl_ack')` (P1-4 에서 이미 구현):
- `ack.plan` 있으면 `setPlan` 호출 → React Flow re-render 자연 발생.
- `ack.invalidated` 있으면 `useHitl.cascadeResult` 에 저장 → WorkflowPage 가 구독 → `WorkflowCanvas.invalidatedIds` 로 전달 → NodeComponent 🔴 tint.

→ **별도 갱신 로직 X**. 기존 hitl_ack 흐름 재활용.

---

## 6. Save / Load — Workflow Template

### 6.1 사용자 흐름

```
1. 자연어: "블루밍글로우 네이버 리뷰 분석"
   → AI 자동 plan 생성 (5 노드)
   → 캔버스에 자동 배치

2. 사용자 만족 / 편집 완료
   → [💾 저장] 버튼
   → 모달: 이름 / 설명 / 태그 / param_slots (자동 추출 + 수정)

3. 다음에:
   "마케팅 분석 패턴 써줘, 브랜드는 무지개셔벗"
   → 시스템: 저장된 template 검색 (memory search) → param 채움 → plan 생성

4. 누적되면:
   "분석" 한 마디 → 시스템 자동 제안 (H4)
```

### 6.2 param_slots 자동 추출

저장 시 시스템이 todos 의 `tool_params` 안에서 specific value (`"블루밍글로우"`) 를 감지 → **placeholder 변환 제안**:

```
tool_params: {"brand": "블루밍글로우"}
   ↓ 사용자 확인
tool_params: {"brand": "{{brand}}"}
param_slots: [{"name": "brand", "type": "string", "required": true}]
```

### 6.3 API 영역 (간략)

```python
# MemoryManager 신규 메서드
async def save_workflow_template(
    user_id: str, name: str, plan: Plan, param_slots: list[dict]
) -> str  # memory_entry_id

async def load_workflow_template(memory_id: str) -> dict
async def apply_template_with_params(memory_id: str, params: dict) -> Plan
async def list_workflow_templates(user_id: str, query: str = "") -> list[dict]
```

→ E1 메모리 인프라 (Sprint 15 P0) 자연 확장. **별도 테이블 X**.

---

## 7. Phase 분해 — 4 Phase (W1~W4)

| Phase | 내용 | 시간 | Sprint |
|-------|------|------|--------|
| **W1 Read-only 시각화** | React Flow 통합 + 자동 레이아웃 (dagre). 편집 X / Save X. 기존 list UI 와 toggle | ~3~5일 | Sprint 15 P0 |
| **W2 시각적 편집** ✅ | 우클릭 (ContextMenu) / 더블클릭 (PropertyPanel) / EditToolbar / cascade tint. 드래그 position 변경은 W2 후속 | 8 Stage TDD (~1주) | Sprint 15 P1 — **2026-05-16 완료** (ADR-012) |
| **W3 Save / Library** | "내 워크플로우" 저장 + 호출. param_slots 자동 추출. memory_entries 통합 | ~3~5일 | Sprint 15 P1 또는 Sprint 16 |
| **W4 노드 라이브러리** | 좌측 팔레트 → 새 노드 드래그-in. branch/join 노드 타입. 사용자 자유 빌더 | ~1~2주 | Sprint 16+ |

**총 ~4~6주**. 단계별 가치 증명 가능.

### 7.1 W1 (read-only) — Sprint 15 P0 통합 사양

| 항목 | 내용 |
|------|------|
| Frontend 컴포넌트 | `<WorkflowCanvas plan={plan} readOnly />` |
| 입력 | 기존 `progress.plan` (`planner.Plan` dict) |
| 렌더링 | dagre 자동 레이아웃 → React Flow |
| 인터랙션 | 줌 / 팬 / 미니맵 / 노드 클릭 → 상세 표시 (편집 X) |
| Toggle | 헤더에 "📋 리스트 / 🔗 그래프" 토글 (기본 그래프) |
| 백엔드 변경 | 0 (position 필드는 frontend 가 dagre 로 계산) |

→ **백엔드 손대지 않고 W1 진입 가능**. Sprint 15 P0 의 dashboard 작업에 자연 포함.

---

## 8. 학습 곡선 — Frontend 모름 고려

| 우선순위 | 학습 항목 | 시간 | Vision 기여 |
|:---:|-----------|------|------------|
| 1 | TypeScript 기초 (필수) | 1주 | ⭐⭐⭐⭐⭐ |
| 2 | Tailwind v3.4 + utility 사고 | 3일 | ⭐⭐⭐⭐⭐ |
| 3 | shadcn/ui (CLI / 컴포넌트) | 1일 | ⭐⭐⭐⭐ |
| 4 | Zustand (Redux 대비 매우 단순) | 반나절 | ⭐⭐⭐⭐ |
| 5 | TanStack Query | 1일 | ⭐⭐⭐⭐ |
| 6 | **React Flow (@xyflow/react)** ⭐ | 2~3일 | ⭐⭐⭐⭐⭐ vision 핵심 |
| 7 | dagre (자동 레이아웃) | 반나절 | ⭐⭐⭐ |
| 8 | react-hook-form + zod | 1일 | ⭐⭐⭐ |

→ **총 ~3주 학습** 으로 운영 가능. React Flow 학습이 가장 가치 큼 (workflow / DAG / mind map / decision tree 평생 자산).

---

## 9. 테스트 전략

### 9.1 단위 테스트

- 노드 컴포넌트 렌더링 (Vitest + RTL)
- dagre 레이아웃 계산 함수
- visualization_meta 변환 함수

### 9.2 통합 테스트

- React Flow + workflow plan dict → 정상 렌더링
- 드래그 후 position 저장 → ws_hitl `todo_modify` 호출
- NL 편집 + 시각적 편집 공존 (L1 Lock)

### 9.3 E2E 테스트

- Playwright + MSW (WebSocket mock)
- 자연어 입력 → 캔버스 표시 → 시각적 편집 → 저장 → 재호출

### 9.4 Storybook (선택)

- 노드 타입별 / 상태별 시각화 검증
- shadcn/ui 컴포넌트 갤러리

---

## 10. 관련 spec / ADR / Memory

### 10.1 spec
- [00_vision_and_intent.md](00_vision_and_intent.md) — vision H4 맞춤화
- [30_DATA_MODELS_v1.1.md](30_DATA_MODELS_v1.1.md) — PlannedTodo 확장
- [35_DB_SCHEMA_v1.0.md](35_DB_SCHEMA_v1.0.md) — memory_entries.type=`workflow_template`
- [21_WEBSOCKET_PROTOCOL_v1.5.md](21_WEBSOCKET_PROTOCOL_v1.5.md) — 기존 메시지 재활용

### 10.2 ADR
- [ADR-002](adr/ADR-002_nl_edit_phased_roadmap.md) — NL 1·2·3차
- [ADR-010](adr/ADR-010_plan_schema_unification.md) — `planner.Plan` 단일화
- [ADR-015](adr/) (예정) — 메모리 + Clarification 통합

### 10.3 Memory (사용자 박제)
- `project_extension_ease_priority.md` — 5 원칙 (JSONB / Optional / 확장 우선) 부합
- `project_nl_edit_roadmap.md` — NL 1·2·3차
- `project_llm_heavy_initial.md` — 초기 LLM 우선 (param_slots 자동 추출도 LLM)

### 10.4 탐색 자취 (참고)
- [docs/_claude/new_frontend/](../_claude/new_frontend/) — 14 문서 (tech stack 비교 / state architecture / component inventory / design system 등)
- 본 spec 은 위 자취 중 **vision H4 의 핵심 영역만 정제**

---

## 11. Risk + 완화

| Risk | 완화 |
|------|------|
| React Flow 학습 비용 | 공식 예제 충실. dagre 통합 패턴 검증됨 |
| 노드 많아지면 캔버스 압도 (n8n 약점) | NL 편집과 공존 — 많아도 자연어로 제어 가능 |
| `frozen=False` (PlannedTodo) → mutation 위험 | `model_copy(update=...)` 관행 유지 |
| param_slots 자동 추출 LLM 실패 | 사용자 수동 편집 fallback |
| position 동기화 (여러 사용자) | L1 Lock + 최후 쓰기 우선 (POC) |
| 모바일 / 작은 화면 | W3 까지 데스크탑 우선. 모바일은 Sprint 17+ |

---

## 12. 완료 기준 (Acceptance) — Phase 별

### W1 (Sprint 15 P0)
- [ ] `<WorkflowCanvas plan={plan} readOnly />` 렌더링
- [ ] dagre 자동 레이아웃 — 노드 겹침 없음
- [ ] 줌 / 팬 / 미니맵 작동
- [ ] 리스트 ↔ 그래프 toggle
- [ ] 기존 list UI 와 동일 데이터 표시 (drift 0)

### W2 (Sprint 15 P1)
- [ ] 노드 우클릭 → 삭제 → ws_hitl `todo_delete` 호출
- [ ] 더블클릭 → 속성 패널 → 수정 → `todo_modify`
- [ ] 드래그 → position 저장 (`todo_modify` 확장)
- [ ] NL 편집과 공존 (L1 Lock 작동)

### W3 (Sprint 15 P1 또는 16)
- [ ] [💾 저장] → memory_entries 에 `workflow_template` 저장
- [ ] param_slots 자동 추출 (LLM)
- [ ] "마케팅 분석 패턴 써줘" → template 호출 → plan 생성

### W4 (Sprint 16+)
- [ ] 좌측 노드 라이브러리
- [ ] branch / join 노드 타입
- [ ] 사용자 자유 빌더 모드

---

## 13. 변경 이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-05-12 | 초안 — React Flow / dagre / 3-panel / 노드 schema (PlannedTodo Optional 3 필드) / Save/Load (memory_entries.type=workflow_template) / 4 Phase W1~W4 / 학습 곡선 / 테스트 전략. vision H4 맞춤화의 UI 구체화. backend 변경 ~60 LoC (사용자 5 원칙 부합) |
| v1.1 | 2026-05-13 | **§2.3 Layout 정정** — 3-Panel 제거. v1 GlobalLayout 채택 (사용자 통찰 "동료 화면 + 채팅 지시"). Workflow Canvas = `/workflow` 라우트의 Outlet 콘텐츠 + 우측 SideChatPanel 에서 NL 편집. §2.4 시각화 vs 자연어 공존 UX 갱신 |
