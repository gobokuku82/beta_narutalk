"""
Information Retrieval Agent with Tools 테스트
Tool을 사용하는 정보검색 에이전트를 테스트합니다.
"""

import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.langgraph.agents.info_retrieval_with_tools import InfoRetrievalWithTools
from app.langgraph.state import AgentState, initialize_state
from langchain_core.messages import HumanMessage
import logging
logger = logging.getLogger(__name__)


async def test_info_retrieval_basic():
    """기본 정보 검색 테스트"""
    print("\n=== InfoRetrieval Basic Test ===")
    
    # Agent 초기화
    agent = InfoRetrievalWithTools()
    
    # State 생성
    state = {
        "messages": [HumanMessage(content="아스피린에 대해 알려줘")],
        "session_id": "test_session_001",
        "agent_outputs": {},
        "context": {}
    }
    
    # Agent 실행
    result = await agent.process(state)
    
    assert "messages" in result, "응답 메시지가 없습니다"
    assert len(result["messages"]) > 0, "응답이 비어있습니다"
    
    print(f"✅ 쿼리: 아스피린에 대해 알려줘")
    print(f"✅ 응답 길이: {len(result['messages'][0].content)} 문자")
    
    # agent_outputs 확인
    if "agent_outputs" in result and "info_retrieval" in result["agent_outputs"]:
        info = result["agent_outputs"]["info_retrieval"]
        print(f"✅ 사용된 도구: {info.get('tools_used', [])}")
        print(f"✅ 도구 실행 수: {len(info.get('tool_results', []))}")


async def test_info_retrieval_with_multiple_tools():
    """여러 도구를 사용하는 정보 검색 테스트"""
    print("\n=== InfoRetrieval Multiple Tools Test ===")
    
    # Agent 초기화
    agent = InfoRetrievalWithTools()
    
    # 복잡한 쿼리
    state = {
        "messages": [HumanMessage(content="당뇨병 치료제의 최신 연구 동향과 시장 규모를 알려줘")],
        "session_id": "test_session_002",
        "agent_outputs": {},
        "context": {}
    }
    
    # Agent 실행
    result = await agent.process(state)
    
    assert "messages" in result, "응답 메시지가 없습니다"
    
    # 결과 분석
    if "agent_outputs" in result and "info_retrieval" in result["agent_outputs"]:
        info = result["agent_outputs"]["info_retrieval"]
        tools_used = info.get("tools_used", [])
        
        print(f"✅ 복합 쿼리 처리 완료")
        print(f"✅ 사용된 도구: {tools_used}")
        
        # 여러 도구가 사용되었는지 확인
        if len(tools_used) > 1:
            print(f"✅ 멀티 도구 실행 성공 ({len(tools_used)}개)")
        else:
            print(f"⚠️ 단일 도구만 사용됨")


async def test_info_retrieval_error_handling():
    """오류 처리 테스트"""
    print("\n=== InfoRetrieval Error Handling Test ===")
    
    # Agent 초기화
    agent = InfoRetrievalWithTools()
    
    # 빈 메시지로 테스트
    state = {
        "messages": [],
        "session_id": "test_session_003",
        "agent_outputs": {},
        "context": {}
    }
    
    try:
        result = await agent.process(state)
        
        # 에러가 있어도 결과를 반환해야 함
        assert "messages" in result, "에러 상황에서도 메시지를 반환해야 합니다"
        
        if "error" in str(result.get("agent_outputs", {})):
            print(f"✅ 오류 처리 성공")
        else:
            print(f"✅ 빈 쿼리 처리 성공")
            
    except Exception as e:
        print(f"❌ 예외 처리 실패: {e}")
        raise


async def test_tool_execution_modes():
    """도구 실행 모드 테스트 (직접 실행 vs Agent 실행)"""
    print("\n=== Tool Execution Modes Test ===")
    
    agent = InfoRetrievalWithTools()
    
    # 간단한 쿼리 (직접 실행 예상)
    simple_query = {
        "messages": [HumanMessage(content="아스피린 검색")],
        "session_id": "test_session_004",
        "agent_outputs": {},
        "context": {}
    }
    
    result = await agent.process(simple_query)
    
    if "agent_outputs" in result and "info_retrieval" in result["agent_outputs"]:
        info = result["agent_outputs"]["info_retrieval"]
        context = info.get("context", {})
        
        if context.get("agent_execution") == "completed":
            print(f"✅ Agent 실행 모드 사용")
        else:
            print(f"✅ 직접 도구 실행 모드 사용")
    
    # 복잡한 쿼리 (Agent 실행 예상)
    complex_query = {
        "messages": [HumanMessage(content="아스피린의 역사, 효능, 부작용, 그리고 최신 연구 동향을 모두 알려줘")],
        "session_id": "test_session_005", 
        "agent_outputs": {},
        "context": {}
    }
    
    result = await agent.process(complex_query)
    
    if "agent_outputs" in result and "info_retrieval" in result["agent_outputs"]:
        info = result["agent_outputs"]["info_retrieval"]
        context = info.get("context", {})
        
        if context.get("agent_execution") == "completed":
            print(f"✅ 복잡한 쿼리에 Agent 실행 모드 사용")
        else:
            print(f"✅ 복잡한 쿼리에도 직접 실행 모드 사용")


async def test_graph_compilation():
    """Subgraph 컴파일 테스트"""
    print("\n=== Graph Compilation Test ===")
    
    try:
        # Agent 생성 (graph 컴파일 포함)
        agent = InfoRetrievalWithTools()
        
        # graph가 정상적으로 생성되었는지 확인
        assert agent.graph is not None, "Graph가 생성되지 않았습니다"
        
        # 노드 확인 (LangGraph 내부 구조)
        print(f"✅ Subgraph 컴파일 성공")
        print(f"✅ Agent 초기화 완료")
        
    except Exception as e:
        print(f"❌ Graph 컴파일 실패: {e}")
        raise


async def run_all_tests():
    """모든 테스트 실행"""
    print("=" * 60)
    print("Information Retrieval with Tools 테스트 시작")
    print("=" * 60)
    
    test_functions = [
        test_graph_compilation,
        test_info_retrieval_basic,
        test_info_retrieval_with_multiple_tools,
        test_tool_execution_modes,
        test_info_retrieval_error_handling
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"❌ {test_func.__name__} 실패: {str(e)}")
            logger.error(f"Test failed: {test_func.__name__}", exc_info=True)
    
    print("\n" + "=" * 60)
    print(f"테스트 완료: 성공 {passed}/{len(test_functions)}, 실패 {failed}/{len(test_functions)}")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)