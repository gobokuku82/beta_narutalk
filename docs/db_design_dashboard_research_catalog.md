I have everything I need. The plan doc confirms the §-references used throughout the five researches. Now I'll synthesize the full Korean catalog.

# 데이터 → 대시보드 설계 워크벤치 — 설계 레퍼런스 & 옵션 카탈로그

> 입력 자료: 5개 리서치(A 레퍼런스 도구 · B 레이아웃 · C 지표 스키마 · D 핸드오프 · E 정보구조) 통합
> 근거 계획서: `c:\kdy\Projects\narutalk_upgrade\beta_v0033\docs\db_design_dashboard_workbench_plan.md`
> 성격: **빌드 계획서가 아니라, 사용자가 골라야 할 "선택지 메뉴"** — 7번 결정 포인트에서 같이 정하기 위한 자료.

---

## 1) 한눈 요약 — 우리가 내려야 할 결정 메뉴

이번 워크벤치의 빠진 조각은 **② 지표 설계**다(①데이터/ERD는 완료). 5개 리서치가 공통으로 가리키는 결론은 하나로 수렴한다:

> **지표(metric) = "차트"가 아니라, 한 번 정의해 재사용하는 작은 선언적 객체** = `집계(aggregate) × 칼럼` + `차원[]` + `필터[]` + `시간단위` + `차트힌트`. Looker·Cube·Rill·dbt·Metabase·Power BI 전부 같은 어휘를 쓴다. **그 어휘가 곧 우리 명세 스키마이고, 그대로 쓰면 Claude Code 가 즉시 알아본다.**

골라야 할 6개 결정(상세는 §7):

| # | 결정 | 추천(기본값) | 대안 |
|---|---|---|---|
| D1 | 명세 포맷 (계획 Q1) | **하이브리드**: `dashboard-spec.md`(의도+검증) 안에 JSON 블록 + 형제 `spec.json` | JSON only / MD only |
| D2 | 지표 스키마 깊이 (계획 Q3) | **`base` + `derived{ratio, formula, growth}`** (90% 커버) | 풀 타입(running/share/conversion) |
| D3 | 빌더 입력 방식 | **폼(블록 스테퍼) + "AI가 초안 제안"** + 고급 토글로 자유 SQL | 폼 전용 / 자유 SQL 동등 |
| D4 | 차트 enum 확장 (계획 §5.1) | `line·bar·pie·kpi·table` **+ `bullet`(목표대비) + `heatmap`** + `stacked`/`pivot` 플래그 | 현 5종 유지 |
| D5 | 레이아웃 (계획 Q5) | **`layout: null`** — 지표 목록 + 그룹 라벨만, 픽셀 배치는 Claude Code | 경량 그리드 / 풀 그리드 |
| D6 | 정보구조 (페이지 나누기) | **Option C: 가이드형 허브-앤-스포크** (진행도 + 자유 이동) | 탭(A) / 위저드(B) / 4-surface(D) |

---

## 2) 레퍼런스 도구 — 우리가 훔칠 패턴

