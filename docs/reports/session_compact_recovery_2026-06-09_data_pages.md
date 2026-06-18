# 세션 컴팩트 복구 — Postgres 인프라 + 분석 6 페이지 실데이터 배선 (2026-06-09)

> 목적: 컨텍스트 압축 후 이어서 작업하기 위한 상태 박제.
> ⚠️ **별도 동시 세션** 복구문서 있음: `session_compact_recovery_2026-06-09.md`(출력/표시 레이어·채팅 시각화) = **다른 작업스트림, 무관**. 본 문서 = 데이터/페이지 배선.
> 이 세션 = **파이프라인 Postgres 활성화 + 분석 6 페이지 실데이터 배선 완료**. 다음 = **채팅 패널·외곽(chrome)·나머지 nav 페이지**.

---

## 0. 한 줄 요약

`.env DATA_BACKEND=postgres` 활성 + **분석 6 페이지(월간결산·대시보드·비용·채널·트렌드·소재) 전부 Postgres 실데이터 배선** 완료. PILOT(하드코딩) 0개. 다음 = **콘텐츠 영역 밖**(우측 AI 채팅 패널·TopBar/Sidebar 외곽·포트폴리오/에이전트/워크플로우/메모리/대화이력/리포트/관찰).

---

## 1. 환경 (변동 없음)

- PostgreSQL `localhost:5432`, pw `root1234`. DB: `octormate_system`(체크포인트)·`octormate_data`(client schema, clumi).
- `.env`: `DATA_BACKEND=postgres` **활성**(raw 읽기·정제/계산 저장 모두 Postgres). gitignore.
- 시작: `uv run python run_server_v2.py`(8001) + `cd frontend && pnpm run dev`(5173).
- ⚠️ **이 세션에 새 엔드포인트 5개 추가 → 백엔드 재시작해야 분석 페이지 실데이터 뜸.**

---

## 2. 이 세션에 한 것

### A. 파이프라인 Postgres 마무리 + 활성화
- ga4 대용량 스트리밍 적재(252MB/95MB, peak 68MB) `16bc314` · P5 네이밍 정합(legacy 39→0) `250c2f9` · `.env` 활성화

### B. /db 콘솔 client 선택 전역 통합 `40a396c`
- DataConsolePage 자체 selector 제거 → 전역(`useCurrentClient`), TopBar 드롭다운 /db서도 표시.
- `_workspace` = 내부 원본 창고(사용자가 편집 가능 유지 선택).

### C. ★ 분석 6 페이지 실데이터 배선 (핵심)
**검증된 4단계 템플릿**: 인벤토리 → 없는 데이터 mock(실측기반) → overview 엔드포인트(`dashboard1.py`) → `useXOverview` 훅 + 페이지.

| 페이지 | 엔드포인트(`/api/dashboard1/`) | 데이터 | 커밋 |
|---|---|---|---|
| 대시보드 | `overview` | 퍼널(노출→클릭→전환→매출)+CTR/CVR/AOV·일별ROAS·목표 | e0d62be·3af6cd2 |
| 비용 | `cost-overview` | KPI·채널비중(C09)·키워드표(T07)·페이싱(campaigns+daily 조인) | 9453672·8d77a18·e93654c·8e295e4·dfc88fc |
| 채널 | `channel-overview` | 채널비교(T05)·스파크라인(daily roas)·목표·3단계퍼널(C06) | 1fb40f7·2781c29 |
| 트렌드 | `trend-overview` | 일별 노출/전환/ROAS 시계열(daily 집계)·목표선 | f607878·2481f7f |
| 소재 | `creative-overview` | 소재표(creatives)·피로(freq≥3.5) | c9ea76c·49eadca |

- **신규 mock 2개만**(실측기반): `data/clumi/raw/marketing_monthly_targets.csv`·`channel_targets.csv`. 소스 등록 SOURCE_REGISTRY 28→**30**(internal 14), 카운트 테스트 갱신(`862d27c`·`1fb40f7`). **data/ gitignore → 로컬 파일**(커밋 안 됨).
- 나머지(퍼널·페이싱·시계열·소재·스파크라인)는 **기존 raw 유도**(daily_performance·orders·campaigns·creatives). "없는 줄 알았는데 있던" 케이스 다수.
- ROAS = **광고성과(전환매출÷광고비)** 기준 통일. 목표 대비 = 실측 vs *_targets raw 비교.

### D. ⚠️ 동시 세션 충돌 (재발 주의)
- **다른 작업스트림이 같은 `main`에서 진행 중**(output 개편·design-system·전환Sprint·main.py `files_router` 추가).
- "전환 Sprint"(`134c3d4`)가 `frontend/src/api/pipelines.ts`(useCategoryResults/vizOutput) **삭제** → 내 cost 배선 빌드 깨짐 → 복구(`a9596b6` 후 살아있는 패턴으로 재배선). **교훈: 같은 파일 동시편집 금지, per-endpoint hook(useMonthlyData식)만.**

---

## 3. 배선 패턴 (다음 페이지도 동일)

```
features/{page}/Page.tsx → api/hooks/useXOverview.ts → GET /api/dashboard1/{x}-overview
   → dashboard1.py (PipelineRunner 조립 + DataSource raw) → Postgres(octormate_data.clumi)
```
- overview 엔드포인트는 전부 `dashboard1.py`에 모음(새 라우트 등록 회피, main.py 동시충돌 회피).
- **DataTable(HTML)은 ChartFrame `responsive` 금지**(recharts 컨테이너→겹침) — 자체 렌더. PacingWidget/FunnelChart = `responsive=false` + 내용 맞춤 높이.

---

## 4. 다음 — 콘텐츠 영역 **밖** (사용자 지시)

지금까지 = 분석 6 페이지(콘텐츠)만. **아직 안 본/배선 안 된:**
1. **우측 AI 채팅 패널**(`features/agent/SideChatPanel.tsx`) — 에이전트 실행은 동작(리뷰 PPT 등). 표시/UX 검토. *(동시 세션이 채팅 마크다운/슬라이드 작업 중 — 충돌 주의!)*
2. **외곽 chrome**: `components/layout/{TopBar,Sidebar,GlobalLayout}.tsx`.
3. **나머지 nav 페이지**(대부분 PILOT/미연결 추정): 포트폴리오·에이전트·에이전트관찰·워크플로우·메모리·대화이력·승인대기(HITL)·리포트.

> 각 영역 **인벤토리 먼저**(실데이터 vs PILOT). `PILOT_`·`Array.from`·`mock` grep으로 빠르게 식별. 분석 6과 동일 4단계.

---

## 5. 즉시 할 일
1. (선택) 백엔드 재시작 후 6 페이지 최종 확인.
2. 다음 영역 **인벤토리** → 배선. **단, 채팅/output 관련은 동시 세션과 충돌하니 그쪽 끝난 뒤 또는 영역 분리.**
3. path-scoped 원샷 커밋(내 파일만), 같은 파일 동시편집 금지.

## 6. 포인터
- 엔드포인트: `backend/api_v2/routes/dashboard1.py`(overview 5종) · 훅: `frontend/src/api/hooks/use*Overview.ts`
- 페이지: `frontend/src/features/{dashboard,cost,channel,trend,creative,monthly}/`
- 외곽/채팅: `components/layout/*` · `features/agent/SideChatPanel.tsx` · nav: `features/navigation/store.ts`
- mock 명세: `docs/_claude/data/대시보드_필요데이터_명세_2026-06-09.md`
- 사용자 방식: 초보자·전문가단일권장·동조금지·객관판단·uv·메모리업데이트 자제·계획서먼저·커밋 내파일만.
