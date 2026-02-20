# ABOUTME: Tests for work_journal_summarizer.py CLI pipeline functions.
# ABOUTME: Validates provider-agnostic output and main() orchestration behavior.

import datetime
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import work_journal_summarizer as wjs
from content_processor import ProcessedContent, ProcessingStats
from file_discovery import FileDiscoveryResult
from llm_data_structures import AnalysisResult, APIStats
from logger import ErrorCategory
from output_manager import OutputResult, ProcessingMetadata
from summary_generator import PeriodSummary, SummaryStats


class TestBannerProviderOutput:
    """The banner in main() should display provider info from get_provider_info(),
    not hardcoded AWS/Bedrock fields."""

    def _make_config(self):
        """Build a minimal AppConfig mock with google_genai as the provider."""
        config = MagicMock()
        config.processing.base_path = "/tmp/journals"
        config.processing.output_path = "/tmp/output"
        config.logging.level.value = "INFO"
        config.logging.log_dir = "/tmp/logs"
        config.logging.console_output = False
        config.logging.file_output = False
        config.llm.provider = "google_genai"
        config.llm.fallback_providers = []
        return config

    def _make_args(self):
        """Build a minimal args namespace for a non-dry-run invocation."""
        args = MagicMock()
        args.start_date = datetime.date(2025, 1, 6)
        args.end_date = datetime.date(2025, 1, 10)
        args.summary_type = "weekly"
        args.base_path = None
        args.output_dir = None
        args.log_level = None
        args.log_dir = None
        args.no_console = False
        args.dry_run = False
        args.save_example_config = None
        args.config = None
        return args

    @patch("work_journal_summarizer.parse_arguments")
    @patch("work_journal_summarizer.ConfigManager")
    @patch("work_journal_summarizer.create_logger_with_config")
    @patch("work_journal_summarizer.UnifiedLLMClient")
    @patch("work_journal_summarizer.FileDiscovery")
    def test_banner_does_not_contain_hardcoded_aws_region(
        self, mock_fd_cls, mock_llm_cls, mock_logger_fn, mock_cm_cls, mock_parse
    ):
        """When provider is google_genai, banner must NOT print 'AWS Region'."""
        args = self._make_args()
        mock_parse.return_value = args

        config = self._make_config()
        mock_cm = MagicMock()
        mock_cm.get_config.return_value = config
        mock_cm_cls.return_value = mock_cm

        mock_logger = MagicMock()
        mock_logger_fn.return_value = mock_logger

        mock_llm = MagicMock()
        mock_llm.get_provider_info.return_value = {
            "provider": "google_genai",
            "project": "my-project",
            "location": "us-central1",
            "model": "gemini-2.0-flash-001",
            "active_provider": "google_genai",
            "fallback_providers": [],
        }
        mock_llm.get_provider_name.return_value = "google_genai"
        mock_llm_cls.return_value = mock_llm

        # Make file discovery return empty so main() exits early after the banner
        mock_fd = MagicMock()
        discovery_result = MagicMock()
        discovery_result.found_files = []
        discovery_result.missing_files = []
        discovery_result.total_expected = 0
        mock_fd.discover_files.return_value = discovery_result
        mock_fd_cls.return_value = mock_fd

        captured = StringIO()
        with patch("sys.stdout", captured):
            try:
                wjs.main()
            except (SystemExit, Exception):
                pass  # We only care about stdout content

        output = captured.getvalue()
        assert "AWS Region" not in output, (
            f"Banner should not contain hardcoded 'AWS Region' when using google_genai.\n"
            f"Captured output:\n{output}"
        )

    @patch("work_journal_summarizer.parse_arguments")
    @patch("work_journal_summarizer.ConfigManager")
    @patch("work_journal_summarizer.create_logger_with_config")
    @patch("work_journal_summarizer.UnifiedLLMClient")
    @patch("work_journal_summarizer.FileDiscovery")
    def test_banner_prints_provider_info_keys(
        self, mock_fd_cls, mock_llm_cls, mock_logger_fn, mock_cm_cls, mock_parse
    ):
        """Banner should print keys from get_provider_info() (excluding fallback_providers)."""
        args = self._make_args()
        mock_parse.return_value = args

        config = self._make_config()
        mock_cm = MagicMock()
        mock_cm.get_config.return_value = config
        mock_cm_cls.return_value = mock_cm

        mock_logger = MagicMock()
        mock_logger_fn.return_value = mock_logger

        mock_llm = MagicMock()
        mock_llm.get_provider_info.return_value = {
            "provider": "google_genai",
            "project": "my-project",
            "location": "us-central1",
            "model": "gemini-2.0-flash-001",
            "active_provider": "google_genai",
            "fallback_providers": [],
        }
        mock_llm.get_provider_name.return_value = "google_genai"
        mock_llm_cls.return_value = mock_llm

        mock_fd = MagicMock()
        discovery_result = MagicMock()
        discovery_result.found_files = []
        discovery_result.missing_files = []
        discovery_result.total_expected = 0
        mock_fd.discover_files.return_value = discovery_result
        mock_fd_cls.return_value = mock_fd

        captured = StringIO()
        with patch("sys.stdout", captured):
            try:
                wjs.main()
            except (SystemExit, Exception):
                pass

        output = captured.getvalue()
        # Provider info keys (title-cased, underscores to spaces) should appear
        assert "Provider: google_genai" in output, (
            f"Expected 'Provider: google_genai' in banner output.\n"
            f"Captured output:\n{output}"
        )
        assert "Project: my-project" in output, (
            f"Expected 'Project: my-project' in banner output.\n"
            f"Captured output:\n{output}"
        )
        # fallback_providers should NOT appear
        assert "Fallback Providers" not in output


