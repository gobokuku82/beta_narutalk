# SQLite 데이터베이스 스키마 문서

## 시스템 개요
- **DBMS**: SQLite 3.x
- **인코딩**: UTF-8
- **총 데이터베이스**: 5개
- **총 테이블**: 6개
- **총 레코드**: 9,011개

## 파일 구조
```
database/
├── hr_information/
│   └── hr_data.db
└── sales_performance_db/
    ├── sales_performance_db.db
    ├── clients_db.db
    ├── clients_info.db
    └── sales_target_db.db
```

---

# 1. hr_data.db

**경로**: `database/hr_information/hr_data.db`  
**테이블 수**: 2개

## 1.1 인사자료 테이블

**레코드 수**: 80개

### 컬럼 구조
| 순번 | 컬럼명 | 데이터 타입 | NULL 허용 | 기본값 | Primary Key |
|------|--------|------------|-----------|--------|--------------|
| 0 | 사번 | TEXT | YES | NULL | NO |
| 1 | 성명 | TEXT | YES | NULL | NO |
| 2 | 본부 | TEXT | YES | NULL | NO |
| 3 | 직급 | TEXT | YES | NULL | NO |
| 4 | 부서 | TEXT | YES | NULL | NO |
| 5 | 지점 | TEXT | YES | NULL | NO |
| 6 | 연락처 | TEXT | YES | NULL | NO |
| 7 | 월평균사용예산 | REAL | YES | NULL | NO |
| 8 | 최근 평가 | TEXT | YES | NULL | NO |
| 9 | 기본급(₩) | TEXT | YES | NULL | NO |
| 10 | 성과급(₩) | TEXT | YES | NULL | NO |
| 11 | 책임업무 | TEXT | YES | NULL | NO |

## 1.2 지점연락처 테이블

**레코드 수**: 14개

### 컬럼 구조
| 순번 | 컬럼명 | 데이터 타입 | NULL 허용 | 기본값 | Primary Key |
|------|--------|------------|-----------|--------|--------------|
| 0 | 본부 | TEXT | YES | NULL | NO |
| 1 | 부서 | TEXT | YES | NULL | NO |
| 2 | 지점 | TEXT | YES | NULL | NO |
| 3 | 지점 연락처 | TEXT | YES | NULL | NO |

---

# 2. sales_performance_db.db

**경로**: `database/sales_performance_db/sales_performance_db.db`  
**테이블 수**: 1개

## 2.1 sales_performance 테이블

**레코드 수**: 1,711개

### 컬럼 구조
| 순번 | 컬럼명 | 데이터 타입 | NULL 허용 | 기본값 | Primary Key |
|------|--------|------------|-----------|--------|--------------|
| 0 | 사번 | TEXT | YES | NULL | NO |
| 1 | 담당자 | TEXT | YES | NULL | NO |
| 2 | 거래처ID | TEXT | YES | NULL | NO |
| 3 | 품목 | TEXT | YES | NULL | NO |
| 4 | 202212 | INTEGER | YES | NULL | NO |
| 5 | 202301 | INTEGER | YES | NULL | NO |
| 6 | 202302 | INTEGER | YES | NULL | NO |
| 7 | 202303 | INTEGER | YES | NULL | NO |
| 8 | 202304 | INTEGER | YES | NULL | NO |
| 9 | 202305 | INTEGER | YES | NULL | NO |
| 10 | 202306 | INTEGER | YES | NULL | NO |
| 11 | 202307 | INTEGER | YES | NULL | NO |
| 12 | 202308 | INTEGER | YES | NULL | NO |
| 13 | 202309 | INTEGER | YES | NULL | NO |
| 14 | 202310 | INTEGER | YES | NULL | NO |
| 15 | 202311 | INTEGER | YES | NULL | NO |
| 16 | 202312 | INTEGER | YES | NULL | NO |
| 17 | 202401 | INTEGER | YES | NULL | NO |
| 18 | 202402 | INTEGER | YES | NULL | NO |
| 19 | 202403 | INTEGER | YES | NULL | NO |
| 20 | 202404 | INTEGER | YES | NULL | NO |
| 21 | 202405 | INTEGER | YES | NULL | NO |
| 22 | 202406 | INTEGER | YES | NULL | NO |
| 23 | 202407 | INTEGER | YES | NULL | NO |
| 24 | 202408 | INTEGER | YES | NULL | NO |
| 25 | 202409 | INTEGER | YES | NULL | NO |
| 26 | 202410 | INTEGER | YES | NULL | NO |
| 27 | 202411 | INTEGER | YES | NULL | NO |

