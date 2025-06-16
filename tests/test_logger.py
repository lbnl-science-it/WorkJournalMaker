"""
Tests for the Comprehensive Error Handling & Logging System - Phase 7

This module contains comprehensive tests for the logging system, including
error categorization, progress tracking, graceful degradation, and
error reporting functionality.
"""

import pytest
import tempfile
import time
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime

from logger import (
    JournalSummarizerLogger, LogConfig, LogLevel, ErrorCategory,
    ProcessingProgress, ErrorReport, create_default_logger,
    create_logger_with_config
)


class TestLogConfig:
    """Test LogConfig dataclass functionality."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = LogConfig()
        
        assert config.level == LogLevel.INFO
        assert config.console_output is True
        assert config.file_output is True
        assert config.log_dir == "~/Desktop/worklogs/summaries/error_logs/"
        assert config.include_timestamps is True
        assert config.include_module_names is True
        assert config.max_file_size_mb == 10
        assert config.backup_count == 5
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = LogConfig(
            level=LogLevel.DEBUG,
            console_output=False,
            file_output=True,
            log_dir="/tmp/test_logs/",
            max_file_size_mb=5
        )
        
        assert config.level == LogLevel.DEBUG
        assert config.console_output is False
        assert config.file_output is True
        assert config.log_dir == "/tmp/test_logs/"
        assert config.max_file_size_mb == 5


class TestErrorCategory:
    """Test ErrorCategory enum functionality."""
    
    def test_error_categories(self):
        """Test all error categories are defined."""
        expected_categories = {
            "file_system", "api_failure", "processing_error",
            "configuration_error", "network_error", "validation_error"
        }
        
        actual_categories = {category.value for category in ErrorCategory}
        assert actual_categories == expected_categories


class TestProcessingProgress:
    """Test ProcessingProgress dataclass functionality."""
    
    def test_default_progress(self):
        """Test default progress values."""
        progress = ProcessingProgress("Test Phase", 8, 0.5, 0.25)
        
        assert progress.current_phase == "Test Phase"
        assert progress.total_phases == 8
        assert progress.current_phase_progress == 0.5
        assert progress.overall_progress == 0.25
        assert progress.estimated_time_remaining is None
        assert progress.files_processed == 0
        assert progress.total_files == 0
        assert progress.errors_encountered == 0
        assert isinstance(progress.start_time, float)
    
    def test_progress_with_values(self):
        """Test progress with specific values."""
        progress = ProcessingProgress(
            "Content Processing", 8, 0.75, 0.40,
            estimated_time_remaining=120.5,
            files_processed=15,
            total_files=20,
            errors_encountered=2
        )
        
        assert progress.current_phase == "Content Processing"
        assert progress.current_phase_progress == 0.75
        assert progress.overall_progress == 0.40
        assert progress.estimated_time_remaining == 120.5
        assert progress.files_processed == 15
        assert progress.total_files == 20
        assert progress.errors_encountered == 2


class TestErrorReport:
    """Test ErrorReport dataclass functionality."""
    
    def test_basic_error_report(self):
        """Test basic error report creation."""
        report = ErrorReport(
            category=ErrorCategory.FILE_SYSTEM,
            message="File not found"
        )
        
        assert report.category == ErrorCategory.FILE_SYSTEM
        assert report.message == "File not found"
        assert report.file_path is None
        assert isinstance(report.timestamp, datetime)
        assert report.exception_type is None
        assert report.stack_trace is None
        assert report.recovery_action is None
        assert report.phase is None
    
    def test_detailed_error_report(self):
        """Test detailed error report with all fields."""
        test_path = Path("/test/file.txt")
        report = ErrorReport(
            category=ErrorCategory.API_FAILURE,
            message="API request failed",
            file_path=test_path,
            exception_type="ConnectionError",
            stack_trace="Traceback...",
            recovery_action="Check network connection",
            phase="LLM Analysis"
        )
        
        assert report.category == ErrorCategory.API_FAILURE
        assert report.message == "API request failed"
        assert report.file_path == test_path
        assert report.exception_type == "ConnectionError"
        assert report.stack_trace == "Traceback..."
        assert report.recovery_action == "Check network connection"
        assert report.phase == "LLM Analysis"


class TestJournalSummarizerLogger:
    """Test JournalSummarizerLogger functionality."""
    
    @pytest.fixture
    def temp_log_dir(self):
        """Create temporary directory for log files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def test_config(self, temp_log_dir):
        """Create test configuration with temporary directory."""
        return LogConfig(
            level=LogLevel.DEBUG,
            log_dir=temp_log_dir,
            console_output=False,  # Disable console for tests
            file_output=True
        )
    
    def test_logger_initialization(self, test_config):
        """Test logger initialization."""
        logger = JournalSummarizerLogger(test_config)
        
        assert logger.config == test_config
        assert isinstance(logger.log_file_path, Path)
        assert logger.log_file_path.exists()
        assert logger.progress.current_phase == "Initialization"
        assert logger.progress.total_phases == 8
        assert len(logger.error_reports) == 0
    
    def test_log_file_creation(self, test_config):
        """Test log file creation with timestamp."""
        logger = JournalSummarizerLogger(test_config)
        
        # Check log file exists and has correct naming pattern
        assert logger.log_file_path.exists()
        assert "journal_summarizer_" in logger.log_file_path.name
        assert logger.log_file_path.suffix == ".log"
        
        # Check log directory was created
        assert logger.log_file_path.parent.exists()
    
    def test_phase_tracking(self, test_config):
        """Test phase start and completion tracking."""
        logger = JournalSummarizerLogger(test_config)
        
        # Start a phase
        logger.start_phase("Test Phase")
        assert logger.progress.current_phase == "Test Phase"
        assert "Test Phase" in logger.phase_start_times
        
        # Complete the phase
        time.sleep(0.01)  # Small delay to measure time
        logger.complete_phase("Test Phase")
        
        # Check that phase was tracked
        assert "Test Phase" in logger.phase_start_times
    
    def test_progress_tracking(self, test_config):
        """Test progress calculation and tracking."""
        logger = JournalSummarizerLogger(test_config)
        
        # Update progress
        logger.update_progress("Content Processing", 0.5, 10, 20)
        
        assert logger.progress.current_phase == "Content Processing"
        assert logger.progress.current_phase_progress == 0.5
        assert logger.progress.files_processed == 10
        assert logger.progress.total_files == 20
        assert 0.0 <= logger.progress.overall_progress <= 1.0
    
    def test_error_categorization(self, test_config):
        """Test error categorization and tracking."""
        logger = JournalSummarizerLogger(test_config)
        
        # Log different types of errors
        logger.log_error_with_category(
            ErrorCategory.FILE_SYSTEM,
            "File not found",
            file_path=Path("/test/file.txt"),
            recovery_action="Check file path"
        )
        
        logger.log_error_with_category(
            ErrorCategory.API_FAILURE,
            "API timeout",
            exception=ConnectionError("Connection timeout")
        )
        
        # Check error reports
        assert len(logger.error_reports) == 2
        assert logger.progress.errors_encountered == 2
        
        # Check first error
        first_error = logger.error_reports[0]
        assert first_error.category == ErrorCategory.FILE_SYSTEM
        assert first_error.message == "File not found"
        assert first_error.file_path == Path("/test/file.txt")
        assert first_error.recovery_action == "Check file path"
        
        # Check second error
        second_error = logger.error_reports[1]
        assert second_error.category == ErrorCategory.API_FAILURE
        assert second_error.message == "API timeout"
        assert second_error.exception_type == "ConnectionError"
    
    def test_warning_logging(self, test_config):
        """Test warning logging with categorization."""
        logger = JournalSummarizerLogger(test_config)
        
        # Log a warning
        logger.log_warning_with_category(
            ErrorCategory.PROCESSING_ERROR,
            "File encoding detected as unusual",
            file_path=Path("/test/file.txt")
        )
        
        # Warnings shouldn't be added to error reports
        assert len(logger.error_reports) == 0
        assert logger.progress.errors_encountered == 0
    
    def test_error_summary(self, test_config):
        """Test error summary generation."""
        logger = JournalSummarizerLogger(test_config)
        
        # Add some errors
        logger.log_error_with_category(ErrorCategory.FILE_SYSTEM, "Error 1")
        logger.log_error_with_category(ErrorCategory.FILE_SYSTEM, "Error 2")
        logger.log_error_with_category(ErrorCategory.API_FAILURE, "Error 3")
        
        # Get error summary
        summary = logger.get_error_summary()
        
        assert summary["total_errors"] == 3
        assert summary["categories"]["file_system"] == 2
        assert summary["categories"]["api_failure"] == 1
        assert len(summary["recent_errors"]) == 3
        
        # Check recent error structure
        recent_error = summary["recent_errors"][0]
        assert "category" in recent_error
        assert "message" in recent_error
        assert "timestamp" in recent_error
        assert "phase" in recent_error
    
    def test_should_continue_processing(self, test_config):
        """Test processing continuation logic."""
        logger = JournalSummarizerLogger(test_config)
        
        # Should continue with no errors
        assert logger.should_continue_processing() is True
        
        # Add non-critical errors
        for i in range(5):
            logger.log_error_with_category(ErrorCategory.FILE_SYSTEM, f"Error {i}")
        
        assert logger.should_continue_processing() is True
        
        # Add critical errors
        for i in range(15):
            logger.log_error_with_category(ErrorCategory.API_FAILURE, f"Critical Error {i}")
        
        assert logger.should_continue_processing() is False
    
    def test_progress_bar_creation(self, test_config):
        """Test progress bar formatting."""
        logger = JournalSummarizerLogger(test_config)
        
        # Test progress bar at different completion levels
        bar_0 = logger._create_progress_bar(0.0, width=10, prefix="Start", suffix="0%")
        bar_50 = logger._create_progress_bar(0.5, width=10, prefix="Half", suffix="50%")
        bar_100 = logger._create_progress_bar(1.0, width=10, prefix="Done", suffix="100%")
        
        assert "Start" in bar_0 and "0%" in bar_0
        assert "Half" in bar_50 and "50%" in bar_50
        assert "Done" in bar_100 and "100%" in bar_100
        
        # Check bar contains progress characters
        assert "░" in bar_0  # Empty progress
        assert "█" in bar_50 and "░" in bar_50  # Partial progress
        assert "█" in bar_100  # Full progress
    
    @patch('sys.stdout')
    def test_progress_display(self, mock_stdout, test_config):
        """Test progress bar display to console."""
        logger = JournalSummarizerLogger(test_config)
        
        # Update progress to trigger display
        logger.update_progress("Test Phase", 0.5, 5, 10)
        
        # Check that progress was displayed (print was called)
        # Note: This is a basic test since we're mocking stdout
        assert logger.progress.current_phase == "Test Phase"
        assert logger.progress.files_processed == 5
        assert logger.progress.total_files == 10
    
    def test_error_report_generation(self, test_config):
        """Test comprehensive error report generation."""
        logger = JournalSummarizerLogger(test_config)
        
        # Add various errors
        logger.log_error_with_category(
            ErrorCategory.FILE_SYSTEM, 
            "File permission denied",
            file_path=Path("/test/file1.txt"),
            recovery_action="Check file permissions"
        )
        logger.log_error_with_category(
            ErrorCategory.API_FAILURE,
            "API rate limit exceeded"
        )
        
        # Generate report
        report = logger.generate_error_report()
        
        assert "## Error Report" in report
        assert "Total Errors: 2" in report
        assert "File System Errors" in report
        assert "Api Failure Errors" in report
        assert "File permission denied" in report
        assert "API rate limit exceeded" in report
        assert "Check file permissions" in report
    
    def test_empty_error_report(self, test_config):
        """Test error report generation with no errors."""
        logger = JournalSummarizerLogger(test_config)
        
        report = logger.generate_error_report()
        assert report == "No errors encountered during processing."
    
    def test_logger_cleanup(self, test_config):
        """Test logger cleanup and resource management."""
        logger = JournalSummarizerLogger(test_config)
        
        # Add some activity
        logger.start_phase("Test Phase")
        logger.log_error_with_category(ErrorCategory.FILE_SYSTEM, "Test error")
        
        # Close logger
        logger.close()
        
        # Check that handlers were cleared
        assert len(logger.logger.handlers) == 0