class TestRunFileDiscovery:
    """Tests for the extracted _run_file_discovery phase function."""

    def test_returns_file_discovery_result_on_success(self):
        """_run_file_discovery returns the FileDiscoveryResult from FileDiscovery."""
        config = MagicMock()
        config.processing.base_path = "/tmp/journals"
        args = MagicMock()
        args.start_date = datetime.date(2025, 1, 6)
        args.end_date = datetime.date(2025, 1, 10)
        logger = MagicMock()

        expected_result = FileDiscoveryResult(
            found_files=[Path("/tmp/journals/worklog_2025-01-06.txt")],
            missing_files=[],
            total_expected=1,
            date_range=(datetime.date(2025, 1, 6), datetime.date(2025, 1, 10)),
            processing_time=0.01,
        )

        with patch("work_journal_summarizer.FileDiscovery") as mock_fd_cls:
            mock_fd = MagicMock()
            mock_fd.discover_files.return_value = expected_result
            mock_fd_cls.return_value = mock_fd

            captured = StringIO()
            with patch("sys.stdout", captured):
                result = wjs._run_file_discovery(config, args, logger)

        assert isinstance(result, FileDiscoveryResult)
        assert len(result.found_files) == 1
        assert result.total_expected == 1

    def test_returns_empty_result_on_exception(self):
        """_run_file_discovery returns an empty FileDiscoveryResult when discovery fails."""
        config = MagicMock()
        config.processing.base_path = "/nonexistent"
        args = MagicMock()
        args.start_date = datetime.date(2025, 1, 6)
        args.end_date = datetime.date(2025, 1, 10)
        logger = MagicMock()
        logger.should_continue_processing.return_value = True

        with patch("work_journal_summarizer.FileDiscovery") as mock_fd_cls:
            mock_fd_cls.side_effect = OSError("No such directory")

            captured = StringIO()
            with patch("sys.stdout", captured):
                result = wjs._run_file_discovery(config, args, logger)

        assert isinstance(result, FileDiscoveryResult)
        assert result.found_files == []
        assert result.total_expected == 0

    def test_returns_none_on_critical_failure(self):
        """_run_file_discovery returns None when logger says stop processing."""
        config = MagicMock()
        config.processing.base_path = "/nonexistent"
        args = MagicMock()
        args.start_date = datetime.date(2025, 1, 6)
        args.end_date = datetime.date(2025, 1, 10)
        logger = MagicMock()
        logger.should_continue_processing.return_value = False

        with patch("work_journal_summarizer.FileDiscovery") as mock_fd_cls:
            mock_fd_cls.side_effect = OSError("No such directory")

            captured = StringIO()
            with patch("sys.stdout", captured):
                result = wjs._run_file_discovery(config, args, logger)

        assert result is None

    def test_prints_discovery_statistics(self):
        """_run_file_discovery prints discovery results to stdout."""
        config = MagicMock()
        config.processing.base_path = "/tmp/journals"
        args = MagicMock()
        args.start_date = datetime.date(2025, 1, 6)
        args.end_date = datetime.date(2025, 1, 10)
        logger = MagicMock()

        expected_result = FileDiscoveryResult(
            found_files=[Path("/tmp/journals/worklog_2025-01-06.txt")],
            missing_files=[Path("/tmp/journals/worklog_2025-01-07.txt")],
            total_expected=2,
            date_range=(datetime.date(2025, 1, 6), datetime.date(2025, 1, 10)),
            processing_time=0.05,
        )

        with patch("work_journal_summarizer.FileDiscovery") as mock_fd_cls:
            mock_fd = MagicMock()
            mock_fd.discover_files.return_value = expected_result
            mock_fd_cls.return_value = mock_fd

            captured = StringIO()
            with patch("sys.stdout", captured):
                wjs._run_file_discovery(config, args, logger)

        output = captured.getvalue()
        assert "File Discovery Results" in output
        assert "Total files expected: 2" in output
        assert "Files found: 1" in output
        assert "Files missing: 1" in output


