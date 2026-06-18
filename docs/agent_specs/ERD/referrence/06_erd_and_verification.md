# 06 · ERD 관계 결정 & 외부 검증

> **이 문서는 octorad_raw_metadata_v0_1.md에 없는 내용만 담습니다.**  
> metadata는 컬럼 단위 의미·출처를 다루고, 이 문서는 **테이블 간 관계 구조·외부 검증 판정·Canonical Name 결정**을 다룹니다.

---

## 1. ERD FK 관계 — 확정 17건

> metadata는 컬럼 레벨에서 FK를 태그로 표시하지만, 관계 전체 목록·추정 근거·구조도는 이 문서에만 있습니다.

| # | FK 테이블 | FK 컬럼 | → | PK 테이블 | PK 컬럼 | 관계 의미 |
|---|---|---|---|---|---|---|
| 1 | `creatives` | `campaign_id` | → | `campaigns` | `campaign_id` | 광고소재 → 캠페인 |
| 2 | `daily_performance` | `campaign_id` | → | `campaigns` | `campaign_id` | 일별성과 → 캠페인 |
| 3 | `daily_performance` | `creative_id` | → | `creatives` | `creative_id` | 일별성과 → 소재 |
| 4 | `crm_message_variants` | `campaign_id` | → | `crm_campaigns` | `campaign_id` | CRM 메시지 변형 → CRM 캠페인 |
| 5 | `crm_send_logs` | `campaign_id` | → | `crm_campaigns` | `campaign_id` | 발송로그 → CRM 캠페인 |
| 6 | `crm_send_logs` | `variant_id` | → | `crm_message_variants` | `variant_id` | 발송로그 → 메시지 변형 |
| 7 | `customer_rfm` | `member_id` | → | `customers` | `member_id` | RFM 스냅샷 → 회원 |
| 8 | `customer_grade_history` | `member_id` | → | `customers` | `member_id` | 등급이력 → 회원 |
| 9 | `orders` | `member_id` | → | `customers` | `member_id` | 주문 → 회원 (nullable=비회원 허용) |
| 10 | `signup_events` | `member_id` | → | `customers` | `member_id` | 가입이벤트 → 회원 |
| 11 | `promotion_usage_history` | `member_id` | → | `customers` | `member_id` | 프로모션 사용이력 → 회원 |
| 12 | `promotion_usage_history` | `order_id` | → | `orders` | `order_id` | 프로모션 사용이력 → 주문 |
| 13 | `orders` | `promotion_code` | → | `promotions` | `promotion_code` | 주문 → 프로모션 |
| 14 | `promotion_performance` | `promotion_id` | → | `promotions` | `promotion_id` | 프로모션 성과 → 마스터 |
| 15 | `promotion_usage_history` | `promotion_id` | → | `promotions` | `promotion_id` | 사용이력 → 프로모션 마스터 |
| 16 | `promotion_performance` | `promotion_code` | → | `promotions` | `promotion_code` | 성과집계 → 프로모션 코드 |
| 17 | `promotion_usage_history` | `promotion_code` | → | `promotions` | `promotion_code` | 사용이력 → 프로모션 코드 |

---

## 2. 추정 FK 관계 — 7건 (실값 대조 전 JOIN 금지)

| # | FK 테이블 | FK 컬럼 | →? | PK 테이블 | PK 컬럼 | 불확실 이유 |
|---|---|---|---|---|---|---|
| 추1 | `crm_campaigns` | `campaign_id` | →? | `campaigns` | `campaign_id` | CRM=int, 광고=string. 타입 불일치, 별도 도메인 가능성 |
| 추2 | `ga4_traffic_source` | `user_pseudo_id` | →? | `ga4_page_events` | `user_pseudo_id` | 동일 GA4 export 공유 식별자. FK라기보다 join key |
| 추3 | `ga4_page_events` | `user_id` | →? | `customers` | `member_id` | GA4 user_id=member_id 동의어 추정, 대부분 null |
| 추4 | `ga4_traffic_source` | `user_id` | →? | `customers` | `member_id` | GA4 user_id=member_id 동의어 추정, 대부분 null |
| 추5 | `meta_ads_by_age` | `account_id` | →? | `meta_ads_performance` | `account_id` | Meta 3소스가 동일 account_id 공유. 명시 PK 테이블 없음 |
| 추6 | `meta_instagram_inapp` | `account_id` | →? | `meta_ads_performance` | `account_id` | 공유 차원키(ad_account). 명시 PK 없음 |
| 추7 | `kakao_bizmessage` | `template_code` | →? | `naver_talktalk` | `code` | 매우 약함 — status code 혼동 가능. 도메인 상 무관 |