### 특징
- 월별 매출 데이터가 개별 컬럼으로 저장 (2022년 12월 ~ 2024년 11월)
- YYYYMM 형식의 컬럼명 사용

---

# 3. clients_db.db

**경로**: `database/sales_performance_db/clients_db.db`  
**테이블 수**: 1개

## 3.1 거래처자료 테이블

**레코드 수**: 6,912개

### 컬럼 구조
| 순번 | 컬럼명 | 데이터 타입 | NULL 허용 | 기본값 | Primary Key |
|------|--------|------------|-----------|--------|--------------|
| 0 | 거래처ID | TEXT | YES | NULL | NO |
| 1 | 월 | INTEGER | YES | NULL | NO |
| 2 | 매출 | INTEGER | YES | NULL | NO |
| 3 | 월방문횟수 | INTEGER | YES | NULL | NO |
| 4 | 사용 예산 | INTEGER | YES | NULL | NO |
| 5 | 총환자수 | INTEGER | YES | NULL | NO |
| 6 | 담당자 | TEXT | YES | NULL | NO |

### 특징
- 월 컬럼은 YYYYMM 형식의 정수값
- 거래처별 월간 활동 데이터 저장

---

# 4. sales_target_db.db

**경로**: `database/sales_performance_db/sales_target_db.db`  
**테이블 수**: 1개

## 4.1 지점별목표 테이블

**레코드 수**: 6개

### 컬럼 구조
| 순번 | 컬럼명 | 데이터 타입 | NULL 허용 | 기본값 | Primary Key |
|------|--------|------------|-----------|--------|--------------|
| 0 | 지점 | TEXT | YES | NULL | NO |
| 1 | 담당자 | TEXT | YES | NULL | NO |
| 2 | 202312 | INTEGER | YES | NULL | NO |
| 3 | 202401 | INTEGER | YES | NULL | NO |
| 4 | 202402 | INTEGER | YES | NULL | NO |
| 5 | 202403 | INTEGER | YES | NULL | NO |
| 6 | 202404 | INTEGER | YES | NULL | NO |
| 7 | 202405 | INTEGER | YES | NULL | NO |
| 8 | 202406 | INTEGER | YES | NULL | NO |
| 9 | 202407 | INTEGER | YES | NULL | NO |
| 10 | 202408 | INTEGER | YES | NULL | NO |
| 11 | 202409 | INTEGER | YES | NULL | NO |
| 12 | 202410 | INTEGER | YES | NULL | NO |
| 13 | 202411 | INTEGER | YES | NULL | NO |

### 특징
- 월별 목표 금액이 개별 컬럼으로 저장 (2023년 12월 ~ 2024년 11월)

---

# 5. clients_info.db

**경로**: `database/sales_performance_db/clients_info.db`  
**테이블 수**: 1개

## 5.1 거래처정보 테이블

**레코드 수**: 288개

### 컬럼 구조
| 순번 | 컬럼명 | 데이터 타입 | NULL 허용 | 기본값 | Primary Key |
|------|--------|------------|-----------|--------|--------------|
| 0 | ID | TEXT | YES | NULL | NO |
| 1 | 원장명 | TEXT | YES | NULL | NO |
| 2 | 지역구 | TEXT | YES | NULL | NO |
| 3 | 병원연락처 | TEXT | YES | NULL | NO |

---

# 데이터베이스 관계

## 주요 외래키 관계 (논리적)

### 1. 직원-영업실적 관계
- **Parent**: 인사자료.사번
- **Child**: sales_performance.사번
- **관계**: 1:N (한 직원이 여러 영업 실적 보유)

### 2. 거래처정보-영업실적 관계
- **Parent**: 거래처정보.ID
- **Child**: sales_performance.거래처ID
- **관계**: 1:N (한 거래처에 여러 품목 거래)

### 3. 거래처정보-거래처자료 관계
- **Parent**: 거래처정보.ID
- **Child**: 거래처자료.거래처ID
- **관계**: 1:N (한 거래처의 여러 월별 데이터)

