# modoo 브랜치 UI 참조 색인

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-05-15 |
| 목적 | `modoo`(영상 시연용 mockup) 브랜치의 UI/UX 작업을 **코드 복사 없이** 참조하기 위한 색인 |
| 원칙 | `modoo` 브랜치 = 레퍼런스 그 자체 (git 영구 보관). 코드를 별도 폴더로 복사하지 않는다 — 빌드 깨짐 + 좀비코드 + 스냅샷 고착 |

---

## 0. 브랜치 안 바꾸고 modoo 파일 보는 법

```bash
git show modoo:frontend/src/features/agent/ChatTodoCard.tsx      # 파일 1개 열람
git diff main modoo -- frontend/src/features/workflow/           # 폴더 단위 diff
git log modoo --oneline                                          # modoo 커밋 목록
```

---

## 1. UI 작업 카탈로그

`modoo` 는 `a5c4fc3`(Warm Neutral) 에서 분기 → **디자인 시스템·9개 페이지 기본 스타일은 main 과 동일**.
아래는 `a5c4fc3` 이후 modoo 가 추가한 UI/UX 작업.

| UI 작업 | 파일 (modoo) | 커밋 | 성격 / 재사용성 |
|---------|-------------|------|----------------|
| **Todo 인터페이스** — 채팅창 내 todo 카드, 상위/하위 2단 구조, 단계별 완료 애니메이션 | `features/agent/ChatTodoCard.tsx` | `b5ea365` | 데모 전용 (demoStore 의존). 실 WS 연결 시 **재구현** — 디자인·레이아웃만 참고 |
| **채팅 패널 UX** — todo 카드 + 일시정지 배너 + 중지 버튼 + thinking 인디케이터 | `features/agent/SideChatPanel.tsx` | `22133be` | 데모 전용. UX 흐름(질문→thinking→todo→답변) 참고 |
| **노드 수정 인터페이스** — 노드 내 하위단계 표시, 제목 더블클릭 인라인 rename, 이름 변경 시 하위계획 자동생성 | `features/workflow/NodeComponent.tsx` | `9dc07fa` | 디자인 참고. rename/자동생성 로직은 데모용 |
| **워크플로우 편집 캔버스** — 노드 드래그/연결/추가/삭제 툴바, "변경 적용" | `features/workflow/WorkflowCanvas.tsx` | `5113947` | 실제 W2(시각 편집) groundwork — useNodesState 패턴 일부 재사용 가능 |
| **노드 가변 높이** — 하위단계 수에 따라 노드 높이 자동 계산 | `lib/dagre.ts` | `ee8578c` | ✅ 재사용 가능 (순수 레이아웃 로직) |
| **리포트 8섹션 종합** — 핵심요약/기간추이/채널/캠페인/소재/퍼널/키워드/AI인사이트 | `features/report/ReportPage.tsx` | `8f9e228` | ✅ **cherry-pick 가능** — 실 `/api/mock` 훅 사용, demoStore 무관 |
| **송신 아이콘** — Send(종이비행기) → CornerDownLeft(↵) | `features/agent/SideChatPanel.tsx` | `83f6ae4` | ✅ cherry-pick 가능 |
| **전체 화면 구성 변화** — 사이드바 에이전트/메모리 탭 제거 등 | `features/navigation/store.ts` | `7868865` | 데모용 결정 — 참고만 |

---

## 2. main 으로 가져갈 수 있는 것 (cherry-pick 후보 3개)

데모와 무관하게 진짜 개선/수정인 커밋:

```bash
git cherry-pick a89c5ed   # fix: ab-tests 스키마 버그 (소재분석 데이터 로드 실패) — 실제 버그
git cherry-pick 8f9e228   # feat: ReportPage 8섹션 종합 리포트 — 실 훅 사용, 그대로 동작
git cherry-pick 83f6ae4   # style: 송신 아이콘 Send → CornerDownLeft
```

→ 나머지는 전부 데모 전용(demoStore 의존)이라 cherry-pick 불가 — **디자인·UX 흐름만 참고**해서 실 WS 기반으로 재구현.

**타이밍**: 이 cherry-pick 은 통합 작업(Phase 0~5) + agent_specs 문서 검증 **이후**. 지금은 색인만.

---

## 3. 참고할 UX 흐름 (재구현 시 모방 대상)

modoo 데모가 검증한 UX 시나리오 — 실 WS 기반으로 만들 때 이 흐름을 모방:

1. **질문 → todo 표시 → 단계별 완료 → 답변** — 채팅창 안에서 작업 단계가 보이고 하나씩 체크되는 흐름
2. **todo → "워크플로우로 보기"** — 채팅의 todo 카드에서 워크플로우 캔버스로 전환
3. **실행 중 일시정지 → 수정 → 계속** (HITL) — 진행 중 멈추고 워크플로우에서 계획 편집 후 재개
4. **워크플로우 노드 편집** — 드래그/연결/추가/삭제, 노드 이름 변경

→ 실 구현 시: 1·3 은 `spec 21` 의 `node_event`/`hitl_request`/`paused`/`resumed` 로, 4 는 W2 시각편집으로.

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-05-15 | 초안 — modoo UI 작업 색인. 코드 복사 대신 브랜치 + 색인 문서로 참조 |
