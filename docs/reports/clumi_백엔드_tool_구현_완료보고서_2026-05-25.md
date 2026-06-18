# C:LUMI 백엔드 tool 구현 — 완료보고서 (2026-05-25)

> ⚠️ **OUTDATED (2026-05-27 이후)** — 본 보고서의 backend path/class/folder 명은 옛 것.
> - `routes/clumi.py` → `routes/dashboard1.py` (commit b17ec8a)
> - `tools/collection/clumi/` → `tools/collection/raw/`, `ClumiCollectorBase` → `RawCollectorBase` (commit cadc95b)
> - `tools/preprocessing/clumi/` → `tools/preprocessing/marketing/` (commit f7de6c4)
> - tool DataSource DI 전환 완료 (commit 4219f8b·1627699·49dfed1)
> - 새 위치: `docs/_claude/architecture/`, 회복: `docs/reports/session_compact_recovery_2026-05-27.md`
> - 정량 정답 17/17 은 그대로 유효 (Sprint 16 rename 후도 보존).

---

> 2026-05-23 시작 → 2026-05-25 정량 정답 17/17 박제 완성.
> methodology_calculations 의 모든 정답값을 회귀 검증된 tool 로 누적.

---

## 0. 메타

| 항목 | 내용 |
|---|---|
| 시작 / 종료 | 2026-05-23 (cleaning 1차) → 2026-05-25 (정량 17/17 완성) |
| 작성일 | 2026-05-25 |
| 위치 | `docs/reports/clumi_백엔드_tool_구현_완료보고서_2026-05-25.md` |
| 선행 | `docs/_claude/data/tool_매핑_계획서_2026-05-23.md` (전략) |
| 선행 | `docs/_claude/data/tool_세부계획_시범+인프라_2026-05-23.md` (Step 1~8) |
| 선행 | `docs/reports/clumi_분석_최종검증_및_구현계획_2026-05-22.md` (3축 검증) |
| 커밋 수 | **+18** (bc60517 ~ c439286) |
| 테스트 | **86/86 PASS** (clumi/, 8.00s) |
| catalog | **34 tools** (14 기존 + 20 신규 C:LUMI) |
| 정답 박제 | **정량 17/17** + MoM 6 변화율 |

---

## 1. 한 줄 요약

**C:LUMI 백엔드 tool 시스템 — 정량 정답 17/17 박제 완성.** 기존 14 블루밍글로우 도메인 tool 위에 cleaning · preprocessing · metrics · comparison 4 layer (20 tools) + 6 helper + storage 추상 인프라 + ERD 자동 생성 시스템 + 86 테스트 누적.

---

## 2. 정답 박제표 (methodology 17/17 정량 + MoM 6)

### 2.1 단일 metrics (17 정답 → 13 tools)

| ID | 지표 | 정답값 | tool | 소스 |
|---|---|--:|---|---|
| S001 | 총매출 4월 | 119,539,660 | `revenue_total` | #05 orders |
| S002 | 프로모션 매출 | 43,400,360 | `promotion_revenue` | #05 (promo_code) |
| **S003** | **총 마케팅비** | **18,306,923** | `ad_cost_aggregator` | #01·#04·#15·#16·#17 |
| S004 | 전체 ROAS | 6.53 | `roas_overall` | S001/S003 |
| S005 | 프로모션 ROAS | 2.37 | `promotion_roas` | S002/S003 |
| S028 | 재구매율 4월 | 79.0% | `repurchase_rate_mom` | #05 (is_first_order) |
| S028 | 재구매율 3월 | 76.2% | `repurchase_rate_mom` | 동일 |
| S032 | 전체 CAC | 30,512 | `cac_overall` | S003/S069 |
| S037 | 35-44 회원 | 2,884 | `age_segment` | #06 customers |
| S046 | SILVER 매출 | 65,757,080 | `grade_revenue` | #05×#06 join |
| S046 | WELCOME 회원비중 | 74.5% | `grade_revenue` | 동일 |
| S048 | 객단가 4월 | 62,293 | `aov_monthly` | #05 |
| S054 | 알수없음 매출비중 | 39.8% | `unknown_revenue_share` | #05 (channel) |
| **S067** | **가입전환율** | **2.50%** | `signup_conversion` | GA4 #07 + #06 |
| S069 | 신규회원 4월 | 600 | `new_members_monthly` | #06 (signup_date) |

