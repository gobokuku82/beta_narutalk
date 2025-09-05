"""
Database Tools
Mock 데이터베이스와 상호작용하는 도구들
"""

from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun
import logging
logger = logging.getLogger(__name__)
import sys
from pathlib import Path
import time

# Add database test path to system path
try:
    sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "database" / "test"))
    from mock_data import get_mock_db
except ImportError as e:
    logger.warning(f"Failed to import mock_data: {e}")
    # If import fails, create a simple mock class
    class SimpleMockDB:
        def get_drug_by_name(self, name):
            return None
        def search_drugs(self, keyword, category=None):
            return []
        def get_sales_summary(self, period):
            return {"total": 0, "period": period}
        def generate_mock_trend(self, metric, periods):
            return []
        def get_team_performance(self):
            return {"teams": []}
        def get_monthly_sales(self, year, month):
            return {"sales": 0}
        def get_regulations(self, agency, category=None):
            return []
        def get_recent_updates(self, limit):
            return []
        def get_risk_assessment(self):
            return {"risk_level": "low"}
        def search_customers(self, keyword, customer_type=None):
            return []
        def get_customer_purchases(self, customer_id):
            return []
        def get_kpi_metrics(self):
            return {"revenue": {"achievement": 0}, "customer_retention": {"achievement": 0}, "market_share": {"actual": 0}}
        def get_product_ranking(self, limit):
            return []
    
    def get_mock_db():
        return SimpleMockDB()

from .base import BaseTool, ToolResult, StructuredTool


# Input schemas for structured tools
class DrugSearchInput(BaseModel):
    """약물 검색 입력"""
    keyword: str = Field(description="검색할 약물명 또는 키워드")
    category: Optional[str] = Field(None, description="약물 카테고리 필터")


class SalesAnalysisInput(BaseModel):
    """매출 분석 입력"""
    period: str = Field(description="분석 기간 (YYYY-MM)")
    analysis_type: str = Field(default="summary", description="분석 유형: summary, trend, comparison")


class ComplianceCheckInput(BaseModel):
    """규정 확인 입력"""
    agency: str = Field(description="규제 기관: KFDA, FDA")
    category: Optional[str] = Field(None, description="규정 카테고리: GMP, GCP, advertising")
    query: Optional[str] = Field(None, description="특정 규정 관련 질문")


class CustomerSearchInput(BaseModel):
    """고객 검색 입력"""
    keyword: str = Field(description="병원/의원/약국 이름 또는 지역")
    customer_type: Optional[str] = Field(None, description="고객 유형: hospital, clinic, pharmacy")


