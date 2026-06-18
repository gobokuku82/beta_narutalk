# Session Compact Recovery — 2026-06-12 v2 (슬라이스1→stub0→HITL수술→게이트대장→2트랙 계획·3중 검증)

> **다음 세션 첫 행동**: ① 본 문서 → ② [계획_마스터_2트랙_순서](계획_마스터_2트랙_순서_2026-06-12.md)(다음 작업의 단일 진실) → ③ §5 대기 결정.
> 자매 복구 문서: [아침 세션(헌법~stub처분)](session_compact_recovery_2026-06-12_헌법_정리Sprint_stub처분.md) · [동시 세션(pushdown·portfolio)](session_compact_recovery_2026-06-12.md) — 본 문서가 최신.
> 코드 상태: main `e6dd044`. **BE 919 pass / 3 fail(사전존재 — dc_perm·batch5·household[오너 데이터 건]) / 2 skip · FE 94/94 + tsc 클린.**

## §1 한 줄

오너 결정으로 슬라이스 1(period 정직, G2 달성) → stub 최종 처분(17→**0**, chart_generator 실구현) → HITL 간헐멈춤 수술(D5 자동승인 폐기·검토 모달 부활) → 게이트 대장 43(+HTML 뷰) → **2트랙(멀티쿼리×pushdown) 계획서 3장 작성 + 3중 검증(문서 2라운드 + 테스트 기반 실측)** 까지 완료. 다음 = 마스터 승인 1 확인 → [1] M0 측정 착수.

## §2 오너 비준 결정 (이 세션)

| 결정 | 내용 |
|---|---|
| 슬라이스 1 먼저 | stub 재논의보다 period 정직 우선 + template_selector 즉시 폐기(소비자 0) |
| stub 최종 처분 | 권장안 그대로: chart_generator **실구현**(matplotlib·한국어·Warm Neutral 미러) / chart_to_slide 폐기(pptx_generator가 흡수) / slide_designer 폐기(D10 확보 시 재채용) → **stub 제도 폐지**(mock_tools.py 삭제, 비구현=시끄러운 실패) |
| HITL = 방향 1 | "검토 ON=사람이 확인 후 실행"이 원래 의도(의도 전달 오류로 D5 자동승인 도입됐던 것) → D5 폐기·PlanReviewModal 부활·순단 복구(resume_query)·timeout 30분 동결(ON/OFF 선택권 있어 불요) |
| 구조도 전략 | 한 장 손그림 대신 **게이트 대장(표=진실) + 생성 그림** — spec 43 + `generate_gate_map`(md §4 + **HTML 뷰** 동시 생성) + 동기 테스트 |
| 2트랙 정의 | A=멀티쿼리(복합 의도 — "tool compose" 아님, compose는 ADR-023 금지어) / B=pushdown(데이터 로드). 순서 [1] A-M0 측정 → [2] B → [3] A-M1 수술 (**승인 1 최종 확인 대기** — "좋아"가 승인인지 미확정) |
| pushdown | **기승인** ("좋아", P 헤더) — 단 §8 보완 5건(V1~V5)을 승인 1에 흡수 |
| 검증 방식 | 문서 검증만으론 부족 — **테스트 기반(실행) 검증** 요구·수행됨 |

## §3 이 세션의 커밋 (main, 시간순 — portfolio 류는 동시 세션)

`8ee4614` template_selector 폐기(3차) → `e101a48` **슬라이스 1**(period 정직 4겹, DoD=G2) → `8605f0d` 적대리뷰 15건 반영 → `7f3002d` 보고서 → `30a5b26` data_gate `_dataref` count=0 인지 → `cf8f1e6` **stub 0**(chart 실구현+2종 폐기+mock 소멸) → `89e46fc` 보고서 → `7b89567` chart 고도화지도 docstring → `cb1707f` **HITL 멈춤 수술** → `28bc5b2` 보고서 → `00b539f` 근본원인 허브 v7(§9 외부검토) → `b0bf295`+`2b00177`+`7ad808a` **게이트 대장 43** → `0d69771` **계획서 2장 신설**(마스터+멀티쿼리) → `eedf35c` 검증 R1 반영(확증 25) → `3ee7640` 검증 R2 반영(확증 17) → `f3fcb7c` **테스트 기반 검증**(실측 11) → `e453394` 대장 v1.1(§5 오버레이+G28) → `e6dd044` **HTML 뷰 생성기**

## §4 ★보존 필수 사실

