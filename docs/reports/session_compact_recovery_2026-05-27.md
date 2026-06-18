# Session Compact 준비 (2026-05-27) — Backend 잔존 + agent_specs 업데이트 직전

> compact 직후 이어서 작업 재개. **현 = G1 (cleaning YAML tags clumi 제거) 진입 직전**.

---

## 0. 메타

| 항목 | 내용 |
|---|---|
| 작성일 | 2026-05-27 |
| 위치 | `docs/reports/session_compact_recovery_2026-05-27.md` |
| Compact 시점 | 오늘 12 commits 완료 + 통합 후속 계획서 작성 직후, G1 진입 전 |
| 작업 도메인 | docs/agent_specs 업데이트 + backend 잔존 정리 |
| Branch | main |

---

## 1. 현 작업 한 줄

**오늘 (2026-05-27) 12 commits — 아키텍처 재정렬 (data_sources/workspace) + clumi → dashboard1/marketing/raw rename 완료. 다음 = G1 cleaning YAML tags clumi 제거.**

---

## 2. 즉시 다음 액션 (compact 직후 이 순서)

1. **본 문서 §1·§2 + §4 핵심 결정 읽기**
2. **G1 세부 계획서 정독**: `docs/_claude/architecture/g1_cleaning_tags_2026-05-27.md`
3. **G1 진입** — Step 1·2 (sed + pytest)
   - 자동 커밋: `refactor(cleaning): YAML tags clumi 제거 (3 파일, 회사 이름 → 기능 태그)`
4. **G2** — docs/reports 4 파일 outdated 마커
5. **G3** — docs/agent_specs 업데이트 (ADR-022 + 5 명세) ★ 큰 작업

---

## 3. 오늘 완료된 것 (12 commits)

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
+ B8 docs 정합 (gitignored — 커밋 없음)
```

**검증**: backend 204 PASS · frontend build SUCCESS · live uvicorn 정답값 17 보존.

---

## 4. 핵심 결정 (compact 에서 잃지 말 것)

### 4.1 사용자 P1·P2·P3 원칙 (메모리 박제 = `project_tool_data_agent_separation`)

| # | 원칙 | 구현 |
|---|---|---|
| **P1** | tool = 순수 기능 (data 경로 박힘 X) | 46 tool 모두 `self.ds.get(client, source_id)` |
| **P2** | data 로드 = 별도 source ("관절") | `app/data_sources/` Repository + `app/workspace/` |
| **P3** | client 동적 분기 (회사 무관) | TopBar → store → API param → ExecutionContext.client_id → DataSource |

### 4.2 이름 정정 원칙

| 차원 | 잘못 | 정정 |
|---|---|---|
| backend file | `routes/clumi.py` | `routes/dashboard1.py` |
| backend path | `/api/clumi/...` | `/api/dashboard1/...` |
| collection 21 | `clumi_orders_collector` | `orders_collector` |
| collection 폴더 | `collection/clumi/` | `collection/raw/` |
| collection base | `ClumiCollectorBase` | `RawCollectorBase` |
| preprocessing 폴더 | `preprocessing/clumi/` | `preprocessing/marketing/` |
| frontend page | `Clumi2026Dashboard` | `Dashboard1Page` |
| frontend hook | `useClumiData` | `useDashboard1Data` |
| frontend path | `/clumi/2026-04` | `/dashboard1` |

**원칙**: `clumi` = *회사 이름* (data/clumi/ 디렉토리 + client='clumi' param 만). 코드 path 에는 *기능 이름*.

### 4.3 변경 안 한 것 (호환 유지)

| 영역 | 사유 |
|---|---|
| `clumi_loader.py` 함수명 (`load_clumi_source`) + dict (`CLUMI_SOURCES`) | _base·grade_system_unifier·missing_value_diagnostic 가 import. 일괄 rename 별도 |
| `data/clumi/raw/` 디렉토리 | clumi 는 *회사 이름* — 그대로 정상 |
| `data/clumi/cleaned·computed/` cache 파일들 | 정답값 보존 |

### 4.4 폴더 구조 (Hexagonal)

```
backend/app/
├── data_sources/        ★ INPUT 관절 (agent + API 공유)
├── workspace/           ★ OUTPUT 공유 (cleaned·computed)
├── models/              Pydantic 도메인
├── dream_agent/         agent 작동
│   ├── tools/           Use Cases (DataSource DI)
│   ├── states/          agent 상태
│   └── ...
└── api_v2/              direct API

