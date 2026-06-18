# 16. Layer Dependency Architecture — 물리 모듈 레이어 의존 구조 (v1.0)

> **위상**: 백엔드 물리 레이어(폴더)의 **의존 방향**을 file:line 근거로 박제하는 단일 권위 문서. 개념 4-Layer 파이프라인(Cognitive→Planning→Execution→Response)은 [10_system_architecture](10_system_architecture_v1.9.md)가, 본 문서는 *모듈 의존 그래프*를 다룬다.
> **근거**: 2026-06-05 코드 전수 import 분석(workflow `wf_d37097fe`, 6 agent) → 직접 grep 검증 → 독립 적대적 에이전트 재검증 → **사용자 설계 확인(매니저=cross-cutting)**. 불변식·위반은 §7 명령으로 재현 가능.
> **결정 근거**: [ADR-022](adr/ADR-022_data_source_workspace_layer_separation.md)(DataSource/Workspace 분리), [ADR-029](adr/ADR-029_folder_naming_principles.md)(폴더 명명).

---

## §1 두 종류 — 레이어 스택 vs cross-cutting 서비스

**(A) 레이어 스택** — 의존은 *하향*만:
```
 top entry      backend/api_v2/              ← 아무도 역참조 안 함 (HTTP/WS route)
                      │ (down)
 orchestration  app/dream_agent/  cognitive → planning → execution → response   (+ system_graph 조립)
                      │ (down)              app/pipelines/ (orchestration 형제·비-agent 실행 entry)
 tool layer     app/dream_agent/tools/
                      │ (down)
 agent data     app/dream_agent/{models, schemas}   (순수 계약)
                      │ (down)
 data layer     app/{data_sources, workspace, schemas}
```
규칙: 스택은 위 → 아래로만 import. 아래 → 위 = 위반. stage↔stage(같은 칸)는 sideways 허용하되 **순환 금지**.

**(B) Cross-cutting 서비스/매니저** (스택 *밖*, 가로지름) — **사용자 설계 의도(2026-06-05 확인)**:
> 매니저는 layer 가 아니라 **목적이 있는 자유로운 기능**이다. *layer 가 필요시 부르고, 매니저끼리도 서로 부른다.* layer 가 기준점, 매니저는 cross-cutting.

| 서비스 | 무엇 |
|---|---|
| `app/core` | logging · config · 순수 데코레이터 |
| `app/dream_agent/llm_manager` | LLM 클라이언트 공장 (`get_llm_client`) |
| `app/ml_models` | 감성/키워드/추천 모델 facade |
| `app/dream_agent/workflow_managers` | HITL · session · callback · todo · learning |

→ 이들에 대한 호출은 **스택 방향 규칙의 대상이 아니다**(서비스는 누구나 부를 수 있음). 단 cross-cutting 도:
- **(a) 순환 금지** — 그래서 V1(core↔workflow_managers 순환)은 진짜 문제였고 해결됨.
- **(b) stage *구현*보다 *계약*(schemas) 의존 선호** — 매니저가 stage 도메인 타입을 쓰는 건 정상이나, 그 타입이 계약 레이어에 있으면 더 깔끔.

---

## §2 검증된 불변식 (4) — 각 grep 0건 (독립 재검증 confirmed)

| # | 불변식 | 재현 grep | 결과 |
|---|---|---|---|
| **I1** | data layer는 agent를 모른다 | `app\.dream_agent` in `app/{data_sources,workspace,schemas}` | **0건** (전부 import도 docstring도 0) |
| **I2** | tool은 orchestration stage를 모른다 | `app\.dream_agent\.(cognitive\|planning\|execution\|response\|system_graph\|states)` in `app/dream_agent/tools` | **0** (단 cross-cutting llm_manager 호출은 별개 = V3) |
| **I3** | agent data(models/schemas)는 순수 계약 | 위 패턴(+`tools`) in `app/dream_agent/{models,schemas}` | **import 0** (models/__init__의 3 매치는 docstring 포인터) |
| **I4** | orchestration stage는 DAG | pipeline 역방향(cognitive→response, planning→execution) import | **0** — 코드 전체 import 순환 **0** (구 V1 순환 2026-06-05 해결) |

