# report_writer — LLM 마크다운 보고서 작성

> **D13 (레포팅 2갈래) 반영** — `report_text_agent` 소속 (텍스트 markdown 만).
> PDF/Word/Excel 출력은 `pdf_agent` (Phase 4C). PPT 는 `ppt_agent` (D13 Y, Phase 4C).

## 메타

| 항목 | 값 |
|---|---|
| 소속 에이전트 | report_text_agent (D13 분리) |
| 카테고리 (YAML) | `content` (폴더 `report/`) |
| Status | ✅ implemented |
| 버전 | 0.1.0 |
| **Status 마커** (docstring) | ⚠️ **미명시** — 권장: `Status: complete — POC LLM 3단 구성. MVP에서 스토리 다단계 확장.` |
| **DC-10 정합** | docstring ⚠️ / YAML status 필드 없음 / team_catalog `status: implemented` |
| timeout_sec | 90 |
| max_retries | 2 |
| requires_approval | false |
| has_cost / estimated_cost | **true / 0.02** (LLM 호출, 보고서 분량 ~500자) |

## 입출력 계약

### 입력 (params)
- 없음 (모든 입력은 context 에서 자동 수집)

### 입력 (context)
- `context.previous_results` 에서:
  - `find_in_previous(..., "sentiment_distribution")` → 감성 분포
  - `find_in_previous(..., "top_keywords")` → 키워드
  - `find_in_previous(..., "insights")` → 핵심 인사이트

### 출력 (produces)
- `report_text` (string) — markdown 형식 보고서 (3 단 구성)
- 보조: `word_count`, `char_count`

### 출력 dict 스키마

```json
{
  "report_text": "# 블루밍글로우 9월 리뷰 분석\n\n## 1. 핵심 성과 요약\n... (markdown)",
  "word_count": 87,
  "char_count": 542
}
```

## 데이터 source

- **입력**: 이전 분석 + 인사이트 Tool 3종 (sentiment_distribution + top_keywords + insights)
- **LLM 호출**: `get_llm_client("execution")`
- **프롬프트**: 본 Tool 내부 `SYSTEM_PROMPT` + `USER_TEMPLATE`
  - System: "당신은 한국 뷰티 브랜드의 마케팅 분석 보고서를 작성하는 전문 카피라이터입니다."
  - User: 3 데이터 JSON 임베드 + 구성 지시 (1.핵심 성과 / 2.원인 분석 / 3.액션 권고 3가지)

## 로직 단계

1. previous_results 에서 3 키 조회 (`find_in_previous`)
2. `USER_TEMPLATE.format(...)` — JSON 데이터 임베드 (`json.dumps(... ensure_ascii=False)`)
3. `client.generate(prompt, system_prompt)` 호출 → markdown 문자열
4. `len(text.split())` → word_count, `len(text)` → char_count
5. `logger.info(...)` + 반환

## 예외 처리

| 상황 | 동작 |
|---|---|
| 3 입력 모두 부재 | 빈 dict/list → 프롬프트에 빈 데이터 → LLM 일반론 응답 |
| insights 만 부재 | 다른 2종으로 보고서 작성 (구성 일부 누락 가능) |
| LLM 호출 실패 | `max_retries=2` 재시도 → 그래도 실패 시 raise |
| 응답이 markdown 아님 | 그대로 채택 (검증 없음) — 후속 Tool 영향 가능 |

## 의존 Tool

- **이전 (권장)**: `insight_extractor` (insights 의 main source)
- **이전 (보조)**: `sentiment_analyzer` + `keyword_extractor`
- **다음**:
  - `summary_generator` (report_text 도 함께 요약)
  - (Phase 4C) `pdf_agent.pdf_renderer` — markdown → PDF
  - (Phase 4C) `ppt_agent.pptx_generator` — markdown → 슬라이드 분해

## ⚠️ 수정 시 함께 변경 영역

