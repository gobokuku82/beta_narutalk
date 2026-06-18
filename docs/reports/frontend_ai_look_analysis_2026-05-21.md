# 프론트엔드 "AI틱한 느낌" 분석 — 원인과 수정 방향

| 항목 | 내용 |
|------|------|
| 작성일 | 2026-05-21 |
| 분석 대상 | [`frontend/`](../../frontend/) — React + Vite + Tailwind + shadcn/ui (Sprint 15+) |
| 분석 목적 | 사용자 피드백 **"프론트엔드가 AI틱한 느낌이 든다"** 의 구체적 원인 규명 + 수정 위치/방법 제시 |
| 분석 범위 | 11개 feature 페이지 + 공통 레이아웃(GlobalLayout/TopBar/Sidebar) + 공통 컴포넌트(KpiCard/PageHeader/Card) + 디자인 토큰(globals.css/tailwind.config) |
| 결론 (요약) | 디자인 토큰(컬러·타이포)은 양호 — 손대지 말 것. "AI틱"의 실제 원인은 **① 모든 페이지의 동일 템플릿 ② 제품 UI에 남은 개발 스캐폴딩 ③ 아이콘 칩 남용 ④ 다중 세션 생성으로 인한 불일치**. Tier 1(즉효·저비용)부터 단계 적용 권고 |
| 검증 상태 | §6 검증 로그 — 정적 검증(grep/Read) → 문서수정 → 재검증 → **화면 검증(앱 실행·스크린샷 8종, 2026-05-22)** 완료. 화면 검증에서 스캐폴딩 누수 4건 추가 발견 → §2.2 반영 |

---

## 0. 분석 기준 — "AI틱"이란 무엇인가

"AI틱한 느낌" = 사람이 설계한 제품이 아니라 LLM이 스캐폴딩한 데모처럼 보이는 시각적·구조적 신호. 본 분석은 다음 신호를 기준으로 frontend 코드를 전수 점검했다.

| 신호 | 설명 |
|------|------|
| 구조 단조성 | 모든 화면이 같은 틀에서 찍혀 나옴 |
| 스캐폴딩 누수 | 개발 과정 흔적(스프린트 번호, API 경로, 디버그 문구)이 제품 화면에 노출 |
| 기본값 방치 | 프레임워크(shadcn) 기본값을 그대로 사용 — 튜닝 흔적 없음 |
| 장식 의무 채우기 | 의미 없는 아이콘·설명 슬롯을 빈칸 없이 채움 |
| 부분 불일치 | 여러 세션이 합의 없이 생성 → 같은 요소가 다르게 구현됨 |

**점검 결과 요지**: 본 프로젝트는 **컬러·디자인 토큰이 이미 한 번 정리되어 있다**([globals.css](../../frontend/src/styles/globals.css) 의 "2026 Warm Neutral" 주석 §5–11). 따라서 색은 원인이 아니다. 원인은 **구조 단조성·스캐폴딩 누수·기본값 방치·부분 불일치**에 집중되어 있다.

---

## 1. 핵심 결론 — 색이 아니라 구조와 스캐폴딩

> **화면 노출** 열 = 사용자가 실제 화면에서 보게 되는 문제인지. **이번 작업 범위는 화면 ✅ 항목**이다 (8 번과 7d 는 코드 레벨 — 화면 무관, 별도 처리).

| # | 원인 | 화면 노출 | "AI틱" 기여 | 수정 비용 | Tier |
|---|------|:--------:|:----------:|:--------:|:----:|
| 1 | 페이지가 동일 템플릿으로 양산 | ✅ | 상 | 고 | 3 |
| 2 | 개발 스캐폴딩이 제품 UI에 노출 | ✅ | 상 | 저 | 1 |
| 3 | 아이콘 칩(rounded square) 남용 | ✅ | 중 | 중 | 2 |
| 4 | CardDescription 의무 채우기 | ✅ | 중 | 저 | 2 |
| 5 | shadcn 기본값 미조정 (CardTitle 24px) | ✅ | 중 | 저 | 2 |
| 6 | 균일한 밀도 — 시각적 위계 부재 | ✅ | 중 | 중 | 3 |
| 7 | 다중 세션 생성 흔적 (불일치) | ✅ (7d 제외) | 중 | 저 | 1–2 |
| 8 | 장황한 코드 주석 | ❌ 코드 | 하 | 중 | 4 |

