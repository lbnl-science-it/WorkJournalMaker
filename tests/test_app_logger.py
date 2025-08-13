# ABOUTME: Comprehensive test suite for application logger component
# ABOUTME: Tests log rotation, cross-platform directory handling, and structured logging

import os
import tempfile
import shutil
import logging
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from desktop.app_logger import AppLogger


class TestAppLoggerInitialization:
    """Test cases for AppLogger initialization."""
    
    def test_app_logger_initialization_default(self):
        """Test AppLogger initializes with default values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = AppLogger(log_dir=temp_dir)
            
            assert logger.log_dir == Path(temp_dir)
            assert logger.app_name == "WorkJournalMaker"
            assert logger.max_bytes == 10 * 1024 * 1024  # 10MB
            assert logger.backup_count == 5
            assert logger.log_level == logging.INFO
    
    def test_app_logger_initialization_custom(self):
        """Test AppLogger initializes with custom values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = AppLogger(
                log_dir=temp_dir,
                app_name="TestApp",
                max_bytes=1024,
                backup_count=3,
                log_level=logging.DEBUG
            )
            
            assert logger.log_dir == Path(temp_dir)
            assert logger.app_name == "TestApp"
            assert logger.max_bytes == 1024
            assert logger.backup_count == 3
            assert logger.log_level == logging.DEBUG
    
    def test_app_logger_invalid_max_bytes(self):
        """Test AppLogger validation of max_bytes parameter."""
        with pytest.raises(ValueError, match="max_bytes must be positive"):
            AppLogger(max_bytes=0)
        
        with pytest.raises(ValueError, match="max_bytes must be positive"):
            AppLogger(max_bytes=-1)
    
    def test_app_logger_invalid_backup_count(self):
        """Test AppLogger validation of backup_count parameter."""
        with pytest.raises(ValueError, match="backup_count must be non-negative"):
            AppLogger(backup_count=-1)
    
    def test_app_logger_invalid_log_level(self):
        """Test AppLogger validation of log_level parameter."""
        with pytest.raises(ValueError, match="Invalid log level"):
            AppLogger(log_level=999)


