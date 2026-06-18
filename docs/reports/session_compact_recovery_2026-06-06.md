# Session Compact Recovery — 2026-06-06 (B2.1 게이트 → 복합쿼리/에이전트 언어 고도화)

> 이전: `session_compact_recovery_2026-06-05.md`(b70b322, 아키텍처 정리·데이터검증 개념). 본 문서 = 그 위. **다음 세션 1순위 읽기.**
> **한 줄**: B2.1 데이터 게이트(체인 silent-0) 완료(W1-W4) → 검증이 *부분 커버*만 밝혀 종단·직접fetch는 보류·기록 → **복합 다의도 쿼리가 POC 핵심 작업량**임 확인 → 근본=고정·평면 언어(PMAL operation 스칼라) 천장 → **에이전트 언어 고도화**가 핵심 레버 → H5(원문+힌트, steps 그래프) 1차 설계 → 검증=**major_gaps**(종이 완결 불가+현 코드 실행 불가) → **다음 = 테스트 기반 재설계.**
> **검증 상태**: HEAD `3cceed4`. B2.1 가드+e2e 통과(세션 중 실측). 아래 커밋·문서 경로 실측.

---

## §1 이번 세션 커밋 (B2.1, 3건) + 메모리

| 커밋 | 내용 |
|---|---|
| `4710271` | B2.1 W1 — `check_consume_sufficiency`(consumes non-empty 게이트 순수함수) + 의도우선 계획서 |
| `1cdc3ea` | B2.1 W2 — `_run_single_todo` 게이트 배선(불충분→SKIPPED). 회귀: `_FakePool.get_tool_meta` 추가 |
| `3cceed4` | B2.1 W3+W4 — `build_insufficient_data_payload`(결정론 정직 degrade) + e2e(정상 58.3% / 강제 0건 cascade SKIP) |

메모리 갱신: `feedback_plan_intent_before_code`(신설), `feedback_user_beginner_recommend_actively`(강화: 객관평가·무조건동조금지·질문). *모든 분석 문서 = docs/_claude (gitignored), 코드 커밋만 위 3건.*

---

## §2 핵심 전환 (이번 세션의 큰 깨달음 — 순서대로)

1. **B2.1 = 체인 경로 silent-0만 닫음 (net positive, 유지).** 종단 LLM tool(insight/report/summary)·직접-fetch tool(review_sentiment 등)+mock 의 silent-0는 **보류·기록**(현 POC는 필터 없어 진짜 0건 거의 안 터짐). → `b2_silent0_impl_plan_260605_v2.md` §8.
2. **복합 다의도 쿼리 = POC 핵심 작업량 (사용자 확정).** "단순 1사이클"이 아님. 예: "모든 채널 수집→4월 모든 지표→채널별 ROAS→소재별→보고서"(수십 step), "지금 페이지 어떻게 나왔는지+이번달 캠페인 추천"(provenance→추천). **참조 2종**(같은 요청 intra + 이전턴/대시보드 cross) 둘 다 핵심.
3. **근본 = "한 쿼리 = 한 의도" 고정·평면 언어의 천장.** `intent.operation` 스칼라 + `tasks` 18 enum + shim 1:1 축소 → 복합쿼리가 하나로 뭉개짐(특히 reviews 규칙이 diagnose-degrade 이기는 역설). → `cognitive_complexquery_analysis_260606_v1.md`.
4. **PMAL = Performance Marketing Agent Language** (= 사용자가 "에이전트 언어"라 부른 것). **v0 배포 / v1 설계만 / 구현 미착수 = 반쪽 마이그레이션** → 며칠간 "이상한 작업/계획"의 뿌리(증상 패치 반복). spec 37.
5. **방향 = 에이전트 언어 고도화 (H5 유력).** 원문 보존(고정 스키마는 무손실 불가 → 천장 제거) + **steps 그래프 + 참조 3종(step/dashboard/memory) + 양화사(ALL) + op 확장 + output**. cognitive: 원본→정제→언어 **3겹 모두 planning 전달**. 3겹은 **학습 데이터**(추후 NL→언어 파인튜닝 → 런타임 lean = PMAL v2).
6. **H5 1차 초안 검증 = major_gaps (4 렌즈 모두).** 방향은 맞으나 **종이 완결 불가 + 현 코드 실행 불가.** → 다음 = 테스트 기반 재설계.

