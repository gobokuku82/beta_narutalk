# C:LUMI 데이터 파이프라인 계획서 — 데이터 검증 리포트 (3회 사이클)

> ⚠️ **OUTDATED (2026-05-27 이후)** — 파이프라인 backend tool 의 path/class 명은 옛 것.
> - `collection/clumi/` → `collection/raw/` (commit cadc95b)
> - `preprocessing/clumi/` → `preprocessing/marketing/` (commit f7de6c4)
> - tool 의 data 로드: `load_clumi_source(N)` → `self.ds.get(client, "<source_id>")` 로 전환
> - data/ 폴더 (raw 21 source) 와 검증 *산출값* 은 그대로 유효 (cache 보존).
> - 새 위치: `docs/_claude/architecture/`, 회복: `docs/reports/session_compact_recovery_2026-05-27.md`

---

## 0. 메타

| 항목 | 내용 |
|---|---|
| 작성일 | 2026-05-22 |
| 위치 | `docs/reports/data_pipeline_verification_2026-05-22.md` |
| 검증 대상 | `docs/_claude/data/데이터_파이프라인_구조_계획서_2026-05-21.md` (데이터 파이프라인 구조 계획서) |
| 검증 데이터 | `data/clumi/` 20 소스 + 벤더 설명 문서 3종(`README.md`·`clumi_data_dictionary.csv`·`clumi_schema_diagram.md` — 검증 후 `data/clumi/description/` 로 이동) |
| 후속 산출 | 본 검증 기반으로 `docs/_claude/data/data_description/` 에 정확 명세 생성 (`raw_데이터_설명서_2026-05-22.md` + `clumi_데이터사전_검증본.csv`) — 벤더 dictionary 대체 |
| 방법 | 실제 파일 전수 파싱(Python) ↔ 계획서·설명 문서 대조, **3회 사이클** |
| 결론 | 계획서 **골격 유효** — 데이터 사실 **10건 정정**. 핵심 교훈: 설명 문서가 아닌 **실제 파일이 유일한 진실 소스** |

---

## 1. 목적·범위·방법

**목적** — 계획서가 의존하는 데이터 사실(구조·관계·단위·재현 가능성)이 실제 파일과 일치하는지 검증하고, 불일치를 계획서에 반영한다.

**방법** — 3회 사이클. 각 사이클 후 발견을 계획서에 즉시 반영하고 변경 이력에 기록.

| 사이클 | 검증 영역 |
|---|---|
| 1차 | 실제 파일 구조 — 형식·중첩·행수·키 |
| 2차 | 설명 문서(dictionary/README) 대조 + 파일 간 정합성 + 재현 가능성 |
| 3차 | 측정 단위·날짜 형식·엑셀 변환 적합성 |

---

## 2. 1차 검증 — 실제 파일 구조

20개 파일을 전수 파싱(`json.load`/`csv`/`jsonl` 스트리밍/SQL 정규식).

**주요 발견:**

| # | 발견 | 계획서 초안 | 조치 |
|---|---|---|---|
| 1-1 | Meta 01·02·03 의 중첩 배열이 `actions` 1개가 아니라 **4개** (`actions`·`action_values`·`cost_per_action_type`·`purchase_roas`) | "중첩 `actions[]` 1개" | §2.2 정정 — 4종 피벗 |
| 1-2 | #16 `kakao` 캠페인에 `targeting` 키 **없음** (`message_content`·`summary`·`results_sample`) | "`targeting` 포함" | §2.2 정정 |
| 1-3 | #17 `talktalk` 캠페인에 `message_blocks[]`(3블록) 존재 | 미언급 | §2.2·§4.1 추가 |
| 1-4 | JSON `data[]`/`campaigns[]` 길이 전수 = README 카탈로그와 일치 | — | ✅ 확인 |

---

## 3. 2차 검증 — 설명 문서 대조 + 정합성 + 재현성

### 3.1 `data_dictionary.csv` 불일치 ★ (핵심 발견)

**20개 중 19개 파일에서 dictionary 가 실제 구조와 불일치.** `#05 orders` 만 정확.

