# VOCABULARY — UI 어휘 박제 v1 (2026-06-10)

> 페이지 구조 + 단위 어휘 단일 진실. 코드/문서/대화/PR 어휘 통일.
> spec 64 §1 정체성 보완.

## 1. 핵심 어휘 2 개 (2026-06-10 확정)

| 영문 | 한국어 | 정의 |
|---|---|---|
| **Board** | **보드** | 페이지의 메인 콘텐츠 영역. TopBar/Sidebar/SideChatPanel 을 제외한 본문 전체. React Router 의 `<Outlet />` 렌더 영역 |
| **Card** | **카드** | 보드 안의 개별 단위. KPI 표시·차트·표·그룹 strip 등. shadcn ui `Card` 컴포넌트와 일관 |

→ "**보드**" 안에 여러 "**카드**" 가 모임. `/dashboard` (페이지 명) 와 구분되며 "대시(dash)보드" 의 "보드" 정신 유지.

## 2. 보조 어휘 (관련 단위)

| 영문 | 한국어 | 정의 | 예시 |
|---|---|---|---|
| **Hero** | **히어로** | 보드 상단의 강조 카드 (보통 1 개) | `MonthlyHero` (MetricChainStrip wrapper) |
| **Track** | **트랙** | 보드 안의 큰 구분 (그룹화된 카드 묶음) | 페이지의 "01 개요" / "02 상세" 등 |
| **Section** | **섹션** | Track 대체 명칭 — 일반 페이지에서 |  |
| **Strip** | **스트립** | 가로 한 줄에 dense 하게 배치된 cell 들 | `MetricChainStrip` · `MomBar` |
| **Cell** | **셀** | Strip 안의 개별 단위 (Card 보다 작음) | grid 안 cell |
| **Frame** | **프레임** | 차트의 셸 (제목 + 차트 컨테이너) | `ChartFrame` |
| **Chain** | **체인** | 인과 관계로 묶인 메트릭 사슬 | `MetricChainStrip` (count→total→rate) |
| **Active User Bubble** | **액티브 버블** | 진행 중 사용자 메시지 박스 (진행바 오버레이). 마지막 user 메시지에만 적용. state ∈ {analyzing, planning, executing, responding, paused} | `UserBubble` (isLastUser=true) |
| **Static User Bubble** | **스태틱 버블** | 이전 turn 의 정적 사용자 메시지. 진행바 없음 (확정). 좌측 액센트 + bg-muted/40 만 유지 | `UserBubble` (isLastUser=false) |
| **Bubble Fill** | **버블 채움** | Active User Bubble 내부 absolute 진행 채움. `bg-primary/15` (paused 시 `bg-warning/15`), `transform: scaleX(percent/100)`, `transition-transform duration-200 ease-out`. 부모 `overflow-hidden` 으로 rounded 경계 흡수 | `UserBubble.tsx` 의 fill div |
| **Welcome Hero** | **웰컴 히어로** | 첫 진입 화면 상단 강조 섹션. 시스템 정체성 (Brand 워드마크 + 한 줄 가치). 좌측 액센트 strip (PALETTE J) 1군데. 차분한 결 (Apple/Stripe 결) | `WelcomeHero.tsx` |
| **Layer Diagram** | **레이어 다이어그램** | 4-Layer Agent 작동 시각화 (Cognitive→Planning→Execution→Response). inline SVG 화살표 + 노드 4 | `AgentLayerDiagram.tsx` |
| **Page Group Card** | **페이지 그룹 카드** | 컨텍스트 (시스템/클라이언트) 별 페이지 진입 카드 grid. icon + label + desc + path | `PortfolioPage` 의 PageCard |
| **Mono Label** | **모노 라벨** | 2xs 모노스페이스 uppercase tracking-wider 라벨. 헤더·메타·라벨 자리에 절제 사용 | 곳곳 |
| **Persona Card** | **페르소나 카드** | 멀티 페르소나 비전. 1 활성 (좌측 액센트 strip + foreground) + N 예정 (dimmed + "예정" 라벨) 카드 그리드 | `PersonaCards.tsx` |

