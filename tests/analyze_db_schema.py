"""
데이터베이스 스키마 분석 도구
"""

import sqlite3
import os
import sys
import io
from pathlib import Path

# Windows 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding='utf-8',
        errors='replace'
    )

def analyze_database(db_path):
    """데이터베이스 스키마 분석"""

    print(f"\n{'='*80}")
    print(f"📁 Database: {Path(db_path).name}")
    print(f"{'='*80}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 테이블 목록 조회
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        print(f"📊 Tables: {len(tables)}")

        for table_name in tables:
            table = table_name[0]
            print(f"\n📋 Table: {table}")
            print("-" * 60)

            # 테이블 스키마 조회
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()

            print(f"Columns ({len(columns)}):")
            for col in columns:
                cid, name, dtype, notnull, default, pk = col
                pk_marker = " [PK]" if pk else ""
                notnull_marker = " NOT NULL" if notnull else ""
                default_marker = f" DEFAULT {default}" if default else ""
                print(f"  {cid+1:3}. {name:30} {dtype:15}{pk_marker}{notnull_marker}{default_marker}")

            # 인덱스 조회
            cursor.execute(f"PRAGMA index_list({table})")
            indexes = cursor.fetchall()
            if indexes:
                print(f"\nIndexes:")
                for idx in indexes:
                    print(f"  - {idx[1]}")

            # 행 수 조회
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cursor.fetchone()[0]
            print(f"\nRows: {row_count:,}")

            # 샘플 데이터 (처음 3개)
            cursor.execute(f"SELECT * FROM {table} LIMIT 3")
            samples = cursor.fetchall()
            if samples:
                print(f"\nSample Data:")
                # 컬럼명 가져오기
                col_names = [col[1] for col in columns]

                for i, row in enumerate(samples, 1):
                    print(f"  Row {i}:")
                    for j, (col_name, value) in enumerate(zip(col_names, row)):
                        if value is not None:
                            if isinstance(value, (int, float)):
                                print(f"    {col_name}: {value:,}" if isinstance(value, int) else f"    {col_name}: {value:.2f}")
                            else:
                                print(f"    {col_name}: {str(value)[:100]}")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """메인 함수"""

    db_dir = r"C:\kdy\Projects\narutalk_upgrade\beta_v0033\database\storage\sales_performance"

    print("=" * 80)
    print("🔍 Sales Performance Database Schema Analysis")
    print("=" * 80)

    # 데이터베이스 파일 목록
    db_files = [
        "sales_performance_db.db",
        "sales_target_db.db",
        "clients_db.db",
        "clients_info.db"
    ]

    for db_file in db_files:
        db_path = os.path.join(db_dir, db_file)
        if os.path.exists(db_path):
            analyze_database(db_path)
        else:
            print(f"\n⚠️ File not found: {db_file}")

    print("\n" + "=" * 80)
    print("✅ Analysis Complete")
    print("=" * 80)


if __name__ == "__main__":
    main()