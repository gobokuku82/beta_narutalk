# 08. report_text_agent — markdown 보고서 텍스트 + LLM 스토리

## 메타

| 항목 | 값 |
|---|---|
| 소속 팀 | analysis_team |
| handles_tasks | `insight_generation` / `summary_generation` / `report_generation` |
| Tool 수 | 2 implemented + 0 stub (총 2) ✅ |
| 현재 구현률 | **100%** ✅ |
| team_catalog 위치 | `report_text_agent` 블록 (D13 신규) |

## 입출력

- **입력**: `insights` (analysis_agent.insight_extractor 출력) + analysis_results (전체) + `campaigns.목표` (LLM context)
- **출력**: `report_markdown` (markdown 텍스트, LLM 스토리 3단계) + `summary_text` (1줄 요약)
- **다음 에이전트**: pdf (PDF/Word/Excel 변환) + ppt (슬라이드 디자인) + (직접) 채팅 응답

## Tool 목록

| Tool | Status | 카드 | 비고 |
|---|---|---|---|
| report_writer | ✅ implemented (LLM) | [→](../tools/implemented/report_writer.md) | POC-09 AI 리포트 스토리 3단계 |
| summary_generator | ✅ implemented (LLM) | [→](../tools/implemented/summary_generator.md) | 짧은 요약 |

## LLM 스토리 3단계 (POC-09)

1. **핵심 성과** — 무엇이 달성됐는가
2. **원인 분석** — 왜 그렇게 됐는가
3. **다음 액션** — 무엇을 해야 하는가

→ agent_design §04 LLM 활용 원칙 + 환각 방지:
- 숫자는 prompt 에 직접 포함 (LLM 이 만들지 못하게)
- JSON 출력 강제 후 파싱
- "추정" / "가능성" 워터마크

## 데이터 흐름

```
[analysis_agent 9 모듈 결과]
       │ sentiment_distribution / top_keywords / insights / anomalies / ...
       ▼
report_writer (LLM)
       │ report_markdown (3단계 스토리)
       │
       ├──► summary_generator (LLM)
       │      │ summary_text (1줄)
       │      └──► 채팅 응답
       │
       ├──► pdf_agent.pdf_renderer
       │      │ pdf_file_path
       │
       └──► ppt_agent.pptx_generator
              │ pptx_file_path
```

## HITL 카테고리 (D12)

| 카테고리 | 본 에이전트 해당 |
|---|---|
| **생성 후** ⭐ | ✅ (리포트 초안 표시 후 [채택/거부/수정]) |

## Phase 진입

| Phase | 본 에이전트의 작업 |
|---|---|
| Phase 0 (현재) | ✅ 2 Tool implemented (구현률 100%) |
| **Phase 3** | POC-09 강화 — `insight_synthesizer` 신규 (스토리 종합) 검토 |
| **Phase 4C** | pdf / ppt 와 데이터 흐름 검증 |

## ⚠️ 수정 시 함께 변경 영역

| 영역 | 파일 | 변경 시 |
|---|---|---|
| Tool 코드 | `tools/report/report_writer.py` + `tools/shared/summary_generator.py` ⚠️ shared 폴더에 있지만 report_text 소속 | LLM prompt / 스토리 구조 |
| Tool YAML | `tools/catalog/report/` + `tools/catalog/shared/` | params/produces |
| **team_catalog.yaml** | `report_text_agent` 블록 (D13 신규) | Tool 추가 |
| **LLM Prompts stage3** | `planning_stage3_todo.yaml` | report 예시 todo + agent 이름 (report_text_agent) |
| **task_agent_hints** | `team_catalog.yaml` L240-242 `insight_generation` / `summary_generation` / `report_generation` → report_text_agent | 매핑 갱신 |
| **LLM 호출** | `llm_manager/client.py` | LLM provider 변경 시 |
| **Spec 32 §7.1** | report 카테고리 행 | |
| **TOBE_MVP/01** | 매트릭스 report_text 행 | |
| **데이터 source** | (이전 Tool 출력 + `campaigns.목표` LLM context) | |
| **report_writer prompt** | `llm_manager/prompts/` (선택 — 별도 prompt yaml 신설 가능) | LLM 스토리 정밀화 시 |
| **ADR** | LLM 스토리 정밀화 / 다국어 / 멀티 클라이언트 톤 | |
| Tests | `backend/tests/sprint*/test_*report_writer*/*summary*.py` | |

## 참조 코드

- report_writer: [`tools/report/report_writer.py`](../../../backend/app/dream_agent/tools/report/report_writer.py)
- summary_generator: [`tools/shared/summary_generator.py`](../../../backend/app/dream_agent/tools/shared/summary_generator.py) ⚠️ shared 폴더 (Tool 폴더 위치와 소속 에이전트 불일치 — 폴더는 카테고리, 소속은 team_catalog 기준)
- Tool YAML: [`tools/catalog/report/`](../../../backend/app/dream_agent/tools/catalog/report/) + [`tools/catalog/shared/`](../../../backend/app/dream_agent/tools/catalog/shared/)
- team_catalog: `report_text_agent` 블록 (D13)

## 참조 spec

- [17 §2.2 9~10 에이전트](../../agent_specs/17_functions_to_io_v1.0.md)
- [32 §7.1 report 카테고리](../../agent_specs/32_execution_agent_tools_v1.0.md)
- [31 §Agent 4](../../agent_specs/31_execution_agent_function_list_v0.6.md) — report_agent (옛 — D13 분리됨)
- [TOBE_MVP/02 report_text 카드](../../_claude/tool/TOBE_MVP/02_agent_cards.md)
- [TOBE_MVP/03 D13](../../_claude/tool/TOBE_MVP/03_drift_report.md) — 레포팅 2갈래 분리 결정

## 참조 비전 (한국어 narrative)

- [agent_design/04_분석_에이전트.md §POC-09](../../_claude/referrence/agent_design/04_분석_에이전트.md) — AI 리포트 스토리 비전

## 📍 Mock vs 실API 분기

- 외부 API: **LLM (Anthropic Claude / OpenAI GPT)** 의존
- POC: 동일 LLM 호출 (mock 불가)
- MVP+: 멀티 클라이언트 톤 학습 (Phase 2차 — 별도)

## Drift / 결정

- **D13** 🟢 Decided — 레포팅 2갈래 분리 (report_text + pdf + ppt 분리, 2026-05-18)
- ADR-022 (예정): POC → MVP 로드맵 박제

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-19 | 카드 초안 (D13 분리 박제, 2 Tool 100% 구현) |
