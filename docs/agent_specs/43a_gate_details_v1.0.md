# 43a — Gate Details (게이트별 상세 명세: 목적·컨셉·구현·필요성)

| 항목 | 내용 |
|------|------|
| 분류 | 운영 — 게이트(G01~G29) 단독 상세 명세 |
| 버전 | v1.0 |
| 최종 수정일 | 2026-06-19 |
| 진실 소스 | 코드 (file:line) |

> **이 문서 = 게이트 단독 명세.** 각 게이트의 **목적·컨셉·구현방식·필요성**을 코드(file:line) 기준으로 풀어쓴다. 진실 소스는 코드 — 코드와 드리프트 시 코드 우선.
> 출처: 게이트 구조점검 워크플로 `w6pjclwu4`(2026-06-19, 8 에이전트 현 코드 file:line 실측).

---

## §0 읽는 법 — 검사축 4종 + 2축 할루시

게이트는 *무엇을 검사하나*로 갈린다:
- **🅛 언어** = LLM이 만든 layer 간 전달물(쿼리·계획·params·state) 정합 (제어 평면)
- **접점** = 언어의 약속(consumes·params)을 데이터 현실(존재·count·형식)과 대조 (execution 입구)
- **🅓 데이터** = 실데이터·저장 형태 자체 (저장 평면)
- **표면** = 사람에게 나가는 표시·입력의 정직

★ **게이트는 2축 할루시 중 ②축(LLM/에이전트 언어 취약성)을 막는다.** ①축(데이터 정확성)은 canonical이 고쳤고 게이트와 직교. **구조 건강(canonical·② 의미배선 완료)으로 무용화된 게이트 = 0/28**(2026-06-19 감사). 게이트는 데이터가 아니라 "LLM이 스코프를 빠뜨리거나 plan을 잘못 짜거나 빈출력을 성공으로 둔갑"하는 사건을 막기 때문.

표기: **⟨미배선⟩** = 신호 생산하나 런타임 소비처 0 · **🔗+GXX** = 등기통합 쌍(같은 메커니즘 입출구).

---

## §1 Cognitive — 신호 생산

### G01 · QueryMeta 모호 신호 ⟨미배선⟩  [표면]
- **목적**: cognitive가 모호·미지원 질문을 인식해 되묻기 신호(is_ambiguous·clarification_question)를 출력에 남김
- **컨셉**: 의도가 under-specified(대상·작업·기간 불명)면 그 사실을 명시 신호로 emit
- **구현**: `schemas/structured_query.py:149-154` Ambiguity 모델 + `cognitive.yaml` emit 지시 + `cognitive_stage.py:185` 파싱
- **필요성 → retire→planned**: 신호는 생산되나 **런타임 소비처 0**(`cognitive_stage.py:210` 무조건 planning행, planner/responder/hitl 누구도 안 읽음). 유일 reader=측정 하네스. 배선 계획 = HITL clarification (ADR-015). **②완료와 무관**(모호성 인식=별개 축)

## §2 Planning — plan repair (planner.py)

### G02 · subject-coherence 필터  [🅛언어]
- **목적**: 텍스트 의도 없는 숫자 쿼리서 주제-결속(텍스트) todo 제거 → "텍스트 항목 24건으로 숫자 지표 설명" 오답 차단 (F2)
- **컨셉**: 카탈로그가 선언한 주제-결속 산출물(`subject_bound_artifacts`)을 도구의 produces/consumes/params_required 와 대조해 식별(데이터 계약 기반, 이름 휴리스틱 아님) → 메뉴제외 + post-filter 이중 제거
- **구현**: `planner.py:159-184` apply_subject_coherence_filter (메뉴필터 598-617, _has_text_intent 634-646, 식별 _tool_is_subject_bound 63-77)
- **필요성 keep**: plan *경로 선택* 게이트 — LLM이 insight 입력욕심에 텍스트파이프 통째 빨아들이는 취약성 차단. ②는 *뽑힌* 텍스트의 의미를 고칠 뿐 *선택됨*을 못 막음

