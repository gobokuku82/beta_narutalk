"""
자동화된 LLM 통합 테스트
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 환경 변수 로드
load_dotenv()

async def test_llm_basic():
    """기본 LLM 테스트"""
    print("\n=== LLM Basic Test ===")

    try:
        from backend.service.utils import LLMManager

        llm = LLMManager()
        print("[OK] LLM Manager initialized")

        # 간단한 테스트
        response = await llm.generate(
            prompt="Say 'Hello, World!' in Korean",
            model="openai_mini",
            category="test",
            temperature=0
        )

        if response and 'content' in response:
            print(f"[OK] Response: {response['content']}")
            print(f"[INFO] Tokens used: {response['usage']['total_tokens']}")
            return True
        else:
            print("[ERROR] No response from LLM")
            return False

    except Exception as e:
        print(f"[ERROR] {e}")
        return False

async def test_intent_classification():
    """의도 분류 테스트"""
    print("\n=== Intent Classification Test ===")

    try:
        from backend.service.orchestrator.intent_analysis import IntentAnalysisSubGraph

        analyzer = IntentAnalysisSubGraph()
        print("[OK] Intent Analyzer initialized")

        # 테스트 쿼리
        test_query = "지난 분기 서울 지역 매출 실적 분석해줘"

        state = {
            "user_query": test_query,
            "tokens": [],
            "entities": [],
            "intents": [],
            "confidence_scores": {},
            "ambiguous": False
        }

        result = await analyzer.classify_intent(state)

        if result.get("intents"):
            print(f"[OK] Intents detected: {[i['type'] for i in result['intents']]}")
            return True
        else:
            print("[ERROR] No intents detected")
            return False

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_text_to_sql():
    """Text2SQL 테스트"""
    print("\n=== Text2SQL Test ===")

    try:
        from backend.service.agents.sales_analytics_agent import SalesAnalyticsAgent

        agent = SalesAnalyticsAgent()
        print("[OK] Sales Analytics Agent initialized")

        state = {
            "query": "Show total sales for Seoul region last month",
            "sql_query": "",
            "query_results": [],
            "analysis": {},
            "visualization": {}
        }

        # SQL 생성
        state = await agent.text_to_sql(state)

        if state.get("sql_query") and "SELECT" in state["sql_query"]:
            print(f"[OK] SQL generated: {state['sql_query'][:100]}...")
            return True
        else:
            print("[ERROR] SQL generation failed")
            return False

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_token_tracking():
    """토큰 추적 테스트"""
    print("\n=== Token Tracking Test ===")

    try:
        from backend.service.utils import TokenTracker

        tracker = TokenTracker()
        print("[OK] Token Tracker initialized")

        # 테스트 데이터 추적
        tracker.track(
            model="gpt-4o",
            prompt_tokens=100,
            completion_tokens=50,
            category="test"
        )

        stats = tracker.get_current_stats()
        print(f"[OK] Tokens tracked: {stats['tokens']['total']}")
        print(f"[INFO] Estimated cost: ${stats['cost']['total_usd']:.4f}")

        return True

    except Exception as e:
        print(f"[ERROR] {e}")
        return False

async def main():
    """메인 테스트"""
    print("=" * 60)
    print("NaruTalk LLM Integration Automated Test")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # API Key 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR] OPENAI_API_KEY not found!")
        return

    print(f"[OK] API Key found: ...{api_key[-8:]}")

    # 테스트 실행
    results = []

    print("\nRunning tests...")

    # 1. 기본 LLM 테스트
    result = await test_llm_basic()
    results.append(("LLM Basic", result))

    # 2. 의도 분류 테스트
    result = await test_intent_classification()
    results.append(("Intent Classification", result))

    # 3. Text2SQL 테스트
    result = await test_text_to_sql()
    results.append(("Text2SQL", result))

    # 4. 토큰 추적 테스트
    result = await test_token_tracking()
    results.append(("Token Tracking", result))

    # 결과 요약
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    passed = 0
    failed = 0

    for name, success in results:
        if success:
            print(f"[PASS] {name}")
            passed += 1
        else:
            print(f"[FAIL] {name}")
            failed += 1

    print(f"\nTotal: {passed} passed, {failed} failed")

    if failed == 0:
        print("\n[SUCCESS] All tests passed!")
    else:
        print(f"\n[WARNING] {failed} test(s) failed")

if __name__ == "__main__":
    asyncio.run(main())