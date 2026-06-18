# Session Compact 준비 — Cognitive/Planning 설계 + 상위 구조 감사 + 일반화 검증 (2026-06-04)

> **목적**: 긴 세션(데이터 정제 3종 질문 → … → anti-tautological 일반화 테스트) compact 전 상태 박제. 다음 세션 재구성용.
> **핵심 한 줄**: 설계는 깊이 검증됨(PMAL 수렴+sub-plan v1.1), **상위 감사로 moat(skill) 미구현·데이터누적 死배선 발견**, **일반화 테스트로 "메트릭 조회는 진짜 일반화됨 / insight·인과·리포트는 리뷰로 샌다(F2 일반형)" 정직 확인.**

> **🔄 UPDATE (이어진 세션, 2026-06-04 오후) — 진단→구현, 5 커밋**:
> - **F2 수정+보강** (`9a2371a`,`495d98e`): subject-coherence 게이트 2겹(menu-filter + 결정론적 post-filter) — 텍스트 의도(sentiment/keyword task or 리뷰 주제) 없으면 리뷰-데이터 tool 확정 제외. 단위테스트 11(LLM-free). 일반화상 **리뷰누출 0 안정**.
> - **Phase A** (`32d8241`): cognitive = **회사-무관 구조 + `clients/clumi.yaml` 프로필 주입**. 블루밍 잔재(slang/few-shot/legacy source enum/original_domain) 제거. **신규 회사 = `clients/{client}.yaml` 1장 (코드 무변경)**.
> - **Q1 provenance** (`7151cb7`): silent fallback 제거 — client 프로필 없으면 fail-fast, `cognitive done` 로그에 `profile=clumi|none` 박제 (동어반복 방지 토대).
> - **A4-lite** (`646c56e`): planning/cognitive few-shot 블루밍 이름 중립화.
> **현 일반화 = 7~8/10**: T1 메트릭 5/5·리뷰누출 0 안정. 변동/잔존 약점 3 (전부 게이트 무관):
>   ① 비회원 비중 라우팅(member_guest_stats vs 매출-share) ② 예측 WEAK(report_writer가 못하는 예측 서술=narrator 규율) ③ 분포 질의("등급별 매출 어떻게 나뉘어")를 cognitive가 insight 단독 라벨(metric 누락) 변동.
> **다음 = Phase B (PMAL)**: planning `source→collector`·`KPI분기` 하드코딩 → 검증된 (metric,dim)→tool 테이블 + **planner.py 모듈 분리**(Q3: Plan→`schemas/`, DAG/catalog/gate 분리) + **source축 cognitive 제거**(planning 바인딩). 위 약점 ①②③ + source축 한 번에. **검증-재검증(독립 에이전트) 권장 후 구현.**
> **잔존 블루밍**: `response.yaml`(response 레이어 12곳+) — 별도 de-blooming sweep.
> **반동어반복 재확인**: few-shot을 테스트 케이스에 맞춰 넣지 말 것(분포질의 보강도 *일반 규칙*으로). provenance fail-fast로 "되네"의 진위 추적.

---

## §1 세션 arc (무엇을 했나, 순서)
1. 데이터 정제 3종(preprocessing/normalization/cleaning) 차이 질문 → **metrics 35개 = 3역할 융합**(정제4/계산12/시각화정형19) 발견.
2. tool/data 레이어 경계 분석(data_sources=input관절·workspace=output관절·schemas=계약) — 방향(in/out) 깨끗 / schema↔정규화↔계산 연속체 흐림(본질적).
3. **문제 레벨 4층 자(L0작동·L1구조·L2일반화·L3본질)** 정립 — 사용자 진짜 병목 = 데이터지식 아니라 레벨 분류 부재.
4. **사용자 설계 의도 10점 명시** (§6) — tool-compose 3-mode·신뢰=lock-in moat(암묵지→형식지)·4layer+manager.
5. **F1 버그 수정+커밋** — DataFrame 직렬화 크래시(executor) → `json_safe` 정화. 커밋 `801a086`. agent path 9/10.
6. **PMAL(Performance Marketing Agent Language) 설계** → 검증-재검증 5라운드 → **수렴**(operation authored·domain SET·metric open·source 금지·카탈로그 조직=planning 테이블).
7. **cognitive/planning 세부계획서 v1.1** — 검증-재검증, 결합점 3개 역전파.
8. **상위 구조 감사**(독립 5-에이전트, 의도 vs 코드) — moat(skill) 코드 0·데이터누적 死배선.
9. **anti-tautological 일반화 테스트** — 정직한 되네/안되네 (§3).

---

## §2 핵심 산출물 (파일)
| 종류 | 경로 | 상태 |
|---|---|---|
| 상위 진단 | `docs/_claude/architecture/시스템_진단_레이어와_문제레벨_2026-06-02.md` | §0~§8 (§8=상위감사). **다음 세션 1순위 읽기** |
| 설계 계획 | `docs/_claude/4layer_system/cognitive_planning_enhance_260602_v1.md` | PMAL 수렴(§8.3·§8.4), §7·§8 검증 |
| cognitive sub | `docs/_claude/4layer_system/cognitive_subplan_260604_v1.md` | v1.1 (§6 검증·§7 cross-layer) |
| planning sub | `docs/_claude/4layer_system/planning_subplan_260604_v1.md` | v1.1 (§6 검증 — shim F2재유발 경고) |
| 패치노트 | `docs/_claude/patchnote/260602_agent_path_dataframe_serialization.md` | F1 |
| 커밋 | `801a086` (executor.py + test_execution_dataframe_serialization.py) | merged main |
| 하버스 | `backend/_scratch/agent_path_verify.py`(F1·9/10) · `agent_generalization_test.py`(일반화·6/9) | gitignored |
| 메모리 | **박제 안 함** (사용자 요청 — 메모리 비대 우려). docs로만. |

