# raw ERD — clumi (정식)

> **clumi raw 30 파일 / 34 테이블의 ERD (테이블·컬럼·관계).** 데이터 구조 재설계의 L2 인스턴스 기준점.

| 항목 | 내용 |
|---|---|
| 생성일 | 2026-06-13 |
| 원천(ground truth) | **`data/clumi/raw/` 실제 파일** (옛 ERD = 데이터사전 CSV에서 생성 → stale. 본판은 실파일 직독) |
| 생성 파이프라인 | `extract_raw_schema.py`(스키마 추출·GA4 전수 스트리밍) → `gen_dbml_draft.py`(결정론 DBML) → 워크플로 4분석(Ref·그룹·drift·정합) → `assemble_erd.py`(조립) |
| 도구 위치 | `docs/_claude/data/erd/` (재생성 스크립트·중간산출) |
| 규모 | 30 파일 → 34 테이블(SQL 2개가 6 테이블), 11 도메인, 확정 Ref 17 + 추정 7 |
| 렌더 | 아래 §3 DBML 블록 또는 `erd_octorad_raw_v1.0.dbml` 을 https://dbdiagram.io 에 붙여넣기 |
| 메타데이터·설명 | **[octorad_raw_metadata_v0.1.md](octorad_raw_metadata_v0.1.md)** — 테이블 메타(벤더·API·grain·PII) + 컬럼 description 712개(source/confidence). 짝 머신: `octorad_raw_metadata_v0.1.yaml`(canonical contract 씨앗) |

---

## §0 개요

- **이 문서가 답하는 것**: clumi 가 분석에 쓰는 raw 데이터가 *어떤 테이블·컬럼·관계로 이루어졌나*. 지표·계산은 다루지 않음(그건 지표 registry 소관).
- **데이터 구조 재설계 맥락**: 이 ERD = **clumi 인스턴스(L2)**. 계약 *스키마(L1, client-generic)* 와 구별. 새 client 는 같은 L1 스키마에 자기 ERD(인스턴스)를 채운다.
- **두 데이터 family 가 raw 에 공존** (§5 정합 참조): ① 분석 21 파일(데이터사전 등재) + ② demo placeholder 9 파일(사전 미등재, blooming 계열 추정).

## §1 도메인별 테이블 카탈로그

### 광고 캠페인 (자체 정의)

| 테이블 | 행수 | 사전 | 목적 | 핵심 컬럼 |
|---|--:|:--:|---|---|
| `campaigns` | 12 | — | 캠페인 마스터 — 캠페인별 목표·기간·예산·타깃 지표(CPA/ROAS/전환) 정의 (사전 미등재, 컬럼 기반 추정) | campaign_id, name, campaign_type, monthly_budget |
| `creatives` | 12 | — | 광고 소재 마스터 — 캠페인별 크리에이티브(헤드라인/본문/이미지)와 성과 지표(CTR/CVR/ROAS) (사전 미등재, 컬럼 기반 추정) | creative_id, campaign_id, channel, format |
| `daily_performance` | 32 | — | 일별 광고 성과 — 캠페인/소재/채널별 일자 단위 노출·클릭·전환·CPA/ROAS 집계 (사전 미등재, 컬럼 기반 추정) | date, campaign_id, creative_id, channel |
| `budget_allocation` | 5 | — | 예산 배분 계획 — 세그먼트·캠페인유형별 채널(meta/naver/kakao/google) 예산 및 집행률 (사전 미등재, 컬럼 기반 추정) | segment, campaign_type, total_budget, exec_rate |
| `ab_tests` | 5 | — | A/B 테스트 정의 — 지표(metric)별 변형 A/B 값을 비교하는 실험 설정 (사전 미등재, 컬럼 기반 추정) | test_id, metric, variant_a, variant_b |

### 광고 매체 성과 — Meta

| 테이블 | 행수 | 사전 | 목적 | 핵심 컬럼 |
|---|--:|:--:|---|---|
| `meta_ads_performance` | 90 | mock #1 | Meta 광고 캠페인 성과 — 캠페인별 일자 단위 광고비·노출·클릭·도달·구매 액션·ROAS (광고 성과의 기준 테이블) | data[].campaign_id, data[].date_start, data[].spend, data[].account_id |
| `meta_ads_by_age` | 540 | mock #2 | Meta 광고 연령대별 성과 — 캠페인×연령대(breakdown)별 광고비·노출·클릭·구매·매출 | data[].campaign_id, data[].age, data[].date_start, data[].spend |
| `meta_instagram_inapp` | 150 | mock #3 | Meta 인스타/플랫폼 위치별 성과 — 캠페인×노출플랫폼(instagram/facebook)×위치(feed/story/reels)별 성과 | data[].campaign_id, data[].publisher_platform, data[].platform_position, data[].date_start |

### 광고 매체 성과 — Naver

| 테이블 | 행수 | 사전 | 목적 | 핵심 컬럼 |
|---|--:|:--:|---|---|
| `naver_advoost` | 90 | mock #15 | 네이버 ADVoost 성과 — 쇼핑/카탈로그/디스플레이 캠페인별 노출·클릭·비용·VT/CT 전환·ROAS·비디오 시청 | campaign_id, report_date, campaign_type, cost |
| `naver_searchad` | 1,680 | mock #4 | 네이버 검색광고 성과 — 키워드별 일자/디바이스 노출·클릭·비용(salesAmt)·전환매출(convAmt)·ROAS(ror) | data[].nccCampaignId, data[].nccKeywordId, data[].statDt, data[].device |
| `keyword_performance` | 18 | — | 키워드별 검색광고 성과 — 채널/키워드그룹별 키워드 노출·클릭·전환·ROAS·품질점수·경쟁도 (사전 미등재, 컬럼 기반 추정) | keyword, keyword_group, channel, quality_score |

### 광고 목표/예산 설정

| 테이블 | 행수 | 사전 | 목적 | 핵심 컬럼 |
|---|--:|:--:|---|---|
| `channel_targets` | 4 | — | 채널별 목표 지표 — 기간·채널별 목표 CPA/ROAS 설정 (사전 미등재, 컬럼 기반 추정) | period, channel, target_cpa, target_roas |
| `marketing_monthly_targets` | 1 | — | 월간 마케팅 목표 — 기간별 목표 노출/클릭/전환/CTR/CVR/ROAS 및 손익분기 ROAS (사전 미등재, 컬럼 기반 추정) | period, target_roas, breakeven_roas, target_conversions |

### 거래 (Cafe24 주문)

| 테이블 | 행수 | 사전 | 목적 | 핵심 컬럼 |
|---|--:|:--:|---|---|
| `orders` | 3,420 | mock #5 | 주문 트랜잭션 — Cafe24 자사몰 주문별 결제금액·할인·상품·채널귀속(UTM)·프로모션·디바이스 (전환/매출의 중심 테이블) | order_id, member_id, payment_amount, channel_attribution |
| `category_sales` | 155 | mock #12 | 카테고리별 매출 집계 — 일/월별 1단계 카테고리 매출·주문·신규/재구매 구매자 분포 (다중 카테고리 분배) | stat_date, category_lv1, category_code, order_amount |
| `reviews` | 24 | — | 상품 리뷰 — 상품별 리뷰 텍스트·평점·작성일 (사전 미등재, 컬럼 기반 추정) | review_id, product, rating, date |

### 회원 (Cafe24 고객)

| 테이블 | 행수 | 사전 | 목적 | 핵심 컬럼 |
|---|--:|:--:|---|---|
| `customers` | 8,500 | mock #6 | 회원 마스터 — 회원 인구통계·가입정보·마케팅 동의·누적 주문/구매액·등급 (Cafe24 자사몰 회원) | member_id, membership_grade, signup_channel, total_purchase_amount |
| `customer_rfm` | 8,500 | mock #10 | 고객 RFM 분석 — 전 회원(8500)의 R/F/M 점수·세그먼트·CLV·이탈위험·구매성향 스냅샷 | member_id, snapshot_date, rfm_segment, customer_tier |
| `customer_grade_history` | 30,379 | mock #21 | 회원 등급 이력 — 월말 스냅샷별 회원 등급 변화와 누적 주문/매출 추적 | member_id, snapshot_date, grade, is_grade_change |
| `household_structure` | 12 | mock #19 | 가구 구조 분석 — 가구 유형(HT01~HT10)별 회원 분포·매출·재구매율·페르소나·마케팅 시사점 | household_type_code, household_type, member_count, total_revenue_krw |
| `signup_events` | 600 | mock #9 | 회원 가입 이벤트 — 가입 건별 채널·디바이스·UTM·GA세션·가입방식·프로모션코드·첫방문 경과일 추적 | signup_event_id, member_id, signup_channel, ga_session_id |

