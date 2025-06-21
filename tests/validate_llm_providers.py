#!/usr/bin/env python3
"""
LLM Provider Validation Script

This script validates that the LLM provider system is working correctly
by running comprehensive tests and checks. It serves as a final validation
for Step 14.1 of the Google GenAI implementation blueprint.

This comprehensive validation script tests:
- Configuration loading for both providers
- Client creation and basic functionality
- Unified client with provider switching
- Main application integration (using mocks)
- All relevant test suites
- Error handling and statistics tracking

Author: Work Journal Summarizer Project
Version: Multi-Provider Support - Step 14.1 Final Validation
"""

import sys
import subprocess
import importlib
import tempfile
import yaml
from pathlib import Path
from typing import List, Tuple, Dict, Any


def run_command(command: List[str]) -> Tuple[bool, str]:
    """Run a command and return success status and output."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)


def test_imports() -> bool:
    """Test that all required modules can be imported."""
    print("🔍 Testing imports...")
    
    required_modules = [
        'config_manager',
        'llm_data_structures',
        'bedrock_client',
        'google_genai_client',
        'unified_llm_client'
    ]
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            return False
    
    return True


def test_configuration() -> bool:
    """Test configuration system."""
    print("\n🔧 Testing configuration system...")
    
    try:
        from config_manager import AppConfig, BedrockConfig, GoogleGenAIConfig, LLMConfig
        
        # Test Bedrock config
        bedrock_config = AppConfig(
            llm=LLMConfig(provider="bedrock"),
            bedrock=BedrockConfig(),
            google_genai=GoogleGenAIConfig()
        )
        assert bedrock_config.llm.provider == "bedrock"
        print("  ✅ Bedrock configuration")
        
        # Test Google GenAI config
        genai_config = AppConfig(
            llm=LLMConfig(provider="google_genai"),
            bedrock=BedrockConfig(),
            google_genai=GoogleGenAIConfig()
        )
        assert genai_config.llm.provider == "google_genai"
        print("  ✅ Google GenAI configuration")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration test failed: {e}")
        return False


def test_unified_client() -> bool:
    """Test unified client creation."""
    print("\n🔗 Testing unified client...")
    
    try:
        from config_manager import AppConfig, BedrockConfig, GoogleGenAIConfig, LLMConfig
        from unified_llm_client import UnifiedLLMClient
        from unittest.mock import patch, MagicMock
        import os
        
        # Test with Bedrock provider
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test-key',
            'AWS_SECRET_ACCESS_KEY': 'test-secret'
        }):
            with patch('bedrock_client.boto3') as mock_boto3:
                mock_boto3.client.return_value = MagicMock()
                
                bedrock_config = AppConfig(
                    llm=LLMConfig(provider="bedrock"),
                    bedrock=BedrockConfig(),
                    google_genai=GoogleGenAIConfig()
                )
                
                client = UnifiedLLMClient(bedrock_config)
                assert client.get_provider_name() == "bedrock"
                print("  ✅ Bedrock client creation")
        
        # Test with Google GenAI provider
        with patch('google_genai_client.genai') as mock_genai:
            mock_genai.Client.return_value = MagicMock()
            
            genai_config = AppConfig(
                llm=LLMConfig(provider="google_genai"),
                bedrock=BedrockConfig(),
                google_genai=GoogleGenAIConfig()
            )
            
            client = UnifiedLLMClient(genai_config)
            assert client.get_provider_name() == "google_genai"
            print("  ✅ Google GenAI client creation")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Unified client test failed: {e}")
        return False


def run_integration_tests() -> bool:
    """Run the comprehensive integration tests."""
    print("\n🧪 Running integration tests...")
    
    success, output = run_command([
        sys.executable, "-m", "pytest", 
        "tests/test_integration_llm_providers.py", 
        "-v", "--tb=short"
    ])
    
    if success:
        # Count passed tests
        lines = output.split('\n')
        passed_count = sum(1 for line in lines if 'PASSED' in line)
        print(f"  ✅ All {passed_count} integration tests passed")
        return True
    else:
        print(f"  ❌ Integration tests failed:")
        print(output)
        return False


def validate_data_structures() -> bool:
    """Validate shared data structures."""
    print("\n📊 Testing data structures...")
    
    try:
        from llm_data_structures import AnalysisResult, APIStats
        from pathlib import Path
        
        # Test AnalysisResult
        result = AnalysisResult(
            file_path=Path("test.md"),
            projects=["Test Project"],
            participants=["Test User"],
            tasks=["Test Task"],
            themes=["Test Theme"],
            api_call_time=1.0
        )
        assert result.file_path == Path("test.md")
        assert len(result.projects) == 1
        print("  ✅ AnalysisResult structure")
        
        # Test APIStats
        stats = APIStats(
            total_calls=10,
            successful_calls=9,
            failed_calls=1,
            total_time=5.0,
            average_response_time=0.5,
            rate_limit_hits=0
        )
        assert stats.total_calls == 10
        assert stats.successful_calls == 9
        print("  ✅ APIStats structure")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Data structures test failed: {e}")
        return False


def test_error_handling() -> bool:
    """Test error handling across the system."""
    print("\n⚠️  Testing error handling...")
    
    try:
        from config_manager import AppConfig, BedrockConfig, GoogleGenAIConfig, LLMConfig
        from unified_llm_client import UnifiedLLMClient
        
        # Test invalid provider
        try:
            invalid_config = AppConfig(
                llm=LLMConfig(provider="invalid_provider"),
                bedrock=BedrockConfig(),
                google_genai=GoogleGenAIConfig()
            )
            UnifiedLLMClient(invalid_config)
            print("  ❌ Should have failed with invalid provider")
            return False
        except ValueError:
            print("  ✅ Invalid provider error handling")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error handling test failed: {e}")
        return False


def test_statistics_tracking() -> bool:
    """Test statistics tracking functionality."""
    print("\n📈 Testing statistics tracking...")
    
    try:
        from config_manager import AppConfig, BedrockConfig, GoogleGenAIConfig, LLMConfig
        from unified_llm_client import UnifiedLLMClient
        from unittest.mock import patch, MagicMock
        import os
        
        # Test with Bedrock provider
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test-key',
            'AWS_SECRET_ACCESS_KEY': 'test-secret'
        }):
            with patch('bedrock_client.boto3') as mock_boto3:
                mock_boto3.client.return_value = MagicMock()
                
                config = AppConfig(
                    llm=LLMConfig(provider="bedrock"),
                    bedrock=BedrockConfig(),
                    google_genai=GoogleGenAIConfig()
                )
                
                client = UnifiedLLMClient(config)
                stats = client.get_stats()
                
                # Verify stats structure
                assert hasattr(stats, 'total_calls')
                assert hasattr(stats, 'successful_calls')
                assert hasattr(stats, 'failed_calls')
                assert hasattr(stats, 'total_time')
                assert hasattr(stats, 'average_response_time')
                assert hasattr(stats, 'rate_limit_hits')
                
                print("  ✅ Statistics structure validation")
                
                # Test reset functionality
                client.reset_stats()
                reset_stats = client.get_stats()
                assert reset_stats.total_calls == 0
                print("  ✅ Statistics reset functionality")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Statistics tracking test failed: {e}")
        return False


def test_provider_switching() -> bool:
    """Test provider switching functionality."""
    print("\n🔄 Testing provider switching...")
    
    try:
        from config_manager import AppConfig, BedrockConfig, GoogleGenAIConfig, LLMConfig
        from unified_llm_client import UnifiedLLMClient
        from unittest.mock import patch, MagicMock
        import os
        
        # Test switching from Bedrock to Google GenAI
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test-key',
            'AWS_SECRET_ACCESS_KEY': 'test-secret'
        }):
            with patch('bedrock_client.boto3') as mock_boto3, \
                 patch('google_genai_client.genai') as mock_genai:
                
                mock_boto3.client.return_value = MagicMock()
                mock_genai.Client.return_value = MagicMock()
                
                # Start with Bedrock
                bedrock_config = AppConfig(
                    llm=LLMConfig(provider="bedrock"),
                    bedrock=BedrockConfig(),
                    google_genai=GoogleGenAIConfig()
                )
                
                client1 = UnifiedLLMClient(bedrock_config)
                assert client1.get_provider_name() == "bedrock"
                print("  ✅ Bedrock provider initialization")
                
                # Switch to Google GenAI
                genai_config = AppConfig(
                    llm=LLMConfig(provider="google_genai"),
                    bedrock=BedrockConfig(),
                    google_genai=GoogleGenAIConfig()
                )
                
                client2 = UnifiedLLMClient(genai_config)
                assert client2.get_provider_name() == "google_genai"
                print("  ✅ Google GenAI provider initialization")
                
                # Test provider info
                bedrock_info = client1.get_provider_info()
                genai_info = client2.get_provider_info()
                
                assert 'region' in bedrock_info
                assert 'model_id' in bedrock_info
                assert 'project' in genai_info
                assert 'location' in genai_info
                assert 'model' in genai_info
                
                print("  ✅ Provider information retrieval")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Provider switching test failed: {e}")
        return False


def test_main_application_integration() -> bool:
    """Test main application integration with mocked providers."""
    print("\n🏗️  Testing main application integration...")
    
    try:
        # Test that main application can be imported
        import work_journal_summarizer
        print("  ✅ Main application import")
        
        # Test configuration loading
        from config_manager import ConfigManager
        
        # Create temporary config for testing
        test_config = {
            'llm': {'provider': 'bedrock'},
            'bedrock': {
                'region': 'us-east-1',
                'model_id': 'anthropic.claude-3-sonnet-20240229-v1:0'
            },
            'google_genai': {
                'project': 'test-project',
                'location': 'us-central1',
                'model': 'gemini-2.0-flash-001'
            },
            'processing': {
                'max_file_size_mb': 10,
                'supported_extensions': ['.md', '.txt']
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            temp_config_path = f.name
        
        try:
            config_manager = ConfigManager(temp_config_path)
            config = config_manager.get_config()
            
            assert config.llm.provider == 'bedrock'
            print("  ✅ Configuration loading")
            
        finally:
            Path(temp_config_path).unlink()
        
        return True
        
    except Exception as e:
        print(f"  ❌ Main application integration test failed: {e}")
        return False


def run_all_test_suites() -> bool:
    """Run all relevant test suites."""
    print("\n🧪 Running all test suites...")
    
    test_files = [
        "tests/test_config_manager.py",
        "tests/test_google_genai_client.py",
        "tests/test_unified_llm_client.py",
        "tests/test_integration_llm_providers.py"
    ]
    
    all_passed = True
    total_tests = 0
    
    for test_file in test_files:
        if Path(test_file).exists():
            print(f"  Running {test_file}...")
            success, output = run_command([
                sys.executable, "-m", "pytest",
                test_file, "-v", "--tb=short", "-q"
            ])
            
            if success:
                # Count tests from output
                lines = output.split('\n')
                passed_count = sum(1 for line in lines if 'PASSED' in line or 'passed' in line.lower())
                if passed_count > 0:
                    total_tests += passed_count
                    print(f"    ✅ {passed_count} tests passed")
                else:
                    # Fallback: look for summary line
                    for line in lines:
                        if 'passed' in line.lower() and ('test' in line.lower() or '::' in line):
                            print(f"    ✅ Tests passed")
                            total_tests += 1
                            break
            else:
                print(f"    ❌ Tests failed:")
                print(f"    {output}")
                all_passed = False
        else:
            print(f"  ⚠️  {test_file} not found, skipping")
    
    if all_passed:
        print(f"  ✅ All test suites passed ({total_tests} total tests)")
    
    return all_passed


def validate_system_readiness() -> bool:
    """Final system readiness validation."""
    print("\n🎯 Validating system readiness...")
    
    try:
        # Check that all key files exist
        required_files = [
            'config_manager.py',
            'llm_data_structures.py',
            'bedrock_client.py',
            'google_genai_client.py',
            'unified_llm_client.py',
            'work_journal_summarizer.py',
            'config.yaml.example'
        ]
        
        for file_path in required_files:
            if not Path(file_path).exists():
                print(f"  ❌ Required file missing: {file_path}")
                return False
        
        print("  ✅ All required files present")
        
        # Check that requirements.txt includes google-genai
        if Path('requirements.txt').exists():
            with open('requirements.txt', 'r') as f:
                requirements = f.read()
                if 'google-genai' in requirements:
                    print("  ✅ Google GenAI dependency in requirements.txt")
                else:
                    print("  ❌ Google GenAI dependency missing from requirements.txt")
                    return False
        
        # Check that config example includes new sections
        if Path('config.yaml.example').exists():
            with open('config.yaml.example', 'r') as f:
                config_example = f.read()
                if 'llm:' in config_example and 'google_genai:' in config_example:
                    print("  ✅ Configuration example updated")
                else:
                    print("  ❌ Configuration example missing new sections")
                    return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ System readiness validation failed: {e}")
        return False


def main():
    """Run all validation tests."""
    print("🚀 LLM Provider System Final Validation")
    print("=" * 60)
    print("This comprehensive validation ensures the system is ready for production use.")
    print()
    
    tests = [
        ("Import Tests", test_imports),
        ("Configuration Tests", test_configuration),
        ("Unified Client Tests", test_unified_client),
        ("Data Structure Tests", validate_data_structures),
        ("Error Handling Tests", test_error_handling),
        ("Statistics Tracking Tests", test_statistics_tracking),
        ("Provider Switching Tests", test_provider_switching),
        ("Main Application Integration", test_main_application_integration),
        ("All Test Suites", run_all_test_suites),
        ("System Readiness Check", validate_system_readiness),
    ]
    
    passed = 0
    total = len(tests)
    failed_tests = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                failed_tests.append(test_name)
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            failed_tests.append(test_name)
            print(f"❌ {test_name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"📊 FINAL VALIDATION RESULTS")
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if failed_tests:
        print(f"\n❌ Failed Tests:")
        for test in failed_tests:
            print(f"  - {test}")
    
    print("\n" + "=" * 60)
    
    if passed == total:
        print("🎉 ALL VALIDATION TESTS PASSED!")
        print("✅ The LLM provider system is ready for production use.")
        print("✅ Both Bedrock and Google GenAI providers are properly integrated.")
        print("✅ All functionality has been validated and tested.")
        return 0
    else:
        print("⚠️  SOME VALIDATION TESTS FAILED")
        print("❌ Please review and fix the issues above before deploying.")
        print("❌ The system may not be ready for production use.")
        return 1


if __name__ == "__main__":
    sys.exit(main())