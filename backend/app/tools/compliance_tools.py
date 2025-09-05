"""
Compliance Tools
규정 확인 및 컴플라이언스 관련 도구들
"""

from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
from langchain.callbacks.manager import AsyncCallbackManagerForToolRun
import logging
logger = logging.getLogger(__name__)
import time
from datetime import datetime
import random
import json

from app.core.config import settings
from .base import BaseTool, ToolResult, StructuredTool


class ComplianceCheckInput(BaseModel):
    """컴플라이언스 체크 입력"""
    check_type: str = Field(description="확인 유형: drug_regulation, clinical_trial, marketing, quality")
    target: str = Field(description="확인 대상 (제품명, 시험명 등)")
    regulations: Optional[List[str]] = Field(None, description="확인할 규정 목록")


class RegulatorySearchInput(BaseModel):
    """규제 검색 입력"""
    keyword: str = Field(description="검색 키워드")
    jurisdiction: Optional[str] = Field(None, description="관할 지역: KFDA, FDA, EMA")
    category: Optional[str] = Field(None, description="카테고리: drug, device, cosmetic")


class RiskAssessmentInput(BaseModel):
    """리스크 평가 입력"""
    assessment_type: str = Field(description="평가 유형: product, process, supplier")
    target: str = Field(description="평가 대상")
    criteria: Optional[List[str]] = Field(None, description="평가 기준")


class AuditTrailInput(BaseModel):
    """감사 추적 입력"""
    entity: str = Field(description="감사 대상")
    period: str = Field(description="감사 기간")
    scope: Optional[List[str]] = Field(None, description="감사 범위")


