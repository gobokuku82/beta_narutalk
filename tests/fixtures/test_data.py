"""
테스트 데이터 및 Fixtures
"""

from typing import Dict, List, Any
from datetime import datetime

# 테스트 쿼리 시나리오
TEST_QUERIES = {
    "simple": [
        "사번이 1234인 직원 정보 조회",
        "부서별 인원 현황",
        "최근 공지사항 조회"
    ],
    "medium": [
        "2024년 3분기 매출 데이터 분석",
        "작년 대비 성장률 계산",
        "특정 제품의 재고 현황 및 예측"
    ],
    "complex": [
        "2024년 3분기 매출을 분석하고 전년 동기 대비 성장률을 계산한 후 보고서 작성",
        "모든 부서의 규정 준수 현황을 검토하고 위반 사항 정리",
        "신약 개발 프로젝트 진행 상황을 종합하여 임원 보고서 작성"
    ],
    "handoff": [
        "데이터를 조회한 후 분석 보고서 작성",
        "정보를 검색하고 규정 검증 수행",
        "SQL 실행 후 결과를 문서로 생성"
    ],
    "error": [
        "존재하지 않는 테이블 조회",
        "",  # 빈 쿼리
        "DELETE FROM users",  # 위험한 쿼리
    ]
}

# 테스트 사용자 컨텍스트
TEST_CONTEXTS = {
    "admin": {
        "user_id": "test_admin",
        "role": "admin",
        "department": "IT",
        "permissions": ["read", "write", "delete"]
    },
    "viewer": {
        "user_id": "test_viewer",
        "role": "viewer",
        "department": "Sales",
        "permissions": ["read"]
    },
    "analyst": {
        "user_id": "test_analyst",
        "role": "analyst",
        "department": "Data",
        "permissions": ["read", "analyze"]
    }
}

# 테스트 세션 데이터
TEST_SESSIONS = {
    "new": {
        "session_id": "test_session_new",
        "history": []
    },
    "existing": {
        "session_id": "test_session_existing",
        "history": [
            {
                "query": "이전 질문",
                "response": "이전 응답",
                "timestamp": "2024-01-01T10:00:00"
            }
        ]
    }
}

# 예상 응답 데이터
EXPECTED_RESPONSES = {
    "success": {
        "status": "success",
        "result": {
            "answer": "테스트 응답",
            "confidence": 0.95,
            "sources": ["database"],
            "agents_used": ["sql_analysis"]
        }
    },
    "error": {
        "status": "error",
        "error": "처리 중 오류 발생"
    },
    "cached": {
        "status": "success",
        "cached": True,
        "result": {
            "answer": "캐시된 응답"
        }
    }
}

# Mock 데이터베이스 레코드
MOCK_DB_RECORDS = {
    "employees": [
        {"사번": "1234", "성명": "홍길동", "부서": "개발팀", "직급": "과장"},
        {"사번": "5678", "성명": "김철수", "부서": "영업팀", "직급": "대리"},
        {"사번": "9012", "성명": "이영희", "부서": "기획팀", "직급": "사원"}
    ],
    "sales": [
        {"년도": 2024, "분기": 3, "매출": 1500000000, "제품": "A"},
        {"년도": 2024, "분기": 2, "매출": 1200000000, "제품": "A"},
        {"년도": 2023, "분기": 3, "매출": 1000000000, "제품": "A"}
    ],
    "inventory": [
        {"제품코드": "P001", "제품명": "제품A", "재고": 100, "창고": "서울"},
        {"제품코드": "P002", "제품명": "제품B", "재고": 50, "창고": "부산"}
    ]
}

# 성능 테스트 설정
PERFORMANCE_CONFIG = {
    "load_test": {
        "concurrent_users": 10,
        "requests_per_user": 5,
        "duration_seconds": 30
    },
    "memory_test": {
        "iterations": 100,
        "check_interval": 10
    },
    "response_time": {
        "acceptable_ms": 2000,
        "target_ms": 1000
    }
}

# State 압축 테스트 데이터
LARGE_STATE = {
    "messages": [f"메시지 {i}" for i in range(100)],
    "intermediate_results": {f"step_{i}": {"data": f"결과 {i}" * 100} for i in range(20)},
    "context": {"large_data": "x" * 10000}
}

# Agent 선택 테스트 케이스
AGENT_SELECTION_CASES = [
    {
        "query": "데이터 조회",
        "expected_agents": ["sql_analysis_agent"]
    },
    {
        "query": "정보 검색",
        "expected_agents": ["information_retrieval_agent"]
    },
    {
        "query": "보고서 작성",
        "expected_agents": ["document_generation_agent"]
    },
    {
        "query": "규정 확인",
        "expected_agents": ["compliance_validation_agent"]
    },
    {
        "query": "데이터 분석 후 보고서 작성",
        "expected_agents": ["sql_analysis_agent", "document_generation_agent"]
    }
]

# Subgraph 테스트 시나리오
SUBGRAPH_SCENARIOS = [
    {
        "name": "parallel_analysis",
        "tasks": [
            {"type": "analysis", "query": "매출 분석"},
            {"type": "retrieval", "query": "경쟁사 정보"}
        ],
        "execution": "parallel"
    },
    {
        "name": "sequential_processing",
        "tasks": [
            {"type": "retrieval", "query": "데이터 검색"},
            {"type": "validation", "query": "규정 검증"}
        ],
        "execution": "sequential"
    }
]

# Human-in-Loop 테스트 케이스
HUMAN_IN_LOOP_CASES = [
    {
        "scenario": "approval_required",
        "trigger": "DELETE 쿼리 실행",
        "intervention_type": "APPROVAL",
        "user_response": {"approved": False, "reason": "위험한 작업"}
    },
    {
        "scenario": "correction_needed",
        "trigger": "잘못된 결과",
        "intervention_type": "CORRECTION",
        "user_response": {"approved": True, "modifications": {"corrected_value": "수정된 값"}}
    }
]

# 캐시 테스트 데이터
CACHE_TEST_DATA = {
    "queries": [
        {"query": "캐시 테스트 1", "result": "결과 1"},
        {"query": "캐시 테스트 2", "result": "결과 2"},
        {"query": "캐시 테스트 3", "result": "결과 3"}
    ],
    "ttl_seconds": 5,
    "max_size": 10
}

def get_test_query(category: str, index: int = 0) -> str:
    """테스트 쿼리 반환"""
    queries = TEST_QUERIES.get(category, [])
    return queries[index] if index < len(queries) else ""

def get_test_context(role: str = "admin") -> Dict[str, Any]:
    """테스트 컨텍스트 반환"""
    return TEST_CONTEXTS.get(role, TEST_CONTEXTS["admin"]).copy()

def get_mock_db_data(table: str) -> List[Dict[str, Any]]:
    """Mock DB 데이터 반환"""
    return MOCK_DB_RECORDS.get(table, [])