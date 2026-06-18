# Session Compact Recovery — 2026-06-18 (할루시 3축 재정립 + 컨텍스트 엔지니어링 S1~S3)

> **다음 세션 첫 행동**: ① **[docs/_claude/ROADMAP.md](../_claude/ROADMAP.md) 읽기 = 닻** (§0 진짜 목표 + §0.1 ★할루시 3축 + §3 다음 한 걸음) → ② 본 문서 → ③ [S1-S3 계획서](../_claude/plans/S1-S3_execution_LLM_의미배선_구현계획_2026-06-18.md)·[고도화 계획서](../_claude/plans/gate최소화_컨텍스트엔지니어링_고도화_계획서_2026-06-18.md). 코드 `main 5ac8109`.
> **작업방식(필독 memory)**: `project_hallucination_root_cause_data_engineering`(★본 목표)·`project_agent_language_accumulation_intent`(컨텍스트 누적 의도)·`feedback_tool_work_pilot_first_data_layer_bound`·`feedback_targeted_git_add_no_blind_discard`(git add -A 금지·③ 미커밋 보존)·`feedback_anti_sycophancy_evidence_labeling`·`feedback_plan_intent_before_code`·`project_catalog_code_drift`(grep 단정 금지·실측)·`feedback_no_claude_commit_attribution`·`feedback_completion_report_on_done`.
> **★ 현 위치**: S1~S3(execution LLM 의미 배선) 첫 슬라이스 완료·검증. 다음 = report_writer/diagnoser/forecaster 동일 배선 **또는** C2(에이전트 e2e·②축 할루시 정량).

---

## §1 한 줄 요약
이 세션 = 데이터 본선(canonical) 완주 → 운영 대시보드 정렬 → 4중 감사 → ★**할루시 근본을 "데이터 엔지니어링"에서 "3축(정확성/이해/planning)"으로 정밀화** → ②축(데이터 이해=컨텍스트 엔지니어링) 근본 수정 S1~S3 착수·검증.

## §2 ★★ 할루시 3축 (이 세션의 핵심 깨달음 — 로드맵 정정)
이전 프레이밍 "근본=데이터 엔지니어링·gate=증상"은 **옳았으나 거칠었다**. 4중 감사로 3축 분해:
1. **① 데이터 정확성** — 틀린/이중세계 값. → **✅ canonical 해결**(A-5: World-B 전멸·26.8M/MER 4.46).
2. **② 데이터 이해 (컨텍스트 엔지니어링)** — 값은 맞는데 **LLM이 의미(단위·함정라벨)를 못 받음.** 의미 인프라(_COL_DESC·_lineage·glossary) 다 있으나 execution 해석 LLM 3종(insight_extractor·report_writer·summary_generator)에 **미배선**(벌거벗은 json.dumps). → **❌ 진짜 남은 데이터측 근본 = S1~S3로 착수.**
3. **③ planning 취약성** — LLM 스코프 누락·빈입력·둔갑. → 게이트가 지킴(28 중 25 정당).

★ **게이트 인과 재귀속 결론**(오너 가설 "데이터 문제를 planning이 억울하게 뒤집어썼다" 검증): **data_correctness 누명 = 거의 0건**(period:'all'은 param-flow 버그·데이터 멀쩡, canonical cutover도 tool 0 삭제). **단 ②(의미 미전달)는 진짜**(G04·G13). planning은 정당 배치(억울 아님). **진짜 억울 = 의미 인프라가 execution에 안 닿는 것.** 게이트 retire는 데이터 수정이 아니라 미배선(G01·G08)·중복통합 기준만.

