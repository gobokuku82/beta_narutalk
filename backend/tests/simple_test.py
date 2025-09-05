"""
간단한 통합 테스트
Tool 시스템이 정상 작동하는지 확인합니다.
"""

import asyncio
import sys
from pathlib import Path

# 부모 디렉토리를 path에 추가
sys.path.append(str(Path(__file__).parent.parent))

# 기본 로깅 설정
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_basic_imports():
    """기본 import 테스트"""
    print("\n=== 기본 Import 테스트 ===")
    
    try:
        # Tool imports
        from app.tools.base import BaseTool, ToolResult, ToolRegistry
        print("✅ Base tools imported")
        
        from app.tools.database_tools import DrugSearchTool, CustomerSearchTool
        print("✅ Database tools imported")
        
        from app.tools.search_tools import WebSearchTool
        print("✅ Search tools imported")
        
        from app.tools.document_tools import DocumentGeneratorTool, ReportBuilderTool
        print("✅ Document tools imported")
        
        from app.tools.compliance_tools import ComplianceCheckTool, RiskAssessmentTool
        print("✅ Compliance tools imported")
        
        from app.tools.analysis_tools import DataAnalysisTool, TrendAnalysisTool
        print("✅ Analysis tools imported")
        
        return True
    except ImportError as e:
        print(f"❌ Import 실패: {e}")
        return False


async def test_tool_execution():
    """도구 실행 테스트"""
    print("\n=== Tool 실행 테스트 ===")
    
    try:
        from app.tools.database_tools import DrugSearchTool
        
        # 도구 생성
        tool = DrugSearchTool()
        print(f"✅ DrugSearchTool 생성 완료")
        
        # 도구 실행
        result = await tool._arun(keyword="아스피린")
        
        if result.success:
            print(f"✅ Tool 실행 성공")
            print(f"  - 검색 결과: {result.data.get('count', 0)}개")
            print(f"  - 실행 시간: {result.execution_time:.3f}초")
        else:
            print(f"❌ Tool 실행 실패: {result.error}")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Tool 실행 중 오류: {e}")
        return False


async def test_agent_initialization():
    """Agent 초기화 테스트"""
    print("\n=== Agent 초기화 테스트 ===")
    
    try:
        from app.langgraph.agents.info_retrieval_with_tools import InfoRetrievalWithTools
        
        # Agent 생성
        agent = InfoRetrievalWithTools()
        print(f"✅ InfoRetrievalWithTools 생성 완료")
        
        # Tools 확인
        if hasattr(agent, 'tools'):
            print(f"✅ Agent에 {len(agent.tools)}개의 도구 등록됨")
            for tool in agent.tools:
                print(f"  - {tool.name}")
        
        # Graph 확인
        if hasattr(agent, 'graph'):
            print(f"✅ Agent Subgraph 컴파일 완료")
        
        return True
    except Exception as e:
        print(f"❌ Agent 초기화 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_simple_query():
    """Agent 간단한 쿼리 테스트"""
    print("\n=== Agent 쿼리 처리 테스트 ===")
    
    try:
        from app.langgraph.agents.info_retrieval_with_tools import InfoRetrievalWithTools
        from langchain_core.messages import HumanMessage
        
        # Agent 생성
        agent = InfoRetrievalWithTools()
        
        # 테스트 State
        state = {
            "messages": [HumanMessage(content="아스피린에 대해 알려줘")],
            "session_id": "test_001",
            "agent_outputs": {},
            "context": {}
        }
        
        print(f"Query: 아스피린에 대해 알려줘")
        
        # Agent 실행
        result = await agent.process(state)
        
        if "messages" in result and len(result["messages"]) > 0:
            print(f"✅ Agent 응답 생성 성공")
            response_content = result["messages"][0].content
            print(f"  - 응답 길이: {len(response_content)} 문자")
            
            # agent_outputs 확인
            if "agent_outputs" in result:
                outputs = result["agent_outputs"]
                if "info_retrieval" in outputs:
                    info = outputs["info_retrieval"]
                    print(f"  - 사용된 도구: {info.get('tools_used', [])}")
        else:
            print(f"❌ Agent 응답이 없습니다")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Agent 쿼리 처리 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multi_agent_supervisor():
    """Multi-Agent Supervisor 테스트"""
    print("\n=== Multi-Agent Supervisor 테스트 ===")
    
    try:
        from app.langgraph.supervisor_multi_agent import MultiAgentSupervisor
        
        # Supervisor 생성
        supervisor = MultiAgentSupervisor()
        print(f"✅ MultiAgentSupervisor 생성 완료")
        
        # 등록된 에이전트 확인
        if hasattr(supervisor, 'agents'):
            print(f"✅ {len(supervisor.agents)}개의 에이전트 등록됨")
            for agent_name in supervisor.agents.keys():
                print(f"  - {agent_name}")
        
        # 복합 쿼리 분석 테스트
        query = "아스피린의 매출을 분석하고 보고서를 작성해줘"
        plan = await supervisor.analyze_complex_query(query)
        
        if "tasks" in plan:
            print(f"✅ 복합 쿼리 분석 성공")
            print(f"  - 식별된 작업: {len(plan['tasks'])}개")
            print(f"  - 실행 계획: {plan.get('execution_plan', 'unknown')}")
            
            for task in plan["tasks"]:
                print(f"    • {task.get('agent', 'unknown')}: {task.get('action', 'N/A')[:30]}...")
        
        return True
    except Exception as e:
        print(f"❌ Supervisor 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """메인 테스트 실행"""
    print("="*60)
    print("Tool Integration Simple Test")
    print("="*60)
    
    tests = [
        ("기본 Import", test_basic_imports),
        ("Tool 실행", test_tool_execution),
        ("Agent 초기화", test_agent_initialization),
        ("Agent 쿼리 처리", test_agent_simple_query),
        ("Multi-Agent Supervisor", test_multi_agent_supervisor)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"테스트: {test_name}")
        print(f"{'='*60}")
        
        try:
            success = await test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ 테스트 실행 중 예외 발생: {e}")
            results.append((test_name, False))
    
    # 결과 요약
    print(f"\n{'='*60}")
    print("Test Result Summary")
    print(f"{'='*60}")
    
    passed = 0
    failed = 0
    
    for test_name, success in results:
        if success:
            print(f"✅ {test_name}: PASS")
            passed += 1
        else:
            print(f"❌ {test_name}: FAIL")
            failed += 1
    
    print(f"\n총 {len(tests)}개 테스트 중:")
    print(f"  - 성공: {passed}개")
    print(f"  - 실패: {failed}개")
    print(f"  - 성공률: {(passed/len(tests)*100):.1f}%")
    
    print(f"\n{'='*60}")
    if failed == 0:
        print("SUCCESS: All tests passed!")
    else:
        print(f"WARNING: {failed} tests failed")
    print(f"{'='*60}")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)