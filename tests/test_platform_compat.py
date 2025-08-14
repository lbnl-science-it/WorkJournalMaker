# ABOUTME: Test suite for cross-platform compatibility layer
# ABOUTME: Validates platform-specific behaviors, path handling, and system integration

import os
import sys
import tempfile
import platform
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Optional, Any

import pytest

from desktop.platform_compat import (
    PlatformCompat,
    PathUtils,
    ProcessUtils,
    EnvironmentUtils,
    BrowserUtils,
    SignalUtils,
    get_platform_compat
)


class TestPlatformCompat:
    """Test the main PlatformCompat class."""
    
    def test_platform_detection(self):
        """Test platform detection methods."""
        compat = PlatformCompat()
        
        # Should detect current platform correctly
        current_system = platform.system()
        assert compat.is_windows() == (current_system == 'Windows')
        assert compat.is_macos() == (current_system == 'Darwin')
        assert compat.is_linux() == (current_system == 'Linux')
        
        # Only one should be true
        platform_checks = [compat.is_windows(), compat.is_macos(), compat.is_linux()]
        assert sum(platform_checks) == 1
    
    def test_get_platform_info(self):
        """Test platform information gathering."""
        compat = PlatformCompat()
        info = compat.get_platform_info()
        
        # Should have required keys
        required_keys = ['system', 'version', 'architecture', 'python_version']
        for key in required_keys:
            assert key in info
            assert info[key] is not None
            assert isinstance(info[key], str)
    
    def test_get_system_paths(self):
        """Test system paths retrieval."""
        compat = PlatformCompat()
        paths = compat.get_system_paths()
        
        # Should have required path keys
        required_keys = ['home', 'temp', 'app_data', 'logs']
        for key in required_keys:
            assert key in paths
            assert paths[key] is not None
            assert isinstance(paths[key], Path)
    
    @patch('platform.system')
    def test_platform_detection_mocked_windows(self, mock_system):
        """Test platform detection with mocked Windows."""
        mock_system.return_value = 'Windows'
        compat = PlatformCompat()
        
        assert compat.is_windows() is True
        assert compat.is_macos() is False
        assert compat.is_linux() is False
    
    @patch('platform.system')
    def test_platform_detection_mocked_macos(self, mock_system):
        """Test platform detection with mocked macOS."""
        mock_system.return_value = 'Darwin'
        compat = PlatformCompat()
        
        assert compat.is_windows() is False
        assert compat.is_macos() is True
        assert compat.is_linux() is False
    
    @patch('platform.system')
    def test_platform_detection_mocked_linux(self, mock_system):
        """Test platform detection with mocked Linux."""
        mock_system.return_value = 'Linux'
        compat = PlatformCompat()
        
        assert compat.is_windows() is False
        assert compat.is_macos() is False
        assert compat.is_linux() is True


