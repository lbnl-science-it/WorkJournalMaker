"""
Integration tests for Phase 7: Comprehensive Error Handling & Logging

This module tests the integration of the logging system with the main
work journal summarizer application, ensuring proper error handling
and progress tracking throughout the processing pipeline.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import date

from work_journal_summarizer import parse_arguments, _perform_dry_run
from logger import create_logger_with_config, ErrorCategory


class TestLoggingIntegration:
    """Test logging system integration with main application."""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary directory for log files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    def test_argument_parsing_with_logging_options(self):
        """Test argument parsing includes logging options."""
        test_args = [
            '--start-date', '2024-04-01',
            '--end-date', '2024-04-30',
            '--summary-type', 'weekly',
            '--log-level', 'DEBUG',
            '--no-console',
            '--dry-run'
        ]
        
        with patch('sys.argv', ['test'] + test_args):
            args = parse_arguments()
            
            assert args.start_date == date(2024, 4, 1)
            assert args.end_date == date(2024, 4, 30)
            assert args.summary_type == 'weekly'
            assert args.log_level == 'DEBUG'
            assert args.no_console is True
            assert args.dry_run is True
    
    def test_dry_run_functionality(self, temp_log_dir):
        """Test dry run mode with logging."""
        # Create mock arguments
        args = MagicMock()
        args.start_date = date(2024, 4, 1)
        args.end_date = date(2024, 4, 30)
        args.summary_type = 'weekly'
        args.base_path = temp_log_dir  # Use temp dir as base path
        
        # Create logger
        logger = create_logger_with_config(
            log_level="INFO",
            log_dir=temp_log_dir,
            console_output=False,
            file_output=True
        )
        
        # Mock environment variables
        with patch.dict(os.environ, {
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret'
        }):
            # Run dry run
            _perform_dry_run(args, logger)
        
        # Check that logger captured the dry run
        assert logger.log_file_path.exists()
        
        # Check for any configuration errors
        error_summary = logger.get_error_summary()
        # Should have minimal errors since we provided valid config
        assert error_summary["total_errors"] <= 1  # May have base path error
        
        logger.close()
    
    def test_dry_run_with_missing_config(self, temp_log_dir):
        """Test dry run mode with missing configuration."""
        # Create mock arguments with invalid base path
        args = MagicMock()
        args.start_date = date(2024, 4, 1)
        args.end_date = date(2024, 4, 30)
        args.summary_type = 'monthly'
        args.base_path = "/nonexistent/path"
        
        # Create logger
        logger = create_logger_with_config(
            log_level="DEBUG",
            log_dir=temp_log_dir,
            console_output=False,
            file_output=True
        )
        
        # Mock missing environment variables
        with patch.dict(os.environ, {}, clear=True):
            # Run dry run
            _perform_dry_run(args, logger)
        
        # Check that errors were logged
        error_summary = logger.get_error_summary()
        assert error_summary["total_errors"] >= 2  # Base path + AWS credentials
        
        # Check error categories
        categories = error_summary["categories"]
        assert "file_system" in categories
        assert "configuration_error" in categories
        
        logger.close()