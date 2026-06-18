# Session Compact 준비 (2026-05-31 v5) — 작업 ⑪ + ⑬ 완료, 작업 ⑫ 잔존

> v4 = 작업 ④·⑤·⑥·⑦·⑧·⑨·⑩ 완료 ([session_compact_recovery_2026-05-31_v4.md](./session_compact_recovery_2026-05-31_v4.md)).
> v5 = **작업 ⑪ (client_id agent path 흐름 복구, 6 commit) + ⑬ (死코드 cleanup, 2 commit)** 추가.

---

## ★ 이어가기 (compact 직후 진입)

### 1분 요약 (v5)

- **본질 진단 Q3 해소** — `BaseTool.fetch` helper-B 가 agent path 에서도 작동 (recent ①.x batch 6 batch 완전 마감).
- **client 흐름 활성화** — frontend `useCurrentClient()` → payload `client_id` → AgentState → ExecutionContext → BaseTool.fetch → DataSource 전 사슬 연결.
- **死코드 폐기** — Executor 클래스 (147 줄) + _run_agent legacy (351 줄 + WQ-07) = 약 500 줄 cleanup.
- 골든 baseline 변동 0: **590 passed / 14 failed (11 HITL + 3 pyarrow) / 2 skipped**. sprint15 broken **17/54** (작업 ⑫ 잔존). S001=119,539,660.

### 작업 ⑪·⑬ 누적 commit (8)

| commit | 작업 | hash |
|---|---|---|
| 1 | 작업 ⑪.A AgentState client_id 필드 + init_agent_state 파라미터 | `5dbc26e` |
| 2 | 작업 ⑪.C execution_stage ExecutionContext.client_id 전달 | `2f55809` |
| 3 | 작업 ⑪.B ws_agent payload → init_agent_state (2 곳) | `1eefc1a` |
| 4 | 작업 ⑪.D frontend sendQuery clientId + SideChatPanel disabled 가드 | `65bfd16` |
| 5 | 작업 ⑪.E 21·11·i6 spec client_id 박제 | `4a9a9a9` |
| 6 | 작업 ⑪.F 신규 테스트 3 파일 (sprint13, 13 passed) | `6e8dae0` |
| 7 | 작업 ⑬.1 Executor 클래스 폐기 (147 줄) | `fd6345b` |
| 8 | 작업 ⑬.2 _run_agent + 'start' 분기 폐기 (381 줄 + WQ-07) | `533a632` |

### compact 후 첫 행동

1. 본 문서 §0~§3 정독.
2. §2 다음 우선순위 (3 옵션) 중 선택 또는 사용자 다른 결정.
3. 진입 시 §5 함정 + §6 진입 안전 준수.

---

## 0. 본질 진단 + 작업 ⑪·⑬ 박제

### 0.1 본질 진단 workflow (2026-05-31, 9 agent)

| Q | 결과 | 해소 |
|---|---|---|
| Q1 I/O+트리거 명확 | Partial — dual-source drift (Planner team_catalog 38 ↔ ToolRegistry 90, ~52 invisible) | 후속 작업 (②.2 catalog 단일화) |
| Q2 각 tool 작동 | 90/90 import OK, sprint15 54 failed = 6 collector load_mock_csv 死코드 | 작업 ⑫ |
| **Q3 관절 부재** | 관절 6개 존재. 단 **client_id agent path 단절** (가장 결정적) | **작업 ⑪ ✓ 해소** |
| Q4 누락 차원 | top 5 (데이터 일관성·timeout·LLM trace·composition·examples) | 후속 작업 |

→ 사용자 직관 적중률 3/4 (80%).

### 0.2 작업 ⑪ client_id agent path 흐름 복구

**계획서**: [계획_작업⑪_client_id_agent_흐름복구_2026-05-31.md](./계획_작업⑪_client_id_agent_흐름복구_2026-05-31.md) (v1→v2→v3, 1·2차 적대적 검증 후 진입)

**전 사슬 (활성화 완료)**:
```
frontend useCurrentClient() (api/clients.ts:43)
  → sendQuery({clientId}) (api/ws.ts:122)
  → ws_agent payload (client_id 키)
  → init_agent_state(client_id=...) (agent_state.py:67)
  → AgentState.client_id (TypedDict total=False)
  → execution_stage:175 ExecutionContext(client_id=state.get(...))
  → BaseTool.fetch(source_id, context) (base_tool.py:29)
  → DataSource.get(client, source_id)  ✓ 활성
```

**UI 가드**: `useCurrentClient` undefined 시 disabled (placeholder 분기, silent return). 사용자 [feedback_user_beginner_recommend_actively] 정합 — sonner toast backup 옵션 제거, 전문가 단일 권장.

