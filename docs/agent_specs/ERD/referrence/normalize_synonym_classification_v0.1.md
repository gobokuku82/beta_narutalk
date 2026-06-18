# 채널 간 동의어 통합 분류 — normalize_synonym_classification

> **v0.1 — 명명 전 분류 초안, 실파일 raw 근거**
>
> clumi 단일 client raw 채널 간 **동의어 컬럼**을 통합 후보 cluster 로 종합한다.
> 이 문서는 **명명(canonical name) 결정 *전* 단계**다. 통합명은 정하지 않고, 각 cluster 가 던지는 `naming_question` 만 §4 에 취합한다 — 오너가 다음 턴에 결정.
>
> - **컬럼명 ground truth** = `docs/_claude/data/erd/_raw_schema_inventory.json` (파일 basename = 테이블명, path = 컬럼 경로). 데이터사전(`clumi_data_dictionary.csv` / 폐기 `clumi_mock_NN`)의 단순화·폐기 표기가 아니라 인벤토리 경로를 채택.
> - 4 도메인 워크플로 결과 종합: `_wf_syn_adperf.json`(광고성과) · `_wf_syn_msg.json`(메시징) · `_wf_syn_ident.json`(식별차원) · `_wf_syn_timeunit.json`(시간단위).
> - 검증: 인벤토리에서 `action_values[]`·`purchase_roas[]` 중첩 배열, NaverSA `salesAmt`·`convAmt`·`ccnt`·`crto`·`nccCampaignId`·`statDt` 실재 확인 / `convCnt` **부재** 확인(사전↔raw drift).

---

## ① 목적 · 범위

| 항목 | 내용 |
|---|---|
| **목적** | 채널마다 다른 이름·타입·포맷·grain 으로 흩어진 **같은 의미의 컬럼**을 동의어 cluster 로 묶어, 후속 normalize/통합 모델의 입력으로 삼는다. |
| **이번 단계** | 분류 + 충돌 식별 + 명명 질문 취합. **통합명 확정은 다음 턴(오너 결정)**. |
| **다음 단계** | §4 naming_question 에 오너가 답 → canonical 명/단위/grain 규칙 확정 → normalizer 설계. |
| **범위 IN** | clumi raw 채널: Meta 3소스(ads_performance/by_age/instagram_inapp) · NaverSA(searchad) · ADVoost(advoost) · Kakao(bizmessage) · Talktalk · interest_alert · instagram_engagement · CRM(crm_messages/crm_send_logs) · 내부 마스터(customers/orders/campaigns/creatives/daily·keyword_performance 등) · GA4(traffic_source/page_events) · signup_events · 등급/RFM/지역. |
| **범위 OUT** | 목표/계획값 ROAS(target_roas/breakeven_roas) = 관측치 아님 → 별도 목표값 도메인. 단일출처 컬럼(동의어 군집 미형성). 개별 이벤트 grain(results_sample[]·event 타임스탬프 raw) — 집계와 분리. |
| **근거 원칙** | 모든 cluster 멤버 = 인벤토리 실재 컬럼. 사전에만 있고 raw 부재인 컬럼(convCnt 등)은 멤버에서 빼고 §5 에 drift 로 기록. |

**도메인 간 경계 주의 (cross-domain 의미함정 — §3 와 중복 박제):**
- 광고 ROAS(배수/%) vs 메시징 **ROI**(roi_percent) → **절대 합치지 말 것**.
- 광고 clicks/CTR(노출 대비) vs 메시징 click(발송/오픈 대비) → 분모 다름, 별 cluster.
- 메시징 conversions vs 광고 conversions → source/attribution 모델 다름, 합산 금지.

---

## ② 도메인별 cluster 표

> 표기: `★` = 의미함정/치명 충돌 포함 cluster. (table.column) 은 인벤토리 경로.

### 2-A. 광고 성과 (ad performance) — `_wf_syn_adperf.json`

