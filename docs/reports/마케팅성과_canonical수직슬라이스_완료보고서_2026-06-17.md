# 완료보고서 — 마케팅 성과 페이지 (canonical 수직 슬라이스)

> 2026-06-17 · 계획서 [frontend_마케팅성과_수직슬라이스](../_claude/plans/frontend_마케팅성과_수직슬라이스_2026-06-17.md) 실행.
> World-A canonical 정형 테이블을 **처음으로 화면까지 end-to-end 연결**한 첫 수직 슬라이스.

## 1. 무엇을 했나
`clumi.blended_computed·*_normalized` → **신규 읽기 API** → **신규 프론트 페이지**의 3단 관절을 완성:
- **백엔드 읽기 API** `GET /api/canonical/marketing-performance?client=&period=` — asyncpg 풀로 정형 테이블 직접 SELECT·집계(dashboard1 `_cached_or_run` 구 경로 미사용). 신규 namespace `/api/canonical/*`.
- **프론트 페이지** `/marketing-performance` (분석 그룹 탭) — KPI strip(MER·총비용·총매출·TACoS) + 채널별 광고비 bar + 일별 ROAS line + 광고 매체 성과 표 + 메시징 성과 표(분리).

## 2. 왜 이렇게
- **새 DB에 맞춰 새로 신축**(오너 지시) — 기존 dashboard1 페이지(World-B `_workspace` 캐시)는 미접촉. 기존 컴포넌트(KpiCard·ChartFrame·DataTable·PageHeader)·훅 패턴(useMonthlyData)·디자인 토큰은 **참고·재사용**.
- **읽기 경로 = asyncpg** (`data_console.py` 패턴, convention) — async 라우트에서 sync `connect()` 블로킹 회피. 구 캐시 경로 미답습.
- **광고(ROAS)·메시징(ROI) 분리**(C6.3) — 표·라벨에서 명시 분리, 동일 축 비교 금지 주석.
- **채널 ROAS = Σ전환매출 ÷ Σ광고비**(집계 후 비율, 행 평균 아님) — 기존 `_compute` 공식 재사용(메트릭 발명 0).

## 3. 변경표
| 구분 | 파일 |
|---|---|
| 백엔드 신규 | `backend/app/schemas/outputs/canonical.py`(응답모델) · `backend/api_v2/routes/canonical.py`(라우터) · `backend/tests/canonical/test_marketing_performance.py`(테스트 4) |
| 백엔드 수정 | `api_v2/routes/__init__.py` · `api_v2/main.py`(canonical_router 등록) |
| 프론트 신규 | `features/marketing-performance/types.ts`(Zod) · `MarketingPerformancePage.tsx` · `api/hooks/useMarketingPerformance.ts` |
| 프론트 수정 | `routes/router.tsx`(route) · `features/navigation/store.ts`(탭) · `components/layout/Sidebar.tsx`(Target 아이콘) |

## 4. 검증 수치
- **백엔드 테스트 4 passed**(live clumi): ★KPI `total_marketing_cost=18,306,923`·`MER 6.53` 재현(교차세계 정답) · 채널 ROAS=Σrev/Σcost 결정성 · 메시징 분리(ad_channels에 msg 누설 0) · KPI↔채널합 정합 · 일별 광고비 합 == 총광고비.
- **전체 회귀 991 passed** / 2 skipped / pre-existing 5(parquet env·DC_PERM_6·o04 — 무관).
- **프론트 `tsc --noEmit` 통과**(타입 에러 0). full app에 `/api/canonical/marketing-performance` 라우트 등록 확인.

## 5. 다음
- **수동 스모크**: dev 서버(FE 5173 → /api 프록시 8001)에서 `/marketing-performance` 렌더·수치 확인(오너 시각 검수).
- **확장**: 회원/프로모션/세그먼트 도메인 페이지(해당 raw canonical 피봇 선행) · 전역 period 셀렉터 · 캠페인 드릴다운(`*_computed` 행 활용).
- **cutover(후속)**: 도메인 다 옮긴 뒤 구 dashboard1 페이지 폐기 + C-2(구 serving 캐시) 정리.
