# 제로베이스 개발 문서 가이드

> 소프트웨어 개발 시 어떤 문서를, 어떤 순서로 만들어야 하는지 안내합니다.
> 이 가이드를 따라 단계별로 문서를 작성하면 체계적인 개발이 가능합니다.

---

## 문서 작성 순서 (필수)

```
Step 1: 제품 기획서 (Product Spec)
    ↓
Step 2: 유스케이스 (Use Cases)
    ↓
Step 3: 아키텍처 (Architecture)
    ↓
Step 4: 계약 (Contract)
    ↓
Step 5: 타입 정의 (Types)
    ↓
Step 6: 구현 (Implementation)
```

**중요**: 이 순서를 지키지 않으면 나중에 큰 수정이 필요해집니다.

---

## Step 1: 제품 기획서 (Product Spec)

### 목적
"무엇을 만들 것인가?"를 정의합니다.

### 작성 위치
```
docs/specs/PRODUCT_SPEC.md
```

### 포함 내용

```markdown
# 제품명

## 1. 문제 정의
- 이 제품이 해결하려는 문제는 무엇인가?
- 왜 이 문제를 해결해야 하는가?

## 2. 목표 사용자
- 누가 이 제품을 사용하는가?
- 사용자의 기술 수준은?

## 3. 핵심 기능 (Features)
| 기능 ID | 기능명 | 설명 | 우선순위 |
|---------|--------|------|----------|
| F001 | 의도 분석 | 사용자 입력에서 의도 추출 | 필수 |
| F002 | 작업 계획 | 의도에 따른 실행 계획 생성 | 필수 |
| ... | ... | ... | ... |

## 4. 제약 조건
- 기술적 제약 (예: Python 3.10+)
- 비용 제약 (예: LLM API 비용)
- 시간 제약 (예: 응답 시간 3초 이내)

## 5. 성공 기준
- 어떤 상태가 되면 "완료"인가?
```

### 현재 상태
- [docs/PLANNING.md](./PLANNING.md)에 일부 내용 존재
- **필요 작업**: 위 템플릿에 맞게 정리

---

## Step 2: 유스케이스 (Use Cases)

### 목적
"사용자가 어떻게 사용하는가?"를 구체적으로 정의합니다.

### 작성 위치
```
docs/specs/USE_CASES.md
```

### 포함 내용

```markdown
# 유스케이스 문서

## UC-001: 데이터 수집 요청

### 기본 정보
- Actor: 마케터
- 목표: 올리브영 리뷰 데이터 수집

### 시나리오
1. 사용자가 "올리브영 리뷰 수집해줘"라고 입력
2. 시스템이 의도를 분석 (DATA_SCIENCE.data_collection)
3. 시스템이 실행 계획 생성
4. 실행 결과를 사용자에게 반환

### 입력 예시
- "올리브영 리뷰 수집해줘"
- "네이버 쇼핑 리뷰 1000개 모아줘"

### 출력 예시
```json
{
  "status": "success",
  "data": {...},
  "message": "리뷰 1000개 수집 완료"
}
```

### 예외 상황
- 사이트 차단 시: 에러 메시지 반환
- 데이터 없음: 빈 결과 반환

---

## UC-002: 데이터 분석 요청
...
```

### 현재 상태
- [docs/PLANNING.md](./PLANNING.md)에 간략한 예시만 존재
- **필요 작업**: 모든 도구(18개)에 대한 유스케이스 작성

---

## Step 3: 아키텍처 (Architecture)

### 목적
"어떤 구조로 만들 것인가?"를 정의합니다.

### 작성 위치
```
docs/SYSTEM_ARCHITECTURE.md  (이미 존재)
```

### 포함 내용

```markdown
# 시스템 아키텍처

## 1. 전체 구조도
(다이어그램)

## 2. Layer별 역할
| Layer | 역할 | 입력 | 출력 |
|-------|------|------|------|
| Cognitive | 의도 파악 | 사용자 입력 | Intent |
| Planning | 계획 수립 | Intent | Plan |
| Execution | 실행 | Plan | Result |
| Response | 응답 생성 | Result | Response |

## 3. 컴포넌트별 책임
...

## 4. 데이터 흐름
...
```

### 현재 상태
- [docs/SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md) 존재
- **상태**: 대부분 완료

---

## Step 4: 계약 (Contract)

### 목적
"Layer 간 어떤 데이터를 주고받는가?"를 정의합니다.

### 작성 위치
```
docs/specs/LAYER_CONTRACTS.md  (신규 작성 필요)
```

### 포함 내용

```markdown
# Layer 간 계약

## Contract 1: Cognitive → Planning

### 입력 (Cognitive 출력)
```python
class CognitiveOutput:
    intent: UnifiedIntent
    current_context: str
    dialogue_context: dict
```

### 출력 (Planning 입력)
Planning Layer는 위 CognitiveOutput을 그대로 받음

### 불변 조건 (Invariants)
- intent는 반드시 존재해야 함
- confidence는 0.0 ~ 1.0 범위

### 예외 조건
- 의도 분석 실패 시: fallback intent 사용

---

## Contract 2: Planning → Execution
...
```

