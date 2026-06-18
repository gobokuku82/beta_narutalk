# Session Compact Recovery — 2026-06-17 v2 (할루시 로드맵 재정립 + canonical tool 전환 진행 중)

> **다음 세션 첫 행동**: ① **[docs/_claude/ROADMAP.md](../_claude/ROADMAP.md) 읽기 = 닻**(§0 진짜 목표 + §3 다음 한 걸음) → ② 본 문서 → ③ [agent_C 계획서](../_claude/plans/agent_C_계획서_2026-06-17.md)·[A4 tool감사 대조표](../_claude/plans/agent_A4_tool감사_대조표_2026-06-17.md). 코드 `main 2266a62`.
> **작업방식(필독 memory)**: `project_hallucination_root_cause_data_engineering`(★본 목표)·`project_data_layer_roadmap_sequence`·`feedback_tool_work_pilot_first_data_layer_bound`(contract·파일럿·data layer)·`feedback_targeted_git_add_no_blind_discard`(git add -A 금지·내가 안 만든 변경 폐기 금지)·`feedback_anti_sycophancy_evidence_labeling`·`feedback_plan_intent_before_code`·`feedback_no_claude_commit_attribution`·`feedback_no_mixed_codebases`·`feedback_test_no_resource_limit`·`feedback_completion_report_on_done`·`feedback_convention_over_hardcoding`.
> **★ 현 위치**: A-5.2(google canonical 피봇 = re-baseline 18.3M→26.8M) **착수 직전, 오너 go 대기.** A-5.1(ad_cost_helper 폐기) 완료.

---

## §1 한 줄 요약
이 세션 = ① DB제작 마무리(computed/blended + 라이브 12테이블) → ② 마케팅 성과 페이지(수직슬라이스+심화) → ③ **★대전환: 로드맵 재정립** — "에이전트 할루시 제거가 목표 / gate(8→27)는 증상 / 근본=데이터 엔지니어링 / canonical이 본선" → ④ 에이전트 진단(C1)·tool 전수 감사(A-4) → ⑤ **핵심 5 지표 tool을 canonical로 전환(A3)** + ad_cost_helper 폐기(A-5.1). 다음 = google 피봇(re-baseline) → daily_performance 전환 → A-7 tool 구조 점검 → C2 에이전트 e2e.

---

## §2 ★★ 진짜 목표와 through-line (이걸 놓치면 또 길 잃는다 — 세션 내내 3회 교정함)
**목표 = 에이전트의 할루시네이션 제거.**
1. 4-layer + manager **구조는 잘 돈다**(진단 `w91cuceso` 확인 — Cognitive→Planning→Execution→Response 구동·HITL 有).
2. **그러나 출력 할루시가 심함** → 막으려 **gate 신설 → 8 → 27개로 증식**([게이트 대장 43](../agent_specs/43_gate_ledger_v1.0.md)).
3. ★ **근본 원인 = 데이터 엔지니어링**(부정확·불일치 데이터: 이중세계·틀린 normalized·미reconcile → 에이전트 입력/산출 흔들림 → 할루시).
4. ★ **전략 = gate 추가 아니라 데이터부터 재수술**(canonical raw→(clean)→normalized→computed) → 입력 깨끗 → **할루시 근본 감소 → gate 증식 멈춤**.

→ **canonical(데이터 엔지니어링) = 본선 / 에이전트(C) = 그 위 검증 / gate = 증상 계기판.** 매 작업: "할루시 근본(데이터)을 고치나, 증상(gate/페이지)을 늘리나"로 판단.

**내가 길 잃은 패턴(교정됨)**: "다음작업/더 다듬기" 마다 ③(페이지 폴리시: 마케팅 성과 심화·카탈로그)으로 직행 → 곧 drop할 DB 위에서 페이지 칠함. 오너 교정: "프론트 연결됐으니 drop 위험 → 거기서 이상해졌다." 해소책 = A3(tool→canonical)이 drop 위험을 해소(tool이 canonical 읽으면 옛 데이터 drop해도 안전).

