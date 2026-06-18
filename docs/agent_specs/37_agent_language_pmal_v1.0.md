# 37 — Agent Language (PMAL) — 구조 + 진화

> **PMAL = Performance Marketing Agent Language.** cognitive 레이어의 *출력*이자 planning 레이어의 *입력* — 시스템의 핵심 inter-layer 계약(에이전트 언어). 자연어(사용자) → **PMAL**(cognitive) → tool DAG(planning).
> 본 문서 = PMAL 의 **구조 + 진화 로드맵**의 단일 진실 소스. 설계 수렴 원문 = `docs/_claude/4layer_system/cognitive_planning_enhance_260602_v1.md` §8 (gitignored 자취). 본 spec = 그 정제·승격본(committed 계약).

관련 spec: [14 System Agent Overview](14_system_agent_overview_v1.0.md) (레이어 책임) · [20 Interface Contract](20_INTERFACE_CONTRACT_v1.1.md) (Layer Contract) · [30 Data Models](30_DATA_MODELS_v1.1.md) (Pydantic).
코드 위치: `backend/app/dream_agent/schemas/structured_query.py` (현 v0) · `cognitive/cognitive_stage.py` (생산) · `planning/planner.py` (소비) · `llm_manager/prompts/cognitive.yaml` + `clients/{client}.yaml` (프롬프트).

---

## §0 상태

| | 상태 |
|---|---|
| **v0 (현재 배포)** | `StructuredQuery` — `targets`/`goal`/`tasks[TaskType 18]`/`meta`. **source 축이 cognitive 출력에 존재**, TaskType = 닫힌 enum. |
| **v1 (PMAL, 본 spec 목표)** | 설계 **수렴 완료**(검증-재검증 통과, 원문 §8.3/§8.4). 구현 = **Phase B (planned)**. |
| **F2 잠정 가드** | subject-coherence 게이트(planner) — 텍스트 의도 없으면 리뷰-데이터 tool 제외. v1 의 degrade 계약을 완전 구현하기 전까지의 안전망. (commit `9a2371a`·`495d98e`) |
| **client 분리** | cognitive 프롬프트는 회사-무관 + `clients/{client}.yaml` 주입 완료 (Phase A, commit `32d8241`). PMAL few-shot 도 동일 구조로 client 별. |
| **분석 사다리 구현 (2026-06-10~11)** | `diagnose`/`forecast`/`attribute` 가 *degrade 에서 **실제 분석 tool** 로* 구현(diagnoser/forecaster/insight_extractor). `recommend` operation + `factual_lookup`→Q&A 카테고리 추가. **operation→tool 라우팅·카테고리 상세 = [39 Query Categories & Routing](39_query_categories_and_routing_v1.0.md).** §3 의 "no-tool→degrade"는 깊은 3층에 한해 *해소*(실 tool 매핑). |

---

## §1 언어란 무엇인가 — 레이어 헌장

PMAL 은 **두 레이어를 독립 구현·검증 가능**하게 만드는 중간 언어다 (cognitive = 유효 PMAL 산출하나 / planning = PMAL→맞는 plan 짜나).

### 핸드오프 3조건 (PMAL 이 반드시 충족)
1. **NL-free** — 모호성 해소 완료 (오타·은어·"지난달"→`2026-04` 절대화).
2. **도메인-complete** — subject 보존. "ROAS 분석"의 ROAS 가 살아있음 (degrade 금지). ← F2 근본 차단.
3. **카탈로그-free** — tool/skill 명·데이터 위치 없음. planning 이 바인딩.

### 레이어 책임
| | cognitive | planning |
|---|---|---|
| **책임** | 자연어 → PMAL | PMAL → tool DAG / skill |
| **안다 ✅** | 도메인 지식 (ROAS·매출·CAC 가 *무엇인지*) — 안정적 | 카탈로그 (metric→tool 바인딩·source·의존성) — 휘발적 |
| **모른다 ❌** | 카탈로그·tool명·데이터 위치·계획 방법 | 자연어 재해석 (cognitive 가 이미 끝냄) |
| **성공 기준** | intent-fidelity (NL-free·도메인-complete·카탈로그-free) | tool 정확 선택 + **결정성**(같은 PMAL→같은 plan) + skill 우선 |
| **안티패턴** | "ROAS분석"→"분석"(도메인 손실)·tool명 emit | NL 재해석·같은 입력에 흔들리는 plan |

