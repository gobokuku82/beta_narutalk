"""
Verify that dynamic default values are truly random and not hardcoded
"""

import asyncio
import sys
import os
import io
from pathlib import Path
from datetime import datetime
import json

# Windows encoding setup
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding='utf-8',
        errors='replace'
    )

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(Path('.env'))

from backend.service.agents.document_generation_agent import DocumentGenerationAgent


async def generate_multiple_documents(count=3):
    """Generate multiple documents to verify randomness"""

    agent = DocumentGenerationAgent()
    results = []

    print(f"\n📝 Generating {count} documents to verify dynamic values...")
    print("=" * 60)

    for i in range(count):
        print(f"\n🔄 Generation {i+1}:")

        # Generate with minimal input to force default generation
        result = await agent.execute({
            "doc_type": "product_seminar_application",
            "interaction_mode": "auto"
        })

        if result.get("status") == "success":
            data = result.get("data", {})
            collected = data.get("collected_data", {})

            # Extract key fields to compare
            key_fields = {
                "date": collected.get("date"),
                "location": collected.get("location"),
                "product_name": collected.get("product_name"),
                "pm_attendance": collected.get("pm_attendance"),
                "expected_attendees": collected.get("expected_attendees"),
                "purpose": collected.get("purpose")
            }

            results.append(key_fields)

            print(f"  Date: {key_fields['date']}")
            print(f"  Location: {key_fields['location'][:30]}...")
            print(f"  Product: {key_fields['product_name']}")
            print(f"  PM Attendance: {key_fields['pm_attendance']}")
            print(f"  Expected Attendees: {key_fields['expected_attendees']}")

    return results


async def analyze_randomness(results):
    """Analyze if values are truly random"""

    print("\n" + "=" * 60)
    print("📊 RANDOMNESS ANALYSIS")
    print("=" * 60)

    # Check each field for uniqueness
    fields_to_check = ["date", "location", "product_name", "pm_attendance", "expected_attendees", "purpose"]

    for field in fields_to_check:
        values = [r[field] for r in results if r.get(field)]
        unique_values = set(values)

        print(f"\n{field}:")
        print(f"  Total values: {len(values)}")
        print(f"  Unique values: {len(unique_values)}")

        if len(unique_values) == 1:
            print(f"  ⚠️  WARNING: All values are the same! ({values[0]})")
        else:
            print(f"  ✅ Values are different:")
            for val in unique_values:
                print(f"     - {val[:50] if isinstance(val, str) else val}")

    # Overall assessment
    print("\n" + "=" * 60)
    print("🎯 CONCLUSION:")

    all_different = all(
        len(set(r[field] for r in results if r.get(field))) > 1
        for field in fields_to_check
        if any(r.get(field) for r in results)
    )

    if all_different:
        print("✅ Dynamic value generation is working correctly!")
        print("   Different values are being generated for each document.")
    else:
        print("⚠️  Some fields may still be using fixed values.")
        print("   Check the fields marked with WARNING above.")


async def main():
    """Main test function"""

    print("\n" + "🔍" * 20)
    print(" DYNAMIC VALUE GENERATION VERIFICATION ")
    print("🔍" * 20)

    # Generate multiple documents
    results = await generate_multiple_documents(count=5)

    # Analyze randomness
    await analyze_randomness(results)

    print("\n✨ Verification complete!")


if __name__ == "__main__":
    asyncio.run(main())