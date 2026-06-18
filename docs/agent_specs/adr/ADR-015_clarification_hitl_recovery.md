# ADR-015: Clarification 자동 판정 + Tool ValueError → HITL recovery 자동 변환

## Status

**Proposed** (2026-05-19) — Stage 0 (P2/P3 fix plan 박제) ~ Stage 1 (실 구현 대기).

**Amended** (2026-06-01, 작업 ⑫ 후속) — broken 5 ads collector 폐기 박제:
- 본문 line 41·98 의 `meta_collector` 인용 (HITL date_from/date_to 트리거 시나리오) = 결정 박제 시점 (2026-05-19) 이력 보존
- 실 상태: broken 5 폐기됨 (⑫.A). HITL 트리거 시나리오는 신 ads collector 등재 시 (MVP+ 작업 ⑭) 재박제 결정.

이전 이력:
- (없음 — 신규 본문 작성)

후속 이력:
- (예정) Accepted — P2 + P3 sprint 완료 + 사용자 채팅 시나리오 2 재테스트 통과 시.

**범위 분할 박제**: 기존 INDEX 의 015 명세 = "메모리 + Clarification + 자유 대화 통합 architecture". 본 ADR 은 그 중 **Clarification + HITL recovery 부분만** 다룸. 메모리 통합 + 자유 대화는 별도 ADR (예: 018 메모리 layer) 으로 이연.

## Context

### 발견 — 사용자 채팅 시나리오 2 (2026-05-19)

사용자가 채팅 UI 에 입력:
> "메타광고 성과보여줘" (기간 누락)

**Cognitive 자취** (백엔드 로그):
```
2026-05-19 20:46:00 cognitive done
  brand=None
  depth=brief
  tasks=['summary_generation']      ← data_collection 누락
```

**Planner stage1~3** (정상 동작):
```
stage1: teams=['analysis_team']
stage2: agents=['collection_agent','channel_normalizing_agent','report_text_agent']
stage3: todos=3 (implicit_prerequisites 룰로 data_collection + data_preprocessing 자동 후행)
```

**Executor 결과**:
```
ERROR Todo execution failed
  error="Missing required params: ['date_from', 'date_to']."
  todo_id=todo_001  tool=meta_collector

→ EXECUTION_ALL_FAILED (하드 종료, 사용자에게 재질문 없음)
```

### 원인 추적

#### 원인 1 (P2 영역) — Cognitive Ambiguity 자동 판정 미동작

`schemas/structured_query.py:132-137` 의 `Ambiguity` 모델은 박제됨:
```python
class Ambiguity(BaseModel):
    is_ambiguous: bool = False
    severity: str = "none"
    reasons: list[str] = Field(default_factory=list)
    clarification_question: Optional[str] = None
```

하지만 `cognitive/prompts/*.yaml` 의 LLM prompt 에 **"필수 params 누락 시 ambiguous 판정 강제"** 룰 미박제. LLM 이 자체 추론에 맡김 → 확률적으로 통과/실패 → 본 사례는 통과 (잘못된 통과).

#### 원인 2 (P3 영역) — Executor 의 ValueError → HITL emit 자동 변환 미구현

`execution/executor.py` 의 `_execute_todo()` 가 ValueError catch 시:
```python
except Exception as e:
    logger.error("Todo execution failed", ...)
    result.status = TodoStatus.FAILED
    result.error_message = str(e)
```

→ `Missing required params` 패턴 인식 후 `HITLRequestType.CLARIFICATION` emit 로직 미구현. 결과 = `EXECUTION_ALL_FAILED` 하드 종료.

#### 원인 3 (구조적) — clarification 흐름 책임 위치 모호

| 단계 | 책임 후보 | 현재 |
|---|---|---|
| NL → params 추출 단계 (Cognitive) | LLM 자율 / prompt 룰 명시 | LLM 자율 (미흡) |
| Plan 생성 후 검증 단계 (Planner) | 미동작 (Plan 만 만들고 검증 없음) | — |
| Tool 실행 단계 (Executor) | ValueError fail-fast / HITL emit | fail-fast 만 |
| 채팅 UI 단 (frontend) | hitl_request 이벤트 렌더링 | 미박제 |

→ **clarification 의 책임 위치 결정 + 흐름 통합 필요**.

