# 33. Cleaning tools — 인벤토리

| 항목 | 내용 |
|---|---|
| 카테고리 | **cleaning** |
| 의도 (32 §2.5) | 데이터 자체 정제 (결측·이상치·비즈니스 필터·검증·보정) |
| 핵심 동사 | filter, validate, impute, correct |
| 출력 모양 | 정제된 DataFrame/dict |
| 짝 문서 | [32 §2.5](../32_execution_agent_tools_v1.0.md) |

## 판정 기준 (vs normalization)

- 컬럼·형식 통일 = **normalization**
- 행 단위 처리 (제거·보정·검증) = cleaning ✅
- 비즈니스 정의에 따른 필터(C40 취소 등) = cleaning ✅

## tool 목록

| name | input | output (produces) | status | 의도 |
|---|---|---|---|---|
| active_orders_filter | orders | orders_active · count · dropped | complete | order_status='C40'(취소) 제거 + 기간 필터 |
| member_metrics_validator | orders · customers | validated_customers · mismatches · mismatch_count · customer_count · active_orders_member | complete | customers 누적 vs orders 실측 보정 |
| missing_value_diagnostic | source_id | column_stats · classification | complete | 결측 통계 + 의미있는 NaN 분류 |

## sub-category 후보 (현 tool 적음)

| sub | 의도 | 적용 가능 시 |
|---|---|---|
| filter | 비즈니스 필터 (취소·환불 등) | tool 수 5+ |
| validate | 데이터 무결성 검증 | tool 수 3+ |
| impute | 결측 채움 | tool 수 3+ |
| outlier | 이상치 탐지·제거 | tool 수 3+ |

## anti-pattern

- **카테고리 의도 흐림** — preprocessing(자연어) 와 혼동. cleaning = *정형 데이터* 처리.
- **계산 끼움** — 분리된 metric 산출 X (총합·평균 등). 단 cleaning 결과 옆에 *보조 메타* (count·dropped·mismatch_count 등) 는 OK — 정제 결과 검증·로깅 용. 본격 계산은 metrics 카테고리.
