"""
Compliance Validation Agent
규정 준수 검증 에이전트
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json

logger = logging.getLogger(__name__)


class ComplianceValidationAgent:
    """규정 준수 및 검증을 담당하는 에이전트"""

    def __init__(self, llm_provider: str = "openai"):
        """Initialize compliance validation agent"""
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.name = "ComplianceValidationAgent"

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """메인 실행 메서드"""
        start_time = datetime.now()

        try:
            # Extract task parameters
            validation_type = task.get("validation_type", "hr_policy")
            content_to_validate = task.get("content_to_validate", "")
            rules_to_check = task.get("rules_to_check", [])
            strict_mode = task.get("strict_mode", True)
            compliance_level = task.get("compliance_level", "must")

            # Perform validation based on type
            if validation_type == "hr_policy":
                result = await self._validate_hr_policy(
                    content_to_validate, rules_to_check, strict_mode
                )
            elif validation_type == "legal":
                result = await self._validate_legal_compliance(
                    content_to_validate, rules_to_check, compliance_level
                )
            elif validation_type == "regulatory":
                result = await self._validate_regulatory_compliance(
                    content_to_validate, rules_to_check
                )
            else:  # internal
                result = await self._validate_internal_policy(
                    content_to_validate, rules_to_check, strict_mode
                )

            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                "success": True,
                "confidence_score": result.get("confidence", 0.95),
                "execution_time": execution_time,
                "is_compliant": result.get("is_compliant", False),
                "violations": result.get("violations", []),
                "warnings": result.get("warnings", []),
                "recommendations": result.get("recommendations", []),
                "compliance_score": result.get("compliance_score", 0.0),
                "checked_rules": result.get("checked_rules", [])
            }

        except Exception as e:
            logger.error(f"Compliance validation failed: {str(e)}")
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                "success": False,
                "confidence_score": 0.0,
                "execution_time": execution_time,
                "is_compliant": False,
                "error": str(e)
            }

    async def _validate_hr_policy(
        self, content: str, rules: List[str], strict_mode: bool
    ) -> Dict[str, Any]:
        """HR 정책 준수 검증"""

        # Default HR rules if not provided
        if not rules:
            rules = await self._get_default_hr_rules()

        # Check compliance for each rule
        violations = []
        warnings = []
        checked_rules = []

        for rule in rules:
            check_result = await self._check_single_rule(content, rule, strict_mode)
            checked_rules.append(rule)

            if check_result["status"] == "violation":
                violations.append({
                    "rule": rule,
                    "description": check_result["description"],
                    "severity": check_result["severity"]
                })
            elif check_result["status"] == "warning":
                warnings.append(check_result["description"])

        # Calculate compliance score
        compliance_score = 1.0 - (len(violations) / max(len(rules), 1))
        is_compliant = len(violations) == 0 if strict_mode else compliance_score >= 0.7

        # Generate recommendations
        recommendations = await self._generate_recommendations(violations, warnings)

        return {
            "is_compliant": is_compliant,
            "violations": violations,
            "warnings": warnings,
            "recommendations": recommendations,
            "compliance_score": compliance_score,
            "checked_rules": checked_rules,
            "confidence": 0.92
        }

    async def _validate_legal_compliance(
        self, content: str, rules: List[str], compliance_level: str
    ) -> Dict[str, Any]:
        """법적 준수 검증"""

        system_prompt = """당신은 법적 규정 준수 전문가입니다.
        주어진 내용이 법적 요구사항을 충족하는지 검증하세요."""

        user_prompt = f"""다음 내용의 법적 준수 여부를 검증하세요:
        내용: {content}

        확인할 법적 규정: {', '.join(rules) if rules else '근로기준법, 개인정보보호법, 고용법'}
        준수 수준: {compliance_level}

        검증 항목:
        1. 법적 요구사항 충족 여부
        2. 잠재적 법적 위험
        3. 개선 필요사항"""

        response = await self.llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        # Parse LLM response
        validation_result = self._parse_legal_validation(response.content)

        return {
            "is_compliant": validation_result["is_compliant"],
            "violations": validation_result["violations"],
            "warnings": validation_result["warnings"],
            "recommendations": validation_result["recommendations"],
            "compliance_score": validation_result["score"],
            "checked_rules": rules or ["근로기준법", "개인정보보호법", "고용법"],
            "confidence": 0.88
        }

    async def _validate_regulatory_compliance(
        self, content: str, rules: List[str]
    ) -> Dict[str, Any]:
        """규제 준수 검증"""

        # Simulate regulatory check
        violations = []
        warnings = []

        # Check for common regulatory issues
        if "개인정보" in content and "동의" not in content:
            violations.append({
                "rule": "개인정보보호 규정",
                "description": "개인정보 수집 시 동의 절차 누락",
                "severity": "high"
            })

        if "계약" in content and "서명" not in content:
            warnings.append("계약서에 서명란이 명시되지 않음")

        compliance_score = 1.0 - (len(violations) * 0.3) - (len(warnings) * 0.1)
        is_compliant = len(violations) == 0

        return {
            "is_compliant": is_compliant,
            "violations": violations,
            "warnings": warnings,
            "recommendations": ["규제 준수 체크리스트 작성 권장"],
            "compliance_score": max(0, compliance_score),
            "checked_rules": rules or ["개인정보보호 규정", "노동 규제"],
            "confidence": 0.85
        }

    async def _validate_internal_policy(
        self, content: str, rules: List[str], strict_mode: bool
    ) -> Dict[str, Any]:
        """내부 정책 준수 검증"""

        # Internal policy validation
        violations = []
        warnings = []

        # Check internal policies
        internal_checks = [
            ("승인 절차", "approval", "승인 프로세스가 명시되어야 합니다"),
            ("문서 번호", "doc_number", "문서 번호 체계를 따라야 합니다"),
            ("보안 등급", "security_level", "보안 등급 표시가 필요합니다")
        ]

        for policy_name, keyword, description in internal_checks:
            if keyword not in content.lower():
                if strict_mode:
                    violations.append({
                        "rule": policy_name,
                        "description": description,
                        "severity": "medium"
                    })
                else:
                    warnings.append(description)

        compliance_score = 1.0 - (len(violations) * 0.25)
        is_compliant = len(violations) == 0

        return {
            "is_compliant": is_compliant,
            "violations": violations,
            "warnings": warnings,
            "recommendations": ["내부 정책 가이드라인 참조 필요"],
            "compliance_score": max(0, compliance_score),
            "checked_rules": rules or [check[0] for check in internal_checks],
            "confidence": 0.9
        }

    async def _get_default_hr_rules(self) -> List[str]:
        """기본 HR 규정 목록 반환"""
        return [
            "연차 사용 규정",
            "근무 시간 규정",
            "휴가 신청 절차",
            "출장 규정",
            "경비 처리 규정",
            "인사 평가 규정"
        ]

    async def _check_single_rule(
        self, content: str, rule: str, strict_mode: bool
    ) -> Dict[str, Any]:
        """단일 규정 확인"""

        prompt = f"""다음 내용이 '{rule}'을 준수하는지 확인하세요:
        내용: {content}

        엄격 모드: {strict_mode}

        응답 형식:
        - status: violation/warning/compliant
        - description: 설명
        - severity: high/medium/low"""

        response = await self.llm.ainvoke([HumanMessage(content=prompt)])

        # Parse response (simplified)
        result_text = response.content.lower()
        if "violation" in result_text or "위반" in result_text:
            return {
                "status": "violation",
                "description": f"{rule} 위반 사항 발견",
                "severity": "high" if strict_mode else "medium"
            }
        elif "warning" in result_text or "경고" in result_text:
            return {
                "status": "warning",
                "description": f"{rule} 관련 주의 필요",
                "severity": "low"
            }
        else:
            return {
                "status": "compliant",
                "description": f"{rule} 준수",
                "severity": "none"
            }

    async def _generate_recommendations(
        self, violations: List[Dict], warnings: List[str]
    ) -> List[str]:
        """위반사항 기반 권고사항 생성"""

        recommendations = []

        if violations:
            recommendations.append("발견된 위반사항을 즉시 수정하시기 바랍니다")
            for v in violations[:3]:  # Top 3 violations
                recommendations.append(f"{v['rule']} 관련 정책 재검토 필요")

        if warnings:
            recommendations.append("경고 사항에 대한 검토가 필요합니다")

        if not violations and not warnings:
            recommendations.append("현재 규정을 잘 준수하고 있습니다")

        return recommendations

    def _parse_legal_validation(self, llm_response: str) -> Dict[str, Any]:
        """LLM 법적 검증 응답 파싱"""

        # Simple parsing logic (in production, use more sophisticated parsing)
        is_compliant = "준수" in llm_response or "compliant" in llm_response.lower()

        violations = []
        if "위반" in llm_response or "violation" in llm_response.lower():
            violations.append({
                "rule": "법적 요구사항",
                "description": "법적 준수 사항 위반 발견",
                "severity": "high"
            })

        warnings = []
        if "주의" in llm_response or "warning" in llm_response.lower():
            warnings.append("법적 검토 필요")

        score = 1.0 if is_compliant else 0.5

        return {
            "is_compliant": is_compliant,
            "violations": violations,
            "warnings": warnings,
            "recommendations": ["법무팀 검토 권장"],
            "score": score
        }

    async def execute_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph 노드 실행 메서드"""

        # Extract task from state
        execution_state = state.get("execution_manager_state", {})
        pending_tasks = execution_state.get("pending_tasks", [])

        if not pending_tasks:
            logger.warning("No pending tasks for compliance validation")
            return state

        # Get first task for this agent
        task = None
        for t in pending_tasks:
            if t.get("agent") == "ComplianceValidationAgent":
                task = t
                break

        if not task:
            logger.warning("No compliance validation task found")
            return state

        # Execute task
        result = await self.execute(task)

        # Update state
        completed_tasks = execution_state.get("completed_tasks", [])
        completed_tasks.append({
            "task_id": task.get("task_id"),
            "agent": self.name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })

        # Remove from pending
        pending_tasks.remove(task)

        state["execution_manager_state"]["pending_tasks"] = pending_tasks
        state["execution_manager_state"]["completed_tasks"] = completed_tasks

        # Store agent-specific result
        if "agent_results" not in state:
            state["agent_results"] = {}
        state["agent_results"][self.name] = result

        logger.info(f"Compliance validation completed for task {task.get('task_id')}")
        return state