### 2.2 MoM 비교 (6 변화율 → 3 comparison tools)

| 변화율 | 값 | tool |
|---|--:|---|
| 전체 주문 고객 MoM | +14.9% (1,206→1,386) | `repurchase_mom` |
| 기존 (재구매) 고객 MoM | +19.2% (919→1,095) | `repurchase_mom` |
| **신규 주문 고객 MoM** | **+1.4%** (287→291) — *recovery 핵심 질문 답* | `repurchase_mom` |
| 재구매율 변화 | +2.8%p (76.2%→79.0%) | `repurchase_mom` |
| 객단가 MoM | +5.6% (58,999→62,293) | `aov_mom` |
| 주문수 MoM | +42.6% (1,346→1,919) | `aov_mom` |
| 구매자수 MoM | +14.9% | `aov_mom` |
| 신규 가입 회원 MoM | −0.2% (601→600) | `new_members_mom` |

→ recovery §4.3 "왜 매출 +50.5% 인데 신규 +1.4%?" **완전 답 박제**. 신규 가입 (-0.2%) vs 신규 주문 고객 (+1.4%) 의미 구분.

---

## 3. layer 별 통계

| Layer | 폴더 | tool 수 | 신규? |
|---|---|--:|:--:|
| analysis | `tools/analysis/` | 3 (ml 2 + llm 1) | 기존 |
| collection | `tools/collection/` | 6 | 기존 |
| **cleaning** | `tools/cleaning/` | 3 | **신규** ✨ |
| **comparison** | `tools/comparison/` | 3 | **신규** ✨ |
| **metrics** | `tools/metrics/` | 12 | **신규** ✨ |
| preprocessing | `tools/preprocessing/` | 5 (기존 3 + clumi 2) | 일부 신규 |
| report | `tools/report/` | 1 | 기존 |
| shared | `tools/shared/` | 1 (summary_generator) | 기존 |
| **합계** | | **34** | **20 신규 + 14 기존** |

---

## 4. 기존 tool vs 신규 tool

### 4.1 기존 tool (14, 블루밍글로우 도메인 — 본 세션 무수정 보존)

| 폴더 | tool | 역할 |
|---|---|---|
| `analysis/ml/` | `sentiment_analyzer` | 리뷰 감성 분석 |
| `analysis/ml/` | `keyword_extractor` | 리뷰 키워드 추출 |
| `analysis/llm/` | `insight_extractor` | 리뷰 인사이트 |
| `collection/` | `meta_collector` | 메타 광고 수집 (data/mock) |
| `collection/` | `naver_sa_collector` | 네이버 SA 수집 |
| `collection/` | `naver_gfa_collector` | 네이버 GFA 수집 |
| `collection/` | `kakao_collector` | 카카오 광고 수집 |
| `collection/` | `google_ads_collector` | 구글 광고 수집 |
| `collection/` | `review_collector` | 리뷰 수집 |
| `preprocessing/data_normalization/` | `format_normalizer` | 광고 포맷 정규화 |
| `preprocessing/data_normalization/` | `review_normalizer` | 리뷰 정규화 |
| `preprocessing/text_cleaning/` | `text_preprocessor` | 리뷰 텍스트 전처리 |
| `report/` | `report_writer` | 보고서 작성 |
| `shared/` | `summary_generator` | 공통 요약 |

→ **모두 `data/blooming/`(구 `data/mock/`) 도메인**. C:LUMI 작업과 격리 보존.

### 4.2 신규 tool (20, C:LUMI 도메인)

#### cleaning (3) — methodology §정제 1·3 + POC 운영
| tool | 산출 | 회귀값 |
|---|---|--:|
| `active_orders_filter` | cleaned/orders_active_*.parquet | 4월 1,919 / 3-4월 3,265 |
| `member_metrics_validator` | cleaned/customers_validated.parquet | mismatch_count=0 (mock 정합) |
| `missing_value_diagnostic` | cleaned/missing_diagnostic_*.json | semantic NaN 분류 |

