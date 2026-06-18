# Session Compact 준비 (2026-05-30) — 작업 ② 권한정리 진행 중 (contract A 완료)

> compact 직후 바로 이어 작업 재개용. **현 = tool 레이어 권한 정리 진행 중.**
> 작업 ① 완료(9 commit) + ②-b expand·contract A 완료(2 commit). 남은 = contract B/C + 死dict 정리 + ②-a + 실구동 스모크 + 작업 ③.

---

## ★ 이어가기 (2026-05-30) ⭐ 최신

### 0. 현재 진행

**작업 ① (client 흐름 정리) — 완료 (9 commit).** tool 42개 client-free + runner/pipeline API client 필수 + 프론트 데이터기반(useCurrentClient).

**작업 ② (권한 = tool 이 데이터 I/O 직접 안 함) — 진행 중.**
- ②-b expand (`a01d57f`): 진입점(dashboard1·runner) 저장 추가, no-op(tool 이 아직 저장 = 중복 무해).
- ②-b contract A (`47b9f04`): **computed 19 tool**(metrics 12 + comparison 7) self-save 제거. 진입점 save 자동 활성화. **저장 위반 ~68% 해소.**
- ⚠️ contract A 잔여: **死 record/result/meta dict + 미사용 import 18 tool**(스크립트 한계). 동작 무관 but (가) 깔끔 미달.
- 남은: contract B/C + ②-a + 死코드 정리 + 실구동 스모크 + 작업 ③.

### 1. ⚠️ 작업 규칙 (필독)

1. **convention 우선·하드코딩 자제** (memory `feedback_convention_over_hardcoding`).
2. **한 턴 = ONE 변경 → 검증 → 커밋.** 대안 메뉴 나열 자제.
3. **자명하면 안 묻고 실행.** 큰 결합/방향 결정만 surface.
4. **사용자 방식: 계획서 → 세부계획서 → 검증/재검증 → 작업.** 큰 작업은 반드시 계획부터.
5. **死 코드 싫어함** — (가) 깔끔 수술 선호.
6. **"수정 → 테스트" 원칙** — golden은 코드 정확성, 실구동(서버+브라우저)은 별도. 큰 변경 쌓이면 실구동 스모크.
7. **사용자=비전공자, 사용자편 X** — 직설적·전문가 단일 권장 (memory `feedback_user_beginner_recommend_actively`).

### 2. 이번 세션 commits (시간순 11개)

| commit | 단계 | 내용 |
|---|---|---|
| `f7f74a8` | ①.1 | BaseTool.fetch(source_id, context) 헬퍼 추가 (동작 무변경) |
| `d521a61` | ①.2 | metrics 19 client-free + ctx fixture 16 |
| `8dee1ec` | ①.3 | analysis 6 (패턴 B — ml client→context.client_id) |
| `ba04bc0` | ①.4 | preprocessing/marketing 10 (ad_cost = 패턴 C) |
| `62f46b2` | ①.5 | cleaning·normalization·comparison 7 (패턴 A) |
| `52bf5ac` | ①.6a | runner client 필수+ctx 정합 · pipeline API Query 필수 |
| `ebfd17a` | ①.6c | 프론트 useCurrentClient() 데이터기반 (5 페이지 + TopBar + RefreshButton) |
| `a01d57f` | ②-b expand | dashboard1 _cached_or_run 저장 추가 · runner fallback 메타 강화 |
| `47b9f04` | ②-b contract A | computed 19 tool(metrics 12 + comparison 7) self-save 제거 + test R5/R6 삭제 |

### 3. 핵심 계획서 (docs/reports/)

- `tool레이어_권한정리_계획서_2026-05-29.md` — ① + ② 상위 계획·권한 규칙·레이어 정의.
- `세부계획_작업①_client필수화_2026-05-29.md` — ① 실행 (helper-B, 패턴 A/B/C, ctx fixture).
- `계획_작업②_권한정리_2026-05-29.md` — ② 상위 (②-a clumi_loader + ②-b self-save).
- `세부계획_작업②b_순수화_2026-05-29.md` — ②-b expand-contract, A/B/C 분류, 함정.
- `데이터레이어_정리_계획서_2026-05-29.md` — 이전 세션(데이터 레이어, 단계 2 E11 해소).

### 4. 검증 (회귀 기준)

