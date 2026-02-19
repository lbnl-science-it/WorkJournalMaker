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

from config_manager import AppConfig, BedrockConfig, GoogleGenAIConfig, CBORGConfig, LLMConfig
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
        assert "Supported providers: ['bedrock', 'google_genai', 'cborg']" in str(exc_info.value)
    
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


class TestUnifiedLLMClientFallback:
    """Test suite for provider fallback chain behavior."""

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
            raw_response='{"test": "response"}'
        )

    @pytest.fixture
    def fallback_config(self):
        """Config with google_genai primary, bedrock and cborg fallbacks."""
        return AppConfig(
            llm=LLMConfig(
                provider="google_genai",
                fallback_providers=["bedrock", "cborg"]
            ),
            bedrock=BedrockConfig(region="us-east-1", model_id="test-model"),
            google_genai=GoogleGenAIConfig(project="test-project", model="test-model"),
            cborg=CBORGConfig()
        )

    @pytest.fixture
    def no_fallback_config(self):
        """Config with no fallback providers."""
        return AppConfig(
            llm=LLMConfig(provider="google_genai", fallback_providers=[]),
            google_genai=GoogleGenAIConfig(project="test-project", model="test-model"),
        )

    @patch('unified_llm_client.GoogleGenAIClient')
    def test_primary_succeeds_no_fallback_triggered(
        self, mock_google_client, fallback_config, mock_analysis_result
    ):
        """When the primary provider succeeds, no fallback should be attempted."""
        mock_primary = Mock()
        mock_primary.analyze_content.return_value = mock_analysis_result
        mock_google_client.return_value = mock_primary
        callback = Mock()

        client = UnifiedLLMClient(fallback_config, on_fallback=callback)
        result = client.analyze_content("test content", Path("test.md"))

        assert result == mock_analysis_result
        callback.assert_not_called()

    @patch('unified_llm_client.BedrockClient')
    @patch('unified_llm_client.GoogleGenAIClient')
    def test_primary_fails_secondary_succeeds(
        self, mock_google_client, mock_bedrock_client,
        fallback_config, mock_analysis_result
    ):
        """When primary fails, fallback to secondary with notification."""
        mock_primary = Mock()
        mock_primary.analyze_content.side_effect = Exception("Google API down")
        mock_google_client.return_value = mock_primary

        mock_secondary = Mock()
        mock_secondary.analyze_content.return_value = mock_analysis_result
        mock_bedrock_client.return_value = mock_secondary

        callback = Mock()
        client = UnifiedLLMClient(fallback_config, on_fallback=callback)
        result = client.analyze_content("test content", Path("test.md"))

        assert result == mock_analysis_result
        callback.assert_called_once()
        msg = callback.call_args[0][0]
        assert "google_genai" in msg
        assert "bedrock" in msg

    @patch('unified_llm_client.CBORGClient')
    @patch('unified_llm_client.BedrockClient')
    @patch('unified_llm_client.GoogleGenAIClient')
    def test_primary_and_secondary_fail_tertiary_succeeds(
        self, mock_google_client, mock_bedrock_client, mock_cborg_client,
        fallback_config, mock_analysis_result
    ):
        """When primary and secondary fail, fallback to tertiary."""
        mock_primary = Mock()
        mock_primary.analyze_content.side_effect = Exception("Google down")
        mock_google_client.return_value = mock_primary

        mock_secondary = Mock()
        mock_secondary.analyze_content.side_effect = Exception("Bedrock down")
        mock_bedrock_client.return_value = mock_secondary

        mock_tertiary = Mock()
        mock_tertiary.analyze_content.return_value = mock_analysis_result
        mock_cborg_client.return_value = mock_tertiary

        callback = Mock()
        client = UnifiedLLMClient(fallback_config, on_fallback=callback)
        result = client.analyze_content("test content", Path("test.md"))

        assert result == mock_analysis_result
        assert callback.call_count == 2

    @patch('unified_llm_client.CBORGClient')
    @patch('unified_llm_client.BedrockClient')
    @patch('unified_llm_client.GoogleGenAIClient')
    def test_all_providers_fail_raises_last_exception(
        self, mock_google_client, mock_bedrock_client, mock_cborg_client,
        fallback_config
    ):
        """When all providers fail, the last exception is raised."""
        mock_primary = Mock()
        mock_primary.analyze_content.side_effect = Exception("Google down")
        mock_google_client.return_value = mock_primary

        mock_secondary = Mock()
        mock_secondary.analyze_content.side_effect = Exception("Bedrock down")
        mock_bedrock_client.return_value = mock_secondary

        mock_tertiary = Mock()
        mock_tertiary.analyze_content.side_effect = Exception("CBORG down")
        mock_cborg_client.return_value = mock_tertiary

        callback = Mock()
        client = UnifiedLLMClient(fallback_config, on_fallback=callback)

        with pytest.raises(Exception, match="CBORG down"):
            client.analyze_content("test content", Path("test.md"))

    @patch('unified_llm_client.BedrockClient')
    @patch('unified_llm_client.GoogleGenAIClient')
    def test_notification_callback_message_format(
        self, mock_google_client, mock_bedrock_client,
        fallback_config, mock_analysis_result
    ):
        """Notification callback receives a message with provider names and error."""
        mock_primary = Mock()
        mock_primary.analyze_content.side_effect = Exception("API quota exceeded")
        mock_google_client.return_value = mock_primary

        mock_secondary = Mock()
        mock_secondary.analyze_content.return_value = mock_analysis_result
        mock_bedrock_client.return_value = mock_secondary

        callback = Mock()
        client = UnifiedLLMClient(fallback_config, on_fallback=callback)
        client.analyze_content("test content", Path("test.md"))

        msg = callback.call_args[0][0]
        assert "google_genai" in msg
        assert "API quota exceeded" in msg
        assert "bedrock" in msg

    @patch('unified_llm_client.GoogleGenAIClient')
    def test_lazy_initialization_fallback_not_created_at_startup(
        self, mock_google_client, fallback_config, mock_analysis_result
    ):
        """Fallback clients should NOT be created during __init__."""
        mock_primary = Mock()
        mock_primary.analyze_content.return_value = mock_analysis_result
        mock_google_client.return_value = mock_primary

        with patch('unified_llm_client.BedrockClient') as mock_bedrock, \
             patch('unified_llm_client.CBORGClient') as mock_cborg:
            client = UnifiedLLMClient(fallback_config)

            # Fallback clients not instantiated at init time
            mock_bedrock.assert_not_called()
            mock_cborg.assert_not_called()

            # Primary succeeds — still no fallback creation
            client.analyze_content("test content", Path("test.md"))
            mock_bedrock.assert_not_called()
            mock_cborg.assert_not_called()

    @patch('unified_llm_client.BedrockClient')
    @patch('unified_llm_client.GoogleGenAIClient')
    def test_lazy_initialization_fallback_created_on_failure(
        self, mock_google_client, mock_bedrock_client,
        fallback_config, mock_analysis_result
    ):
        """Fallback client should be created only when primary fails."""
        mock_primary = Mock()
        mock_primary.analyze_content.side_effect = Exception("Google down")
        mock_google_client.return_value = mock_primary

        mock_secondary = Mock()
        mock_secondary.analyze_content.return_value = mock_analysis_result
        mock_bedrock_client.return_value = mock_secondary

        client = UnifiedLLMClient(fallback_config)

        # Before analyze, bedrock not created
        mock_bedrock_client.assert_not_called()

        client.analyze_content("test content", Path("test.md"))

        # Now bedrock was created
        mock_bedrock_client.assert_called_once()

    @patch('unified_llm_client.GoogleGenAIClient')
    def test_get_provider_info_reports_fallback_chain(
        self, mock_google_client, fallback_config
    ):
        """get_provider_info should report active provider and fallback list."""
        mock_primary = Mock()
        mock_primary.get_provider_info.return_value = {
            "provider": "google_genai",
            "project": "test-project",
            "model": "test-model"
        }
        mock_google_client.return_value = mock_primary

        client = UnifiedLLMClient(fallback_config)
        info = client.get_provider_info()

        assert info["active_provider"] == "google_genai"
        assert info["fallback_providers"] == ["bedrock", "cborg"]

    @patch('unified_llm_client.GoogleGenAIClient')
    def test_no_fallback_config_error_propagates(
        self, mock_google_client, no_fallback_config
    ):
        """With no fallback providers, errors from the primary should propagate."""
        mock_primary = Mock()
        mock_primary.analyze_content.side_effect = Exception("Google down")
        mock_google_client.return_value = mock_primary

        client = UnifiedLLMClient(no_fallback_config)

        with pytest.raises(Exception, match="Google down"):
            client.analyze_content("test content", Path("test.md"))

    @patch('unified_llm_client.GoogleGenAIClient')
    def test_default_callback_uses_logging(self, mock_google_client, fallback_config, caplog):
        """Without an on_fallback callback, fallback notification goes to logging.warning."""
        mock_primary = Mock()
        mock_primary.analyze_content.side_effect = Exception("Google down")
        mock_google_client.return_value = mock_primary

        with patch('unified_llm_client.BedrockClient') as mock_bedrock:
            mock_secondary = Mock()
            mock_secondary.analyze_content.return_value = AnalysisResult(
                file_path=Path("test.md"),
                projects=[], participants=[], tasks=[], themes=[],
                api_call_time=0.5, raw_response="{}"
            )
            mock_bedrock.return_value = mock_secondary

            client = UnifiedLLMClient(fallback_config)

            with caplog.at_level("WARNING"):
                client.analyze_content("test content", Path("test.md"))

            # Default callback uses logging.warning, producing a WARNING-level record
            fallback_messages = [
                r for r in caplog.records
                if "Falling back to" in r.message and r.levelname == "WARNING"
            ]
            assert len(fallback_messages) >= 1

    @patch('unified_llm_client.BedrockClient')
    @patch('unified_llm_client.GoogleGenAIClient')
    def test_active_provider_updates_after_fallback(
        self, mock_google_client, mock_bedrock_client,
        fallback_config, mock_analysis_result
    ):
        """After a successful fallback, active_provider_name should update."""
        mock_primary = Mock()
        mock_primary.analyze_content.side_effect = Exception("Google down")
        mock_google_client.return_value = mock_primary

        mock_secondary = Mock()
        mock_secondary.analyze_content.return_value = mock_analysis_result
        mock_bedrock_client.return_value = mock_secondary

        client = UnifiedLLMClient(fallback_config)
        assert client.active_provider_name == "google_genai"

        client.analyze_content("test content", Path("test.md"))
        assert client.active_provider_name == "bedrock"

    @patch('unified_llm_client.BedrockClient')
    @patch('unified_llm_client.GoogleGenAIClient')
    def test_test_connection_falls_back(
        self, mock_google_client, mock_bedrock_client, fallback_config
    ):
        """test_connection should try fallbacks if the primary fails."""
        mock_primary = Mock()
        mock_primary.test_connection.return_value = False
        mock_google_client.return_value = mock_primary

        mock_secondary = Mock()
        mock_secondary.test_connection.return_value = True
        mock_bedrock_client.return_value = mock_secondary

        callback = Mock()
        client = UnifiedLLMClient(fallback_config, on_fallback=callback)
        result = client.test_connection()

        assert result is True
        callback.assert_called_once()

    @patch('unified_llm_client.BedrockClient')
    @patch('unified_llm_client.GoogleGenAIClient')
    def test_fallback_client_initialization_failure_skips_to_next(
        self, mock_google_client, mock_bedrock_client, fallback_config, mock_analysis_result
    ):
        """If a fallback client fails to initialize, skip to the next fallback."""
        mock_primary = Mock()
        mock_primary.analyze_content.side_effect = Exception("Google down")
        mock_google_client.return_value = mock_primary

        # Bedrock fails to initialize
        mock_bedrock_client.side_effect = Exception("AWS credentials missing")

        with patch('unified_llm_client.CBORGClient') as mock_cborg:
            mock_tertiary = Mock()
            mock_tertiary.analyze_content.return_value = mock_analysis_result
            mock_cborg.return_value = mock_tertiary

            callback = Mock()
            client = UnifiedLLMClient(fallback_config, on_fallback=callback)
            result = client.analyze_content("test content", Path("test.md"))

            assert result == mock_analysis_result
            # Two notifications: google→bedrock (init fail), google→cborg (success)
            assert callback.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__])