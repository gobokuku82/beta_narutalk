# canonical 레이어 ERD/metadata/description — normalized · computed

> **v0.1 — SPEC(contract)에서 *생성*** (손수작성 X, INDEX §2 정정). raw=[erd_octorad_raw](erd_octorad_raw_v1.0.md), 본 문서=normalized+computed.
> 생성일 2026-06-14. 원천: `octorad_canonical_contract_v0.1.yaml` + `data/clumi/_canonical/` (data_pilot materialized, 검증 8/8).

---

## §1 normalized (cleaned) 레이어

> 채널 translator 출력 = canonical measures(원자값) + lineage. grain = 채널 × period(2026-04).

### ERD (DBML)
```dbml
Table normalized_measures {
  channel varchar [note: 'meta/naver_sa/advoost/kakao/talktalk/orders']
  period varchar [note: 'YYYY-MM (KST)']
  ad_cost_krw int [note: '광고 매체 집행비(meta/naver/advoost). ⚠ salesAmt=비용(C6.1). ★C6.3 검증역반영(verify']
  impressions int [note: '노출수 — 광고가 화면에 표출된 횟수 (매체 공통, Naver impCnt 포함). 도달(paid_reach)과 구분 — 1인']
  clicks int [note: '전체 클릭(링크 외 포함). 링크클릭은 link_clicks 별 필드.']
  link_clicks int [note: '링크 클릭 (Meta 전용). CTR canonical 분자.']
  conversion_count int [note: '전환수. Meta는 actions[] 배열에서 action_type=omni_purchase 필터(미필터=silent-0, C']
  vt_conversion_count int [note: '조회연결(view-through) 전환 — CT와 분리(이중계상 방지).']
  conversion_revenue_krw int [note: '전환매출. ⚠ Naver convAmt=매출(salesAmt=비용과 짝, C6.1). Meta action_values omn']
  paid_reach int [note: '유료 도달 (Meta). ⚠ IG organic reach(organic_reach)와 합산 금지(C6.4).']
  impression_frequency float [note: '노출/도달 (Meta 전용). customer_rfm.frequency(구매빈도)와 동음이의 — 무관.']
  msg_cost_krw int [note: '메시징 발송비(★C6.3 ad_cost와 분리, verify A4). MER 분모(총마케팅비)엔 포함']
  msg_target_count int [note: '메시징 발송 대상 수 (수신동의 친구·대상). 광고 impressions와 무관 — 메시징 깔때기 분모']
  msg_open_count int [note: '메시징 오픈(열람) 수. 광고 노출과 다른 행동 — open_rate 분모 미확정(M5 보류)이라 count만 채택']
  msg_click_count int [note: '광고 clicks와 동음이의(분리)']
  msg_conversion_count int [note: '광고 전환과 절대 분리(C6.3)']
  msg_conversion_revenue_krw int [note: '메시징 전환 매출. ★C6.3 광고 conversion_revenue_krw와 절대 분리(별 measure). msg_roi_']
  order_revenue_krw int [note: '자사몰 주문 매출(MER 분자). 활성주문(order_status!=C40)']
  _lineage json [note: 'source_channel·source_column·raw_value·transform (신뢰)']
}
```

### metadata

| 항목 | 값 |
|---|---|
| layer | cleaned (normalized) |
| grain | 채널 × period |
| 생성 | 채널 translator(contract+config) |
| 채널 | advoost, kakao, meta, naver_sa, orders, talktalk |
| 신뢰 | 모든 값 lineage 동반 (정규화값 ← 원본 raw) |

### description (measure 컬럼)

