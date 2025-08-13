# ABOUTME: Comprehensive test suite for desktop application core component
# ABOUTME: Tests integration of all components, startup/shutdown sequences, and error handling

import asyncio
import pytest
import threading
import time
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import tempfile

from desktop.desktop_app import DesktopApp
from desktop import port_detector
from desktop.server_manager import ServerManager
from desktop.browser_controller import BrowserController
from desktop.app_logger import AppLogger


class TestDesktopAppInitialization:
    """Test cases for DesktopApp initialization."""
    
    def test_desktop_app_initialization_default(self):
        """Test DesktopApp initializes with default values."""
        app = DesktopApp()
        
        assert app.host == "127.0.0.1"
        assert app.port_range == (8000, 8099)
        assert app.web_app_module == "web.app:app"
        assert app.startup_timeout == 30.0
        assert app.shutdown_timeout == 10.0
        assert app.auto_open_browser is True
        assert app.preferred_browser is None
    
    def test_desktop_app_initialization_custom(self):
        """Test DesktopApp initializes with custom values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            app = DesktopApp(
                host="localhost",
                port_range=(3000, 3010),
                web_app_module="custom.app:application",
                log_dir=temp_dir,
                startup_timeout=60.0,
                shutdown_timeout=20.0,
                auto_open_browser=False,
                preferred_browser="chrome"
            )
            
            assert app.host == "localhost"
            assert app.port_range == (3000, 3010)
            assert app.web_app_module == "custom.app:application"
            assert app.startup_timeout == 60.0
            assert app.shutdown_timeout == 20.0
            assert app.auto_open_browser is False
            assert app.preferred_browser == "chrome"
    
    def test_desktop_app_invalid_port_range(self):
        """Test DesktopApp validation of port range."""
        with pytest.raises(ValueError, match="Invalid port range"):
            DesktopApp(port_range=(8100, 8000))  # start > end
        
        with pytest.raises(ValueError, match="Invalid port range"):
            DesktopApp(port_range=(0, 1000))  # port too low
        
        with pytest.raises(ValueError, match="Invalid port range"):
            DesktopApp(port_range=(65000, 70000))  # port too high
    
    def test_desktop_app_invalid_timeouts(self):
        """Test DesktopApp validation of timeout values."""
        with pytest.raises(ValueError, match="Startup timeout must be positive"):
            DesktopApp(startup_timeout=0)
        
        with pytest.raises(ValueError, match="Shutdown timeout must be positive"):
            DesktopApp(shutdown_timeout=-1)
    
    def test_desktop_app_component_initialization(self):
        """Test that all component instances are created properly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            app = DesktopApp(log_dir=temp_dir)
            
            assert isinstance(app.server_manager, ServerManager)
            assert isinstance(app.browser_controller, BrowserController)
            assert isinstance(app.logger, AppLogger)
            
            # Check component configuration
            assert app.server_manager.host == app.host
            assert app.browser_controller.preferred_browser == app.preferred_browser


