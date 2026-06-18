# Sprint 15 — Phase E4 세부 작업계획서 (NL 2차 LLM Tool Routing)

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-04-28 |
| Phase | E-4 — NL 2차 (ADR-002 §2차) |
| 마스터 | [`sprint15_implementation_plan.md`](./sprint15_implementation_plan.md) |
| 의존 | Phase E-3 ✅ (Clarification 작동 — Vision H0 + 양방향 통신 토대) |
| 다음 | E-5 (자연 v? bump — 누적 결과 정리) |
| 예상 작업량 | ~6시간 (1~2세션) |
| Acceptance | NL 복잡 명령 + LLM Tool Routing + ISSUE-009/011 자연 해소 + R-21~R-25 PASS |

---

## 0. 본 문서의 역할

Phase E-4 의 **NL 2차 (자유 대화 본격) 첫 구현 작업 카탈로그**.

**Vision 매핑**: H1 발견 가설의 본격 구현. 사용자 도메인 지식 가정 X (LLM 매개 의도 해석).

다루지 않는 것:
- 메모리 통합 (→ Phase E-2 / E-3 작동 가정)
- Pattern 추출 (→ Sprint 17+)
- NL 3차 자유 대화 (→ Sprint 18+ 메모리 + 패턴 기반)

---

## 1. Phase E-4 의 의도

### 1.1 NL 1차 vs 2차 차이

| 차원 | NL 1차 (Sprint 14 A3 + Phase C) | NL 2차 (본 phase) |
|------|------|------|
| 범위 | 단순 자연어 단일 조작 ("4번 삭제") | 복잡 NL 다중 조작 + LLM Tool Routing |
| LLM 호출 | 1회 (parse_instruction) | 다중 가능 (intent → routing → planning) |
| Tool 매핑 | 사용자가 명시 또는 기존 todo 의 tool 유지 | **LLM 이 task → tool 자동 매핑** |
| 예시 | "4번 삭제", "3-4 순서 바꿔" | "가격대 낮은 경쟁사만 남기기", "감성 강도별로 클러스터링", "이거 빠르게 끝내줘" |
| ISSUE | — | **ISSUE-009 / 011 자연 해결** |

### 1.2 ISSUE 자연 해결 매핑

| ISSUE | NL 2차 적용으로 해소 방법 |
|------|------|
| **009** tool 미지정 SKIP | 사용자가 task 만 입력 → LLM 이 tool catalog 보고 매핑 → SKIP 안 됨 |
| **011** pdf_renderer hallucination | LLM Tool Routing 에 catalog grounding 강제 → catalog 외 tool 생성 X |

→ **NL 2차 = ISSUE-009/011 의 본질적 해결**.

### 1.3 작업 원칙

- **ADR-002 §2차** 기반
- **메모리 활용** — 사용자 자주 사용 tool 패턴 등 (Phase E-2/E-3 산출물)
- **catalog grounding** — LLM 이 catalog 안의 tool 만 사용

---

## 2. 작업 분해 — 5 sub-phase

```
E4-1  Tool catalog grounding 강화 (LLM 입력에 catalog 포함)
        ↓
E4-2  plan_editor 확장 — multi-step + tool 매핑
        ↓
E4-3  복잡 NL prompt 작성
        ↓
E4-4  ISSUE-009/011 회귀 fix 검증
        ↓
E4-5  E2E 시나리오 R-23~R-25
```

### 시간 추정

| Sub-phase | 시간 | 누적 |
|-----------|------|------|
| E4-1 catalog grounding | 1.5h | 1.5h |
| E4-2 plan_editor 확장 | 2h | 3.5h |
| E4-3 NL 2차 prompt | 1h | 4.5h |
| E4-4 ISSUE 회귀 | 1h | 5.5h |
| E4-5 E2E 검증 | 30min | **6h** |

---

## 3. E4-1: Tool Catalog Grounding (~1.5시간)

### 3.1 목표

LLM 이 plan / NL 편집 시 **catalog 외 tool 생성 못 하도록** 강제. ISSUE-011 (pdf_renderer hallucination) 자연 해소.

### 3.2 작업 1.1 — Tool Catalog 로더 강화

**파일**: `backend/app/dream_agent/tools/registry.py` (수정)

**기능**:
- 모든 catalog YAML 파일 로드 → 통합 dict
- `get_tool_catalog_summary()` — LLM prompt 에 주입할 형태:
  - tool name / description / required params / category
- `is_valid_tool(name) -> bool` — catalog 검증