class DrugSearchTool(StructuredTool):
    """약물 정보 검색 도구"""
    
    name: str = "drug_search"
    description: str = "의약품 정보를 검색합니다. 약물명, 성분, 카테고리로 검색 가능합니다."
    args_schema: type[BaseModel] = DrugSearchInput
    db: Any = Field(default=None, exclude=True)
    
    def __init__(self):
        super().__init__()
        self.db = get_mock_db()
    
    async def _arun(
        self,
        keyword: str,
        category: Optional[str] = None,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """약물 검색 실행"""
        start_time = time.time()
        
        try:
            # 약물 이름으로 먼저 검색
            drug = self.db.get_drug_by_name(keyword)
            if drug:
                return ToolResult(
                    success=True,
                    data=drug,
                    error=None,
                    execution_time=time.time() - start_time,
                    tool_name=self.name
                )
            
            # 키워드로 검색
            results = self.db.search_drugs(keyword, category)
            
            if results:
                return ToolResult(
                    success=True,
                    data={
                        "count": len(results),
                        "drugs": results
                    },
                    error=None,
                    execution_time=time.time() - start_time,
                    tool_name=self.name
                )
            else:
                return ToolResult(
                    success=True,
                    data={"message": f"'{keyword}'에 대한 약물 정보를 찾을 수 없습니다."},
                    error=None,
                    execution_time=time.time() - start_time,
                    tool_name=self.name
                )
            
        except Exception as e:
            return self.handle_error(e)
    
    def _run(self, *args, **kwargs):
        """동기 실행은 지원하지 않음"""
        raise NotImplementedError("Use async execution instead")


class SalesAnalysisTool(StructuredTool):
    """매출 데이터 분석 도구"""
    
    name: str = "sales_analysis"
    description: str = "매출 데이터를 분석합니다. 월별 매출, 제품별 실적, 팀별 성과를 조회할 수 있습니다."
    args_schema: type[BaseModel] = SalesAnalysisInput
    db: Any = Field(default=None, exclude=True)
    
    def __init__(self):
        super().__init__()
        self.db = get_mock_db()
    
    async def _arun(
        self,
        period: str,
        analysis_type: str = "summary",
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """매출 분석 실행"""
        start_time = time.time()
        
        try:
            if analysis_type == "summary":
                data = self.db.get_sales_summary(period)
            elif analysis_type == "trend":
                data = self.db.generate_mock_trend("sales", 6)
            elif analysis_type == "comparison":
                # 팀별 성과 비교
                data = self.db.get_team_performance()
            else:
                # 기본: 월별 매출
                year, month = period.split("-")
                month_kr = f"{int(month)}월"
                data = self.db.get_monthly_sales(int(year), month_kr)
            
            return ToolResult(
                success=True,
                data=data,
                error=None,
                execution_time=time.time() - start_time,
                tool_name=self.name
            )
            
        except Exception as e:
            return self.handle_error(e)
    
    def _run(self, *args, **kwargs):
        """동기 실행은 지원하지 않음"""
        raise NotImplementedError("Use async execution instead")


class ComplianceCheckTool(StructuredTool):
    """규정 확인 도구"""
    
    name: str = "compliance_check"
    description: str = "의약품 관련 규정을 확인합니다. KFDA, FDA 규정 및 GMP, GCP 가이드라인을 조회할 수 있습니다."
    args_schema: type[BaseModel] = ComplianceCheckInput
    db: Any = Field(default=None, exclude=True)
    
    def __init__(self):
        super().__init__()
        self.db = get_mock_db()
    
    async def _arun(
        self,
        agency: str,
        category: Optional[str] = None,
        query: Optional[str] = None,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """규정 확인 실행"""
        start_time = time.time()
        
        try:
            # 규정 조회
            regulations = self.db.get_regulations(agency, category)
            
            # 최근 업데이트 조회
            updates = self.db.get_recent_updates(3)
            
            # 리스크 평가 조회
            risk = self.db.get_risk_assessment()
            
            data = {
                "agency": agency,
                "category": category,
                "regulations": regulations,
                "recent_updates": updates,
                "risk_assessment": risk
            }
            
            # 특정 질문이 있으면 관련 정보만 필터
            if query:
                data["query_response"] = f"'{query}'에 대한 규정 정보"
            
            return ToolResult(
                success=True,
                data=data,
                error=None,
                execution_time=time.time() - start_time,
                tool_name=self.name
            )
            
        except Exception as e:
            return self.handle_error(e)
    
    def _run(self, *args, **kwargs):
        """동기 실행은 지원하지 않음"""
        raise NotImplementedError("Use async execution instead")


class CustomerSearchTool(StructuredTool):
    """고객 정보 검색 도구"""
    
    name: str = "customer_search"
    description: str = "병원, 의원, 약국 등 고객 정보를 검색합니다."
    args_schema: type[BaseModel] = CustomerSearchInput
    db: Any = Field(default=None, exclude=True)
    
    def __init__(self):
        super().__init__()
        self.db = get_mock_db()
    
    async def _arun(
        self,
        keyword: str,
        customer_type: Optional[str] = None,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """고객 검색 실행"""
        start_time = time.time()
        
        try:
            # 고객 검색
            results = self.db.search_customers(keyword, customer_type)
            
            if results:
                # 고객별 구매 이력 추가
                for customer in results:
                    customer_id = customer.get('id')
                    if customer_id:
                        purchases = self.db.get_customer_purchases(customer_id)
                        if purchases:
                            customer['recent_purchases'] = purchases[0]
                
                data = {
                    "count": len(results),
                    "customers": results
                }
            else:
                data = {
                    "count": 0,
                    "message": f"'{keyword}'에 해당하는 고객을 찾을 수 없습니다."
                }
            
            return ToolResult(
                success=True,
                data=data,
                error=None,
                execution_time=time.time() - start_time,
                tool_name=self.name
            )
            
        except Exception as e:
            return self.handle_error(e)
    
    def _run(self, *args, **kwargs):
        """동기 실행은 지원하지 않음"""
        raise NotImplementedError("Use async execution instead")


class KPIMetricsTool(BaseTool):
    """KPI 지표 조회 도구"""
    
    name: str = "kpi_metrics"
    description: str = "주요 성과 지표(KPI)를 조회합니다."
    db: Any = Field(default=None, exclude=True)
    
    def __init__(self):
        super().__init__()
        self.db = get_mock_db()
    
    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """KPI 조회 실행"""
        start_time = time.time()
        
        try:
            kpi = self.db.get_kpi_metrics()
            
            # 제품 순위 추가
            ranking = self.db.get_product_ranking(5)
            
            data = {
                "kpi_metrics": kpi,
                "product_ranking": ranking,
                "summary": {
                    "revenue_achievement": f"{kpi['revenue']['achievement']}%",
                    "customer_retention": f"{kpi['customer_retention']['achievement']}%",
                    "market_share": f"{kpi['market_share']['actual']}%"
                }
            }
            
            return ToolResult(
                success=True,
                data=data,
                error=None,
                execution_time=time.time() - start_time,
                tool_name=self.name
            )
            
        except Exception as e:
            return self.handle_error(e)
    
    def _run(self, *args, **kwargs):
        """동기 실행은 지원하지 않음"""
        raise NotImplementedError("Use async execution instead")


# Tool 레지스트리에 등록
def register_database_tools():
    """모든 데이터베이스 도구를 레지스트리에 등록"""
    from .base import tool_registry
    
    tools = [
        (DrugSearchTool(), "database"),
        (SalesAnalysisTool(), "database"),
        (ComplianceCheckTool(), "database"),
        (CustomerSearchTool(), "database"),
        (KPIMetricsTool(), "database")
    ]
    
    for tool, category in tools:
        tool_registry.register(tool, category)
    
    logger.info(f"Registered {len(tools)} database tools")