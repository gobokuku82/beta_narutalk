# P2 — _schema.yaml taxonomy drift 봉합 완료보고서 (2026-06-18)

> 상위 = [tool 심층감사 §4](tool구조_심층감사_카테고리_프롬프트_layer_2026-06-18.md) P2 · [ROADMAP A-7](../_claude/ROADMAP.md). census = 워크플로 `w4s3cujaz`(4트랙 병렬 실측 + 적대 synthesis, 250k tok).
> **한 줄**: 감사가 "3중 drift 봉합 8→10~11"로 적은 P2를 실측한 결과 — **실제는 단일 drift(주석 stale)였고, 정본 enum은 이미 11**. 같은 stale 주석 3곳을 정본(11)으로 일괄 정정. **doc_only·코드영향 0·신규실패 0.**

## 1. 무엇을 (What)
tool 카테고리 taxonomy의 **stale 문서 주석 3곳**을 정본(`enums.py ToolCategory` 11 멤버)에 맞춰 정정:
- `tools/catalog/_schema.yaml:20-22` — "8 카테고리" → 11 (데이터 단계축 8 + 비단계축 rendering·qa·decision 3)
- `tools/registry.py:75` — "박제 8 카테고리 정합" → "정본 enums.py ToolCategory 11 멤버"
- `models/enums.py:24` — Status "= 9" → "= 11" (qa·decision 누락 표현 정정)

## 2. 왜 (Why) — 실측이 감사 프레이밍을 정정
- 감사 표현 "_schema 8 ↔ 디스크 11 ↔ team_catalog 3" **3중 drift는 부정확**(census 확증): team_catalog는 카테고리가 1급 키가 아니라 **Team→Agent→Tool 축**이고 카테고리는 *주석에만* 등장(team_catalog.yaml:5,28). 라우팅은 category가 아니라 **TaskType↔agent**(planner.py:653·691). → 실제 drift = **_schema 주석(8) vs 현실(11)** 단일축.
- **정본 = `enums.py:30-42` ToolCategory enum — 이미 11 멤버**(RENDERING·QA·DECISION 포함). decision/qa/rendering tool은 **오늘 이미 로드·테스트 통과**. `_schema.yaml`은 registry가 `_` 파일 skip(registry.py:52)이라 **애초에 파싱 안 됨** → 그 8-목록은 순수 stale 주석.
- 즉 P2는 "3소스 정합"이 아니라 **"이미 정확한 enum에 문서가 못 따라온 것을 catch-up"**. 봉합 = 같은 사실(카테고리 수)이 잘못 적힌 3곳을 모두 정정(부분 정정 시 다음 독자 재혼란).

## 3. 변경표 (전부 주석/docstring — 코드 로직 0)
| 파일 | before | after |
|---|---|---|
| `tools/catalog/_schema.yaml:20-22` | "33/* 박제 8 카테고리" + 8 나열 | "정본=enums.py 11" + 단계축 8 / 비단계축 3 분리 나열 |
| `tools/registry.py:75` | "박제 8 카테고리 정합" | "정본 = enums.py ToolCategory 11 멤버" |
| `models/enums.py:24` | "8 분석 단계 + rendering = 9" | "단계축 8 + rendering + qa·decision = 11" |

## 4. 검증 수치
- **census 실측**(서브에이전트 grep을 직접 Read로 재확인): enum 11 멤버(enums.py:30-42)·registry 단일 검증 `ToolCategory(category_str)`(registry.py:84)·_schema 미파싱(registry.py:52)·11 디렉토리 전부 `dir_name==declared_category`(drift 0).
- **registry 로드 smoke**: 92 tool 로드·카테고리 분포 `{analysis 11, cleaning 3, collection 22, comparison 7, decision 1, metrics 35, normalization 6, preprocessing 1, qa 1, rendering 3, report 2}` = census 정확 일치. _schema.yaml 여전히 valid YAML.
- **전체 회귀 1038 passed**(S2-ext와 동일)·**신규실패 0**(pre-existing 10 불변). adding_3_breaks=false 확증.

## 5. 부수 발견 (catalog_code_drift, P2 외)
- census가 같은 "8 카테고리" stale를 3곳에서 발견 → 3곳 다 정정(완전 봉합). 그 외 코드 drift 0(11 dir 전부 dir명==선언 category).
- **오분류 회수(P4) 대상 = 본 census 기준 0건** — 디스크 11 dir 전부 선언 category 일치(drift 0). 단 P4는 "카테고리 *내부* 오분류"(예 metrics에 정제룰 위장)라 별개 — census는 dir↔category 일치만 확인, dir *선택*의 적정성은 P4에서.

## 6. 정직 경고
1. **doc_only** — 동작·테스트 무변경. "기능 개선"이 아니라 **문서 정합 catch-up**. (감사가 "8→10~11"로 키운 것보다 실제 작업은 작았음.)
2. **카테고리 *의미*는 오너 도메인** — rendering/qa/decision 정의는 이미 enums.py docstring + 설계서(질의응답/의사결정_260610)에 오너 박제. P2는 그 반영일 뿐 신규 결정 0. 새 카테고리 신설·의미 변경은 P2 범위 밖.
3. **남은 P3·P4는 실제 코드/계약 영향** — P4(오분류 회수)는 카테고리 이동→planning 라우팅 영향(파일럿·회귀), P3(consumes 일원화)는 catalog_code_drift 실측. P2(doc_only)와 위험도 차원이 다름.

## 7. 다음
- **P4 오분류 회수** (metrics 35 비대 — 정제 위장 tool을 cleaning으로·grade_timeseries→metrics·review_normalizer→text) — ⚠ 카테고리 이동은 enum/team_catalog/라우팅 영향 → data_pilot 검증 후.
- **P3 consumes per-tool catalog 일원화** — ⚠ catalog_code_drift 실측 대조.
- (P5 보류: ai_recommendation/recommender 출력키 통일·output persist 계약 = 오너 결정/DB 재구축 시점.)
