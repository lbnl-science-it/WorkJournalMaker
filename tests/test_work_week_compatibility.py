"""
Backward compatibility tests for work week functionality.

This module contains comprehensive compatibility tests to ensure the work week functionality
maintains backward compatibility with existing installations and data.
"""

import asyncio
import pytest
import pytest_asyncio
import tempfile
import shutil
import os
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
from web.services.work_week_service import WorkWeekService, WorkWeekConfig, WorkWeekPreset
from web.services.entry_manager import EntryManager
from web.services.settings_service import SettingsService
from web.database import DatabaseManager, JournalEntryIndex
from web.utils.timezone_utils import get_timezone_manager
from file_discovery import FileDiscovery
from config_manager import AppConfig
from logger import JournalSummarizerLogger


class TestWorkWeekBackwardCompatibility:
    """Test class for work week backward compatibility validation."""
    
    @pytest_asyncio.fixture
    async def legacy_setup(self):
        """Set up a legacy-style directory structure for testing."""
        temp_dir = tempfile.mkdtemp()
        
        # Create legacy daily directories (pre-work-week implementation)
        legacy_entries = []
        base_date = date(2024, 1, 1)
        
        for i in range(30):  # 30 days of legacy entries
            entry_date = base_date + timedelta(days=i)
            # Legacy implementation: each day gets its own directory
            daily_dir = os.path.join(temp_dir, f"week_ending_{entry_date.strftime('%Y-%m-%d')}")
            os.makedirs(daily_dir, exist_ok=True)
            
            # Create entry file
            entry_file = os.path.join(daily_dir, f"{entry_date.strftime('%Y-%m-%d')}.md")
            entry_content = f"Legacy entry for {entry_date.strftime('%Y-%m-%d')}\n\nThis is test content."
            
            with open(entry_file, 'w') as f:
                f.write(entry_content)
            
            legacy_entries.append({
                'date': entry_date,
                'file_path': entry_file,
                'directory': daily_dir,
                'content': entry_content
            })
        
        yield {
            'temp_dir': temp_dir,
            'legacy_entries': legacy_entries
        }
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest_asyncio.fixture
    async def database_with_legacy_data(self):
        """Set up database with legacy journal entry data."""
        db_manager = DatabaseManager(":memory:")
        await db_manager.initialize()
        
        # Insert legacy journal entries with daily week endings
        legacy_entries = []
        base_date = date(2024, 1, 1)
        
        async with db_manager.get_session() as session:
            for i in range(30):
                entry_date = base_date + timedelta(days=i)
                # Legacy behavior: week_ending_date equals entry_date
                entry = JournalEntryIndex(
                    file_path=f"/test/week_ending_{entry_date.strftime('%Y-%m-%d')}/{entry_date.strftime('%Y-%m-%d')}.md",
                    entry_date=entry_date,
                    week_ending_date=entry_date,  # Legacy: daily week endings
                    content_hash="legacy_hash",
                    file_size=100,
                    last_modified=datetime.now(),
                    user_id="legacy_user"
                )
                session.add(entry)
                legacy_entries.append(entry)
            
            await session.commit()
        
        yield {
            'db_manager': db_manager,
            'legacy_entries': legacy_entries
        }

    @pytest.mark.asyncio
    async def test_existing_entry_accessibility(self, legacy_setup):
        """Verify that existing entries remain accessible after work week implementation."""
        temp_dir = legacy_setup['temp_dir']
        legacy_entries = legacy_setup['legacy_entries']
        
        # Initialize FileDiscovery with legacy directory structure
        discovery = FileDiscovery(temp_dir)
        
        # Test that all legacy entries can still be discovered
        discovered_files = discovery.discover_files()
        
        # Verify all legacy entries are found
        legacy_file_paths = {entry['file_path'] for entry in legacy_entries}
        discovered_file_paths = {file_info['file_path'] for file_info in discovered_files}
        
        missing_files = legacy_file_paths - discovered_file_paths
        assert not missing_files, f"Legacy files not discovered: {missing_files}"
        
        # Verify each legacy entry can be read
        for entry in legacy_entries:
            assert os.path.exists(entry['file_path']), f"Legacy file missing: {entry['file_path']}"
            
            with open(entry['file_path'], 'r') as f:
                content = f.read()
                assert content == entry['content'], f"Legacy file content changed: {entry['file_path']}"
        
        print(f"✓ All {len(legacy_entries)} legacy entries remain accessible")

    @pytest.mark.asyncio
    async def test_mixed_directory_structure_handling(self, legacy_setup):
        """Test that the system handles mixed old and new directory structures."""
        temp_dir = legacy_setup['temp_dir']
        
        # Add new work week style directories alongside legacy ones
        new_entries = self._create_new_style_directories(temp_dir)
        
        # Test file discovery with mixed structure
        discovery = FileDiscovery(temp_dir)
        discovered_files = discovery.discover_files()
        
        # Count legacy vs new style entries
        legacy_count = len(legacy_setup['legacy_entries'])
        new_count = len(new_entries)
        total_expected = legacy_count + new_count
        
        assert len(discovered_files) == total_expected, \
            f"Expected {total_expected} files, found {len(discovered_files)}"
        
        # Verify both old and new entries are accessible
        for file_info in discovered_files:
            assert os.path.exists(file_info['file_path']), f"File not accessible: {file_info['file_path']}"
        
        print(f"✓ Mixed structure handling: {legacy_count} legacy + {new_count} new entries")

    @pytest.mark.asyncio
    async def test_file_discovery_compatibility(self, legacy_setup):
        """Test file discovery works with legacy directory structures."""
        temp_dir = legacy_setup['temp_dir']
        legacy_entries = legacy_setup['legacy_entries']
        
        # Initialize services
        db_manager = DatabaseManager(":memory:")
        await db_manager.initialize()
        settings_service = SettingsService(db_manager)
        work_week_service = WorkWeekService(db_manager, settings_service)
        
        # Test FileDiscovery integration with work week service
        discovery = FileDiscovery(temp_dir)
        
        # Test week ending discovery for legacy dates
        for entry in legacy_entries[:5]:  # Test first 5 entries
            entry_date = entry['date']
            
            # Legacy method should still work
            week_ending_legacy = discovery._find_week_ending_for_date(entry_date)
            assert week_ending_legacy is not None, f"Could not find week ending for legacy date {entry_date}"
            
            # Verify the legacy week ending matches the entry date (legacy behavior)
            assert week_ending_legacy == entry_date, \
                f"Legacy week ending {week_ending_legacy} doesn't match entry date {entry_date}"
        
        print("✓ File discovery maintains compatibility with legacy structures")

    @pytest.mark.asyncio
    async def test_database_migration_compatibility(self, database_with_legacy_data):
        """Test database schema migration maintains data integrity."""
        db_manager = database_with_legacy_data['db_manager']
        legacy_entries = database_with_legacy_data['legacy_entries']
        
        # Verify legacy data is intact
        async with db_manager.get_session() as session:
            # Query all journal entries
            result = await session.execute("SELECT * FROM journal_entry_index")
            entries = result.fetchall()
            
            assert len(entries) == len(legacy_entries), \
                f"Expected {len(legacy_entries)} entries, found {len(entries)}"
            
            # Verify each legacy entry maintains its data
            for entry_row in entries:
                # Legacy entries should have week_ending_date equal to entry_date
                entry_date = entry_row[2]  # entry_date column
                week_ending_date = entry_row[3]  # week_ending_date column
                
                assert entry_date == week_ending_date, \
                    f"Legacy entry lost daily week ending: {entry_date} != {week_ending_date}"
        
        print(f"✓ Database migration preserves {len(legacy_entries)} legacy entries")

    @pytest.mark.asyncio
    async def test_api_backward_compatibility(self):
        """Verify no breaking API changes in work week implementation."""
        # Test that existing API endpoints still work
        db_manager = DatabaseManager(":memory:")
        await db_manager.initialize()
        settings_service = SettingsService(db_manager)
        
        # Test existing settings API compatibility
        user_id = "test_user"
        
        # Original settings operations should still work
        all_settings = await settings_service.get_all_settings(user_id)
        assert isinstance(all_settings, dict), "Settings API returned invalid format"
        
        # Test setting individual values (existing behavior)
        await settings_service.set_setting(user_id, "timezone", "UTC")
        timezone = await settings_service.get_setting(user_id, "timezone")
        assert timezone == "UTC", "Legacy setting operation failed"
        
        # Test that new work week settings don't break existing functionality
        work_week_service = WorkWeekService(db_manager, settings_service)
        
        # Get default work week config (should not affect existing settings)
        default_config = await work_week_service.get_default_work_week_config()
        assert default_config is not None, "Default work week config failed"
        
        # Verify existing settings still work after work week initialization
        timezone_after = await settings_service.get_setting(user_id, "timezone")
        assert timezone_after == "UTC", "Work week implementation broke existing settings"
        
        print("✓ API backward compatibility maintained")

    @pytest.mark.asyncio
    async def test_entry_manager_compatibility(self, legacy_setup):
        """Test EntryManager works with legacy and new directory structures."""
        temp_dir = legacy_setup['temp_dir']
        
        # Set up services
        db_manager = DatabaseManager(":memory:")
        await db_manager.initialize()
        settings_service = SettingsService(db_manager)
        work_week_service = WorkWeekService(db_manager, settings_service)
        
        entry_manager = EntryManager(db_manager, work_week_service, temp_dir)
        
        user_id = "test_user"
        
        # Test reading existing legacy entries
        for entry in legacy_setup['legacy_entries'][:3]:  # Test first 3
            entry_date = entry['date']
            
            # Should be able to read legacy entry
            content = await entry_manager.get_entry_content(user_id, entry_date)
            assert content is not None, f"Could not read legacy entry for {entry_date}"
            assert entry['content'] in content, f"Legacy content not preserved for {entry_date}"
        
        # Test creating new entries (should use new work week logic)
        new_date = date(2024, 2, 15)
        new_content = "New entry with work week logic"
        
        success = await entry_manager.save_entry_content(user_id, new_date, new_content)
        assert success, "Failed to create new entry with work week logic"
        
        # Verify new entry uses proper work week directory structure
        retrieved_content = await entry_manager.get_entry_content(user_id, new_date)
        assert new_content in retrieved_content, "New entry content not saved correctly"
        
        print("✓ EntryManager maintains compatibility with legacy entries")

    @pytest.mark.asyncio
    async def test_configuration_migration_safety(self):
        """Test that work week configuration changes don't affect existing entries."""
        # Set up test environment
        temp_dir = tempfile.mkdtemp()
        
        try:
            db_manager = DatabaseManager(":memory:")
            await db_manager.initialize()
            settings_service = SettingsService(db_manager)
            work_week_service = WorkWeekService(db_manager, settings_service)
            entry_manager = EntryManager(db_manager, work_week_service, temp_dir)
            
            user_id = "migration_test_user"
            
            # Create entries with default configuration (Monday-Friday)
            default_config = WorkWeekConfig(
                preset=WorkWeekPreset.MONDAY_FRIDAY,
                start_day=1, end_day=5, timezone="UTC"
            )
            await work_week_service.update_work_week_config(user_id, default_config)
            
            # Create some entries
            test_dates = [date(2024, 1, 15), date(2024, 1, 16), date(2024, 1, 17)]
            original_entries = {}
            
            for test_date in test_dates:
                content = f"Entry for {test_date}"
                await entry_manager.save_entry_content(user_id, test_date, content)
                original_entries[test_date] = content
            
            # Change work week configuration to Sunday-Thursday
            new_config = WorkWeekConfig(
                preset=WorkWeekPreset.SUNDAY_THURSDAY,
                start_day=7, end_day=4, timezone="UTC"
            )
            await work_week_service.update_work_week_config(user_id, new_config)
            
            # Verify existing entries are still accessible with original content
            for test_date, original_content in original_entries.items():
                retrieved_content = await entry_manager.get_entry_content(user_id, test_date)
                assert original_content in retrieved_content, \
                    f"Configuration change affected existing entry for {test_date}"
            
            # Create new entry with new configuration
            new_date = date(2024, 2, 20)
            new_content = f"New entry with Sunday-Thursday config for {new_date}"
            await entry_manager.save_entry_content(user_id, new_date, new_content)
            
            # Verify new entry uses new configuration
            retrieved_new_content = await entry_manager.get_entry_content(user_id, new_date)
            assert new_content in retrieved_new_content, "New entry not created with new configuration"
            
            print("✓ Configuration changes don't affect existing entries")
            
        finally:
            shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_data_integrity_validation(self, database_with_legacy_data):
        """Validate data integrity during work week implementation."""
        db_manager = database_with_legacy_data['db_manager']
        legacy_entries = database_with_legacy_data['legacy_entries']
        
        # Count original entries
        original_count = len(legacy_entries)
        
        # Initialize work week service (simulates deployment)
        settings_service = SettingsService(db_manager)
        work_week_service = WorkWeekService(db_manager, settings_service)
        
        # Verify all data is still present
        async with db_manager.get_session() as session:
            result = await session.execute("SELECT COUNT(*) FROM journal_entry_index")
            current_count = result.scalar()
            
            assert current_count == original_count, \
                f"Data loss detected: {original_count} -> {current_count} entries"
            
            # Verify no corruption in existing data
            result = await session.execute("SELECT * FROM journal_entry_index")
            entries = result.fetchall()
            
            for entry_row in entries:
                # Verify required fields are not null
                assert entry_row[1] is not None, "file_path is null"  # file_path
                assert entry_row[2] is not None, "entry_date is null"  # entry_date
                assert entry_row[3] is not None, "week_ending_date is null"  # week_ending_date
                
                # Verify file paths are valid
                file_path = entry_row[1]
                assert isinstance(file_path, str) and len(file_path) > 0, \
                    f"Invalid file_path: {file_path}"
        
        print(f"✓ Data integrity validated: {original_count} entries preserved")

    @pytest.mark.asyncio
    async def test_timezone_compatibility(self):
        """Test timezone handling compatibility with existing installations."""
        db_manager = DatabaseManager(":memory:")
        await db_manager.initialize()
        settings_service = SettingsService(db_manager)
        work_week_service = WorkWeekService(db_manager, settings_service)
        
        user_id = "timezone_test_user"
        
        # Test with various timezone configurations
        timezones = ["UTC", "America/New_York", "Europe/London", "Asia/Tokyo"]
        
        for timezone in timezones:
            # Set user timezone (existing functionality)
            await settings_service.set_setting(user_id, "timezone", timezone)
            
            # Get work week configuration with timezone
            config = await work_week_service.get_user_work_week_config(user_id)
            assert config.timezone == timezone, f"Timezone not properly set: {config.timezone}"
            
            # Test calculation with timezone
            test_date = date(2024, 1, 15)
            week_ending = await work_week_service.calculate_week_ending_date(
                test_date, config, timezone
            )
            
            assert week_ending is not None, f"Week ending calculation failed for timezone {timezone}"
            assert isinstance(week_ending, date), f"Invalid week ending type for timezone {timezone}"
        
        print(f"✓ Timezone compatibility tested with {len(timezones)} timezones")

    def _create_new_style_directories(self, base_dir: str) -> List[Dict[str, Any]]:
        """Create new work week style directories for testing."""
        new_entries = []
        base_date = date(2024, 2, 1)
        
        # Create weekly directories (new style)
        for week in range(4):
            # Calculate week ending date (Friday for Monday-Friday work week)
            monday = base_date + timedelta(weeks=week)
            friday = monday + timedelta(days=4)  # Friday is 4 days after Monday
            
            # Create weekly directory
            weekly_dir = os.path.join(base_dir, f"week_ending_{friday.strftime('%Y-%m-%d')}")
            os.makedirs(weekly_dir, exist_ok=True)
            
            # Create entries for each day of the work week
            for day in range(5):  # Monday to Friday
                entry_date = monday + timedelta(days=day)
                entry_file = os.path.join(weekly_dir, f"{entry_date.strftime('%Y-%m-%d')}.md")
                entry_content = f"New style entry for {entry_date.strftime('%Y-%m-%d')}\n\nWork week entry content."
                
                with open(entry_file, 'w') as f:
                    f.write(entry_content)
                
                new_entries.append({
                    'date': entry_date,
                    'file_path': entry_file,
                    'directory': weekly_dir,
                    'content': entry_content,
                    'week_ending': friday
                })
        
        return new_entries


