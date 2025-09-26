"""
Test for Simplified Document Generation Agent
Tests the new 3-node workflow
"""

import asyncio
import sys
import os
import io
from pathlib import Path
from datetime import datetime

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


async def test_simple_query():
    """Test with a simple natural language query"""
    print("\n" + "="*80)
    print("TEST 1: Simple Natural Language Query")
    print("="*80)

    agent = DocumentGenerationAgent()

    query = "제품설명회 신청서 만들어줘. 12월 30일에 신약X 설명회 예정이야."

    print(f"Query: {query}")
    print("-"*40)

    result = await agent.execute({
        "user_query": query,
        "interaction_mode": "auto"
    })

    print_result(result)
    return result


async def test_complete_data():
    """Test with complete data provided upfront"""
    print("\n" + "="*80)
    print("TEST 2: Complete Data Provided")
    print("="*80)

    agent = DocumentGenerationAgent()

    input_data = {
        "doc_type": "product_seminar_report",
        "data": {
            "seminar_type": "단일",
            "pm_attendance": "참석",
            "date": "2024-12-15 14:00",
            "location": "서울 강남구 컨퍼런스홀",
            "product_name": "항암제 Y",
            "actual_attendees": "32명",
            "result": "매우 성공적. 참석자 만족도 95%",
            "main_content": "1. 제품 메커니즘 설명\n2. 임상 3상 데이터\n3. 처방 가이드라인",
            "payment_details": "강의료: 800,000원\n식대: 400,000원",
            "budget_usage": "총 예산: 1,500,000원\n사용: 1,200,000원\n잔액: 300,000원"
        }
    }

    print(f"Document Type: {input_data['doc_type']}")
    print(f"Data Fields Provided: {len(input_data['data'])}")
    print("-"*40)

    result = await agent.execute(input_data)

    print_result(result)
    return result


async def test_minimal_query():
    """Test with minimal information"""
    print("\n" + "="*80)
    print("TEST 3: Minimal Query")
    print("="*80)

    agent = DocumentGenerationAgent()

    query = "제품설명회 결과보고서"

    print(f"Query: {query}")
    print("-"*40)

    result = await agent.execute({
        "user_query": query,
        "interaction_mode": "auto"
    })

    print_result(result)
    return result


def print_result(result):
    """Print test result details"""
    if result.get("status") == "success":
        print("✅ SUCCESS")

        data = result.get("data", {})
        final_doc = data.get("final_document", {})

        if final_doc.get("status") == "success":
            print(f"📄 Document Generated:")
            print(f"   - Type: {final_doc.get('doc_type')}")
            print(f"   - Format: {final_doc.get('format')}")
            print(f"   - Path: {final_doc.get('file_path')}")
            print(f"   - Size: {final_doc.get('file_size', 0):,} bytes")
            print(f"   - Data Fields Used: {final_doc.get('data_used', 0)}")

            # Verify file exists
            file_path = final_doc.get('file_path', '')
            if file_path and os.path.exists(file_path):
                print(f"   ✅ File exists and is accessible")
            else:
                print(f"   ⚠️ File not found at path")

        # Show workflow steps
        if data.get("execution_step"):
            print(f"\n📊 Workflow completed at: {data.get('execution_step')}")

        # Show collected data summary
        collected_data = data.get("collected_data", {})
        if collected_data:
            print(f"\n📋 Data collected: {len(collected_data)} fields")
            # Show first 3 fields as sample
            for i, (key, value) in enumerate(list(collected_data.items())[:3]):
                if isinstance(value, str):
                    value_str = value[:50] + "..." if len(value) > 50 else value
                else:
                    value_str = str(value)[:50]
                print(f"   - {key}: {value_str}")

    else:
        print(f"❌ FAILED: {result.get('error', 'Unknown error')}")

        # Show errors if any
        data = result.get("data", {})
        if data.get("errors"):
            print(f"\n🔴 Errors encountered:")
            for error in data["errors"]:
                print(f"   - {error}")


async def test_workflow_steps():
    """Test and display workflow steps"""
    print("\n" + "="*80)
    print("WORKFLOW ANALYSIS")
    print("="*80)

    agent = DocumentGenerationAgent()

    # Test workflow with insufficient data to trigger collection
    input_data = {
        "doc_type": "product_seminar_application",
        "data": {
            "product_name": "테스트약",
            # Intentionally missing most required fields
        }
    }

    print("Testing workflow with insufficient data...")
    print(f"Provided fields: {list(input_data['data'].keys())}")
    print("-"*40)

    result = await agent.execute(input_data)

    data = result.get("data", {})

    # Check workflow execution
    print("\n🔄 Workflow Execution:")
    print(f"1. Analysis Complete: {'query_analysis' in data or 'template_analysis' in data}")
    print(f"2. Data Collection Triggered: {'collected_data' in data and len(data.get('collected_data', {})) > 1}")
    print(f"3. Document Generated: {'final_document' in data}")

    # Show missing fields that were auto-filled
    missing = data.get("missing_fields", [])
    if missing:
        print(f"\n📝 Fields that were auto-filled: {len(missing)}")
    else:
        print("\n✅ All required fields were collected/generated")

    return result


async def main():
    """Run all tests"""
    print("\n" + "🚀"*20)
    print(" SIMPLIFIED DOCUMENT GENERATION AGENT TEST ")
    print("🚀"*20)

    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ WARNING: OPENAI_API_KEY not found - LLM features may not work")
    else:
        print("✅ OpenAI API Key found")

    # Run tests
    tests = [
        ("Simple Query", test_simple_query),
        ("Complete Data", test_complete_data),
        ("Minimal Query", test_minimal_query),
        ("Workflow Analysis", test_workflow_steps)
    ]

    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, "Success" if result.get("status") == "success" else "Failed"))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, f"Error: {str(e)[:50]}"))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    for name, status in results:
        icon = "✅" if "Success" in status else "❌"
        print(f"{icon} {name}: {status}")

    # Check generated files
    print("\n📁 Generated Files:")
    output_dir = Path("./generated_documents")
    if output_dir.exists():
        files = list(output_dir.glob("*.docx"))
        recent_files = sorted(files, key=lambda x: x.stat().st_mtime)[-5:]
        for file in recent_files:
            mod_time = datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            print(f"   - {file.name} ({file.stat().st_size:,} bytes) - {mod_time}")

    print("\n" + "="*80)
    print("✨ All tests completed!")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())