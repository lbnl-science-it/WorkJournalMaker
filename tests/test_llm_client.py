#!/usr/bin/env python3
"""
Test suite for LLM Client - Phase 4: LLM API Integration

Comprehensive tests for AWS Bedrock Claude integration with entity extraction,
error handling, retry logic, and response parsing.

Author: Work Journal Summarizer Project
Version: Phase 4 - LLM API Integration Tests
"""

import pytest
from unittest.mock import patch, MagicMock, call
import json
import time
from pathlib import Path
from botocore.exceptions import ClientError, BotoCoreError

from llm_client import LLMClient, AnalysisResult, APIStats


class TestLLMClient:
    """Test suite for LLMClient class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_content = """
        Today I worked on the DataPipeline project with Sarah and Mike.
        We completed the ETL optimization task and started planning
        the database migration. The main theme was performance improvement.
        """
        
        self.test_file_path = Path("/test/worklog_2024-04-01.txt")
        
        # Mock successful Bedrock response
        self.mock_bedrock_response = {
            'content': [{
                'text': json.dumps({
                    'projects': ['DataPipeline', 'Database Migration'],
                    'participants': ['Sarah', 'Mike'],
                    'tasks': ['ETL optimization', 'database migration planning'],
                    'themes': ['performance improvement']
                })
            }]
        }
        
        # Mock API response body
        self.mock_response_body = MagicMock()
        self.mock_response_body.read.return_value = json.dumps(self.mock_bedrock_response).encode()
    
    @patch.dict('os.environ', {
        'AWS_ACCESS_KEY_ID': 'test-key',
        'AWS_SECRET_ACCESS_KEY': 'test-secret'
    })
    @patch('boto3.client')
    def test_successful_api_call(self, mock_boto):
        """Test successful Bedrock API response parsing."""
        # Setup mock client
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        mock_client.invoke_model.return_value = {
            'body': self.mock_response_body
        }
        
        # Create client and analyze content
        client = LLMClient()
        result = client.analyze_content(self.test_content, self.test_file_path)
        
        # Verify result structure
        assert isinstance(result, AnalysisResult)
        assert result.file_path == self.test_file_path
        assert result.projects == ['DataPipeline', 'Database Migration']
        assert result.participants == ['Sarah', 'Mike']
        assert result.tasks == ['ETL optimization', 'database migration planning']
        assert result.themes == ['performance improvement']
        assert result.api_call_time > 0
        assert result.raw_response is not None
        
        # Verify API call was made correctly
        mock_client.invoke_model.assert_called_once()
        call_args = mock_client.invoke_model.call_args
        assert call_args[1]['modelId'] == "anthropic.claude-3-sonnet-20240229-v1:0"
        assert call_args[1]['contentType'] == 'application/json'
        assert call_args[1]['accept'] == 'application/json'
        
        # Verify request body structure
        request_body = json.loads(call_args[1]['body'])
        assert 'messages' in request_body
        assert request_body['messages'][0]['role'] == 'user'
        assert 'anthropic_version' in request_body
        assert 'max_tokens' in request_body
        
        # Verify stats tracking
        stats = client.get_stats()
        assert stats.total_calls == 1
        assert stats.successful_calls == 1
        assert stats.failed_calls == 0
    
    @patch.dict('os.environ', {
        'AWS_ACCESS_KEY_ID': 'test-key',
        'AWS_SECRET_ACCESS_KEY': 'test-secret'
    })
    @patch('boto3.client')
    def test_api_timeout_handling(self, mock_boto):
        """Test timeout and retry logic with Bedrock."""
        # Setup mock client that fails then succeeds
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        
        # First call raises BotoCoreError, second succeeds
        mock_client.invoke_model.side_effect = [
            BotoCoreError(),
            {'body': self.mock_response_body}
        ]
        
        # Create client and analyze content
        client = LLMClient()
        with patch('time.sleep') as mock_sleep:  # Speed up test
            result = client.analyze_content(self.test_content, self.test_file_path)
        
        # Verify retry occurred
        assert mock_client.invoke_model.call_count == 2
        mock_sleep.assert_called_once_with(2)  # First retry delay
        
        # Verify successful result after retry
        assert isinstance(result, AnalysisResult)
        assert len(result.projects) > 0
        
        # Verify stats
        stats = client.get_stats()
        assert stats.total_calls == 1
        assert stats.successful_calls == 1
    
    @patch.dict('os.environ', {
        'AWS_ACCESS_KEY_ID': 'test-key',
        'AWS_SECRET_ACCESS_KEY': 'test-secret'
    })
    @patch('boto3.client')
    def test_malformed_response_handling(self, mock_boto):
        """Test handling of invalid Bedrock responses."""
        # Setup mock client with malformed response
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        
        malformed_response_body = MagicMock()
        malformed_response_body.read.return_value = json.dumps({
            'content': [{'text': 'Invalid JSON response'}]
        }).encode()
        
        mock_client.invoke_model.return_value = {
            'body': malformed_response_body
        }
        
        # Create client and analyze content
        client = LLMClient()
        result = client.analyze_content(self.test_content, self.test_file_path)
        
        # Should return empty result structure on parse failure
        assert isinstance(result, AnalysisResult)
        assert result.projects == []
        assert result.participants == []
        assert result.tasks == []
        assert result.themes == []
        assert "ERROR" not in result.raw_response  # Parse error, not API error
        
        # Stats should show successful API call but parsing handled gracefully
        stats = client.get_stats()
        assert stats.total_calls == 1
        assert stats.successful_calls == 1
    
    def test_entity_deduplication(self):
        """Test removal of duplicate entities."""
        client = LLMClient.__new__(LLMClient)  # Create without __init__
        
        # Test data with duplicates
        entities = {
            'projects': ['Project A', 'project a', 'Project B', 'Project A'],
            'participants': ['John Doe', 'john doe', 'Jane Smith', ''],
            'tasks': ['Task 1', 'Task 1', 'Task 2', None],
            'themes': ['Theme A', 'theme a', 'Theme B']
        }
        
        result = client._deduplicate_entities(entities)
        
        # Verify deduplication (case-insensitive)
        assert len(result['projects']) == 2
        assert 'Project A' in result['projects']
        assert 'Project B' in result['projects']
        
        assert len(result['participants']) == 2
        assert 'John Doe' in result['participants']
        assert 'Jane Smith' in result['participants']
        
        assert len(result['tasks']) == 2
        assert 'Task 1' in result['tasks']
        assert 'Task 2' in result['tasks']
        
        assert len(result['themes']) == 2
        assert 'Theme A' in result['themes']
        assert 'Theme B' in result['themes']
    
    def test_prompt_generation(self):
        """Test prompt template formatting for Claude."""
        client = LLMClient.__new__(LLMClient)  # Create without __init__
        
        test_content = "Sample journal content"
        prompt = client._create_analysis_prompt(test_content)
        
        # Verify prompt contains required elements
        assert "JOURNAL CONTENT:" in prompt
        assert test_content in prompt
        assert "projects" in prompt
        assert "participants" in prompt
        assert "tasks" in prompt
        assert "themes" in prompt
        assert "JSON" in prompt
        
        # Test content truncation
        long_content = "x" * 10000
        long_prompt = client._create_analysis_prompt(long_content)
        assert "[Content truncated for analysis]" in long_prompt
        assert len(long_prompt) < len(long_content) + 1000  # Should be truncated
    
    @patch.dict('os.environ', {
        'AWS_ACCESS_KEY_ID': 'test-key',
        'AWS_SECRET_ACCESS_KEY': 'test-secret'
    })
    @patch('boto3.client')
    def test_bedrock_rate_limiting(self, mock_boto):
        """Test Bedrock rate limiting and backoff."""
        # Setup mock client that hits rate limit then succeeds
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        
        # Create throttling exception
        throttling_error = ClientError(
            error_response={'Error': {'Code': 'ThrottlingException'}},
            operation_name='InvokeModel'
        )
        
        mock_client.invoke_model.side_effect = [
            throttling_error,
            {'body': self.mock_response_body}
        ]
        
        # Create client and analyze content
        client = LLMClient()
        with patch('time.sleep') as mock_sleep:  # Speed up test
            result = client.analyze_content(self.test_content, self.test_file_path)
        
        # Verify retry occurred with backoff
        assert mock_client.invoke_model.call_count == 2
        mock_sleep.assert_called_once_with(2)  # Exponential backoff: 2^0 + 1
        
        # Verify rate limit tracking
        stats = client.get_stats()
        assert stats.rate_limit_hits == 1
        assert stats.successful_calls == 1
    
    @patch.dict('os.environ', {})  # Empty environment
    def test_aws_credential_handling(self):
        """Test AWS credential validation and error handling."""
        # Should raise ValueError when credentials are missing
        with pytest.raises(ValueError, match="AWS credentials not found"):
            LLMClient()
    
    @patch.dict('os.environ', {
        'AWS_ACCESS_KEY_ID': 'test-key',
        'AWS_SECRET_ACCESS_KEY': 'test-secret'
    })
    @patch('boto3.client')
    def test_json_extraction_from_markdown(self, mock_boto):
        """Test extraction of JSON from markdown code blocks."""
        client = LLMClient.__new__(LLMClient)  # Create without __init__
        
        # Test JSON in markdown code block
        markdown_text = """
        Here's the analysis:
        ```json
        {"projects": ["Test Project"], "participants": ["John"]}
        ```
        """
        
        json_text = client._extract_json_from_text(markdown_text)
        parsed = json.loads(json_text)
        assert parsed['projects'] == ['Test Project']
        assert parsed['participants'] == ['John']
        
        # Test JSON without markdown
        plain_json = '{"projects": ["Direct JSON"], "participants": []}'
        extracted = client._extract_json_from_text(plain_json)
        assert extracted == plain_json
        
        # Test no JSON found
        no_json_text = "This is just plain text"
        result = client._extract_json_from_text(no_json_text)
        assert result == no_json_text
    
    @patch.dict('os.environ', {
        'AWS_ACCESS_KEY_ID': 'test-key',
        'AWS_SECRET_ACCESS_KEY': 'test-secret'
    })
    @patch('boto3.client')
    def test_api_failure_handling(self, mock_boto):
        """Test handling of complete API failures."""
        # Setup mock client that always fails
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        mock_client.invoke_model.side_effect = Exception("API Error")
        
        # Create client and analyze content
        client = LLMClient()
        result = client.analyze_content(self.test_content, self.test_file_path)
        
        # Should return empty result on complete failure
        assert isinstance(result, AnalysisResult)
        assert result.projects == []
        assert result.participants == []
        assert result.tasks == []
        assert result.themes == []
        assert "ERROR: API Error" in result.raw_response
        
        # Verify stats tracking
        stats = client.get_stats()
        assert stats.total_calls == 1
        assert stats.successful_calls == 0
        assert stats.failed_calls == 1
    
    def test_stats_reset(self):
        """Test statistics reset functionality."""
        client = LLMClient.__new__(LLMClient)  # Create without __init__
        client.stats = APIStats(5, 3, 2, 10.0, 2.0, 1)
        
        # Reset stats
        client.reset_stats()
        
        # Verify all stats are reset
        stats = client.get_stats()
        assert stats.total_calls == 0
        assert stats.successful_calls == 0
        assert stats.failed_calls == 0
        assert stats.total_time == 0.0
        assert stats.average_response_time == 0.0
        assert stats.rate_limit_hits == 0
    
    @patch.dict('os.environ', {
        'AWS_ACCESS_KEY_ID': 'test-key',
        'AWS_SECRET_ACCESS_KEY': 'test-secret'
    })
    @patch('boto3.client')
    def test_request_format_validation(self, mock_boto):
        """Test that request format matches Bedrock Messages API specification."""
        # Setup mock client
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        mock_client.invoke_model.return_value = {
            'body': self.mock_response_body
        }
        
        # Create client and analyze content
        client = LLMClient()
        client.analyze_content(self.test_content, self.test_file_path)
        
        # Verify request format
        call_args = mock_client.invoke_model.call_args
        request_body = json.loads(call_args[1]['body'])
        
        # Check required fields for Messages API
        assert 'anthropic_version' in request_body
        assert request_body['anthropic_version'] == 'bedrock-2023-05-31'
        assert 'max_tokens' in request_body
        assert 'messages' in request_body
        assert isinstance(request_body['messages'], list)
        assert len(request_body['messages']) == 1
        
        # Check message format
        message = request_body['messages'][0]
        assert 'role' in message
        assert message['role'] == 'user'
        assert 'content' in message
        assert isinstance(message['content'], str)
        
        # Check optional parameters
        assert 'temperature' in request_body
        assert 'top_p' in request_body
        assert request_body['temperature'] == 0.1
        assert request_body['top_p'] == 0.9


class TestAnalysisResult:
    """Test suite for AnalysisResult dataclass."""
    
    def test_analysis_result_creation(self):
        """Test AnalysisResult creation and field access."""
        file_path = Path("/test/file.txt")
        result = AnalysisResult(
            file_path=file_path,
            projects=['Project A'],
            participants=['John'],
            tasks=['Task 1'],
            themes=['Theme A'],
            api_call_time=1.5,
            confidence_score=0.9,
            raw_response='{"test": "data"}'
        )
        
        assert result.file_path == file_path
        assert result.projects == ['Project A']
        assert result.participants == ['John']
        assert result.tasks == ['Task 1']
        assert result.themes == ['Theme A']
        assert result.api_call_time == 1.5
        assert result.confidence_score == 0.9
        assert result.raw_response == '{"test": "data"}'


class TestAPIStats:
    """Test suite for APIStats dataclass."""
    
    def test_api_stats_creation(self):
        """Test APIStats creation and field access."""
        stats = APIStats(
            total_calls=10,
            successful_calls=8,
            failed_calls=2,
            total_time=15.5,
            average_response_time=1.94,
            rate_limit_hits=1
        )
        
        assert stats.total_calls == 10
        assert stats.successful_calls == 8
        assert stats.failed_calls == 2
        assert stats.total_time == 15.5
        assert stats.average_response_time == 1.94
        assert stats.rate_limit_hits == 1