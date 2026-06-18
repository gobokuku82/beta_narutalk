# PALETTE — 색 토큰 기준 v1 (2026-06-08)

> globals.css 의 HSL 토큰 결정을 박제. 새 색 추가/변경 시 본 문서의 룰 5개를 통과해야 함.
> spec 61 §4.1 / 본 문서 단일 진실. 변경 시 globals.css + 본 문서 동시 갱신.

## 1. 결정된 5 룰

| # | 룰 | 값 |
|---|---|---|
| **R1** | 채도(S) 상한 (의미 강조 허용) | 모든 토큰 **S ≤ 60%** |
| **R2** | 명도(L) 범위 | 라이트 색 토큰 **L ∈ [38%, 56%]** (대부분 40~50%) |
| **R3** | Hue family | **자유** — 채도 상한이 family 통일 임무 (warm bias 강제 X) |
| **R4** | 역할별 채도 segmentation | accent > brand > status > chart > muted (위계로 S 차등) |
| **R5** | WCAG 대비비 | 텍스트 vs 배경 **AA (4.5:1)** 최소, 큰 글자 3:1 |

추가 룰:
- **카드 vs 배경 명도 차** : 4~6%p (현 100−96=4 유지)
- **다크 모드 변환** : hue 동일, L invert (라이트 40% → 다크 60%), S 약간 ↑ (eye fatigue 보정)

## 2. 역할별 채도 segmentation (R4 구체)

```
S 범위    | 0%  10%  20%  30%  40%  50%  60%
────────┼──────────────────────────────────
border  | ━━━━━ (≤10%)
muted   | ━━━━━━━ (≤20%)
chart   |       ━━━━━━━━ (14~32%)         ← 분류 색 5개
status  |             ━━━━━━━━ (22~58%)   ← 의미 강조 허용
brand   |                   ━━━━━━━━ (36~58%) ← 브랜드 식별성
accent  |                         ━━━━━━ (50~60%) ← --primary 옥스블러드 1개
```

→ 같은 막대에 여러 색 섞일 때 accent/brand 가 자동으로 도드라짐. chart 는 절제.

## 3. 현 토큰 매핑 (라이트, 2026-06-08)

### 베이스
| 토큰 | HSL | segment | 비고 |
|---|---|---|---|
| `--background` | 39 38% 96% | base | warm beige |
| `--card` | 0 0% 100% | base | 순백 (배경과 4%p 분리) |
| `--foreground` | 20 8% 15% | text | 본문 |
| `--muted-foreground` | 34 9% 42% | text-muted | 보조 |
| `--border` | 38 23% 88% | muted | hairline |
| `--muted` | 40 24% 93% | muted | bg layer |

### Accent (위계 최상, 1개만)
| 토큰 | HSL | S | 메모 |
|---|---|---|---|
| `--primary` | 350 55% 38% | 55% | 옥스블러드/마호가니 |

### Brand (channel — 브랜드 식별성)
| 토큰 | HSL | S | 메모 |
|---|---|---|---|
| `--channel-naver` | 140 36% 40% | 36% | 네이버 녹 |
| `--channel-kakao` | 40 58% 48% | 58% | kakao 노랑 (62→58 cap, 2026-06-08) |
| `--channel-meta` | 214 40% 48% | 40% | 메타 파랑 |
| `--channel-google` | 8 52% 50% | 52% | 구글 빨강 |

### Status (의미 색)
| 토큰 | HSL | S | 메모 |
|---|---|---|---|
| `--success` | 142 24% 40% | 24% | 정상 (warm green) |
| `--destructive` | 6 38% 44% | 38% | 과소진 (dusty terracotta) |
| `--warning` | 32 42% 44% | 42% | 저소진 (dusty mustard) |

### Chart (분류 색 5개)
| 토큰 | HSL | S | 메모 |
|---|---|---|---|
| `--chart-1` | 210 25% 48% | 25% | warm steel blue |
| `--chart-2` | 20 32% 50% | 32% | terracotta |
| `--chart-3` | 160 22% 40% | 22% | muted sage |
| `--chart-4` | 285 14% 54% | 14% | dusty plum |
| `--chart-5` | 34 14% 50% | 14% | warm grey |

