# Session Compact Recovery — 2026-06-11~12 (분석→헌법→정리 Sprint→stub 처분)

> **다음 세션 첫 행동**: ① 본 문서 → ② [헌법 19](../agent_specs/19_architecture_constitution_v1.0.md)(모든 변경의 자) → ③ §6 대기 중 결정/다음 작업.
> 코드 상태: main, 마지막 커밋 `92a5af0`. 전체 회귀 **869 pass / 16 fail(사전존재 §5) / 2 skip** · frontend tsc 클린 + vitest 82/82.

---

## §1 한 줄

전체 코드분석 → Fable 구조 심층검토 + 2차 fresh-eyes 재분석(에이전트 147, 발견 115 검증) → **아키텍처 헌법(spec 19) 제정 + 오너 비준 3건** → 슬라이스 0 완료(정직 장치 수리 3건) → 정리 전환 Sprint(~4,320줄 삭제) → stub 처분 1·2차(카탈로그 108→**95**, stub 17→**4**). 다음 = chart_generator 결정 → 슬라이스 1(period 정직, DoD=G2).

## §2 이 세션의 결정 (오너 비준 — 전부 헌법 19에 박제)

| 결정 | 내용 |
|---|---|
| **D1** 계약 진실소스 | **코드 1곳** (schemas 상수·Pydantic·enum). catalog YAML=파생·표시용 — YAML에 값 제약 신규 선언 금지 |
| **D2** 위반 처리 | **거부** (정직 SKIPPED/에러 — coerce 금지) |
| **D3** period 없음 UX | **정직 degrade 먼저** ("기간을 알려주세요". 자동 기본월 금지. HITL 되묻기=D5 제거 후) |
| 조직 모델 | 실무 4부서 불변 + 사규집(Contract)+검문소(Guardrail)+운영위(Policy)+감사실(Harness). "하네스=게이트" 명명 금지 — planner 게이트들의 직함=**plan repair**. 8gate 면접: 전원 현역, 7명 재분류+2명 권한 조정 |
| 죽은 코드 3분류 | ①죽음(삭제—git이 보관소, legacy 폴더 금지) ②미구현(planned 마커+기한) ③유령 선언(라우팅 표가 생사 판정). 구분 4문항: 한때 돌았나/대체재 가동?/살아있는 계획?/마커? |
| stub 처분 방향 | **"구현 가능한 건 구현하면서 줄이자"** — mock "되는 척"보다 정직 degrade. 폐기 13종(아래 §4), 잔여 4종 |
| 완료보고서 규칙 | 작업 완료마다 docs/reports/ 완료보고서 필수 (메모리 박제) |

## §3 이 세션의 커밋 (전부 main)

| 커밋 | 내용 |
|---|---|
| `d767c84`+`58ce95b`… | (06-11) 코드분석보고서 / 슬라이스 0-① **hitl legacy 폐기**(`b75df88` — hitl_ack accepted 항상-false 거짓신호 수정, 장부 트랙 ~290줄) |
| `33b48c1` | 슬라이스 0-② layer guard "success"→"completed" (+brand·_LOG_PATH 절대경로·conftest autouse 격리·LG-03b 박제) |
| `9323414` | 슬라이스 0-③ 거짓 성공 2경로 차단 (responder FAILED 정직 문구+error 필드 첫 배선 / ws error→END에 LAYER_ERROR 신설+complete(aborted)) |
| `6b452e7` | **헌법 19 제정** + INDEX 등재 |
| `57ee019`/`a740f25`/`043ebe3`/`b169622` | 정리 전환 Sprint ①~④: backend 죽은 코드(domain 11종·errors/decorators·session_manager·executor 잔재) / 루트(tests 트리·_old_run_server·dashboard mount) / frontend mock 스키마 241줄 / planned 마커+llm_config 블록 제거 |
| `271ec8d` | stub 1차: trend_analyzer·competitor_comparator 폐기 (★도메인 정의 보존 — §4) |
| `6735724` | stub 2차: creative_team 전체(agent 4+tool 9)+word/excel filler 폐기 — 프롬프트 3장 동기, S2 박제 테스트 |
| 보고서 6건 | 6c749fd·5b7d5b8·3d6c6fa·92a5af0 등 — docs/reports/ {슬라이스0×2, 정리Sprint, stub×2, 헌법} |

