"""
Pytest configuration and fixtures
테스트 환경 설정 및 공통 fixture
"""

import pytest
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 환경 변수 로드
load_dotenv(project_root / ".env")

# 스키마 정보 임포트
from database.schemas.schema_definitions import (
    HR_SCHEMA,
    SALES_SCHEMA,
    get_database_path,
    get_table_schema
)

@pytest.fixture(scope="session")
def project_dir():
    """프로젝트 루트 디렉토리"""
    return project_root

@pytest.fixture(scope="session")
def db_paths():
    """데이터베이스 파일 경로 딕셔너리"""
    return {
        "hr_data": os.getenv("HR_DB_PATH", "./database/storage/hr_information/hr_data.db"),
        "clients_db": os.getenv("CLIENTS_DB_PATH", "./database/storage/sales_performance/clients_db.db"),
        "clients_info": os.getenv("CLIENTS_INFO_PATH", "./database/storage/sales_performance/clients_info.db"),
        "sales_performance": os.getenv("SALES_PERFORMANCE_PATH", "./database/storage/sales_performance/sales_performance_db.db"),
        "sales_target": os.getenv("SALES_TARGET_PATH", "./database/storage/sales_performance/sales_target_db.db"),
        "hr_rules_chroma": os.getenv("HR_RULES_CHROMA_PATH", "./database/storage/hr_rules/chromadb"),
        "compliance_chroma": os.getenv("COMPLIANCE_CHROMA_PATH", "./database/storage/rules_compliance/chroma_db")
    }

@pytest.fixture(scope="session")
def schema_info():
    """데이터베이스 스키마 정보"""
    return {
        "hr": HR_SCHEMA,
        "sales": SALES_SCHEMA
    }

@pytest.fixture
def sample_queries():
    """테스트용 샘플 쿼리"""
    return {
        "hr_simple": "김철수 과장의 정보를 보여줘",
        "hr_list": "영업1팀 직원 목록",
        "sales_top": "2024년 10월 실적 Top 5",
        "sales_region": "서울 지역 거래처 매출",
        "complex": "지난 분기 서울 지역 거래처별 매출 실적을 분석하고 규정 위반 사항이 있는지 검토해줘"
    }

@pytest.fixture
def test_user():
    """테스트용 사용자 정보"""
    return {
        "user_id": "test_user_001",
        "session_id": "test_session_123",
        "department": "테스트팀",
        "role": "테스터"
    }

# 테스트 실행 전 설정
def pytest_configure(config):
    """pytest 실행 전 설정"""
    # 테스트 모드 설정
    os.environ["TEST_MODE"] = "true"
    os.environ["USE_MOCK_DATA"] = "false"

    # 로깅 설정
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

# 테스트 리포트 커스터마이징 (pytest-html이 설치된 경우에만)
try:
    import pytest_html
    def pytest_html_results_table_header(cells):
        """HTML 리포트 테이블 헤더 커스터마이징"""
        cells.insert(1, '<th class="sortable">Module</th>')

    def pytest_html_results_table_row(report, cells):
        """HTML 리포트 테이블 행 커스터마이징"""
        cells.insert(1, f'<td>{report.location[0]}</td>')
except ImportError:
    pass  # pytest-html not installed, skip customization

# 테스트 마커 정의
def pytest_collection_modifyitems(config, items):
    """테스트 마커 자동 추가"""
    for item in items:
        # DB 테스트 마킹
        if "db" in item.nodeid:
            item.add_marker(pytest.mark.db)

        # 에이전트 테스트 마킹
        if "agent" in item.nodeid:
            item.add_marker(pytest.mark.agent)

        # 통합 테스트 마킹
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)