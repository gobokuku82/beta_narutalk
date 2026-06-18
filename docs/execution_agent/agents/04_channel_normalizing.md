# 04. channel_normalizing_agent — 4 채널 광고성과 통합 정규화

## 메타

| 항목 | 값 |
|---|---|
| 소속 팀 | analysis_team |
| handles_tasks | `data_preprocessing` |
| Tool 수 | 1 implemented + 4 stub (총 5) |
| 현재 구현률 | 20% |
| team_catalog 위치 | `channel_normalizing_agent` 블록 |
| 분리 이유 | **D9 결정** — 마케팅 도메인 (4 채널 API 스키마 + KPI 공식) |

## 입출력

- **입력**: 매체별 raw 데이터 (collection_agent 출력 — Phase 1B 진입 시) 또는 `mock_data_daily_performance.csv` (현재)
- **출력**: `normalized_data` (현 단순 통합) → MVP 시 `daily_performance` 통합 스키마 (16 컬럼)
- **다음 에이전트**: analysis (모든 분석 모듈)

## Tool 목록

| Tool | Status | 카드 | 역할 |
|---|---|---|---|
| format_normalizer | ✅ implemented | [→](../tools/implemented/format_normalizer.md) | 채널별 컬럼 → 통일 스키마 매핑 |
| kpi_calculator | 🟡 stub (Phase 1B) | (예정) | CTR/CVR/CPC/CPA/ROAS 자동 계산 |
| anomaly_flagger | 🟡 stub (Phase 1B) | (예정) | `pixel_error_flag` / `data_missing_flag` |
| creative_history_updater | 🟡 stub (Phase 1B) | (예정) | 소재 집행일수 + Frequency 주간 이동평균 |
| external_variables_joiner | 🟡 stub (Phase 1B) | (예정) | 외부변수 JOIN (올영세일/황사/공휴일/날씨) |

## 통합 스키마 — `daily_performance` (16 컬럼, MVP 목표)

```
date            YYYY-MM-DD
channel         naver / meta / kakao / google
campaign_id, campaign_name, adgroup_id, ad_id
impressions, clicks, conversions
spend, revenue
roas, ctr, cvr, cpa
frequency       (메타만, 나머지 NULL)
+ pixel_error_flag, data_missing_flag, is_holiday, is_oliveyoung_sale, ...
```

## 데이터 흐름

```
[매체별 raw 4 + datalab + external_variables]  (Phase 1B+)
       │
       ▼
format_normalizer (4 채널 컬럼 매핑)
       │ 메타: inline_link_clicks → clicks
       │ 네이버: clkCnt → clicks
       │ 구글: cost_micros/1e6 → spend
       │ 카카오: metricsGroup.click → clicks
       ▼
kpi_calculator (CTR/CVR/CPC/CPA/ROAS)
       │
       ▼
anomaly_flagger (pixel_error, data_missing)
       │
       ▼
creative_history_updater (Frequency 이동평균)
       │
       ▼
external_variables_joiner (날짜 JOIN)
       │
       ▼
[daily_performance 통합 16 컬럼]
       │
       ▼
   분석 모듈 (POC-01~09)
```

## HITL 카테고리 (D12)

| 카테고리 | 본 에이전트 해당 | 비고 |
|---|---|---|
| 조회·자동 | ✅ (자동 실행) | 일 1회 (수집 후) |

## Phase 진입

| Phase | 본 에이전트의 작업 |
|---|---|
| Phase 0 (현재) | ✅ format_normalizer 단순 통합만 |
| **Phase 1B** | 4 Tool 신규 (kpi_calculator + anomaly_flagger + creative_history_updater + external_variables_joiner) + format_normalizer 확장 (4 채널 매핑 룰 흡수) |
| **Phase 6+** | mock → 실API (네이버광고 / 메타광고 등) — API 스키마 변경 시 매핑 룰 갱신 |

## ⚠️ 수정 시 함께 변경 영역

