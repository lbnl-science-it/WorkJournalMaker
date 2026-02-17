#!/usr/bin/env python3
"""
Test Suite for Path Resolution Engine - Phase 4

This module tests executable-aware path resolution functionality including:
- Relative path resolution against executable directory
- Tilde expansion in different environments
- Absolute path handling unchanged
- Directory auto-creation with permission fallback
- User data directory fallback on permission errors
- Cross-platform path resolution

Tests follow TDD principles with comprehensive coverage of all path scenarios.
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from typing import Optional, Dict, Any

# Import the modules we'll be testing
from config_manager import ExecutableDetector
from web.database import DatabaseManager


class TestDatabaseManagerPathResolution:
    """Test cases for DatabaseManager path resolution functionality."""

    def test_database_manager_accepts_database_path_parameter(self):
        """Test that DatabaseManager constructor accepts database_path parameter."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Use a path within temp directory that can actually be created
            test_db_path = str(Path(temp_dir) / "database" / "path.db")
            
            # Should be able to create DatabaseManager with database_path
            db_manager = DatabaseManager(database_path=test_db_path)
            assert hasattr(db_manager, 'database_path')
            # Path might be resolved, so check that it ends with the expected file
            assert db_manager.database_path.endswith("path.db")
            assert "database" in db_manager.database_path

    def test_database_manager_default_path_when_none_provided(self):
        """Test DatabaseManager uses default path when database_path is None."""
        db_manager = DatabaseManager(database_path=None)
        
        # Should use the existing default path logic
        assert db_manager.database_path is not None
        assert isinstance(db_manager.database_path, str)

    def test_database_manager_path_resolution_method_exists(self):
        """Test that DatabaseManager has _resolve_path_executable_safe method."""
        db_manager = DatabaseManager()
        
        # Should have the path resolution method
        assert hasattr(db_manager, '_resolve_path_executable_safe')
        assert callable(getattr(db_manager, '_resolve_path_executable_safe'))


class TestExecutableAwarePathResolution:
    """Test cases for executable-aware relative path resolution."""

    def test_relative_path_resolution_against_executable_directory(self):
        """Test relative paths resolve against executable directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exe_dir = Path(temp_dir) / "executable_dir"
            exe_dir.mkdir()
            
            # Test relative path
            relative_path = "data/journal.db"
            
            with patch.object(ExecutableDetector, 'get_executable_directory', return_value=exe_dir):
                db_manager = DatabaseManager(database_path=relative_path)
                resolved_path = db_manager._resolve_path_executable_safe(relative_path)
                
                expected_path = exe_dir / "data" / "journal.db"
                # Use Path.samefile or string comparison that handles symlinks/canonicalization
                resolved_path_obj = Path(resolved_path)
                expected_path_obj = Path(expected_path)
                
                # Check that the paths resolve to the same location
                assert resolved_path_obj.resolve() == expected_path_obj.resolve()

    def test_relative_path_with_dot_notation(self):
        """Test relative paths with ./ and ../ notation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exe_dir = Path(temp_dir) / "app" / "bin"
            exe_dir.mkdir(parents=True)
            
            test_cases = [
                ("./database.db", "database.db"),
                ("../data/journal.db", str(Path("..") / "data" / "journal.db")),
                ("../../shared/db.sqlite", str(Path("..") / ".." / "shared" / "db.sqlite"))
            ]
            
            for input_path, expected_relative in test_cases:
                with patch.object(ExecutableDetector, 'get_executable_directory', return_value=exe_dir):
                    db_manager = DatabaseManager(database_path=input_path)
                    resolved_path = db_manager._resolve_path_executable_safe(input_path)
                    
                    expected_full = exe_dir / expected_relative
                    # Use Path objects to handle canonicalization properly
                    resolved_path_obj = Path(resolved_path)
                    expected_full_obj = Path(expected_full)
                    assert resolved_path_obj.resolve() == expected_full_obj.resolve()

    def test_absolute_path_unchanged(self):
        """Test that absolute paths are returned unchanged."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exe_dir = Path(temp_dir) / "executable_dir"
            exe_dir.mkdir()
            
            absolute_path = str(Path(temp_dir) / "absolute" / "database.db")
            
            with patch.object(ExecutableDetector, 'get_executable_directory', return_value=exe_dir):
                db_manager = DatabaseManager(database_path=absolute_path)
                resolved_path = db_manager._resolve_path_executable_safe(absolute_path)
                
                # Absolute paths should resolve to the same location
                resolved_path_obj = Path(resolved_path)
                absolute_path_obj = Path(absolute_path)
                assert resolved_path_obj.resolve() == absolute_path_obj.resolve()

    def test_windows_absolute_path_unchanged(self):
        """Test that Windows absolute paths are handled correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exe_dir = Path(temp_dir) / "executable_dir"
            exe_dir.mkdir()
            
            # Windows-style absolute path
            windows_path = "C:\\Users\\TestUser\\Documents\\journal.db"
            
            with patch.object(ExecutableDetector, 'get_executable_directory', return_value=exe_dir):
                db_manager = DatabaseManager(database_path=windows_path)
                resolved_path = db_manager._resolve_path_executable_safe(windows_path)
                
                # Should handle Windows paths correctly (treat as absolute and return unchanged)
                # On Unix systems, Windows paths should be returned as-is since they're treated as absolute
                assert resolved_path == windows_path