### G03 · complete_dataflow_chain  [🅛언어]
- **목적**: LLM이 전처리 체인서 필수 tool(예: 정규화/전처리 도구) 빠뜨려 consumer 입력=0(silent-0 ~40%) 차단
- **컨셉**: 카탈로그 produces/consumes로 "consumer가 먹는 artifact 생산자가 plan에 있나" 검사 → 없으면 삽입·배선 (하드코딩 체인 아님, 멱등 fixpoint)
- **구현**: `planner.py:321-385` (호출 779), _build_producer_index 기반 최대 100회 루프
- **필요성 keep**: consumes 생산자 누락이라는 plan 구조 결손 — 데이터값/의미와 무관. ⚠카탈로그 drift 시 못 잡는 약점은 잔존

### G04 · ensure_interpretation_fed  [🅛언어]
- **목적**: 해석 tool(insight/diagnoser/forecaster)이 계산 metric 없이 raw만 받아 빈입력 EMPTY 되는 것을 대표 metric 삽입으로 차단 (해석 tool은 consumes 미선언이라 G03가 못 챙김)
- **컨셉**: _INTERPRETATION_TOOLS 시 computed 산출자(generic task_type: metric_calculation/comparison/analysis) 있나 검사 → 없으면 카탈로그 `domain_headline_metric`[domain] 삽입 (미등록 도메인=무발동)
- **구현**: `planner.py:399-462` (호출 783), _resolved_month 있을 때만 삽입(없으면 degrade)
- **필요성 keep (★②완료 검증 대상)**: data_comprehension root로 표기됐으나 *실가드*는 "metric이 plan에 아예 없어 입력 비는" 사건. **②(중앙주입)는 *주어진* metric의 단위 오독을 고침 → G04와 보완**(의미배선=해석 / G04=존재). §0.1 "의미주입은 0건입력 제거 아님" 그대로 — 대체 안 됨

### G05 · enforce_breakdown_dimension  [🅛언어]
- **목적**: breakdown+dimensions인데 차원분해 tool 없어 전체 scalar로 ~60% 붕괴하는 것을 차원 tool 삽입으로 차단
- **컨셉**: operation=breakdown & dimensions 시 produces='rows' + name.startswith(dimension)로 식별 (예: dimension=`<dim>` → 도구명 `<dim>_aggregate` 매칭; dimension은 쿼리가 요청한 토큰, 도메인 하드코딩 아님)
- **구현**: `planner.py:462-508` (호출 775), 매칭 없으면 graceful 무발동
- **필요성 keep**: breakdown인데 LLM이 차원 tool 안 고르는 plan 결손 — ②/canonical과 직교

### G06 · bind_temporal_params + _resolved_month  [🅛언어]
- **목적**: LLM이 놓친 period를 쿼리 절대월로 결정론 바인딩 + 01-12 검증("2026-13" 환각·optional tool 무언 전체기간 확장=period:'all' 버그 차단)
- **컨셉**: _resolved_month로 절대월+zero-pad+검증 → setdefault 바인딩(LLM값 안 덮음), MoM은 period_a/b 결정론 도출
- **구현**: `planner.py:291-318` (_resolved_month 270-288, _prev_month 259-267, 호출 788)
- **필요성 keep(★강)**: `wgl8y5yk5` 진단대로 period:'all'은 *param-flow 메커니즘 버그*(데이터 멀쩡)—이 게이트가 정공법 대체(R-1). silent-0 핵심막. 날짜 산술이라 ②/canonical과 완전 직교

### G07 · detect_plan_gaps  [표면]
- **목적**: 각 todo 필수 param이 채워지나 실행 전 자가평가 → 미바인딩이면 gap(정직 degrade 씨앗)
- **컨셉**: produced_by 인덱스로 upstream 수집, 못 채우면 gap append (SCOPE_PARAMS는 상류충족 불인정), plan 불변
- **구현**: `planner.py:228-256` (SCOPE_PARAMS 연동 253, 호출 796) — 현재 비차단·logger.warning만
- **필요성 keep**: silent-0 역추적·정직 degrade 토대. ②/canonical과 무관(param 바인딩 여부만)

