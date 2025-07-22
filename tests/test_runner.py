#!/usr/bin/env python3
"""
Test runner for XScraper - runs all tests in sequence
"""
import os
import sys
import subprocess
from pathlib import Path

def run_test_file(test_file):
    """Run a single test file and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {test_file}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=False, 
                              text=True, 
                              cwd=os.path.dirname(test_file))
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running {test_file}: {e}")
        return False

def main():
    """Run all tests in the tests directory"""
    tests_dir = Path(__file__).parent
    
    # Define test order (most basic to most complex)
    test_order = [
        'test_decodo_proxy.py',
        'test_auto_login.py', 
        'test_backup_login.py',
        'test_backup_switching.py',
        'test_rate_limit_debugging.py',
        'test_rate_limit_handling.py',
        'test_multi_account.py'
    ]
    
    print("🚀 XScraper Test Suite")
    print("=" * 60)
    
    results = {}
    
    for test_name in test_order:
        test_path = tests_dir / test_name
        if test_path.exists():
            success = run_test_file(str(test_path))
            results[test_name] = success
        else:
            print(f"⚠️  Test file not found: {test_name}")
            results[test_name] = False
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())