class TestAppLoggerDirectoryHandling:
    """Test cases for log directory handling."""
    
    def test_log_directory_creation(self):
        """Test automatic creation of log directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "logs" / "subdir"
            
            logger = AppLogger(log_dir=str(log_dir))
            logger.setup_logging()
            
            assert log_dir.exists()
            assert log_dir.is_dir()
    
    def test_log_directory_permissions(self):
        """Test log directory permissions are set correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "logs"
            
            logger = AppLogger(log_dir=str(log_dir))
            logger.setup_logging()
            
            assert log_dir.exists()
            # Check that directory is readable and writable
            assert os.access(log_dir, os.R_OK | os.W_OK)
    
    def test_existing_log_directory(self):
        """Test handling of existing log directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir) / "existing_logs"
            log_dir.mkdir()
            
            # Create a test file in the directory
            test_file = log_dir / "test.txt"
            test_file.write_text("test content")
            
            logger = AppLogger(log_dir=str(log_dir))
            logger.setup_logging()
            
            # Directory should still exist with existing content
            assert log_dir.exists()
            assert test_file.exists()
    
    @patch('platform.system')
    def test_default_log_directory_windows(self, mock_platform):
        """Test default log directory on Windows."""
        mock_platform.return_value = 'Windows'
        
        logger = AppLogger()
        default_dir = logger.get_default_log_directory()
        
        # Should use LOCALAPPDATA or fallback to user home
        expected_patterns = [
            "AppData/Local/WorkJournalMaker/logs",
            "WorkJournalMaker/logs"
        ]
        
        assert any(pattern in str(default_dir) for pattern in expected_patterns)
    
    @patch('platform.system')
    def test_default_log_directory_macos(self, mock_platform):
        """Test default log directory on macOS."""
        mock_platform.return_value = 'Darwin'
        
        logger = AppLogger()
        default_dir = logger.get_default_log_directory()
        
        # Should use ~/Library/Logs/AppName
        assert "Library/Logs/WorkJournalMaker" in str(default_dir)
    
    @patch('platform.system')
    def test_default_log_directory_linux(self, mock_platform):
        """Test default log directory on Linux."""
        mock_platform.return_value = 'Linux'
        
        logger = AppLogger()
        default_dir = logger.get_default_log_directory()
        
        # Should use ~/.local/share/AppName/logs or fallback
        expected_patterns = [
            ".local/share/WorkJournalMaker/logs",
            "WorkJournalMaker/logs"
        ]
        
        assert any(pattern in str(default_dir) for pattern in expected_patterns)


class TestAppLoggerLoggingSetup:
    """Test cases for logging setup and configuration."""
    
    def test_setup_logging_creates_handlers(self):
        """Test that setup_logging creates appropriate handlers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = AppLogger(log_dir=temp_dir)
            logger.setup_logging()
            
            # Should have both file and console handlers
            handlers = logger.logger.handlers
            assert len(handlers) >= 2
            
            # Check for RotatingFileHandler and StreamHandler
            handler_types = [type(h).__name__ for h in handlers]
            assert 'RotatingFileHandler' in handler_types
            assert 'StreamHandler' in handler_types
    
    def test_setup_logging_file_rotation(self):
        """Test file rotation configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = AppLogger(
                log_dir=temp_dir,
                max_bytes=1024,
                backup_count=3
            )
            logger.setup_logging()
            
            # Find the RotatingFileHandler
            file_handler = None
            for handler in logger.logger.handlers:
                if hasattr(handler, 'maxBytes'):
                    file_handler = handler
                    break
            
            assert file_handler is not None
            assert file_handler.maxBytes == 1024
            assert file_handler.backupCount == 3
    
    def test_setup_logging_log_format(self):
        """Test log format configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = AppLogger(log_dir=temp_dir)
            logger.setup_logging()
            
            # Check that handlers have formatters
            for handler in logger.logger.handlers:
                assert handler.formatter is not None
                
                # Check format includes expected fields
                format_str = handler.formatter._fmt
                expected_fields = ['%(asctime)s', '%(name)s', '%(levelname)s', '%(message)s']
                for field in expected_fields:
                    assert field in format_str
    
    def test_setup_logging_log_level(self):
        """Test log level configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = AppLogger(log_dir=temp_dir, log_level=logging.DEBUG)
            logger.setup_logging()
            
            assert logger.logger.level == logging.DEBUG
            
            # All handlers should also respect the log level
            for handler in logger.logger.handlers:
                assert handler.level == logging.DEBUG
    
    def test_multiple_setup_calls(self):
        """Test that multiple setup_logging calls don't create duplicate handlers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = AppLogger(log_dir=temp_dir)
            
            logger.setup_logging()
            initial_handler_count = len(logger.logger.handlers)
            
            logger.setup_logging()
            final_handler_count = len(logger.logger.handlers)
            
            assert initial_handler_count == final_handler_count


