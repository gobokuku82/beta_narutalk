"""
Integration Test for Tool System
Tests the tool integration with agents
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))


async def test_imports():
    """Test basic imports"""
    print("\n=== Import Test ===")
    
    try:
        from app.tools.base import BaseTool, ToolResult
        print("OK: Base tools imported")
        
        from app.tools.database_tools import DrugSearchTool
        print("OK: Database tools imported")
        
        from app.langgraph.agents.info_retrieval_with_tools import InfoRetrievalWithTools
        print("OK: Info retrieval agent imported")
        
        from app.langgraph.supervisor_multi_agent import MultiAgentSupervisor
        print("OK: Multi-agent supervisor imported")
        
        return True
    except ImportError as e:
        print(f"ERROR: Import failed - {e}")
        return False


async def test_tool_execution():
    """Test tool execution"""
    print("\n=== Tool Execution Test ===")
    
    try:
        from app.tools.database_tools import DrugSearchTool
        
        tool = DrugSearchTool()
        print("OK: Tool created")
        
        result = await tool._arun(keyword="aspirin")
        
        if result.success:
            print("OK: Tool executed successfully")
            print(f"  Results: {result.data.get('count', 0)}")
            return True
        else:
            print(f"ERROR: Tool failed - {result.error}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False


async def test_agent():
    """Test agent with tools"""
    print("\n=== Agent Test ===")
    
    try:
        from app.langgraph.agents.info_retrieval_with_tools import InfoRetrievalWithTools
        from langchain_core.messages import HumanMessage
        
        agent = InfoRetrievalWithTools()
        print("OK: Agent created")
        
        state = {
            "messages": [HumanMessage(content="Tell me about aspirin")],
            "session_id": "test",
            "agent_outputs": {},
            "context": {}
        }
        
        result = await agent.process(state)
        
        if "messages" in result and result["messages"]:
            print("OK: Agent processed query")
            return True
        else:
            print("ERROR: No response from agent")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_supervisor():
    """Test multi-agent supervisor"""
    print("\n=== Supervisor Test ===")
    
    try:
        from app.langgraph.supervisor_multi_agent import MultiAgentSupervisor
        
        supervisor = MultiAgentSupervisor()
        print("OK: Supervisor created")
        
        if supervisor.agents:
            print(f"OK: {len(supervisor.agents)} agents registered")
        
        query = "Analyze drug sales and create report"
        plan = await supervisor.analyze_complex_query(query)
        
        if "tasks" in plan:
            print(f"OK: Query analyzed - {len(plan['tasks'])} tasks")
            return True
        else:
            print("ERROR: No tasks identified")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("="*50)
    print("TOOL INTEGRATION TEST")
    print("="*50)
    
    tests = [
        ("Imports", test_imports),
        ("Tool Execution", test_tool_execution),
        ("Agent Processing", test_agent),
        ("Multi-Agent Supervisor", test_supervisor)
    ]
    
    results = []
    
    for name, test_func in tests:
        print(f"\nRunning: {name}")
        print("-"*30)
        try:
            success = await test_func()
            results.append((name, success))
        except Exception as e:
            print(f"EXCEPTION: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    
    for name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"  [{status}] {name}")
    
    print(f"\nResults: {passed}/{total} passed")
    print(f"Success Rate: {passed/total*100:.0f}%")
    
    if passed == total:
        print("\nSUCCESS: All tests passed!")
    else:
        print(f"\nFAILURE: {total-passed} tests failed")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)