---

## §3 ROADMAP 구조 (= [docs/_claude/ROADMAP.md](../_claude/ROADMAP.md) 요약 — 닻)
### 트랙 A — 데이터 엔지니어링 (★본선) — 오너 명시 중간 과정
| 단계 | 상태 |
|---|---|
| A-1 raw→(clean)→normalized→computed 확정 | 🟦 ad·msg·주문 ✅(MER 6.53) / google·daily·clean단계 ⬜ |
| A-2 DB 구조 확인 | ✅ clumi 42테이블 |
| A-3 DB 정상성(깨끗한 단일진실?) | ⚠ 신·구 공존(옛 World-B 잔존) |
| A-4 기존 tool 구조 전수 점검 | ✅ 감사 `wa7ora1u6`(§6) |
| A-5 옛 World-B 제거 + daily/google 전환 | 🟦 A-5.1 ad_cost_helper 폐기 ✅ / A-5.2 google·A-5.3 daily ⬜ |
| A-6 tool/data layer 분리 확인 | 🟦 감사 `wm425xjo3`: 입력·의존·schema clean / 출력 leaky(rendering·_storage) |
| **A-7 ★ TOOL 전체 구조 점검**(A-5 후·오너 명시) | ⬜ ①카테고리 유지vs수정/확장 ②카테고리별 tool 구성 ③완전재구축vs점검후결정(살릴/수정/삭제) ④그후 방향 |
### 트랙 C — 에이전트 (그 위 검증·본 목표) — 상세=[agent_C 계획서](../_claude/plans/agent_C_계획서_2026-06-17.md)
| C1 진단 ✅ | C2 e2e+clumi 프로필 ⬜(다음 데이터 후) | C3 metric stub 실측(이미 stub 0 판명) | C4 성장(sub_intents·모호성 HITL·qa RAG) |
### 가로지름 — gate(증상): 27개([대장 43](../agent_specs/43_gate_ledger_v1.0.md)). 데이터 수술 후 1회 감사(은퇴·통합). "gate 증식 멈춤"=성공지표.

### ★ 작업 가드레일 (오너 명시, ROADMAP §6.1 / memory `feedback_tool_work_pilot_first_data_layer_bound`)
1. **interface contract 준수+갱신**: [20_INTERFACE_CONTRACT_v1.1](../agent_specs/20_INTERFACE_CONTRACT_v1.1.md)(4-layer I/O: StructuredQuery·Plan·ExecutionResult·ResponsePayload).
2. **파일럿 먼저**: tool 직접 수정 전 `backend/app/data_pilot_project/`에서 DB 검증 → 그 결과로 production tool 구현.
3. **data layer만**: tool은 `data_sources`·`workspace`·`schemas`로만(raw 직독 금지·`self.fetch`). [[project_intended_layer_architecture]]·[[project_tool_data_agent_separation]].

---

## §4 이번 세션 커밋 지도 (main, `3f33ea3`→`2266a62`)
| 커밋 | 내용 |
|---|---|
| `3f33ea3` | DB제작 Step5b+6 — translator computed(5)+blended_computed + 테스트 11 |
| `ed5701d` | computed/blended 완료보고서 |
| (`a64931a`) | (오너) 65 §5.3 DB 연결 현황 — 내 작업 무관 |
| `d8d3cc6` | `build_canonical_pivot.py`(라이브 적재) + C-1 orphan 76 DROP + C-2 정정 |
| `db2a188` | **마케팅 성과 페이지** 수직슬라이스(`/api/canonical/marketing-performance` + 프론트) |
| `f436dbc` | fix: 페이지 icon TrendingUp→Target(replace_all 누락 런타임 버그) |
| `ed5ca90` | 마케팅 성과 심화 — 캠페인 드릴다운 + ROAS 비교 차트 |
| `59c729a` | 마케팅 성과 — 전환 사슬(MetricChainStrip) + 캠페인 채널 필터 |
| `1be066c` | **① 연결 검증** `test_pipeline_connection`(4단) + `/api/canonical/catalog` 인벤토리 endpoint |
| `7a5113f` | **A3** ad_cost_total → canonical 전환 |
| `7e07a82` | **A3** roas·cac·promotion·channel_cac → canonical 전환 (ad_cost_helper 소비처 0) |
| `2266a62` | **A-5.1** ad_cost_helper 폐기 |

