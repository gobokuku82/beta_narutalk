# 세션 compact 복구 — 복합쿼리 + 에이전트 언어 씨앗 + 레이어 정리 (2026-06-10)

> **compact 후 이 문서 읽고 이어서.** (별도 thread = 프론트 디자인은 `session_compact_recovery_2026-06-10.md`)
> 추적 앵커 3종(§5) 따라가면 전체 복원.

## 0. 한 줄 / 현재 위치
출력/표시 레이어(완료) 이후 **"복합쿼리를 사용자에게 여러 결과로 제대로 처리"** + **에이전트 언어 MVP 씨앗** 작업. S1 씨앗·param 바인딩·coverage 점수표·버그픽스·레이어 정리(死코드+layer_guard 이동)까지 완료. **깨끗한 정지점.** 다음 = 백로그(§4)에서 사용자 선택.

## 1. 북극성 + 구조
- **북극성**: 복합쿼리("A하고 B하고 C해줘")가 여러 결과로 처리 + 에이전트 언어를 MVP용 씨앗으로 키움.
- **4-leg**: `복합쿼리 → cognitive 전달 → planning compose → execution → response 표시`
  - cognitive ✅(의도 포착, S1 씨앗) / planning ✅(coverage 89%) / **execution ✅ 병목 아님(병렬+직렬+체인 확인)** / 표시 ⬜병목(첫1개)
- **체크포인트 3개**: ①변환 품질(coverage 89%·noise) ②능력 경계(도구없음/모호 처리 — 설계 미정) ③표시(여러 결과 합치기)

## 2. 이번 세션 완료 (커밋 — 내 작업만)
| 영역 | 커밋 |
|---|---|
| 다운로드 경로 완성(프론트 attachments 배선 + 칩 + pptx 인라인 마크다운) | d7e3879 |
| 복합쿼리 천장 측정도구(corpus_compound + harness dag/deps) | 2511d7c |
| **S1 다의도 씨앗** sub_intents (append-only, 무회귀) | 8c3147a |
| **R3 param 바인딩**(MoM period_a/b·단일 period 결정론) | 2055ec8 |
| **coverage 점수표**(LLM-judge: 요청의도 vs plan covered/missing/noise) | d85f061 |
| ~~리뷰 누수 픽스~~ → **revert**(보고서 깨져서) | 9a69190 → 9e8a856 |
| **버그픽스 COGNITIVE_EMPTY_QUERY**(layer_guard brand 경로 버그) | 57dcfc5 |
| **死코드 제거**(_domains v1 실행기 + pause.py / content_agents 보존) | 27d7c92 |
| **레이어 이동**: layer_guard→`dream_agent/system_graph/layer_inspector.py` + error_codes→`app/core/error_codes.py` | 542223f |

