"""
Interactive Document Generation Test
Tests the new query-based document generation with GPT-4o-mini
"""

import asyncio
import sys
import os
import io
from pathlib import Path

# Windows 인코딩 설정
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding='utf-8',
        errors='replace'
    )

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv(Path('.env'))

from backend.service.agents.document_generation_agent import DocumentGenerationAgent


async def test_query_to_document():
    """Test natural language query to document generation"""

    print("=" * 80)
    print("🤖 Interactive Document Generation Test")
    print("=" * 80)

    # Initialize agent
    agent = DocumentGenerationAgent()

    # Test cases with natural language queries
    test_queries = [
        {
            "name": "Simple Application Query",
            "query": "제품설명회 신청서 만들어줘. 12월 25일 오후 2시에 서울 강남 회의실에서 신약B 제품 설명회 할거야. 20명 정도 참석 예정이고, PM도 참석한다고 해.",
            "expected_type": "product_seminar_application"
        },
        {
            "name": "Report Query with Details",
            "query": "지난주 진행한 제품설명회 결과보고서 작성해줘. 제품명은 항암제X이고, 15명 참석했어. 강의료 50만원, 다과비 20만원 썼고, 전체적으로 만족도가 높았어.",
            "expected_type": "product_seminar_report"
        },
        {
            "name": "Minimal Query",
            "query": "제품설명회 신청서",
            "expected_type": "product_seminar_application"
        }
    ]

    for i, test_case in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"📝 Test Case {i}: {test_case['name']}")
        print(f"Query: {test_case['query']}")
        print("-" * 60)

        try:
            # Prepare input
            input_data = {
                "user_query": test_case["query"],
                "interaction_mode": "auto"  # Auto-fill missing fields
            }

            print("\n🔄 Processing query...")

            # Execute agent
            result = await agent.execute(input_data)

            # Check result
            if result.get("status") == "success":
                print("✅ Document generation successful!")

                # Get final document info
                final_doc = result.get("data", {}).get("final_document", {})

                if final_doc:
                    print(f"\n📄 Document Details:")
                    print(f"   - Type: {final_doc.get('doc_type', 'N/A')}")
                    print(f"   - Format: {final_doc.get('format', 'N/A')}")
                    print(f"   - Title: {final_doc.get('title', 'N/A')}")
                    print(f"   - Word Count: {final_doc.get('word_count', 0)}")

                    # Check if Word file was created
                    if final_doc.get('format') == 'word':
                        content_path = final_doc.get('content', '')
                        if content_path and os.path.exists(content_path):
                            file_size = os.path.getsize(content_path)
                            print(f"   - File: {content_path}")
                            print(f"   - Size: {file_size:,} bytes")
                        else:
                            print(f"   - File path: {content_path}")

                    # Show metadata
                    metadata = final_doc.get('metadata', {})
                    if metadata:
                        print(f"\n📊 Metadata:")
                        for key, value in metadata.items():
                            print(f"   - {key}: {value}")

                # Show collected data
                collected = result.get("data", {}).get("collected_data", {})
                if collected:
                    print(f"\n📋 Collected Data:")
                    for key, value in collected.items():
                        if isinstance(value, list):
                            print(f"   - {key}: {len(value)} items")
                        else:
                            print(f"   - {key}: {value[:50]}..." if isinstance(value, str) and len(value) > 50 else f"   - {key}: {value}")

            else:
                print(f"❌ Document generation failed: {result.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"❌ Error during test: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 80)
    print("✅ All tests completed!")

    # Check generated files
    output_dir = Path("./generated_documents")
    if output_dir.exists():
        files = list(output_dir.glob("*.docx"))
        if files:
            print(f"\n📁 Generated Word documents:")
            for file in sorted(files)[-5:]:  # Show last 5 files
                print(f"   - {file.name} ({file.stat().st_size:,} bytes)")


async def test_interactive_flow():
    """Test interactive data collection flow (simulation)"""

    print("\n" + "=" * 80)
    print("🔄 Testing Interactive Flow")
    print("=" * 80)

    agent = DocumentGenerationAgent()

    # Simulate user providing minimal info
    input_data = {
        "user_query": "제품설명회 결과보고서 만들어줘",
        "interaction_mode": "auto"
    }

    print("User: 제품설명회 결과보고서 만들어줘")
    print("\n🤖 Agent analyzing query and generating document...")

    result = await agent.execute(input_data)

    if result.get("status") == "success":
        print("\n✅ Document created with auto-filled data!")

        # Show what was auto-filled
        collected = result.get("data", {}).get("collected_data", {})
        missing = result.get("data", {}).get("missing_fields", [])

        if collected:
            print("\n📝 Auto-filled fields:")
            for key in ["date", "location", "product_name", "actual_attendees", "result"]:
                if key in collected:
                    print(f"   - {key}: {collected[key]}")

        if missing:
            print(f"\n⚠️ Note: In real interactive mode, the agent would ask for:")
            for field in missing[:3]:  # Show first 3
                print(f"   - {field.get('label', field.get('name'))}")

    else:
        print(f"❌ Failed: {result.get('error')}")


async def main():
    """Main test function"""

    print("=" * 80)
    print("🚀 Starting Interactive Document Generation Tests")
    print("=" * 80)

    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found in .env file")
        return

    print("✅ OpenAI API key found")

    # Run tests
    await test_query_to_document()
    await test_interactive_flow()

    print("\n" + "=" * 80)
    print("🎉 All tests completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())