> **2종 지식 원칙**: cognitive 가 필요한 것(도메인 지식, tool 추가와 무관하게 안정)과 아닌 것(카탈로그 지식, 휘발적)은 *종류가 다르다*. → cognitive 는 tool 이 90개든 900개든 **불변**.

---

## §2 PMAL 축 구조 (v1 — 수렴, 원문 §8.3)

```
intent: {
  operation:  measure(default) | breakdown | rank | compare | trend | diagnose | forecast | attribute | recommend
              # AUTHORED — cognitive 가 명시적으로 고름 (파생/재해석 X). 미언급 → measure.
              # rank ≠ breakdown (같은 dim, 다른 의도). compare-vs-target 은 benchmark 로.
              # recommend = 의사결정(행동 제안, 2026-06-10 추가). diagnose/forecast/attribute = 분석 사다리 깊은층(실 tool). → [39]
              # sub_intents[] = 복합쿼리 시 cognitive 가 각 의도 나열(신뢰성 emit 확인). planning 소비=R2(미배선).
  domain:     [revenue, ad_performance, customers, channel, conversion, promotion, reviews]
              # SET (스칼라 X — ROAS 처럼 다중도메인 metric 대응). few-shot 그룹·routing 힌트일 뿐 *조직 key 아님*.
  metric:     [ROAS, CAC, revenue, AOV, repurchase_rate, new_members, ad_cost, CTR, CVR, ...]
              # 1차 조직키. OPEN vocab + 동의어 사전 ("수익률"→ROAS). 닫힌 enum X (tool 결합 회피).
  dimensions: [creative, channel, campaign, keyword, member_grade, age, category, member/guest]
              # 진짜 disambiguator (tool 선택을 가르는 축).
}
period:    { resolved: "2026-04", compare_to: "2026-03"|null, granularity: month|day }   # NL-free 절대화
benchmark: { vs: target|prev|competitor, value? } | null   # "목표 ROAS 대비" — period 파생 아님
filters:   { audience?, budget?, segment?, ... }
output:    { type: metric|insight|report|chart, depth: brief|standard|detailed }
meta:      { confidence, ambiguity, raw_input, language }   # 기존 SQ 유지
# ⚠ NO source 축 — cognitive 는 source-free. (source 바인딩은 planning. §3)
```

### 축 설계 결정 (검증-재검증으로 못박힌 것)
| 결정 | 이유 |
|---|---|
| **operation = authored (파생 X)** | rank≠breakdown, compare-vs-target 은 파생 불가. 파생 = planning 의 NL 재해석 = charter 위반. 미언급 시 default=measure. |
| **domain = SET (스칼라 X)** | ROAS=revenue∩ad_performance 등 ~28% metric 이 다중도메인. 단일값 불가. domain 은 힌트일 뿐 조직 key 아님. |
| **metric = OPEN vocab (닫힌 enum X)** | 닫힌 enum 은 tool 수 1:1 추종 = 카탈로그 결합. open + 동의어 사전이 안정적. |
| **source 축 금지** | source=데이터 위치 = 카탈로그. cognitive 에 두면 charter 위반(과거 `targets.source` 회귀). 진짜 disambiguator 는 dimension 이지 source 아님. |
| **empty operation 유지 (diagnose/forecast/attribute)** | 카탈로그에 tool 0개여도 *삭제 금지* — F2 의 유일한 구조적 anchor. ~~대신 "no-tool→degrade" 계약(§3).~~ **2026-06-10 갱신: 이제 실 tool 매핑(diagnoser/forecaster/insight_extractor) → degrade 해소, anchor 는 유지(라우팅 [39]).** |

---

## §3 레이어 분리 — 카탈로그 조직은 planning 테이블 (원문 §8.4)

**핵심 원칙: 카탈로그 조직(metric×dimension×source)은 PLANNING 테이블에 산다 — cognitive 언어가 아니다.**