## §4 ★보존해야 할 오너 도메인 정의 (메모리 `project_stub_tool_definitions` + spec 32 §7.1)

- **trend_analyzer = 트렌드 분석** — forecaster(예측)와 **다른 개념**. "forecaster가 대체" 분류는 오답(오너 정정).
- **competitor_comparator = A/B 테스트 분석** — 단일 tool 구현 어려움 → 폐기 후 재검토.
- 재구현 조건: 헌법 §7 채용 3문항 + **계산 방법은 오너 제공**.
- TaskType(image_generation 등)은 **언어 레이어에 유지** — 인식해야 "미지원" 정직 응답 가능.

현 카탈로그: 팀 3(analysis/qa/decision) · **95 tool = implemented 91 + stub 4**(chart_generator·template_selector·slide_designer·chart_to_slide). `test_d1_output_category_split.py::test_s2_4`가 stub 구성 박제 — 무단 변경 시 RED.

## §5 사전 존재 테스트 실패 16 (이 세션 무관 — HEAD 재현 확인됨)

test_hitl_timeout_integration 10 + test_hitl_timeout_resume_query_unit 1 (mock WS 경유 broadcast) · test_dc_perm DC_PERM_6 1 · test_batch5 o04 1 · test_phase3_pptx* 3. +opt-in DC 문서부패: DC1 mock_data 경로 5·DC4 링크 11·DC5 버전 20.

## §6 다음 (우선순위 순)

1. **오너 결정 대기**: chart_generator 구현 여부 — 묶인 처분: template_selector(폐기 권고—소비자 0), chart_to_slide(chart에 동반), slide_designer(브랜드 디자인 규칙 확보까지 보류). [stub 2차 보고서 §4·§5](stub처분2차_creative_word_excel_폐기_완료보고서_2026-06-12.md)
2. **슬라이스 1 — period 정직** (의존성 0, DoD=**G2**): ①오염원 5곳 `period or "all"` 데이터 제거 + **카탈로그 produces의 period 제거**(ad_cost_total:245·revenue_total:425 — 2차 재분석 C3 정정) ②`_inject_prev_outputs`에 SCOPE_PARAMS 주입 금지 ③executor 경계 YYYY-MM 검사→SKIPPED(invalid_param) + `_resolved_month` '2026-13' 구멍 보강 ④executor validate_params 호출 ⑤gaps→"기간을 알려주세요" (헌법 §8)
3. 슬라이스 2 후보: ①모호/미지원 정직 종착(되묻기 — creative 폐기로 필요성↑) ②mock 표기 H2 ③cycle 차단+'완료' 어휘 통일 ④혼합 집계(3월 ROAS 1111% 실측) ⑤frontend 신호 소비+운영 2건(todo_add drift·입력 잠금)
4. 보류 인계: `_storage` 30곳(유령 2차) · ToolSpec 표시 필드 · docs/specs 구세대 트리 16파일(오너 결정) · §5 사전존재 16+36

## §7 문서 지도 (이 세션 산출)

- ⭐ [헌법 19](../agent_specs/19_architecture_constitution_v1.0.md) — 불변식 5·5층 용어·R1~R6·신호 라우팅 표·H1~H5·채용 3문항·슬라이스 매핑·G1~G6
- 분석(gitignored): docs/_claude/4layer_system/ — [분석종합+조직모델](../_claude/4layer_system/아키텍처_분석종합_조직모델_260611.md)(8gate 면접 결과지) · [Fable 검토](../_claude/4layer_system/fable_structural_review_260611.md) · [2차 재분석](../_claude/4layer_system/재분석_2차_fresh_eyes_결과_260611.md)(신규 부류 4: 모름의 전멸·mock 무표기·stale 캐시·혼합 집계) · 현상황 앵커(미결정 전부 해소 표기)
- 완료보고서: 슬라이스0 ×2 · 정리Sprint · stub처분 ×2 (각 커밋 해시 명기)
- 메모리 신규 2: feedback_completion_report_on_done · project_stub_tool_definitions