### 1.1 이미 잘 된 것 — 건드리지 말 것

- [globals.css](../../frontend/src/styles/globals.css) 디자인 토큰: 따뜻한 뉴트럴 베이스 + 단일 마호가니 액센트, 그라데이션·glow 없음. 의도가 명확하고 일관됨.
- HSL CSS 변수 → Tailwind 토큰 매핑 구조, 라이트/다크 토큰 분리. 표준적이고 확장 가능.
- **→ 색·토큰 시스템은 그대로 둔다. 여기를 손대면 오히려 회귀한다.**

---

## 2. 원인별 상세 분석

### 2.1 원인 1 — 11개 페이지가 동일 템플릿으로 양산 (Tier 3)

**증상**: 11개 feature 페이지 전부가 아래 외곽 골격을 공유하고, 데이터 페이지는 그 위에 동일한 추가 블록을 얹는다.

```
<div className="space-y-6 p-6">                     ← 11개 페이지 전부
  <PageHeader title= description= badge= icon= />   ← 11개 전부
  <Card> ... </Card>  <Card> ... </Card>  ...       ← Card 세로 스택, 11개 전부
</div>
```

**위치**: 공통 블록의 적용 범위 (grep 으로 전수 확인).

| 공통 블록 | 적용 | 페이지 |
|----------|:----:|--------|
| `space-y-6 p-6` 래퍼 + `PageHeader`(badge) + `Card` 세로 스택 | 11 | 전체 |
| KPI 4칸 그리드 (`KpiCard` ×4) | 5 | 대시보드 / 포트폴리오 / 트렌드 / 소재 / 비용 |
| `데이터: /api/mock/...` footer | 7 | 위 5 + 채널분석 + 리포트 |
| 개발자용 에러 카드 (원인 2c 참조) | 7 | footer 와 동일 7개 |

→ "헤더 → KPI 4칸 → 차트 카드 → 출처 footer" 풀 템플릿은 5개 데이터 페이지에 거의 동일하게 반복되고, 나머지 페이지도 외곽 골격(래퍼 + 헤더 + 카드 스택)을 그대로 공유한다. 채널분석·리포트는 데이터 페이지지만 `KpiCard` 를 쓰지 않아, "데이터 페이지 = KPI 4칸" 도 아닌 어중간한 부분 일관성이다.

**페이지 파일 색인**:

| 페이지 | 파일 |
|--------|------|
| 대시보드 | [DashboardPage.tsx](../../frontend/src/features/dashboard/DashboardPage.tsx) |
| 포트폴리오 | [PortfolioPage.tsx](../../frontend/src/features/portfolio/PortfolioPage.tsx) |
| 채널분석 | [ChannelAnalysisPage.tsx](../../frontend/src/features/channel/ChannelAnalysisPage.tsx) |
| 트렌드분석 | [TrendAnalysisPage.tsx](../../frontend/src/features/trend/TrendAnalysisPage.tsx) |
| 소재분석 | [CreativeAnalysisPage.tsx](../../frontend/src/features/creative/CreativeAnalysisPage.tsx) |
| 비용최적화 | [CostOptimizationPage.tsx](../../frontend/src/features/cost/CostOptimizationPage.tsx) |
| 리포트 | [ReportPage.tsx](../../frontend/src/features/report/ReportPage.tsx) |
| HITL 센터 | [HitlCenterPage.tsx](../../frontend/src/features/hitl/HitlCenterPage.tsx) |
| 메모리 | [MemoryPage.tsx](../../frontend/src/features/memory/MemoryPage.tsx) |
| 대화이력 | [ConversationsPage.tsx](../../frontend/src/features/conversations/ConversationsPage.tsx) |
| 설정 | [SettingsPage.tsx](../../frontend/src/features/settings/SettingsPage.tsx) |

