# ADR-026: Visualization-First Iterative Design Flow — 10 step 작업 방법론

## Status

**Accepted** (2026-05-28) — 사용자 통찰 *"시각화 → 값 → 방법 → tool/pipeline → 필요 data → raw 검증 → 역방향 정합"* 박제. ADR-024 (V1~V5 검증) 와 *상호 보완* — *어떤 순서로* 작업하는가의 framing.

## Context

### 1. 사용자 통찰 (2026-05-28)

68 spec Batch 5 (Creative) V3 게이트 중 사용자 명시:

> "지금 문제가 근본이 빠졌다. 시각화-어떤방식으로 값이 나오는지 - 값을 만들기위해서는 어떻게 해야하는지 - tool과 파이프라인 구성 - 어떤 data가 필요한가 - 그 data가 실제 raw데이터의 모양인가 검증 - 그 raw data를 기반으로 tool / pipeline이 어떻게 되는가 - 값을 만들 수 잇는가 - 값이 나오는가 - 시각화로 표현되는가
> 이 구조로 작업을 해야해. 그니깐 data가 문제면 data를 바꾸고, tool이 문제면 tool을 추가/수정, 그리고 파이프라인을 만들고 해야해"

→ 본 시스템의 기존 작업 = **본말전도** (기존 mock 데이터 → 거기서 유추한 시각화). 사용자 의도 = **시각화 출발 → 역방향 정합**.

### 2. 기존 ADR 의 빈 영역

| ADR | 역할 | 본 ADR 영역 |
|---|---|---|
| ADR-022·023·025 | 시스템 *구조* (DataSource·5 주체·3 Layer) | (구조) |
| ADR-024 | 작업 *검증 사이클* (V1~V5) | (검증) |
| **ADR-026 (본)** | 작업 *순서* (10 step) | ⭐ |

→ ADR-024 = *어떤 검증* / ADR-026 = *어떤 순서*. 상호 보완.

### 3. 기존 batch (68 spec) 의 작업 평가

| Batch | 작업 흐름 | 평가 |
|---|---|---|
| Batch 1 (Dashboard1 clumi) | ✅ 시각화 → tool → raw (정방향) | 🟢 모범 사례 |
| Batch 2·3 (Dashboard v1·Channel blooming) | ⚠️ raw → 시각화 (역방향) | 🟠 부분 위반 |
| Batch 4·5 (Trend·Creative blooming) | ❌ raw 사전박힘 가정 | 🔴 명백 위반 |

→ **본 ADR 의 즉시 적용 필요성** = 명백 위반 박제.

### 4. 산업 표준 매핑

| 패턴 | 본 ADR 대응 |
|---|---|
| User Story → Acceptance Criteria → Test (BDD) | 시각화 → 결과값 → 검증 |
| Domain-Driven Design (DDD) 의 *Ubiquitous Language* | 시각화 정의 (step 1) = ground truth |
| Specification by Example (Gojko Adzic) | step 6 raw 검증 = 실 예시 정합 |
| Data Mesh (Zhamak Dehghani) 의 *outcome-driven product* | step 1·2 = outcome 명시 |

→ **본 ADR = 산업 표준의 본 시스템 정합 박제**.

## Decision

### 1. 10 step 정밀화

