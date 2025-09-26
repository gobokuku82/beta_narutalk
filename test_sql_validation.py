"""
SQL Validation 문제 테스트
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path('.env'))

from backend.service.tools.text2sql_tool import get_text2sql_tool
from backend.service.tools.sql_generator import SQLGenerator

async def test_validation():
    """SQL validation 테스트"""

    print("=" * 60)
    print("SQL Validation Test")
    print("=" * 60)

    # Tool 초기화
    tool = get_text2sql_tool()
    generator = SQLGenerator()

    # 테스트 쿼리
    query = "윤수아와 최수아의 2024년과 2023년 실적을 비교해서 성장률과 성장금액 비교"

    print(f"\n쿼리: {query}")

    # SQL 생성
    result = await tool.generate_sql(query)

    if result.get('sql'):
        sql = result['sql']
        print(f"\n생성된 SQL:")
        print(sql)

        print(f"\n검증 테스트:")
        print(f"  - 첫 50자: {repr(sql[:50])}")
        print(f"  - startswith('SELECT'): {sql.startswith('SELECT')}")
        print(f"  - upper().startswith('SELECT'): {sql.upper().startswith('SELECT')}")
        print(f"  - strip().upper().startswith('SELECT'): {sql.strip().upper().startswith('SELECT')}")

        # Validation
        is_valid = generator.validate_sql(sql)
        print(f"\n검증 결과: {is_valid}")

        if not is_valid:
            # 수정된 validation 테스트
            sql_cleaned = sql.strip()
            print(f"\n수정 후:")
            print(f"  - cleaned[:50]: {repr(sql_cleaned[:50])}")
            print(f"  - cleaned.upper().startswith('SELECT'): {sql_cleaned.upper().startswith('SELECT')}")

if __name__ == "__main__":
    asyncio.run(test_validation())