**골격**:
```python
def get_tool_catalog_summary() -> list[dict]:
    """LLM prompt 주입용 — 모든 tool 의 핵심 정보."""
    catalog = load_tool_catalog()  # 기존 함수
    summary = []
    for name, spec in catalog.items():
        summary.append({
            "name": name,
            "description": spec.get("description"),
            "category": spec.get("category"),
            "required_params": [
                p["name"] for p in spec.get("parameters", [])
                if p.get("required")
            ],
            "produces": spec.get("produces", []),
            "depends_on": spec.get("dependencies", []),
        })
    return summary


def is_valid_tool(name: str) -> bool:
    """LLM 출력 검증."""
    return name in load_tool_catalog()
```

### 3.3 작업 1.2 — Planning stage3 prompt 강화

**파일**: `backend/app/dream_agent/llm_manager/prompts/planning_stage3_todo.yaml` (수정)

**추가 instruction**:
```yaml
# 추가 — catalog grounding
catalog_grounding: |
  ## ⚠️ 중요: Tool Catalog 외 사용 금지
  
  아래 catalog 에 명시된 tool 만 사용하세요. 다른 이름의 tool 을 만들거나
  추측하지 마세요. catalog 외 tool 사용 시 시스템이 reject 합니다.
  
  Tool catalog:
  {catalog_summary_json}
  
  각 todo 의 `tool` 필드는 반드시 위 catalog 의 name 중 하나여야 합니다.
```

→ template 변수에 `catalog_summary_json` 추가.

### 3.4 작업 1.3 — Planning stage3 출력 검증

**파일**: `backend/app/dream_agent/planning/planner.py` (수정)

**변경 — `_build_todos` 의 출력 검증**:
```python
async def _build_todos(self, sq_json: str, agents_selected: list[str]) -> Plan | None:
    # ... LLM 호출
    
    plan = Plan.model_validate(result)
    
    # 신규: catalog grounding 검증
    from app.dream_agent.tools.registry import is_valid_tool
    invalid_todos = [t.id for t in plan.todos if t.tool and not is_valid_tool(t.tool)]
    if invalid_todos:
        logger.error(
            "planner generated invalid tool",
            invalid_todos=invalid_todos,
        )
        # 옵션 1: 자동 fix — invalid tool → None (executor 가 SKIP)
        # 옵션 2: re-prompt LLM (Sprint 16+)
        # POC: 옵션 1
        for t in plan.todos:
            if t.tool and not is_valid_tool(t.tool):
                logger.warning(f"todo {t.id} tool '{t.tool}' invalid, removing")
                t.tool = None
    
    return plan
```

### 3.5 단위 테스트

**경로**: `backend/tests/sprint15/test_catalog_grounding_unit.py` (신규)

**TC**:
- TC-CG-01: get_tool_catalog_summary 모든 tool 포함
- TC-CG-02: is_valid_tool — 유효 tool True
- TC-CG-03: is_valid_tool — 가상 tool ("pdf_renderer") False
- TC-CG-04: planner 가 invalid tool 생성 시 자동 None 처리

### 3.6 Acceptance — E4-1

- [ ] registry.py 의 catalog summary + is_valid_tool
- [ ] planning prompt 에 catalog 주입
- [ ] planner 의 출력 검증
- [ ] 4 TC 통과
- [ ] **ISSUE-011 회귀 테스트**: "PDF 렌더링" 같은 쿼리 → pdf_renderer 생성 안 됨 확인

---

## 4. E4-2: plan_editor 확장 — Multi-step (~2시간)

### 4.1 목표

NL 1차의 단일 action (add/remove/modify/reorder) 를 **multi-step plan** 으로 확장.

예: "가격대 낮은 경쟁사만 남기기" → 다중 remove + reorder + (optional) modify.

### 4.2 파일

**경로**: `backend/app/dream_agent/workflow_managers/hitl_manager/plan_editor.py` (수정)

### 4.3 변경 — multi-step action

**parse_instruction 출력 확장**:
```python
# Before (NL 1차):
{
    "action": "remove",
    "target_todo_ids": ["t1"],
    "params": {},
    "reason": "..."
}

# After (NL 2차):
{
    "actions": [  # ← list, multi-step
        {"action": "remove", "target_todo_ids": ["t3", "t5"], "params": {}},
        {"action": "modify", "target_todo_ids": ["t1"], "params": {"priority": 1}},
        {"action": "reorder", "target_todo_ids": ["t2"], "params": {"new_position": 0}},
    ],
    "reason": "...",
    "interpretation": "사용자가 가격대 낮은 경쟁사만 남기길 원함",
}
```

