#!/usr/bin/env python3
"""
Test Runner for Calendar API Implementation (Step 8)

This script provides an easy way to run all calendar-related tests
with different configurations and reporting options.
"""

import sys
import os
import argparse
import subprocess
import time
from pathlib import Path

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent))


def run_command(cmd, description=""):
    """Run a command and return the result."""
    print(f"\n{'='*60}")
    if description:
        print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=False)
    end_time = time.time()
    
    duration = end_time - start_time
    status = "PASSED" if result.returncode == 0 else "FAILED"
    
    print(f"\nResult: {status} (Duration: {duration:.2f}s)")
    return result.returncode == 0


def run_unit_tests():
    """Run unit tests for calendar functionality."""
    cmd = [
        "python", "-m", "pytest",
        "tests/test_calendar_api_endpoints.py",
        "-v", "--tb=short", "-m", "not slow"
    ]
    return run_command(cmd, "Calendar API Endpoints Unit Tests")


def run_integration_tests():
    """Run integration tests for calendar service."""
    cmd = [
        "python", "-m", "pytest",
        "tests/test_calendar_service_integration.py",
        "-v", "--tb=short"
    ]
    return run_command(cmd, "Calendar Service Integration Tests")


def run_performance_tests():
    """Run performance tests for calendar API."""
    cmd = [
        "python", "-m", "pytest",
        "tests/test_calendar_api_performance.py",
        "-v", "--tb=short", "-m", "not slow"
    ]
    return run_command(cmd, "Calendar API Performance Tests")


def run_load_tests():
    """Run load/stress tests for calendar API."""
    cmd = [
        "python", "-m", "pytest",
        "tests/test_calendar_api_performance.py",
        "-v", "--tb=short", "-m", "slow"
    ]
    return run_command(cmd, "Calendar API Load/Stress Tests")


def run_comprehensive_tests():
    """Run comprehensive validation tests."""
    cmd = [
        "python", "-m", "pytest",
        "tests/test_calendar_comprehensive.py",
        "-v", "--tb=short"
    ]
    return run_command(cmd, "Calendar Implementation Validation Tests")


def run_all_tests():
    """Run all calendar tests."""
    cmd = [
        "python", "-m", "pytest",
        "tests/test_calendar_api_endpoints.py",
        "tests/test_calendar_service_integration.py",
        "tests/test_calendar_api_performance.py",
        "tests/test_calendar_comprehensive.py",
        "-v", "--tb=short", "-m", "not slow"
    ]
    return run_command(cmd, "All Calendar Tests (excluding slow tests)")


def run_all_tests_including_slow():
    """Run all calendar tests including slow ones."""
    cmd = [
        "python", "-m", "pytest",
        "tests/test_calendar_api_endpoints.py",
        "tests/test_calendar_service_integration.py",
        "tests/test_calendar_api_performance.py",
        "tests/test_calendar_comprehensive.py",
        "-v", "--tb=short"
    ]
    return run_command(cmd, "All Calendar Tests (including slow tests)")


def run_with_coverage():
    """Run tests with coverage reporting."""
    cmd = [
        "python", "-m", "pytest",
        "tests/test_calendar_api_endpoints.py",
        "tests/test_calendar_service_integration.py",
        "tests/test_calendar_comprehensive.py",
        "--cov=web.api.calendar",
        "--cov=web.services.calendar_service",
        "--cov-report=html",
        "--cov-report=term-missing",
        "-v", "--tb=short", "-m", "not slow"
    ]
    return run_command(cmd, "Calendar Tests with Coverage")


def validate_environment():
    """Validate that the test environment is properly set up."""
    print("Validating test environment...")
    
    # Check if required files exist
    required_files = [
        "web/api/calendar.py",
        "web/services/calendar_service.py",
        "web/models/journal.py",
        "tests/test_calendar_api_endpoints.py",
        "tests/test_calendar_service_integration.py",
        "tests/test_calendar_api_performance.py",
        "tests/test_calendar_comprehensive.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    # Check if pytest is available
    try:
        subprocess.run(["python", "-m", "pytest", "--version"], 
                      capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ pytest is not available. Please install it with: pip install pytest")
        return False
    
    print("✅ Environment validation passed")
    return True


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="Test runner for Calendar API implementation (Step 8)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_calendar_tests.py --unit          # Run unit tests only
  python run_calendar_tests.py --integration   # Run integration tests only
  python run_calendar_tests.py --performance   # Run performance tests only
  python run_calendar_tests.py --all           # Run all tests (excluding slow)
  python run_calendar_tests.py --all --slow    # Run all tests including slow ones
  python run_calendar_tests.py --coverage      # Run tests with coverage
  python run_calendar_tests.py --validate      # Validate environment only
        """
    )
    
    parser.add_argument("--unit", action="store_true",
                       help="Run unit tests for calendar API endpoints")
    parser.add_argument("--integration", action="store_true",
                       help="Run integration tests for calendar service")
    parser.add_argument("--performance", action="store_true",
                       help="Run performance tests (excluding slow tests)")
    parser.add_argument("--load", action="store_true",
                       help="Run load/stress tests (slow)")
    parser.add_argument("--comprehensive", action="store_true",
                       help="Run comprehensive validation tests")
    parser.add_argument("--all", action="store_true",
                       help="Run all calendar tests")
    parser.add_argument("--slow", action="store_true",
                       help="Include slow tests (use with --all or --performance)")
    parser.add_argument("--coverage", action="store_true",
                       help="Run tests with coverage reporting")
    parser.add_argument("--validate", action="store_true",
                       help="Validate test environment only")
    
    args = parser.parse_args()
    
    # If no specific test type is specified, run all tests
    if not any([args.unit, args.integration, args.performance, args.load,
                args.comprehensive, args.all, args.coverage, args.validate]):
        args.all = True
    
    print("Calendar API Tests Runner (Step 8)")
    print("="*60)
    
    # Validate environment first
    if not validate_environment():
        sys.exit(1)
    
    if args.validate:
        print("✅ Environment validation completed successfully")
        sys.exit(0)
    
    # Track test results
    results = []
    
    # Run requested tests
    if args.unit:
        results.append(("Unit Tests", run_unit_tests()))
    
    if args.integration:
        results.append(("Integration Tests", run_integration_tests()))
    
    if args.performance:
        if args.slow:
            results.append(("Performance Tests (with slow)", run_load_tests()))
        else:
            results.append(("Performance Tests", run_performance_tests()))
    
    if args.load:
        results.append(("Load/Stress Tests", run_load_tests()))
    
    if args.comprehensive:
        results.append(("Comprehensive Tests", run_comprehensive_tests()))
    
    if args.coverage:
        results.append(("Tests with Coverage", run_with_coverage()))
    
    if args.all:
        if args.slow:
            results.append(("All Tests (including slow)", run_all_tests_including_slow()))
        else:
            results.append(("All Tests", run_all_tests()))
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    
    passed = 0
    failed = 0
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status}: {test_name}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All calendar tests passed! Step 8 implementation is working correctly.")
        sys.exit(0)
    else:
        print(f"\n⚠️  {failed} test suite(s) failed. Please review and fix issues.")
        sys.exit(1)


if __name__ == "__main__":
    main()