# docs/execution_agent/ — 실행 에이전트 상세 명세

| 항목 | 내용 |
|------|------|
| 폴더 목적 | **실행 에이전트 (execution agent / tool) 의 카드 단위 깊이 명세** |
| 독자 | Tool 작성·검토·디버깅하는 개발자 |
| 상위 spec | [agent_specs/32 Execution Agent Tools](../agent_specs/32_execution_agent_tools_v1.0.md) (요약·표 위주) |
| 본 폴더 차별 | **에이전트별 + Tool별 깊은 카드** (입출력 계약 / 로직 / 예외 / 코드 link / 변경 이력) |
| 시작일 | 2026-05-19 |
| 갱신 트리거 | Tool 추가/rename/폐기 + 에이전트 구조 변경 시 |

---

## 0. 본 폴더의 역할

> **실행 에이전트의 모든 디테일을 카드 단위로 한 곳에**.
>
> 시스템 spec (`agent_specs/`) 은 아키텍처 전체. 본 폴더는 **각 에이전트 × Tool 단위 깊이**.

### 언제 본 폴더 보나
- Tool 1개의 입출력 / 로직 / 예외 / 코드 / 의존 Tool 까지 다 알고 싶을 때
- 에이전트 1개의 책임 / Tool 목록 / 데이터 흐름 한 페이지로 보고 싶을 때
- Tool 추가·수정·디버깅 작업 시 첫 진입점

### 본 폴더가 *아닌* 곳
- 시스템 전체 아키텍처 → [agent_specs/14](../agent_specs/14_system_agent_overview_v1.0.md)
- 변경 작업 절차 → [agent_specs/41](../agent_specs/41_agent_tool_change_hub_v1.0.md) + [40](../agent_specs/40_agent_tool_lifecycle_v1.0.md)
- 종단 매핑 → [agent_specs/17](../agent_specs/17_functions_to_io_v1.0.md)
- Tool ↔ Data 매트릭스 → [TOBE_MVP/01](../_claude/tool/TOBE_MVP/01_tool_data_matrix.md)
- 비전 narrative → [agent_design/](../_claude/referrence/agent_design/)

---

## 1. 폴더 구조

```
docs/execution_agent/
├── README.md                ← (현재)
├── 00_overview.md           ← 10 에이전트 + ~46 Tool 전체 한눈
├── INDEX.md                 ← 분야별 진입점 / FAQ
│
├── agents/                  ← 10 에이전트 카드
│   ├── 01_chat_hub.md
│   ├── 02_collection.md
│   ├── 03_text_preprocessing.md
│   ├── 04_channel_normalizing.md
│   ├── 05_analysis.md
│   ├── 06_image.md
│   ├── 07_storyboard.md
│   ├── 08_report_text.md
│   ├── 09_pdf.md
│   └── 10_ppt.md
│
└── tools/                   ← Tool 카드
    ├── implemented/         ← ✅ 동작 검증된 8개
    │   ├── review_collector.md
    │   ├── format_normalizer.md
    │   ├── text_preprocessor.md
    │   ├── sentiment_analyzer.md
    │   ├── keyword_extractor.md
    │   ├── insight_extractor.md
    │   ├── report_writer.md
    │   └── summary_generator.md
    └── stub/                ← 🟡 미구현 (Phase 진입 시 채움)
```

---

## 2. 카드 템플릿 — Agent

