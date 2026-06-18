# 계획 — 작업 ⑭ team_catalog 신 21 collector 등재 (dual-source drift collection 100% 해소)

> **상태**: **v3** (2차 적대적 검증 반영 = minor_fix_then_proceed). **사용자 승인 대기**.
> v1 → v2 → v3: 1차 15 + 2차 10 = 25 변경 반영. 3차 round 우회 (ROI 음수).

---

## 0. 메타 + 본질 진단 정정

### 0.1 메타

| 항목 | 값 |
|---|---|
| 작업 번호 | ⑭ |
| 작업명 | team_catalog 신 21 collector 등재 (collection 카테고리 100% Planner 시야 회복) |
| 작성일 | 2026-06-01 (v3) |
| 패턴 | 작업 ⑤·⑨·⑪·⑫ |
| 분량 | 中 (**4 commit + 계획서 commit 0 · 5 파일 · 약 220 lines 추가**) |
| 후속 | ⑰ metrics 35 / cleaning 3 / comparison 7 / analysis 6 / normalization 4 = 55 잔존 등재 |

### 0.2 본질 진단 Q1 정량 정정

| 박제 | 정량 |
|---|---|
| compact v4 인용 "Planner 38 / 실 구현 15 / invisible 52" | **stale** (작업 ⑫.D 후) |
| **실측 (2026-06-01)** | team_catalog **31 entry** / status:implemented **9** / **invisible 76** |
| 작업 ⑭ 후 예상 | team_catalog **52 entry** / implemented **30** / **invisible 55** |
| 해소율 | **27.6%** (21/76) — collection 카테고리 22 = 100% 가시화 |
| 잔존 55 (별 작업 ⑰+) | metrics 35 + comparison 7 + analysis 6 + normalization 4 + cleaning 3 |

### 0.3 역드리프트 박제

stub 3 (youtube/coupang/oliveyoung) = ToolRegistry 0 / team_catalog 1 → **작업 ⑱ 별 정리**.

---

## 1. 사용자 결정 (1차+2차 검증 통합, 본 작업 ⑭ 실 행동 관여만)

> 2차 정정: 결정 surface 13 → **본 작업 6** + **별 작업 결정 (⑱·⑲)** 분리. 비전공자 가독성 + 결정 inflation 회피.

| # | 결정 | 권장 적용 |
|---|---|---|
| **D1** | Source enum 확장 | **옵션 A** — 신 8 추가 (META, KAKAO, GA4, ORDERS, CUSTOMERS, PROMOTIONS, CATEGORY_SALES, CRM) + **cognitive.yaml prompt 동반** |
| D2 | agent 분리 vs 통합 | **통합** (collection_agent 단일 25 tool) |
| D3 | 자동화 vs 수동 | **수동 즉시** + 자동화 별 작업 **⑲** (sync_team_catalog.py 약 50 lines) |
| D4 | Stage 3 prompt 동반 | **필수** — intent 분기 + examples + 기존 충돌 해소 |
| D5 | format_normalizer dependencies | **후속 ADR 분리** |
| D6 | 신 21 description 단일 진실 | **per-tool yaml** (`backend/app/dream_agent/tools/catalog/collection/**/*.yaml`) 그대로 복사 — 2차 정정 |

별 작업 결정:
- ⑱ youtube/coupang/oliveyoung stub 3 역드리프트 폐기
- ⑲ ToolRegistry → team_catalog 자동 sync (sync_team_catalog.py)

### 1.1 D1 부록 — 21 collector → 신 8 Source enum 매핑 (1차 신설, 2차 sanity 보강)

| collector | Source enum 흡수 |
|---|---|
| meta_ads_performance · meta_ads_by_age · meta_instagram_inapp · instagram_engagement | `META` |
| naver_searchad · naver_advoost · naver_interest_alert · naver_talktalk | `NAVER` (기존) |
| ga4_traffic_source · ga4_page_events | `GA4` |
| kakao_bizmessage | `KAKAO` |
| orders · customer_grade_history | `ORDERS` |
| customers · customer_rfm · signup_events · **household_structure** | `CUSTOMERS` |
| promotions · ad_change_history | `PROMOTIONS` |
| category_sales | `CATEGORY_SALES` |
| crm_messages | `CRM` |

