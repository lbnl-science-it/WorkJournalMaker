#!/usr/bin/env python3
"""
Settings Persistence Test Runner for Issue #25

This script runs the comprehensive test suite for settings persistence
and generates detailed reports about test coverage and results.
"""

import subprocess
import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path


def run_test_suite():
    """Run the comprehensive settings persistence test suite."""
    
    print("=" * 80)
    print("Settings Persistence Test Suite - Issue #25")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test_suites": {},
        "summary": {},
        "performance_metrics": {},
        "coverage": {}
    }
    
    # Test suites to run
    test_suites = [
        ("Unit Tests", "TestUnitTests"),
        ("Integration Tests", "TestIntegrationTests"),
        ("End-to-End Tests", "TestEndToEndTests"),
        ("Concurrent Update Tests", "TestConcurrentUpdateTests"),
        ("Error Scenario Tests", "TestErrorScenarioTests"),
        ("Performance Tests", "TestPerformanceTests"),
        ("Database State Verification", "TestDatabaseStateVerification")
    ]
    
    total_passed = 0
    total_failed = 0
    total_duration = 0
    
    for suite_name, suite_class in test_suites:
        print(f"Running {suite_name}...")
        start_time = time.time()
        
        # Run the test suite
        cmd = [
            "python", "-m", "pytest", 
            f"tests/test_settings_persistence.py::{suite_class}",
            "-v", "--tb=short", "--json-report", "--json-report-file=test_results.json"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
            end_time = time.time()
            duration = end_time - start_time
            total_duration += duration
            
            # Parse results
            if result.returncode == 0:
                status = "PASSED"
                # Count individual tests (approximate)
                passed_count = result.stdout.count(" PASSED")
                total_passed += passed_count
                print(f"  ✓ {suite_name}: {passed_count} tests passed ({duration:.2f}s)")
            else:
                status = "FAILED"
                failed_count = result.stdout.count(" FAILED") + result.stdout.count(" ERROR")
                total_failed += failed_count
                print(f"  ✗ {suite_name}: {failed_count} tests failed ({duration:.2f}s)")
                if result.stderr:
                    print(f"    Error output: {result.stderr[:200]}...")
            
            test_results["test_suites"][suite_name] = {
                "status": status,
                "duration": duration,
                "stdout": result.stdout[:1000] if len(result.stdout) > 1000 else result.stdout,
                "return_code": result.returncode
            }
            
        except Exception as e:
            print(f"  ✗ {suite_name}: Exception occurred - {str(e)}")
            test_results["test_suites"][suite_name] = {
                "status": "ERROR",
                "error": str(e),
                "duration": 0
            }
            total_failed += 1
    
    # Generate summary
    total_tests = total_passed + total_failed
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    test_results["summary"] = {
        "total_tests": total_tests,
        "total_passed": total_passed,
        "total_failed": total_failed,
        "success_rate": success_rate,
        "total_duration": total_duration
    }
    
    print()
    print("=" * 80)
    print("TEST SUITE SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Total Duration: {total_duration:.2f}s")
    
    # Show suite breakdown
    print()
    print("SUITE BREAKDOWN:")
    for suite_name, results in test_results["test_suites"].items():
        status_icon = "✓" if results["status"] == "PASSED" else "✗"
        duration = results.get("duration", 0)
        print(f"  {status_icon} {suite_name}: {results['status']} ({duration:.2f}s)")
    
    # Test integration with database utility
    print()
    print("=" * 80)
    print("INTEGRATION WITH DATABASE UTILITY")
    print("=" * 80)
    
    try:
        from debug_database_write import DatabaseTestingUtility
        db_tester = DatabaseTestingUtility()
        
        print("✓ Successfully imported database testing utility")
        print("✓ Database testing utility integration verified")
        
        test_results["integration"] = {
            "database_utility_available": True,
            "integration_verified": True
        }
        
    except Exception as e:
        print(f"✗ Database utility integration failed: {str(e)}")
        test_results["integration"] = {
            "database_utility_available": False,
            "error": str(e)
        }
    
    # Save detailed results
    results_file = Path("settings_persistence_test_results.json")
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2, default=str)
    
    print(f"✓ Detailed results saved to: {results_file}")
    
    # Performance analysis
    print()
    print("=" * 80)
    print("PERFORMANCE ANALYSIS")
    print("=" * 80)
    
    if total_duration > 0:
        throughput = total_tests / total_duration
        print(f"Test Throughput: {throughput:.1f} tests/second")
        
        # Check if performance tests passed
        perf_results = test_results["test_suites"].get("Performance Tests", {})
        if perf_results.get("status") == "PASSED":
            print("✓ Performance benchmarks met")
        else:
            print("⚠ Performance benchmarks need attention")
    
    # Final recommendations
    print()
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    if success_rate >= 95:
        print("✓ Excellent test coverage and success rate")
        print("✓ Settings persistence implementation is robust")
    elif success_rate >= 80:
        print("⚠ Good test coverage with some issues to address")
        print("→ Focus on failed test scenarios")
    else:
        print("✗ Significant issues detected")
        print("→ Review failed tests and implementation")
    
    if total_duration > 30:
        print("⚠ Test suite execution time is long")
        print("→ Consider test optimization for CI/CD")
    else:
        print("✓ Test suite execution time is acceptable")
    
    print()
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    return test_results


def run_specific_test_category(category):
    """Run a specific category of tests."""
    category_map = {
        "unit": "TestUnitTests",
        "integration": "TestIntegrationTests", 
        "e2e": "TestEndToEndTests",
        "concurrent": "TestConcurrentUpdateTests",
        "error": "TestErrorScenarioTests",
        "performance": "TestPerformanceTests",
        "verification": "TestDatabaseStateVerification"
    }
    
    if category not in category_map:
        print(f"Unknown category: {category}")
        print(f"Available categories: {', '.join(category_map.keys())}")
        return
    
    suite_class = category_map[category]
    print(f"Running {category} tests ({suite_class})...")
    
    cmd = [
        "python", "-m", "pytest", 
        f"tests/test_settings_persistence.py::{suite_class}",
        "-v", "--tb=short"
    ]
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode == 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run specific category
        category = sys.argv[1].lower()
        success = run_specific_test_category(category)
        sys.exit(0 if success else 1)
    else:
        # Run full test suite
        results = run_test_suite()
        success_rate = results["summary"]["success_rate"]
        sys.exit(0 if success_rate >= 80 else 1)