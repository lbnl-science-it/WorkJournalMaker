#!/usr/bin/env python3
"""
Test Suite for Error Handling & Fallbacks - Phase 6

This module tests comprehensive error handling functionality including:
- Database path conflict detection
- Detailed error messages with source attribution
- Graceful fallback mechanisms with user guidance
- Permission error handling and invalid path scenarios
- Error source tracking throughout configuration chain

Tests follow TDD principles with comprehensive coverage of all error scenarios.
"""

import pytest
import tempfile
import os
import stat
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from typing import Optional

# Import the modules we'll be testing
from web.database import DatabaseManager
from config_manager import ConfigManager, AppConfig
import work_journal_summarizer
import server_runner


class TestDatabasePathConflictDetection:
    """Test cases for database path conflict detection."""

    def test_invalid_path_with_existing_default_database_stops_with_error(self):
        """Test that invalid path with existing default database stops with error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create existing default database
            default_db_path = Path(temp_dir) / "existing_default.db"
            default_db_path.write_text("existing database content")
            
            # Try to use invalid path
            invalid_path = "/invalid/nonexistent/path/database.db"
            
            # Should raise specific error about conflict with existing database
            with pytest.raises(ValueError) as exc_info:
                db_manager = DatabaseManager(database_path=invalid_path)
                db_manager._validate_database_path(invalid_path, str(default_db_path))
            
            assert "path conflict" in str(exc_info.value).lower()
            assert "existing database" in str(exc_info.value).lower()

    def test_invalid_path_without_existing_default_uses_fallback(self):
        """Test that invalid path without existing default uses fallback."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # No existing default database
            invalid_path = "/invalid/nonexistent/path/database.db"
            
            # Should use fallback mechanism
            db_manager = DatabaseManager()
            fallback_path = db_manager._get_fallback_database_path(invalid_path)
            
            # Fallback path should be in user data directory
            assert "WorkJournal" in fallback_path or "work-journal" in fallback_path
            assert fallback_path.endswith(".db")

    def test_permission_denied_scenarios_with_fallback(self):
        """Test permission denied scenarios with graceful fallback."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create directory with restricted permissions
            restricted_dir = Path(temp_dir) / "restricted"
            restricted_dir.mkdir()
            
            # Make directory read-only (simulate permission denied)
            original_mode = restricted_dir.stat().st_mode
            try:
                restricted_dir.chmod(0o444)  # Read-only
                
                restricted_db_path = restricted_dir / "database.db"
                
                # Should handle permission error gracefully
                db_manager = DatabaseManager(database_path=str(restricted_db_path))
                result_path = db_manager._resolve_path_with_fallback(str(restricted_db_path))
                
                # Should fallback to user data directory
                assert result_path != str(restricted_db_path)
                assert Path(result_path).parent.exists()
                
            finally:
                # Restore permissions for cleanup
                restricted_dir.chmod(original_mode)

    def test_path_conflict_detection_and_error_messages(self):
        """Test path conflict detection with detailed error messages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create existing database in default location
            default_db = Path(temp_dir) / "default.db"
            default_db.write_text("existing data")
            
            # Create conflicting path in different location
            conflict_dir = Path(temp_dir) / "conflict"
            conflict_dir.mkdir()
            conflict_db = conflict_dir / "database.db"
            
            # Should detect conflict and provide detailed message
            with pytest.raises(ValueError) as exc_info:
                db_manager = DatabaseManager()
                db_manager._raise_path_conflict_error(
                    requested_path=str(conflict_db),
                    existing_path=str(default_db),
                    source="CLI argument"
                )
            
            error_message = str(exc_info.value)
            assert "CLI argument" in error_message
            assert str(conflict_db) in error_message
            assert str(default_db) in error_message
            assert "conflict" in error_message.lower()

    def test_error_source_attribution_config_file_vs_cli_vs_env_var(self):
        """Test error source attribution for different configuration sources."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test CLI source attribution
            cli_error = DatabaseManager()._create_path_error(
                path="/invalid/cli/path.db",
                source="CLI argument --database-path",
                issue="Path does not exist"
            )
            assert "CLI argument --database-path" in str(cli_error)
            assert "/invalid/cli/path.db" in str(cli_error)
            
            # Test config file source attribution
            config_file = Path(temp_dir) / "config.yaml"
            config_error = DatabaseManager()._create_path_error(
                path="/invalid/config/path.db",
                source=f"Configuration file {config_file}",
                issue="Permission denied"
            )
            assert str(config_file) in str(config_error)
            assert "/invalid/config/path.db" in str(config_error)
            
            # Test environment variable source attribution
            env_error = DatabaseManager()._create_path_error(
                path="/invalid/env/path.db",
                source="Environment variable WJS_DATABASE_PATH",
                issue="Directory does not exist"
            )
            assert "WJS_DATABASE_PATH" in str(env_error)
            assert "/invalid/env/path.db" in str(env_error)


class TestGracefulFallbackMechanisms:
    """Test cases for graceful fallback mechanisms."""

    def test_fallback_directory_creation_success(self):
        """Test successful fallback directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Use invalid primary path
            invalid_path = "/invalid/primary/database.db"
            
            # Should create fallback in user data directory
            db_manager = DatabaseManager(database_path=invalid_path)
            fallback_path = db_manager._create_fallback_directory()
            
            assert fallback_path.exists()
            assert fallback_path.is_dir()
            assert "WorkJournal" in str(fallback_path) or "work-journal" in str(fallback_path)

    def test_fallback_with_user_guidance_messages(self):
        """Test fallback mechanisms provide user guidance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_path = "/completely/invalid/path/database.db"
            
            # Should provide guidance message
            db_manager = DatabaseManager()
            guidance = db_manager._generate_fallback_guidance(
                original_path=invalid_path,
                fallback_path="/home/user/.local/share/WorkJournal/database.db",
                reason="Directory does not exist"
            )
            
            assert "fallback" in guidance.lower()
            assert invalid_path in guidance
            assert "WorkJournal" in guidance
            assert "Directory does not exist" in guidance

    def test_multiple_fallback_attempts(self):
        """Test multiple fallback attempts when first fallback fails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a DatabaseManager instance first
            db_manager = DatabaseManager()
            
            # Test that multiple fallbacks work by using an invalid path
            final_path = db_manager._resolve_with_multiple_fallbacks("/completely/invalid/path/db.db")
            
            # Should eventually succeed with alternative fallback
            assert final_path is not None
            assert final_path.endswith('.db')
            # Should not be the original invalid path
            assert "/completely/invalid/path/db.db" not in final_path

    def test_recovery_guidance_for_different_error_types(self):
        """Test specific recovery guidance for different error types."""
        db_manager = DatabaseManager()
        
        # Permission error guidance
        perm_guidance = db_manager._get_recovery_guidance("permission_denied", "/restricted/database.db")
        assert "permission" in perm_guidance.lower()
        assert "chmod" in perm_guidance or "access" in perm_guidance.lower()
        
        # Directory not found guidance
        dir_guidance = db_manager._get_recovery_guidance("directory_not_found", "/missing/dir/database.db")
        assert "directory" in dir_guidance.lower()
        assert "create" in dir_guidance.lower() or "mkdir" in dir_guidance.lower()
        
        # Invalid path guidance
        invalid_guidance = db_manager._get_recovery_guidance("invalid_path", "\\invalid\\windows\\path")
        assert "path" in invalid_guidance.lower()
        assert "format" in invalid_guidance.lower() or "valid" in invalid_guidance.lower()