### 의도 vs 현실의 괴리

**의도** (`models/hitl.py:HITLRequest` + `models/enums.py:HITLRequestType.CLARIFICATION`):
> "필수 params 누락 시 자연스러운 사용자 재질문 — 채팅 UI 에 자동 question 표시 + 사용자 답변 → 같은 conversation 안에서 재실행."

**현실**:
> `EXECUTION_ALL_FAILED` 메시지 + 사용자가 처음부터 다시 입력해야 함. HITL clarification 미발동.

### 영향 — 본 결정이 향후 모든 Tool/Cognitive 의 clarification 패턴에 미치는 효과

본 sprint 의 광고 collector 만의 문제가 아님. 향후 모든 Tool 의 fail-fast 가드 ↔ HITL recovery 통합 패턴 결정 필요:

| Tool | 필수 params | 누락 시 |
|---|---|---|
| meta_collector | date_from, date_to | 본 ADR 영역 |
| review_collector | brand | 동일 |
| insight_extractor | (자동 수집) | clarification 불필요 |
| pdf_renderer | template (Phase 4C) | 동일 패턴 적용 |
| image_generator | brand, theme (Phase 4A) | 동일 패턴 적용 |

→ 본 ADR = clarification + HITL recovery 통합 패턴의 기준선.

## Decision

**3-Layer Clarification Pattern** 채택:

### Layer 1 (예방) — Cognitive Ambiguity prompt 룰 명시

`cognitive/prompts/cognitive_prompt.yaml` 등에 ambiguity 룰 박제:

```yaml
ambiguity_rules:
  # 룰 1: 데이터 수집/분석 task 의 기간 누락
  - condition: |
      task in [data_collection, sentiment_analysis, keyword_extraction,
               trend_analysis, causal_analysis] AND
      (date_from is missing OR date_to is missing)
    judgment:
      is_ambiguous: true
      severity: medium
      clarification_question: "어느 기간을 조회할까요? (예: 2024년 10월, 지난 30일, 2025-01-01~2025-03-31)"
      missing: [date_from, date_to]
  
  # 룰 2: 콘텐츠 생성 task 의 브랜드 누락
  - condition: |
      task in [image_generation, copy_generation, video_storyboard] AND
      brand is missing
    judgment:
      is_ambiguous: true
      severity: high
      clarification_question: "어느 브랜드의 콘텐츠를 생성할까요?"
      missing: [brand]
```

→ LLM 이 NL → StructuredQuery 변환 시 위 룰 적용 → `is_ambiguous=True` 시 채팅 UI 에 자동 질문. **Executor 도달 전 사용자 재질문**.

### Layer 2 (안전망) — Executor ValueError → HITL emit 자동 변환

`execution/executor.py` 의 `_execute_todo()` 의 ValueError catch 영역 확장:

```python
except ValueError as e:
    msg = str(e)
    
    # "Missing required params" 패턴 매칭
    if _is_missing_params_error(msg):
        missing_fields = _parse_missing_params(msg)
        
        # HITL clarification 자동 emit
        clarification_msg = _generate_clarification_message(
            missing=missing_fields, tool_name=todo.tool,
        )
        
        if cb_manager:
            await cb_manager.emit(session_id, {
                "type": "hitl_request",
                "request_type": HITLRequestType.CLARIFICATION.value,
                "request_id": str(uuid.uuid4()),
                "message": clarification_msg,
                "missing": missing_fields,
                "tool": todo.tool,
                "todo_id": todo.id,
                "timeout_sec": 300,
            })
        
        result.status = TodoStatus.HITL_WAITING  # 신규 enum
        result.error_message = clarification_msg
        # pause_controller 가 사용자 응답 대기
    else:
        result.status = TodoStatus.FAILED
        result.error_message = str(e)
```

**보조 함수** (executor.py 내 또는 별도 helpers/clarification.py):

