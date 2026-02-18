"""
Tests for Work Week Settings Service Integration

This module tests the integration of work week settings into the SettingsService,
including validation, presets, and CRUD operations.
"""

import pytest
import pytest_asyncio
import asyncio
import tempfile
import os
from datetime import datetime
from web.services.settings_service import SettingsService
from web.database import DatabaseManager
from config_manager import ConfigManager, AppConfig
from logger import JournalSummarizerLogger, LogConfig


class TestWorkWeekSettingsIntegration:
    """Test work week settings integration with SettingsService."""
    
    @pytest_asyncio.fixture
    async def settings_service(self):
        """Create a SettingsService with temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # Initialize database manager
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()
        
        # Create mock config and logger
        config = AppConfig()
        log_config = LogConfig()
        logger = JournalSummarizerLogger(log_config)
        
        # Initialize settings service
        service = SettingsService(config, logger, db_manager)
        
        yield service
        
        # Cleanup
        await db_manager.engine.dispose()
        os.unlink(db_path)
    
    @pytest.mark.asyncio
    async def test_work_week_settings_definitions(self, settings_service):
        """Test that work week settings are properly defined."""
        definitions = settings_service.setting_definitions
        
        # Check that work week settings are defined
        assert 'work_week.preset' in definitions
        assert 'work_week.start_day' in definitions
        assert 'work_week.end_day' in definitions
        assert 'work_week.timezone' in definitions
        
        # Check default values
        assert definitions['work_week.preset'].default_value == 'monday_friday'
        assert definitions['work_week.start_day'].default_value == 1
        assert definitions['work_week.end_day'].default_value == 5
        assert definitions['work_week.timezone'].default_value == 'UTC'
        
        # Check validation rules
        preset_options = definitions['work_week.preset'].validation_rules['options']
        assert 'monday_friday' in preset_options
        assert 'sunday_thursday' in preset_options
        assert 'custom' in preset_options
    
    @pytest.mark.asyncio
    async def test_get_work_week_settings(self, settings_service):
        """Test getting work week settings."""
        settings = await settings_service.get_work_week_settings()
        
        # Should return default values
        assert settings['preset'] == 'monday_friday'
        assert settings['start_day'] == 1
        assert settings['end_day'] == 5
        assert settings['timezone'] == 'UTC'
    
    @pytest.mark.asyncio
    async def test_update_work_week_preset_monday_friday(self, settings_service):
        """Test updating work week preset to Monday-Friday."""
        success = await settings_service.update_work_week_preset('monday_friday')
        assert success is True
        
        # Verify settings were updated
        settings = await settings_service.get_work_week_settings()
        assert settings['preset'] == 'monday_friday'
        assert settings['start_day'] == 1  # Monday
        assert settings['end_day'] == 5    # Friday
    
    @pytest.mark.asyncio
    async def test_update_work_week_preset_sunday_thursday(self, settings_service):
        """Test updating work week preset to Sunday-Thursday."""
        success = await settings_service.update_work_week_preset('sunday_thursday')
        assert success is True
        
        # Verify settings were updated
        settings = await settings_service.get_work_week_settings()
        assert settings['preset'] == 'sunday_thursday'
        assert settings['start_day'] == 7  # Sunday
        assert settings['end_day'] == 4    # Thursday
    
    @pytest.mark.asyncio
    async def test_update_work_week_preset_custom(self, settings_service):
        """Test updating work week preset to custom."""
        # First set to Monday-Friday
        await settings_service.update_work_week_preset('monday_friday')
        
        # Then update to custom (should not change start/end days)
        success = await settings_service.update_work_week_preset('custom')
        assert success is True
        
        # Verify preset changed but days remained the same
        settings = await settings_service.get_work_week_settings()
        assert settings['preset'] == 'custom'
        assert settings['start_day'] == 1  # Should remain Monday
        assert settings['end_day'] == 5    # Should remain Friday
    
    @pytest.mark.asyncio
    async def test_validate_custom_work_week_valid(self, settings_service):
        """Test validation of valid custom work week."""
        result = await settings_service.validate_custom_work_week(2, 6)  # Tue-Sat
        
        assert result['valid'] is True
        assert len(result['errors']) == 0
        assert len(result['warnings']) == 0
        assert len(result['auto_corrections']) == 0
    
    @pytest.mark.asyncio
    async def test_validate_custom_work_week_invalid_days(self, settings_service):
        """Test validation with invalid day values."""
        result = await settings_service.validate_custom_work_week(0, 8)  # Invalid days
        
        assert result['valid'] is False
        assert any("Start day must be between" in error for error in result['errors'])
        assert any("End day must be between" in error for error in result['errors'])
    
    @pytest.mark.asyncio
    async def test_validate_custom_work_week_same_days(self, settings_service):
        """Test validation when start and end days are the same."""
        result = await settings_service.validate_custom_work_week(3, 3)  # Same day
        
        assert result['valid'] is False
        assert any("cannot be the same" in error for error in result['errors'])
        assert result['auto_corrections']['start_day'] == 1
        assert result['auto_corrections']['end_day'] == 5
        assert len(result['warnings']) > 0
    
    @pytest.mark.asyncio
    async def test_get_work_week_presets(self, settings_service):
        """Test getting available work week presets."""
        presets = await settings_service.get_work_week_presets()
        
        assert 'monday_friday' in presets
        assert 'sunday_thursday' in presets
        assert 'custom' in presets
        
        # Check Monday-Friday preset details
        mf_preset = presets['monday_friday']
        assert mf_preset['name'] == 'Monday - Friday'
        assert mf_preset['start_day'] == 1
        assert mf_preset['end_day'] == 5
        
        # Check Sunday-Thursday preset details
        st_preset = presets['sunday_thursday']
        assert st_preset['name'] == 'Sunday - Thursday'
        assert st_preset['start_day'] == 7
        assert st_preset['end_day'] == 4
        
        # Check custom preset details
        custom_preset = presets['custom']
        assert custom_preset['name'] == 'Custom'
        assert custom_preset['start_day'] is None
        assert custom_preset['end_day'] is None
    
    @pytest.mark.asyncio
    async def test_update_work_week_configuration_preset_only(self, settings_service):
        """Test updating work week configuration with preset only."""
        result = await settings_service.update_work_week_configuration('sunday_thursday')
        
        assert result['success'] is True
        assert 'preset' in result['updated_settings']
        assert result['updated_settings']['preset'] == 'sunday_thursday'
        assert len(result['errors']) == 0
        
        # Verify the configuration was applied
        settings = await settings_service.get_work_week_settings()
        assert settings['preset'] == 'sunday_thursday'
        assert settings['start_day'] == 7
        assert settings['end_day'] == 4
    
    @pytest.mark.asyncio
    async def test_update_work_week_configuration_custom(self, settings_service):
        """Test updating work week configuration with custom days."""
        result = await settings_service.update_work_week_configuration(
            preset='custom',
            start_day=2,  # Tuesday
            end_day=6,    # Saturday
            timezone='US/Pacific'
        )
        
        assert result['success'] is True
        assert result['updated_settings']['preset'] == 'custom'
        assert result['updated_settings']['start_day'] == 2
        assert result['updated_settings']['end_day'] == 6
        assert result['updated_settings']['timezone'] == 'US/Pacific'
        
        # Verify the configuration was applied
        settings = await settings_service.get_work_week_settings()
        assert settings['preset'] == 'custom'
        assert settings['start_day'] == 2
        assert settings['end_day'] == 6
        assert settings['timezone'] == 'US/Pacific'
    
    @pytest.mark.asyncio
    async def test_update_work_week_configuration_invalid_custom(self, settings_service):
        """Test updating work week configuration with invalid custom days."""
        result = await settings_service.update_work_week_configuration(
            preset='custom',
            start_day=3,  # Same as end day
            end_day=3
        )
        
        assert result['success'] is False
        assert len(result['errors']) > 0
        assert any("cannot be the same" in error for error in result['errors'])
    
    @pytest.mark.asyncio
    async def test_work_week_settings_validation(self, settings_service):
        """Test work week settings validation through update_setting."""
        # Test valid preset
        result = await settings_service.update_setting('work_week.preset', 'sunday_thursday')
        assert result is not None
        assert result.parsed_value == 'sunday_thursday'
        
        # Test invalid preset
        with pytest.raises(ValueError):
            await settings_service.update_setting('work_week.preset', 'invalid_preset')
        
        # Test valid day
        result = await settings_service.update_setting('work_week.start_day', '3')
        assert result is not None
        assert result.parsed_value == 3
        
        # Test invalid day
        with pytest.raises(ValueError):
            await settings_service.update_setting('work_week.start_day', '8')
        
        # Test valid timezone
        result = await settings_service.update_setting('work_week.timezone', 'Europe/London')
        assert result is not None
        assert result.parsed_value == 'Europe/London'
        
        # Test empty timezone
        with pytest.raises(ValueError):
            await settings_service.update_setting('work_week.timezone', '')
    
    @pytest.mark.asyncio
    async def test_work_week_settings_in_get_all_settings(self, settings_service):
        """Test that work week settings appear in get_all_settings."""
        all_settings = await settings_service.get_all_settings()
        
        # Check that work week settings are included
        assert 'work_week.preset' in all_settings
        assert 'work_week.start_day' in all_settings
        assert 'work_week.end_day' in all_settings
        assert 'work_week.timezone' in all_settings
        
        # Verify default values
        assert all_settings['work_week.preset'].parsed_value == 'monday_friday'
        assert all_settings['work_week.start_day'].parsed_value == 1
        assert all_settings['work_week.end_day'].parsed_value == 5
        assert all_settings['work_week.timezone'].parsed_value == 'UTC'
    
    @pytest.mark.asyncio
    async def test_work_week_settings_categories(self, settings_service):
        """Test that work week settings are properly categorized."""
        categories = settings_service.get_setting_categories()
        
        assert 'work_week' in categories
        work_week_settings = categories['work_week']
        
        assert 'work_week.preset' in work_week_settings
        assert 'work_week.start_day' in work_week_settings
        assert 'work_week.end_day' in work_week_settings
        assert 'work_week.timezone' in work_week_settings
    
    @pytest.mark.asyncio
    async def test_work_week_settings_export_import(self, settings_service):
        """Test exporting and importing work week settings."""
        # Update some work week settings
        await settings_service.update_work_week_configuration(
            preset='sunday_thursday',
            timezone='US/Eastern'
        )
        
        # Export settings
        export_data = await settings_service.export_settings()
        assert 'work_week.preset' in export_data.settings
        assert 'work_week.timezone' in export_data.settings
        assert export_data.settings['work_week.preset']['value'] == 'sunday_thursday'
        assert export_data.settings['work_week.timezone']['value'] == 'US/Eastern'
        
        # Reset to defaults
        await settings_service.update_work_week_preset('monday_friday')
        
        # Import settings
        imported = await settings_service.import_settings(export_data.dict())
        assert 'work_week.preset' in imported
        assert 'work_week.timezone' in imported
        
        # Verify imported settings
        settings = await settings_service.get_work_week_settings()
        assert settings['preset'] == 'sunday_thursday'
        assert settings['timezone'] == 'US/Eastern'


@pytest.mark.asyncio
async def test_work_week_settings_backward_compatibility():
    """Test that work week settings don't break existing settings functionality."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        # Initialize database and settings service
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()
        
        config = AppConfig()
        log_config = LogConfig()
        logger = JournalSummarizerLogger(log_config)
        service = SettingsService(config, logger, db_manager)
        
        # Test that existing settings still work
        result = await service.update_setting('editor.font_size', '18')
        assert result is not None
        assert result.parsed_value == 18
        
        # Test that new work week settings work alongside existing ones
        result = await service.update_setting('work_week.preset', 'sunday_thursday')
        assert result is not None
        assert result.parsed_value == 'sunday_thursday'
        
        # Get all settings and verify both types are present
        all_settings = await service.get_all_settings()
        assert 'editor.font_size' in all_settings
        assert 'work_week.preset' in all_settings
        assert all_settings['editor.font_size'].parsed_value == 18
        assert all_settings['work_week.preset'].parsed_value == 'sunday_thursday'
        
        # Cleanup
        await db_manager.engine.dispose()
        
    finally:
        os.unlink(db_path)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])