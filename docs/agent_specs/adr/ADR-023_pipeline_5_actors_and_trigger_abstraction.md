# ADR-023: Pipeline 5 주체 분리 + Trigger 추상화 + DataSource 진화

## Status

**Accepted** (2026-05-27) — POC v1 구현 전 framing 박제 완료.

## Context

### 1. 사용자 발견 (2026-05-27 토의 누적)

ADR-022 (DataSource / Workspace 관절) 적용 후 *시스템 작동의 *주체* 가 명확하지 않다* 는 발견. 사용자 다중 통찰 누적:

| 시점 | 사용자 통찰 |
|---|---|
| 65 spec §14.6 검토 후 | "agent 와 별도로 백엔드에 *정보 수집·표시* 해주는 *소스코드 작업자* 가 하나 더 필요" |
| Pipeline Runner 합의 후 | "Pipeline maker (chainer/composer) 도 있어야 하지 않나?" |
| Fetch 책임 토의 | "Fetch 는 DataSource 가 해야 하지 않나? Tool = data 요청자 / DataSource +@ = 가져오는 행위자" |
| Pipeline 종류 분리 | "static (정해둔 것) / custom (사용자 Canvas) / agent 요청 — 별도 저장 + 별도 작업 공간" |
| 어디에 구현 질문 | "Pipeline Maker 는 지금 어디에 구현?" |

→ **5 주체 + Trigger 추상화 + DataSource 진화 + SessionWorkspace** 의 통합 framing 필요.

### 2. ADR-022 와의 관계

ADR-022 = *Tool ↔ Data 관절* (P1·P2·P3). 본 ADR = ADR-022 위에 *작동 주체* 의 분리 박제.

| 영역 | ADR-022 | ADR-023 (본) |
|---|---|---|
| Tool ↔ Data | ✅ 분리 | (전제) |
| 작동 주체 | 모호 (agent + direct API 만) | ✅ 5 주체 명시 |
| Pipeline 정의 | 없음 | ✅ YAML DSL |
| Trigger | 암묵 (사용자 호출만) | ✅ 추상화 (button/upload/cron/webhook/agent) |
| Workspace scope | 단일 (공유) | ✅ Shared + Session 분리 |
| Auth 위치 | 미정 | ✅ DataSource 내부 (MVP) |

### 3. 산업 표준 검증

| 패턴 | 본 ADR 의 대응 |
|---|---|
| Airflow DAG + Scheduler + Executor | Pipeline + Maker + Runner |
| Great Expectations / Soda / Pandera | Validator |
| Repository Pattern (Fowler 1996) | DataSource ABC + Adapter 진화 (ADR-022 정합) |
| LangChain Agent / AutoGen sandbox | SessionWorkspace 격리 |
| Anthropic Claude Skills | Agent Maker (추후 토의) |

→ **본 ADR = 산업 표준 패턴의 본 시스템 정합**.

## Decision

### 1. 5 주체 분리

```
1. Agent          — 사용자 질의 처리 (LLM 자율, 대화 기반)
2. Direct API     — 요청-응답 (Workspace cache 우선, lazy compute)
3. Pipeline Maker — Pipeline 정의 작성 (개발자 / Canvas / Agent)
4. Pipeline Runner — Pipeline 실행 (static, 미리 만들어진 것)
5. Validator      — Pipeline 산출물 검산 (schema / 범위 / 정답값)
```

#### 주체별 책임 매트릭스

| 주체 | 입력 | 산출물 | LLM 사용 | 실행 시점 |
|---|---|---|:---:|---|
| Agent | 사용자 질의 | dynamic plan + 응답 | ✅ | 대화 시 |
| Direct API | HTTP 요청 | cache or tool result | ❌ | 요청 시 |
| Pipeline Maker (개발자) | (수동) | YAML in `pipelines/flows/` | ❌ | 사전 |
| Pipeline Maker (Canvas) | 사용자 UI 조작 | YAML in `memory_entries` | ❌ | 사전·사용자별 |
| Pipeline Maker (Agent) ⚠️ | LLM 추론 | dynamic pipeline | ✅ | 실행 시 (= Maker + Runner 통합) |
| Pipeline Runner | Trigger + YAML | Workspace 저장 결과 | ❌ | Trigger 시 |
| Validator | Pipeline 결과 | pass/fail + 오류 | ❌ | Runner 직후 |

### 2. Pipeline DSL — YAML 포맷

3 Maker 공통 산출물:

