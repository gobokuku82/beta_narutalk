"""
Compliance Check Agent - Policy and regulation compliance verification
Fully compliant with LangGraph 0.6.x Context API
"""

from typing import Dict, Any, List, Type
from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime
import asyncio
from pathlib import Path
import logging
from datetime import datetime
import json

from ..core.base_agent import BaseAgent
from ..core.states import ComplianceState
from ..core.context import AgentContext
from ..core.config import Config


logger = logging.getLogger(__name__)


class ComplianceCheckAgent(BaseAgent):
    """Agent for checking compliance with policies and regulations with Runtime support"""

    def __init__(self):
        super().__init__("compliance_check_agent")
        self.compliance_db_path = Config.get_database_path("compliance")

    def _get_state_schema(self) -> Type:
        """Get the state schema for this agent"""
        return ComplianceState

    def _build_graph(self):
        """Build the compliance check workflow with context support"""
        # StateGraph with context_schema following LangGraph 0.6.x pattern
        self.workflow = StateGraph(ComplianceState, context_schema=AgentContext)

        # Add nodes - all nodes will receive Runtime parameter
        self.workflow.add_node("analyze_request", self.analyze_request)
        self.workflow.add_node("fetch_policies", self.fetch_policies)
        self.workflow.add_node("check_compliance", self.check_compliance)
        self.workflow.add_node("generate_recommendations", self.generate_recommendations)
        self.workflow.add_node("format_results", self.format_results)

        # Add edges
        self.workflow.add_edge(START, "analyze_request")
        self.workflow.add_edge("analyze_request", "fetch_policies")
        self.workflow.add_edge("fetch_policies", "check_compliance")
        self.workflow.add_edge("check_compliance", "generate_recommendations")
        self.workflow.add_edge("generate_recommendations", "format_results")
        self.workflow.add_edge("format_results", END)

    async def _validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data"""
        required_fields = ["check_type"]
        for field in required_fields:
            if field not in input_data:
                self.logger.error(f"Missing required field: {field}")
                return False
        return True

    def _create_initial_state(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create initial ComplianceState from input data
        Only workflow data, no context fields
        """
        return {
            # Workflow status fields
            "status": "pending",
            "execution_step": "starting",

            # ComplianceState specific fields
            "check_type": input_data.get("check_type", "general"),
            "check_target": input_data.get("check_target", ""),
            "period": input_data.get("period", "current"),
            "applicable_policies": [],
            "compliance_status": {},
            "violations": [],
            "risk_level": "",
            "recommendations": [],
            "compliance_report": {}
        }

    # ==================== Node Functions with Runtime ====================
    # All nodes now receive Runtime[AgentContext] and return partial updates

    async def analyze_request(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Analyze the compliance check request

        Args:
            state: Current workflow state
            runtime: Runtime with context access

        Returns:
            Partial state update (only changed fields)
        """
        try:
            # Access context through runtime
            user_id = getattr(runtime.context, "user_id", "unknown")
            self.logger.info(f"Analyzing compliance request for user: {user_id}")

            check_type = state.get("check_type", "general")
            check_target = state.get("check_target", "")

            # Determine risk level based on check type
            risk_level = "medium"
            if check_type in ["financial", "legal", "security"]:
                risk_level = "high"
            elif check_type in ["administrative", "general"]:
                risk_level = "low"

            self.logger.info(f"Compliance check: type={check_type}, target={check_target}, risk={risk_level}")

            # Return ONLY changed fields (Context API pattern)
            return {
                "status": "processing",
                "execution_step": "request_analyzed",
                "risk_level": risk_level
            }

        except Exception as e:
            self.logger.error(f"Error analyzing request: {e}")

            # Log error in context if possible
            if hasattr(runtime.context, 'add_error'):
                runtime.context.add_error(f"Request analysis failed: {str(e)}")

            # Return failure status
            return {
                "status": "failed",
                "execution_step": "analysis_failed"
            }

    async def fetch_policies(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Fetch relevant policies for the compliance check

        Args:
            state: Current workflow state
            runtime: Runtime with context access

        Returns:
            Partial state update
        """
        try:
            # Access context
            session_id = getattr(runtime.context, "session_id", "unknown")
            self.logger.info(f"Fetching policies for session: {session_id}")

            check_type = state.get("check_type", "general")

            # Mock policy data for now
            # TODO: Integrate with real policy database
            mock_policies = []
            if check_type == "hr":
                mock_policies = [
                    {"id": "HR001", "title": "근태 관리 규정", "category": "attendance"},
                    {"id": "HR002", "title": "연차 사용 규정", "category": "leave"}
                ]
            elif check_type == "financial":
                mock_policies = [
                    {"id": "FIN001", "title": "경비 처리 규정", "category": "expense"},
                    {"id": "FIN002", "title": "구매 승인 규정", "category": "procurement"}
                ]
            else:
                mock_policies = [
                    {"id": "GEN001", "title": "일반 업무 규정", "category": "general"}
                ]

            self.logger.info(f"Found {len(mock_policies)} applicable policies")

            # Return partial update
            return {
                "execution_step": "policies_fetched",
                "applicable_policies": mock_policies
            }

        except Exception as e:
            self.logger.error(f"Error fetching policies: {e}")

            # Log error in context
            if hasattr(runtime.context, 'add_error'):
                runtime.context.add_error(f"Policy fetch failed: {str(e)}")

            return {
                "execution_step": "policy_fetch_failed",
                "applicable_policies": []
            }

    async def check_compliance(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Check compliance against policies

        Args:
            state: Current workflow state
            runtime: Runtime with context access

        Returns:
            Partial state update
        """
        try:
            # Access context for logging
            user_id = getattr(runtime.context, "user_id", "unknown")
            self.logger.info(f"Checking compliance for user: {user_id}")

            policies = state.get("applicable_policies", [])
            check_target = state.get("check_target", "")

            compliance_status = {}
            violations = []

            # Mock compliance check
            for policy in policies:
                # Simulate compliance check (random for demo)
                import random
                is_compliant = random.choice([True, True, False])  # 66% compliant

                compliance_status[policy["id"]] = {
                    "policy": policy["title"],
                    "compliant": is_compliant,
                    "checked_at": datetime.now().isoformat()
                }

                if not is_compliant:
                    violations.append({
                        "policy_id": policy["id"],
                        "policy_title": policy["title"],
                        "violation_type": "minor",
                        "description": f"{check_target}이(가) {policy['title']}을 위반했을 가능성이 있습니다."
                    })

            self.logger.info(f"Compliance check complete: {len(violations)} violations found")

            # Return partial update
            return {
                "execution_step": "compliance_checked",
                "compliance_status": compliance_status,
                "violations": violations
            }

        except Exception as e:
            self.logger.error(f"Error checking compliance: {e}")

            # Log error in context
            if hasattr(runtime.context, 'add_error'):
                runtime.context.add_error(f"Compliance check failed: {str(e)}")

            return {
                "execution_step": "compliance_check_failed",
                "compliance_status": {},
                "violations": []
            }

    async def generate_recommendations(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Generate recommendations based on compliance check

        Args:
            state: Current workflow state
            runtime: Runtime with context access

        Returns:
            Partial state update
        """
        try:
            # Access context
            session_id = getattr(runtime.context, "session_id", "unknown")
            self.logger.info(f"Generating recommendations for session: {session_id}")

            violations = state.get("violations", [])
            risk_level = state.get("risk_level", "medium")

            recommendations = []

            if violations:
                # Generate recommendations for each violation
                for violation in violations:
                    recommendations.append({
                        "priority": "high" if risk_level == "high" else "medium",
                        "action": f"{violation['policy_title']} 준수를 위한 조치 필요",
                        "description": f"정책 검토 및 필요시 시정 조치를 취하시기 바랍니다.",
                        "deadline": "즉시" if risk_level == "high" else "1주일 이내"
                    })
            else:
                # No violations - positive recommendation
                recommendations.append({
                    "priority": "low",
                    "action": "현재 규정을 잘 준수하고 있습니다",
                    "description": "계속해서 규정을 준수해 주시기 바랍니다.",
                    "deadline": "해당 없음"
                })

            self.logger.info(f"Generated {len(recommendations)} recommendations")

            # Return partial update
            return {
                "execution_step": "recommendations_generated",
                "recommendations": recommendations
            }

        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")

            # Log error in context
            if hasattr(runtime.context, 'add_error'):
                runtime.context.add_error(f"Recommendation generation failed: {str(e)}")

            return {
                "execution_step": "recommendation_generation_failed",
                "recommendations": []
            }

    async def format_results(
        self,
        state: Dict[str, Any],
        runtime: Runtime[AgentContext]
    ) -> Dict[str, Any]:
        """
        Format the compliance check results

        Args:
            state: Current workflow state
            runtime: Runtime with context access

        Returns:
            Partial state update with final report
        """
        try:
            # Access context
            user_id = getattr(runtime.context, "user_id", "unknown")
            self.logger.info(f"Formatting results for user: {user_id}")

            compliance_report = {
                "status": "success",
                "check_type": state.get("check_type", ""),
                "check_target": state.get("check_target", ""),
                "risk_level": state.get("risk_level", ""),
                "summary": {
                    "total_policies": len(state.get("applicable_policies", [])),
                    "violations_found": len(state.get("violations", [])),
                    "compliance_rate": self._calculate_compliance_rate(state)
                },
                "compliance_status": state.get("compliance_status", {}),
                "violations": state.get("violations", []),
                "recommendations": state.get("recommendations", []),
                "generated_at": datetime.now().isoformat()
            }

            self.logger.info("Compliance report generated successfully")

            # Return partial update
            return {
                "status": "completed",
                "execution_step": "results_formatted",
                "compliance_report": compliance_report
            }

        except Exception as e:
            self.logger.error(f"Error formatting results: {e}")

            # Log error in context
            if hasattr(runtime.context, 'add_error'):
                runtime.context.add_error(f"Result formatting failed: {str(e)}")

            return {
                "status": "failed",
                "execution_step": "formatting_failed",
                "compliance_report": {
                    "status": "error",
                    "error": str(e)
                }
            }

    # ==================== Helper Methods ====================

    def _calculate_compliance_rate(self, state: Dict[str, Any]) -> float:
        """Calculate compliance rate"""
        compliance_status = state.get("compliance_status", {})
        if not compliance_status:
            return 100.0

        total = len(compliance_status)
        compliant = sum(1 for s in compliance_status.values() if s.get("compliant"))

        return round((compliant / total) * 100, 1) if total > 0 else 100.0