"""
Compliance Validation Agent
규정 위반 검토 에이전트 - RuleDB 활용
"""

from typing import Dict, Any, List, Optional, Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import Tool
from pydantic import BaseModel, Field
import logging
from datetime import datetime
import httpx
import asyncio
import json

logger = logging.getLogger(__name__)


class ComplianceCheckRequest(BaseModel):
    """규정 검토 요청"""
    
    document_type: str
    document_content: Dict[str, Any]
    check_level: Literal["basic", "standard", "strict"] = "standard"
    regulations_to_check: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ComplianceIssue(BaseModel):
    """규정 위반 이슈"""
    
    severity: Literal["critical", "high", "medium", "low"]
    regulation_type: str
    violation_code: str
    description: str
    affected_field: str
    suggestion: str
    reference: Optional[str] = None


class ComplianceCheckResult(BaseModel):
    """규정 검토 결과"""
    
    check_id: str
    document_id: str
    status: Literal["approved", "rejected", "conditional"]
    issues: List[ComplianceIssue]
    total_score: float  # 0-100
    checked_regulations: List[str]
    check_timestamp: str
    recommendations: List[str]


class ComplianceValidationAgent:
    """
    규정 검증 에이전트
    - RuleDB를 통한 규정 확인
    - 1차: 법규 검토 (의료법, 리베이트법, 공정거래규약)
    - 2차: 내부 규정 검토
    """
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        """
        Initialize Compliance Agent
        
        Args:
            api_base_url: FastAPI 서버 URL
        """
        
        self.api_base_url = api_base_url
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)  # 정확성을 위해 temperature=0
        
        # 규정별 도구 초기화
        self.tools = self._initialize_compliance_tools()
        
        # 규정 체크 우선순위
        self.check_priority = [
            "medical_law",        # 의료법
            "rebate_law",        # 리베이트법
            "fair_trade",        # 공정거래규약
            "internal_policy"    # 내부 규정
        ]
        
        # 캐시 (동일 문서 재검토 방지)
        self.cache = {}
    
    def _initialize_compliance_tools(self) -> Dict[str, Tool]:
        """규정 검토 도구 초기화"""
        
        tools = {
            "medical_law": Tool(
                name="check_medical_law",
                description="의료법 위반 검토",
                func=self._check_medical_law
            ),
            "rebate_law": Tool(
                name="check_rebate_law",
                description="리베이트 쌍벌제법 위반 검토",
                func=self._check_rebate_law
            ),
            "fair_trade": Tool(
                name="check_fair_trade",
                description="공정거래규약 위반 검토",
                func=self._check_fair_trade
            ),
            "internal_policy": Tool(
                name="check_internal_policy",
                description="내부 규정 위반 검토",
                func=self._check_internal_policy
            )
        }
        
        return tools
    
    async def validate_compliance(
        self,
        request: ComplianceCheckRequest
    ) -> ComplianceCheckResult:
        """
        규정 준수 검증 메인 메서드
        """
        
        logger.info(f"Starting compliance check for {request.document_type}")
        
        # 캐시 확인
        cache_key = self._generate_cache_key(request.document_content)
        if cache_key in self.cache:
            logger.info("Using cached compliance result")
            return self.cache[cache_key]
        
        # 1차: 법규 검토
        law_issues = await self._perform_law_checks(request)
        
        # 2차: 내부 규정 검토
        internal_issues = await self._perform_internal_checks(request)
        
        # 모든 이슈 통합
        all_issues = law_issues + internal_issues
        
        # 점수 계산
        compliance_score = self._calculate_compliance_score(all_issues)
        
        # 상태 결정
        status = self._determine_status(compliance_score, all_issues)
        
        # 권고사항 생성
        recommendations = await self._generate_recommendations(all_issues, request)
        
        # 결과 구성
        result = ComplianceCheckResult(
            check_id=self._generate_check_id(),
            document_id=request.metadata.get("document_id", "unknown"),
            status=status,
            issues=all_issues,
            total_score=compliance_score,
            checked_regulations=request.regulations_to_check or self.check_priority,
            check_timestamp=datetime.now().isoformat(),
            recommendations=recommendations
        )
        
        # 캐시 저장
        self.cache[cache_key] = result
        
        logger.info(f"Compliance check completed: {status} (score: {compliance_score})")
        return result
    
    async def _perform_law_checks(
        self,
        request: ComplianceCheckRequest
    ) -> List[ComplianceIssue]:
        """1차 법규 검토"""
        
        issues = []
        
        # RuleDB에서 법규 규칙 조회
        rules = await self._fetch_rules_from_db(["medical_law", "rebate_law", "fair_trade"])
        
        # 병렬로 법규 검토 수행
        check_tasks = []
        
        if self._should_check_medical_law(request.document_type):
            check_tasks.append(self._check_medical_law(request.document_content, rules.get("medical_law", [])))
        
        if self._should_check_rebate_law(request.document_type):
            check_tasks.append(self._check_rebate_law(request.document_content, rules.get("rebate_law", [])))
        
        if self._should_check_fair_trade(request.document_type):
            check_tasks.append(self._check_fair_trade(request.document_content, rules.get("fair_trade", [])))
        
        if check_tasks:
            check_results = await asyncio.gather(*check_tasks)
            for result in check_results:
                if result:
                    issues.extend(result)
        
        return issues
    
    async def _perform_internal_checks(
        self,
        request: ComplianceCheckRequest
    ) -> List[ComplianceIssue]:
        """2차 내부 규정 검토"""
        
        # RuleDB에서 내부 규정 조회
        internal_rules = await self._fetch_rules_from_db(["internal_policy"])
        
        # 내부 규정 검토
        issues = await self._check_internal_policy(
            request.document_content,
            internal_rules.get("internal_policy", [])
        )
        
        return issues
    
    async def _fetch_rules_from_db(self, rule_types: List[str]) -> Dict[str, List[Dict]]:
        """
        FastAPI를 통해 RuleDB에서 규칙 조회
        """
        
        rules = {}
        
        async with httpx.AsyncClient() as client:
            for rule_type in rule_types:
                try:
                    response = await client.get(
                        f"{self.api_base_url}/rules/{rule_type}",
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        rules[rule_type] = response.json()
                    else:
                        logger.error(f"Failed to fetch rules for {rule_type}: {response.status_code}")
                        rules[rule_type] = []
                        
                except Exception as e:
                    logger.error(f"Error fetching rules for {rule_type}: {e}")
                    rules[rule_type] = []
        
        return rules
    
    async def _check_medical_law(
        self,
        content: Dict[str, Any],
        rules: List[Dict]
    ) -> List[ComplianceIssue]:
        """의료법 위반 검토"""
        
        issues = []
        
        # 규칙 기반 검사
        for rule in rules:
            violation = await self._evaluate_rule(content, rule, "medical_law")
            if violation:
                issues.append(violation)
        
        # LLM 기반 추가 검사
        llm_check = await self._llm_medical_law_check(content)
        issues.extend(llm_check)
        
        return issues
    
    async def _check_rebate_law(
        self,
        content: Dict[str, Any],
        rules: List[Dict]
    ) -> List[ComplianceIssue]:
        """리베이트법 위반 검토"""
        
        issues = []
        
        # 금지된 키워드 체크
        prohibited_keywords = [
            "현금", "상품권", "접대", "향응", "금품", "리베이트",
            "사례비", "답례품", "후원", "협찬"
        ]
        
        content_str = json.dumps(content, ensure_ascii=False).lower()
        
        for keyword in prohibited_keywords:
            if keyword in content_str:
                issues.append(ComplianceIssue(
                    severity="high",
                    regulation_type="rebate_law",
                    violation_code="RB001",
                    description=f"리베이트 의심 키워드 감지: {keyword}",
                    affected_field="content",
                    suggestion="해당 내용을 제거하거나 수정하세요",
                    reference="약사법 제47조의2"
                ))
        
        # 금액 관련 검토
        if "budget" in content or "amount" in content:
            amount = content.get("budget", content.get("amount", 0))
            if isinstance(amount, (int, float)) and amount > 100000:  # 10만원 초과
                issues.append(ComplianceIssue(
                    severity="medium",
                    regulation_type="rebate_law",
                    violation_code="RB002",
                    description=f"과도한 금액 감지: {amount}원",
                    affected_field="budget/amount",
                    suggestion="금액을 재검토하거나 정당한 사유를 명시하세요",
                    reference="공정경쟁규약 제8조"
                ))
        
        return issues
    
    async def _check_fair_trade(
        self,
        content: Dict[str, Any],
        rules: List[Dict]
    ) -> List[ComplianceIssue]:
        """공정거래규약 위반 검토"""
        
        issues = []
        
        # 제품설명회 관련 검토
        if "seminar" in str(content).lower() or "product_seminar" in content.get("document_type", ""):
            # 참석자 수 확인
            attendees = content.get("expected_attendees", content.get("actual_attendees", 0))
            if attendees > 50:
                issues.append(ComplianceIssue(
                    severity="medium",
                    regulation_type="fair_trade",
                    violation_code="FT001",
                    description=f"과도한 참석자 수: {attendees}명",
                    affected_field="attendees",
                    suggestion="소규모 그룹으로 나누어 진행하는 것을 권장합니다",
                    reference="공정경쟁규약 세부운영기준"
                ))
        
        # 샘플 제공 관련 검토
        if "sample" in str(content).lower():
            quantity = content.get("quantity", 0)
            if quantity > 10:
                issues.append(ComplianceIssue(
                    severity="low",
                    regulation_type="fair_trade",
                    violation_code="FT002",
                    description=f"과도한 샘플 수량: {quantity}개",
                    affected_field="quantity",
                    suggestion="샘플 제공 목적과 필요성을 명확히 기재하세요",
                    reference="공정경쟁규약 제10조"
                ))
        
        return issues
    
    async def _check_internal_policy(
        self,
        content: Dict[str, Any],
        rules: List[Dict]
    ) -> List[ComplianceIssue]:
        """내부 규정 위반 검토"""
        
        issues = []
        
        # 문서 작성 시기 검토
        if "visit_date" in content or "event_date" in content:
            date_str = content.get("visit_date", content.get("event_date", ""))
            # 날짜 파싱 및 검증 (7일 이내 작성 규정)
            try:
                from datetime import datetime, timedelta
                event_date = datetime.fromisoformat(date_str)
                if (datetime.now() - event_date).days > 7:
                    issues.append(ComplianceIssue(
                        severity="low",
                        regulation_type="internal_policy",
                        violation_code="IP001",
                        description="보고서 작성 지연 (7일 초과)",
                        affected_field="date",
                        suggestion="향후 적시에 보고서를 작성해주세요",
                        reference="내부 영업 규정 3.2조"
                    ))
            except:
                pass
        
        # 필수 정보 누락 검토
        required_fields = self._get_required_fields(content.get("document_type", ""))
        missing_fields = [f for f in required_fields if not content.get(f)]
        
        if missing_fields:
            issues.append(ComplianceIssue(
                severity="medium",
                regulation_type="internal_policy",
                violation_code="IP002",
                description=f"필수 정보 누락: {', '.join(missing_fields)}",
                affected_field="required_fields",
                suggestion="누락된 정보를 보완해주세요",
                reference="문서 작성 가이드라인"
            ))
        
        return issues
    
    async def _evaluate_rule(
        self,
        content: Dict[str, Any],
        rule: Dict[str, Any],
        regulation_type: str
    ) -> Optional[ComplianceIssue]:
        """개별 규칙 평가"""
        
        # 규칙 조건 확인
        if not self._check_rule_conditions(content, rule.get("conditions", [])):
            return None
        
        # 위반 사항 생성
        return ComplianceIssue(
            severity=rule.get("severity", "medium"),
            regulation_type=regulation_type,
            violation_code=rule.get("code", "UNKNOWN"),
            description=rule.get("description", "규정 위반"),
            affected_field=rule.get("field", "unknown"),
            suggestion=rule.get("suggestion", "내용을 검토해주세요"),
            reference=rule.get("reference")
        )
    
    async def _llm_medical_law_check(self, content: Dict[str, Any]) -> List[ComplianceIssue]:
        """LLM을 활용한 의료법 검토"""
        
        system_prompt = """당신은 의료법 전문가입니다.
        
        다음 내용을 검토하여 의료법 위반 가능성을 평가하세요:
        1. 의료 광고 규정 위반
        2. 환자 정보 보호 위반
        3. 의료인 품위 손상
        4. 불법 의료 행위
        
        위반 사항이 있다면 JSON 형식으로 반환하세요:
        [{"severity": "high/medium/low", "description": "위반 내용", "suggestion": "개선 방안"}]
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"검토 내용: {json.dumps(content, ensure_ascii=False)}")
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            # JSON 파싱
            content_str = response.content
            if "```json" in content_str:
                content_str = content_str.split("```json")[1].split("```")[0].strip()
            
            violations = json.loads(content_str)
            
            issues = []
            for v in violations:
                issues.append(ComplianceIssue(
                    severity=v.get("severity", "medium"),
                    regulation_type="medical_law",
                    violation_code="ML_LLM",
                    description=v.get("description", ""),
                    affected_field="content",
                    suggestion=v.get("suggestion", ""),
                    reference="의료법"
                ))
            
            return issues
        except:
            return []
    
    def _check_rule_conditions(self, content: Dict[str, Any], conditions: List[Dict]) -> bool:
        """규칙 조건 확인"""
        
        for condition in conditions:
            field = condition.get("field")
            operator = condition.get("operator")
            value = condition.get("value")
            
            if field not in content:
                return False
            
            content_value = content[field]
            
            if operator == "equals" and content_value != value:
                return False
            elif operator == "contains" and value not in str(content_value):
                return False
            elif operator == "greater_than" and content_value <= value:
                return False
            elif operator == "less_than" and content_value >= value:
                return False
        
        return True
    
    def _calculate_compliance_score(self, issues: List[ComplianceIssue]) -> float:
        """규정 준수 점수 계산"""
        
        if not issues:
            return 100.0
        
        # 심각도별 감점
        severity_penalties = {
            "critical": 30,
            "high": 20,
            "medium": 10,
            "low": 5
        }
        
        total_penalty = sum(
            severity_penalties.get(issue.severity, 0)
            for issue in issues
        )
        
        # 최소 0점
        score = max(0, 100 - total_penalty)
        
        return score
    
    def _determine_status(
        self,
        score: float,
        issues: List[ComplianceIssue]
    ) -> str:
        """규정 준수 상태 결정"""
        
        # Critical 이슈가 있으면 무조건 거부
        if any(issue.severity == "critical" for issue in issues):
            return "rejected"
        
        # 점수 기반 결정
        if score >= 80:
            return "approved"
        elif score >= 60:
            return "conditional"
        else:
            return "rejected"
    
    async def _generate_recommendations(
        self,
        issues: List[ComplianceIssue],
        request: ComplianceCheckRequest
    ) -> List[str]:
        """개선 권고사항 생성"""
        
        recommendations = []
        
        # 이슈별 권고사항
        for issue in issues:
            if issue.suggestion not in recommendations:
                recommendations.append(issue.suggestion)
        
        # LLM 기반 종합 권고사항
        if issues:
            system_prompt = """발견된 규정 위반 사항을 바탕으로 
            실행 가능한 개선 방안 3가지를 제시하세요."""
            
            issue_summary = "\n".join([
                f"- {issue.description} ({issue.severity})"
                for issue in issues[:5]  # 상위 5개만
            ])
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"위반 사항:\n{issue_summary}")
            ]
            
            response = await self.llm.ainvoke(messages)
            
            # 권고사항 추가
            recommendations.append(response.content)
        
        return recommendations[:5]  # 최대 5개 권고사항
    
    def _should_check_medical_law(self, document_type: str) -> bool:
        """의료법 검토 필요 여부"""
        return document_type in ["visit_report", "product_seminar_request", "sample_request"]
    
    def _should_check_rebate_law(self, document_type: str) -> bool:
        """리베이트법 검토 필요 여부"""
        return document_type in ["product_seminar_request", "sample_request", "product_seminar_report"]
    
    def _should_check_fair_trade(self, document_type: str) -> bool:
        """공정거래규약 검토 필요 여부"""
        return True  # 모든 문서에 적용
    
    def _get_required_fields(self, document_type: str) -> List[str]:
        """문서 유형별 필수 필드"""
        
        required_fields_map = {
            "visit_report": ["hospital_name", "visit_date", "doctor_name", "discussion_content"],
            "product_seminar_request": ["hospital_name", "requested_date", "products"],
            "sample_request": ["hospital_name", "doctor_name", "product_name", "quantity"]
        }
        
        return required_fields_map.get(document_type, [])
    
    def _generate_cache_key(self, content: Dict[str, Any]) -> str:
        """캐시 키 생성"""
        
        import hashlib
        content_str = json.dumps(content, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(content_str.encode()).hexdigest()
    
    def _generate_check_id(self) -> str:
        """검토 ID 생성"""
        
        from uuid import uuid4
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"CHECK_{timestamp}_{str(uuid4())[:8]}"


# === Graph Node Function ===

async def compliance_validation_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Graph node for compliance validation
    """
    
    agent = ComplianceValidationAgent()
    
    # 검토할 문서 추출
    documents = state.get("generated_documents", [])
    
    if not documents:
        return {
            "compliance_status": "no_documents",
            "compliance_issues": []
        }
    
    # 각 문서에 대해 규정 검토
    all_issues = []
    all_results = []
    
    for doc in documents:
        request = ComplianceCheckRequest(
            document_type=doc.get("document_type", "unknown"),
            document_content=doc.get("content", {}),
            check_level=state.get("compliance_level", "standard"),
            metadata=doc.get("metadata", {})
        )
        
        result = await agent.validate_compliance(request)
        all_results.append(result.dict())
        all_issues.extend(result.issues)
    
    # 최종 상태 결정
    if any(r["status"] == "rejected" for r in all_results):
        final_status = "rejected"
    elif any(r["status"] == "conditional" for r in all_results):
        final_status = "conditional"
    else:
        final_status = "approved"
    
    # 상태 업데이트
    return {
        "compliance_status": final_status,
        "compliance_issues": [issue.dict() for issue in all_issues],
        "compliance_results": all_results,
        "next_step": "complete" if final_status == "approved" else "revision_needed"
    }
