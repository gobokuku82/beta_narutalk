# C:LUMI Frontend 진입 직전 — Compact 준비 (2026-05-26)

> ⚠️ **OUTDATED (2026-05-27 이후)** — Sprint 16 backend/frontend rename 작업 *이전* 시점.
> - 본 보고서가 가리키는 `/clumi/2026-04` route 는 `/dashboard1` 로 변경 (commit b17ec8a)
> - `features/clumi/` → `features/dashboard1/`, `useClumiData` → `useDashboard1Data` (commit ba242c7·e88e362)
> - 본 보고서 §"진입 직전" 의 단일-회사 가정 → 다중 client (TopBar 드롭다운 + ?client= param) 로 발전
> - 최신 compact 회복 문서: `docs/reports/session_compact_recovery_2026-05-27.md`
> - data/ 자산 (raw 21 + cleaned 13 + computed 22) 과 정답 17 은 그대로 유효.

---

> compact 직후 이어서 작업 재개. **현 작업 = `/clumi/2026-04` 대시보드 페이지 신설 Step 1 (Pydantic Output) 진입 직전**.

---

## 0. 메타

| 항목 | 내용 |
|---|---|
| 작성일 | 2026-05-26 |
| 위치 | `docs/reports/session_compact_recovery_2026-05-26.md` |
| Compact 시점 | frontend 대시보드 계획서 작성 완료 + 컨벤션 위반 사전 수정 직후, Step 1 진입 전 |
| 작업 도메인 | C:LUMI — 28 요소 한 스크롤 대시보드 (insights 0) |
| Branch | main (origin/main +22 직전 또는 동기화 가능) |

---

## 1. 현 작업 한 줄

**backend 65 tool 완성 (정량 17/17·MoM 6·118 tests) → frontend `Clumi2026Dashboard` 1 페이지 신설 계획서 작성·컨벤션 수정 완료. 다음 = Step 1 Pydantic Output 17 모델 작성.**

---

## 2. 즉시 다음 액션 (compact 직후 이 순서)

1. **본 문서 §1·§2 + §4 핵심 결정 읽기**
2. **계획서 정독**: `docs/_claude/frontend/clumi_2026_04_대시보드_계획서_2026-05-26.md`
   - §3 frontend 소스코드 위치 (features/clumi/ flat + api/hooks/useClumiData.ts)
   - §4 Step 1-7 시퀀스
3. **Step 1 진입** — Pydantic Output 17 모델 신설:
   - 파일: `backend/app/dream_agent/models/clumi_outputs.py`
   - 17 모델 (각 tool 의 produces 와 짝)
   - `models/__init__.py` export
   - `tests/clumi/test_clumi_outputs.py` (17 validate 케이스)
   - 자동 커밋: `feat(models): clumi Pydantic Output 17 — frontend typed contract`
4. **Step 2** — `backend/api_v2/routes/clumi.py` 18 endpoint + 캐시
5. **Step 3-7** — frontend (위치 §4)

---

## 3. 완료된 것 (검증 상태)

| 영역 | 산출 | 상태 |
|---|---|---|
| **backend tool 65** | 14 기존 + 51 신규 (cleaning 3·preprocessing 4·normalization 4·metrics 12·comparison 7·collection 21) | ✅ |
| **테스트** | `backend/tests/clumi/` 118/118 PASS | ✅ |
| **정량 정답** | methodology 17/17 (S001·S002·S003·S004·S005·S028·S032·S037·S046·S048·S054·S067·S069) | ✅ |
| **MoM 패턴** | 6 변화율 (매출 +50.5%·재구매·신규주문 +1.4%·객단가·신규가입 -0.2%·etc) | ✅ |
| **정제 10/10 규칙** | active·KST·회원검증·채널·광고비·GA4세션·카테고리·등급·UTM·비회원 | ✅ |
| **인프라** | storage 추상 (FileStorage·PostgresStorage 골격) · 6 helper · ToolSpec.storage | ✅ |
| **ERD** | raw L1/L2/L3 (DBML 자동) + cleaned (6 entity) + computed (15 entity) | ✅ |
| **분석 계획서** | inventory 매핑 (69 산출물 × 65 tool, MVP 섹션 5+1-1) | ✅ |
| **대시보드 계획서** | 28 요소 1 페이지 / 8 컴포넌트 / 18 endpoint / Step 1-7 (3-4일) | ✅ |
| **컨벤션 수정** | features/clumi/ flat (sub 폴더 X), api/hooks/useClumiData.ts 통합 | ✅ |