| # | concept | 채널별 (table.column) | 단위/포맷 | 충돌 요약 |
|---|---|---|---|---|
| A1 ★ | 광고비 (ad spend/cost) | meta_ads_performance/by_age/instagram_inapp `data[].spend` · naver_searchad `data[].salesAmt` · naver_advoost `cost` · kakao_bizmessage `campaigns[].summary.total_cost_krw` · naver_talktalk 동일 | KRW (Meta=str, naver/kakao/talktalk=int) | **salesAmt=매출 아닌 광고비** / 타입 str↔int / Meta account_currency 의존 / grain 일별 vs 캠페인누계 / interest_alert 비용 부재 |
| A2 | 노출수 (impressions) | meta 3소스 `data[].impressions` · naver_searchad `data[].impCnt` · naver_advoost `impressions` | count (Meta/advoost=str, naver=int) | impCnt 명칭 / 타입 / 메시지 send_count 와 동의어 아님 / IG views 혼동 주의 |
| A3 | 클릭수 (clicks) | meta 3소스 `data[].clicks` · naver_searchad `data[].clkCnt` · naver_advoost `clicks` | count (str/int) | Meta clicks(전체)≠inline_link_clicks / clkCnt 명칭 / 메시지 click 별 cluster |
| A4 ★ | 전환수 (conversions) | meta 3소스 `data[].actions[](type=purchase).value` · naver_searchad `data[].ccnt` · naver_advoost `click_through_conversions`·`view_through_conversions`·`total_conversions` · kakao/talktalk `campaigns[].summary.conversion_count` · interest_alert `conversion_count` | count (Meta=중첩배열, naver ccnt=int?, 나머지 str/int) | **Meta actions[] 배열 필터(평탄키 가정 시 silent-0)** / **ccnt 건수 vs CVR% 미확정** / VT 포함 여부 / advoost total=VT+CT 이중계상 / attribution 정의 차 |
| A5 ★ | 전환매출 (conversion revenue) | meta 3소스 `data[].action_values[](type=purchase).value` · naver_searchad `data[].convAmt` · naver_advoost `conversion_value` · kakao/talktalk `campaigns[].summary.conversion_amount_krw` · interest_alert `conversion_amount` | KRW (Meta=중첩배열str, naver/kakao/talktalk=int) | **convAmt=매출 / salesAmt=비용 짝(최대 오염원)** / Meta action_values 배열 / 명칭 4종(_krw/없음/convAmt/value) / interest _krw 누락 |
| A6 ★ | ROAS | meta 3소스 `data[].purchase_roas[](type=purchase/omni).value` · naver_searchad `data[].ror` · naver_advoost `roas` | Meta=배수(1.04) / naver ror·advoost roas=%(512/928) | **단위 100배 차(배수 vs %)** / Meta 중첩배열 / **roi_percent(ROI)와 혼동 금지** / 동명 roas(advoost%)↔Meta 배수 |
| A7 | CTR | meta 3소스 `data[].ctr` · naver_searchad `data[].ctr` · naver_advoost `ctr` | % (Meta/advoost=str, naver=float) | Meta ctr(all)≠inline_link_click_ctr / naver·advoost 정의 불명 / 메시지 click_rate 별 cluster |
| A8 | CPC | meta 3소스 `data[].cpc` · naver_searchad `data[].cpc` · naver_advoost `cpc` | KRW (str/int) | Meta cpc(all)≠cost_per_inline_link_click / 통화 / 메시지 cost_per_message_krw 아님 |
| A9 | CPM | meta 3소스 `data[].cpm` · naver_advoost `cpm` | KRW/1000 (전부 str) | Meta+advoost 2채널뿐(빈약) / naver SA 부재(검색=CPC) / 통화 |
| A10 ★ | CVR | naver_searchad `data[].crto` · naver_advoost `ctcvr`·`vtcvr` | % | **ccnt(사전 CVR) vs crto(인벤토리 율) 미확정** / Meta 직접 컬럼 없음(파생) / advoost VT/CT 분해 / 메시지 CVR 분모 다름 |
| A11 ★ | 도달 (reach) | meta 3소스 `data[].reach` · instagram_engagement `data[].insights.data[name=reach].value` | count unique (Meta=str, IG=중첩int) | **유료 reach vs 유기 reach 합산 시 의미왜곡** / 구조 flat vs 중첩 insights / naver·메시지 부재 |
| A12 | 빈도 (frequency) | meta 3소스 `data[].frequency` | ratio(imp/reach) | **단일채널(Meta만) — 채널 간 동의어 미달, 경계선** / customer_rfm.frequency(구매빈도) 동음이의 |

### 2-B. 메시징 / CRM (messaging) — `_wf_syn_msg.json`

| # | concept | 채널별 (table.column) | 단위/포맷 | 충돌 요약 |
|---|---|---|---|---|
| M1 | 발송 대상 수 (audience) | kakao `summary.target_recipients` · talktalk `summary.target_friends` · crm_send_logs `target_count` | 건/명 (int) | recipients/friends/count 비대칭 / 톡톡=opt-in 친구 모집단 / interest_alert 부재 / crm=variant grain |
| M2 ★ | 송달 성공 수 (delivered) | kakao `summary.success_count` · talktalk `summary.delivered_count` · crm_send_logs `delivered_count` | 건 (int) | **success(요청수락) vs delivered(단말도달) 동일단계인지 dict 미명시** / kakao엔 delivered 없음, 반대로 success 없음 |
| M3 | 총 발송 시도 (sent/attempted) | interest_alert `message_send_count` · kakao `summary.target_recipients`(≈시도) · crm_send_logs `target_count` | 건 (interest=str) | M1·M2 와 겹침 / interest send_count=시도/성공 불명 / 월별 grain |
| M4 | 오픈 수 (opens) | kakao/talktalk/crm `*.open_count` · interest_alert `message_open_count` | 건 (interest=str) | message_ 접두만 차이 / grain / 측정정의 dict 미명시 |
| M5 ★ | 오픈율 (open rate) | kakao/talktalk `summary.open_rate` · crm_send_logs `open_rate` · interest_alert `message_open_rate` | % (float/decimal/str) | **분모(대상/송달/시도) 채널별 미명시 — 통합 시 벤치마크 왜곡** / 타입 혼재 |
| M6 | 클릭 수 (clicks) | kakao/talktalk/crm `*.click_count` · interest_alert `message_click_count` | 건 (interest=str) | message_ 접두 / 광고 clicks 와 동음이의(별 cluster) / 타입 |
| M7 ★ | 클릭율 (click rate, CTR-vs-sent) | kakao/talktalk `summary.click_rate` · crm_send_logs `click_rate` · interest_alert `message_click_rate` | % (float/decimal/str) | **click_rate(발송·송달 대비) vs CTOR(오픈 대비) 분리 필수** / 분모 미명시 |
| M8 ★ | 오픈대비 클릭율 (CTOR) | kakao/talktalk/crm `summary.click_through_rate_open` | % | **dict 미등재(인벤토리에만)** / click_rate 와 분모 다름 — 통합 시 합쳐질 위험 / interest 부재 |
| M9 ★ | 전환 수 (conversions) | kakao/talktalk/crm `summary.conversion_count` · interest_alert `conversion_count` | 건 (interest=str) | **attribution 모델 채널별 불명** / 광고 전환과 합산 금지 / interest=클릭기반 시사 |
| M10 ★ | 전환 매출 (conversion revenue) | kakao/talktalk `summary.conversion_amount_krw` · crm_send_logs `conversion_amount_krw`(bigint) · interest_alert `conversion_amount` | KRW (int/bigint/str) | **interest _krw 누락 → 단위 misread 위험** / 타입 혼재 / attribution 상속 |
| M11 ★ | ROI (%) | kakao/talktalk `summary.roi_percent` · crm_send_logs `roi_percent`(decimal) | % (2960/9731/2861.54) | **ROI≠ROAS 절대 합치지 말 것** / 산식(net/gross) 미명시(스케일 차 의심) / interest 부재 / crm 비용컬럼 외부 |
| M12 ★ | 평균 주문금액 (AOV) | kakao/talktalk `summary.avg_order_value` · crm_send_logs `avg_order_value` · interest_alert `avg_order_value` | KRW (interest=str) | **avg_order_value 가 promotion/rfm/category 도메인에도 다수 존재 → join/혼동 금지** / _krw 미명시 |

