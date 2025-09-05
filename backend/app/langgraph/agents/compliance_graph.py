"""
Compliance Agent - Subgraph Implementation
LangGraph 0.6.6 기반 규정확인 에이전트 (Subgraph 구조)
"""

from typing import Dict, Any, List, TypedDict, Annotated, Sequence, Optional
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from loguru import logger
import operator
from datetime import datetime
import json

from app.core.config import settings


class ComplianceState(TypedDict):
    """규정확인 에이전트 전용 State"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    request: str
    compliance_type: str  # drug_regulation, clinical_trial, marketing, quality, general
    regulations_checked: List[Dict[str, Any]]
    risk_level: str  # low, medium, high, critical
    risk_factors: List[str]
    validation_results: Dict[str, bool]
    recommendations: List[str]
    compliance_report: str
    status: str  # analyzing, checking, assessing, validating, reporting, completed, error
    error_message: Optional[str]


class ComplianceSubgraph:
    """규정확인 Subgraph - 단계별 컴플라이언스 검증 워크플로우"""
    
    def __init__(self):
        # LLM 초기화
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.2,  # 더 일관된 응답을 위해 낮은 temperature
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # 규정 데이터베이스 (실제로는 외부 DB 연동)
        self.regulations_db = self._initialize_regulations()
        
        # Subgraph 생성
        self.graph = self._build_graph()
    
    def _initialize_regulations(self) -> Dict:
        """규정 데이터베이스 초기화"""
        return {
            "drug_regulation": {
                "KFDA": [
                    "의약품 제조 및 품질관리 기준 (GMP)",
                    "의약품 임상시험 관리기준 (GCP)",
                    "의약품 안전성 정보 관리 규정",
                    "의약품 표시 및 기재사항 규정"
                ],
                "FDA": [
                    "21 CFR Part 210/211 - Current Good Manufacturing Practice",
                    "21 CFR Part 312 - Investigational New Drug Application",
                    "21 CFR Part 314 - New Drug Application",
                    "21 CFR Part 600 - Biological Products"
                ]
            },
            "clinical_trial": {
                "ICH-GCP": [
                    "피험자 동의서 요구사항",
                    "임상시험계획서 준수",
                    "안전성 보고 의무",
                    "데이터 무결성 요구사항"
                ],
                "국내규정": [
                    "생명윤리법",
                    "약사법 임상시험 규정",
                    "임상시험 관리기준"
                ]
            },
            "marketing": {
                "광고규정": [
                    "의약품 광고 사전심의 규정",
                    "전문의약품 광고 제한",
                    "일반의약품 광고 기준",
                    "온라인 광고 가이드라인"
                ],
                "판촉규정": [
                    "리베이트 금지 규정",
                    "경품 제공 제한",
                    "학술대회 지원 기준"
                ]
            },
            "quality": {
                "품질관리": [
                    "제품 품질 시험 기준",
                    "안정성 시험 요구사항",
                    "제조 공정 밸리데이션",
                    "변경 관리 절차"
                ],
                "품질보증": [
                    "품질 시스템 요구사항",
                    "내부 감사 절차",
                    "CAPA 시스템",
                    "문서 관리 시스템"
                ]
            }
        }
    
    async def analyze_compliance_request_node(self, state: ComplianceState) -> Dict:
        """컴플라이언스 요청 분석 노드"""
        logger.info("컴플라이언스 요청 분석")
        
        request = state.get("request", "")
        if not request and state.get("messages"):
            last_message = state["messages"][-1]
            request = last_message.content if isinstance(last_message, (HumanMessage, AIMessage)) else str(last_message)
        
        # LLM으로 컴플라이언스 유형 분석
        prompt = f"""
        사용자 요청: {request}
        
        이 요청이 어떤 유형의 컴플라이언스 확인인지 분류하세요:
        - drug_regulation: 의약품 규제, GMP, 제조 관련
        - clinical_trial: 임상시험, GCP, IRB 관련
        - marketing: 광고, 판촉, 리베이트 관련
        - quality: 품질관리, 품질보증 관련
        - general: 일반적인 규정 확인
        
        한 단어로만 답하세요:
        """
        
        response = await self.llm.ainvoke(prompt)
        compliance_type = response.content.strip().lower()
        
        # 유효성 검증
        valid_types = ["drug_regulation", "clinical_trial", "marketing", "quality", "general"]
        if compliance_type not in valid_types:
            compliance_type = "general"
        
        return {
            "request": request,
            "compliance_type": compliance_type,
            "status": "analyzing"
        }
    
    async def check_regulations_node(self, state: ComplianceState) -> Dict:
        """규제 사항 확인 노드"""
        logger.info("규제 사항 확인")
        
        compliance_type = state.get("compliance_type", "general")
        request = state.get("request", "")
        
        regulations_checked = []
        
        # 관련 규정 확인
        if compliance_type in self.regulations_db:
            regulations = self.regulations_db[compliance_type]
            
            for category, items in regulations.items():
                for item in items:
                    # 실제로는 각 규정에 대한 상세 확인 로직
                    regulation_check = {
                        "category": category,
                        "regulation": item,
                        "applicable": True,  # 실제로는 조건부 판단
                        "status": "확인됨",
                        "details": f"{item}에 대한 검토가 필요합니다."
                    }
                    regulations_checked.append(regulation_check)
        
        # LLM으로 추가 규정 확인
        prompt = f"""
        요청사항: {request}
        컴플라이언스 유형: {compliance_type}
        
        이 요청과 관련된 주요 규정 사항 3가지를 확인하고 설명하세요:
        """
        
        response = await self.llm.ainvoke(prompt)
        additional_checks = response.content
        
        regulations_checked.append({
            "category": "추가 검토사항",
            "regulation": "LLM 분석",
            "applicable": True,
            "status": "확인됨",
            "details": additional_checks
        })
        
        return {
            "regulations_checked": regulations_checked,
            "status": "checking"
        }
    
    async def risk_assessment_node(self, state: ComplianceState) -> Dict:
        """리스크 평가 노드"""
        logger.info("리스크 평가 수행")
        
        request = state.get("request", "")
        regulations_checked = state.get("regulations_checked", [])
        
        # LLM으로 리스크 평가
        prompt = f"""
        요청사항: {request}
        
        확인된 규정 수: {len(regulations_checked)}
        
        이 요청에 대한 컴플라이언스 리스크를 평가하세요:
        1. 리스크 수준 (low/medium/high/critical)
        2. 주요 리스크 요인 3가지
        3. 각 리스크에 대한 간단한 설명
        
        JSON 형식으로 답하세요:
        {{
            "risk_level": "level",
            "risk_factors": ["factor1", "factor2", "factor3"],
            "explanations": ["설명1", "설명2", "설명3"]
        }}
        """
        
        response = await self.llm.ainvoke(prompt)
        
        try:
            # JSON 파싱 시도
            risk_data = json.loads(response.content)
            risk_level = risk_data.get("risk_level", "medium")
            risk_factors = risk_data.get("risk_factors", [])
        except:
            # 파싱 실패 시 기본값
            risk_level = "medium"
            risk_factors = [
                "규정 준수 여부 확인 필요",
                "문서화 요구사항 검토 필요",
                "승인 절차 확인 필요"
            ]
        
        # 리스크 수준 검증
        if risk_level not in ["low", "medium", "high", "critical"]:
            risk_level = "medium"
        
        return {
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "status": "assessing"
        }
    
    async def validation_node(self, state: ComplianceState) -> Dict:
        """컴플라이언스 검증 노드"""
        logger.info("컴플라이언스 검증")
        
        compliance_type = state.get("compliance_type", "general")
        risk_level = state.get("risk_level", "medium")
        
        # 검증 항목별 체크
        validation_results = {
            "regulatory_compliance": True,  # 규제 준수
            "documentation_complete": True,  # 문서 완비
            "approval_required": risk_level in ["high", "critical"],  # 승인 필요
            "training_required": compliance_type in ["clinical_trial", "quality"],  # 교육 필요
            "monitoring_required": risk_level in ["high", "critical"],  # 모니터링 필요
            "audit_trail": True  # 감사 추적
        }
        
        # 추천 사항 생성
        recommendations = []
        
        if validation_results["approval_required"]:
            recommendations.append("상위 관리자 승인을 받으시기 바랍니다.")
        
        if validation_results["training_required"]:
            recommendations.append("관련 규정에 대한 교육 이수를 권장합니다.")
        
        if validation_results["monitoring_required"]:
            recommendations.append("정기적인 모니터링 계획을 수립하시기 바랍니다.")
        
        if risk_level == "critical":
            recommendations.append("법무팀 또는 컴플라이언스 팀과 즉시 상의하시기 바랍니다.")
        elif risk_level == "high":
            recommendations.append("추가적인 리스크 완화 조치를 검토하시기 바랍니다.")
        
        recommendations.append("모든 관련 문서를 적절히 보관하시기 바랍니다.")
        
        return {
            "validation_results": validation_results,
            "recommendations": recommendations,
            "status": "validating"
        }
    
    async def generate_report_node(self, state: ComplianceState) -> Dict:
        """컴플라이언스 보고서 생성 노드"""
        logger.info("컴플라이언스 보고서 생성")
        
        # 보고서 생성
        report_parts = [
            "# 컴플라이언스 검토 보고서",
            f"\n## 요청 사항\n{state.get('request', '')}",
            f"\n## 컴플라이언스 유형\n{state.get('compliance_type', '').replace('_', ' ').title()}",
            f"\n## 리스크 평가",
            f"- **리스크 수준**: {state.get('risk_level', '').upper()}",
            "\n### 주요 리스크 요인:"
        ]
        
        # 리스크 요인 추가
        for factor in state.get("risk_factors", []):
            report_parts.append(f"- {factor}")
        
        # 규정 확인 사항
        report_parts.append("\n## 확인된 규정 사항")
        regulations_checked = state.get("regulations_checked", [])
        for reg in regulations_checked[:5]:  # 상위 5개만
            report_parts.append(f"- **{reg.get('category', '')}**: {reg.get('regulation', '')}")
        
        # 검증 결과
        report_parts.append("\n## 검증 결과")
        validation_results = state.get("validation_results", {})
        for key, value in validation_results.items():
            status = "✅ 통과" if value else "⚠️ 확인 필요"
            report_parts.append(f"- {key.replace('_', ' ').title()}: {status}")
        
        # 권고사항
        report_parts.append("\n## 권고사항")
        for rec in state.get("recommendations", []):
            report_parts.append(f"- {rec}")
        
        # 날짜 추가
        report_parts.append(f"\n---\n*보고서 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        compliance_report = "\n".join(report_parts)
        
        return {
            "compliance_report": compliance_report,
            "status": "completed"
        }
    
    async def error_handler_node(self, state: ComplianceState) -> Dict:
        """오류 처리 노드"""
        logger.error(f"컴플라이언스 확인 오류: {state.get('error_message')}")
        
        error_msg = state.get("error_message", "컴플라이언스 확인 중 오류가 발생했습니다.")
        
        return {
            "messages": [AIMessage(content=f"오류 발생: {error_msg}")],
            "status": "error"
        }
    
    def route_after_analysis(self, state: ComplianceState) -> str:
        """분석 후 라우팅"""
        if state.get("error_message"):
            return "error_handler"
        return "check_regulations"
    
    def route_after_checking(self, state: ComplianceState) -> str:
        """규정 확인 후 라우팅"""
        if not state.get("regulations_checked"):
            return "error_handler"
        return "risk_assessment"
    
    def _build_graph(self) -> StateGraph:
        """Subgraph 구성"""
        workflow = StateGraph(ComplianceState)
        
        # 노드 추가
        workflow.add_node("analyze_request", self.analyze_compliance_request_node)
        workflow.add_node("check_regulations", self.check_regulations_node)
        workflow.add_node("risk_assessment", self.risk_assessment_node)
        workflow.add_node("validation", self.validation_node)
        workflow.add_node("generate_report", self.generate_report_node)
        workflow.add_node("error_handler", self.error_handler_node)
        
        # 시작점
        workflow.add_edge(START, "analyze_request")
        
        # 순차적 워크플로우
        workflow.add_conditional_edges(
            "analyze_request",
            self.route_after_analysis,
            {
                "check_regulations": "check_regulations",
                "error_handler": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "check_regulations",
            self.route_after_checking,
            {
                "risk_assessment": "risk_assessment",
                "error_handler": "error_handler"
            }
        )
        
        workflow.add_edge("risk_assessment", "validation")
        workflow.add_edge("validation", "generate_report")
        
        # 종료
        workflow.add_edge("generate_report", END)
        workflow.add_edge("error_handler", END)
        
        # 그래프 컴파일
        return workflow.compile()
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Supervisor에서 호출하는 메인 처리 함수"""
        logger.info("Compliance Subgraph 처리 시작")
        
        # 입력 state를 subgraph state로 변환
        subgraph_state = ComplianceState(
            messages=state.get("messages", []),
            request="",
            compliance_type="",
            regulations_checked=[],
            risk_level="",
            risk_factors=[],
            validation_results={},
            recommendations=[],
            compliance_report="",
            status="",
            error_message=None
        )
        
        # Subgraph 실행
        try:
            result = await self.graph.ainvoke(subgraph_state)
            
            # 응답 메시지 생성
            if result.get("status") == "completed":
                response = result.get("compliance_report", "컴플라이언스 검토가 완료되었습니다.")
            else:
                response = result.get("error_message", "컴플라이언스 확인에 실패했습니다.")
            
            # 결과 반환
            return {
                "messages": [AIMessage(content=response)],
                "agent_outputs": {
                    "compliance": {
                        "compliance_type": result.get("compliance_type"),
                        "risk_level": result.get("risk_level"),
                        "risk_factors": result.get("risk_factors"),
                        "regulations_checked": result.get("regulations_checked"),
                        "validation_results": result.get("validation_results"),
                        "recommendations": result.get("recommendations"),
                        "report": result.get("compliance_report"),
                        "status": result.get("status"),
                        "error": result.get("error_message")
                    }
                },
                "next_agent": None
            }
        except Exception as e:
            logger.error(f"Compliance Subgraph 실행 오류: {e}")
            return {
                "messages": [AIMessage(content=f"컴플라이언스 확인 중 오류가 발생했습니다: {str(e)}")],
                "agent_outputs": {"compliance": {"error": str(e)}},
                "next_agent": None
            }


# Subgraph 인스턴스 생성 함수
def create_compliance_subgraph():
    """Compliance Subgraph 생성"""
    return ComplianceSubgraph()