#### preprocessing/clumi (2) — 정제 5·6
| tool | 산출 | 회귀값 |
|---|---|--:|
| `ad_cost_aggregator` | cleaned/ad_cost_total_*.json | 18,306,923 (5매체) |
| `ga4_session_aggregator` | cleaned/ga4_sessions_summary.json | session_start=24,000 |

#### metrics (12) — methodology_calculations 정답
| tool | S### | 정답값 |
|---|---|--:|
| `revenue_total` | S001 | 119,539,660 |
| `promotion_revenue` | S002 | 43,400,360 |
| `roas_overall` | S004 | 6.53 |
| `promotion_roas` | S005 | 2.37 |
| `repurchase_rate_mom` | S028 | 79.0% / 76.2% |
| `cac_overall` | S032 | 30,512 |
| `age_segment` | S037 | 35-44=2,884 |
| `grade_revenue` | S046 | SILVER 65,757,080 |
| `aov_monthly` | S048 | 62,293 |
| `unknown_revenue_share` | S054 | 39.8% |
| `signup_conversion` | S067 | 2.50% |
| `new_members_monthly` | S069 | 600 |

#### comparison (3) — MoM 비교 (composer 패턴)
| tool | 산출 |
|---|---|
| `repurchase_mom` | S028 MoM 변화율 (+14.9% / +19.2% / +1.4% / +2.8%p) |
| `aov_mom` | S048 MoM (+5.6% / +42.6% / +14.9%) |
| `new_members_mom` | S069 MoM (-0.2%) |

---

## 5. 인프라 신설

### 5.1 모델 확장 (`backend/app/dream_agent/models/`)

| 파일 | 변경 |
|---|---|
| `tool.py` | + `Layer Literal["raw","cleaned","computed"]`, + `StoragePolicy` Pydantic, + `ToolSpec.storage: Optional[StoragePolicy]` (기존 14 tool 호환 — None default) |
| `__init__.py` | + `StoragePolicy` export |

### 5.2 Registry 확장

| 파일 | 변경 |
|---|---|
| `tools/registry.py` | `_load_yaml` 에 storage 블록 파싱 추가 (기존 catalog 무수정 호환) |

### 5.3 Helper 6 (`backend/app/dream_agent/tools/shared/`)

| 파일 | 책임 | 사용 tool 수 |
|---|---|--:|
| `storage.py` | `StorageBackend` ABC + `FileStorage` 구현 + `PostgresStorage` 골격 + `get_storage()`/`set_storage()`/`reset_storage()` | 20 |
| `clumi_loader.py` | `load_clumi_source()` + `stream_clumi_source()` + `CLUMI_SOURCES` (file_no 1·4·5·6·7·15·16·17 등록) | 14 |
| `missing_helper.py` | `is_missing` / `safe_int` / `safe_float` / `safe_str` / `null_stats` / `classify_missing` | 6 |
| `order_helper.py` | `filter_active_orders` / `filter_period` / `CANCELLED_STATUS='C40'` | 6 |
| `ad_cost_helper.py` | `aggregate_ad_cost` + 5매체 extractor + `CHANNELS` dict | 3 |
| `ga4_helper.py` | `get_event_param` / `count_events_by_name` / `count_session_starts` / `session_start_by_source` | 2 |

**규칙 박제**: 동일 로직이 3 tool 이상 반복 → helper 화 (조기 추상화 비용 방지).

### 5.4 저장 경로 정책

| Layer | 폴더 | 포맷 | gitignore |
|---|---|---|---|
| raw | `data/clumi/` | csv/json/jsonl/sql | ✅ (전체 data/ 제외 — 100MB 문제) |
| cleaned | `data/clumi_cleaned/` + `_schema/` | parquet/json | ✅ |
| computed | `data/clumi_computed/` + `_schema/` | json | ✅ |

