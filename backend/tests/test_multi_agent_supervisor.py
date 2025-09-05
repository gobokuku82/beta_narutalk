"""
Multi-Agent Supervisor 테스트
복합 질의 처리 및 병렬 실행을 테스트합니다.
"""

import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.langgraph.supervisor_multi_agent import (
    MultiAgentSupervisor,
    create_multi_agent_supervisor_graph,
    run_multi_agent_supervisor
)
from langchain_core.messages import HumanMessage
import logging
logger = logging.getLogger(__name__)


async def test_supervisor_initialization():
    """Supervisor 초기화 테스트"""
    print("\n=== Supervisor Initialization Test ===")
    
    try:
        supervisor = MultiAgentSupervisor()
        
        # 에이전트 확인
        assert len(supervisor.agents) > 0, "에이전트가 초기화되지 않았습니다"
        print(f"✅ 초기화된 에이전트 수: {len(supervisor.agents)}")
        print(f"✅ 사용 가능한 에이전트: {list(supervisor.agents.keys())}")
        
    except Exception as e:
        print(f"❌ Supervisor 초기화 실패: {e}")
        raise


async def test_complex_query_analysis():
    """복합 질의 분석 테스트"""
    print("\n=== Complex Query Analysis Test ===")
    
    supervisor = MultiAgentSupervisor()
    
    # 복합 질의
    query = "아스피린의 매출 데이터를 분석하고 FDA 규정을 확인한 후 보고서를 작성해줘"
    
    # 쿼리 분석
    plan = await supervisor.analyze_complex_query(query)
    
    assert "tasks" in plan, "작업 계획이 없습니다"
    assert len(plan["tasks"]) > 0, "작업이 식별되지 않았습니다"
    
    print(f"✅ 복합 질의 분석 완료")
    print(f"✅ 식별된 작업 수: {len(plan['tasks'])}")
    print(f"✅ 실행 계획: {plan.get('execution_plan', 'unknown')}")
    
    for task in plan["tasks"]:
        print(f"  - {task['agent']}: {task.get('action', 'N/A')[:50]}...")


async def test_parallel_execution():
    """병렬 실행 테스트"""
    print("\n=== Parallel Execution Test ===")
    
    supervisor = MultiAgentSupervisor()
    
    # 병렬 실행 가능한 작업들
    tasks = [
        {"agent": "info_retrieval", "action": "아스피린 정보 검색", "parallel": True},
        {"agent": "analytics", "action": "매출 데이터 분석", "parallel": True}
    ]
    
    state = {
        "messages": [HumanMessage(content="테스트")],
        "session_id": "test_parallel",
        "agent_outputs": {},
        "context": {}
    }
    
    # 병렬 실행
    start_time = asyncio.get_event_loop().time()
    result = await supervisor.execute_parallel_tasks(tasks, state)
    execution_time = asyncio.get_event_loop().time() - start_time
    
    assert "agent_outputs" in result, "에이전트 출력이 없습니다"
    assert result.get("execution_type") == "parallel", "병렬 실행이 아닙니다"
    
    print(f"✅ 병렬 실행 완료")
    print(f"✅ 실행 시간: {execution_time:.2f}초")
    print(f"✅ 처리된 에이전트: {list(result.get('agent_outputs', {}).keys())}")


async def test_sequential_execution():
    """순차 실행 테스트"""
    print("\n=== Sequential Execution Test ===")
    
    supervisor = MultiAgentSupervisor()
    
    # 순차 실행이 필요한 작업들 (이전 결과가 다음 작업에 필요)
    tasks = [
        {"agent": "info_retrieval", "action": "데이터 수집", "dependencies": []},
        {"agent": "analytics", "action": "수집된 데이터 분석", "dependencies": [0]},
        {"agent": "doc_generation", "action": "분석 결과로 보고서 작성", "dependencies": [1]}
    ]
    
    state = {
        "messages": [HumanMessage(content="테스트")],
        "session_id": "test_sequential",
        "agent_outputs": {},
        "context": {}
    }
    
    # 순차 실행
    result = await supervisor.execute_sequential_tasks(tasks, state)
    
    assert "agent_outputs" in result, "에이전트 출력이 없습니다"
    assert result.get("execution_type") == "sequential", "순차 실행이 아닙니다"
    
    print(f"✅ 순차 실행 완료")
    print(f"✅ 처리된 에이전트: {list(result.get('agent_outputs', {}).keys())}")


async def test_full_supervisor_process():
    """전체 Supervisor 프로세스 테스트"""
    print("\n=== Full Supervisor Process Test ===")
    
    # Graph 생성
    app = create_multi_agent_supervisor_graph()
    
    # 복합 질의 State
    state = {
        "messages": [HumanMessage(content="당뇨병 치료제의 시장 분석과 규정 확인을 해줘")],
        "session_id": "test_full_process",
        "agent_outputs": {},
        "context": {},
        "should_end": False
    }
    
    # Graph 실행
    result = await app.ainvoke(state)
    
    assert "messages" in result, "응답 메시지가 없습니다"
    assert len(result["messages"]) > len(state["messages"]), "새로운 메시지가 추가되지 않았습니다"
    
    print(f"✅ 전체 프로세스 실행 완료")
    
    # 메타데이터 확인
    if "metadata" in result:
        metadata = result["metadata"]
        if "execution_plan" in metadata:
            plan = metadata["execution_plan"]
            print(f"✅ 실행된 작업 수: {len(plan.get('tasks', []))}")
            print(f"✅ 실행 유형: {metadata.get('execution_type', 'unknown')}")


async def test_error_handling():
    """오류 처리 테스트"""
    print("\n=== Error Handling Test ===")
    
    supervisor = MultiAgentSupervisor()
    
    # 잘못된 작업
    tasks = [
        {"agent": "invalid_agent", "action": "테스트", "parallel": False}
    ]
    
    state = {
        "messages": [],
        "session_id": "test_error",
        "agent_outputs": {},
        "context": {}
    }
    
    # 오류가 발생해도 결과를 반환해야 함
    result = await supervisor.execute_sequential_tasks(tasks, state)
    
    # 오류가 있어도 구조는 유지되어야 함
    assert isinstance(result, dict), "오류 상황에서도 dict를 반환해야 합니다"
    
    print(f"✅ 오류 처리 성공")
    print(f"✅ 반환된 키: {list(result.keys())}")


async def test_run_multi_agent_supervisor_helper():
    """헬퍼 함수 테스트"""
    print("\n=== Helper Function Test ===")
    
    # 헬퍼 함수로 실행
    result = await run_multi_agent_supervisor(
        user_input="아스피린에 대한 간단한 정보를 알려줘",
        session_id="test_helper",
        user_id="test_user"
    )
    
    assert result["success"], f"실행 실패: {result.get('error')}"
    assert "message" in result, "응답 메시지가 없습니다"
    
    print(f"✅ 헬퍼 함수 실행 성공")
    print(f"✅ 세션 ID: {result['session_id']}")
    print(f"✅ 실행 유형: {result.get('execution_type', 'unknown')}")
    
    # agent_outputs 확인
    if "agent_outputs" in result:
        print(f"✅ 사용된 에이전트: {list(result['agent_outputs'].keys())}")


async def run_all_tests():
    """모든 테스트 실행"""
    print("=" * 60)
    print("Multi-Agent Supervisor 테스트 시작")
    print("=" * 60)
    
    test_functions = [
        test_supervisor_initialization,
        test_complex_query_analysis,
        test_parallel_execution,
        test_sequential_execution,
        test_full_supervisor_process,
        test_error_handling,
        test_run_multi_agent_supervisor_helper
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