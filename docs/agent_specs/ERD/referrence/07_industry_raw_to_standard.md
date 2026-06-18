# 07 · 업계 실무 — raw 광고데이터 → 표준데이터 변환 (외부 리서치)

> **에이전트 제작과 별개**로, 퍼포먼스 마케팅/데이터분석 회사가 멀티채널 raw 광고데이터를 *표준(canonical) 데이터*로 바꾸는 실무를 조사. 우리 [명명](../normalize_canonical_naming_v0.1.md)·[분류](normalize_synonym_classification_v0.1.md)·[구현 리서치](normalize_implementation_research_v0.1.md) 결정의 *업계 교차검증*.
> 조사일 2026-06-14. 도구: Funnel.io · Improvado · Supermetrics · Adverity · Northbeam.

---

## ① 업계가 푸는 문제 = 우리와 동일

> "같은 지표가 플랫폼마다 다른 이름·단위·정의" — 이게 이 업종(marketing data integration)의 **존재 이유**.

- **spend 동의어**: Facebook `amount spent` · Twitter `spend` · Google Ads `cost`(`cost_micros`) · LinkedIn `costInLocalCurrency` · Naver `salesAmt`. → 우리 A1 `ad_cost_krw`와 동일 문제.
- **노출 동의어**: Google `impressions` · Meta `reach`/`impressions` · TikTok `views`.
- **campaign_id**: `campaign_id` vs `campaignId` vs `campaign-id` vs `cid`.
- **날짜**: `YYYY-MM-DD` vs Unix vs `YYYYMMDD`.

→ 우리가 raw ERD·분류에서 잡은 충돌(C1~C7)이 **업계 표준 문제와 1:1 일치**. 우리만의 특이사항이 아님.

---

## ② ★ 업계 표준 패턴 — Marketing Common Data Model (MCDM)

> Improvado·Funnel·Adverity 공통 = **단일 표준 스키마에 모든 소스를 매핑**. "one field name, one data type, one unit of measurement for every marketing concept."

| 업계 방식 | 구체 (출처) | = 우리 |
|---|---|---|
| **canonical 스키마** | "single standardized schema all sources map into" | canonical data contract |
| **mapping table = schema contract** | "a mapping table that documents every source's field name, data type, and transformation logic" (Improvado) | **채널별 declarative translator + contract** (리서치 ⓓ·ⓔ) |
| **field 변환 예시** | Google `cost_micros` → `ad_spend`(USD) · Meta Unix ts → ISO 8601 · 모든 campaign ID → `campaign_id` (Improvado) | ad_cost_krw·report_date·campaign_id 결정과 동일 |
| **통화 정규화** | "converting all spend to a base currency" | conversion config (KRW) |
| **타임존 정규화** | "aligning timestamp reporting to UTC/standard zone" | report_date KST |
| **ID 조정** | "mapping platform-specific identifiers to canonical formats" | campaign crosswalk (C5) |
| **dimensional model** | fact(impressions/clicks/conversions) + dimension(campaign/channel/time) | measure vs dimension/metric 분리 |
| **rule-based 추출** | 캠페인명에서 regex로 market/카테고리 추출(Funnel) | campaign_name 파싱 |

### ★ 값 표현 = "siloed + unified 나란히" (= 우리 lineage 결정 검증)
> Funnel "Data Explorer" = **플랫폼 원본(siloed) 필드와 통합(unified) 필드를 *나란히* 표시.** → 우리 §1.5 "정규화값 + 원본 lineage 보존" 결정이 **업계 관행과 일치**. 원본을 버리지 않는다.

### 거버넌스 (= 우리 RED 테스트·Status·schema_version 방향)
- Improvado: **250+ 데이터 품질 룰**(중복·예산·attribution 검증) + **실시간 스키마 모니터링 2년 변경이력** + **backwards-compatible 변환**(API 진화 시 과거 데이터 보존).
- → 우리 "살아있는 문서 RED 테스트" · `schema_version`+append-only(memory `extension_ease`) · drift 검출과 같은 결.

---

## ③ ★★ MER / Blended ROAS — "채널 ROAS 비교불가"의 업계 정답

> 우리 §1.5 "비교성 ⚠"(채널 ROAS는 attribution 달라 cross-channel 비교 위험)의 **업계 표준 해법**. 이게 이번 리서치 최대 수확.