**왜 AI틱한가**: LLM은 "대시보드 페이지"를 요청받으면 항상 같은 몰드(헤더 → KPI 4칸 → 카드 세로 스택)로 출력한다. 페이지의 실제 목적(요약 vs 비교 vs 탐색)에 따라 정보 구조가 달라지지 않는다. 사람이 설계한 제품은 페이지마다 레이아웃이 다르다.

**수정 방향**: 페이지를 목적별 레이아웃으로 분화.
- 요약형(포트폴리오/대시보드): 주력 시각화 1개를 크게 + 보조 지표는 작게.
- 비교형(채널분석): 좌우 split — 매체를 나란히 배치.
- 탐색형(트렌드): 시계열을 풀폭으로 + 상단 필터.
- 공통 래퍼 `space-y-6 p-6` 를 모든 페이지에 강제하지 말 것. 페이지별 grid 구성을 허용.
- **점진 적용**: 페이지 1개씩. 먼저 1개 페이지를 시범 재설계해 패턴을 확정한 뒤 확산.

---

### 2.2 원인 2 — 개발 스캐폴딩이 제품 UI에 노출 (Tier 1, 즉효)

가장 빠르고 효과가 큰 항목. 사용자가 보는 화면에 개발 과정의 흔적이 그대로 남아 있다.

#### 2a. 스프린트 번호 배지 — 11개 페이지

[PageHeader](../../frontend/src/components/layout/PageHeader.tsx) 의 `badge` 슬롯에 내부 스프린트 번호가 노출된다.

| 파일 | 라인 | 값 |
|------|:----:|----|
| HitlCenterPage.tsx | 28 | `badge="Sprint 3-1"` |
| PortfolioPage.tsx | 77 | `badge="실 데이터"` |
| ReportPage.tsx | 78 | `badge="Sprint 3"` |
| SettingsPage.tsx | 80 | `badge="Sprint 3"` |
| ChannelAnalysisPage.tsx | 87 | `badge="Sprint 2"` |
| DashboardPage.tsx | 89 | `badge="Sprint 2"` |
| ConversationsPage.tsx | 92 | `badge="Sprint 3"` |
| CreativeAnalysisPage.tsx | 101 | `badge="Sprint 3"` |
| TrendAnalysisPage.tsx | 143 | `badge="Sprint 3"` |
| MemoryPage.tsx | 154 | `badge="Sprint 3"` |
| CostOptimizationPage.tsx | 158 | `badge="Sprint 3"` |

**수정**: 11곳의 `badge=` 인자 전부 제거. "실 데이터"·"Sprint N" 모두 사용자에게 의미 없음. (배지가 정말 필요하면 "베타" 같은 사용자용 라벨만.)

#### 2b. 데이터 출처 / 샘플 안내 footer·문구 — 11곳

페이지 하단·카드 설명에 API 경로·"로컬 샘플"·"mock 데이터"·"Sprint N 연동 예정" 같은 개발 안내가 노출된다. **⑧–⑪ 4건은 화면 검증(§6.4)에서 추가 발견했다** — 1차 정적 grep 이 `데이터:`/`api/mock` 패턴만 검색해 누락한 것.

| # | 파일 | 라인 | 노출 문구 |
|---|------|:----:|----------|
| ① | PortfolioPage.tsx | 181 | `데이터: /api/mock/channel-performance + /api/mock/company` |
| ② | ChannelAnalysisPage.tsx | 214 | `데이터: /api/mock/...` |
| ③ | DashboardPage.tsx | 234 | `데이터: /api/mock/...` |
| ④ | ReportPage.tsx | 235 | `데이터: /api/mock/...` |
| ⑤ | CreativeAnalysisPage.tsx | 290 | `데이터: /api/mock/...` |
| ⑥ | TrendAnalysisPage.tsx | 350 | `데이터: /api/mock/...` |
| ⑦ | CostOptimizationPage.tsx | 355 | `데이터: /api/mock/...` |
| ⑧ | MemoryPage.tsx | 214–215 | `로컬 샘플 데이터 — 백엔드 memory_entries API 연동은 Sprint 5+` |
| ⑨ | ConversationsPage.tsx | 150–151 | `로컬 샘플 데이터 — 백엔드 conversations API 연동은 Sprint 4` |
| ⑩ | ReportPage.tsx | 229 | `본 리포트는 mock 데이터 기반으로 생성되었습니다 · OctorAD Dream Agent` |
| ⑪ | SettingsPage.tsx | 133 | `CardDescription` — `로그인 정보 (Sprint 6+ 연동 예정)` |

