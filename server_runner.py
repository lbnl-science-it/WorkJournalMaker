# ABOUTME: Main entry point script for the desktop application package
# ABOUTME: Provides CLI interface, signal handling, and application lifecycle management

import argparse
import logging
import signal
import sys
import time
from typing import Optional, Tuple

from desktop.desktop_app import DesktopApp


def parse_args(args: Optional[list] = None) -> argparse.Namespace:
    """Parse command line arguments.
    
    Args:
        args: List of arguments to parse (uses sys.argv if None)
        
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Work Journal Maker Desktop Application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Start with default settings
  %(prog)s --host localhost --port-range 3000-3010  # Custom host and port range
  %(prog)s --log-level DEBUG --no-browser    # Debug mode without auto-opening browser
  %(prog)s --browser chrome --log-dir ./logs # Specific browser and log directory
        """
    )
    
    # Network configuration
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host address to bind the server (default: %(default)s)"
    )
    
    parser.add_argument(
        "--port-range",
        default="8000-8099",
        help="Port range for server (format: START-END or single PORT, default: %(default)s)"
    )
    
    # Logging configuration
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: %(default)s)"
    )
    
    parser.add_argument(
        "--log-dir",
        help="Directory for log files (uses default if not specified)"
    )
    
    # Browser configuration
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Don't automatically open browser"
    )
    
    parser.add_argument(
        "--browser",
        help="Preferred browser to open (e.g., chrome, firefox, safari)"
    )
    
    # Timeout configuration
    parser.add_argument(
        "--startup-timeout",
        type=float,
        default=30.0,
        help="Maximum time to wait for server startup in seconds (default: %(default)s)"
    )
    
    parser.add_argument(
        "--shutdown-timeout",
        type=float,
        default=10.0,
        help="Maximum time to wait for server shutdown in seconds (default: %(default)s)"
    )
    
    return parser.parse_args(args)


def parse_port_range(port_range: str) -> Tuple[int, int]:
    """Parse port range string into start and end ports.
    
    Args:
        port_range: Port range string (e.g., "8000-8099" or "8080")
        
    Returns:
        Tuple of (start_port, end_port)
        
    Raises:
        ValueError: If port range format is invalid
    """
    if "-" in port_range:
        parts = port_range.split("-")
        if len(parts) != 2:
            raise ValueError(f"Invalid port range format: {port_range}")
        
        try:
            start_port = int(parts[0])
            end_port = int(parts[1])
        except ValueError:
            raise ValueError(f"Invalid port range format: {port_range}")
    else:
        try:
            start_port = end_port = int(port_range)
        except ValueError:
            raise ValueError(f"Invalid port range format: {port_range}")
    
    # Validate port range
    if start_port > end_port:
        raise ValueError(f"Invalid port range: start port {start_port} > end port {end_port}")
    
    if start_port < 1024 or end_port > 65535:
        raise ValueError("Port numbers must be between 1024 and 65535")
    
    return start_port, end_port


