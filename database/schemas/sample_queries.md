# 📊 Text2SQL 샘플 쿼리 가이드

이 문서는 자연어 질문을 SQL 쿼리로 변환하는 예시를 제공합니다.

## 🎯 인사 관련 쿼리

### 1. 직원 정보 조회

**자연어 질문**: "김철수 과장의 정보를 보여줘"
```sql
SELECT *
FROM 인사자료
WHERE 성명 = '김철수' AND 직급 = '과장';
```

**자연어 질문**: "영업1팀 직원 목록을 보여줘"
```sql
SELECT 사번, 성명, 직급, 연락처
FROM 인사자료
WHERE 부서 = '영업1팀'
ORDER BY 직급 DESC, 성명;
```

### 2. 조직별 인원 현황

**자연어 질문**: "부서별 인원수를 알려줘"
```sql
SELECT 부서, COUNT(*) as 인원수
FROM 인사자료
GROUP BY 부서
ORDER BY 인원수 DESC;
```

**자연어 질문**: "직급별 평균 기본급은 얼마야?"
```sql
SELECT 직급,
       AVG(CAST(REPLACE(REPLACE("기본급(₩)", ',', ''), '₩', '') AS INTEGER)) as 평균기본급
FROM 인사자료
GROUP BY 직급
ORDER BY 평균기본급 DESC;
```

### 3. 지점 정보

**자연어 질문**: "서울 지점들의 연락처를 알려줘"
```sql
SELECT 지점, "지점 연락처"
FROM 지점연락처
WHERE 지점 LIKE '%서울%';
```

## 💼 영업 실적 쿼리

### 1. 개인별 실적

**자연어 질문**: "김영희의 2024년 10월 실적은?"
```sql
SELECT sp.담당자, sp.거래처ID, sp."202410" as 실적, ci.원장명, ci.지역구
FROM sales_performance sp
LEFT JOIN 거래처정보 ci ON sp.거래처ID = ci.ID
WHERE sp.담당자 = '김영희' AND sp."202410" > 0;
```

**자연어 질문**: "2024년 상반기 직원별 총 실적"
```sql
SELECT 담당자,
       SUM("202401" + "202402" + "202403" + "202404" + "202405" + "202406") as 상반기_총실적
FROM sales_performance
GROUP BY 담당자
ORDER BY 상반기_총실적 DESC;
```

### 2. 거래처별 분석

**자연어 질문**: "매출 top 10 거래처는?"
```sql
SELECT cd.거래처ID, ci.원장명, ci.지역구, SUM(cd.매출) as 총매출
FROM 거래처자료 cd
LEFT JOIN 거래처정보 ci ON cd.거래처ID = ci.ID
GROUP BY cd.거래처ID, ci.원장명, ci.지역구
ORDER BY 총매출 DESC
LIMIT 10;
```

**자연어 질문**: "서울 지역 거래처들의 평균 월 방문 횟수"
```sql
SELECT ci.지역구, AVG(cd.월방문횟수) as 평균방문횟수
FROM 거래처자료 cd
INNER JOIN 거래처정보 ci ON cd.거래처ID = ci.ID
WHERE ci.지역구 LIKE '%서울%'
GROUP BY ci.지역구;
```

### 3. 시계열 분석

**자연어 질문**: "2024년 월별 전체 매출 추이"
```sql
WITH monthly_sales AS (
    SELECT '202401' as 월, SUM("202401") as 매출 FROM sales_performance
    UNION ALL
    SELECT '202402', SUM("202402") FROM sales_performance
    UNION ALL
    SELECT '202403', SUM("202403") FROM sales_performance
    UNION ALL
    SELECT '202404', SUM("202404") FROM sales_performance
    UNION ALL
    SELECT '202405', SUM("202405") FROM sales_performance
    UNION ALL
    SELECT '202406', SUM("202406") FROM sales_performance
    UNION ALL
    SELECT '202407', SUM("202407") FROM sales_performance
    UNION ALL
    SELECT '202408', SUM("202408") FROM sales_performance
    UNION ALL
    SELECT '202409', SUM("202409") FROM sales_performance
    UNION ALL
    SELECT '202410', SUM("202410") FROM sales_performance
)
SELECT 월, 매출
FROM monthly_sales
WHERE 매출 > 0
ORDER BY 월;
```

## 🎯 목표 대비 실적

### 1. 지점별 달성률

**자연어 질문**: "2024년 10월 지점별 목표 달성률"
```sql
WITH 지점실적 AS (
    SELECT i.지점, SUM(sp."202410") as 실적
    FROM 인사자료 i
    INNER JOIN sales_performance sp ON i.사번 = sp.사번
    GROUP BY i.지점
)
SELECT
    t.지점,
    t."202410" as 목표,
    COALESCE(r.실적, 0) as 실적,
    ROUND(CAST(COALESCE(r.실적, 0) AS FLOAT) / t."202410" * 100, 2) as 달성률
FROM 지점별목표 t
LEFT JOIN 지점실적 r ON t.지점 = r.지점
WHERE t."202410" > 0;
```