### 2-C. 식별 · 차원 (identity & dimension) — `_wf_syn_ident.json`

| # | concept | 채널별 (table.column) | 단위/포맷 | 충돌 요약 |
|---|---|---|---|---|
| I1 ★ | 캠페인 ID | meta 3소스 `data[].campaign_id` · naver_searchad `data[].nccCampaignId` · naver_advoost `campaign_id` · kakao/talktalk `campaigns[].campaign_id` · crm `crm_campaigns.campaign_id`(int) · campaigns/creatives/daily_performance `campaign_id` · ad_change_history `data[].object_id`(조건부) | string(Meta 17자리/cmp-/GFA/CMP_KKO/NTT) · CRM int | **ID 공간 전부 다름 → cross-channel join 불가** / 타입 int↔str / object_id=object_type 분기 / 내부 campaign_id 가 Meta 공간인지 미단정 |
| I2 | 캠페인명 | meta `data[].campaign_name` · advoost `campaign_name` · kakao/talktalk `campaigns[].campaign_name` · crm `crm_campaigns.campaign_name` · campaigns `name` · creatives `name`(소재명 의심) · ad_change_history `data[].object_name` | string | 언어 혼재(영문코드 vs 한글) / campaigns.name 컬럼명 / **creatives.name=소재명 가능(편입 위험)** / naver SA 캠페인명 미관측 |
| I3 | 소재(크리에이티브) ID | creatives `creative_id` · daily_performance `creative_id` | string | 내부 2테이블만 / IG media id·crm variant_id 별 공간 |
| I4 ★ | 회원 ID (member_id) | customers/orders/customer_rfm/customer_grade_history/signup_events `member_id` · promotions `promotion_usage_history.member_id` · ga4_traffic_source/ga4_page_events `user_id` | string | **GA4=user_id 명칭 차** / NULL 의미(비회원/비로그인) join 누락 / kakao cid 부분포함(동치 아님) |
| I5 ★ | GA4 익명 client ID | ga4_traffic_source/ga4_page_events `user_pseudo_id` · signup_events `ga_client_id` | string({n}.{n}) | **member_id(회원)와 절대 동일 cluster 금지** / 명칭 차(pseudo_id↔ga_client_id) / 회원당 N:1 |
| I6 | GA4 세션 ID | ga4 `event_params[key=ga_session_id].value.int_value` · signup_events `ga_session_id` | int (signup=str) | 구조 중첩 vs 평면 / 타입 int↔str |
| I7 ★ | 채널 / attribution | orders `channel_attribution` · daily/creatives/keyword_performance/channel_targets `channel` · interest_alert `channel` · crm `crm_campaigns.channels`(다중값) · ga4 `...default_channel_group` | string (분류체계 상이) | **orders 세분 enum vs GA4 표준그룹 vs 단일값 → 직접 동치 불가, 매핑사전 필요** / crm channels 콤마 다중값 / 표기 차 |
| I8 | UTM source | orders `utm_source` · customers `signup_utm_source` · signup_events `utm_source` · ga4 `traffic_source.source`·`...last_click...source`·`collected...manual_source` | string | **값 입도(meta 통합 vs facebook/instagram 분리)** / GA4 시점 3종 동일명 / signup_ 접두 |
| I9 | UTM medium | orders `utm_medium` · customers `signup_utm_medium` · signup_events `utm_medium` · ga4 medium 3변형 | string | **source/medium 경계 혼탁(orders.utm_medium 에 facebook 값)** / GA4 시점 변형 / 명칭 차 |
| I10 | UTM campaign | orders `utm_campaign` · customers `signup_utm_campaign` · signup_events `utm_campaign` · ga4 `...campaign_name`·`manual_campaign_name` 다수 | string | utm_campaign↔campaign_name↔campaign_id 느슨 매핑 / GA4 정본 모호(campaign_id 거의 null) |
| I11 ★ | 회원 등급 (grade/tier) | customers `member_grade` · customer_grade_history `grade`·`previous_grade` · customer_rfm `customer_tier` | string | **운영 등급(WELCOME/BASIC/SILVER/GOLD/VIP) vs RFM tier(Platinum/Gold/Silver/Bronze/Inactive) 다른 축 — 묶으면 오염** / customers BASIC vs history REGULAR 값셋 불일치 |
| I12 | 연령대 (age group) | customers `age_group` · meta_ads_by_age `data[].age` | string(18-24…65+) | 버킷 경계 일치하나 의미 다름(개인속성 vs 광고노출 차원) / orders.customer_age_group 미관측 |
| I13 | 지역 (region) | customers `region` · household_structure `top_region` · signup_events `geo_region` · ga4 `geo.region` | 한글 광역 vs 영문(Gyeonggi-do) | **언어 충돌 한↔영 매핑 필수** / 입도(GA4 계층 vs 광역단일) / 거주지 vs 접속지 |
| I14 | 디바이스 (device) | orders `device_type` · customers `signup_device` · signup_events `signup_device` · ga4 `device.category` · naver_searchad `data[].device` | 내부(mobile_web/app/pc) vs GA4(mobile/desktop/tablet) vs naver(M/P) | **값 도메인 3종 충돌** / 입도(web/app 구분 vs 미구분, tablet) / 명칭 차 |

### 2-D. 시간 · 단위 · 포맷 (time/unit/format) — `_wf_syn_timeunit.json`

> ※ T3~T8 은 §2-A 의 광고 지표(A1·A4·A5·A6·A2·A3·I1)와 같은 concept 을 **시간/단위/포맷 관점**으로 재교차한 것. 멤버에 daily_performance/keyword_performance/CRM/GA4 등 시간·집계 출처가 추가됨. 통합 시 §2-A 와 합산 정렬 필요.

