#!/usr/bin/env python3
"""
Tests for Bedrock Client - Phase 8: Configuration Management & API Fallback

This module contains comprehensive tests for the BedrockClient class,
including API integration, error handling, retry logic, and configuration management.

Author: Work Journal Summarizer Project
Version: Phase 8 - Configuration Management & API Fallback
"""

import pytest
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

from bedrock_client import BedrockClient, AnalysisResult, APIStats
from config_manager import BedrockConfig


class TestBedrockClient:
    """Test cases for BedrockClient class."""
    
    @pytest.fixture
    def bedrock_config(self):
        """Create a test Bedrock configuration."""
        return BedrockConfig(
            region="us-east-1",
            model_id="test-model",
            timeout=30,
            max_retries=2,
            rate_limit_delay=0.1
        )
    
    @pytest.fixture
    def mock_bedrock_response(self):
        """Create a mock Bedrock API response."""
        return {
            'content': [{
                'text': json.dumps({
                    'projects': ['Project Alpha', 'Beta Initiative'],
                    'participants': ['John Doe', 'Jane Smith'],
                    'tasks': ['Code review', 'Documentation update'],
                    'themes': ['Development', 'Quality Assurance']
                })
            }]
        }
    
    @patch.dict('os.environ', {
        'AWS_ACCESS_KEY_ID': 'test-access-key',
        'AWS_SECRET_ACCESS_KEY': 'test-secret-key'
    })
    @patch('boto3.client')
    def test_successful_client_creation(self, mock_boto, bedrock_config):
        """Test successful creation of Bedrock client."""
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        
        bedrock_client = BedrockClient(bedrock_config)
        
        assert bedrock_client.config == bedrock_config
        assert bedrock_client.client == mock_client
        mock_boto.assert_called_once_with(
            'bedrock-runtime',
            region_name='us-east-1',
            aws_access_key_id='test-access-key',
            aws_secret_access_key='test-secret-key'
        )
    
    @patch.dict('os.environ', {}, clear=True)
    def test_missing_credentials_error(self, bedrock_config):
        """Test error handling when AWS credentials are missing."""
        with pytest.raises(ValueError, match="AWS credentials not found"):
            BedrockClient(bedrock_config)
    
    @patch.dict('os.environ', {
        'AWS_ACCESS_KEY_ID': 'test-access-key'
        # Missing AWS_SECRET_ACCESS_KEY
    }, clear=True)
    def test_missing_secret_key_error(self, bedrock_config):
        """Test error handling when AWS secret key is missing."""
        with pytest.raises(ValueError, match="AWS credentials not found"):
            BedrockClient(bedrock_config)
    
    @patch.dict('os.environ', {
        'AWS_ACCESS_KEY_ID': 'test-access-key',
        'AWS_SECRET_ACCESS_KEY': 'test-secret-key'
    })
    @patch('boto3.client')
    def test_successful_content_analysis(self, mock_boto, bedrock_config, mock_bedrock_response):
        """Test successful content analysis."""
        mock_client = MagicMock()
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = json.dumps(mock_bedrock_response).encode()
        mock_client.invoke_model.return_value = mock_response
        mock_boto.return_value = mock_client
        
        bedrock_client = BedrockClient(bedrock_config)
        
        test_content = "Today I worked on Project Alpha with John Doe. We completed code review tasks."
        test_path = Path("/test/file.txt")
        
        result = bedrock_client.analyze_content(test_content, test_path)
        
        assert isinstance(result, AnalysisResult)
        assert result.file_path == test_path
        assert 'Project Alpha' in result.projects
        assert 'John Doe' in result.participants
        assert 'Code review' in result.tasks
        assert 'Development' in result.themes
        assert result.api_call_time > 0
    
    @patch.dict('os.environ', {
        'AWS_ACCESS_KEY_ID': 'test-access-key',
        'AWS_SECRET_ACCESS_KEY': 'test-secret-key'
    })
    @patch('boto3.client')
    def test_api_call_failure(self, mock_boto, bedrock_config):
        """Test handling of API call failures."""
        mock_client = MagicMock()
        mock_client.invoke_model.side_effect = Exception("API Error")
        mock_boto.return_value = mock_client
        
        bedrock_client = BedrockClient(bedrock_config)
        
        test_content = "Test content"
        test_path = Path("/test/file.txt")
        
        result = bedrock_client.analyze_content(test_content, test_path)
        
        # Should return empty result on failure
        assert isinstance(result, AnalysisResult)
        assert result.file_path == test_path
        assert result.projects == []
        assert result.participants == []
        assert result.tasks == []
        assert result.themes == []
        assert "ERROR:" in result.raw_response
    
    @patch.dict('os.environ', {
        'AWS_ACCESS_KEY_ID': 'test-access-key',
        'AWS_SECRET_ACCESS_KEY': 'test-secret-key'
    })
    @patch('boto3.client')
    def test_rate_limiting_retry(self, mock_boto, bedrock_config):
        """Test retry logic for rate limiting."""
        from botocore.exceptions import ClientError
        
        mock_client = MagicMock()
        
        # First call fails with throttling, second succeeds
        throttling_error = ClientError(
            error_response={'Error': {'Code': 'ThrottlingException'}},
            operation_name='InvokeModel'
        )
        
        mock_response = {
            'body': MagicMock()
        }
        mock_bedrock_response = {
            'content': [{'text': '{"projects": [], "participants": [], "tasks": [], "themes": []}'}]
        }
        mock_response['body'].read.return_value = json.dumps(mock_bedrock_response).encode()
        
        mock_client.invoke_model.side_effect = [throttling_error, mock_response]
        mock_boto.return_value = mock_client
        
        bedrock_client = BedrockClient(bedrock_config)
        
        with patch('time.sleep') as mock_sleep:
            result = bedrock_client.analyze_content("test content", Path("/test/file.txt"))
            
            # Should have retried and succeeded
            assert isinstance(result, AnalysisResult)
            assert bedrock_client.stats.rate_limit_hits == 1
            assert bedrock_client.stats.successful_calls == 1
            mock_sleep.assert_called_once()
    
    @patch.dict('os.environ', {
        'AWS_ACCESS_KEY_ID': 'test-access-key',
        'AWS_SECRET_ACCESS_KEY': 'test-secret-key'
    })
    @patch('boto3.client')
    def test_max_retries_exceeded(self, mock_boto, bedrock_config):
        """Test behavior when max retries are exceeded."""
        from botocore.exceptions import ClientError
        
        mock_client = MagicMock()
        throttling_error = ClientError(
            error_response={'Error': {'Code': 'ThrottlingException'}},
            operation_name='InvokeModel'
        )
        mock_client.invoke_model.side_effect = throttling_error
        mock_boto.return_value = mock_client
        
        bedrock_client = BedrockClient(bedrock_config)
        
        with patch('time.sleep'):
            result = bedrock_client.analyze_content("test content", Path("/test/file.txt"))
            
            # Should return empty result after max retries
            assert isinstance(result, AnalysisResult)
            assert result.projects == []
            assert bedrock_client.stats.failed_calls == 1
            assert bedrock_client.stats.rate_limit_hits == bedrock_config.max_retries + 1
    
    @patch.dict('os.environ', {
        'AWS_ACCESS_KEY_ID': 'test-access-key',
        'AWS_SECRET_ACCESS_KEY': 'test-secret-key'
    })
    @patch('boto3.client')
    def test_malformed_response_handling(self, mock_boto, bedrock_config):
        """Test handling of malformed API responses."""
        mock_client = MagicMock()
        mock_response = {
            'body': MagicMock()
        }
        # Invalid JSON response
        mock_response['body'].read.return_value = b'{"invalid": json}'
        mock_client.invoke_model.return_value = mock_response
        mock_boto.return_value = mock_client
        
        bedrock_client = BedrockClient(bedrock_config)
        
        result = bedrock_client.analyze_content("test content", Path("/test/file.txt"))
        
        # Should handle malformed response gracefully
        assert isinstance(result, AnalysisResult)
        assert result.projects == []
        assert result.participants == []
        assert result.tasks == []
        assert result.themes == []
    
    def test_entity_deduplication(self, bedrock_config):
        """Test entity deduplication functionality."""
        with patch.dict('os.environ', {
            'AWS_ACCESS_KEY_ID': 'test-access-key',
            'AWS_SECRET_ACCESS_KEY': 'test-secret-key'
        }):
            with patch('boto3.client'):
                bedrock_client = BedrockClient(bedrock_config)
                
                entities = {
                    'projects': ['Project Alpha', 'project alpha', 'PROJECT ALPHA', 'Beta Project'],
                    'participants': ['John Doe', 'john doe', 'Jane Smith'],
                    'tasks': ['Code Review', 'code review', 'Testing'],
                    'themes': ['Development', 'development', 'QA']
                }
                
                deduplicated = bedrock_client._deduplicate_entities(entities)
                
                # Should remove case-insensitive duplicates
                assert len(deduplicated['projects']) == 2  # Alpha and Beta
                assert len(deduplicated['participants']) == 2  # John and Jane
                assert len(deduplicated['tasks']) == 2  # Review and Testing
                assert len(deduplicated['themes']) == 2  # Development and QA
    
    def test_json_extraction_from_markdown(self, bedrock_config):
        """Test JSON extraction from markdown-formatted text."""
        with patch.dict('os.environ', {
            'AWS_ACCESS_KEY_ID': 'test-access-key',
            'AWS_SECRET_ACCESS_KEY': 'test-secret-key'
        }):
            with patch('boto3.client'):
                bedrock_client = BedrockClient(bedrock_config)
                
                # Test JSON in markdown code block
                markdown_text = '''Here is the analysis:
```json
{"projects": ["Test Project"], "participants": ["Test User"], "tasks": [], "themes": []}
```
End of analysis.'''
                
                extracted_json = bedrock_client._extract_json_from_text(markdown_text)
                parsed = json.loads(extracted_json)
                
                assert parsed['projects'] == ['Test Project']
                assert parsed['participants'] == ['Test User']
    
    def test_content_truncation(self, bedrock_config):
        """Test content truncation for long inputs."""
        with patch.dict('os.environ', {
            'AWS_ACCESS_KEY_ID': 'test-access-key',
            'AWS_SECRET_ACCESS_KEY': 'test-secret-key'
        }):
            with patch('boto3.client'):
                bedrock_client = BedrockClient(bedrock_config)
                
                # Create very long content
                long_content = "A" * 10000
                
                prompt = bedrock_client._create_analysis_prompt(long_content)
                
                # Should be truncated
                assert len(prompt) < len(bedrock_client.ANALYSIS_PROMPT) + 10000
                assert "[Content truncated for analysis]" in prompt
    
    @patch.dict('os.environ', {
        'AWS_ACCESS_KEY_ID': 'test-access-key',
        'AWS_SECRET_ACCESS_KEY': 'test-secret-key'
    })
    @patch('boto3.client')
    def test_api_statistics_tracking(self, mock_boto, bedrock_config, mock_bedrock_response):
        """Test API statistics tracking."""
        mock_client = MagicMock()
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = json.dumps(mock_bedrock_response).encode()
        mock_client.invoke_model.return_value = mock_response
        mock_boto.return_value = mock_client
        
        bedrock_client = BedrockClient(bedrock_config)
        
        # Make multiple API calls
        for i in range(3):
            bedrock_client.analyze_content(f"test content {i}", Path(f"/test/file{i}.txt"))
        
        stats = bedrock_client.get_stats()
        
        assert stats.total_calls == 3
        assert stats.successful_calls == 3
        assert stats.failed_calls == 0
        assert stats.total_time > 0
        assert stats.average_response_time > 0
    
    @patch.dict('os.environ', {
        'AWS_ACCESS_KEY_ID': 'test-access-key',
        'AWS_SECRET_ACCESS_KEY': 'test-secret-key'
    })
    @patch('boto3.client')
    def test_connection_test(self, mock_boto, bedrock_config):
        """Test connection testing functionality."""
        mock_client = MagicMock()
        mock_response = {
            'body': MagicMock()
        }
        mock_response['body'].read.return_value = b'{"test": "success"}'
        mock_client.invoke_model.return_value = mock_response
        mock_boto.return_value = mock_client
        
        bedrock_client = BedrockClient(bedrock_config)
        
        # Test successful connection
        assert bedrock_client.test_connection() == True
        
        # Test failed connection
        mock_client.invoke_model.side_effect = Exception("Connection failed")
        assert bedrock_client.test_connection() == False
    
    def test_stats_reset(self, bedrock_config):
        """Test statistics reset functionality."""
        with patch.dict('os.environ', {
            'AWS_ACCESS_KEY_ID': 'test-access-key',
            'AWS_SECRET_ACCESS_KEY': 'test-secret-key'
        }):
            with patch('boto3.client'):
                bedrock_client = BedrockClient(bedrock_config)
                
                # Manually set some stats
                bedrock_client.stats.total_calls = 5
                bedrock_client.stats.successful_calls = 3
                bedrock_client.stats.failed_calls = 2
                
                # Reset stats
                bedrock_client.reset_stats()
                
                stats = bedrock_client.get_stats()
                assert stats.total_calls == 0
                assert stats.successful_calls == 0
                assert stats.failed_calls == 0
                assert stats.total_time == 0.0
    
    def test_request_formatting(self, bedrock_config):
        """Test Bedrock request formatting."""
        with patch.dict('os.environ', {
            'AWS_ACCESS_KEY_ID': 'test-access-key',
            'AWS_SECRET_ACCESS_KEY': 'test-secret-key'
        }):
            with patch('boto3.client'):
                bedrock_client = BedrockClient(bedrock_config)
                
                test_prompt = "Test prompt"
                request_body = bedrock_client._format_bedrock_request(test_prompt)
                
                assert request_body['anthropic_version'] == "bedrock-2023-05-31"
                assert request_body['max_tokens'] == 1000
                assert len(request_body['messages']) == 1
                assert request_body['messages'][0]['role'] == 'user'
                assert request_body['messages'][0]['content'] == test_prompt
                assert request_body['temperature'] == 0.1
                assert request_body['top_p'] == 0.9
    
    def test_get_provider_info(self, bedrock_config):
        """Test get_provider_info returns correct bedrock-specific information."""
        with patch.dict('os.environ', {
            'AWS_ACCESS_KEY_ID': 'test-access-key',
            'AWS_SECRET_ACCESS_KEY': 'test-secret-key'
        }):
            with patch('boto3.client'):
                bedrock_client = BedrockClient(bedrock_config)
                
                provider_info = bedrock_client.get_provider_info()
                
                expected_info = {
                    "provider": "bedrock",
                    "region": bedrock_config.region,
                    "model_id": bedrock_config.model_id
                }
                
                assert provider_info == expected_info
                assert provider_info["provider"] == "bedrock"
                assert provider_info["region"] == bedrock_config.region
                assert provider_info["model_id"] == bedrock_config.model_id


if __name__ == '__main__':
    pytest.main([__file__])