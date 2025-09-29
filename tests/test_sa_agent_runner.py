"""
Sales Analytics Agent - Test Runner
판매 분석 에이전트 테스트 실행기

모든 테스트를 실행하는 통합 테스트 러너

사용법:
    python tests/test_sa_agent_runner.py
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime

def run_test(test_file: str, args: list = None) -> int:
    """Run a single test file"""
    print(f"\n{'='*60}")
    print(f"Running: {test_file}")
    print(f"{'='*60}")

    cmd = [sys.executable, test_file]
    if args:
        cmd.extend(args)

    result = subprocess.run(cmd, capture_output=False, text=True)
    return result.returncode

def main():
    """Main test runner"""
    tests = [
        ("tests/test_sa_agent_structure.py", []),  # Structure validation
        ("tests/test_sa_agent_batch.py", ["--category", "basic"]),  # Basic batch tests only for quick test
        # Interactive test requires user input, so we skip it in automated run
    ]

    print(f"Sales Analytics Agent Test Suite")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    results = {}
    for test_file, args in tests:
        test_name = Path(test_file).stem
        return_code = run_test(test_file, args)
        results[test_name] = "PASSED" if return_code == 0 else "FAILED"

    # Summary
    print(f"\n{'='*60}")
    print("Test Summary:")
    print(f"{'='*60}")
    for test_name, status in results.items():
        color = "\033[92m" if status == "PASSED" else "\033[91m"
        reset = "\033[0m"
        print(f"{test_name}: {color}{status}{reset}")

    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Return 0 if all passed, 1 otherwise
    return 0 if all(s == "PASSED" for s in results.values()) else 1

if __name__ == "__main__":
    sys.exit(main())