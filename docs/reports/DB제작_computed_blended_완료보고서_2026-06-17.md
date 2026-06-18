# 완료보고서 — DB 제작 Step5b+6 (computed 5 + blended_computed)

> 작업: normalized 피봇 DB 제작의 computed/blended 레이어 구현 · 2026-06-17 · 커밋 `3f33ea3`
> 상위 추적: [DB제작_구현현황](DB제작_구현현황_2026-06-17.md)(§4 권위) · [ADR-032](../agent_specs/adr/ADR-032_normalized_pivot_persistence_decisions.md)(잠정) · [ERD](../agent_specs/ERD/erd_octorad_normalized_computed_v0.1.dbml)

## 1. 무엇을 했나
`canonical_translator`의 2단계 산출을 **normalized(6) → computed(5) → blended(1)** 전체로 확장.
- **computed 5테이블** (`{source_id}_computed`): 소스별 normalized 행 → *행단위* 파생지표.
  - ad (meta·naver_sa·advoost): `roas_x·ctr_pct·cpc_krw·cpm_krw·cvr_pct` (+ meta 전용 `link_ctr_pct`).
  - msg (kakao·talktalk): `msg_roi_pct·msg_avg_order_value_krw`(재계산).
  - orders = computed 없음(blended 분자로만 사용).
- **blended_computed 1테이블** (PK=period, layer='blended'): period 단위 1행 — `total_ad/msg/marketing_cost·total_order_revenue·mer·tacos_pct`.
- **persist 메서드**: `persist_computed`·`persist_blended`·`persist_all`(G7 순서 normalized→computed→blended).

## 2. 왜 이렇게
- **공식 불변(메트릭=오너 도메인)**: computed 파생은 기존 `_compute`의 채널식과 **동일 공식**을 *행단위*로 재사용 — 새 공식 발명 0. roas/ctr/cpc/cpm/cvr/msg_roi 모두 `_compute` line 247~261과 일치.
- **`msg_avg_order_value_krw` 재계산**: ERD line 31 "채널 보고 파생값은 computed서 재계산" 원칙 → `msg_conv_revenue/msg_conv_count`(표준 AOV). normalized의 채널보고값(M12)과 의도적 구분.
- **네이밍 `{source_id}_computed`**: 오너의 `{stem}_{layer}` 접미사 규칙 준수(normalized와 동일 stem). ⚠ ERD v0.1의 shorthand `meta_computed`/`kakao_computed`는 규칙 위반이라 `meta_ads_performance_computed`/`kakao_bizmessage_computed`로 **정정**(ERD·Ref·TableGroup 동기화).
- **blended 스코프 = 계획 §4의 6지표만**: ERD의 `acquisition_mer`(is_first_order 필요)·`blended_platform_roas_x`는 measure16/P2 미산출 → 컬럼 보류(ERD에 ⏳ 표기). 스코프 절제.

## 3. 변경표
| 파일 | 변경 |
|---|---|
| `backend/app/dream_agent/tools/normalization/canonical_translator.py` | `_computed_ad`/`_computed_msg`·`_AD/_MSG_COMPUTED_TYPES` 모듈헬퍼 + `_build_computed`/`_build_blended` 메서드 + execute에 `computed_tables`/`blended` 키 + `persist_computed`/`persist_blended`/`persist_all`. Status 갱신. |
| `backend/tests/test_canonical_relational_load.py` | computed/blended 검증 4종 추가(행수·재계산 결정성·blended MER·persist 멱등). |
| `docs/agent_specs/ERD/erd_octorad_normalized_computed_v0.1.dbml` | computed 테이블 네이밍 `{source_id}_computed` 정정 + acquisition_mer/platform_roas P2 표기. |
| `docs/reports/DB제작_구현현황_2026-06-17.md` | §4 현황표 Step5b/6/7 ✅ · §6 변경이력. |

## 4. 검증 수치
- **신규 test 4 + 기존 7 = `test_canonical_relational_load.py` 11 passed** (live DB temp schema에서 persist 검증 포함 — skip 안 됨).
  - computed 행수 = normalized 동일(meta 90·naver_sa 180·advoost 90·kakao 2·talktalk 2). orders computed 부재 확인.
  - 파생값 결정성: `roas_x == round(rev/cost, 2)` 전행 재계산 일치.
  - **blended 1행 · `total_marketing_cost_krw = 18,306,923` · `mer = 6.53`**(교차세계 정답 보존, google 제외).
  - computed/blended persist **멱등**(2회 == 1회) + DB 실제 행수 일치.
- **전체 회귀 987 passed** / 2 skipped / pre-existing 5 fail(parquet env×3·test_DC_PERM_6·test_o04 — 본 작업 무관).

## 5. 다음 (남은 일)
1. **⚠ 라이브 clumi 적재 (미완)** — 현재 정형 테이블은 *temp schema*에서만 검증. 실제 `clumi` schema엔 normalized/computed/blended **0**. 적재하려면 선행:
   - **C-1**: clumi orphan 76 typed 테이블 DROP (`setup_data_db.cleanup_legacy` 접미사 규칙).
   - **C-2**: stale `_workspace` 50행(layer='cleaned' 7·옛 computed 41·dangling raw 2) purge — **현 코드경로 없음 → 신규 스크립트 필요**.
   - 이후 `persist_all(result, 'clumi')` 실행 → 라이브 12테이블 생성.
2. **P2(별트랙)**: google 6채널+re-baseline(26.8M·MER 4.46) · `acquisition_mer`·`blended_platform_roas_x`(measure16) · rendering Workspace 위임 · cleaning `_storage`→State.
