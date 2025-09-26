"""
최종 SQL Generation 테스트
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

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 환경 변수 로드
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path('.env'))

# 로그 설정 - INFO 레벨만
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from backend.service.tools.sql_generator import SQLGenerator
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

async def test_direct_llm():
    """LLM 직접 호출로 SQL 생성"""

    print("=" * 60)
    print("Direct LLM SQL Generation")
    print("=" * 60)

    # LLM 초기화
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1
    )

    # 직접 프롬프트
    prompt = """
Generate a SQLite query for the following request:
"윤수아와 최수아의 2024년과 2023년 실적을 비교해서 성장률과 성장금액 비교"

Database schema:
- Table: sales_performance
- Columns:
  - 담당자 (TEXT) - employee name
  - "202301", "202302", ..., "202312" (INTEGER) - 2023 monthly sales columns
  - "202401", "202402", ..., "202411" (INTEGER) - 2024 monthly sales columns

Requirements:
1. Sum all 2023 columns (202301 to 202312) for total 2023 sales
2. Sum all 2024 columns (202401 to 202411) for total 2024 sales
3. Calculate growth amount (2024 total - 2023 total)
4. Calculate growth rate percentage
5. Filter for employees: '윤수아' and '최수아'

Example for summing year totals:
SUM(`202301` + `202302` + `202303` + ... + `202312`) as total_2023

Return ONLY the SQL query, no markdown, no explanations.
"""

    messages = [
        SystemMessage(content="You are a SQL expert. Generate safe SELECT queries only."),
        HumanMessage(content=prompt)
    ]

    print("\n호출 중...")
    response = await llm.ainvoke(messages)
    sql = response.content.strip()

    # 마크다운 코드 블록 제거
    if "```sql" in sql.lower():
        sql = sql.split("```sql")[1].split("```")[0].strip()
    elif "```" in sql:
        sql = sql.split("```")[1].split("```")[0].strip()

    print("\nLLM이 생성한 SQL:")
    print(sql)

    # SQL 실행
    from backend.service.tools.sql_executor import SQLExecutor
    executor = SQLExecutor()

    print("\nSQL 실행 중...")
    results, error = executor.execute_query(
        sql=sql,
        db_name="sales_performance"
    )

    if error:
        print(f"실행 오류: {error}")
    else:
        print(f"성공! {len(results)}개 행 반환")
        for i, row in enumerate(results):
            print(f"\n{row['담당자']}:")
            val_2023 = row.get('total_2023', 0)
            val_2024 = row.get('total_2024', 0)
            growth = row.get('growth_amount', 0)
            rate = row.get('growth_rate', 0)
            print(f"  2023년: {val_2023:,}원")
            print(f"  2024년: {val_2024:,}원")
            print(f"  성장금액: {growth:,}원")
            print(f"  성장률: {rate:.1f}%")

if __name__ == "__main__":
    asyncio.run(test_direct_llm())