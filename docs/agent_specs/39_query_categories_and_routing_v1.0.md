# 39 — Query Categories & Routing (쿼리 카테고리 + operation→tool 배선)

> 사용자 요청은 **"결(category)"이 다르다**. 시스템은 cognitive 의 `operation`을 보고 4개 카테고리로 라우팅한다. 본 문서 = **카테고리 정의 + cognitive→tool 배선의 단일 진실 소스**.
> 2026-06-10~11 세션에 분석 사다리 완성 + Q&A·의사결정 카테고리 신설 + 복합쿼리 라우팅 보정.

관련 spec: [37 PMAL](37_agent_language_pmal_v1.0.md)(operation 어휘) · [32 Execution Tools](32_execution_agent_tools_v1.0.md)(tool 현황) · [18 Engineering Disciplines](18_engineering_disciplines_v1.0.md)(축).
코드: `cognitive/intent_shim.py`(operation→task) · `planning/planner.py`(short-circuit + Stage3) · `planning/catalog/team_catalog.yaml`(task→agent hint) · `cognitive/cognitive_stage.py:195`(shim 게이트).

---

## §1 시스템의 "결" — 4 카테고리

| 결 | 카테고리 | 예 | operation | 상태 |
|---|---|---|---|---|
| 데이터 보여줘 | **분석·탐색** | "4월 ROAS 보여줘" | measure/breakdown/rank/compare/trend | ✅ |
| 데이터 해석해줘 | **분석·깊은층(사다리)** | "왜 떨어졌어"·"무슨 의미"·"예측" | diagnose/attribute/forecast | ✅ (2026-06-10) |
| 그냥 물어봄 | **질의응답(Q&A)** | "ROAS가 뭐야?"·"뭐 할 수 있어?" | (measure + factual_lookup task) | ✅ 신설 (2026-06-10) |
| 뭘 해야 해 | **의사결정** | "개선안 추천"·"예산 배분" | recommend | ✅ 신설(추천 단일, 2026-06-10) |

> 텍스트(리뷰)는 분석 내 분기: domain∋reviews → sentiment. 크리에이티브(이미지/카피)는 Q4 범위.

---

## §2 분석 사다리 (인지 깊이) — 탐색→진단→추론→예측

`operation`이 **깊이 선택자**다. 깊은 3층(진단/추론/예측)은 과거 DEGRADE(매핑 tool 부재)였으나 2026-06-10 에 LLM tool 로 구현:

| 단계 | operation | tool | produces | 비고 |
|---|---|---|---|---|
| 탐색 | measure/breakdown/rank/trend | metric/comparison 도구(revenue_total·roas_overall·mom_revenue…) | 수치 | 기존 |
| **진단** | diagnose | `diagnoser`(LLM) | diagnosis | "왜·원인" |
| **추론** | attribute | `insight_extractor`(LLM, **도메인무관**) | insights | "함의·의미·시사점" |
| **예측** | forecast | `forecaster`(LLM) | forecast | "앞으로·예측" |

- 셋 다 **LLMTool** 패턴(collect_inputs = previous_results 분석 산출 전반, 도메인무관 OR-입력). ML=mock(ml_models), 현재 LLM 이 분석.
- **feeding 보강**(하네스 ⒝): 해석 tool 이 계산 산출 없이 raw 만 받으면 도메인 대표 metric 결정론 삽입(`ensure_interpretation_fed`).

---

## §3 라우팅 배선 — cognitive → tool

```
cognitive (cognitive.yaml): NL → operation(authored) + domain + sub_intents(복합 시)
   ↓ cognitive_stage.py:195 — intent_shim 발동 조건:
        domain 있음  OR  operation ∈ {recommend, diagnose, forecast, attribute}
        (measure+factual_lookup=Q&A·모호는 LLM tasks 유지 — measure 제외가 보호)
   ↓ intent_shim.py — operation → TaskType (단일 파생):
        reviews(domain) → SENTIMENT_ANALYSIS   (operation 무관·최우선)
        diagnose → CAUSAL_ANALYSIS              forecast → TREND_ANALYSIS
        attribute → INSIGHT_GENERATION          recommend → RECOMMENDATION
        compare → COMPETITOR_COMPARISON         그 외 → METRIC_CALCULATION
   ↓ planner.plan():
        ┌ QA short-circuit:        factual_lookup task & 단일의도 → qa_responder 단일 plan
        ├ 의사결정 short-circuit:  recommendation task & 단일의도 → recommender 단일 plan
        └ 그 외 / 복합(sub_intents≥2): Stage1(팀)→Stage2(agent)→Stage3(todo+DAG) LLM
   ↓ 결정론 게이트: breakdown_dimension(⒠) → dataflow_chain → interpretation_fed → temporal → coherence → validate_dag
```