| # | Step | 정의 | 진입 조건 | 산출물 | 실패 시 → |
|:---:|---|---|---|---|---|
| **1** | **시각화 정의** | 차트·표·KPI·인사이트 *구체 형태* 명세 | 사용자 요청·기획서 | 시각화 ID + 형태 + 단위 | (시작 step — 요청 자체 재정의) |
| **2** | **결과값 정의** | 시각화에 들어가는 *수치·텍스트·구조* 명세 | step 1 완료 | 결과 schema | step 1 재정의 |
| **3** | **방법 정의** | 결과값 산출 *방법론* (sum/groupBy/top-N/NLP 등) | step 2 완료 | methodology ID + 한 줄 설명 | step 2 재정의 |
| **4** | **구조 가설** | tool / pipeline 가설 | step 3 완료 | YAML 가설 (Pipeline name + steps[] + cache 키) | step 3 재정의 |
| **5** | **필요 data 정의** | *입력 필요한 raw 형태* 명세 (논리 schema) | step 4 완료 | 표준 schema | step 4 재정의 |
| **6** | **raw 검증** ⭐ | *현 raw 가 그 모양인가?* — 역방향 정합 | step 5 완료 | PASS / WARN / FAIL | **3 분기 ⭐ — §2** |
| **7** | **raw 기반 재설계** | step 6 결과 반영 — data·tool·pipeline 정정 | step 6 완료 | 정정된 YAML + 정규화 layer 명세 | step 4·5 재진입 |
| **8** | **산출 가능성 검증** | *정의된 방법으로 값 산출 가능?* — *논리* 검증 | step 7 완료 | pass/fail + 누락 영역 | step 7 재진입 |
| **9** | **값 산출** | 실제 *코드 실행* — Pipeline Runner 시도 | step 8 PASS + Phase 1 코드 존재 | 산출물 파일 (Workspace) | step 7·8 재진입 |
| **10** | **시각화 표현** | frontend 가 *실제로 그리는가* | step 9 PASS | 페이지 렌더링 확인 | step 7 재진입 |

### 2. step 6 (raw 검증) 의 3 분기 ⭐

| 결과 | 행동 |
|:---:|---|
| **✅ PASS** | raw 가 정확히 그 모양 → step 7 진행 |
| **⚠️ WARN** | raw 모양 다름 (컬럼명·형식·정규화 필요) → (a) raw 정규화 layer (DataSource — ADR-027) **또는** (b) raw 자체 변환 (mock 이라 가능) |
| **🔴 FAIL** | 필요 raw 자체 부재 → (a) 외부 데이터 추가 입력 **또는** (b) mock raw 생성 **또는** (c) 시각화 재정의 (step 1 회귀) |

→ **mock data 이기 때문에 raw 자체 변경 가능** = 본 framing 의 *핵심 자유도*. POC 단계의 *비밀 무기*.

### 3. ADR-024 V1~V5 매핑

| ADR-024 검증 | ADR-026 step |
|---|---|
| **V1 코드 정합** | step 6 (raw 검증) + step 9 (값 산출) |
| **V2 Cross-reference** | step 4 (구조 가설) + step 7 (재설계) |
| **V3 사용자 검토 게이트** | step 1·3·6·10 *반드시 stop* |
| **V4 정답값 보존** | step 9 — clumi 정답 17 같은 fixture |
| **V5 영역 침범 X** | step 4·7 — 책임 분담 (ADR-027 정합) |

### 4. Loop 중단 조건 (무한 loop 방지)

| 조건 | 행동 |
|---|---|
| 같은 step *3회 이상 실패* | 상위 step 회귀 (예: step 6 3회 fail → step 1 재정의) |
| 사용자 검토 게이트에서 *3 라운드 미해결* | 별 ADR 신설 (예: 본 ADR 자체가 그 사례) |
| step 1 자체 재정의 (시각화 변경) | *별 사이클* 시작 — 본 시각화 보류 박제 |

### 5. 적용 의무 매트릭스

| 작업 유형 | 본 흐름 적용 |
|---|---|
| 신규 시각화 / pipeline | ✅ 의무 (10 step 전수) |
| 기존 spec 보강 (시각화 변경 X) | ⚠️ step 4~10 만 |
| 사소 정정 | — (ADR-024 V3 만) |
| ADR / 메타 작업 | — (ADR-024 적용) |

### 6. 기존 batch *재검토 결과*

| Batch | step 1·2·3 | step 5 | step 6 | step 7 | 평가 |
|---|---|---|---|---|---|
| **Batch 1** (Dashboard1 clumi) | ✅ | clumi orders 등 | ✅ PASS (B1 진짜 raw) | ❌ | 🟢 모범 |
| **Batch 2** (Dashboard v1) | ✅ | blooming campaigns | ⚠️ 한글 컬럼 hardcode | ⚠️ normalizers 필요 | 🟠 부분 |
| **Batch 3** (Channel) | ✅ | blooming channel_perf | ⚠️ 동일 | ⚠️ 동일 | 🟠 부분 |
| **Batch 4** (Trend) | ⚠️ (감성·키워드 mock 가정) | review_trends + daily_perf | 🔴 C08·C12·O03 = B2b ml_mock | 🔴 ml_models/ + ml_mock 박제 | 🔴 명백 |
| **Batch 5** (Creative) | ⚠️ (AI 5축 mock 가정) | creatives + ab_tests | 🔴 C11·K21 = B2b ml_mock + YAML hardcode | 🔴 동일 + YAML 추상화 | 🔴 명백 |

