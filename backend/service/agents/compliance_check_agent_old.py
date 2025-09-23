"""
Compliance Check Agent - Policy and regulation compliance verification
"""

from typing import Dict, Any, List
from langgraph.graph import StateGraph, START, END
import asyncio
from pathlib import Path
import logging
from datetime import datetime

from ..core.base_agent import BaseAgent
from ..core.states import ComplianceState
from ..core.config import Config


logger = logging.getLogger(__name__)


class ComplianceCheckAgent(BaseAgent):
    """Agent for checking policy and regulation compliance"""

    def __init__(self):
        super().__init__("compliance_check_agent")
        self.compliance_db_path = Config.get_database_path("compliance")

    def _build_graph(self):
        """Build the compliance check workflow"""
        self.workflow = StateGraph(ComplianceState)

        # Add nodes
        self.workflow.add_node("parse_request", self.parse_request)
        self.workflow.add_node("load_rules", self.load_compliance_rules)
        self.workflow.add_node("check_compliance", self.check_compliance)
        self.workflow.add_node("identify_violations", self.identify_violations)
        self.workflow.add_node("generate_recommendations", self.generate_recommendations)
        self.workflow.add_node("create_report", self.create_compliance_report)

        # Add edges
        self.workflow.add_edge(START, "parse_request")
        self.workflow.add_edge("parse_request", "load_rules")
        self.workflow.add_edge("load_rules", "check_compliance")
        self.workflow.add_edge("check_compliance", "identify_violations")
        self.workflow.add_edge("identify_violations", "generate_recommendations")
        self.workflow.add_edge("generate_recommendations", "create_report")
        self.workflow.add_edge("create_report", END)

    async def _validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data"""
        required_fields = ["target_action"]
        for field in required_fields:
            if field not in input_data:
                self.logger.error(f"Missing required field: {field}")
                return False
        return True

    async def parse_request(self, state: ComplianceState) -> ComplianceState:
        """Parse the compliance check request"""
        try:
            state["status"] = "processing"

            # Set default check type if not specified
            if not state.get("check_type"):
                state["check_type"] = "policy"

            # Initialize empty lists
            state["violations"] = []
            state["recommendations"] = []
            state["rules_checked"] = []

            self.logger.info(f"Compliance check request parsed - Type: {state.get('check_type')}, Action: {state.get('target_action')}")
            return state

        except Exception as e:
            self.logger.error(f"Error parsing request: {e}")
            state["error_logs"] = state.get("error_logs", []) + [str(e)]
            state["status"] = "failed"
            return state

    async def load_compliance_rules(self, state: ComplianceState) -> ComplianceState:
        """Load relevant compliance rules"""
        try:
            check_type = state.get("check_type", "policy")
            target_action = state.get("target_action", "")

            # For now, use mock rules
            # TODO: Load from real compliance database later
            mock_rules = self._get_mock_compliance_rules(check_type, target_action)

            state["rules_checked"] = mock_rules
            self.logger.info(f"Loaded {len(mock_rules)} compliance rules")

        except Exception as e:
            self.logger.error(f"Error loading rules: {e}")
            state["error_logs"] = state.get("error_logs", []) + [str(e)]
            state["rules_checked"] = []

        return state

    async def check_compliance(self, state: ComplianceState) -> ComplianceState:
        """Check compliance against loaded rules"""
        try:
            rules = state.get("rules_checked", [])
            context = state.get("context", {})
            target_action = state.get("target_action", "")

            compliance_results = {}
            total_score = 0
            checked_count = 0

            for rule in rules:
                rule_id = rule.get("id", "")
                rule_type = rule.get("type", "")

                # Simple compliance check logic
                is_compliant = self._evaluate_rule(rule, target_action, context)

                compliance_results[rule_id] = {
                    "rule": rule,
                    "compliant": is_compliant,
                    "checked_at": datetime.now().isoformat()
                }

                if is_compliant:
                    total_score += 1
                checked_count += 1

            # Calculate compliance score
            state["compliance_score"] = (total_score / checked_count * 100) if checked_count > 0 else 0
            state["is_compliant"] = state["compliance_score"] >= 80  # 80% threshold
            state["compliance_checks"] = compliance_results

            self.logger.info(f"Compliance check completed - Score: {state['compliance_score']:.1f}%")

        except Exception as e:
            self.logger.error(f"Error checking compliance: {e}")
            state["error_logs"] = state.get("error_logs", []) + [str(e)]
            state["compliance_score"] = 0
            state["is_compliant"] = False

        return state

    async def identify_violations(self, state: ComplianceState) -> ComplianceState:
        """Identify specific violations"""
        try:
            compliance_checks = state.get("compliance_checks", {})
            violations = []

            for rule_id, result in compliance_checks.items():
                if not result.get("compliant", True):
                    rule = result.get("rule", {})
                    violations.append({
                        "rule_id": rule_id,
                        "rule_name": rule.get("name", "Unknown Rule"),
                        "severity": rule.get("severity", "medium"),
                        "description": rule.get("description", ""),
                        "violation_details": f"Action '{state.get('target_action', '')}' violates {rule.get('name', 'rule')}"
                    })

            state["violations"] = violations
            self.logger.info(f"Identified {len(violations)} violations")

        except Exception as e:
            self.logger.error(f"Error identifying violations: {e}")
            state["error_logs"] = state.get("error_logs", []) + [str(e)]
            state["violations"] = []

        return state

    async def generate_recommendations(self, state: ComplianceState) -> ComplianceState:
        """Generate recommendations based on violations"""
        try:
            violations = state.get("violations", [])
            recommendations = []

            for violation in violations:
                severity = violation.get("severity", "medium")
                rule_name = violation.get("rule_name", "")

                # Generate recommendations based on severity
                if severity == "critical":
                    recommendations.append({
                        "priority": "high",
                        "action": f"즉시 {rule_name} 규정을 검토하고 준수하십시오",
                        "details": "이 위반사항은 즉시 조치가 필요합니다"
                    })
                elif severity == "high":
                    recommendations.append({
                        "priority": "medium",
                        "action": f"{rule_name} 규정 준수를 위한 조치 계획을 수립하십시오",
                        "details": "가능한 빠른 시일 내에 개선이 필요합니다"
                    })
                else:
                    recommendations.append({
                        "priority": "low",
                        "action": f"{rule_name} 관련 프로세스 개선을 고려하십시오",
                        "details": "장기적인 개선 계획에 포함시키십시오"
                    })

            # Add general recommendations if compliant
            if state.get("is_compliant", False) and not violations:
                recommendations.append({
                    "priority": "info",
                    "action": "현재 규정을 잘 준수하고 있습니다",
                    "details": "정기적인 검토를 계속하십시오"
                })

            state["recommendations"] = recommendations
            self.logger.info(f"Generated {len(recommendations)} recommendations")

        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            state["error_logs"] = state.get("error_logs", []) + [str(e)]
            state["recommendations"] = []

        return state

    async def create_compliance_report(self, state: ComplianceState) -> ComplianceState:
        """Create the final compliance report"""
        try:
            state["compliance_report"] = {
                "status": "success",
                "check_type": state.get("check_type", ""),
                "target_action": state.get("target_action", ""),
                "is_compliant": state.get("is_compliant", False),
                "compliance_score": state.get("compliance_score", 0),
                "rules_checked": len(state.get("rules_checked", [])),
                "violations": state.get("violations", []),
                "recommendations": state.get("recommendations", []),
                "checked_at": datetime.now().isoformat()
            }

            state["status"] = "completed"
            self.logger.info("Compliance report created successfully")

        except Exception as e:
            self.logger.error(f"Error creating report: {e}")
            state["error_logs"] = state.get("error_logs", []) + [str(e)]
            state["status"] = "failed"
            state["compliance_report"] = {
                "status": "error",
                "error": str(e)
            }

        return state

    def _get_mock_compliance_rules(self, check_type: str, target_action: str) -> List[Dict[str, Any]]:
        """Get mock compliance rules for testing"""
        rules = []

        if "채용" in target_action or "hire" in target_action.lower():
            rules.extend([
                {
                    "id": "HR-001",
                    "name": "채용 프로세스 규정",
                    "type": "policy",
                    "severity": "high",
                    "description": "모든 채용은 공정한 절차를 따라야 함"
                },
                {
                    "id": "HR-002",
                    "name": "차별 금지 정책",
                    "type": "regulation",
                    "severity": "critical",
                    "description": "채용 시 차별 금지"
                }
            ])

        if "지출" in target_action or "expense" in target_action.lower():
            rules.extend([
                {
                    "id": "FIN-001",
                    "name": "지출 승인 규정",
                    "type": "policy",
                    "severity": "medium",
                    "description": "일정 금액 이상 지출은 사전 승인 필요"
                },
                {
                    "id": "FIN-002",
                    "name": "예산 준수 정책",
                    "type": "regulation",
                    "severity": "high",
                    "description": "부서별 예산 한도 준수"
                }
            ])

        # Default rules if no specific match
        if not rules:
            rules = [
                {
                    "id": "GEN-001",
                    "name": "일반 업무 규정",
                    "type": check_type,
                    "severity": "low",
                    "description": "표준 업무 절차 준수"
                }
            ]

        return rules

    def _evaluate_rule(self, rule: Dict[str, Any], target_action: str, context: Dict[str, Any]) -> bool:
        """Evaluate if an action complies with a rule"""
        # Simple mock evaluation logic
        # In real implementation, this would check actual compliance
        import random

        # Simulate compliance check
        if rule.get("severity") == "critical":
            return random.random() > 0.3  # 70% compliant
        elif rule.get("severity") == "high":
            return random.random() > 0.2  # 80% compliant
        else:
            return random.random() > 0.1  # 90% compliant