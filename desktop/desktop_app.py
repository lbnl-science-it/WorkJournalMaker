# ABOUTME: Main desktop application orchestrating all components
# ABOUTME: Handles startup/shutdown sequences, component integration, and lifecycle management

import time
import logging
import threading
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

import requests
from requests.exceptions import RequestException

from desktop import port_detector
from desktop.server_manager import ServerManager
from desktop.browser_controller import BrowserController
from desktop.app_logger import AppLogger


class DesktopApp:
    """Main desktop application orchestrating all components.
    
    Provides a unified interface for managing the complete application lifecycle,
    including port discovery, server management, browser control, and logging.
    """
    
    def __init__(
        self,
        host: str = "127.0.0.1",
        port_range: Tuple[int, int] = (8000, 8099),
        web_app_module: str = "web.app:app",
        log_dir: Optional[str] = None,
        startup_timeout: float = 30.0,
        shutdown_timeout: float = 10.0,
        auto_open_browser: bool = True,
        preferred_browser: Optional[str] = None
    ) -> None:
        """Initialize the DesktopApp.
        
        Args:
            host: Host address for the server
            port_range: Tuple of (start_port, end_port) for port discovery
            web_app_module: Module path for the web application
            log_dir: Directory for log files (uses default if None)
            startup_timeout: Maximum time to wait for server startup
            shutdown_timeout: Maximum time to wait for server shutdown
            auto_open_browser: Whether to automatically open browser
            preferred_browser: Preferred browser name
            
        Raises:
            ValueError: If parameters are invalid
        """
        # Validate inputs
        if port_range[0] > port_range[1]:
            raise ValueError("Invalid port range: start port must be <= end port")
        if port_range[0] < 1024 or port_range[1] > 65535:
            raise ValueError("Invalid port range: ports must be between 1024 and 65535")
        if startup_timeout <= 0:
            raise ValueError("Startup timeout must be positive")
        if shutdown_timeout <= 0:
            raise ValueError("Shutdown timeout must be positive")
        
        self.host = host
        self.port_range = port_range
        self.web_app_module = web_app_module
        self.startup_timeout = startup_timeout
        self.shutdown_timeout = shutdown_timeout
        self.auto_open_browser = auto_open_browser
        self.preferred_browser = preferred_browser
        
        # State tracking
        self.current_port: Optional[int] = None
        self._startup_lock = threading.Lock()
        
        # Initialize components  
        self.server_manager = ServerManager(host=host, app_module=web_app_module)
        self.browser_controller = BrowserController(preferred_browser=preferred_browser)
        self.logger = AppLogger(log_dir=log_dir)
        
        # Setup logging
        self.setup_logging()
    
    def setup_logging(self) -> None:
        """Set up application logging."""
        self.logger.setup_logging()
        self.log_info("Desktop application initialized")
    
    def find_available_port(self) -> Optional[int]:
        """Find an available port for the server.
        
        Returns:
            Available port number or None if no ports available
        """
        try:
            # Try each port in the range
            for port in range(self.port_range[0], self.port_range[1] + 1):
                if port_detector.is_port_available(port):
                    self.log_info(f"Found available port: {port}")
                    return port
            
            self.log_error(f"No available ports in range {self.port_range}")
            return None
        except Exception as e:
            self.log_error(f"Error finding available port: {e}")
            return None
    
    def is_port_available(self, port: int) -> bool:
        """Check if a specific port is available.
        
        Args:
            port: Port number to check
            
        Returns:
            True if port is available, False otherwise
        """
        try:
            return port_detector.is_port_available(port)
        except Exception as e:
            self.log_error(f"Error checking port {port} availability: {e}")
            return False
    
    def start_server(self, port: int) -> bool:
        """Start the web server on the specified port.
        
        Args:
            port: Port number to start server on
            
        Returns:
            True if server started successfully, False otherwise
        """
        try:
            self.log_info(f"Starting server on {self.host}:{port}")
            # Set the port on the server manager
            self.server_manager.port = port
            self.server_manager.start()
            
            # Give the server a moment to start
            time.sleep(0.1)
            
            if self.server_manager.is_running():
                self.log_info(f"Server started successfully on port {port}")
                return True
            else:
                self.log_error(f"Failed to start server on port {port}")
                return False
        except Exception as e:
            self.log_error(f"Exception starting server: {e}")
            return False
    
    def stop_server(self) -> bool:
        """Stop the web server.
        
        Returns:
            True if server stopped successfully, False otherwise
        """
        try:
            self.log_info("Stopping server")
            self.server_manager.stop()
            
            # Give the server a moment to stop
            time.sleep(0.1)
            
            if not self.server_manager.is_running():
                self.log_info("Server stopped successfully")
                return True
            else:
                self.log_error("Failed to stop server")
                return False
        except Exception as e:
            self.log_error(f"Exception stopping server: {e}")
            return False
    
    def is_server_running(self) -> bool:
        """Check if the server is currently running.
        
        Returns:
            True if server is running, False otherwise
        """
        try:
            return self.server_manager.is_running()
        except Exception as e:
            self.log_error(f"Error checking server status: {e}")
            return False
    
    def wait_for_server_ready(self, port: int, timeout: Optional[float] = None) -> bool:
        """Wait for the server to become ready.
        
        Args:
            port: Port number server is running on
            timeout: Maximum time to wait (uses startup_timeout if None)
            
        Returns:
            True if server is ready, False if timeout or error
        """
        if timeout is None:
            timeout = self.startup_timeout
        
        url = self.build_server_url(port)
        start_time = time.time()
        
        self.log_info(f"Waiting for server to be ready at {url}")
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(url, timeout=1.0)
                if response.status_code == 200:
                    self.log_info("Server is ready")
                    return True
            except RequestException:
                pass
            
            time.sleep(0.5)  # Wait before retry
        
        self.log_error(f"Server not ready after {timeout} seconds")
        return False
    
    def build_server_url(self, port: int, path: str = "") -> str:
        """Build server URL from host, port, and optional path.
        
        Args:
            port: Port number
            path: Optional path component
            
        Returns:
            Complete server URL
            
        Raises:
            ValueError: If port is invalid
        """
        if port < 1 or port > 65535:
            raise ValueError(f"Invalid port number: {port}")
        
        url = f"http://{self.host}:{port}"
        if path:
            if not path.startswith('/'):
                path = '/' + path
            url += path
        
        return url
    
    def open_browser(self, url: str) -> bool:
        """Open the specified URL in a browser.
        
        Args:
            url: URL to open
            
        Returns:
            True if browser opened successfully, False otherwise
        """
        try:
            self.log_info(f"Opening browser to {url}")
            result = self.browser_controller.open_browser(url)
            if result:
                self.log_info("Browser opened successfully")
            else:
                self.log_warning("Failed to open browser")
            return result
        except Exception as e:
            self.log_error(f"Exception opening browser: {e}")
            return False
    
    def startup(self) -> bool:
        """Start the complete desktop application.
        
        Performs the full startup sequence:
        1. Find available port
        2. Start server
        3. Wait for server to be ready
        4. Open browser (if enabled)
        
        Returns:
            True if startup successful, False otherwise
        """
        with self._startup_lock:
            if self.is_running():
                self.log_info("Application is already running")
                return True
            
            try:
                self.log_info("Starting desktop application")
                
                # Step 1: Find available port
                port = self.find_available_port()
                if port is None:
                    self.log_error("No available port found")
                    return False
                
                # Step 2: Start server
                if not self.start_server(port):
                    self.log_error("Server startup failed")
                    return False
                
                # Step 3: Wait for server to be ready
                if not self.wait_for_server_ready(port):
                    self.log_error("Server did not become ready")
                    self.stop_server()  # Cleanup
                    return False
                
                # Step 4: Open browser (if enabled)
                server_url = self.build_server_url(port)
                if self.auto_open_browser:
                    browser_success = self.open_browser(server_url)
                    # Browser failure is not fatal - log but continue
                    if not browser_success:
                        self.log_warning("Browser opening failed, but server is running")
                
                # Mark as successfully started
                self.current_port = port
                self.log_info(f"Desktop application started successfully on port {port}")
                return True
                
            except Exception as e:
                self.log_error(f"Exception during startup: {e}")
                return False
    
    def shutdown(self) -> bool:
        """Shutdown the desktop application.
        
        Returns:
            True if shutdown successful, False otherwise
        """
        try:
            if not self.is_running():
                self.log_info("Application is not running")
                return True
            
            self.log_info("Shutting down desktop application")
            
            # Stop the server
            if self.stop_server():
                self.current_port = None
                self.log_info("Desktop application shutdown complete")
                return True
            else:
                self.log_error("Server shutdown failed")
                return False
                
        except Exception as e:
            self.log_error(f"Exception during shutdown: {e}")
            return False
    
    def is_running(self) -> bool:
        """Check if the application is currently running.
        
        Returns:
            True if application is running, False otherwise
        """
        return self.current_port is not None
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get information about the server state.
        
        Returns:
            Dictionary containing server information
        """
        info = {
            'host': self.host,
            'port': self.current_port,
            'url': self.build_server_url(self.current_port) if self.current_port else None,
            'running': self.is_running(),
            'web_app_module': self.web_app_module
        }
        return info
    
    def configure_logging_level(self, level: int) -> None:
        """Configure the logging level.
        
        Args:
            level: Logging level (e.g., logging.DEBUG, logging.INFO)
        """
        self.logger.log_level = level
        self.logger.logger.setLevel(level)
        for handler in self.logger.logger.handlers:
            handler.setLevel(level)
    
    def log_info(self, message: str) -> None:
        """Log an info message."""
        self.logger.info(message)
    
    def log_warning(self, message: str) -> None:
        """Log a warning message."""
        self.logger.warning(message)
    
    def log_error(self, message: str) -> None:
        """Log an error message."""
        self.logger.error(message)
    
    def log_debug(self, message: str) -> None:
        """Log a debug message."""
        self.logger.debug(message)
    
    def __enter__(self) -> 'DesktopApp':
        """Context manager entry."""
        if not self.startup():
            raise RuntimeError("Failed to start desktop application")
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit with cleanup."""
        self.shutdown()