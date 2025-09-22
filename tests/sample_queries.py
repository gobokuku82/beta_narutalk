"""
테스트용 샘플 쿼리 모음
스키마 문서 기반 실제 쿼리
"""

# HR 관련 쿼리
HR_QUERIES = [
    {
        "id": "hr_001",
        "natural": "김철수 과장의 정보를 보여줘",
        "sql": "SELECT * FROM 인사자료 WHERE 성명='김철수' AND 직급='과장'",
        "db": "hr_data",
        "table": "인사자료"
    },
    {
        "id": "hr_002",
        "natural": "영업1팀 직원 목록",
        "sql": "SELECT 사번, 성명, 직급, 연락처 FROM 인사자료 WHERE 부서='영업1팀' ORDER BY 직급 DESC",
        "db": "hr_data",
        "table": "인사자료"
    },
    {
        "id": "hr_003",
        "natural": "부서별 인원수를 알려줘",
        "sql": "SELECT 부서, COUNT(*) as 인원수 FROM 인사자료 GROUP BY 부서 ORDER BY 인원수 DESC",
        "db": "hr_data",
        "table": "인사자료"
    },
    {
        "id": "hr_004",
        "natural": "서울 지점들의 연락처",
        "sql": "SELECT 지점, \"지점 연락처\" FROM 지점연락처 WHERE 지점 LIKE '%서울%'",
        "db": "hr_data",
        "table": "지점연락처"
    }
]

# 영업 실적 관련 쿼리
SALES_QUERIES = [
    {
        "id": "sales_001",
        "natural": "2024년 10월 실적 Top 5",
        "sql": """
            SELECT 담당자, SUM("202410") as 실적
            FROM sales_performance
            WHERE "202410" IS NOT NULL
            GROUP BY 담당자
            ORDER BY 실적 DESC
            LIMIT 5
        """,
        "db": "sales_performance",
        "table": "sales_performance"
    },
    {
        "id": "sales_002",
        "natural": "매출 top 10 거래처는?",
        "sql": """
            SELECT cd.거래처ID, ci.원장명, ci.지역구, SUM(cd.매출) as 총매출
            FROM 거래처자료 cd
            LEFT JOIN 거래처정보 ci ON cd.거래처ID = ci.ID
            GROUP BY cd.거래처ID, ci.원장명, ci.지역구
            ORDER BY 총매출 DESC
            LIMIT 10
        """,
        "db": "clients_db",
        "table": "거래처자료"
    },
    {
        "id": "sales_003",
        "natural": "2024년 상반기 직원별 총 실적",
        "sql": """
            SELECT 담당자,
                   SUM("202401" + "202402" + "202403" + "202404" + "202405" + "202406") as 상반기_총실적
            FROM sales_performance
            GROUP BY 담당자
            ORDER BY 상반기_총실적 DESC
        """,
        "db": "sales_performance",
        "table": "sales_performance"
    },
    {
        "id": "sales_004",
        "natural": "서울 지역 거래처들의 평균 월 방문 횟수",
        "sql": """
            SELECT ci.지역구, AVG(cd.월방문횟수) as 평균방문횟수
            FROM 거래처자료 cd
            INNER JOIN 거래처정보 ci ON cd.거래처ID = ci.ID
            WHERE ci.지역구 LIKE '%서울%'
            GROUP BY ci.지역구
        """,
        "db": "clients_db",
        "table": "거래처자료"
    }
]

# 목표 대비 실적 쿼리
TARGET_QUERIES = [
    {
        "id": "target_001",
        "natural": "2024년 10월 지점별 목표 달성률",
        "sql": """
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
            WHERE t."202410" > 0
        """,
        "db": "sales_target",
        "table": "지점별목표"
    }
]

# 복합 조인 쿼리
COMPLEX_QUERIES = [
    {
        "id": "complex_001",
        "natural": "김철수가 담당하는 거래처들의 정보와 실적",
        "sql": """
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
            ORDER BY cd.월 DESC
        """,
        "db": "multiple",
        "tables": ["인사자료", "거래처자료", "거래처정보"]
    },
    {
        "id": "complex_002",
        "natural": "영업1팀이 관리하는 거래처 수와 총 매출",
        "sql": """
            SELECT
                i.부서,
                COUNT(DISTINCT sp.거래처ID) as 거래처수,
                SUM(sp."202410") as 최근월_매출
            FROM 인사자료 i
            INNER JOIN sales_performance sp ON i.사번 = sp.사번
            WHERE i.부서 = '영업1팀'
            GROUP BY i.부서
        """,
        "db": "multiple",
        "tables": ["인사자료", "sales_performance"]
    }
]

# 모든 쿼리 모음
ALL_QUERIES = {
    "hr": HR_QUERIES,
    "sales": SALES_QUERIES,
    "target": TARGET_QUERIES,
    "complex": COMPLEX_QUERIES
}

def get_query_by_id(query_id: str):
    """ID로 쿼리 찾기"""
    for category in ALL_QUERIES.values():
        for query in category:
            if query["id"] == query_id:
                return query
    return None

def get_queries_by_category(category: str):
    """카테고리별 쿼리 반환"""
    return ALL_QUERIES.get(category, [])

def get_random_queries(n: int = 5):
    """랜덤 쿼리 선택"""
    import random
    all_queries_flat = []
    for queries in ALL_QUERIES.values():
        all_queries_flat.extend(queries)
    return random.sample(all_queries_flat, min(n, len(all_queries_flat)))

# 테스트용 간단한 쿼리
SIMPLE_TEST_QUERIES = [
    "SELECT COUNT(*) FROM 인사자료",
    "SELECT COUNT(*) FROM 거래처자료",
    "SELECT * FROM 인사자료 LIMIT 5",
    "SELECT DISTINCT 부서 FROM 인사자료",
    "SELECT DISTINCT 지점 FROM 인사자료"
]

if __name__ == "__main__":
    print("=== 샘플 쿼리 목록 ===\n")

    for category, queries in ALL_QUERIES.items():
        print(f"\n[{category.upper()}]")
        for query in queries:
            print(f"  - {query['id']}: {query['natural']}")

    print(f"\n총 {sum(len(q) for q in ALL_QUERIES.values())}개의 쿼리가 준비되어 있습니다.")