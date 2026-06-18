# C:LUMI 백엔드 tool 작업 — 세션 Compact 준비 (2026-05-23)

> compact 이후 곧바로 작업 재개할 수 있도록 **상태·결정·다음 액션** 정리.

---

## 0. 메타

| 항목 | 내용 |
|---|---|
| 작성일 | 2026-05-23 |
| 위치 | `docs/reports/session_compact_recovery_2026-05-23.md` |
| Compact 시점 | 백엔드 tool 매핑 계획서 작성 직전 (현 frontend·backend 미조사 상태) |
| 작업 도메인 | C:LUMI 퍼포먼스 마케팅 에이전트 — 데이터 파이프라인 + 분석 + 대시보드 |

---

## 1. 현 작업 한 줄

**데이터 기반·정제·계산은 3축 검증 완료. 백엔드 tool 폴더 8개 구조 확정 직후, `backend/app/dream_agent/` 조사 → tool 매핑 계획서 작성이 다음 작업.**

---

## 2. 즉시 다음 액션 (compact 직후 이 순서로)

1. **`backend/app/dream_agent/` 구조 조사** — 기존 tool 폴더·네이밍·등록 방식·시스템 에이전트(=tool composer)의 tool 사용 패턴 파악
2. **tool 매핑 계획서 작성** (저장 위치 미정 — `docs/_claude/data/` 또는 `backend/` 인근) — 8 폴더 × {기존 tool / 신규 / 합칠 것} 매트릭스 + 에이전트 워크플로우 예시 + tool 메타 포맷 표준
3. **첫 tool 시범 구현** — 한 정제 규칙(예: 활성주문 필터)을 8폴더 구조에 맞춰 1개 만들어 패턴 검증

---

## 3. 완료된 것 (검증 상태)

| 영역 | 산출물 | 상태 |
|---|---|---|
| **데이터** | `data/clumi/` 21 소스 (clumi_v2 통합본) | ✅ byte 정합 (23+9 동일, vs `docs/_claude/referrence/clumi_v2/`) |
| **정확 명세** | `clumi_데이터사전_검증본.csv` 771 컬럼 + `raw_데이터_설명서_2026-05-22.md` | ✅ v2 갱신 |
| **방법론** | methodology 6종 (정제 10·계산 46·시각화·해설 25·시나리오·산출물 69) | ✅ 확보·검증 |
| **분석 정량** | 46 계산식 → `clumi_analysis_2026-04.json` 46 deliverable | ✅ Phase 0~2 완료, 정답 17/17 일치 |
| **3축 최종검증** | 계산식·데이터·정제방법 | ✅ 전부 통과 (`docs/reports/clumi_분석_최종검증_및_구현계획_2026-05-22.md`) |
| **파이프라인 계획서** | `데이터_파이프라인_구조_계획서_2026-05-21.md` | ✅ v2 갱신 (§4.6 실증, §6 방법 확보 현황) |

**남은 작업**: 정성 해설 25 / 백엔드 tool화 / 대시보드 / (장기) 재사용 엔진.

---

## 4. 핵심 결정 (compact 에서 절대 잃지 말 것)

### 4.1 백엔드 tool 폴더 8개 (확정)

`backend/app/dream_agent/tools/`:

| 폴더 | 한국어 | 담당 |
|---|---|---|
| `collection/` | 수집 | 외부→raw. POC=clumi 파일 reader, MVP=API |
| `cleaning/` | 정제 | 데이터 품질(활성주문·결측·검증) — 정제규칙 1·3 |
| `preprocessing/` | 전처리 | 가공·집계 준비 — 정제규칙 5·6·7·10 |
| `normalization/` | 포멧일치화 | 단위·표기 통일 — 정제규칙 2·4·8·9 |
| `metrics/` | 기본 측정 | descriptive 계산 (S001 등 ~30개) |
| `comparison/` | 비교 | MoM·A/B·세그먼트 (S028·S017~S021 등 ~10개) |
| `insights/` | 추론 | 정성 해설 25 (LLM 경유 가능) |
| `prediction/` | 예측 | 예측·forecasting (신규 영역, 현재 없음) |

### 4.2 아키텍처 원칙

- **백엔드 tool = 단일 소스.** 프론트는 사본 X, `/api/data/*` 호출. drift 방지·결정론 보장.
- **tool composer = 기존 시스템 에이전트** (별도 폴더 X, 에이전트 reasoning).
- **tool 원자성** — 1 tool = 1 일. 복합은 composer 가 조립.
- **API 계약**: `GET /api/data/{sheet}?layer=raw|cleaned|computed` · `POST /reprocess` (시각화 계획서 §11).
- **결정론 원칙** — 수집·정제·계산 LLM 미경유 (해설만 LLM 허용).

### 4.3 데이터·방법 사실 (compact 후도 유효)