```yaml
# 예시: pipelines/flows/dashboard1_demo.yaml
name: dashboard1_demo
client: clumi          # 또는 ${client} (실행 시 주입)
period: ${period}
trigger:
  type: manual         # manual | upload | cron | webhook | agent
  cron: null
steps:
  - id: orders_load
    tool: orders_collector
    inputs: {client: ${client}}
    outputs: {raw_orders: data_source}

  - id: revenue_compute
    tool: RevenueTotal
    inputs: {client: ${client}, period: ${period}}
    outputs: {result: ./computed/S001_revenue_total_${period}.json}
    depends_on: [orders_load]

validator:
  - schema: RevenueOutput
  - expected: {value_min: 0, value_max: 1e10}
```

→ **3 Maker 모두 이 포맷 출력**. Runner 는 *어디서 왔든* 같은 방식 실행.

### 3. Trigger 추상화

```
Trigger 종류 (주체만 다름)              → 같은 Pipeline.run() 호출
─────────────────────────────             ──────────────────────────
[POC v1]  버튼 클릭 (mock 자동화)         \
[POC v2]  Canvas → 실행 버튼              ├── 같은 Pipeline
[MVP-1]   사용자 파일 업로드               │   같은 Runner
[MVP-2]   cron 스케줄러                   │   같은 Workspace
[MVP-3]   webhook (외부 API push)          │   (단, agent 는 Session)
[Prod]    agent 요청                      /
```

→ **Trigger 는 Pipeline 작동에 *영향 X***. 주체만 다름.

### 4. DataSource 진화 (ADR-022 정밀화)

#### POC v1 — 단순 file
```python
class FileDataSource(DataSource):
    def __init__(self, mock_source_dir: Path | None = None):
        self.root = DATA_ROOT
        self.mock_source = mock_source_dir  # data/source/raw/

    def get(self, client, source_id):
        path = self.root / client / "raw" / DEFAULT_MAPPING[source_id]
        if not path.exists() and self.mock_source:
            self._copy_from_mock(client, source_id, path)
        return self._load(path)
```

#### MVP — API 어댑터 진화
```python
class ApiDataSource(DataSource):
    def __init__(self, api_clients: dict, auth_manager: AuthManager):
        self.api_clients = api_clients
        self.auth = auth_manager

    def get(self, client, source_id):
        if not self._raw_exists(client, source_id):
            token = self.auth.get_token(client, source_id)
            data = self.api_clients[source_id].fetch(client, token)
            self._save_raw(client, source_id, data)
        return self._load(...)
```

#### *3단 분리* (사용자 의도) = DataSource 내부

```
사용자 표현 → 실제 책임 (MVP DataSource 내부)
─────────────────────────────────────────────
1. 요청   → Tool → DataSource.get() 호출
2. 가져오기 → AuthManager → ApiClient → ExternalAPI → response
3. 저장   → RateLimiter → SchemaValidator → RawSaver → file/DB
```

→ **Collector 변경 0** (영구). DataSource *adapter 만* 교체.

### 5. Workspace 분리 — Shared vs Session

```python
class WorkspaceBackend(ABC):
    def save(self, layer, key, data, scope: str | None = None): ...
    def load(self, layer, key, scope: str | None = None): ...
```

#### SharedWorkspace (현 — Maker 1·2)
- 위치: `data/{client}/cleaned/`, `data/{client}/computed/`
- 사용: Pipeline 결과 공유. 모든 사용자 접근.

#### SessionWorkspace (신규 — Maker 3 = Agent) ⭐
- 위치: `data/{client}/agent_sessions/{session_id}/cleaned/`, `.../computed/`
- 사용: agent 의 one-off 분석 격리
- Lifecycle:
  - 생성: agent 요청 시
  - 만료: session 종료 또는 TTL (예: 24h)
  - cleanup: 만료 시 archive 또는 삭제
- 격리 이유:
  - 공유 cache 오염 방지
  - 사용자 간 data leakage 방지
  - 재현성 (pipeline.yaml 함께 저장)

```
data/{client}/
├── raw/                  공유 (수집된 원본)
├── cleaned/              공유 (Maker 1·2)
├── computed/             공유 (Maker 1·2)
└── agent_sessions/       Session scope (Maker 3)
    └── {session_id}/
        ├── cleaned/
        ├── computed/
        └── pipeline.yaml  ← agent 가 생성한 pipeline (재현용)
```

### 6. 3 Maker × 3 위치 매핑 (POC v1 시점)

