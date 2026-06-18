# 33. Normalization tools — 인벤토리

| 항목 | 내용 |
|---|---|
| 카테고리 | **normalization** |
| 의도 (32 §2.5) | raw 의 컬럼명·형식·단위·시간대를 표준 schema 로 통일 (의미 변경 X) |
| 핵심 동사 | unify, standardize, map |
| 출력 모양 | 표준 schema 의 DataFrame/dict/list |
| 짝 문서 | [32 §2.5](../32_execution_agent_tools_v1.0.md) |
| tool 수 | **6** (2026-05-30) |

## 판정 기준 (vs cleaning·metrics)

- 컬럼명 통일·코드값 매핑·시간대 변환 = normalization ✅
- 결측·이상치·취소 행 제거 = **cleaning**
- 합산·평균·분배 계산 = **metrics**

## tool 목록

### dashboard1 / methodology 라인 (4)

| name | input | output | status | 의도 |
|---|---|---|---|---|
| utm_normalizer | orders | source/medium dist | complete | `(not set)`→`unknown` 등 UTM 정규화 |
| channel_attribution_normalizer | orders | by_raw/by_group/mapping | complete | 10채널 → 그룹 매핑 (Meta/Naver/CRM 등) |
| grade_system_unifier | customers · grade_history | standard_grade_dist | complete | 등급 체계 표준 통일 (WELCOME~VIP) |
| kst_timezone_normalizer | ga4 jsonl | total + boundary_shifts | complete | UTC → KST 시간대 변환 |

### 분석 team 라인 (2 — ADR-014 v2 단일책임 분리)

| name | input | output | status | 의도 |
|---|---|---|---|---|
| format_normalizer | 5매체 ads raw (meta·google·naver_sa·naver_gfa·kakao) | normalized_ads (ads.v1) | complete | 광고 5매체 raw → daily_performance 통일 스키마 |
| review_normalizer | raw_reviews (naver_blog·shopping·cafe·oliveyoung) | normalized_reviews (review.v1) | complete | 4 출처 리뷰 raw → 통일 review 스키마 |

## anti-pattern

- **계산 끼움** — 통일 후 합산까지 한 tool 에서 처리. → metrics 로 분리.
- **의미 변경** — `direct` 를 `paid` 로 바꾸는 등 의미 변형. normalization 은 *표현만* 통일.
- **다도메인 분기** (ADR-014 v2 anti-pattern) — `domain` 매개변수로 ads/review 처리 분기. → 단일 책임 분리 (format_normalizer + review_normalizer).

## 변경 이력

- 2026-05-30: preprocessing/data_normalization/ 폐기 — format_normalizer · review_normalizer 가 normalization 으로 이동 (32 §2.5 정합).
