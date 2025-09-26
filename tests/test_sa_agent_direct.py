"""
Sales Analytics Agent 직접 테스트 (Non-interactive)
"""

import asyncio
import sys
import os
import io
import logging
from datetime import datetime
from typing import Dict, Any

# Windows 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding='utf-8',
        errors='replace'
    )

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 경로 설정 및 환경 변수 로드
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path('.env'))

# 로깅 설정
logging.basicConfig(level=logging.WARNING)

from backend.service.agents.sales_analytics_agent import SalesAnalyticsAgent


async def test_agent():
    """Sales Analytics Agent 테스트"""

    print("=" * 60)
    print("Sales Analytics Agent Direct Test")
    print("=" * 60)

    # 에이전트 초기화
    agent = SalesAnalyticsAgent()
    print("✓ 에이전트 초기화 완료")

    # 테스트 쿼리
    query = "윤수아와 최수아의 2024년과 2023년 실적을 비교해서 성장률과 성장금액 비교"

    print(f"\n쿼리: {query}")
    print("-" * 60)

    try:
        # 쿼리 실행
        result = await agent.run(
            query=query,
            user_id="test_user",
            session_id=f"test_session_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            language="ko"
        )

        # 결과 출력
        print("\n[결과]")

        if result.get("error"):
            print(f"❌ 오류: {result['error']}")
        else:
            # Generate SQL 여부 확인
            if result.get("generated_sql"):
                print(f"\n📊 생성된 SQL:")
                sql_lines = result['generated_sql'].split('\n')
                for line in sql_lines[:5]:  # 처음 5줄만
                    print(f"  {line}")
                if len(sql_lines) > 5:
                    print(f"  ... (총 {len(sql_lines)} 줄)")

            # 포맷된 결과
            if result.get("formatted_result"):
                print(f"\n📄 응답:")
                print(result['formatted_result'])
            else:
                print("\n⚠️ 포맷된 결과 없음")

            # SQL 실행 결과
            if result.get("sql_results"):
                print(f"\n📊 데이터 ({len(result['sql_results'])}개 행):")
                for i, row in enumerate(result['sql_results'][:3]):  # 처음 3개만
                    print(f"  [{i+1}] {row}")
                if len(result['sql_results']) > 3:
                    print(f"  ... 총 {len(result['sql_results'])}개")

            # 기타 정보
            print(f"\n📍 정보:")
            print(f"  - 메소드: {result.get('method', 'N/A')}")
            print(f"  - 데이터베이스: {result.get('database', 'N/A')}")
            print(f"  - 신뢰도: {result.get('confidence', 0):.2f}")

    except Exception as e:
        print(f"\n❌ 오류 발생:")
        print(f"  {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_agent())