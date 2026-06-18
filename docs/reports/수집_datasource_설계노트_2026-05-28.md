# 수집·data_sources 설계 노트 (2026-05-28)

> 점검보고서(아키텍처_의도정합_점검보고서_2026-05-28.md)의 **순위 0.5 「수집·data_sources 재구조화」** 의
> 실행 설계. 사용자 의도(비전공자) + 점검 증거를 종합한 **제안서** — 검토 후 확정하면 이 위에서 코드 착수.
> 해소 대상 오류: **E5(깨진 collector)·E6(중복)·E8(외부/내부 무구분)·E10(mock_api↔raw 2-layer 미구현)**.

---

## 1. 확정된 결정 (이번 라운드)

| # | 결정 |
|---|---|
| D1 | **2-layer 데이터**: 외부 소스(API mock) → 수집 → 내 서버 raw → 하류 tool. 둘 다 존재해야 함. |
| D2 | **수집 = 외부커넥터 / 내부리더 2종**으로 구분 (현재 무구분이 오류). |
| D3 | **구조 = 옵션 C**: 외부 = **플랫폼당 커넥터**(Meta·Naver·Kakao·Google…), 내부 = **generic 내부리더 1개**. |
| D4 | **tool 순수 원칙**: 정제·지표·분석·추론 tool 은 데이터 직접조회/저장 금지. **수집만 fetch 경계**. |
| D5 | **data_sources = 중개자**: 경로/파일 매핑 1곳 + mock→실(API/DB) 교체 seam. |
| D6 | 외부 분류 확정: 13 외부 / 8 내부 (ad_change_history·household_structure = **외부**로). |

---

## 2. 목표 구조 (큰 그림)

```
[외부 = API]                                   [내 서버 = data/{client}]
data/mock_api/{client}/  ─[외부커넥터(플랫폼당)]─┐
  (지금 mock, 미래 실 API)                       ▼
                                          data/{client}/raw/  ◀─[내부리더(generic)]─ data/{client}/ 내부소스
                                            (수집 landing = 표준 raw)        (orders 등 = 내 서버)
                                                  │
                                                  ▼
                              data_sources.get(client, source) ─▶ 하류 tool
                                = data/{client}/raw 읽어 표준 schema 반환   (정제·지표·분석·추론)
```

**핵심**:
- 데이터 위치는 **2개**: `data/mock_api/{client}`(external=API mock) + `data/{client}`(internal=내 서버).
- **external/internal 구분은 폴더가 아니라 *수집 tool* 에서** — 외부커넥터는 mock_api 읽고, 내부리더는 data/{client} 읽음. **클라이언트 폴더를 external/internal 로 쪼개지 않음.**
- 수집만 *바깥*을 만지고, 그 외 tool 은 `data_sources.get()` 으로 *내 raw* 만 받는다.

---

## 3. 데이터 폴더 레이아웃 (둘 다 현존 — 대이동 없음)

```
data/
├── mock_api/{client}/    # external = API mock (현존). 외부커넥터가 읽음. 미래 = 실 API.
│   └─ (지금 client=clumi → data/mock_api/clumi/)
│      외부 13: meta_ads_performance·meta_ads_by_age·meta_instagram_inapp·instagram_engagement·
│      naver_searchad·naver_advoost·naver_talktalk·naver_interest_alert·kakao_bizmessage·
│      ga4_traffic_source·ga4_page_events·ad_change_history·household_structure  (+ 데이터사전 보존)
└── {client}/             # internal = 내 서버 (현존, = data/clumi). 내부리더가 읽음. 미래 = 실 DB.
    ├── raw/              #   수집 landing: 외부 fetch 결과 + 내부 소스(orders 등 8개). data_sources 가 읽음.
    ├── cleaned/          #   workspace (정제 산출)
    └── computed/         #   workspace (계산 산출)
```

- **external/internal 은 폴더가 아니라 *수집 tool* + 매핑표 `kind` 로 구분.** 클라이언트 폴더 밑 external/internal 하위폴더 = ❌ (안 만듦).
- 플랫폼 구분(Meta/Naver…)도 폴더 아님 — 커넥터(코드) + 매핑표 `platform` 필드에만.
- 데이터사전·스키마다이어그램 = `data/mock_api/{client}/` 에 보존(살림).
- **네이밍 통일**: `clumi_mock_NN_*` (옛) → semantic(`naver_talktalk.json`).

---

## 4. 컴포넌트별 책임

### 4.1 외부커넥터 (플랫폼당, 수집 tool)
- 위치: **`collection/external/{platform}_connector.py`** (Meta·Naver·Kakao·Google…).
- 책임: 해당 플랫폼의 *여러 source* 를 그 플랫폼 방식으로 가져옴(인증·페이징·필드 = 플랫폼 캡슐화).
- **mock→API swap = 여기 1곳(플랫폼당)**: 지금 `data/mock_api/{client}` 파일 읽기 / 미래 실 API 호출.
- 산출: 표준 raw → `data/{client}/raw/` 에 저장.
- **재활용**: 현 `collection/`(Sprint15) 6개가 이미 플랫폼당 실 API 인터페이스 → **이걸 수리**(mock_api 읽기 + 새 데이터모델)해서 토대로 씀. (= E5 해소: 삭제 X, 수리 O)

> **코드 폴더 = 수집 2종(external/internal)으로 분리** (2026-05-28 확정): `collection/external/`(커넥터) + `collection/internal/`(리더). 데이터 폴더가 아닌 *코드(tool)* 구조 — data_sources 레지스트리의 `kind` 와 짝.

