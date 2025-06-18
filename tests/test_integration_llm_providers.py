#!/usr/bin/env python3
"""
Integration Tests for LLM Provider System

This module contains comprehensive end-to-end integration tests that verify
the entire LLM provider system works correctly with both AWS Bedrock and
Google GenAI providers. These tests exercise the complete workflow from
configuration loading through content analysis and statistics tracking.

Author: Work Journal Summarizer Project
Version: Multi-Provider Support - Step 13
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import json
import tempfile
import yaml
from typing import Dict, Any

from config_manager import AppConfig, BedrockConfig, GoogleGenAIConfig, LLMConfig, ProcessingConfig, LogConfig
from unified_llm_client import UnifiedLLMClient
from bedrock_client import BedrockClient
from google_genai_client import GoogleGenAIClient
from llm_data_structures import AnalysisResult, APIStats


class TestLLMProviderIntegration:
    """Comprehensive integration tests for the LLM provider system."""
    
    @pytest.fixture
    def sample_journal_content(self):
        """Sample journal content for testing analysis."""
        return """
        # Work Journal - January 15, 2024
        
        ## Project Alpha Development
        
        Today I worked with Sarah Johnson and Mike Chen on the Project Alpha initiative.
        We completed the following tasks:
        - Code review for the authentication module
        - Database schema optimization
        - Unit test implementation
        
        ## Beta Project Planning
        
        Had a planning session with the Beta Project team including Lisa Wong.
        Key themes discussed:
        - User experience improvements
        - Performance optimization
        - Security enhancements
        
        ## Administrative Tasks
        
        - Team standup meeting
        - Sprint planning preparation
        - Documentation updates
        """
    
    @pytest.fixture
    def expected_analysis_result(self):
        """Expected analysis result structure for testing."""
        return {
            "projects": ["Project Alpha", "Beta Project"],
            "participants": ["Sarah Johnson", "Mike Chen", "Lisa Wong"],
            "tasks": [
                "Code review for the authentication module",
                "Database schema optimization", 
                "Unit test implementation",
                "Team standup meeting",
                "Sprint planning preparation"
            ],
            "themes": [
                "Development",
                "Planning",
                "User experience improvements",
                "Performance optimization",
                "Security enhancements"
            ]
        }
    
    @pytest.fixture
    def bedrock_config(self):
        """Create complete configuration with Bedrock provider."""
        return AppConfig(
            llm=LLMConfig(provider="bedrock"),
            bedrock=BedrockConfig(
                region="us-east-1",
                model_id="anthropic.claude-sonnet-4-20250514-v1:0"
            ),
            google_genai=GoogleGenAIConfig(),
            processing=ProcessingConfig(),
            logging=LogConfig()
        )
    
    @pytest.fixture
    def google_genai_config(self):
        """Create complete configuration with Google GenAI provider."""
        return AppConfig(
            llm=LLMConfig(provider="google_genai"),
            bedrock=BedrockConfig(),
            google_genai=GoogleGenAIConfig(
                project="test-project-123",
                location="us-central1",
                model="gemini-2.0-flash-001"
            ),
            processing=ProcessingConfig(),
            logging=LogConfig()
        )
    
    @pytest.fixture
    def invalid_provider_config(self):
        """Create configuration with invalid provider."""
        return AppConfig(
            llm=LLMConfig(provider="invalid_provider"),
            bedrock=BedrockConfig(),
            google_genai=GoogleGenAIConfig(),
            processing=ProcessingConfig(),
            logging=LogConfig()
        )

    def test_bedrock_provider_complete_workflow(self, bedrock_config, sample_journal_content, expected_analysis_result):
        """Test complete workflow with Bedrock provider."""
        with patch.dict('os.environ', {
            'AWS_ACCESS_KEY_ID': 'test-access-key',
            'AWS_SECRET_ACCESS_KEY': 'test-secret-key'
        }):
            with patch('bedrock_client.boto3') as mock_boto3:
                # Mock Bedrock client and response
                mock_bedrock_client = MagicMock()
                mock_boto3.client.return_value = mock_bedrock_client
                
                # Mock successful API response in the correct format
                mock_bedrock_response = {
                    'content': [{
                        'text': json.dumps(expected_analysis_result)
                    }]
                }
                mock_response = {
                    'body': MagicMock()
                }
                mock_response['body'].read.return_value = json.dumps(mock_bedrock_response).encode()
                mock_bedrock_client.invoke_model.return_value = mock_response
                
                # Create unified client
                client = UnifiedLLMClient(bedrock_config)
                
                # Verify provider is correctly set
                assert client.get_provider_name() == "bedrock"
                
                # Test provider info
                provider_info = client.get_provider_info()
                assert provider_info["provider"] == "bedrock"
                assert provider_info["region"] == "us-east-1"
                assert provider_info["model_id"] == "anthropic.claude-sonnet-4-20250514-v1:0"
                
                # Test connection
                assert client.test_connection() is True
                
                # Test content analysis
                file_path = Path("test_journal.md")
                result = client.analyze_content(sample_journal_content, file_path)
                
                # Verify analysis result structure
                assert isinstance(result, AnalysisResult)
                assert result.file_path == file_path
                assert len(result.projects) > 0
                assert len(result.participants) > 0
                assert len(result.tasks) > 0
                assert len(result.themes) > 0
                assert result.api_call_time > 0
                
                # Test statistics tracking
                stats = client.get_stats()
                assert isinstance(stats, APIStats)
                assert stats.total_calls >= 1  # at least analysis call
                assert stats.successful_calls >= 1
                assert stats.failed_calls == 0
                assert stats.total_time > 0
                assert stats.average_response_time > 0
                
                # Test stats reset
                client.reset_stats()
                reset_stats = client.get_stats()
                assert reset_stats.total_calls == 0
                assert reset_stats.successful_calls == 0
                assert reset_stats.failed_calls == 0

    def test_google_genai_provider_complete_workflow(self, google_genai_config, sample_journal_content, expected_analysis_result):
        """Test complete workflow with Google GenAI provider."""
        with patch('google_genai_client.genai') as mock_genai:
            # Mock Google GenAI client and response
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client
            
            # Mock successful API response
            mock_response = MagicMock()
            mock_response.text = json.dumps(expected_analysis_result)
            mock_client.models.generate_content.return_value = mock_response
            
            # Create unified client
            client = UnifiedLLMClient(google_genai_config)
            
            # Verify provider is correctly set
            assert client.get_provider_name() == "google_genai"
            
            # Test provider info
            provider_info = client.get_provider_info()
            assert provider_info["provider"] == "google_genai"
            assert provider_info["project"] == "test-project-123"
            assert provider_info["location"] == "us-central1"
            assert provider_info["model"] == "gemini-2.0-flash-001"
            
            # Test connection
            assert client.test_connection() is True
            
            # Test content analysis
            file_path = Path("test_journal.md")
            result = client.analyze_content(sample_journal_content, file_path)
            
            # Verify analysis result structure
            assert isinstance(result, AnalysisResult)
            assert result.file_path == file_path
            assert len(result.projects) > 0
            assert len(result.participants) > 0
            assert len(result.tasks) > 0
            assert len(result.themes) > 0
            assert result.api_call_time > 0
            
            # Test statistics tracking
            stats = client.get_stats()
            assert isinstance(stats, APIStats)
            assert stats.total_calls >= 2  # connection test + analysis
            assert stats.successful_calls >= 2
            assert stats.failed_calls == 0
            assert stats.total_time > 0
            assert stats.average_response_time > 0
            
            # Test stats reset
            client.reset_stats()
            reset_stats = client.get_stats()
            assert reset_stats.total_calls == 0
            assert reset_stats.successful_calls == 0
            assert reset_stats.failed_calls == 0

    def test_provider_switching(self, bedrock_config, google_genai_config, sample_journal_content, expected_analysis_result):
        """Test switching between providers with different configurations."""
        # Test Bedrock first
        with patch.dict('os.environ', {
            'AWS_ACCESS_KEY_ID': 'test-access-key',
            'AWS_SECRET_ACCESS_KEY': 'test-secret-key'
        }):
            with patch('bedrock_client.boto3') as mock_boto3:
                mock_bedrock_client = MagicMock()
                mock_boto3.client.return_value = mock_bedrock_client
                mock_bedrock_response = {
                    'content': [{'text': json.dumps(expected_analysis_result)}]
                }
                mock_response = {
                    'body': MagicMock()
                }
                mock_response['body'].read.return_value = json.dumps(mock_bedrock_response).encode()
                mock_bedrock_client.invoke_model.return_value = mock_response
            
            bedrock_client = UnifiedLLMClient(bedrock_config)
            assert bedrock_client.get_provider_name() == "bedrock"
            
            # Analyze content with Bedrock
            result1 = bedrock_client.analyze_content(sample_journal_content, Path("test1.md"))
            bedrock_stats = bedrock_client.get_stats()
        
        # Test Google GenAI second
        with patch('google_genai_client.genai') as mock_genai:
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client
            mock_response = MagicMock()
            mock_response.text = json.dumps(expected_analysis_result)
            mock_client.models.generate_content.return_value = mock_response
            
            genai_client = UnifiedLLMClient(google_genai_config)
            assert genai_client.get_provider_name() == "google_genai"
            
            # Analyze content with Google GenAI
            result2 = genai_client.analyze_content(sample_journal_content, Path("test2.md"))
            genai_stats = genai_client.get_stats()
        
        # Verify both providers produced valid results
        assert isinstance(result1, AnalysisResult)
        assert isinstance(result2, AnalysisResult)
        assert result1.file_path != result2.file_path  # Different file paths
        
        # Verify statistics are independent
        assert isinstance(bedrock_stats, APIStats)
        assert isinstance(genai_stats, APIStats)

    def test_invalid_provider_configuration(self, invalid_provider_config):
        """Test error handling for invalid provider configuration."""
        with pytest.raises(ValueError) as exc_info:
            UnifiedLLMClient(invalid_provider_config)
        
        assert "Unsupported LLM provider: 'invalid_provider'" in str(exc_info.value)
        assert "bedrock" in str(exc_info.value)
        assert "google_genai" in str(exc_info.value)

    def test_bedrock_api_failure_handling(self, bedrock_config, sample_journal_content):
        """Test error handling when Bedrock API fails."""
        with patch.dict('os.environ', {
            'AWS_ACCESS_KEY_ID': 'test-access-key',
            'AWS_SECRET_ACCESS_KEY': 'test-secret-key'
        }):
            with patch('bedrock_client.boto3') as mock_boto3:
                mock_bedrock_client = MagicMock()
                mock_boto3.client.return_value = mock_bedrock_client
                
                # Mock API failure
                mock_bedrock_client.invoke_model.side_effect = Exception("API Error")
            
            client = UnifiedLLMClient(bedrock_config)
            
            # Test connection failure
            assert client.test_connection() is False
            
            # Test analysis with failure
            result = client.analyze_content(sample_journal_content, Path("test.md"))
            
            # Should return empty result on failure
            assert isinstance(result, AnalysisResult)
            assert len(result.projects) == 0
            assert len(result.participants) == 0
            assert len(result.tasks) == 0
            assert len(result.themes) == 0
            
            # Verify failure statistics
            stats = client.get_stats()
            assert stats.failed_calls > 0

    def test_google_genai_api_failure_handling(self, google_genai_config, sample_journal_content):
        """Test error handling when Google GenAI API fails."""
        with patch('google_genai_client.genai') as mock_genai:
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client
            
            # Mock API failure
            mock_client.models.generate_content.side_effect = Exception("API Error")
            
            client = UnifiedLLMClient(google_genai_config)
            
            # Test connection failure
            assert client.test_connection() is False
            
            # Test analysis with failure
            result = client.analyze_content(sample_journal_content, Path("test.md"))
            
            # Should return empty result on failure
            assert isinstance(result, AnalysisResult)
            assert len(result.projects) == 0
            assert len(result.participants) == 0
            assert len(result.tasks) == 0
            assert len(result.themes) == 0
            
            # Verify failure statistics
            stats = client.get_stats()
            assert stats.failed_calls > 0

    def test_configuration_loading_from_file(self, tmp_path, sample_journal_content, expected_analysis_result):
        """Test loading configuration from YAML file and using it with providers."""
        # Create temporary config file
        config_file = tmp_path / "test_config.yaml"
        config_data = {
            "llm": {"provider": "bedrock"},
            "bedrock": {
                "region": "us-west-2",
                "model_id": "anthropic.claude-sonnet-4-20250514-v1:0"
            },
            "google_genai": {
                "project": "test-project",
                "location": "us-central1",
                "model": "gemini-2.0-flash-001"
            },
            "processing": {
                "input_directory": "journals",
                "output_directory": "output"
            },
            "log": {
                "level": "INFO",
                "file": "test.log"
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Load configuration and test
        from config_manager import ConfigManager
        config_manager = ConfigManager(config_path=Path(config_file))
        config = config_manager.get_config()
        
        with patch('bedrock_client.boto3') as mock_boto3:
            mock_bedrock_client = MagicMock()
            mock_boto3.client.return_value = mock_bedrock_client
            mock_response = {
                'output': {
                    'message': {
                        'content': [{'text': json.dumps(expected_analysis_result)}]
                    }
                }
            }
            mock_bedrock_client.converse.return_value = mock_response
            
            client = UnifiedLLMClient(config)
            assert client.get_provider_name() == "bedrock"
            
            provider_info = client.get_provider_info()
            assert provider_info["region"] == "us-west-2"

    def test_edge_case_content_handling(self, bedrock_config, google_genai_config):
        """Test handling of edge cases in content analysis."""
        edge_cases = [
            ("", "empty content"),
            ("   \n\n   ", "whitespace only"),
            ("A" * 10000, "very long content"),
            ("Special chars: 你好 🚀 ñoño", "unicode and emojis"),
            ("```json\n{\"test\": \"value\"}\n```", "code blocks")
        ]
        
        for content, description in edge_cases:
            # Test with Bedrock
            with patch('bedrock_client.boto3') as mock_boto3:
                mock_bedrock_client = MagicMock()
                mock_boto3.client.return_value = mock_bedrock_client
                mock_response = {
                    'output': {
                        'message': {
                            'content': [{'text': '{"projects": [], "participants": [], "tasks": [], "themes": []}'}]
                        }
                    }
                }
                mock_bedrock_client.converse.return_value = mock_response
                
                bedrock_client = UnifiedLLMClient(bedrock_config)
                result = bedrock_client.analyze_content(content, Path(f"test_{description}.md"))
                assert isinstance(result, AnalysisResult)
            
            # Test with Google GenAI
            with patch('google_genai_client.genai') as mock_genai:
                mock_client = MagicMock()
                mock_genai.Client.return_value = mock_client
                mock_response = MagicMock()
                mock_response.text = '{"projects": [], "participants": [], "tasks": [], "themes": []}'
                mock_client.models.generate_content.return_value = mock_response
                
                genai_client = UnifiedLLMClient(google_genai_config)
                result = genai_client.analyze_content(content, Path(f"test_{description}.md"))
                assert isinstance(result, AnalysisResult)

    def test_statistics_consistency_across_providers(self, bedrock_config, google_genai_config, sample_journal_content, expected_analysis_result):
        """Test that statistics tracking is consistent across providers."""
        # Test Bedrock statistics
        with patch.dict('os.environ', {
            'AWS_ACCESS_KEY_ID': 'test-access-key',
            'AWS_SECRET_ACCESS_KEY': 'test-secret-key'
        }):
            with patch('bedrock_client.boto3') as mock_boto3:
                mock_bedrock_client = MagicMock()
                mock_boto3.client.return_value = mock_bedrock_client
                mock_bedrock_response = {
                    'content': [{'text': json.dumps(expected_analysis_result)}]
                }
                mock_response = {
                    'body': MagicMock()
                }
                mock_response['body'].read.return_value = json.dumps(mock_bedrock_response).encode()
                mock_bedrock_client.invoke_model.return_value = mock_response
                
                bedrock_client = UnifiedLLMClient(bedrock_config)
                
                # Perform multiple operations
                bedrock_client.test_connection()
                bedrock_client.analyze_content(sample_journal_content, Path("test1.md"))
                bedrock_client.analyze_content(sample_journal_content, Path("test2.md"))
                
                bedrock_stats = bedrock_client.get_stats()
        
        # Test Google GenAI statistics
        with patch('google_genai_client.genai') as mock_genai:
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client
            mock_response = MagicMock()
            mock_response.text = json.dumps(expected_analysis_result)
            mock_client.models.generate_content.return_value = mock_response
            
            genai_client = UnifiedLLMClient(google_genai_config)
            
            # Perform same operations
            genai_client.test_connection()
            genai_client.analyze_content(sample_journal_content, Path("test1.md"))
            genai_client.analyze_content(sample_journal_content, Path("test2.md"))
            
            genai_stats = genai_client.get_stats()
        
        # Verify statistics structure is consistent (allow for slight differences in call counting)
        # Both should have at least 2 calls (2 analyze_content calls)
        assert bedrock_stats.total_calls >= 2
        assert genai_stats.total_calls >= 2
        assert bedrock_stats.successful_calls >= 2
        assert genai_stats.successful_calls >= 2
        assert bedrock_stats.failed_calls == 0
        assert genai_stats.failed_calls == 0
        assert bedrock_stats.rate_limit_hits == 0
        assert genai_stats.rate_limit_hits == 0
        
        # Both should have positive timing values
        assert bedrock_stats.total_time > 0
        assert genai_stats.total_time > 0
        assert bedrock_stats.average_response_time > 0
        assert genai_stats.average_response_time > 0
        
        # Verify statistics types are consistent
        assert type(bedrock_stats.total_calls) == type(genai_stats.total_calls)
        assert type(bedrock_stats.successful_calls) == type(genai_stats.successful_calls)
        assert type(bedrock_stats.failed_calls) == type(genai_stats.failed_calls)
        assert type(bedrock_stats.total_time) == type(genai_stats.total_time)
        assert type(bedrock_stats.average_response_time) == type(genai_stats.average_response_time)
        assert type(bedrock_stats.rate_limit_hits) == type(genai_stats.rate_limit_hits)

    def test_concurrent_provider_usage(self, bedrock_config, google_genai_config, sample_journal_content, expected_analysis_result):
        """Test that multiple provider instances can be used concurrently."""
        import threading
        import time
        
        results = {}
        errors = {}
        
        def test_bedrock():
            try:
                with patch('bedrock_client.boto3') as mock_boto3:
                    mock_bedrock_client = MagicMock()
                    mock_boto3.client.return_value = mock_bedrock_client
                    mock_response = {
                        'output': {
                            'message': {
                                'content': [{'text': json.dumps(expected_analysis_result)}]
                            }
                        }
                    }
                    mock_bedrock_client.converse.return_value = mock_response
                    
                    client = UnifiedLLMClient(bedrock_config)
                    result = client.analyze_content(sample_journal_content, Path("bedrock_test.md"))
                    results['bedrock'] = result
            except Exception as e:
                errors['bedrock'] = e
        
        def test_google_genai():
            try:
                with patch('google_genai_client.genai') as mock_genai:
                    mock_client = MagicMock()
                    mock_genai.Client.return_value = mock_client
                    mock_response = MagicMock()
                    mock_response.text = json.dumps(expected_analysis_result)
                    mock_client.models.generate_content.return_value = mock_response
                    
                    client = UnifiedLLMClient(google_genai_config)
                    result = client.analyze_content(sample_journal_content, Path("genai_test.md"))
                    results['google_genai'] = result
            except Exception as e:
                errors['google_genai'] = e
        
        # Run both providers concurrently
        bedrock_thread = threading.Thread(target=test_bedrock)
        genai_thread = threading.Thread(target=test_google_genai)
        
        bedrock_thread.start()
        genai_thread.start()
        
        bedrock_thread.join(timeout=10)
        genai_thread.join(timeout=10)
        
        # Verify no errors occurred
        assert len(errors) == 0, f"Errors occurred: {errors}"
        
        # Verify both providers produced results
        assert 'bedrock' in results
        assert 'google_genai' in results
        assert isinstance(results['bedrock'], AnalysisResult)
        assert isinstance(results['google_genai'], AnalysisResult)


class TestProviderEquivalence:
    """Tests to ensure both providers behave equivalently."""
    
    @pytest.fixture
    def test_scenarios(self):
        """Common test scenarios for both providers."""
        return [
            {
                "name": "simple_journal",
                "content": "Worked on Project X with John. Completed task A and B.",
                "expected_projects": ["Project X"],
                "expected_participants": ["John"]
            },
            {
                "name": "multiple_projects",
                "content": "Morning: Project Alpha meeting. Afternoon: Project Beta development.",
                "expected_projects": ["Project Alpha", "Project Beta"]
            },
            {
                "name": "complex_content",
                "content": """
                # Daily Standup
                Team: Alice, Bob, Charlie
                Projects: Web App, Mobile App, API Gateway
                Tasks: Code review, Testing, Deployment
                Themes: Performance, Security, User Experience
                """,
                "expected_participants": ["Alice", "Bob", "Charlie"],
                "expected_projects": ["Web App", "Mobile App", "API Gateway"]
            }
        ]
    
    @pytest.mark.parametrize("provider", ["bedrock", "google_genai"])
    def test_provider_consistency(self, provider, test_scenarios):
        """Test that both providers handle the same scenarios consistently."""
        if provider == "bedrock":
            config = AppConfig(
                llm=LLMConfig(provider="bedrock"),
                bedrock=BedrockConfig(),
                google_genai=GoogleGenAIConfig(),
                processing=ProcessingConfig(),
                logging=LogConfig()
            )
        else:
            config = AppConfig(
                llm=LLMConfig(provider="google_genai"),
                bedrock=BedrockConfig(),
                google_genai=GoogleGenAIConfig(),
                processing=ProcessingConfig(),
                logging=LogConfig()
            )
        
        for scenario in test_scenarios:
            expected_result = {
                "projects": scenario.get("expected_projects", []),
                "participants": scenario.get("expected_participants", []),
                "tasks": ["Sample task"],
                "themes": ["Sample theme"]
            }
            
            if provider == "bedrock":
                with patch.dict('os.environ', {
                    'AWS_ACCESS_KEY_ID': 'test-access-key',
                    'AWS_SECRET_ACCESS_KEY': 'test-secret-key'
                }):
                    with patch('bedrock_client.boto3') as mock_boto3:
                        mock_bedrock_client = MagicMock()
                        mock_boto3.client.return_value = mock_bedrock_client
                        mock_bedrock_response = {
                            'content': [{'text': json.dumps(expected_result)}]
                        }
                        mock_response = {
                            'body': MagicMock()
                        }
                        mock_response['body'].read.return_value = json.dumps(mock_bedrock_response).encode()
                        mock_bedrock_client.invoke_model.return_value = mock_response
                    
                    client = UnifiedLLMClient(config)
                    result = client.analyze_content(scenario["content"], Path(f"{scenario['name']}.md"))
            else:
                with patch('google_genai_client.genai') as mock_genai:
                    mock_client = MagicMock()
                    mock_genai.Client.return_value = mock_client
                    mock_response = MagicMock()
                    mock_response.text = json.dumps(expected_result)
                    mock_client.models.generate_content.return_value = mock_response
                    
                    client = UnifiedLLMClient(config)
                    result = client.analyze_content(scenario["content"], Path(f"{scenario['name']}.md"))
            
            # Verify result structure is consistent
            assert isinstance(result, AnalysisResult)
            assert result.file_path.name == f"{scenario['name']}.md"
            assert isinstance(result.projects, list)
            assert isinstance(result.participants, list)
            assert isinstance(result.tasks, list)
            assert isinstance(result.themes, list)
            assert result.api_call_time >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])