data/
├── clumi/               회사 'clumi'
│   ├── raw/             21 source (orders.csv 등 — semantic name)
│   ├── cleaned/         13 file (ad_cost_total_*.json 등)
│   └── computed/        22 file (S001_revenue_total_*.json 등)
└── blooming/            다른 회사 (옛 캠페인 BI mock — 추후 정리)
```

---

## 5. 파일·문서 위치 맵

### 5.1 신규 자산 (오늘 만든)

| 영역 | 위치 |
|---|---|
| backend Repository | `backend/app/data_sources/` (base + file + __init__) |
| backend Workspace | `backend/app/workspace/` (base + file + __init__) |
| backend admin endpoint | `backend/api_v2/routes/admin.py` (/api/admin/catalog·/clients) |
| backend dashboard1 endpoint | `backend/api_v2/routes/dashboard1.py` (/api/dashboard1/* 20 endpoint) |
| backend standalone | `backend/api_v2/dashboard1_standalone.py` |
| backend dry-run | `backend/scripts/rename_dry_run.py` (재사용 가능) |
| backend tests | `backend/tests/dashboard1/` (rename from clumi) + `data_sources/` + `workspace/` |
| frontend dashboard1 | `frontend/src/features/dashboard1/` (12 파일 flat) |
| frontend hook | `frontend/src/api/hooks/useDashboard1Data.ts` |
| frontend admin hook | `frontend/src/api/hooks/useAdminCatalog.ts` |
| frontend tool palette | `frontend/src/features/workflow/ToolPalette.tsx` |
| frontend TopBar 드롭다운 | `frontend/src/components/layout/TopBar.tsx` (AVAILABLE_CLIENTS) |
| frontend route | `frontend/src/routes/router.tsx` (path '/dashboard1') |

### 5.2 핵심 계획서 (docs/_claude/architecture/, gitignored)

| 파일 | 내용 |
|---|---|
| `tool_data_agent_분리_재정렬_2026-05-26.md` | 통합 인덱스 (3 계획서 진입) |
| `backend_data_agent_2026-05-26.md` | Backend 분리 (Step 2·3·4·5·8) — 완료 |
| `frontend_dashboard1_2026-05-26.md` | Frontend (Step F1·F6·F7) — 완료 |
| `clumi_to_dashboard1_path_rename_2026-05-27.md` | route rename — 완료 |
| `collection_clumi_prefix_removal_2026-05-27.md` | 21 collector rename — 완료 |
| `preprocessing_clumi_to_marketing_2026-05-27.md` | preprocessing 폴더 rename — 완료 |
| **`followups_and_spec_update_2026-05-27.md`** | **★ 현 작업** (G1·G2·G3 통합) |
| **`g1_cleaning_tags_2026-05-27.md`** | **★ 현 진입 — cleaning YAML tags clumi 제거** |

### 5.3 핵심 메모리 (~/.claude/.../memory/)

- `project_tool_data_agent_separation.md` — P1·P2·P3 원칙 + 진행 자취
- `project_core_value_data_transformation.md` — 시스템 본질 (raw → 분석)
- `project_mock_data_as_poc_source.md` — POC 데이터 source
- `feedback_commit_auto_on_completion.md` — 단계 완료 시 자동 커밋

---

## 6. 남은 작업 (G1·G2·G3)

### G1 — Backend code 잔존 (30분)
- cleaning 3 YAML 의 `tags: [..., clumi, ...]` 제거 (sed)
- pytest 회귀 (204 PASS)
- 자동 커밋

### G2 — docs/reports 4 파일 outdated 마커 (10분, gitignored 라 commit 없음)
- `clumi_백엔드_tool_구현_완료보고서_2026-05-25.md`
- `clumi_분석_최종검증_및_구현계획_2026-05-22.md`
- `data_pipeline_verification_2026-05-22.md`
- `session_compact_recovery_2026-05-26.md`

### G3 — docs/agent_specs 업데이트 ★ 큰 작업 (1.5-2시간)
1. ADR-022 신설 (`adr/ADR-022_data_source_workspace_layer_separation.md`)
2. INDEX.md 신규 자산 등재
3. `10_system_architecture` §데이터 layer
4. `30_DATA_MODELS` ExecutionContext.client_id + DataSource·Workspace ABC
5. `32_execution_agent_tools` BaseTool DataSource DI 패턴
6. `63_frontend_backend_contract` Dashboard1 + admin API

---

## 7. 컨텍스트 빠른 복원 (compact 후 "이어서 진행" 만 하면)

1. 본 문서 §1·§2·§4 (현 작업·다음 액션·핵심 결정)
2. G1 세부 계획서 (`g1_cleaning_tags_2026-05-27.md`) §3·§4 (작업 분해 + DoD)
3. G1 진입 → Step 1 (sed) → Step 2 (pytest) → 자동 커밋
4. 다음 G2 (마커) → G3 (spec 업데이트)

---

## 8. 변경 이력

| 일자 | 내용 |
|---|---|
| 2026-05-27 | 초안 — 오늘 12 commits 완료 후 G1 진입 직전 compact 준비. 핵심 결정 (P1/P2/P3 + 이름 정정) + 신규 자산 위치 + 남은 G1·G2·G3 박제. |
