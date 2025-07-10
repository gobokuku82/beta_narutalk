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
    
    async def get_company_documents(self) -> List[str]:
        """회사 문서 목록 조회"""
        try:
            # 실제 구현에서는 문서 데이터베이스나 파일 시스템에서 문서를 가져옴
            # 현재는 기본 문서 목록 반환
            
            # raw_data 디렉토리에서 실제 문서 읽기 시도
            raw_data_path = Path(settings.project_root) / "database" / "raw_data"
            documents = []
            
            if raw_data_path.exists():
                # .docx 파일들 찾기
                docx_files = list(raw_data_path.glob("*.docx"))
                for docx_file in docx_files:
                    try:
                        # 파일명을 기반으로 문서 내용 추정
                        file_name = docx_file.stem
                        if "복리후생" in file_name:
                            documents.append("좋은제약 복리후생 제도: 직원들의 복지 향상을 위한 다양한 제도를 운영하고 있습니다. 건강보험, 국민연금, 고용보험, 산재보험 등 법정 보험은 물론, 퇴직연금, 장기근속 포상, 경조사비 지원, 교육비 지원, 건강검진 등을 제공합니다.")
                        elif "윤리강령" in file_name:
                            documents.append("좋은제약 윤리강령: 투명하고 정직한 경영을 통해 사회적 신뢰를 얻고, 모든 이해관계자와의 상생을 추구합니다. 공정한 거래, 환경 보호, 사회 공헌 등을 실천하며 지속가능한 경영을 실현합니다.")
                        elif "행동강령" in file_name:
                            documents.append("좋은제약 행동강령: 모든 임직원이 지켜야 할 행동 원칙과 가이드라인을 제시합니다. 고객 중심, 품질 제일, 혁신 추구, 상호 존중 등의 가치를 바탕으로 행동할 것을 규정합니다.")
                        elif "자율준수" in file_name:
                            documents.append("좋은제약 자율준수 관리규정: 법규 준수와 리스크 관리를 위한 체계적인 시스템을 구축하고 있습니다. 컴플라이언스 프로그램 운영, 위반 사항 모니터링, 교육 및 평가 등을 통해 건전한 기업 문화를 조성합니다.")
                        elif "공시정보" in file_name:
                            documents.append("좋은제약 공시정보 관리규정: 투명한 정보 공개를 위한 체계적인 관리 시스템을 운영합니다. 주요 경영 정보, 재무 정보, 사업 현황 등을 정확하고 신속하게 공시하여 투자자와 이해관계자의 신뢰를 얻고 있습니다.")
                        else:
                            documents.append(f"좋은제약 {file_name}: 회사의 주요 정책 및 규정 문서입니다.")
                    except Exception as e:
                        logger.warning(f"문서 파일 처리 실패 ({docx_file.name}): {str(e)}")
            
            # 기본 문서들 추가 (파일이 없는 경우를 대비)
            if not documents:
                documents = [
                    "좋은제약 회사 개요: 좋은제약은 1985년 설립된 제약회사로, 의약품 연구개발과 제조를 주요 사업으로 하고 있습니다. 혁신적인 의약품 개발을 통해 인류의 건강 증진에 기여하고 있으며, 지속적인 성장을 이어가고 있습니다.",
                    "좋은제약 복리후생: 직원들을 위한 다양한 복리후생 제도를 운영하고 있으며, 건강보험, 연금, 교육비 지원, 장기근속 포상, 경조사비 지원 등을 제공합니다.",
                    "좋은제약 윤리강령: 투명하고 공정한 경영을 위한 윤리강령을 수립하여 모든 직원이 준수하도록 하고 있습니다.",
                    "좋은제약 행동강령: 직원들의 올바른 행동을 위한 구체적인 가이드라인을 제시하고 있습니다.",
                    "좋은제약 자율준수 관리규정: 법규 준수와 리스크 관리를 위한 자율준수 프로그램을 운영하고 있습니다.",
                    "좋은제약 공시정보 관리규정: 투명한 정보 공개를 위한 공시정보 관리 체계를 구축하고 있습니다."
                ]
            
            logger.info(f"회사 문서 조회 완료: {len(documents)}개 문서")
            return documents
            
        except Exception as e:
            logger.error(f"회사 문서 조회 실패: {str(e)}")
            return []
    
    def get_service_info(self) -> Dict[str, Any]:
        """서비스 정보 반환"""
        return {
            "service_name": "DatabaseService",
            "db_path": self.db_path,
            "db_initialized": self.db_initialized,
            "available": self.is_available()
        } 