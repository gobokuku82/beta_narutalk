# Session Compact Recovery — 2026-06-18(b): ② 데이터 의미 전달 (SSOT provenance + A/B 측정)

> **다음 세션 첫 행동**: ① [ROADMAP §0.1](../_claude/ROADMAP.md)(원칙: 구조 우선·측정=확인) → ② **[② 의사결정 dossier](../_claude/plans/②의미전달_의사결정_dossier_2026-06-18.md)** = 모든 가설·결정·A/B 결과 박제(★핵심 닻) → ③ 본 문서. 코드 `main 7562b63`.
> **작업방식(필독 memory)**: `project_hallucination_root_cause_data_engineering`·`feedback_anti_sycophancy_evidence_labeling`·`feedback_targeted_git_add_no_blind_discard`(git add -A 금지·③ 미커밋 보존)·`feedback_plan_intent_before_code`·`project_catalog_code_drift`·`feedback_no_claude_commit_attribution`·`project_data_viz_work_division`(계산/지표 공식=오너 영역).
> **★ 현 위치**: ② provenance 배선 + A/B 1·2차 완료. **2차(v3 강제형·v4 인라인·v5)도 측정·기각 — 전달 방식으론 v2 못 이김(floor ~4/12). 다음 = 콘텐츠/이름(frequency_ratio 개명).** (dossier §10)

## §1 한 줄 요약
이 세션 = **할루시 ②축('데이터 의미 전달')을 가설-검증 루프로 수술**: 죽은 `canonical_contract.yaml`을 런타임 의미 SSOT로 승격(provenance) → 빠진 지표 5종 추가 → 공식 실데이터 검증(버그1 수정) → **A/B 측정으로 "② 의미배선은 작동하나 내 provenance 리팩터는 손코딩을 못 이김"을 정직하게 입증.**

## §2 기준점 (이 세션 재정립 — ROADMAP §0.1)
- **할루시 = 증상이지 작업 대상 아님.** load-bearing 구조(②③)를 제대로 → 할루시↓. **측정 = 구조 가설을 *확인*하는 도구**(게이트/타깃 아님). 루프: 불안정→가설→테스트→확인.
- **② = 두 반쪽**: 의미 계층(설계: 단위·정의·함정·계보) + 의미 배선(전달). 용어 **"데이터 의미 전달"**.
- **load-bearing(②③) vs decorative(tool/category)**: category는 P2·P4 실측=라우팅 미사용 → 화장(보류).
- **★오너 결정**: 원본 authored 메타데이터(contract=canonical SSOT, CSV=raw 토대)를 LLM이 *파생*받는다. 손코딩 COL_DESC 사본 폐기. **description은 LLM이 읽을 것이니 LLM-grade로 작성.**

## §3 이번 세션 커밋 지도 (②  스레드, `main`)
| 커밋 | 내용 |
|---|---|
| `10c0ff6` | S2-ext: diagnoser/forecaster/report_writer 의미배선 + G-B nested 스캔 |
| `24899fa` | P2: _schema taxonomy stale 주석 봉합(8→11, doc-only) |
| `a7bfca9`·`fe5e154` | C2 ②축 라이브 측정 하네스 + 혼합 결정 + §7 정정(할루시=증상) |
| `a9ad64a` | ② 첫 슬라이스: `semantic_contract.py`(contract reader) + 동치 테스트(전제 확인) |
| `d29a582` | 빠진 계산지표 5종 contract 추가(cac·cpa·aov·promotion_roas·promotion_share_pct, 코드 실측 공식·LLM-grade) |
| `5b0f398` | CPA/CPC 0분모 버그 수정(None 규약, 0=최고 위장 방지) |
| `a9538e7` | **② provenance 배선**: `build_data_glossary`가 contract(SSOT)에서 파생, COL_DESC 강등(residual fallback) |
| `7562b63` | A/B glossary 하네스(`scripts/c2_ab_glossary.py`) — 반증③ 측정 |
| `d7c29bc` | 본 compact 복구 문서 |
| `d7f03c4` | A/B 2차: v3/v4/v5 6조건 + `unit_token` — 전달 방식 가설 측정·기각(§6·dossier §10) |

**미커밋(의도 보존)**: 프론트 ③ 카탈로그(`frontend/src/features/data_catalog/`+Sidebar/store/router). **P4 findings 보고서**(`docs/reports/P4_...`)도 미커밋(보류). ROADMAP·dossier·게이트방법론 = gitignored 작업닻.

