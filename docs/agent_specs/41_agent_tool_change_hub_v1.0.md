# 41. Agent / Tool 변경 작업 — 단일 진입점 (Change Hub)

| 항목 | 내용 |
|------|------|
| 담당자 | 도윤 |
| 분류 | 운영 (40대 — Operations) |
| 진행상태 | Active |
| 버전 | **v1.1** |
| 최종 수정일 | 2026-05-31 |
| 독자 | **실행 에이전트/툴 변경 작업을 시작하는 사람**. 첫 번째로 봐야 할 문서. |
| 짝 문서 | [40 Lifecycle](40_agent_tool_lifecycle_v1.0.md) (상세 절차) ← 본 문서가 진입점, 40 이 깊이 |

> **v1.1 (2026-05-31) 갱신**:
> - §2 박제 단일소스 정리
> - §3 예시 시나리오 표기
> - §4 매트릭스에 spec 30_DATA_MODELS 행 추가
> - §8 link 표 갱신

---

## 0. 본 문서의 역할

> **변경 작업 시 처음부터 끝까지 한 문서만 읽고 작업 가능하게 한다**.
>
> 다른 문서들은 *참조 link 만* 걸어둠. 필요할 때만 들어감.

### 사용자 시나리오

> "카테고리/툴 구조를 재구성하려고 한다. 어디서 시작하지?" *(추상 시나리오 예시 — 현재 tool 카탈로그는 비어 있으며, 카테고리 8값 enum 만 존재)*

→ **본 문서 열기 → §3 변경 종류 결정 → §4 손대는 영역 표 → §5 표준 절차 → 작업**.

여기저기 문서 안 봐도 됨.

---

## 1. ⭐ 절대 손대지 마 — OS 층 (먼저 알아야 할 것)

다음 영역은 변경 작업에서 **건드리지 않음** (어떤 시나리오든):

```
✅ OS 층 (변경 X)
backend/app/dream_agent/
├── cognitive/                    ← Layer 1 (NL → StructuredQuery)
├── planning/                     ← Layer 2 (3-Stage Planner 로직)
├── execution/                    ← Layer 3 (executor, agent_pool)
├── response/                     ← Layer 4 (자연어 변환)
├── workflow_managers/            ← Manager Layer
├── tools/
│   ├── base_tool.py              ← Tool 추상 계약
│   ├── registry.py               ← 자동 import 컨벤션
│   └── shared/helpers.py         ← find_in_previous, helpers
├── models/                       ← Pydantic
├── schemas/
├── states/
├── llm_manager/client.py         ← LLM 호출 인프라
└── system_graph/
```

→ **이 영역 손대야 한다면 v2 메이저 마이그레이션** ([40 §3.E](40_agent_tool_lifecycle_v1.0.md) + 별도 ADR 필요).

상세 = [40 §1 OS vs 콘텐츠 경계](40_agent_tool_lifecycle_v1.0.md).

---

## 2. ⭐ 손대는 영역 — 박제 단일소스

어떤 변경이든 다음 위치만 손댐:

### 2.1 기본 5 영역 (변경 시 거의 항상)

| # | 영역 | 파일 / 폴더 | 무엇 |
|---|---|---|---|
| 1 | **Tool 코드** | [`backend/app/dream_agent/tools/<category>/<name>.py`](../../backend/app/dream_agent/tools/) | Tool 구현 (`class X(BaseTool)`) — BaseTool 부모가 `data_source` DI + `self.fetch(source_id, context)` helper-B 제공 (ADR-022) |
| 2 | **Tool YAML 카탈로그** | [`backend/app/dream_agent/tools/catalog/<category>/<name>.yaml`](../../backend/app/dream_agent/tools/catalog/) | Tool 메타카드 (name·category·description·parameters·produces·timeout·has_cost). 현재 카탈로그 비어 있음. |
| 3 | **Team Catalog** ⭐ | [`backend/app/dream_agent/planning/catalog/team_catalog.yaml`](../../backend/app/dream_agent/planning/catalog/team_catalog.yaml) | Planner 의 진실 소스 (team → agent → tool 계층). |
| 4 | **LLM Prompts** (3 yaml) | [`backend/app/dream_agent/llm_manager/prompts/`](../../backend/app/dream_agent/llm_manager/prompts/) | `planning_stage2_agent.yaml` + `planning_stage3_todo.yaml` + `response.yaml` |
| 5 | **Tests** | 테스트 디렉토리 | 회귀 테스트 |

### 2.2 카테고리 박제 단일소스 (카테고리/구조 변경 시 추가)

