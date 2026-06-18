# Session Compact Recovery — 2026-06-17 (normalized 피봇 DB 제작 *진행 중*)

> **다음 세션 첫 행동**: ① 본 문서 → ② **[DB제작_구현현황](DB제작_구현현황_2026-06-17.md)**(살아있는 추적기·§4 현황표) → ③ [세부05 행emitter 계획서](../_claude/plans/normalized_pivot_세부05_translator_행emitter_2026-06-17.md) → ④ [ADR-032](../agent_specs/adr/ADR-032_normalized_pivot_persistence_decisions.md)(결정·잠정). 코드 `main 22b7b91`.
> **작업방식(필독 memory)**: `feedback_anti_sycophancy_evidence_labeling`(✓검증/⚠추측·file:line·자기정정)·`feedback_plan_intent_before_code`·`feedback_no_mixed_codebases`·`feedback_user_beginner_recommend_actively`(단일 전문권장)·`feedback_test_no_resource_limit`(TDD·skip금지)·`feedback_completion_report_on_done`·`feedback_no_claude_commit_attribution`(Co-Authored 금지, gpgsign=false)·`feedback_convention_over_hardcoding`·`project_normalized_pivot_scope`(★기준점·전범위 FE/BE/통신/DB).
> **★ 현 위치**: DB 제작 진행 중. **12 정형 테이블 중 normalized 6 완료(코드+검증), computed 5·blended 1 미구현.** ⚠ **라이브 clumi DB엔 아직 정형 테이블 0**(검증은 temp schema만 — 실제 clumi 적재=후속 C-2).

---

## §1 한 줄 요약
이번 세션 = ① 4 세부계획서 작성·검증 → ② 데이터층 검증 → ③ canonical_translator 격리신설(PR1) → ④ 물리 ERD → ⑤ **P1 Layer rename(cleaned→normalized)+접미사 네이밍** → ⑥ ADR-032 영속화 결정 → ⑦ **DB 제작 Step1~5(translator 행 emitter + 6 normalized 테이블 적재·검증)**. 다음 = computed/blended + 라이브 적재.

---

## §2 이번 세션 커밋 지도 (✓ `6a248a1`→`7c76fb2`, 16커밋)
| 커밋 | 내용 |
|---|---|
| `6a248a1` | 세부계획서 4종 분할(데이터/tool/기타/테스트, docs/_claude/plans/, gitignore) |
| `afbcad7`·`e717500`·`a42102a` | 미커밋분 정리(deps·scripts·과거리포트) |
| `b5af701` | 데이터층 검증 — google 결정론·8원천 raw 실재·데이터사전 7컬럼 보완(누락133→126) |
| `d6216be`·`a39b2ea` | **PR1** canonical_translator 격리신설(5채널, 18.3M 재현) + google SOURCE_REGISTRY 카운트 정정(16→17) |
| `57f9f7e` | **물리 ERD** `erd_octorad_normalized_computed_v0.1.dbml`(소스별 14테이블) |
| `959e418` | contract gap — report_date/campaign_id sources에 kakao·talktalk·google·orders 추가 |
| `f20e64b` | **★ P1 Layer rename** cleaned→normalized(Literal·LAYER_DIR·tool 24·flow 8·dashboard1 4) + 접미사 SSOT `typed_table_name` |
| `b0ec4dd` | setup_data_db 자기파괴 수정(KEEP_PREFIXES 접두→접미 LAYER_SUFFIXES) + rename 정합 마무리 |
| `79bf23e` | **★ ADR-032**(D1 writer·D2 blended layer·D3 order_status) + D2(Layer 4번째 blended) + D3 |
| `704170c` | D3 SSOT 통일 `order_helper.is_active_order` + DB제작 추적문서 신설 |
| `fdf51f8` | data/tool layer 경계 감사 결과(§1.5 _storage decorative 정정) |
| `3d32aa2` | **DB제작 Step1+2** reserved 가드 + `write_relational_table`(ADR-032 D1) |
| `aff7bbd` | Step3 사전검증(6소스 합불변) + 세부05 계획서 |
| `22b7b91` | **★ DB제작 Step3~5** translator 행 emitter + 6 normalized 테이블 적재 |
| `7c76fb2` | (무관) 65 Dashboard Pages v1.1 — 사전 미커밋분 분리커밋 |

---

## §3 ★ 핵심 결정 (전부 박제됨)
- **[ADR-032](../agent_specs/adr/ADR-032_normalized_pivot_persistence_decisions.md)** (Accepted **잠정 — ⚠UX 디자인 시 대폭 수정 가능**, 오너 명시):
  - **D1**: 정형 테이블 = 전용 `write_relational_table`(append/upsert·DROP 금지) + `is_relational_table` 가드(write_typed_table이 _normalized/_computed/_blended DROP 차단).
  - **D2**: `blended_computed` = Layer Literal **4번째 'blended'**.
  - **D3**: 활성주문 = **C계열 전체 제외**(`order_status not startswith 'C'`). ⚠ **N00(입금전) 포함**(매출인정 — 결제완료만은 오너/UX). 단일 SSOT = `order_helper.is_active_order`.