class TestTildeExpansion:
    """Test cases for tilde expansion in different environments."""

    def test_tilde_expansion_user_home(self):
        """Test tilde expansion to user home directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exe_dir = Path(temp_dir) / "executable_dir"
            exe_dir.mkdir()
            
            tilde_path = "~/Documents/journal.db"
            
            with patch.object(ExecutableDetector, 'get_executable_directory', return_value=exe_dir):
                db_manager = DatabaseManager(database_path=tilde_path)
                resolved_path = db_manager._resolve_path_executable_safe(tilde_path)
                
                # Should expand the tilde to an absolute path
                assert not resolved_path.startswith("~")
                assert "Documents" in resolved_path
                assert "journal.db" in resolved_path
                # Should be an absolute path
                assert Path(resolved_path).is_absolute()

    def test_tilde_expansion_with_different_users(self):
        """Test tilde expansion with specific user notation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exe_dir = Path(temp_dir) / "executable_dir"
            exe_dir.mkdir()
            
            user_path = "~testuser/shared/database.db"
            
            with patch.object(ExecutableDetector, 'get_executable_directory', return_value=exe_dir):
                db_manager = DatabaseManager(database_path=user_path)
                resolved_path = db_manager._resolve_path_executable_safe(user_path)
                
                # Should handle tilde expansion, but may fall back due to non-existent user
                assert not resolved_path.startswith("~")
                # Path should be absolute and may be a fallback path
                assert Path(resolved_path).is_absolute()
                # Should end with .db file
                assert resolved_path.endswith(".db")

    def test_tilde_expansion_in_development_vs_executable(self):
        """Test tilde expansion works consistently in development and executable environments."""
        tilde_path = "~/journal_data/database.db"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            exe_dir = Path(temp_dir) / "app_dir"
            exe_dir.mkdir()
            
            # Mock different executable environments
            environments = [
                (False, "development"),  # Development environment
                (True, "executable")     # Frozen executable environment
            ]
            
            for is_frozen, env_name in environments:
                with patch.object(ExecutableDetector, 'get_executable_directory', return_value=exe_dir):
                    with patch.object(ExecutableDetector, 'is_frozen_executable', return_value=is_frozen):
                        db_manager = DatabaseManager(database_path=tilde_path)
                        resolved_path = db_manager._resolve_path_executable_safe(tilde_path)
                        
                        # Should expand the tilde and be absolute
                        assert not resolved_path.startswith("~")
                        assert Path(resolved_path).is_absolute()
                        assert "database.db" in resolved_path


