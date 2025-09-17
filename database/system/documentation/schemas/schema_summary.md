# 데이터베이스 스키마 요약 (Text2SQL Quick Reference)

## 📊 데이터베이스 구조
좋은제약의 5개 SQLite 데이터베이스로 구성

### 1️⃣ **hr_data.db** - 인사 관리
- `인사자료` (80명): 직원 정보 - 이름, 부서, 직위, 휴가
- `고객연락처` (14명): 주요 고객 연락처

### 2️⃣ **sales_performance_db.db** - 영업 실적
- `sales_performance` (1,711행): 월별 판매 실적 (2022.12~2024.11)
  - 핵심: 팀명, 담당자, 거래처ID, 품목, [월별 판매액]

### 3️⃣ **clients_db.db** - 거래처 관리
- `거래처자료` (6,912행): 방문 횟수, 담당 의사, 환자 수

### 4️⃣ **clients_info.db** - 거래처 정보
- `거래처정보` (288행): 병원명, 진료과목, 연락처

### 5️⃣ **sales_target_db.db** - 영업 목표
- `영업실적목표` (6행): 담당자별 월별 목표액

## 🔗 주요 관계
```
sales_performance.[거래처ID] → clients.[거래처ID]
sales_performance.[담당자] → hr_data.[성명]
sales_target.[담당자] → sales_performance.[담당자]
```

## 💡 쿼리 작성 팁
1. **한글 컬럼명 사용**: `SELECT "담당자", "품목" FROM sales_performance`
2. **월별 데이터**: 컬럼명이 YYYYMM 형식 (예: `"202410"` = 2024년 10월)
3. **조인 예제**:
   ```sql
   SELECT sp."담당자", sp."거래처ID", ci."병원명"
   FROM sales_performance sp
   JOIN "거래처정보" ci ON sp."거래처ID" = ci.ID
   ```

## 🎯 자주 사용하는 쿼리 패턴

### 영업 실적 조회
```sql
-- 2024년 10월 실적
SELECT "담당자", SUM("202410") as "10월실적"
FROM sales_performance
GROUP BY "담당자"
```

### 목표 대비 달성률
```sql
-- 실적과 목표 비교
SELECT
    sp."담당자",
    SUM(sp."202410") as 실적,
    st."202410" as 목표,
    ROUND(100.0 * SUM(sp."202410") / st."202410", 2) as 달성률
FROM sales_performance sp
JOIN "영업실적목표" st ON sp."담당자" = st."담당자"
GROUP BY sp."담당자"
```

### 거래처 정보 조회
```sql
-- 방문 횟수가 많은 거래처
SELECT c."거래처ID", ci."병원명", c."월별방문횟수"
FROM "거래처자료" c
JOIN "거래처정보" ci ON c."거래처ID" = ci.ID
WHERE c."월별방문횟수" > 5
ORDER BY c."월별방문횟수" DESC
```

## ⚠️ 주의사항
- 모든 테이블명과 컬럼명은 **한글**
- 월별 데이터는 개별 컬럼으로 존재 (UNPIVOT 필요시 있음)
- Primary Key 없음 - 중복 데이터 주의
- 인코딩: UTF-8 사용