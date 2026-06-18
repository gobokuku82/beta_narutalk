# 세션 컴팩트 복구 — 누수 완결 · 카드→에이전트 P0~P3 · pushdown 승인 (2026-06-12)

> compact 후 이 문서 읽고 이어서. ⚠️ **동시 세션**이 같은 main에서 작업(정리 Sprint·헌법 spec 19·stub 처분 등) — path-scoped 커밋, 내 파일만.

## 0. 한 줄
**누수 사건 전 층 완결** + **카드→에이전트 P0~P3 완료('에이전트' 필)** + **pushdown 수직 슬라이스 계획 승인됨 → 다음 작업 = S0부터 구현.**

## 1. 환경
- 백엔드 8001: 루트에서 `uv run python run_server_v2.py` (※ backend/ 아님 — 루트). **resume 시 떠있는지 먼저 확인**(수시로 내려감).
- 프론트 5173: `cd frontend && pnpm run dev`. 검증 = `pnpm vitest run` + `pnpm run build` (**typecheck만으론 불충분** — `*/` 주석 사건 교훈).
- ⚠️ **`pnpm run build` 현재 깨짐** (2026-06-12 검증 실측): `src/features/hitl/store.test.ts(71,19) TS2532` — 동시 세션 hitl 수술(`cb1707f`)이 남긴 것. vitest는 94/94 통과. **동시 세션 소관 — 그쪽이 안 고쳤으면 1줄 수정 후 진행.**
- **접속은 `127.0.0.1`** — localhost는 ::1 타임아웃 ~2s/요청 (`bcee112`로 프론트 3곳 고정).
- DB: `octormate_system`(checkpoint) · `octormate_data`(분석, 대용량 raw=행-테이블 `{client}.{tbl}(_id, data jsonb)` + 소형=JSONB blob). pw `root1234`.
- 백엔드 테스트 기준선 (2026-06-12 검증 실측 갱신): **918 passed + 실패 6** — pyarrow 3·DC_PERM_6·o04 + **신규 `test_collector_count_regression[household_structure_collector-12]`**(L4 직후엔 통과했음 — 원인 미조사). 구 hitl fixture 11건은 동시 세션 `cb1707f`가 수리.

## 2. 완결 — 누수 사건 (체인 전체)
허브 = [근본원인_execution_state_raw누수_2026-06-11.md](근본원인_execution_state_raw누수_2026-06-11.md) (v7+ — 동시 세션이 §9 외부검토 추가).
- **L3+L5** state 경계 게이트(>256KB 슬림)+미러 제거: `33ac21a` / 계획 `0725d3e` / 보고 [보고_state경계게이트_구현검증](보고_state경계게이트_구현검증_2026-06-11.md).
- **L4** collector 참조 반환(`_dataref`, 21종): `85ef5de` / 계획 [계획_L4_collector참조반환](계획_L4_collector참조반환_2026-06-11.md). e2e: GA4 ◆DATAREF(38319)+keepalive 완주 · 리뷰 체인 6 todo 정상 · **L3 보편성 라이브 실증**(active_orders_filter ★SLIMMED).
- **레거시 비대 대화 2개 삭제**(API, 오너 승인) → DB blob 155MB+→26KB, 목록 7.1s→2.0s. 이어 **localhost→127.0.0.1**(`bcee112`, ::1 타임아웃 제거) → 목록 **16ms**.
- 효과: checkpoint 155MB→KB · WS ~312MB→KB · 복원 5.5s→ms.

## 3. 완료 — 카드→에이전트 P0~P3 (백엔드 0)
계획 = [카드클릭_에이전트연결_설계계획](카드클릭_에이전트연결_설계계획_2026-06-10.md)(§8 P0~P3 ✅·P0 매핑표) / 설명 = [설명_카드액션메뉴_CardAsk](설명_카드액션메뉴_CardAsk_2026-06-12.md)(v4, 34건 검증).
- `9fe0273`: P0 매핑(/monthly KPI 9=K01~K09) + P1 `actions.ts` askAgent(가드4·`[지표 값 · 기간]` 임베드, 테스트 8) + P2 `CardAsk.tsx`(칩+진단/추천/재검증 활성, 🔍⚡ 비활성) + P3 KpiCell wrap.
- 필 진화(오너 피드백): `6ec35b8` 상시 [✨ AI] → `3300e2d` "에이전트"+아이콘 제거+primary 채움 → `8f5a7e7` **기본 연한톤(primary/15)→hover 짙게** (최종).
- 잔여: **P4**(explicit operation 주입+스키마검증+fallback) · **P5**(methodology_explainer 🔍 활성화 **+ 재검증 ✅ thin 정밀화**) · **P6**(타 섹션·5페이지 확장).