class TestRunContentProcessing:
    """Tests for the extracted _run_content_processing phase function."""

    def test_returns_processed_content_and_stats(self):
        """_run_content_processing returns a tuple of (list, ProcessingStats)."""
        found_files = [Path("/tmp/worklog_2025-01-06.txt")]
        config = MagicMock()
        config.processing.max_file_size_mb = 50

        mock_processed = MagicMock(spec=ProcessedContent)
        mock_processed.file_path = found_files[0]
        mock_processed.date = datetime.date(2025, 1, 6)
        mock_processed.encoding = "utf-8"
        mock_processed.word_count = 100
        mock_processed.line_count = 10
        mock_processed.processing_time = 0.01
        mock_processed.content = "Test content"
        mock_processed.errors = []

        mock_stats = ProcessingStats(
            total_files=1, successful=1, failed=0,
            total_size_bytes=500, total_words=100, processing_time=0.01,
        )

        with patch("work_journal_summarizer.ContentProcessor") as mock_cp_cls:
            mock_cp = MagicMock()
            mock_cp.process_files.return_value = ([mock_processed], mock_stats)
            mock_cp_cls.return_value = mock_cp

            captured = StringIO()
            with patch("sys.stdout", captured):
                content, stats = wjs._run_content_processing(found_files, config)

        assert len(content) == 1
        assert stats.total_files == 1
        assert stats.successful == 1

    def test_prints_processing_statistics(self):
        """_run_content_processing prints content processing results."""
        found_files = [Path("/tmp/worklog_2025-01-06.txt")]
        config = MagicMock()
        config.processing.max_file_size_mb = 50

        mock_processed = MagicMock(spec=ProcessedContent)
        mock_processed.file_path = found_files[0]
        mock_processed.date = datetime.date(2025, 1, 6)
        mock_processed.encoding = "utf-8"
        mock_processed.word_count = 100
        mock_processed.line_count = 10
        mock_processed.processing_time = 0.01
        mock_processed.content = "Test content for preview display here"
        mock_processed.errors = []

        mock_stats = ProcessingStats(
            total_files=1, successful=1, failed=0,
            total_size_bytes=500, total_words=100, processing_time=0.05,
        )

        with patch("work_journal_summarizer.ContentProcessor") as mock_cp_cls:
            mock_cp = MagicMock()
            mock_cp.process_files.return_value = ([mock_processed], mock_stats)
            mock_cp_cls.return_value = mock_cp

            captured = StringIO()
            with patch("sys.stdout", captured):
                wjs._run_content_processing(found_files, config)

        output = captured.getvalue()
        assert "Content Processing Results" in output
        assert "Files processed: 1" in output