### 행동 이벤트 (GA4)

| 테이블 | 행수 | 사전 | 목적 | 핵심 컬럼 |
|---|--:|:--:|---|---|
| `ga4_page_events` | 84,143 | mock #8 | GA4 페이지/행동 이벤트 — 9종 이벤트(page_view/scroll/view_item/add_to_cart/checkout 등) 행동 로그 | user_pseudo_id, user_id, event_name, event_timestamp |
| `ga4_traffic_source` | 38,319 | mock #7 | GA4 트래픽 소스/구매 이벤트 — 3종 이벤트(session_start/first_visit/purchase) 및 유입경로·구매 매출 | user_pseudo_id, user_id, event_name, ecommerce.transaction_id |

### CRM 메시징 (자체)

| 테이블 | 행수 | 사전 | 목적 | 핵심 컬럼 |
|---|--:|:--:|---|---|
| `crm_campaigns` | —(SQL) | mock #18 | CRM 캠페인 마스터 — 멀티채널(카카오/톡톡/이메일) 메시지 캠페인 정의 및 A/B 테스트 여부 | campaign_id, campaign_name, campaign_type, channels |
| `crm_message_variants` | —(SQL) | mock #18 | CRM 메시지 변형 — 캠페인 내 A/B 변형별 메시지 전략·제목·본문·CTA·발송 비율 | variant_id, campaign_id, variant_label, message_strategy |
| `crm_send_logs` | —(SQL) | mock #18 | CRM 발송 결과 로그 — 변형별 송달/오픈/클릭/전환/ROI 등 발송 성과 집계 | send_id, variant_id, campaign_id, conversion_amount_krw |

### 메시징 매체 (Kakao/Naver)

| 테이블 | 행수 | 사전 | 목적 | 핵심 컬럼 |
|---|--:|:--:|---|---|
| `kakao_bizmessage` | 2 | mock #16 | 카카오 비즈메시지 캠페인 — 친구톡/알림톡 발송 캠페인의 대상·성공·오픈·클릭·전환 성과 | campaigns[].campaign_id, campaigns[].template_code, campaigns[].message_type, campaigns[].summary.conversion_amount_krw |
| `naver_talktalk` | 2 | mock #17 | 네이버 톡톡 캠페인 — 친구 대상 메시지 발송 캠페인의 송달·오픈·클릭·전환·친구해제 성과 | campaigns[].campaign_id, channel_id, campaigns[].summary.conversion_amount_krw, friend_summary.marketing_opt_in_count |
| `naver_interest_alert` | 4 | mock #13 | 네이버 스마트스토어 관심고객/알림 — 월별 관심고객·알림수신 옵트인·메시지 발송/오픈/클릭/전환 집계 | channel, collect_date, interest_customer_total, notification_customer_total |

### 프로모션/쿠폰

| 테이블 | 행수 | 사전 | 목적 | 핵심 컬럼 |
|---|--:|:--:|---|---|
| `promotions` | —(SQL) | mock #11 | 프로모션 마스터 — 프로모션 코드별 유형·할인·기간·대상 세그먼트·적용상품·사용한도 정의 | promotion_id, promotion_code, promotion_type, target_segment |
| `promotion_performance` | —(SQL) | mock #11 | 프로모션 성과 집계 — 프로모션별 사용건수·매출·할인액·신규/기존 고객·전환율·ROI 스냅샷 | performance_id, promotion_id, promotion_code, roi_percent |
| `promotion_usage_history` | —(SQL) | mock #11 | 프로모션 사용 이력 — 회원·주문별 프로모션 코드 사용 건별 할인액·주문금액 기록 | usage_id, promotion_code, member_id, order_id |

### 소셜 인게이지먼트 / 광고운영 로그

| 테이블 | 행수 | 사전 | 목적 | 핵심 컬럼 |
|---|--:|:--:|---|---|
| `instagram_engagement` | 40 | mock #14 | Instagram 게시물 인게이지먼트 — 미디어별 좋아요/댓글/도달/저장/인터랙션 및 인사이트 지표 | data[].id, data[].media_type, data[]._meta.category, data[]._meta.related_campaign |
| `ad_change_history` | 50 | mock #20 | Meta 광고 변경 이력 — 캠페인/예산/상태 변경 이벤트 감사 로그 (Meta 표준 + 자사 internal_audit_log) | data[].object_id, data[].event_type, data[].event_time, data[].actor_id |

## §2 관계 (Ref)

**확정 17건** (draft 컬럼 검증 통과 → DBML 활성):

| FK (참조하는 쪽) | → PK (정의처) | 의미 |
|---|---|---|
| `creatives.campaign_id` | `campaigns.campaign_id` | 광고소재→캠페인. campaigns.campaign_id=PK(캠페인 정의처), creatives가 참조. |
| `daily_performance.campaign_id` | `campaigns.campaign_id` | 일별성과→캠페인. campaigns.campaign_id=PK, daily_performance가 참조. |
| `daily_performance.creative_id` | `creatives.creative_id` | 일별성과→소재. creatives.creative_id=PK, daily_performance가 참조. |
| `crm_message_variants.campaign_id` | `crm_campaigns.campaign_id` | 메시지 변형→CRM 캠페인. crm_campaigns.campaign_id=PK, variants가 참조. |
| `crm_send_logs.campaign_id` | `crm_campaigns.campaign_id` | 발송로그→CRM 캠페인. crm_campaigns.campaign_id=PK, send_logs가 참조. |
| `crm_send_logs.variant_id` | `crm_message_variants.variant_id` | 발송로그→메시지 변형. crm_message_variants.variant_id=PK, send_logs가 참조. |
| `customer_rfm.member_id` | `customers.member_id` | RFM 스냅샷→회원. customers.member_id=PK(회원 정의처), customer_rfm가 참조. |
| `customer_grade_history.member_id` | `customers.member_id` | 등급변동이력→회원. customers.member_id=PK, grade_history가 참조. |
| `orders.member_id` | `customers.member_id` | 주문→회원. customers.member_id=PK, orders가 참조(nullable=비회원 주문 허용). |
| `signup_events.member_id` | `customers.member_id` | 가입이벤트→회원. customers.member_id=PK, signup_events가 참조. |
| `promotion_usage_history.member_id` | `customers.member_id` | 프로모션사용이력→회원. customers.member_id=PK, usage_history가 참조. |
| `promotion_usage_history.order_id` | `orders.order_id` | 프로모션사용이력→주문. orders.order_id=PK(주문 정의처), usage_history가 참조. |
| `orders.promotion_code` | `promotions.promotion_code` | 주문→프로모션. promotions.promotion_code=프로모션 정의처(UNIQUE), orders가 참조(nullable). |
| `promotion_performance.promotion_id` | `promotions.promotion_id` | 프로모션성과→프로모션. promotions.promotion_id=PK, performance가 참조. |
| `promotion_usage_history.promotion_id` | `promotions.promotion_id` | 프로모션사용이력→프로모션. promotions.promotion_id=PK, usage_history가 참조. |
| `promotion_performance.promotion_code` | `promotions.promotion_code` | 프로모션성과→프로모션(code). promotions.promotion_code=UNIQUE, performance가 중복참조(promotion_id와 병행 비정규화). |
| `promotion_usage_history.promotion_code` | `promotions.promotion_code` | 프로모션사용이력→프로모션(code). promotions.promotion_code=UNIQUE, usage_history가 중복참조. |

**추정 7건** (검증 필요 — DBML 비활성 주석):

| 추정 관계 | 비고 |
|---|---|
| `crm_campaigns.campaign_id` → `campaigns.campaign_id` | 추정. CRM 캠페인 id 가 광고 campaigns 와 동일 키 공간인지는 불확실(crm_campaigns.campaign_id=int vs campaigns.campaign_id=string). 별 도메인일 가능성 높아 약한 연결. |
| `ga4_traffic_source.user_pseudo_id` → `ga4_page_events.user_pseudo_id` | 추정. 두 GA4 이벤트 스트림은 동일 user_pseudo_id 공간을 공유(같은 GA4 export). FK라기보다 동일 식별자 join 키. |
| `ga4_page_events.user_id` → `customers.member_id` | 추정. GA4 user_id(로그인 사용자)가 customers.member_id 와 매핑될 가능성. 대부분 null, 검증 필요. |
| `ga4_traffic_source.user_id` → `customers.member_id` | 추정. GA4 user_id→회원 매핑 가능성. 대부분 null, 검증 필요. |
| `meta_ads_by_age.account_id` → `meta_ads_performance.account_id` | 추정. Meta 광고 3소스가 동일 account_id(광고계정) 공유. 별 엔티티(ad_account) 테이블 부재로 명시 PK측 없음 — 공유 차원키. |
| `meta_instagram_inapp.account_id` → `meta_ads_performance.account_id` | 추정. Meta Instagram 인앱이 동일 account_id 공유. 공유 차원키(ad_account). |
| `kakao_bizmessage.template_code` → `naver_talktalk.code` | 추정·약함. fk_hints 의 'code' 공유는 응답 status code 와 template_code 혼동 가능성. 실제 FK 아닐 확률 높음 — 도메인상 무관. |

