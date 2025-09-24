"""
Text2SQL 고도화 테스트 스크립트
LLM 기반 SQL 생성 및 실행 테스트
"""

import asyncio
import logging
from backend.service.tools import SQLGenerator, SQLExecutor, SchemaContext

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_llm_sql_generation():
    """LLM 기반 SQL 생성 테스트"""
    print("\n" + "="*70)
    print(" Text2SQL LLM 기반 생성 테스트 ".center(70))
    print("="*70)

    # Initialize components
    sql_generator = SQLGenerator()
    sql_executor = SQLExecutor()
    schema_context = SchemaContext()

    # Test queries
    test_queries = [
        "김철수의 3월 실적 보여줘",
        "작년 대비 올해 성장률이 높은 직원 10명",
        "2024년 상반기 팀별 실적 순위",
        "지난 3개월 매출 추이 분석해줘",
        "이번달 실적 상위 5명과 하위 5명 비교",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n[테스트 {i}] {query}")
        print("-" * 50)

        try:
            # 1. Parse query
            parsed = sql_generator.parse_query(query)
            print(f"📝 파싱 결과: {parsed}")

            # 2. Generate SQL using LLM
            if sql_generator.use_llm:
                sql, explanation = await sql_generator.generate_sql_with_llm(query, parsed)
                print(f"🤖 LLM SQL 생성: {explanation}")
            else:
                sql, explanation = sql_generator.generate_sql(parsed)
                print(f"📋 규칙 기반 SQL: {explanation}")

            print(f"💾 생성된 SQL:\n{sql}")

            # 3. Validate SQL
            if sql_generator.validate_sql(sql):
                print("✅ SQL 검증 통과")

                # 4. Execute SQL
                results, error = sql_executor.execute_query(sql)

                if error:
                    print(f"❌ 실행 오류: {error}")
                else:
                    # 5. Format and display results
                    formatted = sql_executor.format_results(results, max_rows=5)
                    print(f"\n📊 실행 결과:\n{formatted}")
            else:
                print("⚠️ SQL 검증 실패 - 안전하지 않은 쿼리")

        except Exception as e:
            print(f"❌ 오류 발생: {e}")

        input("\nEnter를 눌러 다음 테스트 진행...")


async def test_advanced_sql_features():
    """고급 SQL 기능 테스트"""
    print("\n" + "="*70)
    print(" 고급 SQL 기능 테스트 ".center(70))
    print("="*70)

    sql_generator = SQLGenerator()
    sql_executor = SQLExecutor()

    # Test advanced features
    advanced_tests = [
        {
            "name": "시계열 분석",
            "query": "최근 6개월 매출 추이",
            "type": "trend",
            "entities": {"start_month": "202406", "end_month": "202411"}
        },
        {
            "name": "YoY 비교",
            "query": "작년 대비 올해 성장률",
            "type": "comparison",
            "entities": {"comparison_type": "yoy", "current_period": "202403"}
        },
        {
            "name": "순위 분석",
            "query": "11월 실적 TOP 10",
            "type": "ranking",
            "entities": {"month": "202411", "category": "individual"}
        },
        {
            "name": "팀별 집계",
            "query": "팀별 평균 실적",
            "type": "aggregation",
            "entities": {"month": "202411", "group_by": ["팀명칭"]}
        }
    ]

    for test in advanced_tests:
        print(f"\n[{test['name']}] {test['query']}")
        print("-" * 50)

        try:
            # Generate advanced SQL
            sql, explanation = await sql_generator.generate_advanced_sql(
                test['query'],
                test['type'],
                test['entities']
            )

            print(f"📋 {explanation}")
            print(f"💾 SQL:\n{sql}")

            # Execute
            results, error = sql_executor.execute_query(sql)

            if error:
                print(f"❌ 실행 오류: {error}")
            else:
                formatted = sql_executor.format_results(results, max_rows=5)
                print(f"\n📊 결과:\n{formatted}")

        except Exception as e:
            print(f"❌ 오류: {e}")

        input("\nEnter를 눌러 계속...")


async def test_schema_context():
    """스키마 컨텍스트 테스트"""
    print("\n" + "="*70)
    print(" 스키마 컨텍스트 테스트 ".center(70))
    print("="*70)

    schema_context = SchemaContext()

    # Test schema context generation
    print("\n📚 LLM용 스키마 컨텍스트:")
    print("-" * 50)
    context = schema_context.get_llm_context()
    print(context[:1000] + "...\n")  # Show first 1000 chars

    # Test column validation
    print("📋 컬럼 검증 테스트:")
    test_months = ["202403", "202413", "202411"]
    for month in test_months:
        valid = schema_context.validate_month_column(month)
        print(f"  • {month}: {'✅ 유효' if valid else '❌ 무효'}")

    # Test join hints
    print("\n🔗 JOIN 힌트 생성:")
    hints = schema_context.get_join_hints(["sales_performance", "인사자료"])
    for hint in hints:
        print(f"  • {hint['tables'][0]} ↔ {hint['tables'][1]}")
        print(f"    조건: {hint['condition']}")

    # Test example queries
    print("\n💡 예시 쿼리:")
    examples = schema_context.get_example_queries()
    for i, example in enumerate(examples[:3], 1):
        print(f"  {i}. {example['description']}")
        print(f"     SQL: {example['sql'][:100]}...")


async def interactive_test():
    """대화형 테스트"""
    print("\n" + "="*70)
    print(" Text2SQL 대화형 테스트 ".center(70))
    print("="*70)
    print("종료하려면 'exit' 입력\n")

    sql_generator = SQLGenerator()
    sql_executor = SQLExecutor()

    while True:
        query = input("\n💬 SQL 쿼리 요청: ").strip()

        if query.lower() in ['exit', 'quit', '종료']:
            break

        if not query:
            continue

        try:
            # Parse and generate SQL
            parsed = sql_generator.parse_query(query)

            if sql_generator.use_llm:
                print("🤖 LLM으로 SQL 생성 중...")
                sql, explanation = await sql_generator.generate_sql_with_llm(query, parsed)
            else:
                sql, explanation = sql_generator.generate_sql(parsed)

            print(f"\n📝 설명: {explanation}")
            print(f"💾 SQL:\n{sql}\n")

            # Ask for execution confirmation
            confirm = input("실행하시겠습니까? (y/n): ").lower()

            if confirm == 'y':
                results, error = sql_executor.execute_query(sql)

                if error:
                    print(f"❌ 오류: {error}")
                else:
                    formatted = sql_executor.format_results(results)
                    print(f"\n📊 결과:\n{formatted}")

        except Exception as e:
            print(f"❌ 오류: {e}")


async def main():
    """메인 테스트 함수"""
    while True:
        print("\n" + "="*70)
        print(" Text2SQL 고도화 테스트 메뉴 ".center(70))
        print("="*70)
        print("\n1. LLM SQL 생성 테스트")
        print("2. 고급 SQL 기능 테스트")
        print("3. 스키마 컨텍스트 테스트")
        print("4. 대화형 테스트")
        print("0. 종료")

        choice = input("\n선택: ").strip()

        if choice == "1":
            await test_llm_sql_generation()
        elif choice == "2":
            await test_advanced_sql_features()
        elif choice == "3":
            await test_schema_context()
        elif choice == "4":
            await interactive_test()
        elif choice == "0":
            print("\n테스트 종료")
            break
        else:
            print("잘못된 선택")


if __name__ == "__main__":
    asyncio.run(main())