- 21 소스 / 정제 10규칙 / 계산식 헤더 **46개** (문서가 "47개"라 칭하나 실제 헤더 46).
- 정답 핵심값: 총매출 119,539,660 / 마케팅비 18,306,923 / ROAS 6.53 / CAC 30,512 / 활성주문 1,919.
- 데이터 제약 2건: S019(프로필방문 미수록)·S020(메시지시작 미수록) — methodology 자체 명시.
- vendor `clumi_data_dictionary.csv` 20/21 불일치 — **사용 금지**. 정확본 사전 사용.

---

## 5. 파일·문서 위치 맵

### 데이터·설명
- 데이터 21소스: `data/clumi/` (+ `data/clumi/description/` 벤더 카탈로그 3 + 방법론 6 + `_검증메모`)
- 정확 명세: `docs/_claude/data/data_description/clumi_데이터사전_검증본.csv` + `raw_데이터_설명서_2026-05-22.md`
- 레퍼런스 원본: `docs/_claude/referrence/clumi_v2/` (clumi_v2 받은 그대로)

### 분석 실행
- 파이프라인: `docs/_claude/data/clumi_analysis/pipeline.py` (정제+계산 비-GA4) · `pipeline_ga4.py` (GA4)
- 산출: `docs/_claude/data/clumi_analysis/clumi_analysis_2026-04.json` (46 deliverable)
- 검증: `docs/_claude/data/clumi_analysis/검증_2026-05-22.md` · `verify_final.py`

### 계획·검증
- 파이프라인 계획서: `docs/_claude/data/데이터_파이프라인_구조_계획서_2026-05-21.md` (v2 갱신)
- 시각화 계획서: `docs/_claude/frontend/데이터_시각화_구조_계획서_2026-05-21.md` (v2.4)
- 최종 검증 + 구현 계획: `docs/reports/clumi_분석_최종검증_및_구현계획_2026-05-22.md`
- 검증 리포트: `docs/reports/data_pipeline_verification_2026-05-22.md`
- INDEX: `docs/_claude/INDEX.md` (현 작업 §1.1 추적)

### 백엔드 (조사 대상)
- 에이전트: `backend/app/dream_agent/` (구조 미조사)
- tool 폴더: `backend/app/dream_agent/tools/` (8 폴더 신설 예정)

---

## 6. 유지할 컨벤션·원칙 (메모리·세션 누적)

- **벤더 dictionary 신뢰 X** — 정확본 사전이 진실 소스 (D11)
- **분석은 user methodology 기반** — 정제·계산 로직 임의 생성 금지. methodology_*.md 가 사용자 제공 방법
- **데이터·방법 변경 시 byte 정합 재검증** (해시 대조)
- **벤더 원본 문서 수정 금지** — `_검증메모` 에 오류 표시, 정확본은 별도
- **단계 완료 시 자동 커밋** (feedback 메모리) — Step/Group 완료+테스트 통과 시 자동 git commit
- **테스트 단축/skip 금지** — TDD 우선, 회귀 검증 필수
- **권한 프롬프트 전부 통과** — bypassPermissions, 위험 작업 자동 OK
- **UI "AI 만든 티" 금지** — 액센트 1개 원칙, 색 결정 전 디자인 시스템 조사

---

## 7. 미해결 질문·결정 보류

| # | 항목 | 결정 시점 |
|---|---|---|
| Q1 | tool 매핑 계획서 저장 위치 — `docs/_claude/data/` vs `backend/` 인근 | 백엔드 조사 후 |
| Q2 | tool 메타 포맷 — pydantic schema? LangGraph node? docstring 규약? | 백엔드 조사 시 기존 패턴 확인 |
| Q3 | 정제규칙 일부의 카테고리 경계 — 등급통일(8)이 normalization 인가 preprocessing 인가 등 | 매핑 계획서 작성 시 |
| Q4 | Phase A(해설 25) vs Phase C-1(frontend 조사) 시작 순서 — 백엔드 tool화가 선행되며 Phase A·C 는 후순위로 밀림 | 백엔드 tool화 진행도에 따라 |
| Q5 | clumi_v2 referrence 폴더 향후 관리 (사용자가 직접 레퍼런스로 이동했음) | 사용자 결정 영역 |

---

## 8. 빠르게 컨텍스트 복원하는 법

compact 후 사용자가 "이어서 진행하자"라고만 하면, 아래 순서로 읽으면 즉시 복원:

1. **본 문서 §1·§2** — 현 작업·다음 액션
2. **`docs/reports/clumi_분석_최종검증_및_구현계획_2026-05-22.md`** — 검증 통과 + 구현 Phase
3. **`docs/_claude/data/데이터_파이프라인_구조_계획서_2026-05-21.md` §6 (방법 확보 현황)** — methodology 위치
4. **본 문서 §4 (핵심 결정)** — 8 폴더 + 아키텍처 원칙

→ 그 다음 `backend/app/dream_agent/` 조사 착수.

---

## 9. 변경 이력

| 일자 | 내용 |
|---|---|
| 2026-05-23 | 초안 — 백엔드 tool화 직전 compact 준비. 8 폴더 구조·아키텍처 원칙·다음 액션·문서 위치 맵 정리. |
