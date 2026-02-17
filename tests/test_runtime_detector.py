# ABOUTME: Tests for runtime detection utility
# ABOUTME: Validates PyInstaller detection and directory path resolution

import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import os

from desktop.runtime_detector import (
    is_frozen_executable,
    get_executable_directory,
    get_app_data_dir,
    get_app_config_dir,
    get_app_log_dir,
    get_runtime_info,
    ensure_app_directories
)


class TestRuntimeDetector(unittest.TestCase):
    """Test suite for runtime detection utility."""
    
    def test_is_frozen_executable_development_mode(self):
        """Test detection in development mode (should be False)."""
        # In normal development, this should be False
        result = is_frozen_executable()
        self.assertFalse(result)
    
    def test_get_executable_directory_development_mode(self):
        """Test executable directory in development mode (should be None)."""
        result = get_executable_directory()
        self.assertIsNone(result)
    
    def test_get_app_data_dir_development_mode(self):
        """Test app data directory in development mode."""
        result = get_app_data_dir()
        expected = Path.cwd()
        self.assertEqual(result, expected)
    
    def test_get_runtime_info_development_mode(self):
        """Test runtime info in development mode."""
        info = get_runtime_info()
        
        self.assertFalse(info['is_frozen'])
        self.assertEqual(info['mode'], 'development')
        self.assertEqual(info['platform'], 'Darwin')  # On macOS
        self.assertIsNone(info['executable_dir'])
        self.assertIsNone(info['meipass'])
        self.assertEqual(info['app_data_dir'], str(Path.cwd()))


class TestRuntimeDetectorFrozenMode(unittest.TestCase):
    """Test suite for runtime detection in frozen (PyInstaller) mode."""
    
    @patch('sys.frozen', True, create=True)
    @patch('sys._MEIPASS', '/tmp/meipass', create=True)
    def test_is_frozen_executable_frozen_mode(self):
        """Test detection in frozen mode (should be True)."""
        result = is_frozen_executable()
        self.assertTrue(result)
    
    @patch('sys.frozen', True, create=True) 
    @patch('sys._MEIPASS', '/tmp/meipass', create=True)
    @patch('sys.executable', '/Applications/WorkJournalMaker.app/Contents/MacOS/WorkJournalMaker')
    def test_get_executable_directory_frozen_mode(self):
        """Test executable directory in frozen mode."""
        result = get_executable_directory()
        expected = Path('/Applications/WorkJournalMaker.app/Contents/MacOS')
        self.assertEqual(result, expected)
    
    @patch('sys.frozen', True, create=True)
    @patch('sys._MEIPASS', '/tmp/meipass', create=True)
    @patch('platform.system', return_value='Darwin')
    def test_get_app_data_dir_frozen_macos(self, mock_system):
        """Test app data directory in frozen mode on macOS."""
        result = get_app_data_dir()
        expected = Path.home() / "Library" / "Application Support" / "WorkJournalMaker"
        self.assertEqual(result, expected)
    
    @patch('sys.frozen', True, create=True)
    @patch('sys._MEIPASS', '/tmp/meipass', create=True)
    @patch('platform.system', return_value='Windows')
    @patch.dict(os.environ, {'LOCALAPPDATA': 'C:\\Users\\Test\\AppData\\Local'})
    def test_get_app_data_dir_frozen_windows(self, mock_system):
        """Test app data directory in frozen mode on Windows."""
        result = get_app_data_dir()
        expected = Path('C:\\Users\\Test\\AppData\\Local') / "WorkJournalMaker"
        self.assertEqual(result, expected)
    
    @patch('sys.frozen', True, create=True)
    @patch('sys._MEIPASS', '/tmp/meipass', create=True)
    @patch('platform.system', return_value='Linux')
    def test_get_app_data_dir_frozen_linux(self, mock_system):
        """Test app data directory in frozen mode on Linux."""
        result = get_app_data_dir()
        expected = Path.home() / ".local" / "share" / "WorkJournalMaker"
        self.assertEqual(result, expected)
    
    @patch('sys.frozen', True, create=True)
    @patch('sys._MEIPASS', '/tmp/meipass', create=True)
    @patch('platform.system', return_value='Darwin')
    def test_get_app_config_dir_frozen_macos(self, mock_system):
        """Test app config directory in frozen mode on macOS."""
        result = get_app_config_dir()
        expected = Path.home() / "Library" / "Preferences" / "WorkJournalMaker"
        self.assertEqual(result, expected)
    
    @patch('sys.frozen', True, create=True)
    @patch('sys._MEIPASS', '/tmp/meipass', create=True)
    @patch('platform.system', return_value='Darwin')
    def test_get_app_log_dir_frozen_macos(self, mock_system):
        """Test app log directory in frozen mode on macOS."""
        result = get_app_log_dir()
        expected = Path.home() / "Library" / "Logs" / "WorkJournalMaker"
        self.assertEqual(result, expected)
    
    @patch('sys.frozen', True, create=True)
    @patch('sys._MEIPASS', '/tmp/meipass', create=True)
    @patch('platform.system', return_value='Darwin')
    @patch('sys.executable', '/Applications/WorkJournalMaker.app/Contents/MacOS/WorkJournalMaker')
    def test_get_runtime_info_frozen_mode(self, mock_system):
        """Test runtime info in frozen mode."""
        info = get_runtime_info()
        
        self.assertTrue(info['is_frozen'])
        self.assertEqual(info['mode'], 'desktop')
        self.assertEqual(info['platform'], 'Darwin')
        self.assertIsNotNone(info['executable_dir'])
        self.assertEqual(info['meipass'], '/tmp/meipass')
        self.assertIn('Library/Application Support/WorkJournalMaker', info['app_data_dir'])


class TestDirectoryCreation(unittest.TestCase):
    """Test directory creation functionality."""
    
    @patch('desktop.runtime_detector.get_app_data_dir')
    @patch('desktop.runtime_detector.get_app_config_dir')
    @patch('desktop.runtime_detector.get_app_log_dir')
    def test_ensure_app_directories(self, mock_log_dir, mock_config_dir, mock_data_dir):
        """Test that ensure_app_directories creates all necessary directories."""
        # Create mock Path objects
        mock_data_path = MagicMock(spec=Path)
        mock_config_path = MagicMock(spec=Path)
        mock_log_path = MagicMock(spec=Path)
        
        mock_data_dir.return_value = mock_data_path
        mock_config_dir.return_value = mock_config_path
        mock_log_dir.return_value = mock_log_path
        
        # Call the function
        ensure_app_directories()
        
        # Verify mkdir was called on each directory
        mock_data_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_config_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_log_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)


if __name__ == '__main__':
    unittest.main()