### 2. 개인별 성과

**자연어 질문**: "실적 top 5 직원의 상세 정보"
```sql
WITH 직원실적 AS (
    SELECT 사번, 담당자,
           SUM("202401" + "202402" + "202403" + "202404" +
               "202405" + "202406" + "202407" + "202408" +
               "202409" + "202410") as 총실적
    FROM sales_performance
    GROUP BY 사번, 담당자
)
SELECT
    i.사번, i.성명, i.직급, i.부서, i.지점,
    r.총실적, i."최근 평가"
FROM 직원실적 r
INNER JOIN 인사자료 i ON r.사번 = i.사번
ORDER BY r.총실적 DESC
LIMIT 5;
```

## 🔄 복합 조인 쿼리

### 1. 직원-거래처-실적 통합

**자연어 질문**: "김철수가 담당하는 거래처들의 정보와 실적"
```sql
SELECT
    i.성명 as 담당자,
    ci.원장명,
    ci.지역구,
    ci.병원연락처,
    cd.월,
    cd.매출,
    cd.월방문횟수
FROM 인사자료 i
INNER JOIN 거래처자료 cd ON i.성명 = cd.담당자
INNER JOIN 거래처정보 ci ON cd.거래처ID = ci.ID
WHERE i.성명 = '김철수'
ORDER BY cd.월 DESC;
```

### 2. 부서별 거래처 현황

**자연어 질문**: "영업1팀이 관리하는 거래처 수와 총 매출"
```sql
SELECT
    i.부서,
    COUNT(DISTINCT sp.거래처ID) as 거래처수,
    SUM(sp."202410") as 최근월_매출
FROM 인사자료 i
INNER JOIN sales_performance sp ON i.사번 = sp.사번
WHERE i.부서 = '영업1팀'
GROUP BY i.부서;
```

## 📈 고급 분석 쿼리

### 1. 전월 대비 성장률

**자연어 질문**: "2024년 10월 전월 대비 성장률이 높은 거래처"
```sql
SELECT
    거래처ID,
    "202409" as 전월,
    "202410" as 당월,
    ROUND((CAST("202410" AS FLOAT) - "202409") / "202409" * 100, 2) as 성장률
FROM sales_performance
WHERE "202409" > 0 AND "202410" > 0
ORDER BY 성장률 DESC
LIMIT 10;
```

### 2. 품목별 판매 분석

**자연어 질문**: "품목별 2024년 누적 판매액"
```sql
SELECT
    품목,
    COUNT(DISTINCT 거래처ID) as 거래처수,
    SUM("202401" + "202402" + "202403" + "202404" + "202405" +
        "202406" + "202407" + "202408" + "202409" + "202410") as 누적판매액
FROM sales_performance
GROUP BY 품목
ORDER BY 누적판매액 DESC;
```

## 💡 쿼리 작성 팁

### 1. 날짜 처리
- 월별 컬럼은 YYYYMM 형식 (예: 202401)
- 범위 조회 시 여러 컬럼 합산 필요

### 2. 한글 컬럼명
- 컬럼명에 특수문자가 있으면 큰따옴표 사용
- 예: `"기본급(₩)"`, `"지점 연락처"`

### 3. 데이터 타입 변환
- 금액 필드에 콤마나 원화 기호가 있을 수 있음
- CAST와 REPLACE 함수로 숫자 변환 필요

### 4. NULL 처리
- COALESCE 함수로 NULL 값 대체
- LEFT JOIN 시 NULL 가능성 고려

### 5. 성능 최적화
- 필요한 컬럼만 SELECT
- WHERE 절로 데이터 필터링
- 인덱스 활용 (사번, 거래처ID 등)

## 🔍 자주 묻는 질문 패턴

1. **인원/수량**: "~가 몇 명이야?", "~의 개수는?"
   → COUNT(*) 사용

2. **순위**: "Top N", "가장 높은/낮은"
   → ORDER BY + LIMIT 사용

3. **비교**: "~보다 많은/적은", "평균 이상"
   → 서브쿼리나 HAVING 절 사용

4. **기간**: "이번 달", "작년", "상반기"
   → 해당 월 컬럼 선택 또는 합산

5. **조건**: "~이면서 ~인", "~이거나 ~인"
   → AND/OR 조건 조합

## 📝 주의사항

1. **데이터 정합성**
   - 직원명과 담당자명 일치 확인
   - 거래처ID 형식 일관성 확인

2. **권한 관리**
   - 급여 정보 등 민감 데이터 접근 제한
   - 부서별 조회 권한 설정

3. **쿼리 검증**
   - 대량 데이터 조회 시 LIMIT 사용
   - JOIN 조건 정확성 확인
   - 집계 함수 사용 시 GROUP BY 확인