```
backend golden:
uv run pytest backend/tests/pipelines backend/tests/dashboard1 \
  backend/tests/data_sources backend/tests/workspace \
  backend/tests/permissions backend/tests/ml_models -q
→ 297 passed / 15 failed (15 = pyarrow 환경, 무시)
   ※ 297 = 이전 299 baseline - test_revenue_total R5/R6 2개(②-b contract A 에서 삭제)
   ※ tool-save 단언 테스트는 권한 정리 시 obsolete → entry-save는 test_route H5가 검증

frontend: pnpm -C frontend build (tsc + vite 2934 modules) + 88 vitest
정답 앵커: S001 = 119,539,660 (entry-save 경로로 통과 확인)
```

### 5. 다음 작업 (우선순위)

**남은 ②-b (이어 진행):**

| 단위 | 내용 | 비용·주의 |
|---|---|---|
| **②-b 死코드 정리** | contract A 18 tool 의 死 record/result/meta dict + 미사용 import 제거 | per-tool Edit (multi-line dict regex 위험 — 스크립트 금지). 동작 무관, (가) 깔끔만 |
| **②-b contract B** | cleaned-dict 5 tool(utm_normalizer·channel_attribution_normalizer·ad_cost_aggregator·budget·category_multi·member_guest) self-save 제거 | 패턴 A와 거의 동일(긴 것 먼저 정규식). golden + 캐시 동작 확인 |
| **②-b contract C** | cleaned-DataFrame 2 tool(active_orders_filter·member_metrics_validator) save 제거 + **테스트 4종 재작성**(test_active_orders_filter parquet/schema/roundtrip · test_member_metrics_validator parquet/schema · test_ad_cost_aggregator cleaned/schema · test_storage_backend는 workspace 단위 그대로 OK) | DataFrame 중간물 prod 미소비 → 저장 제거 + 테스트는 단언 삭제 권장 |

**작업 ②-a (별도 단위, ②-b 후):**

| tool | clumi_loader 사용 | 이관 방향 |
|---|---|---|
| `missing_value_diagnostic` | `load_clumi_source(file_no)` | `self.fetch(source_id, context)` (file_no→source_id 매핑) |
| `kst_timezone_normalizer` | `stream_clumi_source(file_no)` | ⚠️ 스트리밍 |
| `grade_system_unifier` | `CLUMI_SOURCES` (매핑 import) | source_id 직접 |
| `ga4_session_aggregator` | `stream_clumi_source(file_no=8)` ※ ga4_page_events.jsonl **265MB** | ⚠️ **결정 필요**: DataSource 에 `stream(client, source_id)` 추가 vs ga4 별도 처리 |
| `collection/_base` | `CLUMI_SOURCES` import (호환) | 확인 후 import 제거 |

**sprint15 collectors** (meta·kakao·naver_sa·naver_gfa·google_ads·review) `load_mock_csv` 사용:
- 이미 깨짐(삭제된 mock 파일 참조) + agent team_catalog·planning prompt·sprint15 테스트 결합.
- → **별도 신중 단위(연기 권장)**. agent 작업 시 함께.

**작업 ① 잔여 (option 나로 미룸 — 실害 없음):**
- dashboard1 API `Query("clumi")` 20 endpoint + `test_route.py` 25 호출 client 보강.
- `useDashboard1Data.ts` `DEFAULT_CLIENT='clumi'` (frontend 가 늘 client 전달하므로 dead default).
- → /dashboard1 레거시 경로 정리 시 함께.

**실구동 스모크 테스트** (작업 ② 마무리 후 권장):
- backend: `uv run python run_server_v2.py` (서버 기동 + `/api/admin/clients`·`/category` 응답).
- frontend: `pnpm -C frontend dev` → 브라우저 client 드롭다운 전환 → 대시보드 갱신 + "루미" 표시 + 빈 client 에러 확인.

**작업 ③ 카테고리 기준 명확화** (별도 분석 문서 필요):
- 개발문서(agent_specs·ADR) 의 카테고리 정의 + 현 tool 분류 대조.
- 사용자 기준: 수집/정제/지표생성/계산/추론 1:1 이어야. 현재 모호(preprocessing↔metrics↔cleaning 경계, comparison↔metrics).

---

## 6. 권한 규칙 / 레이어 정의 (북극성)

**두 레이어:**

| 레이어 | 폴더 | 역할 |
|---|---|---|
| **data layer** | `backend/app/data_sources/` | 데이터 가져오기(읽기) |
| | `backend/app/workspace/` | 산출물 저장·꺼내기 |
| | `backend/app/schemas/` | 데이터 모양(Pydantic) 정의 |
| **tool layer** | `backend/app/dream_agent/tools/` | 데이터 받아 처리(정제·지표·계산·추론) |

