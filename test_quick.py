"""
Quick test to verify system is working
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.WARNING)  # Less verbose

async def test():
    from backend.service.orchestrator.orchestrator import MainOrchestrator

    orchestrator = MainOrchestrator()
    # 컴파일
    app = orchestrator.workflow.compile()

    state = {
        "user_id": "test",
        "session_id": "test",
        "user_query": "최시우 실적 분석",
        "timestamp": "2024-01-01"
    }

    print("Starting test...")
    try:
        result = await asyncio.wait_for(
            app.ainvoke(state, config={"recursion_limit": 50}),
            timeout=20.0
        )
        print("SUCCESS!")
        print(f"Response: {result.get('final_response', 'No response')[:100]}")
        return True
    except asyncio.TimeoutError:
        print("TIMEOUT after 20s")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test())
    print(f"Test {'passed' if success else 'failed'}")