- **★ cleaned=State(임시) 결정** (오너 확정): cleaning→normalization 전달용 *중간물(cleaned)* = **DB 레이어 X, 파이프라인 State(인메모리)** 로. 영속(DB)은 raw/normalized/computed/blended만. cleaning 도구 `_storage:normalized`는 decorative(실 persist 미구동)라 과영속 미발생 — 정합책=저장정책 SSOT화(후속).
- **★ G5 스코프**: 이번 DB 빌드 = **google 제외 12테이블**(blended 18.3M·MER 6.53 유지). google 6채널 통합·re-baseline(→26.8M·MER 4.46) = **P2**.
- **네이밍**: raw `{*}` → `{*}_normalized` → `{*}_computed`(layer=접미사, 소스별 1:1) + `blended_computed`. client = **PostgreSQL schema-per-client**(컬럼 아님). typed_table_name=`{stem}_{layer}`(접두→접미 전환 완료).
- **3 차이 종류**(정규화 본질): ① 이름 다름(rename) ② **의미 다름**(salesAmt=비용·동음이의 — contract가 박제, ★핵심) ③ 있고없고(소스별 measure — 소스별 테이블 정당화).

---

## §4 ★ DB 제작 상태 (추적문서 §4가 권위)
**완료(코드+검증)**: Step1(reserved 가드)·Step2(write_relational_table)·Step3(translator 행 emitter)·Step4(persist_normalized)·Step5(6 normalized 테이블).
**미구현**: Step5b(computed 5)·Step6(blended 1)·Step7(computed/blended 테스트)·전제 C-1/C-2(라이브 정리·적재).

**검증된 적재 결과**(temp schema `test_canonical_rel`에서 — ⚠라이브 clumi 아님):
```
meta_ads_performance_normalized   90행  (ad_cost Σ 9,235,826)
naver_searchad_normalized        180행  (1680→180 campaign×device×date 그룹, Σ 5,999,627)
naver_advoost_normalized          90행  (+vt_conversion, Σ 3,000,000)
kakao_bizmessage_normalized        2행  (msg_ 7컬럼, Σ 59,020)
naver_talktalk_normalized          2행  (Σ 12,450)
orders_normalized               1919행  (활성 C계열제외, Σ 119,539,660)
→ blended 기대: total_marketing_cost 18,306,923 · MER 6.53 (google 제외)
```
검증 통과: 행수·**합 불변(피봇 thesis)**·PK 유일/non-null·행단위 `_lineage jsonb`·**멱등 UPSERT**·MER 보존. test `test_canonical_relational_load.py` 7 passed. 전체 회귀 **983 passed**(pre-existing 5: parquet env×3·test_DC_PERM_6·test_o04).

---

## §5 ★ 핵심 코드 (다음 세션이 손댈 곳)
- **`backend/app/dream_agent/tools/normalization/canonical_translator.py`** (재작성됨):
  - `_ALL_SPECS`(6 소스 spec: channel·source_id·keys(dim/PK 추출)·pk_cols·col_types·measures). `_to_date`·`_DEVICE`(P/M).
  - `_m_meta`(8 measure)·`_m_naver_sa`(5)·`_m_advoost`(6,+vt)·`_m_kakao`/`_m_talktalk`(7,target만 차이)·`_m_orders`(1).
  - `_translate`: filter→keys→**PK 그룹핑(measure 합산)**→행 emit + sums(compute 보존). 반환 {table,pk_cols,col_types,rows[list],measures(sums),...}.
  - `_compute`: sums→MER 등(기존 보존). `execute`: **순수**(행+computed 반환, DB무관). `persist_normalized(result,client)`: write_relational_table로 6 테이블 적재.
  - **다음 추가**: computed 파생(소스별 normalized 행→roas/ctr/cpc/cpm/cvr·msg_roi → `{source}_computed` 적재) + blended(`_compute` 산출 → `blended_computed` PK=period UPSERT). `persist_computed`·`persist_blended` 메서드 신설 권장.
- **`backend/app/data_pg_util.py`**: `write_relational_table(conn,client,table,rows,*,pk_cols,col_types)`(CREATE IF NOT EXISTS+ON CONFLICT UPSERT, DROP금지) · `is_relational_table`(접미사 가드) · `RELATIONAL_LAYERS`·`_REL_SQL_TYPE`·`_rel_adapt`.
- **`backend/app/workspace/base.py`·`models/tool.py`**: `Layer = Literal["raw","normalized","computed","blended"]`. `file.py` LAYER_DIR 4키. `setup_data_db.py` LAYER_SUFFIXES 4개.
- **`backend/app/dream_agent/tools/shared/order_helper.py`**: `is_active_order(status)`(C계열 제외) — 단일 SSOT, canonical_translator·active_orders_filter·member_metrics_validator 참조.

