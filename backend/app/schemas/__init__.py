"""표준 schema — 컬럼명 단일 진실 소스 (ADR-027 §4·§5).

inputs/   — DataSource raw → 표준 Pydantic (컬럼명 = 필드명, 한 곳 집중)
outputs/  — Tool 산출 형식

POC(clumi 단일) = mock raw 가 표준 영어 컬럼명 → load 헬퍼가 identity 매핑.
진짜 2번째 client = normalizers/{client}.yaml 추가로 컬럼 매핑 (MVP+).
"""
