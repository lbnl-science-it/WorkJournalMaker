#!/usr/bin/env python3
"""
Tests for UnifiedLLMClient - Multi-Provider LLM Interface

This module contains comprehensive tests for the UnifiedLLMClient class,
ensuring it correctly delegates to the appropriate underlying provider
and handles all error scenarios properly.

Author: Work Journal Summarizer Project
Version: Multi-Provider Support
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from config_manager import AppConfig, BedrockConfig, GoogleGenAIConfig, LLMConfig
from unified_llm_client import UnifiedLLMClient
from llm_data_structures import AnalysisResult, APIStats


class TestUnifiedLLMClient:
    """Test suite for UnifiedLLMClient functionality."""
    
    @pytest.fixture
    def bedrock_config(self):
        """Create a test configuration with bedrock provider."""
        return AppConfig(
            llm=LLMConfig(provider="bedrock"),
            bedrock=BedrockConfig(region="us-east-1", model_id="test-model"),
            google_genai=GoogleGenAIConfig()
        )
    
    @pytest.fixture
    def google_genai_config(self):
        """Create a test configuration with google_genai provider."""
        return AppConfig(
            llm=LLMConfig(provider="google_genai"),
            bedrock=BedrockConfig(),
            google_genai=GoogleGenAIConfig(project="test-project", model="test-model")
        )
    
    @pytest.fixture
    def invalid_config(self):
        """Create a test configuration with invalid provider."""
        return AppConfig(
            llm=LLMConfig(provider="invalid_provider"),
            bedrock=BedrockConfig(),
            google_genai=GoogleGenAIConfig()
        )
    
    @pytest.fixture
    def mock_analysis_result(self):
        """Create a mock AnalysisResult for testing."""
        return AnalysisResult(
            file_path=Path("test.md"),
            projects=["Test Project"],
            participants=["John Doe"],
            tasks=["Testing"],
            themes=["Development"],
            api_call_time=1.5,
            confidence_score=0.9,
            raw_response='{"test": "response"}'
        )
    
    @pytest.fixture
    def mock_api_stats(self):
        """Create a mock APIStats for testing."""
        return APIStats(
            total_calls=10,
            successful_calls=9,
            failed_calls=1,
            total_time=15.0,
            average_response_time=1.67,
            rate_limit_hits=0
        )
    
    @patch('unified_llm_client.BedrockClient')
    def test_init_with_bedrock_provider(self, mock_bedrock_client, bedrock_config):
        """Test initialization with bedrock provider."""
        mock_client_instance = Mock()
        mock_bedrock_client.return_value = mock_client_instance
        
        unified_client = UnifiedLLMClient(bedrock_config)
        
        # Verify bedrock client was created with correct config
        mock_bedrock_client.assert_called_once_with(bedrock_config.bedrock)
        assert unified_client.provider_name == "bedrock"
        assert unified_client.client == mock_client_instance
    
    @patch('unified_llm_client.GoogleGenAIClient')
    def test_init_with_google_genai_provider(self, mock_google_client, google_genai_config):
        """Test initialization with google_genai provider."""
        mock_client_instance = Mock()
        mock_google_client.return_value = mock_client_instance
        
        unified_client = UnifiedLLMClient(google_genai_config)
        
        # Verify google genai client was created with correct config
        mock_google_client.assert_called_once_with(google_genai_config.google_genai)
        assert unified_client.provider_name == "google_genai"
        assert unified_client.client == mock_client_instance
    
    def test_init_with_invalid_provider(self, invalid_config):
        """Test initialization with invalid provider raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            UnifiedLLMClient(invalid_config)
        
        assert "Unsupported LLM provider: 'invalid_provider'" in str(exc_info.value)
        assert "Supported providers: ['bedrock', 'google_genai']" in str(exc_info.value)
    
    @patch('unified_llm_client.BedrockClient')
    def test_init_with_client_creation_failure(self, mock_bedrock_client, bedrock_config):
        """Test initialization when underlying client creation fails."""
        mock_bedrock_client.side_effect = Exception("Client creation failed")
        
        with pytest.raises(Exception) as exc_info:
            UnifiedLLMClient(bedrock_config)
        
        assert "Client creation failed" in str(exc_info.value)
    
    @patch('unified_llm_client.BedrockClient')
    def test_analyze_content_delegation(self, mock_bedrock_client, bedrock_config, mock_analysis_result):
        """Test that analyze_content properly delegates to underlying client."""
        mock_client_instance = Mock()
        mock_client_instance.analyze_content.return_value = mock_analysis_result
        mock_bedrock_client.return_value = mock_client_instance
        
        unified_client = UnifiedLLMClient(bedrock_config)
        result = unified_client.analyze_content("test content", Path("test.md"))
        
        # Verify delegation
        mock_client_instance.analyze_content.assert_called_once_with("test content", Path("test.md"))
        assert result == mock_analysis_result
    
    @patch('unified_llm_client.GoogleGenAIClient')
    def test_analyze_content_with_google_genai(self, mock_google_client, google_genai_config, mock_analysis_result):
        """Test analyze_content with google_genai provider."""
        mock_client_instance = Mock()
        mock_client_instance.analyze_content.return_value = mock_analysis_result
        mock_google_client.return_value = mock_client_instance
        
        unified_client = UnifiedLLMClient(google_genai_config)
        result = unified_client.analyze_content("test content", Path("test.md"))
        
        # Verify delegation
        mock_client_instance.analyze_content.assert_called_once_with("test content", Path("test.md"))
        assert result == mock_analysis_result
    
    @patch('unified_llm_client.BedrockClient')
    def test_get_stats_delegation(self, mock_bedrock_client, bedrock_config, mock_api_stats):
        """Test that get_stats properly delegates to underlying client."""
        mock_client_instance = Mock()
        mock_client_instance.get_stats.return_value = mock_api_stats
        mock_bedrock_client.return_value = mock_client_instance
        
        unified_client = UnifiedLLMClient(bedrock_config)
        result = unified_client.get_stats()
        
        # Verify delegation
        mock_client_instance.get_stats.assert_called_once()
        assert result == mock_api_stats
    
    @patch('unified_llm_client.BedrockClient')
    def test_reset_stats_delegation(self, mock_bedrock_client, bedrock_config):
        """Test that reset_stats properly delegates to underlying client."""
        mock_client_instance = Mock()
        mock_bedrock_client.return_value = mock_client_instance
        
        unified_client = UnifiedLLMClient(bedrock_config)
        unified_client.reset_stats()
        
        # Verify delegation
        mock_client_instance.reset_stats.assert_called_once()
    
    @patch('unified_llm_client.BedrockClient')
    def test_test_connection_success(self, mock_bedrock_client, bedrock_config):
        """Test successful connection test."""
        mock_client_instance = Mock()
        mock_client_instance.test_connection.return_value = True
        mock_bedrock_client.return_value = mock_client_instance
        
        unified_client = UnifiedLLMClient(bedrock_config)
        result = unified_client.test_connection()
        
        # Verify delegation and result
        mock_client_instance.test_connection.assert_called_once()
        assert result is True
    
    @patch('unified_llm_client.BedrockClient')
    def test_test_connection_failure(self, mock_bedrock_client, bedrock_config):
        """Test failed connection test."""
        mock_client_instance = Mock()
        mock_client_instance.test_connection.return_value = False
        mock_bedrock_client.return_value = mock_client_instance
        
        unified_client = UnifiedLLMClient(bedrock_config)
        result = unified_client.test_connection()
        
        # Verify delegation and result
        mock_client_instance.test_connection.assert_called_once()
        assert result is False
    
    @patch('unified_llm_client.BedrockClient')
    def test_test_connection_exception_handling(self, mock_bedrock_client, bedrock_config):
        """Test connection test with exception handling."""
        mock_client_instance = Mock()
        mock_client_instance.test_connection.side_effect = Exception("Connection error")
        mock_bedrock_client.return_value = mock_client_instance
        
        unified_client = UnifiedLLMClient(bedrock_config)
        result = unified_client.test_connection()
        
        # Verify exception is caught and False is returned
        mock_client_instance.test_connection.assert_called_once()
        assert result is False
    
    @patch('unified_llm_client.BedrockClient')
    def test_get_provider_name_bedrock(self, mock_bedrock_client, bedrock_config):
        """Test get_provider_name returns correct provider name for bedrock."""
        mock_bedrock_client.return_value = Mock()
        
        unified_client = UnifiedLLMClient(bedrock_config)
        assert unified_client.get_provider_name() == "bedrock"
    
    @patch('unified_llm_client.GoogleGenAIClient')
    def test_get_provider_name_google_genai(self, mock_google_client, google_genai_config):
        """Test get_provider_name returns correct provider name for google_genai."""
        mock_google_client.return_value = Mock()
        
        unified_client = UnifiedLLMClient(google_genai_config)
        assert unified_client.get_provider_name() == "google_genai"
    
    @patch('unified_llm_client.BedrockClient')
    def test_get_provider_info_bedrock(self, mock_bedrock_client, bedrock_config):
        """Test get_provider_info delegates to underlying bedrock client."""
        mock_client_instance = Mock()
        expected_info = {
            "provider": "bedrock",
            "region": "us-east-1",
            "model_id": "test-model"
        }
        mock_client_instance.get_provider_info.return_value = expected_info
        mock_bedrock_client.return_value = mock_client_instance
        
        unified_client = UnifiedLLMClient(bedrock_config)
        info = unified_client.get_provider_info()
        
        assert info == expected_info
        mock_client_instance.get_provider_info.assert_called_once()
    
    @patch('unified_llm_client.GoogleGenAIClient')
    def test_get_provider_info_google_genai(self, mock_google_client, google_genai_config):
        """Test get_provider_info delegates to underlying google_genai client."""
        mock_client_instance = Mock()
        expected_info = {
            "provider": "google_genai",
            "project": "test-project",
            "location": "us-central1",
            "model": "test-model"
        }
        mock_client_instance.get_provider_info.return_value = expected_info
        mock_google_client.return_value = mock_client_instance
        
        unified_client = UnifiedLLMClient(google_genai_config)
        info = unified_client.get_provider_info()
        
        assert info == expected_info
        mock_client_instance.get_provider_info.assert_called_once()
    
    @patch('unified_llm_client.BedrockClient')
    def test_error_propagation_from_underlying_client(self, mock_bedrock_client, bedrock_config):
        """Test that errors from underlying client are properly propagated."""
        mock_client_instance = Mock()
        mock_client_instance.analyze_content.side_effect = Exception("API Error")
        mock_bedrock_client.return_value = mock_client_instance
        
        unified_client = UnifiedLLMClient(bedrock_config)
        
        with pytest.raises(Exception) as exc_info:
            unified_client.analyze_content("test content", Path("test.md"))
        
        assert "API Error" in str(exc_info.value)
    
    @patch('unified_llm_client.GoogleGenAIClient')
    @patch('unified_llm_client.BedrockClient')
    def test_provider_switching_by_configuration(self, mock_bedrock_client, mock_google_client):
        """Test that different configurations create different provider clients."""
        mock_bedrock_instance = Mock()
        mock_google_instance = Mock()
        mock_bedrock_client.return_value = mock_bedrock_instance
        mock_google_client.return_value = mock_google_instance
        
        # Create bedrock client
        bedrock_config = AppConfig(llm=LLMConfig(provider="bedrock"))
        bedrock_unified = UnifiedLLMClient(bedrock_config)
        
        # Create google_genai client
        google_config = AppConfig(llm=LLMConfig(provider="google_genai"))
        google_unified = UnifiedLLMClient(google_config)
        
        # Verify correct clients were created
        assert bedrock_unified.provider_name == "bedrock"
        assert google_unified.provider_name == "google_genai"
        assert bedrock_unified.client == mock_bedrock_instance
        assert google_unified.client == mock_google_instance
    
    @patch('unified_llm_client.BedrockClient')
    def test_logging_during_operations(self, mock_bedrock_client, bedrock_config, caplog):
        """Test that appropriate logging occurs during operations."""
        mock_client_instance = Mock()
        mock_client_instance.test_connection.return_value = True
        mock_bedrock_client.return_value = mock_client_instance
        
        with caplog.at_level("INFO"):
            unified_client = UnifiedLLMClient(bedrock_config)
            unified_client.test_connection()
        
        # Check that initialization and connection test are logged
        assert "UnifiedLLMClient initialized with provider: bedrock" in caplog.text
        assert "Connection test successful for bedrock" in caplog.text


if __name__ == "__main__":
    pytest.main([__file__])