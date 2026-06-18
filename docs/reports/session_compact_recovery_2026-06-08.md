# 세션 compact 복구 — silent-0 차단 + 복구(G6) (2026-06-08)

> **compact 후 이 문서 + [데이터흐름맵](./silent0_복구_데이터흐름맵_2026-06-08.md)을 읽고 이어서 진행.** 데이터흐름맵이 canonical(원인·설계 한 장).

## 0. 한 줄 / 현재 위치

silent-0(LLM tool이 데이터 0건에도 거짓 보고서를 지어내는 버그) 작업 중. **report_writer는 차단 완료(R1, 커밋)**, **G6 복구 인프라 코어·감지 완료(커밋)**. 다음 = 합의된 **축2 + 축1 기본**(§2).

## 1. ★ 합의된 다음 작업 (여기서 이어서)

**두 축은 한 쌍**(축2=거짓말 멈춤·신호생성, 축1=신호 받아 이후행동):

| 할 것 | 내용 | 상태 |
|---|---|---|
| **축2 (근본수정)** | `LLMTool` 공통 부모를 만들어 **빈 입력 → LLM 호출 전 멈춤(data_insufficient 신호)** 을 자동화. 기존 3 LLM tool(report_writer 됨 / **insight_extractor·summary_generator 미수정=문2**) 이전. 새 LLM tool은 가드 자동 상속 | **착수 예정** |
| **축1 기본 (배선확인)** | 축2 신호 → 기존 정직메시지([responder.py:83](../../backend/app/dream_agent/response/responder.py#L83) build_insufficient_data_payload) 가 제대로 발동하는지 테스트로 확인 (대부분 공짜, R1에서 됨) | 〃 |
| 축1 HITL (C-lite) | "데이터 없음 → 메뉴 → 다른 기간 재실행". **나중**(기간필터/실고객 트리거 시) | 보류 |

**진행 방식(사용자 지정 프로세스)**: 의도파악 → 어떤 정보 필요 → 외부검색(내 정보 구버전 가정) → 가설수립 → 테스트파일 생성 → 테스트.

## 2. 완료 (커밋됨)

| 커밋 | 내용 |
|---|---|
| `575aa84` | R1 — report_writer 빈입력 거짓보고서 차단 (G1 빈가드 + G2 게이트 consumes=[insights] + G3 orphan 제거) |
| `06467bd` | G6 코어 — recovery/actions.yaml(메뉴) + is_blocked/build_recovery_payload/resolve_choice |
| `69994bb` | G6 execution_stage 감지 wiring (detect-only, load_actions 가드) |
| `205b29b` | G6 감지 테스트 구멍 메움 — detect_recovery 통합 단위 + never-raise |

> 주의: 위 커밋들 사이/이후에 **다른 작업스트림(frontend dashboard1/viz, db scripts)** 커밋이 섞여 있음(134c3d4 등) — silent-0 무관.

## 3. 미커밋 (내 세션 산출 — 커밋 권장)

- `backend/tests/test_hitl_layer_architecture.py` (HITL 아키텍처 박제, 3 pass)
- `backend/tests/test_d3_adjust_query_period.py` (D3 박제, 3 pass)
- `docs/reports/silent0_복구_데이터흐름맵_2026-06-08.md` (canonical 맵)
- `docs/_claude/4layer_system/silent0_g6_interactive_wiring_계획_260607_v1.md` (gitignored — v3 + 정정)

⚠️ **stray(커밋 금지, 검토 후 삭제)**: `d3_answer.json`, `test_cognitive_reentry.py` (repo 루트, 실패 워크플로우 잔재 추정).

## 4. 테스트 현황 (silent-0 관련 = 20 green)

- R1: `test_silent0_fix_r1.py` (5) + characterization 3개 의미반전 처리
- G6 코어/감지: `test_recovery_g6.py` (9, RC-1~9)
- HITL 아키텍처: `test_hitl_layer_architecture.py` (3)
- D3: `test_d3_adjust_query_period.py` (3)
- 전체 회귀: 748 pass, 실패 15 전부 pre-existing(parquet 미설치·sprint14 HITL timeout·DC_PERM — git stash 교차검증). **내 변경 breakage 0.**
- 실행: `.venv/Scripts/python.exe -m pytest <path> -q -p no:cacheprovider` (또는 `uv run pytest`).

## 5. 멘탈 모델 (상세 = 데이터흐름맵)

- **거짓말 정체**: report_writer(Execution LLM tool, [report_writer.py:53](../../backend/app/dream_agent/tools/report/report_writer.py#L53))가 빈 insights에도 LLM 불러 보고서 지어냄. (response LLM 아님, insight tool 아님.)
- **연쇄**: 0건 → insight_extractor(빈 insights 지어냄, 미수정) → report_writer(보고서 지어냄, R1 수정) → responder(성공 오인).
- **데이터부족 판단 위치**: Execution의 data_gate([executor.py:188](../../backend/app/dream_agent/execution/executor.py#L188)). (Planning은 param부족 detect_plan_gaps.)
- **R1 수정 패턴**: consumes 선언 → 게이트가 빈입력 SKIP → data_insufficient 신호 → 정직메시지.

## 6. 핵심 확정 사실 (조사로 박제 — 재조사 불요)

- langgraph **1.1.6** (uv/pyproject 진실. requirements.txt 폐기됨). `interrupt()` **node-agnostic**(어느 레이어든). checkpointer 필수(런타임 AsyncPostgresSaver).
- HITL 이미 **멀티레이어**(planning plan_review + execution pause). 통로 2개=송신(ws_agent)/수신(ws_hitl) 분리, resume은 **turn_id 키·payload 무관 → 3번째 통로 불요**.
- 그래프: [builder.py](../../backend/app/dream_agent/system_graph/builder.py) 정적 엣지 `START→cognitive` 1개뿐, 전구간 Command(goto) → 어느 노드든 점프 가능.
- **복구 재실행에 cognitive 재진입 불요**: cognitive는 user_input 재파싱으로 period 덮어씀. "다른 기간"은 **period param 변경+resume**(기존 [handle_todo_edit](../../backend/app/dream_agent/workflow_managers/hitl_manager/manager.py#L410))로. metric 도구는 **단일월 전용**("/" 범위 거부) → "범위 확대(C-full)"는 도구확장 선행, "단일월 변경(C-lite)"만 작음.

## 7. 사용자 작업 방식 (중요 — 항상 적용)

- **초보자·비전공·DB 약함.** 기술용어는 질문일 수 있음 — 맞추지 말고 전문가 단일 권장.
- **무조건 동조 금지** — 의도 파악 후 코드 면밀 검토, 객관 판단. (이번 세션에 사용자가 내 오판 여러 번 교정: ws_hitl 누락, goto cognitive 과설계 등.)
- **내 정보 구버전 가정** → 외부 검색으로 확인. **uv 사용**(pip/requirements 아님).
- 큰/모호한 작업 = 계획서로 의도·스코프 먼저 합의 후 코드.
- **메모리 업데이트 금지**(사용자: 메모리 너무 큼).

## 8. 문서 색인

- **canonical 맵**: [silent0_복구_데이터흐름맵_2026-06-08.md](./silent0_복구_데이터흐름맵_2026-06-08.md)
- 원인분석: [d4_silent0_rootcause](../_claude/4layer_system/d4_silent0_rootcause_260606_v1.md)
- R1 수정계획: [silent0_수정_실행계획](../_claude/4layer_system/silent0_수정_실행계획_260607_v1.md)
- G6 설계/wiring: [g6_hitl복구_설계](../_claude/4layer_system/silent0_g6_hitl복구_설계_260607_v1.md) · [g6_interactive_wiring_계획 v3](../_claude/4layer_system/silent0_g6_interactive_wiring_계획_260607_v1.md)
- 안전망 진단: [분석파이프라인_데이터안전망](./분석파이프라인_데이터안전망_진단과수정방향_2026-06-07.md)

## 9. compact 후 resume 프롬프트 (복사용)

```
docs/reports/session_compact_recovery_2026-06-08.md 와 silent0_복구_데이터흐름맵_2026-06-08.md 읽고 이어서.
다음 작업 = 축2(근본수정: LLMTool 공통 부모로 insight_extractor·summary_generator 빈입력 가드 자동화, report_writer는 됨) + 축1 기본 배선 확인(축2 신호 → 정직메시지 발동 테스트).
프로세스: 의도→정보→외부검색→가설→테스트파일→테스트. 무조건 동조 말고 객관 판단. uv 사용. stray 파일(d3_answer.json, test_cognitive_reentry.py) 검토.
```
