# normalize canonical 명명 제안 — normalize_canonical_naming

> **v0.1 — 제안(오너 confirm 대기). canonical data contract의 *이름·단위·변환룰* 입력.**
> 입력: [분류 §2·§4](referrence/normalize_synonym_classification_v0.1.md) · [06 검증·작업시트](referrence/06_erd_and_verification.md) · [방법론 ERD/INDEX §4](INDEX.md).
> 모든 행 = **제안**. 오너 confirm 후 `octorad_raw_metadata_v0.1.yaml` canonical alias + conversion config에 부착.

---

## §1 명명 규약 (먼저 결정 — 권장)

| 규약 | 권장 | 이유 |
|---|---|---|
| **언어** | **영문 snake_case** | client-불변·code-facing·벤더중립. (format_normalizer의 한글 `광고비(원)`은 폐기 demo용) |
| **단위 접미사** | `_krw`·`_pct`·`_x`(배수)·`_count`·`_ratio` | 단위를 *이름에* 박아 배수vs% 같은 충돌 차단 |
| **measure vs metric** | 원자값(measure)=cleaned / 파생(metric)=computed | ROAS·CVR·CPC는 파생 → computed 1곳. 채널은 spend·revenue·count만 |
| **namespace prefix** | `msg_`·`promo_`·`rfm_`·`cat_` | AOV·conversion 등 동명이의 분리 |
| **ID** | native 보존 + `channel` 동반, 교차=crosswalk | 채널 ID공간 join 불가(C5) |

> ⚠ 언어(영문)는 오너 확정 필요 — 이후 전부 여기 따름.

---

## §1.5 ★ 칼럼명 + 수치표기 = 한 쌍 (canonical field spec)

> **오너 지적**: **칼럼명 조정**(matching)과 **다 다른 수치를 어떻게 표기**(value)는 한 필드의 *두 축* — 함께 결정한다. 이름만 통일하고 값 표현을 안 정하면 배수vs%·정의차가 그대로 샌다. (§2~5=이름 축, §6=값 축 → **아래 형식으로 묶음**.)

### 한 필드 = 5요소
| 축 | 무엇 |
|---|---|
| **name** (matching) | canonical 이름 + 채널별 source 컬럼 |
| **unit** | 단위·타입 (이름 접미사에 박음 — `_krw`/`_pct`/`_x`) |
| **transform** (mapping) | 채널별 값 변환 (÷100·통화·캐스팅·포맷) |
| **★표현 전략** | 값을 어떻게 저장·노출하나 (아래 결정) |
| **비교성** | 정의 차로 cross-channel 비교가 안전한가 |

### ★ 값 표현 전략 결정 (권장 — confirm 대기)
**단일 정규화값 + 원본 lineage 보존 + 비교성 flag.**
1. **정규화값 1개** (단위통일·캐스팅) = 에이전트 서빙용.
2. **원본 보존(lineage)**: `{source_channel, source_column, raw_value, transform}` — *신뢰*(직전 턴 lineage)·감사용. "이 `ad_cost_krw` 18.3M은 meta.spend 9.2M + naver.salesAmt 6.0M + … 에서 왔다"를 *보여줌*.
3. **파생값(roas_x·cvr_pct·cpc_krw)은 computed에서 재계산** (measure에서) — 채널 보고값보다 일관. 단 채널 보고 roas도 lineage로 보존(대조).
4. **비교성 flag**: 정의 다른 값(clicks all vs link, attribution window)에 ⚠ — *자동 cross-channel 집계 차단*.

### 워크드 예시 (이름+값 묶음)
**`ad_cost_krw`** (KRW int) `measure`
- 매칭: meta `spend` · naver `salesAmt`(⚠비용) · advoost `cost` · kakao/talktalk `summary.total_cost_krw`
- 표기: str→int · `account_currency`→KRW환산 · 나머지 그대로 → **정규화값 + lineage**. 비교성 ✓(동일=집행비용)

**`roas_x`** (배수 float) `metric→computed`
- 매칭: meta `purchase_roas[omni]` · naver `ror` · advoost `roas`
- 표기: meta 그대로 · naver/advoost **÷100** → **computed 재계산**(`conversion_revenue_krw/ad_cost_krw`) 권장 > 채널보고값(lineage 보존). 비교성 ⚠(attribution window 채널차)

**`clicks`** (count int) `measure`
- 매칭: meta `clicks`(전체) · naver `clkCnt`. (링크=`link_clicks` ← meta `inline_link_clicks` 별 필드)
- 표기: str→int → 정규화값 + lineage. 비교성 ⚠ meta `clicks`⊃`link_clicks` → CTR/비교는 `link_clicks`

**`conversion_count`** (count int) `measure`
- 매칭: meta `actions[omni_purchase]` · naver `ccnt` · advoost `click_through_conversions`(CT)
- 표기: 배열필터·str→int. advoost VT=`vt_conversion_count` 별도 → 정규화값 + lineage. 비교성 ⚠ attribution 정의 채널차 — 합산 주의