| # | dict 컬럼 | 실제 키/컬럼 | 불일치 유형 |
|---|---|---|---|
| 01 | 18 | 26 | `roas` 있다 했으나 실제 없음(→`purchase_roas[]`). `actions.*` 평면 표기 |
| 02 | 9 | 27 | 컬럼 대부분 누락 |
| 03 | 8 | 28 | 컬럼 대부분 누락 |
| 04 | 17 | 17 | **컬럼명 전부 다름** — dict `kwd/camp_id/stat_dt` ↔ 실제 `nccKeywordId/nccCampaignId/statDt` |
| 06 | 18 | 26 | dict `membership_grade/point` ↔ 실제 `member_grade/available_point` |
| 09 | 22 | 32 | 컬럼 다수 누락 |
| 10 | 17 | 18 | `last_order_date` 누락 |
| 12 | 12 | 18 | 컬럼 다수 누락 |
| 13 | 11 | 22 | 컬럼 다수 누락 |
| 15 | 15 | 23 | 컬럼 다수 누락 |
| 19 | 11 | 13 | 컬럼 다수 누락 |

추가로 README "빠른 분석 가이드" 의 필드 표기(`#01.actions.purchase_value` 등)도 실재하지 않는 평면 표기를 사용 — 신뢰 불가.