class TestDesktopAppComponentConfiguration:
    """Test cases for component configuration."""
    
    def test_port_detector_configuration(self):
        """Test port detector configuration."""
        app = DesktopApp(host="192.168.1.100", port_range=(5000, 5050))
        
        # Port detector configuration is stored in the app instance
        assert app.host == "192.168.1.100"
        assert app.port_range == (5000, 5050)
    
    def test_server_manager_configuration(self):
        """Test server manager configuration."""
        app = DesktopApp(
            host="localhost",
            web_app_module="test.app:app"
        )
        
        assert app.server_manager.host == "localhost"
        assert app.server_manager.app_module == "test.app:app"
    
    def test_browser_controller_configuration(self):
        """Test browser controller configuration."""
        app = DesktopApp(preferred_browser="firefox")
        
        assert app.browser_controller.preferred_browser == "firefox"
    
    def test_logger_configuration(self):
        """Test logger configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            app = DesktopApp(log_dir=temp_dir)
            
            assert str(app.logger.log_dir) == temp_dir
            assert app.logger.app_name == "WorkJournalMaker"


class TestDesktopAppPortDiscovery:
    """Test cases for port discovery functionality."""
    
    @patch('desktop.port_detector.is_port_available')
    def test_find_available_port_success(self, mock_is_available):
        """Test successful port discovery."""
        mock_is_available.return_value = True
        
        app = DesktopApp()
        port = app.find_available_port()
        
        assert port == 8000  # First port in default range
        mock_is_available.assert_called_with(8000)
    
    @patch('desktop.port_detector.is_port_available')
    def test_find_available_port_failure(self, mock_is_available):
        """Test port discovery failure."""
        mock_is_available.return_value = False  # All ports busy
        
        app = DesktopApp()
        port = app.find_available_port()
        
        assert port is None
        # Should check all ports in range
        assert mock_is_available.call_count == 100  # 8000-8099
    
    @patch('desktop.port_detector.is_port_available')
    def test_check_port_availability(self, mock_is_available):
        """Test checking specific port availability."""
        mock_is_available.return_value = True
        
        app = DesktopApp()
        available = app.is_port_available(8080)
        
        assert available is True
        mock_is_available.assert_called_once_with(8080)


class TestDesktopAppServerManagement:
    """Test cases for server management functionality."""
    
    @patch.object(ServerManager, 'start')
    @patch.object(ServerManager, 'is_running')
    def test_start_server_success(self, mock_is_running, mock_start):
        """Test successful server startup."""
        mock_is_running.return_value = True
        
        app = DesktopApp()
        result = app.start_server(8080)
        
        assert result is True
        mock_start.assert_called_once()
        assert app.server_manager.port == 8080
    
    @patch.object(ServerManager, 'start')
    @patch.object(ServerManager, 'is_running')
    def test_start_server_failure(self, mock_is_running, mock_start):
        """Test server startup failure."""
        mock_is_running.return_value = False
        
        app = DesktopApp()
        result = app.start_server(8080)
        
        assert result is False
        mock_start.assert_called_once()
    
    @patch.object(ServerManager, 'stop')
    @patch.object(ServerManager, 'is_running')
    def test_stop_server(self, mock_is_running, mock_stop):
        """Test server shutdown."""
        mock_is_running.return_value = False  # Server stopped
        
        app = DesktopApp()
        result = app.stop_server()
        
        assert result is True
        mock_stop.assert_called_once()
    
    @patch.object(ServerManager, 'is_running')
    def test_server_status_check(self, mock_is_running):
        """Test server status checking."""
        mock_is_running.return_value = True
        
        app = DesktopApp()
        running = app.is_server_running()
        
        assert running is True
        mock_is_running.assert_called_once()


class TestDesktopAppBrowserControl:
    """Test cases for browser control functionality."""
    
    @patch.object(BrowserController, 'open_browser')
    def test_open_browser_success(self, mock_open):
        """Test successful browser opening."""
        mock_open.return_value = True
        
        app = DesktopApp()
        result = app.open_browser("http://localhost:8080")
        
        assert result is True
        mock_open.assert_called_once_with("http://localhost:8080")
    
    @patch.object(BrowserController, 'open_browser')
    def test_open_browser_failure(self, mock_open):
        """Test browser opening failure."""
        mock_open.return_value = False
        
        app = DesktopApp()
        result = app.open_browser("http://localhost:8080")
        
        assert result is False
        mock_open.assert_called_once_with("http://localhost:8080")
    
    def test_build_server_url(self):
        """Test server URL building."""
        app = DesktopApp(host="127.0.0.1")
        url = app.build_server_url(8080)
        
        assert url == "http://127.0.0.1:8080"
    
    def test_build_server_url_with_path(self):
        """Test server URL building with path."""
        app = DesktopApp(host="localhost")
        url = app.build_server_url(3000, path="/dashboard")
        
        assert url == "http://localhost:3000/dashboard"


class TestDesktopAppStartupSequence:
    """Test cases for application startup sequence."""
    
    @patch.object(DesktopApp, 'find_available_port')
    @patch.object(DesktopApp, 'start_server')
    @patch.object(DesktopApp, 'wait_for_server_ready')
    @patch.object(DesktopApp, 'open_browser')
    def test_startup_sequence_success(self, mock_open_browser, mock_wait_ready, 
                                    mock_start_server, mock_find_port):
        """Test successful complete startup sequence."""
        mock_find_port.return_value = 8080
        mock_start_server.return_value = True
        mock_wait_ready.return_value = True
        mock_open_browser.return_value = True
        
        app = DesktopApp()
        result = app.startup()
        
        assert result is True
        assert app.current_port == 8080
        
        mock_find_port.assert_called_once()
        mock_start_server.assert_called_once_with(8080)
        mock_wait_ready.assert_called_once_with(8080)
        mock_open_browser.assert_called_once_with("http://127.0.0.1:8080")
    
    @patch.object(DesktopApp, 'find_available_port')
    def test_startup_no_available_port(self, mock_find_port):
        """Test startup failure when no port is available."""
        mock_find_port.return_value = None
        
        app = DesktopApp()
        result = app.startup()
        
        assert result is False
        assert app.current_port is None
    
    @patch.object(DesktopApp, 'find_available_port')
    @patch.object(DesktopApp, 'start_server')
    def test_startup_server_start_failure(self, mock_start_server, mock_find_port):
        """Test startup failure when server fails to start."""
        mock_find_port.return_value = 8080
        mock_start_server.return_value = False
        
        app = DesktopApp()
        result = app.startup()
        
        assert result is False
        assert app.current_port is None
    
    @patch.object(DesktopApp, 'find_available_port')
    @patch.object(DesktopApp, 'start_server')
    @patch.object(DesktopApp, 'wait_for_server_ready')
    def test_startup_server_not_ready(self, mock_wait_ready, mock_start_server, mock_find_port):
        """Test startup failure when server doesn't become ready."""
        mock_find_port.return_value = 8080
        mock_start_server.return_value = True
        mock_wait_ready.return_value = False
        
        app = DesktopApp()
        result = app.startup()
        
        assert result is False
        assert app.current_port is None
    
    @patch.object(DesktopApp, 'find_available_port')
    @patch.object(DesktopApp, 'start_server')
    @patch.object(DesktopApp, 'wait_for_server_ready')
    @patch.object(DesktopApp, 'open_browser')
    def test_startup_browser_disabled(self, mock_open_browser, mock_wait_ready,
                                    mock_start_server, mock_find_port):
        """Test startup with browser opening disabled."""
        mock_find_port.return_value = 8080
        mock_start_server.return_value = True
        mock_wait_ready.return_value = True
        
        app = DesktopApp(auto_open_browser=False)
        result = app.startup()
        
        assert result is True
        assert app.current_port == 8080
        
        # Browser should not be opened
        mock_open_browser.assert_not_called()
    
    @patch.object(DesktopApp, 'find_available_port')
    @patch.object(DesktopApp, 'start_server')
    @patch.object(DesktopApp, 'wait_for_server_ready')
    @patch.object(DesktopApp, 'open_browser')
    def test_startup_browser_failure_non_blocking(self, mock_open_browser, mock_wait_ready,
                                                 mock_start_server, mock_find_port):
        """Test that browser opening failure doesn't block startup."""
        mock_find_port.return_value = 8080
        mock_start_server.return_value = True
        mock_wait_ready.return_value = True
        mock_open_browser.return_value = False
        
        app = DesktopApp()
        result = app.startup()
        
        # Startup should still succeed even if browser fails to open
        assert result is True
        assert app.current_port == 8080


