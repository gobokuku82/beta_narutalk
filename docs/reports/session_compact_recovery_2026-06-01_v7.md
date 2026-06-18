# Session Compact 준비 (2026-06-01 v7) — 작업 ⑰·⑳·⑵·⑶·⑷·⑸ 완료, Q1 100% 해소

> v6 = 작업 ⑰ v3 계획 commit 0 직전 ([session_compact_recovery_2026-06-01_v6.md](./session_compact_recovery_2026-06-01_v6.md)).
> v7 = **작업 ⑰ 6 commit + ⑳ atomic + ⑵ Collector 2종류 + ⑶ Archive + ⑷ Param validation + ⑸ v1 폐기/doc-drift 정합 (15 commit) + memory 신 4 정정 1**.

---

## ★ 이어가기 (compact 직후 진입)

### 1분 요약 (v7)

- **Q1 본질 진단 100% 해소** — invisible 76 → 0 누적 자취 (⑭ 22→0 / ⑱ 3→0 / ⑰ 35→0 / ⑳ 17→0).
- **시스템 골격 healthy** — Q1 data/tool 분리 + Q2 pipeline + Q3 FE-BE chain (POC scope) 모두 의도대로 완성.
- **frontend v1 폐기 완료** — ChannelAnalysisPage (마지막 v1) 폐기 + 60번대 spec 정합화 (65/66/63 + 60/61).
- **baseline 불변**: sprint13 단독 **190/0/6** · sprint13+14 통합 **293/11/2** · dashboard1 **303/3 (pyarrow)** · sprint15 **13/0** · pipelines **78/0** · frontend type-check **exit 0** · ToolRegistry **85** · invisible **0** · TaskType **18** · GoalType **6** · Source **17**.

### 본 session 누적 commit (15 + 1)

| # | commit | 작업 |
|---|---|---|
| 1 | `ea26e4e` | ⑰.A client default 12 yaml cleanup |
| 2 | `9e8a984` | ⑰.B TaskType.METRIC_CALCULATION + cognitive.yaml |
| 3 | `850c4ab` | ⑰.C metrics_agent 신설 + Stage 1·2 (5 영역 atomic) |
| 4 | `ee2678d` | ⑰.D Stage 3 분기 + 광고 KPI example (manual smoke 통과) |
| 5 | `ea3c72a` | ⑰.E ADR-027 §3 박제 (metrics drift 100%) |
| 6 | `f4435fa` | **⑳ 잔존 17 등재 — Q1 100% 해소 (invisible 0)** |
| 7 | `4921a63` | ⑵ Collector 2종류 분리 (External/Internal) |
| 8 | `c74f085` | ⑶ Archive 정책 (mtime 자동) |
| 9 | `bb15c90` | ⑷ Param validation 강화 + Pipeline runner 사전 검증 |
| 10 | `fba80fd` | ⑸.A v1 ChannelAnalysisPage + /analysis 폐기 |
| 11 | `d99c5b6` | ⑸.B PagePlaceholder mockCsv prop + orphan pycache 정리 |
| 12 | `220150c` | ⑸.C 65·66·63 spec v2 정합화 (doc-drift 해소) |
| 13 | `a055993` | ⑸.D RefreshButton + periods → `_pipeline/` 공용 utilities |
| 14 | `82786ca` | ⑸.E 60·61 spec 보조 갱신 (라우트 15 + Tech Stack 마커) |
| 15 | `f3e5c90` | 이전 session 계획서 7건 박제 (untracked 정리) |
| (메타) | 현 commit | v7 compact 박제 |

### memory 신 / 정정

| 파일 | 상태 |
|---|---|
| `project_system_health_2026_06_01` | **신** — Q1~Q3 의도 완성, Q4 잔존 |
| `project_collector_two_kinds` | **신** — External 13 + Internal 8 + Archive 정책 |
| `project_data_folder_structure` | **신** — raw/cleaned/computed/description + client 확장 convention + 부실 client = 검증 케이스 |
| `project_skill_definition` | **신** — composable + reusable, **POC 미구현** (유저 데이터 누적 후) |
| `project_mock_data_as_poc_source` | **정정** — `/api/mock` 폐기 박제 유지, **`data/mock_api/` 폴더는 외부 API 시뮬레이터로 살아있음** |
| MEMORY.md | 인덱스 갱신 (24 → 28) |

### compact 후 첫 행동

1. **본 문서 §0~§3 정독** (박제 사슬 + 누적 자취 + 다음 작업 진입 가이드).
2. **§1.2 baseline 정합 명령 1회 실행** (안전 진입).
3. **§2 다음 작업 결정 surface** — 사용자 의향 명시 시 진입.