```markdown
# NN. <agent_name> — <한 줄 역할>

## 메타
| 항목 | 값 |
|---|---|
| 소속 팀 | analysis_team / creative_team |
| handles_tasks | [task_type_list] |
| Tool 수 | implemented N / stub M |
| 현재 구현률 | x% |

## 입출력
- 입력 / 출력 / 다음 에이전트

## Tool 목록
| Tool | Status | 카드 link |

## 데이터 흐름
[Mermaid 또는 ASCII]

## HITL 카테고리 (D12 결정)

| 카테고리 | 본 에이전트 해당 | 게이트 시점 |
|---|---|---|
| 조회·자동 | 데이터 조회/단순 요약 | 없음 (자동) |
| 생성 후 | 콘텐츠 생성 (이미지/리포트) | 결과 표시 후 [채택/거부/재생성] |
| 실행 전 | 광고 운영 영향 (예산/키워드 중지) | 실행 직전 게이트 |
| 외부 발송 | 클라이언트 발송 | 발송 직전 별도 |

→ 본 에이전트의 Tool 호출 시 어느 카테고리? 카드 본문에 명시.
→ 상세 = [agent_specs/02 to_be_mvp §7](../_claude/tool/02_to_be_mvp.md) + [03 Drift D12](../_claude/tool/TOBE_MVP/03_drift_report.md).

## Phase 진입

| Phase | 본 에이전트의 작업 |
|---|---|
| Phase 0 (매핑) | 카드 작성·갱신 |
| Phase 1~6 | Tool 신규/rename/폐기 — [03_gap_and_roadmap](../_claude/tool/03_gap_and_roadmap.md) 참조 |
| Phase 6+ | mock → 실API 전환 (해당 시) |

## ⚠️ 수정 시 함께 변경 영역 (Connected Files)

본 에이전트를 수정 (Tool 추가/제거 / 책임 변경 / rename 등) 시 동시 갱신 필수:

| 영역 | 파일 / line | 어떤 변경 시 |
|---|---|---|
| **team_catalog.yaml** | `planning/catalog/team_catalog.yaml` (해당 agent 블록) | Tool 추가/제거 / handles_tasks / description |
| **LLM Prompts** | `llm_manager/prompts/planning_stage2_agent.yaml` | agent 이름 / 선택 룰 |
| **LLM Prompts** | `llm_manager/prompts/planning_stage3_todo.yaml` | agent 이름 + 예시 todo |
| **LLM Prompts** | `llm_manager/prompts/response.yaml` | 예시 (Tool 이름 매칭) |
| **task_agent_hints** | `team_catalog.yaml` L232-248 | task → agent 매핑 |
| **implicit_prerequisites** | `team_catalog.yaml` L254-265 | task 선행 의존 |
| **Frontend (UI 부수)** | `frontend/src/features/workflow/editing/PropertyPanel.tsx` | placeholder / agent 표시 |
| **Dashboard (부수)** | `dashboard/index.html` | Tool 분기 텍스트 (rename 시) |
| **Spec 32 §7.1** | `docs/agent_specs/32_*.md` | Tool 카운트 / 현황표 |
| **Spec 31** | `docs/agent_specs/31_*.md` | 요구사항 |
| **TOBE_MVP/01 매트릭스** | `docs/_claude/tool/TOBE_MVP/01_tool_data_matrix.md` | Tool ↔ Data 행 |
| **TOBE_MVP/02 agent_cards** | `docs/_claude/tool/TOBE_MVP/02_agent_cards.md` | 짧은 카드 |
| **본 폴더 00_overview** | `docs/execution_agent/00_overview.md` | 에이전트 표 |
| **ADR (큰 결정 시)** | `docs/agent_specs/adr/ADR-XXX_<topic>.md` | 영구 박제할 결정 |
| Tests | `backend/tests/sprint*/` | Planner test / E2E |

→ 더 깊은 절차 = [agent_specs/41 §4 매트릭스](../agent_specs/41_agent_tool_change_hub_v1.0.md) + [40 §3.C](../agent_specs/40_agent_tool_lifecycle_v1.0.md).

## 참조 코드
- team_catalog.yaml L범위
- tools/<category>/ 폴더
- catalog YAML 폴더

## 참조 spec
- agent_specs/17, 32, TOBE_MVP/02

## 참조 비전 (한국어 narrative)
- [agent_design/0X_<에이전트명>.md](../_claude/referrence/agent_design/) — 비전 narrative + 9 분석 모듈 / 콘텐츠 등

## 📍 Mock vs 실API 분기 (Phase 6+ 마크) ⚠️
- 본 에이전트의 Tool 들이 외부 API 의존 — Phase 6+ 진입 시 `USE_MOCK_DATA` 환경변수 분기 도입
- 데이터 source 매핑: [TOBE_MVP/01 매트릭스](../_claude/tool/TOBE_MVP/01_tool_data_matrix.md) §2
- 데이터 ERD: [data/description/mock/RELATIONSHIPS.md §1 Mermaid ERD](../../data/description/mock/RELATIONSHIPS.md)
- 전환 절차: [agent_specs/40 §3.D](../agent_specs/40_agent_tool_lifecycle_v1.0.md) + [data/description/mock/ROADMAP](../../data/description/mock/ROADMAP.md)

## Drift / 결정 (Drift + ADR)
- Drift: [TOBE_MVP/03_drift_report.md](../_claude/tool/TOBE_MVP/03_drift_report.md) D번호
- ADR (영구 박제): [agent_specs/adr/](../agent_specs/adr/)

## Phase
- 현재 Phase / 다음 Phase — [03_gap_and_roadmap](../_claude/tool/03_gap_and_roadmap.md)

## 변경 이력
| 날짜 | 변경 |
```

