# ADR-016: 10 에이전트 구조 — preprocessing 2 분리 + 레포팅 2 갈래 (PPT 별도)

## Status

**Accepted** (2026-05-19) — D9 + D13 Y 결정 박제 후 team_catalog 갱신 commit 완료. 본 ADR = 사후 박제 (decision → code → ADR).

이전 이력:
- D9 Decided (2026-05-18 — 사용자 결정 "전처리 B 분리하는게 맞겠다")
- D13 Y Decided (2026-05-18 — 사용자 결정 "PPT 제작은 하나로 크게 빼야")
- commit 8ce2f3d (2026-05-19 — team_catalog 10 에이전트 구조 박제)
- commit 484f579 (2026-05-19 — execution_agent/ 폴더 신설 + agents/01~10 카드)
- 본 ADR (2026-05-19 — architectural decision 사후 박제)

## Context

### 사용자 의도 시나리오

`docs/_claude/referrence/agent_design/` 의 비전 narrative 8 에이전트 (chat_hub + 7 분석/콘텐츠):
1. chat_hub
2. collection
3. preprocessing
4. analysis
5. image
6. storyboard
7. report
8. (creative_team — 통합 명세 없음)

이 8 에이전트 구조에 대해 사용자가 작업 진행 중 두 번의 결정 발생:

### D9: preprocessing 2 분리 (2026-05-18)

**발견**: preprocessing agent 의 책임이 모호.
- "자연어 텍스트 정제" (review/blog/SNS 본문 — 언어 자원 측면)
- "광고 성과 컬럼 통합" (매체별 raw → 통일 스키마 — 마케팅 도메인 측면)

두 책임이 **다른 영역** (언어학 vs 마케팅 도메인). 단일 agent 로 묶으면 Tool 명단이 혼재.

**사용자 결정** (G1 답변):
> "2개 다 전처리이다... B 분리하는게 맞겠다"

→ preprocessing 1 agent → **text_preprocessing + channel_normalizing 2 agent** 분리.

### D13 Y: 레포팅 2 갈래 — PPT 별도 분리 (2026-05-18)

**발견**: 비전 narrative 의 "리포트 에이전트" 가 다양한 출력 형식 통합:
- markdown 텍스트 보고서
- PDF 출력
- Word 양식
- Excel 양식
- PPT 슬라이드 (시각 디자인 + 발표용)

PPT 의 특수성:
- 슬라이드 단위 (PDF/Word/Excel 의 연속 페이지와 다름)
- 시각 디자인 비중 매우 큼 (레이아웃 + 색 + 폰트)
- 도구 (python-pptx) 가 PDF (reportlab/weasyprint) 와 별개
- 용도 = 발표용 (PDF/Word/Excel = 인쇄/공유/내부 분석)

**사용자 결정** (D13 Y):
> "PPT 제작은 기능을 하나로 크게 빼야 할 것 같아 PPT 제작 에이전트로"

세부 결정:
- (a) PPT 에이전트가 PDF 흡수? → ❌ **별개 유지**
- (b) Word/Excel 어디로? → ✅ **PDF 에이전트에 흡수** (텍스트 기반 통합)
- (c) 스토리보드 PDF? → ✅ **PDF 에이전트가 처리**

→ 레포팅 = **report_text + pdf + ppt 3 갈래** (단, report_text 가 markdown 텍스트만 → pdf 와 ppt 둘 다 입력)

### 최종 10 에이전트 구조

| # | 에이전트 | 책임 | D 결정 |
|---|---|---|---|
| 1 | chat_hub | NL 라우팅 + 11 화면 컨텍스트 + HITL | 비전 박제 |
| 2 | collection | 매체별 raw 적재 (5 광고 + 4 콘텐츠 = 9 Tool) | 비전 박제 |
| 3 | text_preprocessing | 자연어 8 단계 정제 | **D9 신규** |
| 4 | channel_normalizing | 4 채널 광고성과 통합 (5 매체 raw → daily_performance) | **D9 신규** |
| 5 | analysis | 9 분석 모듈 (POC-01~09) | 비전 박제 |
| 6 | image | 광고 이미지 + 5축 채점 | 비전 박제 |
| 7 | storyboard | 영상 4 씬 스토리보드 | 비전 박제 |
| 8 | report_text | markdown 텍스트 + LLM 스토리 | **D13 신규** |
| 9 | pdf | PDF / Word / Excel 통합 출력 | **D13 신규** (Word/Excel 흡수) |
| 10 | ppt ⭐ | PPT 슬라이드 + 시각 디자인 (발표용) | **D13 Y 신규** (큰 별도) |