| 도구 | 핵심 패턴 | 우리 적용 | 출처 |
|---|---|---|---|
| **Metabase** | "블록 체인" 질의 빌더: 데이터 선택→Join→Filter→**Summarize(집계)**→**Breakout(차원)**→Sort→Limit, 각 단계 미리보기. 지표=저장된 집계 객체 | **지표 빌더 UI의 골격**. 비개발자용 용어 차용: "GROUP BY" 대신 **"Summarize"**, 차원=**"Break out by"** | [query builder](https://www.metabase.com/docs/latest/questions/query-builder/editor) · [metrics](https://www.metabase.com/docs/latest/data-modeling/metrics) |
| **LookML / Cube / Rill / dbt** | measure/dimension/filter(segment)/format을 **이식 가능한 config**로 선언. 어휘가 거의 동일 | **이 어휘를 명세 스키마로 그대로 채택** (가장 큰 한 방). Rill metrics-view YAML이 가장 사람-편집 친화적 | [Cube](https://cube.dev/blog/what-the-heck-is-the-semantic-layer) · [LookML](https://docs.cloud.google.com/looker/docs/reference/param-measure-types) · [Rill YAML](https://docs.rilldata.com/reference/project-files/metrics-views) · [dbt](https://docs.getdbt.com/best-practices/how-we-build-our-metrics/semantic-layer-3-build-semantic-models) |
| **Basedash** | "describe → AI가 지표/차트/레이아웃 생성 → 후속 프롬프트로 다듬기". 사전 모델링 불필요 | **"AI가 지표 초안 제안 → 사람이 수정"** 루프. 빈 폼 금지 | [dashboards](https://www.basedash.com/features/dashboards) · [2026 roundup](https://www.basedash.com/blog/best-ai-data-visualization-tools-compared-2026) |
| **Databricks Genie Code (2026)** | 에이전트가 **measures·dimensions·synonyms·문서**를 제안. Metric Views=중앙 KPI 정의 | 깨끗한 ERD 위에서 **테이블별 후보 지표 자동 제안**의 근거. AI-BI 표준 흐름 | [release notes](https://docs.databricks.com/aws/en/ai-bi/release-notes/2026) · [OSI](https://www.databricks.com/blog/redefining-semantics-data-layer-future-bi-and-ai) |
| **Evidence.dev** | "BI as code": SQL + Markdown 컴포넌트, 버전관리되는 텍스트 명세 | **명세를 리뷰 가능한 텍스트 산출물로** — 우리 ③단계 핸드오프의 원형 | [evidence.dev](https://evidence.dev/) · [docs](https://docs.evidence.dev/core-concepts/syntax) |
| **Hex** | 신뢰되는 **시맨틱 모델(진실의 원천)** 과 탐색 표면을 분리 | **지표 정의(governed)** 와 **대시보드 배치(loose intent)** 를 분리 | [hex BI](https://hex.tech/product/bi/) |
| **Power BI Quick Measures** | DAX 없이 폼으로 지표 생성: 시간지능(YTD/YoY/MoM)·누적·비율·비교 카테고리 | 파생 지표 **친화 메뉴의 카테고리 모델** ("성장률/비율/비중/누적/목표대비") | [quick measures](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-quick-measures) |

**훔칠 패턴 Top 7 (랭크):**
1. 지표=차트 아닌 작은 선언 객체 → 우리 ② + 명세 스키마의 핵심
2. 수렴된 시맨틱 어휘를 그대로(OSI 호환) → 핸드오프가 "그냥 동작"
3. 블록 스테퍼를 지표 빌더로(친근한 라벨 + 단계별 미리보기)
4. AI가 제안, 사람이 수정(빈 폼 금지) — "엑셀러, SQL 모름" 페르소나 디리스크
5. 대화형 보정을 2차 입력 모드로("이걸 지역별로 쪼개줘") — 빌더와 챗이 **같은 지표 객체**를 편집
6. 데이터 모양→차트 닫힌 메뉴 매핑(시간→line, 범주 하나→bar, 단일 수치→kpi). `chart_hint` 로만 저장
7. export = 사람용 Markdown + 기계용 JSON, 버전관리 가능

---

## 3) 대시보드 레이아웃 템플릿 카탈로그

> 이 11종은 **빌더의 "스타터 갤러리"** 로 출시 가능 — 클릭하면 `aggregate/dimensions/sort/limit/chart` 가 미리 채워진 지표가 생성됨(계획 미결 #3 폼 가드레일 직접 해결).
> 가정 데이터: fact=**실적**(measure), dim=**거래처·담당자·품목·년월(time)**.

### 페이지 골격 (전체 배치)

원칙: 읽기 순서 좌→우/위→아래, **가장 중요한 것은 좌상단**, 관련 지표는 묶기, 우겨넣지 않기 ([Klipfolio](https://www.klipfolio.com/resources/articles/dashboard-design), [ThoughtSpot](https://www.thoughtspot.com/data-trends/dashboard-design-examples-best-practices)).

```
L1 "스코어카드-탑" (영업 대시보드 기본형)         L2 "드릴 컬럼" (개요→상세 하강)
┌ KPI ┬ KPI ┬ KPI ┬ KPI ┐                       [ KPI row ]
├─────┴──┬──┴────────────┤                       [ 큰 TREND, full width ]
│ TREND  │  BREAKDOWN     │                       [ breakdown ] [ breakdown ]
│ (line) │  (bar)         │                       [ 상세 PIVOT, full width ]
├────────┴───────┬───────┤
│ TOP-N TABLE    │ TARGET│                       L3 "탭 분할" (감사별/페이지별)
└────────────────┴───────┘                       개요 · 거래처 · 품목 · 담당자
```

### 컴포넌트 템플릿 (용도 · 데이터모양 · 스케치)

| # | 템플릿 | 용도 | 데이터모양(지표매핑) |
|---|---|---|---|
| 1 | **KPI/스코어카드** | 헤드라인 숫자 + 전기 대비 델타 | `SUM(실적)`, dim=[], filter=[현재월], chart=kpi |
| 2 | **추이 line/area** | 시간에 따른 변화(#1 용도) | 1 measure × 1 time dim, chart=line |
| 3 | **막대 bar** | 범주별 비교·랭킹(라벨 길면 가로) | `SUM(실적)` × [품목], chart=bar, sort=desc |
| 4 | **누적막대 stacked** | 합계 + 구성 | × [년월, 품목], chart=bar(stacked) |
| 5 | **랭킹/Top-N 테이블** | "누가 1등" 정확값+정렬 | dim+sort=desc+limit=N, chart=table |
| 6 | **불릿(목표 대비)** | "할당 달성?" — 다수 KPI엔 gauge보다 불릿(1/8 공간) | 실적 vs 목표/행, chart=**bullet** |
| 7 | **MoM/YoY 증감** | 전기 대비 성장 | 동일 measure, 두 시간필터, Δ% |
| 8 | **파이/도넛** (절제) | 부분-전체, **≤6~7 조각, 단일 스냅샷** | 작은 cardinality dim, chart=pie |
| 9 | **피벗/매트릭스** | 두 차원 동시·정확값(엑셀 피벗) | 1 measure × 2 dims, chart=table(pivot) |
| 10 | **히트맵** | 두 범주 격자에서 강도 패턴 | 1 measure × 2 dims→color, chart=**heatmap** |
| 11 | **코호트/리텐션** | 첫 거래월 그룹의 재구매(파생계산 필요) | cohort dim × period-offset × retention |

```
#1 KPI          #2 추이             #3 막대                #6 불릿(목표대비)
┌─────────┐    매출┤   ╭─╮         품목A ████████ 420    담당자A ▏░░██████│░░ ◆
│ 총매출   │       │╭─╯ ╰╮        품목B █████ 280       담당자B ▏░░███│░░░░░ ◆
│ ₩1.2B ▲8%│      └┴──┴──→년월    품목C ███ 175

#9 피벗                         #10 히트맵           #11 코호트
        1월  2월  3월  합계            1월 2월 3월     코호트  M0 M1 M2 M3
A상사   120  140  160  420     담당자A ░  ▒  █     2024-01 █  ▓  ▒  ░
B유통    90   95  100  285     담당자B █  ▓  ▒     2024-02 █  ▓  ▒
합계    210  235  260  705     (진할수록 매출↑)    2024-03 █  ▒
```

**빌더에 박을 차트 선택 규칙:** 시간→line(#2) · 범주→bar(#3) · 부분-전체→stacked(#4)>pie(#8, ≤7) · 누가-1등→table(#5) · 목표대비→bullet(#6) · 전기대비→delta(#7) · 두차원 정확→pivot(#9)/패턴→heatmap(#10) · 생애주기→cohort(#11). ([ThoughtSpot 차트가이드](https://www.thoughtspot.com/data-trends/data-visualization/types-of-charts-graphs))

> **차트 enum 갭(계획 §5.1):** 현 `line|bar|pie|kpi|table` 에 **`bullet`(목표/실적) + `heatmap`** 추가 필요. stacked·pivot 은 bar/table의 `stacked`/`pivot` 불리언 플래그로.
> 참고 갤러리: [Coupler](https://www.coupler.io/dashboard-examples/sales-analytics-kpi-dashboard) · [Qlik](https://www.qlik.com/us/dashboard-examples/sales-dashboards) · [불릿](https://www.cleanchart.app/blog/how-to-create-bullet-chart) · [코호트](https://docs.holistics.io/docs/charts/cohort-retention)

---

## 4) 지표(metric) 패턴 카탈로그 + 제안 스키마

### 모든 시맨틱 레이어가 동의하는 지표 골격

| 개념 | LookML | Cube | dbt | Malloy | Power BI |
|---|---|---|---|---|---|
| 계산할 숫자 | measure | measure | metric | measure | measure(DAX) |
| 집계 방식 | `type:` | `type:` | `agg:` | agg func | DAX agg |
| 대상 칼럼 | `sql:` | `sql:` | `expr:` | col ref | col ref |
| 묶음 축 | dimension | dimension | group_by | dimension | visual cols |
| 조건 | filtered measure | `filters:` | `filter:` | `where:` | CALCULATE |
| 시간 단위 | timeframes | granularity | agg_time_dim | timeframe | Date grain |

### A. 베이스 집계 타입 (칼럼 → 숫자)

`count` · `count_distinct` · `sum` · `avg` · `min` · `max`(보편 6종) · `median` · `percentile`(p90 등). **fan-out 경고**: 1:N 조인 너머 칼럼을 sum/avg하면 중복집계 — 우리 지표는 ERD FK 조인 위에 앉으므로 부드러운 경고 필요. ([LookML 타입](https://docs.cloud.google.com/looker/docs/reference/param-measure-types))

### B. 파생/복합 타입 (지표 → 지표) — **계획 §5.1이 빠뜨린 가장 큰 가치**

| 타입 | 정의 | 예시 |
|---|---|---|
| **Ratio** | 분자지표 ÷ 분모지표 | 전환율, 객단가=매출÷주문수 |
| **Derived/formula** | 지표들에 대한 임의 식 | 마진=매출−비용 |
| **Growth(시간비교)** | 지표 vs 이전 기간 | MoM/YoY 성장률 |
| **Running/cumulative** | 시간창 누적 | 누적매출, YTD, 7일 이동평균 |
| **Share of total** | 행값 ÷ 총계 | 거래처별 매출 비중% |
| **Target vs actual** | 실적 vs 목표 | 달성률=실적÷목표 |

핵심 재사용 패턴 — **성장 지표 = 베이스 지표 + 시간 오프셋 + 비교연산**. dbt가 `offset_window`로 선언적 처리(DAX `SAMEPERIODLASTYEAR` 대비 훨씬 쉬움). → **"이 지표의 성장률(MoM/YoY)" 원클릭 토글**로 제공. ([dbt derived](https://docs.getdbt.com/docs/build/derived) · [cumulative](https://docs.getdbt.com/docs/build/cumulative))

### 제안 최소 지표 스키마 (계획 §5.1 정제)

설계 목표: ①비개발자가 폼으로 채움 ②모든 필드가 **ERD 칼럼 드롭다운**에 바인딩(자유 텍스트 아님) ③§6 핸드오프로 라운드트립.

```jsonc
// ── BASE METRIC (카탈로그 A 전부 커버) ──
{
  "id": "m_sales_by_account",
  "name": "거래처별 월 매출 추이",
  "kind": "base",                      // "base" | "derived"  ← A/B 분리 (폼을 두 흐름으로)
  "sourceTable": "실적",                // ERD 테이블 id
  "aggregate": "SUM",                  // SUM|COUNT|COUNT_DISTINCT|AVG|MIN|MAX|MEDIAN|PERCENTILE
  "measureColumn": "실적",              // ERD 칼럼 (COUNT면 생략)
  "dimensions": [
    { "column": "거래처ID" },
    { "column": "년월", "timeGrain": "month" }   // day|week|month|quarter|year
  ],
  "filters": [ { "column": "년월", "op": ">=", "value": "202401" } ],
  "joins": [ { "fk": "실적.거래처ID → 거래처.거래처명" } ],   // ERD-FK 기반 (라벨용)
  "chart": "line",                     // line|bar|pie|kpi|table|bullet|heatmap
  "sort": { "by": "measure", "dir": "desc" },
  "limit": null,
  "format": "currency"                 // number|currency|percent|humanize
}

// ── DERIVED METRIC (카탈로그 B 전부 커버) ──
{
  "id": "m_sales_yoy",
  "name": "매출 YoY 성장률",
  "kind": "derived",
  "subtype": "growth",                 // ratio | formula | growth | running | share | target
  "inputs": ["m_sales_by_account"],    // 다른 지표 id 참조
  "expr": "(A - A_prev) / A_prev",     // inputs 위 화이트리스트 문법
  "offsetWindow": { "n": 1, "grain": "year" },
  "chart": "kpi",
  "format": "percent"
}
```

선택 근거 요약: `kind:base|derived`=보편적 "집계 measure vs 지표-위-지표" 분리(폼을 두 단순 흐름으로 → "한 페이지 우겨넣기 방지"). `RATIO`는 base enum에서 **제외**하고 derived로(sum-of-ratios 평균 오류 방지). `timeGrain`=모든 도구가 시간을 단위 선택 차원으로. `offsetWindow`=dbt에서 직수입, DAX 없이 MoM/YoY. `subtype`=Power BI quick-measure 카테고리와 1:1 → 친근 메뉴. 모든 필드가 ERD id에 바인딩.

**v1 권장 범위(계획 Q3):** `base` + `derived{ratio, formula, growth}` = 비즈니스 대시보드의 ~90%(합계·분해·전환율·YoY·마진). running/share/conversion은 요청 시까지 보류. **자유 SQL 탈출구**: 선택적 `rawSql`을 "고급" 토글 뒤에 숨김(가드레일 UX 훼손 방지).
([Cube measures](https://docs.cube.dev/reference/data-modeling/measures) · [Malloy](https://docs.malloydata.dev/documentation/user_guides/malloy_by_example) · [Power BI quick measures](https://learn.microsoft.com/en-us/power-bi/transform-model/desktop-quick-measures))

---

## 5) 명세→코드 핸드오프 포맷 제안

### 포맷 선택 메뉴 (계획 Q1)

| 옵션 | 장점 | 단점 | 판정 |
|---|---|---|---|
| **JSON/YAML only** | 명확·검증가능·ID 교차참조(Superset/Cube/Grafana) | 순수 구조화 출력은 LLM 추론 ~10–15% 저하, **의도("왜")** 가 빠짐 | 필요하나 불충분 |
| **Markdown only** | 자연어 의도 최고, Claude Code 네이티브 소비(CLAUDE.md/SPEC.md), 리뷰 용이 | 정밀부(칼럼명·FK방향·집계타입) 모호 | 최고 래퍼, 약한 골격 |
| **하이브리드 ✅** | prose=의도/흐름(정확도↑) + fenced JSON=정밀 계약(드리프트 없음), 한 파일 | 약간의 생성 로직 | **권장** |

근거: 순수 JSON은 의도(코드젠 정확도 최대 레버)를 굶기고, 순수 prose는 칼럼명·FK 드리프트. GitHub Spec Kit·Anthropic best-practice 모두 **prose 본문 + fenced JSON 계약 + Given/When/Then 예시** 권장. ([Schema RL arXiv 2502.18878](https://arxiv.org/pdf/2502.18878) · [GitHub spec-driven MD](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-using-markdown-as-a-programming-language-when-building-with-ai/) · [Claude Code best practices](https://code.claude.com/docs/en/best-practices))

### 권장 산출물 — 단일 `dashboard-spec.md` (고정 섹션 순서)

```markdown
# 대시보드 설계 명세 — <Dashboard Name>

## 0. 핸드오프 지시 (READ FIRST)   ← prose: Excel 작성자, 이 명세가 INTENT의 진실원천,
   빌드 순서(DDL 실행→지표=SQL→차트 렌더→조립), 타겟스택, 모호하면 §1 의도 우선

## 1. 의도/맥락 (INTENT — 자연어)   ← 2~6문장: 누가·무슨 결정·"좋음"의 정의
   예) "영업팀장이 거래처별 매출 추세를 매월 점검, 하락 거래처를 빨리 찾기 위함"

## 2. 데이터 구조 (ERD) — contract   ```json { "tables":[...], "fk":[...] } ```
## 3. DDL — ready to run            ```sql CREATE TABLE ... ```
## 4. 지표 (METRICS) — contract      ```json [ {id, name, sourceTable, measure, aggregate,
   dimensions[], filters[], joins[{relationship}], chart, sort, limit, sqlDraft, intent} ] ```
## 5. 대시보드 (composition)         ```json { name, metrics:[ids], layout:null } ```
## 6. 검증 기준 (Given/When/Then)    ← 에이전트 self-check + "재생성 테스트"
```

핵심 결정:
- **`id` 모든 지표에 + 대시보드는 id 참조** → 안정적 교차참조(Superset UUID 교훈), 재export 깔끔한 덮어쓰기.
- 지표 필드명은 **Cube/MetricFlow 어휘 차용**(`measure`/`aggregate`/`dimensions`/`timeGrain`/`joins.relationship`) → Claude Code가 즉시 인식.
- **`sqlDraft` per metric**: 우리가 이미 §5.3에서 생성하는 SQL 초안을 동봉 → "쿼리 추측"을 "이 쿼리 검토"로 전환.
- **`layout: null` 기본**(계획 Q5) → 픽셀 배치는 Claude Code.
- **두 산출물 동시 emit**: `dashboard-spec.md`(주, 붙여넣기용) + `spec.json`(형제, 프로그램 재import용). `.md`가 `.json` 블록을 *포함*하므로 절대 어긋나지 않음(json 먼저 생성 후 md 렌더).

구현 노트: `spec.json`에 **JSON Schema** 제공(유효성+라운드트립), 의도는 JSON 문자열로 우겨넣지 말 것(추론 저하), 단일 파일 co-locate, **용어 1개념=1단어**(지표=metric, 차원=dimension) UI/prose/JSON키 동일. 성장경로: 지표 JSON은 Cube YAML의 준-상위집합 → "Cube 모델로 export" 버튼 거의 공짜.
([Evidence](https://docs.evidence.dev/core-concepts/syntax) · [Superset](https://superset.apache.org/admin-docs/configuration/importing-exporting-datasources/) · [Grafana JSON](https://grafana.com/docs/grafana/latest/visualizations/dashboards/build-dashboards/view-dashboard-json-model/) · [Cube joins](https://cube.dev/docs/product/data-modeling/reference/joins) · [dbt semantic models](https://docs.getdbt.com/docs/build/semantic-models) · [Spec Kit](https://github.com/github/spec-kit))

---

## 6) 정보구조(IA) 옵션 — 페이지/단계 나누기

세 가지 일: ①데이터 이해(완료) · ②지표 설계(다음) · ③명세 산출. 흐름 성격 = **드물게, 순차적이되 재방문 가능, 저장되는 문서 산출** → 이 조합이 IA를 결정.

| 옵션 | 구조 | 장점 | 단점 | 비개발자 적합 |
|---|---|---|---|---|
| **A. 단일 페이지 탭** (데이터/지표/대시보드 탭) | 1 URL, 3 탭 | 빌드 최저(현 페이지 재사용), 작업기억에 전체, ERD↔지표 전환 쉬움 | NN/g: 탭은 완료상태·순서 미표시 → "다 했나?" 모호. ②③ 커지면 "우겨넣기" 위험 | ⚠️ 중 |
| **B. 3-페이지 위저드** (`/data`→`/metrics`→`/export`) | 지속 스테퍼 헤더 | **초보+드문 작업 최적**(NN/g 정확 권장), 각 페이지 단순, 의존성 강제 | 위저드는 경직: 클릭비용↑, ERD로 점프 어려움, **나쁜 중단성** — ERD↔지표 반복 현실과 충돌 | ✅ 첫회 / ⚠️ 반복시 |
| **C. 가이드형 허브-앤-스포크 ✅** | 프로젝트 허브 + 3 스포크, 진행도 표시하되 자유 클릭, 지표 페이지에 ERD 미니맵 | 위저드의 *가독성*(진행도·추천경로) + 허브의 *자유*. ERD↔지표 반복 지원, ERD 컨텍스트 상시(§5.3), ②확장 시 깔끔, 명세=영속 허브 산출물 | A/B보다 빌드↑(허브뷰+교차상태+autosave), 가르칠 개념 약간↑ | ✅✅ 최선 |
| **D. Metabase식 4-surface** (데이터·모델·지표·대시보드) | 모델 표면 별도 분리 | 관심사 최청결, 각 지표 독립 재사용, 진짜 BI 미래대비 | **현 범위 과설계** — 계획에 없는 "모델" 개념(현 §5.1은 조인을 Metric 안에), 빌드비용·내비 최고 | ⚠️ 현재 낮음 |

**추천: Option C (가이드형 허브).** 사용자 두 제약("한 페이지에 우겨넣지 말 것" + 비개발자 친화)을 동시 만족, **ERD와 지표가 반복 공동편집**되는 기술 현실 존중, 산출물의 문서 성격(1 프로젝트=1 명세, autosave)과 일치.

매핑: 허브=프로젝트/명세 개요(③ export가 허브의 "완료" 상태) · 스포크1=데이터(기존 `/db-design`, ① 완료체크 "테이블≥1+FK") · 스포크2=지표 빌더(**ERD 사이드 미니맵**) · 스포크3=명세 export.

근거: NN/g 위저드(초보/드문 셋업, 단 경직·나쁜 중단성) · Boxes&Arrows **"Guide"=위저드 순서 + 허브 자유**(우리 스윗스팟) · Metabase 4표면 분리 · 스테퍼 3~6단계, 항상 뒤로/편집 허용. ([NN/g 위저드](https://www.nngroup.com/articles/wizards/) · [Boxes&Arrows](https://boxesandarrows.com/wizards-and-guides/) · [Metabase Models](https://www.metabase.com/learn/metabase-basics/querying-and-dashboards/models) · [GitLab autosave](https://design.gitlab.com/usability/saving-and-feedback))

---

## 7) 결정 포인트 (대화용)

아래 7개에 답(또는 "추천대로")하면 Phase 1 구체 설계로 진입.

**Q1 — 명세 포맷(계획 Q1).** 추천: **하이브리드** (`dashboard-spec.md` + 형제 `spec.json`).
→ JSON only / MD only 중 더 끌리는 게 있나요, 아니면 하이브리드로 갈까요?

**Q2 — 지표 스키마 깊이(계획 Q3).** 추천: **`base` + `derived{ratio, formula, growth}`** (90% 커버, running/share/conversion 보류).
→ v1에 누적(YTD)·비중·코호트까지 넣을까요, 아니면 나중에?

**Q3 — 빌더 입력 방식(계획 Q3).** 추천: **폼(블록 스테퍼) + "AI가 지표 초안 제안"** + 고급 토글의 자유 SQL.
→ "AI가 테이블별 후보 지표 제안" 기능을 v1에 넣을까요? 자유 SQL은 숨김 토글로 충분한가요?

**Q4 — 차트 enum(계획 §5.1).** 추천: 현 5종 + **`bullet`(목표대비) + `heatmap`** + `stacked`/`pivot` 플래그.
→ 목표 대비(불릿)를 v1 핵심으로 볼까요? 그러면 **목표 테이블/값** 입력 경로도 필요합니다(원천 실적엔 없음).

**Q5 — 레이아웃(계획 Q5).** 추천: **`layout: null`** — 지표 목록 + 그룹 라벨만, 픽셀 배치는 Claude Code. (옵션: 경량 그리드 `{row,col,w,h}`)
→ 이번엔 배치를 다루지 말까요, 아니면 그룹 라벨/탭 수준의 경량 힌트만 넣을까요?

**Q6 — 정보구조.** 추천: **Option C(가이드형 허브)**. (대안: 빠른 출시면 A 탭, 단순 초보면 B 위저드)
→ 명세를 **autosave/resume 되는 "프로젝트"** 로 볼까요, 단일 라이브 문서로 볼까요? (이게 허브 필요 여부 = A↔C를 가름)
→ 첫 실행만 위저드 오버레이(B 느낌) 후 허브(C)로 떨어지는 하이브리드도 가능합니다.

**Q7 — 모델 표면(미래 대비).** 추천: 당분간 **조인을 각 Metric 안에 유지**(현 §5.1), 별도 "모델" 표면(Option D)은 보류.
→ Phase 3/4(DB introspection, 런타임 질의)를 앞당길 계획이 있으면 지금 4-surface를 고려할 가치가 있습니다 — 그럴 의향이 있나요?

---

근거 계획서 위치: `c:\kdy\Projects\narutalk_upgrade\beta_v0033\docs\db_design_dashboard_workbench_plan.md` (§5.1 지표 모델 · §6 핸드오프 · §9 미결질문이 위 D1~D6/Q1~Q7과 직접 대응).