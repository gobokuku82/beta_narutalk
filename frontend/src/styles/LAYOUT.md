# LAYOUT — 페이지 layout 패턴 v1 (2026-06-08)

> 18 페이지 root layout 의 4 표준 패턴 박제.
> spec 64 §3 메타룰 (MR1 임의값 / MR4 위계) 적용.

## 1. 결정된 4 룰

| # | 룰 | 값 |
|---|---|---|
| **L1** | **root layout 은 4 패턴 중 선택** | A default · B centered · C console · D canvas — 본 §2 |
| **L2** | **PageHeader 가 root 직속** | `<div className="...">` 안 첫 element = `<PageHeader />` (canvas D 제외) |
| **L3** | **spacing 4px 그리드 강제** (SPACING S1) | `gap-N`/`space-y-N`/`p-N` 모두 SPACING.md 5 단계 사용 |
| **L4** | **새 패턴 신설 금지** | 4 패턴 외 신규 root 금지. 필요 시 본 문서 §2 확장 합의 |

## 2. 4 표준 패턴

### A · default — 일반 콘텐츠 페이지 (10개)

```tsx
<div className="space-y-6 p-6">
  <PageHeader title="..." description="..." icon={...} />
  {/* 카드·차트·표 등 wide 콘텐츠 */}
</div>
```

| 속성 | 값 |
|---|---|
| Container | full width (max-w 없음) |
| Padding | `p-6` (24px) |
| Section 간격 | `space-y-6` (24px) |
| 어울리는 결 | 차트·표·카드 grid 등 wide 콘텐츠 |
| 페이지 | Channel · Conversations · Cost · Creative · Dashboard · Hitl · Memory · Monthly · Settings · Trend |

### B · centered — 좁은 텍스트 중심 (2개)

```tsx
<div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-6">
  <PageHeader title="..." />
  {/* 카드/리스트 (narrow) */}
</div>
```

| 속성 | 값 |
|---|---|
| Container | `max-w-7xl mx-auto` (1280px 중앙) |
| Padding | `px-4 py-6` (16/24px) |
| Section 간격 | `gap-6` (24px) — flex-col |
| 어울리는 결 | 포트폴리오 그리드 · 리포트 본문 등 |
| 페이지 | Portfolio · Report · AgentObservability |

### C · console — 풀높이 콘솔 (2개)

```tsx
<div className="flex h-full flex-col gap-4 p-6">
  <PageHeader title="..." />
  {/* 풀높이 콘텐츠 (스크롤 X) */}
</div>
```

| 속성 | 값 |
|---|---|
| Container | `h-full flex flex-col` (부모 높이 채움) |
| Padding | `p-6` (24px) |
| Section 간격 | `gap-4` (16px — 콘솔은 dense) |
| 어울리는 결 | DB 콘솔 · 시스템 콘솔 (스크롤 안에서 동작) |
| 페이지 | DataConsole · SystemConsole |

### D · canvas — 풀스크린 캔버스 (1개)

```tsx
<div className="h-full flex flex-col">
  {/* React Flow / 풀스크린 캔버스 (padding 0) */}
</div>
```

| 속성 | 값 |
|---|---|
| Container | `h-full flex flex-col` |
| Padding | **0** (캔버스 가장자리까지) |
| PageHeader | **없음** (캔버스 내부에 floating UI) |
| 어울리는 결 | React Flow · 지도 · 풀스크린 viz |
| 페이지 | Workflow |

## 3. Placeholder 페이지

PagePlaceholder 컴포넌트 사용 — root layout 무관 (placeholder 자체가 standalone):

```tsx
return (
  <PagePlaceholder
    title="..."
    description="..."
    sprintTarget="Sprint N"
  />
);
```

| 페이지 | 비고 |
|---|---|
| AgentChat | Sprint 2 대기 |

## 4. 새 페이지 추가 절차

1. 페이지 결 결정 — 일반 콘텐츠 / 좁은 텍스트 / 풀높이 콘솔 / 풀스크린 캔버스
2. §2 4 패턴 중 선택 (A/B/C/D)
3. 새 패턴 필요 시 **합의 후 본 문서 §2 확장** (L4 룰)
4. PageHeader 활용 — title/description/icon (canvas 제외)
5. 본 문서 §자취 + spec 64 §6 갱신 (필요 시)

## 5. 미래 PageContainer primitive (후보)

현재는 inline `<div className="...">` 패턴. 미래에 컴포넌트로 추출 가능:

```tsx
<PageContainer variant="default">  {/* or "centered" / "console" / "canvas" */}
  <PageHeader title="..." />
  {/* ... */}
</PageContainer>
```

장점: 패턴 변경 시 한 곳만, 일관성 강제.
단점: 18 페이지 모두 수정 필요. 큰 작업.

→ Phase 7 (Enforcement) 와 함께 검토.

## 6. 자취

- **2026-06-08** : v1 박제 — 4 패턴 표준화. AgentObservability `gap-5` → `gap-6` (B 패턴 정합) 1건 정리.
  - 분포: A default 10 / B centered 3 (Portfolio, Report, AgentObservability) / C console 2 / D canvas 1 / Placeholder 1
