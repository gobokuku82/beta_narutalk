# 33. Collection tools — 인벤토리

| 항목 | 내용 |
|---|---|
| 카테고리 | **collection** |
| 의도 (32 §2.5) | raw 데이터를 외부 API / 내부 DB / 파일에서 가져온다 |
| 핵심 동사 | fetch, load, get |
| 출력 모양 | raw dict/list/DataFrame |
| 짝 문서 | [32 §2.5](../32_execution_agent_tools_v1.0.md) |

## tool 목록

> 카테고리 재배치 단계에서 채워짐. 아래는 현 디렉토리 분포 (2026-05-30 시점).

### sub: external (외부 플랫폼)

| name | input | output | status | 의도 |
|---|---|---|---|---|
| meta_ads_performance_collector | — | raw json | partial | Meta 광고 성과 raw |
| meta_ads_by_age_collector | — | raw json | partial | Meta 연령 분포 raw |
| meta_instagram_inapp_collector | — | raw json | partial | Instagram 인앱 raw |
| instagram_engagement_collector | — | raw json | partial | Instagram 인게이지먼트 raw |
| naver_searchad_collector | — | raw json | partial | 네이버 검색광고 raw |
| naver_advoost_collector | — | raw csv | partial | 네이버 ADVoost raw |
| naver_talktalk_collector | — | raw json | partial | 네이버 톡톡 raw |
| naver_interest_alert_collector | — | raw csv | partial | 네이버 관심 알림 raw |
| kakao_bizmessage_collector | — | raw json | partial | 카카오 비즈메시지 raw |
| ga4_traffic_source_collector | — | raw jsonl | partial | GA4 트래픽 소스 raw |
| ga4_page_events_collector | — | raw jsonl | partial | GA4 페이지 이벤트 raw (265MB stream) |
| ad_change_history_collector | — | raw json | partial | 광고 변경 이력 raw |
| household_structure_collector | — | raw csv | partial | 가구 구조 raw |

### sub: internal (내부 데이터)

| name | input | output | status | 의도 |
|---|---|---|---|---|
| orders_collector | — | DataFrame | complete | 주문 raw |
| customers_collector | — | DataFrame | complete | 회원 raw |
| customer_rfm_collector | — | DataFrame | complete | RFM raw |
| customer_grade_history_collector | — | DataFrame | complete | 등급 이력 raw |
| signup_events_collector | — | DataFrame | complete | 가입 이벤트 raw |
| category_sales_collector | — | DataFrame | complete | 카테고리 매출 raw |
| crm_messages_collector | — | text | partial | CRM 메시지 raw |
| promotions_collector | — | text | partial | 프로모션 raw |

### sub: 작업 ⑫ (2026-06-01) 정리 완료

| name | status | 비고 |
|---|---|---|
| meta_collector · kakao_collector · naver_sa_collector · naver_gfa_collector · google_ads_collector | ✅ 폐기 (⑫.A) | broken (load_mock_csv + ADR-027 권한 위반). external/{meta_ads_performance, kakao_bizmessage, naver_searchad, naver_advoost...} 대체재 활성. google_ads = POC clumi 범위 외 |
| review_collector | ✅ 신 패턴 (⑫.B) | helper-B 재작성. `self.fetch("reviews", context)` → raw_reviews 통째. ADR-027 §1 Tool 권한 정합 (RC-05 자동 검증) |

## anti-pattern

- **client 하드코딩** — collector 가 특정 회사명(`clumi`) 직접 참조. → `context.client_id` 사용.
- **raw 자체 변환** — collector 안에서 컬럼명 통일·계산 (= normalization·metrics 책임). collector 는 *가져오기만*.
- **stream 처리 잘못** — 대용량(예: ga4_page_events 265MB) 을 list 전체 로드. → `FileDataSource.stream_jsonl` 사용.