> §2~5 표의 "채널별 변환룰" = transform 축, §6 = 값 규칙 모음. **contract 작성 시 위 5요소로 필드당 1 spec 생성.**

---

## §2 광고 성과 (A) — canonical 제안

| cluster | **canonical** | 단위 | 채널별 변환룰 | 상태 |
|---|---|---|---|---|
| A1 광고비 | `ad_cost_krw` | KRW | Meta `spend`(str→int) · Naver **`salesAmt`**(=비용!) · advoost `cost` · kakao/talktalk `summary.total_cost_krw` | 제안 |
| A2 노출 | `impressions` | count | Naver `impCnt`→ | 제안 |
| A3 클릭(전체) | `clicks` | count | Naver `clkCnt`→ · Meta `clicks`(all) | 제안 |
| A3′ 링크클릭 | `link_clicks` | count | Meta `inline_link_clicks` (Meta 전용) | 제안 |
| A4 전환수 | `conversion_count` | count | Meta `actions[omni_purchase]` · Naver `ccnt` · advoost `click_through_conversions`(CT) | 제안 (VT=`vt_conversion_count` 별도) |
| A5 전환매출 | `conversion_revenue_krw` | KRW | Meta `action_values[omni_purchase]` · Naver `convAmt` · advoost `conversion_value` | 제안 |
| A6 ROAS | `roas_x` | **배수(×)** | Meta `purchase_roas[omni]` 그대로 · Naver `ror`**÷100** · advoost `roas`**÷100** | 제안 (06 확정) |
| A7 CTR | `link_ctr_pct` | % | = link_clicks/impressions. Meta `inline_link_click_ctr`(06 권고). 전체 ctr는 `ctr_pct` 별도 | 제안 |
| A8 CPC | `cpc_krw` | KRW | = ad_cost/clicks. Meta `cpc` · Naver `cpc` | 제안 |
| A9 CPM | `cpm_krw` | KRW | Meta·advoost; Naver SA 파생 | 제안 |
| A10 CVR | `cvr_pct` | % | Naver `crto` · advoost `ctcvr` · Meta 파생(conv/clicks) | 제안 |
| A11 도달 | `paid_reach` | count uniq | Meta `reach`. **IG organic은 `organic_reach` 별도 — 합산금지**(C6.4) | 제안 |
| A12 빈도 | `impression_frequency` | imp/reach | Meta 전용 — 단일출처라 canonical 편입 *선택*. ★구 `frequency_ratio`→개명(2026-06-19): 이름이 LLM '구매빈도(RFM)' prior와 충돌해 할루시(A/B 3차 freq_misread 7→0), Meta 표준명 채택 | 개명 |

---

## §3 메시징/CRM (M) — `msg_` prefix

| cluster | **canonical** | 단위 | 비고 | 상태 |
|---|---|---|---|---|
| M1 발송대상 | `msg_target_count` | count | kakao target_recipients · talktalk target_friends · crm target_count | 제안 |
| M2 송달성공 | `msg_delivered_count` | count | ⚠ success(요청수락) vs delivered(단말도달) 단계 미확정 | **⚠보류** (PA-02) |
| M4 오픈수 | `msg_open_count` | count | | 제안 |
| M5 오픈율 | `msg_open_rate_pct` | % | ⚠ **분모(대상/송달/시도) 미확정** | **⚠보류** (PA-01) |
| M6 클릭수 | `msg_click_count` | count | | 제안 |
| M7 클릭율 | `msg_click_rate_pct` | % | ⚠ 분모 미확정 | **⚠보류** (PA-01) |
| M8 오픈대비클릭율 | `msg_ctor_pct` | % | ⚠ open 대비 — click_rate와 분모 다름 | **⚠보류** |
| M9 전환수 | `msg_conversion_count` | count | 광고 전환과 **절대 분리**(C6.3) | 제안 (06) |
| M10 전환매출 | `msg_conversion_revenue_krw` | KRW | interest `conversion_amount`(_krw 없음) 단위확인 | 제안 |
| M11 ROI | `msg_roi_pct` | % | **ROAS와 분리**. `ROI%=(ROAS−1)×100`(06 P-07). net/gross 산식 ⚠확인 | 제안 (06) |
| M12 AOV | `msg_avg_order_value_krw` | KRW | promo_/rfm_/cat_ 와 prefix 분리 | 제안 |

---

## §4 식별·차원 (I) — canonical 제안

