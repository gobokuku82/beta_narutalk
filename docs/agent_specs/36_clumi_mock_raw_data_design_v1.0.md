# 36 — clumi Mock Raw Data 설계 (POC)

> POC = **clumi 단일 client**. Batch 2~6 시각화에 필요한 데이터는 `data/clumi/raw/` 에 **표준 영어 컬럼명** mock raw 로 생성. 본 문서가 *그 설계의 단일 진실 소스* — 신규 dataset 은 *여기 정의 → 사용자 검토 → 생성*.

## 0. 원칙

| 항목 | 내용 |
|---|---|
| client | clumi 단일 (별 blooming dataset·normalizer 없음 — MVP+ 연기) |
| 위치 | `data/clumi/raw/{name}.csv` (data/ gitignore → 로컬. 본 문서가 git 추적 명세) |
| 컬럼명 | 표준 영어 snake_case → tool 이 그대로 fit (normalizer 불필요) |
| schema 정합 | `backend/app/schemas/inputs/{name}.py` Pydantic 필드명 = 컬럼명 (단일 집중) |
| 등록 | `FileDataSource.DEFAULT_MAPPING` 에 `source_id → filename` 1줄 |
| 절차 | 본 문서에 dataset 추가 → 검토 → CSV+schema+mapping → pipeline (memory `feedback_mock_raw_design_doc_first`) |
| 값 | 시연용 임의 mock. 의미상 그럴듯하게(코스메틱 브랜드 "블루밍글로우"). 정답 비교 대상 X (clumi 정답 17 과 무관) |

관련 spec: [68 Pipeline Catalog](68_pipeline_catalog_v1.0.md) (각 시각화 정의) · [65 Dashboard Pages](65_dashboard_pages_v1.0.md).

---

## 1. campaigns.csv ✅ (Batch 2 — Dashboard v1)

캠페인 마스터 (period 무관 — 캠페인 단위 행). schema: `schemas/inputs/campaigns.py` (`CampaignRow`).
사용 시각화: K10(총수)·K11(진행중)·K12(월예산)·K13(목표ROAS)·T04(테이블).

| 컬럼 | 타입 | 의미 |
|---|---|---|
| campaign_id | str | 캠페인 식별자 (예: BRP-001) |
| campaign_type | str | brand·product·retargeting·search·sns |
| name | str | 캠페인명 |
| product | str | 관련 상품 |
| start_date | str | YYYY-MM-DD |
| end_date | str | YYYY-MM-DD |
| monthly_budget | int | 월예산 (KRW) |
| goal | str | 캠페인 목표 (자유 텍스트) |
| status | str | **active · ended · scheduled** (표준값) |
| owner | str | 담당자 |
| target_roas | float | 목표 ROAS (%) |
| target_cpa | float | 목표 CPA (KRW) |
| target_conversions | int | 목표 전환수 |

현 mock: 12 행 (active 8 / ended 2 / scheduled 2).

---

## 2. daily_performance.csv ✅ (Batch 2·3 — Dashboard v1·Channel)

일별 × 매체 × 캠페인 성과. schema: `schemas/inputs/daily_performance.py` (`DailyPerfRow`).
사용 시각화: C04(일별 라인) · **Batch 3** C05(매체별 막대)·C06(퍼널)·T05(매체 테이블).

| 컬럼 | 타입 | 의미 |
|---|---|---|
| date | str | YYYY-MM-DD |
| channel | str | google·naver·meta·kakao (매체) |
| campaign_id | str | campaigns.csv FK |
| impressions | int | 노출수 |
| clicks | int | 클릭수 |
| ctr | float | 클릭률 (%) |
| conversions | int | 전환수 |
| cvr | float | 전환율 (%) |
| cpc | float | 클릭당 비용 (KRW) |
| roas | float | ROAS (%) |
| cpa | float | 전환당 비용 (KRW) |
| ad_cost | int | 광고비 (KRW) |
| conversion_revenue | int | 전환매출 (KRW) |
| cpm | float | 1000회 노출당 비용 (KRW) |
| creative_id | str | 소재 식별자 (creatives.csv FK — Batch 5) |

현 mock: 32 행 (2026-04-01~08, 8일 × 4 매체).

> **Batch 3 = 신규 데이터 불필요** — 본 dataset 의 `channel` 집계만 추가.

---

## 3. reviews.csv ✅ (Batch 4 — Trend) — 승인·생성·구현 완료

리뷰 (감성·키워드 ml_mock 대상). 사용: C08(감성 도넛)·C12(키워드 랭킹)·O03(최근 리뷰 카드).
ml 결과(감성·키워드)는 raw 에 박지 않고 **ml_model(MockMlModel)** 이 `data/ml_mock/{sentiment,keywords}/clumi.json` 반환 (ADR-028 B2b).

| 컬럼(제안) | 타입 | 의미 |
|---|---|---|
| review_id | str | 리뷰 식별자 |
| date | str | 작성일 YYYY-MM-DD |
| product | str | 대상 상품 |
| rating | int | 평점 1~5 |
| text | str | 리뷰 본문 (감성·키워드 분석 입력) |

→ Batch 4 진입 시 컬럼 확정 + 생성.

---

## 4. creatives.csv ✅ (Batch 5 — Creative) — 승인·생성·구현 완료

광고 소재 마스터. 사용: K18(총수)·K19(평균CTR)·K20(평균ROAS)·K21(피로 소재수)·C11(AI 5축)·O04(소재 카드).
**AI 5축·피로 = raw 아님** → ml_model(MockMlModel) 이 `data/ml_mock/{ai_axes,fatigue}/clumi.json` 반환 (ADR-028 B2b, M3 어댑터). raw 는 식별·카피·소재단위 성과만.

