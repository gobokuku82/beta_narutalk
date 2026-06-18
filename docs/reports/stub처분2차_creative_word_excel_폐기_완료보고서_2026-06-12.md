# 완료보고서 — stub 처분 2차: creative_team 전체 + word/excel 렌더 폐기

> 일자: 2026-06-12 · 커밋: `6735724` (12파일, +93/−263)
> 오너 결정: 크리에이티브 9 폐기 / word·excel_template_filler 폐기 / template_selector·slide_designer·chart_to_slide 는 정체 확인 후 결정

## 1. 무엇을

**11종 폐기** — creative_team **팀 전체**(agent 4 + stub 9) + word_template_filler + excel_template_filler(전속 agent excel_agent 동반). 카탈로그 106→**95** (implemented 91 / **stub 4**).

핵심 원칙: mock "되는 척" → 정직 미지원. **TaskType(image_generation 등)은 언어 레이어에 보존** — cognitive가 의도를 *인식*해야 "미지원입니다" 정직 응답이 가능하기 때문(인식 못 하면 모호 쿼리로 오분류됨).

## 2. 짝 단위 동기 갱신 (반쪽 철거 방지)

| 지점 | 내용 |
|---|---|
| team_catalog | creative_team 블록(80줄) + word/excel 엔트리 + 힌트 5종 + report_generation 3갈래화 + 헤더/설명 정정 |
| **프롬프트 3장** | stage1: "크리에이티브 → 미지원, teams_selected에 포함 금지" 규칙 + few-shot 교체 / stage2: excel→텍스트 정직 규칙, creative 블록·few-shot 제거 / stage3: output_format 분기 정정 + creative few-shot 제거 |
| mock_tools / executor | 크리에이티브 mock 분기 9 + 요약 분기 4 삭제 — 가짜 이미지 경로·슬로건이 답변에 유입되던 경로 봉쇄 |
| 테스트 | test_d1(구 excel 분리 박제) → **의도적 반전**: S2-1 팀 3 / S2-2 폐기 13종 부재 / S2-3 힌트 3갈래 / **S2-4 잔여 stub 정확히 4종** — 처분 결정 없는 stub 추가/누락 시 RED (채용 기준의 기계 가드) |
| spec 10/14/32 | 팀 트리·agent 표·Stage1 서술 정정 + 32 §7.1 처분표 확장 (+14의 SessionManager 잔존 표기도 정리 — Sprint ① 누락분) |

## 3. 검증

YAML 파싱 + 카탈로그 카운트(팀 3 / 95 = 91+4) 실측 · 전체 회귀 **869 통과** (실패 16 = 사전 존재 동일, 신규 파손 0).

행동 변화: "이미지 만들어줘" → (구) mock 경로 `/mock/..._image.png`가 결과인 척 → (신) stage1이 팀 미선택 → 빈 plan 정직 경로. ※빈 plan의 종착이 현재 PLANNING_EMPTY_PLAN fatal("Todo 미생성")이라 문구가 아직 거칠다 — **슬라이스 2-①(모호/미지원 정직 종착 일원화)**이 "크리에이티브는 아직 미지원" 친절 응답으로 다듬을 예정.

## 4. 잔여 stub 4종 — 확인 요청하신 3종의 정체

| tool | 무엇인가 (카탈로그 정의 기준) | 비고 |
|---|---|---|
| `chart_generator` | 분석 결과 → 차트 PNG 생성. produces `chart_image_paths` | **구현 후보 1순위** (기결정 대기) |
| `template_selector` | PDF 보고서의 **템플릿(브랜드 컬러·레이아웃) 선택** 단계. produces `template_choice` | ⚠️ 산출 소비자가 word/excel filler였음 — **둘이 폐기되며 소비자 0** (pdf_renderer는 template를 안 받음). 사실상 동반 폐기가 논리적 |
| `slide_designer` | pptx_generator가 만든 PPT에 **시각 디자인(레이아웃·색·폰트, 브랜드 컬러) 후처리**. pptx_file_path → designed_pptx_path | PPT 꾸미기 단계 — python-pptx로 구현 가능하나 디자인 규칙(브랜드 가이드) 필요 |
| `chart_to_slide` | chart_generator가 만든 **차트 이미지들을 슬라이드로 배치**. chart_image_paths → chart_slides | chart_generator와 짝 — chart 구현 시에만 의미 |

## 5. 다음 (오너 결정 1건 + 작업)

- **결정**: 위 3종 처분 — 권고: `template_selector` 폐기(소비자 0), `slide_designer`·`chart_to_slide`는 chart_generator 구현 여부에 묶어 결정(chart 구현 시 chart_to_slide 동반 가치, slide_designer는 브랜드 디자인 규칙 확보 후).
- **작업**: chart_generator 구현 착수 시 차트 종류·스타일 협의 → 구현 → stub 4→감소. 병행: 슬라이스 2-②(잔여 stub mock 표기 H2).