**수정**: ①–⑩ 의 footer `<p>` 블록 삭제. ⑪ 은 `CardDescription` 에서 "(Sprint 6+ 연동 예정)" 제거(또는 설명 전체 삭제). 어떤 데이터로 그렸는지·언제 연동되는지는 사용자에게 알릴 필요가 없다.

#### 2c. 개발자용 에러 메시지 — 7개 페이지 + 채팅 패널

데이터 로드 실패 시 `백엔드 서버 (localhost:8001) 가 실행 중인지 확인하세요.` 를 최종 사용자에게 표시한다. `localhost:8001` 은 개발자 정보다.

| 파일 | 라인 (제목 / 본문) |
|------|:----:|
| PortfolioPage.tsx | 32 / 34 |
| ReportPage.tsx | 63 / 65 |
| ChannelAnalysisPage.tsx | 69 / 71 |
| DashboardPage.tsx | 72 / 74 |
| CreativeAnalysisPage.tsx | 86 / 88 |
| TrendAnalysisPage.tsx | 128 / 130 |
| CostOptimizationPage.tsx | 143 / 145 |
| SideChatPanel.tsx | 171 (`백엔드 서버 (localhost:8001) 연결 대기 중...`) |

**수정**: 공통 에러 컴포넌트 1개를 만들어 7곳의 중복을 제거.
- 예: `<DataLoadError onRetry={refetch} />` → 문구 "데이터를 불러오지 못했어요. 잠시 후 다시 시도해 주세요." + 재시도 버튼.
- SideChatPanel 의 연결 대기 문구도 `localhost:8001` 제거 → "서버에 연결하는 중..." 수준으로.

---

### 2.3 원인 3 — 아이콘 칩(rounded square) 남용 (Tier 2)

**증상**: 제목·지표마다 `rounded-lg` 정사각형 배경에 아이콘을 넣는 패턴. shadcn/AI 생성물의 대표 시그니처.

| 위치 | 라인 | 코드 |
|------|:----:|------|
| [KpiCard.tsx](../../frontend/src/components/layout/KpiCard.tsx) | 82 | `<div className="flex h-9 w-9 ... rounded-lg bg-muted ...">` |
| [PageHeader.tsx](../../frontend/src/components/layout/PageHeader.tsx) | 23 | `<div className="flex h-10 w-10 ... rounded-lg bg-accent ...">` |

추가로 KPI 아이콘이 개념과 1:1로 과하게 매핑된다 — 예산=Wallet, ROAS=TrendingUp, 노출수=Eye, 클릭수=MousePointerClick. 모든 KPI가 아이콘을 의무적으로 갖는다.

**왜 AI틱한가**: "제목 옆 둥근 사각형 안에 아이콘"은 LLM이 카드/헤더를 그릴 때 거의 항상 붙이는 장식. 정보 가치가 없는데도 빈칸을 채우려 한다.

**수정 방향**:
- [KpiCard.tsx](../../frontend/src/components/layout/KpiCard.tsx): 아이콘 칩 제거. KPI는 숫자가 주인공 — 큰 숫자 + 라벨 + 델타만. (KpiCard.tsx:81–86 의 `Icon` 블록 삭제.)
- [PageHeader.tsx](../../frontend/src/components/layout/PageHeader.tsx): 칩 배경(`bg-accent`)을 제거하고 아이콘만 두거나, 페이지별로 아이콘 자체를 생략. 헤더 1곳 정도는 절제해서 남겨도 무방.

---

### 2.4 원인 4 — CardDescription 의무 채우기 (Tier 2)

**증상**: `CardTitle` 아래 `CardDescription` 슬롯을 거의 항상 채우는데, 내용이 제목의 반복이거나 개수(count) 패딩이다.

