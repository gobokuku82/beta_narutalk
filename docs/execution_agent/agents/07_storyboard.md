# 07. storyboard_agent — 영상 4 씬 스토리보드 (Hook-Value-Result-CTA)

## 메타

| 항목 | 값 |
|---|---|
| 소속 팀 | creative_team |
| handles_tasks | `video_storyboard` |
| Tool 수 | 0 implemented + 3 stub |
| 현재 구현률 | 0% (Phase 4B 진입 시) |
| team_catalog 위치 | `video_agent` 블록 (D15 — Q4 시 `storyboard_agent` 로 rename 예정) |

## 입출력

- **입력**: 채팅 요청 (`duration`, `target`, `theme`) — 11 매트릭스 진입
- **출력**: `storyboard` (씬별 텍스트+이미지+시간) + `storyboard_pdf` (pdf_agent 호출)
- **다음 에이전트**: image (키프레임 호출) + pdf (PDF 출력)

## POC 범위 (agent_design §06)

- **POC**: 스토리보드까지 (4 씬 텍스트 + 키프레임 이미지 + PDF)
- **3차 (MVP+)**: 실제 영상 제작 (Runway Gen-3 / Sora) — 별도 sprint

## Tool 목록 (Phase 4B 신규)

| Tool | Status | 비고 |
|---|---|---|
| storyboard_planner | 🟡 stub | LLM — 4 씬 구조 기획 |
| frame_image_generator | 🟡 stub | image_agent 호출 (`ad_image_generator` 재사용) |
| storyboard_composer | 🟡 stub | pdf_agent 호출 (PDF 합성) |

## 4 씬 구조

| 씬 | 시간 | 라벨 | 핵심 |
|---|---|---|---|
| 1 | 0~3초 | **Hook** | 시선 끌기 |
| 2 | 3~8초 | **Value** | 핵심 가치·성분 |
| 3 | 8~13초 | **Result** | 사용 결과 |
| 4 | 13~15초 | **CTA** | 행동 유도 |

## 데이터 흐름

```
[채팅 요청: "수분크림 15초 광고 스토리보드"]
       │
       ▼
storyboard_planner (LLM, 4 씬 구조)
       │ storyboard (4 씬: Hook/Value/Result/CTA + 텍스트)
       ▼
frame_image_generator
       │ image_agent.ad_image_generator 호출 × 4
       │ frame_images (씬별 키프레임)
       ▼
storyboard_composer
       │ pdf_agent.pdf_renderer 호출
       │ storyboard_pdf
       ▼
HITL: [확인] [수정요청] [PDF 다운로드]
```

## HITL 카테고리 (D12)

| 카테고리 | 본 에이전트 해당 |
|---|---|
| 생성 후 | ✅ (스토리보드 완성 후 마케터 검토) |

## Phase 진입

| Phase | 본 에이전트의 작업 |
|---|---|
| Phase 0 (현재) | 🟡 폴더만 (`tools/video_creation/`) — Tool 0 |
| **Phase 4B** ⭐ | 3 Tool 신규. image_agent (Phase 4A) + pdf_agent (Phase 4C) 의존 |
| **3차 (MVP+)** | 실제 영상 제작 (Runway / Sora) — 별도 sprint |
| **Q4 추후** | rename `video_agent` → `storyboard_agent` (D15) |

## ⚠️ 수정 시 함께 변경 영역

| 영역 | 파일 | 변경 시 |
|---|---|---|
| Tool 코드 | `tools/video_creation/` (현재 빈 폴더) | 신규 |
| Tool YAML | `tools/catalog/video_creation/` | 신규 |
| **team_catalog.yaml** | `video_agent` 블록 (Q4 시 rename → `storyboard_agent`) | Tool 추가 + rename |
| **LLM Prompts stage3** | `planning_stage3_todo.yaml` | storyboard Tool 이름 |
| **image_agent 의존** | image_agent.ad_image_generator (Phase 4A 선결) | |
| **pdf_agent 의존** | pdf_agent.pdf_renderer (Phase 4C 선결) | |
| **외부 API (3차)** | Runway / Sora — API 미확정 | 3차 진입 시 |
| **Spec 32 §7.1** | video_creation 카테고리 행 | |
| **TOBE_MVP/01** | 매트릭스 storyboard 행 | |
| **데이터 source** | `mock_data_company_info.csv` (브랜드 context) | |
| **D15 rename** | Q4 시 video_agent → storyboard_agent (코드 + spec 영향) | |
| **ADR** | Q4 rename / 3차 영상 제작 (Runway vs Sora) | |
| Tests | `backend/tests/sprint*/test_*storyboard*.py` | |

## 참조 코드

- Tool 폴더 (빈): [`tools/video_creation/`](../../../backend/app/dream_agent/tools/video_creation/)
- team_catalog: `video_agent` 블록

## 참조 spec

- [17 §2.2 storyboard](../../agent_specs/17_functions_to_io_v1.0.md)
- [32 §7.1 video_creation](../../agent_specs/32_execution_agent_tools_v1.0.md)
- [31 §Agent 7](../../agent_specs/31_execution_agent_function_list_v0.6.md)
- [TOBE_MVP/02 storyboard 카드](../../_claude/tool/TOBE_MVP/02_agent_cards.md)

## 참조 비전 (한국어 narrative)

- [agent_design/06_스토리보드_에이전트.md](../../_claude/referrence/agent_design/06_스토리보드_에이전트.md) — 4 씬 구조 + POC vs 3차

## 📍 Mock vs 실API 분기

- POC: storyboard_planner (LLM) → frame_image_generator (image_agent mock) → storyboard_composer (PDF mock)
- MVP+ (Phase 4B): 실 API 흐름
- 3차 (별도 sprint): Runway Gen-3 (~$0.05/초) / Sora (API 미확정 — 2026 기준)

## Drift / 결정

- **D15** 🟢 Acknowledged — video_agent ↔ storyboard_agent 명명 (Q4 rename 예정)
- ADR (3차 진입 시): 영상 제작 API 선정 (Runway / Sora)

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-05-19 | 카드 초안 (Phase 4B 진입 전 골격) |
