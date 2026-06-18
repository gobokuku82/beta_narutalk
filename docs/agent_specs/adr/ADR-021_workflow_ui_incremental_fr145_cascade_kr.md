# ADR-021: Workflow UI 점진 진입 정책 + FR-145 cascade 한글화

## Status

**Proposed** (2026-05-17) — Stage 0. Stage 3 통과 시 Accepted.

## Context

### 본 ADR 의 두 영역

본 ADR 은 *두 결정 묶음*:

1. **점진 진입 정책** (메타) — 향후 워크플로우 UI 변경의 작업 패턴.
2. **FR-145 cascade 한글화** (구체) — 점진 진입 정책의 *첫 적용 사례*.

### 배경 — UX 재설계 큰 그림 검토 후 점진 전환

2026-05-17 본 세션 UX 재설계 작업 진행 중 다음 자료 누적:

- `workflow_structure_asis_2026-05-17.md` — as-is 박제
- `workflow_ux_redesign_plan_2026-05-17.md` — to-be 계획서 (페르소나 4종 / UI 약점 33 FR / 상태 매트릭스 / 여정 / IH / 디자인 원칙 / mockup / gap 분해)
- `workflow_user_requirements_2026-05-17.md` — 사용자 원문 5건 + Q-1~Q-8 결정 + 신규 FR 13건 + 용어집 35+

총 **46 FR 후보 + ADR-020 (NL 편집 todo_edit_layer 7 노드, 백엔드 큰 변경)** 도출.

**사용자 인식** (2026-05-17): *"문서를 만들면서 느낀건, 지금 상태에서 약간만 변경 후에 점진적으로 하나씩 수정해야 할것 같아."*

→ 큰 그림 한 번에 결정 = *과설계 위험 + 측정 없이 결정 위험*. POC 단계에 *점진* 전환 합리.

### 본 세션의 점진 정합성

본 세션 이전 작업 (ADR-011 / ADR-012 / ADR-013) 도 *모두 점진 패턴*:
- 8 Stage TDD + atomic commit + main 직접 작업
- 한 ADR = 한 영역 결정
- 매 Stage 4종 회귀 (typecheck / build / vitest / pytest)
- 사용자 E2E 검증 후 다음 ADR

→ 본 점진 진입 = *기존 패턴의 연속*. 새로운 정책이 아니라 *명시적 박제*.

### FR-145 = 점진 진입의 첫 적용

FR-145 = `workflow_ux_redesign_plan_2026-05-17.md` §3.1.3 의 33 FR 중 *가장 작고 안전*:
- 백엔드 영향 = 0
- 분량 = NodeComponent.tsx 1~2 줄
- 영향 페르소나 = P-A1 / P-A3 (영어 "cascade" 도메인 용어 불명)
- 디자인 원칙 = memory `feedback_no_ai_looking_ui.md` 정합 (한국어 일관)

→ *워밍업 적합*. 점진 진입의 패턴 익히기 용도.

### 사용자 결정 (2026-05-17)

- 첫 진입 FR = **FR-145** ("워밍업").
- 한글 단어 = **"재실행 필요"** (현 title 속성에 이미 쓰이는 표현, 결과 견지).

## Decision

### 1. 점진 진입 정책 (메타)

**원칙**: 워크플로우 UI 변경은 *작은 단위 FR 1개* = *작은 ADR 1개* = *압축된 4 Stage TDD* = *atomic commit* 으로 진행.

**한 사이클 패턴**:
```
Stage 0: ADR (작은, 한 FR + 결정 박제)
Stage 1: 코드 변경 + 회귀 4종 (typecheck / build / vitest / pytest)
Stage 2: spec / 문서 갱신 (영향 영역만)
Stage 3: atomic commit + 사용자 E2E 검증 → ADR Accepted
```

(ADR-011 / 012 / 013 의 8 Stage 패턴과 *구조 동일, 분량만 작음*. 변경 분량에 따라 Stage 5~8 까지 확장 가능.)

**FR 선택 기준** (우선순위):
1. 백엔드 영향 0
2. 단일 컴포넌트 변경
3. 영향 페르소나 명확
4. Must 또는 Should 우선순위

**ADR 번호 정책**:
- 본 정책의 ADR 누적 = **ADR-021 부터 연속** (ADR-014~020 = 큰 영역 예약 자리 침범 회피).
- 향후 ADR-022 / 023 / ... = 다음 FR 사이클.

**큰 ADR (ADR-020 todo_edit_layer 등) 진입 시점**:
- 작은 FR 들이 누적되어 *공통 패턴* 발견 시.
- 또는 *작은 FR 로 해결 불가* 한 본질 변경 필요 시.
- **POC 종료까지 진입 안 할 수도 있음** (불필요한 추상화 회피).

### 2. FR-145 cascade 한글화 (구체)

