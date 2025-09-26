"""
Text2SQL Tool 테스트
"""

import asyncio
import sys
import os
import io

# Windows 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding='utf-8',
        errors='replace'
    )

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 환경 변수 로드
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path('.env'))

from backend.service.tools.text2sql_tool import get_text2sql_tool

async def test_text2sql_tool():
    """Text2SQL Tool 테스트"""

    print("=" * 60)
    print("Text2SQL Tool Test")
    print("=" * 60)

    # Tool 초기화
    tool = get_text2sql_tool()
    print(f"\n✓ Tool 초기화 완료")
    print(f"  - LLM 사용 가능: {tool.use_llm}")

    # 테스트 쿼리들
    test_queries = [
        "윤수아와 최수아의 2024년과 2023년 실적을 비교해서 성장률과 성장금액 비교",
        "윤수아 3월 실적",
        "전체 직원 평균 실적",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {query}")
        print("="*60)

        # SQL 생성
        result = await tool.generate_sql(
            query=query,
            context={
                "user_id": "test_user",
                "session_id": f"test_{i}",
                "language": "ko"
            }
        )

        # 결과 출력
        print(f"\n📊 결과:")
        print(f"  - Method: {result.get('method')}")
        print(f"  - Database: {result.get('database')}")
        print(f"  - Confidence: {result.get('confidence'):.2f}")
        print(f"  - Valid: {result.get('is_valid')}")

        if result.get('sql'):
            print(f"\n생성된 SQL:")
            sql_lines = result['sql'].split('\n')
            for line in sql_lines[:10]:  # 처음 10줄만
                print(f"  {line}")
            if len(sql_lines) > 10:
                print(f"  ... (총 {len(sql_lines)} 줄)")

            print(f"\n설명: {result.get('explanation')}")
        else:
            print(f"\n❌ SQL 생성 실패: {result.get('error')}")

async def test_direct_tool_call():
    """Tool 직접 호출 테스트"""

    print("\n" + "=" * 60)
    print("Direct Tool Call Test")
    print("=" * 60)

    tool = get_text2sql_tool()

    # 복잡한 쿼리 테스트
    complex_query = """
    윤수아와 최수아의 2024년 전체 실적을 2023년과 비교하고,
    성장률과 성장금액을 계산해서 보여줘
    """

    print(f"\n쿼리: {complex_query.strip()}")

    result = await tool.generate_sql(complex_query)

    if result.get('sql'):
        print(f"\n✅ SQL 생성 성공!")
        print(f"   Method: {result['method']}")
        print(f"   Database: {result['database']}")

        # SQL 실행 테스트
        from backend.service.tools.sql_executor import SQLExecutor
        executor = SQLExecutor()

        print(f"\n📊 SQL 실행 중...")
        data, error = executor.execute_query(
            sql=result['sql'],
            db_name=result['database']
        )

        if error:
            print(f"❌ 실행 오류: {error}")
        else:
            print(f"✅ 성공! {len(data)}개 행 반환")
            if data:
                print(f"\n첫 번째 결과:")
                for key, value in data[0].items():
                    if key == '담당자':
                        print(f"  {key}: {value}")
                    elif isinstance(value, (int, float)):
                        print(f"  {key}: {value:,}")
                    else:
                        print(f"  {key}: {value}")

async def main():
    """메인 함수"""

    # Tool 기본 테스트
    await test_text2sql_tool()

    # 직접 호출 테스트
    await test_direct_tool_call()

if __name__ == "__main__":
    asyncio.run(main())