→ 핵심 의도(`api_v2 → agent → tool → data`)의 두 불변식(I1·I2)이 **완벽히 holds**. 의외로 깨끗한 레이어드다.

---

## §3 디렉터리 → 레이어/서비스 귀속표

| 디렉터리 | 분류 | 책임 | 비고 |
|---|---|---|---|
| `backend/api_v2/` | 스택: top entry | HTTP/WS route | app 밖. 아무도 역참조 X |
| `app/dream_agent/{cognitive,planning,execution,response}` | 스택: orchestration stage | 4-stage 파이프라인 | system_graph가 조립. stage↔stage 순환 금지 |
| `app/pipelines/` | 스택: orchestration 형제 | 비-agent 선언적 실행 entry | tools/workspace/schemas로 하향 |
| `app/dream_agent/tools/` | 스택: tool layer | 순수기능 도구 | 데이터는 BaseTool.fetch→DataSource only |
| `app/dream_agent/{models,schemas}` | 스택: agent data | Tool I/O 계약 + 레이어 경계 DTO | 순수 Pydantic |
| `app/{data_sources,workspace,schemas}` | 스택: data layer | INPUT 관절 / OUTPUT 저장 / 컬럼 계약 | agent 무지 |
| `app/core` · `llm_manager` · `ml_models` · `workflow_managers` · `states`·`system_graph` | **cross-cutting 서비스/조립** | logging·config / LLM클라 / 모델 / HITL·세션·콜백·learning | 스택 밖 — layer가 부르고 서로 부름(§1B). 순환만 금지 |

---

## §4 의존 점검 (ranked, file:line · cross-cutting 반영)

| 분류 | ID | 내용 | 위치 | 처방/상태 |
|---|---|---|---|---|
| ✅ 해결 | **V1** | (구 🔴 HIGH) foundation↔orchestration **순환**: `core.decorators`(trace_log)↔`workflow_managers.learning_manager`. 순환은 cross-cutting이라도 금지 | (구) core/decorators.py:44,:104 | ✅ trace_log을 learning_manager로 이전 → import 순환 0. 가드 `test_layer_core_purity` |
| ✅ 해결 | **V5** | (구 🟢) **stage↔stage** sideways: responder→`cognitive.intent_shim.DEGRADE_OPS` (둘 다 스택 stage라 진짜 결합) | (구) responder.py:18 | ✅ DEGRADE_OPS→schemas. 가드 `test_layer_stage_independence` |
| 🔵 개선 | **V2** | `app/ml_models`(서비스)→`llm_manager.client`(서비스). §1B상 service→service라 **하드 위반 아님**. 단 ml_models가 agent 클라이언트를 *import*하면 agent 없이 테스트 불가 | ml_models/llm.py:13 | DI(주입)로 개선 — 테스트성·경계. **진행 승인** |
| 🔵 개선 | **V3** | `tools/analysis·report`→`llm_manager.client`. llm_manager=cross-cutting 서비스라 **하드 위반 아님**. 단 **"tool=순수기능"** 원칙상 LLM client 주입이 더 깨끗 | report_writer.py:9, summary_generator.py:9, analysis/llm/insight_extractor.py:13 | DI(ExecutionContext 주입). **진행 승인** |
| 🔵 정상 | **V4** | `workflow_managers.plan_editor`→`planning.planner`(Plan/PlannedTodo). **위반 아님(2026-06-05 정정)**: 매니저는 cross-cutting이라 stage 도메인 타입 사용 정상(§1B). 내가 매니저에 스택 고도를 잘못 부여했던 것 | hitl_manager/plan_editor.py:22 | (선택) `Plan`이 planning·execution·매니저 공용 → 계약(schemas)로 올리면 더 깔끔. 파급 커서 **보류·필요시 논의** |

