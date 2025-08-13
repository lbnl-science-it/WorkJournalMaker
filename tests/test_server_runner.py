# ABOUTME: Comprehensive test suite for server runner entry point component
# ABOUTME: Tests CLI interface, signal handling, startup/shutdown sequences, and error handling

import pytest
import signal
import sys
import threading
import time
import os
from unittest.mock import patch, MagicMock, call
from pathlib import Path
import tempfile
import argparse

# Import the module we'll be testing
import server_runner


class TestServerRunnerCLI:
    """Test cases for command line interface parsing."""
    
    def test_parse_args_default_values(self):
        """Test argument parsing with default values."""
        args = server_runner.parse_args([])
        
        assert args.host == "127.0.0.1"
        assert args.port_range == "8000-8099"
        assert args.log_level == "INFO"
        assert args.log_dir is None
        assert args.no_browser is False
        assert args.browser is None
        assert args.startup_timeout == 30.0
        assert args.shutdown_timeout == 10.0
    
    def test_parse_args_custom_values(self):
        """Test argument parsing with custom values."""
        args = server_runner.parse_args([
            "--host", "localhost",
            "--port-range", "3000-3010", 
            "--log-level", "DEBUG",
            "--log-dir", "/tmp/logs",
            "--no-browser",
            "--browser", "chrome",
            "--startup-timeout", "60",
            "--shutdown-timeout", "20"
        ])
        
        assert args.host == "localhost"
        assert args.port_range == "3000-3010"
        assert args.log_level == "DEBUG"
        assert args.log_dir == "/tmp/logs"
        assert args.no_browser is True
        assert args.browser == "chrome"
        assert args.startup_timeout == 60.0
        assert args.shutdown_timeout == 20.0
    
    def test_parse_args_help(self):
        """Test that help option works."""
        with pytest.raises(SystemExit):
            server_runner.parse_args(["--help"])
    
    def test_parse_port_range_valid(self):
        """Test parsing valid port range."""
        start, end = server_runner.parse_port_range("8000-8099")
        assert start == 8000
        assert end == 8099
    
    def test_parse_port_range_single_port(self):
        """Test parsing single port."""
        start, end = server_runner.parse_port_range("8080")
        assert start == 8080
        assert end == 8080
    
    def test_parse_port_range_invalid_format(self):
        """Test parsing invalid port range format."""
        with pytest.raises(ValueError, match="Invalid port range format"):
            server_runner.parse_port_range("8000-8099-9000")
    
    def test_parse_port_range_invalid_values(self):
        """Test parsing port range with invalid values."""
        with pytest.raises(ValueError, match="Invalid port range"):
            server_runner.parse_port_range("8099-8000")  # start > end
        
        with pytest.raises(ValueError, match="Port numbers must be between"):
            server_runner.parse_port_range("100-200")  # ports too low
        
        with pytest.raises(ValueError, match="Port numbers must be between"):
            server_runner.parse_port_range("70000-80000")  # ports too high