| # | concept | 채널별 (table.column) | 단위/포맷 | 충돌 요약 |
|---|---|---|---|---|
| T1 ★ | 리포트/집계 일자 (day) | meta 3소스 `data[].date_start` · naver_searchad `data[].statDt` · naver_advoost `report_date` · ga4 2소스 `event_date` · daily_performance `date` | YYYY-MM-DD vs **YYYYMMDD**(statDt/GA4) | **포맷 충돌(구분자 유무) 파싱분기** / **GA4 event_date=UTC vs 나머지 KST 가정 → ±1일 silent misalign** / 명칭 차(date_start/statDt/report_date) |
| T2 ★ | 이벤트 타임스탬프 (instant) | ga4 2소스 `event_timestamp` · ad_change_history `data[].event_time_unix`·`event_time`·`date_time_in_timezone` · instagram_engagement `data[].timestamp` | **마이크로초 epoch(16자리) vs 초 epoch(10자리) vs ISO8601 vs KST 슬래시** | **단위 us↔sec(×1e6 보정 누락 시 5만년 오차)** / 같은 instant 3중 인코딩(ad_change_history 내부) / TZ 혼재 / user_first_touch_timestamp 다른 사건 |
| T3 ★ | 광고비 (ad cost) | = A1 + kakao/talktalk `total_cost_krw` | KRW (str vs int) | §A1 와 동일(salesAmt=비용 함정·타입·통화·grain) |
| T4 ★ | 전환/구매 매출 | = A5 + crm_send_logs `conversion_amount_krw` + ga4 `ecommerce.purchase_revenue`(KRW)·`purchase_revenue_in_usd`(USD)·page_events purchase_revenue(전부 null) | KRW + **USD 병기** | **_in_usd 누락 인식 시 통화혼합(~1300배)** / **page_events purchase_revenue 실측 전부 null(존재≠사용가능)** / §A5 함정 상속 |
| T5 ★ | ROAS / ROI | = A6 + kakao/talktalk/crm `roi_percent` + promotions `promotion_performance.roi_percent` | 배수 vs % + **ROI 별개** | §A6(배수↔% 100배) + **roi_percent=ROI≠ROAS** 같은 비율표기 도메인에 모았으되 분리 명시 |
| T6 | 노출수 | = A2 + daily_performance·keyword_performance `impressions` | count (str/int) | §A2(impCnt 명칭·타입) + 집계테이블 추가 |
| T7 | 클릭수 | = A3 + daily_performance·keyword_performance `clicks` | count (str/int) | §A3(clkCnt·Meta 정의차) + 집계테이블 추가 |
| T8 ★ | 전환수 | = A4 + crm_send_logs `conversion_count` + daily/keyword_performance `conversions` | count | §A4 + **naver convCnt 사전엔 있으나 raw 부재(drift), ccnt=CVR% 가능성** / VT 포함 / Meta 배열 |
| T9 ★ | 캠페인 ID (시간/타입 관점) | = I1 + ad_change_history `data[].object_id` | string vs CRM int | §I1(ID 공간 분리·join 불가) + CRM int 타입 충돌 |
| T10 ★ | 발송/스케줄 일시 | kakao/talktalk `campaigns[].send_request_date` · talktalk `send_completion_date` · crm `crm_campaigns.scheduled_at`·`sent_at` · crm_send_logs `sent_at` | ISO 문자열 vs SQL datetime | **단계 의미차(requested/scheduled/sent/completed)** / 포맷 차 / **TZ 암묵 KST(라벨 없음)** |
| T11 ★ | 해시/PII 식별자 | customers `member_name_hash`·`member_phone_hash` · signup_events `ip_hash` · kakao `...phone_number_hash` · talktalk `...friend_id_hash` | SHA256 hex | **해시공간·솔트·원본종류(name/phone/email/ip/friend_id) 달라 join 불가** / orders.guest_email_hash 사전에만(raw 미관측) |

---

## ③ ★ 충돌 레지스터 (통합 시 *반드시* 처리)

> 분류만으로는 안전하지 않은 항목. normalize 전 처리 규칙이 없으면 **영구 오염/silent 오류** 보장. 유형별 정리.

### C-1. 단위 충돌 — 배수 vs % (스케일 100배)
| ID | 위치 | 충돌 | 미처리 시 |
|---|---|---|---|
| C1.1 | A6/T5 ROAS | Meta `purchase_roas`=배수(1.04) vs naver `ror`·advoost `roas`=%(512/928) | 평균/비교 무의미. advoost `roas`(%)가 Meta `roas`(배수)와 동명 → 100배 오류 보장. **canonical 배수 통일 권장 + ror/advoost ÷100** |
| C1.2 | A6 vs M11/T5 | ROAS vs ROI(roi_percent) | 분자 다름(매출 vs 이익). 같은 비율표기라도 **별 canonical** |

### C-2. 단위 충돌 — 통화 (KRW vs USD)
| ID | 위치 | 충돌 | 미처리 시 |
|---|---|---|---|
| C2.1 | T4 GA4 | `purchase_revenue`(KRW) ↔ `purchase_revenue_in_usd`(USD) 나란히 | _in_usd 누락 인식 시 ~1300배 혼합. 모든 `*_in_usd` 동형 |
| C2.2 | A1/A5 Meta | `account_currency` 별도 필드 — KRW 단정 불가(실 API USD 가능) | KRW 강제 가정 시 비KRW 계정 오염 |
| C2.3 | A5/M10/T4 | `conversion_amount_krw`(접미 명시) vs `conversion_amount`·`convAmt`·`purchase_revenue`(접미 없음) | 컬럼명만으로 통화 판단 불가 |

### C-3. 단위/타입 충돌 — us vs sec, str vs int
| ID | 위치 | 충돌 | 미처리 시 |
|---|---|---|---|
| C3.1 | T2 | GA4 `event_timestamp`=마이크로초(16자리) vs ad_change_history `event_time_unix`=초(10자리) | ×1e6 보정 누락 시 약 5만년 오차 |
| C3.2 | 전 도메인 수치 | Meta/advoost/interest/GA4 일부 = **string** vs naver/kakao/talktalk/crm = native int/float | numeric 캐스팅 일관화 없으면 합산/정렬 오류 |