### 4.2 내부리더 (generic 1개, 수집 tool)
- 위치: **`collection/internal/reader.py`** (param = source).
- 책임: 내부 소스를 읽음. 플랫폼 차이 없어 1개로 충분.
- **mock→DB swap = 여기 1곳**: 지금 `internal/` 파일 / 미래 실 DB 쿼리.
- 산출: 표준 raw → `raw/`.

### 4.3 data_sources (중개자, 수집 아님)
- 책임: `get(client, source)` = `raw/` 에서 읽어 **표준 schema(Pydantic)** 로 반환. 하류 tool 의 유일한 데이터 입구.
- **매핑표 1곳**: `(client, source) → {file, kind: external|internal, platform}` ([현 DEFAULT_MAPPING 확장](../../backend/app/data_sources/file.py#L31)).
- ⚠️ 주의: data_sources 는 *바깥 API 를 호출하지 않음*. 바깥 fetch 는 수집(커넥터)의 몫. data_sources 는 *landing raw 읽기* 만. (= 책임 분리: 수집=ingest / data_sources=serve)

### 4.4 하류 tool (정제·지표·분석·추론)
- `data_sources.get()` 으로 **받은 데이터만** 처리. `self.ds.get` 으로 *직접 fetch 금지* 는 순위 4(tool 순수화)에서 완성. (본 노트 범위는 수집·data_sources 까지)

---

## 5. mock → 실(real) 전환 지점 (한눈에)

| 대상 | 지금 (mock) | 미래 (real) | 교체 위치 |
|---|---|---|---|
| 외부 | `data/mock_api/{client}/*` 읽기 | 실 API 호출 | **플랫폼 커넥터 `_fetch()` 1곳** |
| 내부 | `data/{client}/*` 읽기 | 실 DB 쿼리 | **내부리더 `_read()` 1곳** |
| 하류 | `data_sources.get()` (raw 읽기) | **변화 없음** | — (그래서 하류 tool 은 영향 0) |

→ 사용자 의도("교체 시 한 곳만")는 **플랫폼당 1곳 + 내부 1곳**으로 실현. (단일 함수 1곳이 아닌 이유 = 실 API 가 플랫폼마다 다르기 때문 = 옵션 C 채택 근거)

---

## 6. 현재 → 목표 마이그레이션 (무엇이 바뀌나)

| 단계 | 작업 | 해소 |
|---|---|---|
| M0 | **폴더 대이동 없음** (`data/mock_api/{client}`·`data/{client}` 둘 다 현존). 정리만: ① `mock_api` 에 섞인 내부 source(orders 등)는 제거(API 아님) ② semantic 네이밍 통일 ③ 매핑표에 `kind`(external/internal) 표기 | E8·E10 |
| M1 | 외부커넥터: `collection/`(Sprint15) 6개를 **`collection/external/{platform}_connector.py`** 로 수리 (`data/mock_api/{client}` 읽기, `raw/` 산출, 새 데이터모델) | E5 |
| M2 | 내부리더: **`collection/internal/reader.py`** generic 신설 (`data/{client}` 읽기) | E8 |
| M3 | `collection/raw/` 21 thin wrapper → 위 커넥터/리더로 흡수 후 **은퇴**(중복 제거). `clumi_loader` 의존 끊기 | E6·E3 |
| M4 | `data_sources` 매핑표에 `kind`·`platform` 추가, `get()` = `data/{client}/raw` serve 로 정리 | E10 |
| 검증 | 각 단계 후 `DC-PERM + pytest`. pipeline(orders_collector 등 쓰는 K01 등) 깨지지 않게 단계적 전환 | — |

> ⚠️ pipeline 들이 현 `collection/raw/*` collector 를 step 으로 씀(예: K01 의 `orders_load`). M3 에서 한 번에 지우지 말고 **새 커넥터/리더로 flow step 을 교체하며** 점진 전환 (memory `feedback_no_mixed_codebases`).

---

## 7. 결정 사항 (2026-05-28 확정)

| # | 질문 | 결정 |
|---|---|---|
| Q1 | 데이터 위치 | ✅ **external=`data/mock_api/{client}`(API mock) / internal=`data/{client}`(내 서버). 클라이언트 폴더를 external/internal 로 쪼개지 않음.** |
| Q2 | external/internal 을 어디서 구분? | ✅ **폴더 아님 — *수집 tool* + 매핑표 `kind` 에서만 구분.** 플랫폼 구분도 커넥터(코드)+매핑표 `platform` |
| Q3 | `ad_change_history`·`household_structure` | ✅ external (kind=external). 폴더 귀속 문제 자체가 없음(폴더 안 쪼갬) |
| Q4 | google_ads 등 raw 에 없는 source | ✅ **기록만**. 원칙: source 가 `data/mock_api/{client}` 에 없으면 거기에 **mock raw 생성**(설계문서 먼저 — memory `feedback_mock_raw_design_doc_first`) 후 커넥터가 읽음 |

---

## 8. 다음 단계

1. 본 노트 **검토·확정**(특히 §7 열린 결정).
2. 확정 시 **M0(데이터 이동)부터** 착수. 각 단계 DC-PERM+pytest 검증, 완료 시 커밋.
3. 수집 재구조화(순위 0.5) 완료 후 → 순위 1(이름 정리) → 2(레거시 M2) → … 순.

## 변경 이력
| 일자 | 내용 |
|---|---|
| 2026-05-28 | 초안 — 2-layer(external/internal→raw) + 옵션 C(플랫폼 커넥터+generic 리더) + data_sources mediator + 마이그레이션 M0~M4. E5·E6·E8·E10 해소 설계. |