## 4. ★다음 작업 = pushdown 수직 슬라이스 (계획 승인됨)
계획 = [계획_pushdown_수직슬라이스_2026-06-12.md](계획_pushdown_수직슬라이스_2026-06-12.md) (`37f2b3c`) — 오너 "좋아" 승인.
- §2 ADR 4건(최소 where 2연산자 / 규칙은 tool / 두 백엔드 같은답 / text2SQL 비채택)도 함께 승인됨.
- 순서: **S0** ADR 박제(docs/agent_specs/adr/) → **S1** base.py `query()`/`aggregate()`+기본구현(TDD, tool 0 수정) → **S2** PostgresDataSource override(행-테이블만 SQL, blob=fallback)+교차 일관성 → **S3** `ga4_session_aggregator` 전환+정답값 회귀(**24,000/12,496/1,823**)+속도 실측 → **S4** 완료보고서 **+ 설계노트 이력 갱신**.
- 배경 문서: [설계노트_data조회계약_진화](설계노트_data조회계약_진화_2026-06-12.md) (①출구 계약=해결 vs ②조회 계약=이번 슬라이스).

## 5. 백로그 (다음 작업 이후)
1. 카드→에이전트 P4·P5 (§3 잔여)
2. C2: kst_timezone_normalizer 배선 버그 — planner가 produces 키를 source_id로(`DataSourceNotFound`) → GA4 분석 턴 halt (e2e 2회 재현)
3. C1: 테스트 실패 6건 수리 — pyarrow 3·DC_PERM_6·o04 + **신규 `household_structure_collector-12` count 회귀(원인 조사부터 — L4 직후엔 통과)**
4. 프론트 build 깨짐(hitl store.test.ts TS2532) — 동시 세션 소관, 미수리 시 1줄 수정
5. orders_active 류 비-collector 대형 반환 정리 (비긴급 — L3 게이트가 막는 중)
6. 세션연속성 후속(paused 재접속 승인 UI)·대화이력 후속(이어서 대화 P1.5·AI 요약 제목)
- ~~e2e 테스트 대화 5개 삭제~~ — **해소됨** (검증 실측: conversations 0건 — 이미 비워짐)

## 6. 제약 / 작업 방식
- path-scoped 원샷 커밋(내 파일만, `-m`은 `--` 앞에) / Co-Authored-By·attribution 금지 / 계획서 먼저·허가 후 구현 / TDD·회귀 충분히 / uv 사용 / 단계 완료 시 자동 커밋+완료보고서.
- 검증 워크플로(ultracode) 패턴: 문서 작성 후 다중 렌즈 반증 검사 (CardAsk 설명 doc에서 34건 검사·1건 정정 전례).
- ⚠️ 직전 오너 메시지(로고 클릭 홈 이동·셀 가독성)는 **오타로 철회됨** — 작업 대상 아님.

## 7. compact 후 resume 프롬프트 (복사용)
```
docs/reports/session_compact_recovery_2026-06-12.md 읽고 이어서.
다음 작업 = pushdown 수직 슬라이스 구현 (계획 docs/reports/계획_pushdown_수직슬라이스_2026-06-12.md 승인됨):
S0 ADR 박제 → S1 base.py query/aggregate 기본구현(TDD) → S2 Postgres override(행-테이블 SQL)+교차일관성 → S3 ga4_session_aggregator 전환(정답값 24,000/12,496/1,823 회귀+속도실측) → S4 완료보고서+설계노트 이력 갱신.
완결: 누수사건(L3/L4/L5+레거시삭제+localhost→127.0.0.1, 목록 16ms) / 카드→에이전트 P0~P3('에이전트' 필, P4·P5 잔여).
⚠️ 동시 세션 main 작업 중 — path-scoped 내 파일만. 백엔드 기준선 918 passed+실패 6(신규 household count 회귀 포함). 프론트 build가 hitl store.test.ts TS2532로 깨져있을 수 있음(동시 세션 소관). 서버는 루트에서 uv run python run_server_v2.py — 떠있는지 먼저 확인.
```

## 변경 이력
| 날짜 | 내용 |
|---|---|
| 2026-06-12 | v1 — compact용. 누수 완결·카드 P0~P3·pushdown 승인(다음=S0)·백로그·제약. |
| 2026-06-12 | v2 — **검증 워크플로(58건 검사·불일치 11) 반영**: 기준선 918+6(동시세션 cb1707f가 hitl 11건 수리·신규 household count 회귀)·프론트 build 깨짐 경고·테스트 대화 5개 해소됨(DB 0건)·목록 지연 2단계 귀속·S4=+설계노트 이력·P5=+재검증 정밀화·✨ 표기 제거·허브 v7. |