## 4. 다크 모드 토큰 (라이트 invert 룰 R5 적용)

| 토큰 | 라이트 | 다크 | 변환 |
|---|---|---|---|
| `--destructive` | 6 38% 44 | 6 40% **56** | L +12, S +2 |
| `--success` | 142 24% 40 | 142 26% **52** | L +12, S +2 |
| `--warning` | 32 42% 44 | 32 44% **56** | L +12, S +2 |
| `--chart-1` | 210 25% 48 | 210 27% **60** | L +12 |
| `--chart-2` | 20 32% 50 | 20 34% **62** | L +12 |
| `--chart-3` | 160 22% 40 | 160 24% **52** | L +12 |
| `--chart-4` | 285 14% 54 | 285 16% **66** | L +12 |
| `--chart-5` | 34 14% 50 | 34 16% **62** | L +12 |

채널 색 다크 오버라이드 = 없음 (라이트 그대로). 다크 배경에서 가독성 검증 후 별도 결정.

## 5. 룰 위반 / 후속 검토

| 위치 | 사항 | 상태 |
|---|---|---|
| `--channel-kakao` 라이트 | 62→58 cap (2026-06-08) | ✅ 조정 완료 |
| `--warning` 다크 75% | 라이트 invert (56) 적용 | ✅ 조정 완료 |
| workflow `--node-*` (spec 62) | R1 검증 안 함 — workflow canvas 의미 강조 강함 | 후속 별도 검토 |
| 채널 색 다크 오버라이드 X | 다크 배경 위 가독성 미검증 | 후속 (다크 도입 시) |

## 6. 새 색 추가 절차

1. 어느 segment 인가? (accent/brand/status/chart/muted)
2. 해당 segment 의 S/L 범위 안인가? (위 §2 표)
3. 기존 토큰과 hue 충돌 안 하나? (`--primary` 350°, `--destructive` 6°, ...)
4. 다크 모드 값도 같이 (L invert 룰 §4)
5. 본 문서 §3·§4 표 + globals.css 동시 갱신

## 7. 자취

- **2026-05-13** : 초기 shadcn 기본값 (spec 61 §4.1 옛 박제 — 회색/blue 위주)
- **2026-05-14** : "2026 Warm Neutral" — 따뜻한 베이지 + 옥스블러드 액센트 1개 (메모리 `feedback_no_ai_looking_ui`)
- **2026-05-22** : A2 — 차트 5색 역할 분리 (chart-1~5 = 비채널 다계열, channel-* = 채널 분해)
- **2026-06-08 (1)** : Warm Dusty 통일 — status/chart 채도 격차 해소 (commit `9625cea`)
- **2026-06-08 (2)** : palette 기준 5 룰 박제 (본 문서 v1, commit `ac51144`)
- **2026-06-08 (3)** : **§8 효과 (Effects) 카테고리 박제** — 그라데이션 금지 이유 + 대체 11 카테고리 + 페이지별 매핑

---

## 8. 효과 (Effects) — 그라데이션 대체 카테고리

> 색 (§1~§7) 이 "**무엇**" 이라면 효과는 "**어떻게 살아 움직이나**". 두 spec 짝.
> 본 절이 커지면 별도 `EFFECTS.md` 로 split.

### 8.1 그라데이션·glow·glassmorphism 금지 — 이유 박제

메모리 `feedback_no_ai_looking_ui` 의 "그라데이션·glow 금지" 룰의 근거:

| # | 이유 |
|---|---|
| 1 | **자동 생성 어플의 디폴트** — Midjourney/Bento/Lovable 등 AI 도구가 무차별 적용 → 학습된 어감 |
| 2 | **무의미한 색 변화** — A→B 사이 색에 메시지 없음, 장식이 정보를 가림 |
| 3 | **2010s SaaS hero section 회상** — 보라→파랑 그라디언트가 "스타트업 랜딩페이지" 와 결부 |
| 4 | **밝기 변동이 시선 분산** — 한 영역 안 명도 차 → 장식이 데이터보다 먼저 읽힘 |

