# 33. Report tools — 인벤토리

| 항목 | 내용 |
|---|---|
| 카테고리 | **report** (보조 카테고리, 32 §2.5) |
| 의도 | 분석 결과를 사람이 읽는 텍스트(요약·보고서)로 산출 |
| 핵심 동사 | summarize, narrate, format |
| 출력 모양 | text (markdown 또는 plain) |
| 짝 문서 | [32 §2.5](../32_execution_agent_tools_v1.0.md) |
| tool 수 | **2** (2026-05-31) |

## 판정 기준 (vs analysis)

- **데이터에서 새 의미 도출** (감성·키워드·점수) = **analysis**
- **이미 산출된 결과를 종합·서술** (요약·보고서) = report ✅
- 둘 다 LLM 호출 가능. 차이 = *raw 분석* 인가, *결과 종합* 인가.

## tool 목록

| name | input | output | status | 의도 |
|---|---|---|---|---|
| report_writer | analysis_results · insights · top_keywords | report_markdown (긴 보고서) | complete | 마크다운 형식 상세 보고서 작성 (LLM 스토리 3단계) |
| summary_generator | previous_results | summary (한 문장) | complete | 분석 결과 전체를 한 문장(기본 100자) 한국어 요약 |

## team_catalog 등록

분석 team 의 **report_text_agent** 에 등록 (`handles_tasks: insight_generation·summary_generation·report_generation`).

## 향후 진입 후보

| 후보 tool | 의도 |
|---|---|
| `executive_summary` | C-level 1쪽 요약 |
| `slide_outline` | 발표용 슬라이드 outline |
| `email_digest` | 이메일 다이제스트 텍스트 |

→ PDF/이미지 생성(pdf_agent·image_creation_agent) 은 별 카테고리(planned).

## anti-pattern

- **데이터 분석 끼움** — sentiment·keywords 산출 + 보고서 작성 동시. → analysis 가 산출, report 가 종합.
- **시각 spec 생성** — chart spec(vega-lite 등)은 frontend 책임 — report tool 은 텍스트만.

## 변경 이력

- 2026-05-30: summary_generator 가 shared/ (helper 카테고리 위반) → report/ 로 이동. 32 §2.5 "shared = helper only" 박제 정합.