## §3 이번 세션 커밋 지도 (main, `1fe59e8`→`5ac8109`, 13개)
| 커밋 | 내용 |
|---|---|
| `1fe59e8`·`0c6d1e2` | **A-5.2 google canonical 피봇** — re-baseline 18.3M/6.53 → **26.8M/4.46** (29파일: translator·라우트·yaml·docstring·테스트·glossary). 파생: CAC 30,512→44,678·promotion_roas 2.37→1.62 |
| `b9dd42d` | **A-5.3-①** daily 4 tool(daily_performance_totals·aggregate·channel_aggregate·conversion_funnel) → canonical 소비(`shared/canonical_daily.py`). 채널 advoost/google/meta/naver_sa·roas 배수·30일 |
| `a020901` | **A-5.3-②** dashboard1 라우트 3 직독(추이·채널스파크·비용) → canonical. **_campaign_pacing 제거**(기획예산↔실플랫폼 campaign_id 크로스워크 부재, 오너 결정) |
| `83b8d60`·`017e2bd` | **A-5.3-③a** daily_performance.csv·로더·SourceSpec 폐기 (external 17→16) |
| `d38f006`·`7f215d1` | **A-5.3-③b** format_normalizer 폐기 (catalog 93→92, planning 프롬프트·team_catalog·executor 정리). **옛 World-B normalizer 전멸** |
| `e5f873e`·`13f9df0` | **A-7 + 게이트 감사**(`w8477io1y`) — 재구축✗ 정합✓·게이트 28→23·게이트 대장 v1.5 §0 |
| `4b2e7d6` | **컨텍스트엔지 + 게이트 인과 재귀속**(`wgl8y5yk5`) — 할루시 3축·게이트 대장 v1.6 §0.1 |
| `5a9b456` | **tool 구조 심층 감사**(`wiclg6dps`) — 카테고리·프롬프트·layer + stale few-shot 정정(A-5.3 미완 봉합) |
| `5ac8109` | **S1~S3 컨텍스트 엔지니어링** — col_dictionary SSOT + build_data_glossary 주입 + system_prompt 계약 + qa 경로버그 정정 |

**A-3 캐시 cutover** = 코드 아닌 **DB 작업**(커밋 없음): octormate_data clumi `_workspace` cleaned7+computed41+normalized5 삭제 + daily_performance.csv raw 삭제 → 운영 대시보드 재계산 검증(ad-cost 26,806,923·roas 4.46·cac 44,678). raw 30(데이터 소스) 보존.
**미커밋(의도적)**: 프론트 카탈로그 ③ = `frontend/src/features/data_catalog/` + Sidebar/store/router 배선(보존).

## §4 S1~S3 (방금 완료 — ②축 첫 슬라이스)
- **S1** `backend/app/dream_agent/tools/shared/col_dictionary.py` 신설 — `COL_DESC`(단위 roas=배수·*_pct=%·*_krw=원 + 함정 salesAmt=비용·convAmt=매출) + `build_data_glossary(keys, client_id)` + `load_client_glossary`. canonical.py가 `COL_DESC` import(SSOT).
- **S2** insight_extractor·summary_generator `.py`(import+glossary) + `.yaml`(`{glossary}` 블록).
- **S3** 두 yaml system_prompt에 단위 계약.
- **★ qa_responder 버그 정정**: `_load_glossary` 경로 `parents[2]=tools` 오계산 → glossary 빈 채 돌던 것을 공용 `load_client_glossary`로 봉합.
- 검증: `tests/test_s2_data_glossary_injection.py`(5) — 단위·함정·프롬프트 주입 단언. 회귀 **1031 passed·신규실패0**.
- **미배선(후속)**: report_writer(입력=해석된 insights라 canonical키 0, 상류 insight 수정으로 간접수혜)·diagnoser·forecaster 동일 패턴 / S4 단위동봉{value,unit,desc} / S5 lineage 흐름.

## §5 4중 감사 산출 (전부 보고서로 박제)
- A-4 [대조표](../_claude/plans/agent_A4_tool감사_대조표_2026-06-17.md): stub 0·REPLACE/MODIFY/KEEP·data layer clean.
- A-7+gate [보고서](A-7_tool구조점검_게이트감사_2026-06-18.md)(`w8477io1y`): 재구축✗·_schema 3중drift·metrics 35 비대·게이트 28→23.
- 컨텍스트엔지+재귀속 [보고서](컨텍스트엔지니어링_게이트인과재귀속_2026-06-18.md)(`wgl8y5yk5`): 할루시 3축·data_caused 3.
- tool 구조 [보고서](tool구조_심층감사_카테고리_프롬프트_layer_2026-06-18.md)(`wiclg6dps`): 골격✅/의미흐름❌·execution 프롬프트 5 blocker·layer input clean/output leaky·삼중 S1~S3 #1 수렴.

