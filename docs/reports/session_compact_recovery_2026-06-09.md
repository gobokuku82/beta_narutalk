# 세션 compact 복구 — 출력/표시 레이어 + 채팅 시각화 (2026-06-09)

> **compact 후 이 문서 읽고 이어서.** 핵심 계획서: [출력표시레이어_분류_계획](../_claude/4layer_system/출력표시레이어_분류_계획_260608_v1.md) · [채팅_마크다운렌더러_근본수정](../_claude/4layer_system/채팅_마크다운렌더러_근본수정_계획_260609_v1.md) (둘 다 gitignored)

## 0. 한 줄 / 현재 위치

silent-0 차단(완료) 이후 **"분석결과를 어떻게 출력/표시하나"** 전체 작업. **Phase 1(분류)·2(서술tool→response표시)·3(pdf/ppt 실렌더+다운로드)·프론트 채팅 시각화(슬라이드+마크다운렌더) 완료.** 남은 건 excel·pptx파일 마크다운·구조화데이터·다운로드버튼UI (전부 비스코프/보류).

## 1. 시스템 핵심 모델 (★박제 — 사용자 의도)

```
data 계산 ─→ tool 서술 ─────→ response dispatcher ─→ frontend 표시
(metrics)    (report_writer/      (산출물 종류 분류,      (마크다운 렌더,
             summary_generator    LLM 0, 결정론)          슬라이드 카드)
             = LLM 서술)
```
- **"code 계산 / tool 서술 / response 표시" 3분리.** response는 LLM 없이 *표시 결정*(format/내용), 실제 픽셀 렌더는 **frontend**.
- 출력 = 조합형 DAG. `output_format`(text/pdf/ppt/excel)이 흐름 결정 — **의도-주도**(planning LLM이 결정, 하드코딩 X).
- "ppt로 만들어줘"=슬라이드+다운로드 / "pdf로"=PDF다운로드 / 평범="text"답변. (요청 시에만 렌더tool — 헤드리스 검증됨.)

## 2. 완료 (커밋) — 내 작업만

| 영역 | 커밋 |
|---|---|
| silent-0 축2+축1 (LLMTool 빈입력 가드) | af89464 |
| **Phase1 분류**: D1 excel_agent 분리 / D5 report_markdown 정합 / D4 summary 재정의 | 6472d59·f7e39e8·b51cc23 |
| **Phase2 서술→표시**: 2a summary 일반결과 서술 / 2b 의도-주도 chain(프롬프트) / 2c response 결정론 dispatcher·LLM제거 / 死코드 | 6eac6e2·ceddd3f·7d0ed87·660759c |
| **Phase3 렌더+다운로드**: deps / pdf_renderer(reportlab 한국어) / pptx_generator(python-pptx) / ppt output_format 버그수정 / 다운로드 엔드포인트 | 2412ca1·7e23475·48b1dd9·e4c2789·f015cff |
| **프론트 채팅 시각화**: 슬라이드 카드 / 마크다운 렌더러(react-markdown+remark-cjk-friendly) | 287c18a·47f9340 |

> 주의: 위 사이에 **다른 작업스트림(dashboard1 frontend ⒃, Postgres 배선)** 커밋 다수 섞임(e0d62be·3af6cd2 등) — 본 작업 무관.

## 3. 핵심 확정 사실 / 발견 (재조사 불요)

