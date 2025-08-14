# ABOUTME: Runtime environment detection for desktop vs development modes
# ABOUTME: Provides utilities to detect PyInstaller executable and determine appropriate data directories

import sys
import os
import platform
from pathlib import Path
from typing import Optional


def is_frozen_executable() -> bool:
    """
    Detect if running as a PyInstaller frozen executable.
    
    PyInstaller sets sys.frozen = True and sys._MEIPASS when running
    as a bundled executable. This allows us to distinguish between
    development mode and desktop app mode.
    
    Returns:
        bool: True if running as PyInstaller executable, False otherwise
    """
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def get_executable_directory() -> Optional[Path]:
    """
    Get the directory containing the executable.
    
    Returns:
        Path: Directory containing the executable, or None if not frozen
    """
    if is_frozen_executable():
        # PyInstaller sets sys.executable to the path of the executable
        return Path(sys.executable).parent
    return None


def get_app_data_dir() -> Path:
    """
    Get platform-specific application data directory.
    
    Uses OS-standard locations for desktop apps, or current working
    directory for development mode.
    
    Returns:
        Path: Application data directory
    """
    if is_frozen_executable():
        # Desktop app mode - use OS standard locations
        system = platform.system()
        
        if system == "Darwin":  # macOS
            return Path.home() / "Library" / "Application Support" / "WorkJournalMaker"
        elif system == "Windows":
            # Use LOCALAPPDATA if available, fallback to AppData/Local
            local_app_data = os.environ.get("LOCALAPPDATA")
            if local_app_data:
                return Path(local_app_data) / "WorkJournalMaker"
            else:
                return Path.home() / "AppData" / "Local" / "WorkJournalMaker"
        else:  # Linux and other Unix-like systems
            # Follow XDG Base Directory Specification
            xdg_data_home = os.environ.get("XDG_DATA_HOME")
            if xdg_data_home:
                return Path(xdg_data_home) / "WorkJournalMaker"
            else:
                return Path.home() / ".local" / "share" / "WorkJournalMaker"
    else:
        # Development mode - use current working directory
        return Path.cwd()


def get_app_config_dir() -> Path:
    """
    Get platform-specific application configuration directory.
    
    Separate from data directory for better organization.
    
    Returns:
        Path: Application configuration directory
    """
    if is_frozen_executable():
        system = platform.system()
        
        if system == "Darwin":  # macOS
            return Path.home() / "Library" / "Preferences" / "WorkJournalMaker"
        elif system == "Windows":
            # Use APPDATA if available, fallback to AppData/Roaming
            app_data = os.environ.get("APPDATA")
            if app_data:
                return Path(app_data) / "WorkJournalMaker"
            else:
                return Path.home() / "AppData" / "Roaming" / "WorkJournalMaker"
        else:  # Linux and other Unix-like systems
            xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
            if xdg_config_home:
                return Path(xdg_config_home) / "WorkJournalMaker"
            else:
                return Path.home() / ".config" / "WorkJournalMaker"
    else:
        # Development mode - use current working directory
        return Path.cwd()


def get_app_log_dir() -> Path:
    """
    Get platform-specific application log directory.
    
    Returns:
        Path: Application log directory
    """
    if is_frozen_executable():
        system = platform.system()
        
        if system == "Darwin":  # macOS
            return Path.home() / "Library" / "Logs" / "WorkJournalMaker"
        elif system == "Windows":
            # Use LOCALAPPDATA for logs on Windows
            local_app_data = os.environ.get("LOCALAPPDATA")
            if local_app_data:
                return Path(local_app_data) / "WorkJournalMaker" / "Logs"
            else:
                return Path.home() / "AppData" / "Local" / "WorkJournalMaker" / "Logs"
        else:  # Linux and other Unix-like systems
            # Many Linux systems use /var/log for system logs, but for user apps:
            xdg_data_home = os.environ.get("XDG_DATA_HOME")
            if xdg_data_home:
                return Path(xdg_data_home) / "WorkJournalMaker" / "logs"
            else:
                return Path.home() / ".local" / "share" / "WorkJournalMaker" / "logs"
    else:
        # Development mode - use logs directory in project
        return Path.cwd() / "logs"


def get_runtime_info() -> dict:
    """
    Get comprehensive runtime environment information.
    
    Useful for debugging and logging.
    
    Returns:
        dict: Runtime information including mode, directories, and platform details
    """
    return {
        "is_frozen": is_frozen_executable(),
        "mode": "desktop" if is_frozen_executable() else "development",
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "executable_path": sys.executable,
        "executable_dir": str(get_executable_directory()) if get_executable_directory() else None,
        "app_data_dir": str(get_app_data_dir()),
        "app_config_dir": str(get_app_config_dir()),
        "app_log_dir": str(get_app_log_dir()),
        "working_directory": str(Path.cwd()),
        "meipass": getattr(sys, '_MEIPASS', None)  # PyInstaller temp directory
    }


def ensure_app_directories() -> None:
    """
    Ensure all application directories exist.
    
    Creates necessary directories for data, config, and logs.
    Should be called during application startup.
    """
    directories = [
        get_app_data_dir(),
        get_app_config_dir(),
        get_app_log_dir()
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def print_runtime_info() -> None:
    """
    Print runtime information to console.
    
    Useful for debugging and support.
    """
    info = get_runtime_info()
    
    print("=== WorkJournalMaker Runtime Information ===")
    print(f"Mode: {info['mode']}")
    print(f"Platform: {info['platform']}")
    print(f"Python Version: {info['python_version']}")
    print(f"Executable: {info['executable_path']}")
    
    if info['executable_dir']:
        print(f"Executable Directory: {info['executable_dir']}")
    
    print(f"Working Directory: {info['working_directory']}")
    print(f"App Data Directory: {info['app_data_dir']}")
    print(f"App Config Directory: {info['app_config_dir']}")
    print(f"App Log Directory: {info['app_log_dir']}")
    
    if info['meipass']:
        print(f"PyInstaller Temp Directory: {info['meipass']}")
    
    print("=" * 45)


# For testing and debugging
if __name__ == "__main__":
    print_runtime_info()
    
    print("\nEnsuring directories exist...")
    ensure_app_directories()
    
    print("✓ Runtime detection utility working correctly")