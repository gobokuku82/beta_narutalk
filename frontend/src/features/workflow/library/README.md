# library/ — Workflow Template Save/Load (W3 예정)

**상태**: 자리만 잡음. W3 단계 (spec 62 §6 / §7) 에서 채움.

**책임**: 사용자가 만든 plan 을 *재사용 가능 template* 으로 저장 / 불러오기. param_slots 자동 추출.

**의존 (예정)**:
- `useExecution.plan` — 저장 대상
- `memory_entries` (type=`workflow_template`) — DB layer
- `MemoryManager` API — `save_workflow_template / load_workflow_template / apply_template_with_params`

**예정 파일** (W3):
- `SaveTemplateModal.tsx` — 저장 모달 (이름 / 설명 / 태그 / param_slots 추출)
- `TemplateLibraryPanel.tsx` — 저장된 template 목록 + 검색
- `useWorkflowLibrary.ts` — memory API 호출 hook

상세: spec 62 §6 / §7.
