# review_collector — 리뷰 수집 (전 출처 일반화)

> **D2 결정 반영 (2026-05-19 commit 2138798)** — naver_collector → review_collector rename + 출처 일반화.
> 자사·경쟁사 + 전 출처(naver_blog / naver_shopping / naver_cafe / oliveyoung 등) 리뷰를 통합 수집.

## 메타

| 항목 | 값 |
|---|---|
| 소속 에이전트 | collection_agent |
| 카테고리 (YAML) | `data` (※ 폴더 위치는 `collection/` — Spec 32 §7.1 매트릭스는 collection 카테고리로 표기) |
| Status | ✅ implemented |
| 버전 | 0.2.0 (rename 시 minor bump) |
| **Status 마커** (docstring) | `Status: complete — 2026-05-19 D2 결정 (naver_collector 일반화).` ✅ |
| **DC-10 정합** | docstring ✅ / YAML status 필드 없음 (정합 시 추가 권장) / team_catalog `status: implemented` ✅ |
| timeout_sec | 30 |
| max_retries | 2 |
| requires_approval | false |
| has_cost / estimated_cost | false / 0.0 (mock 파일 로드만) |

## 입출력 계약

### 입력 (params)

| name | type | required | default | 설명 |
|---|---|---|---|---|
| brand | string | ✅ | — | 브랜드명 (예 "블루밍글로우") |
| source | string | optional | — | 출처(`naver_blog` / `naver_shopping` / `naver_cafe` / `oliveyoung`). **미지정 = 전체 출처** |
| period | string | optional | `"30d"` | 기간(`7d` / `30d` / `90d` / `all`) |
| limit | integer | optional | `100` | 최대 행 수 |

### 입력 (context)
- `context.previous_results` 사용 안 함 (체인 시작점 Tool)

### 출력 (produces)
- `raw_reviews` (list[dict]) — 원시 CSV 행 그대로. **컬럼 정규화는 format_normalizer 가 담당.**
- 보조: `count`, `brand`, `source` (요청 source 또는 `"all"`), `period`

### 출력 dict 스키마

```json
{
  "raw_reviews": [
    {
      "리뷰ID": "rv_001", "브랜드": "블루밍글로우", "출처": "naver_blog",
      "텍스트": "...", "별점": 5, "감성": "positive",
      "작성일": "2025-09-15", "주요키워드": "보습력,촉촉"
    }
  ],
  "count": 100, "brand": "블루밍글로우", "source": "all", "period": "30d"
}
```

## 데이터 source

- **mock CSV**: [data/mock/mock_data_review_trends.csv](../../../../data/mock/mock_data_review_trends.csv)
- **명세**: [data/description/mock/SCHEMA.md §12 review_trends](../../../../data/description/mock/SCHEMA.md)
- 컬럼 (한글): `리뷰ID / 브랜드 / 출처 / 작성일 / 텍스트 / 별점 / 감성 / 주요키워드`
- 폴백 경로: [tools/shared/helpers.py:load_mock_csv()](../../../../backend/app/dream_agent/tools/shared/helpers.py)

## 로직 단계

1. `params` 병합 (`merge_params`) — `brand` 필수, 나머지 default 적용
2. `mock_data_review_trends.csv` 로드 (`load_mock_csv`)
3. **브랜드 필터** — `df["브랜드"].str.contains(brand)`
4. **출처 필터** — `source` 지정 시만 `df["출처"] == source`, 미지정이면 전체
5. **기간 필터** — `_filter_by_period()` (작성일 컬럼 기준, max date 부터 days 역산)
6. **limit** — `df.head(limit)`
7. `df.to_dict(orient="records")` → `raw_reviews` 반환
8. `logger.info("review_collector completed", ...)`

## 예외 처리

| 상황 | 동작 |
|---|---|
| `brand` 누락 | KeyError → BaseTool 가 예외 raise → executor 가 `tool_result.status = "FAILED"` 박제 |
| 컬럼 없음 (`브랜드`/`출처`/`작성일` 누락) | 해당 필터 skip (조건문) → 빈 결과 가능 |
| `period` 미인식 값 | 필터 적용 안 함 (그대로 반환) |
| mock 파일 부재 | `load_mock_csv()` 가 raise — 상위 fallback (`mock_tools.py`) 으로 위임 |

## 의존 Tool

- **이전**: 없음 (체인 시작점)
- **다음**: `format_normalizer` (raw_reviews → normalized_reviews)

## ⚠️ 수정 시 함께 변경 영역