class TestRunLLMAnalysis:
    """Tests for the extracted _run_llm_analysis phase function."""

    def test_returns_analysis_results_and_stats(self):
        """_run_llm_analysis returns (results, stats, entity_sets) tuple."""
        mock_content = MagicMock()
        mock_content.content = "Worked on ProjectX"
        mock_content.file_path = Path("/tmp/worklog_2025-01-06.txt")
        processed = [mock_content]

        config = MagicMock()

        mock_result = MagicMock(spec=AnalysisResult)
        mock_result.projects = ["ProjectX"]
        mock_result.participants = ["Alice"]
        mock_result.tasks = ["code review"]
        mock_result.themes = ["engineering"]

        mock_stats = MagicMock(spec=APIStats)
        mock_stats.total_calls = 1
        mock_stats.successful_calls = 1
        mock_stats.failed_calls = 0
        mock_stats.total_time = 0.5
        mock_stats.average_response_time = 0.5
        mock_stats.rate_limit_hits = 0

        with patch("work_journal_summarizer.UnifiedLLMClient") as mock_llm_cls:
            mock_llm = MagicMock()
            mock_llm.analyze_content.return_value = mock_result
            mock_llm.get_stats.return_value = mock_stats
            mock_llm_cls.return_value = mock_llm

            captured = StringIO()
            with patch("sys.stdout", captured):
                results, stats, entity_sets, client = wjs._run_llm_analysis(
                    processed, config
                )

        assert len(results) == 1
        assert stats.total_calls == 1
        assert "ProjectX" in entity_sets["projects"]
        assert "Alice" in entity_sets["participants"]

    def test_prints_entity_extraction_summary(self):
        """_run_llm_analysis prints entity extraction stats."""
        mock_content = MagicMock()
        mock_content.content = "Worked on ProjectX"
        mock_content.file_path = Path("/tmp/worklog_2025-01-06.txt")
        processed = [mock_content]

        config = MagicMock()

        mock_result = MagicMock(spec=AnalysisResult)
        mock_result.projects = ["ProjectX"]
        mock_result.participants = []
        mock_result.tasks = ["code review"]
        mock_result.themes = []

        mock_stats = MagicMock(spec=APIStats)
        mock_stats.total_calls = 1
        mock_stats.successful_calls = 1
        mock_stats.failed_calls = 0
        mock_stats.total_time = 0.5
        mock_stats.average_response_time = 0.5
        mock_stats.rate_limit_hits = 0

        with patch("work_journal_summarizer.UnifiedLLMClient") as mock_llm_cls:
            mock_llm = MagicMock()
            mock_llm.analyze_content.return_value = mock_result
            mock_llm.get_stats.return_value = mock_stats
            mock_llm_cls.return_value = mock_llm

            captured = StringIO()
            with patch("sys.stdout", captured):
                wjs._run_llm_analysis(processed, config)

        output = captured.getvalue()
        assert "Entity Extraction Summary" in output
        assert "Unique projects identified: 1" in output


