# 19 — Architecture Constitution (아키텍처 헌법: 불변식 · 경계 규약 · 신호 라우팅)

| 항목 | 내용 |
|------|------|
| 담당자 | 도윤 |
| 분류 | 개발 - 아키텍처 (헌법 — 모든 변경의 자) |
| 진행상태 | **Active** (오너 비준 2026-06-11) |
| 버전 | **v1.0** |
| 최종 수정일 | 2026-06-11 |
| 관련 명세 | [16 Layer Dependency](16_layer_dependency_architecture_v1.0.md)(물리 의존) · [18 Engineering Disciplines](18_engineering_disciplines_v1.0.md)(4축) · [20 Interface Contract](20_INTERFACE_CONTRACT_v1.1.md)(레이어 계약) · [22 Error Codes](22_error_codes_v1.1.md) · **[43 Gate Ledger](43_gate_ledger_v1.0.md)(게이트 전수 등기부 — §5의 게이트 관점 짝, 그림은 생성물)** |
| 배경 분석 | `docs/_claude/4layer_system/` — [분석종합+조직모델](../_claude/4layer_system/아키텍처_분석종합_조직모델_260611.md) · [Fable 구조검토](../_claude/4layer_system/fable_structural_review_260611.md) · [2차 재분석](../_claude/4layer_system/재분석_2차_fresh_eyes_결과_260611.md) |

> **지위**: 이 문서는 *설계 도면이 아니라 헌법*이다 — 무엇을 지을지가 아니라, **짓는 모든 것이 따라야 할 불변 규칙**. 변경 작업이 들어올 때마다 "이 변경은 헌법의 어느 조항에 속하는가"를 묻는 것이 오너의 통제 수단이다. 도면(구현 계획)은 슬라이스마다 그때 그린다.
> 탄생 배경: period="all" silent-zero 사태(2026-06-11) → 구조 진단("검증 신호 무소비 + 무계약 사이드채널이 정직한 실패를 가로챔") → 본 헌법으로 봉인.

---

## §1 불변식 5 (자 — 모든 판정의 기준)

| # | 불변식 | 뜻 |
|---|---|---|
| **I1 정직** | 틀린/불확실한 것을 성공(COMPLETED·성공 문구·그럴듯한 숫자)으로 표시하지 않는다. **1순위.** | 못 하면 "못 한다/~가 필요하다"고 말한다 |
| **I2 추적** | 모든 표시 숫자는 "어느 tool이 어떤 입력(기간·출처)으로 냈나"에 답할 수 있다 | 출처 없는 숫자 금지 |
| **I3 경계 명시** | 데이터는 선언된 채널로만 todo/레이어 경계를 넘는다 | 이름-일치 우연 전달 금지 |
| **I4 단일 어휘** | status·period 같은 경계 어휘는 한 곳에 정의하고 import로만 쓴다 | 문자열 손타이핑 금지 |
| **I5 감지=정책 입력** | 모든 gap/위반 신호는 결정 지점(차단·질문·degrade·표시)에 도달한다 | **로그는 종착지가 아니다.** I5는 I1의 전제 조건 |

---

## §2 5층 용어 (확정 — 오용 금지)

| 층 | 명칭 | 역할 | 소속 코드 |
|---|---|---|---|
| ① 계약 | **Contract** | 값 정의·형식 (예: period=YYYY-MM). §3-D1에 따라 **코드 1곳** | `schemas/` 상수·Pydantic·enum |
| ② 강제 | **Guardrail** (경계검사) | 경계에서 계약 위반 → 정직 SKIPPED/에러. **경로 불변** | data_gate · LLMTool 가드 · validate_params · state_guard |
| ③ 계획 보수 | **Plan repair** | LLM plan의 결손을 결정론으로 수선 (todo 삽입·배선·바인딩) | planner의 게이트군 (dataflow_chain·interpretation_fed·breakdown·bind_temporal) |
| ④ 정책 | **Policy** | 위반·gap 신호를 받아 결정: 차단/기본값/질문/degrade | workflow_managers (실동작 6) |
| ⑤ 하네스 | **Harness** (표준 의미: 외부 구동·측정) | golden query 재현·회귀·진단 사다리 | `scripts/agent_lang_diagnostics/` + pytest + 기준질문 G1~G6 |

**용어 금지 조항**: "하네스 = 8gate/런타임 강제 엔진" 명명 금지 (doc 18의 구 framing — 이 이름 인플레이션이 값-수준 검증 부재를 가렸음). planner 게이트들의 올바른 직함은 **계획 보수(plan repair)**다. 조직 비유: 실무 4부서(4-Layer) 불변 + 사규집(①) + 검문소(②, Execution 소속) + 운영위(④) + 감사실(⑤).

