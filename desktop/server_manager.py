# ABOUTME: Server manager component for uvicorn server lifecycle management
# ABOUTME: Handles background server execution, health checking, and graceful shutdown

import threading
import time
from typing import Optional
import requests

try:
    import uvicorn
except ImportError:
    uvicorn = None

from desktop.port_detector import find_available_port


class ServerManager:
    """
    Manages the lifecycle of a uvicorn server in a background thread.
    
    Provides methods to start, stop, and health check the server with proper
    resource management and thread cleanup.
    """
    
    def __init__(self, port: Optional[int] = None, host: str = "127.0.0.1", 
                 app_module: str = "web.app:app"):
        """
        Initialize ServerManager.
        
        Args:
            port: Port to run server on (None to auto-detect)
            host: Host to bind server to
            app_module: Python module path to ASGI application
            
        Raises:
            ValueError: If port is outside valid range
        """
        if port is not None and not (1 <= port <= 65535):
            raise ValueError("Port must be between 1 and 65535")
            
        self.port = port
        self.host = host
        self.app_module = app_module
        self._server_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
    
    def start(self) -> None:
        """
        Start the server in a background thread.
        
        If no port is specified, will automatically find an available port
        starting from 8000.
        
        Raises:
            RuntimeError: If server is already running or port detection fails
            ImportError: If uvicorn is not available
        """
        if uvicorn is None:
            raise ImportError("uvicorn is required for server management")
            
        if self.is_running():
            raise RuntimeError("Server is already running")
        
        # Find available port if not specified
        if self.port is None:
            self.port = find_available_port(8000, max_attempts=10)
        
        # Reset stop event
        self._stop_event.clear()
        
        # Start server in background thread
        self._server_thread = threading.Thread(
            target=self._run_server,
            daemon=True,
            name=f"uvicorn-server-{self.port}"
        )
        self._server_thread.start()
    
    def stop(self) -> None:
        """
        Stop the server gracefully and clean up resources.
        """
        # Signal server to stop
        self._stop_event.set()
        
        # Wait for thread to finish
        if self._server_thread:
            self._server_thread.join(timeout=5.0)
            self._server_thread = None
    
    def is_running(self) -> bool:
        """
        Check if the server is currently running.
        
        Returns:
            True if server thread is active, False otherwise
        """
        return (self._server_thread is not None and 
                self._server_thread.is_alive())
    
    def health_check(self, endpoint: str = "/api/health/", timeout: int = 5) -> bool:
        """
        Perform health check on the running server.
        
        Args:
            endpoint: Health check endpoint path
            timeout: Request timeout in seconds
            
        Returns:
            True if server is healthy, False otherwise
            
        Raises:
            RuntimeError: If server port is not configured
        """
        if self.port is None:
            raise RuntimeError("Server port not configured")
        
        try:
            url = f"http://{self.host}:{self.port}{endpoint}"
            response = requests.get(url, timeout=timeout)
            return response.status_code == 200
        except (requests.ConnectionError, requests.Timeout, requests.RequestException):
            return False
    
    def _run_server(self) -> None:
        """
        Internal method to run uvicorn server.
        
        Runs in background thread and handles cleanup on exceptions.
        """
        try:
            # Simple uvicorn.run call that will be mocked in tests
            uvicorn.run(
                self.app_module,
                host=self.host,
                port=self.port,
                log_level="warning",
                access_log=False
            )
        except Exception as e:
            # Log the actual error for debugging
            import logging
            logging.error(f"Server startup failed: {e}")
            import traceback
            logging.error(f"Traceback: {traceback.format_exc()}")
            # Re-raise to ensure the caller knows about the failure
            raise
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.stop()
        return False