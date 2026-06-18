# 02. collection_agent — 채널별 데이터 수집 (광고 성과 5 + 콘텐츠 4)

## 메타

| 항목 | 값 |
|---|---|
| 소속 팀 | analysis_team |
| handles_tasks | `data_collection` |
| Tool 수 | **1 implemented + 8 stub (총 9)** — 콘텐츠 4 + 광고 성과 5 |
| 현재 구현률 | ~11% (1/9) |
| team_catalog 위치 | [team_catalog.yaml collection_agent 블록](../../../backend/app/dream_agent/planning/catalog/team_catalog.yaml) |

## 입출력

- **입력**: `brand` (필수), `source` / `period` / `limit` / `campaign_id` (선택)
- **출력 (도메인별 분기)**:
  - 콘텐츠 수집 → `raw_reviews` (list[dict])
  - 광고 성과 수집 → `raw_ads` (list[dict])
- **다음 에이전트**:
  - raw_reviews → text_preprocessing (자연어 정제)
  - raw_ads → channel_normalizing (format_normalizer.ads.v1 → daily_performance 통일)

## Tool 목록 (9)

### 콘텐츠 수집 (4) — produces: `raw_reviews`

| Tool | Status | 카드 | 비고 |
|---|---|---|---|
| **review_collector** | ✅ implemented (v0.2.0) | [→](../tools/implemented/review_collector.md) | D2 결정 — source 파라미터로 출처 분기 (naver_*/oliveyoung 등) |
| youtube_collector | 🟡 stub | (Phase 1A) | 영상 추출 + 댓글 + 자막 별도 로직 |
| coupang_collector | 🟡 stub | (Phase 1A) | 쿠팡 상품 리뷰 |
| oliveyoung_collector | 🟡 stub | (Phase 1A) | 올리브영 — review_collector.source 로 흡수 가능 / 별도 special 로직 시 분리 |

### 광고 성과 수집 (external 활성, ADR-022 helper-B 패턴)

> ⑫ (2026-06-01): broken 5 collector (meta·google_ads·naver_sa·naver_gfa·kakao) 폐기됨. external 신 패턴 (`RawCollectorBase` + `_FILE_NO_TO_SOURCE_ID`) 활성. data/clumi/raw/ 표준 raw 파일 사용. 신 ads chain = MVP+ 결정 (작업 ⑭ team_catalog 등재).

| Tool (external/) | Status | source | API 버전 |
|---|---|---|---|
| meta_ads_performance_collector | ✅ implemented | data/clumi/raw/meta_ads_performance.json | Marketing API v25.0 |
| meta_ads_by_age_collector | ✅ implemented | data/clumi/raw/meta_ads_by_age.json | 동일 (연령별 분리) |
| meta_instagram_inapp_collector | ✅ implemented | data/clumi/raw/meta_instagram_inapp.json | Instagram In-App |
| naver_searchad_collector | ✅ implemented | data/clumi/raw/naver_searchad.json | OpenAPI |
| naver_advoost_collector | ✅ implemented | data/clumi/raw/naver_advoost.csv | OpenAPI |
| naver_interest_alert_collector | ✅ implemented | data/clumi/raw/naver_interest_alert.csv | OpenAPI |
| naver_talktalk_collector | ✅ implemented | data/clumi/raw/naver_talktalk.json | OpenAPI |
| kakao_bizmessage_collector | ✅ implemented | data/clumi/raw/kakao_bizmessage.json | Kakao Biz Message |

→ Google Ads / Naver GFA = POC clumi 범위 외 (data/clumi/raw/ 부재).
→ 신 ads chain (`format_normalizer.ads.v1` 통합) = MVP+ 결정 (작업 ⑭).
→ **진실 소스**: [data/raw/raw_data.xlsx](../../../data/raw/raw_data.xlsx) (실 API 칼럼 레퍼런스 v2)

## 데이터 흐름

```
콘텐츠 수집 (review_collector helper-B, ⑫.B):
  data/clumi/raw/reviews.csv → review_collector ─► raw_reviews
                                                   │
                                                   ▼
                                            review_normalizer
                                                   ▼
                                            text_preprocessor
                                                   ▼
                                                분석 단계

광고 성과 수집 (external 활성, ⑫.A 후 ADR-022 helper-B):
  data/clumi/raw/meta_ads_performance.json → meta_ads_performance_collector ─┐
  data/clumi/raw/naver_searchad.json       → naver_searchad_collector       ─┤
  data/clumi/raw/kakao_bizmessage.json     → kakao_bizmessage_collector     ─├─► (개별 raw)
  data/clumi/raw/naver_advoost.csv         → naver_advoost_collector        ─┤
  data/clumi/raw/naver_talktalk.json       → naver_talktalk_collector       ─┘
                                                                              │
                                                                              ▼
                                                       (format_normalizer.ads.v1 통합 chain
                                                        = MVP+ 작업 ⑭ 결정. format_normalizer
                                                        dependencies: [] 임시 상태)
```

## HITL 카테고리 (D12)

| 카테고리 | 본 에이전트 해당 | 비고 |
|---|---|---|
| 조회·자동 | ✅ (자동 수집) | 매일 02:00 batch |
| 생성 후 | — | |
| 실행 전 | — | |
| 외부 발송 | — | |

→ 조회 카테고리 — 자동 실행, 게이트 없음.

## Phase 진입

