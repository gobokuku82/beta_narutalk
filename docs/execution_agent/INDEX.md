# INDEX — docs/execution_agent/ 분야별 진입점

> **본 폴더 내부 navigation**. 어디 봐야 할지 모를 때 첫 진입.
>
> 외부 spec 진입점 = [agent_specs/42 Quick Navigation](../agent_specs/42_quick_navigation_v1.0.md).

---

## 1. 폴더 안 진입점

| 파일 | 무엇 |
|---|---|
| [README.md](README.md) | 폴더 목적 + 카드 템플릿 + 갱신 정책 |
| [00_overview.md](00_overview.md) | ⭐ **10 에이전트 + ~46 Tool 한 페이지 지도** |
| [01_progress_matrix.md](01_progress_matrix.md) | ⭐ **버전별 진행 매트릭스** (v0.x → MVP) + 피벗 시나리오 |
| (현재) INDEX.md | 분야별 진입점 + FAQ |

### agents/ — 에이전트 카드 10개

| # | 카드 | Tool 수 (impl/total) |
|---|---|---|
| 01 | [chat_hub](agents/01_chat_hub.md) | (Cognitive 내부) |
| 02 | [collection](agents/02_collection.md) | 1/4 |
| 03 | [text_preprocessing](agents/03_text_preprocessing.md) | 1/1 (통합) |
| 04 | [channel_normalizing](agents/04_channel_normalizing.md) | 1/5 |
| 05 | [analysis](agents/05_analysis.md) | 3/5 + 6 POC stub |
| 06 | [image](agents/06_image.md) | 0/6 |
| 07 | [storyboard](agents/07_storyboard.md) | 0/3 |
| 08 | [report_text](agents/08_report_text.md) | 2/2 ✅ |
| 09 | [pdf](agents/09_pdf.md) | 0/5 |
| 10 | [ppt](agents/10_ppt.md) ⭐ | 0/3 |

### tools/implemented/ — 동작 검증된 8개

| Tool | Agent | 카드 |
|---|---|---|
| review_collector | collection | [→](tools/implemented/review_collector.md) |
| format_normalizer | channel_normalizing | [→](tools/implemented/format_normalizer.md) |
| text_preprocessor | text_preprocessing | [→](tools/implemented/text_preprocessor.md) |
| sentiment_analyzer | analysis | [→](tools/implemented/sentiment_analyzer.md) |
| keyword_extractor | analysis | [→](tools/implemented/keyword_extractor.md) |
| insight_extractor | analysis | [→](tools/implemented/insight_extractor.md) |
| report_writer | report_text | [→](tools/implemented/report_writer.md) |
| summary_generator | report_text | [→](tools/implemented/summary_generator.md) |

### tools/stub/ — 미구현 (Phase 진입 시 채움)

(현재 비어있음. Phase 1A 진입 시 youtube_collector 등 추가 시작.)

---

## 2. FAQ — 어디 봐야 하나

### 본 폴더 안

| 질문 | 가는 곳 |
|---|---|
| "10 에이전트 전체 어떻게 구성?" | [00_overview.md](00_overview.md) §1~§2 |
| "어느 Tool 이 implemented?" | [00_overview.md §3](00_overview.md) |
| "Phase 별 우선순위 stub Tool?" | [00_overview.md §4](00_overview.md) |
| "특정 에이전트 깊이 정보?" | [agents/<NN>_<name>.md](agents/) |
| "특정 Tool 입출력 / 로직 / 코드?" | [tools/implemented/<name>.md](tools/implemented/) |

### 본 폴더 밖