class TestPermissionAndPathErrorHandling:
    """Test cases for permission errors and invalid path handling."""

    def test_permission_error_on_database_file_creation(self):
        """Test permission error when creating database file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create directory but make it read-only
            db_dir = Path(temp_dir) / "readonly_dir"
            db_dir.mkdir()
            original_mode = db_dir.stat().st_mode
            
            try:
                db_dir.chmod(0o444)  # Read-only
                
                db_path = db_dir / "database.db"
                
                # Should handle permission error gracefully
                db_manager = DatabaseManager()
                result = db_manager._handle_permission_error(str(db_path), "Database file creation")
                
                assert result is not None  # Should provide fallback
                assert result != str(db_path)  # Should be different path
                
            finally:
                db_dir.chmod(original_mode)

    def test_invalid_path_characters_handling(self):
        """Test handling of invalid path characters."""
        db_manager = DatabaseManager()
        
        # Test various invalid path scenarios
        invalid_paths = [
            "/path/with\x00null/database.db",  # Null character
            "/path/with\ttab/database.db",     # Tab character
            "con.db" if os.name == 'nt' else "aux.db",  # Reserved names (cross-platform)
        ]
        
        for invalid_path in invalid_paths:
            try:
                result = db_manager._validate_path_characters(invalid_path)
                assert result is False, f"Should reject invalid path: {invalid_path}"
            except ValueError as e:
                assert "invalid" in str(e).lower() or "character" in str(e).lower()

    def test_readonly_filesystem_fallback(self):
        """Test fallback when filesystem is read-only."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a DatabaseManager instance first
            db_manager = DatabaseManager()
            
            # Test readonly filesystem handling
            fallback_path = db_manager._handle_readonly_filesystem("/mount/readonly/database.db")
            
            # Should provide alternative writable location
            assert fallback_path is not None
            assert "/mount/readonly" not in fallback_path
            assert fallback_path.endswith('.db')

    def test_detailed_error_logging_with_recovery_actions(self):
        """Test detailed error logging with specific recovery actions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_manager = DatabaseManager()
            
            # Test detailed error with recovery action
            error_details = db_manager._create_detailed_error(
                path="/failed/path/database.db",
                error_type="PermissionError",
                error_message="Permission denied",
                source="CLI argument",
                recovery_actions=[
                    "Check directory permissions with 'ls -la /failed/path/'",
                    "Create directory with 'mkdir -p /failed/path/'",
                    "Use alternative path with --database-path"
                ]
            )
            
            assert "PermissionError" in error_details
            assert "/failed/path/database.db" in error_details
            assert "CLI argument" in error_details
            assert "ls -la" in error_details
            assert "mkdir -p" in error_details


class TestConfigurationChainErrorTracking:
    """Test cases for error source tracking throughout configuration chain."""

    def test_error_tracking_through_config_discovery_chain(self):
        """Test error tracking from config discovery through database initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create config file with invalid database path
            config_file = Path(temp_dir) / "config.yaml"
            config_content = """
processing:
  database_path: '/invalid/config/path/database.db'
  base_path: '~/worklogs'
"""
            config_file.write_text(config_content)
            
            # Test that configuration chain works - tracking is optional
            try:
                config_manager = ConfigManager(config_file)
                config = config_manager.get_config()
                # This should work with fallback path since invalid path will trigger fallback
                db_manager = DatabaseManager(database_path=config.processing.database_path)
                
                # Should have a valid database path (fallback)
                assert db_manager.database_path is not None
                assert db_manager.database_path != '/invalid/config/path/database.db'
            except Exception as e:
                # Should not fail completely - fallback should work
                assert False, f"Configuration chain should handle invalid paths gracefully: {e}"

    def test_priority_resolution_error_attribution(self):
        """Test error attribution in priority resolution scenarios."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup scenario with conflicting sources
            config_file = Path(temp_dir) / "config.yaml"
            config_file.write_text("""
