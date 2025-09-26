"""
직접 SQL 생성 테스트
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

# 로그 설정
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from backend.service.tools.sql_generator import SQLGenerator

async def test_sql_generation():
    """SQL 생성 테스트"""

    print("=" * 60)
    print("Direct SQL Generation Test with LLM")
    print("=" * 60)

    # API 키 확인
    api_key = os.getenv('OPENAI_API_KEY')
    print(f"\nAPI Key 로드: {'Yes' if api_key else 'No'}")
    if api_key:
        print(f"API Key 시작: {api_key[:20]}...")

    # SQLGenerator 초기화
    generator = SQLGenerator()
    print(f"SQLGenerator LLM 사용 가능: {generator.use_llm}")

    # 테스트 쿼리
    query = "윤수아와 최수아의 2024년과 2023년 실적을 비교해서 성장률과 성장금액 비교"

    print(f"\n쿼리: {query}")
    print("-" * 60)

    try:
        # 1. 파싱
        parsed = generator.parse_query(query)
        print(f"\n파싱 결과:")
        for key, value in parsed.items():
            print(f"  {key}: {value}")

        # 2. LLM으로 SQL 생성
        if generator.use_llm:
            print(f"\nLLM으로 SQL 생성 중...")
            sql, explanation = await generator.generate_sql_with_llm(
                query=query,
                parsed=parsed
            )

            print(f"\n생성된 SQL:")
            print(sql)
            print(f"\n설명: {explanation}")

            # 3. SQL 실행
            from backend.service.tools.sql_executor import SQLExecutor
            executor = SQLExecutor()

            print(f"\nSQL 실행 중...")
            results, error = executor.execute_query(
                sql=sql,
                db_name="sales_performance"
            )

            if error:
                print(f"실행 오류: {error}")
            else:
                print(f"성공! {len(results)}개 행 반환")
                if results:
                    # 첫 번째 결과 출력
                    first = results[0]
                    print(f"\n첫 번째 결과:")
                    for key, value in first.items():
                        print(f"  {key}: {value}")
        else:
            print("LLM을 사용할 수 없습니다!")

    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_sql_generation())