`_schema/` = 동반 메타 (DB 전환 시 컬럼 정의·formula 재사용).

---

## 6. 테스트 통계

### 6.1 86/86 PASS (8.00s)

| 파일 | 케이스 | 영역 |
|---|--:|---|
| `test_storage_backend.py` | 8 | FileStorage 4 method × 3 포맷 + meta 동반 |
| `test_active_orders_filter.py` | 7 | 1,919 / 3,265 회귀 + storage round-trip |
| `test_member_metrics_validator.py` | 6 | mismatch=0 + customer_count=8,500 |
| `test_missing_value_diagnostic.py` | 11 | tool 6 + helper 5 (is_missing/safe_*/null_stats) |
| `test_revenue_total.py` | 6 | S001 119,539,660 회귀 |
| `test_metrics_3.py` | 7 | S048·S028·S069 |
| `test_grade_revenue.py` | 7 | S046 5등급 표 |
| `test_metrics_segment.py` | 7 | S054·S037 (11 bucket 정답표) |
| `test_ad_cost_aggregator.py` | 8 | S003 5매체 + helper |
| `test_metrics_marketing.py` | 6 | S002·S004·S032·S005 + 일관성 |
| `test_comparison_mom.py` | 7 | S028 MoM·S048 MoM·S069 MoM |
| `test_ga4_signup.py` | 6 | session_start=24,000 + S067=2.50% + helper |
| **합계** | **86** | 0 skip |

### 6.2 회귀 박제 정답 (17 정량)

`clumi_answer_values` 메타가 각 catalog YAML 에 박제됨 — methodology 변경 시 *catalog 1 곳만* 수정하면 회귀 테스트가 자동 검출.

---

## 7. ERD 산출 (gitignored — `docs/_claude/data/erd/`)

| 파일 | 설명 | entity / 컬럼 |
|---|---|---|
| `raw_clumi_erd_L1_full.dbml` | raw 전체 | 21 entity / 771 컬럼 |
| `raw_clumi_erd_L2_compact.dbml` | raw 축약 | 21 / 94 |
| `raw_clumi_erd_L3_relations.dbml` | raw 관계만 | 21 / 44 |
| `cleaned_clumi_erd_L1_full.dbml` | cleaned | **6 entity** (active orders × 2 periods + customers_validated + missing_diag × 2 + ad_cost_total + ga4_sessions_summary) |
| `computed_clumi_erd_L1_full.dbml` | computed | **15 entity** (S001·S002·S004·S005·S028·S032·S037·S046·S048·S054·S067·S069 + MoM 3) |
| `manual_refs.yaml` | 사람 검토 Ref 정의 | 7 (cleaning 3 누적 trigger) |

생성 스크립트 (4): `build_erd_L1.py` · `build_erd_L2_L3.py` · `build_erd_cleaned.py` · `build_erd_computed.py`. 모두 *DBML 공식 spec 부합 + preflight 검증*.

---

## 8. 문서 산출

### git 추적 (`docs/reports/`)

| 파일 | 신설 |
|---|---|
| `clumi_분석_최종검증_및_구현계획_2026-05-22.md` | ✅ 세션 초 |
| `data_pipeline_verification_2026-05-22.md` | ✅ |
| `session_compact_recovery_2026-05-23.md` | ✅ |
| `clumi_백엔드_tool_구현_완료보고서_2026-05-25.md` | ✅ (본 문서) |

### gitignored (`docs/_claude/data/`)

| 파일 | 설명 |
|---|---|
| `tool_매핑_계획서_2026-05-23.md` | 전략 — 8 폴더 매핑 + §9 점진 보완 정책 + §10 자체 검증 |
| `tool_세부계획_시범+인프라_2026-05-23.md` | 실행 — Step 1~8 + 15 테스트 + 12 DoD |
| `erd/raw_clumi_erd_2026-05-23.md` | ERD README |

---

## 9. git 커밋 timeline (origin/main +18)

