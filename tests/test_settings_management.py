"""
Comprehensive Tests for Settings Management System

This module tests the settings service, API endpoints, and integration
with the existing configuration system.
"""

import pytest
import pytest_asyncio
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from fastapi.testclient import TestClient
import sys
import json

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent))

from web.app import app
from web.database import DatabaseManager
from web.services.settings_service import SettingsService
from web.models.settings import (
    WebSettingCreate, WebSettingUpdate, SettingsImport,
    SettingsBulkUpdateRequest
)
from config_manager import ConfigManager
from logger import create_logger_with_config

class TestSettingsService:
    """Test the SettingsService class."""
    
    @pytest_asyncio.fixture
    async def temp_workspace(self):
        """Create temporary workspace for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest_asyncio.fixture
    async def test_config(self, temp_workspace):
        """Create test configuration."""
        config_manager = ConfigManager()
        config = config_manager.get_config()
        # Override paths for testing
        config.processing.base_path = str(temp_workspace / "worklogs")
        config.processing.output_path = str(temp_workspace / "output")
        return config
    
    @pytest_asyncio.fixture
    async def test_db_manager(self, temp_workspace):
        """Create test database manager."""
        db_path = temp_workspace / "test_settings.db"
        db_manager = DatabaseManager(str(db_path))
        await db_manager.initialize()
        yield db_manager
        if db_manager.engine:
            await db_manager.engine.dispose()
    
    @pytest_asyncio.fixture
    async def settings_service(self, test_config, test_db_manager):
        """Create settings service for testing."""
        try:
            logger = create_logger_with_config(test_config.logging)
        except Exception:
            # Fallback to JournalSummarizerLogger if create_logger_with_config fails
            from logger import JournalSummarizerLogger
            logger = JournalSummarizerLogger(test_config.logging)
        return SettingsService(test_config, logger, test_db_manager)
    
    @pytest.mark.asyncio
    async def test_get_all_settings(self, settings_service):
        """Test getting all settings."""
        settings = await settings_service.get_all_settings()
        
        assert isinstance(settings, dict)
        assert len(settings) > 0
        
        # Check that filesystem settings are present
        assert 'filesystem.base_path' in settings
        assert 'filesystem.output_path' in settings
        assert 'editor.auto_save_interval' in settings
        assert 'ui.theme' in settings
        
        # Verify setting structure
        for key, setting in settings.items():
            assert hasattr(setting, 'key')
            assert hasattr(setting, 'value')
            assert hasattr(setting, 'value_type')
            assert hasattr(setting, 'parsed_value')
            assert setting.key == key
    
    @pytest.mark.asyncio
    async def test_get_specific_setting(self, settings_service):
        """Test getting a specific setting."""
        setting = await settings_service.get_setting('ui.theme')
        
        assert setting is not None
        assert setting.key == 'ui.theme'
        assert setting.value_type == 'string'
        assert setting.parsed_value in ['light', 'dark', 'auto']
    
    @pytest.mark.asyncio
    async def test_update_setting(self, settings_service):
        """Test updating a setting."""
        # Update theme setting
        updated_setting = await settings_service.update_setting('ui.theme', 'dark')
        
        assert updated_setting is not None
        assert updated_setting.key == 'ui.theme'
        assert updated_setting.value == 'dark'
        assert updated_setting.parsed_value == 'dark'
        
        # Verify the change persisted
        retrieved_setting = await settings_service.get_setting('ui.theme')
        assert retrieved_setting.parsed_value == 'dark'
    
    @pytest.mark.asyncio
    async def test_update_filesystem_path(self, settings_service, temp_workspace):
        """Test updating filesystem path settings."""
        new_path = str(temp_workspace / "new_worklogs")
        
        # Update base path
        updated_setting = await settings_service.update_setting('filesystem.base_path', new_path)
        
        assert updated_setting is not None
        assert updated_setting.parsed_value == new_path
        
        # Verify directory was created (if auto_create_directories is enabled)
        path_obj = Path(new_path)
        # Directory creation depends on auto_create_directories setting
    
    @pytest.mark.asyncio
    async def test_validation_rules(self, settings_service):
        """Test setting validation rules."""
        # Test invalid theme value
        with pytest.raises(ValueError):
            await settings_service.update_setting('ui.theme', 'invalid_theme')
        
        # Test invalid font size (too small)
        with pytest.raises(ValueError):
            await settings_service.update_setting('editor.font_size', '8')
        
        # Test invalid font size (too large)
        with pytest.raises(ValueError):
            await settings_service.update_setting('editor.font_size', '30')
        
        # Test valid font size
        updated_setting = await settings_service.update_setting('editor.font_size', '18')
        assert updated_setting.parsed_value == 18
    
    @pytest.mark.asyncio
    async def test_bulk_update_settings(self, settings_service):
        """Test bulk updating multiple settings."""
        settings_to_update = {
            'ui.theme': 'dark',
            'editor.font_size': '20',
            'editor.auto_save_interval': '45'
        }
        
        result = await settings_service.bulk_update_settings(settings_to_update)
        
        assert result.success_count == 3
        assert result.error_count == 0
        assert len(result.updated_settings) == 3
        
        # Verify updates
        theme_setting = await settings_service.get_setting('ui.theme')
        assert theme_setting.parsed_value == 'dark'
        
        font_setting = await settings_service.get_setting('editor.font_size')
        assert font_setting.parsed_value == 20
    
    @pytest.mark.asyncio
    async def test_bulk_update_with_errors(self, settings_service):
        """Test bulk update with some invalid values."""
        settings_to_update = {
            'ui.theme': 'dark',  # Valid
            'editor.font_size': '50',  # Invalid (too large)
            'unknown.setting': 'value'  # Invalid (unknown setting)
        }
        
        result = await settings_service.bulk_update_settings(settings_to_update)
        
        assert result.success_count == 1
        assert result.error_count == 2
        assert len(result.validation_errors) == 2
    
    @pytest.mark.asyncio
    async def test_reset_setting(self, settings_service):
        """Test resetting a setting to default value."""
        # First change a setting
        await settings_service.update_setting('ui.theme', 'dark')
        
        # Reset it
        reset_setting = await settings_service.reset_setting('ui.theme')
        
        assert reset_setting is not None
        assert reset_setting.parsed_value == 'light'  # Default value
    
    @pytest.mark.asyncio
    async def test_export_import_settings(self, settings_service):
        """Test exporting and importing settings."""
        # Update some settings first
        await settings_service.update_setting('ui.theme', 'dark')
        await settings_service.update_setting('editor.font_size', '18')
        
        # Export settings
        export_data = await settings_service.export_settings()
        
        assert export_data.version == '1.0'
        assert 'ui.theme' in export_data.settings
        assert export_data.settings['ui.theme']['value'] == 'dark'
        
        # Reset settings
        await settings_service.reset_all_settings()
        
        # Import settings back
        imported_settings = await settings_service.import_settings(export_data.dict())
        
        assert 'ui.theme' in imported_settings
        
        # Verify import worked
        theme_setting = await settings_service.get_setting('ui.theme')
        assert theme_setting.parsed_value == 'dark'
    
    @pytest.mark.asyncio
    async def test_setting_categories(self, settings_service):
        """Test getting settings organized by category."""
        categories = settings_service.get_setting_categories()
        
        assert isinstance(categories, dict)
        assert 'filesystem' in categories
        assert 'editor' in categories
        assert 'ui' in categories
        assert 'calendar' in categories
        assert 'backup' in categories
        
        # Check that filesystem category contains expected settings
        filesystem_settings = categories['filesystem']
        assert 'filesystem.base_path' in filesystem_settings
        assert 'filesystem.output_path' in filesystem_settings

class TestSettingsAPI:
    """Test the Settings API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_get_all_settings_endpoint(self, client):
        """Test GET /api/settings/ endpoint."""
        response = client.get("/api/settings/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        
        # Check for expected settings
        assert 'filesystem.base_path' in data
        assert 'ui.theme' in data
    
    def test_get_settings_categories_endpoint(self, client):
        """Test GET /api/settings/categories endpoint."""
        response = client.get("/api/settings/categories")
        
        assert response.status_code == 200
        data = response.json()
        assert 'categories' in data
        assert isinstance(data['categories'], dict)
        assert 'filesystem' in data['categories']
    
    def test_get_specific_setting_endpoint(self, client):
        """Test GET /api/settings/{key} endpoint."""
        response = client.get("/api/settings/ui.theme")
        
        assert response.status_code == 200
        data = response.json()
        assert data['key'] == 'ui.theme'
        assert 'value' in data
        assert 'parsed_value' in data
    
    def test_get_nonexistent_setting_endpoint(self, client):
        """Test GET /api/settings/{key} with nonexistent key."""
        response = client.get("/api/settings/nonexistent.setting")
        
        assert response.status_code == 404
    
    def test_update_setting_endpoint(self, client):
        """Test PUT /api/settings/{key} endpoint."""
        response = client.put(
            "/api/settings/ui.theme",
            json={"value": "dark"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['key'] == 'ui.theme'
        assert data['value'] == 'dark'
        assert data['parsed_value'] == 'dark'
    
    def test_update_setting_invalid_value(self, client):
        """Test PUT /api/settings/{key} with invalid value."""
        response = client.put(
            "/api/settings/ui.theme",
            json={"value": "invalid_theme"}
        )
        
        assert response.status_code == 400
    
    def test_bulk_update_settings_endpoint(self, client):
        """Test POST /api/settings/bulk-update endpoint."""
        response = client.post(
            "/api/settings/bulk-update",
            json={
                "settings": {
                    "ui.theme": "dark",
                    "editor.font_size": "18"
                }
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['success_count'] == 2
        assert data['error_count'] == 0
    
    def test_reset_setting_endpoint(self, client):
        """Test POST /api/settings/{key}/reset endpoint."""
        # First change the setting
        client.put("/api/settings/ui.theme", json={"value": "dark"})
        
        # Then reset it
        response = client.post("/api/settings/ui.theme/reset")
        
        assert response.status_code == 200
        data = response.json()
        assert data['key'] == 'ui.theme'
        assert data['parsed_value'] == 'light'  # Default value
    
    def test_export_settings_endpoint(self, client):
        """Test GET /api/settings/export/current endpoint."""
        response = client.get("/api/settings/export/current")
        
        assert response.status_code == 200
        data = response.json()
        assert 'version' in data
        assert 'exported_at' in data
        assert 'settings' in data
        assert isinstance(data['settings'], dict)
    
    def test_import_settings_endpoint(self, client):
        """Test POST /api/settings/import endpoint."""
        # First export settings
        export_response = client.get("/api/settings/export/current")
        export_data = export_response.json()
        
        # Modify a setting in the export
        export_data['settings']['ui.theme']['value'] = 'dark'
        
        # Import the modified settings
        response = client.post(
            "/api/settings/import",
            json={"settings": export_data}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_validate_filesystem_path_endpoint(self, client):
        """Test GET /api/settings/filesystem/validate-path endpoint."""
        response = client.get(
            "/api/settings/filesystem/validate-path",
            params={"path": "/tmp/test_path", "create_if_missing": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert 'path' in data
        assert 'exists' in data
        assert 'is_directory' in data
        assert 'absolute_path' in data
    
    def test_settings_health_check_endpoint(self, client):
        """Test GET /api/settings/health endpoint."""
        response = client.get("/api/settings/health")
        
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert 'database_connected' in data
        assert 'settings_count' in data

class TestSettingsIntegration:
    """Test integration between settings and other components."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_filesystem_path_integration(self, client):
        """Test that filesystem path changes are properly validated."""
        # Test updating base path
        response = client.put(
            "/api/settings/filesystem.base_path",
            json={"value": "/tmp/test_journal_path"}
        )
        
        assert response.status_code == 200
        
        # Verify the path was updated
        get_response = client.get("/api/settings/filesystem.base_path")
        assert get_response.status_code == 200
        data = get_response.json()
        assert "/tmp/test_journal_path" in data['parsed_value']
    
    def test_readonly_settings_protection(self, client):
        """Test that read-only settings cannot be modified."""
        # Try to update a read-only setting (LLM provider)
        response = client.put(
            "/api/settings/llm.provider",
            json={"value": "different_provider"}
        )
        
        # Should fail because it's read-only
        assert response.status_code == 400
    
    def test_settings_persistence(self, client):
        """Test that settings persist across requests."""
        # Update a setting
        update_response = client.put(
            "/api/settings/ui.theme",
            json={"value": "dark"}
        )
        assert update_response.status_code == 200
        
        # Verify it persists in a new request
        get_response = client.get("/api/settings/ui.theme")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data['parsed_value'] == 'dark'

if __name__ == "__main__":
    pytest.main([__file__, "-v"])