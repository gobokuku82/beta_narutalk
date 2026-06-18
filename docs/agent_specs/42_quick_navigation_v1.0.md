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
| Tool 구현 현황 + 확장 가이드 | [32 Execution Agent Tools](32_execution_agent_tools_v1.0.md) |
| Tool 요구사항 카탈로그 | [31 Execution Agent Function List](31_execution_agent_function_list_v0.6.md) |
| Pydantic 모델 / Core Enum | [30 DATA MODELS](30_DATA_MODELS_v1.1.md) |
| Manager Layer (HITL / Session / Callback / 등) | [12 Manager Layer](12_manager_layer_v1.4.md) |
| WebSocket 프로토콜 | [21 WS Protocol](21_WEBSOCKET_PROTOCOL_v1.5.md) |
| Vision / Intent (north star) | [00 Vision and Intent](00_vision_and_intent.md) |

---

## 2. 자주 묻는 질문 → 어디 가나

### 2.1 구조·동작 질문

| 질문 | 가는 곳 |
|---|---|
| "지금 에이전트 구조 어떻게 되어 있나?" | [17 §2 9 에이전트](17_functions_to_io_v1.0.md) + [team_catalog.yaml](../../backend/app/dream_agent/planning/catalog/team_catalog.yaml) |
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
| "카테고리 재구성 (예: 7→12)?" | [41 §6 예시](41_agent_tool_change_hub_v1.0.md) → [40 §3.E](40_agent_tool_lifecycle_v1.0.md) |
| "데이터 source mock → 실API?" | [40 §3.D](40_agent_tool_lifecycle_v1.0.md) + [data/description/mock/ROADMAP](../../data/description/mock/ROADMAP.md) |
| "v1 → v2 메이저?" | [40 §3.E + §4](40_agent_tool_lifecycle_v1.0.md) |
| "OS 층을 손대야 할까?" | [40 §1 경계 확인](40_agent_tool_lifecycle_v1.0.md) — 대부분 답 = ❌ 안 손댐 |

### 2.3 데이터 질문

| 질문 | 가는 곳 |
|---|---|
| "Tool 이 무슨 CSV 무슨 컬럼 쓰나?" | [TOBE_MVP/01 매트릭스](../../docs/_claude/tool/TOBE_MVP/01_tool_data_matrix.md) |
| "mock CSV 12 개 schema?" | [data/description/mock/SCHEMA](../../data/description/mock/SCHEMA.md) |
| "시트 간 관계 / 조인?" | [data/description/mock/RELATIONSHIPS](../../data/description/mock/RELATIONSHIPS.md) |
| "데이터 함정 / NaN / % 문자열?" | [data/description/mock/RELATIONSHIPS §3](../../data/description/mock/RELATIONSHIPS.md) |
| "데이터 source 진화 (POC→MVP→Prod)?" | [data/description/mock/ROADMAP](../../data/description/mock/ROADMAP.md) |
| "/api/mock/... endpoint?" | [data/description/mock/API_MAPPING](../../data/description/mock/API_MAPPING.md) |
| "Frontend 페이지 → CSV 매핑?" | [data/description/mock/UI_MAPPING](../../data/description/mock/UI_MAPPING.md) |

### 2.4 결정·박제 질문

| 질문 | 가는 곳 |
|---|---|
| "이거 왜 이렇게 만들었지? (과거 결정)" | [agent_specs/adr/](adr/) — Michael Nygard ADR |
| "Drift / 미해결 결정?" | [TOBE_MVP/03 Drift Report](../../docs/_claude/tool/TOBE_MVP/03_drift_report.md) |
| "POC → MVP 결정 로그?" | [tool/04_decisions](../../docs/_claude/tool/04_decisions.md) |
| "사용자 작업 자취 30+?" | [_claude/INDEX](../../docs/_claude/INDEX.md) |
| "비전 narrative (한국어)?" | [docs/_claude/referrence/agent_design/](../../docs/_claude/referrence/agent_design/) |

### 2.5 작업 계획 / 로드맵 질문

| 질문 | 가는 곳 |
|---|---|
| "POC → MVP 어떻게 갈 것인가?" | [tool/03_gap_and_roadmap](../../docs/_claude/tool/03_gap_and_roadmap.md) |
| "현재 As-Is 상태?" | [tool/01_as_is_poc](../../docs/_claude/tool/01_as_is_poc.md) |
| "To-Be 비전?" | [tool/02_to_be_mvp](../../docs/_claude/tool/02_to_be_mvp.md) |
| "Migration plan?" | [TOBE_MVP/04_migration_plan_2026-05-18](../../docs/_claude/tool/TOBE_MVP/04_migration_plan_2026-05-18.md) |

---

## 3. INDEX 들 — 분야별 진입점 7개

본 시스템에는 **7 진입점** 이 있음. 영역마다 INDEX 가 별도:

| # | INDEX | 위치 | 무엇 | 자동 로드? |
|---|---|---|---|---|
| **0** | **CLAUDE.md** ⭐ | [`.claude/CLAUDE.md`](../../.claude/CLAUDE.md) | 마스터 — 5 핵심 진입점 | ✅ 매 세션 |
| 1 | `agent_specs/INDEX.md` | [INDEX.md](INDEX.md) | 정식 spec 56+ (00~66 + adr/) | ❌ |
| 2 | `agent_specs/adr/INDEX.md` | [adr/INDEX.md](adr/INDEX.md) | ADR (결정 박제) | ❌ |
| 3 | `_claude/INDEX.md` | [docs/_claude/INDEX.md](../_claude/INDEX.md) | Sprint 자취 30+ | ❌ |
| 4 | `tool/README.md` | [docs/_claude/tool/README.md](../_claude/tool/README.md) | POC ↔ MVP 4 문서 | ❌ |
| 5 | `tool/TOBE_MVP/README.md` | [docs/_claude/tool/TOBE_MVP/README.md](../_claude/tool/TOBE_MVP/README.md) | Tool↔Data 매핑 4 문서 | ❌ |
| 6 | `data/description/mock/INDEX.md` | [data/description/mock/INDEX.md](../../data/description/mock/INDEX.md) | mock 12 CSV 해설 6 문서 | ❌ |

→ **마스터 = CLAUDE.md** (자동 로드, 가벼움 유지). 나머지 6개는 영역별 깊이 진입점.

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
├── mock/*.csv              ← POC raw 12 파일
└── description/mock/       ← 데이터 해설 6 문서 (INDEX/SCHEMA/...)

docs/
├── agent_specs/            ← git 추적 정식 spec (00~66 + adr/)
└── _claude/                ← gitignored 자취·계획서·박제
    ├── INDEX.md
    ├── referrence/agent_design/    ← MVP 비전 narrative (한국어)
    └── tool/
        ├── 01~04 (As-Is/To-Be/Gap/Decisions)
        └── TOBE_MVP/01~04 (Tool↔Data 매핑 + Drift + Migration plan)
```

⭐ = 변경 작업 시 손대는 영역 (4 파일 + 1 폴더, [41 §2](41_agent_tool_change_hub_v1.0.md))

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

## 6. 변경 이력

| 버전 | 날짜 | 변경 |
|------|------|------|
| v1.0 | 2026-05-18 | 초안 — 사용자 요청 "흩어진 spec/문서 진입점 한 곳에" 반영. CLAUDE.md 무거워지지 않게 별도 spec 으로 분리. §1 자주 보는 spec 11 link + §2 FAQ 25 + §3 INDEX 7 매트릭스 + §4 디렉토리 한 페이지 지도. |
