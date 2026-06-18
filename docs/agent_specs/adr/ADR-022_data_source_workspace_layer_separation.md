# ADR-022: DataSource / Workspace Layer 분리 — Tool ↔ Data 사이 "관절" 신설

## Status

**Accepted** (2026-05-27) — Sprint 16 13 commits 으로 적용 완료 (ba242c7 ~ f7de6c4).

**Amended** (2026-05-31, 작업 ⑥) — §4 Tool DI 패턴 + §5 ExecutionContext.client_id 갱신:
- helper-B `self.fetch(source_id, context)` 도입 (작업 ②-a)
- POC `"clumi"` default 폐기 — ExecutionContext.client_id fail-fast (workspace 단계 5, commit `4fc3f4f`)
- 46 tool → 90 tool 정합 (작업 ④-L5/L7 commit `dd9dbd1`·`3738be6`)

## Context

### 1. 사용자 도메인 본질 (memory `project_tool_data_agent_separation`)

**P1**: tool = *순수 기능* (data 경로 박힘 X)
**P2**: data 로드 = *별도 source* — "관절"
**P3**: client 동적 분기 (회사 무관 — 어떤 client 이든 같은 tool 적용)

→ 본 ADR 은 P1·P2·P3 의 *구현 결정 박제*.

### 2. as-is — tool 안에 data 경로가 박힘 (2026-05-26 진단)

```python
# 옛 (Sprint 13~15)
class ActiveOrdersFilter(BaseTool):
    async def execute(self, params, state):
        # 직접 호출 — data 경로 박힘
        df = load_clumi_source(5)  # ORDERS_FILE_NO=5 = clumi 회사 전용
        # 회사 분기 X, tool 이 'clumi' 만 안다
```

**문제 3축**:

| 축 | 진단 |
|---|---|
| **결합** | tool ↔ data path 1:1 박힘. 회사 변경 = tool 코드 수정 |
| **다중 client X** | `load_clumi_source` 가 *clumi* 라는 회사 이름을 함수명에 포함 — *blooming* 추가 시 함수 새로 |
| **테스트 어려움** | mock data 주입 = monkeypatch 만 가능. DI 부재 |

### 3. 사용자 질문 (2026-05-26)

> *"tool이 어떤 데이터를 어디에서 가져와야 하는걸 결정하는 부분이 필요한건가?"*

→ tool 은 "*무엇을*" 만 알고, "*어디서*"는 별도. **Repository Pattern** (Martin Fowler 1996) 의 정확한 motivation.

### 4. 3 옵션 검토

| 옵션 | 책임 | 장단 |
|---|---|---|
| **A** | Agent 가 data 위치 결정 → tool 에 주입 | 유연하나 agent 복잡 ↑. POC 단계 over |
| **B** ✅ | Tool 이 "무엇" 결정 + DataSource 가 "어디" 결정 | Repository Pattern 정합. 분리 적당 |
| **C** | 외부 declarative (YAML) 로 매핑 주입 | 추가 layer 1. POC 단계 over. MVP+ 고려 |

→ **B 선택**. P1·P2·P3 와 자연 정합.

### 5. 배치 결정 — `dream_agent/` 안 vs 형제

초기 안: `backend/app/dream_agent/data_sources/` (agent 안)
사용자 발언:
> *"에이전트와 시스템 ( 2개의 서로 다른 주체 ) 가 data를 요청하는거면 dream_agent 폴더와 별도로 models/db/schemas 폴더를 만들어야 하지 않는가?"*

→ **agent + 직접 API 둘 다 공유**해야 함. `dream_agent/` 안에 두면 잘못된 의존 방향.

**결정**: `backend/app/data_sources/` + `backend/app/workspace/` (dream_agent 형제).

## Decision

### 1. 폴더 구조 — Hexagonal (Ports & Adapters) 정합

```
backend/app/
├── data_sources/          ★ INPUT 관절 (Repository Pattern)
│   ├── __init__.py       # get_default_data_source() 헬퍼
│   ├── base.py           # DataSource ABC (Port)
│   └── file.py           # FileDataSource (Adapter — 현 POC)
├── workspace/             ★ OUTPUT 관절 (Tool 결과 영속화)
│   ├── __init__.py       # get_default_workspace()
│   ├── base.py           # WorkspaceBackend ABC
│   └── file.py           # FileWorkspace (Adapter)
├── models/                Pydantic 도메인
├── dream_agent/           Agent 작동 영역
│   ├── tools/             Use Cases (DataSource DI)
│   ├── states/
│   └── ...
└── api_v2/                Direct API (Agent 우회 — frontend 직접 호출)
    └── routes/
        ├── dashboard1.py  /api/dashboard1/* (20 endpoint)
        └── admin.py       /api/admin/catalog · /clients
```