class TestRunSummaryGeneration:
    """Tests for the extracted _run_summary_generation phase function."""

    def test_returns_summaries_and_stats(self):
        """_run_summary_generation returns (summaries, summary_stats) tuple."""
        mock_analysis = MagicMock(spec=AnalysisResult)
        analysis_results = [mock_analysis]
        llm_client = MagicMock()
        args = MagicMock()
        args.summary_type = "weekly"
        args.start_date = datetime.date(2025, 1, 6)
        args.end_date = datetime.date(2025, 1, 10)

        mock_summary = MagicMock(spec=PeriodSummary)
        mock_summary.period_name = "Week of Jan 6"
        mock_summary.start_date = datetime.date(2025, 1, 6)
        mock_summary.end_date = datetime.date(2025, 1, 10)
        mock_summary.entry_count = 5
        mock_summary.word_count = 500
        mock_summary.generation_time = 1.0
        mock_summary.projects = ["ProjectX"]
        mock_summary.participants = ["Alice"]
        mock_summary.themes = ["engineering"]
        mock_summary.summary_text = "Weekly summary text."

        mock_stats = MagicMock(spec=SummaryStats)
        mock_stats.total_periods = 1
        mock_stats.successful_summaries = 1
        mock_stats.failed_summaries = 0
        mock_stats.total_entries_processed = 5
        mock_stats.total_generation_time = 1.0
        mock_stats.average_summary_length = 500

        with patch("work_journal_summarizer.SummaryGenerator") as mock_sg_cls:
            mock_sg = MagicMock()
            mock_sg.generate_summaries.return_value = ([mock_summary], mock_stats)
            mock_sg_cls.return_value = mock_sg

            captured = StringIO()
            with patch("sys.stdout", captured):
                summaries, stats = wjs._run_summary_generation(
                    analysis_results, llm_client, args
                )

        assert len(summaries) == 1
        assert stats.total_periods == 1

    def test_prints_summary_statistics(self):
        """_run_summary_generation prints summary generation stats."""
        mock_analysis = MagicMock(spec=AnalysisResult)
        llm_client = MagicMock()
        args = MagicMock()
        args.summary_type = "weekly"
        args.start_date = datetime.date(2025, 1, 6)
        args.end_date = datetime.date(2025, 1, 10)

        mock_summary = MagicMock(spec=PeriodSummary)
        mock_summary.period_name = "Week of Jan 6"
        mock_summary.start_date = datetime.date(2025, 1, 6)
        mock_summary.end_date = datetime.date(2025, 1, 10)
        mock_summary.entry_count = 5
        mock_summary.word_count = 500
        mock_summary.generation_time = 1.0
        mock_summary.projects = ["ProjectX"]
        mock_summary.participants = []
        mock_summary.themes = []
        mock_summary.summary_text = "Weekly summary."

        mock_stats = MagicMock(spec=SummaryStats)
        mock_stats.total_periods = 1
        mock_stats.successful_summaries = 1
        mock_stats.failed_summaries = 0
        mock_stats.total_entries_processed = 5
        mock_stats.total_generation_time = 1.0
        mock_stats.average_summary_length = 500

        with patch("work_journal_summarizer.SummaryGenerator") as mock_sg_cls:
            mock_sg = MagicMock()
            mock_sg.generate_summaries.return_value = ([mock_summary], mock_stats)
            mock_sg_cls.return_value = mock_sg

            captured = StringIO()
            with patch("sys.stdout", captured):
                wjs._run_summary_generation([mock_analysis], llm_client, args)

        output = captured.getvalue()
        assert "Summary Generation Results" in output
        assert "Successful summaries: 1" in output