## §4 ★★ A/B 측정 결과 (반증③ — 이 세션의 핵심 발견)
`scripts/c2_ab_glossary.py`: LLM 분석기 4종 동일 입력·glossary 3조건(OFF 사전없음/v1 손코딩 COL_DESC/v2 contract 파생) 실 LLM·단위오독 LLM 판정.
- **easy(roas/cac/mer)**: off=v1=v2=0 — LLM이 자명 단위 이미 앎.
- **하드(tacos_pct/msg_roi_pct/frequency_ratio/promotion_roas/cpc, reps=3·n=12)**: **OFF 7 / v1 3 / v2 5** unit_error.

★ **두 결론**:
1. **② 의미배선 작동 (반증③ 기각)**: OFF 7 → ON 3~5. 비자명 지표서 사전이 ②축 할루시 ~30~55%↓. **② 전제 검증됨 — decorative 아님.** (easy 차이0은 LLM이 이미 알아서.)
2. **⚠ provenance(v2)가 손코딩(v1) 미개선·약간 후퇴**(3 vs 5+fab). contract description이 COL_DESC의 "★%/★배수,%아님"보다 무딤(semantic 없는 키=formula 파생). → **provenance 가치 = SSOT/드리프트0(유지보수)지 할루시 아님.** (정직: 내 a9538e7이 할루시는 안 줄임.)
- ★ noise: n=12·판정기 단일·페이로드1 → v1 3 vs v2 5는 노이즈 범위(확실=미개선, 불확실=정말 더 나쁜가).
- ★ **frequency_ratio는 전 조건 '구매빈도/횟수' 오독** — v2 경고("구매빈도 무관")도 LLM 무시. **강 prior는 프롬프트 경고로 안 꺾임.**

## §5 ② 구조 현황 (SSOT 아키텍처)
```
원본(SSOT) 2층:
  raw 층      → data/clumi/description/clumi_data_dictionary.csv (360행, 사람 토대, dict_gate 정합)
  canonical층 → docs/agent_specs/ERD/octorad_canonical_contract_v0.1.yaml (LLM-facing SSOT, measures+metrics+dimensions+time)
배선: semantic_contract.describe(key) → build_data_glossary가 우선 사용 → residual(tool 합성키 total_*·by_channel)만 COL_DESC fallback
폐기 대상(점진): 손코딩 COL_DESC (현재 residual fallback로 잔존)
coverage: COL_DESC 71키 중 49(69%) contract 파생, residual 22=전부 tool-output 합성키+dimension(진짜 지표 0)
```

## §6 ★ A/B 2차 (v3/v4/v5) — 측정 완료·기각 (커밋 d7f03c4, dossier §10)
오너 제안(강제형·인라인)을 v3/v4/v5로 측정. **결과: 전부 v2 미개선** (off 8 / v1 3 / v2 4 / **v3 5+fab3 / v4 4 / v5 5**).
- **v3 강제형**(블록 강제헤더+system_prompt 메타규칙): v2보다 나쁨, **날조↑**(강명령형이 과단정화).
- **v4 인라인**(`tacos_pct: 22.37`→`"22.37 (%)"`, 블록 제거): v2 동률 — 단위는 나르나 trap 잃음, 순효과 0.
- **v5**(블록+인라인): 개선 없음.
- ★ **floor ~4/12는 전달 실패가 아님** = 콘텐츠/이름: **frequency_ratio 강-prior(블록·강제형·인라인 3중 다 '구매빈도' 오독 → 3중 입증)** · promotion_roas trap · msg_roi ROI≠ROAS축. noise(n=12)지만 "v3/v4가 v2 이긴다" 기각은 robust.

### A/B 3차 (v6/v7 개명) — 측정·★확정 (dossier §11, freq_misread 격리지표)
**freq_misread: v2 7 → v6 0 → v7 2.** v2(`frequency_ratio`)는 "구매빈도 무관" 경고를 *갖고도* 7/12 오독, v6(`impression_frequency`)은 경고 *빼고도* 0/12. **이름이 원인**(프롬프트 아님) — 2차 "프롬프트로 안 꺾임"(3중) + 3차 "개명으로 꺾임" = 폐곡선. ★구조(이름) 고치니 할루시 사라짐 = 근본원인 명제 첫 정량 증거. ⚠ 표준 용어(impression_frequency)가 신조어(exposures_per_reach=v7 2+불안정)보다 우월 → 신조어 금지.

