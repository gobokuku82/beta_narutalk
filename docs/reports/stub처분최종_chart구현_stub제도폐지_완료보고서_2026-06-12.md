# 완료보고서 — stub 처분 최종: chart_generator 실구현 + stub 제도 폐지

> 일자: 2026-06-12 · 커밋: `cf8f1e6` (9파일, +447/−80) · 오너 결정: "권장안 그대로"
> 도착점: **카탈로그 92 tool = implemented 92 · stub 0** — "구현 가능한 건 구현하면서 줄이자"의 완결 (출발점: stub 17종)

## 1. 무엇을

| 처분 | 내용 |
|---|---|
| **chart_generator 실구현** | 분석 산출 → 차트 PNG. matplotlib(Agg) + 한국어 폰트(맑은고딕, Linux/macOS fallback). **산출 형태 기반 결정론 선택**(LLM 0): by_채널/분포 dict→가로 막대 · date rows→라인(수치열≤2) · 범주 rows→막대(roas 우선). 최대 4장 |
| **pptx_generator 차트 첨부 실구현** | chart_image_paths 선택 소비 — 섹션 뒤 차트 슬라이드(제목+이미지). **구 chart_to_slide 의 책임을 여기로 흡수** (docstring에만 있던 의도를 코드로) |
| **chart_to_slide 폐기** | 산출(chart_slides) 소비자 0 (헌법 R6 — template_selector 와 동일 근거) + 기능 중복 |
| **slide_designer 폐기** | 브랜드 디자인 자산(D10) 확보 전 구현 불가. stub 잔류 = mock "디자인된 척" 경로 → 메뉴 제거가 정직. 재채용 = D10 + 헌법 §7 3문항 |
| **stub 제도 자체 폐지** | mock_tools.py 삭제 + executor mock 분기 제거. 비구현 tool 이 카탈로그에 등재되면 조용한 mock 대신 **시끄러운 실패**(I1). 미구현 의도 표기는 코드 `Status: planned` 마커(DC-10)가 담당 |

## 2. 차트 디자인 (시각화 분담 — Claude 몫, 오너 거부권 유효)

- **팔레트 = frontend 미러**: globals.css `--chart-1~5` Warm Dusty 5색(hex 변환) + 본문/경계 warm neutral 톤. 그라데이션·장식 금지, 시리즈당 단색 ([[feedback_no_ai_looking_ui]] 정합)
- **정직 장치**: ① 차트화 가능한 산출 없으면 data_insufficient → SKIPPED (빈/장식 차트 생성 금지) ② `_dataref`/`_state_guard` 참조 스텁은 비차트화(모형을 그리지 않음) ③ 중첩 dict(by_category)는 어떤 수치인지 제목에 표기 ④ pptx 는 없는 이미지 파일을 빈 슬라이드로 꾸미지 않음
- 산출 소비자: responder `_collect_attachments`(chart attachment + 다운로드 링크 — 기존 배선) + pptx_generator(신규)

## 3. 검증

- 신규 박제 9 (test_phase3_chart_generator): 형태별 선택 3 + 한국어/중첩 라벨 + 체이닝 + 정직 2 + pptx 첨부 2
- S2 박제 재작성: **S2-4 = "전 tool implemented"** (stub 재등장 시 RED), 폐기 16종 부재
- 전체 회귀 **908 pass / 14 fail / 2 skip** — 실패 14 = 사전존재 16 **− pptx 3 (python-pptx 1.0.2 설치로 해소)** + household 1(동시 세션 data 복구 건, 코드 무관). 신규 파손 0
- 카탈로그 실측: 92 = implemented 92 · stub 0

## 4. 환경 변화 (오너 인지 필요)

- **python-pptx 1.0.2 설치** — pptx_generator 가 "implemented 인데 환경에서 못 도는" 상태였음(사전존재 실패 3건의 원인). matplotlib 3.7.1 은 기존재. ⚠️ 의존성 매니페스트(requirements.txt)가 현재 리포에 없음 — 환경 재구축 시 `pip install python-pptx matplotlib` 필요. 매니페스트 복원은 오너 데이터/환경 작업과 묶어 결정 권장.

## 5. 다음

1. **슬라이스 2 착수 가능** (오너 승인 시): 후보 ①모호/미지원 정직 종착(되묻기 — PLANNING_EMPTY_PLAN fatal 대체) ②mock 표기 H2(stub 폐지로 범위 축소 — LLM tool 의 모델 표기 중심) ③cycle 차단+'완료' 어휘 통일 ④혼합 집계(3월 ROAS 1111%) ⑤frontend 신호 소비
2. 오너 확인 대기 (기존 2건): household 데이터 12행 진위 / signup_conversion 분모 계산 방법
3. 차트 비주얼 확인: 실제 쿼리로 PDF/PPT 뽑아보고 색·형태 마음에 안 들면 거부권 — 팔레트/형태 휴리스틱은 chart_generator.py 상수로 한 곳