| 질문 | 가는 곳 |
|---|---|
| "변경 작업 시작" | [agent_specs/41 Change Hub](../agent_specs/41_agent_tool_change_hub_v1.0.md) |
| "Tool 추가 절차 step-by-step" | [agent_specs/32 §9](../agent_specs/32_execution_agent_tools_v1.0.md) + [40 §3.A](../agent_specs/40_agent_tool_lifecycle_v1.0.md) |
| "Tool I/O 메커니즘 (params/produces)" | [agent_specs/17 §5](../agent_specs/17_functions_to_io_v1.0.md) |
| "기능 → 에이전트 → 툴 종단 매핑" | [agent_specs/17](../agent_specs/17_functions_to_io_v1.0.md) |
| "Tool ↔ Data 매핑 표" | [TOBE_MVP/01](../_claude/tool/TOBE_MVP/01_tool_data_matrix.md) |
| "데이터 source / mock CSV" | [data/description/mock/SCHEMA](../../data/description/mock/SCHEMA.md) |
| "비전 narrative (한국어)" | [_claude/referrence/agent_design/](../_claude/referrence/agent_design/) |
| "Drift / 결정" | [TOBE_MVP/03 Drift](../_claude/tool/TOBE_MVP/03_drift_report.md) + [agent_specs/adr/](../agent_specs/adr/) |
| **"MVP 진실 소스 (사용자 명세) vs 우리 박제"** ⭐ | [TOBE_MVP/05 양립 박제](../_claude/tool/TOBE_MVP/05_tool_inventory_dual.md) — 이미지 42 + 우리 30 영역별 대조 + 결정 보류 8 영역 |
| **"P1/P2/P3 Fix Plan — collection · normalize · HITL"** ⭐ | [TOBE_MVP/06 fix plan](../_claude/tool/TOBE_MVP/06_collection_normalize_fix_plan_2026-05-19.md) — 사용자 채팅 2 시나리오 발견 갭 + UX 겸 코드 수정 계획 (P1 상세 + P2/P3 개요) |
| **"분석 Tool 13 종합 plan — 마케터 요구 8 항목"** ⭐ | [TOBE_MVP/07 analysis tools design](../_claude/tool/TOBE_MVP/07_analysis_tools_design_2026-05-20.md) — channel_performance / funnel / CAC / kpi_anomaly / fatigue 등 13 Tool 의 우선순위 + 의존 + Phase 3.A~D 단계 plan |
| **"5 단계 Master Plan (사용자 확정 2026-05-20)"** ⭐⭐ | [TOBE_MVP/08 master plan](../_claude/tool/TOBE_MVP/08_master_plan_2026-05-20.md) — 설계→구현→E2E→수집고도화→분석고도화. 단계 1 ✅ + 단계 2~5 진입 plan + ADR 정합 매트릭스 |
| **"Computed Metrics Layer — Tool 책임 외 영역"** ⭐⭐ | [TOBE_MVP/09 computed metrics](../_claude/tool/TOBE_MVP/09_computed_metrics_layer_2026-05-20.md) + [ADR-020](../agent_specs/adr/ADR-020_computed_metrics_layer.md) — 단순 계산은 Tool 영역 X (frontend/backend metrics). 07 plan 13→9 Tool 재정정 |
| "POC → MVP 로드맵" | [_claude/tool/03_gap_and_roadmap](../_claude/tool/03_gap_and_roadmap.md) |
| **"Status 마커 + DC-10 검증"** | [feedback_code_status_markers 메모리](C:/Users/gobok/.claude/projects/c--kdy-Projects-octormate-beta-v001/memory/feedback_code_status_markers.md) + [tests/docs/test_doc_code_contract.py](../../backend/tests/docs/test_doc_code_contract.py) (DC-10 검증 코드) |
| **"HITL 4 카테고리"** | [02_to_be_mvp §7](../_claude/tool/02_to_be_mvp.md) + [03 Drift D12](../_claude/tool/TOBE_MVP/03_drift_report.md) |
| **"Phase 진입 매트릭스"** | [00_overview §8](00_overview.md) + [03_gap_and_roadmap](../_claude/tool/03_gap_and_roadmap.md) |
| **"데이터 ERD (시트 간 관계)"** ⭐ | [data/description/mock/RELATIONSHIPS.md §1 Mermaid ERD](../../data/description/mock/RELATIONSHIPS.md) — 12 CSV ERD + 강한/약한 관계 + ASCII 그림 |
| **"Mock vs 실API 분기 (Phase 6+)"** | [agent_specs/40 §3.D](../agent_specs/40_agent_tool_lifecycle_v1.0.md) + [data/description/mock/ROADMAP](../../data/description/mock/ROADMAP.md) |
| **"비전 narrative (한국어)"** | [_claude/referrence/agent_design/](../_claude/referrence/agent_design/) — 에이전트 8 + design_csv 8 |

---

## 3. 자주 가는 코드 link

| 영역 | 위치 |
|---|---|
| **Planner 진실 소스** | [planning/catalog/team_catalog.yaml](../../backend/app/dream_agent/planning/catalog/team_catalog.yaml) |
| Tool 코드 | [tools/<category>/](../../backend/app/dream_agent/tools/) |
| Tool 메타카드 | [tools/catalog/<category>/](../../backend/app/dream_agent/tools/catalog/) |
| LLM Prompts | [llm_manager/prompts/](../../backend/app/dream_agent/llm_manager/prompts/) |
| BaseTool 계약 | [tools/base_tool.py](../../backend/app/dream_agent/tools/base_tool.py) |
| 자동 import | [tools/registry.py](../../backend/app/dream_agent/tools/registry.py) |
| Executor (I/O 룰) | [execution/executor.py](../../backend/app/dream_agent/execution/executor.py) |
| Helpers | [tools/shared/helpers.py](../../backend/app/dream_agent/tools/shared/helpers.py) |
| mock fallback | [execution/mock_tools.py](../../backend/app/dream_agent/execution/mock_tools.py) |

---

## 4. 카드별 cross-link 패턴

각 카드는 다음 4 영역으로 link:

```
[카드]
  ├── 참조 코드   → backend/app/dream_agent/...
  ├── 참조 spec   → docs/agent_specs/17/32/...
  ├── 참조 비전   → docs/_claude/referrence/agent_design/...
  └── Drift/결정  → docs/_claude/tool/TOBE_MVP/03_drift_report.md
```

→ 카드 1개에서 모든 관련 자료에 1 클릭으로 도달.

---

## 5. 갱신 정책

| 트리거 | 갱신 |
|---|---|
| Tool 신규 implemented | `tools/implemented/<name>.md` 신규 + 해당 agent 카드 + 00_overview 표 |
| Tool 폐기/rename | 양쪽 카드 변경 이력 + INDEX 갱신 |
| 새 에이전트 추가 | `agents/NN_<name>.md` + 00_overview + INDEX |
| 카드 템플릿 변경 | README.md + 모든 카드 일괄 |

상세 = [README §4 갱신 정책](README.md).

---

## 6. 작업 진입 추천

| 상황 | 추천 |
|---|---|
| 처음 진입 | [00_overview.md](00_overview.md) |
| 특정 Tool 작업 | [tools/implemented/<name>.md](tools/implemented/) |
| 새 Tool 추가 | [agent_specs/41 Change Hub](../agent_specs/41_agent_tool_change_hub_v1.0.md) → 본 폴더 신규 카드 |
| 에이전트 구조 변경 | [agent_specs/40 §3.C/E](../agent_specs/40_agent_tool_lifecycle_v1.0.md) + 본 폴더 카드 일괄 |

---

## 7. 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-05-19 | 폴더 신규 — Step 1 (README + 00_overview + INDEX) 골격. Step 2/3 진입 대기. |
