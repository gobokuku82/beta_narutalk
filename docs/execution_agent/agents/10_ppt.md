# 10. ppt_agent ⭐ — PPT 슬라이드 + 시각 디자인

## 메타

| 항목 | 값 |
|---|---|
| 소속 팀 | analysis_team |
| handles_tasks | `report_generation` |
| Tool 수 | 0 implemented + 3 stub |
| 현재 구현률 | 0% (Phase 4C 진입 시) |
| team_catalog 위치 | `ppt_agent` 블록 (**D13 Y 신규** — 큰 별도 책임) |
| 책임 범위 | **PPT 슬라이드 + 시각 디자인 + 발표용** — PDF/Word/Excel 과 다른 도구·로직 |
| 분리 이유 | 사용자 결정 — "PPT 제작은 하나로 크게 빼야 함" |

## 입출력

- **입력**: `report_markdown` (report_text_agent 출력) + `chart_image_paths` (pdf_agent.chart_generator 출력) + `brand_style` (D10)
- **출력**: `pptx_file_path` + `designed_pptx_path` (디자인 적용 후)
- **다음 에이전트**: 채팅 (HITL — 생성 후 다운로드 또는 외부 발송)

## Tool 목록 (Phase 4C 신규)

| Tool | Status | 도구 | 비고 |
|---|---|---|---|
| pptx_generator | 🟡 stub | **python-pptx** (신규 도입) | 슬라이드 구조 + 텍스트 + 차트 배치 |
| slide_designer | 🟡 stub | python-pptx + 브랜드 컬러 | 레이아웃·색·폰트 — 브랜드 적용 |
| chart_to_slide | 🟡 stub | python-pptx | 분석 결과 차트 → 슬라이드 배치 |

## PPT 의 특수성 (PDF 와 다른 점)

| 영역 | PPT | PDF |
|---|---|---|
| 단위 | 슬라이드 (장표) | 연속 페이지 |
| 시각 강조 | 매우 높음 (디자인 + 레이아웃) | 텍스트 중심 |
| 용도 | 발표용 | 인쇄/공유 |
| 도구 | python-pptx | reportlab / weasyprint |
| 데이터 흐름 | report_markdown + chart + brand_style → 슬라이드 단위 분해 | report_markdown + chart → PDF 연속 페이지 |

## 데이터 흐름

```
[report_markdown from report_text_agent]
       │
       ▼
chart_to_slide (분석 결과 → 슬라이드 단위)
       │ chart_slides
       │
       ▼
pptx_generator (슬라이드 구조 + 텍스트 + 차트)
       │ pptx_file_path
       │
       ▼
slide_designer (브랜드 컬러 + 폰트 + 레이아웃)
       │ designed_pptx_path
       │
       ▼
HITL: [확인] [수정요청] [다운로드] [외부 발송 — 별도 승인]
```

## HITL 카테고리 (D12)

| 카테고리 | 본 에이전트 해당 |
|---|---|
| 생성 후 | ✅ (PPT 완성 후 마케터 검토) |
| 외부 발송 | △ (클라이언트 발표용 — 별도 승인) |

## Phase 진입

| Phase | 본 에이전트의 작업 |
|---|---|
| Phase 0 (현재) | 🟡 **team_catalog entry 박제 완료** (2026-05-18, commit 8ce2f3d) — Tool 0 |
| **Phase 4C** ⭐ | 3 Tool 신규. python-pptx 도입. report_text_agent (Phase 0) + pdf_agent.chart_generator (Phase 4C 공용) 의존 |

## ⚠️ 수정 시 함께 변경 영역

| 영역 | 파일 | 변경 시 |
|---|---|---|
| Tool 코드 | `tools/ppt/` (Phase 4C 신규 폴더) | 신규 |
| Tool YAML | `tools/catalog/ppt/` (Phase 4C 신규) | 신규 |
| **team_catalog.yaml** | `ppt_agent` 블록 (D13 Y) | Tool 추가 |
| **LLM Prompts stage3** | `planning_stage3_todo.yaml` | ppt Tool 이름 + 예시 (`output_format=ppt` 분기) — 이미 PPT example 박제 (2026-05-18) |
| **task_agent_hints** | `team_catalog.yaml` L241 `report_generation: [..., ppt_agent]` | 변경 없음 |
| **chart_generator 공용** | pdf_agent.chart_generator 의 결과 재사용 | Phase 4C |
| **외부 의존성** | python-pptx (신규 라이브러리) | requirements.txt |
| **브랜드 디자인 자산** | `mock_data_brand_style.csv` (D10, 사용자 작업 중) | slide_designer 의존 |
| **Spec 32 §7.1** | ppt 카테고리 행 (신규 카테고리) | Phase 4C 진입 시 |
| **TOBE_MVP/01** | 매트릭스 ppt 행 (이미 박제 — 2026-05-18) | |
| **데이터 source** | report_markdown + chart_images + brand_style | |
| **agent_design 갱신** | agent_design 에는 PPT 명시 없음 — 갱신 권장 (D14 — 사용자 추가 비전) | |
| **ADR** | ⭐ ADR-XXX PPT 에이전트 분리 (D13 Y 박제) + python-pptx 도입 + slide 디자인 시스템 |
| Tests | `backend/tests/sprint*/test_*ppt*.py` | |

## 참조 코드

- Tool 폴더: (Phase 4C 시 `tools/ppt/` 신규)
- team_catalog: `ppt_agent` 블록 (D13 Y 신규)
- LLM Prompts: [`planning_stage3_todo.yaml`](../../../backend/app/dream_agent/llm_manager/prompts/planning_stage3_todo.yaml) PPT example 박제 (2026-05-18)

## 참조 spec

- [17 §2.2 ppt (D13 Y)](../../agent_specs/17_functions_to_io_v1.0.md)
- [32 §7.1](../../agent_specs/32_execution_agent_tools_v1.0.md) — Phase 4C 진입 시 ppt 카테고리 행 추가
- [TOBE_MVP/02 ppt 카드](../../_claude/tool/TOBE_MVP/02_agent_cards.md)
- [TOBE_MVP/03 D13](../../_claude/tool/TOBE_MVP/03_drift_report.md) — Y 채택 박제

## 참조 비전 (한국어 narrative)

- (없음 — agent_design 에 PPT 별도 명시 X. D14 — 사용자 추가 비전. 향후 agent_design 에 §11_PPT_에이전트.md 추가 권장)

## 📍 Mock vs 실API 분기

- POC: python-pptx 호출 (라이브러리, 외부 API X)
- MVP+: Cloudinary / S3 (PPT 저장 + 외부 공유 link)

## Drift / 결정

- **D13** 🟢 Decided — Y 채택 (PPT 별도 분리, PDF/Word/Excel 은 pdf_agent 유지), 2026-05-18 (commit 8ce2f3d)
- **D10** 🟢 Decided — 브랜드 디자인 자산 (사용자 작업 중) — slide_designer 의존
- **D14** ⚠️ Pending — agent_design 비전 갱신 (PPT 에이전트 명시 추가)
- ADR (Phase 4C): PPT 분리 결정 박제 + python-pptx 도입 + slide 디자인 시스템

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-19 | 카드 초안 (D13 Y 신규 박제 — 큰 별도 책임). Phase 4C 진입 전 골격. |
