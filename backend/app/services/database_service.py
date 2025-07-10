"""
데이터베이스 서비스

SQLite 데이터베이스를 사용하여 직원 정보 등을 관리하는 서비스입니다.
"""

import sqlite3
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from ..core.config import settings

logger = logging.getLogger(__name__)

class DatabaseService:
    """데이터베이스 서비스"""
    
    def __init__(self):
        self.db_path = settings.sqlite_db_path
        self.db_initialized = False
        
        # 데이터베이스 초기화 시도 (실패해도 서비스는 계속 실행)
        try:
            self._initialize_database()
        except Exception as e:
            logger.warning(f"데이터베이스 초기화 실패: {str(e)}")
            logger.info("데이터베이스 서비스가 초기화되지 않았습니다. 기본 기능만 제공됩니다.")
    
    def _initialize_database(self):
        """데이터베이스 초기화"""
        try:
            # 데이터베이스 디렉토리 생성
            db_dir = Path(self.db_path)
            db_dir.mkdir(parents=True, exist_ok=True)
            
            # 직원 데이터베이스 파일 경로
            employees_db_path = db_dir / "employees.db"
            
            # 직원 데이터베이스 연결 테스트
            conn = sqlite3.connect(str(employees_db_path))
            cursor = conn.cursor()
            
            # 테이블 존재 확인
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='employees';
            """)
            
            if not cursor.fetchone():
                # 테이블 생성 (예시)
                cursor.execute("""
                    CREATE TABLE employees (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        department TEXT,
                        position TEXT,
                        email TEXT,
                        phone TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # 샘플 데이터 삽입
                sample_data = [
                    ("김현성", "개발부", "시니어 개발자", "kim@company.com", "010-1234-5678"),
                    ("박지영", "마케팅부", "마케팅 매니저", "park@company.com", "010-2345-6789"),
                    ("이수민", "인사부", "인사팀장", "lee@company.com", "010-3456-7890"),
                    ("정민호", "영업부", "영업대표", "jung@company.com", "010-4567-8901"),
                    ("최영수", "기술부", "CTO", "choi@company.com", "010-5678-9012"),
                    ("김미라", "디자인부", "UI/UX 디자이너", "kim.m@company.com", "010-6789-0123")
                ]
                
                cursor.executemany("""
                    INSERT INTO employees (name, department, position, email, phone)
                    VALUES (?, ?, ?, ?, ?)
                """, sample_data)
                
                conn.commit()
                logger.info("직원 데이터베이스 초기화 완료")
            
            conn.close()
            self.db_initialized = True
            logger.info("데이터베이스 서비스 초기화 완료")
            
        except Exception as e:
            logger.error(f"데이터베이스 초기화 실패: {str(e)}")
            raise
    
    def is_available(self) -> bool:
        """데이터베이스 서비스 사용 가능 여부 확인"""
        return self.db_initialized
    
    async def search_employee_info(self, query: str) -> Optional[str]:
        """직원 정보 검색"""
        if not self.is_available():
            logger.warning("데이터베이스 서비스를 사용할 수 없습니다.")
            return self._fallback_employee_search(query)
        
        try:
            employees_db_path = Path(self.db_path) / "employees.db"
            conn = sqlite3.connect(str(employees_db_path))
            cursor = conn.cursor()
            
            # 이름 또는 부서로 검색
            cursor.execute("""
                SELECT name, department, position, email, phone 
                FROM employees 
                WHERE name LIKE ? OR department LIKE ? OR position LIKE ?
            """, (f"%{query}%", f"%{query}%", f"%{query}%"))
            
            results = cursor.fetchall()
            conn.close()
            
            if results:
                employee_info = []
                for result in results:
                    name, dept, pos, email, phone = result
                    employee_info.append(f"이름: {name}\n부서: {dept}\n직책: {pos}\n이메일: {email}\n전화: {phone}")
                
                return "\n\n".join(employee_info)
            else:
                return None
                
        except Exception as e:
            logger.error(f"직원 정보 검색 실패: {str(e)}")
            return None
    
    def _fallback_employee_search(self, query: str) -> str:
        """데이터베이스 없이 기본 직원 검색 결과 반환"""
        # 기본 검색 결과
        fallback_employees = {
            "김현성": "개발부 시니어 개발자",
            "박지영": "마케팅부 마케팅 매니저", 
            "이수민": "인사부 인사팀장",
            "정민호": "영업부 영업대표"
        }
        
        query_lower = query.lower()
        for name, info in fallback_employees.items():
            if query_lower in name.lower() or query_lower in info.lower():
                return f"이름: {name}\n정보: {info}\n(기본 검색 결과)"
        
        return f"'{query}'와 관련된 직원 정보를 찾을 수 없습니다."
    
    async def get_all_employees(self) -> List[Dict[str, Any]]:
        """모든 직원 정보 조회"""
        if not self.is_available():
            logger.warning("데이터베이스 서비스를 사용할 수 없습니다.")
            return self._fallback_all_employees()
        
        try:
            employees_db_path = Path(self.db_path) / "employees.db"
            conn = sqlite3.connect(str(employees_db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, department, position, email, phone 
                FROM employees
            """)
            
            results = cursor.fetchall()
            conn.close()
            
            employees = []
            for result in results:
                employees.append({
                    "id": result[0],
                    "name": result[1],
                    "department": result[2],
                    "position": result[3],
                    "email": result[4],
                    "phone": result[5]
                })
            
            return employees
            
        except Exception as e:
            logger.error(f"직원 정보 조회 실패: {str(e)}")
            return []
    
    def _fallback_all_employees(self) -> List[Dict[str, Any]]:
        """데이터베이스 없이 기본 직원 목록 반환"""
        return [
            {
                "id": 1,
                "name": "김현성",
                "department": "개발부",
                "position": "시니어 개발자",
                "email": "kim@company.com",
                "phone": "010-1234-5678"
            },
            {
                "id": 2,
                "name": "박지영", 
                "department": "마케팅부",
                "position": "마케팅 매니저",
                "email": "park@company.com",
                "phone": "010-2345-6789"
            }
        ]
    
    def get_service_info(self) -> Dict[str, Any]:
        """서비스 정보 반환"""
        return {
            "service_name": "DatabaseService",
            "db_path": self.db_path,
            "db_initialized": self.db_initialized,
            "available": self.is_available()
        } 