---

## §3 문서 지도 (이번 세션 산출 — 전부 docs/_claude, gitignored)

| 문서 | 무엇 |
|---|---|
| **`_claude/poc_to_mvp_roadmap.md`** | ★ POC→MVP 허브(간략, 데이터/에이전트/프론트). 작성패턴 "지금 X→MVP Y"로 갱신. 세부=spoke 링크 |
| **`_claude/4layer_system/agent_language_enhancement_plan_260606_v1.md`** | ★ 언어 고도화: 코퍼스(Q-A/Q-B lv5)·가설 H0~H5·**§2.1 H5 스키마**·**§2.2 검증 발견(구멍 A~D)** |
| `_claude/4layer_system/cognitive_complexquery_analysis_260606_v1.md` | 복합쿼리 진단(붕괴1~7) + 해법 5(E~A) |
| `_claude/4layer_system/b2_silent0_impl_plan_260605_v2.md` | silent-0 종단/직접fetch 보류·기록 + 재방문 트리거 |
| `agent_specs/37_agent_language_pmal_v1.0.md` | PMAL 정의·v0→v1·진화 v2(학습)/v3(skill) |

---

## §4 다음 — 테스트 기반 에이전트 언어 재설계 (사용자 계획)

**타깃 = `agent_language_enhancement_plan` §2.2 검증 구멍 (A~D):**
- **A 표현**: fan-out/중첩 grouping 1급 자리(group_by 유령 필드), op 닫힌 enum 천장(rank/diagnose 회귀), 조건/집계의집계 미표현.
- **B 실행 blocker(★)**: steps→tool 결정론 컴파일러 없음, quantifier ALL resolver 없음, planner/executor가 inputs/output 안 읽음, **fan-out artifact 키 충돌**(13 collector 'count', 채널별 ROAS 'roas' 덮어쓰기), report `analysis_results` orphan→SKIP.
- **C ref 실체 없음**: dashboard ref 입력 경로(cognitive에 없음), memory ref 저장소(닭-달걀), deictic 비결정.
- **D 마이그레이션**: 3중 표현 혼재, F2 스칼라(per-step 불가), 3-stage 전면 재작성, 빅뱅.

**우선순위**: B(실행 가능성)·A(fan-out/op)부터. **POC 즉시 액션**: 쿼리 3겹 저장 배선(`@trace_log`, 현재 미배선 — 학습 데이터 누적 시작).
**방식**: 다양한 테스트 → 결과 기반 언어 재설계(사용자 명시). provenance(Q-B 전반부)가 제일 tractable한 첫 슬라이스.

---

## §5 사용자 컨텍스트 / 작업 원칙 (강하게 적용)

- 비전공·개발경험 없음. **반드시 객관 평가·무조건 동조 금지·필요시 질문**(가설형 "X 아닌가?"는 검증 요청이지 동의 요청 아님). 단일 전문가 권장(옵션 나열 X) but 가치판단은 사용자 게이트.
- **큰/모호 작업 = 의도·스코프 계획서 먼저 → 검증-재검증 루프 → 코드는 "하자" 할 때만.** 검증 = 독립 적대(동어반복 ✗). 검증 과잉 금지·작동 우선.
- **복합 다의도 쿼리가 핵심**(단순 1사이클 아님). POC 한계는 "정직 degrade + 기록". mock→real = ABC 동일교체(tool 0변경). 새 client = 폴더만.
- 이번 세션 자기교정: "POC니 미루자"를 반복하다 *복합이 핵심*이란 사실에 결론 뒤집음 — 제품 요구 수준을 과소평가 말 것.

## §6 한 문장 재개

> HEAD `3cceed4`. B2.1 silent-0 게이트(체인) 완료·종단/직접fetch 보류기록. **복합쿼리가 POC 핵심** → 에이전트 언어(PMAL) 고도화가 레버 → H5(원문+steps그래프) 1차 설계했으나 검증=major_gaps(`agent_language_enhancement_plan §2.2` A~D: 표현 천장·실행blocker·ref실체·빅뱅). **다음 = §2.2 구멍 타깃 테스트 기반 재설계**(B실행·A표현 먼저, provenance 슬라이스부터, 3겹저장 @trace_log 즉시). 허브=`poc_to_mvp_roadmap.md`. 코드는 사용자 "하자" 시.