> **2차 별주**: `household_structure` = folder external (외부 인구통계 API) but Source enum=`CUSTOMERS` (의미 분류). ⑲ sync 자동화 시 folder ↔ Source 매핑 dict 별도 필요.

---

## 2. 현황 spot-check

### 2.1 team_catalog 현 구조 (작업 ⑫.D 후)

| 항목 | 값 |
|---|---|
| 파일 | [team_catalog.yaml](../../backend/app/dream_agent/planning/catalog/team_catalog.yaml) |
| 구조 | `teams` → `analysis_team` → `agents` → ... |
| team 정의 | analysis_team (7 agent) + creative_team (4 agent) + operations_team (주석) = 11 agent |
| 총 entry | 31 / status:implemented 9 / collection_agent 4 entry |

### 2.2 신 21 collector 실 PRODUCES_KEY + yaml produces (1차+2차 정정)

> **2차 정정**: yaml produces = `[<name>_raw, count]` **2-key** (1차 v2 "raw 단일" 박제 오류). 신 21 등재 시 2-key 그대로 복사.

| collector | .py PRODUCES_KEY | 실 yaml produces |
|---|---|---|
| meta_ads_performance_collector | `meta_ads_raw` | `[meta_ads_raw, count]` |
| meta_ads_by_age_collector | `meta_ads_by_age_raw` | `[meta_ads_by_age_raw, count]` |
| meta_instagram_inapp_collector | `meta_inapp_raw` | `[meta_inapp_raw, count]` |
| naver_searchad_collector | `naver_sa_raw` | `[naver_sa_raw, count]` |
| naver_advoost_collector | `naver_advoost_raw` | `[naver_advoost_raw, count]` |
| naver_interest_alert_collector | `naver_alert_raw` | `[naver_alert_raw, count]` |
| naver_talktalk_collector | `talktalk_raw` | `[talktalk_raw, count]` |
| kakao_bizmessage_collector | `kakao_raw` | `[kakao_raw, count]` |
| ga4_traffic_source_collector | `clumi_ga4_traffic_raw` | `[clumi_ga4_traffic_raw, count]` |
| ga4_page_events_collector | `clumi_ga4_page_raw` | `[clumi_ga4_page_raw, count]` |
| ad_change_history_collector | `ad_change_raw` | `[ad_change_raw, count]` |
| household_structure_collector | `household_raw` | `[household_raw, count]` |
| instagram_engagement_collector | `instagram_raw` | `[instagram_raw, count]` |
| orders_collector | `orders_raw` | `[orders_raw, count]` |
| customers_collector | `customers_raw` | `[customers_raw, count]` |
| customer_rfm_collector | `rfm_raw` | `[rfm_raw, count]` |
| customer_grade_history_collector | `grade_history_raw` | `[grade_history_raw, count]` |
| signup_events_collector | `signup_raw` | `[signup_raw, count]` |
| promotions_collector | `promotions_raw` | `[promotions_raw, count]` |
| category_sales_collector | `category_sales_raw` | `[category_sales_raw, count]` |
| crm_messages_collector | `crm_raw` | `[crm_raw, count]` |

### 2.3 Planner Stage 3 _get_agent_tools (catalog 경로)