| Maker | 위치 | 산출물 저장 | POC v1 | POC v2 | MVP+ |
|---|---|---|:---:|:---:|:---:|
| **1. 개발자 코드** | (IDE 작성) | `backend/app/pipelines/flows/*.yaml` | ✅ 활성 | ✅ | ✅ |
| **2. Workflow Canvas** | `frontend/src/features/workflow/` ([62 spec](../62_workflow_canvas_design_v1.2.md)) | `memory_entries.type='custom_pipeline'` | (있음, 연동 X) | ✅ 활성 | ✅ |
| **3. Agent Maker** ⚠️ | `backend/app/dream_agent/planning/` (Sprint 9) | **Skills 패턴 박제 (구현 추후 토의)** | (있음, pipeline 출력 X) | ⏸️ | ⏸️ |

#### Agent Maker — Skills 박제 (사용자 결정 2026-05-27)

**현 코드 충돌 위험** 인지 → 구현 미정. **Skills 패턴**으로 박제만:

| 항목 | 내용 |
|---|---|
| 책임 | LLM 이 사용자 질의 → dynamic pipeline 생성 + 즉시 실행 (Maker + Runner 통합) |
| 저장 위치 | `dream_agent/planning/` (현 Sprint 9 Planning Layer 의 확장) |
| 결과 격리 | SessionWorkspace 사용 (위 §5) |
| 산업 표준 참조 | **Anthropic Claude Skills** + LangChain Agent + AutoGen orchestrator |
| 충돌 위험 | Planning Layer 의 *기존 3-stage prompt 흐름* 과 *Pipeline DSL 출력* 의 통합 — 어떻게 통합할지 미정 |
| 진입 시점 | **추후 사용자 토의 후 별도 ADR** (ADR-024 가능) |
| POC v1·v2 영향 | ❌ 없음 (Maker 1·2 만 활성) |

→ **본 ADR 에서는 *존재 박제* 만**. 구현은 별도 ADR / sprint 결정.

### 7. POC v1 → POC v2 → MVP 진화

#### POC v1 (현 진입 가능)
- 활성 주체: Agent (기존) + Direct API (기존) + **Maker 1 (개발자) + Runner + Validator (신규)**
- Maker 위치: `backend/app/pipelines/flows/*.yaml` (개발자 IDE 작성)
- Trigger: 버튼 1개 (`POST /api/admin/pipelines/run/{name}`)
- Workspace: SharedWorkspace 만
- DataSource: FileDataSource + `mock_source_dir` 옵션
- Auth: ❌ 미구현

#### POC v2 (Canvas 연동)
- 추가 활성: **Maker 2 (Canvas)**
- 추가 위치: `frontend/src/features/workflow/` ↔ `backend/api_v2/routes/pipelines.py` 신규
- Trigger: + Canvas "▶ 실행" 버튼
- Workspace: SharedWorkspace + 사용자별 cache (선택)

#### MVP-1 (사용자 업로드)
- 추가 활성: Trigger 종류 +업로드
- DataSource: + UploadDataSource

#### MVP-2 (외부 API)
- DataSource: + ApiDataSource + AuthManager
- Trigger: + cron + webhook

#### MVP+ (Agent Maker 활성)
- 추가 활성: **Maker 3 (Agent)** ⚠️ — 별도 ADR 후
- 추가 위치: + `agent_runner.py` + SessionWorkspace 활용

### 8. 어휘 통일

| 단어 | 의미 | 사용 영역 |
|---|---|---|
| **Pipeline** | 한 작업 단위 (정의) | 모든 |
| **Step** | Pipeline 내 단일 tool 호출 | Pipeline 내부 |
| **Tool** | 최소 단위 함수 | 변경 X (collector, cleaner, computer) |
| **Maker** | Pipeline 정의 *작성자* | 3 종 |
| **Runner** | Pipeline *실행자* | static |
| **Validator** | 산출물 *검산자* | Runner 직후 |
| **Trigger** | Pipeline 시작 *주체* | button / upload / cron / webhook / agent |
| **Workspace** | tool 산출물 영속화 | Shared / Session |
| **DataSource** | data 가져오는 행위자 | Repository (ABC) + adapter |

**금지 단어** (혼선 회피):
- ❌ chain / compose / composer / chainer / flow / fetcher
- ❌ "ad_cost_kpi 와 revenue_kpi 별도 tool" (anti-pattern from 65 §14.5)

## Consequences

### 긍정

