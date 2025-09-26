"""
LLM 응답 직접 테스트
"""

import asyncio
import sys
import os
import io
import logging

# Windows 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding='utf-8',
        errors='replace'
    )

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path('.env'))

# 로그 레벨 설정
logging.basicConfig(level=logging.WARNING)

from backend.service.tools.sql_generator import SQLGenerator

async def test_llm_response():
    """LLM 응답 테스트"""

    print("=" * 60)
    print("LLM Response Test")
    print("=" * 60)

    generator = SQLGenerator()

    if not generator.use_llm:
        print("LLM이 사용 불가능합니다.")
        return

    query = "윤수아와 최수아의 2024년과 2023년 실적을 비교해서 성장률과 성장금액 비교"
    parsed = generator.parse_query(query)

    print(f"\n쿼리: {query}")
    print(f"\n파싱: {parsed}")

    try:
        # LLM 호출
        sql, explanation = await generator.generate_sql_with_llm(query, parsed)

        print(f"\n생성된 SQL:")
        print(f"{sql}")

        print(f"\n설명: {explanation}")

        # Validation
        is_valid = generator.validate_sql(sql)
        print(f"\n검증 결과: {is_valid}")

    except Exception as e:
        print(f"\n오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_llm_response())