class TestDesktopAppShutdownSequence:
    """Test cases for application shutdown sequence."""
    
    @patch.object(DesktopApp, 'stop_server')
    def test_shutdown_sequence_success(self, mock_stop_server):
        """Test successful shutdown sequence."""
        mock_stop_server.return_value = True
        
        app = DesktopApp()
        app.current_port = 8080  # Simulate running state
        
        result = app.shutdown()
        
        assert result is True
        assert app.current_port is None
        mock_stop_server.assert_called_once()
    
    @patch.object(DesktopApp, 'stop_server')
    def test_shutdown_server_not_running(self, mock_stop_server):
        """Test shutdown when server is not running."""
        app = DesktopApp()
        # current_port is None (not running)
        
        result = app.shutdown()
        
        assert result is True
        mock_stop_server.assert_not_called()
    
    @patch.object(DesktopApp, 'stop_server')
    def test_shutdown_server_stop_failure(self, mock_stop_server):
        """Test shutdown when server stop fails."""
        mock_stop_server.return_value = False
        
        app = DesktopApp()
        app.current_port = 8080
        
        result = app.shutdown()
        
        assert result is False
        # Port should still be set since shutdown failed
        assert app.current_port == 8080


class TestDesktopAppServerReadiness:
    """Test cases for server readiness checking."""
    
    @patch('requests.get')
    def test_wait_server_ready_success(self, mock_get):
        """Test successful server readiness check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        app = DesktopApp()
        result = app.wait_for_server_ready(8080, timeout=1.0)
        
        assert result is True
        mock_get.assert_called()
    
    @patch('requests.get')
    def test_wait_server_ready_timeout(self, mock_get):
        """Test server readiness check timeout."""
        from requests.exceptions import RequestException
        mock_get.side_effect = RequestException("Connection refused")
        
        app = DesktopApp()
        result = app.wait_for_server_ready(8080, timeout=0.1)
        
        assert result is False
    
    @patch('requests.get')
    def test_wait_server_ready_http_error(self, mock_get):
        """Test server readiness with HTTP errors."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        app = DesktopApp()
        result = app.wait_for_server_ready(8080, timeout=0.1)
        
        assert result is False
    
    @patch('requests.get')
    def test_wait_server_ready_retry_logic(self, mock_get):
        """Test server readiness retry logic."""
        # First two calls fail, third succeeds
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        
        from requests.exceptions import RequestException
        mock_get.side_effect = [
            RequestException("Connection refused"),
            mock_response_fail,
            mock_response_success
        ]
        
        app = DesktopApp()
        result = app.wait_for_server_ready(8080, timeout=2.0)
        
        assert result is True
        assert mock_get.call_count == 3


