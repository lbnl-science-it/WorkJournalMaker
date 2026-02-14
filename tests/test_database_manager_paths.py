# ABOUTME: Tests for database manager path resolution
# ABOUTME: Validates proper database location based on runtime environment

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import os
import tempfile
import shutil

from web.database import DatabaseManager


class TestDatabaseManagerPaths(unittest.TestCase):
    """Test database path resolution based on runtime environment."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_development_mode_path(self):
        """Test database path in development mode."""
        # In development mode, should use ./web/journal_index.db
        db_manager = DatabaseManager()
        
        expected_path = Path.cwd() / "web" / "journal_index.db"
        actual_path = Path(db_manager.database_path)
        
        self.assertEqual(actual_path, expected_path)
    
    @patch('sys.frozen', True, create=True)
    @patch('sys._MEIPASS', '/tmp/meipass', create=True)
    @patch('platform.system', return_value='Darwin')
    @patch('desktop.runtime_detector.Path.home')
    def test_desktop_mode_path_macos(self, mock_home, mock_system):
        """Test database path in desktop mode on macOS."""
        # Mock home directory
        mock_home.return_value = self.temp_dir
        
        # Clear any cached modules to ensure fresh import
        import sys
        modules_to_clear = [mod for mod in sys.modules.keys() if 'runtime_detector' in mod]
        for mod in modules_to_clear:
            del sys.modules[mod]
        
        db_manager = DatabaseManager()
        
        expected_path = self.temp_dir / "Library" / "Application Support" / "WorkJournalMaker" / "journal_index.db"
        actual_path = Path(db_manager.database_path)
        
        self.assertEqual(actual_path, expected_path)
        
        # Verify directory was created
        self.assertTrue(expected_path.parent.exists())
    
    @patch('sys.frozen', True, create=True)
    @patch('sys._MEIPASS', '/tmp/meipass', create=True)
    @patch('platform.system', return_value='Windows')
    @patch.dict(os.environ, {'LOCALAPPDATA': str(Path(tempfile.gettempdir()) / 'TestAppData')})
    def test_desktop_mode_path_windows(self, mock_system):
        """Test database path in desktop mode on Windows."""
        # Create mock LOCALAPPDATA directory
        test_appdata = Path(tempfile.gettempdir()) / 'TestAppData'
        test_appdata.mkdir(exist_ok=True)
        
        try:
            # Clear any cached modules to ensure fresh import
            import sys
            modules_to_clear = [mod for mod in sys.modules.keys() if 'runtime_detector' in mod]
            for mod in modules_to_clear:
                del sys.modules[mod]
            
            db_manager = DatabaseManager()
            
            expected_path = test_appdata / "WorkJournalMaker" / "journal_index.db"
            actual_path = Path(db_manager.database_path)
            
            self.assertEqual(actual_path, expected_path)
            
            # Verify directory was created
            self.assertTrue(expected_path.parent.exists())
            
        finally:
            # Clean up
            if test_appdata.exists():
                shutil.rmtree(test_appdata)
    
    def test_explicit_path_override(self):
        """Test that explicit path overrides automatic detection."""
        custom_path = "/tmp/custom_journal.db"
        
        db_manager = DatabaseManager(database_path=custom_path)
        
        self.assertEqual(db_manager.database_path, custom_path)
    
    def test_fallback_on_import_error(self):
        """Test fallback behavior when runtime_detector import fails."""
        # Mock the import to fail
        with patch('builtins.__import__', side_effect=ImportError):
            db_manager = DatabaseManager()
            
            # Should fall back to web/journal_index.db
            expected_path = Path("web/journal_index.db")
            actual_path = Path(db_manager.database_path)
            
            self.assertEqual(actual_path, expected_path)
    
    def test_directory_creation(self):
        """Test that database directory is created during initialization."""
        test_db_path = self.temp_dir / "subdir" / "test.db"
        
        # Directory should not exist initially
        self.assertFalse(test_db_path.parent.exists())
        
        # Create DatabaseManager with custom path
        db_manager = DatabaseManager(database_path=str(test_db_path))
        
        # Directory should be created by _get_default_database_path or constructor
        self.assertTrue(test_db_path.parent.exists())


class TestDatabaseManagerInitialization(unittest.TestCase):
    """Test database manager initialization."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_db_path = self.temp_dir / "test_journal.db"
    
    def tearDown(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_database_manager_initialization(self):
        """Test that DatabaseManager initializes without errors."""
        db_manager = DatabaseManager(database_path=str(self.test_db_path))
        
        self.assertEqual(db_manager.database_path, str(self.test_db_path))
        self.assertIsNone(db_manager.engine)
        self.assertIsNone(db_manager.SessionLocal)
    
    def test_path_resolution_consistent(self):
        """Test that path resolution is consistent across multiple calls."""
        db_manager1 = DatabaseManager()
        db_manager2 = DatabaseManager()
        
        self.assertEqual(db_manager1.database_path, db_manager2.database_path)


if __name__ == '__main__':
    unittest.main()