### C-4. 날짜/시간 포맷 충돌
| ID | 위치 | 충돌 | 미처리 시 |
|---|---|---|---|
| C4.1 | T1 | naver `statDt`·GA4 `event_date`=YYYYMMDD vs Meta/advoost/daily=YYYY-MM-DD | 파싱 분기 필수 |
| C4.2 | T1 | GA4 event_date=UTC(명시) vs 나머지 KST 영업일 가정 | UTC 자정 경계 ±1일 silent misalignment |
| C4.3 | T2/T10 | 같은 instant 가 epoch/ISO8601/`YYYY/MM/DD HH:MM:SS KST` 3형태(ad_change_history 내부) + send 일시 ISO vs SQL datetime, TZ 암묵 | 시각 정렬 오류 |

### C-5. ID 공간 충돌 — 동의어이나 join 불가
| ID | 위치 | 충돌 | 미처리 시 |
|---|---|---|---|
| C5.1 | I1/T9 campaign_id | Meta 17자리 / naver `cmp-` / advoost `GFA` / kakao `CMP_KKO` / talktalk `NTT` / CRM int — 발급체계 전부 다름 | cross-channel **직접 join 시 전부 미스매치**. 연결은 campaign_name/utm_campaign 매핑테이블로만 |
| C5.2 | I4/I5 | member_id(회원 평문키) vs user_pseudo_id(익명 쿠키) | 동일 cluster 로 묶으면 회원↔익명 혼동(N:1) |
| C5.3 | T11 PII 해시 | name/phone/email/ip/friend_id 해시 — 공간·솔트 다름 | 'hash' 한 키로 묶으면 join 불가인데 가능하다고 오인 |

### C-6. 의미함정 — 이름이 의미와 반대/혼동
| ID | 위치 | 함정 | 미처리 시 |
|---|---|---|---|
| **C6.1 (최우선)** | A1/A5/T3/T4 | **naver_searchad `salesAmt`=매출 아닌 광고비(비용)** / `convAmt`=매출 — 헷갈림 쌍 | 비용↔매출 뒤섞임 → ROAS 뒤집힘. 영구 오염원 1순위 |
| C6.2 | A4/A5/A6 Meta | `actions[]`·`action_values[]`·`purchase_roas[]` = `[{action_type,value}]` 중첩 배열 (flat 가정 X) | action_type=purchase 필터 없이 추출 시 silent-0 누락 |
| C6.3 | A6 vs M11 | `roi_percent`=ROI(이익) ≠ ROAS(매출) | ROAS 통합명에 합치면 지표 의미 붕괴 |
| C6.4 | A11 | Meta reach(유료) vs instagram_engagement reach(유기) | 합산 시 광고비 대비 도달 분석에 유기 도달 섞임 |
| C6.5 | M2 | kakao `success_count`(요청수락) vs talktalk/crm `delivered_count`(단말도달) — 동일단계 dict 미확정 | 통합이 의미 동일성을 가짜로 주장 |
| C6.6 | M5/M7/M8 | open_rate/click_rate 분모(대상/송달/시도/오픈) 채널별 미명시 / click_rate vs CTOR | 분모 다른 율 평균 → 벤치마크 왜곡 |
| C6.7 | I11 | 운영 grade vs RFM customer_tier 다른 분류축 / BASIC vs REGULAR 값셋 | 등급 묶으면 오염 |
| C6.8 | T4 | ga4_page_events `purchase_revenue` 구조상 존재하나 실측 전부 **null** | catalog≠code drift 동형 — 존재≠사용가능 |
| C6.9 | I2 | creatives `name` = 캠페인명 아닌 소재명 가능 | 캠페인명 cluster 편입 시 오염 |

### C-7. grain 충돌 (합산 전 정렬 필요)
| ID | 위치 | 충돌 |
|---|---|---|
| C7.1 | A1/A4 등 | Meta/naver/advoost=일×캠페인(×세그) vs kakao/talktalk summary=캠페인 누계 → 단순 합산 전 grain 정렬 |
| C7.2 | M*/interest | interest_alert=월별 채널 집계(캠페인 분해 없음) vs kakao/talktalk=캠페인, crm=variant |
| C7.3 | I12 | age_group: customers=개인속성 행 vs meta_ads_by_age=노출 집계 차원 |

---

## ④ 명명 결정 대기 목록 (오너 다음 턴 결정)

> 각 cluster `naming_question` 취합. **이름·단위·grain·매핑정책**을 함께 결정해야 함(이름만으로 충돌 안 풀림).

### 광고 성과
- **A1 광고비**: spend vs cost vs ad_cost(KRW)? `salesAmt`를 이 cluster 에 넣을 때 '비용=매출 이름' 함정을 매핑에 명시(미명시 시 영구 오염). 통화 정규화·grain 규칙을 통합명에 함께 선언.
- **A2 노출**: impressions 통합, impCnt 만 alias. 메시지 send_count 를 '노출'로 끌어올지(권장: 별 cluster).
- **A3 클릭**: clicks 통합하되 all clicks vs link clicks 정의 명시. Meta 둘 다 존재 → canonical 결정.
- **A4 전환수**: (a)전환 정의(purchase only vs 전체 액션) (b)VT 포함 여부 (c)Meta actions[] 평탄화 규칙 (d)naver ccnt 건수/율 확정 — **4개 모두 선결**.
- **A5 전환매출**: conversion_revenue(KRW)? convAmt 는 매출, salesAmt 는 비용으로 정확 분리(최대 오염원). interest conversion_amount KRW 여부 확인.
- **A6 ROAS**: 배수 vs % 먼저 결정. advoost roas(%)를 두면 Meta roas(배수)와 동명 100배 오류 → 정규화 방향(권장: 배수 통일)·ror/advoost ÷100 규칙 명시.
- **A7 CTR**: ctr 통합, Meta ctr vs inline_link_click_ctr canonical, naver/advoost 정의 정합. 메시지 click_rate 끌지 말 것.
- **A8 CPC**: cpc(KRW), Meta cpc vs cost_per_inline_link_click canonical + 통화.
- **A9 CPM**: cpm(KRW). 커버 Meta+advoost 둘뿐 → naver SA 부재를 결손/파생 중 무엇으로.
- **A10 CVR**: 통합 가능성 자체 불확실 — naver SA CVR 컬럼 정체(ccnt vs crto) 확정 선결. 분모(노출 대비 vs 클릭 대비) 통일.
- **A11 reach**: paid_reach/organic_reach 분리할지가 핵심. 단순 통합 시 유기 도달 오염.
- **A12 frequency**: Meta 외 동의어 없어 단일출처에 가까움 → cluster 유지 실익 적음. customer_rfm.frequency(구매빈도) 동음이의 분리 표기.