- **슬라이스 1 메커니즘**: 'period:"all"' 방출→주입→startswith 0건→CAC 0원 거짓성공을 4겹(P1 주입금지·P2 경계거부·P3 gap탐지·P4 "기간을 알려주세요")으로 차단. drift 정합 9곳(코드 period 강제 17종 vs 카탈로그 2종 — 주입에 기생했었음). SCOPE_PARAMS 계약 상수(schemas).
- **카탈로그 = 92 tool 전부 implemented, stub 0**. `test_s2_4`가 박제. 비구현 tool 등재 = executor 시끄러운 실패.
- **HITL**: hitl_request→frontend 자동 approve가 1/20 순단과 겹치면 30분 침묵이 원인이었음. 수리 = D5 7줄 삭제+모달 부활+재연결 시 resume_query+accepted:false 토스트+하네스 2줄 수리(헛붉던 11건 복구 — **사전존재 실패 16→3**). 서버 무수정.
- **테스트 기반 검증 실측** ([검증_테스트기반](검증_테스트기반_계획서3장_2026-06-12.md)): pushdown 효과 **26배 선납**(604ms→23.6ms, 정답값 3개 양측 일치) / GA4 traffic **마커만 소실·행-테이블 생존(38,319행, typed 31컬럼 — 스케치와 다른 모양!)** / corpus 키 type↔kind 불일치 / **e2e 파일럿: 인식 ✓(sub_intents 2)인데 '추천' 의도가 계획에서 통째 탈락** — G7 빨간불 원인 축이 표시 이전에 계획에도(regime 우려 실증).
- 환경: **python-pptx 1.0.2 설치됨**(사전존재 pptx 3건 해소) — requirements.txt 부재라 재구축 시 `pip install python-pptx matplotlib`. `DATA_BACKEND=postgres`는 스크립트에 무효(기본 FileDataSource).
- 게이트 대장 갱신법: 표 수정 → `cd backend && python -m scripts.generate_gate_map` → md §4 + `docs/_claude/gate_ledger.html` 동시 재생성 (동기 테스트가 강제).

## §5 다음 (우선순위)

1. **★승인 1 확인** — 마스터 순서([1] M0 측정 → [2] pushdown → [3] M1 수술). 오너 "좋아" 해석 미확정 상태로 compact됨.
2. 승인 시 **[1] A-M0**: 측정기 정비 4(T1 비파괴 출력·T2 corpus 인자화+type/kind+n_sub·T3 표시 판정기·T4 귀속 판정기) → 14쿼리×3런 full-graph(File 백엔드) + fresh 재기준선 5런 → 측정 보고서+수술표+G8 원문 → 계획 v2 오너 승인 → [2]로.
3. **[2] B pushdown**: P 계획 §0~7 + **§8 V1~V5 필수**(V1 마커 복원[경량 옵션 가능 — 행 생존 실측]·V2 마커 생존 가드=G28·V3 스트리밍 유지·V4 기준선 실측·V5 postgres 경로 fixture 실측). 행-테이블 2모양(typed/generic) 인지 설계.
4. 오너 답변 대기 2건(불변): household 12행 진위 / signup_conversion 분모 월 기준.
5. 백로그: 슬라이스 2 후보(모호 되묻기=C5로 흡수 예정·mock 표기 H2·cycle 차단·혼합 집계 G6·frontend 신호 소비·SKIPPED 사유) · docs/specs 구세대 트리(오너 결정) · 사전존재 3.

## §6 문서 지도

- ⭐ [계획_마스터_2트랙_순서](계획_마스터_2트랙_순서_2026-06-12.md) v1.2 — 다음 작업 단일 진실 (체크박스·게이트·결정 포인트)
- [계획_멀티쿼리](계획_멀티쿼리_복합의도_수직슬라이스_2026-06-12.md) v1.3 / [계획_pushdown](계획_pushdown_수직슬라이스_2026-06-12.md) v1.2(§8 V1~V5) / [검증_테스트기반](검증_테스트기반_계획서3장_2026-06-12.md)
- [43 게이트 대장](../agent_specs/43_gate_ledger_v1.0.md) v1.2 (§5 건설 오버레이) + 🖥 [HTML 뷰](../_claude/gate_ledger.html)(생성물)
- [헌법 19](../agent_specs/19_architecture_constitution_v1.0.md) v1.0.1 (신호 6행 등재·D5 제거 박제·슬라이스 0/1/정리 ✅)
- 완료보고서: 슬라이스1 / stub최종 / HITL수술 / 게이트대장 (각 커밋 해시 명기) · [근본원인 허브](근본원인_execution_state_raw누수_2026-06-11.md) v7(§9)