class TestDirectoryAutoCreation:
    """Test cases for directory auto-creation with permission fallback."""

    def test_directory_auto_creation_success(self):
        """Test successful directory creation for database path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exe_dir = Path(temp_dir) / "executable_dir"
            exe_dir.mkdir()
            
            # Path to non-existent directory
            db_path = str(Path(temp_dir) / "new_dir" / "subdirectory" / "database.db")
            
            with patch.object(ExecutableDetector, 'get_executable_directory', return_value=exe_dir):
                db_manager = DatabaseManager(database_path=db_path)
                resolved_path = db_manager._resolve_path_executable_safe(db_path)
                
                # Directory should be created automatically
                parent_dir = Path(resolved_path).parent
                assert parent_dir.exists()
                assert resolved_path == db_path

    def test_directory_creation_with_relative_path(self):
        """Test directory creation with relative paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exe_dir = Path(temp_dir) / "executable_dir"
            exe_dir.mkdir()
            
            # Relative path requiring directory creation
            relative_path = "data/nested/deep/database.db"
            
            with patch.object(ExecutableDetector, 'get_executable_directory', return_value=exe_dir):
                db_manager = DatabaseManager(database_path=relative_path)
                resolved_path = db_manager._resolve_path_executable_safe(relative_path)
                
                # Should resolve relative to executable and create directories
                expected_full_path = exe_dir / "data" / "nested" / "deep" / "database.db"
                assert resolved_path == str(expected_full_path)
                
                # Parent directory should be created
                assert expected_full_path.parent.exists()

    def test_directory_creation_permission_error_fallback(self):
        """Test fallback to user data directory on permission errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exe_dir = Path(temp_dir) / "executable_dir"
            exe_dir.mkdir()
            
            # Path that would cause permission error
            restricted_path = "/root/restricted/database.db"
            
            with patch.object(ExecutableDetector, 'get_executable_directory', return_value=exe_dir):
                # Mock permission error during directory creation
                with patch('pathlib.Path.mkdir', side_effect=PermissionError("Permission denied")):
                    db_manager = DatabaseManager(database_path=restricted_path)
                    
                    # Should have fallback mechanism
                    assert hasattr(db_manager, '_get_user_data_directory')
                    fallback_dir = db_manager._get_user_data_directory()
                    assert isinstance(fallback_dir, Path)


class TestUserDataDirectoryFallback:
    """Test cases for user data directory fallback logic."""

    def test_get_user_data_directory_method_exists(self):
        """Test that DatabaseManager has _get_user_data_directory method."""
        db_manager = DatabaseManager()
        
        assert hasattr(db_manager, '_get_user_data_directory')
        assert callable(getattr(db_manager, '_get_user_data_directory'))

    def test_user_data_directory_cross_platform(self):
        """Test user data directory detection across platforms."""
        db_manager = DatabaseManager()
        
        # Mock different platforms
        platforms = [
            ("darwin", "macOS"),
            ("linux", "Linux"), 
            ("win32", "Windows")
        ]
        
        for platform, platform_name in platforms:
            with patch('sys.platform', platform):
                user_data_dir = db_manager._get_user_data_directory()
                
                assert isinstance(user_data_dir, Path)
                # Should return a reasonable user data directory for each platform
                assert len(str(user_data_dir)) > 0

    def test_fallback_path_construction(self):
        """Test fallback path construction when primary path fails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exe_dir = Path(temp_dir) / "executable_dir"
            exe_dir.mkdir()
            
            # Original path that will fail
            failing_path = "/invalid/permission/denied/database.db"
            
            with patch.object(ExecutableDetector, 'get_executable_directory', return_value=exe_dir):
                db_manager = DatabaseManager(database_path=failing_path)
                
                # Mock permission error and test fallback
                with patch('pathlib.Path.mkdir', side_effect=PermissionError("Access denied")):
                    with patch.object(db_manager, '_get_user_data_directory') as mock_user_data:
                        user_data_path = Path(temp_dir) / "user_data"
                        mock_user_data.return_value = user_data_path
                        
                        # Should construct fallback path
                        fallback_path = db_manager._resolve_path_executable_safe(failing_path)
                        
                        # Fallback should be in user data directory
                        expected_fallback = user_data_path / "WorkJournalMaker" / "database.db"
                        # The exact fallback logic will be tested when implemented


