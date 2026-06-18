# `docs/walkthroughs/` — 코드 동작 설명 문서 모음

| 항목 | 내용 |
|------|------|
| 생성일 | 2026-04-24 |
| 용도 | **Annotated Walkthrough** — 실행 흐름을 따라가며 "어디서 / 어떤 신호가 / 어떤 함수가 / 어떤 분기에서 / 왜 / 기대 응답" 을 서사형으로 설명 |
| 대상 독자 | 프로젝트 의도·구현 대조를 원하는 사람 (코드 해석력 낮아도 읽을 수 있도록) |
| 업계 용어 | Diátaxis 프레임워크의 **Explanation** 유형. Narrative Runbook 또는 Walkthrough 라고도 함 |

---

## 다른 문서 유형과의 차이

| 폴더 | 유형 | 성격 | 독자 |
|------|------|------|------|
| `docs/agent_specs/` | **Reference** | 정식 API·구조 계약 — 건조·정확 | 계약 참조할 때 |
| `docs/reports/` | **Records** | 완료 보고서·테스트 로그·플레이북 | 결과 확인, 실행 가이드 |
| `docs/_claude/` | **Drafts** | 내부 계획서 (gitignored) | Claude 작업 중 |
| **`docs/walkthroughs/`** | **Explanation** | 서사형 설명 — 왜 이런가, 어떻게 움직이나 | 이해·리뷰 |

---

## 문서 목록

| # | 파일 | Sprint | 범위 |
|---|------|--------|------|
| 1 | [sprint14_a3_walkthrough.md](./sprint14_a3_walkthrough.md) | 14 A3 | 서버 기동 → Plan review 편집 → Execution pause → Turn 종료. 10단계 + 에러 경로 |

---

## 새 walkthrough 추가 가이드

Sprint 15+ 에서 기능 추가 시:

1. 파일명: `sprint<N>_<feature>_walkthrough.md` (예: `sprint15_memory_walkthrough.md`)
2. 구조: **L1 (한 줄) / L2 (중급) / L3 (상세 + 분기)** 3단계
3. 각 단계마다: **시스템 측** (코드·함수·상태) + **사용자 측** (UI·가능 액션) 분리
4. 마지막에 **검증 로그 섹션** (Self-consistency / Code cross-check / Coverage / Intent alignment)
5. 이 README 의 표에 행 추가

---

## 유지 원칙

- **진실 소스는 코드**. Walkthrough 가 코드와 어긋나면 코드 기준으로 문서 수정
- **drift 발견 시 기록**: "이 walkthrough 를 쓰다 발견한 drift" 는 별도 섹션에 남겨 이후 개선 근거로
- **버전**: 큰 변경 시 `_v1.1` suffix 또는 변경 이력 섹션 업데이트