**호환성**: NL 1차 형식 (단일 `action`) 도 받아 [{...}] 으로 변환.

### 4.4 apply_edit 확장

```python
async def apply_edit(
    self, plan: Plan, parsed: dict[str, Any], user_instruction: str,
) -> tuple[Plan, list[PlanChange]]:
    """Multi-step apply.
    
    Returns:
        (수정된 Plan, 변경 list — 각 step 별 PlanChange)
    """
    # NL 1차 호환
    actions = parsed.get("actions") or [
        {
            "action": parsed.get("action"),
            "target_todo_ids": parsed.get("target_todo_ids", []),
            "params": parsed.get("params", {}),
        }
    ]
    
    current_plan = plan
    changes: list[PlanChange] = []
    
    for step in actions:
        new_plan, change = await self._apply_single_step(current_plan, step, user_instruction)
        current_plan = new_plan
        changes.append(change)
    
    return current_plan, changes


async def _apply_single_step(self, plan: Plan, step: dict, instruction: str):
    """기존 apply_edit 의 single step logic."""
    action = step.get("action", "unknown")
    target_ids = step.get("target_todo_ids", [])
    params = step.get("params", {})
    # ... 기존 add/remove/modify/reorder logic
```

### 4.5 LLM Tool Routing — 사용자 새 todo 의 자동 tool 매핑

**Use case**: 사용자가 "Twitter 리뷰 분석 추가" → tool 미지정. NL 2차에서 LLM 이 catalog 보고 자동 매핑.

**구현**:
```python
async def parse_instruction(
    self, instruction: str, plan: Plan,
) -> dict[str, Any]:
    """NL 2차 — multi-step + tool routing."""
    
    # 신규: catalog summary 주입
    from app.dream_agent.tools.registry import get_tool_catalog_summary
    catalog = get_tool_catalog_summary()
    
    system_prompt = """
    당신은 Plan 편집을 multi-step 으로 변환하는 AI 입니다.
    
    ## 지원 actions (각 step):
    - add: Todo 추가 (tool 미지정 시 catalog 에서 자동 매핑)
    - remove: Todo 삭제
    - modify: Todo 수정
    - reorder: 순서 변경
    
    ## ⚠️ Tool Catalog (반드시 이 안에서만 선택)
    {catalog_json}
    
    ## 응답 형식 (JSON)
    {
        "actions": [...],
        "reason": "...",
        "interpretation": "..."
    }
    """.format(catalog_json=json.dumps(catalog, ensure_ascii=False, indent=2))
    
    # ... LLM 호출
```

### 4.6 ISSUE-009 자연 해결

`add` action 시 LLM 이 tool 자동 매핑:
- 사용자: "+ Twitter 리뷰 분석 추가"
- LLM 출력:
  ```json
  {
    "actions": [
      {
        "action": "add",
        "params": {
          "agent": "analysis_agent",
          "task": "Twitter 리뷰 분석",
          "tool": "naver_collector",  // ← LLM 이 catalog 에서 매핑 (또는 가장 가까운)
          "tool_params": {"brand": "..."}
        }
      }
    ]
  }
  ```

→ **tool 미지정 SKIP (ISSUE-009) 자연 해결**.

### 4.7 단위 테스트

**경로**: `backend/tests/sprint15/test_plan_editor_v2_unit.py` (신규)

**TC**:
- TC-PE-V2-01: NL 2차 multi-step parse — actions list
- TC-PE-V2-02: NL 1차 형식 → 자동 변환
- TC-PE-V2-03: add 시 tool 자동 매핑 (catalog grounding)
- TC-PE-V2-04: 유효하지 않은 tool 거부

### 4.8 Acceptance — E4-2

- [ ] parse_instruction 의 actions list 반환
- [ ] apply_edit multi-step
- [ ] catalog grounding LLM prompt
- [ ] tool 자동 매핑 작동
- [ ] 4 TC 통과

---

## 5. E4-3: 복잡 NL Prompt 작성 (~1시간)

### 5.1 파일

**경로**: `backend/app/dream_agent/llm_manager/prompts/nl_edit_v2.yaml` (신규)

또는 기존 `plan_editor` 안의 prompt 확장.

### 5.2 Prompt 내용

