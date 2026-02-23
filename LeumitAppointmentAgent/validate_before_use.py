#!/usr/bin/env python3
"""
Pre-commit validation script
Runs all tests before allowing code changes to be used

Exit codes:
  0 = All tests passed
  1 = Tests failed
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd_args, description, cwd):
    """Run a command and return success status"""
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print(f"{'='*70}\n")
    
    result = subprocess.run(cmd_args, cwd=cwd, capture_output=False, text=True)
    return result.returncode == 0

def main():
    """Run all validation checks"""
    project_dir = Path(__file__).parent.resolve()
    
    checks = [
        ([sys.executable, "test_agent_simple.py"], "Unit Tests"),
        ([sys.executable, "test_workflow_integration.py"], "Workflow Integration Tests"),
        ([sys.executable, "-m", "py_compile", "persistent_agent.py"], "Python Syntax Check"),
    ]
    
    all_passed = True
    failed_checks = []
    
    for cmd_args, description in checks:
        if not run_command(cmd_args, description, cwd=project_dir):
            all_passed = False
            failed_checks.append(description)
    
    print("\n" + "="*70)
    if all_passed:
        print("✅ ALL VALIDATION CHECKS PASSED")
        print("="*70)
        print("\nCode is ready to use")
        return 0
    else:
        print("❌ VALIDATION FAILED")
        print("="*70)
        print("\nFailed checks:")
        for check in failed_checks:
            print(f"  ✗ {check}")
        print("\n⚠️  DO NOT USE THIS CODE - FIX TESTS FIRST")
        return 1

if __name__ == "__main__":
    sys.exit(main())
