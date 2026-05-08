# ABOUTME: Tests for database manager path resolution
# ABOUTME: Validates proper database location based on runtime environment

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import os
import tempfile
import shutil
import platform

from web.database import DatabaseManager


class TestDatabaseManagerPaths(unittest.TestCase):
    """Test database path resolution based on runtime environment."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_development_mode_path(self):
        """Test database path in development mode uses OS-standard dir with _dev suffix."""
        db_manager = DatabaseManager()
        actual_path = Path(db_manager.database_path)
        self.assertEqual(actual_path.name, "journal_index_dev.db")
        if platform.system() == "Darwin":
            expected_dir = Path.home() / "Library" / "Application Support" / "WorkJournalMaker"
        else:
            expected_dir = Path.home() / ".local" / "share" / "WorkJournalMaker"
        self.assertEqual(actual_path.parent, expected_dir)

    @patch('sys.frozen', True, create=True)
    @patch('sys._MEIPASS', '/tmp/meipass', create=True)
    @patch('platform.system', return_value='Darwin')
    @patch('desktop.runtime_detector.Path.home')
    def test_desktop_mode_path_macos(self, mock_home, mock_system):
        """Test database path in desktop mode on macOS uses prod filename."""
        mock_home.return_value = self.temp_dir
        import sys
        modules_to_clear = [mod for mod in sys.modules.keys() if 'runtime_detector' in mod]
        for mod in modules_to_clear:
            del sys.modules[mod]
        db_manager = DatabaseManager()
        expected_path = self.temp_dir / "Library" / "Application Support" / "WorkJournalMaker" / "journal_index.db"
        actual_path = Path(db_manager.database_path)
        self.assertEqual(actual_path, expected_path)
        self.assertTrue(expected_path.parent.exists())

    def test_explicit_path_override(self):
        """Test that explicit path overrides automatic detection."""
        custom_path = str(self.temp_dir / "custom_journal.db")
        db_manager = DatabaseManager(database_path=custom_path)
        self.assertEqual(db_manager.database_path, custom_path)

    def test_explicit_tilde_path_expansion(self):
        """Test that tilde paths are expanded."""
        db_manager = DatabaseManager(database_path="~/test_journal.db")
        actual_path = Path(db_manager.database_path)
        self.assertTrue(actual_path.is_absolute())
        self.assertNotIn("~", str(actual_path))

    def test_directory_creation(self):
        """Test that database directory is created during initialization."""
        test_db_path = self.temp_dir / "subdir" / "test.db"
        self.assertFalse(test_db_path.parent.exists())
        db_manager = DatabaseManager(database_path=str(test_db_path))
        self.assertTrue(test_db_path.parent.exists())

    def test_path_resolution_consistent(self):
        """Test that path resolution is consistent across multiple calls."""
        db_manager1 = DatabaseManager()
        db_manager2 = DatabaseManager()
        self.assertEqual(db_manager1.database_path, db_manager2.database_path)

    def test_removed_methods_do_not_exist(self):
        """Test that removed fallback methods are no longer on DatabaseManager."""
        db_manager = DatabaseManager(database_path=str(self.temp_dir / "test.db"))
        removed_methods = [
            '_get_user_data_directory',
            '_get_fallback_database_path',
            '_resolve_path_executable_safe',
            '_is_windows_absolute_path',
            '_ensure_directory_exists',
            '_resolve_path_with_fallback',
            '_handle_permission_error',
            '_handle_readonly_filesystem',
            '_create_fallback_directory',
            '_generate_fallback_guidance',
            '_resolve_with_multiple_fallbacks',
            '_get_recovery_guidance',
            '_create_detailed_error',
            '_track_configuration_source',
            '_aggregate_configuration_errors',
            '_validate_database_path',
            '_raise_path_conflict_error',
            '_create_path_error',
            '_validate_path_characters',
        ]
        for method_name in removed_methods:
            self.assertFalse(
                hasattr(db_manager, method_name),
                f"Method {method_name} should have been removed"
            )


class TestDatabaseManagerInitialization(unittest.TestCase):
    """Test database manager initialization."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_db_path = self.temp_dir / "test_journal.db"

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_database_manager_initialization(self):
        """Test that DatabaseManager initializes without errors."""
        db_manager = DatabaseManager(database_path=str(self.test_db_path))
        self.assertEqual(db_manager.database_path, str(self.test_db_path))
        self.assertIsNone(db_manager.engine)
        self.assertIsNone(db_manager.SessionLocal)


if __name__ == '__main__':
    unittest.main()
