#!/usr/bin/env python3
"""
Tests for Google GenAI Client Error Handling and Retry Logic

This module contains comprehensive tests for the error handling and retry logic
implemented in GoogleGenAIClient, following Step 6 of the implementation blueprint.
"""

import pytest
import time
from unittest.mock import MagicMock, patch
from pathlib import Path

from google_genai_client import GoogleGenAIClient
from config_manager import GoogleGenAIConfig
from llm_data_structures import AnalysisResult, APIStats


class TestGoogleGenAIRetryLogic:
    """Test suite for Google GenAI client retry logic and error handling."""
    
    @pytest.fixture
    def google_genai_config(self):
        """Provide test configuration for Google GenAI."""
        return GoogleGenAIConfig(
            project="test-project-123",
            location="us-central1",
            model="gemini-2.0-flash-001"
        )
    
    @pytest.fixture
    def mock_rate_limit_error(self):
        """Mock rate limiting error."""
        error = Exception("Rate limit exceeded - too many requests")
        return error
    
    @pytest.fixture
    def mock_auth_error(self):
        """Mock authentication error."""
        error = Exception("Authentication failed - invalid credentials")
        return error
    
    @pytest.fixture
    def mock_network_error(self):
        """Mock network error."""
        error = ConnectionError("Network connection failed")
        return error
    
    @pytest.fixture
    def mock_timeout_error(self):
        """Mock timeout error."""
        error = TimeoutError("Request timed out")
        return error
    
    @pytest.fixture
    def mock_invalid_request_error(self):
        """Mock invalid request error."""
        error = Exception("Invalid request - bad parameter")
        return error
    
    @patch('google_genai_client.genai')
    def test_retry_logic_with_rate_limiting(self, mock_genai, google_genai_config, mock_rate_limit_error):
        """Test retry logic with rate limiting scenarios."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        genai_client = GoogleGenAIClient(google_genai_config)
        
        # Mock successful response after retries
        mock_response = MagicMock()
        mock_response.text = "Success after retries"
        
        # First two calls fail with rate limit, third succeeds
        mock_client.models.generate_content.side_effect = [
            mock_rate_limit_error,
            mock_rate_limit_error,
            mock_response
        ]
        
        start_time = time.time()
        result = genai_client._make_api_call_with_retry("test prompt", max_retries=3)
        end_time = time.time()
        
        # Should succeed after retries
        assert result == "Success after retries"
        
        # Should have taken some time due to backoff
        assert end_time - start_time >= 1.0  # At least 1 second for backoff
        
        # Should track rate limit hits
        stats = genai_client.get_stats()
        assert stats.rate_limit_hits == 2
    
    @patch('google_genai_client.genai')
    def test_retry_logic_exhausted_with_rate_limiting(self, mock_genai, google_genai_config, mock_rate_limit_error):
        """Test retry logic when all retries are exhausted with rate limiting."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        genai_client = GoogleGenAIClient(google_genai_config)
        
        # All calls fail with rate limit
        mock_client.models.generate_content.side_effect = mock_rate_limit_error
        
        with pytest.raises(Exception, match="Rate limit exceeded"):
            genai_client._make_api_call_with_retry("test prompt", max_retries=2)
        
        # Should track rate limit hits
        stats = genai_client.get_stats()
        assert stats.rate_limit_hits == 3  # max_retries + 1
    
    @patch('google_genai_client.genai')
    def test_authentication_error_no_retry(self, mock_genai, google_genai_config, mock_auth_error):
        """Test that authentication errors are not retried."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        genai_client = GoogleGenAIClient(google_genai_config)
        
        # Authentication error should not be retried
        mock_client.models.generate_content.side_effect = mock_auth_error
        
        start_time = time.time()
        with pytest.raises(Exception, match="Authentication failed"):
            genai_client._make_api_call_with_retry("test prompt", max_retries=3)
        end_time = time.time()
        
        # Should fail immediately without retries
        assert end_time - start_time < 0.5  # Should be very fast
        
        # Should only be called once (no retries)
        assert mock_client.models.generate_content.call_count == 1
    
    @patch('google_genai_client.genai')
    def test_network_error_with_retry(self, mock_genai, google_genai_config, mock_network_error):
        """Test that network errors are retried with exponential backoff."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        genai_client = GoogleGenAIClient(google_genai_config)
        
        # Mock successful response after network errors
        mock_response = MagicMock()
        mock_response.text = "Success after network retry"
        
        # First call fails with network error, second succeeds
        mock_client.models.generate_content.side_effect = [
            mock_network_error,
            mock_response
        ]
        
        start_time = time.time()
        result = genai_client._make_api_call_with_retry("test prompt", max_retries=2)
        end_time = time.time()
        
        # Should succeed after retry
        assert result == "Success after network retry"
        
        # Should have taken some time due to backoff
        assert end_time - start_time >= 1.0  # At least 1 second for backoff
        
        # Should be called twice (original + 1 retry)
        assert mock_client.models.generate_content.call_count == 2
    
    @patch('google_genai_client.genai')
    def test_invalid_request_error_no_retry(self, mock_genai, google_genai_config, mock_invalid_request_error):
        """Test that invalid request errors are not retried."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        genai_client = GoogleGenAIClient(google_genai_config)
        
        # Invalid request error should not be retried
        mock_client.models.generate_content.side_effect = mock_invalid_request_error
        
        start_time = time.time()
        with pytest.raises(Exception, match="Invalid request"):
            genai_client._make_api_call_with_retry("test prompt", max_retries=3)
        end_time = time.time()
        
        # Should fail immediately without retries
        assert end_time - start_time < 0.5  # Should be very fast
        
        # Should only be called once (no retries)
        assert mock_client.models.generate_content.call_count == 1
    
    @patch('google_genai_client.genai')
    def test_timeout_error_with_retry(self, mock_genai, google_genai_config, mock_timeout_error):
        """Test that timeout errors are retried."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        genai_client = GoogleGenAIClient(google_genai_config)
        
        # Mock successful response after timeout
        mock_response = MagicMock()
        mock_response.text = "Success after timeout retry"
        
        # First call times out, second succeeds
        mock_client.models.generate_content.side_effect = [
            mock_timeout_error,
            mock_response
        ]
        
        result = genai_client._make_api_call_with_retry("test prompt", max_retries=2)
        
        # Should succeed after retry
        assert result == "Success after timeout retry"
        
        # Should be called twice (original + 1 retry)
        assert mock_client.models.generate_content.call_count == 2
    
    @patch('google_genai_client.genai')
    @patch('google_genai_client.time.sleep')  # Mock sleep to speed up tests
    def test_exponential_backoff_timing(self, mock_sleep, mock_genai, google_genai_config):
        """Test that exponential backoff timing is correct."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        genai_client = GoogleGenAIClient(google_genai_config)
        
        # Mock rate limiting error for all attempts
        rate_limit_error = Exception("Rate limit exceeded")
        mock_client.models.generate_content.side_effect = rate_limit_error
        
        with pytest.raises(Exception):
            genai_client._make_api_call_with_retry("test prompt", max_retries=3)
        
        # Check that sleep was called with exponential backoff
        sleep_calls = mock_sleep.call_args_list
        assert len(sleep_calls) == 3  # Should sleep 3 times for 3 retries
        
        # Check that sleep times follow exponential pattern (with jitter)
        for i, call in enumerate(sleep_calls):
            sleep_time = call[0][0]  # First argument to sleep()
            expected_base = 2 ** i
            # Should be at least the base time, but less than base + 2 (due to jitter)
            assert expected_base <= sleep_time < expected_base + 2
    
    @patch('google_genai_client.genai')
    def test_analyze_content_error_handling_with_retry(self, mock_genai, google_genai_config):
        """Test analyze_content error handling with retry logic."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        genai_client = GoogleGenAIClient(google_genai_config)
        
        # Mock rate limiting error followed by success
        rate_limit_error = Exception("Rate limit exceeded")
        mock_response = MagicMock()
        mock_response.text = '{"projects": ["TestProject"], "participants": [], "tasks": [], "themes": []}'
        
        mock_client.models.generate_content.side_effect = [
            rate_limit_error,
            mock_response
        ]
        
        result = genai_client.analyze_content("test content", Path("/test/file.txt"))
        
        # Should succeed after retry
        assert isinstance(result, AnalysisResult)
        assert result.projects == ["TestProject"]
        assert result.api_call_time > 0
        
        # Should track statistics correctly
        stats = genai_client.get_stats()
        assert stats.total_calls == 1
        assert stats.successful_calls == 1
        assert stats.failed_calls == 0
        assert stats.rate_limit_hits == 1
    
    @patch('google_genai_client.genai')
    def test_analyze_content_failed_requests_statistics(self, mock_genai, google_genai_config):
        """Test that failed requests still update statistics correctly."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        genai_client = GoogleGenAIClient(google_genai_config)
        
        # Mock authentication error (should not retry)
        auth_error = Exception("Authentication failed")
        mock_client.models.generate_content.side_effect = auth_error
        
        result = genai_client.analyze_content("test content", Path("/test/file.txt"))
        
        # Should return empty result
        assert isinstance(result, AnalysisResult)
        assert result.projects == []
        assert result.participants == []
        assert result.tasks == []
        assert result.themes == []
        assert "ERROR (Exception): Authentication failed" in result.raw_response
        assert result.api_call_time > 0
        
        # Should track statistics correctly
        stats = genai_client.get_stats()
        assert stats.total_calls == 1
        assert stats.successful_calls == 0
        assert stats.failed_calls == 1
        assert stats.total_time > 0
        assert stats.average_response_time > 0
    
    @patch('google_genai_client.genai')
    def test_connection_test_with_retry_logic(self, mock_genai, google_genai_config):
        """Test connection testing uses retry logic."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        genai_client = GoogleGenAIClient(google_genai_config)
        
        # Mock network error followed by success
        network_error = ConnectionError("Network connection failed")
        mock_response = MagicMock()
        mock_response.text = '{"test": "success"}'
        
        mock_client.models.generate_content.side_effect = [
            network_error,
            mock_response
        ]
        
        result = genai_client.test_connection()
        
        # Should succeed after retry
        assert result == True
        
        # Should be called twice (original + 1 retry, max_retries=1 for connection test)
        assert mock_client.models.generate_content.call_count == 2
    
    @patch('google_genai_client.genai')
    def test_connection_test_failure_scenarios(self, mock_genai, google_genai_config):
        """Test connection test handles different failure scenarios correctly."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        genai_client = GoogleGenAIClient(google_genai_config)
        
        # Test different error types
        error_scenarios = [
            Exception("Authentication failed - invalid credentials"),
            Exception("Invalid request - bad parameter"),
            ConnectionError("Network connection failed"),
            Exception("Rate limit exceeded")
        ]
        
        for error in error_scenarios:
            # Reset for each test
            mock_client.reset_mock()
            mock_client.models.generate_content.side_effect = error
            
            result = genai_client.test_connection()
            
            # Should return False for all error types
            assert result == False
    
    def test_error_classification_methods(self, google_genai_config):
        """Test error classification methods work correctly."""
        with patch('google_genai_client.genai'):
            genai_client = GoogleGenAIClient(google_genai_config)
            
            # Test rate limit error detection
            rate_limit_errors = [
                Exception("Rate limit exceeded"),
                Exception("Quota exceeded"),
                Exception("Too many requests"),
                Exception("Resource exhausted"),
                Exception("HTTP 429 error")
            ]
            
            for error in rate_limit_errors:
                assert genai_client._is_rate_limit_error(error) == True
            
            # Test authentication error detection
            auth_errors = [
                Exception("Authentication failed"),
                Exception("Unauthorized access"),
                Exception("Permission denied"),
                Exception("Invalid credentials"),
                Exception("HTTP 401 error"),
                Exception("HTTP 403 error")
            ]
            
            for error in auth_errors:
                assert genai_client._is_authentication_error(error) == True
            
            # Test network error detection
            network_errors = [
                ConnectionError("Connection failed"),
                Exception("Network timeout"),
                Exception("DNS resolution failed"),
                Exception("SSL certificate error")
            ]
            
            for error in network_errors:
                assert genai_client._is_network_error(error) == True
            
            # Test invalid request error detection
            invalid_request_errors = [
                Exception("Invalid request"),
                Exception("Bad request"),
                Exception("Malformed input"),
                Exception("Invalid parameter"),
                Exception("HTTP 400 error")
            ]
            
            for error in invalid_request_errors:
                assert genai_client._is_invalid_request_error(error) == True
            
            # Test timeout error detection
            timeout_errors = [
                TimeoutError("Request timed out"),
                Exception("Deadline exceeded"),
                Exception("Connection timeout")
            ]
            
            for error in timeout_errors:
                assert genai_client._is_timeout_error(error) == True
    
    @patch('google_genai_client.genai')
    def test_graceful_degradation_all_retries_exhausted(self, mock_genai, google_genai_config):
        """Test graceful degradation when all retries are exhausted."""
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        
        genai_client = GoogleGenAIClient(google_genai_config)
        
        # Mock persistent network error
        network_error = ConnectionError("Persistent network failure")
        mock_client.models.generate_content.side_effect = network_error
        
        result = genai_client.analyze_content("test content", Path("/test/file.txt"))
        
        # Should return empty result gracefully
        assert isinstance(result, AnalysisResult)
        assert result.projects == []
        assert result.participants == []
        assert result.tasks == []
        assert result.themes == []
        assert "ERROR (ConnectionError): Persistent network failure" in result.raw_response
        assert result.api_call_time > 0
        
        # Should track as failed call
        stats = genai_client.get_stats()
        assert stats.total_calls == 1
        assert stats.successful_calls == 0
        assert stats.failed_calls == 1