---

## 0. 박제 단일소스 사슬 + 작업 ⑰~⑸ 박제

### 0.1 박제 단일소스 사슬 (v6 §0.1 + ⑳/⑵/⑶/⑷/⑸ 갱신)

| # | 박제 위치 | 작업 commit |
|---|---|---|
| 1 | `enums.py:29-40` ToolCategory 8값 | `dd9dbd1` |
| 2 | `catalog/{8 폴더}/` 85 yaml | `7f0ee5f`·⑫.A·⑳ |
| 3 | `33_tools_by_category/*` (8 문서) | `aeee54f`·`59bd6af` |
| 4 | `32 v1.2` §2.5·§5·§6·§7·§8·§9·§11 | `aeee54f`~`b534ec6` |
| 5 | `_schema.yaml` line 20 | `58c8228` |
| 6 | `ADR-022 amended` §4·§5 | `19c0ac9` |
| 7 | `30_DATA_MODELS:409` | `75cc921` |
| 8 | `API_SPEC:834` | `75cc921` |
| 9 | `frontend ToolPalette` | `7f0ee5f` |
| 10 (⑪) | `AgentState client_id` + frontend useCurrentClient | `5dbc26e`·`65bfd16` |
| 11 (⑭) | team_catalog 신 21 + cognitive.yaml Source 17 | `f35e8d2`·`8d9e8b7` |
| 12 (⑱) | cleaning_agent 3 등재 | `76b4996` |
| 13 (⑰) | metrics_agent 35 등재 + TaskType.METRIC_CALCULATION + Stage 1·2·3 | `850c4ab`·`9e8a984`·`ee2678d` |
| 14 (⑳) | **analysis_agent 18 + channel_normalizing 6 (잔존 17 등재) + Q1 100% 해소 박제** | `f4435fa` |
| 15 (⑵·⑶) | ExternalRawCollectorBase + InternalRawCollectorBase + Archive 정책 | `4921a63`·`c74f085` |
| 16 (⑷) | BaseTool.validate_params + Pipeline runner 사전 검증 | `bb15c90` |
| 17 (⑸) | 60번대 spec v2 정합화 + frontend v1 폐기 + _pipeline/ 분리 | `fba80fd`~`82786ca` |
| (메타) | `session_compact_recovery_2026-06-01_v7.md` (본 문서) | 현 commit |

### 0.2 Q1 본질 진단 정량 자취

| 시점 | invisible | 해소율 | 박제 |
|---|---:|---:|---|
| 작업 ⑫.D 후 (진단 시점) | 76 | 0% | 본질 진단 |
| 작업 ⑭ 후 (collection 22→0) | 55 | 27.6% | `c826af2` |
| 작업 ⑱ 후 (cleaning 3→0) | 52 | 31.6% | `43a7501` |
| 작업 ⑰ 후 (metrics 35→0) | 17 | 77.6% | `ea3c72a` |
| **작업 ⑳ 후 (잔존 17→0)** | **0** | **100% ✓** | `f4435fa` |

### 0.3 본 session 본질 자취 (4 영역)

- **데이터 거버넌스**: External/Internal collector 분리 + mtime 기반 archive 정책 (사용자 의도 정합)
- **silent failure 차단**: Param validation 사전 검증 (BaseTool + Pipeline runner)
- **v1 폐기 완료**: ChannelAnalysisPage 폐기 + 60번대 spec doc-drift 정합화
- **시스템 골격 의도 정합 박제**: memory `project_system_health_2026_06_01` + Q1~Q3 healthy

---

## 1. 검증 baseline (불변, 작업 ⑸ 종료 시점)

### 1.1 회귀 baseline

| 영역 | baseline | 검증 명령 (cwd=backend 또는 frontend) |
|---|---|---|
| sprint13 단독 | **190 passed / 0 failed / 6 deselected** | `cd backend && uv run pytest tests/sprint13 -q` |
| sprint14 단독 | 103 passed / 11 failed (HITL) / 2 skipped / 11 deselected | `cd backend && uv run pytest tests/sprint14 -q` |
| sprint13+14 통합 | **293 passed / 11 failed (HITL) / 2 skipped / 17 deselected** | `cd backend && uv run pytest tests/sprint13 tests/sprint14 -q` |
| dashboard1 영역 | **303 passed / 3 failed (pyarrow)** | `cd backend && uv run pytest tests/{pipelines,dashboard1,data_sources,workspace,permissions,ml_models} -q` |
| pipelines (단독) | **78 passed / 0 failed** | `cd backend && uv run pytest tests/pipelines -q` |
| sprint15 | **13 passed / 0 failed** | `cd backend && uv run pytest tests/sprint15 -q` |
| frontend type-check | exit 0 | `cd frontend && pnpm exec tsc --noEmit` |