### G08 · validate_dag ⟨미배선⟩  [runtime]
- **목적**: depends_on 미지참조·dag 미지 todo·cycle 탐지(executor 무한루프/KeyError 전 포착)
- **컨셉**: todo_ids 집합으로 unknown 의존 수집 + detect_cycle(DFS 3색)
- **구현**: `planner.py:511-524` (detect_cycle 124-156) — **808행에서 issues 받지만 차단/halt에 안 씀(반환만)**
- **필요성 → retire→planned**: 게이트로서 *작동 안 함*(로그only, 차단 배선=슬라이스2-③ 예정). G02~G07 삽입 todo가 유효 id라 실무 cycle 위험 낮음. ②/canonical과 직교

## §3 Execution 입구 — Guardrail (검문소)

### G09 · data_gate check_consume_sufficiency  [접점]
- **목적**: consumes artifact가 실행 전 존재+non-empty인지 검사 → silent-0 거짓 COMPLETED를 SKIPPED+사유로 전환
- **컨셉**: '파이프 연결'이 아닌 '물 흐름(받은 데이터 충분성)' 보장. `_dataref` 스텁은 **count**로 판정(0건 맹점 봉합)
- **구현**: `execution/data_gate.py:42-77` (dataref count 분기 63-68)
- **필요성 keep**: canonical은 '값 정확성'이지 '0건 수집'을 안 막음. 0건 수집이 truthy 스텁으로 통과해 silent-0 재발하는 것을 막는 유일 장치

### G10 · _param_boundary_issue  [접점]
- **목적**: 실행 직전 param 경계 강제 — 필수 누락(missing_param)·스코프 형식위반(invalid_param) coerce 없이 정직 SKIPPED
- **컨셉**: 헌법 D2·D3 — 'all'/'3months'가 흘러 startswith 0건 거짓완료 되던 경로 차단
- **구현**: `executor.py:133-165` (params_required 149-151 + SCOPE_PARAMS YYYY-MM 정규식 152-161 + validate_params 162-164, _is_valid_period 123-130)
- **필요성 keep**: period:'all'은 param-flow 버그라 canonical로 안 고쳐짐. LLM이 채운 스코프 형식오류의 유일 backstop

### G11 · _inject_prev_outputs 스코프 차단 🔗+G12  [접점]
- **목적**: 상류 COMPLETED 산출을 미바인딩 param에 체이닝하되 시간스코프·내부키 오염 차단
- **컨셉**: 헌법 R2 — 시간 스코프는 쿼리에서만; 상류 'all'/타월 라벨이 period로 흘러 silent-0 만들던 경로 차단
- **구현**: `executor.py:280-300` — COMPLETED·dict만 순회, `_`키/SCOPE_PARAMS면 setdefault 스킵
- **필요성 merge(+G12, 코드 유지)**: G12와 동일 오염모델(사유dict·스코프라벨의 LLM payload 유입). ⚠retire 금지(오염원 5곳 live라 silent-0 재발)

### G12 · ctx.previous_results COMPLETED 필터 🔗(G11쌍)  [접점]
- **목적**: SKIP/FAILED 사유dict가 데이터인 척 LLM payload에 유입 방지 (R-8)
- **구현**: `executor.py:188-198` — ctx 합성 시 status==COMPLETED만 {tid: data}
- **필요성 merge(+G11)**: G11과 같은 기준(주석이 '_inject와 같은 기준' 명시). 코드 별위치라 물리병합 불가, 등기만 통합. **②전제**: 깨끗한 inputs를 glossary 빌더에 공급

