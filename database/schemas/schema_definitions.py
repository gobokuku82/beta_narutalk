"""
SQLite 데이터베이스 스키마 정의
Text2SQL 엔진을 위한 테이블 구조 정보
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class DataType(Enum):
    """SQL 데이터 타입"""
    TEXT = "TEXT"
    INTEGER = "INTEGER"
    REAL = "REAL"
    BLOB = "BLOB"
    NULL = "NULL"


@dataclass
class ColumnInfo:
    """컬럼 정보"""
    name: str
    data_type: str
    nullable: bool = True
    primary_key: bool = False
    default: Any = None
    description: str = ""


@dataclass
class TableInfo:
    """테이블 정보"""
    name: str
    database: str
    columns: List[ColumnInfo]
    description: str = ""
    row_count: int = 0


# HR 데이터베이스 스키마
HR_SCHEMA = {
    "database": "hr_data.db",
    "path": "database/storage/hr_information/hr_data.db",
    "tables": {
        "인사자료": TableInfo(
            name="인사자료",
            database="hr_data",
            description="직원 인사 정보 관리 테이블",
            row_count=80,
            columns=[
                ColumnInfo(name="사번", data_type="TEXT", description="직원 고유 식별 번호"),
                ColumnInfo(name="성명", data_type="TEXT", description="직원 이름"),
                ColumnInfo(name="본부", data_type="TEXT", description="소속 본부"),
                ColumnInfo(name="직급", data_type="TEXT", description="직원 직급"),
                ColumnInfo(name="부서", data_type="TEXT", description="소속 부서"),
                ColumnInfo(name="지점", data_type="TEXT", description="근무 지점"),
                ColumnInfo(name="연락처", data_type="TEXT", description="직원 연락처"),
                ColumnInfo(name="월평균사용예산", data_type="REAL", description="월 평균 사용 예산"),
                ColumnInfo(name="최근 평가", data_type="TEXT", description="최근 인사 평가 결과"),
                ColumnInfo(name="기본급(₩)", data_type="TEXT", description="기본 급여"),
                ColumnInfo(name="성과급(₩)", data_type="TEXT", description="성과 급여"),
                ColumnInfo(name="책임업무", data_type="TEXT", description="주요 책임 업무"),
            ]
        ),
        "지점연락처": TableInfo(
            name="지점연락처",
            database="hr_data",
            description="지점별 연락처 정보",
            row_count=14,
            columns=[
                ColumnInfo(name="본부", data_type="TEXT", description="본부명"),
                ColumnInfo(name="부서", data_type="TEXT", description="부서명"),
                ColumnInfo(name="지점", data_type="TEXT", description="지점명"),
                ColumnInfo(name="지점 연락처", data_type="TEXT", description="지점 대표 연락처"),
            ]
        )
    }
}

# 영업 실적 데이터베이스 스키마
SALES_SCHEMA = {
    "clients_db": {
        "database": "clients_db.db",
        "path": "database/storage/sales_performance/clients_db.db",
        "tables": {
            "거래처자료": TableInfo(
                name="거래처자료",
                database="clients_db",
                description="거래처별 월간 실적 데이터",
                row_count=6912,
                columns=[
                    ColumnInfo(name="거래처ID", data_type="TEXT", description="거래처 고유 식별자"),
                    ColumnInfo(name="월", data_type="INTEGER", description="데이터 월 (YYYYMM)"),
                    ColumnInfo(name="매출", data_type="INTEGER", description="월 매출액"),
                    ColumnInfo(name="월방문횟수", data_type="INTEGER", description="월간 방문 횟수"),
                    ColumnInfo(name="사용 예산", data_type="INTEGER", description="월간 사용 예산"),
                    ColumnInfo(name="총환자수", data_type="INTEGER", description="월간 총 환자 수"),
                    ColumnInfo(name="담당자", data_type="TEXT", description="담당 직원명"),
                ]
            )
        }
    },
    "clients_info": {
        "database": "clients_info.db",
        "path": "database/storage/sales_performance/clients_info.db",
        "tables": {
            "거래처정보": TableInfo(
                name="거래처정보",
                database="clients_info",
                description="거래처 기본 정보",
                row_count=288,
                columns=[
                    ColumnInfo(name="ID", data_type="TEXT", description="거래처 고유 ID"),
                    ColumnInfo(name="원장명", data_type="TEXT", description="병원장/원장 이름"),
                    ColumnInfo(name="지역구", data_type="TEXT", description="소재 지역구"),
                    ColumnInfo(name="병원연락처", data_type="TEXT", description="병원 대표 연락처"),
                ]
            )
        }
    },
    "sales_performance": {
        "database": "sales_performance_db.db",
        "path": "database/storage/sales_performance/sales_performance_db.db",
        "tables": {
            "sales_performance": TableInfo(
                name="sales_performance",
                database="sales_performance_db",
                description="직원별 거래처별 월간 판매 실적",
                row_count=1711,
                columns=[
                    ColumnInfo(name="사번", data_type="TEXT", description="직원 사번"),
                    ColumnInfo(name="담당자", data_type="TEXT", description="담당 직원명"),
                    ColumnInfo(name="거래처ID", data_type="TEXT", description="거래처 고유 ID"),
                    ColumnInfo(name="품목", data_type="TEXT", description="판매 품목"),
                    # 월별 실적 컬럼들 (202212 ~ 202411)
                    ColumnInfo(name="202212", data_type="INTEGER", description="2022년 12월 판매 실적"),
                    ColumnInfo(name="202301", data_type="INTEGER", description="2023년 1월 판매 실적"),
                    ColumnInfo(name="202302", data_type="INTEGER", description="2023년 2월 판매 실적"),
                    ColumnInfo(name="202303", data_type="INTEGER", description="2023년 3월 판매 실적"),
                    ColumnInfo(name="202304", data_type="INTEGER", description="2023년 4월 판매 실적"),
                    ColumnInfo(name="202305", data_type="INTEGER", description="2023년 5월 판매 실적"),
                    ColumnInfo(name="202306", data_type="INTEGER", description="2023년 6월 판매 실적"),
                    ColumnInfo(name="202307", data_type="INTEGER", description="2023년 7월 판매 실적"),
                    ColumnInfo(name="202308", data_type="INTEGER", description="2023년 8월 판매 실적"),
                    ColumnInfo(name="202309", data_type="INTEGER", description="2023년 9월 판매 실적"),
                    ColumnInfo(name="202310", data_type="INTEGER", description="2023년 10월 판매 실적"),
                    ColumnInfo(name="202311", data_type="INTEGER", description="2023년 11월 판매 실적"),
                    ColumnInfo(name="202312", data_type="INTEGER", description="2023년 12월 판매 실적"),
                    ColumnInfo(name="202401", data_type="INTEGER", description="2024년 1월 판매 실적"),
                    ColumnInfo(name="202402", data_type="INTEGER", description="2024년 2월 판매 실적"),
                    ColumnInfo(name="202403", data_type="INTEGER", description="2024년 3월 판매 실적"),
                    ColumnInfo(name="202404", data_type="INTEGER", description="2024년 4월 판매 실적"),
                    ColumnInfo(name="202405", data_type="INTEGER", description="2024년 5월 판매 실적"),
                    ColumnInfo(name="202406", data_type="INTEGER", description="2024년 6월 판매 실적"),
                    ColumnInfo(name="202407", data_type="INTEGER", description="2024년 7월 판매 실적"),
                    ColumnInfo(name="202408", data_type="INTEGER", description="2024년 8월 판매 실적"),
                    ColumnInfo(name="202409", data_type="INTEGER", description="2024년 9월 판매 실적"),
                    ColumnInfo(name="202410", data_type="INTEGER", description="2024년 10월 판매 실적"),
                    ColumnInfo(name="202411", data_type="INTEGER", description="2024년 11월 판매 실적"),
                ]
            )
        }
    },
    "sales_target": {
        "database": "sales_target_db.db",
        "path": "database/storage/sales_performance/sales_target_db.db",
        "tables": {
            "지점별목표": TableInfo(
                name="지점별목표",
                database="sales_target_db",
                description="지점별 월간 판매 목표",
                row_count=6,
                columns=[
                    ColumnInfo(name="지점", data_type="TEXT", description="지점명"),
                    ColumnInfo(name="담당자", data_type="TEXT", description="담당자명"),
                    ColumnInfo(name="202312", data_type="INTEGER", description="2023년 12월 목표"),
                    ColumnInfo(name="202401", data_type="INTEGER", description="2024년 1월 목표"),
                    ColumnInfo(name="202402", data_type="INTEGER", description="2024년 2월 목표"),
                    ColumnInfo(name="202403", data_type="INTEGER", description="2024년 3월 목표"),
                    ColumnInfo(name="202404", data_type="INTEGER", description="2024년 4월 목표"),
                    ColumnInfo(name="202405", data_type="INTEGER", description="2024년 5월 목표"),
                    ColumnInfo(name="202406", data_type="INTEGER", description="2024년 6월 목표"),
                    ColumnInfo(name="202407", data_type="INTEGER", description="2024년 7월 목표"),
                    ColumnInfo(name="202408", data_type="INTEGER", description="2024년 8월 목표"),
                    ColumnInfo(name="202409", data_type="INTEGER", description="2024년 9월 목표"),
                    ColumnInfo(name="202410", data_type="INTEGER", description="2024년 10월 목표"),
                    ColumnInfo(name="202411", data_type="INTEGER", description="2024년 11월 목표"),
                ]
            )
        }
    }
}


def get_all_schemas() -> Dict[str, Any]:
    """모든 데이터베이스 스키마 반환"""
    return {
        "hr_data": HR_SCHEMA,
        "sales": SALES_SCHEMA
    }


def get_table_schema(database_name: str, table_name: str) -> TableInfo:
    """특정 테이블의 스키마 정보 반환"""
    schemas = get_all_schemas()

    if database_name == "hr_data":
        if table_name in schemas["hr_data"]["tables"]:
            return schemas["hr_data"]["tables"][table_name]
    elif database_name in ["clients_db", "clients_info", "sales_performance", "sales_target"]:
        if table_name in schemas["sales"][database_name]["tables"]:
            return schemas["sales"][database_name]["tables"][table_name]

    raise ValueError(f"Table '{table_name}' not found in database '{database_name}'")


def get_database_path(database_name: str) -> str:
    """데이터베이스 파일 경로 반환"""
    schemas = get_all_schemas()

    if database_name == "hr_data":
        return schemas["hr_data"]["path"]
    elif database_name in schemas["sales"]:
        return schemas["sales"][database_name]["path"]

    raise ValueError(f"Database '{database_name}' not found")


def list_all_tables() -> List[tuple]:
    """모든 테이블 목록 반환 (database_name, table_name)"""
    tables = []
    schemas = get_all_schemas()

    # HR 데이터베이스
    for table_name in schemas["hr_data"]["tables"]:
        tables.append(("hr_data", table_name))

    # Sales 데이터베이스들
    for db_name, db_info in schemas["sales"].items():
        for table_name in db_info["tables"]:
            tables.append((db_name, table_name))

    return tables


if __name__ == "__main__":
    # 스키마 정보 확인용 테스트
    print("=== 전체 테이블 목록 ===")
    for db, table in list_all_tables():
        print(f"- {db}.{table}")

    print("\n=== HR 인사자료 테이블 스키마 ===")
    hr_table = get_table_schema("hr_data", "인사자료")
    print(f"테이블명: {hr_table.name}")
    print(f"설명: {hr_table.description}")
    print(f"행 개수: {hr_table.row_count}")
    print("컬럼:")
    for col in hr_table.columns:
        print(f"  - {col.name} ({col.data_type}): {col.description}")