## §3 ERD (DBML)

> dbdiagram.io 에 붙여넣어 렌더. 컬럼명에 `.`/`[]` 있는 것 = JSON/JSONL 중첩 경로(평탄화 표기).

```dbml
// raw_clumi ERD v2 draft — extract_raw_schema.py 산출(실제 raw 파일 ground truth)
// Ref/TableGroup 은 합성 단계가 추가. 본 초안 = 컬럼 정확성 보장.

Table ab_tests {
  name varchar
  metric varchar
  a_value varchar
  b_value varchar
  test_id varchar
  variant_a varchar
  variant_b varchar
  Note: 'ab_tests | rows=5 | '
}

Table ad_change_history {
  "_meta.ad_account_id" varchar
  "_meta.query_date_range.since" datetime [note: 'date/datetime']
  "_meta.query_date_range.until" datetime [note: 'date/datetime']
  "_meta.source" varchar
  "_meta.total_events" int
  "data[].actor_id" varchar
  "data[].actor_name" varchar
  "data[].application_id" varchar [note: 'null']
  "data[].application_name" varchar [note: 'null']
  "data[].date_time_in_timezone" varchar
  "data[].event_time" datetime [note: 'date/datetime']
  "data[].event_time_unix" int
  "data[].event_type" varchar
  "data[].extra_data" varchar
  "data[].object_id" varchar
  "data[].object_name" varchar
  "data[].object_type" varchar
  "data[].translated_event_type" varchar
  "paging.cursors.after" varchar
  "paging.cursors.before" varchar
  Note: 'ad_change_history | rows=50 | '
}

Table budget_allocation {
  segment varchar
  exec_rate varchar
  meta_budget varchar
  kakao_budget varchar
  naver_budget varchar
  total_budget varchar
  campaign_type varchar
  google_budget varchar
  Note: 'budget_allocation | rows=5 | '
}

Table campaigns {
  goal varchar
  name varchar
  owner varchar
  status varchar
  product varchar
  end_date datetime [note: 'date/datetime']
  start_date datetime [note: 'date/datetime']
  target_cpa varchar
  campaign_id varchar
  target_roas varchar
  campaign_type varchar
  monthly_budget varchar
  target_conversions varchar
  Note: 'campaigns | rows=12 | '
}

Table category_sales {
  share_pct varchar
  stat_date datetime [note: 'date/datetime']
  order_count varchar
  category_lv1 varchar
  category_lv2 varchar
  order_amount varchar
  refund_count varchar
  category_code varchar
  category_name varchar
  refund_amount varchar
  unique_buyers varchar
  avg_order_value varchar
  new_buyer_count varchar
  new_buyer_amount varchar
  product_quantity varchar
  top_product_name varchar
  repeat_buyer_count varchar
  repeat_buyer_amount varchar
  Note: 'category_sales | rows=155 | '
}

Table channel_targets {
  period varchar
  channel varchar
  target_cpa varchar
  target_roas varchar
  Note: 'channel_targets | rows=4 | '
}

Table creatives {
  cpa varchar
  cpc varchar
  ctr varchar
  cvr varchar
  body varchar
  name varchar
  roas varchar
  format varchar
  status varchar
  channel varchar
  headline varchar
  run_days varchar
  frequency varchar
  image_url varchar
  start_date datetime [note: 'date/datetime']
  campaign_id varchar
  creative_id varchar
  landing_url varchar
  Note: 'creatives | rows=12 | '
}

Table crm_campaigns {
  campaign_id int
  campaign_name varchar(200)
  campaign_type varchar(30)
  trigger_type varchar(30)
  target_segment varchar(100)
  channels varchar(200)
  scheduled_at datetime
  sent_at datetime
  status varchar(20)
  ab_test tinyint(1)
  variant_count int
  created_by varchar(50)
  created_at datetime
  updated_at datetime
  INSERT into
  Note: 'crm_campaigns |  | from crm_messages.sql'
}

Table crm_message_variants {
  variant_id varchar(20)
  campaign_id int
  variant_label varchar(10)
  message_strategy varchar(30)
  subject_line varchar(200)
  body_text text
  cta_text varchar(100)
  cta_url varchar(500)
  image_url varchar(500)
  preview_text varchar(200)
  personalization_tags varchar(200)
  send_ratio decimal(4,3)
  created_at datetime
  INSERT into
  Note: 'crm_message_variants |  | from crm_messages.sql'
}

Table crm_send_logs {
  send_id int
  variant_id varchar(20)
  campaign_id int
  sent_at datetime
  target_count int
  delivered_count int
  delivered_rate decimal(5,2)
  open_count int
  open_rate decimal(5,2)
  click_count int
  click_rate decimal(5,2)
  click_through_rate_open decimal(5,2)
  conversion_count int
  conversion_amount_krw bigint
  conversion_rate_click decimal(5,2)
  avg_order_value int
  roi_percent decimal(10,2)
  unsubscribe_count int
  complaint_count int
  created_at datetime
  INSERT into
  Note: 'crm_send_logs |  | from crm_messages.sql'
}

Table customer_grade_history {
  grade varchar
  member_id varchar
  snapshot_date datetime [note: 'date/datetime']
  previous_grade varchar [null]
  is_grade_change varchar
  cumulative_orders varchar
  cumulative_amount_krw varchar
  Note: 'customer_grade_history | rows=30379 | '
}

Table customer_rfm {
  f_score varchar
  m_score varchar
  r_score varchar
  frequency varchar
  member_id varchar
  rfm_score varchar
  rfm_segment varchar
  monetary_krw varchar
  recency_days varchar [null]
  customer_tier varchar
  snapshot_date datetime [note: 'date/datetime']
  avg_order_value varchar
  last_order_date datetime [null, note: 'date/datetime']
  churn_risk_score varchar
  days_as_customer varchar
  first_order_date datetime [null, note: 'date/datetime']
  predicted_clv_krw varchar
  next_purchase_propensity varchar
  Note: 'customer_rfm | rows=8500 | '
}

Table customers {
  age varchar
  gender varchar
  region varchar
  age_group varchar
  member_id varchar
  birth_year varchar
  created_at datetime [note: 'date/datetime']
  updated_at datetime [note: 'date/datetime']
  signup_date datetime [note: 'date/datetime']
  member_email varchar
  member_grade varchar
  total_orders varchar
  member_status varchar
  signup_device varchar
  household_size varchar
  marital_status varchar
  signup_channel varchar
  available_point varchar
  last_login_date datetime [note: 'date/datetime']
  last_order_date datetime [null, note: 'date/datetime']
  member_name_hash varchar
  member_phone_hash varchar
  signup_utm_medium varchar
  signup_utm_source varchar
  marketing_sms_agree varchar
  signup_utm_campaign varchar [null]
  marketing_email_agree varchar
  marketing_kakao_agree varchar
  total_purchase_amount varchar
  Note: 'customers | rows=8500 | '
}

Table daily_performance {
  cpa varchar
  cpc varchar
  cpm varchar
  ctr varchar
  cvr varchar
  date datetime [note: 'date/datetime']
  roas varchar
  clicks varchar
  ad_cost varchar
  channel varchar
  campaign_id varchar
  conversions varchar
  creative_id varchar
  impressions varchar
  conversion_revenue varchar
  Note: 'daily_performance | rows=32 | '
}

Table ga4_page_events {
  app_info varchar [note: 'null']
  batch_event_index int
  batch_ordering_id int
  batch_page_id int
  "collected_traffic_source.dclid" varchar [note: 'null']
  "collected_traffic_source.gclid" varchar [note: 'null']
  "collected_traffic_source.manual_campaign_id" varchar [note: 'null']
  "collected_traffic_source.manual_campaign_name" varchar [note: 'null']
  "collected_traffic_source.manual_content" varchar [note: 'null']
  "collected_traffic_source.manual_medium" varchar [note: 'null']
  "collected_traffic_source.manual_source" varchar [note: 'null']
  "collected_traffic_source.manual_term" varchar [note: 'null']
  "collected_traffic_source.srsltid" varchar [note: 'null']
  "device.category" varchar
  "device.is_limited_ad_tracking" varchar
  "device.language" varchar
  "device.mobile_brand_name" varchar
  "device.mobile_model_name" varchar
  "device.operating_system" varchar
  "device.operating_system_version" varchar
  "device.time_zone_offset_seconds" int
  "device.web_info.browser" varchar
  "device.web_info.browser_version" varchar
  "device.web_info.hostname" varchar
  ecommerce varchar [note: 'null']
  "ecommerce.purchase_revenue" varchar [note: 'null']
  "ecommerce.purchase_revenue_in_usd" varchar [note: 'null']
  "ecommerce.refund_value" varchar [note: 'null']
  "ecommerce.refund_value_in_usd" varchar [note: 'null']
  "ecommerce.shipping_value" varchar [note: 'null']
  "ecommerce.shipping_value_in_usd" varchar [note: 'null']
  "ecommerce.tax_value" varchar [note: 'null']
  "ecommerce.tax_value_in_usd" varchar [note: 'null']
  "ecommerce.total_item_quantity" int
  "ecommerce.transaction_id" varchar [note: 'null']
  "ecommerce.unique_items" int
  event_bundle_sequence_id int
  event_date date [note: 'date(yyyymmdd)']
  event_dimensions varchar [note: 'null']
  event_name varchar
  "event_params[].key" varchar
  "event_params[].value.double_value" float
  "event_params[].value.int_value" int
  "event_params[].value.string_value" varchar
  event_previous_timestamp varchar [note: 'null']
  event_server_timestamp_offset int
  event_timestamp int
  event_value_in_usd varchar [note: 'null']
  "geo.city" varchar
  "geo.continent" varchar
  "geo.country" varchar
  "geo.metro" varchar
  "geo.region" varchar
  "geo.sub_continent" varchar
  is_active_user boolean [note: 'bool']
  "items[]" varchar [note: 'array(empty)']
  "items[].affiliation" varchar
  "items[].coupon" varchar [note: 'null']
  "items[].creative_name" varchar [note: 'null']
  "items[].creative_slot" varchar [note: 'null']
  "items[].item_brand" varchar
  "items[].item_category" varchar
  "items[].item_category2" varchar [note: 'null']
  "items[].item_category3" varchar [note: 'null']
  "items[].item_category4" varchar [note: 'null']
  "items[].item_category5" varchar [note: 'null']
  "items[].item_id" varchar
  "items[].item_list_id" varchar [note: 'null']
  "items[].item_list_index" int [note: 'int | null']
  "items[].item_list_name" varchar [note: 'null']
  "items[].item_name" varchar
  "items[].item_refund" varchar [note: 'null']
  "items[].item_refund_in_usd" varchar [note: 'null']
  "items[].item_revenue" varchar [note: 'null']
  "items[].item_revenue_in_usd" varchar [note: 'null']
  "items[].item_variant" varchar [note: 'null']
  "items[].location_id" varchar [note: 'null']
  "items[].price" float
  "items[].price_in_usd" float
  "items[].promotion_id" varchar [note: 'null']
  "items[].promotion_name" varchar [note: 'null']
  "items[].quantity" int
  platform varchar
  "privacy_info.ads_storage" varchar
  "privacy_info.analytics_storage" varchar
  "privacy_info.uses_transient_token" varchar
  publisher varchar [note: 'null']
  "session_traffic_source_last_click.cross_channel_campaign.campaign_id" varchar [note: 'null']
  "session_traffic_source_last_click.cross_channel_campaign.campaign_name" varchar [note: 'null']
  "session_traffic_source_last_click.cross_channel_campaign.default_channel_group" varchar
  "session_traffic_source_last_click.cross_channel_campaign.medium" varchar
  "session_traffic_source_last_click.cross_channel_campaign.primary_channel_group" varchar
  "session_traffic_source_last_click.cross_channel_campaign.source" varchar
  "session_traffic_source_last_click.google_ads_campaign" varchar [note: 'null']
  "session_traffic_source_last_click.manual_campaign.campaign_id" varchar [note: 'null']
  "session_traffic_source_last_click.manual_campaign.campaign_name" varchar [note: 'null']
  "session_traffic_source_last_click.manual_campaign.content" varchar [note: 'null']
  "session_traffic_source_last_click.manual_campaign.creative_format" varchar [note: 'null']
  "session_traffic_source_last_click.manual_campaign.marketing_tactic" varchar [note: 'null']
  "session_traffic_source_last_click.manual_campaign.medium" varchar [note: 'null']
  "session_traffic_source_last_click.manual_campaign.source" varchar [note: 'null']
  "session_traffic_source_last_click.manual_campaign.source_platform" varchar [note: 'null']
  "session_traffic_source_last_click.manual_campaign.term" varchar [note: 'null']
  stream_id varchar
  "traffic_source.medium" varchar
  "traffic_source.name" varchar
  "traffic_source.source" varchar
  user_first_touch_timestamp int
  user_id varchar [note: 'null']
  user_ltv varchar [note: 'null']
  "user_properties[]" varchar [note: 'array(empty)']
  user_pseudo_id varchar
  Note: 'ga4_page_events | rows=84143 | 이종 이벤트 9종 전수 스캔'
}

Table ga4_traffic_source {
  app_info varchar [note: 'null']
  batch_event_index int
  batch_ordering_id int
  batch_page_id int
  "collected_traffic_source.dclid" varchar [note: 'null']
  "collected_traffic_source.gclid" varchar [note: 'null']
  "collected_traffic_source.manual_campaign_id" varchar [note: 'null']
  "collected_traffic_source.manual_campaign_name" varchar [note: 'null']
  "collected_traffic_source.manual_content" varchar [note: 'null']
  "collected_traffic_source.manual_medium" varchar [note: 'null']
  "collected_traffic_source.manual_source" varchar [note: 'null']
  "collected_traffic_source.manual_term" varchar [note: 'null']
  "collected_traffic_source.srsltid" varchar [note: 'null']
  "device.category" varchar
  "device.is_limited_ad_tracking" varchar
  "device.language" varchar
  "device.mobile_brand_name" varchar
  "device.mobile_model_name" varchar
  "device.operating_system" varchar
  "device.operating_system_version" varchar
  "device.time_zone_offset_seconds" int
  "device.web_info.browser" varchar
  "device.web_info.browser_version" varchar
  "device.web_info.hostname" varchar
  ecommerce varchar [note: 'null']
  "ecommerce.purchase_revenue" int
  "ecommerce.purchase_revenue_in_usd" float
  "ecommerce.refund_value" varchar [note: 'null']
  "ecommerce.refund_value_in_usd" varchar [note: 'null']
  "ecommerce.shipping_value" int
  "ecommerce.shipping_value_in_usd" float [note: 'float | int']
  "ecommerce.tax_value" int
  "ecommerce.tax_value_in_usd" int
  "ecommerce.total_item_quantity" int
  "ecommerce.transaction_id" varchar
  "ecommerce.unique_items" int
  event_bundle_sequence_id int
  event_date date [note: 'date(yyyymmdd)']
  event_dimensions varchar [note: 'null']
  event_name varchar
  "event_params[].key" varchar
  "event_params[].value.double_value" float
  "event_params[].value.int_value" int
  "event_params[].value.string_value" varchar
  event_previous_timestamp varchar [note: 'null']
  event_server_timestamp_offset int
  event_timestamp int
  event_value_in_usd float [note: 'float | null']
  "geo.city" varchar
  "geo.continent" varchar
  "geo.country" varchar
  "geo.metro" varchar
  "geo.region" varchar
  "geo.sub_continent" varchar
  is_active_user boolean [note: 'bool']
  "items[]" varchar [note: 'array(empty)']
  "items[].affiliation" varchar
  "items[].coupon" varchar [note: 'null']
  "items[].creative_name" varchar [note: 'null']
  "items[].creative_slot" varchar [note: 'null']
  "items[].item_brand" varchar
  "items[].item_category" varchar
  "items[].item_category2" varchar [note: 'null']
  "items[].item_category3" varchar [note: 'null']
  "items[].item_category4" varchar [note: 'null']
  "items[].item_category5" varchar [note: 'null']
  "items[].item_id" varchar
  "items[].item_list_id" varchar [note: 'null']
  "items[].item_list_index" varchar [note: 'null']
  "items[].item_list_name" varchar [note: 'null']
  "items[].item_name" varchar
  "items[].item_refund" varchar [note: 'null']
  "items[].item_refund_in_usd" varchar [note: 'null']
  "items[].item_revenue" int
  "items[].item_revenue_in_usd" float
  "items[].item_variant" varchar [note: 'null']
  "items[].location_id" varchar [note: 'null']
  "items[].price" float
  "items[].price_in_usd" float
  "items[].promotion_id" varchar [note: 'null']
  "items[].promotion_name" varchar [note: 'null']
  "items[].quantity" int
  platform varchar
  "privacy_info.ads_storage" varchar
  "privacy_info.analytics_storage" varchar
  "privacy_info.uses_transient_token" varchar
  publisher varchar [note: 'null']
  "session_traffic_source_last_click.cross_channel_campaign.campaign_id" varchar [note: 'null']
  "session_traffic_source_last_click.cross_channel_campaign.campaign_name" varchar [note: 'null']
  "session_traffic_source_last_click.cross_channel_campaign.default_channel_group" varchar
  "session_traffic_source_last_click.cross_channel_campaign.medium" varchar
  "session_traffic_source_last_click.cross_channel_campaign.primary_channel_group" varchar
  "session_traffic_source_last_click.cross_channel_campaign.source" varchar
  "session_traffic_source_last_click.google_ads_campaign" varchar [note: 'null']
  "session_traffic_source_last_click.manual_campaign.campaign_id" varchar [note: 'null']
  "session_traffic_source_last_click.manual_campaign.campaign_name" varchar [note: 'null']
  "session_traffic_source_last_click.manual_campaign.content" varchar [note: 'null']
  "session_traffic_source_last_click.manual_campaign.creative_format" varchar [note: 'null']
  "session_traffic_source_last_click.manual_campaign.marketing_tactic" varchar [note: 'null']
  "session_traffic_source_last_click.manual_campaign.medium" varchar [note: 'null']
  "session_traffic_source_last_click.manual_campaign.source" varchar [note: 'null']
  "session_traffic_source_last_click.manual_campaign.source_platform" varchar [note: 'null']
  "session_traffic_source_last_click.manual_campaign.term" varchar [note: 'null']
  stream_id varchar
  "traffic_source.medium" varchar
  "traffic_source.name" varchar
  "traffic_source.source" varchar
  user_first_touch_timestamp int
  user_id varchar [note: 'null']
  user_ltv varchar [note: 'null']
  "user_properties[]" varchar [note: 'array(empty)']
  user_pseudo_id varchar
  Note: 'ga4_traffic_source | rows=38319 | 이종 이벤트 3종 전수 스캔'
}

Table household_structure {
  top_region varchar
  member_count varchar
  snapshot_date datetime [note: 'date/datetime']
  household_type varchar
  primary_persona varchar
  purchaser_count varchar
  member_share_pct varchar
  purchase_rate_pct varchar
  repurchaser_count varchar
  total_revenue_krw varchar
  avg_household_size varchar
  preferred_category varchar
  household_type_code varchar
  repurchase_rate_pct varchar
  top_region_share_pct varchar
  marketing_implication varchar
  avg_revenue_per_member_krw varchar
  avg_revenue_per_purchaser_krw varchar
  Note: 'household_structure | rows=12 | '
}

Table instagram_engagement {
  "data[]._meta.category" varchar
  "data[]._meta.related_campaign" varchar [note: 'null']
  "data[].caption" varchar
  "data[].children.data[].id" varchar
  "data[].children.data[].media_type" varchar
  "data[].children.data[].media_url" varchar
  "data[].comments_count" int
  "data[].id" varchar
  "data[].insights.data[].id" varchar
  "data[].insights.data[].name" varchar
  "data[].insights.data[].period" varchar
  "data[].insights.data[].title" varchar
  "data[].insights.data[].values[].value" float [note: 'float | int']
  "data[].like_count" int
  "data[].media_product_type" varchar
  "data[].media_type" varchar
  "data[].media_url" varchar
  "data[].permalink" varchar
  "data[].thumbnail_url" varchar
  "data[].timestamp" datetime [note: 'date/datetime']
  "data[].username" varchar
  "paging.cursors.after" varchar
  "paging.cursors.before" varchar
  Note: 'instagram_engagement | rows=40 | '
}

Table kakao_bizmessage {
  "campaigns[].campaign_id" varchar
  "campaigns[].campaign_name" varchar
  "campaigns[].campaign_type" varchar
  "campaigns[].message_content.body" varchar
  "campaigns[].message_content.button.name" varchar
  "campaigns[].message_content.button.type" varchar
  "campaigns[].message_content.button.url_mobile" varchar
  "campaigns[].message_content.button.url_pc" varchar
  "campaigns[].message_type" varchar
  "campaigns[].next" boolean [note: 'bool']
  "campaigns[].results_sample[].cid" varchar
  "campaigns[].results_sample[].code" varchar
  "campaigns[].results_sample[].code_detail.detail_code" varchar
  "campaigns[].results_sample[].code_detail.detail_message" varchar
  "campaigns[].results_sample[].message_type" varchar
  "campaigns[].results_sample[].phone_number_hash" varchar
  "campaigns[].results_sample[].rcs_status" varchar
  "campaigns[].results_sample[].reg_date" datetime [note: 'date/datetime']
  "campaigns[].results_sample[].result_date" datetime [note: 'date/datetime']
  "campaigns[].results_sample[].send_date" datetime [note: 'date/datetime']
  "campaigns[].results_sample[].sender_key" varchar
  "campaigns[].results_sample[].status" varchar
  "campaigns[].results_sample[].template_code" varchar
  "campaigns[].results_sample[].uid" varchar
  "campaigns[].results_sample_note" varchar
  "campaigns[].send_request_date" datetime [note: 'date/datetime']
  "campaigns[].sender_key" varchar
  "campaigns[].sender_no" varchar
  "campaigns[].summary.avg_order_value" int
  "campaigns[].summary.click_count" int
  "campaigns[].summary.click_rate" float
  "campaigns[].summary.click_through_rate_open" float
  "campaigns[].summary.conversion_amount_krw" int
  "campaigns[].summary.conversion_count" int
  "campaigns[].summary.conversion_rate_click" float
  "campaigns[].summary.cost_per_message_krw" int
  "campaigns[].summary.fail_count" int
  "campaigns[].summary.open_count" int
  "campaigns[].summary.open_rate" float
  "campaigns[].summary.revenue_per_message_krw" float
  "campaigns[].summary.roi_percent" float
  "campaigns[].summary.success_count" int
  "campaigns[].summary.success_rate" float
  "campaigns[].summary.target_recipients" int
  "campaigns[].summary.total_cost_krw" int
  "campaigns[].template_code" varchar
  "campaigns[].template_name" varchar
  "campaigns[].total_count_in_db" int
  code varchar
  "code_detail.detail_code" varchar
  "code_detail.detail_message" varchar
  next boolean [note: 'bool']
  "query_date_range.end_date" datetime [note: 'date/datetime']
  "query_date_range.start_date" datetime [note: 'date/datetime']
  status varchar
  Note: 'kakao_bizmessage | rows=2 | '
}

Table keyword_performance {
  roas varchar
  clicks varchar
  ad_cost varchar
  channel varchar
  keyword varchar
  competition varchar
  conversions varchar
  impressions varchar
  keyword_group varchar
  quality_score varchar
  conversion_revenue varchar
  Note: 'keyword_performance | rows=18 | '
}

Table marketing_monthly_targets {
  period varchar
  target_ctr varchar
  target_cvr varchar
  target_roas varchar
  target_clicks varchar
  breakeven_roas varchar
  target_conversions varchar
  target_impressions varchar
  Note: 'marketing_monthly_targets | rows=1 | '
}

Table meta_ads_by_age {
  "data[].account_currency" varchar
  "data[].account_id" varchar
  "data[].account_name" varchar
  "data[].action_values[]" varchar [note: 'array(empty)']
  "data[].action_values[].action_type" varchar
  "data[].action_values[].value" varchar
  "data[].actions[].action_type" varchar
  "data[].actions[].value" varchar
  "data[].age" varchar
  "data[].attribution_setting" varchar
  "data[].buying_type" varchar
  "data[].campaign_id" varchar
  "data[].campaign_name" varchar
  "data[].clicks" varchar
  "data[].cost_per_action_type[]" varchar [note: 'array(empty)']
  "data[].cost_per_action_type[].action_type" varchar
  "data[].cost_per_action_type[].value" varchar
  "data[].cost_per_inline_link_click" varchar
  "data[].cpc" varchar
  "data[].cpm" varchar
  "data[].ctr" varchar
  "data[].date_start" datetime [note: 'date/datetime']
  "data[].date_stop" datetime [note: 'date/datetime']
  "data[].frequency" varchar
  "data[].impressions" varchar
  "data[].inline_link_click_ctr" varchar
  "data[].inline_link_clicks" varchar
  "data[].objective" varchar
  "data[].purchase_roas[]" varchar [note: 'array(empty)']
  "data[].purchase_roas[].action_type" varchar
  "data[].purchase_roas[].value" varchar
  "data[].reach" varchar
  "data[].spend" varchar
  "data[].unique_clicks" varchar
  "paging.cursors.after" varchar
  "paging.cursors.before" varchar
  Note: 'meta_ads_by_age | rows=540 | '
}

Table meta_ads_performance {
  "data[].account_currency" varchar
  "data[].account_id" varchar
  "data[].account_name" varchar
  "data[].action_values[]" varchar [note: 'array(empty)']
  "data[].action_values[].action_type" varchar
  "data[].action_values[].value" varchar
  "data[].actions[].action_type" varchar
  "data[].actions[].value" varchar
  "data[].attribution_setting" varchar
  "data[].buying_type" varchar
  "data[].campaign_id" varchar
  "data[].campaign_name" varchar
  "data[].clicks" varchar
  "data[].cost_per_action_type[].action_type" varchar
  "data[].cost_per_action_type[].value" varchar
  "data[].cost_per_inline_link_click" varchar
  "data[].cpc" varchar
  "data[].cpm" varchar
  "data[].ctr" varchar
  "data[].date_start" datetime [note: 'date/datetime']
  "data[].date_stop" datetime [note: 'date/datetime']
  "data[].frequency" varchar
  "data[].impressions" varchar
  "data[].inline_link_click_ctr" varchar
  "data[].inline_link_clicks" varchar
  "data[].objective" varchar
  "data[].purchase_roas[]" varchar [note: 'array(empty)']
  "data[].purchase_roas[].action_type" varchar
  "data[].purchase_roas[].value" varchar
  "data[].reach" varchar
  "data[].spend" varchar
  "data[].unique_clicks" varchar
  "paging.cursors.after" varchar
  "paging.cursors.before" varchar
  Note: 'meta_ads_performance | rows=90 | '
}

Table meta_instagram_inapp {
  "data[].account_currency" varchar
  "data[].account_id" varchar
  "data[].account_name" varchar
  "data[].action_values[]" varchar [note: 'array(empty)']
  "data[].action_values[].action_type" varchar
  "data[].action_values[].value" varchar
  "data[].actions[].action_type" varchar
  "data[].actions[].value" varchar
  "data[].attribution_setting" varchar
  "data[].buying_type" varchar
  "data[].campaign_id" varchar
  "data[].campaign_name" varchar
  "data[].clicks" varchar
  "data[].cost_per_action_type[].action_type" varchar
  "data[].cost_per_action_type[].value" varchar
  "data[].cost_per_inline_link_click" varchar
  "data[].cpc" varchar
  "data[].cpm" varchar
  "data[].ctr" varchar
  "data[].date_start" datetime [note: 'date/datetime']
  "data[].date_stop" datetime [note: 'date/datetime']
  "data[].frequency" varchar
  "data[].impressions" varchar
  "data[].inline_link_click_ctr" varchar
  "data[].inline_link_clicks" varchar
  "data[].objective" varchar
  "data[].platform_position" varchar
  "data[].publisher_platform" varchar
  "data[].purchase_roas[]" varchar [note: 'array(empty)']
  "data[].purchase_roas[].action_type" varchar
  "data[].purchase_roas[].value" varchar
  "data[].reach" varchar
  "data[].spend" varchar
  "data[].unique_clicks" varchar
  "paging.cursors.after" varchar
  "paging.cursors.before" varchar
  Note: 'meta_instagram_inapp | rows=150 | '
}

Table naver_advoost {
  report_date datetime [note: 'date/datetime']
  campaign_id varchar
  campaign_name varchar
  campaign_type varchar
  campaign_objective varchar
  creative_type varchar
  impressions varchar
  clicks varchar
  cost varchar
  ctr varchar
  cpc varchar
  cpm varchar
  view_through_conversions varchar
  click_through_conversions varchar
  total_conversions varchar
  conversion_value varchar
  roas varchar
  vtcvr varchar
  ctcvr varchar
  video_play_25 varchar
  video_play_50 varchar
  video_play_75 varchar
  video_play_100 varchar
  Note: 'naver_advoost | rows=90 | '
}

Table naver_interest_alert {
  channel varchar
  shop_name varchar
  collect_date varchar
  avg_order_value varchar
  conversion_count varchar
  conversion_amount varchar
  message_open_rate varchar
  snapshot_datetime datetime [note: 'date/datetime']
  message_click_rate varchar
  message_open_count varchar
  message_send_count varchar
  message_click_count varchar
  interest_customer_added varchar
  interest_customer_total varchar
  notification_opt_in_rate varchar
  interest_customer_removed varchar
  conversion_rate_from_click varchar
  notification_customer_added varchar
  notification_customer_total varchar
  interest_customer_net_change varchar
  notification_customer_removed varchar
  notification_customer_net_change varchar
  Note: 'naver_interest_alert | rows=4 | '
}

Table naver_searchad {
  "data[].avgRnk" float
  "data[].ccnt" int
  "data[].clkCnt" int
  "data[].convAmt" int
  "data[].cpConv" int
  "data[].cpc" int
  "data[].crto" float
  "data[].ctr" float
  "data[].device" varchar
  "data[].id" varchar
  "data[].impCnt" int
  "data[].nccAdgroupId" varchar
  "data[].nccCampaignId" varchar
  "data[].nccKeywordId" varchar
  "data[].ror" float
  "data[].salesAmt" int
  "data[].statDt" datetime [note: 'date/datetime']
  Note: 'naver_searchad | rows=1680 | '
}

Table naver_talktalk {
  "campaigns[].campaign_id" varchar
  "campaigns[].campaign_name" varchar
  "campaigns[].campaign_type" varchar
  "campaigns[].channel" varchar
  "campaigns[].channel_id" varchar
  "campaigns[].message_blocks[].block_type" varchar
  "campaigns[].message_blocks[].content.action_type" varchar
  "campaigns[].message_blocks[].content.action_url" varchar
  "campaigns[].message_blocks[].content.alt_text" varchar
  "campaigns[].message_blocks[].content.height" int
  "campaigns[].message_blocks[].content.name" varchar
  "campaigns[].message_blocks[].content.text" varchar
  "campaigns[].message_blocks[].content.url" varchar
  "campaigns[].message_blocks[].content.width" int
  "campaigns[].message_blocks[].order" int
  "campaigns[].next" boolean [note: 'bool']
  "campaigns[].results_sample[].clicked_at" datetime [note: 'date/datetime | null']
  "campaigns[].results_sample[].delivered_at" datetime [note: 'date/datetime | null']
  "campaigns[].results_sample[].delivered_status" varchar
  "campaigns[].results_sample[].error_code" varchar [note: 'null']
  "campaigns[].results_sample[].error_message" varchar [note: 'null']
  "campaigns[].results_sample[].favorite" boolean [note: 'bool']
  "campaigns[].results_sample[].friend_id_hash" varchar
  "campaigns[].results_sample[].message_id" varchar
  "campaigns[].results_sample[].opened_at" datetime [note: 'date/datetime | null']
  "campaigns[].results_sample[].unfriend_after_send" boolean [note: 'bool']
  "campaigns[].results_sample[].unfriend_at" datetime [note: 'date/datetime']
  "campaigns[].results_sample_note" varchar
  "campaigns[].send_completion_date" datetime [note: 'date/datetime']
  "campaigns[].send_request_date" datetime [note: 'date/datetime']
  "campaigns[].summary.avg_order_value" int
  "campaigns[].summary.click_count" int
  "campaigns[].summary.click_rate" float
  "campaigns[].summary.click_through_rate_open" float
  "campaigns[].summary.conversion_amount_krw" int
  "campaigns[].summary.conversion_count" int
  "campaigns[].summary.conversion_rate_click" float
  "campaigns[].summary.cost_per_message_krw" int
  "campaigns[].summary.delivered_count" int
  "campaigns[].summary.delivered_rate" float
  "campaigns[].summary.failed_count" int
  "campaigns[].summary.open_count" int
  "campaigns[].summary.open_rate" float
  "campaigns[].summary.revenue_per_message_krw" float
  "campaigns[].summary.roi_percent" float
  "campaigns[].summary.target_friends" int
  "campaigns[].summary.total_cost_krw" int
  "campaigns[].summary.unfriend_after_send" int
  "campaigns[].summary.unfriend_rate" float
  "campaigns[].total_count_in_db" int
  channel varchar
  channel_id varchar
  channel_name varchar
  channel_status varchar
  code int
  "friend_summary.active_friends_30d" int
  "friend_summary.channel_status" varchar
  "friend_summary.favorite_count" int
  "friend_summary.marketing_opt_in_count" int
  "friend_summary.marketing_opt_in_rate" float
  "friend_summary.net_change_april" int
  "friend_summary.new_friends_april" int
  "friend_summary.total_friends" int
  "friend_summary.unfriend_april" int
  "query_date_range.end_date" datetime [note: 'date/datetime']
  "query_date_range.start_date" datetime [note: 'date/datetime']
  shop_id varchar
  snapshot_datetime datetime [note: 'date/datetime']
  status varchar
  Note: 'naver_talktalk | rows=2 | '
}

Table orders {
  order_id varchar
  referrer varchar [null, note: '(미관측)']
  utm_term varchar [null, note: '(미관측)']
  member_id varchar [null]
  created_at datetime [note: 'date/datetime']
  order_date datetime [note: 'date/datetime']
  updated_at datetime [note: 'date/datetime']
  used_point varchar
  utm_medium varchar [null]
  utm_source varchar [null]
  device_type varchar
  items_count varchar
  utm_content varchar [null, note: '(미관측)']
  order_status varchar
  shipping_fee varchar
  utm_campaign varchar [null]
  is_first_order varchar
  payment_amount varchar
  payment_method varchar
  product_amount varchar
  promotion_code varchar [null]
  total_quantity varchar
  discount_amount varchar
  top_product_name varchar
  product_categories varchar
  channel_attribution varchar
  Note: 'orders | rows=3420 | '
}

Table promotions {
  promotion_id int
  promotion_code varchar(50)
  promotion_name varchar(200)
  promotion_type varchar(30)
  start_date datetime
  end_date datetime
  discount_type varchar(20)
  discount_value int
  min_order_amount int
  max_discount_amount int
  target_segment varchar(50)
  applicable_products text
  max_usage_per_user int
  total_usage_limit int
  is_active tinyint(1)
  created_at datetime
  updated_at datetime
  INSERT into
  Note: 'promotions |  | from promotions.sql'
}

Table promotion_performance {
  performance_id int
  promotion_id int
  promotion_code varchar(50)
  snapshot_date date
  total_usage_count int
  unique_users_count int
  total_revenue bigint
  total_discount_given bigint
  avg_order_value int
  new_customer_count int
  existing_customer_count int
  conversion_rate decimal(5,2)
  roi_percent decimal(8,2)
  created_at datetime
  INSERT into
  Note: 'promotion_performance |  | from promotions.sql'
}

Table promotion_usage_history {
  usage_id bigint
  promotion_id int
  promotion_code varchar(50)
  member_id varchar(20)
  order_id varchar(20)
  used_at datetime
  discount_amount int
  order_amount int
  is_first_order tinyint(1)
  order_status varchar(20)
  INSERT into
  Note: 'promotion_usage_history |  | from promotions.sql'
}

Table reviews {
  date datetime [note: 'date/datetime']
  text varchar
  rating varchar
  product varchar
  review_id varchar
  Note: 'reviews | rows=24 | '
}

Table signup_events {
  browser varchar
  ip_hash varchar
  geo_city varchar
  referrer varchar [null]
  utm_term varchar [null]
  device_os varchar
  member_id varchar
  created_at datetime [note: 'date/datetime']
  geo_region varchar
  user_agent varchar
  utm_medium varchar
  utm_source varchar
  geo_country varchar
  utm_content varchar [null]
  ga_client_id varchar
  landing_page varchar
  utm_campaign varchar [null]
  ga_session_id varchar
  signup_device varchar
  signup_method varchar
  signup_channel varchar
  event_value_krw varchar
  signup_event_id varchar
  signup_timestamp datetime [note: 'date/datetime']
  first_visit_source varchar
  has_promotion_code varchar
  marketing_sms_agree varchar
  promotion_code_used varchar [null]
  signup_form_version varchar
  days_from_first_visit varchar
  marketing_email_agree varchar
  marketing_kakao_agree varchar
  Note: 'signup_events | rows=600 | '
}

// ========== Refs (확정 — draft 컬럼 검증 통과) ==========
Ref: creatives.campaign_id > campaigns.campaign_id
Ref: daily_performance.campaign_id > campaigns.campaign_id
Ref: daily_performance.creative_id > creatives.creative_id
Ref: crm_message_variants.campaign_id > crm_campaigns.campaign_id
Ref: crm_send_logs.campaign_id > crm_campaigns.campaign_id
Ref: crm_send_logs.variant_id > crm_message_variants.variant_id
Ref: customer_rfm.member_id > customers.member_id
Ref: customer_grade_history.member_id > customers.member_id
Ref: orders.member_id > customers.member_id
Ref: signup_events.member_id > customers.member_id
Ref: promotion_usage_history.member_id > customers.member_id
Ref: promotion_usage_history.order_id > orders.order_id
Ref: orders.promotion_code > promotions.promotion_code
Ref: promotion_performance.promotion_id > promotions.promotion_id
Ref: promotion_usage_history.promotion_id > promotions.promotion_id
Ref: promotion_performance.promotion_code > promotions.promotion_code
Ref: promotion_usage_history.promotion_code > promotions.promotion_code

// ========== Refs (추정 — 검증 필요, 비활성) ==========
// Ref: crm_campaigns.campaign_id > campaigns.campaign_id  // 추정: 추정. CRM 캠페인 id 가 광고 campaigns 와 동일 키 공간인지는 불확실(crm_campaigns.campaign_id=int vs campaigns.campaign_id=string). 별 도메인일 가능성 높아 약한 연결.
// Ref: ga4_traffic_source.user_pseudo_id > ga4_page_events.user_pseudo_id  // 추정: 추정. 두 GA4 이벤트 스트림은 동일 user_pseudo_id 공간을 공유(같은 GA4 export). FK라기보다 동일 식별자 join 키.
// Ref: ga4_page_events.user_id > customers.member_id  // 추정: 추정. GA4 user_id(로그인 사용자)가 customers.member_id 와 매핑될 가능성. 대부분 null, 검증 필요.
// Ref: ga4_traffic_source.user_id > customers.member_id  // 추정: 추정. GA4 user_id→회원 매핑 가능성. 대부분 null, 검증 필요.
// Ref: meta_ads_by_age.account_id > meta_ads_performance.account_id  // 추정: 추정. Meta 광고 3소스가 동일 account_id(광고계정) 공유. 별 엔티티(ad_account) 테이블 부재로 명시 PK측 없음 — 공유 차원키.
// Ref: meta_instagram_inapp.account_id > meta_ads_performance.account_id  // 추정: 추정. Meta Instagram 인앱이 동일 account_id 공유. 공유 차원키(ad_account).
// Ref: kakao_bizmessage.template_code > naver_talktalk.code  // 추정: 추정·약함. fk_hints 의 'code' 공유는 응답 status code 와 template_code 혼동 가능성. 실제 FK 아닐 확률 높음 — 도메인상 무관.

// ========== TableGroups (도메인) ==========
TableGroup "광고 캠페인 (자체 정의)" {
  campaigns
  creatives
  daily_performance
  budget_allocation
  ab_tests
}
TableGroup "광고 매체 성과 — Meta" {
  meta_ads_performance
  meta_ads_by_age
  meta_instagram_inapp
}
TableGroup "광고 매체 성과 — Naver" {
  naver_advoost
  naver_searchad
  keyword_performance
}
TableGroup "광고 목표/예산 설정" {
  channel_targets
  marketing_monthly_targets
}
TableGroup "거래 (Cafe24 주문)" {
  orders
  category_sales
  reviews
}
TableGroup "회원 (Cafe24 고객)" {
  customers
  customer_rfm
  customer_grade_history
  household_structure
  signup_events
}
TableGroup "행동 이벤트 (GA4)" {
  ga4_page_events
  ga4_traffic_source
}
TableGroup "CRM 메시징 (자체)" {
  crm_campaigns
  crm_message_variants
  crm_send_logs
}
TableGroup "메시징 매체 (Kakao/Naver)" {
  kakao_bizmessage
  naver_talktalk
  naver_interest_alert
}
TableGroup "프로모션/쿠폰" {
  promotions
  promotion_performance
  promotion_usage_history
}
TableGroup "소셜 인게이지먼트 / 광고운영 로그" {
  instagram_engagement
  ad_change_history
}
```

