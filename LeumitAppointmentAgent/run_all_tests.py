"""
Test Suite Runner - Runs all tests

Execute with: python run_all_tests.py
"""

import subprocess
import sys
import signal
import os

# Force UTF-8 encoding on Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

TEST_TIMEOUT = 45  # 45 seconds timeout per test

def run_test_file(filename, description):
    """Run a test file and report results"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}Running: {description}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, filename],
            capture_output=False,
            text=True,
            timeout=TEST_TIMEOUT
        )
        
        if result.returncode == 0:
            print(f"\n{GREEN}[PASS] {description} PASSED{RESET}")
            return True
        else:
            print(f"\n{RED}[FAIL] {description} FAILED{RESET}")
            return False
    
    except subprocess.TimeoutExpired:
        print(f"\n{RED}[TIMEOUT] {description} TIMEOUT (exceeded {TEST_TIMEOUT}s){RESET}")
        return False
    except Exception as e:
        print(f"\n{RED}[ERROR] {description} ERROR: {e}{RESET}")
        return False


def main():
    print("\n" + "="*70)
    print("LEUMIT APPOINTMENT AGENT - FULL TEST SUITE")
    print("="*70)
    
    tests = [
        ("test_agent_simple.py", "Unit Tests (Logic & Hashing)"),
        ("test_workflow_integration.py", "Workflow Integration Tests"),
        ("test_calendar_appointment.py", "Calendar & Appointment Booking Tests"),
        ("test_logging.py", "Logging Configuration Tests"),
        ("test_log_naming.py", "Log File Naming Tests"),
        ("test_simple.py", "Simple Browser Connection Tests"),
        ("test_browser_persistence.py", "Browser Persistence Tests"),
        ("test_independent_chrome.py", "Independent Chrome Launch Tests")
    ]
    
    results = []
    
    for test_file, description in tests:
        passed = run_test_file(test_file, description)
        results.append((description, passed))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUITE SUMMARY")
    print("="*70 + "\n")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for description, passed in results:
        status = f"{GREEN}[PASS]{RESET}" if passed else f"{RED}[FAIL]{RESET}"
        print(f"  {status}: {description}")
    
    print(f"\n{BLUE}Total: {passed_count}/{total_count} test suites passed{RESET}\n")
    
    if passed_count == total_count:
        print(f"{GREEN}{'='*70}{RESET}")
        print(f"{GREEN}ALL TESTS PASSED{RESET}")
        print(f"{GREEN}{'='*70}{RESET}\n")
        return 0
    else:
        print(f"{RED}{'='*70}{RESET}")
        print(f"{RED}SOME TESTS FAILED{RESET}")
        print(f"{RED}{'='*70}{RESET}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