| # | 박제 위치 | 무엇 |
|---|---|---|
| 1 | [`enums.py`](../../backend/app/dream_agent/models/enums.py) | `ToolCategory` enum (8값: collection·normalization·cleaning·preprocessing·metrics·comparison·analysis·report) |
| 2 | [`catalog/`](../../backend/app/dream_agent/tools/catalog/) | tool yaml — 폴더 = 카테고리 1:1 (registry 자동 import, 현재 카탈로그 비어 있음) |
| 3 | [`_schema.yaml`](../../backend/app/dream_agent/tools/catalog/_schema.yaml) | catalog 진짜 schema — category 8값 |
| 4 | [`30_DATA_MODELS_v1.1.md`](30_DATA_MODELS_v1.1.md) §6 | ToolSpec.category 주석 (8 카테고리) |
| 5 | [`frontend ToolPalette`](../../frontend/src/features/workflow/ToolPalette.tsx) | `tool.category` 직접 사용 |

> **수정 line 수가 가장 큰 영역 = 3 (team_catalog) + 4 (LLM Prompts)**. 카테고리 변경은 §2.2 의 위치 모두 동기 갱신 필수.

---

## 3. 변경 종류 결정 — 5 시나리오

자신의 변경이 어떤 종류인지 확인 → 해당 시나리오로 (§5 의 절차 따름):

| 종류 | 시나리오 | 빈도 | 작업량 | 상세 |
|---|---|---|---|---|
| **A** | Tool 1개 추가 | 자주 | 0.5~1일 | [40 §3.A](40_agent_tool_lifecycle_v1.0.md) |
| **B** | Tool 폐기/rename | 가끔 | 0.5일 | [40 §3.B](40_agent_tool_lifecycle_v1.0.md) |
| **C** | 에이전트 추가/분리/합병 | 드물게 | 1일 | [40 §3.C](40_agent_tool_lifecycle_v1.0.md) |
| **D** | 데이터 source 변경 (mock → 실API) | Sprint 6+ | source당 2~3일 | [40 §3.D](40_agent_tool_lifecycle_v1.0.md) |
| **E** | 카테고리/에이전트/툴 대규모 재구성 | 매우 드물게 | 1~2 sprint | [40 §3.E](40_agent_tool_lifecycle_v1.0.md) + 본 문서 §6 예시 |

> **표현 예시 — "카테고리/툴 구조 대규모 재구성" = 시나리오 E** *(추상 시나리오)*. 본 문서 §6 참조.

---

## 4. 손대는 영역 — 변경 종류별 매트릭스

각 시나리오에서 §2 의 영역 중 어디 손대는지:

| 영역 | A. Tool 추가 | B. Tool rename | C. 에이전트 변경 | D. 데이터 source | E. 대규모 재구성 |
|---|---|---|---|---|---|
| 1. Tool 코드 (.py) | ✅ 1개 추가 | ✅ rename | — | △ (collector 내부 분기) | ✅ 다수 |
| 2. Tool YAML | ✅ 1개 추가 | ✅ rename | — | — | ✅ 다수 |
| 3. team_catalog ⭐ | ✅ 1행 추가 | ✅ 1행 갱신 | ✅ **다수** | — | ✅ **전면 재작성** |
| 4. LLM Prompts (3 yaml) | △ Stage 3 보강 | ✅ 5+ line | ✅ **다수** | — | ✅ **다수** |
| 5. Tests | ✅ 1 unit | ✅ rename | △ Planner test | ✅ fixture | ✅ 다수 |
| spec 17 (Functions→I/O) | — | — | △ 에이전트 구조 | — | ✅ 갱신 |
| **30_DATA_MODELS** §6 (카테고리 enum 박제 + DataSource DI) | — | — | — | △ DataSource ABC 확장 | ✅ 8 카테고리 갱신 |
| **frontend ToolPalette** | — | — | — | — | ✅ `tool.category` 자동 정합 |
| **_schema.yaml** (catalog 진짜 schema) | — | — | — | — | ✅ category 행 갱신 |

→ **카테고리/에이전트 매핑 변경 (C, E)** 시 → **team_catalog + LLM Prompts 3 yaml + §2.2 박제 단일소스** 동시 갱신이 핵심.

---

## 5. 표준 변경 절차 — 5 Phase (어떤 시나리오든)

```
Phase 1. 영향 범위 측정 (grep)
   ↓
Phase 2. 계획서 작성
   ↓
Phase 3. 검증 (영향 분석 재검토)
   ↓
Phase 4. 작업 진입 (40 §3 의 해당 시나리오 따름)
   ↓
Phase 5. 회귀 + 자동 커밋
```

