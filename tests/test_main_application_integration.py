"""
Integration tests for main application with unified LLM client.

Tests that the main application works correctly with both bedrock and google_genai providers,
including dry-run and normal execution modes.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os
import datetime
from dataclasses import dataclass, field
from typing import List

# Import the main application components
from work_journal_summarizer import main, _perform_dry_run
from config_manager import AppConfig, BedrockConfig, GoogleGenAIConfig, LLMConfig, ProcessingConfig
from unified_llm_client import UnifiedLLMClient
from llm_data_structures import AnalysisResult, APIStats
from file_discovery import FileDiscoveryResult


@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def sample_journal_files(temp_directory):
    """Create sample journal files for testing."""
    files = []
    
    # Create sample journal files
    for i in range(3):
        file_path = temp_directory / f"journal_{i}.md"
        content = f"""
# Daily Journal Entry {i}

## Projects
- Project Alpha development
- Beta testing coordination

## Participants
- John Doe (lead developer)
- Jane Smith (QA engineer)

## Tasks
- Code review for feature X
- Bug fixes for issue #{i}
- Documentation updates

## Themes
- Software development
- Quality assurance
- Team collaboration
"""
        file_path.write_text(content)
        files.append(file_path)
    
    return files


@pytest.fixture
def bedrock_config():
    """Create a bedrock configuration for testing."""
    return AppConfig(
        bedrock=BedrockConfig(
            region="us-east-1",
            model_id="anthropic.claude-3-sonnet-20240229-v1:0"
        ),
        llm=LLMConfig(provider="bedrock"),
        processing=ProcessingConfig()
    )


@pytest.fixture
def google_genai_config():
    """Create a google_genai configuration for testing."""
    return AppConfig(
        bedrock=BedrockConfig(),  # Still needed for backward compatibility
        google_genai=GoogleGenAIConfig(
            project="geminijournal-463220",
            location="us-central1",
            model="gemini-2.0-flash-001"
        ),
        llm=LLMConfig(provider="google_genai"),
        processing=ProcessingConfig()
    )


@pytest.fixture
def invalid_provider_config():
    """Create a configuration with invalid provider for testing."""
    return AppConfig(
        bedrock=BedrockConfig(),
        google_genai=GoogleGenAIConfig(),
        llm=LLMConfig(provider="invalid_provider"),
        processing=ProcessingConfig()
    )


@pytest.fixture
def mock_analysis_result():
    """Create a mock analysis result for testing."""
    return AnalysisResult(
        file_path=Path("test.md"),
        projects=["Project Alpha", "Beta testing"],
        participants=["John Doe", "Jane Smith"],
        tasks=["Code review", "Bug fixes"],
        themes=["Software development", "Quality assurance"],
        api_call_time=1.5,
        confidence_score=0.95,
        raw_response='{"projects": ["Project Alpha"], "participants": ["John Doe"]}'
    )


@pytest.fixture
def mock_api_stats():
    """Create mock API stats for testing."""
    return APIStats(
        total_calls=5,
        successful_calls=4,
        failed_calls=1,
        total_time=7.5,
        average_response_time=1.5,
        rate_limit_hits=0
    )


class TestMainApplicationIntegration:
    """Test main application integration with unified client."""

    @patch('work_journal_summarizer.ConfigManager')
    @patch('work_journal_summarizer.UnifiedLLMClient')
    @patch('work_journal_summarizer.FileDiscovery')
    @patch('work_journal_summarizer.ContentProcessor')
    @patch('work_journal_summarizer.SummaryGenerator')
    def test_application_starts_with_bedrock_provider(
        self, 
        mock_summary_gen, 
        mock_content_proc, 
        mock_file_disc, 
        mock_unified_client, 
        mock_config_manager,
        bedrock_config,
        mock_analysis_result,
        mock_api_stats,
        temp_directory
    ):
        """Test that application starts correctly with bedrock provider."""
        # Setup mocks
        mock_config_manager.return_value.get_config.return_value = bedrock_config
        
        mock_client_instance = Mock()
        mock_client_instance.analyze_content.return_value = mock_analysis_result
        mock_client_instance.get_stats.return_value = mock_api_stats
        mock_client_instance.test_connection.return_value = True
        mock_client_instance.get_provider_name.return_value = "bedrock"
        mock_unified_client.return_value = mock_client_instance
        
        mock_file_disc.return_value.discover_files.return_value = FileDiscoveryResult(
            found_files=[temp_directory / "test.md"],
            missing_files=[],
            total_expected=1,
            date_range=(datetime.date(2024, 1, 1), datetime.date(2024, 1, 31)),
            processing_time=0.1
        )
        mock_content_proc.return_value.process_files.return_value = ([], Mock())
        mock_summary_gen.return_value.generate_summary.return_value = (Mock(), Mock())
        
        # Test application startup
        with patch('sys.argv', [
            'work_journal_summarizer.py',
            '--base-path', str(temp_directory),
            '--start-date', '2024-01-01',
            '--end-date', '2024-01-31',
            '--summary-type', 'weekly'
        ]):
            try:
                main()
            except SystemExit:
                pass  # Expected for successful completion
        
        # Verify unified client was created with correct config
        mock_unified_client.assert_called_once_with(bedrock_config)
        
        # Verify client methods were called
        assert mock_client_instance.get_provider_name.called
        assert mock_client_instance.get_stats.called

    @patch('work_journal_summarizer.ConfigManager')
    @patch('work_journal_summarizer.UnifiedLLMClient')
    @patch('work_journal_summarizer.FileDiscovery')
    @patch('work_journal_summarizer.ContentProcessor')
    @patch('work_journal_summarizer.SummaryGenerator')
    def test_application_starts_with_google_genai_provider(
        self, 
        mock_summary_gen, 
        mock_content_proc, 
        mock_file_disc, 
        mock_unified_client, 
        mock_config_manager,
        google_genai_config,
        mock_analysis_result,
        mock_api_stats,
        temp_directory
    ):
        """Test that application starts correctly with google_genai provider."""
        # Setup mocks
        mock_config_manager.return_value.get_config.return_value = google_genai_config
        
        mock_client_instance = Mock()
        mock_client_instance.analyze_content.return_value = mock_analysis_result
        mock_client_instance.get_stats.return_value = mock_api_stats
        mock_client_instance.test_connection.return_value = True
        mock_client_instance.get_provider_name.return_value = "google_genai"
        mock_unified_client.return_value = mock_client_instance
        
        mock_file_disc.return_value.discover_files.return_value = FileDiscoveryResult(
            found_files=[temp_directory / "test.md"],
            missing_files=[],
            total_expected=1,
            date_range=(datetime.date(2024, 1, 1), datetime.date(2024, 1, 31)),
            processing_time=0.1
        )
        mock_content_proc.return_value.process_files.return_value = ([], Mock())
        mock_summary_gen.return_value.generate_summary.return_value = (Mock(), Mock())
        
        # Test application startup
        with patch('sys.argv', [
            'work_journal_summarizer.py',
            '--base-path', str(temp_directory),
            '--start-date', '2024-01-01',
            '--end-date', '2024-01-31',
            '--summary-type', 'weekly'
        ]):
            try:
                main()
            except SystemExit:
                pass  # Expected for successful completion
        
        # Verify unified client was created with correct config
        mock_unified_client.assert_called_once_with(google_genai_config)
        
        # Verify client methods were called
        assert mock_client_instance.get_provider_name.called
        assert mock_client_instance.get_stats.called

    @patch('work_journal_summarizer.ConfigManager')
    @patch('work_journal_summarizer.UnifiedLLMClient')
    def test_error_handling_invalid_provider(
        self, 
        mock_unified_client, 
        mock_config_manager,
        invalid_provider_config
    ):
        """Test error handling when invalid provider is specified."""
        # Setup mocks
        mock_config_manager.return_value.get_config.return_value = invalid_provider_config
        mock_unified_client.side_effect = ValueError("Unknown provider: invalid_provider")
        
        # Test that application handles invalid provider gracefully
        with patch('sys.argv', ['work_journal_summarizer.py', '/tmp']):
            with pytest.raises(SystemExit):
                main()

    @patch('work_journal_summarizer.ConfigManager')
    @patch('work_journal_summarizer.UnifiedLLMClient')
    def test_dry_run_with_bedrock_provider(
        self, 
        mock_unified_client, 
        mock_config_manager,
        bedrock_config,
        mock_api_stats,
        capsys
    ):
        """Test dry-run mode with bedrock provider."""
        # Setup mocks
        mock_config_manager.return_value.get_config.return_value = bedrock_config
        
        mock_client_instance = Mock()
        mock_client_instance.get_stats.return_value = mock_api_stats
        mock_client_instance.test_connection.return_value = True
        mock_client_instance.get_provider_name.return_value = "bedrock"
        mock_client_instance.get_provider_info.return_value = {
            "region": "us-east-1",
            "model_id": "anthropic.claude-3-sonnet-20240229-v1:0"
        }
        mock_unified_client.return_value = mock_client_instance
        
        # Test dry-run mode
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
                pass
        
        # Verify output contains provider information
        captured = capsys.readouterr()
        assert "bedrock" in captured.out.lower()
        assert "us-east-1" in captured.out

    @patch('work_journal_summarizer.ConfigManager')
    @patch('work_journal_summarizer.UnifiedLLMClient')
    def test_dry_run_with_google_genai_provider(
        self, 
        mock_unified_client, 
        mock_config_manager,
        google_genai_config,
        mock_api_stats,
        capsys
    ):
        """Test dry-run mode with google_genai provider."""
        # Setup mocks
        mock_config_manager.return_value.get_config.return_value = google_genai_config
        
        mock_client_instance = Mock()
        mock_client_instance.get_stats.return_value = mock_api_stats
        mock_client_instance.test_connection.return_value = True
        mock_client_instance.get_provider_name.return_value = "google_genai"
        mock_client_instance.get_provider_info.return_value = {
            "project": "geminijournal-463220",
            "location": "us-central1",
            "model": "gemini-2.0-flash-001"
        }
        mock_unified_client.return_value = mock_client_instance
        
        # Test dry-run mode
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
                pass
        
        # Verify output contains provider information
        captured = capsys.readouterr()
        assert "google_genai" in captured.out.lower()
        assert "geminijournal-463220" in captured.out

    @patch('work_journal_summarizer.ConfigManager')
    @patch('work_journal_summarizer.UnifiedLLMClient')
    @patch('work_journal_summarizer.FileDiscovery')
    @patch('work_journal_summarizer.ContentProcessor')
    @patch('work_journal_summarizer.SummaryGenerator')
    def test_equivalent_results_both_providers(
        self, 
        mock_summary_gen, 
        mock_content_proc, 
        mock_file_disc, 
        mock_unified_client, 
        mock_config_manager,
        bedrock_config,
        google_genai_config,
        mock_analysis_result,
        mock_api_stats,
        temp_directory
    ):
        """Test that both providers produce equivalent results when mocked appropriately."""
        # Setup common mocks
        mock_file_disc.return_value.discover_files.return_value = FileDiscoveryResult(
            found_files=[temp_directory / "test.md"],
            missing_files=[],
            total_expected=1,
            date_range=(datetime.date(2024, 1, 1), datetime.date(2024, 1, 31)),
            processing_time=0.1
        )
        mock_content_proc.return_value.process_files.return_value = ([], Mock())
        mock_summary_gen.return_value.generate_summary.return_value = (Mock(), Mock())
        
        # Test with bedrock provider
        mock_config_manager.return_value.get_config.return_value = bedrock_config
        
        mock_client_instance = Mock()
        mock_client_instance.analyze_content.return_value = mock_analysis_result
        mock_client_instance.get_stats.return_value = mock_api_stats
        mock_client_instance.test_connection.return_value = True
        mock_client_instance.get_provider_name.return_value = "bedrock"
        mock_unified_client.return_value = mock_client_instance
        
        with patch('sys.argv', [
            'work_journal_summarizer.py',
            '--base-path', str(temp_directory),
            '--start-date', '2024-01-01',
            '--end-date', '2024-01-31',
            '--summary-type', 'weekly'
        ]):
            try:
                main()
            except SystemExit:
                pass
        
        bedrock_calls = mock_client_instance.analyze_content.call_count
        
        # Reset mocks
        mock_unified_client.reset_mock()
        mock_client_instance.reset_mock()
        
        # Test with google_genai provider
        mock_config_manager.return_value.get_config.return_value = google_genai_config
        mock_client_instance.get_provider_name.return_value = "google_genai"
        mock_unified_client.return_value = mock_client_instance
        
        with patch('sys.argv', [
            'work_journal_summarizer.py',
            '--base-path', str(temp_directory),
            '--start-date', '2024-01-01',
            '--end-date', '2024-01-31',
            '--summary-type', 'weekly'
        ]):
            try:
                main()
            except SystemExit:
                pass
        
        google_calls = mock_client_instance.analyze_content.call_count
        
        # Verify both providers were called the same number of times
        assert bedrock_calls == google_calls

    @patch('work_journal_summarizer.ConfigManager')
    @patch('work_journal_summarizer.UnifiedLLMClient')
    def test_connection_failure_handling(
        self, 
        mock_unified_client, 
        mock_config_manager,
        bedrock_config,
        mock_api_stats
    ):
        """Test handling of connection failures during dry-run."""
        # Setup mocks
        mock_config_manager.return_value.get_config.return_value = bedrock_config
        
        mock_client_instance = Mock()
        mock_client_instance.get_stats.return_value = mock_api_stats
        mock_client_instance.test_connection.return_value = False  # Connection fails
        mock_client_instance.get_provider_name.return_value = "bedrock"
        mock_unified_client.return_value = mock_client_instance
        
        # Test dry-run with connection failure
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
                pass
        
        # Verify connection test was attempted
        mock_client_instance.test_connection.assert_called_once()

    @patch('work_journal_summarizer.ConfigManager')
    @patch('work_journal_summarizer.UnifiedLLMClient')
    @patch('work_journal_summarizer.FileDiscovery')
    @patch('work_journal_summarizer.ContentProcessor')
    def test_api_error_handling_during_analysis(
        self, 
        mock_content_proc, 
        mock_file_disc, 
        mock_unified_client, 
        mock_config_manager,
        bedrock_config,
        temp_directory
    ):
        """Test handling of API errors during content analysis."""
        # Setup mocks
        mock_config_manager.return_value.get_config.return_value = bedrock_config
        
        mock_client_instance = Mock()
        mock_client_instance.analyze_content.side_effect = Exception("API Error")
        mock_client_instance.get_stats.return_value = APIStats(0, 0, 1, 0, 0, 0)
        mock_client_instance.test_connection.return_value = True
        mock_client_instance.get_provider_name.return_value = "bedrock"
        mock_unified_client.return_value = mock_client_instance
        
        mock_file_disc.return_value.discover_files.return_value = FileDiscoveryResult(
            found_files=[temp_directory / "test.md"],
            missing_files=[],
            total_expected=1,
            date_range=(datetime.date(2024, 1, 1), datetime.date(2024, 1, 31)),
            processing_time=0.1
        )
        mock_content_proc.return_value.process_files.return_value = ([], Mock())
        
        # Test that application handles API errors gracefully
        with patch('sys.argv', [
            'work_journal_summarizer.py',
            '--base-path', str(temp_directory),
            '--start-date', '2024-01-01',
            '--end-date', '2024-01-31',
            '--summary-type', 'weekly'
        ]):
            try:
                main()
            except SystemExit:
                pass  # Application should handle errors gracefully
        
        # Verify analyze_content was called despite the error
        assert mock_client_instance.analyze_content.called

    def test_existing_functionality_preserved(self):
        """Test that all existing functionality continues to work."""
        # This test verifies that the refactoring doesn't break existing functionality
        # by checking that all the expected imports and classes are available
        
        # Test imports
        from work_journal_summarizer import main, _perform_dry_run
        from unified_llm_client import UnifiedLLMClient
        from llm_data_structures import AnalysisResult, APIStats
        
        # Test that classes can be instantiated (with mocked dependencies)
        with patch('unified_llm_client.BedrockClient'):
            with patch('unified_llm_client.GoogleGenAIClient'):
                from config_manager import AppConfig
                config = AppConfig()
                client = UnifiedLLMClient(config)
                
                # Test that all expected methods exist
                assert hasattr(client, 'analyze_content')
                assert hasattr(client, 'get_stats')
                assert hasattr(client, 'reset_stats')
                assert hasattr(client, 'test_connection')
                assert hasattr(client, 'get_provider_name')
                assert hasattr(client, 'get_provider_info')


class TestProviderSwitching:
    """Test provider switching functionality."""

    @patch('work_journal_summarizer.ConfigManager')
    @patch('work_journal_summarizer.UnifiedLLMClient')
    def test_provider_switching_bedrock_to_google(
        self, 
        mock_unified_client, 
        mock_config_manager,
        bedrock_config,
        google_genai_config
    ):
        """Test switching from bedrock to google_genai provider."""
        # First call with bedrock
        mock_config_manager.return_value.get_config.return_value = bedrock_config
        
        mock_bedrock_client = Mock()
        mock_bedrock_client.get_provider_name.return_value = "bedrock"
        mock_unified_client.return_value = mock_bedrock_client
        
        client1 = UnifiedLLMClient(bedrock_config)
        provider1 = client1.get_provider_name()
        
        # Second call with google_genai
        mock_config_manager.return_value.get_config.return_value = google_genai_config
        
        mock_google_client = Mock()
        mock_google_client.get_provider_name.return_value = "google_genai"
        mock_unified_client.return_value = mock_google_client
        
        client2 = UnifiedLLMClient(google_genai_config)
        provider2 = client2.get_provider_name()
        
        # Verify different providers were used
        assert provider1 == "bedrock"
        assert provider2 == "google_genai"
        assert provider1 != provider2


if __name__ == "__main__":
    pytest.main([__file__])