planning 이 소유하는 정적 lookup 3종 (Phase B 구현 대상):
1. **`(metric, dimension) → tool`**
   - `roas · ∅` → `roas_overall`
   - `roas · creative` → `creative_roas_avg`
   - `roas · promotion` → `promotion_roas`
   - (현 코드: 이 lookup *부재* → `planner.py` 가 SQ 를 free-text 로 3-stage LLM 에 넘김. 이게 비결정성·F2 의 구조적 원인.)
2. **default-source-per-(metric/dimension)** — source 자동 바인딩 + implicit collector 삽입 (cognitive 무관).
3. **no-tool → graceful degrade 계약** — `diagnose · revenue` 처럼 매핑 tool 이 없으면:
   → `mom_revenue` + dimension breakdown + LLM explainer + **정직한 "인과 분석 미지원"** (자신만만한 거짓 답 금지).

> 이 degrade 계약이 F2 의 *진짜* 해법. 현재는 subject-coherence 게이트(§0)가 잠정적으로 "리뷰 누출"만 막는다.

---

## §4 v0 → v1 마이그레이션

| v0 (StructuredQuery) | v1 (PMAL) | 전환 |
|---|---|---|
| `tasks: [TaskType 18 enum]` | `intent: {operation × domain × metric × dimensions}` | **교체** — operation→TaskType **shim** (역호환) |
| `targets.source` | (제거) | planning 이 (metric,dim)→source 로 바인딩 |
| `targets.brand/product/keywords` | 유지 (엔티티) | — |
| `goal.{type,output_format,depth}` | `output.{type,depth}` + `benchmark` | 재배치 |
| `targets.period` | `period.{resolved, compare_to, granularity}` | **resolved 절대화 강제** |
| `meta` | `meta` | 유지 |

**operation→TaskType shim (B1, `intent_shim.py`)**: 역호환 위해 operation 을 TaskType 으로 매핑. **2026-06-10 갱신**: `diagnose→CAUSAL_ANALYSIS`(diagnoser) / `forecast→TREND_ANALYSIS`(forecaster) / `attribute→INSIGHT_GENERATION`(insight_extractor) / `recommend→RECOMMENDATION`(recommender) — 구 "제외(degrade)"에서 *실 분석 tool 라우팅*으로. shim 발동 게이트(`cognitive_stage.py:195`) = `domain 있음 OR operation∈{recommend,diagnose,forecast,attribute}`. 상세 = [39](39_query_categories_and_routing_v1.0.md).
**점진 전환** ([[feedback_no_mixed_codebases]]): SQ 에 intent 추가 → TaskType deprecate → 전환 sprint 에 일괄 정리. v0/v1 혼재 금지.

---

## §5 진화 로드맵 — 어휘가 어떻게 고도화되나

PMAL 의 진화 축 = **닫힌 enum → 열린 어휘 → 사용 학습 어휘 → skill 참조.**

| 단계 | 어휘 상태 | 무엇이 바뀌나 | 선행 조건 |
|---|---|---|---|
| **v0 (현재)** | TaskType 18 **닫힌 enum** + source 축 | 배포됨 | — |
| **v1 (PMAL)** | metric **열린 어휘** + source 축 제거 + operation authored | 닫힌→열린 어휘, planning 이 source/tool 바인딩, degrade 계약 | (metric,dim)→tool 테이블 = Phase B |
| **v2 (사용 학습)** | client 별 metric glossary·few-shot 가 **실사용에서 누적** | (NL→PMAL) 페어 데이터 → 어휘·동의어·few-shot 자동 확장. client glossary 성장. | 데이터 누적 배선 (`@trace_log`) [[project_llm_heavy_initial]] |
| **v3 (패턴/skill)** | 언어가 저장된 **skill/workflow 참조** | 자주 쓰는 PMAL 패턴을 skill 로 저장 → 언어가 skill 호출 표현 획득. NL편집 3차. | skill 구현 (현 코드=0) [[project_nl_edit_roadmap]] |

