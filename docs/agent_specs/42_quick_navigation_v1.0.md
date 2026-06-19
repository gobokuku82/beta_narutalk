# 42. Quick Navigation — 자주 묻는 질문 진입점

| 항목 | 내용 |
|------|------|
| 담당자 | 도윤 |
| 분류 | 운영 (40대) |
| 진행상태 | Active |
| 버전 | **v1.0** |
| 최종 수정일 | 2026-05-18 |
| 독자 | 어디 봐야 할지 모를 때 / FAQ 진입점 / 자주 보는 spec 빠른 link |
| 관련 | [`.claude/CLAUDE.md`](../../.claude/CLAUDE.md) (매 세션 자동 로드 — 핵심 5 진입점) ↔ 본 문서 (필요 시 사용자가 직접 진입) |

---

## 0. 본 문서의 역할

> **CLAUDE.md 의 5 진입점 외 자주 가는 spec / 문서 / FAQ 매핑**.
>
> CLAUDE.md 는 매 세션 자동 로드되므로 가벼워야 함. 본 문서는 *필요할 때만 읽음* → 깊이 확장.

### 언제 본 문서 보나
- "지금 에이전트 구조 어떻게?" 같은 일반 질문
- spec 번호를 모르는데 무엇 보고 싶을 때
- 변경 작업 진입 전 — 어느 spec 부터 봐야 할지 모를 때

---

## 1. 자주 보는 spec — 개발 시 직접 진입 link

| 무엇 보고 싶나 | 어디 |
|---|---|
| **🚪 Tool/Agent 변경 작업 — 첫 진입점** | [41 Change Hub](41_agent_tool_change_hub_v1.0.md) |
| 🔄 변경·재구성·버전 변경 상세 절차 | [40 Lifecycle](40_agent_tool_lifecycle_v1.0.md) |
| 🔗 기능 → 에이전트 → 툴 → 데이터 → I/O 종단 매핑 | [17 Functions → I/O](17_functions_to_io_v1.0.md) |
| 시스템 4-Layer 통합 지도 (Cognitive/Planning/Execution/Response) | [14 System Agent Overview](14_system_agent_overview_v1.0.md) |
| 한 사이클 sequence (시간 축) | [15 End-to-End Flow](15_end_to_end_flow_v1.0.md) |
| Tool 프레임워크 (BaseTool·ToolSpec·DataSource) | [30 DATA MODELS](30_DATA_MODELS_v1.1.md) §6~§7 |
| Pydantic 모델 / Core Enum | [30 DATA MODELS](30_DATA_MODELS_v1.1.md) |
| Manager Layer (HITL / Session / Callback / 등) | [12 Manager Layer](12_manager_layer_v1.4.md) |
| WebSocket 프로토콜 | [21 WS Protocol](21_WEBSOCKET_PROTOCOL_v1.5.md) |
| Vision / Intent (north star) | [00 Vision and Intent](00_vision_and_intent.md) |

---

## 2. 자주 묻는 질문 → 어디 가나

### 2.1 구조·동작 질문

| 질문 | 가는 곳 |
|---|---|
| "지금 에이전트 구조 어떻게 되어 있나?" | [17 §2 에이전트 구조](17_functions_to_io_v1.0.md) + [team_catalog.yaml](../../backend/app/dream_agent/planning/catalog/team_catalog.yaml) |
| "프롬프트 어디서 어떻게 가져가?" | [17 §5 I/O 메커니즘](17_functions_to_io_v1.0.md) + [planner.py L265/285/305](../../backend/app/dream_agent/planning/planner.py) |
| "Tool 호출 흐름은?" | [17 §5.1~§5.7](17_functions_to_io_v1.0.md) + [executor.py:_run_single_todo](../../backend/app/dream_agent/execution/executor.py) |
| "한 사이클 어떻게 흐르나?" | [15 End-to-End Flow](15_end_to_end_flow_v1.0.md) (Mermaid sequence) |
| "4-Layer 책임 분리?" | [14 System Agent Overview](14_system_agent_overview_v1.0.md) |
| "HITL 흐름?" | [12 Manager Layer §3 HITL](12_manager_layer_v1.4.md) + [13 Lifecycle](13_lifecycle_v1.3.md) |

### 2.2 변경 작업 질문

