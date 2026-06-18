# 40. Agent / Tool Lifecycle — 교체·재구성·버전 변경 운영 가이드

| 항목 | 내용 |
|------|------|
| 담당자 | 도윤 |
| 분류 | 운영 (40대 — Operations) |
| 진행상태 | Active |
| 버전 | **v1.1** |
| 최종 수정일 | 2026-05-31 |
| 독자 | 에이전트/툴을 추가·교체·rename·폐기·재구성하려는 개발자 |
| 관련 spec | [17 Functions → I/O 종단](17_functions_to_io_v1.0.md) · [32 v1.2 Tool 가이드](32_execution_agent_tools_v1.0.md) (카테고리 정의·BaseTool·데이터 흐름) · [33_tools_by_category/](33_tools_by_category/) (90 tool 인벤토리 진실 소스) · [ADR-022 amended](adr/ADR-022_data_source_workspace_layer_separation.md) (DataSource DI + helper-B) · [data/description/mock/ROADMAP](../../data/description/mock/ROADMAP.md) |

> **v1.1 (2026-05-31) 갱신** (작업 ③·④·⑤·⑥·⑦·⑧ 정합 반영):
> - §5.2 신규 — 박제 단일소스 9 곳 enumeration
> - §8 관련 자료 link 갱신 (32 v1.2 + 33/* + ADR-022 + 30·API)
> - §3.A 도입부에 33/* 카테고리별 인벤토리 안내 추가

---

## 0. 본 문서의 역할

> **에이전트OS 는 완성됐다. 그 위의 에이전트/툴/데이터만 바꾸려 할 때 무엇을 손대고 무엇을 안 손대나.**

OctorAD 의 코드는 두 층:
- **OS 층** = 4-Layer + Manager Layer + base_tool 추상 + registry + helpers. **건드리면 안 됨**.
- **콘텐츠 층** = Tool 구현 + YAML 카탈로그 + team_catalog + mock_tools fallback. **자유롭게 교체**.

본 문서가 답하는 6 가지 질문:
1. **OS vs 콘텐츠 경계는 어디인가?** → §1
2. **Tool 1개 추가하려면?** → §3.A
3. **Tool 1개 폐기/rename 하려면?** → §3.B
4. **에이전트 1개 추가/분리/합병 하려면?** → §3.C
5. **데이터 source 를 mock → 실API 로 바꾸려면?** → §3.D
6. **다 지우고 처음부터 (v1 → v2 메이저)** 하려면? → §3.E + §4

---

## 1. 경계 — OS vs 콘텐츠

### 1.1 ✅ OS 층 (절대 건드리지 마)

```
backend/app/dream_agent/
├── cognitive/                  ← Layer 1 (NL → StructuredQuery)
├── planning/                   ← Layer 2 (3-Stage LLM Planner)
├── execution/
│   ├── executor.py             ← _inject_prev_outputs, _run_single_todo
│   ├── agent_pool.py           ← Eager init, get_real_tool
│   └── execution_stage.py
├── response/                   ← Layer 4 (자연어 변환)
├── workflow_managers/          ← Manager Layer (HITL/Session/Callback/Concurrency/Memory/Todo)
├── tools/
│   ├── base_tool.py            ← BaseTool 추상 계약 (모든 Tool 의 부모)
│   ├── registry.py             ← YAML rglob 자동 로드 + import_tool 자동 추론
│   └── shared/helpers.py       ← find_in_previous, load_mock_csv, normalize_channel
├── models/                     ← Pydantic (ToolSpec, ExecutionContext, TodoResult)
├── schemas/                    ← structured_query, execution_result, response_payload
├── states/agent_state.py       ← AgentState TypedDict
├── llm_manager/                ← LLM client + prompt 카탈로그
└── system_graph/               ← LangGraph builder
```

→ 위 영역을 손대면 **모든 Tool 이 영향**. 본 문서의 시나리오 §3 어디에도 위 영역 수정은 없음.

### 1.2 🔄 콘텐츠 층 (자유로운 교체)

```
backend/app/dream_agent/
├── tools/<category>/<name>.py          ← Tool 구현 ⭐
├── tools/catalog/<category>/<name>.yaml ← Tool 메타카드 ⭐
├── planning/catalog/team_catalog.yaml   ← Planner 카탈로그 ⭐
└── execution/mock_tools.py              ← stub Tool fallback

data/mock/*.csv                          ← POC 데이터
data/description/mock/                   ← 데이터 해설
```

→ 위 3 코드 파일 + 데이터 = **전체 교체 가능 영역**. 본 문서의 변경 시나리오는 모두 이 영역.

### 1.3 경계 한 표

| 영역 | 건드림 | 본 문서 §3 시나리오 |
|---|---|---|
| 4-Layer (cognitive/planning/execution/response) | ❌ | (없음 — 절대 X) |
| Manager Layer (workflow_managers/) | ❌ | (없음) |
| base_tool.py / registry.py / helpers.py | ❌ | (없음) |
| models/ / schemas/ / states/ | ❌ | (없음) |
| **tools/<cat>/*.py** | ✅ | A, B, E |
| **tools/catalog/<cat>/*.yaml** | ✅ | A, B, E |
| **planning/catalog/team_catalog.yaml** | ✅ | A, B, C, E |
| **execution/mock_tools.py** | ✅ | A (stub 시), E |
| **data/mock/*.csv** | ✅ | D |
| **data/description/mock/** | ✅ | D (필수 동시) |

---

## 2. 변경 시나리오 5종 한눈

| 시나리오 | 빈도 | 영향 범위 | 작업량 | §|
|---|---|---|---|---|
| **A. Tool 1개 추가** | 자주 | 1 Tool + 1 에이전트 | 0.5~1일 | §3.A |
| **B. Tool 1개 폐기/rename** | 가끔 | 1 Tool + 의존 Tool들 | 0.5일 | §3.B |
| **C. 에이전트 추가/분리/합병** | 드물게 | 1+ 에이전트의 Tool 재배치 | 1일 | §3.C |
| **D. 데이터 source 변경 (mock→실API)** | Sprint 6+ | 매체별 collector + ROADMAP | 매체당 2~3일 | §3.D |
| **E. v1 → v2 메이저 (clean slate)** | 매우 드물게 | 콘텐츠 층 전체 | 2~3 sprint | §3.E + §4 |

---

## 3. 시나리오별 표준 절차

### 3.A — Tool 1개 추가 (가장 빈번)

**의도**: 비전 (예: agent_design) 에 명시된 Tool 1개를 코드로 구현.

> **진입 전 확인** (작업 ④·⑤ 박제):
> - 카테고리 = [33_tools_by_category/](33_tools_by_category/) 8 문서 (진실 소스) 에서 어느 카테고리 결정 (collection/normalization/cleaning/preprocessing/metrics/comparison/analysis/report).
> - BaseTool 패턴 = [ADR-022 amended](adr/ADR-022_data_source_workspace_layer_separation.md) §4 (helper-B `self.fetch(source_id, context)` 사용, client_id fail-fast).
> - YAML status 필드 = 폐기됨 (작업 ⑤). status 박제는 33/* 의 status 컬럼만.

#### Step

| 순 | 작업 | 파일 |
|---|---|---|
| 1 | Tool YAML 메타카드 작성 (status 필드 X) | `tools/catalog/<category>/<name>.yaml` |
| 2 | Tool .py 구현 (BaseTool 상속, `self.fetch()` helper-B) | `tools/<category>/<name>.py` |
| 3 | team_catalog 등록 (해당 agent.tools 배열에 추가) | `planning/catalog/team_catalog.yaml` |
| 4 | (선택) Planner Stage 3 프롬프트 보강 | `llm_manager/prompts/planning_stage3_todo.yaml` |
| 5 | unit + integration 테스트 | `backend/tests/sprint*/` |
| 6 | 33/* 카테고리별 문서에 tool 행 추가 (진실 소스 정합) | `docs/agent_specs/33_tools_by_category/33_<category>.md` |
| 6 | DC-10 Status 마커 3중 정합 검증 | docstring + YAML status + team_catalog status |

#### 핵심 룰
- YAML 경로 `catalog/<cat>/<name>.yaml` ↔ .py 경로 `tools/<cat>/<name>.py` **동일 구조**. registry 가 자동 import (`PascalCase(name)` 클래스명).
- `produces` YAML 키 = 다음 Tool 이 받을 키. 네이밍 통일 필수 ([17 §5.4](17_functions_to_io_v1.0.md)).
- docstring 에 `Status: complete — YYYY-MM-DD 설명` 반드시.

#### Done 기준
- [ ] Planner 가 실제로 이 Tool 을 Todo 에 뽑는지 (integration test)
- [ ] Executor 가 import 해서 실행 성공
- [ ] DC-10 contract test pass

상세 = [17 §7 종단 체크리스트](17_functions_to_io_v1.0.md) + [32 §9 Step-by-Step](32_execution_agent_tools_v1.0.md).

---

### 3.B — Tool 1개 폐기 또는 rename

#### 폐기 — 3 단계 deprecation

| 단계 | 작업 |
|---|---|
| 1. Deprecation 선언 | YAML `status: deprecated` + 폐기 시점 / 대체 Tool 박제. docstring 에도 `Status: deprecated — 폐기 예정 YYYY-MM-DD` |
| 2. 사용처 점검 | `grep "<tool_name>"` — team_catalog / 다른 Tool 의 produces 의존 / 테스트 |
| 3. 마이그레이션 | 의존 Tool 들이 대체 Tool 의 produces 키 사용하도록 변경 |
| 4. 실 삭제 | .py + .yaml + team_catalog 행 삭제 + 의존 테스트 제거 |

#### Rename — 4 단계

| 단계 | 작업 |
|---|---|
| 1. 신규 이름으로 .py + .yaml 작성 (옛 코드 복붙) | 신규 위치 |
| 2. team_catalog 행 갱신 (옛 → 신규) | `team_catalog.yaml` |
| 3. 의존 produces 키 일관성 확인 (rename 이 키 변경 동반?) | 다음 Tool 들 점검 |
| 4. 옛 파일 삭제 | (B 폐기 절차 일부) |

**예시** — `naver_collector` → `review_collector` 일반화 ([Drift D2](../_claude/tool/TOBE_MVP/03_drift_report.md)):
- 입력 변경 — 출처 filter `naver_*` → 전체 (naver/oliveyoung/instagram 등)
- produces 키는 그대로 (`raw_reviews`) → 의존 Tool (format_normalizer) 영향 0
- → **rename + 입력 확장** 패턴

---

### 3.C — 에이전트 추가/분리/합병

**핵심 인사이트**: 에이전트는 `team_catalog.yaml` 의 **논리적 그룹**일 뿐 코드 entity 가 아님. 따라서 에이전트 변경 = team_catalog 만 갱신.

#### 추가 — 신규 에이전트 1개

```yaml
# team_catalog.yaml 일부
analysis_team:
  agents:
    new_agent_name:
      description: "..."
      handles_tasks: [...]
      tools:
        - name: tool_1
          status: stub
          ...
```

→ 코드는 0. 단 Tool 들은 별도 §3.A 절차 따라 작성.

#### 분리 — 기존 에이전트 1개를 2개로

**예시**: `preprocessing_agent` → `text_preprocessing_agent` + `channel_normalizing_agent` (D9 결정)

| 단계 | 작업 |
|---|---|
| 1. team_catalog 에서 옛 agent 의 tools 를 두 신규 agent 로 분배 | `team_catalog.yaml` |
| 2. 옛 agent 항목 삭제 | 동상 |
| 3. Planner Stage 2 프롬프트 갱신 — 새 agent 이름 인지하게 | `llm_manager/prompts/planning_stage2_agent.yaml` |
| 4. handles_tasks 매핑 갱신 (TaskType → agent) | 동상 |
| 5. 테스트 — 새 agent 로 routing 되는지 | integration |

#### 합병 — 2개 에이전트를 1개로

분리 역순.

---

### 3.D — 데이터 source 변경 (mock → 실 API)

상세 = [data/description/mock/ROADMAP](../../data/description/mock/ROADMAP.md). 핵심만:

#### 원칙: API 표면 동결
- `/api/mock/...` 12 endpoint = path / Query params / 응답 schema 동결
- 데이터 source 만 교체 — Frontend / Tool 코드 변경 0

#### Phase 별 진화
| Phase | source | 코드 변화 |
|---|---|---|
| POC (지금) | `data/mock/*.csv` | `mock_data.py` 가 pandas CSV 로드 |
| MVP | 외부 광고 플랫폼 API (Meta/Naver/Kakao/Google + DataLab + 크롤러) | `mock_data.py` 분기 또는 교체 |
| Production | 자체 DB (PostgreSQL/ClickHouse) | DB query + 캐싱 layer |

#### 매체별 전환 절차

| 순 | 작업 | 파일 |
|---|---|---|
| 1 | 외부 API client 작성 (예: `meta_ads_client.py`) | `backend/app/integrations/` (신규) |
| 2 | 환경 변수 추가 (`USE_MOCK_DATA`, `META_ACCESS_TOKEN` 등) | `.env` + `app/core/settings.py` |
| 3 | 해당 collector Tool 내부 분기 (`if settings.USE_MOCK_DATA: ...`) | `tools/collection/<name>.py` |
| 4 | mock vs real fixture 양쪽 회귀 테스트 | `backend/tests/sprint*/` |
| 5 | `data/description/<kind>/` 신설 (예: `data/description/meta_real/`) | 신규 폴더 |
| 6 | ROADMAP.md 갱신 — 해당 매체 "Phase 2 진입" 표기 | `data/description/mock/ROADMAP.md` |
| 7 | rate limit / quota 관제 | `app/integrations/<provider>/limiter.py` |

#### 전환 패턴 (collector 1개당)

```python
class MetaCollector(BaseTool):
    async def execute(self, params, context):
        if settings.USE_MOCK_DATA:
            df = load_mock_csv("mock_data_meta_raw_daily.csv")
        else:
            df = await self._fetch_meta_api(params)
        # 이후 처리는 동일
        ...
```

→ **API 표면 + Tool 인터페이스 = 그대로**. 내부만 교체. 따라서 의존 Tool (`format_normalizer` 등) 영향 0.

---

### 3.E — v1 → v2 메이저 (clean slate)

**전제**: 비전이 옛 코드와 호환 불가할 정도로 다름. 또는 옛 잔재가 새 컨벤션과 충돌. **드문 경우**.

#### 결정 기준

| 옵션 A 점진 교체 | 옵션 B clean slate |
|---|---|
| 옛 Tool 중 50%+ 가 새 비전에 fit | 옛 Tool 의 50%+ 가 폐기 대상 |
| 컨벤션 그대로 유지 | 컨벤션 자체가 변경 |
| 회귀 자산 보존 가치 큼 | 회귀 자산 보존 어려움 |
| 1~2 sprint | 2~3 sprint |

→ **현재 OctorAD = A 적합**. 8 implemented 중 6 그대로 + 2 rename. B 는 정말 새 product 만들 때.

#### B 절차

| 순 | 작업 |
|---|---|
| 1 | **v2 폴더 신설** — `tools/v2/`, `tools/catalog/v2/`, `team_catalog_v2.yaml` (옛 것 그대로 두고 신규 폴더) |
| 2 | **신규 team_catalog_v2 작성** — 모든 Tool `status: stub` |
| 3 | **신규 mock_tools_v2.mock_result()** 분기 채움 |
| 4 | **router 분기** — 환경 변수 또는 turn-id 로 v1/v2 선택 |
| 5 | **v2 Tool 점진 구현** ([3.A 절차] 반복) |
| 6 | **공존 기간 운영** — v1 회귀 유지, v2 새 시나리오 검증 |
| 7 | **cutover** — v2 안정화 후 default 전환 |
| 8 | **v1 폐기** — `tools/v1_legacy/` 로 archive 후 1~2 sprint 후 삭제 |

#### B 가 절대 손대지 말 영역
- OS 층 (4-Layer + Manager + base_tool/registry/helpers)
- models/ / schemas/ / states/ (BaseTool 계약 + AgentState — v2 도 같은 계약 사용)

→ OS 가 바뀌어야 한다면 그건 **v2 아니라 v3** 수준 (그래프 자체 재설계).

---

## 4. 메이저 마이그레이션 패턴 (v1 → v2 일반론)

### 4.1 공존 (Coexistence)

| 단계 | 기간 | 작업 |
|---|---|---|
| 1. Build | 2~4 주 | v2 신규 작성 (v1 유지) |
| 2. Pilot | 1~2 주 | 일부 사용자 / 시나리오만 v2 |
| 3. Cutover | 1 일 | default 를 v2 로 |
| 4. Sunset | 2~4 주 | v1 회귀만 유지 |
| 5. Remove | 1 일 | v1 코드 삭제 |

### 4.2 Deprecation 마커

3 곳 동시:
1. **코드 docstring**: `Status: deprecated — 폐기 예정 YYYY-MM-DD, 대체 = v2/<new>`
2. **YAML**: `status: deprecated`
3. **team_catalog**: 해당 행에 `# DEPRECATED — replaced by v2/<new>` 주석

### 4.3 [v1/v2 섞임 금지](C:/Users/gobok/.claude/projects/c--kdy-Projects-octormate-beta-v001/memory/feedback_no_mixed_codebases.md) 메모리

> 사용자 메모리 원칙: 점진 추가 후 반드시 전환 Sprint. v1 격리 + v2 rename + 한 번에 정리.

→ 공존 기간 길어지면 점점 어디가 v1/v2 인지 헷갈림. **공존 시한 명확 설정** (예: 6주 이내 cutover).

---

## 5. 영향 분석 매트릭스

각 변경 영역이 어디까지 영향을 미치는가:

| 변경 영역 | 영향 받는 곳 |
|---|---|
| `tools/<cat>/<name>.py` 한 파일 | 그 Tool + 의존 Tool (produces 키 변경 시) |
| `tools/catalog/<cat>/<name>.yaml` | Planner 가 보는 메타. parameters / produces 변경 시 다음 Tool 영향 |
| `planning/catalog/team_catalog.yaml` | Planner Stage 1/2 routing 결과 |
| `execution/mock_tools.py` | stub Tool 응답 (POC 데모) |
| `data/mock/*.csv` | 모든 Tool 의 입력. 컬럼 추가 = 안전, 삭제/rename = breaking |
| `llm_manager/prompts/*.yaml` | LLM 결정 영향. Stage 별로 다름 |
| `models/` (Pydantic) | **전 시스템 영향 — 건드리지 마** (OS 층) |
| `base_tool.py` | **모든 Tool 영향 — 건드리지 마** (OS 층) |

### 5.1 변경 비용 색상

| 비용 | 변경 종류 |
|---|---|
| ✅ **무비용** | 신규 Tool 추가, 신규 enum 값 추가, 데이터 행 추가/수정, YAML Optional 추가 |
| 🟡 **중간** | Tool rename, 에이전트 분리/합병, 신규 매체 raw 도입 |
| 🔴 **고비용** | Tool 의 produces 키 rename (의존 chain 영향), 컬럼 삭제, 응답 schema 변경 |
| 🔴🔴 **메이저** | OS 층 변경, v1 → v2 clean slate |

### 5.2 박제 단일소스 9 곳 (+ 메타 1) — 카테고리·구조 변경 시 동기 갱신 필수

작업 ③·④·⑤·⑥·⑦·⑧ (2026-05-30~31) 정합 후 박제 단일소스:

| # | 박제 위치 | 무엇 |
|---|---|---|
| 1 | [`enums.py:29-40`](../../backend/app/dream_agent/models/enums.py) | `ToolCategory` enum (8값) |
| 2 | [`catalog/{8 폴더}/`](../../backend/app/dream_agent/tools/catalog/) | 90 yaml (폴더 = 카테고리 1:1) |
| 3 | [`33_tools_by_category/*`](33_tools_by_category/) | 8 카테고리 인벤토리 + README (진실 소스) |
| 4 | [`32 v1.2`](32_execution_agent_tools_v1.0.md) §2.5·§5·§6·§7·§8·§9·§11 | 카테고리 정의 + BaseTool + 데이터 흐름 |
| 5 | [`_schema.yaml`](../../backend/app/dream_agent/tools/catalog/_schema.yaml) line 20 | catalog 진짜 schema |
| 6 | [`ADR-022 amended §4·§5`](adr/ADR-022_data_source_workspace_layer_separation.md) | DataSource DI + helper-B + client_id fail-fast |
| 7 | [`30_DATA_MODELS:409`](30_DATA_MODELS_v1.1.md) | ToolSpec.category 박제 |
| 8 | [`API_SPEC:834`](../specs/API_SPEC.md) | catalog API filter |
| 9 | [`frontend ToolPalette`](../../frontend/src/features/workflow/ToolPalette.tsx) | `tool.category` 직접 사용 |
| (메타) | [`session_compact v3`](../reports/session_compact_recovery_2026-05-31_v3.md) | 박제 상태 자체 문서화 |

→ 카테고리 추가·rename·폐기 = **9 위치 모두 동기 갱신**. 1 곳 누락 시 silent bug (frontend 와 backend enum mismatch 등).
→ 실 사례 = [계획_작업⑤_32문서_§4-§9_정합](../reports/계획_작업⑤_32문서_§4-§9_정합_2026-05-31.md) (1·2·3차 적대적 검증 루프).

---

## 6. 회귀 테스트 범위 (변경별)

| 변경 | 테스트 범위 |
|---|---|
| 3.A Tool 추가 | 그 Tool unit + Planner 가 뽑는지 integration + DC-10 |
| 3.B Tool 폐기/rename | 그 Tool + 의존 Tool integration + 전체 시나리오 회귀 |
| 3.C 에이전트 추가/분리 | Planner Stage 2 routing 테스트 + 시나리오 회귀 |
| 3.D mock → 실API | mock fixture pass + real fixture pass (둘 다) + 결과 일치 비교 |
| 3.E v1 → v2 | v1 회귀 유지 + v2 신규 시나리오 + cutover 후 default 동작 |

**회귀 명령** (기본):
```bash
pytest backend/tests/sprint13 backend/tests/sprint14 backend/tests/sprint15 -q
pnpm --filter frontend vitest run
```

→ [테스트는 리소스/시간 제약 없이 충분히](C:/Users/gobok/.claude/projects/c--kdy-Projects-octormate-beta-v001/memory/feedback_test_no_resource_limit.md) 메모리 — 단축/skip 제안 X. 변경 모듈 + 인접 모듈 회귀 필수.

---

## 7. 자주 묻는 질문 (FAQ)

### Q1. "지금 만들어진 에이전트를 다 지우고 새로 만들려면?"
→ §3.E (v1 → v2). 단 OS 층은 안 건드리므로 "다 지운다" 도 콘텐츠 층만 (3 파일 + 1 폴더). 시도 전 §1.3 경계 표 확인.

### Q2. "Tool 이름만 바꾸면 코드 어디 손대?"
→ §3.B rename 4 단계. 의존 Tool 의 produces 키 의존 점검 필수.

### Q3. "에이전트 9개 → 10개 추가하려면?"
→ §3.C 추가. team_catalog 만 갱신. 단 신규 에이전트의 Tool 들은 §3.A 별도 작성.

### Q4. "mock 데이터 다 폐기하고 실API 만 쓰려면?"
→ §3.D. 단 mock 보존 권장 — 테스트 / demo / fallback 가치 큼 (ROADMAP §3.5).

### Q5. "OS 코드를 손대야 하는 경우는 언제?"
→ BaseTool 계약 변경 / `_inject_prev_outputs` 룰 변경 / AgentState 스키마 변경. **이건 v3 수준 — 별도 ADR 필요**.

### Q6. "v2 점진 vs clean slate 어느 쪽?"
→ §3.E 결정 기준 표. 옛 Tool 50%+ fit = 점진 (A). 50%+ 폐기 = clean slate (B).

---

## 8. 관련 자료

| 자료 | 본 문서와의 관계 |
|---|---|
| [41 Change Hub v1.1](41_agent_tool_change_hub_v1.0.md) | 본 문서의 진입점 (빠른 시작) — 5 시나리오 한 페이지 결정 + 박제 단일소스 9 곳 |
| [17 Functions → I/O 종단](17_functions_to_io_v1.0.md) | Tool 작성 시 5단계 룰 (§5 I/O 메커니즘) |
| [31 Tool 요구사항](31_execution_agent_function_list_v0.6.md) | 신규 Tool 추가 시 비전 출처 |
| [32 v1.2 Tool 가이드](32_execution_agent_tools_v1.0.md) ⭐ | §2.5 카테고리 8 정의 + §5 BaseTool ADR-022 + §6 YAML + §8 데이터 흐름 (파일명 v1.0 유지, 내용 = v1.2) |
| [33_tools_by_category/](33_tools_by_category/) ⭐ | **현 90 tool 인벤토리 진실 소스** — 8 카테고리 문서 + README, 자주 변경 |
| [ADR-022 amended §4·§5](adr/ADR-022_data_source_workspace_layer_separation.md) ⭐ | DataSource DI 패턴 + helper-B `self.fetch` + client_id fail-fast |
| [30_DATA_MODELS:409](30_DATA_MODELS_v1.1.md) | ToolSpec.category 8 카테고리 박제 |
| [API_SPEC:834](../specs/API_SPEC.md) | catalog API filter 8 카테고리 박제 |
| [enums.py ToolCategory](../../backend/app/dream_agent/models/enums.py) | 8 enum 값 (단일소스 박제 1번) |
| [frontend ToolPalette](../../frontend/src/features/workflow/ToolPalette.tsx) | `tool.category` 직접 사용 (classifyTool 폐기) |
| [data/description/mock/INDEX](../../data/description/mock/INDEX.md) §5.2 | 데이터 변경 시나리오 5종 (본 문서 §3.D 의 깊이) |
| [data/description/mock/ROADMAP](../../data/description/mock/ROADMAP.md) | Phase 별 데이터 source 진화 (§3.D) |
| [tool/TOBE_MVP/01 매트릭스](../../docs/_claude/tool/TOBE_MVP/01_tool_data_matrix.md) | 현 Tool ↔ Data 매핑 (변경 영향 분석) |
| [tool/03 Gap & Roadmap](../../docs/_claude/tool/03_gap_and_roadmap.md) | Phase 0~6 점진 로드맵 |
| [adr/](adr/INDEX.md) | 결정 박제 — 영구 변경은 ADR 작성 |
| [session_compact v3](../reports/session_compact_recovery_2026-05-31_v3.md) | 작업 ④·⑤·⑥·⑦·⑧ 자취 + 다음 세션 진입 |

---

## 9. 변경 정책

| 트리거 | 본 문서 갱신 |
|---|---|
| 신규 변경 시나리오 발생 (예: 신규 LLM provider 도입) | §3 신규 시나리오 추가 |
| OS 층 경계 변경 (드뭄) | §1 갱신 + 별도 ADR |
| 메이저 마이그레이션 패턴 개선 | §4 갱신 |
| 회귀 테스트 명령 변경 | §6 갱신 |

---

## 10. 변경 이력

| 버전 | 날짜 | 변경 |
|------|------|------|
| v1.0 | 2026-05-18 | 초안 — 40대 (Operations) 영역 첫 entry. 5 변경 시나리오 (Tool 추가/폐기/에이전트 재구성/데이터 source/v2 메이저) 표준 절차. OS vs 콘텐츠 경계 §1. 영향 분석 매트릭스 §5. 회귀 테스트 범위 §6. FAQ 6 항목 §7. 17/32/data ROADMAP 와 cross-link. |