---

## §3 비준된 결정 3 (오너, 2026-06-11)

| # | 결정 | 내용 | 근거 |
|---|---|---|---|
| **D1** | 계약 진실소스 = **코드 1곳** | 값 정의·형식은 `schemas/`의 상수·Pydantic·enum이 진실. 카탈로그 YAML은 파생·표시용 — **YAML에 값 제약을 새로 선언하지 않는다** | catalog≠code drift 반복 실측 (9-tool period drift·report_text·죽은 YAML 메타 7계열). YAML 제약 = drift 제조기 |
| **D2** | 위반 처리 = **거부** | 경계 검사에서 계약 위반 값 발견 시 보정(coerce) 금지 — 정직 SKIPPED/에러 + 사유 | 보정은 가정의 침묵 주입 (I1 위반 소지). 71,470원 류 그럴듯한 오답의 원천 차단 |
| **D3** | period 없음 UX = **정직 degrade 먼저** | 기간 없는 쿼리는 "기간을 알려주세요 (예: 2026년 4월)" 응답. 자동 기본월 금지(가정을 답으로 제시 = I1 위반 — 쓰려면 H5 라벨 의무). HITL 되묻기는 D5 자동승인 제거 후 자연 승급 **(D5 제거됨 2026-06-12 멈춤 수술 — 승급 길 열림)** | UX 결정과 부정직-제거의 분리 — 슬라이스 1이 D5와 무관하게 진행 가능 |

---

## §4 경계 규약 R1~R6 (도구↔도구 / 레이어↔레이어)

| # | 규약 | 현재 위반 → 봉인 슬라이스 |
|---|---|---|
| **R1** | 경계 어휘는 정의 1곳 + import — status는 `TodoStatus` enum, period 형식·`SCOPE_PARAMS`는 schemas 상수. 경계 코드에서 문자열 리터럴 비교 금지 | "success" 손타이핑 (✅ 슬라이스 0 수리) · period 형식 정의 0곳 (슬라이스 1) |
| **R2** | **planning이 결정론 바인딩하는 param(SCOPE_PARAMS: period·period_a·period_b, 추후 channel·dimension)은 데이터 사이드채널(`_inject_prev_outputs`)로 유입 금지** | period="all" 누수 (슬라이스 1-②) |
| **R3** | 도구 산출 데이터에 저장키용 placeholder 금지 — 데이터 ≠ 저장 메타. 저장키는 `period_safe` 등 별도 | 오염원 5곳 `period or "all"` + 카탈로그 produces의 period 선언 (슬라이스 1-①) |
| **R4** | 같은 도구는 어느 진입 경로(agent/pipeline/dashboard/standalone)든 같은 검사를 받는다 | validate_params가 pipeline만 (슬라이스 1-④) · standalone의 백엔드 swap 부재 (추후) |
| **R5** | 전달 채널의 필터는 한 계약 — params 주입(COMPLETED만)과 ctx.previous_results(무필터)의 비대칭 해소. 장기: consumes 선언 기반 명시 전달 | 채널 3개 무규약 병존 (장기 — 슬라이스 N) |
| **R6** | **신호는 소비자 지정 없이 만들 수 없다** — 새 gap/issue/메타 필드를 추가하려면 §5 라우팅 표에 소비자를 먼저 등록 | gaps·issues 무소비 (슬라이스 1-⑤·2) |

---

## §5 ★ 신호 라우팅 표 (I5의 집행 — 신호마다 지정 소비자)

> 규칙: 이 표에 없는 신호는 만들 수 없다(R6). "삭제" 판정 신호는 정리 Sprint에서 선언째 제거.