### 영향 — 단순 명명 변경이 아닌 구조적 결정

- **Tool 카탈로그 재배치**: 기존 preprocessing 의 Tool 들이 text 측 / channel 측으로 분리. 향후 신규 Tool 도 어느 agent 소속인지 결정 필요.
- **team_catalog.yaml 의 task_agent_hints**: `data_preprocessing` task 가 **2 agent 매핑** (Planner LLM 선택). `report_generation` task 가 **3 agent 매핑**.
- **implicit_prerequisites**: 분석 task 가 collection + preprocessing 선행 필요. preprocessing 분리 후에도 task type 자체는 단일 유지 (LLM 이 두 agent 중 선택).
- **LLM Prompts (stage2/stage3)**: agent 이름 enum 확장 + 예시 보강 필요.
- **테스트**: Planner E2E 가 새 agent 인식.

## Decision

**10 에이전트 구조 채택** (D9 preprocessing 2 분리 + D13 Y 레포팅 3 갈래 + ppt 별도).

### team_catalog.yaml 구조

```yaml
teams:
  analysis_team:  # 7 agent
    agents:
      collection_agent           # handles_tasks: [data_collection]
      text_preprocessing_agent   # handles_tasks: [data_preprocessing]  # D9 분리
      channel_normalizing_agent  # handles_tasks: [data_preprocessing]  # D9 분리
      analysis_agent             # handles_tasks: [sentiment, keyword, trend, ...]
      report_text_agent          # handles_tasks: [insight, summary, report]  # D13 신규
      pdf_agent                  # handles_tasks: [report_generation]  # D13 통합
      ppt_agent ⭐               # handles_tasks: [report_generation]  # D13 Y 신규

  creative_team:  # 4 agent (Q4 추후 정리 — image+storyboard 흡수 가능성)
    agents:
      image_agent / video_agent / copy_agent / material_agent
```

### task_agent_hints (LLM 가이드)

```yaml
data_preprocessing:    [text_preprocessing_agent, channel_normalizing_agent]  # ⭐ 2 갈래
insight_generation:    report_text_agent
summary_generation:    report_text_agent
report_generation:     [report_text_agent, pdf_agent, ppt_agent]              # ⭐ 3 갈래
```

→ Planner LLM 이 output_format / 사용자 의도 따라 적절한 agent 선택. 강제 아님 (hints).

### Tool 재배치 (10 에이전트 기준)

| Tool | 소속 | 비고 |
|---|---|---|
| text_preprocessor | text_preprocessing_agent | D9 분리 |
| format_normalizer | channel_normalizing_agent | D9 분리 — ads.v1 룰셋 박제 |
| insight_extractor | analysis_agent | (analysis 그대로) |
| report_writer | report_text_agent | D13 분리 — markdown 만 |
| summary_generator | report_text_agent | D13 분리 |
| pdf_renderer / chart_generator / template_selector / word_template_filler / excel_template_filler | pdf_agent | D13 통합 |
| pptx_generator / slide_designer / chart_to_slide | ppt_agent | D13 Y 신규 |

## Consequences

### 긍정 (+)

- **책임 명확화** — text 측 (언어 자원) vs channel 측 (마케팅 도메인) 분리. 향후 Tool 추가 시 소속 결정 명확
- **PPT 의 특수성 반영** — 시각 디자인 + 발표용 = 별도 에이전트 책임. python-pptx + slide_designer 자연스러움
- **확장성** — 매체별 collector 5 (광고) + 4 (콘텐츠) 의 raw_ads / raw_reviews 분기 자연스러움 (D9 의 channel_normalizing 가 ads 도메인 책임)
- **Planner LLM 자유도** — task_agent_hints 의 다중 매핑으로 LLM 이 output_format 따라 선택
- **테스트 격리성** — agent 별 Tool 명단 분리 = unit test 작성 명확

### 부정 (−)

- **agent 카운트 증가** — 8 → 10 (chat_hub 별개 시 7 → 9). team_catalog 복잡도 증가
- **task_agent_hints 의 다중 매핑** — Planner LLM 의 선택 부담 (어느 agent? — output_format 추출 필요)
- **implicit_prerequisites 의 task type 일관성** — data_preprocessing 1 task → 2 agent 매핑. LLM 이 어느 agent 호출할지 의사결정 필요
- **LLM Prompts 보강 부담** — stage2/3 의 agent enum + 예시 추가
- **Q4 (creative_team) 정리 미해결** — 사용자 명세 이미지 = image + storyboard 2 agent. 우리 team_catalog = 4 agent (image/video/copy/material). 추후 sprint