class TestDesktopAppErrorHandling:
    """Test cases for error handling scenarios."""
    
    @patch.object(DesktopApp, 'find_available_port')
    def test_startup_exception_handling(self, mock_find_port):
        """Test startup exception handling."""
        mock_find_port.side_effect = Exception("Unexpected error")
        
        app = DesktopApp()
        result = app.startup()
        
        assert result is False
        assert app.current_port is None
    
    @patch.object(DesktopApp, 'stop_server')
    def test_shutdown_exception_handling(self, mock_stop_server):
        """Test shutdown exception handling."""
        mock_stop_server.side_effect = Exception("Shutdown error")
        
        app = DesktopApp()
        app.current_port = 8080
        
        result = app.shutdown()
        
        assert result is False
    
    def test_invalid_url_building(self):
        """Test URL building with invalid inputs."""
        app = DesktopApp()
        
        # Should handle invalid port gracefully
        with pytest.raises(ValueError):
            app.build_server_url(-1)
        
        with pytest.raises(ValueError):
            app.build_server_url(70000)


class TestDesktopAppLogging:
    """Test cases for logging functionality."""
    
    def test_logging_integration(self):
        """Test that logging is properly integrated."""
        with tempfile.TemporaryDirectory() as temp_dir:
            app = DesktopApp(log_dir=temp_dir)
            
            # Logger should be set up
            assert app.logger is not None
            
            # Test logging methods
            app.log_info("Test info message")
            app.log_warning("Test warning message")
            app.log_error("Test error message")
    
    @patch.object(AppLogger, 'setup_logging')
    def test_setup_logging_called(self, mock_setup):
        """Test that logger setup is called during initialization."""
        app = DesktopApp()
        
        # setup_logging is called once during initialization
        mock_setup.assert_called_once()


class TestDesktopAppContextManager:
    """Test cases for context manager support."""
    
    @patch.object(DesktopApp, 'startup')
    @patch.object(DesktopApp, 'shutdown')
    def test_context_manager_success(self, mock_shutdown, mock_startup):
        """Test successful context manager usage."""
        mock_startup.return_value = True
        mock_shutdown.return_value = True
        
        with DesktopApp() as app:
            assert app is not None
            mock_startup.assert_called_once()
        
        mock_shutdown.assert_called_once()
    
    @patch.object(DesktopApp, 'startup')
    @patch.object(DesktopApp, 'shutdown')
    def test_context_manager_startup_failure(self, mock_shutdown, mock_startup):
        """Test context manager with startup failure."""
        mock_startup.return_value = False
        
        with pytest.raises(RuntimeError, match="Failed to start desktop application"):
            with DesktopApp() as app:
                pass
        
        mock_shutdown.assert_not_called()
    
    @patch.object(DesktopApp, 'startup')
    @patch.object(DesktopApp, 'shutdown')
    def test_context_manager_exception_handling(self, mock_shutdown, mock_startup):
        """Test context manager exception handling."""
        mock_startup.return_value = True
        mock_shutdown.return_value = True
        
        with pytest.raises(ValueError, match="Test exception"):
            with DesktopApp() as app:
                raise ValueError("Test exception")
        
        # Shutdown should still be called
        mock_shutdown.assert_called_once()


