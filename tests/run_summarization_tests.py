#!/usr/bin/env python3
"""
Test Runner for Web Summarization Service

This script runs all tests related to the Web Summarization Service
with proper configuration and reporting.
"""

import sys
import subprocess
from pathlib import Path
import argparse


def run_tests(test_type="all", verbose=False, coverage=False):
    """
    Run summarization tests with specified options.
    
    Args:
        test_type: Type of tests to run ("all", "unit", "api", "integration")
        verbose: Enable verbose output
        coverage: Enable coverage reporting
    """
    
    test_files = {
        "unit": ["test_web_summarization_service.py"],
        "api": ["test_summarization_api.py"],
        "integration": ["test_summarization_integration.py"],
        "all": [
            "test_web_summarization_service.py",
            "test_summarization_api.py", 
            "test_summarization_integration.py"
        ]
    }
    
    if test_type not in test_files:
        print(f"Invalid test type: {test_type}")
        print(f"Available types: {', '.join(test_files.keys())}")
        return False
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test files
    for test_file in test_files[test_type]:
        cmd.append(str(Path(__file__).parent / test_file))
    
    # Add options
    if verbose:
        cmd.extend(["-v", "-s"])
    
    if coverage:
        cmd.extend([
            "--cov=web.services.web_summarizer",
            "--cov=web.api.summarization",
            "--cov-report=html:tests/coverage_html",
            "--cov-report=term-missing"
        ])
    
    # Add pytest configuration
    cmd.extend([
        "--tb=short",
        "--strict-markers",
        "--disable-warnings"
    ])
    
    print(f"Running {test_type} tests for Web Summarization Service...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return False


def main():
    """Main function to parse arguments and run tests."""
    parser = argparse.ArgumentParser(
        description="Run Web Summarization Service tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_summarization_tests.py                    # Run all tests
  python run_summarization_tests.py --type unit       # Run only unit tests
  python run_summarization_tests.py --type api -v     # Run API tests with verbose output
  python run_summarization_tests.py --coverage        # Run all tests with coverage
        """
    )
    
    parser.add_argument(
        "--type", "-t",
        choices=["all", "unit", "api", "integration"],
        default="all",
        help="Type of tests to run (default: all)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Enable coverage reporting"
    )
    
    args = parser.parse_args()
    
    success = run_tests(
        test_type=args.type,
        verbose=args.verbose,
        coverage=args.coverage
    )
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()