| 위치 | 제목 | 설명 (불필요) |
|------|------|--------------|
| DashboardPage.tsx | "캠페인 목록" | "N개 캠페인" |
| ChannelAnalysisPage.tsx | "매체별 노출 / 클릭 / 전환" | "4 채널 성과 비교" |
| TrendAnalysisPage.tsx | "일별 성과 추이" | "노출 / 클릭 / 전환 시계열 (N일)" |

**수정 방향**: 제목을 반복하거나 개수만 적는 `CardDescription` 은 제거. 정말 필요한 정보(집계 기간, 갱신 시각 등)가 있을 때만 사용하고, 그런 경우 제목 옆 작은 인라인 메타로 두는 편이 낫다.

---

### 2.5 원인 5 — shadcn 기본값 미조정: CardTitle 24px (Tier 2)

**증상**: [card.tsx:39](../../frontend/src/components/ui/card.tsx) 의 `CardTitle` 이 shadcn 기본값 `text-2xl font-semibold`(24px) 그대로다. 이 컴포넌트가 페이지 내 **섹션 제목**("캠페인 목록" 등)으로 쓰이는데, 페이지 H1([PageHeader](../../frontend/src/components/layout/PageHeader.tsx) 의 `text-xl`=20px)보다 오히려 크다. 섹션 제목이 페이지 제목보다 큰 역전 현상. 게다가 [HitlCenterPage.tsx:78](../../frontend/src/features/hitl/HitlCenterPage.tsx) 은 ad-hoc 으로 `className="text-base"` 를 덮어쓰는데 같은 파일의 다른 `CardTitle`(35·67행)은 기본값 24px — 기본값을 안 고치고 일부만 국소 패치해 **한 파일 안에서도 제목 크기가 불일치**한다.

**왜 AI틱한가**: 프레임워크 기본값을 한 번도 안 건드린 신호. 사람은 자기 페이지의 타이포 위계에 맞춰 컴포넌트를 조정한다.

**수정**: [card.tsx](../../frontend/src/components/ui/card.tsx) 의 `CardTitle` 을 `text-base font-semibold`(16px) 수준으로 낮춤. 한 곳 수정으로 전역 반영된다. (페이지 H1 20px > 섹션 제목 16px 위계 회복.)

---

### 2.6 원인 6 — 균일한 밀도, 시각적 위계 부재 (Tier 3)

**증상**: 모든 페이지가 `space-y-6 p-6`(동일 간격·여백), 모든 [Card](../../frontend/src/components/ui/card.tsx) 가 동일한 미세 그림자(card.tsx:12). 화면에서 "가장 중요한 것"과 "부수적인 것"이 똑같은 무게로 보인다. focal point 가 없다.

**수정 방향**: 페이지 내 위계를 만든다.
- 주력 카드 1개를 2-column span 으로 크게, 보조 카드는 작게.
- 모든 카드에 동일 그림자를 주지 말고, 주력만 살짝 강조하거나 보조는 보더만.
- 원인 1(레이아웃 분화)과 함께 진행하는 것이 자연스럽다.

---

### 2.7 원인 7 — 다중 세션 생성 흔적: 불일치 5종 (Tier 1–2)

같은 요소가 파일마다 다르게 구현되어 있다. 여러 세션이 합의 없이 코드를 생성한 전형적 신호.