### 4. 직원-거래처자료 관계
- **Parent**: 인사자료.성명
- **Child**: 거래처자료.담당자
- **관계**: 1:N (이름 기반 약한 참조)

### 5. 지점-지점목표 관계
- **Parent**: 지점연락처.지점
- **Child**: 지점별목표.지점
- **관계**: 1:N

### 6. 직원-지점목표 관계
- **Parent**: 인사자료.성명
- **Child**: 지점별목표.담당자
- **관계**: 1:N (이름 기반 약한 참조)

---

# 데이터 특성

## 공통 특성
1. **모든 컬럼이 NULL 허용**: NOT NULL 제약 없음
2. **Primary Key 미설정**: 명시적 기본키 없음
3. **Foreign Key 제약 없음**: 참조 무결성 미적용
4. **인덱스 없음**: 쿼리 성능 최적화 필요

## 데이터 타입 특이사항
1. **급여 정보**: TEXT 타입으로 저장 (기본급(₩), 성과급(₩))
2. **월별 데이터**: 개별 컬럼으로 저장 (정규화 필요)
3. **날짜 형식**: YYYYMM 형식의 INTEGER 또는 컬럼명
4. **한글 컬럼명**: 모든 테이블과 컬럼명이 한글

## 인코딩
- 모든 데이터베이스 파일: UTF-8

---

# SQL 쿼리 작성 가이드

## 한글 컬럼명 처리
```sql
-- 큰따옴표 사용 필수
SELECT "사번", "성명", "부서"
FROM "인사자료"
WHERE "부서" = '영업1팀'
```

## 월별 데이터 접근
```sql
-- 특정 월 데이터
SELECT "담당자", "202410" as "2024년10월"
FROM sales_performance
WHERE "202410" IS NOT NULL

-- 분기별 집계
SELECT "담당자",
       ("202401" + "202402" + "202403") as "1분기",
       ("202404" + "202405" + "202406") as "2분기"
FROM sales_performance
```

## 테이블 조인
```sql
-- 영업실적과 거래처정보 조인
SELECT sp."담당자", sp."거래처ID", ci."원장명", sp."202411"
FROM sales_performance sp
LEFT JOIN "거래처정보" ci ON sp."거래처ID" = ci.ID

-- 직원정보와 영업실적 조인 (이름 기반)
SELECT hr."사번", hr."성명", sp."거래처ID", sp."품목"
FROM "인사자료" hr
LEFT JOIN sales_performance sp ON hr."사번" = sp."사번"
```

## NULL 처리
```sql
-- NULL을 0으로 처리
SELECT "담당자", 
       COALESCE("202410", 0) as "10월실적",
       COALESCE("202411", 0) as "11월실적"
FROM sales_performance
```

---

# 데이터 무결성 검증 쿼리

## 고아 레코드 확인
```sql
-- 존재하지 않는 직원의 영업실적
SELECT DISTINCT "사번"
FROM sales_performance
WHERE "사번" NOT IN (SELECT "사번" FROM "인사자료" WHERE "사번" IS NOT NULL)

-- 존재하지 않는 거래처의 거래자료
SELECT DISTINCT "거래처ID"
FROM "거래처자료"
WHERE "거래처ID" NOT IN (SELECT ID FROM "거래처정보" WHERE ID IS NOT NULL)
```

## 중복 데이터 확인
```sql
-- 거래처정보 중복 확인
SELECT ID, COUNT(*) as cnt
FROM "거래처정보"
GROUP BY ID
HAVING cnt > 1

-- 거래처자료 중복 확인
SELECT "거래처ID", "월", COUNT(*) as cnt
FROM "거래처자료"
GROUP BY "거래처ID", "월"
HAVING cnt > 1
```

---

# 제약사항 및 주의사항

1. **Primary Key 부재**: 데이터 중복 가능성
2. **Foreign Key 미적용**: 참조 무결성 보장 안됨
3. **이름 기반 참조**: 담당자명으로 연결 시 동명이인 문제
4. **월별 컬럼 구조**: 새로운 월 추가 시 스키마 변경 필요
5. **데이터 타입 불일치**: 급여가 TEXT로 저장
6. **인덱스 부재**: 대용량 데이터 조회 시 성능 저하
7. **NULL 허용**: 모든 필드가 NULL 가능하여 데이터 품질 관리 어려움
