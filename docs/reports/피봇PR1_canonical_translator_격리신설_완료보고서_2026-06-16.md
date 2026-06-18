# 완료보고서 — 피봇 PR1: canonical_translator 격리 신설 (2026-06-16)

> 세부계획 [02 tool 구현](../_claude/plans/normalized_pivot_세부02_tool_구현_2026-06-16.md) T1(P2 격리)의 첫 구현. 오너 승인("응") 후 착수.
> 방식: `feedback_no_mixed_codebases`(격리 우선 — 기존 tool 0 수정) · `feedback_test_no_resource_limit`(변경+인접 회귀).

## 무엇을 / 왜
피봇의 심장 = **단일 contract-driven translator**가 산발한 하드코딩 normalizer(ad_cost_helper 등)를 흡수. 프로토타입(`data_pilot_project/{pipeline,compute}.py`)을 **production BaseTool `normalization/canonical_translator`로 충실 포팅**. 첫 PR은 **격리**(기존 tool 미수정 = 회귀 0) + **5채널**(google 제외)로 기존 정답을 *정확 재현* → 포팅 충실성 증명. google 6채널·measure16·aMER·re-baseline은 후속 PR.

## 변경 파일 (tracked)
| 파일 | 내용 |
|---|---|
| `backend/app/dream_agent/tools/normalization/canonical_translator.py` | 신규 — BaseTool. raw(self.fetch) → canonical measures + computed(MER) + lineage |
| `backend/app/dream_agent/tools/catalog/normalization/canonical_translator.yaml` | 신규 — catalog 등록(registry 자동 추론) |
| `backend/tests/test_canonical_translator.py` | 신규 — 8 테스트(정답 재현 + 교차세계 동치 + lineage) |
| `backend/tests/test_normalized_pivot_baseline.py` | catalog count 92→93(신설 +1) |
| `backend/tests/data_sources/test_file.py` | google-count 정정 16→17·30→31(7e17c24 google 누락분) |

## 검증 (✓ 실행)
- **정답 재현(독립 경로)**: tool 산출 = `self.fetch`(DataSource) 경로로 `total_marketing_cost` **18,306,923** · MER **6.53** · 채널별(meta 9,235,826·naver_sa 5,999,627·advoost 3,000,000·kakao 59,020·talktalk 12,450) — production ad_cost_helper와 **완전 일치**. = 피봇 thesis가 *production tool 수준*에서 실증.
- **회귀**: 피봇 스위트 **72 passed**(translator 8 + baseline 10 + dimension 4 + data_sources 등). data_pilot gate **OVERALL PASS**. catalog 순회 테스트(collectors·period·slice1) **38 passed**.
- **전체 backend 스위트**: 975 passed / 6 failed.

## 정직 — 전체 스위트 6 실패 = **전부 pre-existing**(내 PR1 회귀 0, stash로 증명)
clean HEAD(내 변경 stash)에서도 동일 6 실패 → 내 작업과 무관:
- 3 = parquet 환경(pyarrow 미설치) — `test_save_parquet*`·`test_meta_companion_schema`
- 1 = `test_kind_counts`(google 7e17c24 등록 후 카운트 미갱신) → **본 PR서 정정**(16→17)
- 2 = `test_DC_PERM_6_tool_no_ml_model_bypass`·`test_o04_cards_sorted_by_roas` — 무관·범위 밖(미수정, 별도 추적 권장)

## 한계 (과신 금지)
- **5채널·핵심measure만.** google·measure16(link_clicks·reach·frequency·vt·msg_target/open/click)·aMER = 미구현(후속 PR). re-baseline(18.3M→26.8M) 미발생.
- storage layer = `cleaned`(현 Workspace Literal). P1 `normalized` rename 시 tool·catalog·test storage assert 동반 갱신 필요(명시해 둠).
- currency config = mock KRW identity 임시. conversion_config 외부화(D3)는 후속.
- 기존 tool(ad_cost_total 등) **미전환** — 여전히 ad_cost_helper 사용. A/B 전환은 P3.

## 다음
- **PR2**: google 6채널 통합 + measure 16 추출 + aMER → re-baseline(EXPECT 갱신, [04] N3).
- 또는 **P1 받침대**(Layer rename·관계형 스키마·config 이전, [03]) 선행 — 순서는 오너 판단.