class TestPathUtils:
    """Test the PathUtils utility class."""
    
    def test_normalize_path(self):
        """Test path normalization."""
        utils = PathUtils()
        
        # Test basic normalization
        result = utils.normalize_path('/foo/bar/../baz')
        assert result == Path('/foo/baz')
        
        # Test with string input
        result = utils.normalize_path('~/documents/test.txt')
        assert isinstance(result, Path)
    
    def test_get_executable_extension(self):
        """Test executable extension retrieval."""
        utils = PathUtils()
        
        with patch('platform.system') as mock_system:
            # Windows should return .exe
            mock_system.return_value = 'Windows'
            assert utils.get_executable_extension() == '.exe'
            
            # macOS should return empty string
            mock_system.return_value = 'Darwin'
            assert utils.get_executable_extension() == ''
            
            # Linux should return empty string
            mock_system.return_value = 'Linux'
            assert utils.get_executable_extension() == ''
    
    def test_make_executable(self):
        """Test making files executable."""
        utils = PathUtils()
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            
            try:
                # Make executable
                utils.make_executable(temp_path)
                
                if platform.system() != 'Windows':
                    # On Unix-like systems, check permissions
                    stat = temp_path.stat()
                    assert stat.st_mode & 0o111  # Has execute permission
                
            finally:
                temp_path.unlink()
    
    def test_get_app_data_dir(self):
        """Test application data directory retrieval."""
        utils = PathUtils()
        app_name = "TestApp"
        
        with patch('platform.system') as mock_system:
            # Test Windows path
            mock_system.return_value = 'Windows'
            with patch.dict(os.environ, {'LOCALAPPDATA': 'C:\\Users\\Test\\AppData\\Local'}):
                result = utils.get_app_data_dir(app_name)
                assert 'TestApp' in str(result)
            
            # Test Windows fallback
            mock_system.return_value = 'Windows'
            with patch.dict(os.environ, {}, clear=True):
                result = utils.get_app_data_dir(app_name)
                assert isinstance(result, Path)
            
            # Test macOS path
            mock_system.return_value = 'Darwin'
            result = utils.get_app_data_dir(app_name)
            assert 'Library' in str(result)
            assert 'Application Support' in str(result)
            
            # Test Linux path
            mock_system.return_value = 'Linux'
            result = utils.get_app_data_dir(app_name)
            assert '.local' in str(result) or 'share' in str(result)
    
    def test_get_logs_dir(self):
        """Test logs directory retrieval."""
        utils = PathUtils()
        app_name = "TestApp"
        
        with patch('platform.system') as mock_system:
            # Test Windows
            mock_system.return_value = 'Windows'
            result = utils.get_logs_dir(app_name)
            assert 'TestApp' in str(result)
            assert 'logs' in str(result).lower()
            
            # Test macOS
            mock_system.return_value = 'Darwin'
            result = utils.get_logs_dir(app_name)
            assert 'Library' in str(result)
            assert 'Logs' in str(result)
            
            # Test Linux
            mock_system.return_value = 'Linux'
            result = utils.get_logs_dir(app_name)
            assert 'logs' in str(result).lower()
    
    def test_join_paths(self):
        """Test cross-platform path joining."""
        utils = PathUtils()
        
        result = utils.join_paths('home', 'user', 'documents', 'file.txt')
        assert isinstance(result, Path)
        assert 'home' in str(result)
        assert 'user' in str(result)
        assert 'documents' in str(result)
        assert 'file.txt' in str(result)


class TestProcessUtils:
    """Test the ProcessUtils utility class."""
    
    def test_get_current_pid(self):
        """Test current process ID retrieval."""
        utils = ProcessUtils()
        pid = utils.get_current_pid()
        
        assert isinstance(pid, int)
        assert pid > 0
        assert pid == os.getpid()
    
    def test_is_process_running(self):
        """Test process running check.""" 
        utils = ProcessUtils()
        
        # Current process should be running
        current_pid = os.getpid()
        assert utils.is_process_running(current_pid) is True
        
        # Invalid PID should not be running
        assert utils.is_process_running(999999) is False
    
    @patch('os.kill')
    @patch('platform.system')
    def test_terminate_process_unix(self, mock_system, mock_kill):
        """Test process termination on Unix-like systems."""
        mock_system.return_value = 'Darwin'  # Non-Windows system
        utils = ProcessUtils()
        
        # Test successful termination
        mock_kill.return_value = None
        result = utils.terminate_process(1234)
        assert result is True
        mock_kill.assert_called_with(1234, 15)  # SIGTERM
    
    @patch('subprocess.run')
    @patch('platform.system')
    def test_terminate_process_windows(self, mock_system, mock_run):
        """Test process termination on Windows."""
        mock_system.return_value = 'Windows'
        utils = ProcessUtils()
        
        # Test successful termination
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        result = utils.terminate_process(1234)
        assert result is True
        mock_run.assert_called_once()
    
    def test_get_environment_separator(self):
        """Test environment path separator."""
        utils = ProcessUtils()
        
        with patch('platform.system') as mock_system:
            # Windows uses semicolon
            mock_system.return_value = 'Windows'
            assert utils.get_environment_separator() == ';'
            
            # Unix-like systems use colon
            mock_system.return_value = 'Darwin'
            assert utils.get_environment_separator() == ':'
            
            mock_system.return_value = 'Linux'
            assert utils.get_environment_separator() == ':'


