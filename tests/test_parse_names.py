"""
Test Korean name parsing with conjunctions
"""

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

from backend.service.tools.sql_generator import SQLGenerator

def test_name_parsing():
    """Test parsing of Korean names with conjunctions"""

    print("=" * 60)
    print("Korean Name Parsing Test")
    print("=" * 60)

    generator = SQLGenerator()

    test_queries = [
        "윤수아와 최수아의 2024년과 2023년 실적을 비교",
        "윤수아와 최수아 3월 실적",
        "김영희과 이철수의 평균 실적",
        "박지민, 김민수 그리고 정현우의 실적 비교",
        "윤수아 3월 실적",  # Single name test
    ]

    for query in test_queries:
        print(f"\n쿼리: {query}")
        parsed = generator.parse_query(query)

        print(f"파싱 결과:")
        if parsed.get("names"):
            print(f"  - 다중 이름: {parsed['names']}")
        elif parsed.get("name"):
            print(f"  - 단일 이름: {parsed['name']}")
        else:
            print(f"  - 이름 없음")

        if parsed.get("year"):
            print(f"  - 년도: {parsed['year']}")
        if parsed.get("years"):
            print(f"  - 다중 년도: {parsed['years']}")
        if parsed.get("month"):
            print(f"  - 월: {parsed['month']}")
        if parsed.get("action"):
            print(f"  - 액션: {parsed['action']}")

        # Generate SQL (rule-based)
        sql, explanation = generator.generate_sql(parsed)
        print(f"\n생성된 SQL:")
        print(f"  {sql[:100]}...")  # First 100 chars
        print(f"설명: {explanation}")

        print("-" * 60)

if __name__ == "__main__":
    test_name_parsing()