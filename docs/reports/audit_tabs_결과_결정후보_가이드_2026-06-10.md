# Phase 7 audit:tabs 결과 + 결정 후보 가이드 (2026-06-10)

> 직전 commit `55f9e0c` 의 audit:tabs 적용 결과 + 페이지 재구성 결과보고서 §7 의 5 결정 후보 (a)·(b)·(c)·(d)·(f) 각각 자세 설명.
> 본 문서를 보고 사용자가 어디부터 진행할지 결정.

## Part 1 — audit:tabs 결과

### 1.1 산출물

| 산출물 | 위치 |
|---|---|
| 검증 스크립트 | `frontend/scripts/audit-tabs.sh` |
| package.json | `audit:tabs` + `audit:all` (tokens + tabs 통합) |
| spec 갱신 | `spec_64 §4.2` |

### 1.2 검증 3 카테고리

| # | 검사 | 동작 | 실패 시 |
|---|---|---|---|
| **[1]** | store TABS path → router 등록 | 사이드바 path 가 router 에 createRoute 로 등록됐는가 | FAIL — 사이드바 클릭 시 404 |
| **[2]** | router path → sidebar/settings/index 표시 | router 등록됐는데 어디서도 navigate 안 되는 orphan 라우트 | WARN — 의도된 hidden 라우트라면 OK |
| **[3]** | ICON_MAP 키 → store TABS 사용 | Sidebar import 했는데 사용 안 하는 잔존 아이콘 | WARN — 다른 컴포넌트 사용 가능 |

### 1.3 현 상태 검증

```
[1] OK — 14 tab path 모두 router 등록 (404 0건)
[2] OK — 모든 router path 가 sidebar/settings/index
[3] WARN — MessageSquare (TopBar AI 버튼) · Settings (Sidebar footer)
         = expected (store TABS 외 사용, false positive 없음)
```

→ 정합 완전. 다음 페이지 추가/삭제 시 `pnpm audit:all` 한 번에 자동 검증.

### 1.4 명령어 충돌 회피

| 명령 | 동작 |
|---|---|
| `pnpm audit` | pnpm **내장 보안 취약점 검사** (npm 의 audit 와 동일) |
| `pnpm audit:tokens` | 디자인 토큰 정합 (TYPOGRAPHY·SPACING·RADIUS·ELEVATION) |
| `pnpm audit:tabs` | Sidebar/Router 정합 (신설) |
| `pnpm audit:all` | tokens + tabs 통합 — **사용 권장** |

`pnpm audit` 와 충돌 회피 위해 우리 통합 명령은 `audit:all`.

---

## Part 2 — 결정 후보 5 가지 (페이지 재구성 결과보고서 §7)

### (a) Sidebar default = expanded?

| 측면 | 내용 |
|---|---|
| **현재** | collapsed (w-20, 아이콘만 + 작은 라벨 `text-2xs`) |
| **변경 후** | expanded (w-56, 아이콘 + 풀라벨 `text-sm`) |
| **의도** | 처음 진입 시 사이드바 라벨이 한눈에 보임. 사용자 학습성 ↑ |
| **장점** | 새 사용자가 메뉴 구조 빠르게 파악. SYSTEM 6 + CLIENT 8 라벨 보임 |
| **단점** | 메인 콘텐츠 영역이 좁아짐 (36px 차이). 패널 width 절약 X |
| **변경 영향** | `navigation/store.ts` 의 `isSidebarExpanded: false` → `true` (1 줄) |
| **위험** | 0. 사용자가 toggle 버튼으로 언제든 변경 가능. localStorage 저장됨 |
| **작업량** | 1 분 |
| **추천** | ★★ — UX 가치 있음 단 사용자 선호 |

### (b) group label 변경?

| 측면 | 내용 |
|---|---|
| **현재** | SYSTEM_TABS 그룹 = "리포트" / "관찰" / "시스템" / (default) |
| **현재** | CLIENT_TABS 그룹 = "분석" / "AI" |
| **변경 옵션** | "관찰" → "활동" / "모니터링" / "Activity" / "Observability" 등 |
| **변경 옵션** | "리포트" → "보고서" / "Report" |
| **변경 옵션** | "시스템" → "관리" / "Admin" |
| **의도** | 그룹 라벨이 더 명확하거나 일관된 톤 |
| **변경 영향** | `store.ts` 의 group 필드 (몇 줄) |
| **위험** | 0 |
| **작업량** | 5 분 |
| **추천** | ★ — 현 라벨도 명확. 강한 선호 없으면 유지 |

### (c) `/agent-observability` 짧은 라벨?

