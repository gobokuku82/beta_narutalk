# Session Compact Recovery — 2026-06-16 (normalized 피봇 계획 완성 + google 채널 추가 + 데이터 4범주 규명)

> **다음 세션 첫 행동**: ① 본 문서 → ② **[normalized 피봇 최종 계획서](../_claude/plans/normalized_tool_pivot_계획서_2026-06-15.md)**(핵심) → ③ [ERD/INDEX](../agent_specs/ERD/INDEX.md). 코드 `main 2ebd21e`.
> **작업방식(필독)**: memory `feedback_anti_sycophancy_evidence_labeling`(✓검증/⚠추측·file:line)·`feedback_plan_intent_before_code`·`feedback_no_mixed_codebases`(v1/v2 격리→전환)·`project_normalized_pivot_scope`·`project_data_viz_work_division`·`feedback_no_claude_commit_attribution`.
> **★ 핵심 상태**: 열린 결정 **0건**(전부 정리됨). 계획·검증·데이터 준비 완료. **다음 = P0 상세설계(작업), 구현은 그 후.**

---

## §1 현상황 — 한 줄

직전 compact([2026-06-15 ERD시각화·피봇계획](session_compact_recovery_2026-06-15_ERD시각화_normalized피봇계획.md))에 이어, 이번 세션 = **계획 검증 완료 + 명명 통일 + 데이터 4범주 규명 + google 채널 추가 + 모든 열린결정 해소**. **이제 P0 상세설계만 남음**(설계 작업, 결정 아님). 구현(P1~P5) 미시작.

---

## §2 산출물 지도 (✓ 커밋 실측, `8d5bc77`→`2ebd21e` 11커밋)

| 커밋 | 내용 |
|---|---|
| `86aa8bd` | 셋업 문서 DB명 정합(README·.env.example → octormate_system) |
| `e296562` | **★ 베이스라인 테스트** `test_normalized_pivot_baseline.py`(10 PASS) — 교차세계 동치(World A canonical == World B 18,306,923·MER 6.53) + 결정 invariant(dormancy·소비처·Layer·tool수) |
| `5e2479d` | **★ dimension 프로토타입** `data_pilot_project/dimensions.py`+`dimension_maps.yaml`(config 외부화) + `test_dimension_normalizer_prototype.py`(4 PASS) — production 3 normalizer를 단일 translator가 재현 실증 |
| `b687a36` | **변환 시각화** `erd_octorad_pivot_migration.html` — 기준→신규 카테고리/툴 표 |
| `a0033ef` | **명명 통일** — `normalized`=레이어 / `canonical`=표준. `cleaned_canonical_measures`→`normalized_measures` 등 |
| `0f3dc35`·`164d2c5` | daily_performance 정체규명 + 레거시→demo 표시 |
| `3eafb9f` | **★ 흐름 HTML에 목표(target) 레인 추가** — 실적↔목표 점선 대조엣지(tg13·gap4) |
| `7e17c24` | **★ google = canonical 18번째 유료채널(A1)** — `google_ads_performance.csv`(180행·8.5M) + schema·registry·contract·dbml·사전·flow HTML |
| `2ebd21e` | **mer/aMER formula 텍스트 정정** total_ad_cost→total_marketing_cost(=ad+msg, 6.53 불변) |

**최종 계획서**(gitignore): [normalized_tool_pivot_계획서_2026-06-15.md](../_claude/plans/normalized_tool_pivot_계획서_2026-06-15.md) — v1~v4+검증을 단일 통합본으로 정리. §0 현황·§2 범위결정·§3 변경점(카테고리/툴/데이터레이어/기타)·§5 로드맵 P0~P5·§8 결정표·§9 검증근거.
생성기(gitignore): `docs/_claude/data/erd/` — gen_erd_html·gen_pivot_migration_html·gen_normalized_erd·gen_layer_docs. + `backend/scripts/gen_google_ads_mock.py`(tracked).

---

## §3 ★ 데이터 4범주 (이번 세션 규명 — 가장 중요)

광고 데이터가 성격별로 나뉨. 혼동의 근원이었고, 36 설계doc + 실측으로 확정:

| 범주 | 출처 | 값 | 피봇 처리 |
|---|---|---|---|
| **실적(actual)** | canonical(벤더 소스)=World A · ad_cost_helper(production)=World B | 18,306,923 (ad 18,235,453 + msg 71,470)·MER 6.53 | = 정답 → normalized (B는 msg를 ad에 합산 → 분리) |
| **목표(target)** | campaigns·channel_targets·budget_allocation·marketing_monthly_targets (**기존 4파일**) | target_roas·예산 등 | **재사용**, 새 파일 불요·피봇 범위 밖 |
| **대시보드 demo** | daily_performance 등 Batch 2~6 | "정답 비교 X" ([36 설계doc](../agent_specs/36_clumi_mock_raw_data_design_v1.0.md) §0 명시) | **의도된 demo**(레거시 아님). 피봇 통합 시 canonical 대체 |
| **★신규(A1)** | `google_ads_performance` (clumi_mock_18) | 8.5M/월·180행(roas4.12·cpa10.3k) | **canonical 18번째 유료채널.** 배선 완료, re-baseline=P2 |