| measure | 단위 | 설명 | 채널 source |
|---|---|---|---|
| `ad_cost_krw` | KRW | 광고 매체 집행비(meta/naver/advoost). ⚠ salesAmt=비용(C6.1). ★C6.3 검증역반영(verify B1/D2/A4) kakao/talktalk 메시징비는 msg_cost_krw 분리. MER 분모=ad+msg. | meta:data[].spend · naver_sa:data[].salesAmt · advoost:cost · google:cost |
| `impressions` | count | 노출수 — 광고가 화면에 표출된 횟수 (매체 공통, Naver impCnt 포함). 도달(paid_reach)과 구분 — 1인 다중노출 가능. | meta:data[].impressions · naver_sa:data[].impCnt · advoost:impressions · google: |
| `clicks` | count | 전체 클릭(링크 외 포함). 링크클릭은 link_clicks 별 필드. | meta:data[].clicks · naver_sa:data[].clkCnt · advoost:clicks · google:clicks |
| `link_clicks` | count | 링크 클릭 (Meta 전용). CTR canonical 분자. | meta:data[].inline_link_clicks |
| `conversion_count` | count | 전환수. Meta는 actions[] 배열에서 action_type=omni_purchase 필터(미필터=silent-0, C6.2). advoost는 CT(클릭연결). | meta:data[].actions[] · naver_sa:data[].ccnt · advoost:click_through_conversions |
| `vt_conversion_count` | count | 조회연결(view-through) 전환 — CT와 분리(이중계상 방지). | advoost:view_through_conversions |
| `conversion_revenue_krw` | KRW | 전환매출. ⚠ Naver convAmt=매출(salesAmt=비용과 짝, C6.1). Meta action_values omni_purchase. | meta:data[].action_values[] · naver_sa:data[].convAmt · advoost:conversion_value |
| `paid_reach` | count_unique | 유료 도달 (Meta). ⚠ IG organic reach(organic_reach)와 합산 금지(C6.4). | meta:data[].reach |
| `impression_frequency` | ratio | 노출/도달 (Meta 전용). customer_rfm.frequency(구매빈도)와 동음이의 — 무관. | meta:data[].frequency |
| `msg_cost_krw` | KRW | 메시징 발송비(★C6.3 ad_cost와 분리, verify A4). MER 분모(총마케팅비)엔 포함 | kakao:campaigns[].summary.total_cost_krw · talktalk:campaigns[].summary.total_co |
| `msg_target_count` | count | 메시징 발송 대상 수 (수신동의 친구·대상). 광고 impressions와 무관 — 메시징 깔때기 분모 | kakao:campaigns[].summary.target_recipients · talktalk:campaigns[].summary.targe |
| `msg_open_count` | count | 메시징 오픈(열람) 수. 광고 노출과 다른 행동 — open_rate 분모 미확정(M5 보류)이라 count만 채택 | kakao:summary.open_count · talktalk:summary.open_count · crm:crm_send_logs.open_ |
| `msg_click_count` | count | 광고 clicks와 동음이의(분리) | kakao:summary.click_count · talktalk:summary.click_count · crm:crm_send_logs.cli |
| `msg_conversion_count` | count | 광고 전환과 절대 분리(C6.3) | kakao:summary.conversion_count · talktalk:summary.conversion_count · interest:co |
| `msg_conversion_revenue_krw` | KRW | 메시징 전환 매출. ★C6.3 광고 conversion_revenue_krw와 절대 분리(별 measure). msg_roi_pct 분자 | kakao:summary.conversion_amount_krw · talktalk:summary.conversion_amount_krw · c |
| `order_revenue_krw` | KRW | 자사몰 주문 매출(MER 분자). 활성주문(order_status!=C40) | internal:orders.payment_amount |

### ★ raw→normalized 변환 맵 (칼럼명 변경 + 수치 변경)

> normalized 설계의 두 축: **칼럼명**(어느 raw 컬럼 → canonical 이름) + **값변환**(다 다른 수치를 어떻게 통일). matching(이름)=contract sources / mapping(값)=conversion_config. 코드: pipeline.py(이름)·transforms.py(값).

| canonical | 채널 | raw 컬럼 (이름변경 IN) | 값변환 (수치변경) |
|---|---|---|---|
| `ad_cost_krw` | meta | data[].spend | str→int; account_currency→KRW |
| `ad_cost_krw` | naver_sa | data[].salesAmt | as-is |
| `ad_cost_krw` | advoost | cost | str→int |
| `ad_cost_krw` | google | cost | str→int |
| `impressions` | meta | data[].impressions | str→int |
| `impressions` | naver_sa | data[].impCnt | as-is |
| `impressions` | advoost | impressions | str→int |
| `impressions` | google | impressions | str→int |
| `clicks` | meta | data[].clicks | str→int |
| `clicks` | naver_sa | data[].clkCnt | as-is |
| `clicks` | advoost | clicks | str→int |
| `clicks` | google | clicks | str→int |
| `link_clicks` | meta | data[].inline_link_clicks | str→int |
| `conversion_count` | meta | data[].actions[] | filter action_type='omni_purchase' → value(str→int) |
| `conversion_count` | naver_sa | data[].ccnt | 전환수(int) — convCnt 부재(06 검증) |
| `conversion_count` | advoost | click_through_conversions | str→int |
| `conversion_count` | google | conversions | str→int |
| `vt_conversion_count` | advoost | view_through_conversions | str→int |
| `conversion_revenue_krw` | meta | data[].action_values[] | filter omni_purchase → value(str→int); account_currency |
| `conversion_revenue_krw` | naver_sa | data[].convAmt | convAmt=매출 |
| `conversion_revenue_krw` | advoost | conversion_value | str→int |
| `conversion_revenue_krw` | google | conversion_value | str→int |
| `paid_reach` | meta | data[].reach | str→int |
| `impression_frequency` | meta | data[].frequency | as-is |
| `msg_cost_krw` | kakao | campaigns[].summary.total_cost_krw | as-is |
| `msg_cost_krw` | talktalk | campaigns[].summary.total_cost_krw | as-is |
| `msg_target_count` | kakao | campaigns[].summary.target_recipients | as-is |
| `msg_target_count` | talktalk | campaigns[].summary.target_friends | as-is |
| `msg_target_count` | crm | crm_send_logs.target_count | as-is |
| `msg_open_count` | kakao | summary.open_count | as-is |
| `msg_open_count` | talktalk | summary.open_count | as-is |
| `msg_open_count` | crm | crm_send_logs.open_count | as-is |
| `msg_open_count` | interest | naver_interest_alert.message_open_count | as-is |
| `msg_click_count` | kakao | summary.click_count | as-is |
| `msg_click_count` | talktalk | summary.click_count | as-is |
| `msg_click_count` | crm | crm_send_logs.click_count | as-is |
| `msg_click_count` | interest | message_click_count | as-is |
| `msg_conversion_count` | kakao | summary.conversion_count | as-is |
| `msg_conversion_count` | talktalk | summary.conversion_count | as-is |
| `msg_conversion_count` | interest | conversion_count | as-is |
| `msg_conversion_revenue_krw` | kakao | summary.conversion_amount_krw | as-is |
| `msg_conversion_revenue_krw` | talktalk | summary.conversion_amount_krw | as-is |
| `msg_conversion_revenue_krw` | crm | crm_send_logs.conversion_amount_krw | as-is |
| `msg_conversion_revenue_krw` | interest | conversion_amount(단위확인) | as-is |
| `order_revenue_krw` | internal | orders.payment_amount | as-is |