---

## 3. 관계 구조도

### 회원 중심 스타 구조 (확정)

```
customers (PK: member_id)
    ├── orders
    │     └── promotion_usage_history  (order_id)
    ├── customer_rfm
    ├── customer_grade_history
    ├── signup_events
    └── promotion_usage_history  (member_id)
```

### 프로모션 관계 (확정)

```
promotions (PK: promotion_id, promotion_code)
    ├── promotion_performance
    └── promotion_usage_history
```

### CRM 관계 (확정)

```
crm_campaigns (PK: campaign_id, int)
    ├── crm_message_variants (campaign_id)
    └── crm_send_logs (campaign_id)
            └── crm_message_variants (variant_id)
```

### 광고 자체 정의 관계 (확정, Stub 도메인)

```
campaigns (PK: campaign_id, string) ★Stub
    ├── creatives (campaign_id)
    └── daily_performance (campaign_id)
            └── creatives (creative_id)
```

### GA4 ↔ 회원 연결 (추정, 취약)

```
ga4_page_events  ──?──  ga4_traffic_source  (user_pseudo_id join key)
        ↓ user_id (≈member_id, 대부분 null)
     customers.member_id  (추정 매핑, null 다수)
```

### 채널별 campaign_id 네임스페이스 (cross-join 불가)

```
campaigns.campaign_id (string, BRP-/SRC- prefix)  ─ 별도 공간
meta_ads_performance.data[].campaign_id (17자리 숫자 string)  ─ 별도 공간
naver_searchad.data[].nccCampaignId (cmp- prefix)  ─ 별도 공간
kakao_bizmessage.campaigns[].campaign_id (CMP_KKO prefix)  ─ 별도 공간
crm_campaigns.campaign_id (int)  ─ 타입까지 다름

→ 교차 연결은 campaign_name / utm_campaign 매핑 테이블로만 가능
```

---

## 4. 외부 API 문서 검증 결과

