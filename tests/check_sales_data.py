"""
윤수아와 최수아의 실적 데이터 확인
"""

import sqlite3
import sys
import io

# Windows 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding='utf-8',
        errors='replace'
    )

# 데이터베이스 연결
conn = sqlite3.connect('database/storage/sales_performance/sales_performance_db.db')
cursor = conn.cursor()

# 2023년과 2024년 실적 조회
query = """
SELECT
    담당자,
    SUM("202301" + "202302" + "202303" + "202304" + "202305" + "202306" +
        "202307" + "202308" + "202309" + "202310" + "202311" + "202312") as total_2023,
    SUM("202401" + "202402" + "202403" + "202404" + "202405" + "202406" +
        "202407" + "202408" + "202409" + "202410" + "202411") as total_2024
FROM sales_performance
WHERE 담당자 IN ('윤수아', '최수아')
GROUP BY 담당자
"""

cursor.execute(query)
data = cursor.fetchall()

print("=" * 60)
print("윤수아와 최수아의 2023년 vs 2024년 실적 비교")
print("=" * 60)

for row in data:
    name = row[0]
    sales_2023 = row[1] if row[1] else 0
    sales_2024 = row[2] if row[2] else 0

    growth = sales_2024 - sales_2023
    growth_rate = (growth / sales_2023 * 100) if sales_2023 > 0 else 0

    print(f"\n{name}:")
    print(f"  2023년: {sales_2023:,}원")
    print(f"  2024년: {sales_2024:,}원")
    print(f"  성장금액: {growth:,}원")
    print(f"  성장률: {growth_rate:.1f}%")

# 월별 상세 데이터 확인
print("\n" + "=" * 60)
print("월별 상세 데이터 (샘플)")
print("=" * 60)

query2 = """
SELECT 담당자, "202301", "202302", "202303", "202401", "202402", "202403"
FROM sales_performance
WHERE 담당자 IN ('윤수아', '최수아')
LIMIT 5
"""

cursor.execute(query2)
samples = cursor.fetchall()

print("\n담당자 | 2023-01 | 2023-02 | 2023-03 | 2024-01 | 2024-02 | 2024-03")
print("-" * 70)
for row in samples:
    print(f"{row[0]} | {row[1]:,} | {row[2]:,} | {row[3]:,} | {row[4]:,} | {row[5]:,} | {row[6]:,}")

conn.close()