class TestPermissionErrorHandling:
    """Test cases for graceful permission error handling."""

    def test_permission_error_on_directory_creation(self):
        """Test graceful handling of permission errors during directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exe_dir = Path(temp_dir) / "executable_dir"
            exe_dir.mkdir()
            
            restricted_path = "/root/system/database.db"
            
            with patch.object(ExecutableDetector, 'get_executable_directory', return_value=exe_dir):
                # Mock permission error
                with patch('pathlib.Path.mkdir', side_effect=PermissionError("Permission denied")):
                    db_manager = DatabaseManager(database_path=restricted_path)
                    
                    # Should not raise exception, should handle gracefully
                    resolved_path = db_manager._resolve_path_executable_safe(restricted_path)
                    
                    # Should return a fallback path, not the original restricted path
                    assert resolved_path != restricted_path
                    assert isinstance(resolved_path, str)

    def test_permission_error_with_detailed_logging(self):
        """Test that permission errors are logged with detailed information."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exe_dir = Path(temp_dir) / "executable_dir"
            exe_dir.mkdir()
            
            problematic_path = "/system/protected/database.db"
            
            with patch.object(ExecutableDetector, 'get_executable_directory', return_value=exe_dir):
                with patch('pathlib.Path.mkdir', side_effect=PermissionError("Access denied")):
                    # Should log the permission error appropriately
                    db_manager = DatabaseManager(database_path=problematic_path)
                    
                    # The actual logging will be tested when implemented
                    # For now, just ensure it doesn't crash
                    try:
                        resolved_path = db_manager._resolve_path_executable_safe(problematic_path)
                        # Should complete without raising exception
                        assert True
                    except PermissionError:
                        # Should not propagate permission errors
                        assert False, "Permission error should be handled gracefully"

    def test_readonly_filesystem_fallback(self):
        """Test fallback behavior on read-only filesystem."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exe_dir = Path(temp_dir) / "readonly_location"
            exe_dir.mkdir()
            
            # Simulate read-only filesystem error
            readonly_path = str(exe_dir / "database.db")
            
            with patch.object(ExecutableDetector, 'get_executable_directory', return_value=exe_dir):
                with patch('pathlib.Path.mkdir', side_effect=OSError("Read-only file system")):
                    db_manager = DatabaseManager(database_path=readonly_path)
                    
                    # Should fallback to writable location
                    resolved_path = db_manager._resolve_path_executable_safe(readonly_path)
                    
                    # Should provide alternative path, not the original
                    assert resolved_path != readonly_path


class TestCrossPlatformPathResolution:
    """Test cases for cross-platform path resolution compatibility."""

    def test_windows_path_separators(self):
        """Test Windows path separator handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exe_dir = Path(temp_dir) / "executable_dir"
            exe_dir.mkdir()
            
            # Windows-style relative path
            windows_relative = "data\\subdirectory\\database.db"
            
            with patch.object(ExecutableDetector, 'get_executable_directory', return_value=exe_dir):
                db_manager = DatabaseManager(database_path=windows_relative)
                resolved_path = db_manager._resolve_path_executable_safe(windows_relative)
                
                # Should handle Windows separators correctly
                assert "database.db" in resolved_path
                # Path should be resolved relative to executable directory
                assert str(exe_dir) in resolved_path or resolved_path.startswith(str(exe_dir))

    def test_unix_path_separators(self):
        """Test Unix/Linux path separator handling."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exe_dir = Path(temp_dir) / "executable_dir"
            exe_dir.mkdir()
            
            # Unix-style relative path
            unix_relative = "data/subdirectory/database.db"
            
            with patch.object(ExecutableDetector, 'get_executable_directory', return_value=exe_dir):
                db_manager = DatabaseManager(database_path=unix_relative)
                resolved_path = db_manager._resolve_path_executable_safe(unix_relative)
                
                # Should handle Unix separators correctly
                expected_full = exe_dir / "data" / "subdirectory" / "database.db"
                assert resolved_path == str(expected_full)

    def test_mixed_path_separators_normalization(self):
        """Test normalization of mixed path separators."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exe_dir = Path(temp_dir) / "executable_dir"
            exe_dir.mkdir()
            
            # Mixed separators (should be normalized)
            mixed_path = "data/subdirectory\\mixed\\database.db"
            
            with patch.object(ExecutableDetector, 'get_executable_directory', return_value=exe_dir):
                db_manager = DatabaseManager(database_path=mixed_path)
                resolved_path = db_manager._resolve_path_executable_safe(mixed_path)
                
                # Should normalize separators
                assert "database.db" in resolved_path
                # Should use platform-appropriate separators
                resolved_path_obj = Path(resolved_path)
                assert resolved_path_obj.is_absolute() or str(exe_dir) in str(resolved_path_obj.resolve())


