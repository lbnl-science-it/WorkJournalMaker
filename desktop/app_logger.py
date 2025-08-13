# ABOUTME: Cross-platform application logger with structured logging and rotation
# ABOUTME: Handles log directory management, file rotation, and cross-platform log paths

import os
import logging
import platform
from pathlib import Path
from typing import Optional, List, Any
from logging.handlers import RotatingFileHandler


class AppLogger:
    """Cross-platform application logger with structured logging and rotation.
    
    Provides comprehensive logging functionality with automatic log rotation,
    cross-platform directory handling, and structured log formatting.
    """
    
    def __init__(
        self,
        log_dir: Optional[str] = None,
        app_name: str = "WorkJournalMaker",
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        log_level: int = logging.INFO
    ) -> None:
        """Initialize the AppLogger.
        
        Args:
            log_dir: Directory for log files (uses platform default if None)
            app_name: Name of the application for log files and directories
            max_bytes: Maximum size of each log file before rotation
            backup_count: Number of backup log files to keep
            log_level: Logging level (e.g., logging.INFO, logging.DEBUG)
            
        Raises:
            ValueError: If parameters are invalid
        """
        if log_dir is not None and log_dir == "":
            raise ValueError("log_dir cannot be None or empty")
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        if backup_count < 0:
            raise ValueError("backup_count must be non-negative")
        if not isinstance(log_level, int) or log_level not in [
            logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL
        ]:
            raise ValueError("Invalid log level")
            
        self.app_name = app_name
        self.log_dir = Path(log_dir) if log_dir else self.get_default_log_directory()
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.log_level = log_level
        
        # Initialize logger
        self.logger = logging.getLogger(app_name)
        self.logger.setLevel(log_level)
    
    def setup_logging(self) -> None:
        """Set up logging handlers and formatters.
        
        Creates log directory if it doesn't exist and configures both
        file and console handlers with appropriate formatting.
        
        Raises:
            OSError: If log directory cannot be created
        """
        # Clear existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Create log directory if it doesn't exist
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            raise OSError(f"Cannot create log directory {self.log_dir}: {e}")
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # File handler with rotation
        log_file = self.log_dir / f"{self.app_name}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def get_default_log_directory(self) -> Path:
        """Get the default log directory based on the platform.
        
        Returns:
            Path object for the default log directory
        """
        system = platform.system()
        home = Path.home()
        
        if system == 'Windows':
            # Use LOCALAPPDATA if available, otherwise fallback to user home
            local_app_data = os.environ.get('LOCALAPPDATA')
            if local_app_data:
                return Path(local_app_data) / self.app_name / "logs"
            else:
                return home / self.app_name / "logs"
        
        elif system == 'Darwin':  # macOS
            # Use ~/Library/Logs/AppName
            return home / "Library" / "Logs" / self.app_name
        
        else:  # Linux and other Unix-like systems
            # Use XDG Base Directory Specification
            xdg_data_home = os.environ.get('XDG_DATA_HOME')
            if xdg_data_home:
                return Path(xdg_data_home) / self.app_name / "logs"
            else:
                # Fallback to ~/.local/share/AppName/logs
                return home / ".local" / "share" / self.app_name / "logs"
    
    def get_log_files(self) -> List[Path]:
        """Get list of all log files in the log directory.
        
        Returns:
            List of Path objects for log files
        """
        if not self.log_dir.exists():
            return []
        
        log_files = []
        for file_path in self.log_dir.iterdir():
            if file_path.is_file() and (
                file_path.suffix == '.log' or 
                '.log.' in file_path.name
            ):
                log_files.append(file_path)
        
        return sorted(log_files)
    
    def get_log_size(self) -> int:
        """Get total size of all log files in bytes.
        
        Returns:
            Total size of log files in bytes
        """
        total_size = 0
        for log_file in self.get_log_files():
            try:
                total_size += log_file.stat().st_size
            except (OSError, FileNotFoundError):
                # Skip files that can't be accessed
                continue
        
        return total_size
    
    def clear_logs(self) -> None:
        """Clear all log files from the log directory."""
        for log_file in self.get_log_files():
            try:
                log_file.unlink()
            except (OSError, FileNotFoundError):
                # Skip files that can't be deleted
                continue
    
    def configure_console_output(self, enabled: bool) -> None:
        """Configure console output on/off.
        
        Args:
            enabled: True to enable console output, False to disable
        """
        # Remove existing console handlers
        console_handlers = [
            h for h in self.logger.handlers 
            if hasattr(h, 'stream') and hasattr(h.stream, 'write')
        ]
        
        for handler in console_handlers:
            self.logger.removeHandler(handler)
        
        # Add console handler if enabled
        if enabled:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            console_handler = logging.StreamHandler()
            console_handler.setLevel(self.log_level)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def debug(self, message: str) -> None:
        """Log a debug message."""
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        """Log an info message."""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log a warning message."""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log an error message."""
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """Log a critical message."""
        self.logger.critical(message)
    
    def __enter__(self) -> 'AppLogger':
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit with cleanup."""
        # Close and remove all handlers
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)