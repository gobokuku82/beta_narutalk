# 05. analysis_agent — 9 분석 모듈 (POC-01~09)

## 메타

| 항목 | 값 |
|---|---|
| 소속 팀 | analysis_team |
| handles_tasks | `sentiment_analysis` / `keyword_extraction` / `trend_analysis` / `competitor_comparison` / `causal_analysis` |
| Tool 수 | 3 implemented + 2 stub + POC-01~09 (~10 추가) |
| 현재 구현률 | ~30% (3 + 2 = 5 / 약 15) |
| team_catalog 위치 | `analysis_agent` 블록 |

## 입출력

- **입력**: `cleaned_texts` (text_preprocessing 출력) / `daily_performance` (channel_normalizing 출력) / 기타 mock CSV
- **출력**: 9 분석 모듈별 결과 (sentiment_distribution / top_keywords / insights / anomaly_alerts / forecast / ...)
- **다음 에이전트**: report_text (LLM 스토리 종합)

## Tool 목록

### 현 implemented + stub

| Tool | Status | 카드 |
|---|---|---|
| sentiment_analyzer | ✅ implemented (POC: 규칙) | [→](../tools/implemented/sentiment_analyzer.md) |
| keyword_extractor | ✅ implemented | [→](../tools/implemented/keyword_extractor.md) |
| insight_extractor | ✅ implemented (LLM) | [→](../tools/implemented/insight_extractor.md) |
| trend_analyzer | 🟡 stub | (Phase 3) |
| competitor_comparator | 🟡 stub | (예정) |

### POC 9 모듈 (Phase 2~3 신규)

| ID | 모듈 | 필요 Tool | 입력 CSV | Phase |
|---|---|---|---|---|
| POC-01 | KPI 이상 감지 | `kpi_anomaly_detector` | `daily_performance` (CPA 시계열) | Phase 2 |
| POC-02 | KPI 달성률 예측 | `kpi_forecaster` (선형외삽) | `daily_performance` + `campaigns.목표*` | Phase 3 |
| POC-03 | ROAS 원인 분석 | `roas_cause_analyzer` (규칙트리 Freq→올영세일→예산→픽셀) | `daily_performance` + `creatives.Frequency` + `external_variables` | Phase 2 |
| POC-04 | 소재 피로도 감지 | `fatigue_detector` (Freq≥3.5 ∧ CTR 2주 하락) | `creatives.Frequency/fatigue_score` + `daily_performance.CTR` | Phase 2 |
| POC-05 | A/B 테스트 판정 | `ab_test_runner` (proportion_ztest) | `ab_tests` | Phase 3 |
| POC-06 | 무전환 키워드 감지 | `zero_conv_keyword_detector` (클릭≥100 ∧ 전환=0) | `keyword_performance` | Phase 2 |
| POC-07 | 감성 분석 | `sentiment_analyzer` 강화 (POC: 규칙 / MVP: KoBERT) | `review_trends.감성/텍스트` | Phase 3 |
| POC-08 | 검색량 급등 감지 | `trend_spike_detector` (전주 +20%) | `naver_datalab` (없음 — D3) | Phase 3 (DataLab 도착 후) |
| POC-09 | AI 리포트 스토리 | `insight_synthesizer` + `report_writer` (report_text 흡수) | 위 8 결과 종합 | Phase 3 |

## 데이터 흐름

```
[cleaned_texts]                [daily_performance]
       │                              │
       ▼                              ▼
sentiment_analyzer (POC-07)    kpi_anomaly_detector (POC-01)
keyword_extractor              kpi_forecaster (POC-02)
                                roas_cause_analyzer (POC-03)
                                fatigue_detector (POC-04)
                                ab_test_runner (POC-05)
                                zero_conv_keyword_detector (POC-06)
                                trend_spike_detector (POC-08)
       │ sentiment_distribution            │ anomaly_alerts / forecast / ...
       │ top_keywords                       │
       └─────────────┬──────────────────────┘
                     ▼
            insight_extractor (LLM)
                     │ insights
                     ▼
            (POC-09) report_text_agent
                       └► report_writer → markdown
```

## LLM 활용 원칙 (agent_design §04)

| 사용 O | 사용 X |
|---|---|
| 분석 결과 → 한국어 1~2줄 변환 | 이상 감지 판정 → 규칙 / Z-score |
| 소재 5축 채점 (Vision) | A/B 통계 검정 → statsmodels |
| 리포트 스토리 (POC-09) | KPI 사칙연산 |
| 급등 키워드 → 소재 방향 제안 | Frequency 집계 → pandas |

→ **계산은 코드, 자연어는 LLM**.

## HITL 카테고리 (D12)