| # | 불일치 | 위치 A | 위치 B | 수정 |
|---|--------|--------|--------|------|
| 7a | 연결상태 dot 색상 | [TopBar.tsx:70–75](../../frontend/src/components/layout/TopBar.tsx) — 시맨틱 토큰 `bg-success`/`bg-warning`/`bg-muted-foreground` | [SideChatPanel.tsx:97–99](../../frontend/src/features/agent/SideChatPanel.tsx) — 하드코딩 `bg-green-500`/`bg-yellow-500`/`bg-gray-400` | 시맨틱 토큰으로 통일. 공통 `<ConnectionDot/>` 추출 권장 |
| 7b | 연결상태 라벨 언어 | TopBar.tsx:79 — "연결됨"(한국어) | SideChatPanel.tsx:112 — "Connected"(영어) | 한국어로 통일 |
| 7c | 제품명 | index.html:7 "OctorAD Dream Agent" / TopBar.tsx:42 "OctorAD" | SideChatPanel.tsx:92 "OctorAD Agent" | 1개로 확정 후 전체 통일 |
| 7d ⚠️*화면무관* | KpiCard `accent` dead prop | [KpiCard.tsx:11–12, 31–32](../../frontend/src/components/layout/KpiCard.tsx) — "현재 렌더에 미사용" 주석 | 20곳(5개 페이지 ×4)의 `KpiCard` 호출부가 여전히 `accent="meta"` 등을 전달 | prop 제거 + 호출부 정리 (코드 정리 — 이번 화면 작업 범위 밖) |
| 7e | favicon 누락 | [index.html:5](../../frontend/index.html) — `/favicon.svg` 참조 | `public/` 에 favicon.svg 없음 (`.gitkeep` 만 존재) | favicon.svg 추가 또는 참조 제거 |

추가로 하드코딩 색상은 [ChatTodoCard.tsx:60,65](../../frontend/src/features/agent/ChatTodoCard.tsx) (`bg-yellow-500/15`, `bg-green-500/15`), [PauseBox.tsx:43](../../frontend/src/features/agent/PauseBox.tsx) (`border-yellow-500/40`), [SideChatPanel.tsx:126](../../frontend/src/features/agent/SideChatPanel.tsx) (`bg-green-500/10`) 에도 존재 → 모두 `warning`/`success` 시맨틱 토큰으로 정리.

---

### 2.8 원인 8 — 장황한 코드 주석 (Tier 4, 코드 레벨)

**증상**: 거의 모든 파일 상단에 JSDoc 헤더가 있고 `spec: 61 §2.3 / 66 §2.1`, `v1 GlobalLayout.tsx 의 Zustand 포팅` 같은 마이그레이션 서사가 들어 있다. 시각적 "AI틱"과 직접 관련은 약하지만, 코드를 읽는 사람에게는 LLM 산출물 느낌을 준다.

**수정 방향** (우선순위 낮음, 선택):
- `spec: NN §N` 참조는 추적에 쓰이면 유지 가능.
- "v1 ... 의 Zustand 포팅" 같은 마이그레이션 서사는 git 히스토리에 있으니 제거 가능.
- 당연한 동작을 설명하는 인라인 주석 정리.

---

## 3. 수정 우선순위 — 작업 순서

| Tier | 항목 | 예상 규모 | 효과 |
|:----:|------|----------|------|
| **1** | 2a 배지 제거(11곳) / 2b footer·안내문 삭제(11곳) / 2c 에러 문구 공통화 / 7c 제품명 통일 / 7e favicon | 반나절 | 즉시 체감, 위험 거의 없음 |
| **2** | 3 아이콘 칩 제거 / 4 CardDescription 정리 / 5 CardTitle 크기 / 7a·7b dot 통일 | 1–2일 | 컴포넌트 단위 수정, 체감 큼 |
| **3** | 1 페이지별 레이아웃 분화 / 6 시각적 위계 | 페이지별 점진 | 가장 근본적, 페이지당 작업 |
| **4** *(화면 무관)* | 8 코드 주석 정리 / 7d `accent` dead prop 정리 | 선택 | 코드 가독성 |

**권고 진입점**: Tier 1 을 먼저 일괄 적용(작은 변경, 위험 낮음, 체감 즉시) → Tier 2 → Tier 3 는 페이지 1개를 시범 재설계해 패턴 확정 후 확산.

---

## 4. 영향 범위 / 리스크

| 항목 | 영향 | 비고 |
|------|------|------|
| 백엔드 | 없음 | 전부 frontend 표현 레이어. API 계약 무변경 |
| 디자인 토큰 (globals.css) | 없음 (의도적) | §1.1 — 손대지 않음 |
| 라우팅 / 상태관리 | 없음 | 레이아웃·컴포넌트 스타일만 |
| 테스트 | 경미 | store 테스트는 무관. UI 스냅샷 있으면 갱신 필요 |
| Tier 1 리스크 | 낮음 | 삭제·문구 변경 위주 |
| Tier 3 리스크 | 중간 | 페이지 레이아웃 재설계 — 페이지별 점진으로 완화 |