**반면 정확한 것:** README 카탈로그의 행/건수(20 소스 전부), GA4 이벤트 종류(#07 3종·#08 9종), `schema_diagram.md` 의 join key.

→ 계획서에 **§2.6 신설** + **D11**(실제 파일이 진실 소스) 추가.

### 3.2 파일 간 정합성 — 전부 정상

| 관계 | 검증 결과 |
|---|---|
| `orders.member_id` ⊆ `customers` | ✅ 외부 0건 (회원 주문 1,426 distinct) |
| `signup.member_id` ⊆ `customers` | ✅ 외부 0건 (600) |
| `rfm.member_id` == `customers` | ✅ 1:1 완전 (8,500 = 8,500) |
| `orders.order_id` ⊇ GA4 #07 `purchase.transaction_id` | ✅ 1,823 전부 부분집합 |
| GA4 #08 (user,session) ⊆ #07 | ✅ 23,985 쌍 전부 부분집합 |
| GA4 `user_id` ⊆ `customers` | ✅ 외부 0건 (1,421 distinct, #07 행의 81%는 비로그인 NULL) |
| `signup.ga_client_id` ↔ GA4 | 49% 매칭 (README "50%" 와 부합) |

→ **소스 간 join 은 안전.** 계획서 §2.5 에 검증 스탬프 추가.

### 3.3 재현 가능성 검증

| 대상 | 발견 | 계획 영향 |
|---|---|---|
| #10 `customer_rfm` | `rfm.frequency`==`customers.total_orders`, `rfm.monetary`==`customers.total_purchase_amount` 가 **8,500건 전부 일치** | RFM 의 R/F/M 은 `customers`(#06) **평생 집계 컬럼**서 유도 — `orders`(4월 한정) 아님. §2.3·§4.3 정정 |
| #12 `category_sales` | 155행 = **30 일별 + 1 월별 rollup** (`stat_date` 31종) | 재현 시 이중 집계 주의. §4.3 명시 |

### 3.4 SQL·기타 구조

| 항목 | 결과 |
|---|---|
| #11 `promotions.sql` | 3 테이블 — `promotions`(5행)·`promotion_performance`(5)·`promotion_usage_history`(863, 9개 batched INSERT) |
| #11 "823건" 표기 | 863행 중 미취소(`order_status`≠`C40`) = 정확히 823 → schema_diagram **오류 아님** |
| #18 `crm_messages.sql` | 3 테이블 — `crm_campaigns`(4)·`crm_message_variants`(7)·`crm_send_logs`(7) |
| #20 `extra_data` | JSON 문자열, 50/50 파싱 가능. 키 **34종 희소** → long/JSON 보존 권장 |

---

## 4. 3차 검증 — 단위·날짜·엑셀 적합성

| 항목 | 발견 | 계획 영향 |
|---|---|---|
| ROAS 단위 | Meta `purchase_roas` 실측 **0.94~3.13**(비율) / Naver `#04 ror` **855~6036**·`#15 roas` **0~1068**(백분율) | §2.4 단위 행 — 실측 범위 확인, 계획 일치 ✅ |
| 날짜 범위 | 전 파일 2026-04, GA4 는 UTC(`20260331`부터 = KST 4/1) | §2.4 시간 행 일치 ✅ |
| #04 날짜 형식 | `statDt` = `YYYY-MM-DD` — `schema_diagram §5` 가 `YYYYMMDD` 라 한 건 **오류** | §2.2·§2.6 정정. 시간 형식 5종→**6종** |
| #14 instagram `insights` | **Reels(12지표)/일반(9지표) 2변형** | §4.1 피벗 — 합집합 ~12키 |
| GA4 엑셀 적합성 | #08 = 84,143행·평탄화 후 ~101컬럼 → **Excel 한도(1M행/16k열) 내** | §4.1 **"행 한계" 오류 정정** — 실 제약은 265MB 크기·메모리 |
| `channel_attribution` | 10개 채널 깔끔히 분포 (unknown 500 … kakao_message 60) | §4.3 채널 데이터셋 근거 — 정상 |

---

## 5. 발견 종합

| # | 항목 | 설명 문서 / 계획서 초안 | 실제 | 심각도 |
|---|---|---|---|---|
| 1 | `data_dictionary.csv` 컬럼 정의 | 정확하다고 가정 | 19/20 불일치 | **높음** |
| 2 | Meta 01·02·03 중첩 배열 | `actions` 1개 | 4개 | 높음 |
| 3 | Meta flat `roas` | 존재 | 없음 (`purchase_roas[]`) | 높음 |
| 4 | §2.2 CSV 컬럼 수 7개 | dictionary 값 | 실측치 | 중간 |
| 5 | #10 RFM 재현 입력 | `customers`+`orders` | `customers` 평생집계 (orders 아님) | 중간 |
| 6 | #12 category_sales 구조 | 월·일별 | 30 일별 + 1 월별 rollup | 중간 |
| 7 | GA4 `.xlsx` 제약 | "행 한계" | 행/열 한도 내 — 크기 제약 | 중간 |
| 8 | #04 `statDt` 형식 | `YYYYMMDD` (schema_diagram) | `YYYY-MM-DD` | 낮음 |
| 9 | #14 insights 메트릭 | 단일 키 집합 | Reels/일반 2변형 | 낮음 |
| 10 | #11 "823건" | (1차에서 오류로 의심) | 863행 중 미취소분 — 정확 | 낮음(자기정정) |

---

## 6. 계획서 수정 내역

3회 사이클로 계획서 `데이터_파이프라인_구조_계획서_2026-05-21.md` 에 반영 (해당 문서 변경 이력 참조):

- **§2.6 신설** — 데이터 설명 문서 검증 결과 (dictionary 19/20 불일치)
- **§2.2 전수표** — 01·02·03·04·06·09·10·11·12·13·15·16·17·18·19·20 정정 (키/컬럼 수·중첩 구조·SQL 행수)
- **§2.4 횡단 이슈** — Meta 중첩 지표 행 추가, 실측 단위 범위, #04 키워드 부재, 시간 형식 6종
- **§4.1 기능 1** — "스키마는 실제 파일서 도출" 결정, GA4 엑셀 제약 정정
- **§4.3 기능 3** — RFM 입력 = customers 평생집계, category rollup, GA4 퍼널 91% 한계
- **§8 D11** 추가 (실제 파일 = 진실 소스) · **§9 Q5·Q6** 추가 (Meta action_type·#04 키워드 매핑)

---

## 7. 결론

| 판정 | 내용 |
|---|---|
| **계획서 골격** | ✅ 검증 통과 — 4단계 레이어 모델·기능 5+1 매핑·결정론 원칙·작업 분담은 변경 없음 |
| **데이터 사실** | 10건 정정 — 모두 §5 표에 기록 |
| **파일 간 정합성** | ✅ 깨끗 — member_id·order_id·GA4 세션 join 전부 정상. 소스 간 계산 안전 |
| **핵심 교훈** | `clumi_data_dictionary.csv` 와 README "빠른 분석 가이드" 필드 표기는 **신뢰 불가**. 구현 시 **실제 파일을 스캔해 스키마 도출** (D11) |
| **유효한 설명 문서** | README 카탈로그(행수·소스 목록)·`schema_diagram.md` join key 는 정확 — 계속 활용 (단 §5 시간표 #04 항목 제외) |

→ 검증 완료. 계획서는 데이터 사실과 일치하는 상태로 수렴했으며, 다음 단계(세부 구현 계획)로 진행 가능.