## 3. 위계 (시각 강조 순)

```
강조 ↓
Hero (강조 카드)
Card (일반 카드)
Cell (Strip 안 단위)
```

→ Hero 가 보드 상단 / Card 가 중심 / Cell 이 dense.

## 4. 어휘 사용 룰

| 룰 | 의미 |
|---|---|
| **V1** | 코드 (컴포넌트 명·props·변수) 에서 위 어휘 사용 — `Card`, `Hero`, `Strip` 등 |
| **V2** | 문서 (spec·README·결과보고서) 에서 위 어휘 사용 — "보드 안 카드 hover" 등 |
| **V3** | 대화 (리뷰·논의) 에서 위 어휘 사용 — 일관성 |
| **V4** | 새 단위 추가 시 본 문서 §1/§2 확장 + spec 64 §6 자취 갱신 |

## 5. Hover State 룰 (Card · Hero · ChartFrame · Stage · Cell · Row)

### 5.1 외곽 카드 hover (Card · ChartFrame · MetricChainStrip)

| 룰 | 값 |
|---|---|
| **H1** | hover 시 `ring-1 ring-primary/40` (외곽선 굵음 효과, border 두께 변경 X — layout shift 회피) |
| **H2** | hover 시 `-translate-y-1` (4px lift, 2026-06-10 v2 갱신: 2px → 4px 강화) |
| **H3** | hover 시 `bg-primary/4` (옅은 primary 4% tint) |
| **H4** | transition: `transition` (Tailwind default, 다중 property — MOTION M3 transition-all 회피 정합) duration-200 |

### 5.2 내부 단위 hover (Cell · Stage · Row in Strip / Grid)

| 룰 | 값 |
|---|---|
| **H5** | **Cell (Strip 안)** hover = `ring-2 ring-inset ring-primary/40` (안쪽 외곽선, 2px) **만**. bg/lift 없음. ring-inset = 외곽 카드 ring-1 (바깥) 과 위계 자연 분리 + 안쪽이 더 굵음 = 강조 ↑. **2026-06-10 v6 갱신: v5 ring-1 → v6 ring-2 — 외곽선 굵기 2배 (확정)** |
| **H6** | **Nested 카드 wrapper** hover 미적용 — DataTable in ChartFrame 처럼 외곽 카드가 강조 받으면 inner wrapper 는 정적. ring 짤림 회피 (유지) |
| **H7** | **Stage (FunnelChart bar 같은 직접 viz 단위)** hover = `opacity 0.80 → 1.0` + `ring-2 ring-primary/40` (bar 자체 색 진해짐 + 외곽선). recharts 자동 hover 와 정신 동등. 2026-06-10 v2 신설 |

### 5.3 정신

→ 외곽 카드 = **강함** (ring + lift + tint). 내부 단위 = **절제** (bg 만 또는 opacity 만 — ring 없이). 위계 유지.
→ PALETTE §8.2 의 B (hairline 차등 — ring) + I (card lifting — translate) + A (color block — bg tint) + F (motion) 조합.

### 5.4 Hover 적용 매트릭스

| 컴포넌트 | 적용 룰 | 비고 |
|---|---|---|
| `components/ui/card.tsx` (shadcn Card) | H1+H2+H3+H4 | KpiCard·MomBar 등 단독 카드 |
| `components/viz/ChartFrame.tsx` | H1+H2+H3+H4 | 차트 외곽 카드 (default) |
| `components/viz/MetricChainStrip.tsx` 외곽 | H1+H2+H3+H4 | Hero strip 외곽 |
| `components/viz/MetricChainStrip.tsx` NodeTile / TransitionStub | H5 (Cell) | strip 안 단위 |
| `components/viz/FunnelChart.tsx` (stage bar) | H7 (Stage) | bar opacity + ring |
| `components/viz/DataTable.tsx` (wrapper) | 없음 (H6) | nested in ChartFrame |
| `features/monthly/MomBar.tsx` DeltaCell | H5 (Cell) | grid 안 4 cell |

## 6. 자취

