# 완료보고서 — normalized 피봇 세부계획서 4종 분할 작성 (2026-06-16)

## 무엇을
상위 [normalized tool 피봇 최종 계획서](../_claude/plans/normalized_tool_pivot_계획서_2026-06-15.md)(무엇/왜)를 검증한 뒤, 그 P0~P5 로드맵을 **관심사별 세부 실행서 4종**(정확히 어떤 코드/DDL/테스트)으로 분할 작성.

| # | 세부계획서 | 핵심 |
|---|---|---|
| 01 | [데이터 생성/보완](../_claude/plans/normalized_pivot_세부01_데이터_생성보완_2026-06-16.md) | **데이터 생성 = google 1건뿐(완료)**. 누락 measure 7+aMER는 raw에 원천 실재 → 추출(생성 X). blocked 4건은 명시 라벨 |
| 02 | [tool 구현](../_claude/plans/normalized_pivot_세부02_tool_구현_2026-06-16.md) | canonical_translator 신설(프로토타입 포팅)·REPLACE 6 흡수·MODIFY 10 A/B 전환·PR 8단계 시퀀스 |
| 03 | [기타 구현](../_claude/plans/normalized_pivot_세부03_기타_구현_2026-06-16.md) | Layer cleaned→normalized·관계형 스키마 DDL(raw=blob)·contract→config 이전·DB 재구축·정리 sprint |
| 04 | [테스트](../_claude/plans/normalized_pivot_세부04_테스트_2026-06-16.md) | 기존 오라클 3(green)·re-baseline 갱신·신규 N1~N6·phase×게이트 매트릭스 |

> 계획서는 `docs/_claude/`(gitignore). 본 보고서가 tracked 추적 채널.

## 왜 (오너 요청)
"기존 계획서 검증하고 세부계획서를 여러개로 분류해서 작성: 1.데이터 생성/보완 2.tool 구현 3.그외 구현 4.테스트." → 단일 마스터 계획을 실행 단위로 쪼개 P0 상세설계의 골격 확보.

## 검증 (✓ 실측 — 추측 아님)
계획서 작성 전, 의존 사실을 코드/데이터 직접 대조:

| claim | 검증 | 결과 |
|---|---|---|
| 프로토타입 4파일 실재·구조 | pipeline/compute/transforms/dimensions.py 직독 | ✓ CHANNELS 5·AD/MSG 분리·mer=총마케팅비 |
| 교차세계 오라클 green | test_normalized_pivot_baseline(10)·test_dimension_normalizer_prototype(4) 직독 | ✓ 18,306,923·6.53 |
| **누락 measure 원천 raw 실재** | meta inline_link_clicks/reach/frequency(270 occ)·advoost view_through_conversions(헤더)·orders is_first_order(헤더)·kakao summary(10 occ) grep | ✓ **8건 전부 존재 → 생성 불요** |
| Workspace Layer 현 타입 | base.py:21 `Literal["raw","cleaned","computed"]` | ✓ |
| Postgres 저장 구조 | postgres.py `_workspace(layer,key,payload jsonb)`+typed | ✓ |
| contract layers 명명 drift | contract line 17 아직 `cleaned:` | ⚠ P1 정정 대상(세부03 I3) |

## 변경 파일
- 신규 4: `docs/_claude/plans/normalized_pivot_세부01~04_*_2026-06-16.md`
- 수정 1: 마스터 계획서 — 세부 4종 포인터 추가 + §10 "열린 결정 2" → **0(해소)** 정합(mer 정정 완료·coverage=blocked 라벨)
- 신규 1: 본 완료보고서

## 핵심 수치
- 데이터 생성 필요: **1건**(google, 완료) / 추출 대상: measure **8**(원천 실재) / blocked: **4**(외부 doc 대기, fabricate 금지)
- tool 임팩트: REPLACE **6** / MODIFY **10** / KEEP **77**
- re-baseline(P2 예정): 총마케팅비 18,306,923 → **26,806,923**, MER 6.53 → **~4.46**(google +8.5M, 분모만 — 의도된 변동)
- 신규 테스트: N1~N6 (Layer·격리·re-baseline·A/B·정리·dim) / phase 게이트 5단

## 정직 경고 (과신 금지)
1. **구현 코드 0** — 본 작업은 *계획 분할*. canonical_translator·Layer 변경·DB 관계형화 전부 미착수.
2. **re-baseline 미발생** — 답은 아직 18.3M·6.53. google 합산(→26.8M·4.46)은 P2. 4.46은 산정값(정확치는 P2 실측).
3. **MER 하락은 버그 아님** — google 광고비가 orders 매출에 미귀속한 mock 특성. 테스트 갱신 시 이유 주석 필수.
4. blocked 4건은 데이터로 못 메움 — *정의*(Kakao 대행사 doc) 공백. mock 보강 ≠ 해결.

## 다음
**오너 검토 → 승인 시 구현 착수.** P1(받침대: Layer·스키마·config) → P2(translator 격리+google+measure16+aMER, re-baseline) → P3(MODIFY 10 A/B) → P4(정리) → P5(dim/time). 각 phase 게이트 = 세부04 매트릭스.
