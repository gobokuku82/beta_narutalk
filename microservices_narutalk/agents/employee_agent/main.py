"""
직원 분석 에이전트 - 직원 데이터 분석 및 통계
포트: 8003
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="Employee Agent",
    description="직원 데이터 분석 및 통계 에이전트",
    version="1.0.0"
)

# 요청/응답 모델
class AnalyzeRequest(BaseModel):
    employee_id: Optional[str] = None
    analysis_type: str = "general"  # general, performance, attendance
    filters: Optional[Dict[str, Any]] = None

class AnalyzeResponse(BaseModel):
    analysis_type: str
    results: Dict[str, Any]
    timestamp: str
    employee_count: int

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None


# 모의 직원 데이터 (실제로는 SQLite 사용)
MOCK_EMPLOYEES = [
    {
        "id": "emp001",
        "name": "김철수",
        "department": "영업부",
        "position": "과장",
        "join_date": "2020-01-15",
        "performance_score": 85,
        "attendance_rate": 0.95
    },
    {
        "id": "emp002",
        "name": "이영희",
        "department": "개발부",
        "position": "선임",
        "join_date": "2019-05-20",
        "performance_score": 92,
        "attendance_rate": 0.98
    },
    {
        "id": "emp003",
        "name": "박민수",
        "department": "인사부",
        "position": "대리",
        "join_date": "2021-03-10",
        "performance_score": 78,
        "attendance_rate": 0.93
    },
    {
        "id": "emp004",
        "name": "최유진",
        "department": "마케팅부",
        "position": "팀장",
        "join_date": "2018-11-01",
        "performance_score": 88,
        "attendance_rate": 0.96
    }
]


def analyze_employee_data(employee_id: Optional[str] = None, 
                         analysis_type: str = "general") -> Dict[str, Any]:
    """직원 데이터 분석 함수"""
    
    if employee_id:
        # 특정 직원 분석
        employee = next((emp for emp in MOCK_EMPLOYEES if emp['id'] == employee_id), None)
        if not employee:
            return {"error": f"Employee {employee_id} not found"}
        
        if analysis_type == "performance":
            return {
                "employee_id": employee_id,
                "name": employee['name'],
                "performance_score": employee['performance_score'],
                "performance_grade": "A" if employee['performance_score'] >= 90 else "B" if employee['performance_score'] >= 80 else "C",
                "recommendation": "우수한 성과를 보이고 있습니다." if employee['performance_score'] >= 80 else "개선이 필요합니다."
            }
        
        elif analysis_type == "attendance":
            return {
                "employee_id": employee_id,
                "name": employee['name'],
                "attendance_rate": employee['attendance_rate'],
                "attendance_grade": "A" if employee['attendance_rate'] >= 0.95 else "B" if employee['attendance_rate'] >= 0.90 else "C",
                "status": "양호" if employee['attendance_rate'] >= 0.90 else "주의 필요"
            }
        
        else:  # general
            return {
                "employee_id": employee_id,
                "name": employee['name'],
                "department": employee['department'],
                "position": employee['position'],
                "join_date": employee['join_date'],
                "overall_score": (employee['performance_score'] + employee['attendance_rate'] * 100) / 2,
                "status": "우수 직원"
            }
    
    else:
        # 전체 직원 분석
        if analysis_type == "performance":
            avg_performance = sum(emp['performance_score'] for emp in MOCK_EMPLOYEES) / len(MOCK_EMPLOYEES)
            top_performers = [emp for emp in MOCK_EMPLOYEES if emp['performance_score'] >= 90]
            
            return {
                "total_employees": len(MOCK_EMPLOYEES),
                "average_performance": round(avg_performance, 2),
                "top_performers": len(top_performers),
                "performance_distribution": {
                    "A등급 (90+)": len([emp for emp in MOCK_EMPLOYEES if emp['performance_score'] >= 90]),
                    "B등급 (80-89)": len([emp for emp in MOCK_EMPLOYEES if 80 <= emp['performance_score'] < 90]),
                    "C등급 (70-79)": len([emp for emp in MOCK_EMPLOYEES if emp['performance_score'] < 80])
                }
            }
        
        elif analysis_type == "attendance":
            avg_attendance = sum(emp['attendance_rate'] for emp in MOCK_EMPLOYEES) / len(MOCK_EMPLOYEES)
            excellent_attendance = [emp for emp in MOCK_EMPLOYEES if emp['attendance_rate'] >= 0.95]
            
            return {
                "total_employees": len(MOCK_EMPLOYEES),
                "average_attendance": round(avg_attendance, 3),
                "excellent_attendance": len(excellent_attendance),
                "attendance_distribution": {
                    "우수 (95%+)": len([emp for emp in MOCK_EMPLOYEES if emp['attendance_rate'] >= 0.95]),
                    "양호 (90-94%)": len([emp for emp in MOCK_EMPLOYEES if 0.90 <= emp['attendance_rate'] < 0.95]),
                    "개선 필요 (90% 미만)": len([emp for emp in MOCK_EMPLOYEES if emp['attendance_rate'] < 0.90])
                }
            }
        
        else:  # general
            return {
                "total_employees": len(MOCK_EMPLOYEES),
                "departments": list(set(emp['department'] for emp in MOCK_EMPLOYEES)),
                "average_performance": round(sum(emp['performance_score'] for emp in MOCK_EMPLOYEES) / len(MOCK_EMPLOYEES), 2),
                "average_attendance": round(sum(emp['attendance_rate'] for emp in MOCK_EMPLOYEES) / len(MOCK_EMPLOYEES), 3),
                "department_distribution": {
                    dept: len([emp for emp in MOCK_EMPLOYEES if emp['department'] == dept])
                    for dept in set(emp['department'] for emp in MOCK_EMPLOYEES)
                }
            }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_employee(request: AnalyzeRequest):
    """직원 분석"""
    try:
        logger.info(f"Analyzing employee data: {request.employee_id}, type: {request.analysis_type}")
        
        # 직원 분석
        results = analyze_employee_data(request.employee_id, request.analysis_type)
        
        response = AnalyzeResponse(
            analysis_type=request.analysis_type,
            results=results,
            timestamp=datetime.now().isoformat(),
            employee_count=len(MOCK_EMPLOYEES)
        )
        
        logger.info(f"Analysis completed for {request.analysis_type}")
        return response
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/employees")
async def list_employees():
    """직원 목록 조회"""
    return {
        "employees": MOCK_EMPLOYEES,
        "total": len(MOCK_EMPLOYEES),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/stats")
async def get_stats():
    """통계 조회"""
    return {
        "total_employees": len(MOCK_EMPLOYEES),
        "departments": list(set(emp['department'] for emp in MOCK_EMPLOYEES)),
        "average_performance": round(sum(emp['performance_score'] for emp in MOCK_EMPLOYEES) / len(MOCK_EMPLOYEES), 2),
        "average_attendance": round(sum(emp['attendance_rate'] for emp in MOCK_EMPLOYEES) / len(MOCK_EMPLOYEES), 3),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스 체크"""
    return HealthResponse(
        status="healthy",
        service="employee_agent",
        timestamp=datetime.now().isoformat(),
        details={
            "port": 8003,
            "version": "1.0.0",
            "capabilities": ["employee_analysis", "performance_tracking", "attendance_monitoring"],
            "employee_count": len(MOCK_EMPLOYEES)
        }
    )


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "employee_agent",
        "description": "직원 데이터 분석 및 통계 에이전트",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "/analyze",
            "employees": "/employees",
            "stats": "/stats",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003) 