## §4 drift — 옛 ERD(2026-05-23) 대비

> 옛 ERD(21 엔티티, 2026-05-23) vs 신규 인벤토리(30 파일 소스). 신규 추가 테이블 9개, 삭제 테이블 0개, 컬럼 변경 테이블 5개. 추가 테이블 9개는 batch 확장으로 들어온 신규 소스(ab_tests·budget_allocation·campaigns·channel_targets·creatives·daily_performance·keyword_performance·marketing_monthly_targets·reviews). 삭제 테이블 0 — 옛 21 엔티티는 모두 신규 인벤토리에 존속. 컬럼 변경 5건은 모두 '추가만' 발생(삭제 0)이며, 신규 스캐너가 옛 ERD가 버렸던 JSON 래퍼 형제 메타필드(paging.cursors.after/before 전 JSON data[] 소스, ad_change_history 의 _meta.* 5필드)를 전수 포착한 결과. 래퍼 prefix(data[].)·빈배열 컨테이너 마커(items[]·action_values[] 등)는 표기차로 정규화해 제외했으므로, naver_searchad·ga4_traffic_source·ga4_page_events 는 실질 무변동으로 확인.

- **추가 테이블 9**: `ab_tests.csv`, `budget_allocation.csv`, `campaigns.csv`, `channel_targets.csv`, `creatives.csv`, `daily_performance.csv`, `keyword_performance.csv`, `marketing_monthly_targets.csv`, `reviews.csv` — demo placeholder batch(§5).
- **삭제 테이블 0**: 없음(옛 21 엔티티 전부 존속)
- **컬럼 변경 5** (전부 *추가만*, 삭제 0 — 신 스캐너가 옛것이 버린 JSON 래퍼/`_meta` 형제필드 포착):
  - `meta_ads_performance` +[paging_cursors_after, paging_cursors_before]
  - `meta_ads_by_age` +[paging_cursors_after, paging_cursors_before]
  - `meta_instagram_inapp` +[paging_cursors_after, paging_cursors_before]
  - `instagram_engagement` +[paging_cursors_after, paging_cursors_before]
  - `ad_change_history` +[meta_ad_account_id, meta_query_date_range_since, meta_query_date_range_until, meta_source, meta_total_events, paging_cursors_after, paging_cursors_before]