### G13 · LLMTool 빈입력 가드 🔗+G14  [접점]
- **목적**: 입력 전부 0건이면 LLM 호출 전 정직 degrade — 빈 데이터로 보고서 환각하는 silent-0 축2 차단
- **컨셉**: Template Method — execute가 collect_inputs→[전부빔 검사]→run_llm 소유, subclass 못 건너뜀
- **구현**: `tools/llm_tool.py:54-70` 가드 (build_glossary 호출은 74=가드 통과 후)
- **필요성 keep (★②완료 검증)**: **중앙주입(2026-06-19)이 같은 execute()를 건드렸으나 빈입력 가드(58-70)가 glossary(74) *위*에 보존됨을 확인**. 빈입력엔 glossary가 아예 안 만들어짐(조기 return) → 의미주입 무력, 가드만이 방어. §0.1 "의미주입은 0건입력 제거 아님" 그대로

### G14 · silent-0 전파 변환 🔗(G13쌍)  [표면]
- **목적**: G13이 낸 {reason:data_insufficient}가 COMPLETED로 조용히 흐르지 않게 SKIPPED 변환
- **구현**: `executor.py:253-259` — reason=='data_insufficient'면 SKIPPED 아니면 COMPLETED
- **필요성 merge(+G13)**: G13(신호 생성)+G14(status 정직표면화) = silent-0 축2 입출구쌍. G14 없으면 G13 정직신호가 COMPLETED로 삼켜짐

## §4 Execution 출구 — 제어 평면 경계

### G15 · _json_safe  [runtime]
- **목적**: TodoResult.data의 비직렬값(DataFrame·set) 드롭 — checkpoint 직렬화 크래시(F1, 2026-06-02) 방지
- **구현**: `executor.py:97-113` 재귀 — JSON-safe 타입만 통과, else→None
- **필요성 keep**: collector가 raw DataFrame 반환하는 *타입* 문제 — ②/canonical과 무관 순수 런타임. (runner.json_safe와 3중 convention)

### G16 · state_guard slim_execution_result 🔗+G17  [runtime]
- **목적**: state/checkpoint 진입값 >256KB를 참조 스텁 치환 — 104MB/턴 누수(checkpoint 155MB·WS 312MB) 봉인
- **컨셉**: 두 평면(데이터 창고 vs 제어 평면) 경계를 결정론 게이트로 강제 (싱크 측)
- **구현**: `state_guard.py:88-129` slim + approx_json_size(47-75) + _stub(78-85), 원본 불변
- **필요성 merge(+G17, 코드 양쪽 유지)**: G17=collector 비탑재(소스)/G16=새어든 대용량 치환(싱크) = 상보. 둘 중 하나만 두면 비-collector tool 또는 dataref 우회 구멍

### G17 · RawCollectorBase _dataref 🔗(G16쌍)  [runtime]
- **목적**: collector가 raw 데이터셋(예: 38,319행=104MB)을 결과 비탑재, 참조(source_id·count)만 반환 → state 암묵저장 원천차단
- **구현**: `tools/collection/_base.py:116-142` — {_dataref:True, source_id, count, ...} 반환. data_gate.py:59-69가 count==0을 0건 판정(silent-0 동시 차단)
- **필요성 merge(+G16)**: 누수 봉인 구조정책 — ②와 무관. _dataref+count가 G09 0건 판정 입력이기도 해 silent-0 방어와 결합(단순삭제 불가)

### G28 · 수집 save 마커 생존 가드  [🅓데이터]
- **목적**: ≥10,000행 record나 `__streamed__` 마커 키를 blob save로 덮어써 행-테이블이 침묵 소멸하는 실사고(2026-06-11) 차단
- **컨셉**: 데이터 적재 경계의 correctness 라우팅 — list 길이/마커 시 save→save_stream 우회
- **구현**: `workspace/postgres.py:42-62` (STREAM_ROUTE_THRESHOLD=10_000, 마커=data_pg_util.py:29)
- **필요성 keep**: 데이터가 *침묵 소멸*해 행 자체가 사라지는 적재 무결성. **②가 완성돼도 데이터가 사라지면 의미 부여할 대상조차 없음** → 절대 무용화 안 됨

