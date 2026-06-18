# 지표 registry — octorad_metric_registry

> **v0.1 — computed 지표 단일 정의 (contract metrics 확장).** 같은 지표 다른 값 방지(시스템설계지도 §1-B '파편화' 해소).
> 생성: contract.metrics + materialized 실측. 2026-06-14.

---

## 지표 정의 (단일 권위)

| metric | 단위 | formula | grain | 비교성 | 실측(2026-04) |
|---|---|---|---|---|--:|
| `roas_x` | ratio(배수) | conversion_revenue_krw / ad_cost_krw | computed | warn |  |
| `ctr_pct` | percent | clicks / impressions * 100 | computed |  |  |
| `link_ctr_pct` | percent | link_clicks / impressions * 100 | computed |  |  |
| `cpc_krw` | KRW | ad_cost_krw / clicks | computed |  |  |
| `cpm_krw` | KRW | ad_cost_krw / impressions * 1000 | computed |  |  |
| `cvr_pct` | percent | conversion_count / clicks * 100 | computed |  |  |
| `mer` | ratio(배수) | total_revenue / total_marketing_cost | computed | ok | 6.53 |
| `acquisition_mer` | ratio(배수) | new_customer_revenue / total_marketing_cost | computed |  |  |
| `tacos` | percent | total_ad_cost / total_revenue * 100 | computed |  |  |
| `msg_roi_pct` | percent | (msg_conversion_revenue_krw / msg_cost_krw - 1) * 100 | computed |  | {'kakao': 2576.6, 'talktalk': 8731.3} |
| `msg_avg_order_value_krw` | KRW |  | computed |  |  |

## ★ ROAS 일가족 — 단일 권위 (모순 해소)

| 이름 | = | 신뢰 | 비고 |
|---|---|---|---|
| **mer** | total_order_revenue / total_ad_cost | ✅ cross-channel | 전사·의사결정. blended ROAS = 6.53 |
| channel `{ch}_roas_x` | 채널 conversion_revenue / 채널 ad_cost | ⚠ 채널내만 | 광고 매체만(메시징 분리 C6.3). meta 1.91·naver 2.74·advoost 6.5 |
| msg `{ch}_roi_pct` | (매출/비용-1)×100 | ⚠ ROI≠ROAS | kakao 2576%·talktalk 8731% — ad roas와 비교 금지(C6.3) |
| blended_platform_roas | Σ채널매출 / Σ비용 | ⚠ | 채널 보고값 합(과대) — mer와 대비용 |

> 분모=total_ad_cost. ROAS '3값 모순'은 = mer vs 채널 vs 플랫폼블렌디드 grain 차이였음. registry가 grain별 이름·신뢰 단일화.

## 변경 이력
| 날짜 | 내용 |
|---|---|
| 2026-06-14 | v0.1 — contract.metrics → registry. mer 등 실측 동반. ROAS 일가족 단일권위. |