## §6 핵심 위치
- **데이터 사전 SSOT**: `backend/app/dream_agent/tools/shared/col_dictionary.py` (COL_DESC·build_data_glossary·load_client_glossary).
- **canonical**: `tools/normalization/canonical_translator.py`(_CHANNELS 6채널 incl google·_lineage)·`scripts/build_canonical_pivot.py`(라이브 적재)·`api_v2/routes/canonical.py`(_AD_TABLES 4 incl google).
- **daily 전환**: `tools/shared/canonical_daily.py`(load_canonical_ad_rows)·metrics/{daily_performance_totals,aggregate,channel_aggregate}·comparison? (conversion_funnel는 metrics).
- **execution LLM**: `tools/analysis/llm/insight_extractor.py`·`tools/report/{report_writer,summary_generator}.py`·`tools/qa/llm/qa_responder.py` + `tools/prompts/*.yaml`.
- **stage 프롬프트**: `llm_manager/prompts/{cognitive,planning_stage1/2/3}.yaml` + `clients/clumi.yaml`(glossary).
- **게이트 대장**: `docs/agent_specs/43_gate_ledger_v1.0.md`(v1.6 §0·§0.1). §4 mermaid=생성물(직접수정 금지·sync 테스트).

## §7 라이브 DB 상태 (octormate_data clumi)
- canonical 14테이블(_normalized 7 incl google + _computed 6 + blended_computed 1) + *_raw 29 + `_workspace`.
- blended: total_marketing_cost **26,806,923**·MER **4.46**·tacos 22.37%.
- `_workspace`: **raw 30만 남음**(cleaned/computed/normalized 캐시 = A-3에서 삭제, 운영 대시보드는 재계산으로 canonical 서빙). 적재: `cd backend && uv run python -m scripts.build_canonical_pivot --client clumi --period 2026-04`.

## §8 다음 한 걸음 + 남은 일
**다음 (택1)**: ①**S1~S3 확장** report_writer/diagnoser/forecaster 동일 배선(저위험·같은 패턴) / ②**C2 에이전트 e2e** — clients/clumi.yaml + "clumi 4월 ROAS" 라이브 4레이어 통과·canonical 정답(4.46)·**②축 할루시(단위 오독·함정) 감소 정량**(measure_gate_correction 류). **권장 = C2**(S1~S3 효과 입증).
**오너 합의 대기/보류**: 게이트 실제 적용(28→4 메커니즘 + 위생 분리, 코드는 Phase B 측정 후) · ai_recommendation/recommender 통합(출력키 통일 필요, 삭제는 오너 결정) · _schema taxonomy 봉합 8→10~11 · 오분류 회수(정제룰→cleaning·grade_timeseries→metrics) · consumes per-tool catalog 일원화(⚠catalog_code_drift 실측 대조) · output persist 계약(DB 재구축 시점) · dimension normalizer 4종(P5).

## §9 정직 경고 (과신 금지)
1. **S1~S3는 insight_extractor·summary_generator만** — report_writer/diagnoser/forecaster 미배선. ②축 완전 수정 아님(첫 슬라이스).
2. **②축 할루시 감소는 미측정** — S1~S3가 실제로 할루시를 줄였다는 **라이브 증거(C2) 없음**. 프롬프트에 사전이 들어간 것만 검증됨.
3. **게이트 코드는 아직 안 줄임** — 대장(43)에 분석만 박제(v1.5/v1.6 §0). 실제 retire/merge 적용은 오너 승인 + 측정(Phase B) 후. §1/§4 미변경.
4. **운영 대시보드 캐시는 비워둠** — 첫 요청 시 재계산(canonical). channel_targets.csv 채널명(naver/kakao)·프론트 라벨/roas표기는 ③ 디자인 미반영(canonical 데이터엔 정상, 화면 라벨만 어긋남).
5. **_campaign_pacing 제거됨** — 크로스워크 생기면 복원. /비용 pacing=빈 배열.
6. **catalog_code_drift 상존** — team_catalog consumes 8건이 코드 실호출과 일치 보장 없음. consumes 일원화 시 grep 단정 금지·실측 대조.
7. 회귀 baseline **1031 passed**(pre-existing 10: parquet env 4·_scratch 구조 4·test_DC_PERM_6·test_o04).
8. **qa_responder가 그동안 glossary 빈 채 돌았음**(경로 버그, 방금 정정) — 과거 qa 답변 품질이 의미 인프라 없이 나왔을 수 있음.

## §10 메모리 (이 세션 신설/갱신 권장)
- (갱신) `project_hallucination_root_cause_data_engineering` → 3축 정밀화 반영 권장(②축 컨텍스트엔지 추가).
- (참조) `project_agent_language_accumulation_intent`(컨텍스트 누적 의도)가 file:line으로 확증됨 — execution 단절.
- canonical 헤드라인 26.8M/4.46은 코드/ROADMAP/보고서가 기록(메모리 불요).
