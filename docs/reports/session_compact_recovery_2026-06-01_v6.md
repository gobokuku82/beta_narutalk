# Session Compact 준비 (2026-06-01 v6) — 작업 ⑪·⑫·⑬·⑭·⑮·⑱ 완료, 작업 ⑰ v3 계획 commit 0 직전

> v5 = 작업 ⑪+⑬ 완료 ([session_compact_recovery_2026-05-31_v5.md](./session_compact_recovery_2026-05-31_v5.md)).
> v6 = **작업 ⑫ + ⑮ + ⑭ + ⑱ 완료 (17 commit) + 작업 ⑰ v3 계획서 작성 완료 (commit 0 사용자 승인 직전)**.

---

## ★ 이어가기 (compact 직후 진입)

### 1분 요약 (v6)

- **본질 진단 Q1 해소율 31.6%** — collection 22→0 + cleaning 3→0 양방향 drift 해소. 잔존 invisible 52 (metrics 35 + comparison 7 + analysis 6 + normalization 4).
- **작업 ⑰ (metrics 35 등재) v3 계획서 commit 0 직전** — 사용자 11 결정 모두 권장 채택. Phase 0~3 = 5 commit + 계획서 = 6 commit.
- **baseline 불변**: sprint13 단독 190/0/6 · sprint13+14 통합 **293/11/2** · dashboard1 **303/3** (pyarrow) · sprint15 **13/0** · frontend type-check exit 0 · ToolRegistry **85** · TaskType 17 · GoalType 6 · Source 17.

### 작업 ⑪~⑱ 누적 commit (25)

| # | commit | 작업 | hash |
|---|---|---|---|
| 1 | ⑪.A AgentState client_id 필드 + init_agent_state | `5dbc26e` | |
| 2 | ⑪.C execution_stage ExecutionContext.client_id | `2f55809` | |
| 3 | ⑪.B ws_agent payload 2 곳 | `1eefc1a` | |
| 4 | ⑪.D frontend sendQuery clientId + SideChatPanel disabled | `65bfd16` | |
| 5 | ⑪.E 21·11·i6 spec | `4a9a9a9` | |
| 6 | ⑪.F sprint13 신규 test 3 (RC + EP + E2E, 13 passed) | `6e8dae0` | |
| 7 | ⑬.1 Executor 클래스 폐기 (147 줄) | `fd6345b` | |
| 8 | ⑬.2 _run_agent + 'start' 분기 폐기 (381 줄 + WQ-07) | `533a632` | |
| 9 | v5 compact 박제 (⑪+⑬) | `7840513` | |
| 10 | ⑫.A broken 5 ads collector 폐기 (load_mock_csv 死코드) | `e5e9805` | |
| 11 | ⑫.B review_collector helper-B 재작성 (ADR-027 권한 정합) | `508e520` | |
| 12 | ⑫.C+D format_normalizer + team_catalog broken 5 정리 | `d4b02be` | |
| 13 | ⑫.E LLM prompt 4 곳 brand silently drop 해소 | `7a35da8` | |
| 14 | ⑫.F sprint15 broken test 7 폐기 (54 fail → 0, FN01-08 회복) | `958255f` | |
| 15 | ⑫.G sprint13 신규 test 3 (RC unit 5 + chain 1, 6 passed) | `f2debaa` | |
| 16 | ⑫.H ADR-027 §3 권한 위반 broken 6 해소 박제 | `078ddfc` | |
| 17 | ⑫.후속 load_mock_csv + MOCK_DATA_DIR 死코드 폐기 (38 줄) | `90b7fba` | |
| 18 | ⑮ broken 5 이름 잔존 9 docs doc-drift 정리 | `59bd6af` | |
| 19 | ⑭ 계획서 v3 박제 | `c3618ba` | |
| 20 | ⑭.C Source enum +8 (META/KAKAO/GA4/ORDERS/CUSTOMERS/PROMOTIONS/CATEGORY_SALES/CRM) | `f27f705` | |
| 21 | ⑭.A+D team_catalog 신 21 등재 (collection drift 22→0) | `f35e8d2` | |
| 22 | ⑭.B+B' Stage3 intent 분기 + cognitive.yaml Source enum 9→17 | `8d9e8b7` | |
| 23 | ⑭.E ADR-027 §3 박제 동기화 (collection drift 100%) | `c826af2` | |
| 24 | ⑱.A stub 3 폐기 (youtube/coupang/oliveyoung 역드리프트) | `b70f58a` | |
| 25 | ⑱.B cleaning_agent 신설 + cleaning 3 등재 (drift 3→0) | `76b4996` | |
| 26 | ⑱.C ADR-027 §3 박제 갱신 (collection·cleaning 양방향 0) | `43a7501` | |

