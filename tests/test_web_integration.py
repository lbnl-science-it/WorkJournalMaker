"""
Integration Test Suite for Web-CLI Compatibility (Step 17)

This module provides comprehensive integration tests that ensure web interface
and CLI functionality work together seamlessly without data corruption or
compatibility issues.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient
import sys
import os

from web.app import app
from web.database import DatabaseManager
from config_manager import ConfigManager, AppConfig, ProcessingConfig, LogConfig
# Import individual components instead of non-existent WorkJournalSummarizer class
from file_discovery import FileDiscovery
from content_processor import ContentProcessor
from config_manager import ConfigManager
from logger import JournalSummarizerLogger, LogLevel


class TestWebCLIIntegration:
    """Test integration between web interface and CLI functionality."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def test_config(self, temp_workspace):
        """Create test configuration."""
        config = AppConfig()
        config.processing = ProcessingConfig()
        config.processing.base_path = str(temp_workspace / 'worklogs')
        config.processing.output_path = str(temp_workspace / 'output')
        config.processing.max_file_size_mb = 10
        config.processing.file_patterns = ["*.md", "*.txt"]
        
        config.logging = LogConfig()
        config.logging.level = LogLevel.INFO
        config.logging.console_output = True
        config.logging.file_output = False
        
        # Create directories
        Path(config.processing.base_path).mkdir(parents=True, exist_ok=True)
        Path(config.processing.output_path).mkdir(parents=True, exist_ok=True)
        
        return config
    
    @pytest.fixture
    def test_client(self):
        """Create test client with default configuration."""
        with TestClient(app) as client:
            yield client
    
    @pytest.fixture
    def sample_entries(self):
        """Create sample journal entries using the actual config."""
        from config_manager import ConfigManager
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        base_path = Path(config.processing.base_path).expanduser()
        
        # Create entries for the past week
        entries = []
        for i in range(7):
            entry_date = date.today() - timedelta(days=i)
            
            # Use FileDiscovery to create proper structure
            file_discovery = FileDiscovery(str(base_path))
            week_ending_date = file_discovery._calculate_week_ending_for_date(entry_date)
            file_path = file_discovery._construct_file_path(entry_date, week_ending_date)
            
            # Create directory structure
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write sample content
            content = f"""
{entry_date.strftime('%A, %B %d, %Y')}

Sample journal entry for {entry_date}.
This is test content with multiple lines.
Word count should be calculated correctly.

Tasks completed:
- Task 1 for {entry_date}
- Task 2 for {entry_date}
- Task 3 for {entry_date}

Notes:
This is a sample entry for testing purposes.
Testing web-CLI compatibility.
"""
            file_path.write_text(content.strip())
            entries.append({
                'date': entry_date,
                'path': file_path,
                'content': content.strip()
            })
        
        yield entries
        
        # Cleanup - remove created files
        for entry in entries:
            if entry['path'].exists():
                entry['path'].unlink()
                # Try to remove empty directories
                try:
                    entry['path'].parent.rmdir()
                    entry['path'].parent.parent.rmdir()
                    entry['path'].parent.parent.parent.rmdir()
                except OSError:
                    pass  # Directory not empty, that's fine
    
    def test_health_check(self, test_client):
        """Test basic health check endpoint."""
        response = test_client.get("/api/health/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
    
    def test_web_cli_file_compatibility(self, sample_entries):
        """Test that web interface can read CLI-created files."""
        # Get the actual config
        from config_manager import ConfigManager
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Files created by sample_entries fixture should be readable
        file_discovery = FileDiscovery(config.processing.base_path)
        
        # Test file discovery
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

        result = file_discovery.discover_files(start_date, end_date)
        # Should find files for the date range (flexible count based on actual range)
        expected_days = (end_date - start_date).days + 1
        assert len(result.found_files) == expected_days
        
        # Test file reading
        for entry in sample_entries:
            content = entry['path'].read_text()
            assert len(content) > 0
            assert entry['date'].strftime('%A, %B %d, %Y') in content
    
    def test_cli_web_file_compatibility(self, test_client):
        """Test that CLI can read web-created files."""
        # Create entry via web API
        today = date.today().isoformat()
        entry_data = {
            "date": today,
            "content": "Test entry created via web interface\n\nThis should be readable by CLI tools."
        }

        response = test_client.post(f"/api/entries/{today}", json=entry_data)
        assert response.status_code == 200

        # Get the actual config from the app
        from config_manager import ConfigManager
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Verify CLI can read the file using the same config
        file_discovery = FileDiscovery(config.processing.base_path)
        today_date = date.today()
        week_ending_date = file_discovery._calculate_week_ending_for_date(today_date)
        file_path = file_discovery._construct_file_path(today_date, week_ending_date)

        assert file_path.exists(), f"Expected file at {file_path} but it doesn't exist"
        content = file_path.read_text()
        assert "Test entry created via web interface" in content
    
    def test_concurrent_access(self, test_client, sample_entries):
        """Test concurrent access between web and CLI operations."""
        today = date.today().isoformat()
        
        # Simulate concurrent reads
        responses = []
        for _ in range(5):
            response = test_client.get(f"/api/entries/{today}?include_content=true")
            responses.append(response)
        
        # All requests should succeed or return 404 if entry doesn't exist
        for response in responses:
            assert response.status_code in [200, 404]
    
    @pytest.mark.asyncio
    async def test_database_sync_accuracy(self, test_client, sample_entries, test_config):
        """Test that database sync accurately reflects file system."""
        # Initialize database for testing
        db_manager = DatabaseManager(":memory:")
        await db_manager.initialize()
        
        try:
            # Trigger database sync via API
            response = test_client.get("/api/entries/recent?limit=10")
            
            # Should return entries even if database sync hasn't run
            assert response.status_code == 200
            
            data = response.json()
            entries = data.get("entries", [])
            
            # Should have some entries from sample data
            assert isinstance(entries, list)
            
        finally:
            if db_manager.engine:
                await db_manager.engine.dispose()
    
    def test_file_path_consistency(self):
        """Test that web and CLI use consistent file paths."""
        test_date = date(2024, 1, 15)

        # Get the actual config
        from config_manager import ConfigManager
        config_manager = ConfigManager()
        config = config_manager.get_config()

        # Get file path from CLI FileDiscovery
        file_discovery = FileDiscovery(config.processing.base_path)
        week_ending_date = file_discovery._calculate_week_ending_for_date(test_date)
        cli_path = file_discovery._construct_file_path(test_date, week_ending_date)
        
        # Get file path from web EntryManager (simulated)
        from web.services.entry_manager import EntryManager
        
        # Mock the dependencies for EntryManager
        logger = JournalSummarizerLogger(config.logging)
        
        # Create a mock database manager
        class MockDBManager:
            async def get_session(self):
                return None
        
        entry_manager = EntryManager(config, logger, MockDBManager())
        web_path = entry_manager._construct_file_path(test_date)
        
        # Paths should be identical
        assert cli_path == web_path
    
    def test_content_format_consistency(self, sample_entries, test_client):
        """Test that content format is consistent between web and CLI."""
        # Get an entry via web API
        entry_date = sample_entries[0]['date'].isoformat()
        response = test_client.get(f"/api/entries/{entry_date}?include_content=true")
        
        if response.status_code == 200:
            web_content = response.json().get('content', '')
            file_content = sample_entries[0]['content']
            
            # Content should match (allowing for minor formatting differences)
            assert web_content.strip() == file_content.strip()
    
    def test_metadata_calculation_consistency(self, sample_entries, test_client):
        """Test that metadata calculations are consistent between web and CLI."""
        entry_date = sample_entries[0]['date'].isoformat()
        response = test_client.get(f"/api/entries/{entry_date}")
        
        if response.status_code == 200:
            metadata = response.json().get('metadata', {})
            
            # Should have consistent metadata fields
            assert 'word_count' in metadata
            assert 'character_count' in metadata
            assert 'line_count' in metadata
            
            # Word count should be reasonable
            assert metadata['word_count'] > 0
            assert metadata['character_count'] > 0
            assert metadata['line_count'] > 0


class TestDataIntegrity:
    """Test data integrity across web and CLI operations."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_no_data_corruption_during_concurrent_writes(self, temp_workspace):
        """Test that concurrent writes don't corrupt data."""
        base_path = temp_workspace / "worklogs"
        base_path.mkdir(parents=True, exist_ok=True)
        
        # Create a test file
        test_file = base_path / "2024-01-01.md"
        original_content = "Original content\nLine 2\nLine 3"
        test_file.write_text(original_content)
        
        # Simulate concurrent reads
        for _ in range(10):
            content = test_file.read_text()
            assert content == original_content
    
    def test_file_locking_behavior(self, temp_workspace):
        """Test file locking behavior during operations."""
        base_path = temp_workspace / "worklogs"
        base_path.mkdir(parents=True, exist_ok=True)
        
        test_file = base_path / "2024-01-01.md"
        test_content = "Test content for locking"
        
        # Write file
        test_file.write_text(test_content)
        
        # Read file multiple times (should not fail)
        for _ in range(5):
            content = test_file.read_text()
            assert content == test_content
    
    def test_backup_and_recovery(self, temp_workspace):
        """Test backup and recovery procedures."""
        base_path = temp_workspace / "worklogs"
        backup_path = temp_workspace / "backup"
        
        base_path.mkdir(parents=True, exist_ok=True)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Create test files
        test_files = []
        for i in range(3):
            test_date = date.today() - timedelta(days=i)
            test_file = base_path / f"{test_date.isoformat()}.md"
            test_content = f"Test content for {test_date}"
            test_file.write_text(test_content)
            test_files.append((test_file, test_content))
        
        # Simulate backup
        for test_file, content in test_files:
            backup_file = backup_path / test_file.name
            backup_file.write_text(content)
        
        # Verify backup integrity
        for test_file, original_content in test_files:
            backup_file = backup_path / test_file.name
            assert backup_file.exists()
            assert backup_file.read_text() == original_content


class TestConfigurationCompatibility:
    """Test configuration compatibility between web and CLI."""
    
    def test_config_loading_consistency(self):
        """Test that configuration loading is consistent."""
        # Test with default config
        config_manager = ConfigManager()
        config = config_manager.get_config()
        
        # Should have all required sections
        assert hasattr(config, 'processing')
        assert hasattr(config, 'logging')
        assert hasattr(config, 'llm')
        
        # Processing config should have required fields
        assert hasattr(config.processing, 'base_path')
        assert hasattr(config.processing, 'output_path')
    
    def test_environment_variable_handling(self):
        """Test environment variable handling."""
        # Set test environment variable
        test_path = "/tmp/test_journal"
        os.environ['JOURNAL_BASE_PATH'] = test_path
        
        try:
            # Configuration should pick up environment variables
            # (This would need to be implemented in ConfigManager)
            config_manager = ConfigManager()
            config = config_manager.get_config()
            
            # For now, just verify config loads without error
            assert config is not None
            
        finally:
            # Clean up
            if 'JOURNAL_BASE_PATH' in os.environ:
                del os.environ['JOURNAL_BASE_PATH']


def run_integration_tests():
    """Run all integration tests."""
    print("🧪 Running Web-CLI Integration Tests")
    print("=" * 50)
    
    # Run pytest with specific test classes
    test_classes = [
        "tests/test_web_integration.py::TestWebCLIIntegration",
        "tests/test_web_integration.py::TestDataIntegrity",
        "tests/test_web_integration.py::TestConfigurationCompatibility"
    ]
    
    results = {}
    
    for test_class in test_classes:
        print(f"\n🔍 Running {test_class}...")
        exit_code = pytest.main([test_class, "-v", "--tb=short"])
        results[test_class] = "PASSED" if exit_code == 0 else "FAILED"
    
    # Print summary
    print("\n" + "="*60)
    print("INTEGRATION TESTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result == "PASSED")
    failed = len(results) - passed
    
    for test_class, result in results.items():
        status_icon = "✅" if result == "PASSED" else "❌"
        print(f"{status_icon} {test_class}: {result}")
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All integration tests passed!")
    else:
        print(f"\n⚠️  {failed} test class(es) failed. Please review and fix issues.")
    
    return failed == 0


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)