| 카테고리 | 본 에이전트 해당 | 사례 |
|---|---|---|
| 조회·자동 | ✅ (대부분) | KPI 이상감지 / ROAS 원인 / 피로도 / 감성 — 자동 알림 |
| 생성 후 | △ (POC-09 리포트) | 리포트 초안 표시 후 [채택/거부] |
| 실행 전 | △ (POC-05 / POC-06) | A/B 테스트 시작 / 무전환 키워드 중지 — 사전 승인 |
| 외부 발송 | — | |

## Phase 진입

| Phase | 본 에이전트의 작업 |
|---|---|
| Phase 0 (현재) | ✅ 3 implemented (sentiment + keyword + insight) |
| **Phase 2** | POC-01/03/04/06 = 4 Tool 신규 (대시보드 + 비용최적화 + 소재 영역) |
| **Phase 3** | POC-02/05/07/08/09 = 5 Tool 신규 + sentiment 고도화 (KoBERT?) |

## ⚠️ 수정 시 함께 변경 영역

| 영역 | 파일 | 변경 시 |
|---|---|---|
| Tool 코드 | `tools/analysis/ml/` + `tools/analysis/llm/` | 분석 로직 |
| Tool YAML | `tools/catalog/analysis/` | params/produces |
| **team_catalog.yaml** | `analysis_agent` 블록 | Tool 추가 (9 모듈) |
| **LLM Prompts stage3** | `planning_stage3_todo.yaml` | 분석 Tool 이름 + 예시 todo (분석 모듈 chain) |
| **task_agent_hints** | `team_catalog.yaml` (sentiment/keyword/trend/competitor/causal → analysis_agent) | 새 task type 추가 시 |
| **implicit_prerequisites** | `team_catalog.yaml` L256-260 (분석 → data_collection + data_preprocessing 선행) | task 추가 시 |
| **Spec 32 §7.1** | analysis ml/llm 카테고리 행 | |
| **TOBE_MVP/01** | 매트릭스 analysis 행 (POC-01~09) | |
| **데이터 source** | `daily_performance` + `creatives` + `keyword_performance` + `ab_tests` + `review_trends` + `external_variables` (D3) + `naver_datalab` (D3) | |
| **POC-07 sentiment 고도화** | KoBERT 모델 인프라 / 의존성 | Phase 3 |
| **POC-03 RAG** (간접) | external_variables 데이터 | D3 |
| **ADR** | POC-01~09 분석 모듈 결정 / KoBERT 도입 | |
| Tests | `backend/tests/sprint*/test_*analysis*/sentiment*/keyword*.py` | |

## 참조 코드

- Tool 코드 폴더: [`tools/analysis/ml/`](../../../backend/app/dream_agent/tools/analysis/ml/) + [`tools/analysis/llm/`](../../../backend/app/dream_agent/tools/analysis/llm/)
- Tool 메타: [`tools/catalog/analysis/`](../../../backend/app/dream_agent/tools/catalog/analysis/)
- team_catalog: `analysis_agent` 블록

## 참조 spec

- [17 §2.2 9~10 에이전트 + §3.2 8 implemented 체인](../../agent_specs/17_functions_to_io_v1.0.md)
- [32 §7.1 analysis ml + llm](../../agent_specs/32_execution_agent_tools_v1.0.md)
- [31 v0.6 §POC-01~09](../../agent_specs/31_execution_agent_function_list_v0.6.md)
- [TOBE_MVP/02 analysis 카드](../../_claude/tool/TOBE_MVP/02_agent_cards.md)

## 참조 비전 (한국어 narrative)

- [agent_design/04_분석_에이전트.md](../../_claude/referrence/agent_design/04_분석_에이전트.md) — 9 분석 모듈 + LLM 활용 원칙

## 📍 Mock vs 실API 분기

- POC: mock CSV (12개) 직독
- MVP+: KoBERT 모델 (POC-07), Vision LLM (POC-05 5축 채점 — image_agent), DataLab API (POC-08)

비용 예상 (MVP 진입 시):
- GPT-4o LLM (POC-09 리포트 스토리): $5/M tokens
- KoBERT (POC-07): $0 (사전학습 모델, 자체 호스팅)
- Vision (POC-05): $10/M tokens

## Drift / 결정

- **D6** 🟢 Acknowledged — sentiment_analyzer 방법론 (POC: 규칙 → MVP: ML/KoBERT 결정 미정)
- **D7** 🟢 Acknowledged — A/B 테스트 표본 8건 (POC demo only, MVP 실데이터)
- **D3** 🟢 Decided — external_variables 데이터 (POC-03 의존, 사용자 작업 중)
- **D9** 🟡 AI 5축 정의 (image_agent 영역, Phase 4A 진입 전 결정)
- ADR: POC-01~09 모듈 신규 결정 / KoBERT 도입 / RAG (image 의존)

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-19 | 카드 초안. POC-01~09 9 모듈 매핑. |
