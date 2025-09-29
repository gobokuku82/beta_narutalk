"""Test SQL generation with validation"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.service.tools.sql_generator import SQLGenerator

def test_sql_generation():
    """Test SQL generation with validation"""

    generator = SQLGenerator()

    test_queries = [
        "김철수의 실적",  # Invalid employee
        "윤수아의 실적",  # Valid employee
        "2025년 12월 실적",  # Invalid future date
        "2024년 3월 실적",  # Valid date
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print("-"*40)

        # Parse query
        parsed = generator.parse_query(query)
        print(f"Parsed: {parsed}")

        # Generate SQL
        sql, explanation = generator.generate_sql(parsed)
        print(f"SQL: {sql}")
        print(f"Explanation: {explanation}")

if __name__ == "__main__":
    test_sql_generation()