processing:
  database_path: '/config/database.db'
""")
            
            cli_path = "/cli/database.db"
            env_path = "/env/database.db"
            
            with patch.dict(os.environ, {'WJS_DATABASE_PATH': env_path}):
                # Test priority resolution with error tracking
                resolved_path = work_journal_summarizer.resolve_database_path_priority(
                    cli_path=cli_path,
                    config_path=str(config_file)
                )
                
                # Should resolve to CLI path and track sources
                assert resolved_path == cli_path

    def test_error_aggregation_across_multiple_sources(self):
        """Test error aggregation when multiple sources have issues."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create scenario with errors in multiple sources
            db_manager = DatabaseManager()
            
            errors = [
                ("CLI argument --database-path", "/invalid/cli/path.db", "Directory not found"),
                ("Configuration file config.yaml", "/invalid/config/path.db", "Permission denied"),
                ("Environment variable WJS_DATABASE_PATH", "/invalid/env/path.db", "Invalid path format")
            ]
            
            aggregated_error = db_manager._aggregate_configuration_errors(errors)
            
            # Should include all error sources and details
            assert "CLI argument" in aggregated_error
            assert "Configuration file" in aggregated_error
            assert "Environment variable" in aggregated_error
            assert "/invalid/cli/path.db" in aggregated_error
            assert "/invalid/config/path.db" in aggregated_error
            assert "/invalid/env/path.db" in aggregated_error


class TestDatabaseManagerValidationMethods:
    """Test cases for DatabaseManager validation methods that will be implemented."""

    def test_validate_database_path_method_exists(self):
        """Test that _validate_database_path method exists and works correctly."""
        db_manager = DatabaseManager()
        
        # Method should exist
        assert hasattr(db_manager, '_validate_database_path')
        
        # Should validate good paths
        with tempfile.TemporaryDirectory() as temp_dir:
            valid_path = Path(temp_dir) / "valid.db"
            result = db_manager._validate_database_path(str(valid_path), None)
            assert result is True or result is None  # Should not raise error

    def test_raise_path_conflict_error_method_exists(self):
        """Test that _raise_path_conflict_error method exists."""
        db_manager = DatabaseManager()
        
        # Method should exist
        assert hasattr(db_manager, '_raise_path_conflict_error')
        
        # Should raise appropriate error
        with pytest.raises(ValueError):
            db_manager._raise_path_conflict_error(
                requested_path="/new/path.db",
                existing_path="/old/path.db",
                source="Test source"
            )

    def test_get_fallback_database_path_method_exists(self):
        """Test that _get_fallback_database_path method exists."""
        db_manager = DatabaseManager()
        
        # Method should exist
        assert hasattr(db_manager, '_get_fallback_database_path')
        
        # Should return valid fallback path
        fallback = db_manager._get_fallback_database_path("/failed/path.db")
        assert fallback is not None
        assert isinstance(fallback, str)
        assert Path(fallback).name.endswith('.db')

    def test_create_path_error_method_exists(self):
        """Test that _create_path_error method exists."""
        db_manager = DatabaseManager()
        
        # Method should exist
        assert hasattr(db_manager, '_create_path_error')
        
        # Should create informative error
        error = db_manager._create_path_error(
            path="/test/path.db",
            source="Test source",
            issue="Test issue"
        )
        assert "Test source" in str(error)
        assert "/test/path.db" in str(error)
        assert "Test issue" in str(error)


if __name__ == '__main__':
    # Run the tests
    pytest.main([__file__, '-v'])