# ADR-000: Architecture Decision Record (ADR) 도입

## Status

Accepted (2026-04-27)

## Context

Sprint 14 A3 Phase 5 진행 중 다음과 같은 **결정 누락** 패턴이 반복적으로 발생함:

- Sprint 12 → Sprint 13 전환 시 `_run_agent` legacy 경로 처리 정책 미결정 → 350줄 dead code 잔류
- Plan review 편집 가능성 결정 미진 → Y-a 결정 후에도 ws_hitl 분기 dead code 발생
- AgentPool eager vs lazy 정책 미명시 → memory 와 코드 불일치 (drift)

이런 **임시 결정 → 발견 → drift 정정 사이클** 의 비용을 줄이려면 결정 자체를 영속 기록할 장치가 필요함. 또한 비전문가 사용자가 "왜 이렇게 결정했는지" 추후 재검토할 수 있어야 함.

`agent_specs/INDEX.md` 에는 이미 "관련 ADR 있으면 `adr/` 에 작성 *(Sprint 14 도입 예정)*" 로 적혀 있었으나 실제 폴더는 미생성 상태였음.

## Decision

`docs/agent_specs/adr/` 폴더를 도입하고 **Michael Nygard ADR 표준 형식** 을 사용한다.

### 폴더 구조
```
docs/agent_specs/adr/
├── INDEX.md                     # 검색·상태 일괄 표
├── ADR-000_adr_process.md       # 본 문서
├── ADR-001_<topic>.md
├── ADR-002_<topic>.md
└── ...
```

### 파일명 규칙
- `ADR-<3자리 번호>_<snake_case 주제>.md`
- 번호는 시간순 단조 증가, 재사용 안 함 (deprecated 후에도 번호 유지)

### 각 ADR 표준 형식

```markdown
# ADR-NNN: 제목

## Status
Proposed | Accepted (날짜) | Superseded by ADR-MMM | Deprecated

## Context
배경 — 무엇 때문에 결정 필요했나, 어떤 제약/관찰이 있었나

## Decision
결정 사항 — 무엇을 하기로 했나 (능동태)

## Consequences
결과 — 좋은 점 / 나쁜 점 / 위험 / trade-off

## Alternatives Considered
검토했던 다른 옵션과 그것을 선택하지 않은 이유

## Related
관련 ADR / 코드 / 문서 / 커밋 SHA
```

### 작성 트리거 (언제 ADR 쓸 것인가)

다음 중 하나 이상 해당 시 **반드시** ADR 작성:

1. **방향성 결정** — 두 가지 이상 옵션 중 한쪽 선택 (예: hitl/pause 통합 vs 분리)
2. **계약 변경** — API/메시지/스키마/저장소 구조 변경
3. **장기 의존** — 라이브러리/프레임워크/DB 등 큰 의존 채택
4. **policy 결정** — eager vs lazy, sync vs async, single vs multi-tenant 등 시스템 전반 정책
5. **trade-off** — "A를 위해 B를 포기" 형태 결정

다음은 ADR 불필요:
- 변수명, 라인 정렬 같은 코드 스타일
- 구현 디테일 (어떤 자료구조 쓸지 등)
- 일회성 버그 수정

### 상태 관리

| Status | 의미 |
|--------|------|
| `Proposed` | 논의 중. 코드 변경 전 |
| `Accepted` | 결정 완료, 적용됨. 본 ADR 들의 default |
| `Superseded by ADR-MMM` | 다른 결정으로 대체됨. 본문은 그대로 두고 Status 만 변경 |
| `Deprecated` | 더 이상 유효하지 않음. 대체 없이 폐기 |

**중요**: ADR 은 **결정 시점의 사실** 을 기록. 나중에 결정이 바뀌어도 옛 ADR 본문은 절대 수정하지 않고 새 ADR 추가 + 기존 Status 변경.

### INDEX.md

`docs/agent_specs/adr/INDEX.md` 에 모든 ADR 의 표 형태 목록 유지. 컬럼: 번호, 제목, 상태, 작성일, 영향 범위, 관련 ADR.

상위 `docs/agent_specs/INDEX.md` 의 "사용/관리 규칙" 섹션에서 ADR 폴더로 링크 추가.

## Consequences

### 좋은 점

- **결정 누락 가시화**: ADR 작성을 강제하면 "결정해야 하는데 안 했다" 가 줄어듦
- **추후 재검토 가능**: "왜 이렇게 했더라?" 의 답이 항상 같은 위치에 있음
- **비전문가 친화적**: 코드를 읽지 않고도 ADR 만 읽으면 시스템 의도 파악 가능
- **Drift 방지**: 결정 박제 → memory/문서/코드 불일치 발견 시 ADR 기준으로 정정

### 나쁜 점 / 비용

- **작성 시간**: 큰 결정마다 20~30분 추가 비용
- **유지 부담**: 결정 변경 시 새 ADR 작성 + 기존 상태 갱신 필요 (잊으면 outdated)
- **POC 단계 부적합 위험**: 너무 많이 쓰면 발견 사이클 둔화. "ADR 작성 트리거" 를 명확히 해 과잉 생성 방지

### 위험

- ADR 이 **현 상태와 어긋남**: superseded 표시 안 한 outdated ADR 이 있으면 misleading. INDEX 갱신 필수
- **ADR 만 보고 코드 안 봄**: 진실 소스는 코드. ADR 은 결정 근거이지 명세가 아님

## Alternatives Considered

### Alt-1. Decision Log (1줄 결정 기록)

`docs/decisions.md` 에 시간순 한 줄씩.

- 장점: 가벼움, 작성 부담 적음
- 단점: 맥락 부족. "왜 그랬더라?" 답 안 됨
- 결론: 보조 도구로 가능. ADR 의 대체로는 불충분 — 채택 X

### Alt-2. RFC (Request for Comments)

각 결정 전에 RFC 작성 → 팀 리뷰 → 승인 → 코드.

- 장점: 사전 검토 강력
- 단점: 1~2주 사이클. POC 속도 저해
- 결론: POC 단계엔 과함. MVP 이후 검토 — 채택 X

### Alt-3. ADR 미도입 (현 상태 유지)

- 장점: 작성 부담 없음
- 단점: 결정 누락 반복. 본 Sprint 14 A3 에서 이미 비용 지불됨
- 결론: 채택 X

## Related

- 상위 인덱스: [`docs/agent_specs/INDEX.md`](../INDEX.md)
- 본 ADR 도입 트리거 사례: [`docs/_claude/sprint14_a3_implementation_plan.md`](../../_claude/sprint14_a3_implementation_plan.md), [`docs/_claude/sprint14_a3_missed_points.md`](../../_claude/sprint14_a3_missed_points.md)
- Walkthrough: [`docs/walkthroughs/sprint14_a3_walkthrough.md`](../../walkthroughs/sprint14_a3_walkthrough.md)

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-04-27 | 초안 + Accepted (사용자 결정) |