| 측면 | 내용 |
|---|---|
| **현재** | 탭 label = "에이전트 관찰" (5 자, group "관찰" 안) |
| **변경 옵션** | "관찰" (2 자, group 명과 중복) · "에이전트" (3 자) · "Agent Obs" (영문) |
| **의도** | 1) group "관찰" 안에 있으니 탭 label 중복 회피 / 2) 더 간결 |
| **변경 영향** | `store.ts` 의 SYSTEM_TABS 의 한 줄 — `label` 만 |
| **위험** | 0 |
| **작업량** | 1 분 |
| **추천 옵션** | "에이전트" — 짧으면서 group "관찰" 과 안 겹침 |
| **추천** | ★★ — 작은 가치 |

### (d) type `'portfolio'` → `'system'` rename?

| 측면 | 내용 |
|---|---|
| **현재** | `NavigationContext = 'portfolio' \| 'client'`. UI label 만 "시스템" |
| **현재 문제** | 코드 타입과 UI 라벨 의미 drift — 'portfolio' 가 코드 곳곳에 있는데 UI 는 "시스템" |
| **변경 후** | `NavigationContext = 'system' \| 'client'`. 의미 정합 |
| **의도** | 코드와 UI 의미 일치 (drift 제거). 미래 개발자 헷갈림 ↓ |
| **변경 영향** | NavigationContext type · store.ts (10 줄) · TopBar (3 줄) · localStorage migration |
| **localStorage migration** | 기존 사용자의 저장된 `'portfolio'` 값을 `'system'` 으로 변환하는 helper. 안 하면 localStorage 깨짐 → 사용자 첫 방문 상태로 리셋 |
| **위험** | 중 — migration 실패 시 사용자 세션 초기화 |
| **작업량** | 30~40 분 |
| **추천** | ★ — 의미 정합 가치 있으나 POC 단계 over-engineering 가능. MVP 후 권장 |

### (f) 다음 작업 영역 — 큰 결정

| 후보 | 의미 | 작업량 |
|---|---|---|
| **f1. 빈 페이지 완성** | Settings·Workflow·AgentObservability·Memory·Conversations 등 placeholder 상태 페이지 실제 콘텐츠 채우기 | 페이지당 2~5 시간 |
| **f2. 데이터/백엔드** | clumi data pipeline 완성. 분석 5 페이지 (dashboard·channel·trend·creatives·cost) PILOT mock → 실데이터 배선 | 큰 작업, 1~2 주 |
| **f3. 데이터 시각화 다듬기** | ChartFrame·DataTable·MetricChainStrip 등 viz/* 컴포넌트의 visual 추가 다듬기 | 1~2 시간 |
| **f4. AI 채팅 패널 UX** | SideChatPanel 의 메시지 흐름 / 작업 단계 표시 / Slide 보기 등 사용성 개선 | 2~5 시간 |
| **f5. 테스트** | 누락된 단위/E2E 테스트 추가. 회귀 방지 | 4~8 시간 |
| **f6. 다크 모드 도입** | 라이트 만 박제됨. 다크 토큰은 PALETTE.md 의 invert 룰로 derive 완료 → 실제 토글 UI 추가 | 1~2 시간 |
| **f7. 채널 색 정리** | 채널 색 (kakao·naver·meta·google) 다크 오버라이드 추가 + 격차 좁힘 | 30 분 |

---

## Part 3 — 권장 조합

### 빠른 마무리 (소작업 묶음) — 30 분

(a) **Sidebar default = expanded** (1 분) + (c) **에이전트 관찰 → "에이전트"** (1 분) + (f7) **채널 색 다크 오버라이드** (30 분).

→ 작은 가치 누적 + 다크 모드 준비.

### 중간 마무리 — 1~2 시간

빠른 마무리 + (f3) **viz/* 다듬기** + (f6) **다크 모드 토글 UI**.

→ 디자인 시스템 완전 마무리. 이후 본격 데이터 작업.

### 큰 다음 단계 — 1~2 주

(f2) **데이터/백엔드 — clumi pipeline + 분석 5 페이지 실데이터 배선**.

→ POC 의 본질 (raw → 분석 변환 파이프라인) 완성.

---

## Part 4 — 자취

- **2026-06-09 (12 commit)** : 외부영역 정합 + ◈ OctorAD · 브랜드 (`075ede6`)
- **2026-06-09 (13 commit)** : 페이지 재구성 (`9a12c7a` + `c6c1bd9`)
- **2026-06-09 (14 commit)** : audit:tabs 신설 (`55f9e0c`)
- **2026-06-10 (본 문서)** : 결정 가이드 박제 — 사용자 결정 후 진행