**규칙 한 줄:** data layer 만 데이터가 *어디* 있고 *어떻게* 저장/로드되는지 안다. tool layer 는 받아 처리만 한다 — 직접 가지러/저장하러 가지 않고 data layer 에 *부탁*한다.

**누가 무엇을 아는가:**

| | data layer | tool layer |
|---|:--:|:--:|
| 파일 경로·이름 | 안다 | 모른다 |
| `open`·`read_csv`·`save` | 한다 | **안 한다** ❌ (위반 = ②) |
| 계산·정제·추론 | 안 함 | 한다 |
| 데이터 요청 | (응답) | 부탁 (`self.fetch`/`self.ds.get`) |

**현재 위반 (작업 ② 대상):**
- ②-a 직접 읽기: clumi_loader 5 tool (위 §5 표).
- ②-b 직접 저장: ~28 tool 중 **19개 contract A 완료**, 7 cleaned-dict + 2 cleaned-DataFrame 남음.

---

## 7. helper-B 패턴 (작업 ① 핵심)

**tool 은 client 를 모름:**
```python
# 전 (각 tool 에 산재)
client = merged.get("client", DEFAULT_CLIENT)   # ← 삭제됨
df = self.ds.get(client, "orders")              # ← 삭제됨
# 후 (helper-B)
df = self.fetch("orders", context)              # client 글자 없음 ✅
```

`BaseTool.fetch(source_id, context)` ([base_tool.py](../../backend/app/dream_agent/tools/base_tool.py)):
- 내부: `self.ds.get(context.client_id, source_id)`. `context.client_id` 없으면 `ValueError` (fail-fast).
- 진입점이 ctx.client_id 채움: dashboard1 `_ctx(client)` · runner `client_id=client` · agent(미확인, ②-a 시).

**예외 패턴 (작업 ①에서 적용됨):**
- 패턴 A (단순 ds.get): 대부분 tool.
- 패턴 B (analysis + ml): `ml.xxx(client=context.client_id)` 동반 (review_sentiment 등 5).
- 패턴 C (헬퍼+f-string): `aggregate_ad_cost(self.ds, context.client_id, ...)` + `f"data/{context.client_id}/..."` (ad_cost_aggregator).

**진입점 (client 보장):**
- dashboard1 API: `Query(..., description="회사 식별자 (필수)")` (단 dashboard1.py 20 endpoint는 ①.6b로 보류).
- runner `runner.py:149`: `client = variables.get("client")` + 없으면 ValueError.
- runner `runner.py:185`: `client_id=client` (정합).
- 프론트: `useCurrentClient()` = `selectedClientId ?? clients.find(c=>c.raw_count>0)?.id ?? clients[0]?.id`.

---

## 8. ②-b expand-contract 메커니즘 (작업 ② 핵심)

**expand (a01d57f):** 진입점이 "tool 이 저장 안 했으면(not exists) 저장" 추가.
- dashboard1 `_cached_or_run`: execute 후 `if not exists: save(clean, meta=result.get("_meta"), client=client)`.
- runner: fallback save 이미 보유, meta 를 `result.output.get("_meta")` 로 강화.
- 효과: tool 이 저장 중인 동안 진입점 save 는 skip(무해). contract 후 자동 활성.

**contract A (47b9f04):** computed 19 tool `get_default_workspace().save("computed", ...)` 제거.
- 진입점이 return dict 를 저장(rich result 가 아닌 return 만).
- output_model.model_validate(loaded) 통과(extra=ignore). 값 동일.
- test_route H5(cache consistency r1==r2) 통과.

**잔여 死코드 (contract A 18 tool, 정리 필요):**
- `record`/`result`/`meta = {...}` (저장용이었음) — 미사용 변수로 잔존.
- `from app.workspace import get_default_workspace` / `from app.dream_agent.tools.shared.storage import get_storage` — 미사용 import 잔존(스크립트 conditional 미작동).

---

## 9. 중요 함정 / 교훈 (이 세션에서 발견)

1. **Regex alternation 순서 — 긴 것 먼저.**
   `(?:loc|location)` 는 `location=location` 에서 `loc` 만 잡고 `ation` 잔존 → "countation" 코드 손상.
   ✅ `(?:location|loc)` (긴 것 먼저). `_storage` 패턴(`\}` 앵커)은 자동 backtrack 으로 안전.