---

## §6 점검/감사 결과 (이번 세션 워크플로 3회)
- **`wykcrn2iw`**(피봇 기준점 점검): "테이블 사전생성=순서 틀림" 3 critical(write_typed_table DROP·translator 집계1행·blended 미설계) → ADR-032로 해소. setup_data_db 자기파괴 발견.
- **`whfxphnah`**(DB제작 직전 점검): D3 정의분기 적발(→SSOT 통일)·라이브DB orphan 76·_workspace 'cleaned' 라벨 잔존(C-1/C-2 필요)·HOW gap 5(→세부05 해소).
- **`wm425xjo3`**(data/tool 경계 감사): **입력경계·의존방향·schema = clean** ✅(tool은 self.fetch만·data layer가 tool import 0·schema 실검증). **출력경계 = leaky** ⚠: (a)rendering 3종(pptx/pdf/chart) Workspace 우회 직접 파일write(ADR-022 위반, DB와 무관·후속) (b)`_storage` 힌트 decorative(진입점이 실 persist 결정). → DB 빌드는 `_storage` 미의존·명시 persist(반영됨).

---

## §7 남은 일 (우선순위)
1. **Step5b computed**: 소스별 normalized 행 → ad(meta·naver_sa·advoost)=roas_x·ctr_pct·cpc_krw·cpm_krw·cvr_pct / msg(kakao·talktalk)=msg_roi_pct·msg_avg_order_value_krw → `{source}_computed`(PK=normalized와 동일). orders=computed 없음.
2. **Step6 blended**: `_compute` 산출 → `blended_computed`(PK=period, layer='blended', write_relational_table). total_ad/msg/marketing_cost·total_order_revenue·mer·tacos_pct.
3. **Step7 테스트**: computed/blended 검증(행단위 파생·Σ소스=blended·MER 6.53). test_canonical_relational_load 확장.
4. **전제 C-1**: 라이브 clumi orphan 76 DROP(`setup_data_db.cleanup_legacy` 접미사규칙이 처리).
5. **전제 C-2**: stale `_workspace` 50행(layer='cleaned' 7·옛 computed 41·dangling raw 2) purge — **현 코드경로 없음**, 스크립트 필요.
6. **라이브 적재**: persist_normalized/computed/blended를 client='clumi'로 실행 → 라이브 12테이블 생성(현재 0).
7. (후속/별트랙) **P2**: google 6채널+re-baseline(26.8M·MER 4.46) / measure16 잔여(link_ctr·aMER) / rendering Workspace 위임 / cleaning `_storage` State 정합 / contract→backend config(D3 위치) / 옛 cleaned·computed blob 삭제(P4).

---

## §8 정직 경고 (과신 금지)
1. **라이브 clumi DB에 정형 테이블 0** — 검증은 *temp schema*에서만. 실제 clumi 적재는 C-2(전제 청소) 후. "테이블 만들었다"는 *코드+temp검증* 수준, 라이브 미반영.
2. **computed/blended 미구현** — normalized 6만 코드 완료. 12 중 6.
3. **measure16 부분만** — meta/advoost/msg 확장은 했으나 link_ctr_pct·acquisition_mer(aMER) 미산출(measure는 있으나 metric 미빌드).
4. **google 제외(G5)** — blended 18.3M은 *5채널 기준*. ERD엔 google 테이블 있으나 미적재(P2). re-baseline 26.8M 미발생.
5. **컨테스트 18,306,923·MER 6.53 = 5채널 정답** — 다수 코드/문서가 이 값 가정. google 통합 시 갱신 필요.
6. **cleaning `_storage` State 미전환** — decorative라 무해하나 설계정합은 후속.

---

## §9 관련 문서·memory
**문서**: [DB제작_구현현황](DB제작_구현현황_2026-06-17.md)(추적·권위) · [세부05](../_claude/plans/normalized_pivot_세부05_translator_행emitter_2026-06-17.md)(설계) · [ADR-032](../agent_specs/adr/ADR-032_normalized_pivot_persistence_decisions.md) · [ERD](../agent_specs/ERD/erd_octorad_normalized_computed_v0.1.dbml) · [세부01~04](../_claude/plans/)(데이터/tool/기타/테스트) · 점검리포트 3 · 완료보고서들(docs/reports/).
**memory**: `project_normalized_pivot_scope`(★기준점·범위·결정 ADR-032 링크·cleaned=State) · `feedback_*`(§머리말) · `project_data_analyst_4_layers` · `project_intended_layer_architecture` · `project_collector_two_kinds` · `project_catalog_code_drift`(_storage decorative 함정).