| 컬럼(제안) | 타입 | 의미 |
|---|---|---|
| creative_id | str | 소재 식별자 (daily_performance.creative_id FK) |
| campaign_id | str | campaigns.csv FK |
| name | str | 소재명 |
| channel | str | 매체 (google·naver·meta·kakao) |
| format | str | image·video·carousel |
| headline | str | 카피 헤드라인 |
| body | str | 카피 본문 |
| image_url | str | 썸네일/이미지 URL |
| landing_url | str | 랜딩 URL |
| start_date | str | 집행 시작 YYYY-MM-DD |
| status | str | active·ended·paused |
| frequency | float | 노출 빈도 |
| run_days | int | 집행 일수 |
| ctr | float | 소재 CTR (%) |
| cvr | float | 소재 CVR (%) |
| cpc | float | CPC (KRW) |
| roas | float | ROAS (%) |
| cpa | float | CPA (KRW) |

→ K19/K20 = `ctr`/`roas` 평균, K18 = count, K21 = ml_model fatigue, C11 = ml_model ai_axes.

---

## 5. ab_tests.csv ✅ (Batch 5 — Creative) — 승인·생성·구현 완료

AB 테스트 결과 (T06 테이블). winner 는 tool 이 a_value/b_value 비교로 파생 (raw 아님).

| 컬럼(제안) | 타입 | 의미 |
|---|---|---|
| test_id | str | 테스트 식별자 |
| name | str | 테스트명 |
| metric | str | 비교 지표 (ctr·cvr·roas 등) |
| variant_a | str | A안 소재 (creative_id 또는 설명) |
| variant_b | str | B안 소재 |
| a_value | float | A안 지표값 |
| b_value | float | B안 지표값 |

→ 7 컬럼. winner·lift = tool 파생.

---

## 6. budget_allocation.csv ✅ (Batch 6 — Cost) — 승인·생성·구현 완료

예산 배분 (구분 × 채널 매트릭스). 사용: K22(총예산)·K23(집행률)·C09(채널 비중 도넛)·C10(누적 막대).

| 컬럼(제안) | 타입 | 의미 |
|---|---|---|
| segment | str | 구분 (캠페인 유형 그룹 — 누적 막대 x축) |
| campaign_type | str | 캠페인 유형 |
| naver_budget | int | 네이버 예산 (KRW) |
| kakao_budget | int | 카카오 예산 (KRW) |
| meta_budget | int | 메타 예산 (KRW) |
| google_budget | int | 구글 예산 (KRW) |
| total_budget | int | 총 예산 (KRW) |
| exec_rate | float | 집행률 (%) |

→ 채널 컬럼명(naver/kakao/meta/google) = 표준 영어 (normalizer 불필요).

---

## 7. keyword_performance.csv ✅ (Batch 6 — Cost) — 승인·생성·구현 완료

키워드 성과. 사용: K24(평균 ROAS + 운영 수)·T07(ROI Top12 + 경쟁 Badge).

| 컬럼(제안) | 타입 | 의미 |
|---|---|---|
| keyword | str | 키워드 |
| channel | str | 매체 |
| impressions | int | 노출수 |
| clicks | int | 클릭수 |
| conversions | int | 전환수 |
| ad_cost | int | 광고비 (KRW) |
| conversion_revenue | int | 전환매출 (KRW) |
| roas | float | ROAS (%) |
| competition | str | 경쟁강도 (high·mid·low — T07 Badge) |
| quality_score | float | 품질지수 |
| keyword_group | str | 키워드 그룹 |

> **O05 AI 추천** = raw 아님. `ai_recommendation_tool` → `ml_model.generate_recommendation` → POC `MockMlModel`(`data/ml_mock/recommendations/clumi.json`) / MVP+ `LlmMlModel` swap. 베타 0.001 (단순 prompt).

---

## 변경 이력

| 일자 | 내용 |
|---|---|
| 2026-05-28 | 초안 — POC clumi 단일 mock raw 설계 단일 소스. §1 campaigns·§2 daily_performance 소급 정리(Batch 2 생성분). §3~5 reviews·creatives·ab_tests = Batch 4·5 진입 시 컬럼 확정 placeholder. memory `feedback_mock_raw_design_doc_first`·`project_poc_single_client_clumi`. (60→30번대 정정: 69→36) |
| 2026-05-28 (검토 요청) | §4 creatives (18 컬럼: 식별·카피·소재단위 성과) + §5 ab_tests (7 컬럼) **구체 제안 → 사용자 검토 대기**. ML 결과(AI 5축·피로·감성·키워드) = raw 아님, MockMlModel(M3) 제공 명시. Batch 3 = 신규 데이터 불필요(daily_performance 재사용) 확정. |
| 2026-05-28 (§1~5 생성) | §1~5 (campaigns·daily_performance·reviews·creatives·ab_tests) **승인·생성·구현 완료** (Batch 2·3·4·5 = 45 pipeline). §6 budget_allocation·§7 keyword_performance **구체 제안 → Batch 6 검토 대기**. O05 추천 = MockMlModel.generate_recommendation 명시. |
| 2026-05-28 (§6·7 생성) | §6 budget_allocation(5행)·§7 keyword_performance(18행) **승인·생성·구현 완료** (Batch 6 = Cost 7 pipeline). **🎉 전체 52 pipeline 백엔드 완성.** O05 AI 추천 = MockMlModel.generate_recommendation(`recommendations/clumi.json`) 작동. |
