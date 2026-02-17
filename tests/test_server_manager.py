# ABOUTME: Comprehensive test suite for server manager component
# ABOUTME: Tests uvicorn server lifecycle, threading, health checks, and resource management

import pytest
import time
import threading
import requests
from unittest.mock import patch, MagicMock, call
from desktop.server_manager import ServerManager


class TestServerManagerInitialization:
    """Test cases for ServerManager initialization."""
    
    def test_server_manager_initialization_default_values(self):
        """Test ServerManager initializes with proper default values."""
        manager = ServerManager()
        
        assert manager.port is None
        assert manager.host == "127.0.0.1"
        assert manager.app_module == "web.app:app"
        assert manager._server_thread is None
        assert manager._stop_event is not None
        assert manager.is_running() is False
    
    def test_server_manager_initialization_custom_values(self):
        """Test ServerManager initializes with custom values."""
        manager = ServerManager(
            port=9000,
            host="localhost",
            app_module="custom.app:application"
        )
        
        assert manager.port == 9000
        assert manager.host == "localhost"
        assert manager.app_module == "custom.app:application"
        assert manager.is_running() is False
    
    def test_server_manager_invalid_port(self):
        """Test ServerManager validation of port numbers."""
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            ServerManager(port=0)
        
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            ServerManager(port=65536)
        
        with pytest.raises(ValueError, match="Port must be between 1 and 65535"):
            ServerManager(port=-1)


class TestServerManagerLifecycle:
    """Test cases for server lifecycle management."""
    
    @patch('desktop.server_manager.find_available_port')
    @patch('uvicorn.run')
    def test_start_server_with_available_port(self, mock_uvicorn, mock_find_port):
        """Test starting server when port detection finds available port."""
        mock_find_port.return_value = 8001
        mock_uvicorn.return_value = None
        
        manager = ServerManager()
        manager.start()
        
        # Should find available port
        mock_find_port.assert_called_once_with(8000, max_attempts=10)
        assert manager.port == 8001
        
        # Should start server in background thread
        time.sleep(0.05)  # Allow thread to start
        assert manager._server_thread is not None
        
        # Check that uvicorn.run was called with correct parameters
        mock_uvicorn.assert_called_once_with(
            "web.app:app",
            host="127.0.0.1",
            port=8001,
            log_level="warning",
            access_log=False
        )
        
        # Cleanup
        manager.stop()
    
    @patch('desktop.server_manager.find_available_port')
    @patch('uvicorn.run')
    def test_start_server_with_specific_port(self, mock_uvicorn, mock_find_port):
        """Test starting server with a specific port."""
        mock_uvicorn.return_value = None
        
        manager = ServerManager(port=9000)
        manager.start()
        
        # Should not call port detection when port is specified
        mock_find_port.assert_not_called()
        assert manager.port == 9000
        
        # Should start server thread
        time.sleep(0.05)
        assert manager._server_thread is not None
        
        # Check that uvicorn.run was called with correct parameters
        mock_uvicorn.assert_called_once_with(
            "web.app:app",
            host="127.0.0.1",
            port=9000,
            log_level="warning",
            access_log=False
        )
        
        # Cleanup
        manager.stop()
    
    @patch('desktop.server_manager.find_available_port')
    def test_start_server_port_detection_failure(self, mock_find_port):
        """Test server startup when port detection fails."""
        mock_find_port.side_effect = RuntimeError("No available ports")
        
        manager = ServerManager()
        
        with pytest.raises(RuntimeError, match="No available ports"):
            manager.start()
        
        assert manager.is_running() is False
        assert manager._server_thread is None
    
    @patch('uvicorn.run')
    def test_start_server_already_running(self, mock_uvicorn):
        """Test that starting an already running server raises exception."""
        # Make uvicorn.run block to simulate a running server
        import threading
        stop_event = threading.Event()
        
        def blocking_run(*args, **kwargs):
            stop_event.wait(timeout=10)  # Block until told to stop
        
        mock_uvicorn.side_effect = blocking_run
        
        manager = ServerManager(port=8000)
        manager.start()
        
        time.sleep(0.05)  # Allow first start to begin
        
        with pytest.raises(RuntimeError, match="Server is already running"):
            manager.start()
        
        # Clean up
        stop_event.set()
        manager.stop()
        
        # Cleanup
        manager.stop()
    
    @patch('uvicorn.run')
    def test_stop_server_graceful_shutdown(self, mock_uvicorn):
        """Test graceful server shutdown."""
        # Make uvicorn.run block to simulate a running server
        import threading
        stop_event = threading.Event()
        
        def blocking_run(*args, **kwargs):
            # Check manager's stop event periodically
            while not stop_event.is_set():
                time.sleep(0.01)
        
        mock_uvicorn.side_effect = blocking_run
        
        manager = ServerManager(port=8000)
        # Override the stop event with our test one for this test
        original_stop_event = manager._stop_event
        manager._stop_event = stop_event
        
        manager.start()
        
        time.sleep(0.05)
        assert manager.is_running() is True
        
        manager.stop()
        
        # Should stop cleanly
        assert manager.is_running() is False
        assert manager._server_thread is None
        assert manager._stop_event.is_set()
    
    def test_stop_server_not_running(self):
        """Test stopping server when it's not running."""
        manager = ServerManager()
        
        # Should not raise exception
        manager.stop()
        
        assert manager.is_running() is False
    
    @patch('uvicorn.run')
    def test_server_thread_cleanup_on_exception(self, mock_uvicorn):
        """Test proper cleanup when server thread encounters exception."""
        mock_uvicorn.side_effect = Exception("Server startup failed")
        
        manager = ServerManager(port=8000)
        manager.start()
        
        # Wait for thread to complete
        time.sleep(0.1)
        
        # Should clean up properly - thread exists but is no longer running
        assert manager.is_running() is False
        # Thread object exists but is stopped
        assert manager._server_thread is not None
        assert not manager._server_thread.is_alive()


