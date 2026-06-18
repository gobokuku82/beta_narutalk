# Sprint 15 — Phase E3 세부 작업계획서 (Clarification HITL)

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-04-28 |
| Phase | E-3 — Clarification HITL (5 항목 정책 #5 + CAP-001) |
| 마스터 | [`sprint15_implementation_plan.md`](./sprint15_implementation_plan.md) |
| 의존 | Phase E-2 ✅ (Cognitive cascade 작동) |
| 다음 | [`sprint15_phase_e4_nl_v2.md`](./sprint15_phase_e4_nl_v2.md) (NL 2차) |
| 예상 작업량 | ~4시간 (1세션) |
| Acceptance | Cognitive 출력 schema 확장 + Validator + 신규 HITL trigger + ws_hitl message + 대시보드 모달 |

---

## 0. 본 문서의 역할

Phase E-3 의 **Clarification HITL 첫 구현 작업 카탈로그**.

**5 항목 정책 #5 + CAP-001 의 실현** — 모호한 쿼리 시 시스템이 사용자에게 묻기.

**Vision 매핑**: H0 의도 모호성 가설의 자동 해결 메커니즘 (Phase E-2 cascade + 본 phase = 완성).

---

## 1. Phase E-3 의 의도

### 1.1 사용자 사례 4 가지 (의도 문서 §1.1 / settlement §2.3)

| # | 쿼리 | 부족 정보 | 모호도 유형 |
|---|------|---------|------|
| 1 | "리뷰를 찾아줘" | brand + channel + 기간 | (a) Missing field |
| 2 | "네이버에서 리뷰를 찾아줘" | brand | (a) Missing field |
| 3 | "블루밍글로우 리뷰 찾아줘" | (channel default 가능) | (b) Default confirm |
| 4 | "아모레 글로우 네이버 리뷰" | brand 해석 (1개 vs 2개) | (c) Entity ambiguity |

→ **모호도 3 유형 모두 처리** + **메모리 누적 시 점진 자동 해결**.

### 1.2 작업 원칙

- **Hybrid trigger** — LLM 자체 감지 + Required field validator (backup)
- **메모리 cascade 우선** — 답이 메모리에 있으면 묻지 X
- **Loop 방지** — max 2회 attempts
- **UX 점진 결정** — 사용자 의도 lock ("기존 todo 유지 + 부족분 요청"). 시각적 디자인은 구현 중
- **Messages append-only** ⭐ (35 spec §0.1 설계 원칙) — clarification 질의/답변은 같은 turn 의 `content.messages` 배열에 추가. **별도 row 생성 X**. (단 `type=preference` 로 자동 promote 는 별도 — 다음 turn 자동 활용용)

---

## 2. 작업 분해 — 6 sub-phase

```
E3-1  Cognitive 출력 schema 확장 (clarifications_needed)
        ↓
E3-2  Required field Validator (LLM 누락 backup)
        ↓
E3-3  Cognitive node 통합 (메모리 cascade + interrupt + max 2회)
        ↓
E3-4  ws_hitl 신규 message type (clarification_request / response)
        ↓
E3-5  대시보드 Clarification 모달 (UX 점진)
        ↓
E3-6  E2E 통합 시나리오 (R-19~R-22)
```

### 시간 추정

| Sub-phase | 시간 | 누적 |
|-----------|------|------|
| E3-1 schema 확장 | 30min | 0.5h |
| E3-2 Validator | 30min | 1h |
| E3-3 Cognitive 통합 | 1h | 2h |
| E3-4 ws_hitl 신규 | 1h | 3h |
| E3-5 대시보드 모달 | 1h | 4h |
| E3-6 E2E 검증 | 30min | **4.5h** |

(예상 4h 보다 약간 길어질 가능성. 4~4.5h)

---

## 3. E3-1: Cognitive 출력 schema 확장 (~30분)

### 3.1 파일

**경로**: `backend/app/dream_agent/schemas/structured_query.py` (수정)

### 3.2 변경 — ClarificationRequest 추가

```python
"""StructuredQuery — Cognitive 출력 schema.

Sprint 15 Phase E-3: clarifications_needed 필드 추가.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class ClarificationRequest(BaseModel):
    """모호도 보완 요청 — 단일 항목.
    
    3 유형:
        - missing_field: 필수 정보 누락 (brand 등)
        - default_confirm: 시스템 default 적용 OK 인지 confirm
        - ambiguity: entity 다중 해석
    """
    type: Literal["missing_field", "default_confirm", "ambiguity"]
    field: str                              # "brand", "channel", "period" 등
    question: str                           # 사용자에게 보여줄 질문
    options: Optional[list[str]] = None     # ambiguity / default_confirm 시
    default_value: Optional[str] = None     # default_confirm 시
    reason: str = ""                        # 왜 묻는지 (UX 보조)


class StructuredQuery(BaseModel):
    """Cognitive 출력 — 기존 + clarification 확장."""
    
    # ... 기존 필드 (intent / goal / entities / depth / tasks 등)
    
    # 신규 (Sprint 15 E-3)
    clarifications_needed: list[ClarificationRequest] = Field(default_factory=list)
    clarification_attempts: int = Field(default=0, description="max 2회 loop 방지")
```

### 3.3 LLM Prompt 갱신

**파일**: `backend/app/dream_agent/llm_manager/prompts/cognitive.yaml` (수정)

**추가 instruction**:
```yaml
# 추가 — clarification 감지
clarification_instruction: |
  사용자 쿼리에 다음과 같은 모호도가 있으면 `clarifications_needed` 에 추가하세요:
  
  1. **Missing field** — 필수 정보 누락:
     - 예: "리뷰 찾아줘" → brand 누락
     - {"type": "missing_field", "field": "brand", "question": "어떤 브랜드의 리뷰를 분석할까요?", "reason": "리뷰 수집 도구는 브랜드명이 필요합니다."}
  
  2. **Default confirm** — default 적용 OK 인지 확인:
     - 예: "블루밍글로우 리뷰 찾아줘" → channel 미명시 (naver default?)
     - {"type": "default_confirm", "field": "channel", "question": "기본 채널인 네이버에서 진행할까요?", "default_value": "naver", "reason": "채널을 명시하지 않으셨습니다."}
  
  3. **Ambiguity** — entity 다중 해석:
     - 예: "아모레 글로우 네이버 리뷰" → 1 brand vs 2 brand
     - {"type": "ambiguity", "field": "brand", "question": "어떤 의미인가요?", "options": ["아모레퍼시픽 글로우 (1개 brand)", "아모레퍼시픽 + 블루밍글로우 (2개 brand)"], "reason": "브랜드명 분리가 모호합니다."}
  
  필수 정보가 충분하거나 default 가 명확하면 빈 list 반환.
```

### 3.4 Acceptance — E3-1

- [ ] ClarificationRequest 모델 추가
- [ ] StructuredQuery 에 clarifications_needed + clarification_attempts 필드
- [ ] cognitive prompt 갱신 (3 유형 instruction)
- [ ] 단위 테스트: ClarificationRequest validation

---

## 4. E3-2: Required Field Validator (~30분)

### 4.1 목표

LLM 이 clarification 감지 누락 시 **자동 backup** — required field (brand 등) 비어있으면 ClarificationRequest 자동 추가.

### 4.2 파일

**경로**: `backend/app/dream_agent/cognitive/clarification_validator.py` (신규)

### 4.3 코드

```python
"""Clarification Validator — Sprint 15 P0 E-3.

LLM 이 누락한 모호도를 backup 으로 감지.

Status: complete — Sprint 15 P0.
"""

from app.core.logging import get_logger
from app.dream_agent.schemas.structured_query import (
    StructuredQuery,
    ClarificationRequest,
)

logger = get_logger(__name__)


# Required fields by intent
REQUIRED_FIELDS_BY_INTENT = {
    "review_analysis": ["brand"],
    "data_collection": ["brand"],
    "report_generation": ["brand"],
    # ... 다른 intent
}


def validate(sq: StructuredQuery) -> StructuredQuery:
    """Required field 검사 — 누락 시 ClarificationRequest 자동 추가.
    
    LLM 이 clarifications_needed 에 이미 추가했으면 중복 안 함.
    """
    intent_str = (sq.intent.category if sq.intent else None) or ""
    required = REQUIRED_FIELDS_BY_INTENT.get(intent_str, [])
    
    existing_fields = {c.field for c in sq.clarifications_needed}
    new_clarifications = list(sq.clarifications_needed)
    
    for field in required:
        if field in existing_fields:
            continue  # LLM 이 이미 추가
        
        # entity 에서 값 찾기
        value = _extract_entity_value(sq, field)
        if value:
            continue  # 값 있음
        
        # 누락 → 자동 추가
        new_clarifications.append(ClarificationRequest(
            type="missing_field",
            field=field,
            question=_default_question(field),
            reason=f"{field} 정보가 필요합니다.",
        ))
        logger.info("validator added clarification", field=field, intent=intent_str)
    
    sq_dict = sq.model_dump()
    sq_dict["clarifications_needed"] = [c.model_dump() for c in new_clarifications]
    return StructuredQuery.model_validate(sq_dict)


def _extract_entity_value(sq: StructuredQuery, field: str) -> str | None:
    """entities 에서 field 값 추출."""
    if not sq.entities:
        return None
    for entity in sq.entities:
        if entity.type == field and entity.value:
            return entity.value
    return None


def _default_question(field: str) -> str:
    """field 별 기본 질문."""
    questions = {
        "brand": "어떤 브랜드를 분석할까요?",
        "channel": "어떤 채널 (네이버 / 인스타 / 등) 에서 수집할까요?",
        "period": "분석 기간은 어떻게 설정할까요? (예: 최근 30일)",
    }
    return questions.get(field, f"{field} 를 알려주세요.")
```

### 4.4 단위 테스트

**경로**: `backend/tests/sprint15/test_clarification_validator_unit.py` (신규)

- TC-CV-01: brand 누락 → 자동 추가
- TC-CV-02: brand 있음 → skip
- TC-CV-03: LLM 이 이미 추가 → 중복 X
- TC-CV-04: REQUIRED_FIELDS_BY_INTENT 매핑 정확

### 4.5 Acceptance — E3-2

- [ ] clarification_validator.py 신규
- [ ] validate() 함수
- [ ] 4 TC 통과

---

## 5. E3-3: Cognitive Node 통합 (~1시간)

### 5.1 목표

Cognitive node 에서:
1. LLM 호출 → StructuredQuery
2. **Validator backup** 적용
3. **메모리 cascade** — 답이 있으면 augment + skip
4. 여전히 남으면 **interrupt(type="clarification")**
5. 사용자 답변 → memory 저장 + cognitive 재실행
6. **max 2회** 도달 시 직진 + warning

### 5.2 파일

**경로**: `backend/app/dream_agent/cognitive/cognitive_stage.py` (수정)

### 5.3 변경 흐름

```python
async def cognitive_node(state, config):
    session_id = state["session_id"]
    user_id = state.get("user_id", "demo")
    query = state["query"]
    
    # 1. 메모리 cascade (Phase E-2 에서 추가됨)
    mm = get_memory_manager()
    context = await mm.get_context(session_id, user_id)
    augmented_query = augment_query_with_context(query, context)
    
    # 2. Cognitive LLM 호출
    sq = await cognitive_llm.generate(augmented_query)
    
    # 3. Validator backup
    from .clarification_validator import validate
    sq = validate(sq)
    
    # 4. 메모리 cascade — 답이 있으면 자동 augment
    for req in list(sq.clarifications_needed):
        answer = await mm.find_clarification_answer(
            session_id=session_id, user_id=user_id, field=req.field,
        )
        if answer:
            sq = augment_with_answer(sq, req.field, answer)
            sq.clarifications_needed.remove(req)
            logger.info("clarification auto-resolved from memory", field=req.field, value=answer)
    
    # 5. 여전히 남으면 interrupt (max 2회)
    if sq.clarifications_needed:
        if sq.clarification_attempts >= 2:
            # max 도달 — 직진 + warning
            logger.warning(
                "clarification max attempts reached, proceeding with defaults",
                fields=[c.field for c in sq.clarifications_needed],
            )
            # default 적용 또는 빈 값 진행
            sq.clarifications_needed = []  # clear
        else:
            # interrupt
            from langgraph.types import interrupt
            user_response = interrupt({
                "type": "clarification",
                "session_id": session_id,
                "requests": [c.model_dump() for c in sq.clarifications_needed],
                "attempts": sq.clarification_attempts,
            })
            
            # 사용자 답변 처리
            for req in sq.clarifications_needed:
                value = user_response.get(req.field)
                if value is not None:
                    sq = augment_with_answer(sq, req.field, value)
                    # 메모리 저장 (다음 turn 자동 활용)
                    await mm.store_clarification(
                        session_id=session_id, user_id=user_id,
                        field=req.field, value=value,
                    )
            
            sq.clarification_attempts += 1
            sq.clarifications_needed = []  # 처리 완료
    
    # 6. Planning 진입
    return Command(
        update={"structured_query": sq.model_dump()},
        goto="planning",
    )


def augment_with_answer(sq: StructuredQuery, field: str, value: Any) -> StructuredQuery:
    """답변을 entities 에 추가 (또는 적절한 위치)."""
    sq_dict = sq.model_dump()
    # entities 에 추가
    entities = sq_dict.get("entities", [])
    entities.append({"type": field, "value": value, "source": "clarification"})
    sq_dict["entities"] = entities
    return StructuredQuery.model_validate(sq_dict)
```

### 5.4 helper 함수

**파일**: `backend/app/dream_agent/cognitive/clarification_helpers.py` (신규, ~30 LoC)

- `augment_with_answer(sq, field, value) -> StructuredQuery`
- `augment_query_with_context(query, context) -> str` (Phase E-2 와 일치)

### 5.5 Acceptance — E3-3

- [ ] cognitive_node 6 단계 흐름
- [ ] memory cascade 자동 augment
- [ ] interrupt(type="clarification") 작동
- [ ] max 2회 loop 방지
- [ ] 단위 테스트: 메모리 hit / miss / max 도달 시나리오

---

## 6. E3-4: ws_hitl 신규 message type (~1시간)

### 6.1 목표

LangGraph interrupt(type="clarification") → ws_agent broadcast → 대시보드 모달 → 답변 → ws_hitl resume.

### 6.2 ws_agent 변경

**파일**: `backend/api_v2/ws_agent.py` (수정)

**변경**: interrupt payload 의 type 별 분기 추가
```python
# _build_hitl_request_data 또는 broadcast 지점
if intr_value.get("type") == "clarification":
    # 신규 message type
    await broadcast({
        "type": "clarification_request",
        "session_id": session_id,
        "requests": intr_value.get("requests"),
        "attempts": intr_value.get("attempts"),
    })
else:
    # 기존 plan_review / pause
    ...
```

### 6.3 ws_hitl 변경

**파일**: `backend/api_v2/ws_hitl.py` (수정)

**추가 메시지 핸들러**:
```python
async def _handle_clarification_response(websocket: WebSocket, data: dict) -> None:
    """clarification_response — Sprint 15 P0 E-3.
    
    Status: complete — Sprint 15 P0.
    """
    # 1. is_turn_active 가드
    is_active, turn_id = await _check_turn_active(websocket, data, "clarification_response")
    if not is_active:
        return
    
    payload = data.get("data", {})
    session_id = payload.get("session_id") or turn_id
    answers = payload.get("answers", {})  # {field: value}
    
    if not session_id or not answers:
        await _safe_send(websocket, {"type": "error", **ErrorCodes.INVALID_MESSAGE})
        return
    
    # 2. resume — Cognitive 가 interrupt 에서 받을 dict
    hitl = get_hitl_manager()
    await hitl.signal_resume(session_id, answers)
    
    # 3. ack
    await _safe_send(websocket, {
        "type": "hitl_ack",
        "data": {
            "action": "clarification_response",
            "session_id": session_id,
            "accepted": True,
        },
    })
```

**routing 추가**:
```python
# 메시지 타입별 dispatch (기존 todo_delete / todo_edit_nl 등 옆에)
elif msg_type == "clarification_response":
    await _handle_clarification_response(websocket, data)
```

### 6.4 Acceptance — E3-4

- [ ] ws_agent 의 interrupt payload 분기
- [ ] ws_hitl 의 _handle_clarification_response 핸들러
- [ ] resume 흐름 작동
- [ ] 통합 테스트 (group J — Clarification)

---

## 7. E3-5: 대시보드 Clarification 모달 (~1시간)

### 7.1 목표

`clarification_request` 수신 → 모달 표시 → 사용자 답변 → `clarification_response` 송신.

**UX 사용자 의도 lock**: "기존 todo 유지 + 부족분 요청".

### 7.2 변경

**파일**: `dashboard/index.html` (수정)

### 7.3 모달 HTML 구조

```html
<!-- 신규 — Clarification 모달 -->
<div id="clarification-overlay" class="modal-overlay hidden">
    <div class="modal-content">
        <h3>💬 정보 보완 요청</h3>
        <p id="clarification-intro">분석을 시작하기 전에 몇 가지 정보를 알려주세요.</p>
        <div id="clarification-fields"></div>
        <div class="modal-actions">
            <button id="clarification-submit" class="primary">✅ 확인</button>
            <button id="clarification-cancel" class="secondary">❌ 취소</button>
        </div>
    </div>
</div>
```

### 7.4 JavaScript

```javascript
// clarification_request 수신
function handleClarificationRequest(data) {
    const requests = data.requests;
    const container = document.getElementById('clarification-fields');
    container.innerHTML = '';
    
    requests.forEach(req => {
        const fieldDiv = document.createElement('div');
        fieldDiv.className = 'clarification-field';
        fieldDiv.dataset.field = req.field;
        
        let inputHtml = '';
        if (req.type === 'missing_field') {
            // text input
            inputHtml = `
                <label>${req.question}</label>
                <p class="reason">${req.reason}</p>
                <input type="text" id="clar-${req.field}" required>
            `;
        } else if (req.type === 'default_confirm') {
            // Yes/No 라디오
            inputHtml = `
                <label>${req.question}</label>
                <p class="reason">${req.reason}</p>
                <label><input type="radio" name="clar-${req.field}" value="${req.default_value}" checked> 네, ${req.default_value} 로 진행</label>
                <label><input type="radio" name="clar-${req.field}" value="other"> 다른 값:</label>
                <input type="text" id="clar-${req.field}-other" placeholder="다른 값 입력">
            `;
        } else if (req.type === 'ambiguity') {
            // 옵션 라디오
            const optionsHtml = req.options.map((opt, i) =>
                `<label><input type="radio" name="clar-${req.field}" value="${i}"> ${opt}</label>`
            ).join('<br>');
            inputHtml = `
                <label>${req.question}</label>
                <p class="reason">${req.reason}</p>
                ${optionsHtml}
            `;
        }
        
        fieldDiv.innerHTML = inputHtml;
        container.appendChild(fieldDiv);
    });
    
    document.getElementById('clarification-overlay').classList.remove('hidden');
}

// 답변 송신
async function submitClarification() {
    const fields = document.querySelectorAll('.clarification-field');
    const answers = {};
    
    fields.forEach(div => {
        const field = div.dataset.field;
        // 입력 type 별 값 추출
        const text = div.querySelector(`#clar-${field}`)?.value;
        const radio = div.querySelector(`input[name="clar-${field}"]:checked`);
        const otherText = div.querySelector(`#clar-${field}-other`)?.value;
        
        if (radio && radio.value === 'other' && otherText) {
            answers[field] = otherText;
        } else if (radio) {
            answers[field] = radio.value;
        } else if (text) {
            answers[field] = text;
        }
    });
    
    // ws_hitl 송신
    sendHitlMessage({
        type: 'clarification_response',
        data: {
            session_id: _currentSessionId,
            answers: answers,
        },
    });
    
    document.getElementById('clarification-overlay').classList.add('hidden');
}