```yaml
system_prompt: |
  당신은 사용자의 자연어 명령을 Plan 편집 multi-step 으로 변환하는 AI 입니다.
  
  ## 사용자 의도 해석
  사용자가 명시한 의미와 implicit 의미를 모두 고려하세요.
  
  예시:
  - "가격대 낮은 경쟁사만 남기기"
    → 의미: 가격대 낮은 경쟁사가 아닌 todo 들 모두 remove
    → 단계: 1) entities 분석 (어느 todo 가 가격대 높은 경쟁사?) 2) remove 단계 다중
  
  - "감성 강도별로 클러스터링"
    → 의미: sentiment_analyzer 결과를 강도 그룹화
    → 단계: 1) 기존 todo 유지 2) 신규 todo 추가 (cluster_tool, depends_on=sentiment)
  
  - "이거 빠르게 끝내줘"
    → 의미: 우선순위 ↑ + 부수 todo (예: PDF) 제외
    → 단계: 1) priority 변경 2) 부수 todo remove
  
  ## 다단계 처리
  여러 actions 를 list 로 반환. 각 step 은 독립적이지 않을 수 있음 (순서 중요).
  
  ## Tool 자동 매핑
  사용자가 task 만 입력하고 tool 미지정 시, catalog 에서 가장 적합한 tool 자동 선택.
  
  {catalog_grounding}
  
  ## 응답 형식
  {output_format_json}
```

### 5.3 응답 형식 (JSON Schema)

```json
{
  "actions": [
    {
      "action": "add | remove | modify | reorder",
      "target_todo_ids": ["t1", "t2"],
      "params": {
        "task": "...",
        "tool": "...",
        "tool_params": {...},
        "priority": 1,
        "new_position": 0
      }
    }
  ],
  "reason": "사용자 의도 설명",
  "interpretation": "implicit 의미 해석",
  "confidence": 0.0 ~ 1.0
}
```

### 5.4 Acceptance — E4-3

- [ ] nl_edit_v2.yaml 작성
- [ ] catalog grounding 통합
- [ ] LLM 응답 형식 명시

---

## 6. E4-4: ISSUE 회귀 검증 (~1시간)

### 6.1 ISSUE-009 — Tool 미지정 SKIP

**테스트 시나리오**:
1. Plan review 모달
2. 🗣 textarea: `"트위터 리뷰 분석 추가"` (tool 미지정)
3. NL 2차 처리 → LLM 이 catalog 에서 매핑
4. add action with tool=auto-matched
5. Execution 시 SKIP 안 됨

**Acceptance**:
- [ ] tool 자동 매핑 작동
- [ ] 추가된 todo 가 execution 정상 (skip X)
- [ ] log 에 `LLM tool routing tool=...` 표시

### 6.2 ISSUE-011 — Hallucination

**테스트 시나리오**:
1. 쿼리: `"리뷰 분석하고 PDF 로 출력"` (planning stage3 시점에서 발생)
2. Stage3 LLM 출력 → catalog grounding 으로 pdf_renderer 같은 hallucination 차단
3. todo.tool = None or 가장 가까운 tool (예: report_writer)
4. Execution 정상 또는 명시적 SKIP

**Acceptance**:
- [ ] catalog 외 tool 생성 안 됨
- [ ] 또는 자동 fix (None / 대체)
- [ ] log 검증

---

## 7. E4-5: E2E 시나리오 R-23~R-25 (~30분)

### 7.1 R-23 — 복잡 NL 다중 조작

**시나리오**:
1. Plan: 8 todos
2. NL: `"감성 분석 빼고, 키워드 추출은 우선순위 1로, 마지막에 요약 추가"`
3. 기대 결과:
   - actions: [
     {action: remove, target: [sentiment_analyzer]},
     {action: modify, target: [keyword_extractor], params: {priority: 1}},
     {action: add, params: {task: "요약", tool: "summary_generator"}},
   ]
4. 모달 갱신 + 사용자 승인 → execution

### 7.2 R-24 — Tool 자동 매핑

**시나리오**:
1. Plan: 5 todos
2. NL: `"분석 추가"` (모호 — 여러 분석 tool 가능)
3. LLM 이 catalog 보고 적합한 tool 매핑 또는 clarification trigger
4. 답변 → tool 확정 → add

### 7.3 R-25 — Hallucination 방어

**시나리오**:
1. NL: `"동영상 만들어 추가"` (catalog 에 video tool 없음)
2. LLM 이 catalog 외 tool 생성 시도 → reject 또는 ambiguity clarification
3. 사용자 안내: "현재 catalog 에 동영상 tool 이 없습니다."

