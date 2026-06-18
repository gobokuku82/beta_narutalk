# 38. 외부 API 수집 → 회사 DB 저장 아키텍처 (Collection→Storage)

> **상태**: as-built 박제 + MVP 방향 (2026-06-09). 진실 소스 = 코드(`backend/`).
> **의도**: "외부 API에서 데이터 수집 → 회사 내부 DB(`octormate_data.{client}._workspace` raw, 과거엔 `data/{client}/raw/` 파일)에 저장." 이 사용자 의도가 코드 어디에 어떻게 구현돼 있는지 + 아직 mock 인 부분을 한 곳에 정리.
> **이미 분산 문서 있음 (본 문서 = 통합 hub)**: [ADR-022](adr/ADR-022_data_source_workspace_layer_separation.md)(DataSource/Workspace 관절·mock→real seam) · [ADR-027](adr/ADR-027_five_actor_permission_separation.md)(DataSource 책임) · [ADR-028](adr/ADR-028_hardcode_prohibition_and_raw_classification.md)(raw 4분류) · [수집·datasource 설계노트](../reports/수집_datasource_설계노트_2026-05-28.md)(M0~M4 mock→실 교체) · [33_collection](33_tools_by_category/33_collection.md)(수집 tool 인벤토리) · [35_DB_SCHEMA](35_DB_SCHEMA_v1.0.md) · [36_clumi_mock_raw](36_clumi_mock_raw_data_design_v1.0.md).

---

## 1. 사용자 의도 (박제)

```
외부 플랫폼 API ──수집──▶ 회사 내부 DB ──소비──▶ tool/분석
(Meta·Naver·         (raw 저장 =          (집계·시각화)
 Kakao·Google …)      "원천 적재")
```

- **2종 분리** (memory `project_collector_two_kinds`):
  - **external** = 외부 API에서 *수집해야* 하는 데이터 (광고 성과·GA4 등). 원천 = 플랫폼 API (현재는 **mock_api 로 시뮬레이션**).
  - **internal** = 회사 자체 데이터 (주문·고객·소재·캠페인·목표 등). 원천 = 회사 DB/파일 자체 = **`data/{client}/raw/` 가 곧 원천** (그 앞단계 없음).
- "회사 내부 DB 저장" = POC 에서는 **Postgres `octormate_data.{client}._workspace(layer='raw')`** (DB 도입 전엔 `data/{client}/raw/` 파일이 그 역할).
- 왜 2종인가: external 은 플랫폼마다 schema·인증·주기가 제각각 → 커넥터로 흡수해야 함. internal 은 우리가 구조를 통제 → 직접 읽으면 됨.

---

## 2. As-built 파이프라인 (검증됨)

데이터가 Postgres raw 로 들어오는 **진입점은 2개**다.

```
[A. 초기 부트스트랩 — seed]
data/{client}/raw/*  (30 소스, ext+int 전부) ─ load_raw_to_data_db.py ─▶ {client}._workspace(raw)
                                               (소형 blob / 50MB+ jsonl 스트리밍)

[B. 런타임 수집 — external 만]
data/mock_api/{client}/*  ─ ExternalRawCollector._fetch_from_mock_api ─┬─(file BE)─▶ data/{client}/raw/ 복사
   (외부 API 시뮬레이터)                                                 └─(pg BE)──▶ {client}._workspace(raw) upsert

[internal 은 수집 단계 없음]
InternalRawCollector ─ ds.get(client, source_id) ─▶ raw 를 "읽기"만 (mock_api 안 거침)
```

### external_flow
`ExternalRawCollectorBase._fetch_from_mock_api`([_base.py](../../backend/app/dream_agent/tools/collection/_base.py) L164~) 가 `data/mock_api/{client}/clumi_mock_*_{stem}.{ext}` 를 읽고 백엔드에 따라 분기(L195~):
- **file 백엔드**: `_fetch_to_file`(L200~) — `data/{client}/raw/{filename}` 로 복사 + mtime 갱신 시 `raw_history` 보관.
- **postgres 백엔드**: `_fetch_to_workspace`(L230~) — `_parse_raw_file` 파싱 후 `get_default_workspace().save("raw", filename, …, client)` → `{client}._workspace(raw)` upsert.

