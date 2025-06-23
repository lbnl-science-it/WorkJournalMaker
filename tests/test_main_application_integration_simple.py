"""
Simplified integration tests for main application with unified LLM client.

These tests focus on the core integration points without complex mocking.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

# Import the main application components
from work_journal_summarizer import main
from config_manager import AppConfig, BedrockConfig, GoogleGenAIConfig, LLMConfig, ProcessingConfig
from unified_llm_client import UnifiedLLMClient
from llm_data_structures import AnalysisResult, APIStats


class TestMainApplicationIntegrationSimple:
    """Simplified integration tests for main application."""

    def test_unified_client_import_and_creation(self):
        """Test that UnifiedLLMClient can be imported and created."""
        # Test bedrock configuration
        bedrock_config = AppConfig(
            llm=LLMConfig(provider="bedrock"),
            bedrock=BedrockConfig(),
            processing=ProcessingConfig()
        )
        
        with patch('unified_llm_client.BedrockClient'):
            client = UnifiedLLMClient(bedrock_config)
            assert client.get_provider_name() == "bedrock"
        
        # Test google_genai configuration
        google_config = AppConfig(
            llm=LLMConfig(provider="google_genai"),
            google_genai=GoogleGenAIConfig(),
            bedrock=BedrockConfig(),  # Still needed for backward compatibility
            processing=ProcessingConfig()
        )
        
        with patch('unified_llm_client.GoogleGenAIClient'):
            client = UnifiedLLMClient(google_config)
            assert client.get_provider_name() == "google_genai"

    def test_invalid_provider_handling(self):
        """Test that invalid provider raises appropriate error."""
        invalid_config = AppConfig(
            llm=LLMConfig(provider="invalid_provider"),
            bedrock=BedrockConfig(),
            google_genai=GoogleGenAIConfig(),
            processing=ProcessingConfig()
        )
        
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            UnifiedLLMClient(invalid_config)

    def test_provider_switching(self):
        """Test switching between providers."""
        # Create configs for both providers
        bedrock_config = AppConfig(
            llm=LLMConfig(provider="bedrock"),
            bedrock=BedrockConfig(region="us-east-1"),
            processing=ProcessingConfig()
        )
        
        google_config = AppConfig(
            llm=LLMConfig(provider="google_genai"),
            google_genai=GoogleGenAIConfig(project="test-project"),
            bedrock=BedrockConfig(),
            processing=ProcessingConfig()
        )
        
        with patch('unified_llm_client.BedrockClient') as mock_bedrock:
            with patch('unified_llm_client.GoogleGenAIClient') as mock_google:
                # Test bedrock client creation
                client1 = UnifiedLLMClient(bedrock_config)
                mock_bedrock.assert_called_once()
                assert client1.get_provider_name() == "bedrock"
                
                # Test google client creation
                client2 = UnifiedLLMClient(google_config)
                mock_google.assert_called_once()
                assert client2.get_provider_name() == "google_genai"

    def test_client_interface_compatibility(self):
        """Test that UnifiedLLMClient maintains the same interface as BedrockClient."""
        config = AppConfig(
            llm=LLMConfig(provider="bedrock"),
            bedrock=BedrockConfig(),
            processing=ProcessingConfig()
        )
        
        with patch('unified_llm_client.BedrockClient') as mock_bedrock_class:
            mock_bedrock_instance = Mock()
            mock_bedrock_instance.analyze_content.return_value = AnalysisResult(
                file_path=Path("test.md"),
                projects=["Test Project"],
                participants=["Test User"],
                tasks=["Test Task"],
                themes=["Test Theme"],
                api_call_time=1.0,
                confidence_score=0.9,
                raw_response="test response"
            )
            mock_bedrock_instance.get_stats.return_value = APIStats(
                total_calls=1, successful_calls=1, failed_calls=0,
                total_time=1.0, average_response_time=1.0, rate_limit_hits=0
            )
            mock_bedrock_instance.test_connection.return_value = True
            mock_bedrock_instance.get_provider_info.return_value = {"region": "us-east-1", "model_id": "test-model"}
            mock_bedrock_class.return_value = mock_bedrock_instance
            
            client = UnifiedLLMClient(config)
            
            # Test all interface methods exist and work
            result = client.analyze_content("test content", Path("test.md"))
            assert isinstance(result, AnalysisResult)
            assert result.projects == ["Test Project"]
            
            stats = client.get_stats()
            assert isinstance(stats, APIStats)
            assert stats.total_calls == 1
            
            connection_ok = client.test_connection()
            assert connection_ok is True
            
            client.reset_stats()  # Should not raise an error
            
            provider_name = client.get_provider_name()
            assert provider_name == "bedrock"
            
            provider_info = client.get_provider_info()
            assert isinstance(provider_info, dict)

    @patch('work_journal_summarizer.ConfigManager')
    def test_main_application_uses_unified_client(self, mock_config_manager):
        """Test that main application creates UnifiedLLMClient instead of BedrockClient directly."""
        config = AppConfig(
            llm=LLMConfig(provider="bedrock"),
            bedrock=BedrockConfig(),
            processing=ProcessingConfig()
        )
        mock_config_manager.return_value.get_config.return_value = config
        
        with patch('work_journal_summarizer.UnifiedLLMClient') as mock_unified_client:
            with patch('sys.argv', [
                'work_journal_summarizer.py',
                '--base-path', '/tmp',
                '--start-date', '2024-01-01',
                '--end-date', '2024-01-31',
                '--summary-type', 'weekly',
                '--dry-run'
            ]):
                try:
                    main()
                except SystemExit:
                    pass  # Expected for dry-run mode
                
                # Verify UnifiedLLMClient was called with the config
                mock_unified_client.assert_called()
                call_args = mock_unified_client.call_args[0]
                assert len(call_args) == 1
                assert isinstance(call_args[0], AppConfig)

    def test_backward_compatibility(self):
        """Test that existing functionality is preserved."""
        # Verify that all expected classes and functions can be imported
        from work_journal_summarizer import main
        from unified_llm_client import UnifiedLLMClient
        from llm_data_structures import AnalysisResult, APIStats
        from config_manager import AppConfig, BedrockConfig, GoogleGenAIConfig, LLMConfig
        
        # Verify that the default configuration still uses bedrock
        config = AppConfig()
        assert config.llm.provider == "bedrock"
        
        # Verify that UnifiedLLMClient can be created with default config
        with patch('unified_llm_client.BedrockClient'):
            client = UnifiedLLMClient(config)
            assert client.get_provider_name() == "bedrock"


if __name__ == "__main__":
    pytest.main([__file__])