> **진화 원칙**: 어휘 확장은 *사용에서* 자라야 한다 (선험적 enum 폭증 X). 단 — few-shot 을 *테스트 케이스에 맞춰* 넣는 것은 동어반복(금지). 일반 규칙·실사용 페어로만 확장.

---

## §6 검증 쿼리 → PMAL 매핑 (F2 차단 증명, 원문 §6.4)

| 자연어 | PMAL intent | planning 매핑 |
|---|---|---|
| "4월 ROAS" | `measure · ad_performance · [ROAS]` | `roas_overall` |
| "채널별 CAC" | `breakdown · ad_performance · [CAC] · dim:[channel]` | `channel_cac_compare` |
| "3월 vs 4월 매출" | `compare · revenue · [revenue] · period{2026-04 ← 2026-03}` | `mom_revenue` |
| **"왜 매출이 늘었어?"** | **`diagnose · revenue · [revenue]`** | revenue tools + 인과 explainer (degrade) |
| "등급별 매출" | `breakdown · revenue · [revenue] · dim:[member_grade]` | `grade_revenue` |
| "ROAS 상위 소재" | `rank · ad_performance · [ROAS] · dim:[creative]` | `creative_roas_avg` top-N |

→ "왜 매출?"이 `domain:revenue`로 못 박혀 더는 리뷰로 안 샘. **operation(HOW) × domain/metric(WHAT) 분리**가 핵심.

---

## §7 미해결 / Drift 방지

- **소비자 미구현**: `planner.py` 가 아직 (metric,dim)→tool 구조적 lookup 없이 free-text 3-stage LLM. v1 = 이 lookup 구축이 본체 (Phase B). + `planner.py` 모듈 분리(Plan→`schemas/`, DAG/catalog/gate). **2026-06-11 stage-2 근원귀속이 확인: 이 free-text Stage3 가 복합쿼리 비결정성(todo 수 변동)의 *지배적* 원인** ([18 §3](18_engineering_disciplines_v1.0.md)).
- **sub_intents → planning 미배선 (R2)**: cognitive 가 복합쿼리에 `intent.sub_intents[]` 를 신뢰성 emit(lv4=2, 단일=0 확인)하나 **planning 코드 소비처 0**(죽은 씨앗). 현재 복합쿼리는 Stage3 LLM 이 sq_json 전체를 읽어 *보상*(coverage ~96%). R2 = sub_intents 명시 소비(다단계 plan). 단 Stage3 보상과의 이중분해 정합 주의.
- **few-shot 전략**: PMAL = LLM 미학습 신규 DSL → few-shot 이 시범(결정적). clumi 도메인·op×domain 공간 커버·카탈로그-free. client 별 `clients/{client}.yaml` 에 위치.
- **다중 의도/도메인 쿼리**: 표현력 설계 잔존 (old `tasks[]` 대비 회귀 방지).
- **진실 소스 = 코드**. 본 spec 은 계약. 구현 시 `structured_query.py` ↔ 본 문서 동기화 (Drift 방지).

---

## §8 변경 이력

| 버전/일자 | 내용 |
|---|---|
| v1.0 — 2026-06-04 | 신설. `_claude/4layer_system/cognitive_planning_enhance_260602_v1.md` §8(수렴 PMAL)·§1.5(헌장) 승격. 구조(§2)·레이어 분리(§3)·마이그레이션(§4)·**진화 로드맵 v0~v3(§5)**·F2 차단 매핑(§6). 현 상태 = v0 배포 / v1 설계 수렴·구현 Phase B planned. |
| v1.1 — 2026-06-11 | **분석 사다리 구현 + 카테고리 신설 반영** (파일명 유지, 라우팅 상세는 [39] 위임). §0 상태행·§2 operation(+recommend·sub_intents)·§2 decision row·§4 shim(diagnose/forecast/attribute/recommend→실 tool)·§7(stage-2 비결정성 확인 + sub_intents R2 미배선) 갱신. 구 "no-tool→degrade"는 깊은 3층에 한해 실 tool(diagnoser/forecaster/insight_extractor)로 해소. 짝 = [18 Engineering Disciplines](18_engineering_disciplines_v1.0.md)·[39 Query Categories](39_query_categories_and_routing_v1.0.md). |