### Phase 1 — 영향 범위 측정 명령 (grep)

```bash
# 변경 대상 (예: Tool 이름) 의 모든 사용처
grep -rn "<old_name>\|<OldClassName>" backend/ docs/agent_specs/ frontend/src/

# 매핑된 prompt 안 line 수
grep -n "<old_name>" backend/app/dream_agent/llm_manager/prompts/*.yaml

# 의존 테스트
grep -rn "<old_name>" backend/
```

→ 결과를 다음 표에 정리:

| 영역 | 파일 | 변경 line | 비고 |
|---|---|---|---|
| ... | ... | ... | ... |

### Phase 2 — 계획서 작성

변경 계획서를 작성해 영향 파일·line·롤백 절차를 박제.

→ 큰 작업 (시나리오 E) = **계획서 → 1차 적대적 검증 (workflow) → 갱신 → 2차 검증 → 사용자 승인 → 진입** 패턴 권장.

### Phase 3 — 검증 체크리스트

| 체크 | 어떻게 |
|---|---|
| 빠진 영역 없나? | §2 / §4 매트릭스 재확인 |
| LLM Prompts 3 yaml 갱신했나? | grep `<old_name>` `prompts/*.yaml` → 0 결과 |
| Dead code 발견했나? | `planner.py` 가 로드하는 prompt vs 실제 파일 비교 |
| team_catalog `task_agent_hints` 갱신했나? | (변경 종류 C/E 시 누락 흔함) |
| OS 층 안 건드렸나? | §1 영역 git diff 확인 |

### Phase 4 — 작업 진입 (시나리오별)

| 시나리오 | 따라야 할 절차 |
|---|---|
| A | [40 §3.A 6 Step](40_agent_tool_lifecycle_v1.0.md) |
| B | [40 §3.B Rename 4 단계](40_agent_tool_lifecycle_v1.0.md) |
| C | [40 §3.C 추가/분리/합병](40_agent_tool_lifecycle_v1.0.md) |
| D | [40 §3.D + ROADMAP](40_agent_tool_lifecycle_v1.0.md) |
| E | [40 §3.E 절차](40_agent_tool_lifecycle_v1.0.md) + 본 문서 §6 |

### Phase 5 — 회귀 + 자동 커밋

```bash
# 전체 회귀
pytest backend/ -q
pnpm --filter frontend vitest run

# 자동 커밋
git add <변경 파일>
git commit -m "<적절한 메시지>"
```

기대: **회귀 pass + frontend vitest pass**.

---

## 6. 예시 시나리오 — 카테고리/툴 구조 대규모 재구성 *(추상 시나리오, 참고용)*

대규모 재구성 시나리오 (시나리오 E). 가장 큰 변경 유형.

### Step 1 — 변경 결정 박제

- 결정 로그에 결정 신규 추가
- 추가 정보: 옛 카테고리 → 신 카테고리 매핑 표
- ADR 작성 권장

### Step 2 — 영향 범위 측정 (Phase 1)

```bash
# 각 옛 카테고리/툴 명 → grep
for name in tool_old_1 tool_old_2 ...; do
  echo "=== $name ==="
  grep -rn "$name" backend/ docs/agent_specs/
done
```

### Step 3 — 계획서 작성 (Phase 2)

내용:
- 옛 ↔ 신 카테고리/툴 매핑 표
- 영향 파일 + line 수
- Phase별 작업 (A+B 한 commit 권장)
- 회귀 명령
- 롤백 절차

### Step 4 — 작업 진입 (Phase 4)

| 단계 | 파일 |
|---|---|
| 1. team_catalog 전면 재작성 (신 카테고리/툴 구조) | [team_catalog.yaml](../../backend/app/dream_agent/planning/catalog/team_catalog.yaml) |
| 2. LLM Prompts 3 yaml 일괄 갱신 | [planning_stage2_agent.yaml](../../backend/app/dream_agent/llm_manager/prompts/planning_stage2_agent.yaml) + [planning_stage3_todo.yaml](../../backend/app/dream_agent/llm_manager/prompts/planning_stage3_todo.yaml) + [response.yaml](../../backend/app/dream_agent/llm_manager/prompts/response.yaml) |
| 3. Tool 코드 rename/추가/폐기 (시나리오 A/B 절차 반복) | [tools/<cat>/<name>.py](../../backend/app/dream_agent/tools/) |
| 4. Tool YAML 카탈로그 동기 | [tools/catalog/<cat>/<name>.yaml](../../backend/app/dream_agent/tools/catalog/) |
| 5. spec 17 갱신 (에이전트 구조) | [17_*](17_functions_to_io_v1.0.md) |
| 6. spec 30 §6 갱신 (ToolSpec.category 박제) | [30_DATA_MODELS](30_DATA_MODELS_v1.1.md) |
| 7. Tests 갱신 + 회귀 | 테스트 디렉토리 |