> ⚠ 내가 daily_performance를 "3-World 충돌"→"목표"→"레거시"로 **3번 오판**한 뒤 **36 설계doc(시스템 자체 문서)**로 최종 정정. 교훈 = §6 원칙.

---

## §4 확정 사실 (✓ 실측/실행)

- **피봇 범위 결정**(오너 위임→내 결정): **AD-canonical 집중 부분 피봇**. 실측 임팩트 = **REPLACE 5(+shared ad_cost_helper)/MODIFY 10/KEEP 77** (원계획 "8/23/61" 과대추정 정정, 2 병렬분석).
- **canonical_translator(신규)** = 하드코딩 normalizer 6종(format_normalizer·channel_attribution·grade_system·utm·kst + ad_cost_helper) 통합. measures+dimensions 교차세계 동치로 실증(test 10+4 PASS).
- **데이터레이어**: Workspace `cleaned`→`normalized` 신설 + 하이브리드(raw blob / normalized·computed 관계형). DB octormate_system(checkpoint)·octormate_data(데이터).
- **google A1 완료**: 데이터·schema·SOURCE_REGISTRY·contract(ad_cost_krw 등 5 measure에 google source)·raw dbml·사전(clumi_mock_18)·flow HTML(⏳신규). **pipeline 미통합 → gate green 유지(18.3M)**; re-baseline(→~26.8M·MER~4.46)은 P2.
- **mer = 매출/총마케팅비(ad+msg)** 확정(07§③ 시스템 정의·코드·정답 6.53). tacos는 ad-only 정상.
- **회귀 오라클 green**: data_pilot gate OVERALL PASS + 교차세계 테스트(measure10·dim4) 21 PASS — google·mer 변경 후에도.

---

## §5 ★ 정직 경고 (다음 세션 과신 금지)

1. **구현 코드 0.** 계획·검증·데이터준비만 완료. canonical_translator·tool 전환·DB 관계형화 = **전부 미시작**. "구현은 승인 후"(오너).
2. **re-baseline 미발생**: 답은 아직 18.3M·MER 6.53(prototype 5채널). google 합산(→~26.8M·MER~4.46)은 **P2에서** — 지금 18.3M 가정하는 코드/문서 많음.
3. **daily_performance = 대시보드 demo**(레거시 아님). 36 설계doc 권위. P3/P4서 canonical 대체.
4. **미생산 measure 7·aMER·CPA = 데이터 있음**(meta inline_link_clicks·reach·frequency / advoost vt / kakao summary / orders is_first_order 전부 실재) → P2 translator 추출/정의로 해결, **데이터 생성 불요**. blocked 라벨 임시일 뿐.
5. §10 임팩트 수치(5/10/77)·google 스케일(8.5M)은 합리적 근사 — P0서 tool별 확정.

---

## §6 ★ 작업 원칙 (이번 세션 확립)

- **mock·계산정의 권위 = 설계문서 + 실벤더스키마 + 업계표준** (오너 기억 아님). clumi mock은 "원본에 맞게" 생성된 것이라 오너가 세부를 모름 → 데이터사전·methodology·36·07 doc로 판단·제시. memory `project_normalized_pivot_scope` 말미.
- **계산 로직 = 오너 영역**이나, 오너가 "구현만 시켜 모름"이면 표준으로 결정(임의 생성 아님, 근거 제시). mer가 그 예.
- 신규 mock = **설계doc 먼저**(`feedback_mock_raw_design_doc_first`). google이 그 절차(36/사전 등재 후 생성).

---

## §7 남은 일 / 다음 (열린 결정 0 → P0)

**열린 결정 없음.** 다음은 결정이 아니라 **작업**:

1. **P0 상세설계** (내 작업): ① 물리 ERD DDL(octormate_data: raw blob + `normalized_measures`·`computed_metrics` 관계형) ② Workspace Layer `raw/normalized/computed` 코드변경 명세 ③ tool별 PR 변경표(REPLACE 6·MODIFY 10) ④ DB 리셋·재구축 스크립트
2. → 오너 검토·승인
3. → **구현 P1~P5**: P1 contract코드화+관계형스키마 / P2 canonical_translator(격리)+**google통합+16measure추출+aMER·CPA빌드→re-baseline** / P3 지표10 점진전환(A/B) / P4 정리(REPLACE6폐기·daily_performance폐기·옛DB삭제) / P5 dim·time확장

회귀 안전망 = 교차세계 테스트(measure+dim) + data_pilot gate. P2 re-baseline 시 기준값 갱신.

---

## §8 관련 memory
`project_normalized_pivot_scope`(피봇 범위·4범주·google·mock권위)·`project_data_viz_work_division`(계산=오너영역)·`feedback_anti_sycophancy_evidence_labeling`·`feedback_no_mixed_codebases`·`project_erd_new_world_clean_build`·`feedback_mock_raw_design_doc_first`·`feedback_no_claude_commit_attribution`.