**미커밋(의도적)**: 프론트 카탈로그 페이지 = `frontend/src/features/data_catalog/` + router/nav/Sidebar 카탈로그 배선 = **③(보류)**. ROADMAP·agent_C·A4대조표 = docs/_claude(gitignored, 로컬).

---

## §5 핵심 결정 (전부 ROADMAP/메모리 박제)
- **★ 가 결정 (google 포함)**: A-5.2에서 google_ads_performance를 canonical에 피봇 → **re-baseline: 총마케팅비 18,306,923→~26,800,000 · MER 6.53→~4.46.** 옳은 갱신(google 실채널)이나 *모든 canonical 테스트·전환 5tool 기대값·마케팅 페이지 신뢰게이트·18.3M 가정 문서* 동시 갱신 필요. **착수 직전 오너 go 대기.**
- **daily_performance 처리(실측 결정)**: daily_performance.csv=World-C mock(26.6M 미reconcile, mock_api 원본 아님). 4 tool(channel_aggregate·conversion_funnel·daily_performance_totals·daily_performance_aggregate)이 읽음. **검증: ①일별/채널 시계열 필요O ②canonical(report_date)에서 파생 가능O(정합 18.3M, creative_id는 4tool 미사용=무손실, google는 canonical 피봇 필요) ③신규생성 불요.** → **csv 삭제 + 4 tool을 canonical 일별집계로 전환(파일럿 먼저).** (A-5.3)
- **C-2 = 옛 serving 캐시(삭제 X)**: clumi `_workspace` cleaned 7+computed 41 = stale 아님 = **운영 대시보드 라이브 serving 캐시**(main.py DATA_BACKEND=postgres→PostgresWorkspace, dashboard1 `_cached_or_run`이 동일 cache_key 읽음). 삭제하면 운영 5p+/monthly 파손. **API가 canonical 읽도록 cutover 후 폐기.** (C-1 typed orphan 76은 DROP 완료, serving 무해.)
- **format_normalizer**: REPLACE·dormant이나 catalog/team_catalog/prompt/registry/test 걸쳐 제거 복잡 → **daily/World-C 정리와 함께**(A-5.3 동반).

---

## §6 진단 결과 (워크플로 2회)
### `w91cuceso` — 에이전트 4-layer 진단 (C1)
- **에이전트는 미착수 아님 — 구동 중.** 진입 `ws_agent.run_turn`(ws_agent.py:490) → LangGraph `astream`+interrupt(204-488) → `system_graph/builder.py:27-44`(4노드, Command.goto 동적 라우팅). main.py:47 lifespan eager init.
- ⚠ **정정: 13-node 아님 = 4-node(=4-layer).** execution 내부는 Phase while-loop(노드 아님).
- 레이어: Cognitive(cognitive_stage.py:128, StructuredQuery PMAL intent)✅ · Planning(planner.py:622, 3-stage LLM+결정론 보강, team_catalog 10 agent·~90 tool)✅**가장 성숙** · Execution(executor.py:171, agent_pool·data_gate·state_guard)🟦 · Response(responder.py:490, 결정론 시각화·**LLM 0**, 서술은 execution 도구가)✅.
- 갭: ★clumi client 프로필 부재(`llm_manager/prompts/clients/{client}.yaml` 없어 generic 모드) · ★e2e 실작동 미검증 · execution raw→state 누수(state_guard로 완화) · sub_intents/모호성 HITL(성장).