### 메시징 / CRM
- **M1 발송대상**: target_count vs recipients? 톡톡 opt-in 친구 vs 알림톡 비친구 — 단일명이 두 모집단 가림.
- **M2 송달성공**: delivered_count vs success_count? 같은 단계(요청수락 vs 단말도달) 정의서 없이 단정 불가 → 통일이 동일성 가짜 주장 위험.
- **M3 시도수**: interest message_send_count 를 '발송대상'에 매핑할지 '송달'에 매핑할지 — requested/delivered 미명시로 귀속 불가.
- **M4 오픈수**: open_count, interest message_ 접두가 다른 알림유형 구분 의도인지(제거 시 의미 누락) 확인.
- **M5 오픈율**: open_rate, 분모(대상/송달/시도) 채널별 확정이 핵심 — 미통일 시 왜곡.
- **M6 클릭수**: click_count, interest message_ 접두 처리는 M4 와 동일.
- **M7 클릭율**: click_rate(=CTR), CTOR 과 구분되는 이름(예 ctr_vs_sent) 필요. 분모 통일.
- **M8 CTOR**: ctor(=click/open), click_rate 와 혼동 → 분모 표기(_open) 보존.
- **M9 전환수**: conversion_count, 메시징 내부 attribution 동일 여부 불명 — 합산 시 동일정의 보장 안 됨.
- **M10 전환매출**: conversion_amount_krw, interest 는 _krw 없으나 동일 KRW → _krw 부착이 안전(원본명 그대로면 misread).
- **M11 ROI**: roi_percent, ROAS 와 절대 분리. ROI 산식(net/gross) 통일 확인 없이 평균/비교 불가. 메시지=ROI만/광고=ROAS만 비대칭을 분석 레이어에서 어떻게 비교가능하게 만들지가 상위 질문.
- **M12 AOV**: avg_order_value 도메인 전반 과다 재사용 → 메시징 한정 namespace(예 msg_avg_order_value)+KRW 명시.

### 식별 · 차원
- **I1 campaign_id**: 통합명 가능하나 '채널 간 join 키로 쓰지 말 것' 강하게 박제. 진짜 교차 키는 campaign_name 규칙/utm_campaign 기반 별도 매핑테이블. 채널 prefix(meta:/naver_sa:/advoost:) vs 내부 마스터 정규화 결정.
- **I2 campaign_name**: 영문코드↔한글 정규화 정책. campaigns.name 리네임 시 creatives.name(소재명) 혼동 방지 위해 테이블 맥락 유지.
- **I3 creative_id**: 내부 2테이블만 공유. IG media id·crm variant_id 를 소재 차원으로 통합할지 별개 유지할지.
- **I4 member_id**: canonical member_id 통합 시 GA4 user_id alias 하되 user_pseudo_id(쿠키)와 혼동 금지. 비회원/비로그인 NULL 규약 명시.
- **I5 anon_client_id**: 단일명, user_id(회원)와 명확 분리. 회원당 N:1.
- **I6 ga_session_id**: GA4 event_params 평탄화 + 타입 통일(int).
- **I7 channel**: 표준 그룹 레벨 vs plat 세분 레벨 중 어디로 normalize. crm channels 다중값 분해. **orders↔GA4 매핑사전이 핵심 난관**.
- **I8 utm_source**: 어트리뷰션 시점(first/last/collected) 보존 여부 + meta↔facebook/instagram 값 매핑사전. signup_ 접두 맥락 보존 권장.
- **I9 utm_medium**: source 와 경계 재정의(orders 의 facebook 값을 medium 으로 둘지). GA4 시점 변형 보존은 I8 동일.
- **I10 utm_campaign**: GA4 다중 변형 중 정본(보통 session last-click) 선택 + utm_campaign↔campaign_name↔campaign_id 매핑사전.
- **I11 grade/tier**: membership_grade(운영) vs customer_tier(RFM) 별개 — 묶으면 오염(분리 권장). 묶더라도 REGULAR vs BASIC 라벨 정합화 선결.
- **I12 age_group**: '회원 속성 연령대' vs '광고 breakdown 차원'을 같은 값 도메인으로 볼지 분리할지. 버킷 경계 호환되어 값 도메인 공유 가능.
- **I13 region**: 한글/영문 정본 결정 + 매핑사전. 거주지 vs 배송지 vs 접속지 의미 구분 보존 여부.
- **I14 device**: 공통 최소 분류(mobile/desktop/tablet) normalize vs web/app 세분 보존. 네이버 M/P 코드 디코딩 규약.

### 시간 · 단위 · 포맷
- **T1 report_date**: KST day 통합 시 GA4 UTC→KST 변환 여부, statDt 정수형 ISO normalize 시점(수집기 vs normalizer).
- **T2 event_ts**: 기준단위(us vs ms) 통일, ISO/KST 파생표시 vs 원본보존, *_unix(초) ×1e6 보정 여부.
- **T3 ad_cost_krw**: salesAmt 비용→광고비 명시 매핑(sales 오인 위험), Meta 비KRW 환산 책임위치, summary 누계 vs 일별 동일컬럼 여부.
- **T4 conversion_revenue_krw**: USD 병기 환산 vs 별도보존, Meta action_values 정규 action_type(purchase vs omni_purchase) 확정, GA4 purchase_revenue=KRW 선언 위치.
- **T5 ROAS/ROI**: ROAS canonical 배수 vs % + 채널별 ÷100/×100 보정표, ROI 를 ROAS 와 별도 canonical, Meta purchase_roas 배열 action_type 채택값.
- **T6 impressions / T7 clicks**: naver SA `*Cnt` 패턴(impCnt/clkCnt/convCnt/ccnt) 묶음 규칙 normalize vs 개별 매핑.
- **T8 conversions**: NaverSA 전환'수' 실재 컬럼 확인, VT 포함/제외 통일, Meta actions 배열 action_type 채택키.
- **T9 campaign_id**: 채널 네임스페이스 prefix 보존, cross-channel 연결은 ID 아닌 명/UTM 매핑테이블로 별도 설계.
- **T10 send datetime**: 단계(requested/scheduled/sent/completed) 분리 vs 단일 sent_at, KST 명시 선언 위치.
- **T11 PII 해시**: 통합 사실상 불가(join 안 됨). 동일인 식별은 member_id/user_pseudo_id 평문키로만. 통합명 두려면 원본종류(name/phone/email/ip) 접미 보존 필수.

