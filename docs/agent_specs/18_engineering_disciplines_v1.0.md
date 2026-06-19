# 18 — Engineering Disciplines (하네스 · 프롬프트 · 컨텍스트 · Tool 구현)

> 이 시스템은 **4개의 엔지니어링 축**으로 만들어진다. 각 축은 *다른 관심사*를 책임지고, *다른 실패 모드*를 낳는다. "복합쿼리가 흔들리면 어느 축의 문제인가?" 같은 질문의 단일 진실 소스.
> 사용자 프레임 박제: **8gate=하네스 엔지니어링 / 4-Layer=컨텍스트 엔지니어링 / 프롬프트=프롬프트 엔지니어링** + **tool 구현(4번째 축)**. stage-2 근원귀속(2026-06-11)이 각 축의 책임을 실측으로 못박았다.

관련 spec: [14 System Agent Overview](14_system_agent_overview_v1.0.md)(4-Layer 책임) · [16 Layer Dependency](16_layer_dependency_architecture_v1.0.md)(물리 의존) · [37 PMAL](37_agent_language_pmal_v1.0.md)(에이전트 언어).

---

## §1 4개의 엔지니어링 축

| 축 | = 무엇 | 책임(무엇을 보장) | 코드 위치 |
|---|---|---|---|
| **컨텍스트 엔지니어링** | **4-Layer** (Cognitive→Planning→Execution→Response) | *어떤 정보가 어디로 흐르나* — 레이어 간 계약(PMAL)·핸드오프·상태(AgentState/ExecutionContext/previous_results) | `dream_agent/{cognitive,planning,execution,response}/` · `states/` · `models/execution.py` |
| **프롬프트 엔지니어링** | **LLM 프롬프트** (시스템 지시 + 입력쿼리) | *LLM 이 무엇을 어떻게 출력하나* — cognitive 분류·planning 도구선택·tool 분석 | `llm_manager/prompts/cognitive.yaml` · `planning_stage{1,2,3}_*.yaml` · `tools/prompts/*.yaml` · `clients/{client}.yaml` |
| **하네스 엔지니어링** | **결정론 게이트(8gate)** | *LLM 비결정·환각을 결정론으로 보강·차단* — 누락 보강·빈입력 차단·순서 보장·정직 degrade | `planning/planner.py`(게이트군) · `execution/executor.py` · `tools/llm_tool.py` |
| **tool 구현** | **도구 실행 로직** | *실제 계산·분석·수집이 맞나* — 순수 기능, produces/consumes 계약 | `tools/<category>/` (카탈로그는 현재 비어 있음 — `tools/{registry,base_tool,llm_tool}` 만) |

> **핵심 통찰(2026-06-11)**: 네 축은 *독립적으로 실패*한다. 한 증상(예 "복합쿼리가 깨진다")의 근원은 정확히 한 축(또는 둘)에 있고, 엉뚱한 축을 고치면 헛수고다. → §3 근원귀속.

---

## §2 하네스(8gate) — 두 종류

게이트는 **한 덩어리가 아니다.** 두 종류이고 운명이 다르다:

### ⓐ 현실가드 (영구 필요 — 데이터/능력 한계의 정직 처리)
| 게이트 | 코드 | 역할 |
|---|---|---|
| **data_gate** (소비 충분성) | `executor._run_single_todo` `check_consume_sufficiency` | consumes artifact 0건/부재면 SKIPPED + 정직 사유 (거짓 COMPLETED 금지) |
| **LLMTool silent-0 가드** | `tools/llm_tool.py` `execute` | 빈입력에 LLM 호출 전 차단 → `{reason: data_insufficient}` (환각 차단). executor 가 SKIPPED 전파(2026-06-11 ⒞) |
| **build_degrade / insufficient payload** | `response/responder.py` | 실행 0/데이터 불충분을 결정론 정직 메시지로 |

### ⓑ 가리개·보강 (LLM 뇌 고치면 축소 — 비결정·누락 보상)
| 게이트 | 코드 | 역할 |
|---|---|---|
| **complete_dataflow_chain** | `planner.py:299` | Stage3 가 빠뜨린 생산자를 produces/consumes 로 결정론 삽입 |
| **ensure_interpretation_fed** | `planner.py:383` | 해석 tool(insight/diagnoser/forecaster)이 계산 산출 없이 raw 만 받으면 도메인 대표 metric 삽입(2026-06-10) |
| **enforce_breakdown_dimension** | `planner.py:445` | operation=breakdown+dimensions 인데 차원분해(rows) tool 누락 시 차원대응 tool 삽입. convention=produces∋rows + name.startswith(dim)(하드코딩 맵 없음, 예: `<dim>`→`<dim>_aggregate`). "<dim>별 <metric>" scalar 붕괴 해소(2026-06-11 ⒠) |
| **bind_temporal_params** | `planner.py:274` | period / period_a·b(기간 비교) 결정론 바인딩 |
| **apply_subject_coherence_filter** | `planner.py:152` | 텍스트 의도 없으면 텍스트-데이터 tool 제외(F2 잠정 가드) |
| **validate_dag / detect_cycle** | `planner.py:117` | DAG 무결성(순환 탐지) |
| **QA / recommendation short-circuit** | `planner.py` `_is_qa`/`_is_recommendation` | factual/recommend 단일의도 → 결정론 단일 plan(LLM 우회). **단일의도 한정**(sub_intents≥2면 우회, 2026-06-11 ⒟) |

