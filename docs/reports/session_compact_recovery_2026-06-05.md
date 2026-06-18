# Session Compact Recovery — 2026-06-05 (아키텍처 정리 + 데이터검증 개념 정립)

> 이전: `session_compact_recovery_2026-06-04_v2.md`(PMAL B1 W1~W3·F2 해결 시점). 본 문서 = 그 위에 **B1 닫기 + 리뷰 흔들림 해결 + 시스템 구조 분석/권위문서 + 아키텍처 위반 정리 + LLM-tool 프롬프트 외부화** 시점. **다음 세션 1순위 읽기.**
> **한 줄**: B1 닫고(diagnose 정직), 리뷰 ~40% silent-0를 dataflow 완성으로 0%화, 시스템 레이어 의존을 spec 16으로 박제, V1 순환·V5 옆결합·매니저 모델 정정, LLM-tool 프롬프트 외부화. **남은 핵심 = B2 데이터 게이트(tool 경계 데이터 충분성 검증).**
> **검증 상태**: HEAD `42ff823`. 가드+핵심 테스트 **46 통과(재실행 확인)**. 아래 모든 커밋 해시·파일 경로·테스트 수는 실측.

---

## §1 이번 세션 커밋 (에이전트-백엔드 8건, 시간순)

| 커밋 | 내용 |
|---|---|
| `71ec8f5` | **B1 닫기** — diagnose/forecast/attribute 빈-실행 시 거짓("데이터 없음") 대신 정직 degrade. `responder.build_degrade_payload`(결정론, LLM 우회). |
| `311fb0f` | **리뷰 흔들림 해결** — `complete_dataflow_chain`(planner): consumes/produces 메타로 누락 producer(review_normalizer) 결정론 삽입. + `text_preprocessor` 카탈로그 메타 정정(raw_reviews→**normalized_reviews**, 거짓이었음). 흔들림 **40%→0%**. |
| `097cb02` | Stage3 few-shot 모순 제거 — 리뷰 예시 3개에 review_normalizer 포함(prose 규칙과 일치). 위생(완성 함수가 진짜 보장). |
| `544eebc` | **spec 16 신규** — Layer Dependency Architecture v1.0. 물리 레이어 의존 방향 단일 권위 박제. |
| `2a27a93` | **V1 순환 해소** — `trace_log`(미사용)을 `core/decorators.py`→`learning_manager/decorators.py` 이전. core↛dream_agent. |
| `2367d19` | **V5 옆결합 해소** — `DEGRADE_OPS`를 `cognitive.intent_shim`→`schemas.structured_query` 이전. response↛cognitive. |
| `dbc732e` | spec 16 정정 — **매니저=cross-cutting**(사용자 설계 확인). V4 위반→정상 재분류, V2/V3 reframe. |
| `42ff823` | **LLM-tool 프롬프트 외부화** — insight_extractor/report_writer/summary_generator 인라인 프롬프트 → `tools/prompts/*.yaml` + `tools/shared/prompt_loader`. |

> 병행(내 작업 아님, 같은 브랜치에 섞임): `0eab800`(프론트 관찰 대시보드), `157c364`(backend/_old·_old_api 245파일 삭제).

---

## §2 현 상태 (검증됨)

- **end-to-end 4종 정상**(세션 중 실측): 매출 **119,539,660원** / ROAS **6.53** / 리뷰 긍정 **58.3%** / diagnose **정직 degrade**("인과 분석 준비 중").
- **리뷰 체인 흔들림 0%**(세션 중 5/5 실측 — normalizer 항상 포함, 58.3% 일관). 이전 5회 중 2회 누락(40%)이었음. *LLM 호출 필요라 재실행은 안 함, 세션 중 검증.*
- **import 순환 0**(V1 해결), **response↛cognitive**(V5 해결) — grep·테스트 확인.
- 가드 테스트 3 신규: `test_layer_core_purity`(core↛agent) · `test_layer_stage_independence`(response↛cognitive) · `test_tool_prompt_externalization`. + `test_planning_dataflow_completion`(5) 등. **46 통과 @HEAD.**

---

## §3 권위 문서 / 개념 정립 (박제)