| cluster | **canonical** | 비고 | 상태 |
|---|---|---|---|
| I1 캠페인ID | `campaign_id` + `channel` 동반 | 채널별 native 유지(C5 join불가). 교차=crosswalk(name/UTM) | 제안 |
| I2 캠페인명 | `campaign_name` | 영문코드↔한글 정규화. creatives.name(소재명) 혼동주의 | 제안 |
| I3 소재ID | `creative_id` | | 제안 |
| I4 회원ID | `member_id` | GA4 `user_id` alias. **null=비회원/비로그인** | 제안 |
| I5 익명ID | `anon_client_id` | GA4 `user_pseudo_id`. **member_id와 분리**(C5.2) | 제안 |
| I6 세션ID | `ga_session_id` | int 통일 | 제안 |
| I7 채널 | `channel_group`(정규화) + `channel_raw` 보존 | orders↔GA4 **매핑사전 필요** | 제안 |
| I8 utm_source | `utm_source` | meta↔facebook/instagram 매핑. 시점(first/last) 보존 | 제안 |
| I9 utm_medium | `utm_medium` | source 경계 재정의 | 제안 |
| I10 utm_campaign | `utm_campaign` | 정본=last-click | 제안 |
| I11 등급 | `membership_grade`(운영) · `rfm_tier`(RFM) **분리** | 다른 축(C6.7) — 묶지 말 것 | 제안 |
| I12 연령대 | `age_group` | 버킷 공유 | 제안 |
| I13 지역 | `region`(한글 정본) + `region_en` 매핑 | 거주/접속 구분 보존 | 제안 |
| I14 디바이스 | `device_type`(mobile/desktop/tablet) | naver M/P 디코딩 | 제안 |

---

## §5 시간 (T) — canonical 제안

| cluster | **canonical** | 단위 | 변환룰 | 상태 |
|---|---|---|---|---|
| T1 보고날짜 | `report_date` | date (KST) | GA4 `event_date`(UTC)→KST · naver `statDt`(int)→date · YYYY-MM-DD 통일 | 제안 |
| T2 이벤트시각 | `event_ts` | datetime (KST, ISO) | GA4 `event_timestamp`(μs)÷1e6 · `event_time_unix`(s) 자릿수 확인 | 제안 |

---

## §6 ★ 숫자(값) 변환 규칙 요약 — "어떤 식으로" (conversion config 입력)

| 충돌 | canonical 규칙 |
|---|---|
| ROAS 배수 vs % | **배수(×) 통일.** Naver `ror`·advoost `roas` **÷100** |
| 통화 | **KRW 통일.** Meta `account_currency` 확인 후 환산(rate+effective date). `*_in_usd` 분리 |
| 전환 추출 | Meta 배열 `action_type='omni_purchase'` 필터 (미필터=silent-0) |
| 의미함정 | `salesAmt→ad_cost_krw`(비용) · `convAmt→conversion_revenue_krw`(매출) **혼동금지** |
| 날짜/TZ | KST `YYYY-MM-DD`. GA4 UTC→KST |
| 타임스탬프 | KST datetime. μs÷1e6 |
| 타입 | string 수치 → numeric 캐스팅 일관화 |
| measure/metric | spend·revenue·count = cleaned. **roas_x·cvr_pct·cpc_krw 파생 = computed 1곳** |

> ★ **blended 지표 (07 업계 반영)**: 채널 ROAS는 attribution 달라 cross-channel 비교 위험(업계 ~28-40% 과대; 실례 Meta 2.0 vs 전채널 MER 3.5). → **`mer`**(=`total_revenue / total_ad_cost` = blended ROAS = 우리 "전사 ROAS 18.3M 분모") **신설**. 채널은 `{channel}_roas_x` + **비교성⚠ "합산금지"**. 의사결정·전사 = `mer`, 전술 최적화 = 채널 ROAS. 변종 `acquisition_mer`(신규고객)·`tacos`. 전부 computed 1곳 재계산. (출처 [07](referrence/07_industry_raw_to_standard.md))

---

## §7 ⚠ 보류 (Kakao 외부 블로커 — 06 PARTIAL)

- **M5/M7/M8** (메시징 오픈율·클릭율·CTOR): 분모(대상/송달/시도/오픈) 미확정 → **Kakao 공식 doc(대행사 계약) 필요. 그 전까지 명명·통합·채널 간 비교 금지.**
- **M2** (송달): success vs delivered 단계 정의 미확정.

---

## §8 다음

1. **오너 confirm**: §1 언어(영문) + §2~5 canonical 이름 + §6 변환룰. 조정/확정.
2. confirm 후 → **canonical data contract** 작성 (이 명명 + alias + conversion + semantic을 yaml SPEC으로). 그 SPEC이 normalized ERD/metadata/desc 생성 + lineage.
3. M5/M7/M8/M2는 Kakao 블로커 해소 시.

## 변경 이력
| 날짜 | 내용 |
|---|---|
| 2026-06-14 | v0.1 — 분류 §4 + 06 §5 + 검증규칙 종합 canonical 명명 제안(전부 confirm 대기). 규약(영문 snake_case·단위접미사·measure/metric 분리) + A/M/I/T 도메인별 이름 + 숫자 변환룰. M5/M7/M8 Kakao 블로커 보류. |