### internal_flow
`InternalRawCollectorBase`([_base.py](../../backend/app/dream_agent/tools/collection/_base.py) L135~)는 별도 수집 로직 없이 부모 `RawCollectorBase.execute`(L97~) → `ds.get(client, source_id)` 로 **raw 를 읽기만** 한다. (ds = FileDataSource → `data/{client}/raw/` / PostgresDataSource → `{client}._workspace(raw)`)

### seed_flow
`load_raw_to_data_db.py`([script](../../backend/scripts/load_raw_to_data_db.py)) — `EXCLUDE={pipeline, mock_api, description}`(L30)로 **mock_api 를 client 에서 제외**, `data/{client}/raw/` 의 30 소스를 `FileDataSource.get`/`stream_jsonl` 로 읽어 `PostgresWorkspace.save`/`save_stream` 로 `{client}._workspace(raw)` 적재. `setup_data_db.py` 는 `data/{client}/computed/` 만(역시 mock_api 제외, L50).
→ **Postgres 의 실제 seed 원천은 `data/{client}/raw/` 이지 mock_api 가 아니다.** mock_api 는 런타임 external 수집기만 읽는다.

### DATA_BACKEND 토글
`api_v2/main.py` lifespan(L86~102): `settings.DATA_BACKEND=="postgres"`(기본값 `"file"`, [config.py](../../backend/app/core/config.py)) 이면 `set_workspace(PostgresWorkspace())` + `set_data_source(PostgresDataSource())`. 이후 모든 tool 이 `get_default_workspace()`/`get_default_data_source()` 싱글톤 경유로 무관하게 동작. 변환 실패 시 file 백엔드로 폴백(경고). 현재 `.env` = `DATA_BACKEND=postgres` 활성.

---

## 3. 소스 레지스트리 현황 (★ 카운트 정정)

**`SOURCE_REGISTRY`** ([file.py](../../backend/app/data_sources/file.py) L45~84) = **external 16 + internal 14 = 30 소스**.
**collector 클래스** = **external 13 + internal 8 = 21종** (FILE_NO 레거시 매핑 기반).

> ⚠️ 기존 문서/주석의 "external 13 + internal 8" 은 **collector 클래스 수**이고, **레지스트리(30)** 와 다르다. 차이 9종 = collector 없이 raw 로만 존재하는 소스. (예: [33_collection](33_tools_by_category/33_collection.md) 의 "13+8" 은 collector 기준이라 레지스트리 카운트로 오독 금지.)

| 구분 | 레지스트리 | collector 클래스 | collector 없는 소스 | 의미 |
|---|---|---|---|---|
| external | 16 | 13 | **reviews · keyword_performance · daily_performance** (3) | 🔴 **갭** — external 인데 mock_api·collector 둘 다 없음. 손으로 둔 raw 파일로만 존재 → 수집 경로 부재 |
| internal | 14 | 8 | campaigns · creatives · budget_allocation · ab_tests · marketing_targets · channel_targets (6) | 🟢 정상 — internal 은 수집 불요(raw 직접 읽음) |

→ **사용자가 "수집부가 덜 구현됐다"고 느낀 실체** = external 3종(reviews·keyword_performance·daily_performance)이 external 로 분류돼 있으나 수집 경로(mock_api+collector)가 없는 점. MVP 진입 시 ① 실제 API 커넥터를 붙이거나 ② internal 로 재분류 결정 필요.

---

## 4. mock → real (MVP 방향)