**미완성** (frontend 와 독립):
- insights 28 박스 (LLM, methodology_insights.md 박스 작성 룰 박제됨)
- prediction (장기)
- 신규 17 metric (광고효율 CTR/CPC/CPM/CVR·퍼널 GA4 #08·세그먼트 확장)

---

## 4. 핵심 결정 (compact 에서 절대 잃지 말 것)

### 4.1 페이지 명세

| 항목 | 값 |
|---|---|
| URL | `/clumi/2026-04` |
| 형태 | 한 스크롤 페이지 (세로 길게) |
| 요소 | **28** (KPI 9 + MoM 4 + LTV 2 + 광고비 1 + 채널 2 + 연령 2 + 카테고리 1 + 회원 4 + Header 3) |
| insights | **0** (사용자 명시 — 정량만) |
| Section 수 | 8 + Header |

### 4.2 28 요소 정확값 (회귀 박제)

```
KPI 9:
  매출 119,539,660 · 마케팅비 18,306,923 · ROAS 6.53
  CAC 30,512 · 프로모션매출 43,400,360 · 프로모션 ROAS 2.37
  신규 600 · 객단가 62,293 · 가입전환 2.50%

MoM 4 (4월 vs 3월):
  매출 +50.5% · 주문 +42.6% · 기존고객 +19.2% · 신규주문 +1.4%

LTV 2:
  등급 도트 (4시점): 6,680 → 7,299 → 7,900 → 8,500
  등급 표: WELCOME 74.5%·0% / REGULAR 18.1%·34.7% / SILVER 7.1%·57.8%★ / GOLD 0.3%·7.5% / VIP 0·0

광고비 1:
  Meta 9,235,826 + NaverSA 5,999,627 + ADVoost 3,000,000 + Kakao 59,020 + Talktalk 12,450 = 18,306,923

채널 2: 10채널 분포 (Naver 530·Unknown 481·Meta 388·Direct 273·...) + 알수없음 매출비중 39.8%
연령 2: 11 bucket (40-44=1,455·35-39=1,429·...) + 35-44 합 2,884
카테고리 1: 스킨케어 67.7M·클렌징 19.1M·마스크팩 19.4M·자외선차단 6.9M·기타 6.5M
회원 4: 회원 1,779 / 비회원 140 + 재구매율 4월 79.0% / 3월 76.2% + 신규가입 MoM -0.2%
```

### 4.3 Frontend 소스코드 위치 (사용자 핵심 질문 답)

**컨벤션 실측 후 확정**:
- `components/` = **공용 UI 디자인 시스템 전용** (layout·markdown·ui — shadcn). 도메인 X
- `features/<domain>/` = **도메인 컴포넌트 + 페이지 — flat 평탄** (sub 폴더 X — 기존 18 feature 모두 동일)
- `api/hooks/` = **API fetch hooks 모음** (useMockData·useWebSocket 과 동급)

```
frontend/src/
├── features/clumi/                  ← 신설 (flat)
│   ├── Clumi2026Dashboard.tsx       ← 메인 페이지
│   ├── KpiCard.tsx                  ← 8 도메인 컴포넌트 flat
│   ├── MomBar.tsx
│   ├── GradeDotChart.tsx
│   ├── GradeRatioTable.tsx
│   ├── AdCostBar.tsx
│   ├── ChannelDistTable.tsx
│   ├── AgeBucketBar.tsx
│   ├── CategoryDistTable.tsx
│   ├── MemberGuestSummary.tsx
│   ├── types.ts                     ← Pydantic Output 와 짝
│   └── periods.ts                   ← '2026-04' 상수
├── api/hooks/
│   └── useClumiData.ts              ← 신규 (18 endpoint 통합 react-query)
├── components/                       ← 변경 없음 (KpiCard base 만 ui/Card 재사용)
└── routes/router.tsx                 ← clumi2026Route 추가 (`/clumi/2026-04`)
```

### 4.4 Backend 신설 (Step 1·2)

- **`backend/app/dream_agent/models/clumi_outputs.py`** — Pydantic Output 17 모델
- **`backend/api_v2/routes/clumi.py`** — 18 endpoint (KPI 9 + MoM 4 + Segment 7 — 일부 통합)
- **`backend/api_v2/main.py`** — include_router 1줄
- 기존 65 tool **무수정** (단지 호출)
- 캐시 정책: `storage.exists('computed', key)` hit 시 즉시 반환, miss 시 tool 실행

### 4.5 18 endpoint 매핑

```
GET /api/clumi/kpi/revenue?period={p}           → revenue_total
GET /api/clumi/kpi/ad-cost?period={p}           → ad_cost_aggregator
GET /api/clumi/kpi/roas?period={p}              → roas_overall
GET /api/clumi/kpi/cac?period={p}               → cac_overall
GET /api/clumi/kpi/promotion-revenue?period={p} → promotion_revenue
GET /api/clumi/kpi/promotion-roas?period={p}    → promotion_roas
GET /api/clumi/kpi/new-members?period={p}       → new_members_monthly
GET /api/clumi/kpi/aov?period={p}               → aov_monthly
GET /api/clumi/kpi/signup-conversion?period={p} → signup_conversion
GET /api/clumi/mom/revenue?a={a}&b={b}          → mom_revenue
GET /api/clumi/mom/repurchase?a={a}&b={b}       → repurchase_mom
GET /api/clumi/mom/aov?a={a}&b={b}              → aov_mom
GET /api/clumi/mom/new-members?a={a}&b={b}      → new_members_mom
GET /api/clumi/segment/grade?period={p}         → grade_revenue
GET /api/clumi/segment/grade-timeseries         → grade_timeseries
GET /api/clumi/segment/age                      → age_segment
GET /api/clumi/segment/category?period={p}      → category_multi_distributor
GET /api/clumi/segment/channel?period={p}       → channel_attribution_normalizer
GET /api/clumi/segment/member-guest?period={p}  → member_guest_splitter
GET /api/clumi/segment/unknown-share?period={p} → unknown_revenue_share
```

### 4.6 Step 1-7 시퀀스 (자동 커밋 7회)

```
Step 1 (0.5일) — Pydantic Output 17 모델 + test
Step 2 (0.5일) — API route 18 endpoint + 캐시 + HTTP 회귀
Step 3 (0.5일) — features/clumi/ types + api/hooks/useClumiData.ts
Step 4 (1.0일) — 8 도메인 컴포넌트 (flat)
Step 5 (0.5일) — Clumi2026Dashboard 페이지 + router 등록
Step 6 (0.5일) — API 연동 + 28 요소 화면 회귀
Step 7 (0.5일) — KPI 9 ⓘ tooltip (progressive disclosure 1차)
```
총 **3-4일** (집중).

### 4.7 5 메타 질문 답 (frontend 디자인 핵심)

| Q | 답 |
|---|---|
| Q1 어떤 시각화 | 3축 분리 — 분석 대시보드 1차 / 검증 모니터링 2차 / 세부옵션 3차 (순차) |
| Q2 표시할 데이터 | inventory.md 69 산출물 = 답. 추측 X. 본 페이지 = 28 정량 |
| Q3 결과 표현 방식 | KPI 카드 9 + 차트 7 + 표 23 + 해설 28 (inventory §통계) |
| Q4 세부설정 옵션 | ⓘ tooltip (MVP) → ⋮ drawer (2차) → tool chain DAG (3차) |
| Q5 보고싶은 것 | inventory + 카톡 K1-K20 = 답. *자산 망각* 진단 |

### 4.8 분석/추론/예측 분리 (사용자 1번 답)

- **분석** = metrics + comparison + visualization → ✅ 완성
- **추론** = insights 28 박스 (LLM) → ⏳ 본 페이지 *제외*
- **예측** = forecasting → ⏳ inventory 외, 별도 영역

### 4.9 컨벤션 위반 회피 (마지막 수정)

**사용자 질문**: "components 폴더로 만들어야 하는거 아닌가?"
**답**: 기존 18 feature 모두 flat 평탄 — `features/clumi/components/` sub 폴더 X. **`features/clumi/*.tsx` flat** + **`api/hooks/useClumiData.ts` 통합**.

---

## 5. 파일·문서 위치 맵

### 핵심 입력 (정독 대상)

| 파일 | 역할 |
|---|---|
| `docs/_claude/frontend/clumi_2026_04_대시보드_계획서_2026-05-26.md` | **현 작업 계획서** (Step 1-7) |
| `docs/_claude/frontend/clumi_분석계획서_inventory매핑_2026-05-25.md` | inventory 매핑 + MVP 선정 근거 |
| `docs/reports/clumi_백엔드_tool_구현_완료보고서_2026-05-25.md` | backend 65 tool 자산 가시화 |
| `data/clumi/description/deliverable_inventory.md` | **69 산출물 sitemap** (frontend = inventory) |
| `data/clumi/description/methodology_*.md` | 6 methodology (cleaning 10·calculations 46·insights 25·visualization·deliverable·scenario) |

### Backend 자산 (호출 대상)

| 영역 | 위치 |
|---|---|
| catalog YAML | `backend/app/dream_agent/tools/catalog/` (65 yaml) |
| tool .py | `backend/app/dream_agent/tools/` (cleaning·comparison·metrics·normalization·preprocessing/clumi·collection/clumi 6 폴더) |
| helper | `backend/app/dream_agent/tools/shared/` (storage·clumi_loader·missing·order·ad_cost·ga4) |
| 모델 | `backend/app/dream_agent/models/tool.py` (ToolSpec.storage + StoragePolicy) |
| 테스트 | `backend/tests/clumi/` (118 케이스) |

### Frontend 신설 위치 (작업 대상)

| 영역 | 위치 |
|---|---|
| 도메인 | `frontend/src/features/clumi/` (10 파일 flat) |
| API hooks | `frontend/src/api/hooks/useClumiData.ts` |
| 라우트 | `frontend/src/routes/router.tsx` (clumi2026Route 추가) |
| (참고) 공용 UI | `frontend/src/components/ui/` (수정 X, 재사용만) |

### Data 산출 (gitignored — 캐시)

| 위치 | 내용 |
|---|---|
| `data/clumi/` | raw 21 소스 (gitignored — GA4 100MB+) |
| `data/clumi_cleaned/` | tool 산출 (parquet·json + `_schema/`) |
| `data/clumi_computed/` | metric 산출 (S001~S069 json + `_schema/`) |

### ERD (gitignored)

| 파일 | 내용 |
|---|---|
| `docs/_claude/data/erd/raw_clumi_erd_L1_full.dbml` | 21 entity 전체 (DBML, dbdiagram.io 렌더링) |
| `raw_clumi_erd_L2_compact.dbml` | 핵심만 |
| `raw_clumi_erd_L3_relations.dbml` | 관계만 |
| `cleaned_clumi_erd_L1_full.dbml` | 6 cleaned entity |
| `computed_clumi_erd_L1_full.dbml` | 15 computed entity |
| `manual_refs.yaml` | 사람 검토 Ref 정의 (7) |

---

## 6. 유지할 컨벤션·원칙 (메모리 일관)

### Backend
- **tool 원자성** — 1 tool = 1 일
- **catalog YAML + tool .py 분리** (메타 / 구현)
- **clumi_answer_values 메타** = 회귀 박제 (catalog YAML 안)
- **storage 추상** — FileStorage POC, PostgresStorage MVP+
- **helper 추출 기준** = 3 tool 이상 반복 시
- **결정론** — 수집·정제·계산 LLM 미경유 (insights 만 LLM)

### Frontend
- **features/<domain>/ flat 평탄** (기존 18 feature 동일)
- **components/ = 공용 UI 전용** (도메인 X)
- **api/hooks/ = fetch hooks 모음**
- **TanStack Router code-based** (router.tsx 단일 진실원)
- **TanStack Query** (캐시·로딩·에러)
- **2026 Warm Neutral 디자인** (메모리: AI 만든 티 금지, 색 결정 전 디자인 시스템 조사)

### 작업 흐름
- **단계 완료 시 자동 커밋** (feedback 메모리)
- **테스트 단축/skip 금지** (TDD 우선, 회귀 필수)
- **권한 프롬프트 전부 통과** (bypassPermissions)
- **회귀 박제 3겹**: backend pytest + API HTTP + frontend e2e (선택)
- **점진 보완** — 추측 일괄 X, 실 구현 후 사전·ERD 자동 갱신

### Git
- **data/ 전체 gitignore** (GA4 100MB+ 제한 회피, filter-branch 적용 이력)
- **docs/_claude/ gitignored** (자취·계획서·박제 로컬 only)
- **docs/reports/ git 추적** (영구 자산)
- **자동 커밋 메시지**: `feat|fix|chore|docs(scope): 한국어 요약` + 본문 + `Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>`

---

## 7. 미해결 / 보류

| # | 항목 | 결정 시점 |
|---|---|---|
| Q1 | 차트 라이브러리 — recharts vs visx vs native SVG | Step 4 진입 시 (frontend 의존성 조사 후) |
| Q2 | navigation 메뉴 추가 vs URL 직접 접근 | Step 5 |
| Q3 | period selector — 4월 고정 vs 임의 YYYY-MM | Step 7 (MVP=고정) |
| Q4 | 회원/비회원 시각화 — pie·bar·단순 숫자 | Step 4 |
| Q5 | 인앱광고 A/B partial — 본 페이지 *제외* | 확정 (정량 28만) |
| Q6 | 검증 모니터링 페이지 (`/admin/data-quality`) | MVP 통과 후 |
| Q7 | insights LLM 박스 — 본 페이지 *제외* | 향후 별도 페이지 (1박스 시범부터) |
| Q8 | 신규 17 metric (광고효율·퍼널·세그먼트 확장) | inventory 매핑 §6 권장 순서 — MVP 후 2차~6차 |

---

## 8. 빠르게 컨텍스트 복원하는 법

compact 후 사용자가 "이어서 진행" 만 하면 다음 순서로 즉시 복원:

1. **본 문서 §1·§2·§4** (현 작업·다음 액션·핵심 결정 28값·위치)
2. **`docs/_claude/frontend/clumi_2026_04_대시보드_계획서_2026-05-26.md` §3·§4** (위치 + Step 시퀀스)
3. **inventory** (`data/clumi/description/deliverable_inventory.md`) — frontend sitemap
4. **완료 보고서** (`docs/reports/clumi_백엔드_tool_구현_완료보고서_2026-05-25.md`) §4 (기존 vs 신규 tool)
5. → Step 1 진입 (`backend/app/dream_agent/models/clumi_outputs.py` 신설)

---

## 9. 변경 이력

| 일자 | 내용 |
|---|---|
| 2026-05-26 | 초안 — frontend 진입 직전 compact 준비. backend 65 tool 완성·정량 17/17·MoM 6·118 tests + 대시보드 계획서 (28 요소·8 컴포넌트·18 endpoint·Step 1-7) + 컨벤션 수정 (features/clumi/ flat + api/hooks/useClumiData.ts) 박제. 다음 = Step 1 Pydantic Output 진입. |