---

## ⑤ 놓친 · 불확실 (missed / uncertain)

> 4 도메인 결과의 `missed_or_uncertain` 취합 + 인벤토리 교차. **실측(raw 1행)으로 풀어야 하는 미결**.

### 치명 — 분류 멤버십이 여기 달림
1. ✅ **[해소 §6] naver_searchad 전환 컬럼**: raw 직독 확정 — `ccnt`=전환수(건,int)·`crto`=CVR(%)·`cpConv`=CPA·`convCnt` 부재. 사전 2중 오류 확인. A4/A10/A8 멤버십 확정.
2. ✅ **[해소 §6] Meta action_type**: raw 직독 — `actions[]`/`action_values[]`/`purchase_roas[]` 중첩배열, purchase=`omni_purchase`(=offsite_conversion.fb_pixel_purchase). flat `roas`/`actions.purchase` 부재. 배열 필터 필수(미필터=silent-0).
3. **사전↔raw drift**: naver `convCnt`, orders `guest_email_hash`, orders `region/customer_age_group/customer_gender` 등 — 데이터사전엔 있으나 인벤토리 미관측. 사전 명칭 채택 금지, 인벤토리 우선.

### 통화/단위 미확인
4. **Meta account_currency 값분포**: mock 은 KRW 로 보이나 실 API USD/현지통화 가능 — spend/cpc/cpm/conversion-value KRW 가정은 추정.
5. **금액 컬럼의 날짜 오파싱 의심**: budget_allocation/campaigns/category_sales/household_structure 의 `*_budget`·`order_amount`·`total_revenue_krw` 가 인벤토리상 'date(yyyymmdd)'로 파싱됨(8자리 숫자를 날짜로 오인 추정) — 금액 cluster 편입 보류, raw 확인.
6. **ad_change_history event_time_unix** 초(10자리) vs ms 자릿수 미실측 — '초 추정' 표기.
7. **GA4 event_value_in_usd / double_value(USD)**: purchase_revenue(KRW)와 다른 축이라 매출 cluster 제외했으나 통화 함정 사례.

### 경계/단일출처 — cluster 편입 여부 미결
8. **메시징 율 동의어 후보(focus 외 본문 제외)**: fail_count↔failed_count(철자 불일치 2채널), success_rate↔delivered_rate, conversion_rate_click↔conversion_rate_from_click, cost_per_message_krw/revenue_per_message_krw — 추가 검토 가치.
9. **CTR/CPC/CVR 파생비율 채널 간 % vs 소수 표기차**(Meta ctr 0.91 vs advoost 0.9459) 가능 — 후속 별도 cluster 권장.
10. **frequency(A12)**: Meta 3소스 내부 동일 컬럼뿐 → '채널 간' 동의어 미달(경계선). CPM(A9) Meta+advoost 2채널뿐 → 동의어로 빈약.
11. **instagram_engagement insights**(views/saved/shares/like_count 등): 유기 인게이지먼트, 유료 12지표와 1:1 동의어 거의 없음. reach 만 Meta reach 와 동음(paid/organic 의미 달라 conflict 강경고).
12. **advoost VT/CT/total_conversions 합산관계**(total=VT+CT 추정): 사전 예시값으로만 정합, 전수 미검증 — A4 이중계상 방지 규칙 필요.
13. **daily_performance/keyword_performance/creatives 성격**: 이미 채널 통합·집계된 파생 테이블(ad_cost/conversions/roas canonical 영어명 보유)인지 raw 인지 불확실. raw 면 광고비/매출 cluster 에 ad_cost/conversion_revenue 도 동의어로 추가 필요 — '동의어를 흡수한 목적지' 성격(통합명 후보 어휘로는 참고: ad_cost, conversions, conversion_revenue).

### 식별/차원 미확인
14. **orders.csv 헤더 재확인**: 인벤토리에 region/age_group/gender 없음(사전엔 있음) → 스캔 누락 vs mock 미생성 미판별. 확인되면 연령대/지역/성별 2~3 멤버 cluster 가능.
15. **kakao results_sample[].cid**(예 M2406032384-0415_001): member_id 부분 포함하나 접미로 직접 join 불가 — I4 미편입. 앞 11자 추출 등 파싱 규칙 검증 필요.
16. **gender**: customers.gender 단일출처만 관측 → 동의어 군집 미형성, 제외(orders 헤더 확인 시 2-멤버 가능).
17. **creatives.name** 캠페인명 vs 소재명 불확실 — I2 에 잠정 포함하되 소재명 개연 큼, 실값 샘플 확인.
18. **ad_change_history object_id/object_name**: object_type(CAMPAIGN/AD_SET/AD/PLAN/REPORT) 분기 — 조건부 동의어(필터 필수), 무조건 join 시 오염.
19. **내부 campaign_id 공간**(campaigns/creatives/daily_performance)이 Meta 17자리와 동일한지 인벤토리만으로 단정 불가 — 같다 가정해 I1 에 넣되 conflicts 명시. 실값 대조 필요.
20. **channel enum 값 분포**: daily/creatives/keyword/channel_targets 의 channel 실제 값셋 인벤토리 미제공(타입만 string). orders.channel_attribution 풍부 enum 과 동일 도메인인지 값 대조 필요.
21. **GA4 traffic_source 3계열**(first-touch/last-click/collected)을 source/medium/campaign cluster 에 함께 넣었으나 어트리뷰션 시점 달라 의미상 별개일 수 — 시점 차원 보존 여부 미결.
22. **목표/계획값 ROAS**(target_roas/breakeven_roas — reviews/marketing_monthly_targets/channel_targets/budget_allocation): 비율표기 도메인이나 '관측치' 아닌 '목표값' → 실측 동의어 cluster 제외, 별도 목표값 도메인 검토.
23. **개별 vs 집계 grain**: kakao/talktalk results_sample[](delivered_status/opened_at/clicked_at 타임스탬프)는 summary.* 와 별 grain — 동의어 분류 제외. crm_send_logs=variant 단위 grain 정렬 별도.
24. **율 분모 미명시(M5/M7/M8)**: 4채널 open_rate/click_rate 분모(대상/송달/시도/오픈)가 dict 미명시 — 동의어로 묶었으나 '같은 율'인지 정의서 없이 확신 불가. **가장 큰 통합 리스크**.