```
bc60517 refactor(data): 도메인별 폴더 분리 — blooming 이동·clumi raw 추가·pipeline 신설
c59d95d docs(reports): C:LUMI 분석 검증·구현 계획·session 회복 보고서 3건
fcc201f feat: storage 추상 인프라 신설 (StorageBackend + ToolSpec.storage 필드)
eb13d7f test: FileStorage 8 케이스
ecc9670 feat: cleaning/active_orders_filter — 시범 tool (1,919 회귀)
bdba7e9 chore(data): clumi_cleaned·computed gitignore
d1dccd6 feat: cleaning/member_metrics_validator — 정제 3 (mismatch=0)
30d1b72 feat: cleaning/missing_value_diagnostic + missing_helper — 정제 layer 완성
9b86629 chore(.gitignore): data/ 전체 제외 — GitHub 100MB 문제 해결 (filter-branch)
4239f02 feat: metrics/revenue_total — S001 (119,539,660)
c728245 feat: metrics 3 묶음 — S048 · S028 · S069
41333a4 feat: metrics/grade_revenue — S046 (첫 join 패턴)
7adcafc feat: metrics 2 묶음 — S054 · S037
c4154df feat: preprocessing/clumi/ad_cost_aggregator — 정제 5 (18,306,923)
788403e feat: metrics 4 묶음 마케팅비 라인 — S002·S004·S032·S005 (정답 14/17)
88e48fe feat: comparison/ layer 신설 — S028 MoM · S048 MoM (composer 패턴)
7efc58e feat: comparison/new_members_mom + RepurchaseMom 회귀 보강 (recovery 답 완성)
c439286 feat: GA4 + signup_conversion (S067=2.50%) — 정량 17/17 완성
```

---

## 10. 누적 자산 가시화

| 자산 | 수 / 크기 |
|---|---|
| 신규 tool | **20** |
| 신규 catalog YAML | 20 (각 tool 1개) |
| 신규 helper | **6** |
| 신규 폴더 | `cleaning/` · `comparison/` · `metrics/` · `preprocessing/clumi/` · `catalog/cleaning/` · `catalog/comparison/` · `catalog/metrics/` · `catalog/preprocessing/clumi/` |
| 모델 확장 | StoragePolicy + ToolSpec.storage |
| 신규 테스트 | **86** (전부 신규 — clumi/ 폴더) |
| ERD 파일 | 5 DBML + 4 생성 스크립트 + 1 manual_refs.yaml |
| 문서 | 4 (보고서 git + 2 계획서 gitignored) |
| 산출 데이터 (gitignored) | `data/clumi_cleaned/` 6 + `data/clumi_computed/` 15 + 각 `_schema/` |
| git 커밋 | **+18** (origin/main 대비) |

---

## 11. 결정·사용자 선호 박제 (이번 세션)

### 11.1 아키텍처 결정

| 결정 | 배경 | 메모리 |
|---|---|---|
| **Fine-grained tool + skill 외부 조합** | 모든 metric 명시 박제, 상위 워크플로우는 사람/agent 가 조립 | `project_extension_ease_priority` 일관 |
| Tool 원자성 (1 tool = 1 일) | 향후 더 복잡한 세부 분석 가능 | 매핑 계획서 §1 |
| Helper 추출 기준 = 3 tool 이상 반복 | 조기 추상화 비용 회피 | `feedback_test_no_resource_limit` 일관 |
| 정답 박제 = `clumi_answer_values` catalog 메타 | methodology 변경 시 회귀 자동 검출 | — |
| Storage layer 추상 (FileStorage → PostgresStorage 골격) | POC 파일·MVP+ DB 교체 무비용 | 매핑 계획서 §6.2 |
| `data/` 전체 gitignore (filter-branch 적용) | GA4 96MB+253MB → GitHub 100MB 거부 | — |
| 점진 보완 정책 (사전·ERD·narrative) | 추측 일괄 보강 금지, 실 구현이 truth | 매핑 계획서 §9 |
| `docs/_claude/` 로컬 only (자취·계획서) | CLAUDE.md 정책 | — |

### 11.2 발견·교정