- **`docs/agent_specs/16_layer_dependency_architecture_v1.0.md`** (committed 단일 권위): 물리 레이어 의존.
  - 검증 불변식(grep 0): **I1 data↛agent · I2 tool↛orchestration stage · I3 agent-data 순수 · I4 stage DAG**.
  - **매니저/서비스 = cross-cutting**(core·llm_manager·ml_models·workflow_managers) — 스택 밖, layer가 부르고 서로 부름. 스택 방향 규칙 대상 아님(순환만 금지). ← 사용자 설계.
  - 위반 5: ✅V1(순환)·✅V5(stage↔stage) 해결 / V2·V3 soft(cross-cutting 서비스 호출, DI는 선택) / **V4 정상(매니저 cross-cutting, 위반 아님 — 내 오분류 정정)**.
- **`docs/_claude/4layer_system/structure_map_260605_v1.md`** + **`structure_viz_260605.html`**(브라우저 Mermaid): 파이프라인/구조 분석. (gitignored)
- **`docs/_claude/4layer_system/b2_data_contract_plan_260605_v1.md`**: ★B2 데이터 게이트 계획서. (gitignored)
- **데이터 검증 책임 분담**(개념): **선언=tool**(`consumes`/`produces` 메타) / **형태 계약=data layer**(`schemas`) / **집행·검수=execution**(tool 경계 게이트). tool↔tool은 현재 느슨한 dict(`find_in_previous`) → B2 대상. *stage 경계는 이미 `model_validate`로 Pydantic 계약 검증 중(튼튼).*
- **LLM-tool 구조**: `프롬프트 YAML(외부, tools/prompts/)` + `로직 .py` + `LLM client`. 프롬프트=콘텐츠→코드 밖(client overlay 추후 확장점).

---

## §4 다음 (우선순위)

1. **★ B2 데이터 게이트** (계획서 있음, 최고 가치) — tool 실행 전 `consumes` artifact 존재+non-empty 검사 → silent-0 거짓 성공 대신 **SKIPPED+정밀 사유+정직 degrade**. "tool이 받은 데이터가 충분한지" 문제의 실물. (TDD: 순수함수 충분성검사 → executor 배선 → 정직 전파.)
   - 짝 UX: **모호성 되묻기**(요청이 모호하면 cognitive가 HITL clarify) = 미배선(clarification_question 생성되나 안 물음). 불충분 원인 분기 — 되물음O(요청 모호)=cognitive / 되물음X(데이터 0건)=execution degrade / 시스템결함=완성함수. UX 결정(되묻기 임계 등) 선행.
2. **(선택) V2/V3 DI** — tool/ml_models에 LLM client 주입(import 제거). soft(cross-cutting이라 하드 위반 아님) — tool 순수성·테스트성 가치 판단. *프롬프트 외부화는 이미 완료.*
3. **(연기)**: W4 source축 제거→B2(역F2 지뢰), 조합형 diagnose(M3 skeleton+fill, ADR-024 skill 게이트·진짜 인과 불가), spec 10 §7.7.2 폐기 DI 예시 교체·카운트 정정·ADR-029 normalizers 부재 박제.

---

## §5 사용자 컨텍스트

- 비전공자·"작동하는 에이전트" 우선. **단일 전문가 권장**(옵션 나열 X).
- **동어반복 검증 거부**(안 가르친 입력으로 판정). **TDD RED→GREEN**. **무조건 동의 금지·객관 평가**(이번 세션 V2/V3·tool 카운트·V4를 객관 재평가로 정정·다운그레이드).
- **검증 과잉 금지**(작동 우선) · **계획서만 쌓지 말 것** · **메모리 박제 자제(docs)**. bypassPermissions 전역.
- **설계 의도**: 매니저=cross-cutting 목적 기능(layer 아님). tool=순수기능. 회사 다르면 시스템 다름(client별).

## §6 한 문장 재개

> HEAD `42ff823`. B1 닫힘·리뷰 흔들림 0%·spec 16(레이어 의존 권위)·V1/V5 해소·매니저=cross-cutting 정정·LLM-tool 프롬프트 외부화 완료(46 테스트 통과). 다음 = **B2 데이터 게이트**(tool 경계 non-empty 계약 검사 → silent-0 정직 degrade; 계획서 `b2_data_contract_plan_260605_v1.md`) + 짝 UX(모호성 되묻기, 미배선). V2/V3 DI는 soft 선택, 조합형 diagnose는 게이트된 다음 phase. 사용자=비전공·작동우선·객관평가·TDD·단일권장.
