# DreamAgent V2 — Vision & Intent

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-04-28 |
| 작성자 | 사용자 (§1, §3, §5, §6) + Claude (§2, §4, §7) |
| 위치 | `docs/agent_specs/00_vision_and_intent.md` (agent_specs 폴더 최상단 — 모든 spec 의 north star) |
| 권한 | §1 / §3 / §5 / §6 = 사용자 전용 수정 / §2 / §4 / §7 = Claude 갱신 (사용자 검토) |
| 상태 | ✅ **v1.0 lock** (2026-04-28 사용자 검토 통과) |

---

## 0. 본 문서의 역할

**모든 후속 결정 (Sprint / ADR / Spec / 코드) 의 north star**.

다른 문서가 모호할 때 본 문서를 참조. 본 문서는 vision (최상위) 이라 자주 변경되지 않음. 변경 시 모든 하위 문서 영향 검토 필수.

본 문서가 다루지 않는 것:
- 세부 시스템 spec (→ `docs/agent_specs/` 하위 번호 문서)

---

## 1. 컨셉 (Vision) — 사용자 verbatim

> 사용자와 에이전트의 파트너쉽을 통한 생동형 AI 를 만든다. 클로드나 제미나이처럼 사용자와 LLM 이 서로 브레인스토밍도 하고, 토론을 하면서 더 좋은 계획을 세운다. 실행 에이전트는 function / graph 구조로 만들어져 있고 사용자의 의도를 파악해 todo plan 을 만들고 수정 / 삭제 / 보완을 할 수 있다.
>
> (브레인 스토밍의 의미는 사용자가 어떤 todo 가 작동할지 모르니, 에이전트와의 소통을 통해 만드는 것이고 이게 앱의 자료이고 / 각 기업의 암묵지를 패턴화해서 각 기업의 맞춤형 에이전트를 만드는 것이다.)

### 핵심 키워드

- **파트너쉽** — 사용자 ↔ 에이전트 동등 협업 (사용자가 모든 걸 알 필요 없음)
- **생동형** — 정적 ≠ 살아있는 / 진화하는
- **브레인스토밍** — 사용자가 모르는 것을 대화로 발견
- **암묵지 패턴화** — 대화 누적 = 기업별 맞춤 데이터
- **맞춤형 에이전트** — 패턴 데이터 기반 기업별 fitting

---

## 2. 핵심 가치 가설 (Claude 정리, 사용자 검토)

§1 비전에서 도출되는 측정 가능한 가설들. 각각 **POC 단계에서 검증** 필요.

### 가설 H0 — 의도 모호성 가설 (전제)

> 사용자는 자기 의도를 처음부터 명확하게 표현하지 못한다. 의도는 대화를 통해 명확해진다.

**측정 지표 후보**:
- 첫 쿼리에 필수 정보 (entity / source / 기간 등) 누락 비율
- 사용자가 시스템 응답을 보고 의도를 정정 / 보완하는 빈도
- "내가 원한 건 이거야" 같은 사용자 자기 발견 신호

**현 상태**: ✅ **R-8 첫 시도로 입증** — 사용자가 "데이터 수집한 후..." 쿼리에 필수 entity 누락 → `<collector>` KeyError fatal. entity 명시한 쿼리로 재시도 시 성공. 즉 **사용자가 처음부터 필수 entity 가 필요한지 인지 못함**.

→ H0 = H1 의 **전제**. H0 가 참이라야 H1 (발견 가치) 의미 있음.

### 가설 H1 — 발견 가설

> 사용자는 자기가 어떤 todo 가 작동할지 **알지 못한다**. 그러나 에이전트와의 대화를 통해 **발견**할 수 있다.

**측정 지표 후보**:
- 사용자 첫 쿼리 ↔ 최종 승인 plan 의 차이 (첫 시도에 100% 일치 = 발견 X / 차이가 클수록 발견 성공)
- 사용자 편집 횟수 (편집 = 발견의 흔적)
- "이걸 찾고 싶었어" 같은 사용자 만족 신호

**현 상태**: 이번 R-5~R-7 검증으로 **부분 입증** — 사용자가 plan review 단계에서 의도 발견 (예: "이 선행 단계는 삭제하면 안 되는구나")

### 가설 H2 — 학습 가설

> 발견 과정 자체가 **학습 데이터** 다. 누적되면 기업 / 사용자별 패턴이 드러난다.

**측정 지표 후보**:
- 학습 데이터 캡처율 (대화 / 편집 / 답변 기록 누락 0)
- 패턴 추출 성공률 (예: "이 사용자는 항상 entity=<특정 값>" 자동 학습)
- 패턴 적용 후 사용자 만족 향상

