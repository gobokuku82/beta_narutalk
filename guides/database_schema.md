# Database Schema Documentation

## 1. Sales Performance Database (sales_performance_db.db)

### Table: sales_performance
실적 데이터를 월별로 저장하는 테이블

**Columns:**
- 성명 (TEXT) - 직원 이름
- 팀명칭 (TEXT) - 팀 이름
- 거래처ID (TEXT) - 거래처 식별자
- 품목 (TEXT) - 판매 품목
- 202212 ~ 202411 (INTEGER) - 월별 매출액 (YYYYMM 형식)

**특징:**
- 각 월별 매출이 별도 컬럼으로 구성 (피벗 형태)
- 직원별, 거래처별, 품목별로 세분화된 매출 데이터

## 2. Sales Target Database (sales_target_db.db)

### Table: 영업목표
영업 목표 관련 데이터

## 3. Clients Database (clients_db.db)

### Table: 거래처자료
거래처 정보 관리

## 4. HR Information Database (hr_data.db)

### Tables:
1. **인사자료** - 직원 정보
   - 성명 (TEXT)
   - 나이 (TEXT)
   - 성별 (TEXT)
   - 입사일 (TEXT)
   - 부서 (TEXT)
   - 직급 (TEXT)
   - 연락처 (TEXT)
   - 연차사용예정 (REAL)
   - 거주지 (TEXT)

2. **비상연락처** - 비상 연락처 정보

## Schema 특성 분석

### 문제점:
1. **한글 컬럼명** - SQL 생성시 주의 필요
2. **월별 컬럼 구조** - 정규화되지 않은 형태
3. **인코딩 이슈** - CP949 인코딩 사용

### 장점:
1. 단순한 구조로 직관적
2. 빠른 조회 가능 (피벗된 형태)
3. Excel 스타일의 데이터 구조

## Text2SQL 구현시 고려사항

1. **컬럼명 처리**
   - 한글 컬럼명을 백틱(`)으로 감싸기
   - 예: SELECT `성명`, `202403` FROM sales_performance

2. **날짜 처리**
   - "3월 실적" → 202403 컬럼
   - "작년 실적" → 2023XX 컬럼들의 합

3. **조인 전략**
   - sales_performance + 인사자료 (성명으로 조인)
   - sales_performance + 거래처자료 (거래처ID로 조인)

4. **집계 함수**
   - 월별 합계: 여러 월 컬럼의 SUM
   - 팀별 평균: GROUP BY 팀명칭