// 이벤트 wire-up
document.getElementById('clarification-submit').addEventListener('click', submitClarification);
document.getElementById('clarification-cancel').addEventListener('click', () => {
    // 취소 = turn 종료 (또는 default 진행 — UX 결정)
    document.getElementById('clarification-overlay').classList.add('hidden');
});

// ws_agent message handler 에서
if (msg.type === 'clarification_request') {
    handleClarificationRequest(msg);
}
```

### 7.5 CSS (간단)

```css
.modal-overlay { position: fixed; ... }
.clarification-field { margin: 12px 0; }
.reason { color: #888; font-size: 0.9em; }
```

### 7.6 Acceptance — E3-5

- [ ] 모달 HTML
- [ ] 3 유형 (missing_field / default_confirm / ambiguity) UI
- [ ] 답변 송신 정상
- [ ] 사용자 브라우저 검증

---

## 8. E3-6: E2E 통합 시나리오 (~30분)

### 8.1 R-19 — Missing field

**시나리오**:
1. 첫 사용자, 메모리 비어있음
2. 쿼리: `"리뷰를 찾아줘"` (brand 누락)
3. Cognitive → clarifications_needed = [brand]
4. interrupt → 모달 표시: "어떤 브랜드를 분석할까요?"
5. 사용자: "블루밍글로우" 입력 → 답변 송신
6. memory.store_clarification(brand="블루밍글로우")
7. Cognitive 재실행 → planning → execution → response

**검증**:
- [ ] 모달 표시됨
- [ ] 답변 후 진행 정상
- [ ] DB 에 entry 생성: type=preference, scope=user, key=brand, value="블루밍글로우"

### 8.2 R-20 — H0 자동 해결

**시나리오** (R-19 직후):
1. 같은 사용자, 메모리에 brand 저장됨
2. 쿼리: `"리뷰를 찾아줘"` (brand 또 누락)
3. Cognitive → clarifications_needed = [brand]
4. **메모리 cascade → 자동 augment, 모달 표시 X**
5. planning → execution → response (brand=블루밍글로우 자동 사용)

**검증**:
- [ ] 모달 표시 안 됨 ⭐ (가장 중요)
- [ ] 결과: brand 블루밍글로우 자동 적용
- [ ] 로그: `clarification auto-resolved from memory field=brand value=블루밍글로우`

### 8.3 R-21 — Default confirm

**시나리오**:
1. 쿼리: `"블루밍글로우 리뷰 찾아줘"` (channel 미명시)
2. Cognitive → default_confirm: channel default = naver
3. 모달: "기본 채널인 네이버에서 진행할까요?" Yes/No
4. Yes → naver 사용
5. 메모리 저장 (사용자가 항상 naver 선호 학습)

### 8.4 R-22 — Ambiguity

**시나리오**:
1. 쿼리: `"아모레 글로우 네이버 리뷰"`
2. Cognitive → ambiguity: brand options 2 개
3. 모달: 라디오 옵션 2 개
4. 선택 → 적용

### 8.5 Acceptance — E3-6

- [ ] R-19 ~ R-22 모두 PASS
- [ ] R-20 의 H0 자동 해결 ⭐ 가장 중요
- [ ] `sprint14_a3_test_log.md` 또는 신규 `sprint15_test_log.md` 세션 추가

---

## 9. 검증 / 테스트 strategy

### 9.1 자동 테스트

```bash
# Group J — Clarification
pytest backend/tests/sprint15/test_clarification_validator_unit.py -v
pytest backend/tests/sprint15/test_clarification_integration.py -v

# 전체 회귀
pytest backend/tests/ -v
```

**기대**: 269 (E-2 + sidebar) + 8 (E-3) = **277+ passed**.

### 9.2 통합 시나리오

§8 의 R-19~R-22.

### 9.3 메모리 검증 (DB)

```sql
-- Clarification 후 자동 저장 확인
SELECT key, content, source, created_at
FROM memory_entries
WHERE type = 'preference' AND scope_type = 'user' AND scope_id = 'demo'
  AND content->>'from_clarification' = 'true';
```

---

## 10. Risk + 완화

| Risk | 완화 |
|------|------|
| LLM 이 모호도 감지 안 함 (false negative) | Validator backup (E3-2) |
| Validator 가 false positive (불필요한 질문) | REQUIRED_FIELDS_BY_INTENT 보수적 정의 + 메모리 cascade 우선 |
| max 2회 도달 후 사용자 frustration | warning 로그 + UX 안내 ("정보 부족, 진행합니다") |
| 메모리 cascade 가 stale 답 적용 | ttl 정책 + 사용자 명시 변경 시 explicit upsert |
| 모달 vs inline UX 결정 변경 | 본 phase = 모달 (사용자 의도). 추후 변경 시 별도 ADR |
| Clarification 답변 송신 실패 (네트워크) | retry + 사용자 visible error |
| 메모리 자동 답이 사용자 의도와 다른 경우 | "지난번처럼 X 로 진행할까요?" confirm 옵션 (Sprint 16+) |

---

## 11. 완료 체크리스트

### E3-1 schema 확장
- [ ] ClarificationRequest 모델
- [ ] StructuredQuery 확장
- [ ] cognitive prompt 갱신

### E3-2 Validator
- [ ] clarification_validator.py
- [ ] 4 TC 통과

### E3-3 Cognitive 통합
- [ ] cognitive_node 6 단계 흐름
- [ ] memory cascade auto-resolve
- [ ] max 2회 loop 방지

### E3-4 ws_hitl
- [ ] interrupt 분기
- [ ] _handle_clarification_response
- [ ] 통합 테스트

### E3-5 대시보드 모달
- [ ] HTML / CSS / JavaScript
- [ ] 3 유형 UI
- [ ] 답변 송신

### E3-6 E2E
- [ ] R-19 (missing) PASS
- [ ] R-20 (H0 자동 해결) PASS ⭐
- [ ] R-21 (default confirm) PASS
- [ ] R-22 (ambiguity) PASS

### Phase E-3 종합
- [ ] 자동 테스트 277+ passed
- [ ] 커밋 (`feat(sprint15): Phase E-3 Clarification HITL — 양방향 의도 통신 + H0 자동 해결`)
- [ ] 다음 [`sprint15_phase_e4_nl_v2.md`](./sprint15_phase_e4_nl_v2.md)

---

## 12. 다음 Phase 연결

Phase E-3 완료 후 → **Phase E-4**: NL 2차 (LLM Tool Routing)

E-3 까지 = **자유 대화 양방향 의도 통신 작동**. E-4 = 자유 대화의 복잡 NL 처리.

[`sprint15_phase_e4_nl_v2.md`](./sprint15_phase_e4_nl_v2.md) 참조.

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-28 | 초안 — Phase E-3 6 sub-phase. schema 확장 + Validator + Cognitive 통합 + ws_hitl + 모달 + E2E. ~4.5h. R-19~22 시나리오 |
| 2026-04-29 | **Messages append-only 정책 명시** (35 spec §0.1 설계 원칙). Clarification 질의/답변은 같은 turn 의 messages 배열에 append. 별도 row 생성 X. preference promote 는 별도 (다음 turn 자동 활용) |