**현 상태**: 메모리 시스템 **미구현**. 학습 데이터 캡처 = 0%. CAP-001 으로 식별됨.

### 가설 H3 — 패턴화 가설

> 학습 데이터 → 기업의 **암묵지 패턴화** 가 가능하다. 즉 데이터에서 의미 있는 규칙성을 추출할 수 있다.

**측정 지표 후보**:
- 패턴 발견 후 cognitive 의 자동 default 적용률
- "이 패턴 맞나요?" 사용자 confirm 시 yes 비율

**현 상태**: 메모리 + 패턴 추출 모두 **미구현** (Sprint 16+).

### 가설 H4 — 맞춤화 가설

> 패턴화된 암묵지로 **기업별 맞춤형 에이전트** 를 만들 수 있다. 즉 에이전트가 "이 기업의 방식" 을 이해한다.

**측정 지표 후보**:
- 기업 A 의 에이전트 ↔ 기업 B 의 에이전트의 응답 차이 (같은 쿼리에 다른 plan = 맞춤 작동)
- 신규 사용자 onboarding 시간 단축 (패턴이 default 가 되면 사용자가 매번 묻지 않아도 됨)

**현 상태**: **미진입** (Sprint 18+ 또는 MVP 이후).

### 가설 의존도

```
H4 맞춤화
  ↑ depends on
H3 패턴화
  ↑ depends on
H2 학습 데이터 누적
  ↑ depends on
H1 발견 (대화)
  ↑ depends on
H0 의도 모호성 (전제)
  ↑ depends on
파트너쉽 인터랙션 모델 (자유 대화)
```

→ **H0 입증 → H1 부터 한 단계씩**. 현재 H0 ✅ 입증, H1 부분 입증, H2 미진입.

---

## 3. 아키텍처 가설 — 사용자 verbatim (검증 대기)

> ⚠️ 사용자 표기: "여기부터는 내 생각. 틀릴 수도 있고 맞을 수도 있고, 참고만 할 것"

### 3.1 4layer + Manager 시스템 (사용자 가설)

> 4layer (cognitive - planning - execution - response) layer 를 통해 사용자 쿼리를 에이전트 언어로 변경하고 언어를 해석해서 에이전트가 todo 를 만들고 실행한다. 편의상 **시스템에이전트 / 실행(기능)에이전트** 로 나눈다. 기능에이전트는 tool 등 작업에 대한 것이고, 시스템 에이전트는 4layer 와 manager 시스템이다.

### 3.2 Manager 시스템 (사용자 가설)

> hitl / todo / memory / callback / feedback (learning) 등 시스템 에이전트를 외부에서 통제하는 시스템이다.

### 3.3 현재 시스템과의 매핑 (Claude 정리)

| 사용자 가설 항목 | 현재 코드 위치 | 일치 / 불일치 |
|---------------|------------|------------|
| 4layer (cognitive-planning-execution-response) | `backend/app/dream_agent/{cognitive,planning,execution,response}/` | ✅ 일치 |
| 시스템 에이전트 = 4layer + manager | 코드 구조 일치 | ✅ 일치 |
| 실행 (기능) 에이전트 = tool | `tools/{registry,base_tool,llm_tool}` (카탈로그 비어있음) | ✅ 일치 |
| Manager: hitl | `workflow_managers/hitl_manager/` | ✅ 구현됨 |
| Manager: todo | `workflow_managers/todo_manager/` | ✅ 구현됨 |
| Manager: memory | `workflow_managers/memory_manager/` | 🟡 폴더 + `__init__.py` 만 (placeholder) |
| Manager: callback | `workflow_managers/callback_manager/` | ✅ 구현됨 |
| Manager: feedback (learning) | `workflow_managers/{feedback,learning}_manager/` | 🟡 부분 — feedback 폴더 + learning 폴더 분리 |

→ **사용자 가설은 코드와 거의 일치**. 메모리 + feedback / learning 만 미완.

### 3.4 가설 검증 / 갱신 트리거

본 §3 가 "가설" 인 이상, 다음 시점에 갱신:
- ADR-015 (메모리 + clarification + 자유 대화 architecture) 결정 후 → §3 정확화
- Sprint 16+ 본격 production 진입 시 → §3 lock

---

## 4. POC 1차 학습 — 의도 ↔ 현실 gap (Claude 정리)

Sprint 14 A3 R-1~R-8 + R-16 검증 + 9 ISSUE 누적으로 측정된 **vision ↔ 현 시스템 gap**.

### 4.1 Vision 별 진척

