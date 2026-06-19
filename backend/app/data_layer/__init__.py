"""Data Layer — 데이터 입출력·스키마 추상 골격.

프레임 추출(2026-06-19, guides §6 "data layer" 단위 관리): 흩어져 있던 3개 폴더를 통합.

| 하위 | 역할 |
|------|------|
| `data_sources/` | 입력(raw 읽기) 추상 — `DataSource` ABC + File/Postgres 구현 + `SOURCE_REGISTRY`(빈 골격) |
| `workspace/`    | 출력(정제/계산 저장) 추상 — `WorkspaceBackend` ABC + File/Postgres 구현 |
| `schemas/`      | 표준 입력/출력 스키마 골격 — 도메인 DTO 는 새 도메인이 채운다 |

새 도메인 데이터는 이 레이어에 붙는다 (SOURCE_REGISTRY 등록 + schemas 추가).
"""