| 영역 | 파일 | 어떤 변경 시 |
|---|---|---|
| Tool 코드 | [`tools/collection/review_collector.py`](../../../../backend/app/dream_agent/tools/collection/review_collector.py) | 로직 / 시그니처 |
| Tool 메타카드 | [`catalog/collection/review_collector.yaml`](../../../../backend/app/dream_agent/tools/catalog/collection/review_collector.yaml) | params / produces / status / description |
| **team_catalog.yaml** | [`planning/catalog/team_catalog.yaml`](../../../../backend/app/dream_agent/planning/catalog/team_catalog.yaml) `collection_agent.tools[review_collector]` | name / params_required/optional / produces |
| LLM Prompts (stage3) | [`llm_manager/prompts/planning_stage3_todo.yaml`](../../../../backend/app/dream_agent/llm_manager/prompts/planning_stage3_todo.yaml) | Tool 이름 + 예시 todo (D2 rename 시 변경 완료) |
| LLM Prompts (response) | [`llm_manager/prompts/response.yaml`](../../../../backend/app/dream_agent/llm_manager/prompts/response.yaml) | 예시 tool 이름 |
| **format_normalizer.yaml** | `catalog/preprocessing/data_normalization/format_normalizer.yaml` `dependencies` | ⚠️ 현재 `[naver_collector]` stale → `[review_collector]` 갱신 권장 |
| **Spec 32 §7.1** | [`agent_specs/32_*.md`](../../../agent_specs/32_execution_agent_tools_v1.0.md) | collection 카테고리 행 |
| **TOBE_MVP/01** | [`tool/TOBE_MVP/01_tool_data_matrix.md`](../../../_claude/tool/TOBE_MVP/01_tool_data_matrix.md) | Tool ↔ Data 행 |
| 본 폴더 agent 카드 | [`agents/02_collection.md`](../../agents/02_collection.md) | Tool 목록 표 |
| 본 폴더 00_overview | [`00_overview.md`](../../00_overview.md) | implemented Tool 표 |
| 본 폴더 INDEX | [`INDEX.md`](../../INDEX.md) | implemented 표 |
| Tests | [`backend/tests/sprint*/`](../../../../backend/tests/) | Planner test / E2E |

### 변경 종류별 최소 갱신
- **출처 추가** (예 youtube): YAML `parameters.source.description` + team_catalog `params_optional` 갱신 — 다른 Tool 추가는 별개 (`youtube_collector` stub)
- **컬럼 추가** (mock CSV 확장): SCHEMA.md + `_filter_by_period` 영향 없으면 코드 변경 0
- **brand alias 정규화**: 별도 helper 추가 + 로직 변경

## 참조 코드

- 구현: [`tools/collection/review_collector.py`](../../../../backend/app/dream_agent/tools/collection/review_collector.py)
- 메타: [`catalog/collection/review_collector.yaml`](../../../../backend/app/dream_agent/tools/catalog/collection/review_collector.yaml)
- 폴백 helper: [`tools/shared/helpers.py:load_mock_csv()`](../../../../backend/app/dream_agent/tools/shared/helpers.py)

## 참조 spec

- [agent_specs/17 §3 collection](../../../agent_specs/17_functions_to_io_v1.0.md)
- [agent_specs/32 §7.1 collection](../../../agent_specs/32_execution_agent_tools_v1.0.md)
- [TOBE_MVP/01 §2 collection](../../../_claude/tool/TOBE_MVP/01_tool_data_matrix.md)
- [TOBE_MVP/03 D2 Resolved](../../../_claude/tool/TOBE_MVP/03_drift_report.md)

## 참조 비전 (한국어 narrative)

- [agent_design/02_수집_에이전트.md](../../../_claude/referrence/agent_design/02_수집_에이전트.md) — 매체별 raw 수집 비전 narrative

## 📍 Mock vs 실API 분기 (Phase 6+) ⚠️

- **POC (현재)**: `mock_data_review_trends.csv` 로드만
- **MVP+ (Phase 6+)**: 매체별 실 API (네이버 검색 API / 올리브영 / 쿠팡) 권한 획득 후 `USE_MOCK_DATA` 환경변수 분기 도입
- **사용자 명시**: "수집에이전트는 지금은 mock 사용. 추후 API 권한 얻으면 연결할꺼야"
- **전환 절차**: [agent_specs/40 §3.D](../../../agent_specs/40_agent_tool_lifecycle_v1.0.md) + [data/description/mock/ROADMAP](../../../../data/description/mock/ROADMAP.md)
- **데이터 ERD**: [data/description/mock/RELATIONSHIPS.md §1 Mermaid](../../../../data/description/mock/RELATIONSHIPS.md)

## 테스트

- 단위/integration: 본 Tool 단독 테스트 부재 (sprint 시점 빠른 개발) — Phase 1A 진입 시 보강 권장
- E2E: Planner E2E 테스트가 Planner → review_collector 호출 경로 검증 ([`tests/sprint*/test_planner*.py`](../../../../backend/tests/))
- DC-10 검증: [`tests/docs/test_doc_code_contract.py`](../../../../backend/tests/docs/test_doc_code_contract.py) — docstring Status + team_catalog status 3중 일치

## Phase

| Phase | 본 Tool 의 작업 |
|---|---|
| **Phase 0 (현재 v0.2)** | ✅ implemented — D2 rename 반영 |
| **Phase 1A** | + 5 collector 신규 (youtube/coupang/oliveyoung/naver_sa/meta) → 본 Tool 은 base 패턴 |
| **Phase 6+** | mock → 실 API 전환 (`USE_MOCK_DATA` 분기) |

## Drift / 결정

- **D2** 🔵 Resolved (2026-05-19 commit 2138798) — `naver_collector` 일반화 채택
- 사유: 다른 출처(oliveyoung/naver_shopping) 도 동일 mock 시트 사용 → 1 Tool 로 통합 + `source` 파라미터로 분기
- 향후 ADR: 매체별 실 API 분리 시 별도 collector 분리 가능 (Phase 6+)

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-19 | 카드 초안 — D2 Resolved 박제, source 파라미터 일반화, dependencies stale 발견 박제 |