- **2b 정정 교훈**: "metric 뒤 summary 강제 compose 코드"(8dc6c25)는 **하드코딩**이라 사용자가 반려 → revert(52fbf4f) → **의도-주도 프롬프트**(ceddd3f). flow 분기는 LLM 의도가 결정. (planner.compose_terminal_narration 함수 = revert됨, 없음.)
- **ppt 오매핑 버그**: OutputFormat/ResponseFormat enum + cognitive 프롬프트 enum 나열에 ppt/excel 누락 → "ppt로"가 pdf로 떨어짐. 4곳 추가로 수정(e4c2789).
- **★CJK 마크다운 함정**: `**긍정 58.3%**로`(닫는 ** 뒤 한글)는 CommonMark flanking 규칙상 굵게 안 됨 → react-markdown만으론 `**` 날것. **remark-cjk-friendly** 로 보정(47f9340).
- **렌더 tool 위치**: `ToolCategory.RENDERING` 신설(8→9). `tools/rendering/`(폴더 'output'은 .gitignore `output/` 충돌 회피). registry yaml = `tools/catalog/rendering/`.
- **다운로드**: `GET /api/files/download?p=...`(data/{client}/outputs 한정·traversal차단) + dispatcher가 attachment.url 부여. 산출물은 data/{client}/outputs/ 에 저장.
- response dispatcher = `responder.build_display_payload` (degrade 게이트 2개 유지 + 산출물 분류). LLM 제거됨.

## 4. 남은 것 (미착수 / 보류)

| 항목 | 상태 |
|---|---|
| excel 실 렌더링 | 보류(사용자 "엑셀은 아직"). openpyxl 설치됨, dispatcher·enum·routing 준비됨 |
| pptx **파일**의 마크다운(`**` 날것 in .pptx) | 비스코프 — 다운로드 타겟 별도 |
| 구조화 데이터 방식(슬라이드 JSON) | 추후(더 견고, 무거움) |
| 다운로드 버튼 UI (frontend) | 미구현 — 백엔드 attachment.url은 있으나 채팅에 버튼 렌더 안 함 |
| keyword_extractor auto-insert 실행순서 | 미확인(별건) — insight 전 실행되는지 헤드리스 점검 |
| pnpm-lock 커밋 | foreign 변경(eslint-plugin-tailwindcss) 혼재로 제외 — deps는 package.json 선언 |

## 5. 테스트 / 검증 방법

- 백엔드: `.venv/Scripts/python.exe -m pytest <path> -q -p no:cacheprovider` (backend/ 에서, venv는 repo루트 `.venv`). 전체 ≈834 pass / 16 fail(전부 pre-existing: parquet·sprint14 HITL·DC_PERM·_scratch — stash 교차검증). **내 변경 breakage 0.**
- 프론트: `pnpm typecheck` / `pnpm exec vitest run <file>` (frontend/ 에서).
- 헤드리스 e2e(실LLM): `python -m scripts.agent_lang_diagnostics.run_harness --limit N` (cognitive+planning). 렌더 의도/체인 확인용.

## 6. 사용자 작업 방식 (★항상 적용)

- **초보자·비전공·DB 약함.** 기술용어는 질문일 수 있음 — 맞추지 말고 전문가 단일 권장.
- **무조건 동조 금지** — 의도 파악 후 코드 면밀 검토·객관 판단. (이번 세션 교정: 2b 하드코딩 반려, pptx 다운로드만 생각한 것, 마크다운 날것 등 사용자가 잡음.)
- **내 정보 구버전 가정** → 외부 검색. **uv 사용**(pip/requirements 아님).
- 큰/모호 작업 = **계획서로 의도·스코프 먼저 합의** 후 코드.
- **메모리 업데이트 금지**(너무 큼).
- 단계 완료+테스트 통과 시 **자동 커밋**(내 파일만 명시 staging — frontend/dashboard·requirements deletion 등 남의 것 절대 휩쓸지 말 것).

## 7. compact 후 resume 프롬프트 (복사용)

```
docs/reports/session_compact_recovery_2026-06-09.md 읽고 이어서.
출력/표시 레이어(Phase1~3 + 채팅 마크다운 렌더러) 완료 상태. 다음 후보 = excel 실렌더(보류) /
pptx파일 마크다운 / 다운로드 버튼 UI / keyword 순서 확인 / 구조화데이터. 사용자에게 우선순위 확인.
초보자·객관판단·동조금지·uv·메모리업데이트금지·계획서먼저·커밋시 내파일만 staging.
```