### 7.4 Acceptance — E4-5

- [ ] R-23 ~ R-25 모두 PASS
- [ ] log 검증

---

## 8. 검증 / 테스트 strategy

### 8.1 자동 테스트

```bash
# Phase E-4 단위 + 통합
pytest backend/tests/sprint15/test_catalog_grounding_unit.py -v
pytest backend/tests/sprint15/test_plan_editor_v2_unit.py -v

# 전체 회귀
pytest backend/tests/ -v
```

**기대**: 277 (E-3) + 8 (E-4) = **285+ passed**.

### 8.2 ISSUE 회귀

- ISSUE-009: § 6.1 시나리오
- ISSUE-011: § 6.2 시나리오

### 8.3 E2E (사용자 검증)

R-23/24/25.

---

## 9. Risk + 완화

| Risk | 완화 |
|------|------|
| LLM 의 multi-step 해석 부정확 | confidence 점수 + 사용자 확인 (interpretation 필드 모달 표시) |
| catalog grounding 강제 → 새 tool 도입 시 마찰 | tool 추가 = registry.py 자동 인식 (yaml 추가만) |
| Tool 자동 매핑 부적절 (잘못된 tool 선택) | clarification trigger (E-3) 우선 |
| LLM 비용 증가 (긴 prompt + multi-step) | 토큰 cap (1500) + caching (Sprint 16+) |
| NL 1차 호환성 깨짐 | parse_instruction 의 자동 변환 (단일 → list) + 회귀 테스트 |
| 사용자 의도 와 다른 multi-step 결과 | "이렇게 진행할까요?" preview 모달 (Sprint 16+ — 본 phase 는 직진) |

---

## 10. 완료 체크리스트

### E4-1 catalog grounding
- [ ] registry.py 강화
- [ ] planning prompt 갱신
- [ ] planner 출력 검증
- [ ] 4 TC

### E4-2 plan_editor 확장
- [ ] multi-step parse
- [ ] multi-step apply
- [ ] tool 자동 매핑
- [ ] 4 TC

### E4-3 NL 2차 prompt
- [ ] nl_edit_v2.yaml
- [ ] catalog grounding 통합

### E4-4 ISSUE 회귀
- [ ] ISSUE-009 자연 해결 검증
- [ ] ISSUE-011 자연 해결 검증
- [ ] known_issues 갱신

### E4-5 E2E
- [ ] R-23 (복잡 NL 다중) PASS
- [ ] R-24 (tool 자동 매핑) PASS
- [ ] R-25 (hallucination 방어) PASS

### Phase E-4 종합
- [ ] 자동 테스트 285+ passed
- [ ] ADR-002 §2차 완료 표기
- [ ] 커밋 (`feat(sprint15): Phase E-4 NL 2차 LLM Tool Routing — ISSUE-009/011 자연 해소`)
- [ ] 다음 E-5 (자연 v? bump)

---

## 11. 다음 Phase 연결

Phase E-4 완료 후 → **Phase E-5**: 자연 v? bump (변경 누적 결과)

E-1 ~ E-4 의 모든 변경을 spec / ADR / INDEX 일괄 정리.

---

## 12. 본 Phase 후 — Sprint 15 종결

### 12.1 산출물 정리

- 메모리 시스템 (E-1) ✅
- 채팅 메모리 통합 (E-2) ✅
- Clarification HITL (E-3) ✅ — H0 자동 해결
- NL 2차 (E-4) ✅ — H1 본격

### 12.2 Vision 진척

| 가설 | Sprint 15 결과 |
|------|------|
| H0 의도 모호성 | ✅ 자동 해결 메커니즘 작동 |
| H1 발견 | ✅ NL 2차로 본격 |
| H2 학습 데이터 누적 | ✅ 메모리 인프라 + 자동 저장 |
| H3 패턴화 | ⏳ Sprint 17+ (메모리 누적 후) |
| H4 맞춤화 | ⏳ Sprint 18+ |

### 12.3 Sprint 16+ 후속

- 패턴 추출 (Sprint 17)
- 맞춤형 에이전트 (Sprint 18+)
- 풀 lifecycle metadata (PlannedTodo 확장)
- 외부 시스템 통합 (LangGraph Store 호환 등)

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-28 | 초안 — Phase E-4 5 sub-phase. Catalog grounding + plan_editor 확장 + NL 2차 prompt + ISSUE-009/011 자연 해소 + R-23~25. ~6h. ADR-002 §2차 |