- **2026-06-10 v1** : 보드/카드 어휘 박제 + Hover H1~H5 룰 (강화: ring + bg tint + -translate-y-0.5). Cell hover "미적용".
- **2026-06-10 v2** : H2 lift 강화 (2px → 4px). H5 Cell hover 재정의 (미적용 → bg-primary/8 절제 적용). H7 Stage hover 신설 (FunnelChart 등 직접 viz). 적용 매트릭스 확장 (MomBar 등).
- **2026-06-10 v3** : H5 Cell hover 강화 — bg-primary/8 단독 → bg-primary/15 + ring-1 ring-inset ring-primary/40. dense cell 영역 (Strip) 에서 인지 부족 해결. 외곽 카드 ring (바깥) ↔ Cell ring (안쪽) 위계 자연 분리.
- **2026-06-10 v4** : H5 Cell hover bg 톤 절제 — bg-primary/15 → bg-primary/10. ring 이 메인 신호, bg 는 보조 역할로 정리 (확정).
- **2026-06-10 v5** : H5 Cell hover bg 제거 — bg-primary/10 → 없음. primary ring-inset 단일 신호. 미니멀 (확정).
- **2026-06-10 v6** : H5 Cell hover ring 굵기 2배 — ring-1 → ring-2. 외곽 카드 ring-1 (바깥) ↔ Cell ring-2 (안쪽, 굵음) 위계 강화 (확정).
- **2026-06-10 v7** : Active/Static User Bubble + Bubble Fill 어휘 신설 — 사용자 메시지 박스 progress bar. progress % = phase base + (completed/total) × 65 (executing 구간). 단조 증가 + turnId 변화 시 리셋. 이전 turn user 메시지 = Static (정적). useBubbleProgress hook + UserBubble 컴포넌트 (확정).
- **2026-06-10 v8** : Welcome Hero / Stage Strip / Layer Diagram / Page Group Card / Video Frame 어휘 신설 — PortfolioPage 첫 진입 화면 재설계 (시스템 설명 + 시각화). YouTube 임베드 (nocookie + rel=0 + modestbranding=1). 4-Layer Agent inline SVG. 그라데이션·glow 0.
- **2026-06-10 v9** : Session Header / Overview Card / Mono Label 어휘 신설 — Mirofish 결 첫 진입 시각화 Phase 1. 상단 Brand·LIVE·UTC + 누적 큰 KPI + 4 small KPI + Top Highlight (배경 sparkline). 모노스페이스 폰트 라벨 (font-mono 2xs uppercase tracking-wider). 데이터 = 시뮬레이션+실데이터 혼합 (D3). Welcome Hero / Stage Strip 폐기.
- **2026-06-10 v10** : Persona Tab / Feature Showcase / Showcase Media 어휘 신설 — Header 재구성 (시계 제거, DreamAgent 큰 워드마크 + 페르소나 탭). FeatureShowcase 신설 (데이터 표시·그래프·에이전트 워크플로우 3 카드, inline SVG 자동 애니메이션, shadow-lg ring-1 음영 강조). 향후 GIF/MP4 미디어 교체 자리 마련.
- **2026-06-10 v11** : Feature Showcase / Showcase Media 어휘 폐기 + 컴포넌트 파일 삭제 — 추후 개발 문서 작성 후 정확한 결로 재구현 예정. Persona Tab 어휘는 보존 (MirofishHeader 사용 중).
- **2026-06-12 v12** : 첫 진입 페이지 재설계 (계획서 docs/reports/계획_첫진입페이지_재설계_2026-06-12.md 적용). 폐기: Session Header / Overview Card / Stage Strip / Video Frame / Persona Tab. 신설/갱신: Welcome Hero v2 (차분한 Apple/Stripe 결) / **Persona Card** (3 카드 그리드, 1 활성 + N 예정). 컴포넌트 폐기 = MirofishHeader / OverviewCard / YouTubeEmbed (3 파일). 6 섹션 → 4 섹션 단순화 (Welcome Hero + 4-Layer Diagram + Page Group + Persona Cards).
- **2026-05-22** (이전, 별도) : viz/* 컴포넌트 명명 — ChartFrame, MetricChainStrip, DataTable 등 (도메인 명사 위주)
