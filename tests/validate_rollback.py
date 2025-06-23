#!/usr/bin/env python3
"""
Rollback Validation Script

This script validates that the rollback was successful and the system
is functioning correctly with Bedrock-only functionality.

Author: Work Journal Summarizer Project
Version: Rollback Validation
"""

import sys
import subprocess
import importlib
from pathlib import Path
from typing import List, Tuple


def test_bedrock_only_imports() -> bool:
    """Test that only Bedrock-related imports work."""
    print("🔍 Testing Bedrock-only imports...")
    
    # Test that bedrock_client imports work
    try:
        from bedrock_client import BedrockClient, AnalysisResult, APIStats
        print("  ✅ BedrockClient imports successful")
    except ImportError as e:
        print(f"  ❌ BedrockClient import failed: {e}")
        return False
    
    # Test that unified client imports fail (as expected)
    try:
        from unified_llm_client import UnifiedLLMClient
        print("  ⚠️  UnifiedLLMClient still importable (should be removed)")
        return False
    except ImportError:
        print("  ✅ UnifiedLLMClient properly removed")
    
    # Test that google_genai_client imports fail (as expected)
    try:
        from google_genai_client import GoogleGenAIClient
        print("  ⚠️  GoogleGenAIClient still importable (should be removed)")
        return False
    except ImportError:
        print("  ✅ GoogleGenAIClient properly removed")
    
    return True


def test_main_application() -> bool:
    """Test that main application can be imported and initialized."""
    print("\n🏗️  Testing main application...")
    
    try:
        import work_journal_summarizer
        print("  ✅ Main application import successful")
        
        # Test that it uses BedrockClient
        import inspect
        source = inspect.getsource(work_journal_summarizer)
        
        if "from bedrock_client import BedrockClient" in source:
            print("  ✅ Uses BedrockClient import")
        else:
            print("  ❌ Missing BedrockClient import")
            return False
            
        if "BedrockClient(config.bedrock)" in source:
            print("  ✅ Uses BedrockClient initialization")
        else:
            print("  ❌ Missing BedrockClient initialization")
            return False
            
        if "UnifiedLLMClient" in source:
            print("  ❌ Still references UnifiedLLMClient")
            return False
        else:
            print("  ✅ No UnifiedLLMClient references")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Main application test failed: {e}")
        return False


def test_configuration() -> bool:
    """Test that configuration system works without Google GenAI classes."""
    print("\n🔧 Testing configuration system...")
    
    try:
        from config_manager import ConfigManager, AppConfig, BedrockConfig
        
        # Test basic configuration loading
        config = AppConfig()
        print("  ✅ AppConfig creation successful")
        
        # Test that bedrock config exists
        if hasattr(config, 'bedrock'):
            print("  ✅ Bedrock configuration present")
        else:
            print("  ❌ Bedrock configuration missing")
            return False
        
        # Test that Google GenAI config is removed
        if hasattr(config, 'google_genai'):
            print("  ⚠️  Google GenAI configuration still present")
            return False
        else:
            print("  ✅ Google GenAI configuration properly removed")
        
        # Test that LLM config is removed
        if hasattr(config, 'llm'):
            print("  ⚠️  LLM configuration still present")
            return False
        else:
            print("  ✅ LLM configuration properly removed")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        return False


def test_requirements() -> bool:
    """Test that requirements.txt doesn't include google-genai."""
    print("\n📦 Testing requirements...")
    
    requirements_path = Path("requirements.txt")
    if not requirements_path.exists():
        print("  ⚠️  requirements.txt not found")
        return True
    
    try:
        with open(requirements_path, 'r') as f:
            content = f.read()
        
        if 'google-genai' in content:
            print("  ❌ google-genai still in requirements.txt")
            return False
        else:
            print("  ✅ google-genai removed from requirements.txt")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Requirements test failed: {e}")
        return False