class TestEnvironmentUtils:
    """Test the EnvironmentUtils utility class."""
    
    def test_get_env_var_with_fallback(self):
        """Test environment variable retrieval with fallback."""
        utils = EnvironmentUtils()
        
        # Test existing variable
        with patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
            result = utils.get_env_var_with_fallback('TEST_VAR', 'fallback')
            assert result == 'test_value'
        
        # Test fallback
        result = utils.get_env_var_with_fallback('NONEXISTENT_VAR', 'fallback')
        assert result == 'fallback'
    
    def test_set_env_var(self):
        """Test environment variable setting."""
        utils = EnvironmentUtils()
        
        utils.set_env_var('TEST_SET_VAR', 'test_value')
        assert os.environ.get('TEST_SET_VAR') == 'test_value'
        
        # Cleanup
        del os.environ['TEST_SET_VAR']
    
    def test_get_user_home(self):
        """Test user home directory retrieval."""
        utils = EnvironmentUtils()
        home = utils.get_user_home()
        
        assert isinstance(home, Path)
        assert home.exists()
        assert home.is_dir()
    
    def test_get_temp_dir(self):
        """Test temporary directory retrieval."""
        utils = EnvironmentUtils()
        temp_dir = utils.get_temp_dir()
        
        assert isinstance(temp_dir, Path)
        assert temp_dir.exists()
        assert temp_dir.is_dir()
    
    def test_expand_user_path(self):
        """Test user path expansion."""
        utils = EnvironmentUtils()
        
        # Test tilde expansion
        result = utils.expand_user_path('~/documents')
        assert isinstance(result, Path)
        assert '~' not in str(result)
        
        # Test absolute path (no change)
        result = utils.expand_user_path('/absolute/path')
        assert str(result) == '/absolute/path'


class TestBrowserUtils:
    """Test the BrowserUtils utility class."""
    
    def test_get_default_browsers(self):
        """Test default browser list retrieval."""
        utils = BrowserUtils()
        
        with patch('platform.system') as mock_system:
            # Test Windows browsers
            mock_system.return_value = 'Windows'
            browsers = utils.get_default_browsers()
            assert isinstance(browsers, list)
            assert len(browsers) > 0
            assert 'chrome' in browsers or 'firefox' in browsers
            
            # Test macOS browsers
            mock_system.return_value = 'Darwin'
            browsers = utils.get_default_browsers()
            assert isinstance(browsers, list)
            assert len(browsers) > 0
            assert 'safari' in browsers or 'chrome' in browsers
            
            # Test Linux browsers
            mock_system.return_value = 'Linux'
            browsers = utils.get_default_browsers()
            assert isinstance(browsers, list)
            assert len(browsers) > 0
    
    @patch('webbrowser.get')
    def test_is_browser_available(self, mock_get):
        """Test browser availability check."""
        utils = BrowserUtils()
        
        # Test available browser
        mock_get.return_value = Mock()
        assert utils.is_browser_available('chrome') is True
        
        # Test unavailable browser
        mock_get.side_effect = Exception()
        assert utils.is_browser_available('nonexistent') is False
    
    def test_get_browser_command(self):
        """Test browser command retrieval."""
        utils = BrowserUtils()
        
        with patch('platform.system') as mock_system:
            # Test Windows command
            mock_system.return_value = 'Windows'
            result = utils.get_browser_command('chrome')
            assert isinstance(result, (str, type(None)))
            
            # Test macOS command
            mock_system.return_value = 'Darwin'
            result = utils.get_browser_command('safari')
            assert isinstance(result, (str, type(None)))


class TestSignalUtils:
    """Test the SignalUtils utility class."""
    
    def test_get_supported_signals(self):
        """Test supported signals retrieval."""
        utils = SignalUtils()
        signals = utils.get_supported_signals()
        
        assert isinstance(signals, list)
        assert len(signals) > 0
        
        # SIGINT should always be supported
        import signal
        assert signal.SIGINT in signals
        
        # SIGTERM support depends on platform
        if platform.system() != 'Windows':
            assert signal.SIGTERM in signals
    
    def test_setup_signal_handler(self):
        """Test signal handler setup."""
        utils = SignalUtils()
        
        import signal
        handler_called = {'value': False}
        
        def test_handler(signum, frame):
            handler_called['value'] = True
        
        # Test SIGINT (should work on all platforms)
        original_handler = signal.signal(signal.SIGINT, signal.SIG_DFL)
        try:
            result = utils.setup_signal_handler(signal.SIGINT, test_handler)
            assert result is True
        finally:
            signal.signal(signal.SIGINT, original_handler)
    
    def test_is_signal_supported(self):
        """Test signal support check."""
        utils = SignalUtils()
        
        import signal
        
        # SIGINT should be supported on all platforms
        assert utils.is_signal_supported(signal.SIGINT) is True
        
        # SIGTERM support depends on platform
        if platform.system() == 'Windows':
            # May or may not be supported on Windows
            result = utils.is_signal_supported(signal.SIGTERM)
            assert isinstance(result, bool)
        else:
            # Should be supported on Unix-like systems
            assert utils.is_signal_supported(signal.SIGTERM) is True


