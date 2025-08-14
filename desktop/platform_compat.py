# ABOUTME: Cross-platform compatibility layer for Windows/macOS differences
# ABOUTME: Provides unified interface for platform-specific operations, paths, and system interactions

import os
import sys
import stat
import signal
import tempfile
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union

import webbrowser


class PathUtils:
    """Utility class for cross-platform path operations."""
    
    def __init__(self) -> None:
        """Initialize PathUtils."""
        pass
    
    def normalize_path(self, path: Union[str, Path]) -> Path:
        """Normalize a path for the current platform.
        
        Args:
            path: Path to normalize
            
        Returns:
            Normalized Path object
            
        Raises:
            TypeError: If path is None
            ValueError: If path is invalid
        """
        if path is None:
            raise TypeError("Path cannot be None")
        
        if isinstance(path, str):
            # Handle empty string
            if not path:
                raise ValueError("Path cannot be empty")
            path = Path(path)
        
        # Expand user path and resolve
        return path.expanduser().resolve()
    
    def get_executable_extension(self) -> str:
        """Get the executable file extension for the current platform.
        
        Returns:
            File extension (e.g., '.exe' on Windows, '' on Unix)
        """
        return '.exe' if platform.system() == 'Windows' else ''
    
    def get_executable_path(self, base_name: str) -> Path:
        """Get the full executable path with proper extension.
        
        Args:
            base_name: Base name of the executable
            
        Returns:
            Full executable path with extension
        """
        extension = self.get_executable_extension()
        return Path(f"{base_name}{extension}")
    
    def make_executable(self, file_path: Path) -> None:
        """Make a file executable on the current platform.
        
        Args:
            file_path: Path to the file to make executable
            
        Raises:
            OSError: If file cannot be made executable
        """
        if not file_path.exists():
            raise OSError(f"File does not exist: {file_path}")
        
        if platform.system() == 'Windows':
            # On Windows, executability is determined by file extension
            # No additional permissions needed
            return
        
        # On Unix-like systems, set execute permissions
        try:
            current_mode = file_path.stat().st_mode
            # Add execute permission for user, group, and others
            new_mode = current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
            file_path.chmod(new_mode)
        except OSError as e:
            raise OSError(f"Cannot make file executable: {e}")
    
    def get_app_data_dir(self, app_name: str) -> Path:
        """Get the application data directory for the current platform.
        
        Args:
            app_name: Name of the application
            
        Returns:
            Application data directory path
        """
        system = platform.system()
        
        if system == 'Windows':
            # Use LOCALAPPDATA if available, otherwise fallback to user home
            local_app_data = os.environ.get('LOCALAPPDATA')
            if local_app_data:
                return Path(local_app_data) / app_name
            else:
                return Path.home() / app_name
        
        elif system == 'Darwin':
            # Use ~/Library/Application Support/AppName
            return Path.home() / "Library" / "Application Support" / app_name
        
        else:  # Linux and other Unix-like systems
            # Use XDG Base Directory Specification
            xdg_data_home = os.environ.get('XDG_DATA_HOME')
            if xdg_data_home:
                return Path(xdg_data_home) / app_name
            else:
                # Fallback to ~/.local/share/AppName
                return Path.home() / ".local" / "share" / app_name
    
    def get_logs_dir(self, app_name: str) -> Path:
        """Get the logs directory for the current platform.
        
        Args:
            app_name: Name of the application
            
        Returns:
            Logs directory path
        """
        system = platform.system()
        
        if system == 'Windows':
            # Use LOCALAPPDATA/AppName/logs
            return self.get_app_data_dir(app_name) / "logs"
        
        elif system == 'Darwin':
            # Use ~/Library/Logs/AppName
            return Path.home() / "Library" / "Logs" / app_name
        
        else:  # Linux and other Unix-like systems
            # Use XDG or ~/.local/share/AppName/logs
            return self.get_app_data_dir(app_name) / "logs"
    
    def join_paths(self, *path_parts: str) -> Path:
        """Join path parts using the current platform's separator.
        
        Args:
            *path_parts: Path parts to join
            
        Returns:
            Joined path
        """
        if not path_parts:
            return Path()
        
        result = Path(path_parts[0])
        for part in path_parts[1:]:
            result = result / part
        
        return result