## §5 데이터사전 정합 + stub 분류

> raw 30파일(인벤토리 30 엔트리, SQL 2개는 다중 테이블 포함) vs 데이터사전 21파일(clumi_mock_01~21) 대조. (1) 사전 미등재 raw 9파일=ab_tests/budget_allocation/campaigns/channel_targets/creatives/daily_performance/keyword_performance/marketing_monthly_targets/reviews — blooming demo placeholder 계열로 추정(분석 21파일 family와 분리). (2) 평면 CSV/SQL 실드리프트: orders는 사전이 customer_age_group/customer_gender/guest_email_hash/region을 기재하나 raw에 없고 raw엔 created_at/updated_at/used_point/referrer; customers는 사전 membership_grade/membership_point vs raw member_grade/available_point(이름 드리프트); household_structure는 사전 estimated_member_count/avg_purchase_per_member_krw vs raw member_count/avg_revenue_per_member_krw(이름 드리프트). (3) naver_searchad.json은 사전이 친화 별칭(camp_id/kwd/stat_dt)으로, raw는 네이버 native 키(nccCampaignId/nccKeywordId/statDt)로 — 별칭 vs 벤더키 드리프트. (4) JSON/JSONL(meta 3종·ga4 2종·kakao·talktalk·instagram·ad_change)의 raw_not_in_dict 대량은 사전이 분석 핵심 경로만 큐레이션한 결과로 실 드리프트 아님(best-effort leaf 비교 한계). (5) stub: row<=15 10파일 중 placeholder 6(ab_tests·budget_allocation·campaigns·channel_targets·creatives·marketing_monthly_targets), 나머지 4(household_structure·naver_interest_alert·kakao_bizmessage·naver_talktalk)는 사전 등재된 정상 소수행/중첩파일. household_structure는 過去 10행 stale .bak 잔존.