> ⓐ 는 데이터·능력 한계가 본질이라 *영구*. ⓑ 는 "LLM 이 더 똑똑하면 줄어들" 보상 — 단 LLM 비결정은 본질적이라 ⓑ 도 상당 부분 영구.

---

## §3 ★ stage-2 근원귀속 — 어느 축이 무엇을 깨뜨리나 (실측·적대검증, 2026-06-11)

복합쿼리 깨짐 5종을 4축으로 귀속(워크플로우 6 추적기 + 적대검증):

| 깨짐 | 근원 축 | 메커니즘 |
|---|---|---|
| **비결정성**(todo 수 run마다 변동) | **프롬프트(시스템)** | Stage3(`planning_stage3_todo.yaml`)가 "어느 tool 몇 개 어떤 순서"를 규정 안 함 → LLM free-form. **가장 광범위.** |
| **lv4 "찾아서 추천" 붕괴** | **프롬프트 + 하네스** | cognitive 가 복합을 단일 op=recommend 로 collapse + short-circuit 이 다의도 미지원 → plan 1개로 붕괴. (⒟ 로 단일의도 한정 = 해소) |
| **noise/중복 팽창** | **하네스 + 프롬프트** | dedup 이 auto_id 기준(LLM저작+자동삽입 공존 못 막음) + Stage3 모호 |
| **total period drift** | **tool 구현** | catalog `params_required=[]` vs 코드 period 필수(실측 tool 버그, ⒜ 정합) |
| **silent-0 빈출력** | **하네스** | LLMTool degrade 가 status 전파 안 함(⒞ 해소) |
| **breakdown 차원 누락**(차원별→scalar ~60%) | **프롬프트 → 하네스 해소** | Stage3 가 per-dimension tool 대신 전체 scalar 선택 → 게이트 ⒠(enforce_breakdown_dimension) 결정론 보강 |

### 무게중심: **프롬프트 > 하네스 >> tool 버그. tool·데이터는 주범 아님.**
- **tool 미구현(stub)** = 의도된 POC mock, plan 안 깨뜨림.
- **tool 구현버그** = 국소(total drift 류).
- **데이터 레이어**(data_layer: data_sources/workspace/schemas) = **건강**(기준월 정답 재현). 특정 월 0 = mock raw 시간 커버리지 부재이지 전달버그 아님.
- **적대검증이 1차 오진 2건 기각**: "DAG cycle(역방향 간선)"·"cognitive validation 실패" = 허구(코드 자기일관·`extra='forbid'` 아님).
- **★ 복합 multi-run 베이스라인**(2026-06-11, 5런×14쿼리, `baseline_compound.py`): systematic 깨짐 **0** · lv4/lv5(의존체인·fan-out·산출) **100%** → 깨짐은 좁은 tool-선택 비결정뿐. **R2(sub_intents 본배선)·broad Stage3 재작성 둘 다 데이터 미정당**(고칠 결정론 gap 없음·안정 다수 회귀 위험) → 좁은 게이트 ⒠로 93.5%→**98.5%**(σ22→8.5%). 단발 score_coverage 는 1회 LLM 스냅샷(judge 포함 3중 비결정)이라 **multi-run 평균±안정성 분류(stable/systematic/flaky)**가 ⒝/R2 선택의 근거·회귀 기준선.

> **방법론적 교훈**: 추적기 1차를 코드 실행 없이 단정하면 오진. **catalog≠code 실측 + 적대검증**이 근원귀속의 필수 절차.

---

## §4 축별 실패의 *징후 → 진단* 가이드

| 징후 | 의심 1순위 축 | 확인법 |
|---|---|---|
| 같은 쿼리가 run마다 다른 plan | **프롬프트(Stage3)** | **multi-run 베이스라인**(`baseline_compound.py`) → stable/systematic/flaky 분류. systematic=결정론 gap(게이트 후보)·flaky=비결정(프롬프트 후보) 구분이 핵심 |
| breakdown 쿼리가 차원 무시(차원별→전체) | **프롬프트(Stage3 tool선택) → 하네스 게이트** | operation=breakdown 인데 plan 에 rows 산출 tool 있나? 없으면 게이트 ⒠ 발동(auto_ id 확인) |
| 빈 답·"분석 완료"만 | **하네스(silent-0)** or **데이터 부재** | exec todos SKIPPED? data_insufficient? raw 커버리지 확인 |
| 자신만만한 *틀린* 답(엉뚱한 데이터로 샘) | **컨텍스트(PMAL domain 손실)** or **프롬프트(cognitive)** | intent.domain 보존됐나? F2 |
| tool 실행 에러·0건 | **tool 구현** or **데이터** | tool 코드 실측 + fetch 결과 + catalog≠code drift |
| 의존 순서 꼬임·순환 | **하네스(DAG)** or **프롬프트(Stage3 depends_on)** | validate_dag + depends_on 방향 |

진단 절차: **워크플로우 병렬 추적(축별) → 적대검증(오귀속 색출) → 합성.**

---

## 변경 이력

> 프레임워크 추출(2026-06-19) 이전(마케팅 도메인 시기)의 상세 변경 이력은 git 히스토리를 참조하세요.
