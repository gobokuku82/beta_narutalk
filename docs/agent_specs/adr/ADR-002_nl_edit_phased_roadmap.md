# ADR-002: NL 편집 기능의 점진 고도화 (1·2·3차 로드맵)

## Status

Accepted (2026-04-27)

## Context

Sprint 14 A3 의 자연어 (Natural Language, NL) Todo 편집 범위를 결정해야 함. 사용자 §4 요구:

> 자연어로 요청할 수도 있고, 순서를 변경하거나 삭제하는 단순작업은 간단하면 좋겠다.

이 한 문장에는 **단순 NL** ("4번 삭제") 부터 **복잡 NL** ("가격대가 낮은 경쟁사만 남기고 나머지 삭제") 까지 넓은 스펙트럼이 잠재. 그대로 구현하면:

- **너무 좁게 하면** ("4번 삭제" 만 지원): 사용자 만족도 낮음
- **너무 넓게 하면** (clarification 대화, 메모리 기반 재계획): POC 단계에서 과잉 추상화. 비용·시간 폭증

또한 사용자 메모리 [`project_llm_heavy_initial.md`](../../../C:\Users\gobok\.claude\projects\c--kdy-Projects-octormate-beta-v001\memory\project_llm_heavy_initial.md) 의 원칙: "POC/MVP 초기 = 데이터 수집 단계. 규칙 hardcode 보다 LLM 우선. 페어 누적 → 추후 학습/규칙 추출".

→ 1차로 단순 NL 만 구현해 사용자 입력 패턴을 누적, 그 데이터로 2·3차 설계.

## Decision

NL 편집 기능을 **3단계 점진 고도화** 로 구분.

### 1차 (Sprint 14 A3, 현재 완료)

**범위**: 단순 자연어로 Todo 단일 조작.

- 지원: "4번 삭제", "2번과 3번 순서 바꿔", "agent X 의 task 를 Y 로 변경"
- 제외: 다단계 대화 (clarification), 복합 조건 ("가격대 낮은 경쟁사만"), 메모리 참조

**구현**:
- `plan_editor.parse_instruction` (LLM 1회 호출, temperature=0)
- `apply_edit` 4 action: `add` / `remove` / `modify` / `reorder`
- 다단계 대화 미지원 — `action: "unknown"` 시 즉시 NL_INTENT_UNCLEAR 반환

**측정**: D-14 NL 성공률 100회 측정 (`backend/scripts/a3_nl_success_rate.py`)
- 실패율 < 3%: 1차 유지, 2차로 진행 가능
- 3% ≤ 실패율 < 10%: γ (multi-turn) 재평가 trigger
- 실패율 ≥ 10%: 1차 범위 재설계 (Y-c structured only 축소)

### 1차 한계 (POC 검증으로 입증, 2026-04-27 R-5~R-7)

R-5~R-7 누적 브라우저 검증으로 **구조화 직접 편집의 본질적 한계** 가 측정됨.
4개 ISSUE 가 같은 근본 원인 공유:

| ISSUE | 사용자가 알아야 했던 도메인 지식 |
|-------|-----------------------------|
| 006 | DAG 의존성 (format 삭제 시 downstream 영향) |
| 008 | Pydantic schema (PlannedTodo 필드 — task_type 등) |
| 009 | Tool catalog (어떤 tool 로 실행할지) |

**공통 결론**: 사용자가 시스템 내부 도메인 지식을 가져야만 직접 편집이 안전.
8 tool 도 외우기 어려운데 **10~20 tool 되면 비현실적**. dropdown UI 같은
구조화 강화로도 본질 해결 안 됨.

→ **2/3차 진입 정당성 입증**. 1차의 "성공" 정의는 "기능 작동" 이 아니라
"한계 측정 + 2차 진입 trigger 식별". 상세는
[`docs/reports/sprint14_a3_known_issues.md`](../../reports/sprint14_a3_known_issues.md)
§종합 인사이트 참조.

### 2차 (Sprint 16+ 예상)

**범위**: 복잡 자연어로 Todo 다중 조작 + clarification.

- 지원 예시: "가격대가 낮은 경쟁사만 남기고 나머지 삭제", "첫 3개를 병렬화", "agent A 의 retry 를 모두 비활성화"
- 다단계 대화: "몇 번이요?" 같은 되묻기 (LLM 의 자체 followup)

**진입 조건** (cumulative — 2026-04-27 갱신):
1. 1차 D-14 측정 완료, 실패율 < 5%
2. POC 사용자 패턴 30회+ 누적 (logs/nl_pattern.jsonl 같은 기록)
3. 사용자 명시 결정 (별도 ADR 작성)
4. **(추가)** 사용자 추가/편집 시 **도메인 지식 필요 비율 측정** — ISSUE-006/009 같은 패턴이 5~10% 넘으면 2차 진입 강력 정당성

### 2차의 본질적 가치 (R-5~R-7 검증으로 입증)

POC 1차 검증 결과:
- ISSUE-006 (DAG 의존성 모름) → 2차 LLM 의미 검증으로 자동 해소 가능
- ISSUE-009 (tool catalog 모름) → 2차 LLM Tool Routing 으로 자동 해소
- 사용자가 task 만 입력 → LLM 이 의도 해석 + tool 매핑 + DAG 영향 검토