→ **Batch 4·5 = step 1·6 재진입 필요**. R7 commit 동반 spec 정정.

### 7. F 사이클 (Batch 6 Cost+AI) = *본 ADR 첫 모범 사례*

| 영역 | 이전 batch | F 사이클 |
|---|---|---|
| 작성 순서 | raw → 시각화 (역방향) | **본 ADR step 1~10 적용** |
| hardcode | 박힘 가능 | **금지** (ADR-028) |
| ml_mock | 표시 부재 | **ADR-028 B2b 명시** |

## Consequences

### 긍정

| 영역 | 효과 |
|---|---|
| 본말전도 회피 | 시각화 출발 + 역방향 정합 |
| mock 자유도 활용 | step 6 FAIL 시 *raw 자체 변경 가능* (POC 단계의 자유) |
| 정답값 보존 | step 9 = ADR-024 V4 |
| 다음 작업자 가이드 | 10 step 명시 → 신규 시각화 작업 표준 |

### 비용

| 영역 | 비용 |
|---|---|
| 신규 시각화 시간 ↑ | 단순 추가 보다 2~3 배 (검증 step 포함) |
| 기존 batch 재검토 ↑ | R7 commit + Phase 1 동반 |

### 완화

| 비용 | 완화 |
|---|---|
| 신규 시간 ↑ | 검증 step 으로 *후속 수정* 회피 → 총 비용 ↓ |
| 재검토 ↑ | spec 표면 정정만 (코드 정정 = Phase 1) |

## Alternatives

### A. raw → 시각화 (역방향) — *기각*
- 장: mock 데이터 기반 spec 작성 단순
- 단: 사용자 의도 위배 (시각화 = ground truth 아니라 mock 종속)

### B. 시각화 → 코드 (step 1·9·10 만) — *기각*
- 장: 빠름
- 단: step 6 raw 검증 누락 → 코드 단계에서 *대규모 정정* 위험

### C. step 6 PASS 만 진행, WARN/FAIL = 시각화 제거 — *기각*
- 장: 안전
- 단: mock raw 변경 가능성 = POC 의 핵심 자유도 포기

### D. 본 ADR (10 step 정밀화) — *채택*
- 장: 사용자 의도 + 산업 표준 + POC 자유도 모두 만족

## Related

| ADR / Spec | 관계 |
|---|---|
| [ADR-024](ADR-024_iterative_spec_refinement.md) | V1~V5 검증 = 본 ADR step 의 *검증 도구* |
| [ADR-027](ADR-027_five_actor_permission_separation.md) | 본 ADR step 4·7 의 *책임 분담* |
| [ADR-028](ADR-028_hardcode_prohibition_and_raw_classification.md) | 본 ADR step 6 의 *판단 기준* (raw 4 분류) |
| [ADR-029](ADR-029_folder_naming_principles.md) | 본 ADR step 7 의 *폴더 명명* |
| [65 spec §14.6](../65_dashboard_pages_v1.0.md) | tool chain = step 4 가설 박제 |
| [68 spec](../68_pipeline_catalog_v1.0.md) | Pipeline YAML = step 4~7 산출물 |

## 변경 이력

| 일자 | 내용 |
|---|---|
| 2026-05-28 | 초안 — Accepted. 사용자 통찰 "시각화 → 역방향 정합" 흡수. 10 step 정밀화 + step 6 의 3 분기 (PASS·WARN·FAIL) + ADR-024 V1~V5 매핑 + Loop 중단 (3 회 실패 회귀) + 적용 의무 매트릭스 + 기존 batch 재검토 결과 (Batch 1 모범 / 2·3 부분 / 4·5 명백 위반) + F 사이클 첫 모범 사례 박제. 본 ADR = ADR-024 의 *작업 순서* 보완. POC v1 Phase 1 진입 *전* 의무 적용. |