[planner.py:157-179](../../backend/app/dream_agent/planning/planner.py#L157-L179):
```python
def _get_team_agents(catalog, teams_selected):
    teams = catalog.get("teams", {})
    for team_name in teams_selected:
        team_data = teams.get(team_name, {})
        agents = team_data.get("agents", {})
        ...
```

→ catalog 경로 = `cat['teams']['analysis_team']['agents']`. team_catalog 외부 ToolRegistry tool = Planner LLM 시야 0.

### 2.4 Source enum + cognitive.yaml hardcode (D1 critical)

- **schema** [structured_query.py:81-91](../../backend/app/dream_agent/schemas/structured_query.py#L81-L91) — 9개
- **prompt** [cognitive.yaml:50-52](../../backend/app/dream_agent/llm_manager/prompts/cognitive.yaml#L50-L52) — **prompt 도 9개 hardcode** (1차 critical 발견)

→ schema 만 +8 갱신 시 Cognitive LLM 은 신 8 source 영영 미생성 → 단계 B' 동반 갱신 필수.

### 2.5 Stage 3 prompt 기존 source→collector 매핑

[planning_stage3_todo.yaml:26-31](../../backend/app/dream_agent/llm_manager/prompts/planning_stage3_todo.yaml#L26-L31):
```yaml
- targets.source 에 맞는 collector 선택:
  · unknown → review_collector (default)
  · naver → review_collector              # ← 신 매핑 충돌
  · youtube/coupang/oliveyoung → 동명 stub
```

→ 단계 B.1 **intent 기반 분기** 로 충돌 해소 + **task×source 2D 매트릭스 박제** (2차 should).

### 2.6 회귀 risk = low

- team_catalog 활성 consumer = `planner.py` + `agent_pool.py` 만 (frontend·test grep 0)
- frontend Source enum **literal 미러 0** (grep `'naver'|'meta'|'kakao'` frontend/src = 0 hit; 일반 문자열 매칭은 별개)
- rollback = yaml 단일 파일 revert

---

## 3. 변경 명세 (단계별, **4 commit + 계획서 commit 0**)

> **commit 0**: `docs(reports): ⑭ 계획서 v3` (별 commit, plan 파일 진입 박제).

### 단계 C — Source enum +8 (commit 1)

**파일**: [structured_query.py:81-91](../../backend/app/dream_agent/schemas/structured_query.py#L81-L91)

```python
class Source(str, Enum):
    """데이터 소스 (⑭ 2026-06-01: 신 8개 추가)"""
    # 기존 9
    NAVER = "naver" / YOUTUBE / COUPANG / OLIVEYOUNG / TIKTOK / AMAZON / GOOGLE / MULTI / UNKNOWN
    # ⑭ 신 8 (clumi raw 정합, 21 collector → 매핑 §1.1)
    META           = "meta"
    KAKAO          = "kakao"
    GA4            = "ga4"
    ORDERS         = "orders"
    CUSTOMERS      = "customers"
    PROMOTIONS     = "promotions"
    CATEGORY_SALES = "category_sales"
    CRM            = "crm"
```

**commit message** (2차 should): `refactor(schemas): ⑭.C Source enum +8 (META/KAKAO/GA4/ORDERS/CUSTOMERS/PROMOTIONS/CATEGORY_SALES/CRM)`

### 단계 A+D atomic — team_catalog 신 21 등재 + description + 폐기 주석 정리 (commit 2)

**파일**: [team_catalog.yaml](../../backend/app/dream_agent/planning/catalog/team_catalog.yaml)

#### A.1 collection_agent description 갱신

```yaml
collection_agent:
  description: "마케팅 raw 수집 (콘텐츠 4 + 광고/SNS/웹분석 13 + 거래/회원 8 = 25 tool, helper-B 패턴, ADR-022)"
```

#### A.2 신 21 entry (2차 정정 — description = 실 yaml description 그대로 복사, produces = 2-key)

> **2차 D6 단일 진실**: description source = `backend/app/dream_agent/tools/catalog/collection/**/*.yaml` per-tool yaml. 21 entry 등재 시 per-tool yaml description 그대로 복사 (drift 0).

```yaml
tools:
  # 기존 4 (review + stub 3, ⑫ 정합)
  ...

  # ⑭ (2026-06-01) 신 등재: external 13 (description = per-tool yaml 그대로)
  - name: meta_ads_performance_collector
    status: implemented
    description: "Raw collector — #1 meta_ads_performance. POC: clumi_loader thin wrapper. MVP+: 실 API 교체"
    params_required: []
    params_optional: []
    produces: [meta_ads_raw, count]    # ← 2-key (2차 정정)
  - name: meta_ads_by_age_collector
    status: implemented
    description: "Raw collector — #2 meta_ads_by_age. POC: clumi_loader thin wrapper. MVP+: 실 API 교체"
    params_required: []
    params_optional: []
    produces: [meta_ads_by_age_raw, count]
  # ... (나머지 11 external × 6 lines)

  # ⑭ (2026-06-01) 신 등재: internal 8
  - name: orders_collector
    status: implemented
    description: "Raw collector — #5 orders. POC: clumi_loader thin wrapper. MVP+: 실 API 교체"
    params_required: []
    params_optional: []
    produces: [orders_raw, count]
  # ... (나머지 7 internal × 6 lines)
```

#### A.3 ⑫.D 폐기 주석 갱신

```yaml
# ⑭ (2026-06-01) 완료: broken 5 폐기 + external 13 + internal 8 = 신 21 collection_agent 등재.
# collection 카테고리 ToolRegistry 22 = team_catalog 25 (review 1 + stub 3 + 신 21) 100% 가시화.
# 잔존 invisible 55 = metrics 35 + comparison 7 + analysis 6 + normalization 4 + cleaning 3 (작업 ⑰+).
# 역드리프트 stub 3 (youtube/coupang/oliveyoung) = ToolRegistry 0 / catalog 1 (별 작업 ⑱).
```

**commit message**: `refactor(catalog): ⑭.A+D team_catalog 신 21 등재 (collection_agent 통합, drift 22→0)`

### 단계 B + B' atomic — Stage 3 prompt + cognitive.yaml 동반 (commit 3)

#### B.1 [planning_stage3_todo.yaml](../../backend/app/dream_agent/llm_manager/prompts/planning_stage3_todo.yaml#L26-L31) — intent 분기

```yaml
# ⑭ (2026-06-01) intent 기반 분기 rules
- targets.source 에 맞는 collector 선택:
  · unknown → review_collector (default - 리뷰 분석)
  · naver → 5 collector 중 task 기반 분기:
    - task=sentiment_analysis|keyword_extraction → review_collector
    - task=data_collection + intent=검색광고 → naver_searchad_collector
    - task=data_collection + intent=디스플레이 → naver_advoost_collector
    - task=data_collection + intent=관심알림 → naver_interest_alert_collector
    - task=data_collection + intent=메시지 → naver_talktalk_collector
  · meta → [meta_ads_performance | meta_ads_by_age | meta_instagram_inapp]
  · kakao → kakao_bizmessage_collector
  · ga4 → [ga4_traffic_source | ga4_page_events]
  · orders → orders_collector
  · customers → [customers | customer_rfm | signup_events]
  · promotions → promotions_collector
  · category_sales → category_sales_collector
  · crm → crm_messages_collector
  · youtube / coupang / oliveyoung → 동명 stub
```

+ **examples 신규** (광고 + CRM):
- 예시 N: source=meta, todo_001 = meta_ads_performance_collector
- 예시 N+1: source=orders, todo_001 = orders_collector → todo_002 = customers_collector → todo_003 = customer_rfm_collector

#### B'.1 [cognitive.yaml:50-52](../../backend/app/dream_agent/llm_manager/prompts/cognitive.yaml#L50-L52) — Source enum 9→17

```yaml
source: enum ↓                 ← 데이터 소스 (default: unknown)
        "naver" | "youtube" | "coupang" | "oliveyoung"
        | "tiktok" | "amazon" | "google" | "multi" | "unknown"
        | "meta" | "kakao" | "ga4"                                   # ⑭ 광고/웹분석
        | "orders" | "customers" | "promotions" | "category_sales" | "crm"  # ⑭ 내부
```

+ **examples 8·9 신규** (2차 정정 — 현 examples 1~7 존재):
- 예시 8: 광고 시나리오 (source=meta)
- 예시 9: CRM 시나리오 (source=orders)

**commit message**: `refactor(prompts): ⑭.B+B' Stage3 intent 분기 + cognitive.yaml Source enum 9→17`

### 단계 E — ADR-027 §3 박제 동기화 (commit 4, doc-only, 2차 scope 분리)

> **2차 정정**: ⑮ scope 재정의 **분리** (옵션 a — ⑮ scope 기존 박제 그대로 유지 + ⑭ 박제만 단계 E 에서 추가).

**파일**: [ADR-027 §3](../agent_specs/adr/ADR-027_five_actor_permission_separation.md#L28-L46)

§3 박제 row 추가:
```
✅ 작업 ⑭ (2026-06-01) 부분 해소 — team_catalog 신 21 등재 (external 13 + internal 8) +
   Source enum +8 + cognitive.yaml prompt 갱신 + Stage 3 prompt 매핑 통합.
   collection 카테고리 dual-source drift 100% 해소 (invisible 76 → 55).

잔존 (별 작업, scope 변동 0):
- ⑮: external 13 + RawCollectorBase 21 entries ADR-027 §1 권한 audit (FILE_NO hardcode 패턴, 작업 ⑫.H 박제 유지)
- ⑰: metrics 35 등재 (analysis_agent 통합 vs 신 metrics_agent)
- ⑱: cleaning 3 + youtube/coupang/oliveyoung stub 3 역드리프트 폐기
- ⑲: ToolRegistry → team_catalog 자동 sync (sync_team_catalog.py)
```

**commit message**: `docs(adr): ⑭.E ADR-027 §3 박제 동기화 (collection drift 100% 해소)`

---

## 4. 영향 범위 (5 파일 / 4 commit + 계획서 commit 0)

### 4.1 변경

| 영역 | 파일 | commit |
|---|---|---|
| 백엔드 schema | structured_query.py (Source enum +8) | 1 (C) |
| 백엔드 catalog | team_catalog.yaml (신 21 등재 + description + 주석) | 2 (A+D) |
| LLM prompt | planning_stage3_todo.yaml (Stage 3 intent + examples) | 3 (B) |
| LLM prompt | cognitive.yaml (Source enum prompt 9→17 + examples) | 3 (B' atomic) |
| ADR | ADR-027 §3 박제 동기화 | 4 (E) |
| 계획서 | 본 파일 v3 commit | 0 |
| **합** | **5 파일 / 5 commit (계획서 포함)** | — |

### 4.2 무영향

| 영역 | 사유 |
|---|---|
| 신 21 collector py·yaml | 이미 활성, 변경 0 |
| review_collector.py (⑫.B) | 변경 0 |
| ToolRegistry 분포 (85) | 변경 0 (등재만 변화) |
| 분석 team baseline | 변동 0 |
| dashboard1 / sprint15 / frontend | 변동 0 |
| frontend Source enum literal | 0 hit |
| ADR-027 §1 권한 매트릭스 | 정합 유지 |

---

## 5. 단계별 commit (4 commit, 2차 commit message convention)

> **단계 0**: 진입 직전 baseline spot-check.

| commit | 단계 | 회귀 명령 | commit message |
|---|---|---|---|
| 0 | plan v3 | doc-only | `docs(reports): ⑭ 계획서 v3` |
| 1 | C — Source enum +8 | sprint13 단독 + Pydantic round-trip | `refactor(schemas): ⑭.C Source enum +8` |
| 2 | A+D atomic | sprint13+14 + Planner _load_catalog + drift check | `refactor(catalog): ⑭.A+D team_catalog 신 21 등재` |
| 3 | B+B' atomic | sprint13 Cognitive·planning + manual smoke | `refactor(prompts): ⑭.B+B' Stage3+cognitive Source enum 갱신` |
| 4 | E (doc-only) | baseline 무관 | `docs(adr): ⑭.E ADR-027 §3 박제 동기화` |

---

## 6. 미해결 결정 (2차 정합)

§1 결정 표 (single source). §6 = 본 작업 6 결정 + 별 작업 결정 (⑱·⑲) 분리.

---

## 7. 회귀 baseline 검증 명령 (2차 정정 — 단독 vs 합산 분리)

```bash
# 0. 진입 직전 baseline spot-check (단계 0, 2차 신설)
cd backend && uv run python -c "
from app.dream_agent.planning.planner import _load_catalog
cat = _load_catalog()
coll = cat['teams']['analysis_team']['agents']['collection_agent']['tools']
print(f'collection_agent tools: {len(coll)}')   # 기대: 4
from app.dream_agent.tools.registry import get_registry
reg = get_registry(); reg.load()
print(f'ToolRegistry: {len(reg.get_all())}')   # 기대: 85
from app.dream_agent.schemas.structured_query import Source
print(f'Source enum: {len(Source)}')   # 기대: 9
# 2차 신설 — Pydantic baseline round-trip
from app.dream_agent.schemas.structured_query import Targets
t = Targets(source=Source.NAVER)
assert Targets.model_validate_json(t.model_dump_json()).source == Source.NAVER
print('Pydantic baseline round-trip ✓')
"

# 1. sprint13 단독 (2차 정정 — sprint13 단독 = 190)
cd backend && uv run pytest tests/sprint13 -q
# 기대: 190 passed / 0 failed / 6 deselected

# 2. sprint14 단독 (2차 신설 — sprint14 단독 = 103/11/2)
cd backend && uv run pytest tests/sprint14 -q
# 기대: 103 passed / 11 failed (HITL) / 2 skipped / 11 deselected

# 3. sprint13+14 합산 (2차 정합)
cd backend && uv run pytest tests/sprint13 tests/sprint14 -q
# 기대: 293 passed / 11 failed (HITL) / 2 skipped / 17 deselected — 변동 0

# 4. dashboard1 영역 (불변)
cd backend && uv run pytest tests/{pipelines,dashboard1,data_sources,workspace,permissions,ml_models} -q
# 기대: 303/3 (pyarrow)

# 5. sprint15 (작업 ⑫ baseline 불변)
cd backend && uv run pytest tests/sprint15 -q
# 기대: 13/0

# 6. frontend type-check
cd frontend && pnpm exec tsc --noEmit
# 기대: exit 0

# 7. Planner _get_agent_tools 분포 (단계 2 후)
cd backend && uv run python -c "
from app.dream_agent.planning.planner import _load_catalog
cat = _load_catalog()
coll = cat['teams']['analysis_team']['agents']['collection_agent']['tools']
print(f'collection_agent tools: {len(coll)} entry')
implemented = [t for t in coll if t.get('status') == 'implemented']
print(f'implemented: {len(implemented)}')
"
# 기대: 25 / 22 (review 1 + 신 21)

# 8. ToolRegistry vs team_catalog drift (collection 100%)
cd backend && uv run python -c "
from app.dream_agent.tools.registry import get_registry
from app.dream_agent.planning.planner import _load_catalog
reg = get_registry(); reg.load()
reg_collection = {t.name for t in reg.get_all() if t.category.value == 'collection'}
cat = _load_catalog()
cat_collection = {t['name'] for t in cat['teams']['analysis_team']['agents']['collection_agent']['tools']}
print(f'ToolRegistry: {len(reg_collection)} / team_catalog: {len(cat_collection)}')
print(f'invisible: {sorted(reg_collection - cat_collection)}')   # 기대: []
print(f'역드리프트 (stub): {sorted(cat_collection - reg_collection)}')   # 기대: ['coupang_collector', 'oliveyoung_collector', 'youtube_collector']
"

# 9. 신 7 source × manual smoke (2차 신설 — cognitive.yaml H1 회귀)
# 광고 (source=meta) / CRM (source=orders) / GA4 (source=ga4) 3 시나리오 manual 입력 → Cognitive LLM 출력 검증
# POC = 1회 manual smoke

# 10. Source enum +8 Pydantic round-trip (단계 1·3 후)
cd backend && uv run python -c "
from app.dream_agent.schemas.structured_query import Source, Targets
print(f'Source: {len(Source)}')   # 기대: 17
for s in (Source.META, Source.KAKAO, Source.GA4, Source.ORDERS, Source.CUSTOMERS, Source.PROMOTIONS, Source.CATEGORY_SALES, Source.CRM):
    t = Targets(source=s)
    assert Targets.model_validate_json(t.model_dump_json()).source == s, f'{s} fail'
print('신 8 enum round-trip ✓')
"
```

---

## 8. rollback (cross-단계 의존)

| 단계 revert | 영향 | cross-단계 의존 |
|---|---|---|
| 단계 4 (E) | ADR-027 §3 폐기 | 무관 (doc-only) |
| 단계 3 (B+B') | Stage 3 + cognitive prompt 9개 복귀 | 단계 1 (C) **함께 revert 필수** (schema-prompt drift) |
| 단계 2 (A+D) | team_catalog 130 line 폐기 | 단계 3 단독 잔존 = LLM 호출 0 risk |
| 단계 1 (C) | Source enum 9 복귀 | 단계 3 (B') 단독 잔존 = ValidationError risk |

전체 revert = 작업 ⑫ 종료 baseline.

---

## 9. 검증 체크리스트

### 9.1 정확성 (1·2차 정정)
- [x] 21 PRODUCES_KEY 표 (.py + yaml 2-key) 실측 정합
- [x] catalog 경로 `cat['teams']['analysis_team']` 정정
- [x] cognitive.yaml L50-52 hardcode 발견 + 단계 B' 신설
- [x] Stage 3 prompt intent 분기 + task×source 매트릭스 (2차 should)
- [x] sprint13 단독 190 / sprint14 단독 103/11 baseline 정정

### 9.2 완전성 (critical/high 해소)
- [x] cognitive.yaml 동반 갱신
- [x] ADR-027 §3 단계 E 신설 + ⑮ scope 분리
- [x] 21 → 8 Source enum 매핑 (§1.1)
- [x] description 단일 진실 = per-tool yaml (D6, 2차 정정)
- [x] ⑱/⑲ 번호 통일 (2차 정정)

### 9.3 실행 안전
- [x] commit 순서 C → A+D → B+B' → E (mid-state risk 해소)
- [x] cross-단계 rollback 매트릭스
- [x] 단계 0 spot-check + Pydantic baseline (2차 신설)
- [x] commit message convention (2차 should)

### 9.4 사용자 원칙 정합
- [x] convention 우선 (description = per-tool yaml 단일 진실, 2차 D6 정정)
- [x] 기본값 없음 (params:[] + helper-B fail-fast)
- [x] POC 단계
- [x] tool / data / agent 분리
- [x] 한 turn ONE 변경 (4 commit, atomic 강화)
- [x] 전문가 단일 권장 (결정 surface 13 → 6 축소, 2차)
- [x] ADR-027 §1 권한 매트릭스 정합

---

## 10. 참조

- 측정 workflow (2026-06-01, 9 agent)
- 1차 검증 (5 agent) — major_revision, 15 → v2
- 2차 검증 (5 agent) — minor_fix_then_proceed, 10 → v3 (3차 우회, ROI 음수)
- ADR-022 / ADR-027 / ADR-014 v2
- 메모리 [feedback_convention_over_hardcoding] / [POC clumi 단일 client] / [v1/v2 섞임 금지] / [한 turn ONE 변경]
- 작업 ⑫ 계획 v3 / compact v5

### 10.1 compact v6 trigger

작업 ⑭ + ⑰ 완료 후 작성.

---

## 11. 변경 이력

| 버전 | 날짜 | 내용 |
|---|---|---|
| v1 | 2026-06-01 | 최초 (3 파일 / 4 commit) |
| v2 | 2026-06-01 | 1차 적대적 검증 major_revision (critical 2 해소). 15 항목, 5 파일 / 4 commit |
| v3 | 2026-06-01 | 2차 적대적 검증 minor_fix_then_proceed (high 1 + medium 4). 10 항목 (must 5: baseline 정정·produces 2-key·⑱/⑲ 번호 통일·D6 single source·⑮ scope 분리 + should 4 + optional 1). 3차 round 우회 (ROI 음수) |

---

## 12. 사용자 결정 surface (v3 최종, 2차 축소)

| # | 결정 | 적용 |
|---|---|---|
| D1 | Source enum +8 + cognitive.yaml 동반 | **옵션 A** |
| D2 | agent | **통합** |
| D3 | 자동화 | **수동 즉시** + ⑲ |
| D4 | Stage 3 prompt | **필수** (intent + 매트릭스) |
| D5 | format_normalizer | **후속 ADR** |
| D6 | description 단일 진실 | **per-tool yaml** 그대로 (2차 정정) |
| (commit 순서) | C → A+D → B+B' → E | 권장 적용 |

**별 작업**: ⑱ (stub 폐기) · ⑲ (자동 sync) · ⑰ (metrics 등재)

---

**상태**: v3 작성 완료. **다음 단계**: 사용자 승인 → commit 0 (계획서) → 단계 0 spot-check → commit 1 (단계 C) 진입.