| Phase | 본 에이전트의 작업 |
|---|---|
| Phase 0 (현재 v0.2+) | ✅ review_collector implemented + 8 stub 박제 (4 콘텐츠 + 5 광고) |
| **Phase 1A** | 5 광고 collector 구현 — mock raw CSV read (mock 4종 이미 존재 + naver_gfa mock 신규) |
| **Phase 1B** | 4 콘텐츠 collector 구현 — youtube/coupang/oliveyoung 별도 source 로직 또는 review_collector 흡수 |
| **Phase 6+** | mock → 실API 전환 (매체별 sprint — Meta v25 / Google v24.1 / Naver SA / Naver GFA Beta / Kakao v4) — v2 deprecation 30건 처리 |

## ⚠️ 수정 시 함께 변경 영역

| 영역 | 파일 / line | 변경 시 |
|---|---|---|
| **team_catalog.yaml** | L29-56 collection_agent 블록 | Tool 추가/제거 |
| **LLM Prompts stage2** | `llm_manager/prompts/planning_stage2_agent.yaml` | (영향 적음 — agent 이름 그대로) |
| **LLM Prompts stage3** | `planning_stage3_todo.yaml` | Tool 이름 + 예시 todo (Tool rename 시) |
| **LLM Prompts response** | `response.yaml` | 예시 (Tool 이름) |
| **task_agent_hints** | `team_catalog.yaml` L233 (`data_collection: collection_agent`) | (변경 적음) |
| **Frontend (부수)** | `frontend/src/features/workflow/editing/PropertyPanel.tsx` | placeholder |
| **Dashboard (부수)** | `dashboard/index.html` | (현재 collection Tool 분기 없음) |
| **Spec 32 §7.1** | Tool 행 / 카운트 | Tool 추가 시 |
| **Spec 31** | collection_agent 요구사항 | |
| **TOBE_MVP/01** | 매트릭스 §2 collection 행 | |
| **TOBE_MVP/02** | 짧은 카드 collection | |
| **본 폴더 00_overview** | §2 표 + §3 8 implemented 표 | |
| **데이터 source** | `data/mock/mock_data_review_trends.csv` + (신규 raw CSV — Phase 1A 시) | |
| **ADR** | M2 시 ADR (네이버 SA / Meta API 전환 결정) | |
| Tests | `backend/tests/sprint*/test_*collect*.py` | |

→ 상세 = [40 §3.A Tool 추가](../../agent_specs/40_agent_tool_lifecycle_v1.0.md) + [41 §6 예시](../../agent_specs/41_agent_tool_change_hub_v1.0.md).

## 참조 코드

- Tool 코드 폴더: [`backend/app/dream_agent/tools/collection/`](../../../backend/app/dream_agent/tools/collection/)
- Tool 메타 폴더: [`backend/app/dream_agent/tools/catalog/collection/`](../../../backend/app/dream_agent/tools/catalog/collection/)
- team_catalog: [planning/catalog/team_catalog.yaml L29-56](../../../backend/app/dream_agent/planning/catalog/team_catalog.yaml)
- helpers (mock CSV 로드): [`tools/shared/helpers.py:load_mock_csv`](../../../backend/app/dream_agent/tools/shared/helpers.py)

## 참조 spec

- [17 §2 9~10 에이전트](../../agent_specs/17_functions_to_io_v1.0.md)
- [32 §7.1 collection 카테고리](../../agent_specs/32_execution_agent_tools_v1.0.md)
- [TOBE_MVP/02 collection 카드](../../_claude/tool/TOBE_MVP/02_agent_cards.md)

## 참조 비전 (한국어 narrative)

- [agent_design/02_수집_에이전트.md](../../_claude/referrence/agent_design/02_수집_에이전트.md) — 수집 비전 + 7 raw 테이블 + 매체 API 전환 계획

## 📍 Mock vs 실API 분기 (Phase 6+ 마크) ⚠️

- POC: `mock_data_review_trends.csv` (35 행)
- MVP+ (Phase 6+): 매체별 실 API 전환
  - 네이버 성과형광고 API
  - Meta Marketing API v21.0
  - 네이버 DataLab API
  - 카카오모먼트 / Google Ads API
  - 네이버 블로그/쇼핑 크롤러 / 올리브영 크롤러
- 전환 패턴: `USE_MOCK_DATA` env 분기 (각 collector 내부)
- 데이터 ERD: [RELATIONSHIPS §1 Mermaid](../../../data/description/mock/RELATIONSHIPS.md)
- ROADMAP: [data/description/mock/ROADMAP](../../../data/description/mock/ROADMAP.md)

## Drift / 결정

- **D2** 🔵 Resolved — naver_collector → review_collector rename + 일반화 (2026-05-19, commit 2138798)
- **D1** 🔵 Resolved — 매체별 raw CSV 4종 자동 생성 완료 (2026-05-19, commit 8d1a19c)
- **D3** 🟢 Decided — external_variables 데이터 (사용자 작업 중)
- **D10** 🟢 Decided — 브랜드 디자인 자산 mock 신설 (사용자 작업 중)
- **D17** 🟢 Decided — 5 광고 + 4 콘텐츠 = 9 Tool 단일 collection_agent + Tool 폴더 분류 (POC 적합, Phase 4+ 에이전트 분리 검토)
- **Naver GFA 신규** — raw_data.xlsx v2 발견, OpenAPI Beta 출시 (v1 시점 미공개)
- ADR (Phase 6+): 매체별 실API 전환 결정 박제 — v2 deprecation 30건 처리

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-19 | 카드 초안 + D2 Resolved 박제 |
| 2026-05-19 | 9 Tool 확장 — 5 광고 (meta/google_ads/naver_sa/naver_gfa/kakao) 신규 stub + 데이터 흐름 2 분기 (raw_reviews / raw_ads) + D1 Resolved + D17 박제 |
