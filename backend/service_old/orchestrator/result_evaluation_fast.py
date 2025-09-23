"""
Fast version of ResultEvaluationSubGraph without LLM calls
For debugging and testing purposes
"""

from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class EvaluationState(TypedDict):
    raw_results: Dict[str, Any]
    validation_rules: List[Dict]
    quality_scores: Dict[str, float]
    compliance_checks: Dict[str, Any]
    validated_results: Dict[str, Any]
    issues_found: List[str]
    recommendations: List[str]

class ResultEvaluationSubGraph:
    def __init__(self):
        self.workflow = StateGraph(EvaluationState)
        self._build_graph()

    def _build_graph(self):
        self.workflow.add_node("check_completeness", self.check_completeness)
        self.workflow.add_node("validate_accuracy", self.validate_accuracy)
        self.workflow.add_node("check_compliance", self.check_compliance)
        self.workflow.add_node("calculate_quality", self.calculate_quality_score)
        self.workflow.add_node("generate_recommendations", self.generate_recommendations)

        self.workflow.add_edge(START, "check_completeness")
        self.workflow.add_edge("check_completeness", "validate_accuracy")
        self.workflow.add_edge("validate_accuracy", "check_compliance")
        self.workflow.add_edge("check_compliance", "calculate_quality")

        self.workflow.add_conditional_edges(
            "calculate_quality",
            self.check_quality_threshold,
            {
                "high_quality": END,
                "needs_improvement": "generate_recommendations",
                "low_quality": "generate_recommendations"
            }
        )

        self.workflow.add_edge("generate_recommendations", END)

    async def check_completeness(self, state: EvaluationState) -> EvaluationState:
        """Fast version - no LLM"""
        state["quality_scores"] = state.get("quality_scores", {})
        state["quality_scores"]["completeness"] = 0.85
        logger.info("Completeness check: 0.85 (fast mode)")
        return state

    async def validate_accuracy(self, state: EvaluationState) -> EvaluationState:
        """Fast version - no LLM"""
        state["quality_scores"]["accuracy"] = 0.8
        logger.info("Accuracy check: 0.8 (fast mode)")
        return state

    async def check_compliance(self, state: EvaluationState) -> EvaluationState:
        """Fast version - no LLM"""
        state["compliance_checks"] = {
            "passed": True,
            "details": "Fast mode - compliance assumed OK"
        }
        logger.info("Compliance check: Passed (fast mode)")
        return state

    async def calculate_quality_score(self, state: EvaluationState) -> EvaluationState:
        """Calculate overall quality score"""
        scores = state.get("quality_scores", {})

        if not scores:
            scores = {
                "completeness": 0.7,
                "accuracy": 0.7,
                "compliance": 1.0
            }
            state["quality_scores"] = scores

        # Calculate weighted average
        weights = {
            "accuracy": 0.4,
            "completeness": 0.3,
            "compliance": 0.3
        }

        compliance_checks = state.get("compliance_checks", {})
        if compliance_checks.get("passed"):
            scores["compliance"] = 1.0
        else:
            scores["compliance"] = 0.3

        weighted_sum = 0
        total_weight = 0
        for key, score in scores.items():
            if key != "overall" and key in weights:
                weighted_sum += score * weights.get(key, 0.2)
                total_weight += weights.get(key, 0.2)

        if total_weight > 0:
            state["quality_scores"]["overall"] = weighted_sum / total_weight
        else:
            state["quality_scores"]["overall"] = 0.7

        logger.info(f"Overall quality score: {state['quality_scores']['overall']} (fast mode)")
        return state

    async def generate_recommendations(self, state: EvaluationState) -> EvaluationState:
        """Fast version - no LLM"""
        state["recommendations"] = [
            "데이터 품질 향상 권장",
            "정기적인 검증 프로세스 수립 필요"
        ]
        logger.info("Recommendations generated (fast mode)")
        return state

    def check_quality_threshold(self, state: EvaluationState) -> str:
        """Check quality threshold"""
        overall_score = state.get("quality_scores", {}).get("overall", 0)
        if overall_score >= 0.8:
            return "high_quality"
        elif overall_score >= 0.5:
            return "needs_improvement"
        else:
            return "low_quality"