# 완료보고서 — stub 처분 1차: trend_analyzer·competitor_comparator 폐기

> 일자: 2026-06-12 · 커밋: `271ec8d`
> 분류: 카탈로그 정리 (헌법 I1 — mock "되는 척" → 정직 degrade "안 된다고 말함")
> 오너 결정: 방향 = **"구현 가능한 건 구현하면서 줄이자"** + 2종 즉시 폐기 후 재검토

## 1. 무엇을 왜

stub tool 17종 중 분석 계열 2종을 카탈로그 메뉴에서 제거. 메뉴에 없으면 planner가 선택 불가 → 해당 능력 요청은 가짜 mock 결과(고정 12.5%·"감성/가격 우위") 대신 정직 degrade로 응답.

**★오너 도메인 정정 (영구 보존 — spec 32 §7.1 + 메모리)**:
- `trend_analyzer` = **트렌드 분석** — forecaster(예측)와 **다른 개념**. "forecaster가 대체한다"는 1차 분석의 분류는 오답이었음.
- `competitor_comparator` = **A/B 테스트 분석 tool** (일반 경쟁사 비교 아님) — 단일 tool 구현이 어려워 폐기 후 재검토.

재구현 조건: 헌법 §7 채용 3문항 + **계산 방법은 오너 제공**(정제·계산 임의 생성 금지 원칙).

## 2. 변경 내역 (짝 단위)

| 지점 | 내용 |
|---|---|
| team_catalog.yaml | stub 엔트리 2 제거 + 묘비(도메인 정의 포함) — 108→**106** (implemented 91 / stub 15) |
| mock_tools.py | 두 분기 제거 — 고정 가짜 숫자의 무표기 답변 유입 경로 봉쇄 |
| spec 10 | analysis_agent 도구 표를 실상태로 (diagnoser/forecaster/insight_extractor) |
| spec 32 §7.1 신설 | 폐기 기록 + 도메인 정의 + 재구현 조건 로드맵 |
| 메모리 | project_stub_tool_definitions — 다음 세션이 같은 오분류 반복 방지 |

부수 효과: 두 stub의 `cleaned_texts` params가 subject-coherence 게이트의 리뷰-tool 오분류를 유발하던 함정(06-11 분석 low 이슈) 자동 해소.

## 3. 검증

YAML 파싱 OK · 카탈로그 카운트 106=91+15 실측 · 전체 회귀 **869 통과**(실패 16 = 사전 존재 동일 목록, 신규 파손 0). 코드·테스트의 두 tool 참조 0 확인(ADR·POC_legacy의 역사 기록만 보존).

## 4. 잔여 stub 15종 — 다음 처분 결정 대기 (오너)

| 그룹 | tool | 권고 |
|---|---|---|
| 차트 1 | chart_generator | **구현 후보 1순위** — 보고서(PDF) 시각화 경로와 직결, matplotlib로 구현 가능. 단 차트 종류·스타일은 오너와 협의 |
| 렌더 확장 5 | template_selector, word/excel_template_filler, slide_designer, chart_to_slide | 수요 측정 대기 (G-질문에 없음) — 폐기 또는 보류 |
| 크리에이티브 9 | image_generator, image_resizer, thumbnail_creator, storyboard_creator, video_image_generator, slogan_writer, copy_generator, material_modifier, variation_generator | **폐기 권고** — 외부 API+비용+제품 결정 필요 = 새 제품 영역. 메뉴 제거 후 spec 32 로드맵만 보존 |

병행 필수(어느 처분이든): **슬라이스 2-② mock 표기** — 남는 stub 산출에 "예시(mock) 기반" 라벨(H2).