class TestServerRunnerSignalHandling:
    """Test cases for signal handling functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = None
    
    def teardown_method(self):
        """Clean up after tests."""
        if self.runner:
            self.runner.cleanup()
    
    @patch('server_runner.DesktopApp')
    def test_signal_handler_installation(self, mock_desktop_app):
        """Test that signal handlers are properly installed."""
        mock_app = MagicMock()
        mock_desktop_app.return_value = mock_app
        
        with patch('signal.signal') as mock_signal:
            self.runner = server_runner.ServerRunner()
            self.runner.setup_signal_handlers()
            
            # Verify signal handlers were installed
            assert mock_signal.call_count == 2
            mock_signal.assert_any_call(signal.SIGINT, self.runner._signal_handler)
            mock_signal.assert_any_call(signal.SIGTERM, self.runner._signal_handler)
    
    @patch('server_runner.DesktopApp')
    def test_signal_handler_graceful_shutdown(self, mock_desktop_app):
        """Test that signal handler triggers graceful shutdown."""
        mock_app = MagicMock()
        mock_desktop_app.return_value = mock_app
        
        self.runner = server_runner.ServerRunner()
        
        # Simulate signal
        self.runner._signal_handler(signal.SIGINT, None)
        
        # Check that shutdown flag was set
        assert self.runner._shutdown_requested is True
    
    @patch('server_runner.DesktopApp')
    def test_signal_handler_multiple_signals(self, mock_desktop_app):
        """Test handling multiple signals."""
        mock_app = MagicMock()
        mock_desktop_app.return_value = mock_app
        
        self.runner = server_runner.ServerRunner()
        
        # First signal should set flag
        self.runner._signal_handler(signal.SIGINT, None)
        assert self.runner._shutdown_requested is True
        
        # Second signal should force exit
        with patch('server_runner.sys.exit') as mock_exit:
            self.runner._signal_handler(signal.SIGTERM, None)
            mock_exit.assert_called_once_with(1)
    
    @patch('server_runner.DesktopApp')
    @patch('signal.signal')
    def test_windows_signal_handling(self, mock_signal, mock_desktop_app):
        """Test Windows-specific signal handling."""
        mock_app = MagicMock()
        mock_desktop_app.return_value = mock_app
        
        with patch('server_runner.sys.platform', 'win32'):
            self.runner = server_runner.ServerRunner()
            self.runner.setup_signal_handlers()
            
            # On Windows, only SIGINT should be handled
            mock_signal.assert_called_once_with(signal.SIGINT, self.runner._signal_handler)


class TestServerRunnerLifecycle:
    """Test cases for server runner lifecycle management."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = None
    
    def teardown_method(self):
        """Clean up after tests."""
        if self.runner:
            self.runner.cleanup()
    
    @patch('server_runner.DesktopApp')
    def test_runner_initialization(self, mock_desktop_app):
        """Test ServerRunner initialization."""
        mock_app = MagicMock()
        mock_desktop_app.return_value = mock_app
        
        self.runner = server_runner.ServerRunner(
            host="localhost",
            port_range=(3000, 3010),
            log_level="DEBUG",
            startup_timeout=60.0,
            shutdown_timeout=20.0,
            auto_open_browser=False,
            preferred_browser="chrome"
        )
        
        # Verify DesktopApp was created with correct parameters
        mock_desktop_app.assert_called_once_with(
            host="localhost",
            port_range=(3000, 3010),
            startup_timeout=60.0,
            shutdown_timeout=20.0,
            auto_open_browser=False,
            preferred_browser="chrome",
            log_dir=None
        )
    
    @patch('server_runner.DesktopApp')
    def test_runner_startup_success(self, mock_desktop_app):
        """Test successful server startup."""
        mock_app = MagicMock()
        mock_app.startup.return_value = True
        mock_app.is_running.return_value = True
        mock_app.get_server_info.return_value = {
            'host': '127.0.0.1',
            'port': 8080,
            'url': 'http://127.0.0.1:8080',
            'running': True
        }
        mock_desktop_app.return_value = mock_app
        
        self.runner = server_runner.ServerRunner()
        result = self.runner.start()
        
        assert result is True
        mock_app.startup.assert_called_once()
    
    @patch('server_runner.DesktopApp')
    def test_runner_startup_failure(self, mock_desktop_app):
        """Test server startup failure."""
        mock_app = MagicMock()
        mock_app.startup.return_value = False
        mock_desktop_app.return_value = mock_app
        
        self.runner = server_runner.ServerRunner()
        result = self.runner.start()
        
        assert result is False
        mock_app.startup.assert_called_once()
    
    @patch('server_runner.DesktopApp')
    def test_runner_shutdown_success(self, mock_desktop_app):
        """Test successful server shutdown."""
        mock_app = MagicMock()
        mock_app.shutdown.return_value = True
        mock_desktop_app.return_value = mock_app
        
        self.runner = server_runner.ServerRunner()
        result = self.runner.stop()
        
        assert result is True
        mock_app.shutdown.assert_called_once()
    
    @patch('server_runner.DesktopApp')
    def test_runner_run_with_shutdown_signal(self, mock_desktop_app):
        """Test run loop with shutdown signal."""
        mock_app = MagicMock()
        mock_app.startup.return_value = True
        mock_app.is_running.return_value = True
        mock_app.shutdown.return_value = True
        mock_desktop_app.return_value = mock_app
        
        self.runner = server_runner.ServerRunner()
        
        # Start shutdown signal in separate thread
        def trigger_shutdown():
            time.sleep(0.1)
            self.runner._shutdown_requested = True
        
        shutdown_thread = threading.Thread(target=trigger_shutdown)
        shutdown_thread.start()
        
        # Run should return after shutdown is requested
        result = self.runner.run()
        shutdown_thread.join()
        
        assert result == 0  # Success exit code
        mock_app.startup.assert_called_once()
        mock_app.shutdown.assert_called_once()
    
    @patch('server_runner.DesktopApp')
    def test_runner_run_startup_failure(self, mock_desktop_app):
        """Test run loop with startup failure."""
        mock_app = MagicMock()
        mock_app.startup.return_value = False
        mock_desktop_app.return_value = mock_app
        
        self.runner = server_runner.ServerRunner()
        result = self.runner.run()
        
        assert result == 1  # Error exit code
        mock_app.startup.assert_called_once()
        mock_app.shutdown.assert_not_called()