## 3. 핵심 결정/함정 (재조사 불요)
- **S1 씨앗 = `Intent.sub_intents`**: 복합 시 cognitive가 다의도 나열(append-only). **planning은 아직 미소비**(씨앗만). 현 전달은 `cleaned` 평어로 됨.
- **천장은 문서(06-06)보다 높다**: F1(max_tokens 12000) 이후 planning이 복합 plan 꽤 완전히 컴파일. operation 스칼라(붕괴1)는 그대로지만 cleaned로 우회 보상.
- **coverage 89% / 진짜 문제 = noise(과잉포함)**: #1 = review 파이프가 비리뷰 쿼리에 주입. 근본 = **team_catalog가 `insights ← 감성/키워드(리뷰)`로 하드와이어** → "보고서"가 리뷰 끌어옴.
- **★review-leak 픽스 revert 이유**: 리뷰 차단하니 report_writer가 insights 없어 data_gate가 SKIP → 보고서 안 나옴. **진짜 해법 = report/insight를 리뷰에서 분리(catalog 모델 갭)** — 미해결(CP#1).
- **COGNITIVE_EMPTY_QUERY 버그**: layer_guard가 brand를 *최상위*에서 찾는데 brand는 `targets.brand` → degrade(tasks=[])가 전부 fatal 중단되던 것. 수정됨(targets.brand+intent.domain도 본다).
- **★헤드리스 사각**: layer_guard·data_gate가 WS/execution 경로라 harness/scorecard가 못 잡음 → **사용자 수동테스트가 잡음**. 측정에 execution 포함 필요.
- **layer_guard = layer_inspector로 *이름 바뀜***(guard→inspector). 이동+rename 동시라 헷갈림 주의.
- **분업**: 사용자=값/제품 판단, Claude=기술/객관 분석·실행. (사용자 "핵심설계 어렵다" → 기술설계는 Claude 몫, 값만 못박으면 됨)

## 4. 백로그 (다음 후보 — 사용자 선택)
1. **다시 테스트**(가벼움): "4월 매출 진단하고 채널별 ROAS 비교"가 이제 안 죽는지 체감.
2. **CP#1 보고서↔리뷰 분리**(유력): "보고서 만들어줘"가 주제 맞는 insight 내게 = catalog 모델 손보기. 측정상 felt 갭.
3. **CP#2 능력 경계**: 도구없음/모호 → 2축 라우팅(이해=되묻기 / 능력=정직고지) + capability 메타(선결, 큼).
4. **CP#3 표시**: 여러 결과 합치기(`_find_artifact` 첫1개) — 대개 가려짐.
5. **placement 2단계 나머지**: ws_agent/ws_hitl 통제부 추출(보류, WS밖 진입점 생길 때).
6. **R2**: planning이 sub_intents 소비(씨앗 자라게).

## 5. 추적 문서 (앵커 3종, gitignored)
- [복합쿼리 체크포인트](../_claude/4layer_system/compound_query_checkpoints_260610.md) — "지금 뭐하지" 앵커
- [천장+S1 씨앗](../_claude/4layer_system/compound_query_ceiling_and_s1_seed_260609_v1.md) — 측정·씨앗 박제
- [통제로직 이동계획표](../_claude/architecture/에이전트_통제로직_이동계획표_2026-06-10.md) — 死코드(완료)+이동(layer_guard/error_codes 완료, ws_* 보류)
- 측정 도구: `python -m scripts.agent_lang_diagnostics.{run_harness,score_coverage} --corpus corpus_compound.yaml` (backend/)

## 6. 사용자 작업 방식 (★항상)
- **초보자·비전공·DB 약함.** 기술용어는 질문일 수 있음 — 맞추지 말고 전문가 단일 권장.
- **무조건 동조 금지** — 의도 파악 후 객관 판단. (이번 세션: review-leak revert·layer_guard rename 등 사용자가 잡음)
- 큰/모호 = **계획서/의도 먼저 합의** 후 코드. **uv 사용**(pip 아님). **메모리 업데이트 금지**(큼).
- 단계 완료+테스트 통과 시 **자동 커밋(내 파일만 — 프론트 viz/monthly·pnpm-lock·dashboard·requirements 절대 휩쓸지 말 것)**.
- 회귀: backend `../.venv/Scripts/python.exe -m pytest tests/ -q -p no:cacheprovider`. 정상 = 808 pass / 16 fail(전부 pre-existing: parquet·sprint14 HITL·DC_PERM·batch5).

## 7. resume 프롬프트 (복사용)
```
docs/reports/session_compact_recovery_2026-06-10_복합쿼리_레이어.md 읽고 이어서.
복합쿼리+에이전트언어 작업 깨끗한 정지점. S1 씨앗·param바인딩·coverage점수표·버그픽스(COGNITIVE_EMPTY_QUERY)·
레이어정리(死코드+layer_guard→layer_inspector 이동) 완료. 다음 후보=재테스트/CP#1 보고서↔리뷰분리/
CP#2 능력경계/CP#3 표시/ws_* 추출(보류). 사용자에게 우선순위 확인.
초보자·객관판단·동조금지·uv·메모리금지·계획서먼저·커밋시 내파일만(프론트/dashboard/requirements 제외).
```
