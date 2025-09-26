"""
Test script for Text2SQL functionality
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / '.env')

# Import the tools
from backend.service.tools.text2sql_tool import Text2SQLTool, get_text2sql_tool
from backend.service.tools.sql_executor import SQLExecutor
from backend.service.tools.sql_generator import SQLGenerator

# Test queries
TEST_QUERIES = [
    "윤수아의 2024년 3월 실적 알려줘",
    "지난달 대비 이번달 실적 분석해줘",
    "윤수아와 최수아의 실적 비교해줘",
    "2024년 상반기 실적 추이 보여줘",
    "목표 대비 달성률 얼마지?",
    "작년과 올해 실적 비교해줘",
    "이번달 TOP 5 직원 누구야?",
    "최근 3개월 실적 트렌드 분석해줘"
]


async def test_text2sql_basic():
    """Test basic Text2SQL functionality"""
    print("\n" + "="*60)
    print("1. Testing Basic Text2SQL Tool")
    print("="*60)
    
    # Initialize tool
    tool = get_text2sql_tool()
    
    # Check if LLM is enabled
    print(f"LLM Enabled: {tool.use_llm}")
    
    # Test simple query
    query = "윤수아의 이번달 실적"
    print(f"\nTest Query: {query}")
    
    result = await tool.generate_sql(query)
    
    print(f"Generated SQL: {result.get('sql')}")
    print(f"Target DB: {result.get('database')}")
    print(f"Method: {result.get('method')}")
    print(f"Confidence: {result.get('confidence')}")
    print(f"Parsed: {result.get('parsed')}")
    
    return result


async def test_sql_generation():
    """Test SQL generation with various queries"""
    print("\n" + "="*60)
    print("2. Testing SQL Generation for Various Queries")
    print("="*60)
    
    generator = SQLGenerator()
    
    for i, query in enumerate(TEST_QUERIES[:3], 1):
        print(f"\n[Test {i}] {query}")
        
        # Parse query
        parsed = generator.parse_query(query)
        print(f"Parsed: {parsed}")
        
        # Generate SQL (rule-based)
        sql, explanation = generator.generate_sql(parsed)
        print(f"SQL: {sql[:100]}...")
        print(f"Explanation: {explanation}")
        
        # Validate SQL
        is_valid = generator.validate_sql(sql)
        print(f"Valid: {is_valid}")


async def test_sql_execution():
    """Test SQL execution"""
    print("\n" + "="*60)
    print("3. Testing SQL Execution")
    print("="*60)
    
    executor = SQLExecutor()
    
    # Test connection first
    print("\nTesting database connections:")
    for db_name in ["sales_performance", "sales_target", "clients"]:
        connected = executor.test_connection(db_name)
        print(f"  {db_name}: {'✅ Connected' if connected else '❌ Failed'}")
    
    # Execute simple test query
    test_sql = "SELECT `담당자`, `202411` FROM sales_performance WHERE `담당자` = '윤수아' LIMIT 5"
    print(f"\nTest SQL: {test_sql}")
    
    results, error = executor.execute_query(test_sql, "sales_performance")
    
    if error:
        print(f"❌ Error: {error}")
    else:
        print(f"✅ Success: {len(results)} rows returned")
        if results:
            print("Sample result:")
            for key, value in results[0].items():
                print(f"  {key}: {value}")


async def test_end_to_end():
    """Test end-to-end Text2SQL flow"""
    print("\n" + "="*60)
    print("4. Testing End-to-End Flow")
    print("="*60)
    
    tool = get_text2sql_tool()
    executor = SQLExecutor()
    
    test_query = "윤수아의 2024년 11월 실적"
    print(f"\nQuery: {test_query}")
    
    # Generate SQL
    print("\n1. Generating SQL...")
    sql_result = await tool.generate_sql(test_query)
    
    if not sql_result.get('sql'):
        print(f"❌ SQL generation failed: {sql_result.get('error')}")
        return
    
    sql = sql_result['sql']
    db_name = sql_result['database']
    
    print(f"   Generated SQL: {sql}")
    print(f"   Target DB: {db_name}")
    
    # Execute SQL
    print("\n2. Executing SQL...")
    results, error = executor.execute_query(sql, db_name)
    
    if error:
        print(f"❌ Execution failed: {error}")
    else:
        print(f"✅ Success: {len(results)} rows returned")
        
        # Format results
        print("\n3. Formatted Results:")
        formatted = executor.format_results(results, max_rows=5)
        print(formatted)


async def test_complex_queries():
    """Test complex queries requiring LLM"""
    print("\n" + "="*60)
    print("5. Testing Complex Queries")
    print("="*60)
    
    tool = get_text2sql_tool()
    
    complex_queries = [
        "윤수아와 최수아의 최근 3개월 실적 비교",
        "2023년 대비 2024년 성장률",
        "이번 분기 TOP 10 직원",
        "목표 달성률이 80% 이상인 직원들"
    ]
    
    for query in complex_queries:
        print(f"\nQuery: {query}")
        result = await tool.generate_sql(query)
        
        if result.get('sql'):
            print(f"✅ SQL: {result['sql'][:150]}...")
        else:
            print(f"❌ Failed: {result.get('error')}")


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("Text2SQL DIAGNOSTIC TEST SUITE")
    print("="*80)
    
    # Check environment
    print("\n[Environment Check]")
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"OpenAI API Key: {'✅ Found' if api_key else '❌ Not found'}")
    
    try:
        # Run tests
        await test_text2sql_basic()
        await test_sql_generation()
        await test_sql_execution()
        await test_end_to_end()
        
        if api_key:
            await test_complex_queries()
        else:
            print("\n⚠️ Skipping complex query tests (no API key)")
        
        print("\n" + "="*80)
        print("TEST SUITE COMPLETED")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