**① 사전 미등재 raw 9 파일 (demo placeholder 계열 — 분석 21파일과 다른 family)**: `ab_tests`·`budget_allocation`·`campaigns`·`channel_targets`·`creatives`·`daily_performance`·`keyword_performance`·`marketing_monthly_targets`·`reviews`

**② 실 이름-드리프트 (사전 ≠ raw — ★수정 필요)**:
| 파일 | 사전 | 실제 raw |
|---|---|---|
| customers | `membership_grade`·`membership_point` | `member_grade`·`available_point` |
| household_structure | `estimated_member_count`·`avg_purchase_per_member_krw` | `member_count`·`avg_revenue_per_member_krw` |
| orders | `customer_age_group`·`customer_gender`·`region`·`guest_email_hash` (raw에 없음) | `created_at`·`updated_at`·`used_point`·`referrer` (사전에 없음) |
| naver_searchad | 친화 별칭 `camp_id`·`kwd`·`stat_dt` | 벤더 native `nccCampaignId`·`nccKeywordId`·`statDt` |

> ③ JSON/JSONL 의 raw_not_in_dict 대량은 *사전이 핵심 경로만 큐레이션*한 결과로 실 드리프트 아님(leaf 비교 한계).

**stub/소수행 분류**:
| 파일 | 행 | 판정 |
|---|--:|---|
| `marketing_monthly_targets.csv` | 1 | 사전 미등재 — blooming demo placeholder 계열(분석 21파일 family 아님). 단일 월간 목표치 1행. |
| `channel_targets.csv` | 4 | 사전 미등재 — placeholder 계열. 채널x기간 목표(period/channel/target_cpa/target_roas) 4행. |
| `ab_tests.csv` | 5 | 사전 미등재 — placeholder 계열. A/B 테스트 정의 5행. |
| `budget_allocation.csv` | 5 | 사전 미등재 — placeholder 계열. 세그먼트별 예산배분 5행. |
| `campaigns.csv` | 12 | 사전 미등재 — placeholder 계열. 캠페인 마스터 12행. |
| `creatives.csv` | 12 | 사전 미등재 — placeholder 계열. 크리에이티브 12행. |
| `household_structure.csv` | 12 | 사전 등재(19번)·정상 — 가구유형 12행은 설계상 소수(집계 마스터). 同 디렉토리에 household_structure.csv.stale-10row-v1.bak 존재(인벤토리 제외됨, 과거 10행 버전). |
| `naver_interest_alert.csv` | 4 | 사전 등재(13번)·정상 — 채널 월별 집계라 소수 행 설계. placeholder 아님. |
| `kakao_bizmessage.json` | 2 | 사전 등재(16번)·정상 — row_count=2는 campaigns[] 객체 수(중첩 풍부). placeholder 아님. |
| `naver_talktalk.json` | 2 | 사전 등재(17번)·정상 — row_count=2는 campaigns[] 객체 수(message_blocks·results_sample 중첩). placeholder 아님. |