def test_file_cleanup() -> bool:
    """Test that new files are properly handled."""
    print("\n🗂️  Testing file cleanup...")
    
    new_files = [
        "llm_data_structures.py",
        "google_genai_client.py",
        "unified_llm_client.py"
    ]
    
    files_present = []
    backup_files = []
    
    for file_name in new_files:
        file_path = Path(file_name)
        backup_path = Path(file_name + '.backup')
        
        if file_path.exists():
            files_present.append(file_name)
        elif backup_path.exists():
            backup_files.append(file_name)
    
    if files_present:
        print(f"  ⚠️  Files still present: {', '.join(files_present)}")
        print("     (These should be removed or backed up)")
        return False
    elif backup_files:
        print(f"  ✅ Files backed up: {', '.join(backup_files)}")
    else:
        print("  ✅ New files properly removed")
    
    return True


def test_dry_run() -> bool:
    """Test that dry-run mode works."""
    print("\n🧪 Testing dry-run functionality...")
    
    try:
        result = subprocess.run([
            sys.executable, "work_journal_summarizer.py", "--dry-run"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("  ✅ Dry-run executed successfully")
            
            # Check for Bedrock-specific output
            if "AWS Region" in result.stdout or "bedrock" in result.stdout.lower():
                print("  ✅ Shows Bedrock configuration")
            else:
                print("  ⚠️  No Bedrock configuration shown")
            
            # Check that no Google GenAI references remain
            if "google" in result.stdout.lower() or "genai" in result.stdout.lower():
                print("  ❌ Still shows Google GenAI references")
                return False
            else:
                print("  ✅ No Google GenAI references")
            
            return True
        else:
            print(f"  ❌ Dry-run failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("  ❌ Dry-run timed out")
        return False
    except Exception as e:
        print(f"  ❌ Dry-run test failed: {e}")
        return False


def run_existing_tests() -> bool:
    """Run existing test suites to ensure no regressions."""
    print("\n🧪 Running existing tests...")
    
    test_files = [
        "tests/test_bedrock_client.py",
        "tests/test_config_manager.py"
    ]
    
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"  Running {test_file}...")
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    print(f"    ✅ {test_file} passed")
                else:
                    print(f"    ❌ {test_file} failed:")
                    print(f"    {result.stdout}")
                    print(f"    {result.stderr}")
                    return False
                    
            except subprocess.TimeoutExpired:
                print(f"    ❌ {test_file} timed out")
                return False
            except Exception as e:
                print(f"    ❌ {test_file} error: {e}")
                return False
        else:
            print(f"  ⚠️  {test_file} not found, skipping")
    
    return True


def main():
    """Run all rollback validation tests."""
    print("🔍 Rollback Validation Script")
    print("=" * 40)
    print("Validating that rollback was successful and system works with Bedrock-only functionality.")
    print()
    
    tests = [
        ("Bedrock-only imports", test_bedrock_only_imports),
        ("Main application", test_main_application),
        ("Configuration system", test_configuration),
        ("Requirements cleanup", test_requirements),
        ("File cleanup", test_file_cleanup),
        ("Dry-run functionality", test_dry_run),
        ("Existing tests", run_existing_tests)
    ]
    
    passed = 0
    total = len(tests)
    failed_tests = []
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                failed_tests.append(test_name)
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            failed_tests.append(test_name)
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 ROLLBACK VALIDATION RESULTS")
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if failed_tests:
        print(f"\n❌ Failed Tests:")
        for test in failed_tests:
            print(f"  - {test}")
    
    print("\n" + "=" * 40)
    
    if passed == total:
        print("🎉 ROLLBACK VALIDATION SUCCESSFUL!")
        print("✅ System successfully restored to Bedrock-only functionality")
        print("✅ All functionality validated and working correctly")
        return 0
    else:
        print("⚠️  ROLLBACK VALIDATION ISSUES DETECTED")
        print("❌ Some validation tests failed")
        print("📖 Please review the issues above and complete rollback manually if needed")
        return 1


if __name__ == "__main__":
    sys.exit(main())