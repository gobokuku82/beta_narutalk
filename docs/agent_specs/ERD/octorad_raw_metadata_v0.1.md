# raw ERD 메타데이터 + 컬럼 description — octorad_raw_metadata

> **v0.1 — 테이블 메타데이터 + 컬럼 description. raw ERD([erd_octorad_raw_v1.0](erd_octorad_raw_v1.0.md))의 의미 레이어.**

| 항목 | 내용 |
|---|---|
| 생성일 | 2026-06-14 |
| 규모 | 34 테이블 · 712 컬럼 설명 |
| 원천 | **raw=벤더 스키마 → description 정본=벤더 공식 API doc**(source=vendor_doc) + dict + 분류 §6 실측 + 추론 |
| 머신 sidecar | `octorad_raw_metadata_v0.1.yaml` (canonical contract 씨앗) |
| 원칙 | dict↔raw drift = raw 채택 + semantic_note. 각 설명에 source·confidence 표기(신뢰도 투명) |
| 외부 검증 | 핵심 충돌 컬럼(salesAmt·ccnt·crto·Meta `actions[]`·ROAS·clicks 등)은 [referrence/06](referrence/06_erd_and_verification.md)이 **공식 doc**(Naver Java `Stat.java`·Meta v25)으로 교차검증 — vendor_doc 격상 |

## 신뢰도 분포 (description 출처)

> 설명을 어디서 얻었나 = 얼마나 믿을지. **vendor_doc/classification = 권위, inferred = 검증 필요.**

| source | 컬럼수 | 의미 |
|---|--:|---|
| `vendor_doc` | 266 | 벤더 공식 API 문서(정본) |
| `dict` | 238 | 데이터사전(인간작성) |
| `inferred` | 164 | 컬럼명 기반 추론(검증 필요) |
| `classification` | 44 | 분류 §6 실측확정(salesAmt=비용·ccnt=전환수 등) |

| confidence | 컬럼수 |
|---|--:|
| high | 601 |
| med | 108 |
| low | 3 |


## 광고 성과

### `meta_ads_by_age`

| 메타 | 값 |
|---|---|
| vendor | Meta |
| API/소스 | Meta Marketing API — Ad Insights API (/{ad-account-id}/insights, breakdowns=age) |
| 공식 doc | https://developers.facebook.com/docs/marketing-api/insights/breakdowns/ |
| grain | 일×캠페인×연령대 (breakdowns=age; 540행 ≈ 90 캠페인일 × 6 연령버킷) |
| family·format·rows | ad_performance · json (wrapper: data[]=540, paging) · 540 |
| PII | 없음 |

meta_ads_performance 와 동일 Ads Insights 스키마에 breakdowns=age(연령대) 차원을 추가한 변형. 행이 연령버킷(18-24…65+)으로 분해됨. account_currency/objective/buying_type/attribution_setting 등 메타 컬럼 동일. 전환계는 동일하게 actions/action_values/purchase_roas/cost_per_action_type 중첩 배열(빈배열 변형 포함). 커버: data[].* 전 leaf + age 차원.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `data[].age` | string | 연령대 breakdown 버킷 (18-24 / 25-34 / 35-44 / 45-54 / 55-64 / 65+) |  | vendor_doc | high | 🔑 | I12/C7.3: Meta 표준 age breakdown. customers.age_group 과 버킷 경계 호환하나 의미 다름(광고 노출 차원 vs 개인 속성). |
| `data[].account_currency` | string | 계정 통화 코드 (ISO 4217) | currency_code | vendor_doc | high |  | C2.2. |
| `data[].account_id` | string | Meta 광고 계정 ID |  | vendor_doc | high | 🔑 |  |
| `data[].account_name` | string | 광고 계정 이름 |  | dict | high |  |  |
| `data[].campaign_id` | string | Meta 캠페인 ID (18자리) |  | vendor_doc | high | 🔑 | I1/C5.1: meta_ads_performance.campaign_id 와 동일 공간(FK). |
| `data[].campaign_name` | string | 캠페인명 |  | dict | high |  |  |
| `data[].objective` | string | 캠페인 목표 |  | vendor_doc | high |  |  |
| `data[].buying_type` | string | 구매 방식 (AUCTION/RESERVED) |  | vendor_doc | high |  |  |
| `data[].attribution_setting` | string | 전환 어트리뷰션 설정 |  | vendor_doc | high |  |  |
| `data[].date_start` | date | 리포트 일자 시작 (YYYY-MM-DD) |  | vendor_doc | high | 🔑 | T1. |
| `data[].date_stop` | date | 리포트 일자 종료 (YYYY-MM-DD) |  | vendor_doc | high |  |  |
| `data[].spend` | string | 연령대별 광고비 | account_currency | vendor_doc | high |  | A1: 연령버킷 분해. 합산 시 캠페인 spend 와 일치 검증 가능. |
| `data[].impressions` | string | 연령대별 노출수 | count | vendor_doc | high |  |  |
| `data[].clicks` | string | 연령대별 전체 클릭수 | count | vendor_doc | high |  |  |
| `data[].unique_clicks` | string | 연령대별 유니크 클릭수 | count unique | vendor_doc | high |  |  |
| `data[].inline_link_clicks` | string | 연령대별 인라인 링크 클릭수 | count | vendor_doc | high |  |  |
| `data[].ctr` | string | CTR = clicks/impressions×100 | percent | vendor_doc | high |  |  |
| `data[].inline_link_click_ctr` | string | 링크 클릭률 = inline_link_clicks/impressions×100 | percent | vendor_doc | high |  |  |
| `data[].cpc` | string | CPC = spend/clicks | account_currency per click | vendor_doc | high |  |  |
| `data[].cost_per_inline_link_click` | string | 링크 클릭당 비용 | account_currency per link click | vendor_doc | high |  |  |
| `data[].cpm` | string | CPM = spend/impressions×1000 | account_currency per 1000 impressions | vendor_doc | high |  |  |
| `data[].reach` | string | 연령대별 도달(유니크) | count unique | vendor_doc | high |  | A11: paid reach. breakdown 합이 캠페인 reach 와 다를 수 있음(유니크 중복 제거). |
| `data[].frequency` | string | 빈도 = impressions/reach | ratio | vendor_doc | high |  |  |
| `data[].actions[]` | array<obj{action_type,value}> | 연령대별 액션 건수 배열 {action_type,value} | count | vendor_doc | high |  | A4/C6.2: omni_purchase 필터 필수. |
| `data[].actions[].action_type` | string | 액션 유형 |  | vendor_doc | high |  |  |
| `data[].actions[].value` | string | 건수 | count | vendor_doc | high |  |  |
| `data[].action_values[]` | array<obj{action_type,value}> | 연령대별 매출 배열 (빈배열 변형 array(empty) 관측됨) | account_currency | vendor_doc | high |  | A5: 일부 행은 빈배열(전환 0). |
| `data[].action_values[].action_type` | string | 매출 귀속 액션 유형 |  | vendor_doc | high |  |  |
| `data[].action_values[].value` | string | 매출 금액 | account_currency | vendor_doc | high |  |  |
| `data[].purchase_roas[]` | array<obj{action_type,value}> | ROAS 배열 (배수). 빈배열 변형 관측됨 | ratio (배수) | vendor_doc | high |  | A6/C1.1. |
| `data[].purchase_roas[].action_type` | string | ROAS 귀속 액션 |  | vendor_doc | high |  |  |
| `data[].purchase_roas[].value` | string | ROAS 값(배수) | ratio (배수) | vendor_doc | high |  |  |
| `data[].cost_per_action_type[]` | array<obj{action_type,value}> | 액션 유형별 CPA 배열 (빈배열 변형 관측됨) | account_currency per action | vendor_doc | high |  |  |
| `data[].cost_per_action_type[].action_type` | string | CPA 액션 유형 |  | vendor_doc | high |  |  |
| `data[].cost_per_action_type[].value` | string | 액션당 비용 | account_currency per action | vendor_doc | high |  |  |
| `data[].cost_per_inline_link_click` | string | (중복 표기 — 위 항목 참조) | account_currency per link click | vendor_doc | high |  | 인벤토리 path 중복 없음; 단일 컬럼. |
| `paging.cursors.after` | string | 다음 페이지 커서 |  | vendor_doc | high |  | 페이지네이션 메타. |
| `paging.cursors.before` | string | 이전 페이지 커서 |  | vendor_doc | high |  |  |

### `meta_ads_performance`

| 메타 | 값 |
|---|---|
| vendor | Meta |
| API/소스 | Meta Marketing API — Ad Insights API (/{ad-account-id}/insights, level=campaign, time_increment=1) |
| 공식 doc | https://developers.facebook.com/docs/marketing-api/insights/ |
| grain | 일×캠페인 (date_start=date_stop, time_increment=1; 90행 = 일별 캠페인 집계) |
| family·format·rows | ad_performance · json (wrapper: data[]=90, paging) · 90 |
| PII | 없음 |

Meta(Facebook/Instagram) 캠페인 단위 일별 광고 성과. Ads Insights API 응답을 data[] 배열로 래핑. 핵심 지표(spend/impressions/clicks/reach/frequency/cpc/cpm/ctr)는 평탄 컬럼, 전환계(actions/action_values/purchase_roas/cost_per_action_type)는 {action_type,value} 중첩 배열 — purchase 추출 시 action_type='omni_purchase' 필터 필수(미필터=silent-0, C6.2). 전 수치 컬럼이 string 직렬화(C3.2). 금액은 account_currency 의존(KRW 단정 불가, C2.2). 커버: data[].* 전 leaf + 중첩 액션배열 대표.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `data[].account_id` | string | Meta 광고 계정 ID (예 act_847251963) |  | vendor_doc | high | 🔑 | ad_change_history._meta.ad_account_id 와 연결. dict 예시 act_ 접두. |
| `data[].account_name` | string | 광고 계정 이름 (예 C:LUMI Korea) |  | dict | high |  |  |
| `data[].account_currency` | string | 계정 통화 코드 (ISO 4217). spend/cpc/cpm/conversion-value 의 통화 정본 | currency_code | vendor_doc | high |  | C2.2: mock 은 KRW 로 보이나 실 API 는 USD/현지통화 가능 → 금액 KRW 강제 가정 금지. |
| `data[].campaign_id` | string | Meta 캠페인 고유 ID (18자리 숫자 문자열) |  | vendor_doc | high | 🔑 | I1/C5.1: Meta 전용 ID 공간. naver(cmp-)/advoost(GFA)/kakao(CMP_KKO)/CRM(int) 와 직접 join 불가 — campaign_name/utm 매핑테이블로만 연결. |
| `data[].campaign_name` | string | 캠페인명 (CLUMI_시즌_유형_제품 규칙, 예 CLUMI_SPR_PROSP_Serum) |  | dict | high |  | I2: cross-channel 연결의 실질 키(utm_campaign 과 매핑). |
| `data[].objective` | string | 캠페인 목표 (예 OUTCOME_SALES/OUTCOME_TRAFFIC 등 Meta 캠페인 objective) |  | vendor_doc | high |  |  |
| `data[].buying_type` | string | 구매 방식 (AUCTION / RESERVED) |  | vendor_doc | high |  |  |
| `data[].attribution_setting` | string | 전환 어트리뷰션 설정 (예 7d_click 또는 7d_click_or_1d_view). actions/action_values 의 귀속 창을 규정 |  | vendor_doc | high |  | 전환수/매출 비교 시 채널 간 어트리뷰션 창 차이의 근거(A4/A5 합산 주의). |
| `data[].date_start` | date | 리포트 일자 시작 (YYYY-MM-DD) |  | vendor_doc | high | 🔑 | T1: 일별 grain 이라 date_stop 과 동일. naver statDt(YYYYMMDD)/GA4 event_date(UTC) 와 포맷·TZ 충돌(C4.1/C4.2). KST 영업일 가정. |
| `data[].date_stop` | date | 리포트 일자 종료 (YYYY-MM-DD, 일별이라 date_start 동일) |  | vendor_doc | high |  |  |
| `data[].spend` | string | 광고비 (집행 비용) | account_currency (KRW 추정) | vendor_doc | high |  | A1/T3: string 직렬화(C3.2). naver salesAmt(=비용, C6.1)·advoost cost 와 동의어. 통화 account_currency 의존. |
| `data[].impressions` | string | 노출수 (광고가 화면에 표시된 횟수) | count | vendor_doc | high |  | A2: string. reach(유니크)와 구분. IG views(조회)와 혼동 금지. |
| `data[].clicks` | string | 전체 클릭수 (광고의 모든 클릭, 링크 외 포함) | count | vendor_doc | high |  | A3: clicks(all) ≠ inline_link_clicks(링크만). 메시징 click 과 별 의미. |
| `data[].unique_clicks` | string | 유니크 클릭수 (클릭한 고유 사용자 수) | count unique | vendor_doc | high |  | clicks(총합)와 다름 — 사람 수 기준. |
| `data[].inline_link_clicks` | string | 인라인 링크 클릭수 (광고 내 링크 클릭만) | count | vendor_doc | high |  | A3: clicks(all) 의 부분집합. CTR/CPC canonical 결정 시 clicks vs link-clicks 선택 대상. |
| `data[].ctr` | string | CTR — 클릭률 = clicks / impressions × 100 | percent | vendor_doc | high |  | A7: %. dict 예시 0.91=0.91%. inline_link_click_ctr(링크 한정)과 분자 다름. |
| `data[].inline_link_click_ctr` | string | 링크 클릭률 = inline_link_clicks / impressions × 100 | percent | vendor_doc | high |  | ctr(all) 과 별개 정의. |
| `data[].cpc` | string | CPC — 클릭당 비용 = spend / clicks | account_currency per click | vendor_doc | high |  | A8: cpc(all clicks) ≠ cost_per_inline_link_click. |
| `data[].cost_per_inline_link_click` | string | 링크 클릭당 비용 = spend / inline_link_clicks | account_currency per link click | vendor_doc | high |  | cpc 의 링크 한정 변형. |
| `data[].cpm` | string | CPM — 1000 노출당 비용 = spend / impressions × 1000 | account_currency per 1000 impressions | vendor_doc | high |  | A9: naver SA 부재(검색=CPC), Meta+advoost 2채널뿐. |
| `data[].reach` | string | 도달 — 광고를 본 고유 사용자(유니크) 수 | count unique | vendor_doc | high |  | A11/C6.4: 유료(paid) reach. instagram_engagement insights reach(organic)와 의미 달라 합산 금지. impressions(중복 포함)와 구분. |
| `data[].frequency` | string | 빈도 = impressions / reach (사용자당 평균 노출 횟수) | ratio (impressions/reach) | vendor_doc | high |  | A12: Meta 3소스 내부에만 존재(채널 간 동의어 미달). customer_rfm.frequency(구매빈도)와 동음이의. |
| `data[].actions[]` | array<obj{action_type,value}> | 전환/액션 건수 배열. 각 원소 {action_type, value}. 발생 0이면 원소 부재 가능 | count (value=string) | vendor_doc | high |  | A4/C6.2: list<AdsActionStats>. 구매전환수 = action_type='omni_purchase' 필터. flat actions.purchase 키 부재(dict drift). 미필터 추출=silent-0. |
| `data[].actions[].action_type` | string | 액션 유형 (예 omni_purchase, add_to_cart, link_click, landing_page_view 등) |  | vendor_doc | high |  | purchase = omni_purchase (= offsite_conversion.fb_pixel_purchase, 동일 value). §6 raw 직독 확정. |
| `data[].actions[].value` | string | 해당 action_type 의 건수 (문자열 직렬화) | count | vendor_doc | high |  | C3.2: string. |
| `data[].action_values[]` | array<obj{action_type,value}> | 전환 매출(액션 가치) 배열. 각 원소 {action_type, value} | account_currency (value=string) | vendor_doc | high |  | A5/C6.2: 구매매출 = action_type='omni_purchase' 의 value. §6 예 590,412원. naver convAmt(=매출, C6.1) 와 동의어. |
| `data[].action_values[].action_type` | string | 액션 유형 (매출 귀속 액션, 주로 omni_purchase) |  | vendor_doc | high |  |  |
| `data[].action_values[].value` | string | 해당 액션의 매출 금액 (문자열) | account_currency | vendor_doc | high |  |  |
| `data[].purchase_roas[]` | array<obj{action_type,value}> | 구매 ROAS 배열. value = action_values / spend (배수) | ratio (배수, multiple) | vendor_doc | high |  | A6/C1.1: Meta ROAS=배수(§6 omni_purchase=2.2063). naver ror·advoost roas=%(÷100 필요). roi_percent(ROI)와 절대 합산 금지(C6.3). flat roas 키 부재(dict drift, dict 의 roas=1.04 는 오기). |
| `data[].purchase_roas[].action_type` | string | ROAS 귀속 액션 (omni_purchase) |  | vendor_doc | high |  |  |
| `data[].purchase_roas[].value` | string | ROAS 값 (배수, 예 2.2063) | ratio (배수) | vendor_doc | high |  |  |
| `data[].cost_per_action_type[].action_type` | string | 액션 유형별 CPA 의 액션 유형 |  | vendor_doc | high |  | naver cpConv(CPA)와 동의어 후보(§6). |
| `data[].cost_per_action_type[].value` | string | 해당 action_type 1건당 비용 = spend / actions[type] | account_currency per action | vendor_doc | high |  | meta_ads_performance 에서는 평탄 path 로 관측(빈배열 없음); by_age/instagram_inapp 에는 빈배열 변형도 존재. |
| `paging.cursors.after` | string | 다음 페이지 커서 (Graph API 페이지네이션) |  | vendor_doc | high |  | 데이터 아닌 페이지네이션 메타. |
| `paging.cursors.before` | string | 이전 페이지 커서 |  | vendor_doc | high |  |  |

### `meta_instagram_inapp`

| 메타 | 값 |
|---|---|
| vendor | Meta |
| API/소스 | Meta Marketing API — Ad Insights API (/{ad-account-id}/insights, breakdowns=publisher_platform,platform_position) |
| 공식 doc | https://developers.facebook.com/docs/marketing-api/insights/breakdowns/ |
| grain | 일×캠페인×게재면 (breakdowns=publisher_platform×platform_position; 150행) |
| family·format·rows | ad_performance · json (wrapper: data[]=150, paging) · 150 |
| PII | 없음 |

meta_ads_performance 와 동일 Ads Insights 스키마에 게재 위치 breakdown(publisher_platform × platform_position)을 추가한 변형. 'instagram_inapp' 명칭이나 publisher_platform 에 instagram·facebook 모두 포함될 수 있음. 행이 플랫폼×위치(feed/story/reels/explore 등)로 분해. 전환계는 동일 중첩 배열 구조. 커버: data[].* 전 leaf + 게재면 2차원.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `data[].publisher_platform` | string | 게재 플랫폼 breakdown (instagram, facebook, audience_network, messenger) |  | vendor_doc | high | 🔑 | dict 예시 instagram/facebook. 'inapp' 명칭 불구 facebook 행 가능. |
| `data[].platform_position` | string | 게재 위치 breakdown (feed, story, reels, explore, marketplace 등) |  | vendor_doc | high | 🔑 | publisher_platform 과 조합되어 게재면 정의. |
| `data[].account_currency` | string | 계정 통화 코드 | currency_code | vendor_doc | high |  | C2.2. |
| `data[].account_id` | string | Meta 광고 계정 ID |  | vendor_doc | high | 🔑 |  |
| `data[].account_name` | string | 광고 계정 이름 |  | dict | high |  |  |
| `data[].campaign_id` | string | Meta 캠페인 ID (18자리) |  | vendor_doc | high | 🔑 | I1/C5.1. |
| `data[].campaign_name` | string | 캠페인명 |  | dict | high |  |  |
| `data[].objective` | string | 캠페인 목표 |  | vendor_doc | high |  |  |
| `data[].buying_type` | string | 구매 방식 |  | vendor_doc | high |  |  |
| `data[].attribution_setting` | string | 전환 어트리뷰션 설정 |  | vendor_doc | high |  |  |
| `data[].date_start` | date | 리포트 일자 시작 (YYYY-MM-DD) |  | vendor_doc | high | 🔑 | T1. |
| `data[].date_stop` | date | 리포트 일자 종료 (YYYY-MM-DD) |  | vendor_doc | high |  |  |
| `data[].spend` | string | 게재면별 광고비 | account_currency | vendor_doc | high |  | A1. |
| `data[].impressions` | string | 게재면별 노출수 | count | vendor_doc | high |  |  |
| `data[].clicks` | string | 게재면별 전체 클릭수 | count | vendor_doc | high |  |  |
| `data[].unique_clicks` | string | 게재면별 유니크 클릭수 | count unique | vendor_doc | high |  |  |
| `data[].inline_link_clicks` | string | 게재면별 인라인 링크 클릭수 | count | vendor_doc | high |  |  |
| `data[].ctr` | string | CTR = clicks/impressions×100 | percent | vendor_doc | high |  |  |
| `data[].inline_link_click_ctr` | string | 링크 클릭률 | percent | vendor_doc | high |  |  |
| `data[].cpc` | string | CPC = spend/clicks | account_currency per click | vendor_doc | high |  |  |
| `data[].cost_per_inline_link_click` | string | 링크 클릭당 비용 | account_currency per link click | vendor_doc | high |  |  |
| `data[].cpm` | string | CPM = spend/impressions×1000 | account_currency per 1000 impressions | vendor_doc | high |  |  |
| `data[].reach` | string | 게재면별 도달(유니크) | count unique | vendor_doc | high |  | A11: paid reach. |
| `data[].frequency` | string | 빈도 = impressions/reach | ratio | vendor_doc | high |  |  |
| `data[].actions[].action_type` | string | 액션 유형 (omni_purchase 등) |  | vendor_doc | high |  | A4/C6.2: 평탄 path 로 관측(actions[] 빈배열 없이 leaf 직접). |
| `data[].actions[].value` | string | 액션 건수 | count | vendor_doc | high |  |  |
| `data[].action_values[]` | array<obj{action_type,value}> | 매출 배열 (빈배열 변형 관측됨) | account_currency | vendor_doc | high |  | A5. |
| `data[].action_values[].action_type` | string | 매출 귀속 액션 유형 |  | vendor_doc | high |  |  |
| `data[].action_values[].value` | string | 매출 금액 | account_currency | vendor_doc | high |  |  |
| `data[].cost_per_action_type[].action_type` | string | CPA 액션 유형 |  | vendor_doc | high |  |  |
| `data[].cost_per_action_type[].value` | string | 액션당 비용 | account_currency per action | vendor_doc | high |  |  |
| `data[].purchase_roas[]` | array<obj{action_type,value}> | ROAS 배열(배수). 빈배열 변형 관측됨 | ratio (배수) | vendor_doc | high |  | A6/C1.1. |
| `data[].purchase_roas[].action_type` | string | ROAS 귀속 액션 |  | vendor_doc | high |  |  |
| `data[].purchase_roas[].value` | string | ROAS 값(배수) | ratio (배수) | vendor_doc | high |  |  |
| `paging.cursors.after` | string | 다음 페이지 커서 |  | vendor_doc | high |  | 페이지네이션 메타. |
| `paging.cursors.before` | string | 이전 페이지 커서 |  | vendor_doc | high |  |  |