### `wa7ora1u6` — tool ~80개 전수 감사 (A-4) → [대조표](../_claude/plans/agent_A4_tool감사_대조표_2026-06-17.md)
- ★ **stub = 사실상 0.** "metric 33 stub" 주장 **틀림** — 전 tool implemented(예외 2: canonical_translator=DB단계 partial / inapp_ad_ab_compare=mock 데이터한계). = catalog/docstring drift(metrics "phase1 only" docstring stale).
- ★ **data layer 준수 clean.** raw 직독 위반 2개뿐(`kst_timezone_normalizer`·`ad_cost_helper`)인데 둘 다 REPLACE(제거 대상). KEEP tool 위반 0.
- ★ **핵심 잔여 = dual-world 불일치**: daily_performance 4 tool이 옛 World-C(26.6M) 직독 → canonical(18.3M)과 숫자 불일치 = 할루시 유발원.
- 분류: REPLACE 6(format/channel/grade/utm/kst normalizer + ad_cost_helper) / MODIFY 10(✅5 전환완료 + ⬜5 미전환=daily 4+grade_timeseries) / KEEP ~64(전부 구현·준수).

---

## §7 핵심 코드·문서·메모리 위치
**canonical 파이프라인**:
- `backend/app/dream_agent/tools/normalization/canonical_translator.py` — REPLACE 엔진. `execute()`=순수(소스별 normalized 행+computed+blended 반환). `persist_normalized/computed/blended/persist_all`. _CHANNELS spec(6채널 keys·col_types·measures). **google 추가 지점=여기.**
- `backend/app/data_pg_util.py` — `write_relational_table`(CREATE IF NOT EXISTS+UPSERT, DROP금지)·`is_relational_table`(접미사 가드).
- `backend/scripts/build_canonical_pivot.py` — 라이브 적재(`--client clumi --period 2026-04 [--cleanup-orphans]`).
- `backend/api_v2/routes/canonical.py` — `/api/canonical/marketing-performance`(asyncpg 직접 SELECT) + `/catalog`(인벤토리). `backend/app/schemas/outputs/canonical.py`.
- 테스트 `backend/tests/canonical/`: test_canonical_relational_load(11)·test_marketing_performance(5)·test_catalog(3)·test_pipeline_connection(4). + `test_normalized_pivot_baseline.py`(교차세계 동치 + tripwire: ad_cost_helper 소비처=∅, format_normalizer dormant).
- **전환된 5 tool**: metrics/{ad_cost_total,roas_overall,cac_overall,promotion_roas}.py, comparison/channel_cac_compare.py — 전부 `CanonicalTranslator(get_registry().get("canonical_translator"))` 인스턴스화 → execute → computed 소비.

**에이전트(dream_agent)**: system_graph/builder.py · cognitive/cognitive_stage.py · planning/{planning_stage,planner}.py + catalog/team_catalog.yaml · execution/{execution_stage,executor,agent_pool,data_gate,state_guard}.py · response/{response_stage,responder}.py · states/agent_state.py · llm_manager/{client,config}.py + prompts/. 진입 api_v2/ws_agent.py·main.py.

**파일럿(가드레일)**: `backend/app/data_pilot_project/`(pipeline·transforms·compute·crosswalk·materialize·dimensions·run_pilot·verify_outputs·gate·dict_gate·coverage). canonical_translator가 여기서 포팅됨. **google 피봇 검증=여기 먼저.**

**문서(docs/_claude, gitignored)**: ROADMAP.md(닻) · plans/{normalized_tool_pivot_계획서_2026-06-15(마스터), 세부01~05, agent_C_계획서, agent_A4_tool감사_대조표, frontend_마케팅성과_수직슬라이스}.
**문서(docs, git)**: agent_specs/43_gate_ledger_v1.0.md · 20_INTERFACE_CONTRACT_v1.1.md · adr/ADR-032 · ERD/erd_octorad_normalized_computed_v0.1.dbml · reports/{계획_마스터_2트랙_순서_2026-06-12, DB제작_구현현황_2026-06-17, 완료보고서들}.