class ProcessUtils:
    """Utility class for cross-platform process operations."""
    
    def __init__(self) -> None:
        """Initialize ProcessUtils."""
        pass
    
    def get_current_pid(self) -> int:
        """Get the current process ID.
        
        Returns:
            Current process ID
        """
        return os.getpid()
    
    def is_process_running(self, pid: int) -> bool:
        """Check if a process is running.
        
        Args:
            pid: Process ID to check
            
        Returns:
            True if process is running, False otherwise
        """
        if pid <= 0:
            return False
        
        try:
            if platform.system() == 'Windows':
                # On Windows, use tasklist command
                result = subprocess.run(
                    ['tasklist', '/FI', f'PID eq {pid}'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return str(pid) in result.stdout
            else:
                # On Unix-like systems, use kill with signal 0
                os.kill(pid, 0)
                return True
        except (OSError, subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False
    
    def terminate_process(self, pid: int) -> bool:
        """Terminate a process.
        
        Args:
            pid: Process ID to terminate
            
        Returns:
            True if termination successful, False otherwise
        """
        if pid <= 0:
            return False
        
        try:
            if platform.system() == 'Windows':
                # On Windows, use taskkill command
                result = subprocess.run(
                    ['taskkill', '/PID', str(pid), '/F'],
                    capture_output=True,
                    timeout=10
                )
                return result.returncode == 0
            else:
                # On Unix-like systems, use SIGTERM
                os.kill(pid, signal.SIGTERM)
                return True
        except (OSError, subprocess.TimeoutExpired, subprocess.SubprocessError):
            return False
    
    def get_environment_separator(self) -> str:
        """Get the environment variable path separator.
        
        Returns:
            Path separator (';' on Windows, ':' on Unix-like)
        """
        return ';' if platform.system() == 'Windows' else ':'


class EnvironmentUtils:
    """Utility class for cross-platform environment operations."""
    
    def get_env_var_with_fallback(self, var_name: str, fallback: str) -> str:
        """Get environment variable with fallback value.
        
        Args:
            var_name: Environment variable name
            fallback: Fallback value if variable doesn't exist
            
        Returns:
            Environment variable value or fallback
        """
        return os.environ.get(var_name, fallback)
    
    def set_env_var(self, var_name: str, value: str) -> None:
        """Set environment variable.
        
        Args:
            var_name: Environment variable name
            value: Value to set
        """
        os.environ[var_name] = value
    
    def get_user_home(self) -> Path:
        """Get user home directory.
        
        Returns:
            User home directory path
        """
        return Path.home()
    
    def get_temp_dir(self) -> Path:
        """Get temporary directory.
        
        Returns:
            Temporary directory path
        """
        return Path(tempfile.gettempdir())
    
    def expand_user_path(self, path: str) -> Path:
        """Expand user path (handle ~ expansion).
        
        Args:
            path: Path string to expand
            
        Returns:
            Expanded path
        """
        return Path(path).expanduser()


class BrowserUtils:
    """Utility class for cross-platform browser operations."""
    
    def __init__(self) -> None:
        """Initialize BrowserUtils."""
        pass
    
    def get_default_browsers(self) -> List[str]:
        """Get list of default browsers for the current platform.
        
        Returns:
            List of browser names
        """
        system = platform.system()
        
        if system == 'Windows':
            return [
                'chrome', 'firefox', 'edge', 'ie', 'opera'
            ]
        elif system == 'Darwin':
            return [
                'safari', 'chrome', 'firefox', 'opera'
            ]
        else:  # Linux
            return [
                'firefox', 'chrome', 'chromium', 'opera'
            ]
    
    def is_browser_available(self, browser_name: str) -> bool:
        """Check if a browser is available.
        
        Args:
            browser_name: Name of the browser to check
            
        Returns:
            True if browser is available, False otherwise
        """
        try:
            webbrowser.get(browser_name)
            return True
        except webbrowser.Error:
            return False
        except Exception:
            return False
    
    def get_browser_command(self, browser_name: str) -> Optional[str]:
        """Get the command to launch a browser.
        
        Args:
            browser_name: Name of the browser
            
        Returns:
            Browser command or None if not available
        """
        try:
            system = platform.system()
            
            if system == 'Windows':
                # Windows browser commands
                commands = {
                    'chrome': 'chrome',
                    'firefox': 'firefox',
                    'edge': 'msedge',
                    'ie': 'iexplore'
                }
                return commands.get(browser_name)
            
            elif system == 'Darwin':
                # macOS browser commands
                commands = {
                    'safari': 'open -a Safari',
                    'chrome': 'open -a "Google Chrome"',
                    'firefox': 'open -a Firefox'
                }
                return commands.get(browser_name)
            
            else:  # Linux
                # Linux browser commands
                commands = {
                    'firefox': 'firefox',
                    'chrome': 'google-chrome',
                    'chromium': 'chromium'
                }
                return commands.get(browser_name)
        
        except Exception:
            return None


class SignalUtils:
    """Utility class for cross-platform signal handling."""
    
    def __init__(self) -> None:
        """Initialize SignalUtils."""
        pass
    
    def get_supported_signals(self) -> List[int]:
        """Get list of supported signals for the current platform.
        
        Returns:
            List of supported signal numbers
        """
        supported = [signal.SIGINT]  # SIGINT is always supported
        
        if platform.system() != 'Windows':
            # Unix-like systems support more signals
            supported.extend([
                signal.SIGTERM,
                signal.SIGHUP,
                signal.SIGQUIT
            ])
        else:
            # Windows may support SIGTERM
            if hasattr(signal, 'SIGTERM'):
                try:
                    # Test if SIGTERM can be used
                    old_handler = signal.signal(signal.SIGTERM, signal.SIG_DFL)
                    signal.signal(signal.SIGTERM, old_handler)
                    supported.append(signal.SIGTERM)
                except (OSError, ValueError):
                    pass
        
        return supported
    
    def setup_signal_handler(self, sig: int, handler: Callable) -> bool:
        """Set up a signal handler.
        
        Args:
            sig: Signal number
            handler: Handler function
            
        Returns:
            True if handler was set up successfully, False otherwise
        """
        try:
            signal.signal(sig, handler)
            return True
        except (OSError, ValueError):
            return False
    
    def is_signal_supported(self, sig: int) -> bool:
        """Check if a signal is supported on the current platform.
        
        Args:
            sig: Signal number
            
        Returns:
            True if signal is supported, False otherwise
        """
        try:
            # Try to set a dummy handler and restore original
            old_handler = signal.signal(sig, signal.SIG_DFL)
            signal.signal(sig, old_handler)
            return True
        except (OSError, ValueError):
            return False


class PlatformCompat:
    """Main platform compatibility class providing unified interface."""
    
    def __init__(self) -> None:
        """Initialize PlatformCompat with utility classes."""
        # Initialize utility classes
        self.path_utils = PathUtils()
        self.process_utils = ProcessUtils()
        self.env_utils = EnvironmentUtils()
        self.browser_utils = BrowserUtils()
        self.signal_utils = SignalUtils()
    
    def is_windows(self) -> bool:
        """Check if running on Windows.
        
        Returns:
            True if on Windows, False otherwise
        """
        return platform.system() == 'Windows'
    
    def is_macos(self) -> bool:
        """Check if running on macOS.
        
        Returns:
            True if on macOS, False otherwise
        """
        return platform.system() == 'Darwin'
    
    def is_linux(self) -> bool:
        """Check if running on Linux.
        
        Returns:
            True if on Linux, False otherwise
        """
        return platform.system() == 'Linux'
    
    def get_platform_info(self) -> Dict[str, str]:
        """Get comprehensive platform information.
        
        Returns:
            Dictionary containing platform information
        """
        return {
            'system': platform.system(),
            'version': platform.version(),
            'architecture': platform.architecture()[0],
            'python_version': platform.python_version(),
            'machine': platform.machine(),
            'processor': platform.processor()
        }
    
    def get_system_paths(self) -> Dict[str, Path]:
        """Get important system paths for the current platform.
        
        Returns:
            Dictionary of system paths
        """
        app_name = "WorkJournalMaker"
        
        return {
            'home': self.env_utils.get_user_home(),
            'temp': self.env_utils.get_temp_dir(),
            'app_data': self.path_utils.get_app_data_dir(app_name),
            'logs': self.path_utils.get_logs_dir(app_name)
        }


# Global instance for singleton pattern
_platform_compat_instance: Optional[PlatformCompat] = None


def get_platform_compat() -> PlatformCompat:
    """Get the global platform compatibility instance (singleton).
    
    Returns:
        PlatformCompat instance
    """
    global _platform_compat_instance
    
    if _platform_compat_instance is None:
        _platform_compat_instance = PlatformCompat()
    
    return _platform_compat_instance