**변경 대상**: [frontend/src/features/workflow/canvas/NodeComponent.tsx:43-51](../../../frontend/src/features/workflow/canvas/NodeComponent.tsx#L43-L51)

**Before**:
```tsx
<span
  className="..."
  title="이전 편집의 cascade — 재실행 필요"
>
  <Link2Off className="h-3 w-3" />
  cascade
</span>
```

**After**:
```tsx
<span
  className="..."
  title="이전 편집의 영향 — 재실행 필요"
>
  <Link2Off className="h-3 w-3" />
  재실행 필요
</span>
```

**근거**:
- "cascade" = 도메인 사용자 (P-A1 마케터 / P-A3 PM) 의 *기술 용어 불명* (계획서 §3.1.3 S-09 Nielsen #2 위반).
- "재실행 필요" = 사용자 *액션 가이드* (Nielsen #9 — Help recover) 직관적.
- title 속성도 cascade 단어 제거 → "이전 편집의 영향 — 재실행 필요" 로 통일.

### 3. spec / 문서 갱신 영역 (Stage 2)

다음 4 문서의 *cascade 단어* 인용 부분 정합 갱신:

| 문서 | 변경 영역 |
|---|---|
| `spec 62 v1.2` §4.1 / §5.5 | 노드 시각 사양 표 / 컴포넌트 카탈로그의 cascade 배지 행 — *배지 텍스트* 만 갱신 ("재실행 필요"). 내부 용어 (cascade tint / cascade 결과) 는 *기술 용어* 라 유지. |
| `workflow_structure_asis_2026-05-17.md` §8.2 | 배지 표의 cascade 행 — "cascade" 텍스트 → "재실행 필요" |
| `workflow_user_guide_2026-05-17.md` §4 | 시각 피드백 표의 cascade 행 — *사용자 안내 문서* 라 텍스트 갱신 + 설명 정정 |
| `workflow_ux_redesign_plan_2026-05-17.md` §3.1.3 S-09 | FR-145 = "재실행 필요" 채택 박제 (정정 — 단어 확정) |

코드 주석의 "cascade" 단어 = *기술 용어로 유지* (개발자 시선). UI 텍스트만 한글.

## Consequences

### Positive

1. **점진 패턴 명시 박제** — 향후 ADR-022 / 023 / ... 진입 시 본 ADR 의 패턴 인용 가능.
2. **FR-145 = 작은 가치 즉시 실현** — 도메인 사용자 인지 부하 즉시 감소.
3. **큰 ADR-020 부담 해소** — 작은 FR 들로 누적 → 공통 패턴 발견 후 결정.
4. **본 세션의 ADR-011/012/013 패턴과 일관** — 작업 흐름 인지 부하 0.

### Negative

1. **ADR 수 증가** — 작은 ADR 누적. *(완화: atomic 관리, INDEX 갱신 정책 명시)*
2. **공통 패턴 발견 지연 위험** — 점진 진행 중 큰 영역 결정 늦어질 수 있음. *(완화: 매 사이클 후 점검, 누적 3~5건 시 공통 패턴 검토)*
3. **cascade 용어 = 사용자 vs 개발자 분리** — UI 한글 / 코드 영어 = 매핑 부담. *(완화: spec 62 / as-is 의 용어집에 매핑 명시)*

### Risk Mitigation

- 매 Stage 4종 회귀 (typecheck / build / vitest / pytest) — 기존 패턴 유지.
- atomic commit — 각 사이클 독립.
- 사용자 E2E 검증 게이트 — Stage 3 통과 조건.

## Alternatives Considered

### Alt A: ADR-020 (todo_edit_layer + 46 FR) 한 번에 결정

- 큰 그림 한 번에 결정. *과설계 위험 + 측정 없이 결정 위험*.
- *기각* — 사용자 명시 결정 ("점진적으로 하나씩").

### Alt B: ADR 없이 직접 commit (워밍업)

- 1~2 줄 변경에 ADR 무거움.
- 단 *결정 박제 X* — 향후 "왜 한글화했나" 추적 불가.
- *기각* — 본 세션의 ADR 패턴과 일관 유지.

### Alt C: ADR-021 = FR-145 만 (점진 정책 별도 ADR)

- 점진 진입 정책 = ADR-021 / FR-145 = ADR-022. 분리.
- *기각* — 점진 정책은 *적용 사례 1건과 함께* 박제하는 게 더 구체적. 다음 사이클부터 정책 인용.

## Verification Plan (Stage 별)

| Stage | 내용 |
|-------|------|
| 0 | 본 ADR 작성 (이 문서) |
| 1 | NodeComponent.tsx 변경 (배지 텍스트 + title) + 회귀 4종 (typecheck / build / vitest / pytest) 통과 |
| 2 | 4 문서 갱신 (spec 62 §4.1/§5.5 / as-is §8.2 / user_guide §4 / ux_redesign_plan §3.1.3 S-09) |
| 3 | atomic commit + 사용자 브라우저 E2E 확인 (워크플로우 → 노드 삭제 → 회색 배지 "재실행 필요" 표시 확인) → 본 ADR Status: Proposed → Accepted |

## 관련 명세 / 결정

- `workflow_ux_redesign_plan_2026-05-17.md` §3.1.3 S-09 (cascade 진단 + FR-145 도출)
- `workflow_structure_asis_2026-05-17.md` §8.2 (현 배지 시각 토큰 박제)
- `workflow_user_requirements_2026-05-17.md` §7 용어집 (cascade 정의)
- ADR-012 (W2 cascade tint 도입) / ADR-013 (W2′ batched 시각화)
- memory `feedback_no_ai_looking_ui.md` (디자인 원칙 — 한국어 일관 정합)

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-05-17 | 초안 (Stage 0) — Proposed. 점진 진입 정책 (메타) + FR-145 cascade 한글화 (구체). 4 Stage 압축 패턴 적용. |