→ 핵심 = **"의미 없는 시각 노이즈"**. 그라데이션 자체가 죄가 아니라 *무의미한 색 변화* 가 문제.

### 8.2 허용 효과 11 카테고리 (의미 있는 활기)

| # | 카테고리 | 본질 | 예시 / 이미 적용된 곳 |
|---|---|---|---|
| **A** | **단색 강조 영역 (color block)** | 그라데이션 X, 평면 단색 (액센트 톤다운) | `MonthlyPage` Hero zone wrapper (`bg-accent/50`) — 2026-06-08 |
| **B** | **Hairline 차등** | 보더 두께·색 차등으로 위계 | 강조 카드만 2px / 일반 1px |
| **C** | **Typography 위계** | 글자 자체가 주인공 | `MonthlyPage` PageHeader title "월간 결산" 만 `text-primary` — 2026-06-08 |
| **D** | **간격 (whitespace) 위계** | 색 대신 공간으로 강조 | 강조 영역만 padding ×2 |
| **E** | **Spot icon 큰 사이즈** | 일러스트 X, 의미 있는 1 아이콘 | 빈 상태에 큰 lucide 1개 |
| **F** | **Motion (절제)** | 진입 시 staggered fade-in (50~100ms 차등, 200ms 이내) | recharts chart reveal (기본) |
| **G** | **Texture (절제)** | 종이 결 / dot grid / subtle noise (opacity ≤ 3%) | 배경 미세 texture |
| **H** | **Border-radius 위계** | 형태로 강조 (12px vs 8px) | Hero 카드 더 큰 radius |
| **I** | **Card lifting** | shadow 없이 명도/border로 lift | 강조 카드 `border-foreground/20` |
| **J** | **Color strip (좌/하)** | 측면 한 줄 액센트 (status indicator) | `PacingWidget` 막대 (이미 적용) |
| **K** | **Reading flow guide** | dot line / 화살표로 시선 안내 | `MetricChainStrip` `ArrowRight` (이미 적용) |

**위계** : A·B·C·D (정적 강조, 가장 안전) > F·G (절제 motion/texture) > E·H·I·J·K (구조적).
**금지** : gradient · glow · drop-shadow blur · glassmorphism · 일러스트 · 형광 색.

### 8.3 페이지 결별 적합 매핑

| 페이지 결 | 적합 | 부적합 |
|---|---|---|
| **Hero / 결산 (monthly)** | A 단색 영역, C 타이포, D 간격, K reading flow | F motion 강함 (정적 결산) |
| **운영형 차트 (dashboard·trend)** | F motion (chart reveal), J color strip | A 단색 배경 (차트 가림) |
| **표/데이터 (DataTable)** | B hairline 차등, J in-cell bar | A 단색 영역 (가독성 ↓) |
| **포트폴리오 / 리스트** | I card lifting, H radius 위계 | F motion 과함 |
| **HITL / 승인 대기** | J status strip (urgency), F motion (새 알림) | C 큰 타이포 (긴장 ↑) |
| **빈 상태 (empty)** | E spot icon, C 타이포 | A·B·F 모두 부적합 |
| **에이전트 채팅** | F message reveal motion, B hairline 말풍선 | A 단색 배경 (메시지 가림) |

### 8.4 새 효과 추가 절차

1. 11 카테고리 중 어느 것인가? (위 §8.2)
2. 페이지 결에 적합한가? (위 §8.3)
3. 금지 효과 (gradient/glow/glassmorphism) 회피했나?
4. "의미 있는가?" — 정보 강조 / 위계 표현 / 인터랙션 피드백 중 하나여야 함. 순수 장식 X
5. 코드 적용 전 본 문서 §8.2 의 "이미 적용된 곳" 칸 갱신 (자취 박제)