- **현재(POC)**: `_fetch_from_mock_api` 가 `data/mock_api/{client}/` 테스트 파일을 읽음 = **외부 API 시뮬레이터**. 실 API 없이 end-to-end 검증용.
- **MVP+**: external collector 서브클래스([external/*.py](../../backend/app/dream_agent/tools/collection/external/))의 fetch 로직을 **실 플랫폼 SDK 호출로 교체** (Meta Marketing API·Naver SearchAd·GA4 Data API 등). tool 인터페이스(`DataSource.get` 출력 계약)는 불변이라 **수집기만 업그레이드**하면 됨 — 이게 ADR-022 가 박제한 "관절(seam)".
- **internal 은 교체 불요** — 항상 회사 DB/파일 직접 읽기.

### 아직 문서화/구현 안 된 것 (추후 결정)
1. **실 API 커넥터 구현 전략** — 플랫폼별 인증·토큰 관리, rate limit, schema 정규화(normalizer) 파이프라인. (현재 normalizer 부재 — ADR-029 참조)
2. **Postgres raw 테이블 설계** — CSV→`{client}._workspace` 적재 시 full refresh vs CDC, validation 규칙.
3. **external 3 orphan 소스 처리** — reviews·keyword_performance·daily_performance 를 실 API 붙일지 internal 재분류할지.
4. **mock_api 장기 용도** — MVP 이후 시뮬레이터로 유지(테스트용)할지 폐기할지.

---

## 5. 코드 참조 (진실 소스)

| 영역 | 파일 | 심볼 |
|---|---|---|
| 소스 레지스트리 | [data_sources/file.py](../../backend/app/data_sources/file.py) | `SOURCE_REGISTRY` (L45~84), `source_kind`/`sources_by_kind` |
| 수집기 공통 | [tools/collection/_base.py](../../backend/app/dream_agent/tools/collection/_base.py) | `RawCollectorBase`(L97~), `ExternalRawCollectorBase`(L145~: `_fetch_from_mock_api`/`_fetch_to_file`/`_fetch_to_workspace`), `InternalRawCollectorBase`(L135~) |
| external 수집기 13 | [tools/collection/external/](../../backend/app/dream_agent/tools/collection/external/) | `*_collector.py` |
| internal 수집기 8 | [tools/collection/internal/](../../backend/app/dream_agent/tools/collection/internal/) | `*_collector.py` |
| 읽기(파일) | [data_sources/file.py](../../backend/app/data_sources/file.py) | `FileDataSource` (L108~) |
| 읽기(PG) | [data_sources/postgres.py](../../backend/app/data_sources/postgres.py) | `PostgresDataSource` (L38~) |
| 쓰기(PG) | [workspace/postgres.py](../../backend/app/workspace/postgres.py) | `PostgresWorkspace.save`/`save_stream` |
| seed 스크립트 | [scripts/load_raw_to_data_db.py](../../backend/scripts/load_raw_to_data_db.py) · [scripts/setup_data_db.py](../../backend/scripts/setup_data_db.py) | `EXCLUDE`(mock_api 제외), `load_client` |
| 백엔드 토글 | [api_v2/main.py](../../backend/api_v2/main.py) | lifespan `DATA_BACKEND` (L86~102) |
| DI 싱글톤 | [data_sources/__init__.py](../../backend/app/data_sources/__init__.py) · [workspace/__init__.py](../../backend/app/workspace/__init__.py) | `get_default_*` / `set_*` |

---

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-06-09 | v1.0 신규 — 사용자 질문("external API→회사 DB 저장 의도가 덜 반영된 듯, 문서 있나?") 대응. 3-agent workflow(`wf_c960b7b0`) 로 기존 문서 인벤토리 + as-built 코드 매핑 + 적대적 검증. 검증 정정: 레지스트리 16+14=30 vs collector 13+8=21, external 3 orphan(reviews·keyword_performance·daily_performance) 식별. 기존 분산 문서(ADR-022/027/028·설계노트·33·35·36) 통합 hub. |