class TestServerManagerHealthCheck:
    """Test cases for server health checking."""
    
    @patch('requests.get')
    def test_health_check_server_responsive(self, mock_get):
        """Test health check when server is responsive."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        manager = ServerManager(port=8000)
        
        result = manager.health_check()
        assert result is True
        
        mock_get.assert_called_once_with(
            "http://127.0.0.1:8000/health",
            timeout=5
        )
    
    @patch('requests.get')
    def test_health_check_server_error_response(self, mock_get):
        """Test health check when server returns error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        manager = ServerManager(port=8000)
        
        result = manager.health_check()
        assert result is False
    
    @patch('requests.get')
    def test_health_check_connection_error(self, mock_get):
        """Test health check when connection fails."""
        mock_get.side_effect = requests.ConnectionError("Connection refused")
        
        manager = ServerManager(port=8000)
        
        result = manager.health_check()
        assert result is False
    
    @patch('requests.get')
    def test_health_check_timeout(self, mock_get):
        """Test health check when request times out."""
        mock_get.side_effect = requests.Timeout("Request timed out")
        
        manager = ServerManager(port=8000)
        
        result = manager.health_check()
        assert result is False
    
    def test_health_check_no_port_configured(self):
        """Test health check when no port is configured."""
        manager = ServerManager()
        
        with pytest.raises(RuntimeError, match="Server port not configured"):
            manager.health_check()
    
    @patch('requests.get')
    def test_health_check_custom_endpoint(self, mock_get):
        """Test health check with custom endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        manager = ServerManager(port=8000)
        
        result = manager.health_check(endpoint="/api/status")
        assert result is True
        
        mock_get.assert_called_once_with(
            "http://127.0.0.1:8000/api/status",
            timeout=5
        )


class TestServerManagerThreading:
    """Test cases for threading behavior."""
    
    @patch('uvicorn.run')
    def test_server_runs_in_daemon_thread(self, mock_uvicorn):
        """Test that server runs in a daemon thread."""
        mock_uvicorn.return_value = None
        
        manager = ServerManager(port=8000)
        manager.start()
        
        time.sleep(0.1)
        
        assert manager._server_thread is not None
        assert manager._server_thread.daemon is True
        
        # Cleanup
        manager.stop()
    
    @patch('uvicorn.run')
    def test_multiple_server_threads_not_allowed(self, mock_uvicorn):
        """Test that only one server thread can run at a time."""
        # Make uvicorn.run block to simulate a running server
        import threading
        stop_event = threading.Event()
        
        def blocking_run(*args, **kwargs):
            stop_event.wait(timeout=10)
        
        mock_uvicorn.side_effect = blocking_run
        
        manager = ServerManager(port=8000)
        manager.start()
        
        time.sleep(0.05)  # Allow first start to begin
        first_thread = manager._server_thread
        
        with pytest.raises(RuntimeError, match="Server is already running"):
            manager.start()
        
        # Should still be the same thread
        assert manager._server_thread is first_thread
        
        # Cleanup
        stop_event.set()
        manager.stop()
    
    @patch('uvicorn.run')
    def test_thread_cleanup_on_stop(self, mock_uvicorn):
        """Test proper thread cleanup on stop."""
        mock_uvicorn.return_value = None
        
        manager = ServerManager(port=8000)
        manager.start()
        
        time.sleep(0.1)
        thread = manager._server_thread
        
        manager.stop()
        
        # Thread should be cleaned up
        assert manager._server_thread is None
        # Original thread should eventually finish
        thread.join(timeout=1.0)
        assert not thread.is_alive()


class TestServerManagerErrorHandling:
    """Test cases for error handling scenarios."""
    
    @patch('uvicorn.run')
    def test_uvicorn_import_error(self, mock_uvicorn):
        """Test handling when uvicorn import fails."""
        with patch('desktop.server_manager.uvicorn', None):
            manager = ServerManager(port=8000)
            
            with pytest.raises(ImportError, match="uvicorn is required"):
                manager.start()
    
    @patch('desktop.server_manager.find_available_port')
    @patch('uvicorn.run')
    def test_server_startup_exception_handling(self, mock_uvicorn, mock_find_port):
        """Test handling of exceptions during server startup."""
        mock_find_port.return_value = 8000
        mock_uvicorn.side_effect = OSError("Permission denied")
        
        manager = ServerManager()
        
        # Should not raise exception from main thread
        manager.start()
        
        # Wait for background thread to handle exception
        time.sleep(0.2)
        
        assert manager.is_running() is False
    
    def test_stop_event_handling(self):
        """Test stop event behavior."""
        manager = ServerManager()
        
        # Initially not set
        assert not manager._stop_event.is_set()
        
        manager.stop()
        
        # Should be set after stop
        assert manager._stop_event.is_set()


class TestServerManagerIntegration:
    """Integration tests for ServerManager."""
    
    @patch('uvicorn.run')
    @patch('requests.get')
    def test_full_lifecycle_with_health_check(self, mock_get, mock_uvicorn):
        """Test complete server lifecycle with health checking."""
        # Make uvicorn.run block to simulate a running server
        import threading
        stop_event = threading.Event()
        
        def blocking_run(*args, **kwargs):
            stop_event.wait(timeout=10)
        
        mock_uvicorn.side_effect = blocking_run
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        manager = ServerManager(port=8000)
        
        # Start server
        manager.start()
        time.sleep(0.05)
        
        assert manager.is_running() is True
        assert manager.port == 8000
        
        # Health check should work
        assert manager.health_check() is True
        
        # Stop server
        stop_event.set()
        manager.stop()
        
        assert manager.is_running() is False
    
    @patch('desktop.server_manager.find_available_port')
    @patch('uvicorn.run')
    def test_port_detection_integration(self, mock_uvicorn, mock_find_port):
        """Test integration with port detection utility."""
        mock_find_port.return_value = 8003
        mock_uvicorn.return_value = None
        
        manager = ServerManager()
        manager.start()
        
        # Should integrate with port detector
        mock_find_port.assert_called_once_with(8000, max_attempts=10)
        assert manager.port == 8003
        
        # Cleanup
        manager.stop()


class TestServerManagerContextManager:
    """Test cases for context manager support."""
    
    @patch('uvicorn.run')
    def test_context_manager_support(self, mock_uvicorn):
        """Test that ServerManager can be used as context manager."""
        # Make uvicorn.run block to simulate a running server
        import threading
        stop_event = threading.Event()
        
        def blocking_run(*args, **kwargs):
            stop_event.wait(timeout=10)
        
        mock_uvicorn.side_effect = blocking_run
        
        with ServerManager(port=8000) as manager:
            time.sleep(0.05)
            assert manager.is_running() is True
            stop_event.set()  # Allow server to stop when context exits
        
        # Should automatically stop after context
        assert manager.is_running() is False
    
    @patch('uvicorn.run')
    def test_context_manager_exception_handling(self, mock_uvicorn):
        """Test context manager cleanup on exception."""
        # Make uvicorn.run block to simulate a running server
        import threading
        stop_event = threading.Event()
        
        def blocking_run(*args, **kwargs):
            stop_event.wait(timeout=10)
        
        mock_uvicorn.side_effect = blocking_run
        
        try:
            with ServerManager(port=8000) as manager:
                time.sleep(0.05)
                assert manager.is_running() is True
                stop_event.set()  # Allow server to stop when context exits
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Should still clean up properly
        assert manager.is_running() is False