### 1.2 정합 검증 명령

```bash
# 1. baseline enum + Q1 invisible 0
cd backend && uv run python -c "
from app.dream_agent.schemas.structured_query import TaskType, Source, GoalType
from app.dream_agent.tools.registry import get_registry
from app.dream_agent.planning.planner import _load_catalog
reg = get_registry(); reg.load()
cat = _load_catalog()
agents = cat['teams']['analysis_team']['agents']
all_cat = set()
for a in agents.values():
    for t in a.get('tools', []): all_cat.add(t['name'])
all_reg = {t.name for t in reg.get_all()}
inv = all_reg - all_cat
print(f'TaskType:{len(TaskType)} Source:{len(Source)} GoalType:{len(GoalType)}')
print(f'ToolRegistry:{len(all_reg)} invisible:{len(inv)}')
print(f'analysis_agent:{len(agents[\"analysis_agent\"][\"tools\"])} channel_normalizing:{len(agents[\"channel_normalizing_agent\"][\"tools\"])} metrics_agent:{len(agents[\"metrics_agent\"][\"tools\"])}')
# 기대: TaskType 18 / Source 17 / GoalType 6 / ToolRegistry 85 / invisible 0 / analysis 18 / channel_normalizing 6 / metrics 35
"

# 2. Collector 2종류 분리 검증
cd backend && uv run python -c "
from app.dream_agent.tools.collection._base import (
    RawCollectorBase, InternalRawCollectorBase, ExternalRawCollectorBase
)
from app.dream_agent.tools.registry import get_registry
reg = get_registry(); reg.load()
ext_cls = reg.import_tool('meta_ads_performance_collector')
int_cls = reg.import_tool('orders_collector')
print(f'ext_cls MRO[1]: {ext_cls.__mro__[1].__name__}')  # 기대: ExternalRawCollectorBase
print(f'int_cls MRO[1]: {int_cls.__mro__[1].__name__}')  # 기대: InternalRawCollectorBase
"

# 3. frontend type-check
cd frontend && pnpm exec tsc --noEmit && echo 'exit 0'

# 4. v1 잔존 0
grep -rn "useMockData\|useMock\b\|/api/mock/" frontend/src 2>/dev/null | grep -v node_modules | head -5  # 기대: 잔존 import 0, 주석/박제만
```

---

## 2. 다음 작업 후보 + 권장

### 2.1 권장 옵션 (작업 ⑸ 종료 직후)

| # | 옵션 | 비용 | 가치 |
|---|---|---|---|
| **(가)** | **5 v2 page 실 화면 manual smoke** (dev server + browser) | 2~3시간 | Q4 본질 (project_core_value_data_transformation 정합) — 진단 완료 vs 실 작동 시각 검증 |
| (나) | Step 2: ws_agent → Dashboard 자동 갱신 이벤트 (chat agent path 본질) | ~1일 | UX 미완성 (사용자 의도 = chat path 직접 검증 가능) |
| (다) | Step 3: Tool 실패 retry + timeout (exponential backoff + asyncio.timeout 30s) | ~2일 | POC 신뢰성 (Top 3 디버깅 잔존) |
| (라) | 트리거 조정 옵션 결정 (A 환경변수 / B Context / D manual endpoint) | 5분 결정 + 1 commit | 사용자 "더 생각" 보류 상태 |
| (마) | 61 §1.5 WSMessage schema sprint 21 재동기화 (P1 [MED]) | 1시간 | Phase E 후속, doc-drift 정정 |
| (바) | LLM observability (token/latency/cost) — client.py usage 로깅 | ~3시간 | Top 3 고도화 |

### 2.2 전문가 단일 권장 = **(가) 5 v2 page 실 화면 manual smoke**

이유:
- 시스템 골격 healthy 박제 + 60번대 spec 정합화 완료 = 코드 진단 충분
- 진짜 모르는 것 = 실 화면 UX (memory `project_core_value_data_transformation` = 차트 = 증명)
- 비용 작음 (2~3시간), 가치 큼 (UI 결함 사전 감지)
- 사용자 비전공자 + 직접 평가 가능 (Claude 주도 vs 사용자 협업 균형)

### 2.3 사용자 결정 보류 2건 (재진입 시 surface)

1. **트리거 조정 옵션** (A/B/D) — "더 생각해야 함" 명시
2. **skill 구현 시점** — POC 미구현, 유저 데이터 누적 후 진입