### compact 후 첫 행동

1. **본 문서 §0~§3 정독** (박제 사슬 + 누적 자취 + 작업 ⑰ Phase 0 직진 가이드).
2. **§4 작업 ⑰ commit 0 진입** — `git add docs/reports/계획_작업⑰_metrics35_등재_2026-06-01.md && git commit -m "docs(reports): ⑰ 계획서 v3 ..."` (계획 v3 박제).
3. **§5 함정** + **§6 진입 안전** 준수.

---

## 0. 박제 단일소스 사슬 + 작업 ⑪~⑱ 박제

### 0.1 박제 단일소스 사슬 (compact v5 §0.1 + ⑭ 갱신)

| # | 박제 위치 | 작업 commit |
|---|---|---|
| 1 | `enums.py:29-40` ToolCategory 8값 | `dd9dbd1` |
| 2 | `catalog/{8 폴더}/` 85 yaml | `7f0ee5f`·`e5e9805` (작업 ⑫.A) |
| 3 | `33_tools_by_category/*` (8 문서 + README) | `aeee54f`·`59bd6af` (⑮) |
| 4 | `32 v1.2` §2.5·§5·§6·§7·§8·§9·§11 | `aeee54f`~`b534ec6` |
| 5 | `_schema.yaml` line 20 | `58c8228` |
| 6 | `ADR-022 amended` §4·§5 | `19c0ac9` |
| 7 | `30_DATA_MODELS:409` | `75cc921` |
| 8 | `API_SPEC:834` | `75cc921` |
| 9 | `frontend ToolPalette` | `7f0ee5f` |
| 10 (⑪) | `AgentState client_id` + frontend useCurrentClient | `5dbc26e`·`65bfd16` |
| 11 (⑭) | **team_catalog 신 21 + cognitive.yaml Source 17 + Stage 3 매핑** | `f35e8d2`·`8d9e8b7` |
| 12 (⑱) | **cleaning_agent 3 등재** | `76b4996` |
| (메타) | `session_compact_recovery_2026-06-01_v6.md` (본 문서) | 현 commit |

### 0.2 본질 진단 Q1 정량 자취 (⑭+⑱ → ⑰ 후)

| 시점 | invisible | 해소율 | 박제 |
|---|---:|---:|---|
| 작업 ⑫.D 후 (v5) | 76 | 0% | 본질 진단 |
| 작업 ⑭ 후 (collection 100%) | 55 | 27.6% | `c826af2` |
| 작업 ⑱ 후 (cleaning 100%) | 52 | 31.6% | `43a7501` |
| **작업 ⑰ 후 (metrics 100%) — 진행 예정** | **17** | **77.6%** | `⑰.E` |
| 작업 ⑳ 후 (잔존 17 등재) | 0 | 100% | — |

### 0.3 본질 진단 Q3 해소 (작업 ⑪) — 박제

- recent ①.x batch 6 batch (52bf5ac~ebfd17a) 활성화 완료
- helper-B agent path (frontend useCurrentClient → ws payload → AgentState → ExecutionContext → BaseTool.fetch → DataSource)
- 작업 ⑪ + ⑫ + ⑬ + ⑭ + ⑱ 누적 완료

---

## 1. 검증 baseline (작업 ⑱ 종료 시점, 불변)

### 1.1 회귀 baseline (2차 검증 통일 표기)

