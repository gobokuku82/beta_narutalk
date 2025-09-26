"""
SQLGenerator 직접 테스트
GPT-4o-mini를 사용한 Text2SQL 변환 확인
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

from backend.service.tools.sql_generator import SQLGenerator
from backend.service.tools.sql_executor import SQLExecutor

async def test_sql_generation():
    """SQL 생성 테스트"""

    print("=" * 60)
    print("SQLGenerator Text2SQL 테스트")
    print("=" * 60)

    # SQLGenerator 초기화
    generator = SQLGenerator()

    # LLM 사용 가능 확인
    print(f"\nLLM 사용 가능: {generator.use_llm}")
    print(f"API Key 존재: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")

    # 테스트 쿼리들
    test_queries = [
        "윤수아와 최수아의 2024년과 2023년 실적을 비교해서 성장률과 성장금액 비교",
        "윤수아 3월 실적",
        "전체 직원 평균 실적",
        "이번달 실적 TOP 3"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"테스트 {i}: {query}")
        print("="*60)

        try:
            # 1. Parse query
            parsed = generator.parse_query(query)
            print(f"\n파싱 결과:")
            print(f"  - 이름: {parsed.get('name')}")
            print(f"  - 월: {parsed.get('month')}")
            print(f"  - 년도: {parsed.get('year')}")
            print(f"  - 액션: {parsed.get('action')}")

            # 2. Generate SQL with LLM
            if generator.use_llm:
                print(f"\nLLM으로 SQL 생성 중...")
                sql, explanation = await generator.generate_sql_with_llm(
                    query=query,
                    parsed=parsed
                )
                print(f"\n생성된 SQL:")
                print(f"{sql}")
                print(f"\n설명: {explanation}")
            else:
                print("\nLLM 사용 불가 - Rule-based SQL 생성")
                sql, explanation = generator.generate_sql(parsed)
                print(f"\n생성된 SQL:")
                print(f"{sql}")
                print(f"\n설명: {explanation}")

            # 3. Execute SQL
            print(f"\nSQL 실행 중...")
            executor = SQLExecutor()
            results, error = executor.execute_query(
                sql=sql,
                db_name="sales_performance"
            )

            if error:
                print(f"실행 오류: {error}")
            else:
                print(f"결과: {len(results)}개 행 반환")
                if results and len(results) > 0:
                    print(f"첫 번째 결과: {results[0]}")

        except Exception as e:
            print(f"오류 발생: {e}")
            import traceback
            traceback.print_exc()

async def test_direct_llm_call():
    """LLM 직접 호출 테스트"""

    print("\n" + "=" * 60)
    print("LLM 직접 호출 테스트")
    print("=" * 60)

    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage

    try:
        # LLM 초기화
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            max_tokens=500
        )

        # 테스트 메시지
        messages = [
            SystemMessage(content="You are a SQL expert. Generate safe SELECT queries only."),
            HumanMessage(content="Generate SQL to compare 윤수아 and 최수아's 2023 vs 2024 sales performance")
        ]

        print("\nLLM 호출 중...")
        response = await llm.ainvoke(messages)
        print(f"\nLLM 응답:")
        print(response.content)

    except Exception as e:
        print(f"LLM 호출 실패: {e}")

async def main():
    """메인 함수"""

    # SQL Generation 테스트
    await test_sql_generation()

    # LLM 직접 호출 테스트
    await test_direct_llm_call()

if __name__ == "__main__":
    asyncio.run(main())