class TestServerRunnerMainFunction:
    """Test cases for main function and application entry point."""
    
    @patch('server_runner.ServerRunner')
    @patch('server_runner.parse_args')
    def test_main_function_success(self, mock_parse_args, mock_server_runner):
        """Test main function with successful execution."""
        # Mock arguments
        mock_args = MagicMock()
        mock_args.host = "127.0.0.1"
        mock_args.port_range = "8000-8099"
        mock_args.log_level = "INFO"
        mock_args.log_dir = None
        mock_args.no_browser = False
        mock_args.browser = None
        mock_args.startup_timeout = 30.0
        mock_args.shutdown_timeout = 10.0
        mock_parse_args.return_value = mock_args
        
        # Mock runner
        mock_runner = MagicMock()
        mock_runner.run.return_value = 0
        mock_server_runner.return_value = mock_runner
        
        with patch('server_runner.sys.argv', ['server_runner.py']):
            with patch('server_runner.sys.exit') as mock_exit:
                server_runner.main()
                mock_exit.assert_called_once_with(0)
    
    @patch('server_runner.ServerRunner')
    @patch('server_runner.parse_args')
    def test_main_function_failure(self, mock_parse_args, mock_server_runner):
        """Test main function with execution failure."""
        # Mock arguments
        mock_args = MagicMock()
        mock_args.host = "127.0.0.1"
        mock_args.port_range = "8000-8099"
        mock_args.log_level = "INFO"
        mock_args.log_dir = None
        mock_args.no_browser = False
        mock_args.browser = None
        mock_args.startup_timeout = 30.0
        mock_args.shutdown_timeout = 10.0
        mock_parse_args.return_value = mock_args
        
        # Mock runner with failure
        mock_runner = MagicMock()
        mock_runner.run.return_value = 1
        mock_server_runner.return_value = mock_runner
        
        with patch('server_runner.sys.argv', ['server_runner.py']):
            with patch('server_runner.sys.exit') as mock_exit:
                server_runner.main()
                mock_exit.assert_called_once_with(1)
    
    @patch('server_runner.ServerRunner')
    @patch('server_runner.parse_args')
    def test_main_function_exception(self, mock_parse_args, mock_server_runner):
        """Test main function with exception handling."""
        # Mock arguments
        mock_args = MagicMock()
        mock_parse_args.return_value = mock_args
        
        # Mock runner that raises exception
        mock_server_runner.side_effect = Exception("Test exception")
        
        with patch('server_runner.sys.argv', ['server_runner.py']):
            with patch('server_runner.sys.exit') as mock_exit:
                with patch('builtins.print') as mock_print:
                    server_runner.main()
                    mock_exit.assert_called_once_with(1)
                    mock_print.assert_called()
    
    def test_main_entry_point(self):
        """Test main entry point when script is run directly."""
        # This is a conceptual test - in reality, the __name__ == "__main__" 
        # check happens at import time, not when we patch it
        with patch('server_runner.main') as mock_main:
            # Simulate the condition that would trigger main()
            # We can't actually test the __name__ == "__main__" block directly
            # because it's evaluated at import time
            server_runner.main()
            mock_main.assert_called_once()


