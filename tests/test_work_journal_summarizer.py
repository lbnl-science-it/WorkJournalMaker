# ABOUTME: Tests for work_journal_summarizer.py CLI pipeline functions.
# ABOUTME: Validates provider-agnostic output and main() orchestration behavior.

import datetime
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import work_journal_summarizer as wjs


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
