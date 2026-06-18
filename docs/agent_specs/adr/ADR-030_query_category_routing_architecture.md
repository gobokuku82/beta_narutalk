# ADR-030: 쿼리 카테고리 라우팅 아키텍처 — 분석 사다리 + Q&A·의사결정 신설

## Status

**Accepted** (2026-06-11) — 2026-06-10~11 세션 결정 박제. 사용자 비전("시스템이 결마다 다르게 처리해야") + stage-2 진단을 흡수. 코드 구현 완료(커밋 fda4490·872cefe·b02f3eb·2f4c03a·71f0f6d·a2e17ee·9050096). 상세 스펙 = [39](../39_query_categories_and_routing_v1.0.md).

## Context

### 1. 사용자 통찰
> "분석카테고리가 하는 역할은 탐색 → 진단 → 추론 → 예측. 의사결정 레이어도 있어야해. 옵션 → 시뮬 → 추천 → 승인."
> "아하 질의응답 카테고리가 있어야 하는데 그것또한 없었군. RAG도 만들어야 하는데."

→ 사용자 요청은 **"결(category)"이 다르다**: 데이터 보여줘 / 해석해줘 / 그냥 물어봄 / 뭘 해야 해. 한 파이프라인으로 다 처리하면 안 됨.

### 2. 진단으로 드러난 빈자리 (catalog≠code 실측)
- **분석 깊은 3층**(diagnose/forecast/attribute) = `DEGRADE_OPS`(매핑 tool 부재 → "기능 준비중") = 안 지어진 사다리 윗칸.
- **질의응답** = `FACTUAL_LOOKUP` enum 만 있고 tool·라우팅 0 (response=display-only, 답하는 tool 없음) → "ROAS가 뭐야?"가 끝내 답 안 됨.
- **의사결정** = `ai_recommendation`(complete, ml_model mock)은 있으나 NL 라우팅 0 → "추천해줘"가 분석으로 대체됨.
- 공통 패턴: **"enum/tool 은 있고 배선만 없음"**.

### 3. 제약
- ML 모델 미보유 → `ml_models` ABC + Mock(fixture) DI (ADR-027). "ML 호출됐다 가정", 현재 LLM 이 분석.
- POC 단계 = LLM 적극 사용([memory](../../../) `project_llm_heavy_initial`).

## Decision

### 1. 요청을 **카테고리**로 라우팅 — `operation`이 선택자
cognitive 의 `intent.operation`(authored, [37 PMAL](../37_agent_language_pmal_v1.0.md))이 카테고리·깊이를 정한다:

| 카테고리 | operation | tool |
|---|---|---|
| 분석·탐색 | measure/breakdown/rank/compare/trend | metric/comparison 도구 |
| **분석·진단** | diagnose | `diagnoser`(LLM) |
| **분석·추론** | attribute | `insight_extractor`(LLM, 도메인무관) |
| **분석·예측** | forecast | `forecaster`(LLM) |
| **질의응답** | (measure + factual_lookup) | `qa_responder`(LLM) |
| **의사결정** | recommend | `recommender`(ml_model mock) |

### 2. 분석 = **인지 깊이 사다리** (탐색→진단→추론→예측)
`operation`이 깊이 선택자. 깊은 3층은 **LLMTool**(도메인무관 collect_inputs, ML=mock). 단일 tool 이 아니라 "숫자→의미" 해석 레이어.

### 3. 신규 **카테고리 = ToolCategory enum + 전용 agent**
- `ToolCategory += qa, decision`. registry strict 검증 + team_catalog `qa_agent`/`decision_agent` 등재(executor 가 status 로 implemented 판정).
- Q&A·의사결정은 **결정론 short-circuit**(planner): factual_lookup→qa_responder / recommendation→recommender 단일 plan(LLM 팀선택 우회 — 비결정 회피). **단일의도 한정**(sub_intents≥2 복합이면 Stage3 로 흘림, 2026-06-11).

### 4. 범위 — *단일 tool 부터*
- Q&A = 단일 qa_responder(RAG hook 자리만), 의사결정 = 단일 recommender(옵션·시뮬·승인 추후). 큰틀 구동 후 고도화.

## Consequences

### 긍정
- "ROAS가 뭐야?"·"왜 떨어졌어"·"개선안 추천" 이 각자 맞는 카테고리로 답.
- enum 은 있고 배선만 없던 빈자리 해소(DEGRADE_OPS·FACTUAL_LOOKUP).
- short-circuit 으로 Q&A·추천 비결정성 회피 + ml_model mock 재사용(중복 0).

### 비용 / 잔존
- **복합쿼리에서 short-circuit 트랩**(lv4 붕괴) → 단일의도 한정으로 해소(⒟).
- **sub_intents → planning 미배선(R2)**: 복합쿼리는 Stage3 LLM 보상에 의존(coverage ~96%).
- **Stage3 비결정성**(프롬프트 과소제약) = 잔존 = stage-2 지배 원인 ([18 §3](../18_engineering_disciplines_v1.0.md)).

### 완화
- 근원귀속(워크플로우+적대검증)으로 깨짐을 축에 귀속 → 헛수고 방지.
- 진단 도구(corpus + probe) 영속화로 재측정 가능.

## Alternatives

### A. 단일 파이프라인(카테고리 없음) — *기각*
- 단: "ROAS가 뭐야?"에 데이터 수집·분석 파이프를 돌림(과잉·빈 결과). 결이 다른 요청을 못 가림.

### B. Q&A·추천도 Stage3 LLM 라우팅 — *부분 기각*
- 단: e2e 실측 2/3만 도달(비결정). mock 은 상류 불필요 → 결정론 short-circuit 이 robust.

### C. 본 ADR (카테고리 + 사다리 + short-circuit) — *채택*

## Related

| ADR / Spec | 관계 |
|---|---|
| [39 Query Categories & Routing](../39_query_categories_and_routing_v1.0.md) | 본 결정의 상세 스펙 |
| [37 PMAL](../37_agent_language_pmal_v1.0.md) | operation 어휘(라우팅 입력) |
| [18 Engineering Disciplines](../18_engineering_disciplines_v1.0.md) | stage-2 근원귀속(프롬프트>하네스>>tool) |
| [ADR-027](ADR-027_five_actor_permission_separation.md) | ml_model 어댑터(recommender 백엔드) |

## 변경 이력

| 일자 | 내용 |
|---|---|
| 2026-06-11 | 초안 — Accepted. 2026-06-10~11 세션(분석 사다리 완성 + Q&A·의사결정 카테고리 신설 + 복합쿼리 stage-2 진단·핀포인트) 결정 박제. 카테고리 라우팅(operation 선택자) + 사다리(깊이) + ToolCategory 신설 + 결정론 short-circuit(단일의도 한정). |