class TestDesktopAppIntegration:
    """Integration tests for DesktopApp."""
    
    @patch('desktop.port_detector.is_port_available')
    @patch.object(ServerManager, 'start')
    @patch.object(ServerManager, 'stop')
    @patch.object(ServerManager, 'is_running')
    @patch('requests.get')
    @patch.object(BrowserController, 'open_browser')
    def test_complete_application_lifecycle(self, mock_open_browser, mock_get,
                                          mock_is_running, mock_stop,
                                          mock_start, mock_is_port_available):
        """Test complete application lifecycle from startup to shutdown."""
        # Setup mocks for successful operation
        mock_is_port_available.return_value = True
        mock_is_running.side_effect = [True, False]  # Running during startup, stopped after shutdown
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        mock_open_browser.return_value = True
        
        with tempfile.TemporaryDirectory() as temp_dir:
            app = DesktopApp(log_dir=temp_dir)
            
            # Test startup
            startup_result = app.startup()
            assert startup_result is True
            assert app.current_port == 8000  # First available port
            
            # Verify all startup steps were called
            mock_is_port_available.assert_called()
            mock_start.assert_called_once()
            mock_get.assert_called()
            mock_open_browser.assert_called_once_with("http://127.0.0.1:8000")
            
            # Test that app is in running state
            assert app.is_running()
            
            # Test shutdown
            shutdown_result = app.shutdown()
            assert shutdown_result is True
            assert app.current_port is None
            
            mock_stop.assert_called_once()
    
    def test_multiple_startup_attempts(self):
        """Test that multiple startup attempts are handled correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            app = DesktopApp(log_dir=temp_dir)
            
            with patch.object(app, 'find_available_port', return_value=8000), \
                 patch.object(app, 'start_server', return_value=True), \
                 patch.object(app, 'wait_for_server_ready', return_value=True), \
                 patch.object(app, 'open_browser', return_value=True):
                
                # First startup
                result1 = app.startup()
                assert result1 is True
                assert app.current_port == 8000
                
                # Second startup attempt should be ignored
                result2 = app.startup()
                assert result2 is True  # Still returns True but doesn't restart
                assert app.current_port == 8000


class TestDesktopAppUtilityMethods:
    """Test cases for utility methods."""
    
    def test_is_running_state(self):
        """Test running state detection."""
        app = DesktopApp()
        
        # Initially not running
        assert app.is_running() is False
        
        # Set as running
        app.current_port = 8080
        assert app.is_running() is True
        
        # Reset to not running
        app.current_port = None
        assert app.is_running() is False
    
    def test_get_server_info(self):
        """Test getting server information."""
        app = DesktopApp(host="localhost")
        app.current_port = 3000
        
        info = app.get_server_info()
        
        assert info['host'] == "localhost"
        assert info['port'] == 3000
        assert info['url'] == "http://localhost:3000"
        assert info['running'] is True
    
    def test_get_server_info_not_running(self):
        """Test getting server info when not running."""
        app = DesktopApp()
        
        info = app.get_server_info()
        
        assert info['host'] == "127.0.0.1"
        assert info['port'] is None
        assert info['url'] is None
        assert info['running'] is False
    
    def test_configure_logging_level(self):
        """Test configuring logging level."""
        import logging
        
        with tempfile.TemporaryDirectory() as temp_dir:
            app = DesktopApp(log_dir=temp_dir)
            
            app.configure_logging_level(logging.DEBUG)
            assert app.logger.log_level == logging.DEBUG
            
            app.configure_logging_level(logging.ERROR)
            assert app.logger.log_level == logging.ERROR


class TestDesktopAppPerformance:
    """Test cases for performance-related functionality."""
    
    @patch.object(DesktopApp, 'find_available_port')
    @patch.object(DesktopApp, 'start_server')
    @patch.object(DesktopApp, 'wait_for_server_ready')
    def test_startup_timeout_handling(self, mock_wait_ready, mock_start_server, mock_find_port):
        """Test startup timeout handling."""
        mock_find_port.return_value = 8080
        mock_start_server.return_value = True
        mock_wait_ready.return_value = False  # Server never becomes ready
        
        app = DesktopApp(startup_timeout=0.1)  # Very short timeout
        
        start_time = time.time()
        result = app.startup()
        end_time = time.time()
        
        assert result is False
        # Should respect timeout
        assert (end_time - start_time) < 1.0
    
    def test_concurrent_operations_safety(self):
        """Test thread safety of concurrent operations."""
        app = DesktopApp()
        results = []
        
        def startup_worker():
            with patch.object(app, 'find_available_port', return_value=8000), \
                 patch.object(app, 'start_server', return_value=True), \
                 patch.object(app, 'wait_for_server_ready', return_value=True), \
                 patch.object(app, 'open_browser', return_value=True):
                result = app.startup()
                results.append(result)
        
        # Start multiple threads trying to start the app
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=startup_worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All should succeed because the first thread sets the running state
        # and subsequent threads see the app is already running
        successful_startups = sum(1 for r in results if r is True)
        assert successful_startups == 3  # All return True (first starts, others see it's running)