### 캐논키 개명 ★적용 완료 (2026-06-19, 오너 승인 — dossier §11b)
`frequency_ratio` → `impression_frequency` 실개명. 런타임 4곳(contract SSOT·translator×2·col_dictionary·coverage)+하네스+테스트+ERD doc 7. back-compat alias 미추가(클린 컷). **검증: pilot 9/9(MER 4.46 불변)·coverage FAIL 0·타깃 50 passed·전체 1008 passed/5 failed(전부 pre-existing 신규 0).** 부수: d29a582 누락 5지표 coverage DEFERRAL 추가(잠복 FAIL 해소). 학습=memory `project_canonical_naming_avoid_prior_collision`.

### A/B 4차 (남은 floor 키 개명 점검) — 측정 완료·개명 레버 경계 (dossier §11c)
v2 vs v8(promotion_roas→promotion_roas_x). **proas_unit_err 2→1(노이즈, 저율)** · **msgroi_axis_err 3→3 불변**. → promotion_roas는 개명 대상 아님(명시 semantic 이미 작동), msg_roi는 **semantic 바닥**(ROI≠ROAS 개념혼동, 이름 무관). **개명 레버는 frequency(진짜 동음이의 7/12)에서 큰 것 잡고 소진.** 남은 floor(~3/16)=전달·개명 둘 다 안 통하는 semantic 잔차 → **floor 수용**.

### 다음 세션 시작점 (②축 측정 사이클 종료 — 구조 후속으로)
- (a) **②축 결론**: 의미배선 작동(off 8→on 3~5) + 큰 floor 1개=frequency 개명으로 제거 + 잔여 floor=semantic 수용. ②축 측정 사이클 닫힘.
- (b) **후속 구조**: 중앙주입(LLMTool 베이스 — 6 tool 복붙·qa 비대칭 해소) · COL_DESC residual 합성키 파생→완전 폐기 · 게이트 28→4(방법론 박제됨).
- (c) provenance(v2)는 SSOT/유지보수 가치로 유지.

## §7 미결/보류
- **오너 비차단 정의선택**: CAC 신규회원(600 무필터 vs 571 탈퇴제외 +5.1%)·N00 입금전 매출(active의 68%) — 현 동작 유지 중, 언제든 confirm/change(=tool 변경). contract semantic은 현 동작 정확 기술.
- **후속 구조**: 중앙 주입(LLMTool 베이스 — 6 tool 복붙·qa 비대칭 해소) + COL_DESC residual 합성키 파생 → COL_DESC 완전 폐기.
- **게이트 28→4**: 방법론 박제(`docs/_claude/plans/게이트_검증_방법론_보류_2026-06-18.md`), C2 측정 후. blended_platform_roas_x=tool 없음(contract 제외).

## §8 핵심 위치
- **의미 SSOT**: `docs/agent_specs/ERD/octorad_canonical_contract_v0.1.yaml`(contract) · `backend/app/dream_agent/tools/shared/semantic_contract.py`(reader+describe) · `col_dictionary.py`(build_data_glossary→contract 위임·COL_DESC fallback).
- **측정 하네스**: `backend/scripts/c2_hallucination_measure.py`(C2 라이브 4레이어) · `c2_ab_glossary.py`(A/B glossary 3조건). 결과 = `docs/_claude/4layer_system/diag_results/c2_*.json`.
- **공식 검증**: 워크플로 `wb7456v44`(실데이터 대조). cac=cac_overall·cpa=channel_aggregate·aov=aov_monthly.
- **dossier(★모든 가설·결정)**: `docs/_claude/plans/②의미전달_의사결정_dossier_2026-06-18.md`.

## §9 정직 경고
1. **provenance(a9538e7)는 할루시를 안 줄였다** — SSOT/유지보수 가치만. 할루시 감소는 v3/v4(다음)가 입증해야. 과신 금지.
2. **A/B는 n=12·단일 판정기·페이로드1** — 방향성이지 통계적 확정 아님. v3/v4 측정 시 reps↑·판정기 다양화 권장.
3. **② 의미배선 작동은 *하드 지표 한정*** — 자명 지표(roas/cac)는 LLM이 이미 알아 사전 무효. 사전의 가치는 비자명/시스템특정 키에 집중.
4. 회귀 baseline = **1046 passed**(pre-existing 10: parquet env·_scratch·test_DC_PERM_6·test_o04). 이 세션 신규 테스트 전부 통과, 신규실패 0.
5. **계산 공식 = 오너 영역** — contract 5지표는 *코드 실측* 공식 박제(임의 아님), 오너 확인점 10건 dossier §7.