class TestAppLoggerLoggingFunctionality:
    """Test cases for actual logging functionality."""
    
    def test_log_messages_to_file(self):
        """Test that log messages are written to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = AppLogger(log_dir=temp_dir, app_name="TestApp")
            logger.setup_logging()
            
            test_message = "Test log message"
            logger.info(test_message)
            
            # Force flush
            for handler in logger.logger.handlers:
                handler.flush()
            
            # Check that log file was created and contains message
            log_files = list(Path(temp_dir).glob("*.log"))
            assert len(log_files) > 0
            
            log_content = log_files[0].read_text()
            assert test_message in log_content
    
    def test_different_log_levels(self):
        """Test logging at different levels."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = AppLogger(log_dir=temp_dir, log_level=logging.DEBUG)
            logger.setup_logging()
            
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")
            
            # Force flush
            for handler in logger.logger.handlers:
                handler.flush()
            
            # Check that all messages are in the log file
            log_files = list(Path(temp_dir).glob("*.log"))
            log_content = log_files[0].read_text()
            
            assert "Debug message" in log_content
            assert "Info message" in log_content
            assert "Warning message" in log_content
            assert "Error message" in log_content
            assert "Critical message" in log_content
    
    def test_log_level_filtering(self):
        """Test that log level filtering works correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = AppLogger(log_dir=temp_dir, log_level=logging.WARNING)
            logger.setup_logging()
            
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            
            # Force flush
            for handler in logger.logger.handlers:
                handler.flush()
            
            # Check that only WARNING and ERROR messages are in the log
            log_files = list(Path(temp_dir).glob("*.log"))
            log_content = log_files[0].read_text()
            
            assert "Debug message" not in log_content
            assert "Info message" not in log_content
            assert "Warning message" in log_content
            assert "Error message" in log_content


class TestAppLoggerFileRotation:
    """Test cases for log file rotation."""
    
    def test_file_rotation_on_size_limit(self):
        """Test that log files rotate when size limit is reached."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set very small max_bytes to trigger rotation
            logger = AppLogger(
                log_dir=temp_dir,
                max_bytes=100,  # 100 bytes
                backup_count=2
            )
            logger.setup_logging()
            
            # Write messages until rotation occurs
            for i in range(20):
                logger.info(f"This is a test message number {i} that should cause rotation")
            
            # Force flush
            for handler in logger.logger.handlers:
                handler.flush()
            
            # Check that multiple log files exist
            log_files = list(Path(temp_dir).glob("*.log*"))
            assert len(log_files) > 1
    
    def test_backup_count_limit(self):
        """Test that backup count limit is respected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = AppLogger(
                log_dir=temp_dir,
                max_bytes=50,  # Very small to force frequent rotation
                backup_count=2
            )
            logger.setup_logging()
            
            # Write many messages to force multiple rotations
            for i in range(100):
                logger.info(f"Message {i} with enough content to trigger rotation frequently")
            
            # Force flush
            for handler in logger.logger.handlers:
                handler.flush()
            
            # Should have at most backup_count + 1 files (current + backups)
            log_files = list(Path(temp_dir).glob("*.log*"))
            assert len(log_files) <= 3  # 1 current + 2 backups


class TestAppLoggerContextManager:
    """Test cases for context manager support."""
    
    def test_context_manager_support(self):
        """Test basic context manager functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with AppLogger(log_dir=temp_dir) as logger:
                assert logger is not None
                logger.setup_logging()
                logger.info("Test message in context")
    
    def test_context_manager_cleanup(self):
        """Test context manager cleanup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = AppLogger(log_dir=temp_dir)
            
            with logger:
                logger.setup_logging()
                logger.info("Test message")
                handler_count = len(logger.logger.handlers)
                assert handler_count > 0
            
            # After context, handlers should be cleaned up
            assert len(logger.logger.handlers) == 0


class TestAppLoggerErrorHandling:
    """Test cases for error handling scenarios."""
    
    def test_permission_denied_log_directory(self):
        """Test handling when log directory cannot be created due to permissions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file where we want to create a directory
            blocked_path = Path(temp_dir) / "blocked"
            blocked_path.write_text("blocking file")
            
            # Try to create logger with path that conflicts with existing file
            logger = AppLogger(log_dir=str(blocked_path))
            
            # Should handle the error gracefully
            with pytest.raises(OSError):
                logger.setup_logging()
    
    def test_disk_full_simulation(self):
        """Test handling when disk is full (simulated)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = AppLogger(log_dir=temp_dir)
            logger.setup_logging()
            
            # Mock a file handler that raises OSError (disk full)
            with patch.object(logger.logger.handlers[0], 'emit') as mock_emit:
                mock_emit.side_effect = OSError("No space left on device")
                
                # Should not raise exception from logger perspective
                # (logging module will handle the exception internally)
                try:
                    logger.error("Test message during disk full")
                except OSError:
                    # This is expected behavior - logging will propagate the exception
                    pass
    
    def test_invalid_log_directory_path(self):
        """Test handling of invalid log directory paths."""        
        # Test with empty string
        with pytest.raises(ValueError, match="log_dir cannot be None or empty"):
            AppLogger(log_dir="")


class TestAppLoggerUtilityMethods:
    """Test cases for utility methods."""
    
    def test_get_log_files(self):
        """Test getting list of log files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = AppLogger(log_dir=temp_dir, app_name="TestApp")
            logger.setup_logging()
            
            # Log some messages to create files
            logger.info("Test message")
            for handler in logger.logger.handlers:
                handler.flush()
            
            log_files = logger.get_log_files()
            assert len(log_files) > 0
            assert all(f.suffix == '.log' or '.log.' in f.name for f in log_files)
    
    def test_get_log_size(self):
        """Test getting total size of log files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = AppLogger(log_dir=temp_dir)
            logger.setup_logging()
            
            # Log some messages
            for i in range(10):
                logger.info(f"Test message {i}")
            
            for handler in logger.logger.handlers:
                handler.flush()
            
            total_size = logger.get_log_size()
            assert total_size > 0
    
    def test_clear_logs(self):
        """Test clearing all log files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = AppLogger(log_dir=temp_dir)
            logger.setup_logging()
            
            # Create some log content
            logger.info("Test message")
            for handler in logger.logger.handlers:
                handler.flush()
            
            # Verify logs exist
            assert len(logger.get_log_files()) > 0
            
            # Clear logs
            logger.clear_logs()
            
            # Verify logs are cleared
            assert len(logger.get_log_files()) == 0
    
    def test_configure_console_output(self):
        """Test configuring console output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = AppLogger(log_dir=temp_dir)
            logger.setup_logging()
            
            # Test disabling console output
            logger.configure_console_output(enabled=False)
            
            # Should have only file handler
            console_handlers = [h for h in logger.logger.handlers if hasattr(h, 'stream')]
            assert len(console_handlers) == 0
            
            # Test re-enabling console output
            logger.configure_console_output(enabled=True)
            
            # Should have console handler again
            console_handlers = [h for h in logger.logger.handlers if hasattr(h, 'stream')]
            assert len(console_handlers) > 0


class TestAppLoggerIntegration:
    """Integration tests for AppLogger."""
    
    def test_complete_logging_workflow(self):
        """Test complete logging workflow from setup to cleanup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = AppLogger(
                log_dir=temp_dir,
                app_name="IntegrationTest",
                max_bytes=1024,
                backup_count=2,
                log_level=logging.DEBUG
            )
            
            # Setup logging
            logger.setup_logging()
            
            # Log messages at different levels
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            
            # Check log files
            log_files = logger.get_log_files()
            assert len(log_files) > 0
            
            # Check total size
            total_size = logger.get_log_size()
            assert total_size > 0
            
            # Cleanup
            logger.clear_logs()
            assert len(logger.get_log_files()) == 0
    
    def test_concurrent_logging_safety(self):
        """Test that logging is thread-safe."""
        import threading
        import time
        
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = AppLogger(log_dir=temp_dir)
            logger.setup_logging()
            
            def log_worker(worker_id):
                for i in range(10):
                    logger.info(f"Worker {worker_id}: Message {i}")
                    time.sleep(0.01)  # Small delay
            
            # Create multiple threads
            threads = []
            for i in range(3):
                thread = threading.Thread(target=log_worker, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Force flush
            for handler in logger.logger.handlers:
                handler.flush()
            
            # Verify all messages were logged
            log_files = logger.get_log_files()
            assert len(log_files) > 0
            
            log_content = log_files[0].read_text()
            # Should have 30 messages total (3 workers * 10 messages each)
            message_count = log_content.count("Worker")
            assert message_count == 30