---

## 3. 시스템 상태 박제 (v7 진단 기반)

### 3.1 Q1~Q3 = ✅ healthy (의도 완성)

| 영역 | 박제 |
|---|---|
| Q1 data/tool 분리 | ADR-022/027 박제, helper-B 패턴, ToolRegistry 85 모두 정합 |
| Q2 pipeline 작동 | 52 yaml + Runner + cache_key + FE 5 page 호출 chain, pipelines 78 test passed |
| Q3 FE-BE-Data chain | clumi 단일 client 완전 작동 (raw/cleaned/computed), 다른 client = 부실 검증 케이스 (의도) |

### 3.2 Q4 잔존 (Top 3 디버깅 중 1 완료, 2 잔존)

| 항목 | 상태 |
|---|---|
| Param validation 사전 검증 | ✅ 완료 (commit `bb15c90`) |
| ws_agent → Dashboard 자동 갱신 | ⚠️ 잔존 (~1일 작업) |
| Tool 실패 retry + timeout | ⚠️ 잔존 (~2일 작업) |
| 5 page 실 화면 시각 검증 | ⚠️ 잔존 (manual smoke) |
| DC-PERM-1~6 CI 테스트 | ⚠️ 잔존 (MVP+ 권장) |

### 3.3 본 session 발견 (잔존 후속 작업)

- **RefreshButton 의 force=false 디자인 gap** (commit 미진행, 사용자 결정 대기): RefreshButton 이 cache 무관 강제 재계산 의도면 `force: true` 전송 필요
- **trigger 조정 옵션** (A 환경변수 / B Context / D manual endpoint): 사용자 보류 상태
- **skill 구현**: POC 미구현 박제, 유저 데이터 누적 후

---

## 4. compact 후 첫 행동 (권장)

1. **★ 이어가기 정독** (본 문서 §0~§3).
2. **§1.2 baseline 정합 명령 1회 실행** (안전 진입).
3. **§2 다음 작업 결정** — 사용자 의향 명시 시 진입.
4. 진입 시 §5 함정 + §6 진입 안전 준수.

---

## 5. 함정·교훈 (작업 ⑰~⑸ 누적)

1. 박제 단일소스 사슬 17 곳 + 메타 = 일관 갱신 필수
2. agent workflow line 박제 오류 → 직접 Read spot-check
3. 검증 ROI 곡선 (1차 高 → 2차 中 → 3차 限)
4. ADR amend 패턴 (Status 박제 + 본문 결정 이력 보존)
5. history vs active 박제 구분
6. _claude/ = .gitignored (local only)
7. broken link 점검
8. 빈 폴더 git rm 자동 폐기
9. workflow agent "계획 미실행 = fail" 오인
10. team_catalog ↔ ToolRegistry dual-source drift = 단계별 해소 패턴 (⑭/⑱/⑰/⑳)
11. **死코드 폐기 신중**: GoalType.METRIC = active (페어 박제 TaskType.METRIC_CALCULATION 정합)
12. **implicit_prerequisites yaml 구조 = list-of-dicts** (dict-mapping X)
13. **frontend grep 명령 정확화**: `/api/tools.*clumi` (실 호출만), `client.*clumi` 는 false-alarm
14. **Phase 분할 = ONE 변경 정합** (⑰ 2a + 2b, ⑸ A/B/C/D/E)
15. **Pattern A/B 라벨 = clumi_methodology 박제 유무** (K/S-code 부수)
16. baseline 표기 통일 — sprint13 단독 (190/0/6) vs sprint13+14 통합 (293/11/2)
17. commit message subject convention (recent ⑭/⑰/⑳/⑵/⑶/⑷/⑸ 패턴)
18. cross-Phase rollback 의존 매트릭스 박제
19. Phase 2a → 2b forward dependency (same session 연속 권장)
20. cognitive.yaml prompt §1 enum + §3 매핑 표 + few-shot 동기 갱신 필수
21. **(⑵) 사용자 의도 부정합 시 즉시 revert** — FileDataSource.get() 자동 fetch lazy 패턴 = ADR-027 권한 위반 → revert + ExternalRawCollectorBase 정식 설계
22. **(⑶) Archive mtime 비교** — 자동 갱신 감지 + 사용자 결정 0 + force flag 0
23. **(⑷) Param validation type 검증** — bool 은 int subclass 분리 (False=0 우회), 알 수 없는 타입 = pass (안전 fallback)
24. **(⑸) v1 폐기 진단 오인** — 진단은 5 v1 페이지 박제 / 실제 1개만 잔존 (4개는 이미 폐기). 코드 spot-check 우선
25. **(⑸) 65 spec §2.1 outdated 발견** — workflow 진단 결과가 outdated spec 기준으로 잘못 (실 코드 spot-check 우선 권장)
26. **(⑸) sed 일괄 변경** — `git mv` + sed import 경로 갱신 (mechanical refactor 패턴)
27. **(본 session) RefreshButton force gap** — 사용자 인식 "data 분석 = F5와 다름" vs 실 코드 = 같음 (force 안 보냄). 사용자 결정 보류
28. **(본 session) skill 정의** = composable + reusable, **POC 미구현** (유저 데이터 누적 후, 사용자 명시)
29. **(본 session) mock_api vs mock data 분리** — `/api/mock` 폐기 박제는 유효 / `data/mock_api/` 폴더는 외부 API 시뮬레이터로 살아있음
30. **(본 session) 사용자 "data 폴더 진실" 인식** — `data/{client}/raw/` 단일 진실 / cleaned·computed = 캐시 (자동 재생성) / mock_api = 외부 시뮬레이터