| Vision 요소 | 진척 | gap |
|----------|------|------|
| 파트너쉽 (사용자 ↔ AI 동등) | 🟡 부분 | 시스템 → 사용자 의도 강요 (도메인 지식). 시스템 ← 사용자 의도 확인 부재 (CAP-001) |
| 자유 대화 / 브레인스토밍 | ❌ 미구현 | NL 1차도 fatal (R-16). 대화 컨텍스트 / 다단계 대화 미지원 |
| Plan 동적 진화 (생성/수정/삭제/보완) | 🟡 부분 | 생성 ✅ / 수정 (직접 편집) ✅ / 삭제 ✅ / 보완 ❌ (clarification HITL 부재) |
| 학습 데이터 누적 | ❌ 미구현 | 메모리 시스템 placeholder 만. 캡처율 0% |
| 암묵지 패턴화 | ❌ 미진입 | Sprint 16+ |
| 기업별 맞춤형 | ❌ 미진입 | MVP 이후 |

### 4.2 Vision 막는 ISSUE 매핑

| ISSUE / CAP | 막는 vision 요소 | 우선순위 |
|---------|--------------|--------|
| **016** NL fatal | 자유 대화 (NL 1차도 작동 안 함) | **최고** (Sprint 14 A3 종결 trigger) |
| **CAP-001** Clarification HITL 부재 | 시스템 ← 사용자 의도 확인 (파트너쉽 양방향) | 높 (Sprint 15) |
| **006** 도메인 지식 가정 | 파트너쉽 (사용자 부담 ↑) | 높 (Sprint 15) |
| **메모리 미구현** | 학습 데이터 누적 | 높 (Sprint 15) |
| **009** tool 미지정 SKIP | Plan 보완 / 자유 대화 | 중 (Sprint 15 NL 2차) |
| **010** tool_params 편집 미지원 | Plan 동적 진화 | 중 (NL 2차) |
| **014** UI list-only | 사용자가 시스템 구조 못 봄 → 대화 부담 ↑ | 중 (Sprint 15+) |
| **011** LLM tool hallucination | 학습 데이터 무결성 | 중 |

### 4.3 측정된 한계 (POC 1차의 진짜 산출물)

> 사용자가 시스템 도메인 지식 (DAG / schema / tool catalog) 가져야만 직접 편집이 안전 — 비현실적 가정.

---

## 5. 핵심 비기능 요구 (2026-04-28 사용자 검토 lock)

| 카테고리 | 요구 후보 | 측정 |
|---------|---------|------|
| **자유 대화 latency** | 사용자 입력 → 시스템 응답 P95 < 5초 | OpenTelemetry trace |
| **학습 데이터 무결성** | 대화 / 편집 / 답변 캡처율 100% (rollback 시도 추적) | DB row count vs interaction event count |
| **메모리 일관성** | 같은 사용자 / 세션 간 메모리 상태 일치 | DB transaction integrity |
| **도메인 지식 X** | 사용자 입력에 시스템 schema (tool 이름 / DAG 등) 명시 요구 0 | NL 성공률 + clarification 미사용률 |
| **응답 결정성** | 동일 입력 → 동일 plan 비율 ≥ 90% (학습 적용 시) | A/B replay 테스트 |
| **확장성** (사용자 인사이트) | tool / agent 10~20 개로 확장 시에도 사용자 도메인 지식 0 유지. dropdown UI 같은 구조화 강화 의존 X | tool 개수 ↑ vs NL 성공률 / clarification 사용률 변화 |
| **확장/변경 용이성** ⭐ (사용자 통찰 2026-04-29) | "쓰다보면 UX 변경 多. 지금 결정은 가설. 확장/변경 쉬운 구조 우선" — JSONB content / schema_version / Optional / append-only 등 5 원칙 ([35_DB_SCHEMA §0.1](./35_DB_SCHEMA_v1.0.md)) | 미래 변경의 비용 측정 (대부분 0, 큰 구조 변경만 schema_version v2 분기) |

**보류 (MVP 진입 시 추가 검토)**:
- 개인정보 보호 (POC 단계 사용자 1인이라 의미 작음)
- 인증 / 권한
- 비용 SLO (POC 단계 측정 단계)

---

## 6. 의도 적용 우선순위 (2026-04-28 사용자 lock)

H0~H4 가설을 어느 순서로 검증·구현할지.