---

## §2 computed (metrics) 레이어

> 파생 *재계산*(measure에서). 채널 roas(과대) vs blended mer(신뢰).

### ERD (DBML)
```dbml
Table computed_metrics {
  metric varchar [pk]
  value float
  unit varchar
  formula varchar [note: '재계산 — 채널 보고값 아님']
}
```

### 실측 값 (materialized 2026-04, 검증 8/8)

| metric | 값 | 의미 |
|---|--:|---|
| total_ad_cost_krw | 18,235,453 | 광고 매체(meta/naver/advoost) |
| total_msg_cost_krw | 71,470 | 메시징(C6.3 분리) |
| total_marketing_cost_krw | 18,306,923 | ad+msg (MER 분모) |
| total_order_revenue_krw | 119,539,660 | orders 매출 (MER 분자) |
| **mer** | **6.53** | 전사 ROAS = total_rev/total_cost (신뢰) |
| blended_platform_roas_x | 2.94 | 채널 보고매출 합/비용 (과대) |
| channel_roas_x | meta=1.91, naver_sa=2.74, advoost=6.5 | 채널별(제각각·과대) |
| tacos_pct | 15.25 | 총광고비/매출*100 (전사) |
| channel ctr_pct | meta=1.4, naver_sa=2.08, advoost=0.62 | 채널별 클릭률 (clicks/imp) |
| channel cvr_pct | meta=1.78, naver_sa=2.59, advoost=2.22 | 채널별 전환율 (conv/clicks) |
| channel cpc_krw | meta=543, naver_sa=666, advoost=199 | 채널별 클릭당비용 |
| channel cpm_krw | meta=7588, naver_sa=13821, advoost=1240 | 채널별 1000노출당비용 |

### description (metric)

| metric | 단위 | formula | status | 비교성 |
|---|---|---|---|---|
| `roas_x` | ratio(배수) | conversion_revenue_krw / ad_cost_krw | ✓ | warn |
| `ctr_pct` | percent | clicks / impressions * 100 | ✓ |  |
| `link_ctr_pct` | percent | link_clicks / impressions * 100 | blocked |  |
| `cpc_krw` | KRW | ad_cost_krw / clicks | ✓ |  |
| `cpm_krw` | KRW | ad_cost_krw / impressions * 1000 | ✓ |  |
| `cvr_pct` | percent | conversion_count / clicks * 100 | ✓ |  |
| `mer` | ratio(배수) | total_revenue / total_marketing_cost | ✓ | ok |
| `acquisition_mer` | ratio(배수) | new_customer_revenue / total_marketing_cost | blocked |  |
| `tacos` | percent | total_ad_cost / total_revenue * 100 | ✓ |  |
| `msg_roi_pct` | percent | (msg_conversion_revenue_krw / msg_cost_krw - 1) * 100 | ✓ |  |
| `msg_avg_order_value_krw` | KRW | promo_/rfm_/cat_ 와 prefix 분리 | sourced(채널보고값) |  |

---

## §3 lineage (신뢰)

> 모든 normalized 값이 원본 동반 → computed가 그 위에 재계산 → 에이전트가 raw까지 추적 표시.
예: `mer 6.53 ← total_order_revenue 119,539,660(orders.payment_amount) / total_ad_cost 18,306,923(meta.spend+naver.salesAmt+...)`.

## 변경 이력
| 날짜 | 내용 |
|---|---|
| 2026-06-14 | v0.1 — contract+materialized에서 생성. normalized 16 measures·computed 11 metrics ERD/meta/desc. |