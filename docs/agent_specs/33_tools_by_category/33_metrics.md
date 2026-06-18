# 33. Metrics tools — 인벤토리

| 항목 | 내용 |
|---|---|
| 카테고리 | **metrics** |
| 의도 (32 §2.5) | 순수 계산 (scalar·list·dict·table 무관 — 계산이면 metrics) |
| 핵심 동사 | sum, count, avg, ratio, distribute |
| 출력 모양 | scalar 또는 구조화 dict |
| 짝 문서 | [32 §2.5](../32_execution_agent_tools_v1.0.md) |
| tool 수 | **35** (2026-05-30 기준) |

## 판정 기준 (vs comparison·visualization)

- 단일 시점·단일 객체 산출 = metrics ✅
- 두 시점·두 객체 *조합*(MoM·delta) = **comparison**
- 차트 spec/그리기 = **frontend** (backend tool 아님, visualization 카테고리 폐기)
- 출력이 list/table 이어도 *계산이면* metrics

## 원칙: 1 tool = 1 지표

"generic 엔진" anti-pattern (op+field 로 N 지표 묶기) **금지**. 의미 단위 분리.

## tool 목록 (35 — 의미 단위 그룹)

> 이름 prefix 가 이미 분류 역할. 평탄 폴더 유지.

### 매출 / 객단가 / 회원 (methodology §S* 11)

| name | input | output | status | 의도 |
|---|---|---|---|---|
| revenue_total | period | scalar | complete | S001 총 매출 |
| promotion_revenue | period | scalar+share | complete | S002 프로모션 매출 |
| roas_overall | period | scalar | complete | S004 전체 ROAS |
| promotion_roas | period | scalar | complete | S005 프로모션 ROAS |
| repurchase_rate_mom | period | scalar+counts | complete | S028 재구매율 |
| cac_overall | period | scalar | complete | S032 전체 CAC |
| age_segment | — | table | complete | S037 연령 5세 bucket |
| grade_revenue | period | dict (5등급) | complete | S046 등급별 매출 |
| aov_monthly | period | scalar+counts | complete | S048 월별 객단가 |
| unknown_revenue_share | period | scalar | complete | S054 알수없음 매출 비중 |
| signup_conversion | period | scalar | complete | S067 가입 전환율 |
| new_members_monthly | period | scalar+channels | complete | S069 신규 회원 |

### 캠페인 KPI (campaign_*, campaigns_*, 5)

| name | input | output | status | 의도 |
|---|---|---|---|---|
| campaign_count | — | scalar | complete | K10 총 캠페인 수 (2026-05-30 분리) |
| campaign_active_count | — | scalar | complete | K11 진행중 캠페인 수 (2026-05-30 분리) |
| campaign_budget_total | — | scalar | complete | K12 총 월예산 (2026-05-30 분리) |
| campaign_target_roas_avg | — | scalar | complete | K13 평균 목표 ROAS (2026-05-30 분리) |
| campaigns_table | period · columns | table rows | complete | T04 캠페인 행 목록 |

### 소재 KPI (creative_*, 4)

| name | input | output | status | 의도 |
|---|---|---|---|---|
| creative_count | — | scalar | complete | K18 총 소재 수 (2026-05-30 분리) |
| creative_ctr_avg | — | scalar | complete | K19 평균 CTR (2026-05-30 분리) |
| creative_roas_avg | — | scalar | complete | K20 평균 ROAS (2026-05-30 분리) |
| creative_cards | — | Top-N list | complete | O04 소재 카드 |

### 예산 (budget_*, 3)

| name | input | output | status | 의도 |
|---|---|---|---|---|
| budget_channel_share | — | dict (채널별) | complete | C09 채널별 예산 비중 |
| budget_stacked | — | dict (구분×채널) | complete | C10 stacked bar 데이터 |
| budget_totals | — | dict | complete | K22·K23 총 예산 + 집행률 |

### 일별 성과 (daily_performance_*, 2)

| name | input | output | status | 의도 |
|---|---|---|---|---|
| daily_performance_aggregate | — | series | complete | C04 일별 성과 라인 |
| daily_performance_totals | period | scalar 묶음 | complete | K14~K17 기간 총계 |

### GA4 / 채널 / 전환 (3)

| name | input | output | status | 의도 |
|---|---|---|---|---|
| ga4_session_aggregator | — | scalar+by_event+by_source | complete | 정제 6 세션 카운트 (S067 분모) |
| channel_aggregate | — | dict (매체별) | complete | C05 매체별 bar |
| conversion_funnel | — | 단계 series | complete | C06 노출→클릭→전환 |

### 키워드 (keyword_*, 2)

| name | input | output | status | 의도 |
|---|---|---|---|---|
| keyword_metrics_avg | — | scalar | complete | K24 키워드 평균 ROAS |
| keyword_top_roas | — | Top-N list | complete | T07 키워드 ROI Top-N |

### 광고비 / 카테고리 / 회원분리 / A/B (4 — 묶음 산출)

| name | input | output | status | 의도 / 비고 |
|---|---|---|---|---|
| ad_cost_total | period | total + by_channel | complete | 5매체 광고비 묶음 (cache 공유, 분리 X — rename 완료 2026-05-30 commit 8e45bcb) |
| category_multi_distributor | period · method | by_category dict | complete | 정제 7 매출 분배 |
| member_guest_stats | period | counts + share_pct | complete | 회원/비회원 통계 묶음 (분리 X — rename 완료 2026-05-30 commit 8e45bcb) |
| ab_test_table | — | table rows | complete | T06 A/B 표 |

## sub-folder 권장 — **현 시점 적용 X** (YAGNI)

- 현 35 tool 평탄 = ls 한 화면 + 이름 prefix 가 이미 분류 역할.
- 도입 시 비용(74 mv + 25 import 갱신) > 가치(시각 분류 약간 개선).
- **tool 50+ 시점에 재검토**. 그 전엔 평탄 유지.

## anti-pattern

- **generic 엔진** — op+field 로 여러 지표 묶기. 의미 단위 분리 (campaigns_aggregate→4·creatives_aggregate→3, 2026-05-30 정리 완료).
- **helper wrapper** — tool 본체 = shared 1줄 호출만. 호출자 있으면 묶음 유지 후 rename 검토. (예: 옛 ad_cost_aggregator → ad_cost_total rename 완료 2026-05-30.)
- **이름과 출력 불일치** — `splitter` 인데 출력 = 카운트. rename 검토. (예: 옛 member_guest_splitter → member_guest_stats rename 완료 2026-05-30.)
- **계산 + 시각화 spec 섞음** — vega-lite 등 spec 만들지 않음. 차트는 frontend.

## 변경 이력

- 2026-05-30 v1.1: campaigns_aggregate 4 분리 · creatives_aggregate 3 분리 (32 §2.6 anti-pattern 정리).
- 2026-05-30 v1.0: preprocessing/marketing 11 tool 이동 (폴더 폐기 — 32 §2.5 정합).