### 현재 상태
- [docs/INTERFACE_CONTRACT.md](./INTERFACE_CONTRACT.md)는 REST API 위주
- **필요 작업**: Layer 간 계약 문서 별도 작성

---

## Step 5: 타입 정의 (Types)

### 목적
Contract에서 정의한 데이터 구조를 코드로 작성합니다.

### 작성 위치
```
backend/app/dream_agent/models/
├── intent.py      # UnifiedIntent
├── plan.py        # Plan
├── todo.py        # TodoItem
└── execution.py   # ExecutionResult
```

### 작성 순서
1. **기본 Enum 정의** (IntentDomain 등)
2. **핵심 모델 정의** (UnifiedIntent 등)
3. **관계 설정** (모델 간 참조)

### 현재 상태
- 이미 존재하나 이중 Intent 시스템 문제 있음
- **필요 작업**: Phase 0-1 마이그레이션 계획 참조

---

## Step 6: 구현 (Implementation)

### 목적
타입 정의에 맞춰 실제 로직을 구현합니다.

### 작성 순서
1. Layer 1: Cognitive (의도 파악)
2. Layer 2: Planning (계획 수립)
3. Layer 3: Execution (실행)
4. Layer 4: Response (응답 생성)

### 현재 상태
- 대부분 구현 완료
- **필요 작업**: Pydantic 마이그레이션

---

## 현재 프로젝트 진단

### 존재하는 문서

| 문서 | 상태 | 비고 |
|------|------|------|
| [PLANNING.md](./PLANNING.md) | 부분 완료 | Product Spec 역할, 유스케이스 부족 |
| [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md) | 완료 | 아키텍처 문서 |
| [INTERFACE_CONTRACT.md](./INTERFACE_CONTRACT.md) | 부분 완료 | REST API 위주, Layer 계약 부족 |
| [TOOL_SPECIFICATION.md](./TOOL_SPECIFICATION.md) | 완료 | 도구 스펙 |
| [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) | 부분 완료 | 개발 가이드 |

### 누락된 문서

| 문서 | 우선순위 | 설명 |
|------|----------|------|
| specs/PRODUCT_SPEC.md | 높음 | 체계적인 제품 기획서 |
| specs/USE_CASES.md | 높음 | 상세 유스케이스 |
| specs/LAYER_CONTRACTS.md | 높음 | Layer 간 계약 |

---

## 작업 순서 체크리스트

### Phase A: 문서 정비 (코드 수정 전)

- [ ] **A1**: `docs/specs/` 폴더 생성
- [ ] **A2**: `PRODUCT_SPEC.md` 작성 (PLANNING.md 기반)
- [ ] **A3**: `USE_CASES.md` 작성 (18개 도구별)
- [ ] **A4**: `LAYER_CONTRACTS.md` 작성

### Phase B: 타입 통합 (Pydantic 마이그레이션)

- [ ] **B1**: Phase 0 - Intent 통합 (`reports_mind_dream/cleanup/impl_phase0_*.md` 참조)
- [ ] **B2**: Phase 1 - Foundation 수정
- [ ] **B3**: Phase 2 - Cognitive Layer 수정
- [ ] **B4**: Phase 3-5 - 나머지 Layer 수정

### Phase C: 테스트 및 검증

- [ ] **C1**: 단위 테스트 작성
- [ ] **C2**: 통합 테스트 실행
- [ ] **C3**: 문서 최종 검토

---

## 참고 자료

### 마이그레이션 계획서 (reports_mind_dream/cleanup/)
- `impl_phase0_intent_unification_260203.md` - Intent 통합
- `impl_phase1_foundation_260203.md` - Foundation 수정
- `impl_phase2_cognitive_260203.md` - Cognitive Layer
- `impl_phase3_to_5_260203.md` - 나머지 Phase

### 기존 상세 문서 (README/)
- `README/00_INDEX.md` - 전체 문서 색인
- `README/03_AGENT_LAYERS.md` - 4-Layer 상세 설명

---

## 자주 묻는 질문

### Q: 왜 이 순서를 지켜야 하나요?
A: 뒤의 단계가 앞의 단계에 의존하기 때문입니다.
- 유스케이스가 없으면 어떤 기능이 필요한지 모름
- 아키텍처가 없으면 어디에 코드를 넣을지 모름
- 계약이 없으면 어떤 데이터를 주고받을지 모름
- 타입이 없으면 코드가 일관성 없어짐

### Q: 이미 코드가 있는데 문서부터 만들어야 하나요?
A: 현재 상태에서는 다음 순서를 권장합니다:
1. 기존 코드 분석하여 문서 역작성
2. 문서와 코드 불일치 발견
3. 계획 수립 후 점진적 수정

### Q: specs/ 폴더는 왜 따로 만드나요?
A: 문서 종류를 구분하기 위해서입니다:
- `docs/` - 개발자 참조 문서
- `docs/specs/` - 기획 및 설계 문서 (변경 빈도 낮음)

---

*마지막 업데이트: 2026-02-03*