### short-circuit 단일의도 한정 (2026-06-11 ⒟)
`_is_qa`/`_is_recommendation` 은 **sub_intents≥2(복합)면 우회** → Stage3 가 다의도 체인 컴파일. (단일 추천·QA 라우팅은 보존.) cognitive 가 복합에 sub_intents 신뢰성 emit 확인(lv4=2, 단일=0).

---

## §4 카테고리 → tool/agent (team_catalog)

| 카테고리 | agent | tool | status |
|---|---|---|---|
| 분석(수치) | metrics_agent | revenue_total·roas_overall·mom_revenue·… | implemented |
| 분석(텍스트) | analysis_agent | sentiment_analyzer·keyword_extractor | implemented |
| 분석(해석) | analysis_agent | **insight_extractor·diagnoser·forecaster** | implemented |
| **질의응답** | **qa_agent** | **qa_responder**(LLM, +용어집/능력, RAG hook 자리) | implemented |
| **의사결정** | **decision_agent** | **recommender**(ml_model.generate_recommendation mock) | implemented |
| 산출 | report_text/pdf/ppt/excel agent | summary_generator·report_writer·pdf_renderer·… | implemented |

- ToolCategory enum: collection/normalization/cleaning/preprocessing/metrics/comparison/analysis/report/rendering + **qa·decision**(2026-06-10).
- executor 가 `todo.tool→registry` dispatch + agent pool `status`로 implemented/stub 판정(미등재=RuntimeError → team_catalog 등재 필수).

---

## §5 복합/멀티쿼리 (stage-2 현황 — multi-run 베이스라인 실측 2026-06-11)

- cognitive 가 복합쿼리에 **sub_intents 신뢰성 emit**(lv4=2 등). 단 **planning 이 sub_intents *내용* 미소비**(코드 0건, `len≥2`만 short-circuit 우회 판별로 소비).
- **복합쿼리 = multi-run 베이스라인 측정**(`baseline_compound.py`, 5런×14쿼리): breakdown 게이트 후 **평균 coverage 98.5%(σ8.5%)** — sub_intents 덕분 아니라 **Stage3 LLM 이 전체쿼리(sq_json) 읽어 멀티의도 todo DAG 직접 컴파일.** ([근원귀속](18_engineering_disciplines_v1.0.md) §3)
- **systematic 깨짐 0 · lv4/lv5(의존체인·fan-out·산출) 100% stable.** → 깨짐은 좁은 tool-선택 비결정뿐 → 게이트 ⒠로 93.5%→98.5%.
- **R2(sub_intents → planning 본배선)는 데이터 미정당**: 고칠 결정론 gap(systematic) 없음. broad Stage3 재작성도 안정 다수 회귀 위험. → 큰 빌드 대신 **좁은 결정론 게이트**가 정답(세션 교훈: 게이트 > 프롬프트 비결정).
- 잔존 flaky 1건 = "리뷰 감성+채널 성과"(80%, 리뷰 파이프가 광고 도메인 삼킴) → (ii) cross-domain coherence 게이트 후보. ([findings](../_claude/4layer_system/baseline_compound_findings_260611.md))

---

## §6 변경 이력

| 버전/일자 | 내용 |
|---|---|
| v1.0 — 2026-06-11 | 신설. 2026-06-10~11 세션 흡수 — 분석 사다리(진단·추론·예측 LLM tool, 구 DEGRADE 해소) + Q&A 카테고리(qa_responder) + 의사결정 카테고리(recommender, ml_model mock) + operation→tool 배선(intent_shim + short-circuit) + short-circuit 단일의도 한정(⒟) + 복합쿼리 stage-2 현황. 짝 설계서(자취) = `_claude/4layer_system/{분석레이어,질의응답,의사결정}_설계서_260610.md`. |
| v1.1 — 2026-06-11 | "측정 먼저" 흡수. §3 게이트 체인에 **breakdown_dimension(⒠)** 추가. §5 stage-2 현황을 **multi-run 베이스라인 실측**으로 갱신(98.5%·systematic 0·R2 미정당·breakdown 게이트). 짝 자취 = `_claude/4layer_system/baseline_compound_findings_260611.md`. |