### Step 5 — 회귀 + 자동 커밋 (Phase 5)

commit 분리 권장:
1. `feat(planning): 신 카테고리/툴 구조 — team_catalog + LLM Prompts 동기`
2. `refactor(tools): 옛 카테고리 폐기 + 신규 카테고리 Tool 이전`
3. `test: 신 카테고리 회귀 갱신`
4. `docs(spec): 17/30 갱신 — 신 구조 반영`

---

## 7. 자주 묻는 질문 (FAQ)

### Q1. "내 변경이 어떤 시나리오인지 모르겠다"
→ §3 표에서 가장 가까운 행 선택. 모르면 시나리오 E 로 시작 (가장 큰 변경 가정).

### Q2. "OS 층을 손대야 하는 것 같다"
→ ⚠️ 잠시 멈춤. 정말 OS 층인지 §1 영역 재확인. 만약 정말이라면 별도 ADR 필요.

### Q3. "LLM Prompts 갱신을 빠뜨릴까봐 걱정"
→ 항상 다음 grep 으로 확인:
```bash
grep -n "<old_name>" backend/app/dream_agent/llm_manager/prompts/*.yaml
```
→ 0 결과여야 통과. 만약 매칭 line 있으면 빠뜨린 것.

### Q4. "team_catalog 의 task_agent_hints / implicit_prerequisites 가 자주 누락된다"
→ ⚠️ 사실. 본 영역은 §2 본문 외 [team_catalog.yaml L232-265](../../backend/app/dream_agent/planning/catalog/team_catalog.yaml) 위치. 변경 시 반드시 확인.

### Q5. "회귀 일부 실패. 어떻게 대응?"
→ 절대 `--no-verify` 또는 hook skip 안 함. 실패 원인 분석 → 의존 Tool 의 produces 키 불일치 가능성 (5%) / prompt 와 team_catalog mismatch (10%) / Tool 코드 자체 버그 (나머지).

### Q6. "옛 Tool/에이전트 잔재 자동 검출 도구?"
→ 현재 없음. grep 으로 수동. 향후 Contract Test 도입 검토.

---

## 8. ⭐ 핵심 참조 link — 본 문서에서 갈 수 있는 곳

| 무엇 보고 싶나 | 가는 곳 |
|---|---|
| **변경 상세 절차** | [40 Lifecycle](40_agent_tool_lifecycle_v1.0.md) — 5 시나리오 step-by-step |
| **현 에이전트 구조** | [17 Functions → I/O](17_functions_to_io_v1.0.md) §2.2 |
| **Tool 코드 위치 컨벤션** | [17 §5.1 BaseTool 계약](17_functions_to_io_v1.0.md) + [tools/registry.py](../../backend/app/dream_agent/tools/registry.py) + [base_tool.py](../../backend/app/dream_agent/tools/base_tool.py) (ADR-022 정합) |
| **DataSource DI 패턴 (관절)** ⭐ | [30_DATA_MODELS](30_DATA_MODELS_v1.1.md) §7.5 — helper-B `self.fetch(source_id, context)` + client_id fail-fast (ADR-022) |
| **Tool I/O 룰** (params/produces) | [17 §5.2~§5.4](17_functions_to_io_v1.0.md) |
| **ToolCategory enum + 데이터 모델** | [enums.py](../../backend/app/dream_agent/models/enums.py) + [30_DATA_MODELS](30_DATA_MODELS_v1.1.md) §6 |
| **frontend ToolPalette** | [features/workflow/ToolPalette.tsx](../../frontend/src/features/workflow/ToolPalette.tsx) (`tool.category` 직접 사용) |

---

## 9. 본 문서의 갱신 정책

| 트리거 | 본 문서 갱신 |
|---|---|
| 새 시나리오 종류 발견 (예: 신규 prompt 카테고리) | §3 시나리오 표 + §4 매트릭스 |
| OS 층 경계 변경 (드뭄) | §1 |
| Phase 표준 절차 개선 | §5 |
| 새 진입점 spec 등장 | §8 link 추가 |
| FAQ 신규 | §7 |

---

## 변경 이력

> 프레임워크 추출(2026-06-19) 이전(마케팅 도메인 시기)의 상세 변경 이력은 git 히스토리를 참조하세요.