```python
import re

def _is_missing_params_error(msg: str) -> bool:
    return "Missing required params" in msg

def _parse_missing_params(msg: str) -> list[str]:
    """Tool ValueError message 에서 누락 fields list 추출.
    
    예: "Missing required params: ['date_from', 'date_to']. ..."
        → ['date_from', 'date_to']
    """
    match = re.search(r"Missing required params:\s*\[(.*?)\]", msg)
    if not match:
        return []
    raw = match.group(1)
    return [f.strip().strip("'\"") for f in raw.split(",") if f.strip()]

def _generate_clarification_message(missing: list[str], tool_name: str) -> str:
    """누락 fields → 자연어 질문 생성."""
    if {"date_from", "date_to"} <= set(missing):
        return "어느 기간을 조회할까요? (예: 2024년 10월, 지난 30일)"
    if "brand" in missing:
        return "어느 브랜드를 분석할까요? (예: 블루밍글로우)"
    field_ko = {
        "date_from": "시작일", "date_to": "종료일",
        "brand": "브랜드", "campaign_id": "캠페인 ID",
        "ad_id": "소재 ID", "product": "상품",
    }
    fields = ", ".join(field_ko.get(f, f) for f in missing)
    return f"필수 정보가 누락됐습니다: {fields}. 추가 입력해주세요."
```

### Layer 3 (UI) — 채팅 UI 의 hitl_request 이벤트 렌더링

`frontend/src/api/hooks/useWebSocket.ts` 또는 채팅 컴포넌트에서:
```typescript
case 'hitl_request':
  if (data.request_type === 'clarification') {
    appendAssistantMessage(data.message);
    // 사용자 다음 입력을 같은 conversation 으로 라우팅
    setClarificationContext({
      missing: data.missing,
      tool: data.tool,
      todo_id: data.todo_id,
      request_id: data.request_id,
    });
  }
  break;
```

→ 사용자 답변 → Cognitive 재실행 (이전 conversation 컨텍스트 + clarification 답변 결합).

### 신규 enum: `TodoStatus.HITL_WAITING`

`models/enums.py` 에 추가:
```python
class TodoStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    HITL_WAITING = "hitl_waiting"   # ⭐ ADR-015 신규
```

→ FAILED 과 구분 (FAILED 는 실 에러, HITL_WAITING 은 사용자 응답 대기).

### 책임 매트릭스 (최종)

| 단계 | 책임 | 처리 시점 |
|---|---|---|
| Layer 1 — Cognitive | NL 모호성 prompt 룰 (예방) | NL → StructuredQuery 변환 시 |
| Layer 2 — Executor | Tool ValueError → HITL emit (안전망) | Tool 실행 fail 시 |
| Layer 3 — Frontend | hitl_request 렌더링 + 답변 라우팅 | 채팅 UI |

## Consequences

### 긍정 (+)

- **사용자 UX 자연스러움** — 기간 누락 시 EXECUTION_ALL_FAILED 대신 자동 재질문
- **2-단계 안전망** — Cognitive 가 못 잡아도 Executor 가 잡음. 실 누락 0
- **확장성** — 향후 모든 Tool 의 fail-fast 가드 + HITL recovery 통합 패턴
- **conversation 연속성** — 사용자가 처음부터 재입력 X. 같은 conversation 안에서 답변
- **책임 명확화** — Cognitive/Executor/Frontend 의 clarification 책임 분리

### 부정 (−)

- **Cognitive prompt 복잡도 증가** — ambiguity 룰 enum 늘어날 때마다 prompt 보강
  - mitigation: 룰을 YAML 파일로 분리 + 자동 생성 (taskname → 필수 fields)
- **Executor 코드 복잡도 증가** — 패턴 매칭 + emit + 신규 enum
  - mitigation: 보조 함수 helpers/clarification.py 분리
- **Frontend 작업 필요** — hitl_request 이벤트 렌더링 + clarification context 관리
- **테스트 부담 증가** — Cognitive unit + Executor integration + frontend e2e
- **HITL timeout 처리** — 사용자 응답 없으면 timeout 후 종료 흐름 박제 필요 (기존 sprint14 활용)

### 영향 범위