---

## 3. 카드 템플릿 — Tool

```markdown
# <tool_name>

## 메타
| 항목 | 값 |
|---|---|
| 소속 에이전트 | <agent_name> |
| 카테고리 | <category> |
| Status | implemented / stub / planned |
| 버전 | v0.x.y |
| **Status 마커** (docstring) | `Status: complete \| partial \| planned — 설명` ⭐ 메모리 컨벤션 |
| **DC-10 정합 검증** | docstring `Status` + YAML `status` + team_catalog `status` **3중 일치** |
| timeout_sec | 30 (default) |
| max_retries | 0~2 |
| requires_approval | false / true (Sprint 14 A4 발동) |
| has_cost / estimated_cost | false / 0.0 |

## 입출력 계약

### 입력 (params)
| name | type | required | default | 설명 |

### 입력 (context)
- 사용 영역 명시

### 출력 (produces)
- 키 목록 + 다음 Tool 소비처

### 출력 dict 스키마
```json
{ ... }
```

## 데이터 source
- 사용 CSV / 컬럼 / 외부 API

## 로직 단계
1. ...
2. ...

## 예외 처리
- 케이스별 예외

## 의존 Tool
- 이전 / 다음

## ⚠️ 수정 시 함께 변경 영역 (Connected Files)

본 Tool 을 수정 (rename / 폐기 / params 변경 / produces 키 변경 등) 시 동시 갱신 필수:

| 영역 | 파일 | 어떤 변경 시 |
|---|---|---|
| **Tool 코드** | `backend/app/dream_agent/tools/<cat>/<name>.py` | 로직 / 시그니처 / 예외 |
| **Tool 메타카드** | `backend/app/dream_agent/tools/catalog/<cat>/<name>.yaml` | params / produces / status / description |
| **team_catalog.yaml** | `planning/catalog/team_catalog.yaml` (해당 agent.tools 안 행) | name / status / produces / params_required/optional |
| **LLM Prompts (stage3)** | `llm_manager/prompts/planning_stage3_todo.yaml` | Tool 이름 (정확 매칭) + 예시 todo |
| **LLM Prompts (response)** | `llm_manager/prompts/response.yaml` | 예시 tool 이름 (4 line) |
| **mock_tools.py** | `execution/mock_tools.py` | stub Tool 의 mock 분기 |
| **다음 Tool 의 input** | (produces 키 변경 시) 의존 Tool 들의 params 매칭 | produces 키 rename 시 — 연쇄 영향 |
| **Frontend (부수)** | `frontend/src/features/workflow/editing/PropertyPanel.tsx` L150 | placeholder (Tool 이름) |
| **Dashboard (부수)** | `dashboard/index.html` | Tool 분기 텍스트 (rename 시) |
| **Spec 32 §7.1** | `docs/agent_specs/32_*.md` | Tool 행 / 카운트 |
| **Spec 31** | `docs/agent_specs/31_*.md` | 요구사항 |
| **TOBE_MVP/01 매트릭스** | `docs/_claude/tool/TOBE_MVP/01_tool_data_matrix.md` | Tool ↔ Data 행 |
| **본 폴더 agent 카드** | `docs/execution_agent/agents/<NN>_<agent>.md` Tool 목록 표 |
| **본 폴더 00_overview** | `docs/execution_agent/00_overview.md` Tool 표 |
| **데이터 source 변경 시** | `data/description/mock/SCHEMA.md` + `RELATIONSHIPS.md` | 영향 컬럼 |
| **ADR (큰 결정 시)** | `docs/agent_specs/adr/ADR-XXX_<topic>.md` | 영구 박제할 결정 |
| **DC-10 검증** | docstring + YAML + team_catalog `Status/status` 3중 일치 | rename / status 변경 시 |
| Tests | `backend/tests/sprint*/test_*<tool>*.py` | unit / integration |

### 변경 종류별 최소 갱신 영역

| 변경 종류 | 최소 갱신 |
|---|---|
| **rename** | .py + .yaml + team_catalog + LLM Prompts (stage3 + response) + 카드 (본 폴더 + TOBE_MVP/01) |
| **params 추가/변경** | .py + .yaml (parameters) + (params 명 변경 시) team_catalog `params_required/optional` |
| **produces 키 추가/변경** | .py + .yaml (`produces`) + **의존 Tool 들** (params 매칭 변경 시 — 가장 큰 영향) |
| **로직 변경** | .py + (변경 영향 외부 없음 — 안전) |
| **폐기** | 위 전체 + Spec 32 status `deprecated` + 의존 Tool 영향 분석 |

→ 더 깊은 절차 = [agent_specs/41 §4 매트릭스](../agent_specs/41_agent_tool_change_hub_v1.0.md) + [40 §3.A/B](../agent_specs/40_agent_tool_lifecycle_v1.0.md).

## 참조 코드
- 구현 .py
- 메타 YAML
- helpers / utils

## 참조 spec
- agent_specs / TOBE_MVP / data/description

## 참조 비전 (한국어 narrative)
- [agent_design/0X_<에이전트>.md](../_claude/referrence/agent_design/) — Tool 의 비전 의도

## 📍 Mock vs 실API 분기 (Phase 6+ 마크) ⚠️
- POC: mock 데이터 (data/mock/) 사용
- MVP+: 외부 API 전환 — `USE_MOCK_DATA` env 분기 (Phase 6+)
- 전환 절차: [agent_specs/40 §3.D](../agent_specs/40_agent_tool_lifecycle_v1.0.md) + [data/description/mock/ROADMAP](../../data/description/mock/ROADMAP.md)
- 데이터 ERD: [data/description/mock/RELATIONSHIPS.md §1 Mermaid](../../data/description/mock/RELATIONSHIPS.md)

## 테스트
- 단위 / integration 위치
- DC-10 Status 3중 정합

## Phase
- 본 Tool 의 Phase 진입 (1A/2/3/4 등)

## 변경 이력
| 날짜 | 변경 |
```