class TestLoggerFactoryFunctions:
    """Test logger factory functions."""
    
    def test_create_default_logger(self):
        """Test default logger creation."""
        logger = create_default_logger()
        
        assert isinstance(logger, JournalSummarizerLogger)
        assert logger.config.level == LogLevel.INFO
        assert logger.config.console_output is True
        assert logger.config.file_output is True
    
    def test_create_logger_with_config(self):
        """Test logger creation with custom configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = create_logger_with_config(
                log_level="DEBUG",
                log_dir=temp_dir,
                console_output=False,
                file_output=True
            )
            
            assert isinstance(logger, JournalSummarizerLogger)
            assert logger.config.level == LogLevel.DEBUG
            assert logger.config.console_output is False
            assert logger.config.file_output is True
            assert temp_dir in str(logger.config.log_dir)


class TestGracefulDegradation:
    """Test graceful degradation scenarios."""
    
    @pytest.fixture
    def test_config(self):
        """Create test configuration for degradation tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield LogConfig(
                level=LogLevel.INFO,
                log_dir=temp_dir,
                console_output=False,
                file_output=True
            )
    
    def test_file_permission_error_handling(self, test_config):
        """Test handling of file permission errors."""
        # Create logger first
        logger = JournalSummarizerLogger(test_config)
        
        # Simulate file permission error
        logger.log_error_with_category(
            ErrorCategory.FILE_SYSTEM,
            "Permission denied accessing log file",
            recovery_action="Check file permissions and disk space"
        )
        
        # Logger should continue functioning
        assert len(logger.error_reports) == 1
        assert logger.should_continue_processing() is True
    
    def test_api_failure_recovery(self, test_config):
        """Test recovery from API failures."""
        logger = JournalSummarizerLogger(test_config)
        
        # Simulate multiple API failures
        for i in range(5):
            logger.log_error_with_category(
                ErrorCategory.API_FAILURE,
                f"API call {i} failed",
                recovery_action="Retry with exponential backoff"
            )
        
        # Should still allow processing to continue
        assert logger.should_continue_processing() is True
        assert len(logger.error_reports) == 5
        
        # But too many critical errors should stop processing
        for i in range(10):
            logger.log_error_with_category(
                ErrorCategory.API_FAILURE,
                f"Critical API failure {i}"
            )
        
        assert logger.should_continue_processing() is False
    
    def test_processing_error_accumulation(self, test_config):
        """Test handling of accumulated processing errors."""
        logger = JournalSummarizerLogger(test_config)
        
        # Add many non-critical errors
        for i in range(20):
            logger.log_error_with_category(
                ErrorCategory.PROCESSING_ERROR,
                f"Processing error {i}",
                file_path=Path(f"/test/file_{i}.txt")
            )
        
        # Should still continue processing
        assert logger.should_continue_processing() is True
        assert len(logger.error_reports) == 20
        
        # Error summary should handle large numbers
        summary = logger.get_error_summary()
        assert summary["total_errors"] == 20
        assert summary["categories"]["processing_error"] == 20
        assert len(summary["recent_errors"]) == 5  # Only last 5