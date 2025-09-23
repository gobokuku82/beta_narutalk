"""
Test simple workflow to isolate the problem
"""

import asyncio
from langgraph.graph import StateGraph, START, END
from typing import TypedDict

class SimpleState(TypedDict):
    value: int

async def test_simple():
    workflow = StateGraph(SimpleState)

    # 간단한 노드들
    async def add_one(state):
        print(f"add_one: {state['value']} -> {state['value'] + 1}")
        state['value'] += 1
        return state

    async def multiply_two(state):
        print(f"multiply_two: {state['value']} -> {state['value'] * 2}")
        state['value'] *= 2
        return state

    # 워크플로우 구성
    workflow.add_node("add", add_one)
    workflow.add_node("multiply", multiply_two)

    workflow.add_edge(START, "add")
    workflow.add_edge("add", "multiply")
    workflow.add_edge("multiply", END)

    # 컴파일
    app = workflow.compile()

    # 실행
    initial_state = {"value": 1}
    print(f"Initial state: {initial_state}")

    try:
        result = await asyncio.wait_for(
            app.ainvoke(initial_state),
            timeout=5.0
        )
        print(f"Final state: {result}")
        return True
    except asyncio.TimeoutError:
        print("TIMEOUT - Simple workflow also hangs!")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_simple())
    print(f"\nSimple workflow test: {'PASSED' if success else 'FAILED'}")