class TestRunOutputGeneration:
    """Tests for the extracted _run_output_generation phase function."""

    def test_returns_output_result(self):
        """_run_output_generation returns an OutputResult."""
        mock_summary = MagicMock(spec=PeriodSummary)
        summaries = [mock_summary]
        args = MagicMock()
        args.summary_type = "weekly"
        args.start_date = datetime.date(2025, 1, 6)
        args.end_date = datetime.date(2025, 1, 10)

        mock_metadata = MagicMock(spec=ProcessingMetadata)
        mock_metadata.processing_duration = 5.0
        mock_metadata.files_successfully_processed = 5
        mock_metadata.total_files_found = 5
        mock_metadata.successful_api_calls = 5
        mock_metadata.api_calls_made = 5

        mock_output = MagicMock(spec=OutputResult)
        mock_output.output_path = Path("/tmp/output/summary.md")
        mock_output.file_size_bytes = 2048
        mock_output.generation_time = 0.1
        mock_output.sections_count = 3
        mock_output.metadata_included = True
        mock_output.validation_passed = True

        config = MagicMock()
        config.processing.output_path = "/tmp/output"

        mock_stats = MagicMock(spec=SummaryStats)
        mock_stats.successful_summaries = 1

        with patch("work_journal_summarizer.OutputManager") as mock_om_cls:
            mock_om = MagicMock()
            mock_om.generate_output.return_value = mock_output
            mock_om_cls.return_value = mock_om

            captured = StringIO()
            with patch("sys.stdout", captured):
                result = wjs._run_output_generation(
                    summaries, args, mock_metadata, config, mock_stats
                )

        assert result.output_path == Path("/tmp/output/summary.md")

    def test_prints_output_results(self):
        """_run_output_generation prints output generation results."""
        mock_summary = MagicMock(spec=PeriodSummary)
        args = MagicMock()
        args.summary_type = "weekly"
        args.start_date = datetime.date(2025, 1, 6)
        args.end_date = datetime.date(2025, 1, 10)

        mock_metadata = MagicMock(spec=ProcessingMetadata)
        mock_metadata.processing_duration = 5.0
        mock_metadata.files_successfully_processed = 5
        mock_metadata.total_files_found = 5
        mock_metadata.successful_api_calls = 5
        mock_metadata.api_calls_made = 5

        mock_output = MagicMock(spec=OutputResult)
        mock_output.output_path = Path("/tmp/output/summary.md")
        mock_output.file_size_bytes = 2048
        mock_output.generation_time = 0.1
        mock_output.sections_count = 3
        mock_output.metadata_included = True
        mock_output.validation_passed = True

        config = MagicMock()
        config.processing.output_path = "/tmp/output"

        mock_stats = MagicMock(spec=SummaryStats)
        mock_stats.successful_summaries = 1

        with patch("work_journal_summarizer.OutputManager") as mock_om_cls:
            mock_om = MagicMock()
            mock_om.generate_output.return_value = mock_output
            mock_om_cls.return_value = mock_om

            captured = StringIO()
            with patch("sys.stdout", captured):
                wjs._run_output_generation(
                    [mock_summary], args, mock_metadata, config, mock_stats
                )

        output = captured.getvalue()
        assert "Output Generation Results" in output
        assert "All Phases Complete" in output


class TestDisplayBanner:
    """Tests for the extracted _display_banner function."""

    def test_prints_date_range_and_provider_info(self):
        """_display_banner prints start/end dates and provider info."""
        args = MagicMock()
        args.start_date = datetime.date(2025, 1, 6)
        args.end_date = datetime.date(2025, 1, 10)
        args.summary_type = "weekly"

        config = MagicMock()
        config.processing.base_path = "/tmp/journals"
        config.processing.output_path = "/tmp/output"

        provider_info = {
            "provider": "google_genai",
            "project": "my-project",
            "model": "gemini-2.0-flash",
            "active_provider": "google_genai",
            "fallback_providers": [],
        }

        captured = StringIO()
        with patch("sys.stdout", captured):
            wjs._display_banner(args, config, provider_info)

        output = captured.getvalue()
        assert "Start Date: 2025-01-06" in output
        assert "End Date: 2025-01-10" in output
        assert "Provider: google_genai" in output
        assert "Fallback Providers" not in output


class TestDisplayQualityMetrics:
    """Tests for the extracted _display_quality_metrics function."""

    def test_prints_quality_stats(self):
        """_display_quality_metrics prints average words and lines per file."""
        mock_content = MagicMock()
        mock_content.word_count = 200
        mock_content.line_count = 20
        mock_content.encoding = "utf-8"
        mock_content.errors = []

        captured = StringIO()
        with patch("sys.stdout", captured):
            wjs._display_quality_metrics([mock_content])

        output = captured.getvalue()
        assert "Content Quality Metrics" in output
        assert "Average words per file: 200.0" in output

    def test_reports_encoding_diversity(self):
        """_display_quality_metrics reports detected encodings."""
        mock1 = MagicMock()
        mock1.word_count = 100
        mock1.line_count = 10
        mock1.encoding = "utf-8"
        mock1.errors = []

        mock2 = MagicMock()
        mock2.word_count = 150
        mock2.line_count = 15
        mock2.encoding = "ascii"
        mock2.errors = []

        captured = StringIO()
        with patch("sys.stdout", captured):
            wjs._display_quality_metrics([mock1, mock2])

        output = captured.getvalue()
        assert "utf-8" in output
        assert "ascii" in output