class TestWorkWeekRegressionSafety:
    """Test that work week implementation doesn't break existing functionality."""
    
    @pytest.mark.asyncio
    async def test_cli_compatibility_maintained(self):
        """Verify CLI operations still work after work week implementation."""
        # This would test that command-line operations remain functional
        # For now, we'll test the core components that CLI depends on
        
        temp_dir = tempfile.mkdtemp()
        try:
            # Test FileDiscovery (used by CLI)
            discovery = FileDiscovery(temp_dir)
            
            # Create test structure
            test_date = date(2024, 1, 15)
            test_dir = os.path.join(temp_dir, f"week_ending_{test_date.strftime('%Y-%m-%d')}")
            os.makedirs(test_dir, exist_ok=True)
            
            test_file = os.path.join(test_dir, f"{test_date.strftime('%Y-%m-%d')}.md")
            with open(test_file, 'w') as f:
                f.write("Test CLI content")
            
            # Test discovery (CLI functionality)
            discovered = discovery.discover_files()
            assert len(discovered) > 0, "CLI file discovery broken"
            
            # Test week ending discovery (CLI functionality)
            week_ending = discovery._find_week_ending_for_date(test_date)
            assert week_ending == test_date, "CLI week ending discovery broken"
            
            print("✓ CLI compatibility maintained")
            
        finally:
            shutil.rmtree(temp_dir)

    @pytest.mark.asyncio
    async def test_web_interface_compatibility(self):
        """Verify web interface functionality remains intact."""
        db_manager = DatabaseManager(":memory:")
        await db_manager.initialize()
        settings_service = SettingsService(db_manager)
        
        user_id = "web_test_user"
        
        # Test core web functionality
        # Settings management (existing functionality)
        await settings_service.set_setting(user_id, "theme", "dark")
        theme = await settings_service.get_setting(user_id, "theme")
        assert theme == "dark", "Web settings functionality broken"
        
        # Test settings page data (existing functionality)
        all_settings = await settings_service.get_all_settings(user_id)
        assert isinstance(all_settings, dict), "Web settings page data broken"
        assert "theme" in all_settings, "Settings not properly returned"
        
        # Test work week integration doesn't break web functionality
        work_week_service = WorkWeekService(db_manager, settings_service)
        
        # After work week initialization, web functionality should still work
        theme_after = await settings_service.get_setting(user_id, "theme")
        assert theme_after == "dark", "Work week broke web settings"
        
        print("✓ Web interface compatibility maintained")

    @pytest.mark.asyncio
    async def test_performance_regression_check(self):
        """Check that work week implementation doesn't cause performance regression."""
        import time
        
        # Test database operations performance
        db_manager = DatabaseManager(":memory:")
        await db_manager.initialize()
        settings_service = SettingsService(db_manager)
        
        user_id = "perf_test_user"
        
        # Measure settings operations (should remain fast)
        start_time = time.perf_counter()
        
        for i in range(100):
            await settings_service.set_setting(user_id, f"test_setting_{i}", f"value_{i}")
        
        settings_time = time.perf_counter() - start_time
        
        # Should complete 100 operations in reasonable time
        assert settings_time < 1.0, f"Settings operations too slow: {settings_time:.3f}s"
        
        # Test work week service doesn't slow down basic operations
        work_week_service = WorkWeekService(db_manager, settings_service)
        
        start_time = time.perf_counter()
        
        for i in range(100):
            config = await work_week_service.get_user_work_week_config(user_id)
        
        work_week_time = time.perf_counter() - start_time
        
        # Work week operations should also be fast
        assert work_week_time < 2.0, f"Work week operations too slow: {work_week_time:.3f}s"
        
        print(f"✓ Performance regression check passed: settings={settings_time:.3f}s, work_week={work_week_time:.3f}s")


if __name__ == "__main__":
    # Run compatibility tests
    pytest.main([__file__, "-v", "--tb=short"])