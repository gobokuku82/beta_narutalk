"""
Mock version of ResultEvaluationSubGraph to isolate the issue
"""

import asyncio
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List, Dict, Any

class EvaluationState(TypedDict):
    raw_results: Dict[str, Any]
    validation_rules: List[Dict]
    quality_scores: Dict[str, float]
    compliance_checks: Dict[str, Any]
    validated_results: Dict[str, Any]
    issues_found: List[str]
    recommendations: List[str]

async def test_mock_evaluation():
    """ResultEvaluationSubGraph와 동일한 구조로 Mock 테스트"""

    workflow = StateGraph(EvaluationState)

    # Mock 노드들 (LLM 호출 없이)
    async def check_completeness(state):
        print("check_completeness")
        state["quality_scores"] = {"completeness": 0.8}
        return state

    async def validate_accuracy(state):
        print("validate_accuracy")
        state["quality_scores"]["accuracy"] = 0.7
        return state

    async def check_compliance(state):
        print("check_compliance")
        state["compliance_checks"] = {"passed": True}
        return state

    async def calculate_quality(state):
        print("calculate_quality")
        state["quality_scores"]["overall"] = 0.75
        return state

    async def generate_recommendations(state):
        print("generate_recommendations")
        state["recommendations"] = ["Test recommendation"]
        return state

    def check_quality_threshold(state):
        score = state.get("quality_scores", {}).get("overall", 0)
        if score >= 0.8:
            return "high_quality"
        elif score >= 0.5:
            return "needs_improvement"
        else:
            return "low_quality"

    # 워크플로우 구성 (원본과 동일)
    workflow.add_node("check_completeness", check_completeness)
    workflow.add_node("validate_accuracy", validate_accuracy)
    workflow.add_node("check_compliance", check_compliance)
    workflow.add_node("calculate_quality", calculate_quality)
    workflow.add_node("generate_recommendations", generate_recommendations)

    workflow.add_edge(START, "check_completeness")
    workflow.add_edge("check_completeness", "validate_accuracy")
    workflow.add_edge("validate_accuracy", "check_compliance")
    workflow.add_edge("check_compliance", "calculate_quality")

    workflow.add_conditional_edges(
        "calculate_quality",
        check_quality_threshold,
        {
            "high_quality": END,
            "needs_improvement": "generate_recommendations",
            "low_quality": "generate_recommendations"
        }
    )

    workflow.add_edge("generate_recommendations", END)

    # 컴파일 및 실행
    app = workflow.compile()

    initial_state = {
        "raw_results": {"test": "data"},
        "validation_rules": [],
        "quality_scores": {},
        "compliance_checks": {},
        "validated_results": {},
        "issues_found": [],
        "recommendations": []
    }

    print("Starting mock workflow...")
    try:
        result = await asyncio.wait_for(
            app.ainvoke(initial_state),
            timeout=5.0
        )
        print(f"SUCCESS! Overall score: {result['quality_scores']['overall']}")
        return True
    except asyncio.TimeoutError:
        print("TIMEOUT - Mock workflow also hangs!")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mock_evaluation())
    print(f"\nMock test: {'PASSED' if success else 'FAILED'}")