**계약 spec 갱신 (3 파일)**:
- 21_WEBSOCKET_PROTOCOL_v1.5 §2.1 — query schema 에 `client_id?: string`
- 11_main_graph_state_v1.5 §2.0 — client_id 행 + Writer/Reader 매트릭스
- sprint13_integration_i6_agent_state_spec.md (gitignored) — init_agent_state 시그니처 박제

**신규 테스트 3 파일 (sprint13, 13 passed)**:
- test_init_agent_state_client_id.py (CID-01~06)
- test_execution_stage_client_id_propagation.py (EP-01~04)
- test_agent_path_helper_b_e2e.py (E2E-01~03, helper-B DataSource 위임 검증)

### 0.3 작업 ⑬ 死코드 cleanup (recent ①.x batch 마무리)

| 폐기 | 줄 수 | 사유 |
|---|---:|---|
| executor.py:259-403 `class Executor` | 147 | Grep 활성 `Executor()` 0 hit (`_old/`·`_domains/` 만 매치). 활성 entry = `execute_phase` |
| ws_agent.py:687-1037 `_run_agent` | 351 | frontend `type:'start'` 송신 0 hit. legacy Sprint 12 진입점, Sprint 13 query/resume_query 로 대체 |
| ws_agent.py:658-661 `elif msg_type == "start"` 분기 | 4 | _run_agent 호출 유일 사용처 |
| ws_agent.py:5·103·603 docstring legacy 'start' 언급 | 3 | 정리 |
| test_ws_agent_query_routing_unit.py WQ-07 | 25 | 폐기된 _run_agent 의존 |
| **합** | **~530** | 사용자 원칙 [死코드 즉시 폐기] 정합 |

---

## 1. 검증 baseline (작업 ⑬ 종료 시점, 불변)

### 1.1 회귀 baseline

| 영역 | baseline | 검증 명령 (Bash, cwd=backend) |
|---|---|---|
| sprint13+14 분석 team | 275 passed / 11 failed (HITL) / 2 skipped | `uv run pytest tests/sprint13 tests/sprint14 -q` |
| dashboard1 영역 | 303 passed / 3 failed (pyarrow) | `uv run pytest tests/{pipelines,dashboard1,data_sources,workspace,permissions,ml_models} -q` |
| sprint13 신규 (작업 ⑪.F) | 13 passed | `uv run pytest tests/sprint13/test_init_agent_state_client_id.py tests/sprint13/test_execution_stage_client_id_propagation.py tests/sprint13/test_agent_path_helper_b_e2e.py -v` |
| sprint15 broken | **17 passed / 54 failed** (작업 ⑫ 대상) | `uv run pytest tests/sprint15 -q` |
| frontend type-check | exit 0 | `cd ../frontend && pnpm exec tsc --noEmit` |

### 1.2 통합 회귀 (작업 ⑬ 후)

```bash
# 전체 + sprint13 신규 (작업 ⑪+⑬ 후 baseline)
uv run pytest tests/sprint13 tests/sprint14 tests/pipelines tests/dashboard1 \
              tests/data_sources tests/workspace tests/permissions tests/ml_models -q
# 기대: 590 passed / 14 failed (11 HITL + 3 pyarrow) / 2 skipped
#       작업 ⑪.F 신규 13 - 작업 ⑬.2 WQ-07 폐기 1 = +12 → 578 (v4 baseline) + 12 = 590
```

### 1.3 agent path helper-B smoke (활성화 검증)

```bash
# 90 tool 8 카테고리 (불변)
cd backend && uv run python -c "
from app.dream_agent.tools.registry import get_registry
from collections import Counter
reg = get_registry(); reg.load()
print(Counter(str(t.category.value) for t in reg.get_all()))
print('total:', len(reg.get_all()))
"
# 기대: collection 27, normalization 6, cleaning 3, preprocessing 1,
#       metrics 35, comparison 7, analysis 9, report 2, total 90
```

---

## 2. 다음 우선순위 옵션

### 2.1 권장 옵션 (작업 ⑪+⑬ 후)

| # | 옵션 | 작업 | 분량 |
|---|---|---|---|
| **(가)** | **작업 ⑫ sprint15 broken 정리** | 6 collector 폐기/skip vs 재구현 분기 결정. 별 계획서 (작업 ⑤·⑨·⑪ 패턴) | 中~大 |
| **(나)** | 작업 ②.2 catalog 단일화 (team_catalog ↔ ToolRegistry dual-source drift 해소) | 52 invisible tool Planner LLM 노출 | 中 |
| **(다)** | 65_dashboard_pages_v1.0 정합 (5 곳 outdated, 작업 ⑩-나 발견) | 활성 spec 정합 | 中 |
| **(라)** | 멈춤 + 사용자 다른 우선순위 | — | — |