---

## 4. 갱신 정책

| 트리거 | 갱신 대상 |
|---|---|
| Tool 신규 implemented | `tools/implemented/<name>.md` 신규 + 해당 agent 카드의 Tool 목록 갱신 |
| Tool rename | 양쪽 카드 rename + 변경 이력 추가 |
| Tool 폐기 | 카드에 `Status: deprecated` + 폐기 시점 박제 후 `tools/_archive/` 이동 |
| 에이전트 구조 변경 (D9/D13 같은) | `agents/` 의 영향 받는 카드 + 00_overview + INDEX 동시 갱신 |
| 새 stub → implemented 승급 | `tools/stub/` → `tools/implemented/` 이동 + 카드 내용 보강 |
| 데이터 source 변경 | 의존 Tool 카드의 "데이터 source" 절 갱신 |

---

## 5. 다른 자료와의 정합

| 외부 자료 | 본 폴더와 관계 |
|---|---|
| `agent_specs/32` | **요약 표** — 본 폴더는 깊이 (cross-link) |
| `agent_specs/31` | **요구사항** — 본 폴더는 실 구현 매핑 |
| `agent_specs/17` | **종단 매핑** — 본 폴더 카드의 "참조 spec" link |
| `TOBE_MVP/01 매트릭스` | **Tool ↔ Data 표** — 본 폴더 Tool 카드의 "데이터 source" 와 cross-link |
| `TOBE_MVP/02 agent_cards` | **짧은 카드** — 본 폴더는 깊은 카드 (1차 진입은 TOBE_MVP, 깊이는 본 폴더) |
| `agent_design/` | **비전 narrative (한국어)** — 본 폴더 카드의 "참조 spec" 행에 link |
| 코드 (`tools/*.py`) | **진실 소스** — 본 폴더는 요약 + link |

→ 본 폴더 갱신 시 외부 자료도 동시에 갱신 필요한 항목 = [41 §4 변경 종류별 매트릭스](../agent_specs/41_agent_tool_change_hub_v1.0.md) 참조.

---

## 6. 진입 추천

| 시나리오 | 어디부터 |
|---|---|
| **본 폴더 처음 진입** | [00_overview.md](00_overview.md) (10 에이전트 + 46 Tool 한눈) |
| 특정 에이전트 깊이 | [agents/<NN>_<name>.md](agents/) |
| 특정 Tool 깊이 | [tools/implemented/<name>.md](tools/implemented/) |
| FAQ / 분야별 진입점 | [INDEX.md](INDEX.md) |
| 시스템 전체 spec | [../agent_specs/INDEX.md](../agent_specs/INDEX.md) |
| 변경 작업 시작 | [../agent_specs/41 Change Hub](../agent_specs/41_agent_tool_change_hub_v1.0.md) |

---

## 7. 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-05-19 | 폴더 신규 — Step 1 (README + 00_overview + INDEX). agents/ + tools/implemented/ + tools/stub/ 골격. |