---

## ⑥ 실측 해소 (raw 직독 — 2026-06-14)

> §5 치명 미결 2건을 raw 1행 직독으로 확정. 결과: **분류 추정은 옳았고, 데이터사전 오류가 추가 확인**됨(staleness 테마 강화).

**naver_searchad 전환 컬럼 (✅ 확정)** — 전환>0 행 직독:
| 컬럼 | 정체 | 증거 |
|---|---|---|
| `ccnt` | **전환수(건, int)** | clk=5·ccnt=1, clk=10·ccnt=1 (clkCnt 이하 정수) |
| `crto` | **전환율 CVR(%, float)** | =ccnt/clkCnt×100 (1/5=20.0, 1/10=10.0) |
| `cpConv` | **CPA(전환당비용)** | =salesAmt/ccnt (1678/1=1678) |
| `ror` | **ROAS(%)** | =convAmt/salesAmt×100 (62332/1678≈3714.66) → **salesAmt=비용·convAmt=매출 재확인(C6.1)** |
| `convCnt` | **부재** | 사전 기재됐으나 raw에 없음 |

→ A4(전환수=ccnt)·A10(CVR=crto)·A8(CPA=cpConv) **멤버십 확정**.

**meta_ads_performance 전환·ROAS (✅ 확정)** — [0] 직독:
- `actions[]`·`action_values[]`·`purchase_roas[]` = **중첩 배열** `[{value, action_type}]`. purchase = `action_type='omni_purchase'`(=`offsite_conversion.fb_pixel_purchase`, 동일값). 예: action_values omni_purchase=590,412원, purchase_roas omni_purchase=2.2063(배수).
- **flat `roas`·`actions.purchase` 키 부재** — 추출 = 배열에서 action_type 필터 필수(미필터 시 silent-0 = C6.2 실증).

**데이터사전 추가 오류 (raw 대조 — 누적, raw ERD §5 이름드리프트에 추가)**:
| 사전 표기 | 실제 raw |
|---|---|
| naver `ccnt` = CVR(%) | `ccnt` = 전환수(건) |
| naver `convCnt` = 전환수 | `convCnt` **부재** (CVR은 `crto`) |
| meta `roas` = 1.04 (flat) | `purchase_roas[]` 배열(omni_purchase=2.2063), flat roas 부재 |
| meta `actions.purchase` (flat) | `actions[]` 배열, action_type 필터 필요 |

→ **명명·normalize 설계는 데이터사전이 아니라 raw를 정본으로** (raw ERD가 "실파일 직독"이어야 했던 이유 재확인).

---

## ⑦ 외부 API 문서 검증 ([06](06_erd_and_verification.md) 반영 — 2026-06-14)

> §6 raw 실측을 **공식 벤더 doc으로 교차검증**(06). 우리 실측 ∩ 공식 doc = 상호 보강 → 신뢰도 "실측"→"실측+공식 doc". 출처: Naver `searchad-apidoc` GitHub(FAQ-stat·Java `Stat.java`) · Meta v25 Insights API · Meta Ads MCP. ⚠ 06은 오너 외부 리서치라 제가 재페치 안 함 — 단 우리 raw 직독과 *독립 수렴*해 높은 확신.

**✅ PASS 10 — 충돌 레지스터 격상 (공식 doc 확인)**:
| 검증 | 공식 근거 | 우리 충돌 |
|---|---|---|
| salesAmt=비용 · convAmt=매출 | Java `Integer salesAmt` · FAQ-stat | **C6.1 공식 확정** |
| ccnt=전환수(int) · crto=CVR · convCnt 부재 | Java `Integer ccnt`·`Double crto` | A4/A10·§6 공식 확정 |
| Meta ROAS 배수 vs Naver ror % | Meta 공식 · Naver `ror=전환매출/총비용` | **C1.1 100배 확정** |
| Meta `actions[]` omni_purchase 필터 | Meta v25 · Meta Ads MCP | C6.2 확정 |
| **ROI%=(ROAS−1)×100** | 공식 산식 | **C6.3 산식 추가** (ROAS 4.5× = ROI 350%) |
| impCnt/clkCnt/cpc | Java 타입 | A2/A3/A8 |
| clicks(all) ≠ inline_link_clicks | Meta v25 | A7 — **CTR canonical = `inline_link_click_ctr` 권고** |
| campaign_id 네임스페이스 분리 | Meta · Naver #976 | C5.1 |

**⚠ PARTIAL 2 — 외부 블로커 (지금 못 풂)**:
- 메시징 `open_rate`/`click_rate` **분모**(대상/송달/시도) 미확정 → Kakao 공식 doc(대행사 계약) 필요. **그 전까지 채널 간 율 비교·통합 금지** (M5/M7/M8).
- `success_count`(요청수락) vs `delivered_count`(단말도달) 단계 정의 미확정 (M2).

→ 명명 입력 = [06 §5 canonical name 작업시트](06_erd_and_verification.md) (제안명 `msg_conversion_count`·`msg_roi_pct`·ROAS=배수·CTR=inline_link_click_ctr 등). 방법론·로드맵 = [ERD/INDEX §4](../INDEX.md).
