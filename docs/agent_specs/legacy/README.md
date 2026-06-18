# Legacy — 정정 이전 버전 보관소

> **Status**: 이력 보존 (archive) — 코드 검증으로 정정된 spec 의 *직전* 버전.
> `POC_legacy/` 와 구분 — POC_legacy 는 v1.0 격상 이전(POC 초안) / 본 폴더는 v1.x 이후 정정으로 대체된 버전.

## 폴더 목적

`2026-05-15` agent_specs 다중 사이클 검증(`docs/reports/agent_specs_verification_2026-05-15.md`)에서, 일부 spec 이 백엔드 코드와 광범위하게 어긋난 것이 발견됐다. 일반적인 drift 정정(in-place + "검증 정정" changelog 행)은 본 문서로 처리했지만, **수정 분량이 전면 재작성에 가까운** 경우 원본을 본 폴더에 보존한다.

**보존 이유**: 검증의 기본 원칙은 "코드 = 진실" 이지만, 원본 spec 의 *의도* 가 옳고 코드가 드리프트한 가능성도 있다. 원본을 archive 로 남겨 향후 의도 복원 / 재해석 시 참조한다.

## 파일 목록

| 원본 | 대체 (활성) | 보관 사유 |
|------|-----------|----------|
| [`30_DATA_MODELS_v1.0.md`](30_DATA_MODELS_v1.0.md) | [`../30_DATA_MODELS_v1.1.md`](../30_DATA_MODELS_v1.1.md) | StructuredQuery/Plan/ExecutionResult/Enum 다수 필드가 실제 Pydantic 모델과 불일치 — 사이클 2 정정 |
| [`01_requirements_v1.3.md`](01_requirements_v1.3.md) | [`../01_requirements_v1.6.md`](../01_requirements_v1.6.md) | v1.6 가 현 권위 — Sprint 14 A1+A3 Phase 5 완료 반영본 |
| [`01_requirements_v1.4.md`](01_requirements_v1.4.md) | 동상 | 동상 |
| [`10_system_architecture_v1.8.md`](10_system_architecture_v1.8.md) | [`../10_system_architecture_v1.9.md`](../10_system_architecture_v1.9.md) | v1.9 가 현 권위 |
| [`12_manager_layer_v1.1.md`](12_manager_layer_v1.1.md) | [`../12_manager_layer_v1.3.md`](../12_manager_layer_v1.3.md) | v1.3 가 현 권위 |
| [`22_error_codes_v1.0.md`](22_error_codes_v1.0.md) | [`../22_error_codes_v1.1.md`](../22_error_codes_v1.1.md) | v1.1 = Sprint 14 A3 D7=A- (TODO_EDIT_NOT_PAUSED / INVALID_DAG / NL_INTENT_UNCLEAR 추가) |
| [`21_WEBSOCKET_PROTOCOL_v1.4.md`](21_WEBSOCKET_PROTOCOL_v1.4.md) | [`../21_WEBSOCKET_PROTOCOL_v1.5.md`](../21_WEBSOCKET_PROTOCOL_v1.5.md) | v1.5 = ADR-011 ConnectionManager 채널 분리 (2026-05-16). fan-out 키 user_id → (user_id, channel). spec §3.2 hitl 카탈로그 엄격 적용. |
| [`62_workflow_canvas_design_v1.0.md`](62_workflow_canvas_design_v1.0.md) | [`../62_workflow_canvas_design_v1.2.md`](../62_workflow_canvas_design_v1.2.md) | v1.2 = ADR-013 W2′ 구현 완료 (2026-05-17). v1.1 도 본 폴더에 별도 archive. |
| [`62_workflow_canvas_design_v1.1.md`](62_workflow_canvas_design_v1.1.md) | [`../62_workflow_canvas_design_v1.2.md`](../62_workflow_canvas_design_v1.2.md) | v1.2 = ADR-013 W2′ 엣지·드래그·batched 구현 완료 (main Stage 7, 2026-05-17). §5.5 BatchedToolbar 추가 + §5.7~§5.10 W2′ 신규 절 (엣지/드래그, cycleGuard, issues UX, batched) + §7 Phase 표 W2′ ✅ + §10.2 ADR-013 추가 + §11 Risk 3건 추가. 백엔드 변경 0 (TodoManager 가 이미 모든 필드 통과). |

## 정리 계획

- **Sprint 16+**: 원본 의도 ↔ 현 코드 간 의식적 비교 결론 후 삭제 검토.
- 당분간 **읽기 전용 아카이브** 상태로 유지.

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-05-15 | 초기 생성 — `30_DATA_MODELS_v1.0.md` archive |
| 2026-05-15 (확장) | 구버전 spec 5개 추가 archive (01_v1.3, 01_v1.4, 10_v1.8, 12_v1.1, 22_v1.0) — 활성 spec 의 stale 링크 일괄 정정과 함께 |
| 2026-05-16 | `21_WEBSOCKET_PROTOCOL_v1.4.md` archive — ADR-011 ConnectionManager 채널 분리 (ws_contract 브랜치 Stage 4). v1.5 가 현 권위. |
| 2026-05-16 | `62_workflow_canvas_design_v1.0.md` archive — ADR-012 W2 시각적 편집 구현 완료 (main Stage 7). v1.1 가 현 권위. |
| 2026-05-17 | `62_workflow_canvas_design_v1.1.md` archive — ADR-013 W2′ 엣지·드래그·batched 구현 완료 (main Stage 7, 8 Stage TDD). v1.2 가 현 권위. |
