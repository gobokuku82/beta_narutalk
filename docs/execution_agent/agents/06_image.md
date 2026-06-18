# 06. image_agent — 광고 이미지 + 5축 AI 채점

## 메타

| 항목 | 값 |
|---|---|
| 소속 팀 | creative_team |
| handles_tasks | `image_generation` / `image_editing` |
| Tool 수 | 0 implemented + 6 stub (총 6) |
| 현재 구현률 | 0% (Phase 4A 진입 시) |
| team_catalog 위치 | `image_agent` 블록 (creative_team 안) |

## 입출력

- **입력**: 채팅 요청 (`brand`, `theme`, `keyword`, `count`) + 화면 컨텍스트 (소재ID / 피로도 상태 / 매체) — 11 매트릭스 진입
- **출력**: `image_paths` (3 시안) + `quality_scores` (5축)
- **다음 에이전트**: 채팅 (HITL 카테고리: 생성 후) — 마케터 [채택/거부/재생성]

## Tool 목록 (Phase 4A 신규)

| Tool | Status | 비고 |
|---|---|---|
| brand_guideline_analyzer (RAG) | 🟡 stub | ⭐ **선결 조건** — RAG 인프라 (벡터DB) 필요 |
| ad_image_generator | 🟡 stub | DALL-E 3 API ($0.04~0.08/장) |
| image_resizer | 🟡 stub | Pillow + Cloudinary — 매체별 규격 |
| thumbnail_creator | 🟡 stub | DALL-E 3 |
| background_editor | 🟡 stub | Remove.bg + DALL-E 3 ($0.20/장) |
| creative_quality_scorer (5축 Vision) | 🟡 stub | GPT-4o Vision ($10/M tokens) — Sales/Short/Clear/Visual/Benefit |

## 5축 채점 (D9)

| 축 | 추정 의미 | 0~100 |
|---|---|---|
| Sales | 판매 유도력 | radar 축 |
| Short | 간결성 | |
| Clear | 명확성 | |
| Visual | 비주얼 매력도 | |
| Benefit | 혜택 전달력 | |

→ **D9 Open** — Phase 4A 진입 전 정의 합의 (마케터·디자이너 세션) 필요.

## 데이터 흐름

```
[채팅 요청: "CICA 봄 소재 만들어줘"]
       │
       ▼
brand_guideline_analyzer (RAG)
       │ brand_guidelines (블루밍글로우 컬러/톤/금칙어)
       ▼
ad_image_generator (DALL-E 3)
       │ image_paths (3 시안)
       ▼
creative_quality_scorer (Vision)
       │ quality_scores (5축)
       ▼
HITL: [A안/B안/C안 선택] [다시생성]
       │ (선택 시)
       ▼
(선택) image_resizer / thumbnail_creator
       │ resized_image_paths / thumbnail_paths
```

## HITL 카테고리 (D12)

| 카테고리 | 본 에이전트 해당 | 사례 |
|---|---|---|
| 조회·자동 | — | |
| **생성 후** ⭐ | ✅ (모든 생성 Tool) | 시안 3개 표시 후 마케터 [채택/거부/재생성] |
| 실행 전 | — | |
| 외부 발송 | △ (이미지 매체 자동 업로드 시) | MVP+ |

## Phase 진입

| Phase | 본 에이전트의 작업 |
|---|---|
| Phase 0 (현재) | 🟡 폴더만 (`tools/image_creation/`) — Tool 0 |
| **Phase 4A** ⭐ | 6 Tool 신규 (brand_guideline_analyzer 선결 → 나머지 5) — RAG 인프라 sprint 동시 |
| **Phase 4A 의존** | image_agent → storyboard 의 frame_image_generator + report_ppt 의 chart_image 사용 |

## ⚠️ 수정 시 함께 변경 영역

| 영역 | 파일 | 변경 시 |
|---|---|---|
| Tool 코드 | `tools/image_creation/` (현재 빈 폴더) | 신규 |
| Tool YAML | `tools/catalog/image_creation/` | 신규 |
| **team_catalog.yaml** | `image_agent` 블록 | Tool 추가 |
| **LLM Prompts stage3** | `planning_stage3_todo.yaml` | 이미지 Tool 이름 + 예시 |
| **RAG 인프라** ⭐ | `backend/app/integrations/rag/` (신규) + 벡터DB (pgvector / Chroma) | D8 — RAG 선결 |
| **외부 API client** | DALL-E 3 / Remove.bg / GPT-4o Vision | API key 환경변수 |
| **비용 관제** | `app/core/limits.py` (신규) | Phase 4A 진입 시 |
| **Spec 32 §7.1** | image_creation 카테고리 행 | |
| **TOBE_MVP/01** | 매트릭스 image 행 | |
| **데이터 source** | `mock_data_company_info.csv` + `mock_data_brand_style.csv` (D10) + `mock_data_creatives.csv` (5축 학습 라벨) | |
| **D9 5축 정의** | Phase 4A 진입 전 합의 | |
| **ADR** | ⭐ ADR-XXX RAG 인프라 (벡터DB 선정) / 5축 정의 / DALL-E vs Midjourney | |
| Tests | `backend/tests/sprint*/test_*image*.py` | |

## 참조 코드

- Tool 폴더 (빈): [`tools/image_creation/`](../../../backend/app/dream_agent/tools/image_creation/)
- team_catalog: `image_agent` 블록 (creative_team)

## 참조 spec

- [17 §2.2 image](../../agent_specs/17_functions_to_io_v1.0.md)
- [32 §7.1 image_creation](../../agent_specs/32_execution_agent_tools_v1.0.md) — `brand_guideline_analyzer` 선결 강조
- [31 §Agent 6](../../agent_specs/31_execution_agent_function_list_v0.6.md)
- [TOBE_MVP/02 image 카드](../../_claude/tool/TOBE_MVP/02_agent_cards.md)

## 참조 비전 (한국어 narrative)

- [agent_design/05_이미지_에이전트.md](../../_claude/referrence/agent_design/05_이미지_에이전트.md) — 4 기능 + 5축 채점

## 📍 Mock vs 실API 분기 (Phase 4A — 외부 API 핵심)

본 에이전트는 **외부 API 의존도 가장 높음**:
- DALL-E 3 API (OpenAI) — 이미지 생성
- GPT-4o Vision API — 5축 채점
- Remove.bg API — 배경 편집
- (선택) Cloudinary — 이미지 호스팅

POC: mock fallback (`mock_tools.image_generator` 같은) — placeholder 이미지 path 반환.

MVP+: 실 API + 비용 관제 (월 ~$30~50/마케터).

## Drift / 결정

- **D8** 🟢 Decided — RAG (벡터DB) 인프라 필요 (Phase 4A 선결)
- **D9** 🟡 Open — AI 5축 채점 정의 (Phase 4A 진입 전 합의)
- **D10** 🟢 Decided — 브랜드 디자인 자산 mock 신설 (사용자 작업 중)
- ADR (Phase 4A): RAG 벡터DB 선정 + 5축 정의 + 외부 API client + 비용 관제

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-19 | 카드 초안 (Phase 4A 진입 전 골격) |