| 영역 | 파일 | 어떤 변경 시 |
|---|---|---|
| Tool 코드 | [`tools/report/report_writer.py`](../../../../backend/app/dream_agent/tools/report/report_writer.py) | 로직 / 프롬프트 |
| Tool 메타카드 | [`catalog/report/report_writer.yaml`](../../../../backend/app/dream_agent/tools/catalog/report/report_writer.yaml) | params / produces / cost |
| **team_catalog.yaml** | `report_text_agent.tools[report_writer]` | params_required (현 `[analysis_results]` vs 실 코드 3종 — **간단화 박제**) / produces (`report_markdown` vs 실 `report_text` — **mismatch 박제**) |
| LLM Prompts (stage3) | `planning_stage3_todo.yaml` | Tool 이름 / 예시 |
| LLM Prompts (response) | `response.yaml` | 예시 |
| **프롬프트 SYSTEM/USER** | 본 Tool .py 상수 | 도메인 변경 / 구성 변경 |
| **Phase 4C pdf_agent 연동** | `pdf_renderer` 입력 = `report_markdown` (또는 `report_text`) | produces 키 통일 필요 |
| **Phase 4C ppt_agent 연동** | `pptx_generator` 입력 = `report_markdown` | 마찬가지 |
| **Spec 32 §7.1** | `agent_specs/32_*.md` | content 행 |
| **TOBE_MVP/01** | `tool/TOBE_MVP/01_tool_data_matrix.md` | Tool ↔ Data 행 |
| 본 폴더 agent 카드 | [`agents/08_report_text.md`](../../agents/08_report_text.md) | Tool 목록 |
| Tests | `backend/tests/sprint*/test_*report*.py` | unit (mock LLM) |

### 변경 종류별 최소 갱신
- **분량 변경 (500자 → 1000자)**: USER_TEMPLATE + timeout 조정 + cost 재산정
- **구성 변경 (3단 → 5단)**: USER_TEMPLATE + 시스템 프롬프트 + 예시 보강
- **produces 키 통일 (`report_text` → `report_markdown`)**: 본 Tool .py + YAML + team_catalog + pdf/ppt agent 입력 = 큰 변경 (다음 sprint)
- **다국어 (영문 보고서)**: SYSTEM 다국어 처리 + 사용자 입력 language param 추가

## 참조 코드

- 구현: [`tools/report/report_writer.py`](../../../../backend/app/dream_agent/tools/report/report_writer.py)
- 메타: [`catalog/report/report_writer.yaml`](../../../../backend/app/dream_agent/tools/catalog/report/report_writer.yaml)
- LLM client: [`llm_manager/client.py:get_llm_client`](../../../../backend/app/dream_agent/llm_manager/client.py)
- helper: [`shared/helpers.py:find_in_previous`](../../../../backend/app/dream_agent/tools/shared/helpers.py)

## 참조 spec

- [agent_specs/17 §3 report_text](../../../agent_specs/17_functions_to_io_v1.0.md)
- [agent_specs/32 §7.1 content](../../../agent_specs/32_execution_agent_tools_v1.0.md)
- [TOBE_MVP/01 §2 report](../../../_claude/tool/TOBE_MVP/01_tool_data_matrix.md)
- [TOBE_MVP/03 D13 Y](../../../_claude/tool/TOBE_MVP/03_drift_report.md) — 레포팅 2 갈래 (10 에이전트)

## 참조 비전 (한국어 narrative)

- [agent_design/07_PDF_에이전트.md](../../../_claude/referrence/agent_design/07_PDF_에이전트.md) — 보고서 비전 (D13 으로 text/PDF 분리)

## 📍 Mock vs 실API 분기

- **LLM API 의존** — 분기 없음 (POC 부터 실 API)
- 비용: 보고서 1개 ~0.02 USD (cost 박제됨)

## 테스트

- 단위 부재 (LLM mock 필요)
- E2E: Planner 가 report_text produces 검증
- DC-10: docstring Status 마커 미명시

## Phase

| Phase | 본 Tool 의 작업 |
|---|---|
| **Phase 0 (현재)** | ✅ implemented — 3단 구성 markdown |
| **Phase 4C** | pdf_agent / ppt_agent 와 연계 (report_text → PDF/PPT 변환 입력) |
| **MVP** | 스토리 다단계 (인사이트별 섹션 자동 분기) |

## Drift / 결정

- **D13 Y** 🟢 Decided — 레포팅 2 갈래 (text + pdf + **ppt 별도**)
- **team_catalog mismatch 박제**:
  - params_required `[analysis_results]` (단일) vs 실 코드 3종 (find_in_previous 3회)
  - produces `[report_markdown]` vs 실 `[report_text]` (키 mismatch)
  - 통일 권장 (다음 sprint)

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-19 | 카드 초안 — D13 분리 박제 + produces 키 mismatch 박제 + DC-10 갭 박제 |