| 영역 | baseline | 검증 명령 (Bash, cwd=backend) |
|---|---|---|
| sprint13 단독 | **190 passed / 0 failed / 6 deselected** | `uv run pytest tests/sprint13 -q` |
| sprint14 단독 | 103 passed / 11 failed (HITL) / 2 skipped / 11 deselected | `uv run pytest tests/sprint14 -q` |
| sprint13+14 통합 | **293 passed / 11 failed (HITL) / 2 skipped / 17 deselected** | `uv run pytest tests/sprint13 tests/sprint14 -q` |
| dashboard1 영역 | **303 passed / 3 failed (pyarrow)** | `uv run pytest tests/{pipelines,dashboard1,data_sources,workspace,permissions,ml_models} -q` |
| sprint15 | **13 passed / 0 failed** | `uv run pytest tests/sprint15 -q` |
| frontend type-check | exit 0 | `cd frontend && pnpm exec tsc --noEmit` |

### 1.2 정합 검증 명령

```bash
# 1. baseline enum
cd backend && uv run python -c "
from app.dream_agent.schemas.structured_query import TaskType, Source, GoalType
print(f'TaskType: {len(TaskType)}')   # 기대: 17 (⑰ 후 18)
print(f'Source: {len(Source)}')   # 기대: 17 (⑭.C 신 8)
print(f'GoalType: {len(GoalType)}')   # 기대: 6 (METRIC 유지, ⑰ D2 페어)
"

# 2. ToolRegistry / team_catalog drift
cd backend && uv run python -c "
from app.dream_agent.tools.registry import get_registry
from app.dream_agent.planning.planner import _load_catalog
reg = get_registry(); reg.load()
cat = _load_catalog()
agents = cat['teams']['analysis_team']['agents']
all_cat = set()
for a in agents.values():
    for t in a.get('tools', []): all_cat.add(t['name'])
all_reg = {t.name for t in reg.get_all()}
print(f'ToolRegistry: {len(all_reg)} / team_catalog: {len(all_cat)} / invisible: {len(all_reg - all_cat)}')
# 기대: 85 / 55 (collection 22 + cleaning 3 + 기타 30) / 52 (metrics 35 + comparison 7 + analysis 6 + normalization 4)
"

# 3. agent path helper-B chain (⑪)
cd backend && uv run pytest tests/sprint13/test_review_chain_integration.py -v
# 기대: RCI-01 통과
```

---

## 2. 작업 ⑰ 진입 가이드 (★ 핵심)

### 2.1 작업 ⑰ 본질

**metrics 35 등재 (신 metrics_agent 신설)** — 본질 진단 Q1 최대 단일 해소 (invisible 52 → 17, 67% 해소).

### 2.2 v3 계획서 위치

[docs/reports/계획_작업⑰_metrics35_등재_2026-06-01.md](./계획_작업⑰_metrics35_등재_2026-06-01.md)

### 2.3 사용자 결정 11 (모두 권장 채택)

| # | 결정 | 적용 |
|---|---|---|
| D1 | agent | **B 신 metrics_agent** (cleaning_agent 패턴 정합) |
| D2 | TaskType + GoalType | **METRIC_CALCULATION 추가 + METRIC 유지** (페어, KPI 질의) |
| D3 | Phase 0 분리 | 분리 (12 yaml client param cleanup) |
| D4 | Pattern B 메타 | **per-tool yaml 본문 무변경** + catalog 4-key reflect (메타 strip) |
| D5 | ⑲ kickoff | **⑰ Phase 3 직후 자동 kickoff** |
| D6 | Stage 3 example | +1 (광고 KPI) |
| D7 | token 부담 | OK (+~3K input/요청) |
| (1차) | Phase 2 분할 | 2a (catalog + Stage 1·2) + 2b (Stage 3) |
| (1차) | Stage 1·2 prompt 갱신 | 필수 |
| (2차) | Phase 2a atomic | **5 영역 단일 commit** |
| (2차) | Phase 2b manual smoke | **필수** (광고 KPI LLM 1회, ~$0.01) |

### 2.4 6 commit 진입 순서