**정리**: 스택-방향 하드 결합은 V1(순환)·V5(stage↔stage) **둘뿐 — 모두 ✅ 해결**. V2·V3는 cross-cutting 서비스 호출이라 하드 위반은 아니나 **tool 순수성·테스트성**을 위한 DI 개선 대상(승인·진행). V4는 매니저 cross-cutting이라 정상. **전부 작동 영향 0.**

---

## §5 tool 데이터 접근 규칙 (순수성 경계)

- **유일 진입점**: `BaseTool.fetch(source_id, context)` → `self.ds.get(client, source_id)` ([base_tool.py:54-67](../../backend/app/dream_agent/tools/base_tool.py#L54-L67)). client는 `ExecutionContext.client_id`에서만 흐르고 없으면 fail-fast.
- **직접 파일 I/O 예외 2곳**: `tools/registry.py`(catalog YAML=tool 메타) + `tools/collection/_base.py` External collector(`mock_api→raw` 수집, ADR-027).
- `schemas.inputs.load_*()`는 fetch한 DataFrame을 파싱하는 **순수 함수** → 직접 조회 누수 아님.

---

## §6 기존 문서 정합/drift (본 문서가 정정·승격)

| 문서 | 상태 | 관계 |
|---|---|---|
| spec 10 §7.7.1 | current(한 줄) | 의존 방향 구 박제 → 본 §1·§2가 그래프로 승격 |
| spec 10 §7.7.2 (Tool DI 예시) | **폐기 패턴** | `client='clumi' default` → 실제 `self.fetch+context.client_id`(§5) |
| spec 10 §3 / 카운트 | **stale** | "5 agent" → 실제 9 분석 agent·85 tool. structure_map_260605 §3 |
| ADR-022 | current | DataSource/Workspace 분리 = §1 data layer 근거 |
| ADR-029 | partially-stale | 결정한 `normalizers/` 폴더 부재 → 이력 박제 필요 |

**후속(별도)**: spec 10 §7.7.2 DI 예시 교체 + 카운트 정정, ADR-029 `normalizers/` 부재 박제.

---

## §7 재현 (검증 방법 — 동어반복 방지)

```
# I1: 0
rg "app\.dream_agent" backend/app/data_sources backend/app/workspace backend/app/schemas
# I2: 0 (stage import 없음 — llm_manager 는 cross-cutting=별개)
rg "app\.dream_agent\.(cognitive|planning|execution|response|system_graph|states)" backend/app/dream_agent/tools
# I3: import 0 (docstring만 허용)
rg "app\.dream_agent\.(cognitive|planning|execution|response|system_graph|states|tools)" backend/app/dream_agent/models backend/app/dream_agent/schemas
# 순환 가드: core↛agent
rg "(from|import)\s+app\.dream_agent" backend/app/core   # = 0 (V1 해결)
# V2/V3 (개선 대상): cross-cutting 서비스 직접 import
rg "llm_manager" backend/app/ml_models                              # V2
rg "llm_manager|ml_models" backend/app/dream_agent/tools            # V3
```

---

## §8 한 줄

> 백엔드는 `api_v2→agent→tool→data` **스택 하향**을 잘 지키고(I1·I2 grep 0), 그 위에 **cross-cutting 서비스/매니저**(core·llm_manager·ml_models·workflow_managers)가 가로지른다(스택 밖, 순환만 금지). 스택-방향 하드 결합 V1(순환)·V5(stage↔stage)는 ✅ 해결. V2·V3는 하드 위반 아니나 tool 순수성·테스트성 위해 DI 개선(진행). V4는 매니저 cross-cutting이라 정상(정정). 본 문서가 의존-방향 단일 권위(재현 §7).