### G29 · execution not_executed 등기  [표면] (2026-06-19 신규)
- **목적**: plan엔 있으나 실행 안 된 todo(DAG 미해결 의존·halt 잔여)를 SKIPPED(not_executed)로 명시 등기 — '무기록 증발' 가시화 (M0 실측: 계획11 vs 실행8, 누락3개가 "완료" 둔갑)
- **구현**: `execution/execution_stage.py:346-364` (_build_execution_result 내). 신호 not_executed → responder `_render_skipped_note`·T4 귀속판정기
- **필요성 keep(신규 등재)**: 대장 미등재였던 진짜 게이트. 헌법 §7 채용 3문항(측정근거 M0·층 execution출구·소비자 responder) 충족

## §5 Response — 정직 표면

### G18 · build_degrade_payload  [표면]
- **목적**: 미구현 op(diagnose/forecast/attribute)가 실행 0건 → LLM에 빈 summary 안 넘기고 "준비 중" 정직
- **컨셉**: 기능 부재(데이터 부재 아님)를 LLM이 '데이터 없음'으로 지어내는 할루시 차단 — 진짜 이유(미구현)를 결정론 문구로
- **구현**: `responder.py:47-71` — op∈DEGRADE_OPS & todos 빔이면 _DEGRADE_MESSAGES
- **필요성 keep**: 기능 미구현은 데이터/의미 완성돼도 빈 todos를 만듦. 없으면 "분석을 완료했습니다" 둔갑

### G19 · build_missing_period_payload  [🅛언어]
- **목적**: period 미바인딩으로 막히면 숫자 가정 없이 "기간을 알려주세요" 되묻기 (헌법 D3)
- **컨셉**: 무스코프 수치 단정(구버전 스코프 0값 silent-0) 금지 — period SKIP 시 기간질의 선두, 완료된 비스코프 산출은 뒤에 공존
- **구현**: `responder.py:118-184` — SKIPPED & reason∈{missing/invalid_param} & param∈SCOPE_PARAMS면 ask, FAILED엔 양보
- **필요성 keep (★유일 미래 무용 후보)**: period:'all'은 param-flow 버그라 ②가 안 고침. **진짜 무용화는 *planning param-flow 자체* 수리 시점**(이번 ② 밖, 별개 작업)

### G20 · build_insufficient_data_payload  [표면]
- **목적**: 데이터 0건/부재로 분석 통째 막힘(collector 외 COMPLETED 0) → 정직 degrade
- **구현**: `responder.py:74-115` — SKIPPED & reason=='data_insufficient' & collector외 COMPLETED 0이면 고정 텍스트, 부분성공이면 None
- **필요성 keep**: §0.1 "의미주입은 0건입력 제거 아님" — 없는 데이터 물으면 여전히 data_insufficient SKIP. **데이터 인프라가 정합돼도 '없는 데이터'는 못 만듦** → 안전망 잔존

### G21 · display 거짓-완료 가드 (build_display_payload)  [표면]
- **목적**: FAILED거나 collector만 완료·분석 0인데 "완료" 둔갑 금지 (H4/I1)
- **구현**: `responder.py:389-480` — FAILED→ERROR(402-403), all-SKIPPED-no-COMPLETED→"결과 못 만듦"(458-469), else만 "완료"(471)
- **필요성 keep (catch-all)**: G18~G20이 못 잡은 모든 'FAILED/0산출인데 완료' 케이스 최종 방어선. runtime 사유라 ②와 무관

## §6 시스템·관측 (턴 수명주기)

### G22 · layer_inspector inspect_layer_output  [표면]
- **목적**: 각 layer 출력 빈출력 5종 탐지(EMPTY_QUERY·EMPTY_PLAN·ALL_FAILED·PARTIAL·RESPONSE_EMPTY) → fatal이면 abort
- **구현**: `system_graph/layer_inspector.py:37-139` — 'key in data'만 보고 값 의미 안 읽음. fatal→ws_agent abort
- **필요성 keep**: '빈 출력이 성공으로 흘러나감' 차단. ②는 빈출력 제거 아님 → 안전망 재확인