→ `data_sources/` + `workspace/` = *agent + 직접 API* 둘 다 공유하는 **공용 layer**.

### 2. DataSource ABC (Port)

```python
# backend/app/data_sources/base.py
class DataSource(ABC):
    @abstractmethod
    def get(self, client: str, source_id: str) -> pd.DataFrame | dict | list:
        """client + source_id → 원본 데이터.

        Args:
            client: 회사 식별자 (e.g. "clumi", "blooming")
            source_id: 의미 단위 식별자 (e.g. "orders", "meta_ads_performance")
        """

    @abstractmethod
    def list_sources(self, client: str) -> list[str]: ...

    @abstractmethod
    def has(self, client: str, source_id: str) -> bool: ...
```

### 3. FileDataSource (Adapter — POC)

```python
# backend/app/data_sources/file.py
DEFAULT_MAPPING = {
    "meta_ads_performance": "meta_ads_performance.csv",
    "orders": "orders.csv",
    "customers": "customers.csv",
    # ... 21 source_id
}

class FileDataSource(DataSource):
    """data/{client}/raw/{filename} 패턴."""
    def get(self, client, source_id):
        path = self.root / client / "raw" / DEFAULT_MAPPING[source_id]
        # csv/json/jsonl/sql 자동 분기
```

→ MVP 에서 `PostgresDataSource` 추가 시 ABC 동일 유지.

### 4. Tool 의 DataSource DI 패턴 (amended 2026-05-31)

```python
# 신 (작업 ②-a 2026-05-30 helper-B 도입 후)
class ActiveOrdersFilter(BaseTool):
    # BaseTool.__init__ 이 data_source 받아 self.ds 초기화 (base_tool.py:20-27)
    # 자식은 별도 __init__ 불필요 (기본 패턴)

    async def execute(self, params, context):
        merged = self.merge_params(params)
        df = self.fetch("orders", context)               # ← helper-B: client = context.client_id (fail-fast)
        # 또는 직접: df = self.ds.get(context.client_id, "orders")
```

→ **90 tool (collection 27 + normalization 6 + cleaning 3 + preprocessing 1 + metrics 35 + comparison 7 + analysis 9 + report 2) DI 전환** (작업 ④-L5/L7 commit `dd9dbd1`·`3738be6`).
→ Tool 은 `client` 모름 — `self.fetch()` helper 가 context.client_id 만 사용.

### 5. ExecutionContext.client_id (amended 2026-05-31)

```python
# backend/app/dream_agent/models/execution.py
class ExecutionContext(BaseModel):
    session_id: str
    plan_id: str
    client_id: Optional[str] = None    # ← "clumi" default 폐기 (작업 ②-a + workspace 단계 5 commit `4fc3f4f`)
                                       # 진입점(runner/API)이 채운다. 비면 self.fetch() 가 fail-fast.
    # ...
```

→ Frontend TopBar 드롭다운 → Zustand store → API param → ExecutionContext.client_id → `self.fetch(source_id, context)` → DataSource.get(client_id, ...) 까지 *일관 흐름*.
→ `client_id` 비어있으면 `self.fetch()` 에서 `ValueError` raise (fail-fast, base_tool.py:36-41).

### 6. Workspace (OUTPUT)

```python
class WorkspaceBackend(ABC):
    @abstractmethod
    def save(self, layer: str, key: str, data) -> Path: ...
    @abstractmethod
    def load(self, layer: str, key: str) -> dict | list: ...
```

`LAYER_DIR = {"raw": "clumi/raw", "cleaned": "clumi/cleaned", "computed": "clumi/computed"}`

→ tool 의 결과 산출물 (ad_cost_total_*.json, S001_revenue_total_*.json) 영속화.

## Consequences

### 긍정

| 영역 | 효과 |
|---|---|
| **순수성** | tool = 순수 기능. data 경로 박힘 0 |
| **다중 client** | `?client=blooming` 추가만으로 새 회사 지원 (tool 변경 X) |
| **테스트** | `tool = ActiveOrdersFilter(ds=MockDataSource(...))` DI 로 깔끔 |
| **PG 전환 용이** | MVP 에서 `PostgresDataSource` 추가, default 교체. tool 변경 0 |
| **API ↔ Agent 공유** | `/api/dashboard1/*` 와 agent tool 이 같은 DataSource 사용 |

