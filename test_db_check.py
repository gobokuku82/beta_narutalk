"""
데이터베이스 구조 및 데이터 확인 스크립트
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

def check_database():
    """데이터베이스 확인"""

    # sales_performance_db.db 확인
    print("=" * 60)
    print("sales_performance_db.db 확인")
    print("=" * 60)

    conn = sqlite3.connect('database/storage/sales_performance/sales_performance_db.db')
    cursor = conn.cursor()

    # 테이블 구조 확인
    cursor.execute("PRAGMA table_info(sales_performance)")
    columns = cursor.fetchall()

    print("\n컬럼 정보:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")

    # 실제 컬럼명 확인 (첫 번째 행의 데이터로 추정)
    cursor.execute("SELECT * FROM sales_performance LIMIT 1")
    sample = cursor.fetchone()

    if sample:
        print(f"\n첫 번째 행 데이터 (컬럼 수: {len(sample)}):")
        for i, value in enumerate(sample):
            print(f"  컬럼[{i}]: {value}")

    # 직원명으로 추정되는 두 번째 컬럼의 고유 값 확인
    cursor.execute("SELECT DISTINCT \"직원명\" FROM sales_performance")
    employees = cursor.fetchall()

    print(f"\n직원 목록 (총 {len(employees)}명):")
    for emp in employees[:10]:  # 처음 10명만
        print(f"  - {emp[0]}")

    # 연도별 데이터 확인
    cursor.execute("SELECT \"직원명\", \"202401\", \"202402\", \"202403\" FROM sales_performance WHERE \"직원명\" IN ('윤수아', '최수아') LIMIT 10")
    data = cursor.fetchall()

    print("\n윤수아, 최수아 2024년 1-3월 데이터:")
    for row in data:
        print(f"  {row}")

    conn.close()

    print("\n" + "=" * 60)
    print("결론:")
    print("  - 테이블명: sales_performance")
    print("  - 직원명 컬럼: '직원명' (두 번째 컬럼)")
    print("  - 월별 데이터 컬럼: YYYYMM 형식 (예: '202401')")
    print("  - 인코딩: UTF-8 필요")
    print("=" * 60)

if __name__ == "__main__":
    check_database()