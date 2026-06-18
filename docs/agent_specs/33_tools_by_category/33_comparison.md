# 33. Comparison tools — 인벤토리

| 항목 | 내용 |
|---|---|
| 카테고리 | **comparison** |
| 의도 (32 §2.5) | 두 metrics 를 조합·비교 (MoM·delta·A/B·growth) |
| 핵심 동사 | compare, delta, mom |
| 출력 모양 | 조합 결과 dict |
| 짝 문서 | [32 §2.5](../32_execution_agent_tools_v1.0.md) |

## 판정 기준 (vs metrics)

- 단일 시점/객체 계산 = **metrics**
- 두 시점/객체 *조합* = comparison ✅
- 예: revenue_total(period_a) + revenue_total(period_b) + (b-a)/a*100 = comparison

## 패턴: composer

comparison tool 은 보통 metrics tool 을 두 번 호출 + 차이 계산. **metrics 호출자**.

## tool 목록

| name | input | output | status | 의도 |
|---|---|---|---|---|
| mom_revenue | period_a · period_b | scalar+delta | complete | S001 MoM (+50.5% 등) |
| new_members_mom | period_a · period_b | scalar+delta+channels | complete | S069 MoM |
| repurchase_mom | period_a · period_b | stats+delta | complete | S028 MoM |
| aov_mom | period_a · period_b | stats+delta | complete | S048 MoM |
| grade_timeseries | — | timeline+growth | complete | S045 4시점 시계열 |
| channel_cac_compare | period | by_channel+weighted | complete | S033 채널별 CAC |
| inapp_ad_ab_compare | a_substr · b_substr | a_meta+b_meta | partial | S017~S021 A/B (mock 한계) |

## anti-pattern

- **metrics 안에서 비교** — `revenue_total` 이 두 기간 받으면 안 됨. → comparison tool 별도.
- **delta 산식 중복** — 각 tool 안에 `_pct_change` 함수 중복. → shared/comparison_helper 로 통합 검토.
