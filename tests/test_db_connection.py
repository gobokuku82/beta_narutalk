"""
데이터베이스 연결 테스트
모든 DB 파일의 존재 여부와 연결 상태를 확인
"""

import sqlite3
import os
from pathlib import Path
import chromadb
from chromadb.config import Settings

def test_hr_database(db_paths, schema_info):
    """HR 데이터베이스 연결 및 스키마 테스트"""
    print("\n=== HR 데이터베이스 테스트 ===")

    db_path = Path(db_paths["hr_data"])

    # 파일 존재 확인
    assert db_path.exists(), f"HR DB 파일이 존재하지 않습니다: {db_path}"
    print(f"✓ HR DB 파일 존재: {db_path}")

    # DB 연결 테스트
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 테이블 목록 확인
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    # 스키마 정의된 테이블 확인
    expected_tables = list(schema_info["hr"]["tables"].keys())
    for table_name in expected_tables:
        assert table_name in tables, f"테이블 '{table_name}'이 없습니다"
        print(f"✓ 테이블 확인: {table_name}")

        # 행 개수 확인
        cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
        row_count = cursor.fetchone()[0]
        expected_count = schema_info["hr"]["tables"][table_name].row_count
        print(f"  - 행 개수: {row_count} (예상: {expected_count})")

        # 컬럼 정보 확인
        cursor.execute(f"PRAGMA table_info('{table_name}')")
        columns = cursor.fetchall()
        print(f"  - 컬럼 개수: {len(columns)}")

    conn.close()
    print("✅ HR 데이터베이스 테스트 완료")

def test_sales_databases(db_paths, schema_info):
    """영업 실적 데이터베이스들 연결 테스트"""
    print("\n=== 영업 실적 데이터베이스 테스트 ===")

    sales_dbs = ["clients_db", "clients_info", "sales_performance", "sales_target"]

    for db_name in sales_dbs:
        db_path = Path(db_paths[db_name])

        # 파일 존재 확인
        assert db_path.exists(), f"{db_name} 파일이 없습니다: {db_path}"
        print(f"\n✓ {db_name} 파일 존재")

        # DB 연결 및 테이블 확인
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # 테이블 정보 가져오기
        if db_name in schema_info["sales"]:
            db_schema = schema_info["sales"][db_name]
            expected_tables = list(db_schema["tables"].keys())

            for table_name in expected_tables:
                # 테이블 존재 확인
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name,)
                )
                result = cursor.fetchone()
                assert result is not None, f"테이블 '{table_name}'이 없습니다"

                # 행 개수 확인
                cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
                row_count = cursor.fetchone()[0]
                expected_count = db_schema["tables"][table_name].row_count
                print(f"  - {table_name}: {row_count} rows (예상: {expected_count})")

        conn.close()

    print("\n✅ 영업 실적 데이터베이스 테스트 완료")

def test_chromadb_connections(db_paths):
    """ChromaDB 연결 테스트"""
    print("\n=== ChromaDB 벡터 데이터베이스 테스트 ===")

    # HR Rules ChromaDB
    hr_rules_path = Path(db_paths["hr_rules_chroma"])
    if hr_rules_path.exists():
        print(f"✓ HR Rules ChromaDB 경로 존재: {hr_rules_path}")

        try:
            client = chromadb.PersistentClient(
                path=str(hr_rules_path),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=False
                )
            )
            collections = client.list_collections()
            print(f"  - 컬렉션 개수: {len(collections)}")
            for col in collections:
                print(f"    • {col.name}")
        except Exception as e:
            print(f"  ⚠ ChromaDB 연결 경고: {e}")
    else:
        print(f"⚠ HR Rules ChromaDB 경로 없음: {hr_rules_path}")

    # Compliance ChromaDB
    compliance_path = Path(db_paths["compliance_chroma"])
    if compliance_path.exists():
        print(f"✓ Compliance ChromaDB 경로 존재: {compliance_path}")

        try:
            client = chromadb.PersistentClient(
                path=str(compliance_path),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=False
                )
            )
            collections = client.list_collections()
            print(f"  - 컬렉션 개수: {len(collections)}")
            for col in collections:
                print(f"    • {col.name}")
        except Exception as e:
            print(f"  ⚠ ChromaDB 연결 경고: {e}")
    else:
        print(f"⚠ Compliance ChromaDB 경로 없음: {compliance_path}")

    print("\n✅ ChromaDB 테스트 완료")

def test_sample_query(db_paths):
    """샘플 쿼리 실행 테스트"""
    print("\n=== 샘플 쿼리 실행 테스트 ===")

    # HR DB에서 간단한 쿼리 실행
    hr_db = Path(db_paths["hr_data"])
    if hr_db.exists():
        conn = sqlite3.connect(str(hr_db))
        cursor = conn.cursor()

        # 부서별 인원수 조회
        query = """
        SELECT 부서, COUNT(*) as 인원수
        FROM 인사자료
        GROUP BY 부서
        ORDER BY 인원수 DESC
        LIMIT 5
        """

        cursor.execute(query)
        results = cursor.fetchall()

        print("\n부서별 인원수 (Top 5):")
        for dept, count in results:
            print(f"  - {dept}: {count}명")

        conn.close()

    # Sales DB에서 간단한 쿼리 실행
    sales_db = Path(db_paths["sales_performance"])
    if sales_db.exists():
        conn = sqlite3.connect(str(sales_db))
        cursor = conn.cursor()

        # 최근 월 실적 합계
        query = """
        SELECT SUM("202410") as 총실적
        FROM sales_performance
        WHERE "202410" IS NOT NULL
        """

        try:
            cursor.execute(query)
            result = cursor.fetchone()
            if result and result[0]:
                print(f"\n2024년 10월 총 실적: {result[0]:,}원")
        except Exception as e:
            print(f"\n쿼리 실행 오류: {e}")

        conn.close()

    print("\n✅ 샘플 쿼리 테스트 완료")

# 독립 실행 가능한 테스트
if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 프로젝트 루트 추가
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from database.schemas.schema_definitions import HR_SCHEMA, SALES_SCHEMA
    import os
    from dotenv import load_dotenv

    # 환경 변수 로드
    load_dotenv()

    # DB 경로 설정
    db_paths = {
        "hr_data": os.getenv("HR_DB_PATH", "./database/storage/hr_information/hr_data.db"),
        "clients_db": os.getenv("CLIENTS_DB_PATH", "./database/storage/sales_performance/clients_db.db"),
        "clients_info": os.getenv("CLIENTS_INFO_PATH", "./database/storage/sales_performance/clients_info.db"),
        "sales_performance": os.getenv("SALES_PERFORMANCE_PATH", "./database/storage/sales_performance/sales_performance_db.db"),
        "sales_target": os.getenv("SALES_TARGET_PATH", "./database/storage/sales_performance/sales_target_db.db"),
        "hr_rules_chroma": os.getenv("HR_RULES_CHROMA_PATH", "./database/storage/hr_rules/chromadb"),
        "compliance_chroma": os.getenv("COMPLIANCE_CHROMA_PATH", "./database/storage/rules_compliance/chroma_db")
    }

    schema_info = {
        "hr": HR_SCHEMA,
        "sales": SALES_SCHEMA
    }

    print("=" * 60)
    print("데이터베이스 연결 테스트 시작")
    print("=" * 60)

    try:
        test_hr_database(db_paths, schema_info)
        test_sales_databases(db_paths, schema_info)
        test_chromadb_connections(db_paths)
        test_sample_query(db_paths)

        print("\n" + "=" * 60)
        print("✅ 모든 데이터베이스 테스트 성공!")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)