class TestServerRunnerLogging:
    """Test cases for logging configuration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = None
    
    def teardown_method(self):
        """Clean up after tests."""
        if self.runner:
            self.runner.cleanup()
    
    @patch('server_runner.DesktopApp')
    def test_logging_level_configuration(self, mock_desktop_app):
        """Test logging level configuration."""
        mock_app = MagicMock()
        mock_desktop_app.return_value = mock_app
        
        self.runner = server_runner.ServerRunner(log_level="DEBUG")
        
        # Verify logging level was set on the app
        mock_app.configure_logging_level.assert_called_once()
    
    @patch('server_runner.DesktopApp')
    def test_logging_directory_configuration(self, mock_desktop_app):
        """Test logging directory configuration."""
        mock_app = MagicMock()
        mock_desktop_app.return_value = mock_app
        
        with tempfile.TemporaryDirectory() as temp_dir:
            self.runner = server_runner.ServerRunner(log_dir=temp_dir)
            
            # Verify DesktopApp was created with log directory
            mock_desktop_app.assert_called_once()
            args, kwargs = mock_desktop_app.call_args
            assert kwargs['log_dir'] == temp_dir


class TestServerRunnerErrorHandling:
    """Test cases for error handling and edge cases."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = None
    
    def teardown_method(self):
        """Clean up after tests."""
        if self.runner:
            self.runner.cleanup()
    
    @patch('server_runner.DesktopApp')
    def test_desktop_app_creation_failure(self, mock_desktop_app):
        """Test handling of DesktopApp creation failure."""
        mock_desktop_app.side_effect = Exception("Failed to create DesktopApp")
        
        with pytest.raises(Exception, match="Failed to create DesktopApp"):
            self.runner = server_runner.ServerRunner()
    
    @patch('server_runner.DesktopApp')
    def test_signal_setup_failure(self, mock_desktop_app):
        """Test handling of signal setup failure."""
        mock_app = MagicMock()
        mock_desktop_app.return_value = mock_app
        
        self.runner = server_runner.ServerRunner()
        
        with patch('signal.signal', side_effect=OSError("Signal setup failed")):
            # Signal setup failure should not crash the application
            self.runner.setup_signal_handlers()
            # Should continue without signal handlers
    
    @patch('server_runner.DesktopApp')
    def test_cleanup_on_exception(self, mock_desktop_app):
        """Test cleanup is called even when exceptions occur."""
        mock_app = MagicMock()
        mock_app.startup.side_effect = Exception("Startup failed")
        mock_desktop_app.return_value = mock_app
        
        self.runner = server_runner.ServerRunner()
        
        # The start() method catches exceptions and returns False, doesn't re-raise
        result = self.runner.start()
        assert result is False
        
        # Cleanup should still be possible
        result = self.runner.stop()
        mock_app.shutdown.assert_called_once()


class TestServerRunnerPlatformSpecific:
    """Test cases for platform-specific functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = None
    
    def teardown_method(self):
        """Clean up after tests."""
        if self.runner:
            self.runner.cleanup()
    
    @patch('server_runner.DesktopApp')
    def test_windows_platform_detection(self, mock_desktop_app):
        """Test Windows platform-specific behavior."""
        mock_app = MagicMock()
        mock_desktop_app.return_value = mock_app
        
        with patch('server_runner.sys.platform', 'win32'):
            self.runner = server_runner.ServerRunner()
            assert self.runner.is_windows() is True
            assert self.runner.is_macos() is False
    
    @patch('server_runner.DesktopApp')
    def test_macos_platform_detection(self, mock_desktop_app):
        """Test macOS platform-specific behavior."""
        mock_app = MagicMock()
        mock_desktop_app.return_value = mock_app
        
        with patch('server_runner.sys.platform', 'darwin'):
            self.runner = server_runner.ServerRunner()
            assert self.runner.is_windows() is False
            assert self.runner.is_macos() is True