### 비용

| 영역 | 비용 |
|---|---|
| 코드 분량 | 신규 layer 2 (data_sources/ + workspace/) ≈ 6 파일 추가 |
| Tool 변경 분량 | 46 tool DI 전환 ≈ 13 commits (자동 변환 스크립트 `step4_convert_tools.py` 로 일괄) |
| 호환성 | `clumi_loader.py` 의 `load_clumi_source` + `CLUMI_SOURCES` 는 *호환 유지* (별도 작업 시 일괄 rename) |

### 미해결 (호환 유지 영역)

| 영역 | 사유 |
|---|---|
| `clumi_loader.py` 의 `load_clumi_source` 함수명 | grade_system_unifier·missing_value_diagnostic 가 import — 별도 PR rename |
| `data/clumi/` 디렉토리 명 | clumi *회사 이름* — 그대로 정상 (P3 와 정합) |
| `LAYER_DIR = {"raw": "clumi/raw", ...}` | POC — MVP 에서 dynamic client 분리 |

## Alternatives

### A. Agent 가 data 위치 결정 → tool 에 주입

- 장: 가장 유연. Agent 의 추론 결과로 동적 source 결정
- 단: Agent 복잡도 ↑, POC 단계 over. Reasoning step 추가 필요
- 결: **기각** — POC 단계 over engineering

### C. External Declarative (YAML) 로 매핑 주입

- 장: 코드 변경 없이 mapping 변경
- 단: 추가 layer 1, 추가 검증 layer 필요
- 결: **기각 — MVP+ 고려**. POC 는 Python dict (DEFAULT_MAPPING) 로 충분

### D. Singleton DataSource (Module-level instance)

- 장: import 만으로 사용 가능
- 단: DI 어려움, 테스트 시 monkeypatch 필요
- 결: **부분 채택** — `get_default_data_source()` 는 lazy singleton, BUT tool 은 `ds: DataSource | None = None` 로 DI 가능

## Related

| ADR | 관계 |
|---|---|
| **ADR-014** | Tool 단일 책임 분리 패턴 — 본 ADR 의 *전제* |
| **ADR-020** | Computed Metrics Layer — 본 ADR 의 *Workspace OUTPUT* 영역에 자연 흡수 |
| ADR-017 | Analysis Agent 도메인 분리 — 본 ADR 은 *tool 의 data 분리*, ADR-017 은 *agent 의 도메인 분리* |

## 변경 이력

| 일자 | 내용 |
|---|---|
| 2026-05-27 | 초안 — Sprint 16 13 commits (ba242c7 ~ f7de6c4) 적용 완료 후 박제. Accepted (Status). |
| 2026-05-28 | **본문 변경 X (ADR-000 정합)**. [ADR-027](ADR-027_five_actor_permission_separation.md) 신설로 **DataSource 책임 *명시 확장*** — 정규화·schema 매핑·결측 처리·mock 폴백 책임이 ADR-022 의 *암묵 영역* → ADR-027 의 *명시 표* 로 박제. 본 ADR + ADR-027 = *DataSource 의 *최종 framing**. 사용자 통찰 (2026-05-28 R3·R6) 흡수. |

## Commits (Sprint 16)

```
ba242c7  F1   features/clumi → features/dashboard1 + 사이드바 + TopBar 클라이언트 드롭다운
fd8279e  B2   data/clumi/{raw,cleaned,computed}/ sub 폴더 정리
66c5b75  B3a  app/data_sources/ Repository (관절) + 32 PASS
8bcc501  B3b  app/workspace/ + storage.py shim + 9 PASS
4219f8b  B4   25 tool DataSource DI 전환
1627699  B4e  21 collector base DI 전환
49dfed1  B5   API client param + ExecutionContext.client_id
e88e362  F6   useDashboard1Data(client, period) + TopBar store 연동
b17ec8a  ★    routes/clumi.py → routes/dashboard1.py + /api/dashboard1 rename
fee8a19  F7   workflow tool palette (65 tool 카탈로그)
cadc95b  ★    collection clumi_ prefix 제거 (21 collector + base + raw/ 폴더)
f7de6c4  ★    preprocessing/clumi → preprocessing/marketing
c450330  G1   cleaning YAML tags clumi 제거 (3 파일)
```

**검증**: backend pytest cleaning/registry 2 PASS · frontend build SUCCESS · live uvicorn 정답값 17 보존.