| 영역 | 효과 |
|---|---|
| 책임 분리 | 5 주체 명확 — 어디에 무엇이 있는지 단일 진실 소스 |
| Trigger 추상화 | POC → MVP → Prod 전환 시 *Pipeline 변경 0* |
| DataSource 진화 | Collector / Pipeline / Workspace *영구 변경 0*. *DataSource 만* 교체 |
| Workspace 분리 | agent 격리 → data leakage 회피 + 재현성 |
| 산업 표준 정합 | Airflow + Great Expectations + Repository + Skills 패턴 |
| 어휘 통일 | chain/compose/fetcher 혼선 종식 |

### 비용

| 영역 | 비용 |
|---|---|
| 신규 영역 | `pipelines/` 폴더 (Pipeline ABC + Runner + Validator + parser) |
| DataSource 옵션 | `mock_source_dir` 1 옵션 추가 (~30 라인) |
| 신규 폴더 | `data/source/raw/{client}/` (POC mock 자산) |
| 신규 endpoint | `POST /api/admin/pipelines/run/{name}` |
| 신규 frontend | "🔄 데이터 분석" 버튼 + progress UI |
| 추정 (POC v1) | ~15h ≈ 2일 |

### 미해결 (별도 ADR 또는 sprint)

| 영역 | 사유 |
|---|---|
| **Agent Maker (Maker 3) 구현** | 사용자 결정 — 현 Planning Layer 와 통합 방법 미정. 별도 ADR (가능 ADR-024) |
| **SessionWorkspace lifecycle** | TTL 정책 / cleanup 트리거 / archive 정책 — POC 부재, MVP 결정 |
| **AuthManager 구현** | MVP-2 (외부 API) 진입 시 별도 ADR |
| **Multi-tenant 권한** | API + DataSource 양쪽 — MVP+ 별도 ADR |
| **외부 API 어댑터 (네이버·메타·구글·카카오)** | Sprint 17+ 별도 계획서 |
| **Pipeline 의존성 그래프 (DAG)** | POC = 선형 (depends_on 만), MVP+ DAG 본격 |

## Alternatives

### A. Pipeline 없이 Direct API 로 lazy compute 만 — *기각*
- 장: 단순
- 단: 첫 사용자 느림, cache miss 폭증, 외부 API rate limit 초과 위험. MVP 불가.

### B. Agent 가 모든 것 처리 (Pipeline 불필요) — *기각*
- 장: 통합
- 단: LLM 비용 폭증, 매번 동적 결정 (재현성 X), Validator 부재

### C. Maker / Runner 통합 (분리 X) — *기각*
- 장: 단순
- 단: Trigger 추상화 + 3 Maker 종류 (개발자/Canvas/Agent) *분리 필요* (정의 시점이 다름)

### D. SessionWorkspace 없이 SharedWorkspace 만 — *기각*
- 장: 단순
- 단: agent 의 one-off 분석이 공유 cache 오염, multi-user data leakage

### E. Pipeline DSL = Python class (YAML 미사용) — *부분 채택 가능*
- 장: 타입 안전, IDE 지원
- 단: Canvas 가 Python 생성 어려움, agent 가 Python 생성 모호
- 결: YAML 권장. Python class 는 *내부 표현* 으로 사용 (parser 가 YAML → Python class)

## Related

| ADR / Spec | 관계 |
|---|---|
| [ADR-022](ADR-022_data_source_workspace_layer_separation.md) | 본 ADR 의 *전제* — Tool ↔ Data 분리 |
| [10 §7.7](../10_system_architecture_v1.9.md) | Data Layer Separation — DataSource 진화 명시 |
| [15 spec](../15_end_to_end_flow_v1.0.md) | Agent 의 end-to-end flow — Maker 3 진입 시 갱신 필요 |
| [62 spec](../62_workflow_canvas_design_v1.2.md) | Workflow Canvas = Maker 2 의 본질 |
| [63 spec §2.3](../63_frontend_backend_contract_v1.0.md) | Direct API 명세 — Runner 의 trigger endpoint 추가 필요 |
| [65 spec §14.6](../65_dashboard_pages_v1.0.md) | Tool chain 매핑 — Pipeline DSL 의 *소스* |

## 변경 이력

| 일자 | 내용 |
|---|---|
| 2026-05-27 | 초안 — Accepted. 사용자 다중 토의 (5 주체 + Trigger + DataSource 진화 + SessionWorkspace + 3 Maker 위치 + Skills 박제) 누적 흡수. POC v1 진입 framing 박제. Agent Maker = Skills 박제 만 (구현 추후 별도 ADR — 사용자 결정). |
