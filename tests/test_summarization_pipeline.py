# ABOUTME: Tests for the shared summarization pipeline module.
# ABOUTME: Validates the 4-phase pipeline: discover, process, analyze, generate.
"""
Tests for summarization_pipeline module.

Each pipeline function is tested by mocking its underlying component
to verify correct delegation and return value propagation.
"""

import pytest
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch, call

from content_processor import ProcessedContent, ProcessingStats
from llm_data_structures import AnalysisResult, APIStats
from summary_generator import PeriodSummary, SummaryStats
from file_discovery import FileDiscoveryResult

import summarization_pipeline


class TestDiscoverFiles:
    """Tests for summarization_pipeline.discover_files."""

    @patch('summarization_pipeline.FileDiscovery')
    def test_delegates_to_file_discovery(self, mock_fd_class):
        """Verify discover_files creates FileDiscovery with base_path and calls discover_files."""
        expected_result = Mock(spec=FileDiscoveryResult)
        mock_fd_instance = Mock()
        mock_fd_instance.discover_files.return_value = expected_result
        mock_fd_class.return_value = mock_fd_instance

        result = summarization_pipeline.discover_files(
            "/path/to/journals", date(2024, 1, 1), date(2024, 1, 31)
        )

        mock_fd_class.assert_called_once_with(base_path="/path/to/journals")
        mock_fd_instance.discover_files.assert_called_once_with(date(2024, 1, 1), date(2024, 1, 31))
        assert result is expected_result

    @patch('summarization_pipeline.FileDiscovery')
    def test_propagates_exceptions(self, mock_fd_class):
        """Verify exceptions from FileDiscovery are not swallowed."""
        mock_fd_instance = Mock()
        mock_fd_instance.discover_files.side_effect = FileNotFoundError("base path missing")
        mock_fd_class.return_value = mock_fd_instance

        with pytest.raises(FileNotFoundError, match="base path missing"):
            summarization_pipeline.discover_files(
                "/nonexistent", date(2024, 1, 1), date(2024, 1, 31)
            )


class TestProcessContent:
    """Tests for summarization_pipeline.process_content."""

    @patch('summarization_pipeline.ContentProcessor')
    def test_delegates_to_content_processor(self, mock_cp_class):
        """Verify process_content creates ContentProcessor and calls process_files."""
        mock_processed = [Mock(spec=ProcessedContent)]
        mock_stats = Mock(spec=ProcessingStats)
        mock_cp_instance = Mock()
        mock_cp_instance.process_files.return_value = (mock_processed, mock_stats)
        mock_cp_class.return_value = mock_cp_instance

        file_paths = [Path("/tmp/worklog_2024-01-15.txt")]
        result = summarization_pipeline.process_content(file_paths, max_file_size_mb=25)

        mock_cp_class.assert_called_once_with(max_file_size_mb=25)
        mock_cp_instance.process_files.assert_called_once_with(file_paths)
        assert result == (mock_processed, mock_stats)

    @patch('summarization_pipeline.ContentProcessor')
    def test_uses_default_max_size(self, mock_cp_class):
        """Verify default max_file_size_mb=50 when not specified."""
        mock_cp_instance = Mock()
        mock_cp_instance.process_files.return_value = ([], Mock(spec=ProcessingStats))
        mock_cp_class.return_value = mock_cp_instance

        summarization_pipeline.process_content([])

        mock_cp_class.assert_called_once_with(max_file_size_mb=50)