---

## §3 정직한 현 상태 (anti-tautological 일반화 테스트)
> 동기: 사용자 통찰 — "하드코딩 케이스 통과=당연(동어반복). 숫자맞음=*도구* 공로지 *에이전트* 공로 아님. 안 가르쳐준 입력에서만 측정." 채점=**라우팅(도메인/리뷰누출), 숫자 아님.**

- T0 스크립트 1/1 · **T1 패러프레이즈 4/4** · T2 비스크립트 2/3 · T3 정직한실패 0/2 → **의미있는 점수 6/9**.
- ✅ **GOOD(비동어반복)**: T1 4/4 — few-shot 먼 표현("광고가 돈값", "단골 다시 사는 비율")도 도메인 정확 = **cognitive 진짜 일반화**.
- ⚠️ **일관 실패 = 리뷰 파이프 누출**: `insight/causal/report/forecast` task → `insight_extractor`+`report_writer`(+`review_collector`). "왜 매출?"=순수 F2.
- **정직 요약**: 단순 메트릭 조회는 진짜 작동·일반화. **insight·인과·리포트·예측이 끼면 도메인 무지 TaskType 라우팅으로 리뷰로 샌다(F2 일반형).**

---

## §4 핵심 결정/원칙 (박제)
- **PMAL §8.3**: `intent{operation(authored+default) × domain(SET 힌트) × metric(open vocab) × dimensions}` + period{resolved,compare_to} + benchmark + filters + output. **source 축 금지**(cognitive catalog-free). 카탈로그 조직(metric×dim×source)=**planning 테이블**.
- **레이어 헌장**: cognitive=NL→PMAL(NL-free·도메인-complete·**카탈로그-free**) / planning=모든 tool/skill/source 바인딩.
- **2종 지식**: cognitive=도메인 지식(안정) ≠ 카탈로그 지식(planning·휘발).
- **되네/안되네 기준**: T0(스크립트=함정) 분리, **T1/T2/T3(일반화)가 진짜.** 라우팅 채점(숫자 아님).
- **로드맵 원칙**: 완벽 설계 후 출시 X → **작동 L0 출시 → 써보며 현실이 로드맵 작성** (사용자 자신의 "구현해보고 약점 찾아 보완" 본능 = 정답).
- **결합점 3개**(cognitive↔planning): B1 shim(operation→TaskType, **diagnose/forecast/attribute 제외** — 안 그러면 F2 재유발)·C2 compare_to 해소·C3 metric-토큰 granularity(ad_cost≠budget).

---

## §5 다음 행동 (우선순위)
**상위 감사 §8.5 권장 5** (sub-plan 구현 전 잠글 것):
1. [계약] skill 데이터 계약 박제 (구현 미뤄도)
2. [경량구현] **`@trace_log` 4 stage 부착** → moat 원료(페어 데이터) 누적 시작 ← 가장 싸고 높은 레버리지
3. [구조] hitl_manager의 ExecutionProgress/phase-tracking을 execution으로 분리
4. [구조] tool실행+직렬화(json_safe 3중복)+Workspace를 단일 실행커널로 수렴
5. [범위게이트] response viz

**일반화 테스트가 가리킨 #1 구체 수정**: `insight/causal/report/forecast` TaskType → 리뷰 파이프 라우팅(도메인 무지) 고치기 = **F2 근본**. planning_subplan §6.1과 동일(diagnose shim 제외 + degrade).

**미해결**: sub-plan v1.1 구현 전 결합점 3개 계약 확정 필요.

---

## §6 사용자 컨텍스트 (다음 세션 필독)
- **초보자·비전공자.** 원하는 것 = **"그냥 작동하는 에이전트"**. 방향 잡아주는 리더십 필요 (단일 권장, 옵션 나열 X — [[feedback_user_beginner_recommend_actively]]).
- **함정 경계**: "이렇게 만들었으니 당연히 됨" 동어반복 검증 거부. 의미있는 테스트(일반화) 요구. ← 매우 sharp한 통찰, 존중할 것.
- **검증-재검증 고집**: 매 단계 독립 적대적 검증(1차 설계 Plan + 2차 코드 Explore). 이게 5라운드에서 매번 구현-파괴 버그를 잡음.
- **메모리 비대 우려** → 메모리 박제 자제, docs로.
- 깊은 설계(PMAL)에 함께 들어갔다가 "상위부터 점검" 으로 줌아웃 → moat 미구현 발견. 다음엔 **L0 출시 우선** 정서.

---

## §7 한 문장 재개 (다음 세션이 이것만 읽으면)
> PMAL 설계·sub-plan은 검증 완료됐으나 **moat(skill)는 코드 0·데이터누적 死배선**이고, 일반화 테스트상 **메트릭 조회는 작동/리뷰누출(insight·인과·리포트·예측)이 깨진다.** 다음 = (a) 상위 5 잠그기(특히 ②@trace_log 데이터누적 시작) + (b) #1 수정(insight/causal/report→리뷰 라우팅=F2 근본). 사용자는 "작동하는 에이전트" 출시 우선, 동어반복 검증 거부.