### `naver_advoost`

| 메타 | 값 |
|---|---|
| vendor | Naver Performance Display Ad / ADVoost (구 GFA, 성과형 디스플레이 광고) |
| API/소스 | Naver Performance Display Ad API (Beta) — 성과(report) API. mock raw = 정규화 영어 컬럼명(원 GFA 필드명 아님) |
| 공식 doc | https://naver-ad-api.github.io/openapi-guide/docs/intro |
| grain | 일×캠페인 (report_date × campaign_id). row_count 90 = 일·캠페인 분해. |
| family·format·rows | ad_performance · csv · 90 |
| PII | 없음 |

네이버 성과형 디스플레이(ADVoost/GFA) 캠페인 일별 성과. CSV 23컬럼 전수 커버. ⚠ GFA API는 파트너 한정 beta — 공식 raw 필드 스펙 비공개. mock 컬럼명은 정규화 영어(impressions/clicks/cost/roas 등)라 벤더 raw 필드명과 다름 → vendor_doc 은 제품·지표 존재만 확인, 의미는 dict+분류 채택. 전환=VT/CT 분리(total=VT+CT 추정, A4 이중계상 주의), roas=% 단위.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `report_date` | date/datetime | 리포트 일자 (KST 영업일). | date | dict | high | 🔑 | T1 cluster: statDt·Meta date_start 와 동의어. raw=YYYY-MM-DD. |
| `campaign_id` | string | ADVoost 캠페인 ID (GFA prefix 발급체계, 예 GFA2026040001). |  | dict | high | 🔑 | I1/C5.1: 네이버 SA(cmp-)·Meta(18자리)·kakao(CMP_KKO)와 별 ID 공간, join 불가. |
| `campaign_name` | string | 캠페인명 (예 CLUMI_SHOPPING_PERFORMANCE). |  | dict | high |  | I2 cluster. 영문코드 표기. |
| `campaign_type` | string | 캠페인 유형 (SHOPPING / CATALOG / DISPLAY). |  | dict | high |  | 값셋 dict 예시 기준. |
| `campaign_objective` | string | 캠페인 목표/목적 (예 전환·트래픽·인지). |  | inferred | med |  | 사전 미등재(인벤토리 only). GFA 캠페인 objective 추정. |
| `creative_type` | string | 크리에이티브 유형 (PRODUCT_IMAGE / DYNAMIC_BANNER / VIDEO_15S). |  | dict | high |  | VIDEO 유형일 때만 video_play_* 유의미. |
| `impressions` | string | 노출수. | count | dict | high |  | A2 cluster. raw=string(캐스팅 필요 C3.2). 정규화 영어명(SA impCnt 와 동의어). |
| `clicks` | string | 클릭수. | count | dict | high |  | A3 cluster. raw=string. |
| `cost` | string | 광고비 (KRW). | KRW | dict | high |  | A1/T3 cluster. SA salesAmt(비용)·kakao total_cost_krw 와 동의어. raw=string. |
| `ctr` | string | CTR 클릭률 (%). dict 예시 0.9459 → % 표기. | percent | dict | high |  | A7 cluster. raw=string. SA ctr(float)와 표기/타입 차. |
| `cpc` | string | 평균클릭비용 CPC (KRW). | KRW | inferred | med |  | A8 cluster. 사전 advoost 항목엔 cpc 명시 없음 — SA/Meta cpc 동형 추론. |
| `cpm` | string | 1000노출당 비용 CPM (KRW). | KRW | inferred | med |  | A9 cluster. 사전 미명시 — 디스플레이 표준 CPM 추론. Meta+advoost 2채널뿐. |
| `view_through_conversions` | string | VT 전환 (노출 후 비클릭 전환수). | count | dict | high |  | A4 cluster. total_conversions=VT+CT 추정 → 합산 시 이중계상 금지(C 미결 #12). |
| `click_through_conversions` | string | CT 전환 (클릭 후 전환수). | count | dict | high |  | A4 cluster. |
| `total_conversions` | string | 총 전환수 (VT+CT 추정 합). | count | inferred | med |  | A4: total=VT+CT 추정(전수 미검증). SA ccnt·Meta actions[]와 attribution 모델 달라 합산 금지. |
| `conversion_value` | string | 전환 매출 (KRW). | KRW | dict | high |  | A5/T4 cluster. SA convAmt·kakao conversion_amount_krw 와 동의어. raw=string. |
| `roas` | string | ROAS (%). dict 예시 928.55 → 네이버는 % 표기. | percent | dict | high |  | A6/C1.1 치명: 동명 'roas'이나 Meta purchase_roas(배수)와 100배 차. ÷100 정규화 필요. roi_percent(ROI)와 분리. |
| `vtcvr` | string | VT 전환율 (View-Through CVR, %). | percent | classification | med |  | A10 cluster(분류문서 명시). vt 전환/노출 추정 분모. |
| `ctcvr` | string | CT 전환율 (Click-Through CVR, %). | percent | classification | med |  | A10 cluster. ct 전환/클릭 추정 분모. SA crto 와 분모 정의 비교 필요. |
| `video_play_25` | string | 비디오 25% 시청수 (DISPLAY/VIDEO 소재만). | count | dict | high |  | creative_type=VIDEO 일 때만 유의미. 비영상 소재는 0/null. |
| `video_play_50` | string | 비디오 50% 시청수 (영상 소재만). | count | inferred | high |  | video_play_25/100 사이 quartile. 사전엔 25·100만 예시. |
| `video_play_75` | string | 비디오 75% 시청수 (영상 소재만). | count | inferred | high |  | quartile 시청 지표. |
| `video_play_100` | string | 비디오 100% 완료수 (영상 소재만). | count | dict | high |  | 완전재생(VTR 분자). creative_type=VIDEO 한정. |

### `naver_searchad`

| 메타 | 값 |
|---|---|
| vendor | Naver SearchAd (네이버 검색광고) |
| API/소스 | Naver SearchAd API — StatReport/stat (광고지표조회 STAT) |
| 공식 doc | https://github.com/naver/searchad-apidoc/wiki/FAQ-stat |
| grain | 일×키워드 (statDt × nccKeywordId × device; nccCampaignId/nccAdgroupId 상위차원). row_count 1680 = 일·키워드·디바이스 분해 합. |
| family·format·rows | ad_performance · json · 1680 |
| PII | 없음 |

네이버 검색광고 키워드 단위 일별 성과 통계 (StatReport). wrapper.data[] 배열, leaf 17컬럼 전수 커버. 벤더 공식 stat 필드 정본(FAQ-stat wiki)으로 의미 확정. 치명 함정: salesAmt=매출 아닌 '총비용'(광고비), convAmt=전환매출, ror=ROAS. 사전(clumi_dict)은 폐기 mock 컬럼명(stat_dt/camp_id/convCnt 등)이라 raw와 drift — raw 채택.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `data[].statDt` | date/datetime | 리포트/집계 일자 (KST 영업일). raw=date 파싱(원천 YYYYMMDD 정수형 가능성). T1 cluster: GFA report_date·Meta date_start 와 동의어이나 포맷/TZ 충돌. | date | vendor_doc | high | 🔑 | dict drift: 사전 'stat_dt' → raw 'statDt'. 포맷 충돌(YYYYMMDD vs YYYY-MM-DD) C4.1. |
| `data[].nccCampaignId` | string | 네이버 검색광고 캠페인 ID (cmp- prefix 발급체계). |  | vendor_doc | high | 🔑 | dict drift: 사전 'camp_id' → raw 'nccCampaignId'. I1/C5.1: ID 공간 채널마다 달라 cross-channel join 불가 (Meta 18자리·GFA·CMP_KKO·NTT 와 별 공간). |
| `data[].nccAdgroupId` | string | 광고그룹 ID (grp- 체계). |  | vendor_doc | high | 🔑 | dict drift: 사전 'grp_id' raw 부재 → raw 'nccAdgroupId'. |
| `data[].nccKeywordId` | string | 키워드 ID (nkw- 체계). grain 의 최하위 식별자. |  | vendor_doc | high | 🔑 | dict drift: 사전 'kwd_id' → raw 'nccKeywordId'. 사전 'kwd'(키워드 한글텍스트) raw 부재. |
| `data[].id` | string | stat 행 식별자 (StatReport row id). |  | inferred | med | 🔑 | 사전 미등재(인벤토리 only). 벤더 stat 응답의 row id 추정. |
| `data[].device` | string | 디바이스 구분 (M=mobile, P=pc). 노출/성과 분해 차원. |  | vendor_doc | high | 🔑 | dict drift: 사전 'device_tp' → raw 'device'. I14/C: 값 도메인 M/P 코드 = GA4 mobile/desktop/tablet·내부 mobile_web/app/pc 와 충돌, 디코딩 필요. |
| `data[].impCnt` | int | 노출수. 벤더 공식=노출수(Impressions). | count | vendor_doc | high |  | A2 cluster. 'impCnt' 명칭이 impressions 동의어. raw=int (Meta/advoost는 string). |
| `data[].clkCnt` | int | 클릭수. 벤더 공식=클릭수(Clicks). | count | vendor_doc | high |  | A3 cluster. 메시징 click_count 와 분모 다름(동음이의). |
| `data[].salesAmt` | int | 총비용 = 광고비 (KRW). 벤더 공식 FAQ-stat: salesAmt='총비용'. **매출이 아님**. | KRW | vendor_doc | high |  | C6.1 최우선 오염원: 이름은 sales(매출)이나 의미=비용(광고비). convAmt(매출)와 짝. 미분리 시 ROAS 뒤집힘. §6 실측 재확인(cpConv=salesAmt/ccnt). |
| `data[].convAmt` | int | 전환매출액 (KRW). 벤더 공식=전환매출액. salesAmt(비용)에 대응하는 매출 측. | KRW | vendor_doc | high |  | A5 cluster. C6.1: convAmt=매출 / salesAmt=비용 헷갈림 쌍. §6 실측: ror=convAmt/salesAmt×100 검증. |
| `data[].ccnt` | int | 전환수 (건). §6 raw 직독 실측확정: clk=5·ccnt=1 등 정수 건수. | count | classification | high |  | dict 의미 drift(치명): 사전 ccnt='CVR(%)' → 실제 '전환수(건)'. 사전 'convCnt'(전환수)는 raw 부재. A4 cluster. |
| `data[].crto` | float | 전환율 CVR (%). §6 실측: crto=ccnt/clkCnt×100 (1/5=20.0). 벤더 공식 crto=전환율. | percent | classification | high |  | A10 cluster. dict 미대응(사전은 ccnt를 CVR로 오기). 클릭 대비 전환율(분모=clkCnt). |
| `data[].cpConv` | int | 전환당비용 CPA (KRW). §6 실측: cpConv=salesAmt/ccnt (1678/1=1678). 벤더 공식=전환당비용. | KRW | classification | high |  | A8/A4 파생. 사전 미등재. salesAmt(비용)÷ccnt(전환수) 일관. |
| `data[].ror` | float | ROAS (%). §6 실측: ror=convAmt/salesAmt×100 (62332/1678≈3714.66). 벤더 공식 ror=광고수익률=전환매출/총비용. | percent | classification | high |  | A6/C1.1: 단위 % (Meta purchase_roas=배수와 100배 차). C1.2: ROI(roi_percent)와 분자 다름(혼동 금지). 벤더 wiki는 multiplier 정의이나 mock raw 실측값은 %(512.20). |
| `data[].cpc` | int | 평균클릭비용 CPC (KRW). 벤더 공식=평균클릭비용. | KRW | vendor_doc | high |  | A8 cluster. raw=int (Meta=string). 메시징 cost_per_message_krw 아님. |
| `data[].ctr` | float | 클릭률 CTR (%). 벤더 공식=클릭률. | percent | vendor_doc | high |  | A7 cluster. raw=float (Meta/advoost=string). 노출 대비 클릭(메시징 click_rate 와 분모 다름). |
| `data[].avgRnk` | float | 평균노출순위 (검색결과 평균 게재 순위). 벤더 공식=평균노출순위. | position | vendor_doc | high |  | 검색광고 고유 지표(단일출처). 낮을수록 상위. pcNxAvgRnk/mblNxAvgRnk 등 변형은 mock 미수집. |


## 메시징/CRM

### `crm_campaigns`

| 메타 | 값 |
|---|---|
| vendor | 자사 CRM (own, mock — 벤더 API 없음) |
| API/소스 | 내부 CRM 메시지 발송 시스템 SQL 테이블 (clumi_mock_18_crm_messages.sql). 정규화 3테이블 중 부모(캠페인). |
| grain | 캠페인 단위 (1행 = 1 CRM 캠페인). |
| family·format·rows | messaging · sql · None |
| PII | 없음 |

자사 CRM 멀티채널 메시지 캠페인 마스터(자체 mock, 벤더 API 없음 — 의미는 dict+분류+추론). crm_message_variants(1:N)·crm_send_logs(1:N) 의 부모. 채널 다중값(kakao_friendtalk,naver_talktalk,email 콤마 구분)으로 카카오 비즈메시지·네이버 톡톡·이메일을 한 캠페인이 묶음. ab_test 플래그로 variant 분기. campaign_id=int(카카오/네이버 string ID 공간과 달라 cross-join 불가, C5.1). 시각 컬럼(scheduled_at/sent_at)은 T10 단계 의미차 — TZ 암묵 KST.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `campaign_id` | int | CRM 캠페인 ID (정수, 예 18001). PK. |  | dict | high | 🔑 | I1/C5.1: int 타입 — kakao(CMP_KKO)/naver(NTT) string ID 공간과 달라 직접 join 불가. |
| `campaign_name` | varchar(200) | 캠페인명 (한글, 예 '봄세럼_1+1_혜택안내'). |  | dict | high |  | kakao/talktalk campaign_name 과 느슨 매핑(교차 연결 키). |
| `campaign_type` | varchar(30) | 캠페인 유형 (예 PROMO_PUSH, INFO_EMAIL, LOYALTY_PUSH). |  | dict | high |  |  |
| `trigger_type` | varchar(30) | 발송 트리거 유형 (예약/이벤트 기반 등). |  | inferred | med |  |  |
| `target_segment` | varchar(100) | 대상 세그먼트 (RFM/등급 등 타겟 그룹). |  | inferred | med |  | RFM rfm_segment/customer_tier 와 매핑 가능. |
| `channels` | varchar(200) | 발송 채널 (콤마 구분 다중값, 예 'kakao_friendtalk,naver_talktalk, email'). |  | dict | high |  | I7: 다중값 — 분해 필요. 한 CRM 캠페인이 카카오·네이버·이메일을 동시 묶음. |
| `scheduled_at` | datetime | 예약(스케줄) 발송 일시. | datetime | classification | high |  | T10: scheduled 단계. sent_at 와 단계 의미차. TZ 암묵 KST(라벨 없음). |
| `sent_at` | datetime | 실제 발송 일시 (캠페인 레벨). | datetime | classification | high |  | T10: sent 단계. crm_send_logs.sent_at(variant 레벨)와 grain 다름. |
| `status` | varchar(20) | 캠페인 상태. |  | inferred | med |  |  |
| `ab_test` | tinyint(1) | A/B 테스트 여부 (1=A/B 분기, 0=단일). |  | dict | high |  | 1이면 crm_message_variants 가 다수(A/B), variant_count 와 연동. |
| `variant_count` | int | 변형(variant) 수. |  | inferred | high |  |  |
| `created_by` | varchar(50) | 캠페인 생성자. |  | inferred | med |  |  |
| `created_at` | datetime | 레코드 생성 일시. | datetime | inferred | high |  |  |
| `updated_at` | datetime | 레코드 수정 일시. | datetime | inferred | high |  |  |

### `crm_message_variants`

| 메타 | 값 |
|---|---|
| vendor | 자사 CRM (own, mock — 벤더 API 없음) |
| API/소스 | 내부 CRM SQL 테이블 (clumi_mock_18_crm_messages.sql). crm_campaigns 자식, crm_send_logs 부모. |
| grain | 변형(variant) 단위 (1행 = 1 A/B 변형 = 1 캠페인의 메시지 안). |
| family·format·rows | messaging · sql · None |
| PII | 없음 |

자사 CRM A/B 메시지 변형(콘텐츠 안) 테이블(자체 mock, 벤더 API 없음). crm_campaigns(N:1)↔crm_send_logs(1:N) 의 중간. 변형별 메시지 전략(BENEFIT_FORWARD/URGENCY_FORWARD/LOSS_AVERSION 등)·제목·본문·CTA·발송비율(send_ratio) 보유. cta_url 에 utm 파라미터 포함(orders/signup_events utm_campaign 과 어트리뷰션 연결). 콘텐츠 메타만 — 성과 수치는 crm_send_logs.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `variant_id` | varchar(20) | 변형 ID (예 V18001_A). PK. |  | dict | high | 🔑 |  |
| `campaign_id` | int | 소속 캠페인 ID (FK → crm_campaigns.campaign_id). |  | dict | high | 🔑 | crm_campaigns 부모 참조. |
| `variant_label` | varchar(10) | A/B 라벨 (예 A, B, Single). |  | dict | high |  |  |
| `message_strategy` | varchar(30) | 메시지 전략 (BENEFIT_FORWARD/URGENCY_FORWARD/LOSS_AVERSION/INFORMATIONAL/REVIEW_SOCIAL_PROOF/VIP_EXCLUSIVE). |  | dict | high |  |  |
| `subject_line` | varchar(200) | 제목 (이메일/푸시 제목줄). |  | dict | high |  |  |
| `body_text` | text | 메시지 본문. |  | dict | high |  |  |
| `cta_text` | varchar(100) | CTA 버튼/링크 텍스트 (예 '지금 1+1 받기 →'). |  | dict | high |  |  |
| `cta_url` | varchar(500) | CTA 랜딩 URL (utm 파라미터 포함). |  | dict | high |  | I10: cta_url 내 utm_campaign 이 orders/signup_events.utm_campaign 과 어트리뷰션 연결 — 진짜 교차 키. |
| `image_url` | varchar(500) | 메시지 이미지 URL. |  | inferred | high |  |  |
| `preview_text` | varchar(200) | 미리보기(프리헤더) 텍스트. |  | inferred | high |  |  |
| `personalization_tags` | varchar(200) | 개인화 치환 태그 (예 {name} 등 머지 필드). |  | inferred | med |  |  |
| `send_ratio` | decimal(4,3) | A/B 발송 비율 (예 0.70, 0.30 — 변형별 발송 분할). | 비율(0~1) | dict | high |  | 캠페인 내 variant 들의 send_ratio 합=1 가정. |
| `created_at` | datetime | 레코드 생성 일시. | datetime | inferred | high |  |  |

### `crm_send_logs`

| 메타 | 값 |
|---|---|
| vendor | 자사 CRM (own, mock — 벤더 API 없음) |
| API/소스 | 내부 CRM SQL 테이블 (clumi_mock_18_crm_messages.sql). 발송 성과 집계 (변형 단위). |
| grain | 변형(variant) 단위 발송 집계 (1행 = 1 variant 의 발송→오픈→클릭→전환 누계). |
| family·format·rows | messaging · sql · None |
| PII | 없음 |

자사 CRM 변형별 발송 성과 집계 테이블(자체 mock, 벤더 API 없음 — 의미는 dict+분류+추론). grain=variant 단위(kakao summary=캠페인 누계와 grain 다름, 합산 전 정렬 C7.1). 깔때기: target→delivered→open→click→conversion. 율 컬럼(delivered_rate/open_rate/click_rate/click_through_rate_open/conversion_rate_click) 다수 — 분모 미명시(C6.6). roi_percent=ROI≠ROAS(C6.3). conversion_amount_krw=bigint(타입 혼재). unsubscribe_count/complaint_count=발송 부작용 지표.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `send_id` | int | 발송 로그 ID (정수). PK. |  | inferred | high | 🔑 |  |
| `variant_id` | varchar(20) | 변형 ID (FK → crm_message_variants.variant_id). |  | dict | high | 🔑 | grain 정렬 키 — variant 단위 집계. |
| `campaign_id` | int | 캠페인 ID (FK → crm_campaigns.campaign_id, denormalized). |  | dict | high | 🔑 |  |
| `sent_at` | datetime | 발송 일시 (variant 레벨). | datetime | inferred | high |  | T10. crm_campaigns.sent_at(캠페인 레벨)와 grain 다름. |
| `target_count` | int | 발송 대상 수. | 건 | classification | high |  | M1: kakao target_recipients / talktalk target_friends 와 동의어(명칭 비대칭). |
| `delivered_count` | int | 송달 성공 수 (단말 도달). | 건 | dict | high |  | M2/C6.5: crm/talktalk delivered(단말도달) vs kakao success(요청수락) — 동일 단계 단정 불가. |
| `delivered_rate` | decimal(5,2) | 송달율 (%). | % | inferred | high |  | §5#8: success_rate(kakao)↔delivered_rate(crm) 동의어 후보. =delivered/target 추정. |
| `open_count` | int | 오픈(열람) 수. | 건 | dict | high |  |  |
| `open_rate` | decimal(5,2) | 오픈율 (%). | % | dict | high |  | M5/C6.6: 분모(대상/송달) 미명시 — 채널 간 통합 시 왜곡. |
| `click_count` | int | 클릭 수. | 건 | dict | high |  |  |
| `click_rate` | decimal(5,2) | 클릭율 (%, 발송/송달 대비 CTR). | % | dict | high |  | M7: 발송·송달 대비. click_through_rate_open(오픈 대비)와 분모 다름 — 분리 필수. |
| `click_through_rate_open` | decimal(5,2) | 오픈 대비 클릭율 CTOR (%, click/open). | % | classification | high |  | M8: 사전 미등재(인벤토리에만). click_rate 와 분모 달라 통합 시 합쳐질 위험 — _open 표기 보존. |
| `conversion_count` | int | 전환 수 (메시지 attribution 기반). | 건 | dict | high |  | M9: attribution 모델 광고와 다름 — 광고 전환과 합산 금지. |
| `conversion_amount_krw` | bigint | 전환 매출 (KRW). | KRW | dict | high |  | M10: bigint(kakao int 과 타입 혼재). _krw 접미 명시(통화 안전, C2.3). |
| `conversion_rate_click` | decimal(5,2) | 클릭 대비 전환율 (%). | % | inferred | med |  | §5#8: conversion_rate_click↔conversion_rate_from_click 명칭 불일치 주의. |
| `avg_order_value` | int | 평균 주문 금액 AOV (KRW). | KRW | dict | med |  | M12: 도메인 전반 과다 재사용 — join/혼동 금지. _krw 미명시(통화 추정). |
| `roi_percent` | decimal(10,2) | ROI (%, 이익율). 예 2861.54. | % | classification | high |  | M11/C6.3: ROI≠ROAS — 절대 합치지 말 것. net/gross 산식 미명시. crm 비용 컬럼은 외부. |
| `unsubscribe_count` | int | 수신거부(구독해지) 수 — 발송 부작용 지표. | 건 | inferred | high |  | talktalk unfriend_after_send 와 유사 결(채널 특유 이탈). 마케팅 동의 철회. |
| `complaint_count` | int | 불만/스팸 신고 수 — 발송 부작용 지표. | 건 | inferred | high |  |  |
| `created_at` | datetime | 레코드 생성 일시. | datetime | inferred | high |  |  |

### `kakao_bizmessage`

| 메타 | 값 |
|---|---|
| vendor | Kakao i Connect Message (카카오 i 커넥트 메시지) — BizMessage 친구톡(FT)/알림톡(AT) |
| API/소스 | BizMessage 발송결과 조회 API 응답 (campaigns[] = 캠페인별 발송 통계 + results_sample[] = 개별 발송 결과 표본). 최상위 = 쿼리 응답 래퍼(code/status/next/query_date_range). |
| 공식 doc | https://docs.kakaoi.ai/kakao_i_connect_message/bizmessage_eng/api/api_reference/ |
| grain | 캠페인 누계 (campaigns[] 1행 = 1 캠페인, summary.* = 캠페인 전체 롤업). results_sample[] 는 개별 발송 grain (별도 — 합산 금지). |
| family·format·rows | messaging · json · 2 |
| PII | ⚠ 포함 |

카카오 비즈메시지(친구톡 FT=광고/정보성·채널 친구 한정, 알림톡 AT=정보성·비친구 포함) 캠페인 발송 성과. 벤더(Kakao i Connect Message) 발송결과 조회 API 응답 스키마가 의미의 정본. 구조 3층: (1) 최상위 래퍼=쿼리 응답 메타(code/status/next/query_date_range), (2) campaigns[].summary.*=캠페인별 발송→오픈→클릭→전환 깔때기 누계 통계, (3) campaigns[].results_sample[]=개별 발송 결과 표본(다른 grain). 금액은 KRW(_krw 접미 또는 명시). PII: results_sample[].phone_number_hash=해시(평문 아님, 완화됨). 커버: 핵심 식별·발송메타·summary 전수 + results_sample[] 대표 컬럼(개별 결과코드 구조). roi_percent=ROI≠ROAS(C6.3).

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `code` | string | 쿼리 응답 결과 코드 (래퍼 레벨, 예 200=성공). 발송결과 조회 요청 자체의 처리 코드. |  | vendor_doc | high |  | 벤더 응답 표준: 200=Success/100=Processing/400~520=오류. results_sample[].code(개별 발송 코드)와 레벨 다름. |
| `code_detail.detail_code` | string | 쿼리 응답 상세 결과 코드 (래퍼 레벨, 예 NRM0000=성공). |  | vendor_doc | high |  | NRM 프리픽스=Normal 계열 결과코드. |
| `code_detail.detail_message` | string | 쿼리 응답 상세 메시지 (detail_code 동반 설명, 예 '성공'). |  | vendor_doc | high |  |  |
| `next` | bool | 페이징 — 다음 페이지(추가 결과) 존재 여부. |  | inferred | med |  | 벤더 polling/페이징 패턴. campaigns[].next 와 동명(레벨 다름). |
| `status` | string | 쿼리 응답 상태 라벨. |  | inferred | med |  |  |
| `query_date_range.start_date` | date/datetime | 조회 대상 기간 시작일. |  | inferred | high |  |  |
| `query_date_range.end_date` | date/datetime | 조회 대상 기간 종료일. |  | inferred | high |  |  |
| `campaigns[].campaign_id` | string | 카카오 비즈메시지 캠페인 ID (예 CMP_KKO_20260415_001). 캠페인 식별 PK. |  | dict | high | 🔑 | ID 공간 채널 고유(CMP_KKO 프리픽스) — Meta/naver/CRM int 와 cross-join 불가(C5.1). I1 cluster. |
| `campaigns[].campaign_name` | string | 캠페인명 (한글, 예 '혜택형_봄세럼_1+1_4월중간'). |  | dict | high |  | 교차 연결은 ID 아닌 campaign_name/utm_campaign 매핑으로만(I1). |
| `campaigns[].campaign_type` | string | 캠페인 유형 (벤더/자사 분류 라벨). |  | inferred | med |  |  |
| `campaigns[].message_type` | string | 메시지 타입: FT=친구톡(광고/정보성, 채널 친구 한정), AT=알림톡(정보성, 비친구 포함). |  | vendor_doc | high |  | 벤더 확정: AlimTalk='AT', FriendTalk='ft'/'FT'. 친구톡=광고성→마케팅 동의 모집단, 알림톡=정보성→템플릿 승인 필요. |
| `campaigns[].template_code` | string | 비즈메시지 템플릿 코드 (등록·승인된 메시지 템플릿 식별, 예 CRM_BENEFIT_SPRING_SERUM_V2). |  | vendor_doc | high |  | 벤더 정의: '발송할 실제 메시지 유형으로 등록된 템플릿 코드'. AT는 사전 카카오 검수·승인 필요. |
| `campaigns[].template_name` | string | 템플릿 이름 (template_code 의 사람 읽는 라벨). |  | inferred | med |  |  |
| `campaigns[].sender_key` | string | 발신 프로필 키 (카카오톡 채널 개설 시 Biz 사이트에서 발급). |  | vendor_doc | high |  | 벤더 정의: 'Sender profile key — issued when opening channel at Biz site'. |
| `campaigns[].sender_no` | string | 발신번호 (발신 프로필에 연결된 발신 전화번호). |  | vendor_doc | med |  |  |
| `campaigns[].send_request_date` | date/datetime | 발송 요청 일시 (ISO 문자열, 예 2026-04-15T18:00:00). | datetime | dict | high |  | T10: requested 단계. TZ 라벨 없음(암묵 KST 가정). scheduled/sent/completed 와 단계 의미차. |
| `campaigns[].message_content.body` | string | 메시지 본문 텍스트. |  | inferred | high |  | 친구톡 본문 최대 1000자(벤더). |
| `campaigns[].message_content.button.name` | string | 버튼 제목 (CTA 라벨). |  | vendor_doc | high |  | 벤더 button.name='Button title'. |
| `campaigns[].message_content.button.type` | string | 버튼 기능 분류 (예 웹링크/앱링크). |  | vendor_doc | high |  |  |
| `campaigns[].message_content.button.url_mobile` | string | 모바일에서 버튼 클릭 시 이동 URL. |  | vendor_doc | high |  | 벤더 정의: 'URL to go to when a button is clicked in a mobile environment'. |
| `campaigns[].message_content.button.url_pc` | string | PC에서 버튼 클릭 시 이동 URL. |  | vendor_doc | high |  |  |
| `campaigns[].summary.target_recipients` | int | 발송 대상 수 (수신자 모집단). | 건 | dict | high |  | M1/M3: 톡톡 friends 와 비대칭. 시도수(M3)와 겹침 가능. 친구톡=마케팅동의 친구 모집단. |
| `campaigns[].summary.success_count` | int | 발송 성공 수 (요청 수락된 건). | 건 | classification | high |  | C6.5/M2: kakao success=요청수락(단계). crm/talktalk delivered(단말도달)와 동일 단계 단정 불가. |
| `campaigns[].summary.success_rate` | float | 발송 성공률 (%). | % | inferred | med |  | 분모(대상/시도) 미명시(C6.6). =success_count/target_recipients 추정. |
| `campaigns[].summary.fail_count` | int | 발송 실패 수. | 건 | inferred | high |  | §5#8: fail_count↔failed_count 철자 불일치(채널 간) 주의. |
| `campaigns[].summary.open_count` | int | 오픈(열람) 수. | 건 | dict | high |  |  |
| `campaigns[].summary.open_rate` | float | 오픈율 (%). | % | dict | high |  | M5/C6.6: 분모(대상/송달/시도) 미명시 — 채널 간 통합 시 왜곡. |
| `campaigns[].summary.click_count` | int | 클릭 수 (메시지/버튼 클릭). | 건 | dict | high |  | M6: 광고 clicks(노출 대비)와 동음이의 — 별 cluster. |
| `campaigns[].summary.click_rate` | float | 클릭율 (%, 발송/송달 대비 CTR). | % | dict | high |  | M7: 발송·송달 대비. CTOR(click_through_rate_open, 오픈 대비)와 분모 다름 — 분리 필수. |
| `campaigns[].summary.click_through_rate_open` | float | 오픈 대비 클릭율 CTOR (%, click/open). | % | classification | high |  | M8: 사전 미등재(인벤토리에만). click_rate(발송 대비)와 분모 달라 통합 시 합쳐질 위험 — _open 표기 보존. |
| `campaigns[].summary.conversion_count` | int | 전환 수 (메시지 attribution 기반). | 건 | dict | high |  | M9/C6.3-인접: attribution 모델 광고와 다름 — 광고 전환과 합산 금지. |
| `campaigns[].summary.conversion_rate_click` | float | 클릭 대비 전환율 (%). | % | inferred | med |  | §5#8: conversion_rate_click↔conversion_rate_from_click 명칭 불일치 주의. |
| `campaigns[].summary.conversion_amount_krw` | int | 전환 매출 (KRW). | KRW | dict | high |  | M10/C2.3: _krw 접미 명시(통화 안전). interest_alert 는 _krw 누락. |
| `campaigns[].summary.avg_order_value` | int | 평균 주문 금액 AOV (KRW). | KRW | dict | med |  | M12: avg_order_value 가 promotion/rfm/category 도메인에도 다수 존재 — join/혼동 금지. 메시징 한정 namespace 권장. |
| `campaigns[].summary.roi_percent` | float | ROI (%, 이익율). 예 2960 = 2960%. | % | classification | high |  | M11/C6.3: ROI≠ROAS(매출배수) — 절대 합치지 말 것. net/gross 산식 미명시(스케일 차 의심). |
| `campaigns[].summary.cost_per_message_krw` | int | 메시지 1건당 비용 (KRW). | KRW | inferred | med |  | 광고 CPC 아님(별 도메인). |
| `campaigns[].summary.total_cost_krw` | int | 총 발송 비용 (KRW). | KRW | classification | high |  | A1/T3: 광고비 cluster 에 편입되나 메시징 발송비(send cost) — 광고 spend/salesAmt 와 의미 결 다름. |
| `campaigns[].summary.revenue_per_message_krw` | float | 메시지 1건당 매출 (KRW). | KRW | inferred | med |  |  |
| `campaigns[].next` | bool | 캠페인 내 결과 페이징 — 다음 결과 존재 여부. |  | inferred | med |  | 최상위 next 와 동명(레벨 다름). |
| `campaigns[].total_count_in_db` | int | DB상 해당 캠페인 전체 발송 결과 건수 (results_sample 은 표본). |  | inferred | high |  | results_sample[] != 전수 — total_count_in_db 가 모집단 크기. |
| `campaigns[].results_sample_note` | string | results_sample 이 표본임을 알리는 주석 텍스트. |  | inferred | high |  |  |
| `campaigns[].results_sample[].uid` | string | 발송 결과 UID — 플랫폼이 부여한 메시지 키 ID (개별 발송 식별). |  | vendor_doc | high | 🔑 | 벤더 정의: uid='Message key ID'. 개별 발송 grain — summary 와 합산 금지(C7.1). |
| `campaigns[].results_sample[].cid` | string | 클라이언트 ID — 기업 고객이 정의한 키 ID(메시지 일련번호, 예 M2406032384-0415_001). |  | vendor_doc | high |  | 벤더 정의: cid='Defined Key ID by corporate customer'. 앞부분에 member_id 유사 토큰 포함하나 접미로 직접 join 불가(§5#15) — 파싱 규칙 검증 필요. |
| `campaigns[].results_sample[].phone_number_hash` | string | 수신자 전화번호 SHA256 해시 (평문 아님). |  | inferred | high |  | PII(완화): T11 해시공간·솔트 달라 join 불가. 원본=phone(벤더 phone_number=수신자 번호, 국가코드 82 포함). |
| `campaigns[].results_sample[].message_type` | string | 개별 발송 메시지 타입 (FT/AT, 캠페인 message_type 상속). |  | vendor_doc | high |  |  |
| `campaigns[].results_sample[].template_code` | string | 개별 발송에 사용된 템플릿 코드. |  | vendor_doc | high |  |  |
| `campaigns[].results_sample[].sender_key` | string | 개별 발송 발신 프로필 키. |  | vendor_doc | high |  |  |
| `campaigns[].results_sample[].code` | string | 개별 발송 결과 코드 (200=성공 등, 벤더 표준). |  | vendor_doc | high |  | 벤더: 200=Success/100=Processing/400~520=오류. 캠페인 래퍼 code 와 레벨 다름. |
| `campaigns[].results_sample[].code_detail.detail_code` | string | 개별 발송 상세 결과 코드 (예 NRM0000=성공, NRM1001=휴면 수신자). |  | dict | high |  | dict 명시: NRM0000=정상, NRM1001=휴면. 벤더 휴면(1년 미사용 계정)·차단 여부가 응답에 포함됨 확인. |
| `campaigns[].results_sample[].code_detail.detail_message` | string | 개별 발송 상세 메시지 (detail_code 동반 설명). |  | vendor_doc | high |  |  |
| `campaigns[].results_sample[].status` | string | 개별 발송 상태 (메시지 처리/송달 상태). |  | vendor_doc | med |  |  |
| `campaigns[].results_sample[].rcs_status` | string | RCS(Rich Communication Service) 대체 발송 상태 — 카카오 실패 시 RCS 대체 경로 결과. |  | vendor_doc | med |  | 벤더 BizMessage 는 카카오/RCS/SMS 대체 발송 지원 — rcs_status=RCS 폴백 단계 상태. |
| `campaigns[].results_sample[].reg_date` | date/datetime | 발송 접수(등록) 일시. | datetime | vendor_doc | high |  | 벤더 reg_date=메시지 등록/접수 타임스탬프. T10 단계: requested. |
| `campaigns[].results_sample[].send_date` | date/datetime | 실제 발송 일시. | datetime | inferred | med |  | T10 단계: sent. reg→send→result 3단계 시각. |
| `campaigns[].results_sample[].result_date` | date/datetime | 발송 결과 수신 일시 (단말 도달/실패 확정 시각). | datetime | vendor_doc | med |  | 벤더 ended_date='Date of message result reception' 대응. T10 단계: completed. |


## GA4 행동 — 세션/획득(traffic source) + 구매 전환 (session_start·first_visit·purchase)

### `ga4_traffic_source`

| 메타 | 값 |
|---|---|
| vendor | Google Analytics 4 (GA4) — BigQuery export (clumi 자체 mock raw, GA4 스키마 정합) |
| API/소스 | GA4 BigQuery export events_YYYYMMDD 테이블 (JSONL 변환). 원천 파일 clumi_mock_07_ga4_traffic_source.jsonl |
| 공식 doc | https://support.google.com/analytics/answer/7029846?hl=en |
| grain | 개별 웹 이벤트 1행 = 1 이벤트 (event-level). 세션 시작·첫 방문·구매 이벤트 중심. 일×캠페인 집계 아님. |
| family·format·rows | GA4 행동 — 세션/획득(traffic source) + 구매 전환 (session_start·first_visit·purchase) · jsonl · 38319 |
| PII | 없음 |

GA4 세션·획득 및 구매 전환 이벤트 스트림. 이벤트 3종: session_start 24000·first_visit 12496·purchase 1823. ga4_page_events와 동일한 GA4 BigQuery export 스키마(같은 컬럼 집합)이나 결을 분리: 이 테이블은 traffic_source 3계열(first-touch/collected/session last-click)과 구매(purchase) 이벤트가 실측 채워지는 쪽 — ecommerce.purchase_revenue(KRW)·purchase_revenue_in_usd(USD)·transaction_id(주문ID)·items[] 매출이 purchase 행에 존재. 커버 범위: 핵심 스칼라 + 중첩그룹 대표(traffic_source.*/collected_traffic_source.*/session_traffic_source_last_click.*/ecommerce.*/items[].*/device.*/geo.*/event_params[]). PII 없음(user_id=가명 회원ID).

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `event_date` | date(yyyymmdd) string | 이벤트가 기록된 일자 (YYYYMMDD 문자열) | YYYYMMDD | vendor_doc | high | 🔑 | 벤더 정의: registered timezone 기준. dict drift: 사전(file_no 7)은 'UTC' 주장. C4.2/T1: 타 채널 KST와 ±1일 silent misalign 위험. |
| `event_timestamp` | int | 이벤트가 GA4에 수신된 시각 (마이크로초 epoch, UTC) | microseconds since epoch (16자리) | vendor_doc | high |  | C3.1/T2: 마이크로초 — 초 epoch와 ×1e6 차(보정 누락=약 5만년 오차). |
| `event_name` | string | 이벤트명 (3종: session_start, first_visit, purchase) |  | vendor_doc | high | 🔑 | 이종 이벤트 3종 전수 스캔(인벤토리 note). ecommerce.*·items[] 매출 leaf는 purchase(1823행)에서만 채워짐 — 이벤트 필터 없이 합산 금지. |
| `event_value_in_usd` | float/null | 이벤트 'value' 파라미터의 USD 환산값 | USD | vendor_doc | high |  | page_events와 달리 일부 float 채워짐. C2/통화 함정 — purchase_revenue(KRW)와 다른 축이라 매출 cluster와 혼합 금지(§5 항목7). |
| `user_id` | null/string | 사용자에게 부여된 고유 ID = 로그인 회원 ID (비로그인 null) |  | classification | high | 🔑 | I4: GA4 user_id = 내부 member_id 동의어(명칭만 다름). C5.2: user_pseudo_id와 별 식별공간. null=비로그인. 가명키라 직접 PII 아님. |
| `user_pseudo_id` | string | GA4 가명 클라이언트 ID (쿠키 기반, {n}.{n} 형식) |  | classification | high | 🔑 | I5/C5.2: signup_events.ga_client_id 동의어. 회원당 N:1. member_id(user_id)와 혼동 금지. |
| `user_first_touch_timestamp` | int | 사용자가 사이트를 처음 방문한 시각 (마이크로초 epoch) | microseconds since epoch | vendor_doc | high |  | first_visit 이벤트와 정합. event_timestamp와 다른 사건. |
| `is_active_user` | bool | 해당 달력일 중 활성 사용자 여부 |  | vendor_doc | high |  |  |
| `stream_id` | string | 이벤트 발생 데이터 스트림의 숫자 ID |  | vendor_doc | high |  |  |
| `platform` | string | 이벤트 발생 플랫폼 (Web/IOS/Android) |  | vendor_doc | high |  |  |
| `device.category` | string | [중첩그룹 device.*] 디바이스 카테고리 (mobile/tablet/desktop) |  | vendor_doc | high |  | I14: GA4 값 도메인(mobile/desktop/tablet) vs 내부/naver 충돌. 그룹 leaf=page_events와 동일(category·operating_system(_version)·mobile_brand_name·mobile_model_name·language·is_limited_ad_tracking·time_zone_offset_seconds·web_info.browser(_version)·web_info.hostname). |
| `device.operating_system` | string | [중첩그룹 device.*] 디바이스 OS |  | vendor_doc | high |  |  |
| `device.web_info.browser` | string | [중첩그룹 device.web_info.*] 브라우저 |  | vendor_doc | high |  |  |
| `geo.country` | string | [중첩그룹 geo.*] 이벤트 보고 국가 (IP 기반) |  | vendor_doc | high |  | 그룹 leaf: continent·sub_continent·country·region·metro·city. |
| `geo.region` | string | [중첩그룹 geo.*] 이벤트 보고 지역/시도 (IP 기반, 영문) |  | vendor_doc | high |  | I13: 영문 — 내부 한글 광역과 매핑 필요. 접속지 기준. |
| `traffic_source.source` | string | [중첩그룹 traffic_source.* = user first-touch] 사용자를 처음 획득한 소스/네트워크 |  | classification | high |  | I8/주의21: user-level first-touch. 값 예 facebook/instagram/naver/(direct)/(not set) (dict file_no 7). collected(이벤트시점)·session last-click(세션)과 어트리뷰션 시점 다름 — 별개 의미. 그룹 leaf: name·medium·source. |
| `traffic_source.medium` | string | [중첩그룹 traffic_source.*] 사용자를 처음 획득한 매체 (cpc/shopping/brand/organic 등) |  | classification | high |  | I9: source/medium 입도 차. |
| `traffic_source.name` | string | [중첩그룹 traffic_source.*] 사용자를 처음 획득한 캠페인명 |  | vendor_doc | high |  | I10. |
| `session_traffic_source_last_click.cross_channel_campaign.default_channel_group` | string | [중첩그룹 session_traffic_source_last_click.cross_channel_campaign.* = 세션 last-click] 세션 last-click 기본 채널 그룹 (Paid Search/Paid Social/Direct/Organic Search/Referral/Email/Unassigned) |  | classification | med |  | I7(핵심 난관): GA4 규칙기반 표준 채널 그룹 vs 내부 orders.channel_attribution 세분 enum — 직접 동치 불가, 매핑사전 필요. 의미는 GA4 채널 그룹 정의(answer/9756891)로 확정(메인 스키마 표엔 미기재). cross_channel_campaign leaf: campaign_id(null)·campaign_name·source·medium·default_channel_group·primary_channel_group. |
| `session_traffic_source_last_click.cross_channel_campaign.source` | string | [중첩그룹 ...cross_channel_campaign.*] 세션 last-click 크로스채널 소스 |  | vendor_doc | high |  |  |
| `session_traffic_source_last_click.cross_channel_campaign.medium` | string | [중첩그룹 ...cross_channel_campaign.*] 세션 last-click 크로스채널 매체 |  | vendor_doc | high |  |  |
| `session_traffic_source_last_click.manual_campaign.campaign_name` | null/string | [중첩그룹 session_traffic_source_last_click.manual_campaign.*] 세션 last-click manual(utm) 캠페인명 |  | vendor_doc | high |  | manual_campaign leaf: campaign_id·campaign_name·source·medium·content·term·creative_format·marketing_tactic·source_platform. page_events 대비 manual_campaign.source/medium/content/term 일부 string 더 채워짐(획득 중심 데이터). |
| `collected_traffic_source.manual_source` | null/string | [중첩그룹 collected_traffic_source.* = 이벤트 수집 시점] 이벤트와 함께 수집된 manual source (utm_source) |  | vendor_doc | high |  | I8 'collected' 시점. 그룹 leaf: manual_source/_medium/_campaign_name/_content/_term(여기선 일부 string)·manual_campaign_id + gclid·dclid·srsltid(null). |
| `ecommerce.purchase_revenue` | int | [중첩그룹 ecommerce.*] 구매(purchase) 이벤트의 매출 (로컬 통화 = KRW) | KRW (local currency) | classification | high |  | T4: purchase 이벤트(1823행)에서만 채워짐(page_events는 전부 null=C6.8). orders.payment_amount와 정합(FK transaction_id). C2.1: purchase_revenue(KRW) vs purchase_revenue_in_usd(USD) ~1300배 — _in_usd 누락 인식 시 통화 혼합. 인벤토리 타입=int(원 단위 KRW). |
| `ecommerce.purchase_revenue_in_usd` | float | [중첩그룹 ecommerce.*] 구매 이벤트 매출의 USD 환산값 | USD | vendor_doc | high |  | C2.1/T4: 모든 *_in_usd 동형. KRW(int)와 다른 통화·타입(float). |
| `ecommerce.shipping_value` | int | [중첩그룹 ecommerce.*] 배송비 (로컬 통화 KRW) | KRW (local currency) | vendor_doc | high |  | shipping_value_in_usd(float/int) 병기. tax_value(_in_usd)도 동형. refund_value(_in_usd)는 mock null. |
| `ecommerce.tax_value` | int | [중첩그룹 ecommerce.*] 세금액 (로컬 통화 KRW) | KRW (local currency) | vendor_doc | high |  | tax_value_in_usd 병기. |
| `ecommerce.total_item_quantity` | int | [중첩그룹 ecommerce.*] 구매 이벤트 총 상품 수량 (items.quantity 합) | count | vendor_doc | high |  | unique_items와 짝. 그룹 leaf: purchase_revenue(_in_usd)·refund_value(_in_usd null)·shipping_value(_in_usd)·tax_value(_in_usd)·total_item_quantity·unique_items·transaction_id. |
| `ecommerce.transaction_id` | string | [중첩그룹 ecommerce.*] 이커머스 거래 ID = 주문 ID (purchase 이벤트만) |  | classification | high |  | I/FK: orders.order_id(20260401-0000001 형식)와 동치(dict file_no 7). page_events에서는 전부 null. |
| `items[].item_id` | string | [중첩배열 items[].*] 구매 상품 ID (purchase 이벤트 배열) |  | vendor_doc | high |  | items[]=반복 RECORD(purchase 시 채워짐). 대표 leaf: item_id·item_name·item_brand·item_category·price·price_in_usd·quantity·item_revenue(int)·item_revenue_in_usd(float)·coupon·affiliation. page_events 대비 item_revenue(_in_usd)가 실제 값(매출) 보유. |
| `items[].item_revenue` | int | [중첩배열 items[].*] 상품별 매출 (price × quantity, 로컬 통화 KRW) | KRW (local currency) | vendor_doc | high |  | C2.1: item_revenue(KRW int) vs item_revenue_in_usd(USD float). purchase 이벤트만(page_events는 null). |
| `items[].price` | float | [중첩배열 items[].*] 상품 단가 (로컬 통화 KRW) | KRW (local currency) | vendor_doc | high |  | price_in_usd(USD) 병기. |
| `items[].quantity` | int | [중첩배열 items[].*] 상품 수량 | count | vendor_doc | high |  |  |
| `privacy_info.analytics_storage` | string | [중첩그룹 privacy_info.*] Analytics 저장 동의 여부 (Yes/No/Unset) |  | vendor_doc | high |  | 그룹 leaf: ads_storage·analytics_storage·uses_transient_token. PII 아님. |
| `event_params[].key` | string | [중첩배열 event_params[].*] 이벤트 파라미터 이름 |  | vendor_doc | high |  | 관측 표준 key(dict file_no 7): ga_session_id(int_value, FK ga4_page_events.event_params[ga_session_id])·ga_session_number(int_value). I6: GA4 중첩 vs signup_events.ga_session_id 평면·타입(int↔str). |
| `event_params[].value.int_value` | int | [중첩배열 event_params[].value.*] 파라미터가 정수일 때의 값 (예: ga_session_id, ga_session_number) |  | vendor_doc | high |  | ga_session_id=세션 식별(Unix timestamp 초). I6. |
| `event_params[].value.string_value` | string | [중첩배열 event_params[].value.*] 파라미터가 문자열일 때의 값 |  | vendor_doc | high |  | value union 4종 중 하나만 채워짐. double_value(float)도 존재. |


## GA4 행동 — 페이지/상품 탐색 퍼널 (page_view·scroll·view_item·add_to_cart 등 9종, 결제 진입 단계 포함)

### `ga4_page_events`

| 메타 | 값 |
|---|---|
| vendor | Google Analytics 4 (GA4) — BigQuery export (clumi 자체 mock raw, GA4 스키마 정합) |
| API/소스 | GA4 BigQuery export events_YYYYMMDD 테이블 (JSONL 변환). 원천 파일 clumi_mock_08_ga4_page_events.jsonl |
| 공식 doc | https://support.google.com/analytics/answer/7029846?hl=en |
| grain | 개별 웹 이벤트 1행 = 1 이벤트 (event-level). 1 user_pseudo_id × 1 ga_session_id × N 이벤트. 일×캠페인 집계 아님. |
| family·format·rows | GA4 행동 — 페이지/상품 탐색 퍼널 (page_view·scroll·view_item·add_to_cart 등 9종, 결제 진입 단계 포함) · jsonl · 84143 |
| PII | 없음 |

GA4 웹 행동 이벤트 스트림(상품 탐색·장바구니·체크아웃 진입). 이벤트 9종: page_view 41913·scroll 12675·view_item 12421·view_item_list 8686·add_to_cart 3385·begin_checkout 1421·view_cart 1297·add_shipping_info 1211·add_payment_info 1134. GA4 BigQuery export 스키마(event/user/device/geo/ecommerce/items[]/event_params[]/traffic_source 3계열) 그대로. 커버 범위: 핵심 스칼라 + 중첩그룹 대표(device.*/geo.*/privacy_info.*/items[].*/ecommerce.*/event_params[]/collected_traffic_source.*/session_traffic_source_last_click.*). 이 테이블엔 결제 이벤트(purchase)가 없어 ecommerce.* 금액 leaf 실측 전부 null(C6.8) — 행동 퍼널 전용, 매출은 ga4_traffic_source 참조. PII 없음(user_id=가명 회원ID, IP·해시 미포함).

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `event_date` | date(yyyymmdd) string | 이벤트가 기록된 일자 (YYYYMMDD 문자열) | YYYYMMDD | vendor_doc | high | 🔑 | 벤더 정의: '등록 타임존' 기준 일자. dict drift: 데이터사전(file_no 8)은 'UTC' 주장 — GA4 공식은 property registered timezone. C4.2/T1: 타 채널(Meta/naver KST 영업일)과 ±1일 silent misalign 위험. 파싱 시 statDt/event_date=구분자 없는 8자리(C4.1). |
| `event_timestamp` | int | 이벤트가 GA4에 수신된 시각 (마이크로초 epoch, UTC) | microseconds since epoch (16자리) | vendor_doc | high |  | C3.1/T2: 마이크로초(16자리) — ad_change_history event_time_unix(초,10자리)와 ×1e6 차. 보정 누락 시 약 5만년 오차. UTC. |
| `event_name` | string | 이벤트명 (9종: page_view, scroll, view_item, view_item_list, add_to_cart, view_cart, begin_checkout, add_shipping_info, add_payment_info) |  | vendor_doc | high | 🔑 | 이종 이벤트 9종 전수 스캔(인벤토리 note). 이벤트별로 채워지는 event_params/items[]/ecommerce 필드가 다름 — 단정 join 금지. 결제(purchase) 없음. |
| `event_value_in_usd` | null | 이벤트 'value' 파라미터의 USD 환산값 | USD | vendor_doc | high |  | 실측 전부 null. 이벤트 가치(USD)는 event_params[key=value].value.double_value 로 들어오는 케이스 존재(dict file_no 8). C2/통화 함정 축. |
| `event_bundle_sequence_id` | int | 이벤트가 업로드된 번들의 순차 ID |  | vendor_doc | high |  | GA4 내부 업로드 메타. 분석 의미 낮음. |
| `event_server_timestamp_offset` | int | 수집 시각과 업로드 시각 간 오프셋 (마이크로초) | microseconds | vendor_doc | high |  |  |
| `user_id` | null/string | 사용자에게 부여된 고유 ID = 로그인 회원 ID (비로그인 null) |  | classification | high | 🔑 | I4: GA4 user_id = 내부 member_id(M{YYMM}{6digit})와 동일 cluster. 명칭만 다름(user_id↔member_id). C5.2: user_pseudo_id(익명 쿠키)와 절대 동일시 금지. null=비로그인(join 누락). 가명 회원키라 직접 PII 아님. |
| `user_pseudo_id` | string | GA4 가명 클라이언트 ID (쿠키 기반, {n}.{n} 형식) |  | classification | high | 🔑 | I5/C5.2: 익명 쿠키 ID — member_id(user_id)와 다른 식별 공간. 회원당 N:1(기기/브라우저별). signup_events.ga_client_id 와 동의어. 묶으면 회원↔익명 혼동. |
| `user_first_touch_timestamp` | int | 사용자가 사이트를 처음 방문한 시각 (마이크로초 epoch) | microseconds since epoch | vendor_doc | high |  | event_timestamp(현 이벤트)와 다른 사건(첫 방문). T2에서 별 instant로 분리 권장. |
| `is_active_user` | bool | 해당 달력일 중 한 번이라도 활성 사용자였는지 여부 |  | vendor_doc | high |  | GA4 active user 정의(engaged session 등) 기반 — 단순 이벤트 발생 여부 아님. |
| `stream_id` | string | 이벤트가 발생한 데이터 스트림의 숫자 ID |  | vendor_doc | high |  | GA4 web/app 스트림 식별. campaign_id 와 무관. |
| `platform` | string | 이벤트 발생 플랫폼 (Web/IOS/Android) |  | vendor_doc | high |  | clumi mock=웹 단일 추정. device.category(mobile/desktop/tablet)와 다른 축. |
| `device.category` | string | [중첩그룹 device.*] 디바이스 카테고리 (mobile/tablet/desktop) |  | vendor_doc | high |  | I14: 값 도메인 충돌 — GA4(mobile/desktop/tablet) vs 내부 orders(mobile_web/mobile_app/pc) vs naver(M/P). 통합 시 매핑 필요. 그룹 leaf: category·operating_system(_version)·mobile_brand_name·mobile_model_name·language·is_limited_ad_tracking·time_zone_offset_seconds·web_info.browser(_version)·web_info.hostname. |
| `device.operating_system` | string | [중첩그룹 device.*] 디바이스 OS (iOS/Android/Windows 등) |  | vendor_doc | high |  | operating_system_version 별도 leaf. |
| `device.web_info.browser` | string | [중첩그룹 device.web_info.*] 콘텐츠 조회 브라우저 (Chrome/Safari/Samsung Internet 등) |  | vendor_doc | high |  | web_info 하위: browser·browser_version·hostname. |
| `geo.country` | string | [중첩그룹 geo.*] 이벤트 보고 국가 (IP 기반) |  | vendor_doc | high |  | 그룹 leaf: continent·sub_continent·country·region·metro·city. 접속지 기준(거주/배송지 아님). |
| `geo.region` | string | [중첩그룹 geo.*] 이벤트 보고 지역/시도 (IP 기반, 영문) |  | vendor_doc | high |  | I13: 영문(Seoul, Gyeonggi-do) — 내부 customers.region(한글 광역)과 한↔영 매핑 필수. 접속지 vs 거주지 의미차. |
| `geo.city` | string | [중첩그룹 geo.*] 이벤트 보고 도시 (IP 기반) |  | vendor_doc | high |  |  |
| `traffic_source.source` | string | [중첩그룹 traffic_source.* = user 첫 획득(first-touch)] 사용자를 처음 획득한 소스/네트워크 |  | vendor_doc | high |  | I8/주의21: traffic_source.*=user-level first-touch(사용자 최초 획득). collected_traffic_source(이벤트 시점)·session_traffic_source_last_click(세션 last-click)과 어트리뷰션 시점 다름 — 합치면 의미 혼선. 그룹 leaf: name·medium·source. |
| `traffic_source.medium` | string | [중첩그룹 traffic_source.*] 사용자를 처음 획득한 매체 (cpc/organic/email 등) |  | vendor_doc | high |  | I9: source/medium 경계 — 채널 통합 시 입도 차 주의. |
| `traffic_source.name` | string | [중첩그룹 traffic_source.*] 사용자를 처음 획득한 캠페인명 |  | vendor_doc | high |  | I10: utm_campaign↔campaign_name 느슨 매핑. |
| `collected_traffic_source.manual_source` | null/string | [중첩그룹 collected_traffic_source.* = 이벤트 수집 시점 raw] 이벤트와 함께 수집된 manual source (utm_source) |  | vendor_doc | high |  | 이벤트 시점에 파싱된 utm 파라미터. 그룹 leaf: manual_source/_medium/_campaign_name/_campaign_id/_content/_term + gclid·dclid·srsltid(전부 null 多). I8 시점 3계열 중 'collected'. |
| `collected_traffic_source.manual_campaign_name` | null/string | [중첩그룹 collected_traffic_source.*] 이벤트와 함께 수집된 manual campaign (utm_campaign) |  | vendor_doc | high |  | I10. 대부분 null, 일부 string. |
| `collected_traffic_source.gclid` | null | [중첩그룹 collected_traffic_source.*] 이벤트와 함께 수집된 Google click ID |  | vendor_doc | high |  | mock 실측 전부 null. dclid/srsltid 동일(null). traffic_source가 (not set)일 때 gclid로 보정하는 용도. |
| `session_traffic_source_last_click.cross_channel_campaign.default_channel_group` | string | [중첩그룹 session_traffic_source_last_click.* = 세션 last-click] 세션 last-click의 기본 채널 그룹 (Paid Search/Paid Social/Direct/Organic Search/Referral/Email/Unassigned) |  | vendor_doc | med |  | I7: GA4 규칙기반 표준 채널 그룹 — 내부 orders.channel_attribution 세분 enum과 직접 동치 불가, 매핑사전 필요. default_channel_group은 메인 스키마 표엔 미기재이나 실 export·GA4 채널 그룹 정의(answer/9756891)로 의미 확정. primary_channel_group은 property 기본(primary) 그룹. |
| `session_traffic_source_last_click.cross_channel_campaign.source` | string | [중첩그룹 session_traffic_source_last_click.cross_channel_campaign.*] 세션 last-click 크로스채널 캠페인의 소스 |  | vendor_doc | high |  | cross_channel_campaign leaf: campaign_id(null 多)·campaign_name·source·medium·default_channel_group·primary_channel_group. |
| `session_traffic_source_last_click.cross_channel_campaign.medium` | string | [중첩그룹 ...cross_channel_campaign.*] 세션 last-click 크로스채널 캠페인의 매체 |  | vendor_doc | high |  |  |
| `session_traffic_source_last_click.cross_channel_campaign.campaign_name` | null/string | [중첩그룹 ...cross_channel_campaign.*] 세션 last-click 크로스채널 캠페인명 |  | vendor_doc | high |  | campaign_id는 거의 null — I10/주의21: GA4 캠페인 정본 모호. |
| `session_traffic_source_last_click.manual_campaign.campaign_name` | null/string | [중첩그룹 session_traffic_source_last_click.manual_campaign.*] 세션 last-click manual(utm) 캠페인명 |  | vendor_doc | high |  | manual_campaign leaf: campaign_id·campaign_name·source·medium·content·term·creative_format·marketing_tactic·source_platform (대부분 null). google_ads_campaign 별도(null). |
| `ecommerce.purchase_revenue` | null | [중첩그룹 ecommerce.*] 구매 이벤트의 매출 (로컬 통화 = KRW) | KRW (local currency) | vendor_doc | high |  | C6.8(최우선): page_events에는 purchase 이벤트가 없어 ecommerce 금액 leaf 실측 전부 null — '구조상 존재 ≠ 사용가능'(catalog≠code drift 동형). 매출 분석은 ga4_traffic_source.ecommerce.purchase_revenue 사용. C2.1: purchase_revenue(KRW) vs purchase_revenue_in_usd(USD) ~1300배 통화 함정. |
| `ecommerce.purchase_revenue_in_usd` | null | [중첩그룹 ecommerce.*] 구매 이벤트 매출의 USD 환산값 | USD | vendor_doc | high |  | C2.1/T4: 모든 *_in_usd 동형(통화 병기). page_events 전부 null. |
| `ecommerce.total_item_quantity` | int | [중첩그룹 ecommerce.*] 이벤트 내 총 상품 수량 (items.quantity 합) | count | vendor_doc | high |  | 금액 leaf는 null이나 수량 leaf(total_item_quantity·unique_items)는 commerce 이벤트(view_item/add_to_cart 등)에서 채워짐. 그룹 leaf 전체: purchase_revenue(_in_usd)·refund_value(_in_usd)·shipping_value(_in_usd)·tax_value(_in_usd)·transaction_id(전부 null) + total_item_quantity·unique_items(int). |
| `ecommerce.unique_items` | int | [중첩그룹 ecommerce.*] 이벤트 내 고유 상품 수 (item_id·item_name·item_brand 기준) | count | vendor_doc | high |  |  |
| `ecommerce.transaction_id` | null | [중첩그룹 ecommerce.*] 이커머스 거래 ID |  | vendor_doc | high |  | page_events 전부 null(구매 없음). ga4_traffic_source에서는 string=주문ID(orders.order_id FK). |
| `items[].item_id` | string | [중첩배열 items[].*] 이벤트에 포함된 상품 ID |  | vendor_doc | high |  | items[]=반복 RECORD(view_item/add_to_cart 등 상품 이벤트). 그룹 대표 leaf: item_id·item_name·item_brand·item_category(2~5 null)·item_variant(null)·price·price_in_usd(float)·quantity(int)·item_revenue(_in_usd null)·coupon·affiliation·item_list_id/_index/_name·promotion_*(null)·creative_*(null). 빈배열도 존재(array(empty)). |
| `items[].item_name` | string | [중첩배열 items[].*] 상품명 |  | vendor_doc | high |  |  |
| `items[].price` | float | [중첩배열 items[].*] 상품 단가 (로컬 통화 = KRW) | KRW (local currency) | vendor_doc | high |  | C2.1: price(KRW) vs price_in_usd(USD) 병기. item_revenue·item_revenue_in_usd는 page_events에서 null(매출 없음). |
| `items[].quantity` | int | [중첩배열 items[].*] 상품 수량 (미지정 시 1) | count | vendor_doc | high |  |  |
| `privacy_info.analytics_storage` | string | [중첩그룹 privacy_info.*] Analytics 저장 동의 여부 (Yes/No/Unset) |  | vendor_doc | high |  | consent 상태. 그룹 leaf: ads_storage·analytics_storage·uses_transient_token. PII 아님(동의 플래그). |
| `privacy_info.ads_storage` | string | [중첩그룹 privacy_info.*] 광고 타게팅 저장 동의 여부 (Yes/No/Unset) |  | vendor_doc | high |  |  |
| `event_params[].key` | string | [중첩배열 event_params[].*] 이벤트 파라미터 이름 |  | vendor_doc | high |  | event_params[]=반복 RECORD(key + value union). 관측 표준 key(dict file_no 8): ga_session_id(int_value)·ga_session_number(int_value)·page_location(string_value)·percent_scrolled(int_value, scroll만)·value(double_value, USD). 평탄화 시 key 필터 필수(I6: GA4 중첩 vs signup_events 평면). |
| `event_params[].value.string_value` | string | [중첩배열 event_params[].value.*] 파라미터가 문자열일 때의 값 (예: page_location URL) |  | vendor_doc | high |  | value union 4종 중 하나만 채워짐. |
| `event_params[].value.int_value` | int | [중첩배열 event_params[].value.*] 파라미터가 정수일 때의 값 (예: ga_session_id, percent_scrolled) |  | vendor_doc | high |  | ga_session_id=세션 식별(I6, FK ga4_traffic_source.event_params[ga_session_id]). |
| `event_params[].value.double_value` | float | [중첩배열 event_params[].value.*] 파라미터가 double일 때의 값 (예: value=이벤트 가치 USD) |  | vendor_doc | high |  | float_value leaf는 GA4 공식상 '현재 미사용'이라 인벤토리에도 부재. |


## ad_audit_log

### `ad_change_history`

| 메타 | 값 |
|---|---|
| vendor | Meta |
| API/소스 | Meta Marketing API — Ad Account Activities (change history) (/{ad-account-id}/activities) |
| 공식 doc | https://developers.facebook.com/docs/marketing-api/reference/ad-activity/ |
| grain | 변경 이벤트 단위 (50 이벤트, 계정 변경 감사 로그) |
| family·format·rows | ad_audit_log · json (wrapper: data[]=50, _meta, paging) · 50 |
| PII | ⚠ 포함 |

Meta 광고 계정의 변경 이력(감사 로그). 누가(actor) 무엇을(object) 언제 어떻게 바꿨는지 이벤트 단위로 기록. 데이터 지표가 아닌 운영 변경 추적용. event_type(create_campaign/update_campaign_budget/update_ad_run_status 등 Meta 표준 + 자사 internal_audit_log_added)·object_type(CAMPAIGN/AD_SET/AD/PLAN/REPORT)으로 분기. 같은 instant 가 event_time(UTC ISO)·event_time_unix(초 epoch)·date_time_in_timezone(KST 슬래시) 3중 인코딩(T2/C4.3). extra_data 는 JSON 문자열(파싱 필요). actor_name 등 인명 포함 → PII. wrapper._meta 는 mock 부가 메타. 커버: data[].* + _meta.* + paging 전 leaf.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `data[].event_time` | date | 변경 발생 시각 (UTC ISO 8601, 예 2026-04-01T00:01:23+0000) |  | vendor_doc | high |  | T2/C4.3: 같은 instant 의 UTC ISO 인코딩. event_time_unix·date_time_in_timezone 와 동일 시각 3중 표현. |
| `data[].event_time_unix` | int | 변경 시각 epoch (초 단위, 10자리 추정) | seconds since epoch | inferred | med |  | C3.1: GA4 event_timestamp(마이크로초 16자리)와 단위 다름. §5 미결 — 초/ms 자릿수 실측 권장(현재 '초 추정'). |
| `data[].date_time_in_timezone` | string | 변경 시각 현지시각 표기 (KST, 슬래시 포맷, 예 2026/04/01 09:01:23 KST) |  | dict | high |  | T2/C4.3: KST 라벨 명시. ISO/epoch 와 다른 포맷 — 파싱 분기 필요. |
| `data[].event_type` | string | 이벤트 타입 (Meta 표준: create_campaign, update_campaign_budget, update_ad_run_status 등 + 자사 internal_audit_log_added) |  | vendor_doc | high |  | Activity API 표준 event_type. internal_audit_log_added 는 clumi 자사 증강(비표준). |
| `data[].translated_event_type` | string | 이벤트 타입 한글 설명 (예 'Campaign 일일 예산 변경', '내부 BI: 주간 리뷰') |  | dict | high |  | Meta 가 제공하는 사람용 번역 필드. |
| `data[].object_id` | string | 변경 대상 객체 ID (object_type 에 따라 campaign/ad_set/ad ID) |  | vendor_doc | high | 🔑 | I1/T9/조건부 FK: object_type=CAMPAIGN 일 때만 campaign_id 와 동치(C5.1 ID 공간). PLAN/REPORT 등은 별 공간 — 무조건 join 시 오염. |
| `data[].object_name` | string | 변경 대상 객체 이름 (예 CLUMI_SPR_PROSP_Serum) |  | vendor_doc | high |  | I2: object_type=CAMPAIGN 일 때 campaign_name 과 loose link. |
| `data[].object_type` | string | 변경 대상 타입 (CAMPAIGN / AD_SET / AD / PLAN / REPORT) |  | vendor_doc | high |  | object_id/object_name 해석의 분기 키. join 전 필수 필터. |
| `data[].actor_id` | string | 변경 수행 사용자 ID (Meta 사용자 ID) |  | vendor_doc | high |  | PII: 개인 식별자. |
| `data[].actor_name` | string | 변경 수행자 이름 (예 Park Marketing) |  | vendor_doc | high |  | PII: 평문 인명 — pii_flag=true 근거. |
| `data[].application_id` | string | 변경에 사용된 앱 ID (null=내부 BI/수동) |  | dict | high |  | nullable. null 이면 내부 도구. |
| `data[].application_name` | string | 변경 도구 이름 (예 Meta Business Suite, null 가능) |  | dict | high |  | nullable. |
| `data[].extra_data` | string | 변경 상세 (JSON 직렬화 문자열, 파싱 필요. 예 {"old_daily_budget":"275000",...}) |  | vendor_doc | high |  | 구조화 페이로드가 string 으로 임베드 — 사용 전 JSON 파싱. 예산 변경 전/후 값 등. |
| `_meta.ad_account_id` | string | (wrapper mock 메타) 조회 광고 계정 ID |  | dict | high |  | meta_ads_*.account_id 와 동일 계정. _meta 는 clumi mock 이 부착한 조회 컨텍스트(Graph API 표준 아님). |
| `_meta.query_date_range.since` | date | (wrapper mock 메타) 조회 기간 시작일 |  | inferred | high |  |  |
| `_meta.query_date_range.until` | date | (wrapper mock 메타) 조회 기간 종료일 |  | inferred | high |  |  |
| `_meta.source` | string | (wrapper mock 메타) 데이터 출처 라벨 |  | inferred | med |  |  |
| `_meta.total_events` | int | (wrapper mock 메타) 총 이벤트 수 | count | inferred | high |  | data[] 행수(50)와 일치 기대. |
| `paging.cursors.after` | string | 다음 페이지 커서 |  | vendor_doc | high |  | 페이지네이션 메타. |
| `paging.cursors.before` | string | 이전 페이지 커서 |  | vendor_doc | high |  |  |


## ad_performance_daily

### `daily_performance`

| 메타 | 값 |
|---|---|
| vendor | self_mock_demo |
| API/소스 | data/clumi/raw/daily_performance.csv (자체 mock 일×캠페인×채널 성과 집계) |
| 공식 doc | https://support.google.com/google-ads/answer/2472714 |
| grain | 일 × 캠페인 × 소재 × 채널 1행 |
| family·format·rows | ad_performance_daily · csv · 32 |
| PII | 없음 |

자체 mock 일별 광고 성과 집계 테이블. date×campaign_id×creative_id×channel 단위로 노출/클릭/전환/광고비/전환매출 raw 카운트와 파생지표(cpa/cpc/cpm/ctr/cvr/roas)를 동시 보유. 분류 §5 item13 '채널 통합·집계 완료 파생 테이블' — ad_cost·conversions·conversion_revenue 가 canonical 영어명. roas/ctr/cvr=% 표기. 사전 미등재.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `date` | date | 집계 일자 (YYYY-MM-DD) | date | inferred | high | 🔑 | 분류 §T1: 본 테이블=YYYY-MM-DD(구분자 有). naver statDt·GA4 event_date(YYYYMMDD)와 포맷 충돌. KST 영업일 가정(GA4 UTC와 ±1일 misalign 주의). |
| `campaign_id` | string | 캠페인 ID (FK→campaigns.campaign_id) |  | inferred | high | 🔑 | 내부 네임스페이스(BRP/SRC). 외부채널 join 불가(§C5.1). |
| `creative_id` | string | 소재 ID (FK→creatives.creative_id) |  | inferred | high | 🔑 | 분류 §I3 내부 소재 식별자. |
| `channel` | string | 광고 채널 (google/naver 등 추정 enum) |  | inferred | med | 🔑 | 분류 §I7/item20: 값셋 미확정 — orders.channel_attribution 과 도메인 대조 필요. |
| `impressions` | integer | 노출수 (건) | count | vendor_doc | high |  | 분류 §A2/T6. raw 68200. |
| `clicks` | integer | 클릭수 (건) | count | vendor_doc | high |  | 분류 §A3/T7. raw 2980. |
| `conversions` | integer | 전환수 (건) | count | vendor_doc | high |  | 분류 §A4/T8 canonical 전환수. raw 96. naver ccnt·Meta actions[].omni_purchase 와 동의어이나 attribution 모델 다름 — 합산 주의. |
| `ad_cost` | integer | 광고비 (KRW) | KRW | classification | high |  | 분류 §A1/T3 canonical 광고비. raw 1525440. naver salesAmt(비용 함정 §C6.1)의 정제 후 정본 이름 — 이름=의미 일치. |
| `conversion_revenue` | integer | 전환 매출 (KRW) | KRW | classification | high |  | 분류 §A5/T4 canonical 전환매출. raw 6133793. naver convAmt 의 정제 후 정본. ad_cost(비용)와 짝 — 뒤섞임 금지. |
| `cpc` | integer | 클릭당 비용 CPC (KRW) | KRW | vendor_doc | high |  | 분류 §A8. raw 512. |
| `cpm` | integer | 1000노출당 비용 CPM (KRW) | KRW | vendor_doc | high |  | 분류 §A9. raw 22367. |
| `cpa` | integer | 전환당 비용 CPA (KRW) | KRW | vendor_doc | high |  | raw 15890. = ad_cost/conversions. |
| `ctr` | number | 클릭률 (%) | percent | vendor_doc | high |  | 분류 §A7. raw 4.37 → %. |
| `cvr` | number | 전환율 (%) = 전환/클릭 | percent | vendor_doc | high |  | 분류 §A10. raw 3.22 → %. |
| `roas` | number | 광고비 대비 매출 ROAS (%) | percent | classification | high |  | raw 402.1 → % 표기(배수 아님, §A6/C1.1). = conversion_revenue/ad_cost×100. Meta 배수와 합산 시 ÷100. |


## analytics/category-sales

### `category_sales`

| 메타 | 값 |
|---|---|
| vendor | Cafe24 (자사 분석 산출) |
| API/소스 | Cafe24 주문 → 자사 카테고리별 매출 집계 CSV (다중 카테고리 분배 적용) |
| 공식 doc | https://developers.cafe24.com/docs/en/api/admin/#order |
| grain | stat_date × category = 1행 (월별 '2026-04' + 일별 '2026-04-XX' 혼재 = 155행) |
| family·format·rows | analytics/category-sales · csv · 155 |
| PII | 없음 |

카테고리별 매출 집계 산출(stat_date × category). 155행 = 월별 집계행('2026-04')과 일별 집계행('2026-04-XX') 혼재. Cafe24 주문을 자사 로직으로 카테고리 분배(다중 카테고리 주문은 분수 분배 → order_count/product_quantity 소수)·신규/재구매 분해. 인벤토리 18컬럼 전수 커버. dict(file_no 12)는 일부 컬럼만 기재(category_lv2/category_name/refund_count/refund_amount/new_buyer_amount/repeat_buyer_amount 는 dict 미기재 drift).

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `stat_date` | date/datetime | 집계 일자. '2026-04'=월별, '2026-04-15'=일별 혼재. | date(month or day) | dict | high | 🔑 | PK part(+category). 월/일 grain 혼재 — 합산 전 grain 분리 필수(classification 결산형 vs 운영형). |
| `category_lv1` | string | 카테고리 1단계(한글). 스킨케어/클렌징/마스크팩/자외선차단/기타. |  | dict | high | 🔑 | FK(loose)→orders.product_categories. PK part. |
| `category_lv2` | string | 카테고리 2단계(한글, 하위 분류). |  | inferred | med |  | dict drift: dict 미기재, 인벤토리 존재. |
| `category_code` | string | 카테고리 코드(C001-C005). |  | dict | high |  |  |
| `category_name` | string | 카테고리 표시명. |  | inferred | med |  | dict drift: dict 미기재, 인벤토리 존재. category_lv1 과 동의 가능. |
| `order_count` | string | 주문 수(다중 카테고리 분수 분배 → 소수 가능). | count(fractional) | dict | high |  | 예 1097.1. 분배로 소수. raw string. |
| `order_amount` | date(yyyymmdd)/string | 카테고리 매출. | KRW | dict | med |  | classification §5-5: 인벤토리가 8자리 금액을 date(yyyymmdd)로 오파싱한 것으로 추정. 실제는 금액(KRW). raw string 우선. |
| `product_quantity` | string | 상품 수량(분수 분배). | count(fractional) | dict | high |  | 예 2213.9. |
| `unique_buyers` | string | 유니크 구매자 수. | count | dict | high |  |  |
| `avg_order_value` | string | 평균 주문 금액. | KRW | dict | high |  | classification M12: avg_order_value 도메인 전반 다수 — 혼동 금지. |
| `new_buyer_count` | string | 신규 구매자 수. | count | dict | high |  |  |
| `new_buyer_amount` | date(yyyymmdd)/string | 신규 구매자 매출. | KRW | inferred | med |  | dict drift: dict 미기재. 8자리 금액 date 오파싱 의심(§5-5). |
| `repeat_buyer_count` | string | 기존(재구매) 구매자 수. | count | dict | high |  |  |
| `repeat_buyer_amount` | date(yyyymmdd)/string | 기존 구매자 매출. | KRW | inferred | med |  | dict drift: dict 미기재. 금액 date 오파싱 의심. |
| `refund_count` | string | 환불 건수. | count | inferred | med |  | dict drift: dict 미기재, 인벤토리 존재. |
| `refund_amount` | string | 환불 금액. | KRW | inferred | med |  | dict drift: dict 미기재, 인벤토리 존재. |
| `top_product_name` | string | 카테고리 대표 상품명. |  | dict | high |  |  |
| `share_pct` | string | 매출 비중(%). | percent | dict | high |  | 예 56.59. 전 카테고리 합 100% 기준. |


## analytics/customer-grade-history

### `customer_grade_history`

| 메타 | 값 |
|---|---|
| vendor | Cafe24 (자사 분석 산출) |
| API/소스 | Cafe24 회원 등급 변동 이력 → 자사 스냅샷 산출 CSV (월말 등급 추정 재구성) |
| 공식 doc | https://developers.cafe24.com/docs/en/api/admin/#customers |
| grain | 회원 × snapshot_date(월말) = 1행 (등급 시계열 스냅샷) |
| family·format·rows | analytics/customer-grade-history · csv · 30379 |
| PII | 없음 |

회원 등급의 월말 스냅샷 시계열(member × snapshot_date). 30,379행 = 회원 다수 × 여러 월. 직전 등급 대비 변경 여부와 시점 누적 주문/매출(추정) 포함. Cafe24 직접 제공 이력이 아니라 자사가 등급을 시점별로 재구성한 산출물(cumulative_* 는 '추정' 명시). 인벤토리 7컬럼 전수 커버.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `member_id` | string | 회원 ID. |  | dict | high | 🔑 | FK→customers.member_id. PK part(+snapshot_date). |
| `snapshot_date` | date/datetime | 스냅샷 일자(월말). | date | dict | high | 🔑 | 예 2026-04-30. PK part. |
| `grade` | string | 해당 시점 회원 등급. WELCOME/REGULAR/SILVER/GOLD/VIP. |  | dict | high |  | dict drift/값셋 불일치: customers.member_grade 는 BASIC, 여기는 REGULAR(classification I11★). 등급 통합 시 라벨 정합 선결. |
| `previous_grade` | string | 직전 스냅샷 시점 등급. |  | dict | high |  | nullable(첫 스냅샷). |
| `is_grade_change` | string | 직전 시점 대비 등급 변경 여부(1/0). | 0/1 boolean | dict | high |  | raw string. grade≠previous_grade 일 때 1. |
| `cumulative_orders` | string | 해당 시점까지 누적 주문 수(추정). | count | dict | med |  | dict: '추정' 명시(자사 재구성). 주문 실집계 아닐 수 있음. |
| `cumulative_amount_krw` | string | 해당 시점까지 누적 매출(추정). | KRW | dict | med |  | dict: '추정' 명시. |


## analytics/customer-rfm

### `customer_rfm`

| 메타 | 값 |
|---|---|
| vendor | Cafe24 (자사 분석 산출) |
| API/소스 | Cafe24 주문/회원 원천 → 자사 RFM·CLV 분석 파이프라인 산출 CSV (벤더 직제공 아님) |
| 공식 doc | https://developers.cafe24.com/docs/en/api/admin/#order |
| grain | 회원 1명 × snapshot_date = 1행 (스냅샷 누계) |
| family·format·rows | analytics/customer-rfm · csv · 8500 |
| PII | 없음 |

회원별 RFM/세그먼트/CLV 분석 산출 테이블(snapshot_date 기준 누계, 8500명 = customers 동일 모집단). Cafe24 직제공 필드가 아니라 주문/회원 원천을 자사 분석 로직으로 가공한 파생물 → source 대부분 dict/inferred. recency·frequency·monetary 와 점수(1-5), RFM 코드/세그먼트, 등급, 예측 CLV·이탈위험·재구매성향 포함. 인벤토리 18컬럼 전수 커버.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `member_id` | string | 회원 ID. |  | dict | high | 🔑 | PK(+snapshot_date). FK→customers.member_id(8500 전원). |
| `snapshot_date` | date/datetime | RFM 계산 기준일. | date | dict | high | 🔑 | 예: 2026-04-30. |
| `recency_days` | string | 마지막 주문 후 경과일. | days | dict | high |  | nullable(미구매=NULL). customers.last_order_date 기반. |
| `frequency` | string | 누적 주문 수(= customers.total_orders). | count | dict | high |  | classification A12: customer_rfm.frequency=구매빈도, Meta frequency(노출빈도)와 동음이의 — 분리. |
| `monetary_krw` | string | 누적 구매액(= customers.total_purchase_amount). | KRW | dict | high |  |  |
| `r_score` | string | R(Recency) 점수 1-5(0=미구매). | score 0-5 | dict | high |  | raw string(tinyint 직렬화). |
| `f_score` | string | F(Frequency) 점수 1-5(0=미구매). | score 0-5 | dict | high |  |  |
| `m_score` | string | M(Monetary) 점수 1-5(0=미구매). | score 0-5 | dict | high |  |  |
| `rfm_score` | string | RFM 3자리 코드. 예 533. |  | dict | high |  | r_score·f_score·m_score 연결. |
| `rfm_segment` | string | 11 표준 RFM 세그먼트. Champions/Loyal Customers/At Risk/Lost/Never Purchased 등. |  | dict | high |  | promotions.target_segment 와 매핑. |
| `customer_tier` | string | RFM 기반 고객 등급. Platinum/Gold/Silver/Bronze/Inactive. |  | dict | high |  | classification I11★: customers.member_grade(운영, WELCOME/BASIC/...)와 다른 축 — 묶으면 오염. |
| `avg_order_value` | string | 평균 주문 금액(monetary/frequency). | KRW | dict | high |  | classification M12: avg_order_value 가 promotion/category/messaging 도메인에도 다수 존재 → join/혼동 금지. |
| `first_order_date` | date/datetime | 첫 주문 일시. | datetime | dict | high |  | nullable(미구매). |
| `last_order_date` | date/datetime | 마지막 주문 일시. | datetime | dict | high |  | nullable. customers.last_order_date 와 동일 의미. |
| `days_as_customer` | string | 회원 가입 후 경과일. | days | dict | high |  |  |
| `predicted_clv_krw` | string | 추정 CLV(M × F × retention 모델 산출). | KRW | dict | med |  | 자사 예측 산출(추정값). 관측 매출 아님. |
| `churn_risk_score` | string | 이탈 위험 점수 0-100. | score 0-100 | dict | med |  | 자사 모델 산출. |
| `next_purchase_propensity` | string | 다음 구매 확률 점수 0-100. | score 0-100 | dict | med |  | 자사 모델 산출. |


## analytics/household-segment

### `household_structure`

| 메타 | 값 |
|---|---|
| vendor | Cafe24 (자사 분석 산출) |
| API/소스 | Cafe24 회원/주문 → 자사 가구 유형 추정 집계 CSV |
| 공식 doc | https://developers.cafe24.com/docs/en/api/admin/#customers |
| grain | 가구 유형(household_type_code) × snapshot_date = 1행 (12 유형 집계) |
| family·format·rows | analytics/household-segment · csv · 12 |
| PII | 없음 |

가구 유형별 세그먼트 분석 집계(12 유형). 회원수·비중·구매자/재구매자·구매율/재구매율·총매출·회원당/구매자당 평균매출·평균가구원·TOP지역·선호카테고리·핵심페르소나·마케팅시사점. 회원 인구통계(나이/결혼/가구원)를 자사 로직으로 가구 유형 추정(가중치 분배 → estimated 일부)한 파생물. preferred_category·primary_persona·marketing_implication 은 정성 추정(분석가 노트). 인벤토리 18컬럼 전수 커버. dict(file_no 19)는 member_count/purchaser_count/total_revenue_krw 를 별도 행(file_no 19 household)으로 기재 + estimated_member_count/avg_purchase_per_member_krw 명칭이 인벤토리(member_count/avg_revenue_per_member_krw)와 drift.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `household_type_code` | string | 가구 유형 코드(HT01-HT10 등). |  | dict | high | 🔑 | PK(+snapshot_date). |
| `household_type` | string | 가구 유형(한글). '1인 청년(18-34)', '부부+어린자녀' 등. |  | dict | high |  |  |
| `snapshot_date` | date/datetime | 집계 기준일. | date | dict | high | 🔑 | PK part. |
| `member_count` | string | 해당 가구 유형 회원 수(실제 값). | count | dict | high |  | dict drift: dict 메인행은 estimated_member_count(추정/가중분배)로 기재, 인벤토리·dict 보조행은 member_count(실제). raw member_count 채택. |
| `member_share_pct` | string | 회원 비중(%). | percent | dict | high |  | 전 유형 합 100%. |
| `purchaser_count` | string | 구매한 회원 수. | count | dict | high |  |  |
| `purchase_rate_pct` | string | 구매율(%)= purchaser/member. | percent | inferred | med |  | dict drift: dict 미기재, 인벤토리 존재. |
| `repurchaser_count` | string | 재구매 회원 수. | count | inferred | med |  | dict drift: dict 미기재, 인벤토리 존재. |
| `repurchase_rate_pct` | string | 재구매율(%). | percent | dict | high |  | 예 12.43. |
| `total_revenue_krw` | date(yyyymmdd)/string | 가구 유형별 총 매출(3월+4월 활성). | KRW | dict | med |  | classification §5-5: 8자리 금액 date(yyyymmdd) 오파싱 의심. 실제 KRW. raw string 우선. |
| `avg_revenue_per_member_krw` | string | 회원당 평균 구매액. | KRW | dict | high |  | dict drift: dict=avg_purchase_per_member_krw, raw=avg_revenue_per_member_krw. |
| `avg_revenue_per_purchaser_krw` | string | 구매자당 평균 구매액. | KRW | inferred | med |  | dict drift: dict 미기재, 인벤토리 존재. 분모가 purchaser(member 아님). |
| `avg_household_size` | string | 평균 가구원 수. | persons | dict | high |  | customers.household_size 와 도메인 연결. |
| `top_region` | string | TOP 지역(한글). 예 경기. |  | dict | high |  | FK(loose)→customers.region. classification I13 region cluster. |
| `top_region_share_pct` | string | TOP 지역 비중(%). | percent | inferred | med |  | dict drift: dict 미기재, 인벤토리 존재. |
| `preferred_category` | string | 선호 카테고리(정성 추정). '기초 세럼, 클렌징, 자외선차단' 등. |  | dict | med |  | 정성 추정값(분석가 노트). FK(loose)→category_sales.category_lv1. |
| `primary_persona` | string | 핵심 페르소나 설명(정성). |  | dict | med |  | 정성 텍스트(분석가 작성). |
| `marketing_implication` | string | 마케팅 시사점(분석가 노트, 정성). |  | dict | med |  | 정성 텍스트 — 관측 데이터 아님(주의: 분석 결론을 데이터로 오인 금지). |


## analytics/promotion-performance

### `promotion_performance`

| 메타 | 값 |
|---|---|
| vendor | Cafe24 (자사 분석 산출) |
| API/소스 | Cafe24 프로모션 사용 → 자사 성과 집계 SQL (promotions.sql 내 3테이블 중 1) |
| 공식 doc | https://developers.cafe24.com/docs/en/api/admin/#coupons |
| grain | promotion × snapshot_date = 1행 (집계) |
| family·format·rows | analytics/promotion-performance · sql · 5 |
| PII | 없음 |

프로모션별 성과 집계(promotion × snapshot_date). 사용건수/유니크사용자/매출/할인총액/신규·기존고객/전환율/ROI. Cafe24 주문·사용이력을 자사 로직으로 집계한 파생물. 인벤토리 SQL 14컬럼 전수 커버(INSERT 토큰 제외). dict(file_no 11)는 existing_customer_count/performance_id/created_at 미기재(drift).

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `performance_id` | int | 성과 레코드 ID. |  | inferred | med | 🔑 | dict drift: dict 미기재. PK(surrogate). |
| `promotion_id` | int | 프로모션 ID. |  | dict | high | 🔑 | FK→promotions.promotion_id. |
| `promotion_code` | varchar(50) | 프로모션 코드. |  | inferred | high |  | dict drift: dict 이 행에 미기재. promotions.promotion_code 와 일치(denormalized). |
| `snapshot_date` | date | 집계 기준일. | date | dict | high | 🔑 | PK part. 예 2026-04-30. |
| `total_usage_count` | int | 총 사용 건수. | count | dict | high |  | promotions.total_usage_limit(한도)와 구분. |
| `unique_users_count` | int | 유니크 사용자 수. | count | dict | high |  |  |
| `total_revenue` | bigint | 프로모션 적용 주문 매출 합. | KRW | dict | high |  | _krw 접미 없으나 KRW(classification C2.3 통화 명시 함정). |
| `total_discount_given` | bigint | 총 할인 제공액. | KRW | dict | high |  |  |
| `avg_order_value` | int | 평균 주문 금액. | KRW | dict | high |  | classification M12: avg_order_value 도메인 다수 — 혼동 금지. |
| `new_customer_count` | int | 신규 고객 사용 수. | count | dict | high |  |  |
| `existing_customer_count` | int | 기존 고객 사용 수. | count | inferred | high |  | dict drift: dict 미기재(dict 은 new_customer_count 만). unique_users = new + existing 추정. |
| `conversion_rate` | decimal(5,2) | 전환율(%). | percent | dict | med |  | 분모(노출/대상) 미명시 — 자사 정의. |
| `roi_percent` | decimal(8,2) | ROI(%). 예 481.14. | percent | dict | high |  | classification C6.3/M11★: ROI(이익)≠ROAS(매출) — 광고 ROAS 와 절대 합치지 말 것. |
| `created_at` | datetime | 레코드 생성 일시. | datetime | inferred | med |  | dict drift: dict 미기재. |


## budget_plan

### `budget_allocation`

| 메타 | 값 |
|---|---|
| vendor | self_mock_demo |
| API/소스 | data/clumi/raw/budget_allocation.csv (자체 mock 예산 배분 계획) |
| 공식 doc | https://support.google.com/google-ads/answer/6385083 |
| grain | 세그먼트(=campaign_type) 1행 — 채널별 예산 배분 계획 |
| family·format·rows | budget_plan · csv · 5 |
| PII | 없음 |

자체 mock 예산 배분 계획 테이블. 세그먼트(브랜드/신제품/리타겟/검색/SNS)별로 채널 예산(meta/kakao/naver/google_budget)과 총예산(total_budget), 집행률(exec_rate)을 보유. 전 budget 컬럼은 계획값(관측 성과 아님). 인벤토리 type='date(yyyymmdd)' 는 8자리 숫자 오파싱 — raw 직독 결과 정수 KRW(분류 §5 item5). 사전 미등재.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `segment` | string | 예산 세그먼트 (한글: 브랜드/신제품/리타겟/검색/SNS) |  | inferred | high | 🔑 | campaign_type 와 1:1 매핑되는 한글 라벨로 추정. |
| `campaign_type` | string | 캠페인 유형 (brand/product/retargeting/search/sns) |  | inferred | high |  | segment 의 영문 코드. campaigns.campaign_type 와 동일 enum 도메인 추정. |
| `exec_rate` | number | 예산 집행률 (%) | percent | inferred | med |  | raw 92.4 → % (집행액/계획액). 0~100 범위. |
| `meta_budget` | integer | Meta 채널 배정 예산 (KRW) | KRW | classification | high |  | 인벤토리 type='date(yyyymmdd)' 오파싱(§5 item5). raw 정수 KRW(12000000) → integer. |
| `kakao_budget` | integer | Kakao 채널 배정 예산 (KRW) | KRW | classification | high |  | date 오파싱 정정 — integer KRW(6000000). |
| `naver_budget` | integer | Naver 채널 배정 예산 (KRW) | KRW | classification | high |  | date 오파싱 정정 — integer KRW(18000000). |
| `google_budget` | integer | Google 채널 배정 예산 (KRW) | KRW | classification | high |  | date 오파싱 정정 — integer KRW(29000000). |
| `total_budget` | integer | 세그먼트 총 예산 (KRW) | KRW | classification | high |  | date 오파싱 정정 — integer KRW(65000000). 주의: 채널 예산 합과 불일치할 수 있음(raw: 12M+6M+18M+29M=65M 일치하나 행마다 검증 필요). |


## campaign_master

### `campaigns`

| 메타 | 값 |
|---|---|
| vendor | self_mock_demo |
| API/소스 | data/clumi/raw/campaigns.csv (자체 mock 캠페인 마스터) |
| 공식 doc | https://support.google.com/google-ads/answer/2375420 |
| grain | 캠페인 1행 (캠페인 마스터, 기간=start_date~end_date) |
| family·format·rows | campaign_master · csv · 12 |
| PII | 없음 |

자체 mock 캠페인 마스터 테이블. 캠페인별 목표·소유자·상태·제품·기간·월예산·목표지표(target_cpa/target_roas/target_conversions)를 보유. 내부 campaign_id(BRP-NNN/SRC-NNN) 네임스페이스 — 외부 광고채널 ID와 join 불가(분류 §I1/C5.1). target_* 컬럼은 관측치 아닌 계획값(분류 §5 item22 목표값 도메인). 사전(clumi_data_dictionary) 미등재 — 의미는 컬럼명 추론+raw 직독.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `campaign_id` | string | 캠페인 고유 ID (내부 형식 BRP-NNN·SRC-NNN) |  | inferred | high | 🔑 | 내부 네임스페이스. Meta 18자리/naver cmp-/advoost GFA 와 별 ID 공간 — cross-channel join 불가(§C5.1). creatives.campaign_id·daily_performance.campaign_id 와 내부 FK. |
| `name` | string | 캠페인명 (한글, 예: 루미 7주년 감사제) |  | inferred | high |  | 분류 §I2: campaigns.name=캠페인명. creatives.name(소재명)과 동명 컬럼이나 다른 의미 — 혼동 금지(§C6.9). |
| `goal` | string | 캠페인 목표 (한글 자유서술, 예: 브랜드 인지도 + 매출) |  | inferred | med |  | campaign_type(brand/product 등 enum)과 별개의 정성 목표 서술. |
| `owner` | string | 캠페인 담당자명 (한글 인명) |  | inferred | high |  | 내부 담당자 이름. demo mock 가상 인물 — 실 PII 아님(pii_flag=false). |
| `status` | string | 캠페인 상태 (active 등) |  | inferred | high |  |  |
| `product` | string | 대상 제품 (한글, 예: 전 제품·인기 TOP10) |  | inferred | high |  |  |
| `campaign_type` | string | 캠페인 유형 (brand/product/retargeting/search/sns 추정 enum) |  | inferred | med |  | budget_allocation.campaign_type 와 동일 enum 도메인으로 추정 — 값 대조 권장. |
| `start_date` | date | 캠페인 시작일 (YYYY-MM-DD) | date | inferred | high |  |  |
| `end_date` | date | 캠페인 종료일 (YYYY-MM-DD) | date | inferred | high |  |  |
| `monthly_budget` | integer | 월 예산 (KRW) | KRW | classification | high |  | 인벤토리 type='date(yyyymmdd)' 는 8자리 숫자 오파싱(분류 §5 item5). raw 직독=정수 KRW(25000000) → integer 채택. |
| `target_cpa` | integer | 목표 CPA = 전환당 목표 비용 (KRW) | KRW | vendor_doc | high |  | 목표·계획값(관측치 아님, §5 item22). CPA 정의=총비용/전환수. raw 15000~18000. |
| `target_roas` | number | 목표 ROAS (%) | percent | classification | high |  | 목표값(§5 item22). raw 300~350 → % 표기(배수 아님). 분류 §A6/C1.1 % 컨벤션. Meta 배수와 합산 시 ÷100. |
| `target_conversions` | integer | 목표 전환수 (건) | count | vendor_doc | med |  | 목표값(§5 item22). raw 350~500. |


## commerce/customer-master

### `customers`

| 메타 | 값 |
|---|---|
| vendor | Cafe24 |
| API/소스 | Cafe24 자사몰 회원 (Admin REST API Customers resource 원천 → 자사 ETL CSV) |
| 공식 doc | https://developers.cafe24.com/docs/en/api/admin/#customers |
| grain | 회원 1명 = 1행 (member-level 현재 상태 스냅샷) |
| family·format·rows | commerce/customer-master · csv · 8500 |
| PII | ⚠ 포함 |

Cafe24 자사몰 회원 마스터(현재 상태 스냅샷, 8500명 = customer_rfm 와 동일 모집단). 인구통계(나이/성별/지역/가구)·가입정보(채널/디바이스/UTM)·마케팅 동의·누적 주문/구매액·등급·적립금·해시 PII 포함. 인벤토리 30컬럼 전수 커버. dict 의 membership_grade/membership_point 는 인벤토리상 member_grade/available_point 로 명칭 drift(raw 채택). PII: member_name_hash·member_phone_hash·member_email.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `member_id` | string | 회원 ID(M{YYMM}{6digit}). 전 테이블 join 허브. |  | dict | high | 🔑 | PK. classification I4★: GA4 는 user_id 명칭 차. |
| `member_email` | string | 회원 이메일(평문). PII. |  | inferred | med |  | dict drift: dict 미기재, 인벤토리에 존재. 평문 이메일 추정 → PII. |
| `member_name_hash` | string | 회원 이름 SHA256 해시. PII(가명처리). |  | inferred | med |  | classification T11: 해시 공간/솔트 달라 cross-table join 불가. |
| `member_phone_hash` | string | 회원 전화번호 SHA256 해시. PII(가명처리). |  | inferred | med |  | classification T11 PII 해시 cluster. |
| `member_grade` | string | 회원 운영 등급. WELCOME/BASIC/SILVER/GOLD/VIP. |  | dict | high |  | dict drift: dict=membership_grade, raw=member_grade. classification I11★: 운영 등급 vs RFM customer_tier 다른 축. grade_history 는 REGULAR 값셋 사용(불일치). |
| `member_status` | string | 회원 상태(활성/휴면/탈퇴 등). |  | inferred | med |  | dict drift: dict 미기재, 인벤토리 존재. Cafe24 회원 상태 추정. |
| `age` | string | 만 나이(2026 기준). | years | dict | high |  | raw string. dict(file_no 6 추가행)에서 integer 로 기술되나 인벤토리 string. |
| `age_group` | string | 연령대 버킷. 18-24/25-34/35-44/45-54/55-64/65+. |  | dict | high |  | classification I12: meta_ads_by_age.age 와 버킷 호환(의미는 개인속성 vs 광고차원). |
| `birth_year` | string | 출생연도. | year | inferred | med |  | dict drift: dict 미기재. age 와 정합. |
| `gender` | string | 성별. F/M. |  | dict | high |  | classification §5: 단일출처(동의어 군집 미형성). |
| `region` | string | 지역(광역, 한글). 서울/경기 등 17개. |  | dict | high |  | classification I13: 한글 vs 영문(GA4 geo.region) 매핑 필요. 거주지 vs 접속지 구분. |
| `marital_status` | string | 결혼 여부. single/married/divorced. |  | dict | high |  | household_structure.household_type 매핑(loose). |
| `household_size` | string | 가구원 수(1/2/3/4+). | count | dict | high |  | household_structure.avg_household_size 와 도메인 연결. |
| `signup_date` | date/datetime | 가입 일시(KST). | KST datetime | dict | high |  | signup_events.signup_timestamp 와 join(4월 신규). |
| `signup_channel` | string | 가입 채널. email/kakao/naver. |  | dict | high |  |  |
| `signup_device` | string | 가입 시 디바이스. mobile_web/mobile_app/pc. |  | dict | high |  | classification I14 device 값셋 충돌. |
| `signup_utm_source` | string | 가입 시 utm_source. meta/naver/kakao. |  | dict | high |  | classification I8: signup_ 접두 맥락 보존. |
| `signup_utm_medium` | string | 가입 시 utm_medium. instagram/cpc 등. |  | dict | high |  |  |
| `signup_utm_campaign` | string | 가입 시 utm_campaign. |  | dict | high |  | nullable_seen=true. |
| `marketing_email_agree` | string | 이메일 마케팅 동의(1/0). | 0/1 boolean | dict | high |  | raw string. |
| `marketing_sms_agree` | string | SMS 마케팅 동의(1/0). | 0/1 boolean | dict | high |  |  |
| `marketing_kakao_agree` | string | 카카오 마케팅 동의(1/0). | 0/1 boolean | dict | high |  |  |
| `total_orders` | string | 누적 주문 수. | count | dict | high |  | customer_rfm.frequency 와 동일값(= frequency). |
| `total_purchase_amount` | string | 누적 구매액. | KRW | dict | high |  | customer_rfm.monetary_krw 와 동일값. |
| `last_order_date` | date/datetime | 마지막 주문 일시. | KST datetime | dict | high |  | nullable(주문 0건). customer_rfm.recency_days 산정 기준. |
| `last_login_date` | date/datetime | 마지막 로그인 일시. | KST datetime | inferred | med |  | dict drift: dict 미기재, 인벤토리 존재. |
| `available_point` | string | 보유 적립금. | KRW(point) | dict | high |  | dict drift: dict=membership_point, raw=available_point. |
| `created_at` | date/datetime | 레코드 생성 일시(통상 signup_date 근접). | datetime | inferred | med |  | dict drift: dict 미기재. |
| `updated_at` | date/datetime | 레코드 최종 수정 일시. | datetime | inferred | med |  | dict drift: dict 미기재. |


## commerce/promotion-master

### `promotions`

| 메타 | 값 |
|---|---|
| vendor | Cafe24 (자사몰) |
| API/소스 | Cafe24 자사몰 프로모션/쿠폰 마스터 SQL (promotions.sql 내 3테이블 중 1) |
| 공식 doc | https://developers.cafe24.com/docs/en/api/admin/#coupons |
| grain | 프로모션 1건 = 1행 (promotion master, 1001-1005) |
| family·format·rows | commerce/promotion-master · sql · 5 |
| PII | 없음 |

프로모션/쿠폰 마스터(5건, promotion_id 1001-1005). promotions.sql 내 3테이블(promotions/promotion_performance/promotion_usage_history) 중 정의 테이블. 유형·할인방식·할인값·최소주문·최대할인·대상세그먼트·적용상품·사용한도·활성여부. 인벤토리 SQL DDL 17컬럼 전수 커버(INSERT 토큰은 파서 잡음 — 컬럼 아님, 제외). dict(file_no 11)는 max_discount_amount/max_usage_per_user/total_usage_limit/created_at/updated_at 미기재(drift).

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `promotion_id` | int | 프로모션 ID(1001-1005). |  | dict | high | 🔑 | PK. promotion_performance/usage_history 와 join. |
| `promotion_code` | varchar(50) | 프로모션 코드. SPRING_SERUM_1+1 등. |  | dict | high |  | alt key. orders.promotion_code·usage_history.promotion_code join. |
| `promotion_name` | varchar(200) | 프로모션명(한글). |  | dict | high |  |  |
| `promotion_type` | varchar(30) | 프로모션 유형. PRODUCT_BUNDLE/PERCENT_DISCOUNT/FIXED_AMOUNT/FREE_SHIPPING. |  | dict | high |  | discount_type 과 의미 중첩(고수준 유형). |
| `discount_type` | varchar(20) | 할인 방식. PERCENT/FIXED/BUNDLE_PERCENT/BUY_X_GET_Y. |  | dict | high |  | discount_value 해석 기준(PERCENT면 %, FIXED면 KRW). |
| `discount_value` | int | 할인율 또는 금액. 15/30(%) 또는 5000(KRW). | percent or KRW | dict | high |  | 단위가 discount_type 에 의존 — 단독 해석 함정. |
| `start_date` | datetime | 프로모션 시작 일시. | datetime | dict | high |  |  |
| `end_date` | datetime | 프로모션 종료 일시. | datetime | dict | high |  |  |
| `min_order_amount` | int | 최소 주문 금액(적용 조건). | KRW | dict | high |  |  |
| `max_discount_amount` | int | 최대 할인 한도 금액. | KRW | inferred | med |  | dict drift: dict 미기재, 인벤토리 SQL 존재. PERCENT 할인 상한 추정. |
| `target_segment` | varchar(50) | 대상 세그먼트. ALL/NEW_CUSTOMER_FIRST_ORDER 등. |  | dict | high |  | customer_rfm.rfm_segment 매핑. |
| `applicable_products` | text | 적용 상품(콤마 구분 또는 ALL). |  | dict | high |  |  |
| `max_usage_per_user` | int | 사용자당 최대 사용 횟수. | count | inferred | med |  | dict drift: dict 미기재, SQL 존재. |
| `total_usage_limit` | int | 전체 사용 한도(발급 총량). | count | inferred | med |  | dict drift: dict 미기재, SQL 존재. promotion_performance.total_usage_count(실사용)와 구분. |
| `is_active` | tinyint(1) | 활성 여부(1/0). | 0/1 boolean | dict | high |  |  |
| `created_at` | datetime | 레코드 생성 일시. | datetime | inferred | med |  | dict drift: dict 미기재. |
| `updated_at` | datetime | 레코드 최종 수정 일시. | datetime | inferred | med |  | dict drift: dict 미기재. |


## commerce/promotion-usage

### `promotion_usage_history`

| 메타 | 값 |
|---|---|
| vendor | Cafe24 (자사몰) |
| API/소스 | Cafe24 자사몰 프로모션 사용 이력 SQL (promotions.sql 내 3테이블 중 1) |
| 공식 doc | https://developers.cafe24.com/docs/en/api/admin/#coupons |
| grain | 프로모션 사용 1건(주문 적용) = 1행 (event-level) |
| family·format·rows | commerce/promotion-usage · sql · None |
| PII | 없음 |

프로모션 사용 이력(사용 1건 = 1행, 주문에 코드 적용 시점). 회원·주문·사용일시·할인액·주문금액·첫주문여부·주문상태. orders 와 order_id 로 1:1~N:1 연결. 인벤토리 SQL 10컬럼 전수 커버(INSERT 토큰 제외). row_count 는 인벤토리 SQL 파싱상 미산출(null) — promotion_performance.total_usage_count 합과 정합 추정.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `usage_id` | bigint | 사용 이력 ID. |  | dict | high | 🔑 | PK. |
| `promotion_id` | int | 프로모션 ID. |  | inferred | high |  | dict drift: dict 이 행에 미기재(dict 은 promotion_code 만). FK→promotions.promotion_id. |
| `promotion_code` | varchar(50) | 프로모션 코드. |  | dict | high |  | FK→promotions.promotion_code. |
| `member_id` | varchar(20) | 회원 ID(비회원 적용 시 NULL 가능). |  | dict | high |  | FK→customers.member_id. |
| `order_id` | varchar(20) | 주문 ID. |  | dict | high |  | FK→orders.order_id. |
| `used_at` | datetime | 사용 일시. | datetime | dict | high |  | orders.order_date 와 정합. |
| `discount_amount` | int | 할인액. | KRW | dict | high |  | orders.discount_amount 와 정합. |
| `order_amount` | int | 주문 금액(결제액). | KRW | dict | high |  | orders.payment_amount 와 정합. |
| `is_first_order` | tinyint(1) | 첫 주문 여부(1/0). | 0/1 boolean | inferred | high |  | dict drift: dict 미기재, SQL 존재. orders.is_first_order 와 정합. |
| `order_status` | varchar(20) | 주문 상태(Cafe24 코드). N/C 계열. |  | inferred | med |  | dict drift: dict 미기재, SQL 존재. orders.order_status 와 동일 코드군(C40=취소 등 — 취소 시 할인 환원 판별용). |


## commerce/signup-event

### `signup_events`

| 메타 | 값 |
|---|---|
| vendor | Cafe24 (자사몰) + GA4 연계 |
| API/소스 | Cafe24 자사몰 회원가입 이벤트 로그 (가입 폼 + GA4 세션 결합) CSV |
| 공식 doc | https://developers.cafe24.com/docs/en/api/admin/#customers |
| grain | 가입 이벤트 1건 = 1행 (event-level; 600건 = 4월 신규 가입) |
| family·format·rows | commerce/signup-event · csv · 600 |
| PII | ⚠ 포함 |

회원가입 이벤트 로그(이벤트 단위, 600건 = 2026-04 신규 가입자). 가입 채널/디바이스/OS/브라우저·UTM·GA4 세션 연계(ga_session_id/ga_client_id)·지오·해시 PII(ip_hash)·가입 방식/폼버전·첫방문~가입 경과·프로모션·가입가치 포함. 인벤토리 31컬럼 전수 커버. dict(file_no 9)는 signup_timestamp 를 datetime 으로, 인벤토리는 date/datetime. 인벤토리에만 geo_city/landing_page/created_at 존재(dict 미기재 drift). dict 가 기재한 first_visit_source 는 인벤토리 존재 일치.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `signup_event_id` | string | 가입 이벤트 ID(SE{YYMM}{8digit}). |  | dict | high | 🔑 | PK. |
| `member_id` | string | 회원 ID. |  | dict | high | 🔑 | FK→customers.member_id(4월 신규 한정). |
| `signup_timestamp` | date/datetime | 가입 일시(KST). | KST datetime | dict | high |  | customers.signup_date 와 join. |
| `created_at` | date/datetime | 레코드 생성 일시. | datetime | inferred | med |  | dict drift: dict 미기재, 인벤토리 존재. |
| `signup_channel` | string | 가입 채널. email/kakao/naver. |  | dict | high |  | customers.signup_channel 와 일치. |
| `signup_device` | string | 가입 디바이스. mobile_web/mobile_app/pc. |  | dict | high |  |  |
| `signup_method` | string | 가입 방식(소셜 로그인 분류). email/naver_login/kakao_login/google_login. |  | dict | high |  | signup_channel 보다 세분. |
| `signup_form_version` | string | 회원가입 폼 버전. v1.3/v1.4. |  | dict | high |  |  |
| `device_os` | string | OS. iOS/Android 등. |  | dict | high |  |  |
| `browser` | string | 브라우저. Safari/Chrome/C:LUMI App 등. |  | dict | high |  |  |
| `user_agent` | string | User-Agent 풀텍스트. |  | dict | high |  |  |
| `ip_hash` | string | IP SHA256 해시. PII(가명처리). |  | dict | high |  | classification T11 PII 해시. |
| `geo_country` | string | 국가(영문). |  | inferred | med |  | dict drift: dict 미기재(인벤토리 존재). South Korea 추정. |
| `geo_region` | string | 지역(영문). 예 Seoul. |  | dict | high |  | classification I13: 영문 — customers.region(한글) 매핑 필요. ga4 geo.region 과 join. |
| `geo_city` | string | 도시(영문). |  | inferred | med |  | dict drift: dict 미기재, 인벤토리 존재. |
| `utm_source` | string | UTM source. meta/naver/kakao. |  | dict | high |  | orders.utm_source 와 동일 의미. |
| `utm_medium` | string | UTM medium. instagram/cpc 등. |  | dict | high |  |  |
| `utm_campaign` | string | UTM campaign. |  | dict | high |  | nullable. |
| `utm_content` | string | UTM content. |  | inferred | med |  | dict drift: dict 미기재, 인벤토리 존재(nullable). |
| `utm_term` | string | UTM term(검색어). |  | inferred | med |  | dict drift: dict 미기재, 인벤토리 존재(nullable). |
| `referrer` | string | 유입 referrer URL. |  | inferred | med |  | dict drift: dict 미기재(nullable). |
| `landing_page` | string | 가입 시 랜딩 페이지 URL. |  | inferred | med |  | dict drift: dict 미기재, 인벤토리 존재. |
| `first_visit_source` | string | 첫 방문 채널. instagram/naver 등. |  | dict | high |  | utm_source(가입시점)와 구분되는 첫터치 출처. |
| `days_from_first_visit` | string | 첫 방문~가입 경과일(즉시=0). | days | dict | high |  | raw string. |
| `ga_session_id` | string | GA4 세션 ID. |  | dict | high |  | classification I6: ga4 event_params[ga_session_id](int) 와 타입 차(여기 str). |
| `ga_client_id` | string | GA4 user_pseudo_id(쿠키 클라이언트 ID, {n}.{n}). |  | dict | high |  | classification I5★: ga_client_id↔user_pseudo_id 동일 개념. member_id(회원)와 절대 동일 cluster 금지. |
| `has_promotion_code` | string | 가입 시 프로모션 코드 사용 여부(1/0). | 0/1 boolean | dict | high |  | raw string. |
| `promotion_code_used` | string | 사용한 프로모션 코드. FRIEND_5000/WELCOME_NEW 등. |  | dict | high |  | FK(loose)→promotions.promotion_code. nullable. |
| `event_value_krw` | string | 가입 가치(GA4 sign_up 이벤트값). | KRW | dict | high |  | GA4 부여 이벤트 가치(추정값). |
| `marketing_email_agree` | string | 이메일 마케팅 동의(1/0). | 0/1 boolean | dict | high |  | dict drift: dict(file_no 9)는 customers 에만 명시했으나 인벤토리상 signup_events 에도 존재. |
| `marketing_sms_agree` | string | SMS 마케팅 동의(1/0). | 0/1 boolean | inferred | med |  | dict drift: dict signup_events 미기재, 인벤토리 존재. |
| `marketing_kakao_agree` | string | 카카오 마케팅 동의(1/0). | 0/1 boolean | inferred | med |  | dict drift: dict signup_events 미기재, 인벤토리 존재. |


## commerce/transaction

### `orders`

| 메타 | 값 |
|---|---|
| vendor | Cafe24 |
| API/소스 | Cafe24 자사몰 주문 (Admin REST API Orders resource 원천 → 자사 ETL CSV) |
| 공식 doc | https://developers.cafe24.com/docs/en/api/admin/#order |
| grain | 주문 1건 = 1행 (order-level, 일별 발생; 라인아이템 아님) |
| family·format·rows | commerce/transaction · csv · 3420 |
| PII | ⚠ 포함 |

Cafe24 자사몰 주문 헤더 테이블. 주문 1건당 1행(라인아이템은 top_product_name/product_categories 로 요약). 금액·할인·결제수단·UTM/채널 귀속(last-click)·디바이스 포함. 인벤토리 실측 26컬럼 전수 커버. dict 가 기재한 region/customer_age_group/customer_gender/guest_email_hash 는 인벤토리 미관측(drift) → 제외. 인벤토리에만 있는 referrer/used_point/created_at/updated_at 는 dict 미기재(drift). 인벤토리상 모든 숫자/금액 컬럼이 string 타입(자사 ETL 직렬화).

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `order_id` | string | 주문 ID. YYYYMMDD-NNNNNNN 형식(11~16자). |  | dict | high | 🔑 | PK. promotion_usage_history.order_id, ga4 ecommerce.transaction_id 와 join. |
| `member_id` | string | 회원 ID(M{YYMM}{6digit}). 비회원 주문은 NULL. |  | dict | high | 🔑 | FK→customers.member_id. nullable_seen=true(비회원). dict 의 guest_email_hash 는 인벤토리 미관측. |
| `order_date` | date/datetime | 주문 일시(KST). | KST datetime | dict | high |  |  |
| `created_at` | date/datetime | 레코드 생성 일시. 통상 order_date 와 동일/근접. | datetime | inferred | med |  | dict drift: dict 미기재, 인벤토리에만 존재. Cafe24 ETL 메타 타임스탬프 추정. |
| `updated_at` | date/datetime | 레코드 최종 수정 일시(상태변경 등). | datetime | inferred | med |  | dict drift: dict 미기재, 인벤토리에만 존재. |
| `order_status` | string | 주문 상태(Cafe24 코드). N계열=정상 처리 흐름, C계열=취소 흐름. 관측 예: N10, N40, C40. |  | vendor_doc | med |  | Cafe24 classic 코드군: N00 입금전 / N10 상품준비중 / N20 배송준비중 / N30 배송중 / N40 배송완료 / C00·C40 취소. dict drift: dict 가 N10=신규 라 적었으나 Cafe24 공식 N10=상품준비중. 코드값은 mall 설정 가능(고정 enum 아님). |
| `is_first_order` | string | 신규 회원의 첫 주문 여부(1=신규). | 0/1 boolean | dict | high |  | raw string('1'/'0'). |
| `payment_amount` | string | 실 결제 금액(할인·배송비 반영 후). | KRW | dict | high |  | Cafe24 actual_payment_amount 대응. raw string. |
| `product_amount` | string | 상품 정가 합(할인 전). | KRW | dict | high |  | raw string. product_amount - discount_amount + shipping_fee - used_point ≈ payment_amount 관계. |
| `discount_amount` | string | 할인액(프로모션/쿠폰). | KRW | dict | high |  | promotion_usage_history.discount_amount 와 join. |
| `used_point` | string | 사용한 적립금. | KRW(point) | inferred | med |  | dict drift: dict 미기재, 인벤토리에만 존재. customers.available_point 와 도메인 일치. |
| `shipping_fee` | string | 배송비. | KRW | dict | high |  |  |
| `items_count` | string | 주문 상품 종류 수(UNIQUE SKU 수). | count | dict | high |  | total_quantity(총수량)와 구분. |
| `total_quantity` | string | 주문 총 수량. | count | dict | high |  |  |
| `top_product_name` | string | 주문 내 대표(첫 번째) 상품명. |  | dict | high |  | 주문 라인아이템 미보유 → 대표 1개만. |
| `product_categories` | string | 주문 상품 카테고리(콤마 구분, 한글). |  | dict | high |  | FK(loose)→category_sales.category_lv1. 다중 카테고리 콤마 join. |
| `payment_method` | string | 결제수단. card/kakaopay/naverpay/payco/account_transfer. |  | dict | high |  |  |
| `device_type` | string | 주문 디바이스. mobile_web/mobile_app/pc. |  | dict | high |  | classification I14: 내부 값셋(web/app 구분) vs GA4(mobile/desktop/tablet) vs naver(M/P) 충돌. |
| `channel_attribution` | string | 주문 발생 채널(last-click 귀속). meta_facebook/meta_instagram/naver_*/kakao_message/direct/organic_search/oliveyoung/unknown 등. |  | dict | high |  | classification I7★: orders 세분 enum vs GA4 표준 channel_group 직접 동치 불가, 매핑사전 필요. |
| `promotion_code` | string | 적용 프로모션 코드. |  | dict | high |  | FK→promotions.promotion_code. nullable(미적용). |
| `utm_source` | string | UTM source(주문 시점). meta/naver/kakao/oliveyoung/(direct)/(not set). |  | dict | high |  | classification I8: 값 입도(meta 통합 vs facebook/instagram 분리) 충돌. |
| `utm_medium` | string | UTM medium. facebook/instagram/cpc/shopping/brand/message/referral/organic. |  | dict | high |  | classification I9: utm_medium 에 facebook 값 — source/medium 경계 혼탁. |
| `utm_campaign` | string | UTM campaign. CLUMI_SPR_PROSP_Serum, CRM_BENEFIT_SPRING_SERUM 등. |  | dict | high |  | campaign_name↔campaign_id 느슨 매핑(I10). |
| `utm_content` | (미관측) | UTM content(소재 변형 식별). 인벤토리에서 값 미관측(전부 null/공백 추정). |  | dict | low |  | dict drift: dict 정의 존재하나 인벤토리 types=(미관측). 컬럼은 있으나 실값 없음. |
| `utm_term` | (미관측) | UTM term(검색어). 인벤토리에서 값 미관측. |  | dict | low |  | dict drift: 정의 존재·실값 미관측. orders.utm_term→naver_searchad.kwd join 의도. |
| `referrer` | (미관측) | 유입 referrer URL. 인벤토리에서 값 미관측. |  | inferred | low |  | dict drift: dict 미기재, 인벤토리에 컬럼만 존재하고 값 미관측. |


## creative_master

### `creatives`

| 메타 | 값 |
|---|---|
| vendor | self_mock_demo |
| API/소스 | data/clumi/raw/creatives.csv (자체 mock 소재 마스터+집계지표) |
| 공식 doc | https://support.google.com/google-ads/answer/1722124 |
| grain | 소재(크리에이티브) 1행 (캠페인 기간 누적 집계지표 포함) |
| family·format·rows | creative_master · csv · 12 |
| PII | 없음 |

자체 mock 소재(크리에이티브) 마스터. 소재 메타(headline/body/format/image_url/landing_url)와 누적 성과지표(cpa/cpc/ctr/cvr/roas)를 함께 보유. roas/ctr/cvr 는 % 표기. campaign_id로 campaigns에, creative_id로 daily_performance·ab_tests에 연결. 분류 §I3: creative_id 는 내부 2테이블(creatives·daily_performance) 공유 식별자. 사전 미등재 — 의미=컬럼명 추론+§6 율 스케일.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `creative_id` | string | 소재 고유 ID (내부 형식 CR-NNN) |  | inferred | high | 🔑 | 분류 §I3 내부 소재 식별자. daily_performance.creative_id, ab_tests.variant_a/variant_b 가 이 값 참조. |
| `campaign_id` | string | 소속 캠페인 ID (FK→campaigns.campaign_id) |  | inferred | high |  | 내부 네임스페이스(BRP-NNN). 외부채널 join 불가(§C5.1). |
| `name` | string | 소재명 (한글, 예: 7주년 메인 비주얼) |  | inferred | high |  | 분류 §I2/C6.9: 소재명 — campaigns.name(캠페인명)과 동명이지만 다른 의미. 캠페인명 cluster 편입 금지. |
| `headline` | string | 광고 헤드라인 (한글) |  | inferred | high |  |  |
| `body` | string | 광고 본문 카피 (한글) |  | inferred | high |  |  |
| `format` | string | 소재 포맷 (image 등 추정 enum) |  | inferred | med |  |  |
| `status` | string | 소재 상태 (active 등) |  | inferred | high |  |  |
| `channel` | string | 노출 채널 (google/naver/meta/kakao 추정 enum) |  | inferred | med |  | 분류 §I7/item20: 내부 channel enum 값셋 미확정 — orders.channel_attribution 풍부 enum 과 동일 도메인인지 값 대조 필요. |
| `image_url` | string | 소재 이미지 URL |  | inferred | high |  | demo 더미 URL(img.example). |
| `landing_url` | string | 랜딩 페이지 URL |  | inferred | high |  | demo 더미 URL(shop.example). |
| `start_date` | date | 소재 게재 시작일 (YYYY-MM-DD) | date | inferred | high |  |  |
| `run_days` | integer | 게재 일수 (일) | days | inferred | med |  |  |
| `frequency` | number | 노출 빈도 = impressions/reach (회) | ratio | vendor_doc | med |  | 분류 §A12: 광고 빈도. customer_rfm.frequency(구매빈도) 동음이의 — 분리. |
| `ctr` | number | 클릭률 (%) | percent | vendor_doc | high |  | 분류 §A7. raw 4.34 → % 표기. |
| `cvr` | number | 전환율 (%) = 전환/클릭 | percent | vendor_doc | high |  | 분류 §A10. raw 3.25 → %. |
| `cpc` | integer | 클릭당 비용 CPC (KRW) | KRW | vendor_doc | high |  | 분류 §A8. raw 508 KRW. |
| `cpa` | integer | 전환당 비용 CPA (KRW) | KRW | vendor_doc | high |  | raw 15700 KRW. CPA=비용/전환수. |
| `roas` | number | 광고비 대비 매출 ROAS (%) | percent | classification | high |  | raw 327.6 → % 표기(배수 아님, §A6/C1.1). Meta 배수와 합산 시 ÷100. |


## experiment

### `ab_tests`

| 메타 | 값 |
|---|---|
| vendor | self_mock_demo |
| API/소스 | data/clumi/raw/ab_tests.csv (자체 mock A/B 테스트 결과) |
| 공식 doc | https://support.google.com/google-ads/answer/6260413 |
| grain | A/B 테스트 1행 (테스트당 변형 A vs B 한 지표 비교) |
| family·format·rows | experiment · csv · 5 |
| PII | 없음 |

자체 mock A/B 테스트 결과. 테스트 1건당 비교 지표(metric)와 변형 A/B의 해당 지표값(a_value/b_value), 비교 대상 소재(variant_a/variant_b=creative_id)를 보유. a_value/b_value 의 단위는 metric 값에 따라 달라짐(metric=ctr/cvr→%, metric=roas→%). 사전 미등재.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `test_id` | string | 테스트 고유 ID (내부 형식 AB-NNN) |  | inferred | high | 🔑 |  |
| `name` | string | 테스트명 (한글, 예: 수분크림 헤드라인 AB) |  | inferred | high |  |  |
| `metric` | string | 비교 지표 종류 (ctr/cvr/roas) |  | inferred | high |  | 이 값이 a_value/b_value 의 단위를 결정 — metric=roas 면 a_value=% (raw 2740.0/4020.0), metric=ctr/cvr 면 %(raw 3.6/3.45). 단위가 행마다 다른 polymorphic value 컬럼. |
| `a_value` | number | 변형 A의 지표값 (단위=metric 종속) | metric_dependent | inferred | high |  | metric=roas→% (raw 2740.0), metric=ctr/cvr→% (raw 3.6). 단일 단위로 단정 불가 — metric 컬럼 참조 필수. |
| `b_value` | number | 변형 B의 지표값 (단위=metric 종속) | metric_dependent | inferred | high |  | a_value 와 동일 단위 규칙(metric 종속). |
| `variant_a` | string | 변형 A 소재 ID (→creatives.creative_id) |  | inferred | high |  | creative_id 참조(raw CR-006). 분류 §I3 내부 소재 식별자 공간. |
| `variant_b` | string | 변형 B 소재 ID (→creatives.creative_id) |  | inferred | high |  | creative_id 참조(raw CR-028). |


## keyword_performance

### `keyword_performance`

| 메타 | 값 |
|---|---|
| vendor | self_mock_demo |
| API/소스 | data/clumi/raw/keyword_performance.csv (자체 mock 키워드 성과) |
| 공식 doc | https://support.google.com/google-ads/answer/6167118 |
| grain | 키워드 1행 (키워드×채널 기간 누적 성과) |
| family·format·rows | keyword_performance · csv · 18 |
| PII | 없음 |

자체 mock 키워드 성과 테이블. 키워드별 노출/클릭/전환/광고비/전환매출 raw 카운트와 파생(roas), 그리고 검색광고 고유 차원(keyword_group/competition/quality_score)을 보유. quality_score 는 Google Ads 품질평가점수(1-10) 컨벤션. roas=% 표기. 사전 미등재.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `keyword` | string | 검색 키워드 (한글, 예: 루미 수분크림) |  | inferred | high | 🔑 | 키워드 ID 없음 — keyword 텍스트가 사실상 grain 키. |
| `channel` | string | 검색광고 채널 (naver 등 추정 enum) |  | inferred | med |  | 분류 §I7/item20 값셋 미확정. |
| `keyword_group` | string | 키워드 그룹 (한글: 브랜드/일반) |  | inferred | high |  | 브랜드 키워드 vs 일반(generic) 키워드 분류 — naver searchad camp_name BRAND/GENERAL 분류와 유사 개념. |
| `competition` | string | 경쟁도 (low/high 등 enum) |  | inferred | med |  | 키워드 입찰 경쟁 강도. raw low/high. |
| `quality_score` | number | 품질평가점수 (1-10, 높을수록 우수) | score_1_10 | vendor_doc | high |  | Google Ads Quality Score 컨벤션 — expected CTR·ad relevance·landing page experience 3요소 종합 1~10 진단지표. raw 9.2/7.1. doc=support.google.com/google-ads/answer/6167118. |
| `impressions` | integer | 노출수 (건) | count | vendor_doc | high |  | 분류 §A2/T6. raw 42100. |
| `clicks` | integer | 클릭수 (건) | count | vendor_doc | high |  | 분류 §A3/T7. raw 1980. |
| `conversions` | integer | 전환수 (건) | count | vendor_doc | high |  | 분류 §A4/T8. raw 121. |
| `ad_cost` | integer | 광고비 (KRW) | KRW | classification | high |  | 분류 §A1/T3 canonical 광고비. raw 920000. |
| `conversion_revenue` | integer | 전환 매출 (KRW) | KRW | classification | high |  | 분류 §A5/T4 canonical 전환매출. raw 6440000. |
| `roas` | number | 광고비 대비 매출 ROAS (%) | percent | classification | high |  | raw 700.0 → % 표기(배수 아님, §A6/C1.1). Meta 배수와 합산 시 ÷100. |


## messaging_crm

### `naver_interest_alert`

| 메타 | 값 |
|---|---|
| vendor | Naver SmartStore (스마트스토어 관심고객/소식알림) |
| API/소스 | 스마트스토어 관심고객·소식알림(interest/notification) 월별 집계. 공식 공개 API 미존재(파트너 콘솔/스크래핑 추정), mock 자체 스키마 |
| 공식 doc | https://sell.smartstore.naver.com/ |
| grain | 월별 × 채널 (collect_date=YYYY-MM × channel). row_count 4 = 월 4건(채널/캠페인 분해 없음). |
| family·format·rows | messaging_crm · csv · 4 |
| PII | 없음 |

스마트스토어 관심고객/알림수신 고객 풀과 소식알림 메시지 월별 성과 집계. CSV 22컬럼 전수 커버. 공식 공개 API 없음 — dict+분류+추론. interest(관심고객)/notification(알림수신) 2개 모집단 funnel + 메시지 발송 성과. 함정: 율 분모 미명시(M5/M7), conversion_amount 에 _krw 미부착(KRW 추정), message_send_count 가 시도/성공 불명, grain 이 월별이라 캠페인 분해 불가.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `channel` | string | 채널 (예 naver_smartstore). |  | dict | high | 🔑 | I7 cluster. 단일값. |
| `shop_name` | string | 스마트스토어 상점명. |  | inferred | med |  | 사전 미등재(인벤토리 only). 상점 식별 라벨. |
| `collect_date` | string | 월별 집계 기준월 (YYYY-MM, 예 2026-04). | month | dict | high | 🔑 | grain 키. interest_alert 만 월별 grain(T1 day cluster 와 입도 다름 C7.2). |
| `avg_order_value` | string | 평균 주문금액 AOV (KRW 추정). | KRW | classification | med |  | M12 cluster. _krw 미부착(KRW misread 위험). promotion/rfm/category AOV 와 join 금지. |
| `conversion_count` | string | 전환 수 (건). | count | dict | high |  | M9 cluster. interest=클릭기반 attribution 시사. 광고 전환과 합산 금지. raw=string. |
| `conversion_amount` | string | 전환 매출 (KRW). dict 예시 4280000. | KRW | dict | high |  | M10/C2.3: _krw 접미 누락 → 단위 misread 위험(타 채널 conversion_amount_krw 와 통합 시 명시 필요). |
| `message_open_rate` | string | 소식알림 메시지 오픈율 (%). dict 예시 48.3. | percent | dict | high |  | M5/C6.6: 분모(발송/대상/시도) 미명시 → 통합 시 벤치마크 왜곡. |
| `snapshot_datetime` | date/datetime | 데이터 수집 시각 (스냅샷 timestamp). | datetime | inferred | med |  | collect_date(월)와 별개의 수집 시점. TZ 암묵 KST. |
| `message_click_rate` | string | 소식알림 메시지 클릭율 (%). dict 예시 8.7. | percent | dict | high |  | M7/C6.6: 분모(발송/오픈) 미명시. CTOR 과 구분 필요. |
| `message_open_count` | string | 메시지 오픈 수 (건). | count | dict | high |  | M4 cluster. 'message_' 접두는 알림유형 구분 의도일 수. |
| `message_send_count` | string | 총 메시지 발송수 (건). dict 예시 8950. | count | dict | high |  | M3/C: 시도(sent)인지 성공(delivered)인지 미명시 → M1 발송대상/M2 송달 귀속 불가. |
| `message_click_count` | string | 메시지 클릭 수 (건). | count | dict | high |  | M6 cluster. 광고 clicks 와 동음이의(분모 다름). |
| `interest_customer_added` | string | 월간 신규 관심고객 수. dict 예시 425. | count | dict | high |  | 관심고객 funnel 유입. naver 고유 모집단 지표(동의어 cluster 미형성). |
| `interest_customer_total` | string | 누적 관심고객 수 (월말 기준). dict 예시 2675. | count | dict | high |  | 월말 스톡. added-removed 와 정합(net_change). |
| `notification_opt_in_rate` | string | 관심→알림 옵트인 비율 (%). dict 예시 83.74. | percent | dict | high |  | notification_customer_total/interest_customer_total funnel 전환율. |
| `interest_customer_removed` | string | 월간 관심고객 이탈 수. | count | inferred | high |  | added 대칭. net_change=added-removed. |
| `conversion_rate_from_click` | string | 클릭 대비 전환율 (%, conversion_count/message_click_count 추정). | percent | inferred | med |  | 분모=클릭으로 명시된 CVR. talktalk conversion_rate_click 과 철자 다른 동의어(§5 #8). |
| `notification_customer_added` | string | 월간 신규 알림수신 고객 수. | count | inferred | high |  | notification funnel 유입(interest 하위 모집단). |
| `notification_customer_total` | string | 누적 알림수신 고객 수. dict 예시 2240. | count | dict | high |  | opt-in 모집단 스톡. message_send_count 의 대상 풀. |
| `interest_customer_net_change` | string | 관심고객 순증감 (added-removed). | count | inferred | high |  | 파생 계산값. |
| `notification_customer_removed` | string | 월간 알림수신 고객 이탈 수. | count | inferred | high |  | notification funnel 이탈. |
| `notification_customer_net_change` | string | 알림수신 고객 순증감 (added-removed). | count | inferred | high |  | 파생 계산값. |

### `naver_talktalk`

| 메타 | 값 |
|---|---|
| vendor | Naver TalkTalk (네이버 톡톡 비즈니스 메시지) |
| API/소스 | 네이버 톡톡 파트너센터/비즈니스 메시지 발송·성과. 공식 공개 API 미존재(파트너센터 추정), mock 자체 스키마 (root+wrapper+campaigns[] 중첩) |
| 공식 doc | https://talk.naver.com/ |
| grain | 캠페인 누계 (campaigns[] × summary). channel/friend_summary=계정 스냅샷 1건. results_sample[]=개별 발송 샘플(다른 grain). row_count 2 캠페인. |
| family·format·rows | messaging_crm · json · 2 |
| PII | ⚠ 포함 |

네이버 톡톡 마케팅 메시지 캠페인 성과 + 채널(친구) 스냅샷. JSON 중첩: root(channel/shop/friend_summary) + campaigns[](message_blocks[] 소재 / summary 캠페인누계 성과 / results_sample[] 개별발송샘플). 핵심 컬럼 + 중첩그룹 대표 커버: summary.*(성과 전수)·friend_summary.*(친구 funnel 대표)·message_blocks[].*(소재구조 대표)·results_sample[].*(개별샘플 대표). 함정: target_friends=opt-in 친구(타 채널 recipients 와 모집단 다름), roi_percent=ROI≠ROAS(절대 합치지 말 것), unfriend_after_send=톡톡 특유, results_sample.friend_id_hash=PII 해시, send 일시 4단계 의미차.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `channel_id` | string | 톡톡 채널 ID (예 @clumi_official). |  | dict | high | 🔑 | 계정 식별. root·campaigns[] 양쪽 존재. |
| `channel_name` | string | 톡톡 채널명. |  | inferred | high |  | root 스냅샷. |
| `shop_id` | string | 연결 스마트스토어/상점 ID. |  | inferred | med |  | root 스냅샷. |
| `snapshot_datetime` | date/datetime | 데이터 수집 스냅샷 시각. | datetime | inferred | high |  | TZ 암묵 KST. query_date_range 와 별개. |
| `query_date_range.start_date` | date/datetime | 조회 기간 시작일. | date | inferred | high |  | wrapper 메타. |
| `query_date_range.end_date` | date/datetime | 조회 기간 종료일. | date | inferred | high |  | wrapper 메타. |
| `friend_summary.total_friends` | int | [friend_summary.* 중첩그룹 대표] 누적 친구 수. dict 예시 1487. 그룹: favorite_count(즐겨찾기)·marketing_opt_in_count/rate(마케팅동의 수/율)·active_friends_30d(30일활성)·new_friends_april/unfriend_april/net_change_april(월간 증감) 포함. | count | dict | high |  | 친구 funnel 모집단 스냅샷. marketing_opt_in_count = summary.target_friends 의 모수. |
| `friend_summary.marketing_opt_in_count` | int | 마케팅 수신동의 친구 수. dict 예시 1245. | count | dict | high |  | M1: 발송 대상(target_friends)의 모집단. 알림톡 비친구 대상과 다른 opt-in 모집단. |
| `campaigns[].campaign_id` | string | 톡톡 캠페인 ID (NTT_ prefix, 예 NTT_20260415_001). |  | dict | high | 🔑 | I1/C5.1: NTT 발급체계 — 타 채널 ID 공간과 join 불가. |
| `campaigns[].campaign_name` | string | 캠페인명. |  | inferred | high |  | I2 cluster. |
| `campaigns[].campaign_type` | string | 캠페인 유형 (마케팅 메시지 종류). |  | inferred | med |  | 값셋 미관측. |
| `campaigns[].send_request_date` | date/datetime | 발송 요청 일시. | datetime | dict | high |  | T10/C: requested 단계. send_completion_date(완료)와 단계 의미 차. TZ 암묵 KST. |
| `campaigns[].send_completion_date` | date/datetime | 발송 완료 일시. | datetime | inferred | high |  | T10: completed 단계(requested 이후). |
| `campaigns[].message_blocks[].block_type` | string | [message_blocks[].* 중첩그룹 대표] 메시지 블록 유형 (image/text/button). 그룹: order(순서)·content.{name,text,url,action_type,action_url,alt_text,width,height}(블록 내용) 포함 — 소재 구조 표현. |  | dict | high |  | 소재(크리에이티브) 구조. 성과 아님. content.* leaf 는 블록 종류별 선택 채움. |
| `campaigns[].summary.target_friends` | int | [summary.* 성과 중첩그룹] 발송 대상 친구 수. dict 예시 1245(=marketing_opt_in_count). | count | dict | high |  | M1 cluster. opt-in 친구 모집단 — kakao target_recipients(알림톡 비친구)와 모집단 성격 다름. |
| `campaigns[].summary.delivered_count` | int | 송달 성공 수 (단말 도달). dict 예시 1226. | count | dict | high |  | M2/C6.5: 톡톡=delivered(단말도달), kakao=success_count(요청수락) — 동일단계 미확정. crm delivered_count 와 동의어. |
| `campaigns[].summary.delivered_rate` | float | 송달율 (% = delivered/target). | percent | inferred | high |  | 분모=target_friends 추정. |
| `campaigns[].summary.failed_count` | int | 발송 실패 수. | count | inferred | high |  | §5 #8: kakao fail_count 와 철자 다른 동의어. target=delivered+failed 추정. |
| `campaigns[].summary.open_count` | int | 오픈 수 (건). | count | inferred | high |  | M4 cluster. |
| `campaigns[].summary.open_rate` | float | 오픈율 (%). dict 예시 42.09. | percent | dict | high |  | M5/C6.6: 분모(대상/송달) 미명시. |
| `campaigns[].summary.click_count` | int | 클릭 수 (건). | count | inferred | high |  | M6 cluster. |
| `campaigns[].summary.click_rate` | float | 클릭율 (%, 발송/송달 대비). dict 예시 7.18. | percent | dict | high |  | M7/C6.6: click_through_rate_open(CTOR)와 분모 다름 — 분리 필수. |
| `campaigns[].summary.click_through_rate_open` | float | 오픈 대비 클릭율 CTOR (% = click/open). | percent | classification | high |  | M8/C6.6: dict 미등재(인벤토리 only). click_rate(발송대비)와 혼동 → _open 분모 보존 필수. |
| `campaigns[].summary.conversion_count` | int | 전환 수 (건). dict 예시 14. | count | dict | high |  | M9 cluster. 메시징 attribution — 광고 전환과 합산 금지. |
| `campaigns[].summary.conversion_rate_click` | float | 클릭 대비 전환율 (% = conversion/click). | percent | inferred | med |  | interest_alert conversion_rate_from_click 과 철자 다른 동의어(§5 #8). |
| `campaigns[].summary.conversion_amount_krw` | int | 전환 매출 (KRW). dict 예시 612000. | KRW | dict | high |  | M10/T4 cluster. _krw 명시(interest conversion_amount 와 달리 안전). |
| `campaigns[].summary.avg_order_value` | int | 평균 주문금액 AOV (KRW). | KRW | dict | high |  | M12: 도메인 전반 재사용 — join 혼동 금지. _krw 미부착이나 int KRW. |
| `campaigns[].summary.total_cost_krw` | int | 총 발송 비용 (KRW). | KRW | dict | high |  | A1/T3 cluster. 메시징 발송비 — 광고 spend 와 동의어이나 grain(캠페인누계) 다름. |
| `campaigns[].summary.cost_per_message_krw` | int | 메시지 1건당 비용 (KRW). | KRW | inferred | high |  | §5 #8: total_cost_krw/발송수 파생. 광고 cpc/cpm 아님. |
| `campaigns[].summary.revenue_per_message_krw` | float | 메시지 1건당 매출 (KRW). | KRW | inferred | high |  | §5 #8: conversion_amount/발송수 파생. |
| `campaigns[].summary.roi_percent` | float | ROI (%). dict 예시 9731. 메시징 투자수익률. | percent | dict | high |  | M11/C1.2/C6.3: **ROI≠ROAS — 절대 합치지 말 것**(분자=이익 vs 매출). 산식 net/gross 미명시(스케일 차 의심). |
| `campaigns[].summary.unfriend_after_send` | int | 발송 후 친구 해제 수 (톡톡 특유 이탈). dict 예시 8. | count | dict | high |  | 톡톡 고유 — 발송이 친구 이탈 유발. friend_summary 와 별개 캠페인 귀속. |
| `campaigns[].summary.unfriend_rate` | float | 발송 후 친구 해제율 (%). | percent | inferred | high |  | unfriend_after_send/target_friends 추정. |
| `campaigns[].total_count_in_db` | int | DB 내 전체 발송 결과 건수 (results_sample[] 은 그 일부 샘플). | count | inferred | med |  | results_sample[] 가 전수 아님을 표시(샘플 grain 경고). |
| `campaigns[].results_sample[].friend_id_hash` | string | [results_sample[].* 개별발송 샘플 중첩그룹 대표] 친구 식별 해시 (PII). 그룹: message_id·delivered_status·delivered_at/opened_at/clicked_at/unfriend_at(개별 타임스탬프)·error_code/error_message·favorite·unfriend_after_send 포함 — summary.* 와 다른 grain(개별 발송). |  | classification | high |  | T11/PII: SHA256 해시, 솔트·원본종류(friend_id) 달라 타 채널 해시와 join 불가. pii_flag=true 근거. 개별 grain(C7.2)이라 동의어 분류 제외. |
| `campaigns[].results_sample[].delivered_status` | string | 개별 발송 송달 상태 (delivered/failed 등). |  | inferred | high |  | 개별 grain. summary.delivered_count 의 원천 행. |
| `campaigns[].results_sample_note` | string | results_sample 설명 노트 (샘플임을 명시하는 텍스트). |  | inferred | med |  | 메타 주석. |


## product_review

### `reviews`

| 메타 | 값 |
|---|---|
| vendor | self_mock_demo |
| API/소스 | data/clumi/raw/reviews.csv (자체 mock 제품 리뷰) |
| grain | 리뷰 1행 (제품 리뷰 텍스트) |
| family·format·rows | product_review · csv · 24 |
| PII | 없음 |

자체 mock 제품 리뷰 테이블. 리뷰 1건당 작성일/리뷰 텍스트(한글)/별점(1-5)/제품명/리뷰 ID 보유. 캠페인 성과지표 없음 — 정성 VOC(voice of customer) 도메인. 작성자 식별정보 없음(익명) → pii_flag=false. 표준 벤더 API 아님(자체 mock) — doc_url 없음. 사전 미등재.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `review_id` | string | 리뷰 고유 ID (내부 형식 RV-NNN) |  | inferred | high | 🔑 |  |
| `date` | date | 리뷰 작성일 (YYYY-MM-DD) | date | inferred | high |  |  |
| `product` | string | 리뷰 대상 제품명 (한글, 예: 수분크림/선크림/세럼) |  | inferred | high |  | 제품 마스터 ID 없이 제품명 텍스트만 — join 시 이름 매칭 필요. |
| `rating` | integer | 별점 (1-5) | score_1_5 | inferred | high |  | raw 4/5. 5점 척도. quality_score(1-10)와 다른 척도. |
| `text` | string | 리뷰 본문 (한글 자유서술 VOC) |  | inferred | high |  | 정성 텍스트 — 감성분석/키워드추출 대상. 작성자 식별정보 미포함(익명). |


## social_organic_engagement

### `instagram_engagement`

| 메타 | 값 |
|---|---|
| vendor | Meta |
| API/소스 | Instagram Platform — Instagram Graph API (Media + Media Insights edge, organic) |
| 공식 doc | https://developers.facebook.com/docs/instagram-platform/insights/ |
| grain | 게시물(미디어) 단위 (40 미디어 객체, insights 는 미디어별 metric 집계) |
| family·format·rows | social_organic_engagement · json (wrapper: data[]=40, paging) · 40 |
| PII | 없음 |

유료 광고가 아닌 organic Instagram 게시물 인게이지먼트. Graph API Media 객체(id/caption/media_type/permalink/timestamp/like_count/comments_count 등) + 중첩 insights.data[](미디어별 metric: reach/views/saved/shares/total_interactions/profile_visits/follows/reels_skip_rate)를 합친 구조. insights.data[]={name,period,title,values[].value} 형식. v22+ 에서 impressions/video_views 폐기 → views 사용. reach 는 organic(유기) — meta_ads_* 의 paid reach 와 합산 금지(C6.4). 커버: data[].* leaf + insights metric 대표.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `data[].id` | string | Instagram 미디어 ID (게시물 고유 ID) |  | vendor_doc | high | 🔑 | creatives.creative_id·crm variant_id 와 별 ID 공간. |
| `data[].caption` | string | 게시물 캡션 (본문 + 해시태그) |  | vendor_doc | high |  |  |
| `data[].media_type` | string | 미디어 유형 (IMAGE / VIDEO / CAROUSEL_ALBUM / REELS) |  | vendor_doc | high |  |  |
| `data[].media_product_type` | string | 게재 표면 유형 (FEED / REELS / STORY) |  | vendor_doc | high |  | media_type(콘텐츠 형식)과 구분 — 노출 surface. |
| `data[].media_url` | string | 미디어 파일 URL |  | vendor_doc | med |  | 만료성 URL 가능. |
| `data[].thumbnail_url` | string | 썸네일 URL (영상/캐러셀) |  | vendor_doc | med |  |  |
| `data[].permalink` | string | 게시물 영구 링크 (https://www.instagram.com/p/{shortcode}/) |  | vendor_doc | high |  |  |
| `data[].timestamp` | date | 게시 시각 (ISO 8601, UTC, 예 2026-04-15T10:30:00+0000) |  | vendor_doc | high |  | T2: ISO8601 UTC. meta_ads date_start(YYYY-MM-DD KST)와 TZ/포맷 다름. |
| `data[].username` | string | 게시 계정 사용자명 (예 clumi_official) |  | vendor_doc | high |  |  |
| `data[].like_count` | int | 좋아요 수 | count | vendor_doc | high |  | 미디어 객체 직속 필드(네이티브 int). insights total_interactions 의 구성요소. |
| `data[].comments_count` | int | 댓글 수 | count | vendor_doc | high |  |  |
| `data[].children.data[].id` | string | 캐러셀(CAROUSEL_ALBUM) 자식 미디어 ID |  | vendor_doc | high |  | media_type=CAROUSEL_ALBUM 일 때만 존재. |
| `data[].children.data[].media_type` | string | 자식 미디어 유형 (IMAGE/VIDEO) |  | vendor_doc | high |  |  |
| `data[].children.data[].media_url` | string | 자식 미디어 파일 URL |  | vendor_doc | med |  |  |
| `data[].insights.data[].name` | string | 인사이트 metric 이름 (reach/views/saved/shares/total_interactions/profile_visits/follows/reels_skip_rate) |  | vendor_doc | high |  | 중첩 insights edge. v22 에서 impressions/video_views 폐기 → views. dict 가 name 별 의미 기술(reach=도달, views=조회, saved=저장, shares=공유, total_interactions=likes+comments+saved+shares, profile_visits=프로필방문, follows=신규팔로워, reels_skip_rate=릴스 스킵율). |
| `data[].insights.data[].id` | string | 인사이트 metric 인스턴스 ID |  | vendor_doc | high |  | {media-id}/insights/{name}/... 형식. |
| `data[].insights.data[].period` | string | 집계 기간 (media insights 는 보통 lifetime) |  | vendor_doc | high |  |  |
| `data[].insights.data[].title` | string | metric 사람용 표시명 |  | vendor_doc | high |  |  |
| `data[].insights.data[].values[].value` | number (int/float) | metric 값. name 에 따라 단위 다름 (count: reach/views/saved/shares/total_interactions/profile_visits/follows; ratio: reach=count vs reels_skip_rate=비율 0~1) | varies by name | vendor_doc | high |  | A11/C6.4: name=reach → organic 도달. meta_ads_* paid reach 와 별개 cluster. reels_skip_rate 는 비율(0.32). |
| `data[]._meta.category` | string | (자체 mock 부가) 분석용 카테고리 라벨 (promo_spring_serum/brand/tips/product) |  | dict | med |  | _meta.* 는 Graph API 표준 아님 — clumi mock 이 부착한 분석용 메타데이터(demo 증강). |
| `data[]._meta.related_campaign` | string | (자체 mock 부가) 연관 광고 캠페인 라벨 (Serum1+1/NewSet/Mask5+2) |  | dict | med |  | loose link → campaign_name. nullable. Graph API 비표준 mock 필드. |
| `paging.cursors.after` | string | 다음 페이지 커서 |  | vendor_doc | high |  | 페이지네이션 메타. |
| `paging.cursors.before` | string | 이전 페이지 커서 |  | vendor_doc | high |  |  |


## target_plan

### `channel_targets`

| 메타 | 값 |
|---|---|
| vendor | self_mock_demo |
| API/소스 | data/clumi/raw/channel_targets.csv (자체 mock 채널별 목표값) |
| 공식 doc | https://support.google.com/google-ads/answer/6268637 |
| grain | 기간(월) × 채널 1행 — 목표값 |
| family·format·rows | target_plan · csv · 4 |
| PII | 없음 |

자체 mock 채널별 목표값 테이블. period(월)×channel 단위로 target_cpa(KRW)·target_roas(%) 목표를 보유. 분류 §5 item22: 관측치 아닌 목표·계획값 — 성과 cluster(daily_performance 등)와 합산 금지. 별도 목표값 도메인. 사전 미등재.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `period` | string | 대상 기간 (YYYY-MM, 월별) | month | inferred | high | 🔑 | raw 2026-04 → 월 단위(일자 아님). |
| `channel` | string | 채널 (naver/google/meta/kakao) |  | inferred | high | 🔑 | 분류 §I7: 채널 enum. 본 테이블 값셋(naver/google/meta/kakao) 관측됨. |
| `target_cpa` | integer | 목표 CPA = 전환당 목표비용 (KRW) | KRW | vendor_doc | high |  | 목표값(§5 item22). raw 12000~14000 KRW. |
| `target_roas` | number | 목표 ROAS (%) | percent | classification | high |  | 목표값(§5 item22). raw 300~420 → % 표기(배수 아님). 관측 roas 와 같은 % 스케일. |

### `marketing_monthly_targets`

| 메타 | 값 |
|---|---|
| vendor | self_mock_demo |
| API/소스 | data/clumi/raw/marketing_monthly_targets.csv (자체 mock 월간 마케팅 목표) |
| 공식 doc | https://support.google.com/google-ads/answer/6268637 |
| grain | 기간(월) 1행 — 전사 월간 목표값 |
| family·format·rows | target_plan · csv · 1 |
| PII | 없음 |

자체 mock 월간 마케팅 전사 목표 테이블. period(월) 1행에 노출/클릭/전환 목표 카운트와 비율 목표(target_ctr/target_cvr/target_roas), 손익분기 ROAS(breakeven_roas)를 보유. 분류 §5 item22: 전부 목표·계획값 — 관측 성과와 합산 금지. breakeven_roas 는 손익분기점(이익=0) 기준선. 사전 미등재.

| 컬럼 | 타입 | 설명 | 단위 | src | conf | key | note |
|---|---|---|---|---|:--:|:--:|---|
| `period` | string | 대상 기간 (YYYY-MM, 월별) | month | inferred | high | 🔑 | raw 2026-04. |
| `target_impressions` | integer | 목표 노출수 (건) | count | vendor_doc | high |  | 목표값. raw 1500000. |
| `target_clicks` | integer | 목표 클릭수 (건) | count | vendor_doc | high |  | 목표값. raw 52500. |
| `target_conversions` | integer | 목표 전환수 (건) | count | vendor_doc | high |  | 목표값. raw 2100. |
| `target_ctr` | number | 목표 클릭률 (%) | percent | vendor_doc | high |  | 목표값. raw 3.5 → %. |
| `target_cvr` | number | 목표 전환율 (%) | percent | vendor_doc | high |  | 목표값. raw 4.0 → %. |
| `target_roas` | number | 목표 ROAS (%) | percent | classification | high |  | 목표값(§5 item22). raw 380 → % 표기(배수 아님). |
| `breakeven_roas` | number | 손익분기 ROAS (%) — 이익=0 기준선 | percent | classification | high |  | 목표값/기준선(§5 item22, OUT 범위에 명시). raw 250 → %. 1/마진율 기반 손익분기점. target_roas(380)와 비교해 마진 평가. |


## 다음 단계

- 이 메타데이터 = **canonical data contract 씨앗** (리서치 ⑥). normalize 명명 확정 시 canonical alias·conversion 룰을 여기에 부착.
- `inferred`/`low` confidence 컬럼은 검증 대상(특히 demo family). dict↔raw drift는 semantic_note 참조.
- 살아있는 문서化: raw 스키마 재추출 후 description 미기재 컬럼 = RED (후속).

## 변경 이력
| 날짜 | 내용 |
|---|---|
| 2026-06-14 | v1.0 초안 — 벤더 6그룹 워크플로(dict+분류+벤더doc 머지, source/confidence) → 조립. 34테이블·712컬럼. |