class ServerRunner:
    """Main server runner class for desktop application.
    
    Handles application lifecycle, signal handling, and component coordination.
    """
    
    def __init__(
        self,
        host: str = "127.0.0.1",
        port_range: Tuple[int, int] = (8000, 8099),
        log_level: str = "INFO",
        log_dir: Optional[str] = None,
        startup_timeout: float = 30.0,
        shutdown_timeout: float = 10.0,
        auto_open_browser: bool = True,
        preferred_browser: Optional[str] = None
    ) -> None:
        """Initialize the ServerRunner.
        
        Args:
            host: Host address for the server
            port_range: Tuple of (start_port, end_port)
            log_level: Logging level
            log_dir: Directory for log files
            startup_timeout: Maximum time to wait for server startup
            shutdown_timeout: Maximum time to wait for server shutdown
            auto_open_browser: Whether to automatically open browser
            preferred_browser: Preferred browser name
        """
        self.host = host
        self.port_range = port_range
        self.log_level = log_level
        self.log_dir = log_dir
        self.startup_timeout = startup_timeout
        self.shutdown_timeout = shutdown_timeout
        self.auto_open_browser = auto_open_browser
        self.preferred_browser = preferred_browser
        
        # State management
        self._shutdown_requested = False
        self._signal_count = 0
        
        # Create desktop application
        try:
            self.desktop_app = DesktopApp(
                host=host,
                port_range=port_range,
                startup_timeout=startup_timeout,
                shutdown_timeout=shutdown_timeout,
                auto_open_browser=auto_open_browser,
                preferred_browser=preferred_browser,
                log_dir=log_dir
            )
            
            # Configure logging level
            log_level_int = getattr(logging, log_level.upper())
            self.desktop_app.configure_logging_level(log_level_int)
            
        except Exception as e:
            print(f"Failed to initialize desktop application: {e}")
            raise
    
    def setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            
            # SIGTERM is not available on Windows
            if not self.is_windows():
                signal.signal(signal.SIGTERM, self._signal_handler)
                
        except (OSError, ValueError) as e:
            # Signal setup may fail in some environments (e.g., threads)
            # Log the issue but don't crash the application
            print(f"Warning: Could not set up signal handlers: {e}")
    
    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        self._signal_count += 1
        
        if self._signal_count == 1:
            print(f"\nReceived signal {signum}, shutting down gracefully...")
            self._shutdown_requested = True
        else:
            print(f"\nReceived signal {signum} again, forcing exit...")
            sys.exit(1)
    
    def start(self) -> bool:
        """Start the desktop application.
        
        Returns:
            True if startup successful, False otherwise
        """
        try:
            self.desktop_app.log_info("Starting server runner")
            success = self.desktop_app.startup()
            
            if success:
                server_info = self.desktop_app.get_server_info()
                print(f"Work Journal Maker is running at {server_info['url']}")
                print("Press Ctrl+C to stop the server")
            else:
                print("Failed to start the application")
            
            return success
            
        except Exception as e:
            print(f"Error starting application: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop the desktop application.
        
        Returns:
            True if shutdown successful, False otherwise
        """
        try:
            self.desktop_app.log_info("Stopping server runner")
            success = self.desktop_app.shutdown()
            
            if success:
                print("Application stopped successfully")
            else:
                print("Error stopping the application")
            
            return success
            
        except Exception as e:
            print(f"Error stopping application: {e}")
            return False
    
    def run(self) -> int:
        """Run the complete application lifecycle.
        
        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            # Set up signal handlers
            self.setup_signal_handlers()
            
            # Start the application
            if not self.start():
                return 1
            
            # Main event loop
            try:
                while not self._shutdown_requested and self.desktop_app.is_running():
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print("\nKeyboard interrupt received, shutting down...")
                self._shutdown_requested = True
            
            # Stop the application
            if not self.stop():
                return 1
            
            return 0
            
        except Exception as e:
            print(f"Unexpected error during execution: {e}")
            return 1
    
    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            if hasattr(self, 'desktop_app') and self.desktop_app.is_running():
                self.desktop_app.shutdown()
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def is_windows(self) -> bool:
        """Check if running on Windows platform.
        
        Returns:
            True if on Windows, False otherwise
        """
        return sys.platform.startswith('win')
    
    def is_macos(self) -> bool:
        """Check if running on macOS platform.
        
        Returns:
            True if on macOS, False otherwise
        """
        return sys.platform == 'darwin'


def main() -> None:
    """Main entry point for the application."""
    try:
        # Parse command line arguments
        args = parse_args()
        
        # Parse port range
        port_start, port_end = parse_port_range(args.port_range)
        
        # Create and run server
        runner = ServerRunner(
            host=args.host,
            port_range=(port_start, port_end),
            log_level=args.log_level,
            log_dir=args.log_dir,
            startup_timeout=args.startup_timeout,
            shutdown_timeout=args.shutdown_timeout,
            auto_open_browser=not args.no_browser,
            preferred_browser=args.browser
        )
        
        exit_code = runner.run()
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()