---

## 5. 결론

"AI틱한 느낌"의 원인은 **색이 아니라 구조와 스캐폴딩**이다. 컬러 토큰은 이미 정리되어 있으므로 건드리지 않는다.

가장 빠른 개선은 **Tier 1 — 제품 UI에 남은 개발 흔적 제거**(스프린트 배지, API 경로 footer, `localhost:8001` 에러 문구, 제품명 불일치)이며, 반나절이면 위험 없이 적용 가능하다. 이어서 **Tier 2 — 아이콘 칩·기본값·불일치 정리**로 컴포넌트 단위 체감을 높이고, 가장 근본적인 **Tier 3 — 페이지별 레이아웃 분화**는 페이지 1개 시범 재설계 후 점진 확산한다.

---

## 6. 검증 로그

본 문서의 모든 인용 위치(파일·라인)를 코드와 대조 검증했다.

### 6.1 1차 검증 (작성 직후)

| 주장 | 검증 방법 | 결과 |
|------|----------|:----:|
| `space-y-6 p-6` 11개 페이지 | grep `space-y-6 p-6` (features/) | ✅ 11개 파일 일치 |
| `badge=` 11개 페이지 + 라인 | grep `badge=` | ✅ 11개, 라인 일치 |
| `localhost:8001` 에러 7개 + SideChatPanel | grep `데이터 로드 실패`/`localhost:8001` | ✅ 7페이지 + SideChatPanel:171 |
| `데이터:` footer 7개 페이지 | grep `데이터:` | ✅ 7개 일치 |
| 아이콘 칩 KpiCard:82 / PageHeader:23 | grep `rounded-lg bg-(muted\|accent)` | ✅ 일치 |
| 하드코딩 색상 위치 | grep `bg-(green\|yellow\|gray)-[0-9]` | ✅ SideChatPanel/ChatTodoCard/PauseBox 일치 |
| CardTitle `text-2xl` | Read card.tsx:39 | ✅ 일치 |
| favicon.svg 누락 | Read index.html:5 + `public/` 목록 | ✅ `.gitkeep` 만 존재 |
| 제품명 3종 | grep `OctorAD` | ✅ index.html / TopBar / SideChatPanel 상이 |

### 6.2 검증 중 발견 → 문서 수정

코드 대조 중 §2.1·§2.5 의 서술이 부정확함을 발견하여 정정했다.

| 발견 | 1차 문서 | 수정 후 |
|------|---------|--------|
| KPI 4칸 그리드 범위 | "모든 feature 페이지가 KPI×4 포함 동일 골격 반복" | grep `KpiCard` → 사용 페이지는 **5개뿐**(대시보드/포트폴리오/트렌드/소재/비용). 채널분석·리포트는 데이터 페이지지만 KpiCard 미사용. → 외곽 골격(11)·KPI 그리드(5)·footer(7) 를 분리한 표로 §2.1 정정 |
| CardTitle override | "기본값 text-2xl 그대로" | [HitlCenterPage.tsx:78](../../frontend/src/features/hitl/HitlCenterPage.tsx) 에 ad-hoc `text-base` override 존재 → "기본값 미조정 + 일부 국소 패치 → 파일 내 불일치" 로 §2.5 보강 |
| §2.2 라인 번호 | 일부 기억 의존 | grep 결과를 정본으로 badge·error·footer 라인 전수 대조 — 일치 |

### 6.3 재검증 — 추가 정정 2건

수정본 전체를 코드와 재대조하던 중 정밀도 오류 2건을 추가 발견·정정했다.

| 발견 | 수정 전 | 수정 후 |
|------|--------|--------|
| §2.7 7d — KpiCard `accent` 호출부 수 | "11개" (페이지 수 11 과 혼동) | grep `accent=` → **20곳**(5개 페이지 ×4). "20곳" 으로 정정 |
| §2.5 — HitlCenter 기본값 CardTitle 행 | "36·67행" | `<CardTitle>` 태그는 35행(36행은 본문 텍스트). grep `CardTitle` 로 35/67/78행 확인 → "35·67행" 으로 정정 |