### 2.2 전문가 권장

- **(가) 작업 ⑫ sprint15** = 사용자 명시 잔존 우선순위 (v4 §7.1). 본질 진단 후 ⑪ 완료로 의존 정리됨 (병렬 가능 박제). 6 collector 폐기 시나리오 = 단순.
- (나) catalog 단일화 = 본질 진단 Q1 핵심 해소, recent ①.x batch 외 작업 (별 ②.2).
- (다) = 작은 갱신 (5 곳).

사용자 결정 대기.

---

## 3. 참조 문서

### 3.1 계획서 (작업 ⑪ 적대적 검증 패턴 박제)

| 계획서 | 패턴 |
|---|---|
| [계획_작업⑤_32문서_§4-§9_정합_2026-05-31.md](./계획_작업⑤_32문서_§4-§9_정합_2026-05-31.md) | 작업 ⑤ — 1·2·3차 적대적 검증 |
| [계획_작업⑨_41+40_변경hub_정합_2026-05-31.md](./계획_작업⑨_41+40_변경hub_정합_2026-05-31.md) | 작업 ⑨ — 1·2차 |
| [계획_작업⑪_client_id_agent_흐름복구_2026-05-31.md](./계획_작업⑪_client_id_agent_흐름복구_2026-05-31.md) | **작업 ⑪ — 1·2차 + v1→v2→v3, ROI 한계 3차 우회** |

### 3.2 박제 위치 (작업 ⑪ 후 갱신)

| 위치 | 갱신 내용 |
|---|---|
| backend/app/dream_agent/states/agent_state.py | client_id 필드 + init_agent_state 파라미터 |
| backend/app/dream_agent/execution/execution_stage.py:175 | ExecutionContext(client_id=state.get(...)) |
| backend/api_v2/ws_agent.py:168·238 | init_agent_state(client_id=payload.get(...)) (2 곳) |
| frontend/src/api/ws.ts:122 | sendQuery({clientId}) |
| frontend/src/features/agent/SideChatPanel.tsx:71 | useCurrentClient + disabled 가드 |
| docs/agent_specs/21_WEBSOCKET_PROTOCOL_v1.5.md §2.1 | query schema client_id 박제 |
| docs/agent_specs/11_main_graph_state_v1.5.md §2.0 | client_id 행 + Writer/Reader |

### 3.3 이전 recovery (시간순)

| 문서 | 시점 |
|---|---|
| [v5 (2026-05-31, 작업 ⑪+⑬)](session_compact_recovery_2026-05-31_v5.md) | 본 문서 |
| [v4 (2026-05-31, 작업 ④~⑩)](session_compact_recovery_2026-05-31_v4.md) | 박제 사슬 9 곳 완성 |
| [v3 (2026-05-31, 작업 ⑦까지)](session_compact_recovery_2026-05-31_v3.md) | 작업 ④·⑤·⑥·⑦ |
| [v2 (2026-05-30, 작업 ③+④ 진입)](session_compact_recovery_2026-05-30_v2.md) | 작업 ④ 진입 |
| [v1 (2026-05-30, 작업 ② 마무리)](session_compact_recovery_2026-05-30.md) | 작업 ② contract A |

---

## 4. compact 후 첫 행동 (권장)

1. **★ 이어가기 정독** (본 문서 최상단).
2. **§0 본질 진단 + 작업 ⑪·⑬ 박제 정독** — Q3 해소 + 死코드 폐기 박제.
3. **§1.2 회귀 명령 실행** (안전 진입):
   ```bash
   cd backend && uv run pytest tests/sprint13 tests/sprint14 -q
   # 기대: 287 passed (275 + 13 신규 - 1 WQ07 폐기) / 11 failed (HITL) / 2 skipped
   ```
4. **§2.2 권장 우선순위** = **(가) 작업 ⑫ sprint15 broken 정리** (사용자 명시 잔존).
5. 진입 시 §5 함정 + §6 진입 안전 준수.

---

## 5. 함정·교훈 (작업 ⑪·⑬ 추가)

(v4 §5 14 항목 + 작업 ⑪·⑬ 신규)