**즉 2차는 단순 "복잡한 NL 지원" 이 아니라 "도메인 지식 가정 제거"**. 1차 검증의
4 ISSUE 가 그대로 2차의 구체적 해결 대상.

**예상 구현**:
- `plan_editor` 확장: instruction → multi-step plan
- 새로운 `_handle_todo_edit_nl_clarify` 핸들러 (대화 컨텍스트 유지)
- session 단위 NL 컨텍스트 저장 (Memory 와 별도)

### 3차 (Sprint 17+ 또는 MVP 이후)

**범위**: 메모리·사용자 패턴·외부 컨텍스트 기반의 능동적 사고.

- 지원 예시: "지난 분기와 비슷한 방식으로", "이번엔 빨리 끝내줘", "주말이니까 약식 분석"
- Cognitive layer 재진입 (기존 plan 무시하고 재계획)
- Memory 통합 — 과거 plan/결과 참조

**진입 조건**:
1. 2차 안정화 완료
2. Memory 시스템 (FR-14, Sprint 15) 구축됨
3. 사용자 패턴 100회+ 누적 + 분류 가능한 패턴 식별

**예상 구현**:
- Cognitive layer 가 NL 편집도 처리 (현재는 plan_editor 단독)
- Memory 조회 + 패턴 매칭
- 별도 ADR 으로 상세화 예정

## Consequences

### 좋은 점

- **POC 단계 적정 범위**: 1차는 LLM 1회 호출만 — 빠르고 단순
- **데이터 수집 우선**: 규칙 hardcode 안 함. 사용자 입력 누적 후 학습/규칙 추출
- **확장 여지**: 1차 구현이 2차 확장을 막지 않음 (action enum 에 unknown 여지 둠)
- **명시적 trigger**: 측정값 기반 phase 진행 결정 — 임의 결정 없음

### 나쁜 점 / 비용

- **1차 범위 좁음**: "복잡한 자연어" 가 1차에서 안 됨. 사용자 기대 관리 필요
- **단계 진입 결정 부담**: 2/3차 시작 시점마다 별도 ADR 필요
- **측정 의존**: D-14 같은 측정 인프라가 데이터 정합성 결정. 측정 누락 시 phase 진행 판단 어려움

### 위험

- **사용자 기대 vs 1차 범위 갭**: "AI 에이전트인데 왜 못 하지?" 인상 가능 — UX-12 (NL 파싱 실패 안내 토스트) 로 완화
- **1차 → 2차 마이그레이션 cost**: 1차 plan_editor 가 너무 단순해서 2차 시 재작성 가능. action enum 확장 가능하게 설계해 일부 완화

## Alternatives Considered

### Alt-1. 처음부터 3차 수준 목표

- 장점: 사용자 만족도 높음
- 단점: POC 단계 비용 폭증. Cognitive layer 재진입 + Memory 시스템이 모두 필요
- **불채택** — 메모리 `project_llm_heavy_initial.md` 의 "초기 LLM 多 + 데이터 누적" 원칙 위배

### Alt-2. 1차 vs 2차 단계 구분 없이 단일 범위

"단순/복잡 구분 없이 다 지원하되 LLM 응답 품질에 맡김".

- 장점: 사용자 입장 단순
- 단점: 측정·학습 단위 모호. 어느 입력이 잘 되고 어느 게 안 되는지 분류 불가
- **불채택**

### Alt-3. 자연어 편집 기능 자체 미지원 (구조화 UI 만)

- 장점: 가장 단순
- 단점: 사용자 §4 명시 요구 위배. POC 의 핵심 가치 (자연어 → 자동화) 손상
- **불채택**

## Related

- **사용자 메모리**: [`project_llm_heavy_initial.md`](../../../../../Users/gobok/.claude/projects/c--kdy-Projects-octormate-beta-v001/memory/project_llm_heavy_initial.md), [`project_nl_edit_roadmap.md`](../../../../../Users/gobok/.claude/projects/c--kdy-Projects-octormate-beta-v001/memory/project_nl_edit_roadmap.md)
- **Sprint 14 A3 결정**: D-14 NL 성공률 측정
- **구현**:
  - `backend/app/dream_agent/workflow_managers/hitl_manager/plan_editor.py`
  - `backend/api_v2/ws_hitl.py::_handle_todo_edit_nl`
  - `backend/scripts/a3_nl_success_rate.py` (측정)
- **요구사항**: `01_requirements_v1.6.md` FR-12e, FR-12h (multi-turn out of scope)
- **NFR**: NFR-11 (P95 < 3s), NFR-12 (결정성 — temperature=0)
- **테스트**: `backend/tests/sprint14/test_a3_plan_editor_nl_unit.py` (Group D), `test_a3_ws_hitl_nl_integration.py` (Group E)
- **관련 ADR**: ADR-001 (NL 도 동일 편집 경로)

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-27 | 초안 + Accepted. 1차 (Sprint 14 A3) 구현 완료. 2/3차 진입 조건 명시 |
| 2026-04-27 | R-5~R-7 브라우저 검증 결과 보강 — 1차 한계 측정 (4 ISSUE 공통 근본: 도메인 지식 가정의 한계). 2차 진입 조건에 "도메인 지식 필요 비율" 추가. 2차의 본질적 가치 명시 (도메인 지식 가정 제거). 관련: `docs/reports/sprint14_a3_known_issues.md` §종합 인사이트 |