**최종 재대조 결과**: §2.1 KpiCard 5개 · footer 7개 · 외곽 래퍼 11개 / §2.2 badge 11 · error 7+1 · footer 7 라인 / §2.3 아이콘 칩 2곳 / §2.7 불일치 5종 + accent 20곳 — 전부 grep·Read 결과와 일치. **§2~§3 전체 파일·라인 인용 불일치 0건.** 본 문서는 2026-05-21 기준 frontend 코드와 정합한다.

### 6.4 화면 검증 — 앱 실행 + 스크린샷 (2026-05-22)

사용자 요청("화면상의 문제를 한번 더 검증")에 따라 정적 검증과 별개로 앱을 실제 구동해 육안 검증했다. `npm install` → vite dev 서버(:5173) → Playwright(chromium) 로 8개 화면을 캡처. 백엔드(:8001) 는 미실행이라 데이터 페이지는 에러/로딩 상태로 확인.

| 화면 | 확인된 시각 문제 |
|------|-----------------|
| 포트폴리오(/) | 아이콘 칩(헤더 + KPI 4칸), "실 데이터" 배지, `데이터: /api/mock/...` footer, 24px CardTitle, 중복 CardDescription — 전부 화면 노출 확인 |
| 대시보드·채널·트렌드 | `데이터 로드 실패` + `백엔드 서버 (localhost:8001)...` 개발자 문구가 에러 카드에 그대로 노출 |
| 설정 | "Sprint 3" 배지, 아이콘 칩, 24px CardTitle 노출 |
| 메모리 | "Sprint 3" 배지 + footer "로컬 샘플 데이터 — 백엔드 memory_entries API 연동은 Sprint 5+" 노출 |
| 채팅 패널 | "백엔드 서버 (localhost:8001) 연결 대기 중..." 문구 노출 |

**화면 검증으로 추가 발견한 스캐폴딩 누수 4건** (1차 정적 grep 누락 — `데이터:`/`api/mock` 패턴만 검색했기 때문):

| 발견 | 위치 | 조치 |
|------|------|------|
| "로컬 샘플 데이터 … Sprint 5+" footer | MemoryPage.tsx:214–215 | §2.2 2b ⑧ 추가 |
| "로컬 샘플 데이터 … Sprint 4" footer | ConversationsPage.tsx:150–151 | §2.2 2b ⑨ 추가 |
| "본 리포트는 mock 데이터 기반으로 생성…" | ReportPage.tsx:229 | §2.2 2b ⑩ 추가 |
| "(Sprint 6+ 연동 예정)" CardDescription | SettingsPage.tsx:133 | §2.2 2b ⑪ 추가 |

**검증하지 못한 항목** (백엔드 미실행): 7b "Connected"/"연결됨" 은 연결 성공 상태에서만 노출 → 코드(SideChatPanel.tsx:112 / TopBar.tsx:79)로만 확인. 데이터가 채워진 차트·표·KPI 숫자도 미확인 — 단 KPI 4칸 레이아웃·아이콘 칩 구조는 포트폴리오 화면에서 확인됨.

→ 색상 팔레트(Warm Neutral)는 화면에서도 일관·양호 확인. §1.1 결론 유지.

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-05-21 | 초안 — frontend "AI틱한 느낌" 원인 8종 분석 + Tier별 수정 방향. 컬러 토큰은 양호(제외), 원인은 구조·스캐폴딩·불일치로 규명. 검증 사이클: grep/Read 1차 검증 → §2.1(KPI 그리드 범위 11→5 정정)·§2.5(CardTitle 국소 override 보강) 수정 → 재검증(파일·라인 인용 불일치 0) |
| 2026-05-22 | 화면 검증 추가 — 앱 실행(vite dev) + Playwright 스크린샷 8종으로 시각 문제 육안 확인(§6.4). 스캐폴딩 누수 4건 추가 발견(§2.2 2b ⑧–⑪) → 반영. 사용자 의도(화면상의 문제)에 맞춰 문서 재정리: §1 표에 "화면 노출" 열 추가, 원인 8·7d 를 화면 무관(코드 레벨)으로 분류 |