### 영향 범위

| 영역 | 변경 |
|---|---|
| **team_catalog.yaml** | 10 에이전트 블록 + task_agent_hints + implicit_prerequisites |
| **LLM Prompts** | stage2_agent.yaml + stage3_todo.yaml + response.yaml (agent 이름 enum + 예시) |
| **Tool 재배치** | report/ + shared/ + (Phase 4C 신규 pdf/ + ppt/) 폴더 |
| **execution_agent/agents/** | 10 카드 (01_chat_hub ~ 10_ppt) |
| **Spec 32 §7.1** | 카운트 / 현황표 |
| **Spec 31** | 요구사항 |
| **TOBE_MVP/02 agent_cards** | 짧은 카드 10 |
| **00_overview.md §2** | 표 (10 에이전트) |
| **데이터 source** | collection_agent 9 Tool 의 produces 분기 (raw_reviews / raw_ads) |
| **테스트** | Planner E2E / stage1~3 회귀 |

## Alternatives Considered

### 대안 1 — 비전 narrative 그대로 (8 에이전트, preprocessing 통합, report 통합)

- 장점: 단순. agent 수 적음.
- 단점:
  - preprocessing 의 책임 모호 (언어 vs 마케팅)
  - report 의 출력 형식 혼재 (markdown/PDF/PPT 같은 agent — 도구 분기 부담)
- **기각**: 사용자가 책임 명확화 요청 (D9 + D13 Y).

### 대안 2 — preprocessing 통합 + report 2 갈래 (text + 통합)

- 장점: D9 만 채택. agent 수 9.
- 단점: PPT 특수성 미반영. PDF 안에 PPT 도구 (python-pptx) 혼재.
- **기각**: PPT = 큰 별도 책임 (사용자 명시).

### 대안 3 — preprocessing 2 분리 + report 2 갈래 + ppt 별도 (채택)

- 장점: 책임 분리 명확. PPT 특수성 반영. 향후 Tool 명단 자연스러움.
- 단점: agent 10 (수용 가능).
- **채택**: D9 + D13 Y 모두 채택.

### 대안 4 — preprocessing 2 분리 + report 4 갈래 (text/pdf/word/excel/ppt 5)

- 장점: 모든 출력 형식 별도 agent.
- 단점: 과한 분리 (Word/Excel = 텍스트 기반 양식 → PDF agent 흡수 가능).
- **기각**: 단순화 우선 (D13 (b) Word/Excel → PDF 흡수).

## Related

- **D9 Drift**: [TOBE_MVP/03 §5 D9](../../_claude/tool/TOBE_MVP/03_drift_report.md) — 전처리 2 분리 결정 자취
- **D13 Drift**: [TOBE_MVP/03 §5 D13](../../_claude/tool/TOBE_MVP/03_drift_report.md) — 레포팅 2 갈래 + PPT 별도
- **D16 Drift**: [TOBE_MVP/03 §1 D16](../../_claude/tool/TOBE_MVP/03_drift_report.md) — 사용자 명세 이미지 (10 에이전트 동일, Tool 명단 차이)
- **D17 Drift**: 단일 collection_agent + Tool 폴더 분류 (D9 가 채택한 단일 agent 패턴과 정합)
- **execution_agent/agents/01~10**: 10 카드 박제
- **commit 8ce2f3d**: team_catalog 10 에이전트 구조 박제
- **commit 484f579**: execution_agent/ 폴더 22 파일 신설
- **commit aa0668d**: collection_agent 의 5 광고 + 4 콘텐츠 박제
- **사용자 비전**: [agent_design/](../../_claude/referrence/agent_design/) 한국어 narrative 8 에이전트 (D9/D13 으로 10 으로 진화)
- **사용자 명세 이미지**: 양립 박제 = [05_tool_inventory_dual](../../_claude/tool/TOBE_MVP/05_tool_inventory_dual.md)

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-05-19 | Accepted — 사후 박제 (D9 2026-05-18 + D13 Y 2026-05-18 결정 → team_catalog 박제 후 ADR 작성). 10 에이전트 구조의 architectural decision 자취. |