> 검증일: 2026-06-14  
> 소스: Meta for Developers v25.0 Insights API · Naver searchad-apidoc GitHub (FAQ-stat 공식 위키, Java Stat.java, Issue #1084/#976) · ROAS/ROI 공식 정의 문서

### ✅ PASS — 10건 (공식 문서 확인 완료)

#### P-01 `salesAmt` = 광고비(총비용)

- **우리 주장**: `salesAmt`는 광고비이며 매출이 아님
- **검증 결과**: Naver searchad-apidoc GitHub FAQ-stat「`salesAmt`: 총비용」, Java `Stat.java`에서 `Integer salesAmt` 광고비 필드 확인, 실측 공식 `ror = convAmt/salesAmt×100` 재확인
- **실무 액션**: `salesAmt → ad_cost_krw` 리매핑 필수. normalizer 주석 필수

#### P-02 `convAmt` = 전환매출액

- **우리 주장**: `convAmt`는 전환매출(매출)이며 `salesAmt`(비용)와 절대 혼동 금지
- **검증 결과**: FAQ-stat「`convAmt`: 전환매출액」, 공식 공식 `ror = convAmt/salesAmt×100`으로 양쪽 역할 동시 확인
- **실무 액션**: `convAmt → conversion_revenue_krw` 매핑

#### P-03 `ccnt` = 전환수(건, int) — 사전 오류 확인

- **우리 주장**: `ccnt`는 전환수(건, int). 사전이 CVR%로 잘못 기재한 오류
- **검증 결과**: Java `Stat.java`에서 `Integer ccnt`(int 타입 전환수) 확인. 실측 raw `clk=5, ccnt=1` → 정수 건수 확인
- **실무 액션**: `ccnt → conversion_count` 매핑. 사전의 'ccnt=CVR%' 표기 삭제

#### P-04 `crto` = CVR(%) — `convCnt` 부재 확인

- **우리 주장**: `crto`는 전환율 CVR(%). 사전의 `convCnt`(전환수)는 raw에 없음
- **검증 결과**: Java `Double crto`(float 타입=% 값). 실측 `crto = ccnt/clkCnt×100 (1/5=20.0)`. `convCnt` 필드 부재 확인
- **실무 액션**: `crto → cvr_pct` 매핑. `convCnt` 사용 금지

#### P-05 Meta ROAS = 배수(×), Naver ror = % → 100배 단위 차

- **우리 주장**: Meta `purchase_roas[].value`는 배수(2.2063), Naver `ror`는 %(3714.66) → 100배 차
- **검증 결과**: Meta 공식 문서 ROAS = ratio/multiplier(2.19:1 평균). Naver FAQ-stat `ror = 광고수익률 = 전환매출/총비용`(% 단위). 실측 `ror = 62332/1678×100 = 3714.66`
- **실무 액션**: canonical = 배수(×). Naver ror·advoost roas: ÷100 보정 필수

#### P-06 Meta `actions[]` 배열 구조 + `omni_purchase` 필터 필수

- **우리 주장**: `actions[]`, `action_values[]`, `purchase_roas[]`는 EAV 중첩 배열. flat key 없음. 미필터 시 silent-0
- **검증 결과**: Meta v25.0 Insights API 공식 문서에서 배열 구조 확인. Meta Ads MCP 오픈소스 테스트 코드에서 `action_type='omni_purchase'` 필터 패턴 확인
- **실무 액션**: normalizer에 배열 필터 로직 명시. flat `roas=1.04`(사전 값)는 오기

#### P-07 ROAS ≠ ROI — 산식 다름

- **우리 주장**: 광고 ROAS와 메시징 `roi_percent`는 산식이 달라 절대 합산 금지
- **검증 결과**: 공식 산식 `ROI% = (ROAS - 1) × 100` 확인. A 4.5× ROAS = 350% ROI
- **실무 액션**: `roas_x` (광고)와 `msg_roi_pct` (메시징) 별도 canonical 유지

#### P-08 `impCnt`=노출수, `clkCnt`=클릭수, `cpc`=클릭당비용

- **우리 주장**: Naver 검색광고 stat 필드 의미
- **검증 결과**: FAQ-stat「`impCnt`: 노출수 / `clkCnt`: 클릭수 / `cpc`: 평균클릭비용」. Java `Integer impCnt, Integer clkCnt, Integer cpc` 타입 확인
- **실무 액션**: `impCnt→impressions`, `clkCnt→clicks`, `cpc→cpc_krw` 매핑

#### P-09 Meta `campaign_id` = 숫자 string, Naver `nccCampaignId` = 다른 패턴

- **우리 주장**: 채널별 campaign_id 네임스페이스가 달라 cross-join 불가
- **검증 결과**: Meta Developers API 예시에서 12~17자리 숫자 string 확인. Naver Issue #976에서 `nccCampaignId` 패턴 확인
- **실무 액션**: 채널 prefix 보존. 교차 연결은 campaign_name/UTM 매핑 테이블로

#### P-10 Meta `clicks`(전체) ≠ `inline_link_clicks`(링크 클릭)

- **우리 주장**: Meta CTR 분모 정의 시 two 컬럼이 달라 canonical 선택 필요
- **검증 결과**: Meta v25.0 Insights API 공식 Clicks definition 섹션에서 「Link Clicks = 광고 링크로 이동한 클릭 / Clicks(All) = 상호작용·링크·확장 경험 등 여러 유형」 명시
- **실무 액션**: CTR canonical = `inline_link_click_ctr` 권장

---

### ⚠️ PARTIAL — 2건 (추가 확인 필요)

#### PA-01 메시징 `open_rate` / `click_rate` 분모 정의 ⚠️

- **우리 주장**: 채널별 분모(대상/송달/시도)가 다를 가능성 — 통합 위험
- **검증 시도**: 카카오 Moment API 문서 접근 → 공식 대행사 계약 후 접근 가능 (공개 문서 없음)
- **현재 상태**: 분모 정의 미확인
- **필요 액션**: 카카오 공식 대행사 파트너 채널 통해 API 문서 확인
- **그 전까지**: 채널 간 `open_rate`, `click_rate` 수치 비교 절대 금지

#### PA-02 `kakao_bizmessage.success_count` = delivered 단계 정의 ⚠️

- **우리 주장**: `success_count`(요청 수락)와 `delivered_count`(단말 도달)가 동일 단계인지 불명
- **검증 시도**: 카카오엔터프라이즈 BizMessage API 접근 → 딜러사 계약 필요
- **현재 상태**: 단계 정의 미확인
- **필요 액션**: 카카오엔터프라이즈 또는 NHN 딜러사 공식 문서 확인

---

## 5. Canonical Name 결정 작업 시트

> metadata와 이 문서의 분석을 종합한 최종 결정 입력 시트.  
> 결정 후 `octorad_raw_metadata_v0.1.yaml`의 canonical alias 필드에 부착 예정.

| Cluster ID | Concept | 핵심 결정 사항 | **확정 canonical name** | 단위 | 채널별 변환 규칙 요약 | 확정 여부 |
|---|---|---|---|---|---|---|
| A1 | 광고비 | `salesAmt`=비용 혼동, Meta 통화 의존 | ← 입력 | KRW | Meta: str→float + 통화확인 / Naver salesAmt / Kakao total_cost_krw | 미결정 |
| A3 | 클릭수 | clicks(all) vs inline_link_clicks | ← 입력 | count | Meta: inline_link_clicks 권장 / Naver: clkCnt | 미결정 |
| A4 | 전환수(광고) | 배열 필터, VT 포함 여부, attribution 분리 | ← 입력 | 건(int) | Meta: omni_purchase 필터 / Naver: ccnt / advoost: CT전용 | 미결정 |
| A5 | 전환매출(광고) | convAmt≠salesAmt, 배열 필터, _krw 미명시 | ← 입력 | KRW | Meta: action_values[omni_purchase] / Naver: convAmt | 미결정 |
| A6 | ROAS | 배수vs% 100배 차, 배열 필터, flat key 없음 | ← 입력 | 배수(×) | Meta: 그대로 / Naver ror·advoost: ÷100 | 미결정 |
| A7 | CTR | all vs link-click 분자 다름 | ← 입력 | % | Meta: inline_link_click_ctr / Naver: ctr | 미결정 |
| A10 | CVR | Meta 직접 컬럼 없음, advoost VT/CT 분리 | ← 입력 | % | Meta: 파생(ccnt/clicks×100) / Naver: crto / advoost: ctcvr | 미결정 |
| I1 | 캠페인 ID | 채널별 네임스페이스 분리, cross-join 불가 | ← prefix 보존 권장 | string | 채널 prefix+id / 교차연결=명/UTM 매핑테이블 | 미결정 |
| I4 | 회원 ID | GA4 user_id 명칭 차, 대부분 null | ← 입력 | string | GA4 user_id alias / null=비로그인 | 미결정 |
| M5 | 오픈율 | 분모 미명시 ⚠️ 미확인 | ← 카카오 문서 확인 후 입력 | % | **분모 확인 전 입력 금지** | 미결정 |
| M7 | 클릭율 | click_rate vs CTOR 분모 다름 | ← 카카오 문서 확인 후 입력 | % | **분모 확인 전 입력 금지** | 미결정 |
| M9 | 전환수(메시징) | attribution 다름, 광고 전환과 절대 분리 | `msg_conversion_count` (제안) | 건(int) | 채널 공통 집계 가능 | 미결정 |
| M10 | 전환매출(메시징) | interest _krw 미명시, bigint vs int | ← 입력 | KRW | CRM: bigint / Kakao/Talktalk: int / interest: 단위 확인 | 미결정 |
| M11 | ROI | ROAS와 절대 분리, 산식 미명시 | `msg_roi_pct` (제안) | % | 채널 공통, net/gross 산식 확인 필요 | 미결정 |
| M12 | AOV | 4도메인 동명 grain 다름 | ← prefix 필수 | KRW | msg\_ / promo\_ / rfm\_ / cat\_ prefix | 미결정 |
| T1 | 보고 날짜 | UTC vs KST ±1일, 정수 vs ISO | ← 입력 | date (KST, YYYY-MM-DD) | GA4: UTC→KST / statDt: int→date | 미결정 |
| T2 | 이벤트 타임스탬프 | μs vs ms vs s, 5만년 오차 | ← 입력 | datetime (KST, ISO 8601) | GA4: ÷1e6+UTC→KST / event_time_unix: 자릿수 확인 | 미결정 |