---

## 6. 진입 안전 (compact 후)

- 작업 진입 전 baseline 확인 (293/11/2 + 303/3 + 78/0 + 13/0 + 85 + invisible 0 + TaskType 18 + GoalType 6 + Source 17)
- ONE 변경 원칙: 한 turn = 한 의미 단위 commit
- 큰 결정만 surface, 작은 진행 자명
- 死코드 즉시 폐기 — 신중 적용 (페어 박제 검증)
- 큰 작업 = 계획서 → 1·2차 적대적 검증 → 사용자 승인 → 진입 (작업 ⑤·⑨·⑪·⑫·⑭·⑰ 패턴)
- 사용자 = 비전공자, 직설 전문가 단일 권장
- workflow tool 적극 활용 (ultracode 모드)
- 변경 작업 = 41 v1.1 → 40 v1.1 순서
- **memory 정정 신중**: 사용자 인식 정정 시 기존 박제 invalidate 가능성 (mock_api 정정 사례)

---

## 7. 다음 작업 진입 가이드 (R0~R6)

> 사용자 의향 명시 시 진입.

### R0 — 5 v2 page 실 화면 manual smoke (권장)

- dev server 진입: `cd frontend && pnpm dev`
- 5 page browser 진입 + clumi 선택 → 차트 작동 확인
- "데이터 분석" 버튼 클릭 → pipeline 실행 + invalidate → 차트 갱신 확인
- 발견 UI 결함 박제 (memory `project_system_health_2026_06_01` Q4 갱신)

### R1 — ws_agent → Dashboard 자동 갱신 (1일)

- BE: callback_manager `agent_complete` 이벤트 + ws_agent broadcast 페이로드 추가
- FE: useAgentWebSocket onMessage 핸들러 → queryClient.invalidate
- 테스트: tests/sprint15/test_ws_refresh_event.py
- 회귀: sprint13+14 + dashboard1 baseline 유지

### R2 — Tool 실패 retry + timeout (2일)

- executor._run_single_todo → _run_with_retry(max=3, timeout=30s)
- exponential backoff (1s/2s/4s)
- SKIPPED_DEPENDENCY 마킹
- ExecutionResult 필드: attempts, last_error
- 테스트: tests/tool_execution/test_tool_retry.py 3 시나리오

### R3 — RefreshButton force gap 해소 (사용자 결정 후)

- frontend/src/api/pipelines.ts L193-196 `force: true` 추가
- 또는 옵션 (default false / 명시 force = true)
- 사용자 의도 "다시 분석" 정합

### R4 — LLM observability (3시간)

- llm_manager/client.py 에 usage(input_tokens/output_tokens/duration_ms) 로깅
- structlog 인프라 활용 (이미 완비)
- `logs/llm_usage.jsonl` + `/api/admin/llm-metrics` endpoint

### R5 — 트리거 조정 결정 (5분 + 1 commit)

- 옵션 A 환경변수 `OCTORAD_AUTO_FETCH` (권장, 1줄)
- 옵션 B Context 필드 `ctx.fetch_external`
- 옵션 D 자동 제거 + manual endpoint

### R6 — skill 구현 (유저 데이터 누적 후, MVP+)

- A composable: Planning Stage 3 명시화
- B reusable: UX 저장/재사용 버튼
- 진입 조건: 다회 사용 패턴 누적

---

**작성 완료**: 2026-06-01. 본 문서 = 작업 ⑰·⑳·⑵·⑶·⑷·⑸ 완료 + Q1 100% 해소 + 60번대 doc-drift 정합화 + memory 5건 갱신. compact 진입 가능.