class TestPathResolutionEdgeCases:
    """Test cases for edge cases in path resolution."""

    def test_empty_database_path_handling(self):
        """Test handling of empty or None database_path."""
        # Empty string
        db_manager = DatabaseManager(database_path="")
        resolved_path = db_manager._resolve_path_executable_safe("")
        assert resolved_path != ""  # Should provide fallback
        
        # None value should use default behavior
        db_manager_none = DatabaseManager(database_path=None)
        assert db_manager_none.database_path is not None

    def test_very_long_path_handling(self):
        """Test handling of very long file paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exe_dir = Path(temp_dir) / "executable_dir"
            exe_dir.mkdir()
            
            # Create a very long relative path
            long_components = ["very"] * 20 + ["long"] * 20 + ["path"] * 10
            long_path = os.path.join(*long_components, "database.db")
            
            with patch.object(ExecutableDetector, 'get_executable_directory', return_value=exe_dir):
                db_manager = DatabaseManager(database_path=long_path)
                
                # Should handle long paths without error
                try:
                    resolved_path = db_manager._resolve_path_executable_safe(long_path)
                    assert isinstance(resolved_path, str)
                    assert len(resolved_path) > 0
                except OSError as e:
                    # On some platforms, very long paths might hit OS limits
                    # This is expected behavior
                    assert "too long" in str(e).lower() or "name too long" in str(e).lower()

    def test_special_characters_in_path(self):
        """Test handling of special characters in paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exe_dir = Path(temp_dir) / "executable_dir"
            exe_dir.mkdir()
            
            # Paths with special characters (that are valid on the filesystem)
            special_paths = [
                "data with spaces/database.db",
                "data-with-dashes/database.db",
                "data_with_underscores/database.db",
                "data.with.dots/database.db"
            ]
            
            for special_path in special_paths:
                with patch.object(ExecutableDetector, 'get_executable_directory', return_value=exe_dir):
                    db_manager = DatabaseManager(database_path=special_path)
                    resolved_path = db_manager._resolve_path_executable_safe(special_path)
                    
                    # Should handle special characters correctly
                    assert "database.db" in resolved_path
                    # Should be resolved relative to executable directory
                    expected_full = exe_dir / special_path
                    assert resolved_path == str(expected_full)

    def test_symlink_resolution_handling(self):
        """Test handling of symbolic links in paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exe_dir = Path(temp_dir) / "executable_dir"
            exe_dir.mkdir()
            
            # Create a target directory and symlink (if supported)
            target_dir = Path(temp_dir) / "target"
            target_dir.mkdir()
            symlink_path = Path(temp_dir) / "symlink_to_target"
            
            try:
                symlink_path.symlink_to(target_dir)
                
                # Path using symlink
                symlink_db_path = str(symlink_path / "database.db")
                
                with patch.object(ExecutableDetector, 'get_executable_directory', return_value=exe_dir):
                    db_manager = DatabaseManager(database_path=symlink_db_path)
                    resolved_path = db_manager._resolve_path_executable_safe(symlink_db_path)
                    
                    # Should handle symlinks appropriately
                    assert "database.db" in resolved_path
                    
            except (OSError, NotImplementedError):
                # Symlinks not supported on this platform/filesystem
                pytest.skip("Symlinks not supported on this platform")


class TestIntegrationWithExistingDatabaseManager:
    """Test cases for integration with existing DatabaseManager functionality."""

    def test_integration_with_existing_constructor(self):
        """Test that new database_path parameter integrates with existing constructor logic."""
        # Should work with no parameters (existing behavior)
        db_manager_default = DatabaseManager()
        assert hasattr(db_manager_default, 'database_path')
        assert db_manager_default.database_path is not None
        
        # Should work with explicit database_path
        custom_path = "custom/database/path.db"
        db_manager_custom = DatabaseManager(database_path=custom_path)
        # Path will be resolved relative to executable directory
        assert "custom" in db_manager_custom.database_path
        assert "database" in db_manager_custom.database_path
        assert db_manager_custom.database_path.endswith("path.db")

    def test_integration_with_existing_initialize_method(self):
        """Test that path resolution integrates with existing initialize method."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_db_path = str(Path(temp_dir) / "test_journal.db")
            
            db_manager = DatabaseManager(database_path=custom_db_path)
            
            # Should be able to initialize with custom path
            # Note: This is an async method, so we'll test the setup
            assert db_manager.database_path == custom_db_path
            
            # Directory should exist or be created
            db_path_obj = Path(custom_db_path)
            assert db_path_obj.parent.exists() or not db_path_obj.is_absolute()

    def test_backward_compatibility_with_existing_usage(self):
        """Test backward compatibility with existing DatabaseManager usage patterns."""
        # Existing usage pattern should continue to work
        db_manager = DatabaseManager()
        
        # Should have all existing attributes and methods
        assert hasattr(db_manager, 'database_path')
        assert hasattr(db_manager, '_get_default_database_path')
        
        # Should initialize without error
        assert isinstance(db_manager.database_path, str)
        assert len(db_manager.database_path) > 0


if __name__ == '__main__':
    # Run the tests
    pytest.main([__file__, '-v'])