| 질문 | 가는 곳 |
|---|---|
| "Tool 1개 추가하려면?" | [41 §3.A](41_agent_tool_change_hub_v1.0.md) → [40 §3.A](40_agent_tool_lifecycle_v1.0.md) |
| "Tool rename / 폐기?" | [41 §3.B](41_agent_tool_change_hub_v1.0.md) → [40 §3.B](40_agent_tool_lifecycle_v1.0.md) |
| "에이전트 추가/분리/합병?" | [41 §3.C](41_agent_tool_change_hub_v1.0.md) → [40 §3.C](40_agent_tool_lifecycle_v1.0.md) |
| "카테고리 재구성?" | [41 §6 예시](41_agent_tool_change_hub_v1.0.md) → [40 §3.E](40_agent_tool_lifecycle_v1.0.md) |
| "데이터 source mock → 실API?" | [40 §3.D](40_agent_tool_lifecycle_v1.0.md) |
| "v1 → v2 메이저?" | [40 §3.E + §4](40_agent_tool_lifecycle_v1.0.md) |
| "OS 층을 손대야 할까?" | [40 §1 경계 확인](40_agent_tool_lifecycle_v1.0.md) — 대부분 답 = ❌ 안 손댐 |

### 2.3 데이터 질문

| 질문 | 가는 곳 |
|---|---|
| "Tool 이 무슨 데이터를 쓰나?" | [30 §7.5 DataSource ABC](30_DATA_MODELS_v1.1.md) + `data/raw_data/` |
| "데이터 source 진화 (POC→MVP→Prod)?" | [40 §3.D](40_agent_tool_lifecycle_v1.0.md) |

### 2.4 결정·박제 질문

| 질문 | 가는 곳 |
|---|---|
| "이거 왜 이렇게 만들었지? (과거 결정)" | ADR (Michael Nygard 형식) — 결정 박제 |
| "비전 narrative?" | [00 Vision and Intent](00_vision_and_intent.md) |

---

## 3. INDEX 들 — 분야별 진입점

영역마다 INDEX 가 별도:

| # | INDEX | 위치 | 무엇 | 자동 로드? |
|---|---|---|---|---|
| **0** | **CLAUDE.md** ⭐ | [`.claude/CLAUDE.md`](../../.claude/CLAUDE.md) | 마스터 — 핵심 진입점 | ✅ 매 세션 |
| 1 | `agent_specs/INDEX.md` | [INDEX.md](INDEX.md) | 정식 spec 목록 | ❌ |

→ **마스터 = CLAUDE.md** (자동 로드, 가벼움 유지).

---

## 4. 디렉토리 한 페이지 지도

```
backend/
├── app/dream_agent/
│   ├── cognitive/          ← Layer 1 (NL → StructuredQuery)
│   ├── planning/           ← Layer 2 (3-Stage Planner)
│   │   └── catalog/team_catalog.yaml    ⭐ Planner 진실 소스
│   ├── execution/          ← Layer 3
│   ├── response/           ← Layer 4
│   ├── workflow_managers/  ← Manager Layer (HITL/Session/Callback/...)
│   ├── tools/
│   │   ├── base_tool.py    ⭐ Tool 추상 계약 (절대 안 손댐)
│   │   ├── registry.py     ⭐ 자동 import (절대 안 손댐)
│   │   ├── catalog/<cat>/<name>.yaml    ⭐ Tool 메타카드
│   │   ├── <cat>/<name>.py              ⭐ Tool 코드
│   │   └── shared/helpers.py
│   ├── llm_manager/
│   │   ├── client.py
│   │   └── prompts/
│   │       ├── cognitive.yaml
│   │       ├── planning_stage1_team.yaml      ← planner.py:265 로드
│   │       ├── planning_stage2_agent.yaml     ← planner.py:285 로드 ⭐
│   │       ├── planning_stage3_todo.yaml      ← planner.py:305 로드 ⭐
│   │       └── response.yaml                  ⭐
│   ├── models/             ← Pydantic
│   ├── schemas/            ← I/O 계약
│   └── states/agent_state.py
└── tests/sprint13~15/      ← 회귀 테스트

frontend/src/               ← Vite + React 19 + Zustand + React Flow

data/
└── raw_data/*.csv          ← POC raw 데이터

docs/
└── agent_specs/            ← git 추적 정식 spec
```

⭐ = 변경 작업 시 손대는 영역 ([41 §2](41_agent_tool_change_hub_v1.0.md))

---

## 5. 본 문서 갱신 정책

| 트리거 | 갱신 |
|---|---|
| 신규 spec 추가 (자주 보일 만한 것) | §1 자주 보는 spec 표 |
| 신규 FAQ 발생 | §2 (적절한 sub-section) |
| 새 INDEX 신설 | §3 INDEX 표 |
| 디렉토리 구조 변경 | §4 디렉토리 지도 |
| 본 문서 자체 너무 길어짐 | 분리 (예: 42_quick_navigation.md + 43_faq.md) |

---

## 변경 이력

> 프레임워크 추출(2026-06-19) 이전(마케팅 도메인 시기)의 상세 변경 이력은 git 히스토리를 참조하세요.