**메모리(이 세션 신설/갱신)**: `project_hallucination_root_cause_data_engineering`(★) · `project_data_layer_roadmap_sequence` · `feedback_tool_work_pilot_first_data_layer_bound` · MEMORY.md 등재.

---

## §8 라이브 DB 상태 (octormate_data, clumi schema)
- 42 테이블 = **12 canonical**(meta_ads_performance/naver_searchad/naver_advoost/kakao_bizmessage/naver_talktalk/orders **_normalized** 6 + meta/naver_searchad/naver_advoost/kakao_bizmessage/naver_talktalk **_computed** 5 + **blended_computed** 1) + 29 `*_raw` + `_workspace`.
- 적재값: blended total_marketing_cost **18,306,923**·MER **6.53**·tacos 15.25%. naver_sa Σad_cost 5,999,627. orders_normalized 1919행.
- ⚠ **C-2 미실행**: `_workspace` {cleaned:7, computed:41, raw:31} 그대로(운영 serving 캐시).
- 적재 명령: `cd backend && uv run python -m scripts.build_canonical_pivot --client clumi --period 2026-04`.

---

## §9 다음 한 걸음 + 남은 일
**→ A-5.2 google canonical 피봇 (오너 go 대기, 가 결정):**
1. `data_pilot_project`에 google 추가 → run_pilot/verify로 **26.8M·MER 4.46 확인**(파일럿 먼저).
2. `canonical_translator._CHANNELS`에 google spec 추가(data/clumi/raw/google_ads_performance.csv, 180행·cost 8,500,000) + 라이브 재적재.
3. **re-baseline**: 18.3M/6.53 → 26.8M/4.46 일괄 갱신 — test_canonical_relational_load·test_marketing_performance·test_pipeline_connection·test_normalized_pivot_baseline·build_canonical_pivot·마케팅 페이지 신뢰게이트(EXPECT_TOTAL/EXPECT_MER 상수).

**그 다음**: A-5.3 daily_performance 4 tool→canonical 일별집계 전환(파일럿) + format_normalizer 제거 + daily_performance.csv 폐기 → A-3 DB 정상화 → A-6 분리 재확인 → **A-7 TOOL 전체 구조 점검**(카테고리·구성·재구축 결정) → **C2 에이전트 e2e**(clumi 프로필 + "clumi 4월 ROAS" 라이브 1쿼리 4레이어 통과·정답·할루시 관찰).

---

## §10 정직 경고 (과신 금지)
1. **google re-baseline 미착수** — 시작하면 18.3M/6.53이 26.8M/4.46으로 코드 전반 바뀜. 마케팅 페이지·전 canonical 테스트 기대값 동시 갱신 필요. 미착수 상태에선 18.3M이 정답.
2. **daily_performance dual-world 잔존** — /trend·/channel이 아직 World-C(26.6M). 전환 전까지 그 차트는 MER과 불일치(할루시 가능).
3. **C-2 serving 캐시 미정리** — 운영 대시보드(dashboard1)는 여전히 옛 World-B `_workspace` 캐시 서빙. canonical과 별세계. API cutover 전 삭제 금지.
4. **format_normalizer 미제거** — REPLACE이나 catalog/prompt/registry 걸쳐 복잡, 미착수.
5. **C2 에이전트 e2e 미검증** — 4-layer 구동은 확인했으나 새 canonical로 실질의가 정답 내는지 라이브 검증 안 됨. clumi client 프로필도 없음(generic 모드).
6. **에이전트 stub 아님** — A-4 감사로 tool은 거의 다 구현 확인(할루시는 stub 아니라 데이터 불일치/언어층 원인).
7. **프론트 카탈로그 페이지 미커밋(③)** — 빌드되나 보류. ROADMAP §4 가지치기.
8. 회귀 baseline **997 passed**(pre-existing 5: parquet env×3·test_DC_PERM_6·test_o04).
