"""
Test LangGraph 0.6.7 Runtime patterns
Verify how context is passed and accessed in nodes
"""

import asyncio
import os
import sys
from typing import Dict, Any
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set dummy API key for testing
os.environ['OPENAI_API_KEY'] = 'test-key-123'

async def test_runtime_patterns():
    """Test different context passing methods"""

    try:
        from langgraph.runtime import Runtime
        from langgraph.graph import StateGraph, START, END
        from backend.service.core import (
            SalesState,
            AgentContext,
            create_agent_context,
            create_sales_initial_state
        )

        print("Imports successful")

        # Create a test node that logs runtime details
        async def test_node(state: SalesState, runtime: Runtime[AgentContext]) -> Dict[str, Any]:
            """Test node to inspect runtime"""
            logger.info("=== Node Called ===")
            logger.info(f"State type: {type(state)}")
            logger.info(f"Runtime type: {type(runtime)}")

            # Try to access runtime.context
            try:
                if hasattr(runtime, 'context'):
                    logger.info(f"Runtime has context attribute")
                    context = runtime.context
                    logger.info(f"Context type: {type(context)}")

                    # Try to access context fields
                    if hasattr(context, 'get'):
                        user_id = context.get("user_id", "NOT_FOUND")
                        logger.info(f"Context.get('user_id'): {user_id}")

                    if hasattr(context, '__getitem__'):
                        try:
                            user_id = context["user_id"]
                            logger.info(f"Context['user_id']: {user_id}")
                        except (KeyError, TypeError) as e:
                            logger.error(f"Cannot access context['user_id']: {e}")

                    # Log all context attributes
                    if hasattr(context, '__dict__'):
                        logger.info(f"Context attributes: {context.__dict__}")
                    elif isinstance(context, dict):
                        logger.info(f"Context dict keys: {list(context.keys())[:5]}")
                else:
                    logger.warning("Runtime has no context attribute")
                    logger.info(f"Runtime attributes: {dir(runtime)[:10]}")
            except Exception as e:
                logger.error(f"Error accessing runtime.context: {e}")

            return {"status": "completed", "test_result": "node_executed"}

        # Build test graph
        workflow = StateGraph(
            state_schema=SalesState,
            context_schema=AgentContext
        )
        workflow.add_node("test", test_node)
        workflow.add_edge(START, "test")
        workflow.add_edge("test", END)

        app = workflow.compile()
        logger.info("Graph compiled")

        # Create test context and state
        context = create_agent_context(
            user_id="test_user_123",
            session_id="test_session_456",
            language="ko",
            original_query="Test query"
        )
        logger.info(f"Context created with user_id: {context['user_id']}")

        initial_state = create_sales_initial_state(query="Test sales query")
        logger.info(f"Initial state created")

        # Method 1: Context in configurable
        print("\n=== Method 1: config['configurable']['context'] ===")
        try:
            result1 = await app.ainvoke(
                initial_state,
                config={
                    "configurable": {
                        "thread_id": "test_thread_1",
                        "context": context
                    }
                }
            )
            logger.info(f"Method 1 result: {result1.get('test_result')}")
        except Exception as e:
            logger.error(f"Method 1 failed: {e}")

        # Method 2: Context in config root
        print("\n=== Method 2: config['context'] ===")
        try:
            result2 = await app.ainvoke(
                initial_state,
                config={
                    "configurable": {"thread_id": "test_thread_2"},
                    "context": context
                }
            )
            logger.info(f"Method 2 result: {result2.get('test_result')}")
        except Exception as e:
            logger.error(f"Method 2 failed: {e}")

        # Method 3: Context as separate parameter (current implementation)
        print("\n=== Method 3: separate context parameter ===")
        try:
            result3 = await app.ainvoke(
                initial_state,
                config={"configurable": {"thread_id": "test_thread_3"}},
                context=context  # Separate parameter
            )
            logger.info(f"Method 3 result: {result3.get('test_result')}")
        except Exception as e:
            logger.error(f"Method 3 failed: {e}")

        print("\nAll tests completed. Check logs above to see which method works.")

    except ImportError as e:
        logger.error(f"Import error: {e}")
        print("Failed to import required modules")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()


async def test_simple_node():
    """Test with simple node that doesn't use Runtime type hint"""

    try:
        from langgraph.graph import StateGraph, START, END
        from backend.service.core import SalesState, create_sales_initial_state

        # Simple node without Runtime
        async def simple_node(state: SalesState, config: Dict[str, Any]) -> Dict[str, Any]:
            """Simple node with config parameter"""
            logger.info("=== Simple Node Called ===")
            logger.info(f"Config keys: {list(config.keys())}")

            # Check configurable
            if "configurable" in config:
                configurable = config["configurable"]
                logger.info(f"Configurable keys: {list(configurable.keys())}")

                if "context" in configurable:
                    context = configurable["context"]
                    logger.info(f"Found context in configurable!")
                    logger.info(f"Context user_id: {context.get('user_id')}")

            return {"status": "completed"}

        # Build and run
        workflow = StateGraph(state_schema=SalesState)
        workflow.add_node("simple", simple_node)
        workflow.add_edge(START, "simple")
        workflow.add_edge("simple", END)

        app = workflow.compile()

        result = await app.ainvoke(
            create_sales_initial_state(query="Test"),
            config={
                "configurable": {
                    "thread_id": "test",
                    "context": {"user_id": "simple_test_user"}
                }
            }
        )

        logger.info(f"Simple test result: {result.get('status')}")

    except Exception as e:
        logger.error(f"Simple test failed: {e}")


if __name__ == "__main__":
    print("Starting Runtime pattern tests...\n")
    asyncio.run(test_runtime_patterns())

    print("\n" + "="*50)
    print("Testing simple node without Runtime...\n")
    asyncio.run(test_simple_node())