class TestPlatformCompatIntegration:
    """Test integration scenarios for platform compatibility."""
    
    def test_get_platform_compat_singleton(self):
        """Test platform compatibility singleton."""
        compat1 = get_platform_compat()
        compat2 = get_platform_compat()
        
        assert compat1 is compat2  # Should be the same instance
        assert isinstance(compat1, PlatformCompat)
    
    def test_full_system_paths_integration(self):
        """Test complete system paths integration."""
        compat = get_platform_compat()
        
        # Get all system paths
        paths = compat.get_system_paths()
        
        # Verify all paths exist or can be created
        for path_name, path_obj in paths.items():
            assert isinstance(path_obj, Path)
            
            # Some paths might not exist (like app_data), but parent should
            if not path_obj.exists():
                assert path_obj.parent.exists() or path_obj.parent.parent.exists()
    
    def test_cross_platform_executable_path(self):
        """Test cross-platform executable path handling."""
        compat = get_platform_compat()
        
        base_name = "WorkJournalMaker"
        exe_path = compat.path_utils.get_executable_path(base_name)
        
        # Should include proper extension
        if compat.is_windows():
            assert str(exe_path).endswith('.exe')
        else:
            assert not str(exe_path).endswith('.exe')
    
    def test_environment_and_paths_integration(self):
        """Test integration between environment and path utilities."""
        compat = get_platform_compat()
        
        # Get home directory both ways
        home_from_env = compat.env_utils.get_user_home()
        home_from_paths = compat.get_system_paths()['home']
        
        # Should be the same
        assert home_from_env == home_from_paths
    
    @patch('platform.system')
    def test_cross_platform_signal_compatibility(self, mock_system):
        """Test signal compatibility across platforms."""
        import signal
        
        # Test Windows compatibility
        mock_system.return_value = 'Windows'
        compat = PlatformCompat()
        
        signals = compat.signal_utils.get_supported_signals()
        assert signal.SIGINT in signals
        # SIGTERM may or may not be in Windows signals
        
        # Test Unix compatibility
        mock_system.return_value = 'Darwin'
        compat = PlatformCompat()
        
        signals = compat.signal_utils.get_supported_signals()
        assert signal.SIGINT in signals
        assert signal.SIGTERM in signals


class TestErrorHandling:
    """Test error handling in platform compatibility utilities."""
    
    def test_path_utils_invalid_input(self):
        """Test PathUtils with invalid input."""
        utils = PathUtils()
        
        # Test with None input
        with pytest.raises((TypeError, ValueError)):
            utils.normalize_path(None)
    
    def test_process_utils_invalid_pid(self):
        """Test ProcessUtils with invalid PID."""
        utils = ProcessUtils()
        
        # Test with invalid PID
        assert utils.is_process_running(-1) is False
        assert utils.is_process_running(0) is False
        
        # Test termination with invalid PID
        result = utils.terminate_process(-1)
        assert result is False
    
    def test_environment_utils_missing_vars(self):
        """Test EnvironmentUtils with missing variables."""
        utils = EnvironmentUtils()
        
        # Test missing variable with fallback
        result = utils.get_env_var_with_fallback('DEFINITELY_MISSING_VAR_12345', 'default')
        assert result == 'default'
    
    def test_browser_utils_invalid_browser(self):
        """Test BrowserUtils with invalid browser."""
        utils = BrowserUtils()
        
        # Test non-existent browser
        assert utils.is_browser_available('definitely_not_a_browser_12345') is False
        
        # Test browser command for non-existent browser
        result = utils.get_browser_command('definitely_not_a_browser_12345')
        assert result is None