| 영역 | 변경 |
|---|---|
| `cognitive/prompts/cognitive_prompt.yaml` (또는 동등 파일) | ambiguity_rules 박제 |
| `execution/executor.py` `_execute_todo()` | ValueError catch 확장 |
| `execution/helpers/clarification.py` (신규) | _is_missing / _parse / _generate 함수 |
| `models/enums.py:TodoStatus` | HITL_WAITING 추가 |
| `models/hitl.py:HITLRequest` | (기존 박제 활용 — 변경 없음) |
| `api_v2/connection_manager.py` 또는 ws_agent | hitl_request 이벤트 발행 (기존 cb_manager.emit) |
| `frontend/src/api/hooks/useWebSocket.ts` | hitl_request case 추가 |
| `frontend/src/features/chat/` | clarification context 상태 관리 |
| `backend/tests/sprint*/test_clarification_*.py` (신규) | unit + integration |
| `backend/tests/sprint*/test_cognitive_ambiguity_*.py` (신규) | Cognitive 룰 검증 |
| `frontend/src/**/*.test.tsx` | UI 렌더링 test |
| `docs/_claude/tool/TOBE_MVP/06_fix_plan` | P2 + P3 진행 자취 반영 |

## Alternatives Considered

### 대안 1 — Layer 1 만 (Cognitive prompt 강화만)

- 방법: ambiguity_rules 박제만. Executor 단은 그대로 (FAILED 종료).
- 장점: 작은 변경. 빠른 ship.
- 단점:
  - LLM 환각 시 fail (안전망 없음)
  - Tool ValueError = 여전히 EXECUTION_ALL_FAILED → 사용자 UX 깨짐
- **기각**: 안전망 없으면 silent failure 위험.

### 대안 2 — Layer 2 만 (Executor HITL emit 만)

- 방법: Executor 단의 ValueError → HITL emit 만 박제. Cognitive 는 그대로.
- 장점: 단일 단계 (Tool fail-fast 만 정합).
- 단점:
  - 사용자 응답 = Executor 도달 후 발동 = 늦은 시점 (CPU/시간 낭비)
  - Cognitive prompt 가 약함 (LLM 학습 부담 그대로)
- **기각**: 예방 + 안전망 패턴이 더 견고.

### 대안 3 — 3-Layer 통합 패턴 (채택)

- 방법: Layer 1 (Cognitive prompt) + Layer 2 (Executor HITL emit) + Layer 3 (Frontend)
- 장점: 예방 + 안전망 + UX 통합. 확장성 우수.
- 단점: 변경 영역 큼 (수용 가능 — 책임 분리로 mitigation).
- **채택**: 단순 fix 가 아닌 향후 패턴 기준선.

### 대안 4 — Plan 시점 검증 추가 (Layer 1.5)

- 방법: Planner stage3 가 todos 생성 후 필수 params 검증. 누락 시 planning 단계에서 clarification.
- 장점: Cognitive 와 Executor 사이 추가 게이트.
- 단점: Plan 시점에 tool_params 가 비어있는 게 정상 (LLM 이 만들기 전). 검증 시점 모호.
- **기각**: Cognitive prompt + Executor 안전망 으로 충분.

## Related

- **P2 / P3 fix plan**: [TOBE_MVP/06 §3 + §4](../../_claude/tool/TOBE_MVP/06_collection_normalize_fix_plan_2026-05-19.md) — 상세 원인분석 + UX 시나리오
- **D18 Drift**: [TOBE_MVP/03 §1 D18](../../_claude/tool/TOBE_MVP/03_drift_report.md) — 발견 자취
- **ADR-014**: Tool 매개변수 자동 식별 (P1) — 본 ADR 의 보완 관계 (P1 + Layer 1 = 호출자 부담 감소 / P3 + Layer 2 = 호출되는 측 안전망)
- **ADR-001**: hitl/pause 개념 통합 — HITL 기반 인프라
- **ADR-002**: NL 편집 점진 고도화 — A3 (NL clarification) 흐름
- **ADR-007**: session_id ↔ turn_id — clarification context 식별
- **메모리 통합** (향후 별도 ADR — 예: ADR-018): 기존 INDEX 015 명세의 메모리 부분 이연
- **영향 코드**: executor.py, cognitive/prompts/, models/enums.py, frontend useWebSocket.ts

## 변경 이력

| 날짜 | 내용 |
|---|---|
| 2026-05-19 | Proposed — 사용자 채팅 시나리오 2 발견 후 본문 작성. 기존 INDEX 015 명세 (메모리 + Clarification + 자유대화) 중 **Clarification + HITL recovery 부분만** 다룸. 메모리 통합은 별도 ADR 이연. P2/P3 sprint 완료 후 Accepted 갱신 예정. |