2. **Multi-line dict regex 위험.** `\{[^{}]*\}` 는 중첩 brace 없는 경우만 안전. nested dict 가진 tool 에서 실패 + 동시에 다른 곳을 잘못 매칭하면 corruption. → per-tool Edit 권장.
3. **BOM 주의.** 데이터 파일 편집 시 **plain utf-8(no BOM)**. `encoding='utf-8-sig'` 로 write 하면 BOM 추가됨. JSON 은 `encoding='utf-8'` 로 읽혀 BOM 에서 깨짐. (이전 세션 브랜드 변경 시 회귀 1건 발생, 수정 완료.)
4. **스크립트 후 반드시 grep + golden.** 손상 발견 시 `git checkout HEAD -- <dir>` 로 revert + 다시.
5. **테스트 분류.**
   - golden = 코드 정확성·값·회귀.
   - frontend build = TS 타입체크 + 모듈 변환.
   - 프론트 88 tests = 단위 회귀.
   - **실구동 스모크 = 별개**(서버 기동·브라우저). 큰 리팩터 쌓이면 해야 함.
6. **권한 위반 우선순위 — 저장(~30)이 읽기(5)보다 훨씬 많음.** "권한 완벽 분리"의 본체 = ②-b. ②-a 는 마무리 청소.
7. **option 나 선택의 의미.** /dashboard1 레거시는 frontend 가 늘 client 전달하므로 "dead default" — 위험 없지만 (가) 완전성에선 미달.
8. **計画書 검증으로 수치 정정 확인됨:** "~30 tool" → 실제 46 client 폴백 / "~30" → 정확히 19 computed + 7 cleaned-dict + 2 cleaned-DataFrame = 28 save. clumi_loader 5 사용처.

---

## 10. 코드 위치 빠른 참조

**핵심 파일:**
- `backend/app/dream_agent/tools/base_tool.py` — `BaseTool.fetch(source_id, context)` 헬퍼.
- `backend/app/data_sources/file.py` — `FileDataSource.get(client, source_id)` → `data/{client}/raw/{file}`.
- `backend/app/workspace/file.py` — `FileWorkspace.save/load/exists(layer, key, *, client="clumi")` → `data/{client}/{layer}/{key}` (단계 2 client-aware).
- `backend/app/pipelines/runner.py` — client 필수(line 149) + ctx.client_id 정합(line 185) + fallback save(line 230, meta from `_meta`).
- `backend/api_v2/routes/dashboard1.py` — `_cached_or_run`: storage exists/load with client + `if not exists: save` (expand).
- `backend/api_v2/routes/pipelines.py` — `Query(...)` 필수(category endpoint).
- `frontend/src/api/clients.ts` — `useCurrentClient()` 훅.
- `frontend/src/api/pipelines.ts` — `useCategoryResults(category, client|undefined, period)` + `enabled: !!client`.

**계획서 (docs/reports/):**
- 위 §3 참조.

**git 상태:**
- branch: `main` (origin 대비 ahead — push 안 함).
- 최근 commit: `47b9f04 refactor(tools): ②-b contract A — computed 19 tool self-save 제거 (권한)`.

---

## 11. compact 후 첫 행동 권장

1. **본 문서 §0~§5 정독.** (현재 위치·다음 작업·검증 기준)
2. **수정 → 테스트 원칙.** 작업 ② 마무리(死코드·B·C·②-a) 후 실구동 스모크 권장.
3. **다음 ONE 변경 후보 (사용자 선택):**
   - (A) **死코드 정리** — contract A 18 tool 의 死 record/result/meta + 미사용 import 제거 (per-tool Edit). (가) 깔끔 완성.
   - (B) **contract B** — cleaned-dict 5 tool save 제거. 패턴 A 동일(긴 것 먼저 정규식).
   - (C) **contract C** — cleaned-DataFrame 2 tool + 테스트 4종 재작성.
   - (D) **②-a clumi_loader 5** — file_no→source_id 매핑 + ga4 스트리밍 결정 필요.
   - (E) **실구동 스모크** — 작업 ② 미완성이라 보류 권장(작업 ② 마무리 후).
4. **추천 순서:** A(死코드) → B → C(테스트) → ②-a → 실구동 → 작업 ③.

---

## 12. 사용자 메시지 직전 상태

마지막 메시지: "compact 준비해야해 준비문서 상세하게 작성해줘".
직전 작업: ②-b contract A 커밋(47b9f04) 후 진행 상황 보고 + 다음 단위(B/C·死코드·②-a) 선택 대기 중이었음.

contract A 까지가 **권한 위반의 본체(~68%) 해소된 안정 상태**. compact 직후 §11 의 (A) 死코드 정리부터 권장.