| 순 | 의도 | Sprint | 근거 |
|----|------|--------|------|
| 0 | H0 의도 모호성 — 입증 + 메커니즘 | Sprint 14 A3 | ✅ R-8 첫 시도로 입증됨. CAP-001 (clarification) 으로 메커니즘 진입 |
| 1 | H1 발견 (자유 대화 1차) | Sprint 15 | NL fix + clarification = H1 의 토대 |
| 2 | H2 학습 데이터 누적 | Sprint 15 | 메모리 시스템 구현 — H3/H4 의 입력 |
| 3 | H1 자유 대화 본격 (NL 2차) | Sprint 16 | LLM Tool Routing — 도메인 지식 X |
| 4 | H3 패턴화 | Sprint 17 | 메모리 누적 후 패턴 추출 |
| 5 | H4 맞춤화 | Sprint 18+ | 패턴 적용 본격 — MVP 이후 |

**핵심**: H1+H2 가 같은 Sprint 15 — 메모리 + clarification 통합 (ADR-015). H2 가 H1 본격 (NL 2차) 의 인프라.

---

## 7. ADR / Sprint 매핑 (Claude 갱신, 살아있는 표)

각 ADR 이 어느 vision 요소를 다루는지 추적.

| ADR | 제목 | Vision 요소 | 상태 |
|-----|------|----------|------|
| 000 | ADR 도입 | 메타 | ✅ |
| 001 | hitl/pause 통합 | Plan 동적 진화 (편집 경로 통합) | ✅ |
| 002 | NL 편집 1·2·3차 | 자유 대화 (단계적) | ✅ 1차 / 🟡 2차 / ❌ 3차 |
| 005 | Sprint 12 legacy | 메타 | ✅ |
| 007 | session/turn 네이밍 | 메타 | ✅ |
| **010** | Plan/Todo schema 통합 | 자유 대화의 도구 (Sprint 15) | 🟡 본문 대기 (사전 조사 완료) |
| **015** | 메모리 + 자유 대화 architecture | 파트너쉽 양방향 + 학습 누적 | 🟡 본문 대기 (Q3/Q4 자료 후) |
| 003 | Manager 5 책임 분리 | 시스템 응집성 | ⏳ |
| 008 | Error 처리 통일 | 안정성 | ⏳ |
| 009 | LLM timeout | 안정성 | ⏳ |
| 011 | UI DAG 시각화 | 시스템 구조 가시성 | ⏳ |
| 012 | Cognitive schema 강화 | 자유 대화 (parallelism 의도 반영) | ⏳ |
| 013 | ws_hitl ack 일관성 | 안정성 | ⏳ |
| 014 | LLM tool catalog grounding | 학습 데이터 무결성 | ⏳ |

---

## 8. 본 문서 ↔ 다른 문서 관계

```
docs/agent_specs/00_vision_and_intent.md  ← 본 문서 (north star)
   │
   └─ docs/agent_specs/ (spec 카탈로그)
         ├─ 01_requirements (사용자 5항목 — 본 문서 §1 의 한 시점 표현)
         ├─ 10_system_architecture
         ├─ 12_manager_layer
         ├─ 30_DATA_MODELS (Pydantic)
         ├─ 35_DB_SCHEMA (DB ERD — Sprint 15 P0 baseline)
         └─ ...
```

**참조 규칙**:
- 모순 발견 시 **본 문서 (vision) 가 source of truth**
- 본 문서 변경 시 모든 하위 문서 영향 검토 필수
- 본 문서 §1 / §3 변경은 **사용자 결정** — Claude 단독 X

---

## 9. 검토 + lock 결과 (2026-04-28)

| # | 항목 | 결과 |
|---|------|------|
| 1 | §1 verbatim | ✅ OK (사용자 verbatim 보존) |
| 2 | §2 가설 H1~H4 | ✅ 동의 + **H0 의도 모호성 가설 추가** (전제) |
| 3 | §3 verbatim | ✅ OK (사용자 가설 보존) |
| 4 | §5 비기능 요구 | ✅ 5 + **확장성 추가** (사용자 인사이트) |
| 5 | §6 의도 적용 우선순위 | ✅ 권고 순서 + H0 0순위 추가 |
| 6 | 위치 | ✅ `docs/agent_specs/00_vision_and_intent.md` 확정 |

**의도 문서 v1.0 lock — 모든 후속 결정의 north star**.

다음 갱신 트리거:
- ADR-015 (메모리 + clarification + 자유 대화 architecture) 결정 후 — §3 가설 정확화
- Sprint 15 완료 후 — §4 진척 갱신
- Sprint 16+ 본격 production — §1 vision 미세 조정 가능성

---

## 변경 이력

> 프레임워크 추출(2026-06-19) 이전(마케팅 도메인 시기)의 상세 변경 이력은 git 히스토리를 참조하세요.