class TestAnalyzeContent:
    """Tests for summarization_pipeline.analyze_content."""

    @patch('summarization_pipeline.UnifiedLLMClient')
    def test_iterates_processed_content(self, mock_llm_class):
        """Verify analyze_content calls analyze_content for each ProcessedContent item."""
        mock_llm_instance = Mock()
        mock_result_1 = Mock(spec=AnalysisResult)
        mock_result_2 = Mock(spec=AnalysisResult)
        mock_llm_instance.analyze_content.side_effect = [mock_result_1, mock_result_2]
        mock_llm_instance.get_stats.return_value = Mock(spec=APIStats)
        mock_llm_class.return_value = mock_llm_instance

        content_1 = Mock(spec=ProcessedContent)
        content_1.content = "Day 1 work"
        content_1.file_path = Path("/tmp/worklog_2024-01-15.txt")
        content_2 = Mock(spec=ProcessedContent)
        content_2.content = "Day 2 work"
        content_2.file_path = Path("/tmp/worklog_2024-01-16.txt")

        mock_config = Mock()
        results, stats, client = summarization_pipeline.analyze_content(
            [content_1, content_2], mock_config
        )

        assert len(results) == 2
        assert results[0] is mock_result_1
        assert results[1] is mock_result_2
        mock_llm_instance.analyze_content.assert_any_call("Day 1 work", Path("/tmp/worklog_2024-01-15.txt"))
        mock_llm_instance.analyze_content.assert_any_call("Day 2 work", Path("/tmp/worklog_2024-01-16.txt"))

    @patch('summarization_pipeline.UnifiedLLMClient')
    def test_returns_client_for_reuse(self, mock_llm_class):
        """Verify the UnifiedLLMClient instance is returned for reuse by generate_summaries."""
        mock_llm_instance = Mock()
        mock_llm_instance.get_stats.return_value = Mock(spec=APIStats)
        mock_llm_class.return_value = mock_llm_instance

        mock_config = Mock()
        _, _, client = summarization_pipeline.analyze_content([], mock_config)

        assert client is mock_llm_instance

    @patch('summarization_pipeline.UnifiedLLMClient')
    def test_passes_on_fallback_callback(self, mock_llm_class):
        """Verify on_fallback is passed to UnifiedLLMClient."""
        mock_llm_instance = Mock()
        mock_llm_instance.get_stats.return_value = Mock(spec=APIStats)
        mock_llm_class.return_value = mock_llm_instance

        callback = Mock()
        mock_config = Mock()
        summarization_pipeline.analyze_content([], mock_config, on_fallback=callback)

        mock_llm_class.assert_called_once_with(mock_config, on_fallback=callback)

    @patch('summarization_pipeline.UnifiedLLMClient')
    def test_empty_list_returns_empty_results(self, mock_llm_class):
        """Verify empty processed_content returns empty results and zeroed stats."""
        mock_llm_instance = Mock()
        mock_api_stats = Mock(spec=APIStats)
        mock_llm_instance.get_stats.return_value = mock_api_stats
        mock_llm_class.return_value = mock_llm_instance

        mock_config = Mock()
        results, stats, client = summarization_pipeline.analyze_content([], mock_config)

        assert results == []
        assert stats is mock_api_stats
        assert client is mock_llm_instance
        mock_llm_instance.analyze_content.assert_not_called()


class TestGenerateSummaries:
    """Tests for summarization_pipeline.generate_summaries."""

    @patch('summarization_pipeline.SummaryGenerator')
    def test_delegates_to_summary_generator(self, mock_sg_class):
        """Verify generate_summaries creates SummaryGenerator and calls generate_summaries."""
        mock_summaries = [Mock(spec=PeriodSummary)]
        mock_stats = Mock(spec=SummaryStats)
        mock_sg_instance = Mock()
        mock_sg_instance.generate_summaries.return_value = (mock_summaries, mock_stats)
        mock_sg_class.return_value = mock_sg_instance

        mock_llm_client = Mock()
        mock_results = [Mock(spec=AnalysisResult)]

        result = summarization_pipeline.generate_summaries(
            mock_results, mock_llm_client, "weekly", date(2024, 1, 1), date(2024, 1, 7)
        )

        mock_sg_class.assert_called_once_with(mock_llm_client)
        mock_sg_instance.generate_summaries.assert_called_once_with(
            mock_results, "weekly", date(2024, 1, 1), date(2024, 1, 7)
        )
        assert result == (mock_summaries, mock_stats)

    @patch('summarization_pipeline.SummaryGenerator')
    def test_passes_monthly_summary_type(self, mock_sg_class):
        """Verify monthly summary type is passed through correctly."""
        mock_sg_instance = Mock()
        mock_sg_instance.generate_summaries.return_value = ([], Mock(spec=SummaryStats))
        mock_sg_class.return_value = mock_sg_instance

        summarization_pipeline.generate_summaries(
            [], Mock(), "monthly", date(2024, 1, 1), date(2024, 1, 31)
        )

        mock_sg_instance.generate_summaries.assert_called_once_with(
            [], "monthly", date(2024, 1, 1), date(2024, 1, 31)
        )