class ComplianceCheckTool(StructuredTool):
    """컴플라이언스 체크 도구"""
    
    name: str = "compliance_check"
    description: str = "의약품 규정, 임상시험, 마케팅 등의 컴플라이언스를 확인합니다."
    args_schema: type[BaseModel] = ComplianceCheckInput
    
    def __init__(self):
        super().__init__()
        self.regulations_db = self._init_regulations()
    
    def _init_regulations(self) -> Dict:
        """규정 데이터베이스 초기화"""
        return {
            "drug_regulation": {
                "KFDA": [
                    "의약품 제조 및 품질관리 기준 (GMP)",
                    "의약품 임상시험 관리기준 (GCP)",
                    "의약품 안전성 정보 관리 규정"
                ],
                "FDA": [
                    "21 CFR Part 210/211 - cGMP",
                    "21 CFR Part 312 - IND",
                    "21 CFR Part 314 - NDA"
                ]
            },
            "clinical_trial": {
                "ICH-GCP": [
                    "피험자 동의서 요구사항",
                    "임상시험계획서 준수",
                    "안전성 보고 의무"
                ]
            },
            "marketing": {
                "광고규정": [
                    "의약품 광고 사전심의",
                    "전문의약품 광고 제한",
                    "리베이트 금지"
                ]
            }
        }
    
    async def _arun(
        self,
        check_type: str,
        target: str,
        regulations: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """컴플라이언스 체크 실행"""
        start_time = time.time()
        
        try:
            # Mock 컴플라이언스 체크
            applicable_regulations = self.regulations_db.get(check_type, {})
            
            check_results = []
            issues_found = []
            
            for jurisdiction, regs in applicable_regulations.items():
                for reg in regs:
                    if regulations and reg not in regulations:
                        continue
                    
                    # Mock 체크 결과
                    compliance_status = random.choice(["Compliant", "Non-Compliant", "Partially Compliant"])
                    
                    result = {
                        "regulation": reg,
                        "jurisdiction": jurisdiction,
                        "status": compliance_status,
                        "checked_at": datetime.now().isoformat()
                    }
                    
                    if compliance_status != "Compliant":
                        issues_found.append({
                            "regulation": reg,
                            "issue": f"{target}의 {reg} 준수 필요",
                            "severity": "High" if compliance_status == "Non-Compliant" else "Medium"
                        })
                    
                    check_results.append(result)
            
            # 종합 평가
            total_checks = len(check_results)
            compliant_count = sum(1 for r in check_results if r["status"] == "Compliant")
            compliance_rate = (compliant_count / total_checks * 100) if total_checks > 0 else 0
            
            return ToolResult(
                success=True,
                data={
                    "target": target,
                    "check_type": check_type,
                    "total_checks": total_checks,
                    "compliant_count": compliant_count,
                    "compliance_rate": round(compliance_rate, 1),
                    "check_results": check_results,
                    "issues_found": issues_found,
                    "risk_level": "High" if compliance_rate < 70 else ("Medium" if compliance_rate < 90 else "Low")
                },
                error=None,
                execution_time=time.time() - start_time,
                tool_name=self.name
            )
            
        except Exception as e:
            return self.handle_error(e)
    
    def _run(self, *args, **kwargs):
        """동기 실행은 지원하지 않음"""
        raise NotImplementedError("Use async execution instead")


class RegulatorySearchTool(StructuredTool):
    """규제 검색 도구"""
    
    name: str = "regulatory_search"
    description: str = "의약품 관련 규제 및 가이드라인을 검색합니다."
    args_schema: type[BaseModel] = RegulatorySearchInput
    
    async def _arun(
        self,
        keyword: str,
        jurisdiction: Optional[str] = None,
        category: Optional[str] = None,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """규제 검색 실행"""
        start_time = time.time()
        
        try:
            # Mock 규제 검색 결과
            mock_results = [
                {
                    "title": f"{keyword} 관련 의약품 제조 기준",
                    "jurisdiction": jurisdiction or "KFDA",
                    "category": category or "drug",
                    "regulation_code": f"KFDA-2024-{random.randint(100, 999)}",
                    "effective_date": "2024-01-01",
                    "summary": f"{keyword}에 대한 제조 및 품질관리 기준을 규정",
                    "url": f"https://www.mfds.go.kr/regulation/{random.randint(1000, 9999)}"
                },
                {
                    "title": f"{keyword} 임상시험 가이드라인",
                    "jurisdiction": jurisdiction or "FDA",
                    "category": category or "drug",
                    "regulation_code": f"FDA-CDER-2024-{random.randint(10, 99)}",
                    "effective_date": "2024-03-15",
                    "summary": f"{keyword} 관련 임상시험 수행 시 고려사항",
                    "url": f"https://www.fda.gov/guidance/{random.randint(1000, 9999)}"
                },
                {
                    "title": f"{keyword} 안전성 정보 관리",
                    "jurisdiction": "ICH",
                    "category": category or "drug",
                    "regulation_code": f"ICH-E2E",
                    "effective_date": "2023-11-01",
                    "summary": "약물감시 계획 수립 및 이행 가이드라인",
                    "url": f"https://www.ich.org/page/e2e"
                }
            ]
            
            # 관할 지역 필터
            if jurisdiction:
                mock_results = [r for r in mock_results if r["jurisdiction"] == jurisdiction]
            
            # 카테고리 필터
            if category:
                mock_results = [r for r in mock_results if r["category"] == category]
            
            return ToolResult(
                success=True,
                data={
                    "keyword": keyword,
                    "results_count": len(mock_results),
                    "regulations": mock_results,
                    "filters_applied": {
                        "jurisdiction": jurisdiction,
                        "category": category
                    }
                },
                error=None,
                execution_time=time.time() - start_time,
                tool_name=self.name
            )
            
        except Exception as e:
            return self.handle_error(e)
    
    def _run(self, *args, **kwargs):
        """동기 실행은 지원하지 않음"""
        raise NotImplementedError("Use async execution instead")


class RiskAssessmentTool(StructuredTool):
    """리스크 평가 도구"""
    
    name: str = "risk_assessment"
    description: str = "제품, 프로세스, 공급업체 등의 컴플라이언스 리스크를 평가합니다."
    args_schema: type[BaseModel] = RiskAssessmentInput
    
    async def _arun(
        self,
        assessment_type: str,
        target: str,
        criteria: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """리스크 평가 실행"""
        start_time = time.time()
        
        try:
            # 기본 평가 기준
            default_criteria = {
                "product": ["품질", "안전성", "효능", "규정준수", "공급안정성"],
                "process": ["효율성", "일관성", "문서화", "검증상태", "변경관리"],
                "supplier": ["품질시스템", "납기준수", "가격경쟁력", "기술지원", "인증현황"]
            }
            
            criteria = criteria or default_criteria.get(assessment_type, ["일반평가"])
            
            # Mock 리스크 평가
            risk_scores = {}
            risk_factors = []
            
            for criterion in criteria:
                # 랜덤 점수 생성 (1-10)
                score = random.randint(3, 10)
                risk_scores[criterion] = score
                
                if score < 6:
                    risk_factors.append({
                        "factor": f"{criterion} 리스크",
                        "score": score,
                        "level": "High" if score < 4 else "Medium",
                        "description": f"{target}의 {criterion} 관련 개선 필요"
                    })
            
            # 종합 리스크 레벨 계산
            avg_score = sum(risk_scores.values()) / len(risk_scores) if risk_scores else 0
            
            if avg_score >= 8:
                overall_risk = "Low"
            elif avg_score >= 6:
                overall_risk = "Medium"
            elif avg_score >= 4:
                overall_risk = "High"
            else:
                overall_risk = "Critical"
            
            # 권고사항 생성
            recommendations = []
            for factor in risk_factors:
                if factor["level"] == "High":
                    recommendations.append(f"즉시 {factor['factor']} 개선 조치 필요")
                else:
                    recommendations.append(f"{factor['factor']} 모니터링 강화")
            
            return ToolResult(
                success=True,
                data={
                    "assessment_type": assessment_type,
                    "target": target,
                    "criteria_evaluated": criteria,
                    "risk_scores": risk_scores,
                    "average_score": round(avg_score, 1),
                    "overall_risk_level": overall_risk,
                    "risk_factors": risk_factors,
                    "recommendations": recommendations,
                    "assessed_at": datetime.now().isoformat()
                },
                error=None,
                execution_time=time.time() - start_time,
                tool_name=self.name
            )
            
        except Exception as e:
            return self.handle_error(e)
    
    def _run(self, *args, **kwargs):
        """동기 실행은 지원하지 않음"""
        raise NotImplementedError("Use async execution instead")


class AuditTrailTool(StructuredTool):
    """감사 추적 도구"""
    
    name: str = "audit_trail"
    description: str = "컴플라이언스 감사 추적 및 기록을 관리합니다."
    args_schema: type[BaseModel] = AuditTrailInput
    
    async def _arun(
        self,
        entity: str,
        period: str,
        scope: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> ToolResult:
        """감사 추적 실행"""
        start_time = time.time()
        
        try:
            # 기본 감사 범위
            default_scope = ["문서관리", "변경관리", "교육기록", "일탈처리", "시정조치"]
            scope = scope or default_scope
            
            # Mock 감사 기록 생성
            audit_records = []
            findings = []
            
            for area in scope:
                # 각 영역별 감사 기록
                num_records = random.randint(5, 15)
                area_compliant = random.randint(num_records - 3, num_records)
                
                for i in range(num_records):
                    record = {
                        "area": area,
                        "activity": f"{area} 활동 {i+1}",
                        "date": f"2024-0{random.randint(1, 9)}-{random.randint(10, 28)}",
                        "responsible": f"담당자{random.randint(1, 5)}",
                        "status": "Compliant" if i < area_compliant else "Non-Compliant"
                    }
                    audit_records.append(record)
                    
                    if record["status"] == "Non-Compliant":
                        findings.append({
                            "area": area,
                            "finding": f"{area} 관련 미준수 사항 발견",
                            "severity": random.choice(["Minor", "Major", "Critical"]),
                            "corrective_action": f"{area} 개선 조치 필요"
                        })
            
            # 감사 요약
            total_records = len(audit_records)
            compliant_records = sum(1 for r in audit_records if r["status"] == "Compliant")
            compliance_rate = (compliant_records / total_records * 100) if total_records > 0 else 0
            
            return ToolResult(
                success=True,
                data={
                    "entity": entity,
                    "period": period,
                    "scope": scope,
                    "total_records": total_records,
                    "compliant_records": compliant_records,
                    "non_compliant_records": total_records - compliant_records,
                    "compliance_rate": round(compliance_rate, 1),
                    "audit_records": audit_records[:10],  # 처음 10개만
                    "findings": findings,
                    "audit_summary": {
                        "areas_audited": len(scope),
                        "total_findings": len(findings),
                        "critical_findings": sum(1 for f in findings if f["severity"] == "Critical"),
                        "major_findings": sum(1 for f in findings if f["severity"] == "Major"),
                        "minor_findings": sum(1 for f in findings if f["severity"] == "Minor")
                    },
                    "audit_date": datetime.now().isoformat()
                },
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
def register_compliance_tools():
    """모든 컴플라이언스 도구를 레지스트리에 등록"""
    from .base import tool_registry
    
    tools = [
        (ComplianceCheckTool(), "compliance"),
        (RegulatorySearchTool(), "compliance"),
        (RiskAssessmentTool(), "compliance"),
        (AuditTrailTool(), "compliance")
    ]
    
    for tool, category in tools:
        tool_registry.register(tool, category)
    
    logger.info(f"Registered {len(tools)} compliance tools")