### G23 · ws error→END 정직화  [표면]
- **목적**: stage가 error로 END인데 complete(success)+빈화면으로 나가는 것 차단
- **구현**: `api/ws_agent.py:474-487` — final_state error & not response면 LAYER_ERROR + aborted
- **필요성 keep**: LLM 실패·예외·reject로 error END하는 제어흐름은 ②로 안 사라짐. G22가 못 잡는 구간(chunk 미emit·error만 state) 보완

### G24 · HITL 활성 turn 가드 + resume timeout  [runtime]
- **목적**: stale/완료 turn 명령 거부(turn_not_active) + 무응답 30분→aborted(Queue/슬롯 누수 방지)
- **구현**: `ws_hitl.py`(6 핸들러 is_turn_active) + `hitl_manager/manager.py:411-431`(wait_for asyncio timeout) + ws_agent.py:418-444 drain. HITL_RESUME_TIMEOUT_SEC=1800
- **필요성 keep**: 순수 동시성·수명주기 안전. 무응답·재시작·stale 명령은 의미배선과 직교

## §7 Frontend — 표시·입력 가드

### G25 · zod WSMessageSchema  [runtime]
- **목적**: BE emit WS 메시지를 신뢰 전 형식·discriminator(13종) 검증 → 깨진/구버전 페이로드 드롭
- **구현**: `api/schemas.ts:370` discriminatedUnion + `ws.ts:36` safeParse(실패=드롭)
- **필요성 keep**: BE Pydantic↔FE 직렬화 contract drift 방어. 데이터값/의미와 교차점 0

### G26 · cycleGuard DFS  [runtime]
- **목적**: 시각편집 새 엣지가 DAG cycle 만들지 드롭 전 BFS 사전차단
- **구현**: `cycleGuard.ts:32` wouldAddEdgeCreateCycle + `WorkflowPage.tsx:174` onEdgeConnect(true=드롭)
- **필요성 keep**: 그래프 위상 검증 — BE 왕복 전 UX 가드라 BE 게이트로 대체 불가

### G27 · hitl_ack accepted:false 가시화  [표면]
- **목적**: 승인/거부 거절(accepted:false) 시 침묵 않고 pending 유지+toast — 간헐 멈춤(~1/20) 수술
- **구현**: `features/hitl/store.ts:57-74` — !accepted & approve/reject→toast.error, ack.issues→toast.warning
- **필요성 keep**: turn_not_active/INVALID_DAG 등 서버 거절은 canonical/②가 제거 못 함

---

## §8 한눈에 — guards_against 분포 (왜 0/28 무용)
| guards_against | 게이트 | ②/canonical로 무용? |
|---|---|---|
| **LLM planning 메커니즘** | G02·G03·G04·G05·G06·G07·G09·G10·G11·G12 | ✗ LLM이 스코프 빠뜨리는 사건은 데이터와 무관 |
| **표면 정직** | G01·G07·G14·G18·G19·G20·G21·G22·G23·G27·G29 | ✗ 0건/FAILED는 데이터 인프라와 독립 |
| **runtime 안전** | G08·G15·G16·G17·G24·G25·G26 | ✗ 타입·메모리·DAG·동시성은 의미와 직교 |
| **🅓데이터** | G28 | ✗ 데이터 사라지면 의미 부여 대상조차 없음 |
| **data_comprehension** | G04·G13 | ✗ ②가 *보완*(해석/존재), 대체 아님 |

**결론**: 게이트는 데이터가 아니라 *LLM이 틀린 언어를 만드는 사건*을 막는다 → 구조 건강해도 0개 무용. 정리된 retire 2(G01·G08 미배선)+merge 3쌍은 *배선 미완성·등기 위생*이지 구조 무용화가 아니다.

## 변경 이력
| 날짜 | 내용 |
|---|---|
| 2026-06-19 | v1.0 신설 — 43 대장의 산문 짝. G01~G29 목적·컨셉·구현(file:line)·필요성·미배선여부, 워크플로 `w6pjclwu4` 실측 기반. §8 guards_against 분포. |