| commit | Phase | message |
|---|---|---|
| 0 | plan v3 박제 | `docs(reports): ⑰ 계획서 v3 (metrics 35 등재)` |
| 1 | **Phase 0** — client default 12 yaml | `refactor(catalog): ⑰.A client default 12 yaml cleanup (POC convention)` |
| 2 | **Phase 1** — TaskType + cognitive.yaml | `refactor(schemas): ⑰.B TaskType.METRIC_CALCULATION + cognitive.yaml (페어 박제, GoalType.METRIC 유지)` |
| 3 | **Phase 2a** — team_catalog metrics_agent + Stage 1·2 | `refactor(catalog+prompts): ⑰.C metrics_agent 신설 + Stage 1·2 prompt` |
| 4 | **Phase 2b** — Stage 3 분기 + example | `refactor(prompts): ⑰.D Stage 3 분기 + 광고 KPI example` |
| 5 | **Phase 3** — ADR-027 §3 박제 | `docs(adr): ⑰.E ADR-027 §3 박제 (metrics drift 100% 해소)` |

### 2.5 작업 ⑰ 핵심 박제 정정 (v3 critical 2 해소)

| Critical | v3 정정 |
|---|---|
| §2a.2 implicit_prerequisites yaml 구조 | **list-of-dicts 정합** — 기존 `tasks_requiring_data` enum (team_catalog.yaml L476-478) 에 `metric_calculation` **append** (prerequisites 동일, 신 dict 불요) |
| §7 frontend grep 명령 | **`grep -rn '/api/tools.*clumi\|fetch.*client.*clumi' frontend/src/`** (tool yaml 직접 호출만, 0 hit). v2 `'client.*clumi'` = 16 hit false-alarm |

### 2.6 metrics 35 = 2 패턴 (v3 라벨 정확화)

| 패턴 | 카운트 | 실 기준 |
|---|---:|---|
| Pattern A (compact) | 19 | clumi_methodology 박제 0 (K-code 부수) |
| Pattern B (heavyweight) | 16 | clumi_methodology 박제 (S-code 부수) |

→ Pattern A 19 중 **client default = 12** (Phase 0 scope).

### 2.7 12 yaml `client default=clumi` 명단 (Phase 0 scope)

1. ab_test_table 2. budget_channel_share 3. **budget_stacked** 4. budget_totals 5. campaigns_table 6. channel_aggregate 7. conversion_funnel 8. creative_cards 9. daily_performance_aggregate 10. daily_performance_totals 11. keyword_metrics_avg 12. keyword_top_roas

---

## 3. 다음 우선순위 옵션

### 3.1 권장 옵션 (작업 ⑱ 후)

| # | 옵션 | 작업 |
|---|---|---|
| **(가)** | **작업 ⑰ Phase 0 commit 1 진입** (v3 계획서 commit 0 직후) | Q1 본질 67% 해소 |
| (나) | 작업 ⑲ 자동 sync 선행 | convention 우선 |
| (다) | 작업 ⑮ external 13 + RawCollectorBase 21 ADR-027 §1 audit | FILE_NO hardcode |
| (라) | 멈춤 | 사용자 명시 |

### 3.2 전문가 단일 권장 = (가)

작업 ⑰ Phase 0~3 = 5 commit. 사용자 11 결정 모두 권장 채택 상태. v3 계획서 작성 완료, 사용자 승인 직전.

---

## 4. compact 후 첫 행동 (권장)

1. **★ 이어가기 정독** (본 문서 §0~§3).
2. **§1.2 baseline 정합 검증 명령 실행** (안전 진입):
   ```bash
   cd backend && uv run python -c "..."   # §1.2 #1, #2
   ```
3. **§2 작업 ⑰ commit 0 진입**:
   ```bash
   cd /c/kdy/Projects/octormate/beta_v001
   git add "docs/reports/계획_작업⑰_metrics35_등재_2026-06-01.md"
   git commit -m "docs(reports): ⑰ 계획서 v3 (metrics 35 등재)"
   ```
4. **§2.4 Phase 0~3 순차 진입** (각 단계 회귀 명령 §1.2 / 계획서 §7).
5. 진입 시 §5 함정 + §6 진입 안전 준수.

---

## 5. 함정·교훈 (작업 ⑪~⑱ 누적, ⑰ 진입 직전)