| 신호 (생산지) | 지정 소비자 | 상태 |
|---|---|---|
| `hitl_ack.accepted` | frontend pending 해제·콘솔 표기 | ✅ 수리됨 (슬라이스 0-①) |
| `ExecutionResult.halted_at`/`halt_reason` | responder 실패 고지 + `ResponsePayload.error` | ✅ 배선됨 (0-③) |
| stage `error`(→END) | error 이벤트 + complete(aborted, LAYER_ERROR) | ✅ 배선됨 (0-③) |
| guard PARTIAL warning | `complete.data.guard_warnings` → frontend 표시 | 절반 (발생은 ✅ 0-② / 표시는 슬라이스 2-⑤) |
| `plan.gaps` (detect_plan_gaps) | execution 경계 SKIP 사유 + responder "기간을 알려주세요" | ✅ 배선됨 (슬라이스 1-⑤, e101a48). 장기: plan 카드 |
| period 형식 위반 | executor 경계 검사 → SKIPPED(invalid_param) — 공백은 정규화(검증값=실행값) | ✅ 배선됨 (1-③·리뷰 R-7) |
| param 경계 SKIP 사유 (`missing_param`/`invalid_param`) | 스코프면 responder "기간을 알려주세요" / 비스코프면 거짓-완료 가드 | ✅ 배선됨 (1-③④·R-5·R-6) |
| `_state_guard` 슬림 스텁 (state_guard L3) | responder(dict 스킵)·chart_generator(비차트화) + slim warning 로그(재발 관측) | ✅ (33ac21a) |
| `_dataref` 참조 스텁 (collector L4) | data_gate count 판정(0건 차단)·chart_generator(비차트화)·downstream 은 데이터 평면 직조회 | ✅ (85ef5de + 30a5b26) |
| `hitl_request` (plan_review) | **PlanReviewModal — 사람이 승인/거부** (D5 자동승인 폐기) + 순단 시 frontend 가 resume_query 로 재요청 | ✅ (멈춤 수술 cb1707f, 2026-06-12) |
| `validate_dag` issues (cycle) | **차단**(block) — plan이 execution에 못 감 | 슬라이스 2-③ |
| `QueryMeta.ambiguity`/`clarification_question`/`confidence`/`missing` | 모호 시 되묻기 응답 (PLANNING_EMPTY_PLAN fatal 대체) | 슬라이스 2-① |
| `TodoResult.is_mock` + recommender fixture | 응답에 "예시(mock) 기반" 라벨 | 슬라이스 2-② |
| SKIPPED 사유 (부분 skip) | 응답에 "건너뜀 N건 (사유)" 표기 | 슬라이스 2 |
| `meta.cleaned` (의도 재진술) | 채팅에 "이렇게 이해했어요" 표시 | 슬라이스 2+ |
| `ResponsePayload.error`/`next_actions`/`summary`/`meta.degraded` | frontend extractResponse 소비 + errorMessages 배선 | 슬라이스 2-⑤ |
| 캐시 적중 산출 | "계산 시점" 신선도 표기 (H3) | 슬라이스 2~3 |
| `plan_notes` | plan 카드 (D5 제거 후) | 보류 |
| detect_recovery 메뉴 (G6) | HITL 복구 선택 루프 | 보류 (G6 후반 배선 시) |
| `_storage`·`_meta.formula`·ToolSpec(dependencies/storage/timeout/retries)·프롬프트 YAML `llm_config`·`ttl_seconds`·`TriggerDef`·`task_agent_hints` | **삭제 또는 구현 판정** — 기본 삭제(죽은 선언), ttl_seconds만 구현 가치 검토 | 정리 전환 Sprint |
| `paused_at_phase`·`hitl_ack.restart_from/preserved` | 삭제 후보 (소비 계획 없음) | 정리 전환 Sprint |

---

## §6 정직 표면 규칙 H1~H5 (사용자에게 보이는 모든 것)

| # | 규칙 |
|---|---|
| **H1** | '완료' 집계 어휘 단일 — progress/responder meta/frontend가 같은 집합을 센다 (현재 3중 분열: FAILED·SKIPPED 포함 여부 제각각 — 슬라이스 2-④) |
| **H2** | mock/stub/fixture 산출은 사용자 표면에 표기 의무 — 출처 없는 자신만만한 조언 금지 |
| **H3** | 캐시 서빙은 신선도(계산 시점) 표기 — 영구 stale을 최신인 척 금지 |
| **H4** | 실패·부분실패·모름은 그 사실을 문구로 **먼저** — 성공 문구 fallback 금지 (✅ 0-③ 배선) |
| **H5** | 가정으로 채운 값(기본월 등)은 응답에 가정을 명시 — 라벨 없는 가정 금지 (D3의 짝) |

---

## §7 신규 장치 채용 기준 (상설 — 게이트/가드/매니저/신호 공통)

신규 결정론 장치(게이트·가드·신호·매니저 배선) 제안은 3문항에 전부 답해야 채용:

1. **측정 근거** — multi-run 베이스라인이 이 결손을 systematic으로 보여주는가? (1회 스냅샷·추정 불가)
2. **소속 층** — §2의 ①~⑤ 중 어디 소속인가? (걸치면 분할)
3. **신호 소비자** — 네가 내는 신호는 §5 표의 누가 소비하는가? (로그는 답이 아님)