| 발견 | 해결 |
|---|---|
| **recovery "+1.4%" 의미** — 신규 가입(-0.2%) vs 신규 주문 고객(+1.4%) 구분 | `RepurchaseMom.delta.new_buyers_pct` + `NewMembersMom.delta_pct` 별도 박제 |
| **DBML spec 위반 6종** | filter-branch + 컬럼 normalize + dedup + escape + preflight 검증 |
| **pandas NaN false positive** (6,333 mismatch → 0) | `missing_helper.safe_*` 추출 |
| **AOV truncate 오차** (62,292 vs 62,293) | `//` → `round()` 변경 + methodology §S048 round 명시 박제 |
| **GA4 100MB 거부** | filter-branch history rewrite + `stream_clumi_source` streaming helper |

---

## 12. 다음 단계 (정량 완성 후)

### 12.1 남은 영역

| 영역 | 작업 | 우선 |
|---|---|---|
| **insights (해설 25)** | LLM 호출 패턴 — Phase A | 큰 결정 (프롬프트 디자인·비용) |
| **normalization** | 정제 2·4·8·9 (KST·채널·등급·UTM) | 데이터 품질 |
| **preprocessing 잔존** | 정제 7 카테고리·10 비회원 | 중간 |
| **comparison 확장** | 채널별 / 등급별 비교 등 | 추가 정답값 |
| **skill layer 본격 설계** | 사용자 명시 방향 — tool 조합 메커니즘 | 향후 가시화 |
| **frontend 연동** | 대시보드 데이터 계약 (Phase B) | 다음 큰 단계 |

### 12.2 skill 조합 예시 (사용자 의도 박제)

```
"마케팅 효율 분석" skill
  = revenue_total + ad_cost_aggregator + roas_overall + cac_overall
    + promotion_roas + grade_revenue + insights (LLM 후속)

"MoM 변화 분석" skill
  = aov_mom + repurchase_mom + new_members_mom + revenue_mom (신설 예정)

"가입 퍼널 분석" skill
  = ga4_session_aggregator + signup_conversion + new_members_monthly
    + cac_overall
```

→ tool 은 *원자 단위*, skill 은 *조합 단위*. 현재는 *사람이 조립*, 향후 *catalog/skill/* layer 또는 외부 워크플로우 엔진으로 박제 가능.

### 12.3 즉시 가능한 작업

| 후보 | 작업량 | 가치 |
|---|---|---|
| A. insights 1박스 시범 (LLM 패턴 진입) | 중 | 정성 layer 시작 |
| B. normalization 1 tool (정제 2 KST) | 소 | 데이터 품질 |
| C. comparison 확장 (revenue MoM 등 잔존) | 소 | 자산 보강 |
| D. skill layer 설계 (catalog/skill/) | 중 | 사용자 의도 구현 |
| E. 검토 멈춤 — 자산 점검 | — | 안정화 |

---

## 13. 자체 검증 (보고서 신뢰)

| 축 | 확인 |
|---|---|
| 정답 정합 | 17/17 methodology 정답값 ↔ 86 테스트 회귀 일치 |
| tool 수 | 34 = 14 기존 + 20 신규 (catalog 자동 카운트 일치) |
| 커밋 timeline | 18 = `git log 9b47fb3..HEAD` 실측 일치 |
| Layer 분리 | cleaning/comparison/metrics/preprocessing/clumi 모두 *기존 14 tool 무수정* — 도메인 격리 검증 |
| 회귀 박제 | catalog YAML 의 `clumi_answer_values` ↔ 테스트 assertion 일치 |
| storage 추상 | `set_storage(FileStorage(tmp_path))` 로 모든 테스트 격리 (실 data/ 무변경) |
| methodology 출처 | 모든 신규 tool docstring 에 §S### / §정제 N 참조 박제 |

---

## 14. 변경 이력

| 일자 | 내용 |
|---|---|
| 2026-05-25 | 완료 보고서 1차 — 정량 17/17 + MoM 6 + 18 커밋 + 86 테스트 + 34 tools (14 기존 + 20 신규) + 6 helper + storage 인프라 + ERD 자동 생성 시스템. 사용자 결정 (fine-grained tool + skill 외부 조합) 박제. |
