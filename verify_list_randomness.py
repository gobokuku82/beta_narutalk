"""
Verify that staff and HCP lists are also randomly generated
"""

import asyncio
import sys
import os
import io
from pathlib import Path

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

from backend.service.tools.default_value_generator import DefaultValueGenerator


def test_staff_lists():
    """Test staff list generation for randomness"""

    generator = DefaultValueGenerator()

    print("\n📋 Testing Staff List Generation")
    print("=" * 60)

    staff_lists = []
    for i in range(3):
        staff_list = generator.get_staff_list(count=3)
        staff_lists.append(staff_list)

        print(f"\nGeneration {i+1}:")
        for staff in staff_list:
            print(f"  {staff['no']}. {staff['team']} - {staff['name']}")

    # Check for variety
    print("\n🔍 Staff List Analysis:")
    all_names = []
    for lst in staff_lists:
        names = [s['name'] for s in lst]
        all_names.extend(names)

    unique_names = set(all_names)
    print(f"Total staff entries: {len(all_names)}")
    print(f"Unique names used: {len(unique_names)}")

    if len(unique_names) > 3:
        print("✅ Good variety in staff selection")
    else:
        print("⚠️  Limited variety in staff selection")


def test_hcp_lists():
    """Test HCP list generation for randomness"""

    generator = DefaultValueGenerator()

    print("\n\n🏥 Testing HCP List Generation")
    print("=" * 60)

    hcp_lists = []
    for i in range(3):
        hcp_list = generator.get_hcp_list(count=3)
        hcp_lists.append(hcp_list)

        print(f"\nGeneration {i+1}:")
        for hcp in hcp_list:
            print(f"  {hcp['no']}. {hcp['hospital']} - {hcp['name']}")

    # Check for variety
    print("\n🔍 HCP List Analysis:")
    all_hospitals = []
    all_names = []
    for lst in hcp_lists:
        hospitals = [h['hospital'] for h in lst]
        names = [h['name'] for h in lst]
        all_hospitals.extend(hospitals)
        all_names.extend(names)

    unique_hospitals = set(all_hospitals)
    unique_names = set(all_names)

    print(f"Total HCP entries: {len(all_names)}")
    print(f"Unique hospitals: {len(unique_hospitals)}")
    print(f"Unique HCP names: {len(unique_names)}")

    if len(unique_hospitals) > 2 and len(unique_names) > 3:
        print("✅ Good variety in HCP selection")
    else:
        print("⚠️  Limited variety in HCP selection")


def test_cache_reset():
    """Test that cache reset provides new variations"""

    generator = DefaultValueGenerator()

    print("\n\n🔄 Testing Cache Reset")
    print("=" * 60)

    # Get locations before and after reset
    locations_before = []
    for _ in range(5):
        locations_before.append(generator.get_location())

    generator.reset_cache()

    locations_after = []
    for _ in range(5):
        locations_after.append(generator.get_location())

    print("\nLocations before reset:")
    for loc in locations_before[:3]:
        print(f"  - {loc}")

    print("\nLocations after reset:")
    for loc in locations_after[:3]:
        print(f"  - {loc}")

    # Check if patterns changed
    if locations_before != locations_after:
        print("\n✅ Cache reset working - different patterns after reset")
    else:
        print("\n⚠️  Same pattern after reset")


def main():
    """Run all tests"""

    print("\n" + "🔍" * 20)
    print(" LIST RANDOMNESS VERIFICATION ")
    print("🔍" * 20)

    test_staff_lists()
    test_hcp_lists()
    test_cache_reset()

    print("\n\n✨ List verification complete!")


if __name__ == "__main__":
    main()