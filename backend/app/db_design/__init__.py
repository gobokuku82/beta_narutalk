"""DB설계 워크벤치 백엔드 도메인 로직.

`시스템 → DB설계`(/db-design) 의 ERD 설계를 실제 산출물로 변환하는 도메인 계층.
전송 계층(api/routes/db_design.py)이 여기를 호출한다.

현재:
- erd_build: 설계(ERD) + 엑셀 행 → 실제 SQLite 조립 + 참조 무결성 검사 + 읽기 전용 쿼리.

향후(로드맵): 지표(metric) 발견·정의, 핸드오프 명세(spec) export.
"""
