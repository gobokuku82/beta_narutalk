# 09. pdf_agent — PDF / Word / Excel 텍스트 기반 출력물 통합

## 메타

| 항목 | 값 |
|---|---|
| 소속 팀 | analysis_team |
| handles_tasks | `report_generation` |
| Tool 수 | 0 implemented + 5 stub |
| 현재 구현률 | 0% (Phase 4C 진입 시) |
| team_catalog 위치 | `pdf_agent` 블록 (D13 — PDF/Word/Excel 통합) |
| 책임 범위 | **텍스트 기반 출력물** (PDF + Word + Excel) — PPT 는 별도 ppt_agent (D13 Y) |

## 입출력

- **입력**: `report_markdown` (report_text_agent 출력) + 분석 결과 (차트용)
- **출력**: `pdf_file_path` / `word_file_path` / `excel_file_path`
- **다음 에이전트**: 채팅 (HITL — 생성 후 다운로드 또는 외부 발송)

## Tool 목록 (Phase 4C 신규)

| Tool | Status | 도구 | 비고 |
|---|---|---|---|
| pdf_renderer | 🟡 stub | reportlab / weasyprint | markdown → PDF |
| chart_generator | 🟡 stub | matplotlib / plotly | 시각화 차트 (PDF + ppt_agent 공용) |
| template_selector | 🟡 stub | Jinja2 + 브랜드 컬러 | PDF 템플릿 선택 (D10 의존) |
| word_template_filler | 🟡 stub | python-docx | Word 양식 채우기 |
| excel_template_filler | 🟡 stub | openpyxl | Excel 양식 채우기 |

## 4 종 PDF (agent_design §07)

| 종류 | 대상 | 트리거 |
|---|---|---|
| 성과 보고서 (주/월) | 클라이언트 | 리포트 화면 "생성" |
| 클라이언트 제안서 | 클라이언트 | 채팅 "제안서 만들어줘" |
| 스토리보드 PDF | 디자이너·영상팀 | storyboard 완료 후 자동 (storyboard_agent 호출) |
| 내부 분석 리포트 | 내부 | 채팅 "내부 분석 리포트" |

## 데이터 흐름

```
[report_markdown from report_text_agent]
       │
       ▼
chart_generator (분석 결과 시각화)
       │ chart_image_paths
       │
       ▼
template_selector (브랜드 컬러 — D10)
       │ template_choice
       │
       ▼
pdf_renderer (markdown + chart + template)
       │ pdf_file_path
       │
       │ (Word/Excel 양식 업로드 시)
       ├──► word_template_filler → word_file_path
       └──► excel_template_filler → excel_file_path
       │
       ▼
HITL: [확인] [수정요청] [다운로드] [외부 발송 — 별도 승인]
```

## HITL 카테고리 (D12)

| 카테고리 | 본 에이전트 해당 |
|---|---|
| 생성 후 | ✅ (PDF/Word/Excel 완성 후 검토) |
| **외부 발송** | △ (월간 리포트 클라이언트 발송 시) — 별도 승인 |

## Phase 진입

| Phase | 본 에이전트의 작업 |
|---|---|
| Phase 0 (현재) | 🟡 폴더만 (`tools/pdf/`) — Tool 0 |
| **Phase 4C** ⭐ | 5 Tool 신규. report_text_agent (Phase 0 완료) 의존. ppt_agent 와 chart_generator 공용 |

## ⚠️ 수정 시 함께 변경 영역

| 영역 | 파일 | 변경 시 |
|---|---|---|
| Tool 코드 | `tools/pdf/` (현재 빈 폴더) | 신규 |
| Tool YAML | `tools/catalog/pdf/` | 신규 |
| **team_catalog.yaml** | `pdf_agent` 블록 (D13) | Tool 추가 |
| **LLM Prompts stage3** | `planning_stage3_todo.yaml` | pdf Tool 이름 + 예시 (`output_format=pdf` 분기) |
| **task_agent_hints** | `team_catalog.yaml` L241 `report_generation: [report_text_agent, pdf_agent, ppt_agent]` 3 갈래 | 변경 없음 |
| **chart_generator (공용)** | ppt_agent 와 공용 — 위치 결정 (pdf 소속 vs shared) | Phase 4C 진입 시 |
| **외부 의존성** | reportlab / weasyprint / matplotlib / plotly / python-docx / openpyxl | requirements.txt 추가 |
| **브랜드 디자인 자산** | `mock_data_brand_style.csv` (D10, 사용자 작업 중) | D10 도착 후 |
| **Spec 32 §7.1** | pdf 카테고리 행 | |
| **TOBE_MVP/01** | 매트릭스 pdf 행 | |
| **데이터 source** | report_markdown + 분석 결과 (차트용) | |
| **ADR** | Phase 4C 결정 — reportlab vs weasyprint / chart 라이브러리 / 브랜드 컬러 자동 추출 |
| Tests | `backend/tests/sprint*/test_*pdf*.py` | |

## 참조 코드

- Tool 폴더 (빈): [`tools/pdf/`](../../../backend/app/dream_agent/tools/pdf/)
- team_catalog: `pdf_agent` 블록 (D13)

## 참조 spec

- [17 §2.2 pdf](../../agent_specs/17_functions_to_io_v1.0.md)
- [32 §7.1 pdf 카테고리](../../agent_specs/32_execution_agent_tools_v1.0.md)
- [31 §Agent 5](../../agent_specs/31_execution_agent_function_list_v0.6.md) — pdf_agent (옛 — D13 통합 확장)
- [TOBE_MVP/02 pdf 카드](../../_claude/tool/TOBE_MVP/02_agent_cards.md)

## 참조 비전 (한국어 narrative)

- [agent_design/07_PDF_에이전트.md](../../_claude/referrence/agent_design/07_PDF_에이전트.md) — 4 종 PDF + 기술 구현

## 📍 Mock vs 실API 분기

- POC: 라이브러리 호출 (reportlab/weasyprint) — 외부 API X
- MVP+: Cloudinary / S3 (PDF 저장) — 환경변수 분기

## Drift / 결정

- **D13** 🟢 Decided — pdf_agent 가 PDF + Word + Excel 통합 흡수 (D13 Y, 2026-05-18)
- **D10** 🟢 Decided — 브랜드 디자인 자산 (사용자 작업 중) — template_selector 의존
- ADR (Phase 4C): PDF/Word/Excel 라이브러리 선정 + 브랜드 컬러 추출 (D8 RAG 의존 가능)

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-19 | 카드 초안 (D13 분리 — Word/Excel 흡수 박제) |
