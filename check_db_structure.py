"""
데이터베이스 구조 확인 스크립트
"""
import sqlite3
import os

def check_hr_db():
    """HR 데이터베이스 구조 확인"""
    db_path = "database/hr_information/hr_data.db"

    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 테이블 목록
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("\n=== HR Database Tables ===")
    for table in tables:
        print(f"- {table[0]}")

        # 각 테이블의 컬럼 정보
        cursor.execute(f"PRAGMA table_info('{table[0]}')")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  * {col[1]} ({col[2]})")

        # 샘플 데이터 확인
        cursor.execute(f"SELECT * FROM '{table[0]}' LIMIT 2")
        samples = cursor.fetchall()
        if samples:
            print(f"  Sample data (first 2 rows):")
            for sample in samples:
                print(f"    {sample}")

    conn.close()

def check_sales_db():
    """Sales 데이터베이스 구조 확인"""
    db_path = "database/sales_performance_db"

    # 디렉토리 내 .db 파일 찾기
    if os.path.isdir(db_path):
        for file in os.listdir(db_path):
            if file.endswith('.db'):
                full_path = os.path.join(db_path, file)
                print(f"\n=== Sales Database: {file} ===")

                conn = sqlite3.connect(full_path)
                cursor = conn.cursor()

                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                for table in tables:
                    print(f"- {table[0]}")

                    cursor.execute(f"PRAGMA table_info('{table[0]}')")
                    columns = cursor.fetchall()
                    for col in columns:
                        print(f"  * {col[1]} ({col[2]})")

                conn.close()

def check_main_db():
    """메인 데이터베이스 구조 확인"""
    db_path = "pharma_chatbot.db"

    if os.path.exists(db_path):
        print("\n=== Main Database (pharma_chatbot.db) ===")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            print(f"- {table[0]}")

        conn.close()

if __name__ == "__main__":
    check_hr_db()
    check_sales_db()
    check_main_db()