## §6 GA4 중첩·이종 이벤트 노트

- `ga4_page_events`(84,143행·9 이벤트종)·`ga4_traffic_source`(38,319행·3 이벤트종) = **이종 이벤트 + 깊은 중첩**. 컬럼 112개는 *모든 이벤트종의 key-path 합집합* (전수 스트리밍으로 수집 — 첫 줄 표본 아님).
- 이벤트종마다 채워지는 필드가 다름 → ERD 의 GA4 '컬럼'은 *가능한 전체 경로*이지 한 행이 다 갖는 게 아님.
- `event_params[].key`/`value.*` = GA4 표준 key-value 배열(EAV) 구조. 평탄 컬럼 아님 — 분석 시 pivot 필요.

## §7 재생성 방법

raw 가 바뀌면 (`data/clumi/raw/`):
```
python docs/_claude/data/erd/extract_raw_schema.py   # 실파일 → _raw_schema_inventory.json
python docs/_claude/data/erd/gen_dbml_draft.py        # → raw_clumi_erd_v2_draft.dbml
# (선택) 워크플로 raw-erd-rebuild 재실행 → _wf_*.json 갱신
python docs/_claude/data/erd/assemble_erd.py          # → agent_specs/erd_clumi_raw_v1.0.{md,dbml}
```

> 옛 stale ERD 의 원인 = 데이터사전(파생)에서 생성. 본 파이프라인은 **실파일이 ground truth** 라 같은 종류의 drift 가 안 생긴다(사전은 §5 로 *대조*만).

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-06-13 | v1.0 — 실파일 직독 재생성(옛 `docs/_claude/data/erd/` 2026-05-23 판 대체). 34 테이블·확정 Ref 17·추정 7. drift(추가 9·변경 5)·사전 정합(이름드리프트 3·미등재 9)·stub 분류 박제. |