"""Check actual employees in database"""
import sqlite3
from pathlib import Path

# Database path
db_path = Path("database/storage/sales_performance/sales_performance_db.db")

# Connect to database
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Get all unique employee names
cursor.execute("SELECT DISTINCT 담당자 FROM sales_performance WHERE 담당자 IS NOT NULL")
names = sorted([row[0] for row in cursor.fetchall()])

print("실적이 있는 직원 목록:")
for name in names:
    print(f"  - {name}")

print(f"\n총 {len(names)}명")

# Check specific names
test_names = ['김민지', '이서준', '박지훈', '정미래', '김하늘', '이준호',
               '박서연', '김지우', '이민준', '최지호', '정다은', '김서현']

print("\n추가한 직원 중 실제 데이터베이스에 있는 사람:")
for name in test_names:
    if name in names:
        print(f"  O {name}")
    else:
        print(f"  X {name} (없음)")

conn.close()