- **ROAS** = `채널 매출 ÷ 채널 광고비` (캠페인 단위, 전술 최적화용).
- **MER**(Marketing Efficiency Ratio) = `총 매출 ÷ 총 마케팅비` (= blended ROAS = eROAS = TACoS류). 전사·전략·신뢰용.
- **왜 채널 ROAS는 cross-channel 신뢰 불가**: 각 플랫폼은 *자기가 직접 추적한 전환만* 귀속 → halo·멀티터치 누락 + **과대보고**. 실측 예: DTC 브랜드가 Meta Ads Manager ROAS **2.0**인데 전채널 **MER 3.5** (75% 격차 — paid social의 halo가 플랫폼 지표엔 안 보임).
- **쓰임 분리**: MER=빅픽처·전사·리포팅 / ROAS=개별 캠페인 전술 최적화. **둘 다** 두되 역할 구분.
- 변종: **aMER**(신규고객 MER) · **TACoS**(총광고비/매출).

### → 우리 적용
1. **블렌디드 지표를 1급으로**: `mer`(=`total_revenue / total_ad_cost`) 신설. **우리 "전사 ROAS 18.3M 분모"가 사실상 MER/blended ROAS였음** — 이제 정식 명명·정의.
2. **채널 ROAS = `{channel}_roas_x`, 비교성 ⚠ "inflated, cross-channel 합산금지"** 박제 (업계 28~40% 과대 통설 + 2.0 vs 3.5 실례).
3. **파생은 computed 재계산** 확정 — 채널 보고 ROAS는 lineage 대조용만, 의사결정은 raw measure(spend/revenue)로 재계산한 MER·channel ROAS.

---

## ④ 우리 설계 — 검증/보강 종합

| 우리 결정 | 업계 | 판정 |
|---|---|---|
| canonical data contract (mapping table) | Improvado MCDM "mapping table = schema contract" | ✅ 검증 |
| 채널별 declarative translator + config | Funnel "editable field mapping + smart normalisation" | ✅ 검증 |
| 통화·타임존·ID 정규화 (conversion config) | 업계 표준 기능 | ✅ 검증 |
| 정규화값 + 원본 lineage 보존 (§1.5) | Funnel "siloed + unified 나란히" | ✅ 검증 |
| 파생(ROAS) computed 재계산 + 비교성 flag | MER/blended ROAS·채널 과대보고 | ✅ 검증 + ★MER 신설 |
| measure(cleaned) vs metric(computed) | fact/dimension dimensional model | ✅ 검증 |
| 살아있는 문서·RED·schema_version | 데이터 품질룰·스키마 이력·backward-compat | ✅ 검증 |
| 이름 `ad_cost_krw` | 업계 `ad_spend` (단위접미 없음) | ◯ 우리 `_krw` 접미가 더 명시적 — 유지 |

**보강(신규)**: ① **MER/blended ROAS** 1급 지표(computed) ② 채널 ROAS 과대보고 = 비교성 flag 근거 강화 ③ 거버넌스(품질룰·스키마이력)를 contract에 명문.

---

## ⑤ 반영 위치
- [normalize_canonical_naming](../normalize_canonical_naming_v0.1.md): computed 지표에 `mer`(blended) 추가 + 채널 ROAS 비교성 ⚠ 근거(28~40% 과대) 보강.
- [ERD/INDEX §3 로드맵](../INDEX.md): 지표 registry에 MER/blended·채널 ROAS·TACoS 포함. 거버넌스(품질룰·스키마이력) = contract 항목.

---

## 출처
- [Improvado — Data Integration Challenges (MCDM·mapping table·governance)](https://improvado.io/blog/data-integration-challenges)
- [Funnel.io — Data transformation examples (field harmonization·rule-based)](https://funnel.io/blog/data-transformation-examples) · [Data integration](https://funnel.io/data-integration)
- [Northbeam — MER vs ROAS (formulas·cross-channel)](https://www.northbeam.io/blog/marketing-efficiency-ratio-mer-roas)
- [Improvado vs Supermetrics (ETL·normalization)](https://improvado.io/blog/improvado-vs-supermetrics) · [Funnel vs Supermetrics vs Adverity](https://funnel.io/supermetrics-vs-adverity)
- [Marketing data warehouse schema (dimensional·canonical channel)](https://www.analyticalalley.com/knowledge-hub/marketing-data-warehouse-schema)

## 변경 이력
| 날짜 | 내용 |
|---|---|
| 2026-06-14 | v1 — 업계(Funnel·Improvado·Northbeam) raw→표준 변환 실무 조사. MCDM·mapping table·siloed+unified·MER/blended ROAS. 우리 설계 8/8 검증 + MER 보강. |