| 영역 | 파일 | 변경 시 |
|---|---|---|
| Tool 코드 | `tools/preprocessing/data_normalization/format_normalizer.py` | 매핑 룰 / KPI 공식 |
| Tool YAML | `tools/catalog/preprocessing/data_normalization/format_normalizer.yaml` | params/produces |
| **team_catalog.yaml** | `channel_normalizing_agent` 블록 | Tool 추가 |
| **LLM Prompts stage3** | `planning_stage3_todo.yaml` | Tool 이름 + 예시 |
| **task_agent_hints** | `team_catalog.yaml` L234 두 갈래 매핑 | 변경 없음 |
| **Spec 32 §7.1** | preprocessing 카테고리 행 | Tool 추가 시 |
| **TOBE_MVP/01** | 매트릭스 channel_normalizing 행 | |
| **데이터 source** | `mock_data_daily_performance.csv` (현재) → 매체별 raw 4 (Phase 1B) → 실 API (Phase 6+) | |
| **외부변수 데이터** (D3) | `mock_data_external_variables.csv` (사용자 작업 중) | 데이터 도착 시 |
| **ADR** | 매핑 룰 확정 / 실API 전환 결정 | |
| Tests | `backend/tests/sprint*/test_*format_normalize*.py` | |

## 참조 코드

- Tool: [`tools/preprocessing/data_normalization/format_normalizer.py`](../../../backend/app/dream_agent/tools/preprocessing/data_normalization/format_normalizer.py)
- Tool YAML: [`tools/catalog/preprocessing/data_normalization/`](../../../backend/app/dream_agent/tools/catalog/preprocessing/data_normalization/)
- team_catalog: `channel_normalizing_agent` 블록

## 참조 spec

- [17 §2.2 9~10 에이전트](../../agent_specs/17_functions_to_io_v1.0.md)
- [32 §7.1 preprocessing](../../agent_specs/32_execution_agent_tools_v1.0.md)
- [TOBE_MVP/02 channel_normalizing 카드](../../_claude/tool/TOBE_MVP/02_agent_cards.md)
- [TOBE_MVP/03 D9](../../_claude/tool/TOBE_MVP/03_drift_report.md)

## 참조 비전 (한국어 narrative)

- [agent_design/03_전처리_에이전트.md](../../_claude/referrence/agent_design/03_전처리_에이전트.md) §2-1 데이터 전처리 + §2 매체별 변환 규칙

## 📍 Mock vs 실API 분기 (Phase 6+ 마크) ⚠️

- POC: `mock_data_daily_performance.csv` (이미 정규화된 형태, 5328 행)
- MVP+ (Phase 6+): 매체별 raw → 매체별 API client → 본 에이전트가 통합

매체별 변환 규칙 (참조 — [agent_design §03](../../_claude/referrence/agent_design/03_전처리_에이전트.md)):
- 메타: `inline_link_clicks → clicks`, `actions[purchase] → conversions`, `purchase_roas → roas`
- 네이버 SA: `impCnt → impressions`, `clkCnt → clicks`, `ccnt → conversions`, `salesAmt → spend`
- 카카오: `metricsGroup.imp → impressions`, `metricsGroup.click → clicks`
- 구글: `metrics.cost_micros / 1000000 → spend`, `metrics.cost_per_conversion → cpa`

- 데이터 ERD: [RELATIONSHIPS §1](../../../data/description/mock/RELATIONSHIPS.md)
- ROADMAP: [data/description/mock/ROADMAP](../../../data/description/mock/ROADMAP.md)

## Drift / 결정

- **D9** 🟢 Decided — preprocessing 2 분리 (2026-05-18, commit 8ce2f3d)
- **D3** 🟢 Decided — external_variables (사용자 작업 중)
- **D4** 🟡 Open — format_normalizer 4 채널 매핑 룰 미흡 (Phase 1B 진입 시 확장)
- ADR (Phase 1B/Phase 6+): 매핑 룰 / 실API 전환

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-19 | 카드 초안. D9 분리 박제. |
