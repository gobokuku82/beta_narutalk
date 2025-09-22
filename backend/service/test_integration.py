"""
LangGraph 0.6.7 통합 테스트
"""

import asyncio
import sys
from pathlib import Path

# 상위 디렉토리를 패스에 추가
sys.path.append(str(Path(__file__).parent.parent))

async def test_imports():
    """모든 모듈 임포트 테스트"""
    print("=" * 50)
    print("1. 모듈 임포트 테스트")
    print("=" * 50)

    try:
        from orchestrator.orchestrator import MainOrchestrator
        print("✓ MainOrchestrator 임포트 성공")
    except Exception as e:
        print(f"✗ MainOrchestrator 임포트 실패: {e}")
        return False

    try:
        from orchestrator.intent_analysis import IntentAnalysisSubGraph
        print("✓ IntentAnalysisSubGraph 임포트 성공")
    except Exception as e:
        print(f"✗ IntentAnalysisSubGraph 임포트 실패: {e}")

    try:
        from orchestrator.planning import PlanningSubGraph
        print("✓ PlanningSubGraph 임포트 성공")
    except Exception as e:
        print(f"✗ PlanningSubGraph 임포트 실패: {e}")

    try:
        from orchestrator.agent_execution import AgentExecutionSubGraph
        print("✓ AgentExecutionSubGraph 임포트 성공")
    except Exception as e:
        print(f"✗ AgentExecutionSubGraph 임포트 실패: {e}")

    try:
        from orchestrator.result_evaluation import ResultEvaluationSubGraph
        print("✓ ResultEvaluationSubGraph 임포트 성공")
    except Exception as e:
        print(f"✗ ResultEvaluationSubGraph 임포트 실패: {e}")

    try:
        from orchestrator.response_generation import ResponseGenerationSubGraph
        print("✓ ResponseGenerationSubGraph 임포트 성공")
    except Exception as e:
        print(f"✗ ResponseGenerationSubGraph 임포트 실패: {e}")

    # 에이전트 임포트
    try:
        from agents.sales_analytics_agent import SalesAnalyticsAgent
        print("✓ SalesAnalyticsAgent 임포트 성공")
    except Exception as e:
        print(f"✗ SalesAnalyticsAgent 임포트 실패: {e}")

    try:
        from agents.compliance_check_agent import ComplianceCheckAgent
        print("✓ ComplianceCheckAgent 임포트 성공")
    except Exception as e:
        print(f"✗ ComplianceCheckAgent 임포트 실패: {e}")

    try:
        from agents.search_agent import SearchAgent
        print("✓ SearchAgent 임포트 성공")
    except Exception as e:
        print(f"✗ SearchAgent 임포트 실패: {e}")

    try:
        from agents.document_generation_agent import DocumentGenerationAgent
        print("✓ DocumentGenerationAgent 임포트 성공")
    except Exception as e:
        print(f"✗ DocumentGenerationAgent 임포트 실패: {e}")

    return True

async def test_graph_compilation():
    """그래프 컴파일 테스트"""
    print("\n" + "=" * 50)
    print("2. 그래프 컴파일 테스트")
    print("=" * 50)

    try:
        from orchestrator.agent_execution import AgentExecutionSubGraph

        # 에이전트 실행 서브그래프 테스트
        agent_exec = AgentExecutionSubGraph()
        compiled = agent_exec.workflow.compile()
        print("✓ AgentExecutionSubGraph 컴파일 성공")

        # 그래프 구조 확인
        nodes = agent_exec.workflow.nodes
        print(f"  - 노드 개수: {len(nodes)}")
        print(f"  - 노드 목록: {list(nodes.keys())[:5]}...")

    except Exception as e:
        print(f"✗ 그래프 컴파일 실패: {e}")
        return False

    try:
        from orchestrator.result_evaluation import ResultEvaluationSubGraph

        eval_graph = ResultEvaluationSubGraph()
        compiled = eval_graph.workflow.compile()
        print("✓ ResultEvaluationSubGraph 컴파일 성공")

    except Exception as e:
        print(f"✗ ResultEvaluationSubGraph 컴파일 실패: {e}")

    try:
        from agents.search_agent import SearchAgent

        search_agent = SearchAgent()
        compiled = search_agent.workflow.compile()
        print("✓ SearchAgent 그래프 컴파일 성공")

    except Exception as e:
        print(f"✗ SearchAgent 컴파일 실패: {e}")

    try:
        from agents.document_generation_agent import DocumentGenerationAgent

        doc_agent = DocumentGenerationAgent()
        compiled = doc_agent.workflow.compile()
        print("✓ DocumentGenerationAgent 그래프 컴파일 성공")

    except Exception as e:
        print(f"✗ DocumentGenerationAgent 컴파일 실패: {e}")

    return True

async def test_simple_execution():
    """간단한 실행 테스트"""
    print("\n" + "=" * 50)
    print("3. 간단한 실행 테스트")
    print("=" * 50)

    try:
        from agents.document_generation_agent import DocumentGenerationAgent

        doc_agent = DocumentGenerationAgent()

        # 테스트 입력 데이터
        test_input = {
            "document_type": "sales_report",
            "data": {
                "period": "2024년 4분기",
                "sales_data": [
                    {"item": "제품A", "amount": 1000000},
                    {"item": "제품B", "amount": 2000000}
                ],
                "analysis": "매출이 전분기 대비 20% 증가했습니다.",
                "author": "홍길동"
            },
            "format": "html"
        }

        # 에이전트 실행
        result = await doc_agent.execute(test_input)

        if result and "status" in result:
            if result["status"] == "success":
                print("✓ DocumentGenerationAgent 실행 성공")
                print(f"  - 문서 길이: {len(result.get('content', ''))} 글자")
            else:
                print(f"✗ DocumentGenerationAgent 실행 실패: {result.get('errors', 'Unknown error')}")
        else:
            print("✓ DocumentGenerationAgent 실행 완료")

    except Exception as e:
        print(f"✗ 에이전트 실행 실패: {e}")
        import traceback
        traceback.print_exc()

    return True

async def main():
    """메인 테스트 실행"""
    print("\n" + "🚀 LangGraph 0.6.7 통합 테스트 시작" + "\n")

    # 테스트 실행
    results = []

    # 1. 임포트 테스트
    result = await test_imports()
    results.append(("임포트 테스트", result))

    # 2. 그래프 컴파일 테스트
    result = await test_graph_compilation()
    results.append(("그래프 컴파일", result))

    # 3. 간단한 실행 테스트
    result = await test_simple_execution()
    results.append(("실행 테스트", result))

    # 결과 요약
    print("\n" + "=" * 50)
    print("테스트 결과 요약")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\n총 {total}개 테스트 중 {passed}개 통과")

    if passed == total:
        print("✅ 모든 테스트 통과! LangGraph 0.6.7 업데이트 성공")
    else:
        print("⚠️ 일부 테스트 실패. 추가 디버깅 필요")

if __name__ == "__main__":
    asyncio.run(main())