> 기존 9 게이트는 이 기준의 소급 면접을 통과·재배치 완료 (전원 현역 — [분석종합 §5 면접 결과지](../_claude/4layer_system/아키텍처_분석종합_조직모델_260611.md) 참조).

---

## §8 슬라이스 매핑 (헌법 조항 ↔ 구현 단위)

| 슬라이스 | 내용 | 집행 조항 | 상태 |
|---|---|---|---|
| **0** | hitl_ack 수리 / guard 어휘 / 거짓 성공 2경로 | I1·I4·R1·H4 | ✅ 완료 (b75df88·33b48c1·9323414) |
| **정리 전환 Sprint** | 죽은 코드 ①부류 삭제(짝 단위) + planned 마커 + §5 "삭제 판정" 선언 제거 | I4·R6 | ✅ 완료 (57ee019~b169622 + stub 처분 1~4차, 카탈로그 108→92·stub 0) |
| **1 — period 정직** | ①오염원 5곳+카탈로그 produces 정리 ②SCOPE_PARAMS 주입 금지 ③경계 YYYY-MM 검사(+_resolved_month 보강) ④executor validate_params ⑤gaps→정직 문구 | R1·R2·R3·R4·R6 / D2·D3 | ✅ 완료 (e101a48 + 적대리뷰 8605f0d — G2 달성, drift 정합 9 포함) |
| **2 후보** | ①모호 되묻기 ②mock 표기 ③cycle 차단·'완료' 어휘 통일 ④혼합 집계 정리 ⑤frontend 신호 소비(error/guard_warnings/errorMessages) + 운영 2건(todo_add drift·입력 잠금) | I1·I5·H1·H2 | 후보 |
| **N (장기)** | R5 — consumes 선언 기반 명시 전달로 채널 통일 | I3·R5 | 설계 후 |

---

## §9 검증 = 오너 기준질문 (감사실 ⑤ — 코드 없이 채팅으로)

| # | 질문 | 합격 | 빨간불 | 검증 조항 |
|---|---|---|---|---|
| G1 | "2026년 4월 채널별 CAC 비교해줘" | 가중평균 30,512원·카카오 2,270원 | 다른 숫자·0원 | I2 |
| **G2** | "채널별 성과 비교하고 부진 채널 진단해서 개선안 PDF로" (월 없이) | 숫자 단정 없이 "기간을 알려주세요" | CAC 0원·광고비 71,470원·빈 PDF | I1·D3 — **슬라이스 1의 DoD** |
| G3 | "2026년 5월 매출 알려줘" | "5월 데이터가 없습니다" | 0원을 결과로 표시 | I1 |
| G4 | 일부러 깨지는 복합 요청 | "완료 N · 실패 M" 명시 + 부분 결과 | 턴 전체 중단·성공 문구 단독 | H4 — ✅ 슬라이스 0 검증용 |
| G5 | "예산 어떻게 배분할까?" | "예시(mock) 기반" 표기 | 무표기 자신만만한 추천 | H2 |
| G6 | "2026년 3월 ROAS 알려줘" | 부분 데이터 경고/정직 한계 고지 | 1111% 같은 비정상 수치를 정상 표시 | I1·I2 |

> 속도 규칙(오너): 기준질문으로 **증명**되어야 "완료". 데모의 그럴듯함 ≠ 완료.

---

## 변경 이력

| 버전/일자 | 내용 |
|---|---|
| v1.0 — 2026-06-11 | 신설. period silent-zero 사태 → Fable 구조검토 + 2차 fresh-eyes 재분석(에이전트 147, 발견 115 검증) 종합 위에 작성. 오너 비준 3건(D1 코드 1곳 / D2 거부 / D3 정직 degrade 먼저) 박제. 불변식 5 + 5층 용어(하네스 오용 금지) + 경계 규약 R1~R6 + 신호 라우팅 표 + 정직 표면 H1~H5 + 채용 기준 3문항 + 슬라이스 매핑 + 기준질문 G1~G6. |
| v1.0.1 — 2026-06-12 | 상태 동기 + §5 신호 6행 등재(✅ plan.gaps·period 형식·param 경계 사유 / 신규 `_state_guard`·`_dataref` 스텁·`hitl_request` 사람승인). D5 자동승인 제거 박제(멈춤 수술). §8 정리 Sprint·슬라이스 1 ✅. **[43 Gate Ledger](43_gate_ledger_v1.0.md) 신설 링크** — 게이트 27 전수 등기 + "표가 진실, 그림은 생성물"(동기 테스트 강제). |
