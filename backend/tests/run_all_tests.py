"""
모든 테스트 실행 스크립트
Tool 통합 시스템의 전체 테스트를 실행합니다.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Tuple, List

# 부모 디렉토리를 path에 추가
sys.path.append(str(Path(__file__).parent.parent))

# 환경 변수 설정 (테스트용)
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "test-key")
os.environ["OPENAI_MODEL"] = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")

import logging
logger = logging.getLogger(__name__)

# 로그 설정
logger.remove()  # 기본 핸들러 제거
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO"
)
logger.add(
    "test_results.log",
    format="{time} | {level} | {message}",
    level="DEBUG"
)


async def run_test_module(module_name: str) -> Tuple[bool, str]:
    """개별 테스트 모듈 실행"""
    try:
        if module_name == "test_tools_base":
            from test_tools_base import run_all_tests
        elif module_name == "test_info_retrieval_with_tools":
            from test_info_retrieval_with_tools import run_all_tests
        elif module_name == "test_multi_agent_supervisor":
            from test_multi_agent_supervisor import run_all_tests
        else:
            return False, f"Unknown module: {module_name}"
        
        print(f"\n{'='*60}")
        print(f"Running {module_name}...")
        print(f"{'='*60}")
        
        success = await run_all_tests()
        return success, "Success" if success else "Failed"
        
    except ImportError as e:
        return False, f"Import error: {e}"
    except Exception as e:
        logger.error(f"Test module {module_name} failed: {e}", exc_info=True)
        return False, str(e)


async def run_quick_smoke_test():
    """빠른 연기 테스트 (기본 기능만 확인)"""
    print("\n" + "="*60)
    print("Quick Smoke Test - 기본 기능 확인")
    print("="*60)
    
    results = []
    
    # 1. Tool 시스템 기본 확인
    try:
        from app.tools.base import ToolRegistry
        from app.tools.database_tools import DrugSearchTool
        
        registry = ToolRegistry()
        tool = DrugSearchTool()
        registry.register(tool, "database")
        
        print("✅ Tool 시스템 초기화 성공")
        results.append(("Tool System", True))
    except Exception as e:
        print(f"❌ Tool 시스템 초기화 실패: {e}")
        results.append(("Tool System", False))
    
    # 2. Agent 시스템 확인
    try:
        from app.langgraph.agents.info_retrieval_with_tools import InfoRetrievalWithTools
        
        agent = InfoRetrievalWithTools()
        print("✅ Agent 시스템 초기화 성공")
        results.append(("Agent System", True))
    except Exception as e:
        print(f"❌ Agent 시스템 초기화 실패: {e}")
        results.append(("Agent System", False))
    
    # 3. Supervisor 시스템 확인
    try:
        from app.langgraph.supervisor_multi_agent import MultiAgentSupervisor
        
        supervisor = MultiAgentSupervisor()
        print("✅ Supervisor 시스템 초기화 성공")
        results.append(("Supervisor System", True))
    except Exception as e:
        print(f"❌ Supervisor 시스템 초기화 실패: {e}")
        results.append(("Supervisor System", False))
    
    # 4. 간단한 도구 실행 테스트
    try:
        from app.tools.database_tools import DrugSearchTool
        
        tool = DrugSearchTool()
        result = await tool._arun(keyword="test")
        
        if result.success:
            print("✅ Tool 실행 성공")
            results.append(("Tool Execution", True))
        else:
            print(f"⚠️ Tool 실행은 되었지만 실패: {result.error}")
            results.append(("Tool Execution", False))
    except Exception as e:
        print(f"❌ Tool 실행 실패: {e}")
        results.append(("Tool Execution", False))
    
    # 결과 요약
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n{'='*60}")
    print(f"Smoke Test 결과: {passed}/{total} 성공")
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {name}")
    print(f"{'='*60}")
    
    return passed == total


async def main():
    """메인 테스트 실행"""
    print("="*60)
    print("🚀 Tool Integration System 테스트 시작")
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 연기 테스트 먼저 실행
    smoke_test_passed = await run_quick_smoke_test()
    
    if not smoke_test_passed:
        print("\n⚠️ Smoke 테스트 실패. 상세 테스트를 계속하시겠습니까? (y/n): ", end="")
        # 자동으로 계속 진행 (CI/CD 환경을 위해)
        continue_test = "y"  # input().lower() == "y"
        if continue_test != "y":
            print("테스트를 중단합니다.")
            return 1
    
    # 전체 테스트 모듈 실행
    test_modules = [
        "test_tools_base",
        "test_info_retrieval_with_tools", 
        "test_multi_agent_supervisor"
    ]
    
    results: List[Tuple[str, bool, str]] = []
    
    for module in test_modules:
        success, message = await run_test_module(module)
        results.append((module, success, message))
    
    # 최종 결과 요약
    print("\n" + "="*60)
    print("📊 최종 테스트 결과")
    print("="*60)
    
    passed_count = 0
    failed_count = 0
    
    for module, success, message in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {module}: {message}")
        if success:
            passed_count += 1
        else:
            failed_count += 1
    
    print(f"\n총 테스트: {len(results)}개")
    print(f"성공: {passed_count}개")
    print(f"실패: {failed_count}개")
    print(f"성공률: {(passed_count/len(results)*100):.1f}%")
    
    print(f"\n종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 모든 테스트가 성공했으면 0, 아니면 1 반환
    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)