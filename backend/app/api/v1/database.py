"""
Database API Endpoints
Mock 데이터베이스 CRUD 작업 API
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
logger = logging.getLogger(__name__)
import sys
from pathlib import Path

# Add database test path to system path
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "database" / "test"))
from mock_data import get_mock_db

router = APIRouter()
db = get_mock_db()


class DrugSearchRequest(BaseModel):
    """약물 검색 요청"""
    keyword: str
    category: Optional[str] = None


class CustomerSearchRequest(BaseModel):
    """고객 검색 요청"""
    keyword: str
    customer_type: Optional[str] = None


class DataResponse(BaseModel):
    """데이터 응답"""
    success: bool
    data: Any
    message: Optional[str] = None


# Drug Database APIs
@router.get("/drugs/{drug_id}", response_model=DataResponse)
async def get_drug(drug_id: str):
    """약물 정보 조회"""
    try:
        drug = db.get_drug_by_id(drug_id)
        if drug:
            return DataResponse(success=True, data=drug)
        else:
            raise HTTPException(status_code=404, detail=f"Drug {drug_id} not found")
    except Exception as e:
        logger.error(f"Error fetching drug: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/drugs/search", response_model=DataResponse)
async def search_drugs(request: DrugSearchRequest):
    """약물 검색"""
    try:
        results = db.search_drugs(request.keyword, request.category)
        return DataResponse(
            success=True, 
            data=results,
            message=f"Found {len(results)} drugs"
        )
    except Exception as e:
        logger.error(f"Error searching drugs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drugs/name/{drug_name}", response_model=DataResponse)
async def get_drug_by_name(drug_name: str):
    """이름으로 약물 조회"""
    try:
        drug = db.get_drug_by_name(drug_name)
        if drug:
            return DataResponse(success=True, data=drug)
        else:
            raise HTTPException(status_code=404, detail=f"Drug '{drug_name}' not found")
    except Exception as e:
        logger.error(f"Error fetching drug by name: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/drugs/categories/list", response_model=DataResponse)
async def get_drug_categories():
    """약물 카테고리 목록"""
    try:
        categories = db.get_drug_categories()
        return DataResponse(success=True, data=categories)
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Sales Database APIs
@router.get("/sales/monthly", response_model=DataResponse)
async def get_monthly_sales(
    year: int = Query(2024, description="Year"),
    month: Optional[str] = Query(None, description="Month (e.g., '1월')")
):
    """월별 매출 데이터"""
    try:
        sales = db.get_monthly_sales(year, month)
        return DataResponse(success=True, data=sales)
    except Exception as e:
        logger.error(f"Error fetching sales: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sales/team-performance", response_model=DataResponse)
async def get_team_performance(team_name: Optional[str] = None):
    """팀별 실적 데이터"""
    try:
        performance = db.get_team_performance(team_name)
        return DataResponse(success=True, data=performance)
    except Exception as e:
        logger.error(f"Error fetching performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sales/product-ranking", response_model=DataResponse)
async def get_product_ranking(top_n: int = Query(10, description="Top N products")):
    """제품 판매 순위"""
    try:
        ranking = db.get_product_ranking(top_n)
        return DataResponse(success=True, data=ranking)
    except Exception as e:
        logger.error(f"Error fetching ranking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sales/kpi", response_model=DataResponse)
async def get_kpi_metrics():
    """KPI 지표"""
    try:
        kpi = db.get_kpi_metrics()
        return DataResponse(success=True, data=kpi)
    except Exception as e:
        logger.error(f"Error fetching KPI: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sales/summary", response_model=DataResponse)
async def get_sales_summary(period: str = Query("2024-06", description="Period (YYYY-MM)")):
    """매출 요약"""
    try:
        summary = db.get_sales_summary(period)
        return DataResponse(success=True, data=summary)
    except Exception as e:
        logger.error(f"Error fetching summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Compliance Database APIs
@router.get("/compliance/regulations", response_model=DataResponse)
async def get_regulations(
    agency: Optional[str] = Query(None, description="Agency (KFDA/FDA)"),
    category: Optional[str] = Query(None, description="Category")
):
    """규정 정보"""
    try:
        regulations = db.get_regulations(agency, category)
        return DataResponse(success=True, data=regulations)
    except Exception as e:
        logger.error(f"Error fetching regulations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compliance/updates", response_model=DataResponse)
async def get_recent_updates(limit: int = Query(5, description="Number of updates")):
    """최근 규정 업데이트"""
    try:
        updates = db.get_recent_updates(limit)
        return DataResponse(success=True, data=updates)
    except Exception as e:
        logger.error(f"Error fetching updates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compliance/checklist", response_model=DataResponse)
async def get_compliance_checklist(category: Optional[str] = None):
    """컴플라이언스 체크리스트"""
    try:
        checklist = db.get_compliance_checklist(category)
        return DataResponse(success=True, data=checklist)
    except Exception as e:
        logger.error(f"Error fetching checklist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compliance/risk", response_model=DataResponse)
async def get_risk_assessment():
    """리스크 평가"""
    try:
        risk = db.get_risk_assessment()
        return DataResponse(success=True, data=risk)
    except Exception as e:
        logger.error(f"Error fetching risk assessment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compliance/audit", response_model=DataResponse)
async def get_audit_history():
    """감사 이력"""
    try:
        audits = db.get_audit_history()
        return DataResponse(success=True, data=audits)
    except Exception as e:
        logger.error(f"Error fetching audit history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Customer Database APIs
@router.get("/customers/hospitals", response_model=DataResponse)
async def get_hospitals(hospital_id: Optional[str] = None):
    """병원 정보"""
    try:
        hospitals = db.get_hospital(hospital_id)
        return DataResponse(success=True, data=hospitals)
    except Exception as e:
        logger.error(f"Error fetching hospitals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers/clinics", response_model=DataResponse)
async def get_clinics(clinic_id: Optional[str] = None):
    """의원 정보"""
    try:
        clinics = db.get_clinic(clinic_id)
        return DataResponse(success=True, data=clinics)
    except Exception as e:
        logger.error(f"Error fetching clinics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers/pharmacies", response_model=DataResponse)
async def get_pharmacies(pharmacy_id: Optional[str] = None):
    """약국 정보"""
    try:
        pharmacies = db.get_pharmacy(pharmacy_id)
        return DataResponse(success=True, data=pharmacies)
    except Exception as e:
        logger.error(f"Error fetching pharmacies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers/doctors", response_model=DataResponse)
async def get_doctors(doctor_id: Optional[str] = None):
    """의사 정보"""
    try:
        doctors = db.get_doctor(doctor_id)
        return DataResponse(success=True, data=doctors)
    except Exception as e:
        logger.error(f"Error fetching doctors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/customers/search", response_model=DataResponse)
async def search_customers(request: CustomerSearchRequest):
    """고객 검색"""
    try:
        results = db.search_customers(request.keyword, request.customer_type)
        return DataResponse(
            success=True,
            data=results,
            message=f"Found {len(results)} customers"
        )
    except Exception as e:
        logger.error(f"Error searching customers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers/segments", response_model=DataResponse)
async def get_customer_segments():
    """고객 세그먼트"""
    try:
        segments = db.get_customer_segments()
        return DataResponse(success=True, data=segments)
    except Exception as e:
        logger.error(f"Error fetching segments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Analytics APIs
@router.get("/analytics/trends", response_model=DataResponse)
async def get_trends(
    data_type: str = Query("sales", description="Data type"),
    periods: int = Query(6, description="Number of periods")
):
    """트렌드 데이터"""
    try:
        trends = db.generate_mock_trend(data_type, periods)
        return DataResponse(success=True, data=trends)
    except Exception as e:
        logger.error(f"Error generating trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check
@router.get("/health", response_model=DataResponse)
async def database_health():
    """데이터베이스 상태 확인"""
    try:
        # Check if data is loaded
        data_status = {
            "drugs": bool(db.data.get('drugs')),
            "sales": bool(db.data.get('sales')),
            "compliance": bool(db.data.get('compliance')),
            "customers": bool(db.data.get('customers'))
        }
        
        return DataResponse(
            success=all(data_status.values()),
            data=data_status,
            message="Mock database is operational"
        )
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))