1. 박제 단일소스 사슬 12 곳 + 메타 = 一貫 갱신 필수
2. agent workflow line 박제 오류 → 직접 Read spot-check
3. 검증 ROI 곡선 (1차 高 → 2차 中 → 3차 限)
4. ADR amend 패턴 (Status 박제 + 본문 결정 이력 보존)
5. history vs active 박제 구분
6. _claude/ = .gitignored (local only)
7. broken link 점검
8. 빈 폴더 git rm 자동 폐기
9. workflow agent "계획 미실행 = fail" 오인
10. team_catalog ↔ ToolRegistry dual-source drift = 단계별 해소 (⑭ collection / ⑱ cleaning / ⑰ metrics / ⑳ 잔존)
11. **death code 폐기 신중**: GoalType.METRIC = active (cognitive.yaml L130 + Pydantic round-trip), 페어 박제 (TaskType.METRIC_CALCULATION) 정합
12. **implicit_prerequisites yaml 구조 = list-of-dicts** (dict-mapping X)
13. **frontend grep 명령 정확화**: `/api/tools.*clumi` (실 호출만), `client.*clumi` 는 mock/주석 false-alarm
14. **Phase 분할 = ONE 변경 정합** (Phase 2a + 2b, atomic 강화)
15. **Pattern A/B 라벨 = clumi_methodology 박제 유무** (K/S-code 부수)
16. baseline 표기 통일 — sprint13 단독 (190/0/6) vs sprint13+14 통합 (293/11/2)
17. commit message subject convention (recent ⑭/⑱ 패턴)
18. cross-Phase rollback 의존 매트릭스 박제
19. Phase 2a → 2b forward dependency (same session 연속 권장)
20. cognitive.yaml prompt §1 enum + §3 매핑 표 + few-shot 동기 갱신 필수

---

## 6. 진입 안전 (compact 후 ⑰ 진입)

- 작업 진입 전 baseline 확인 (293/11/2 + 303/3 + 13/0 + ToolRegistry 85 + TaskType 17 + GoalType 6 + Source 17)
- ONE 변경 원칙: 한 turn = 한 의미 단위 commit
- 큰 결정만 surface, 작은 진행 자명
- 死코드 즉시 폐기 — **신중 적용** (GoalType.METRIC 페어, ⑰ D2)
- 큰 작업 = 계획서 → 1·2차 적대적 검증 → 사용자 승인 → 진입 (작업 ⑤·⑨·⑪·⑫·⑭·⑰ 패턴)
- 사용자 = 비전공자, 직설 전문가 단일 권장
- workflow tool 적극 활용 (ultracode 모드)
- 변경 작업 = 41 v1.1 → 40 v1.1 순서

---

## 7. 작업 ⑰ Phase 0 진입 (사용자 승인 직후)

### 7.1 Phase 0 (commit 1) — client default 12 yaml cleanup

대상: 12 metrics yaml (§2.7 명단). `parameters` 안 `- name: client, default: clumi` entry 제거.

회귀: dashboard1 (303/3) + sprint13 단독 (190/0/6) + sprint13+14 통합 (293/11/2) + frontend grep 정확 명령 0 hit.

### 7.2 후속 Phase 1~3 (v3 §3 참조)

- Phase 1: TaskType.METRIC_CALCULATION + cognitive.yaml L74 17→18 + §3 매핑 표 행 추가 + few-shot
- Phase 2a: team_catalog metrics_agent 신설 + 35 entry + implicit_prerequisites append + task_agent_hints + Stage 1·2 prompt
- Phase 2b: Stage 3 분기 + 광고 KPI example
- Phase 3: ADR-027 §3 박제 동기화

### 7.3 후속 작업 (⑰ 종료 후)

- **⑲ 자동 sync 자동 kickoff** (D5, ⑰ Phase 3 직후)
- ⑳ 잔존 17 등재 (comparison 7 + analysis 6 + normalization 4)
- DAG audit (collection → cleaning → metrics 3-hop)
- K-code/S-code taxonomy ADR

---

**작성 완료**: 2026-06-01. 본 문서 = 작업 ⑪·⑫·⑬·⑭·⑮·⑱ 완료 + 작업 ⑰ Phase 0 직진 박제. compact 진입 가능.