15. **agent path 死코드 폐기 = legacy 테스트 동반 폐기** — _run_agent 폐기 시 test_WQ07_legacy_start_still_works 도 함께 폐기 필요 (의도된 회귀, baseline 변동 0 유지).
16. **계획서 v1→v2→v3 ROI 곡선** — 작업 ⑪ = 1차 minor_fix (16 항목) → 2차 minor_fix_then_proceed (9 항목, 3차 우회) → v3 즉시 commit 진입. 작업 ⑤·⑨ 패턴 정합.
17. **frontend showToast 가공 함수 주의** — agent 가 박제 시 비실존 helper 함수 추정 가능. spot-check = `Grep 함수명 frontend/src` 필수. 본 ⑪ = `sonner` 라이브러리 정합 정정 (2차 검증 must 1).
18. **Checkpointer resume 자동 흡수** — `if not resume_only:` 분기로 astream skip → init_agent_state state 미주입 → Checkpointer 가 직전 turn 보존. resume 별 단계 commit 불요 (단계 A 자동 흡수).
19. **TypedDict total=False + state.get 컨벤션** — 직접 인덱싱 `state["client_id"]` 금지 (sprint16+ 신규 노드 KeyError 함정). 박제 코멘트로 예방.
20. **death test = 死코드 폐기 시 동반 폐기** — Grep 검증 후 진입.

---

## 6. 진입 안전 (compact 후 작업 ⑫ 진입 시)

- 작업 진입 전 골든 baseline 확인 (590/14/2 + sprint15 17/54).
- ONE 변경 원칙: 한 turn = 한 의미 단위 commit.
- 큰 결정만 surface, 작은 진행 자명.
- 死코드 즉시 폐기 (사용자 원칙).
- 큰 작업 = 계획서 → 1·2차 적대적 검증 → 사용자 승인 → 진입 (작업 ⑤·⑨·⑪ 패턴).
- 사용자 = 비전공자, 직설 전문가 단일 권장 (옵션 surface 자제, default 미제공 시).
- workflow tool 적극 활용 (ultracode 모드).
- 변경 작업 진입 = [41 v1.1](../agent_specs/41_agent_tool_change_hub_v1.0.md) → [40 v1.1](../agent_specs/40_agent_tool_lifecycle_v1.0.md) 순서.

---

## 7. 작업 ⑫ 진입 (사용자 명시 잔존, v4 §7.1 + ⑪ v3 §6.5)

### 7.1 작업 ⑫ sprint15 broken collector 정리

**대상**: `backend/tests/sprint15/*` (17 passed / 54 failed broken baseline)

**1차 검증 결과 (작업 ⑪ 진행 중 발견)**:
- sprint15 broken 6 collector (meta·kakao·naver_sa·naver_gfa·google_ads·review_collector) = `load_mock_csv(data/mock/*.csv)` 직접 호출
- `data/mock/` 디렉토리 폐기됨 (2026-05-28 박제) → FileNotFoundError 동일 stacktrace 54건
- client_id 무관 (helper-B 패턴 아님)
- 33_collection.md L46-50 에 이미 "deprecated/broken" spec 박제

**작업 ⑫ 시나리오 분기 (계획서에서 결정)**:
- **(a) 단순 폐기/skip** = 6 collector 폐기 + sprint15 broken test 폐기. ⑪ 무관.
- (b) **재구현 (helper-B 패턴)** = ⑪ 선행 필요 (완료). 신규 collection 카테고리 yaml + tool 구현.

**별 계획서 권장** — 작업 ⑤·⑨·⑪ 패턴 (계획서 → 1·2차 적대적 검증 → 승인 → 진입).

진입 순서:
1. sprint15 broken 6 collector 원인 분석 (이미 작업 ⑪ 진행 중 1차 검증 발견)
2. 시나리오 (a) vs (b) 결정 (별 계획서)
3. 계획서 작성 (`docs/reports/계획_작업⑫_sprint15_broken_정리_YYYY-MM-DD.md`)
4. 1·2차 적대적 검증
5. 사용자 승인 → 단계별 commit

### 7.2 작업 ②.2 catalog 단일화 (별 ONE)

대상: team_catalog.yaml ↔ ToolRegistry 90 tool dual-source drift (본질 진단 Q1).

분량: 中. 옵션 (A) team_catalog 폐기 + ToolRegistry 직접 nav, (B) team_catalog 자동 생성. ⑫ 후 또는 병렬 가능.

### 7.3 65_dashboard_pages 정합 (별 ONE)

대상: docs/agent_specs/65_dashboard_pages_v1.0.md (5 곳 outdated, 작업 ⑩-나 발견).

---

**작성 완료**: 2026-05-31. 본 문서 = 작업 ⑪ + ⑬ 완료 박제. compact 진입 가능.
