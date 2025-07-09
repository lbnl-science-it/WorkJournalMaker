"""
Tests for Work Week API Endpoints

This module tests the work week configuration API endpoints,
including validation, error handling, and integration scenarios.
"""

import pytest
import pytest_asyncio
import asyncio
import tempfile
import os
import json
from pathlib import Path
from datetime import datetime
from fastapi.testclient import TestClient
import sys

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))
from web.api.settings import router, get_settings_service
from web.services.settings_service import SettingsService
from web.database import DatabaseManager
from config_manager import ConfigManager, AppConfig
from logger import JournalSummarizerLogger, LogConfig
from fastapi import FastAPI


class TestWorkWeekAPI:
    """Test work week API endpoints."""
    
    @pytest_asyncio.fixture
    async def app_with_db(self):
        """Create FastAPI app with temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # Initialize database manager
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()
        
        # Create mock config and logger
        config = AppConfig()
        log_config = LogConfig()
        logger = JournalSummarizerLogger(log_config)
        
        # Create settings service
        settings_service = SettingsService(config, logger, db_manager)
        
        # Create FastAPI app and include router
        app = FastAPI()
        app.include_router(router)
        
        # Override dependency
        async def override_get_settings_service():
            return settings_service
        
        app.dependency_overrides[get_settings_service] = override_get_settings_service
        
        yield app
        
        # Cleanup
        await db_manager.engine.dispose()
        os.unlink(db_path)
    
    @pytest.fixture
    def client(self, app_with_db):
        """Create test client."""
        return TestClient(app_with_db)
    
    def test_get_work_week_configuration_default(self, client):
        """Test getting default work week configuration."""
        response = client.get("/api/settings/work-week")
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.text}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["preset"] == "monday_friday"
        assert data["start_day"] == 1
        assert data["end_day"] == 5
        assert data["timezone"] == "UTC"
        assert data["start_day_name"] == "Monday"
        assert data["end_day_name"] == "Friday"
        assert data["is_valid"] is True
        assert len(data["validation_errors"]) == 0
    
    def test_get_work_week_presets(self, client):
        """Test getting available work week presets."""
        response = client.get("/api/settings/work-week/presets")
        assert response.status_code == 200
        
        data = response.json()
        assert "presets" in data
        assert "current_preset" in data
        assert data["current_preset"] == "monday_friday"
        
        presets = data["presets"]
        assert "monday_friday" in presets
        assert "sunday_thursday" in presets
        assert "custom" in presets
        
        # Check Monday-Friday preset
        mf_preset = presets["monday_friday"]
        assert mf_preset["name"] == "Monday - Friday"
        assert mf_preset["start_day"] == 1
        assert mf_preset["end_day"] == 5
        assert mf_preset["start_day_name"] == "Monday"
        assert mf_preset["end_day_name"] == "Friday"
        
        # Check Sunday-Thursday preset
        st_preset = presets["sunday_thursday"]
        assert st_preset["name"] == "Sunday - Thursday"
        assert st_preset["start_day"] == 7
        assert st_preset["end_day"] == 4
        assert st_preset["start_day_name"] == "Sunday"
        assert st_preset["end_day_name"] == "Thursday"
        
        # Check custom preset
        custom_preset = presets["custom"]
        assert custom_preset["name"] == "Custom"
        assert custom_preset["start_day"] is None
        assert custom_preset["end_day"] is None
    
    def test_update_work_week_configuration_preset_only(self, client):
        """Test updating work week configuration with preset only."""
        request_data = {
            "preset": "sunday_thursday"
        }
        
        response = client.post("/api/settings/work-week", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "preset" in data["updated_settings"]
        assert data["updated_settings"]["preset"] == "sunday_thursday"
        assert len(data["errors"]) == 0
        
        # Check current configuration
        current_config = data["current_config"]
        assert current_config["preset"] == "sunday_thursday"
        assert current_config["start_day"] == 7  # Sunday
        assert current_config["end_day"] == 4    # Thursday
        assert current_config["is_valid"] is True
    
    def test_update_work_week_configuration_custom(self, client):
        """Test updating work week configuration with custom days."""
        request_data = {
            "preset": "custom",
            "start_day": 2,  # Tuesday
            "end_day": 6,    # Saturday
            "timezone": "US/Pacific"
        }
        
        response = client.post("/api/settings/work-week", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["updated_settings"]["preset"] == "custom"
        assert data["updated_settings"]["start_day"] == 2
        assert data["updated_settings"]["end_day"] == 6
        assert data["updated_settings"]["timezone"] == "US/Pacific"
        
        # Check current configuration
        current_config = data["current_config"]
        assert current_config["preset"] == "custom"
        assert current_config["start_day"] == 2
        assert current_config["end_day"] == 6
        assert current_config["timezone"] == "US/Pacific"
        assert current_config["start_day_name"] == "Tuesday"
        assert current_config["end_day_name"] == "Saturday"
        assert current_config["is_valid"] is True
    
    def test_update_work_week_configuration_invalid_preset(self, client):
        """Test updating work week configuration with invalid preset."""
        request_data = {
            "preset": "invalid_preset"
        }
        
        response = client.post("/api/settings/work-week", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_update_work_week_configuration_invalid_days(self, client):
        """Test updating work week configuration with invalid days."""
        request_data = {
            "preset": "custom",
            "start_day": 0,  # Invalid
            "end_day": 8     # Invalid
        }
        
        response = client.post("/api/settings/work-week", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_update_work_week_configuration_same_days(self, client):
        """Test updating work week configuration with same start/end days."""
        request_data = {
            "preset": "custom",
            "start_day": 3,  # Wednesday
            "end_day": 3     # Wednesday (same day)
        }
        
        response = client.post("/api/settings/work-week", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        # Should succeed but with auto-correction
        assert data["success"] is True
        # Auto-corrected to Monday-Friday
        assert data["updated_settings"]["start_day"] == 1
        assert data["updated_settings"]["end_day"] == 5
    
    def test_validate_work_week_configuration_valid(self, client):
        """Test validating a valid work week configuration."""
        request_data = {
            "preset": "custom",
            "start_day": 2,  # Tuesday
            "end_day": 6     # Saturday
        }
        
        response = client.post("/api/settings/work-week/validate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] is True
        assert len(data["errors"]) == 0
        assert len(data["warnings"]) == 0
        assert len(data["auto_corrections"]) == 0
        
        # Check preview
        preview = data["preview"]
        assert preview["preset"] == "custom"
        assert preview["start_day"] == 2
        assert preview["end_day"] == 6
        assert preview["start_day_name"] == "Tuesday"
        assert preview["end_day_name"] == "Saturday"
        assert preview["is_valid"] is True
    
    def test_validate_work_week_configuration_invalid_same_days(self, client):
        """Test validating work week configuration with same start/end days."""
        request_data = {
            "preset": "custom",
            "start_day": 4,  # Thursday
            "end_day": 4     # Thursday (same day)
        }
        
        response = client.post("/api/settings/work-week/validate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0
        assert any("cannot be the same" in error for error in data["errors"])
        assert len(data["warnings"]) > 0
        assert "start_day" in data["auto_corrections"]
        assert "end_day" in data["auto_corrections"]
        assert data["auto_corrections"]["start_day"] == 1
        assert data["auto_corrections"]["end_day"] == 5
        
        # Preview should show auto-corrected values
        preview = data["preview"]
        assert preview["start_day"] == 1
        assert preview["end_day"] == 5
    
    def test_validate_work_week_configuration_preset_only(self, client):
        """Test validating work week configuration with preset only."""
        request_data = {
            "preset": "sunday_thursday"
        }
        
        response = client.post("/api/settings/work-week/validate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] is True
        assert len(data["errors"]) == 0
        
        # Preview should show preset values
        preview = data["preview"]
        assert preview["preset"] == "sunday_thursday"
        assert preview["start_day"] == 7  # Sunday
        assert preview["end_day"] == 4    # Thursday
    
    def test_validate_work_week_configuration_invalid_preset(self, client):
        """Test validating work week configuration with invalid preset."""
        request_data = {
            "preset": "invalid_preset"
        }
        
        response = client.post("/api/settings/work-week/validate", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_work_week_configuration_persistence(self, client):
        """Test that work week configuration changes persist."""
        # Update to Sunday-Thursday
        request_data = {
            "preset": "sunday_thursday",
            "timezone": "US/Eastern"
        }
        
        response = client.post("/api/settings/work-week", json=request_data)
        assert response.status_code == 200
        
        # Get configuration to verify persistence
        response = client.get("/api/settings/work-week")
        assert response.status_code == 200
        
        data = response.json()
        assert data["preset"] == "sunday_thursday"
        assert data["start_day"] == 7
        assert data["end_day"] == 4
        assert data["timezone"] == "US/Eastern"
    
    def test_work_week_configuration_multiple_updates(self, client):
        """Test multiple work week configuration updates."""
        # First update: Monday-Friday
        response = client.post("/api/settings/work-week", json={"preset": "monday_friday"})
        assert response.status_code == 200
        
        # Second update: Custom
        response = client.post("/api/settings/work-week", json={
            "preset": "custom",
            "start_day": 3,  # Wednesday
            "end_day": 7     # Sunday
        })
        assert response.status_code == 200
        
        # Third update: Sunday-Thursday
        response = client.post("/api/settings/work-week", json={"preset": "sunday_thursday"})
        assert response.status_code == 200
        
        # Verify final state
        response = client.get("/api/settings/work-week")
        assert response.status_code == 200
        
        data = response.json()
        assert data["preset"] == "sunday_thursday"
        assert data["start_day"] == 7
        assert data["end_day"] == 4
    
    def test_work_week_api_error_handling(self, client):
        """Test API error handling scenarios."""
        # Test malformed JSON
        response = client.post("/api/settings/work-week", 
                                   content="invalid json", 
                                   headers={"content-type": "application/json"})
        assert response.status_code == 422
        
        # Test missing required fields
        response = client.post("/api/settings/work-week", json={})
        assert response.status_code == 422
        
        # Test invalid field types
        response = client.post("/api/settings/work-week", json={
            "preset": 123,  # Should be string
            "start_day": "invalid"  # Should be int
        })
        assert response.status_code == 422
    
    def test_work_week_timezone_handling(self, client):
        """Test timezone handling in work week configuration."""
        timezones = ["UTC", "US/Pacific", "US/Eastern", "Europe/London", "Asia/Tokyo"]
        
        for timezone in timezones:
            request_data = {
                "preset": "monday_friday",
                "timezone": timezone
            }
            
            response = client.post("/api/settings/work-week", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["current_config"]["timezone"] == timezone
    
    def test_work_week_validation_with_current_settings(self, client):
        """Test validation considers current settings when fields are omitted."""
        # Set initial configuration
        client.post("/api/settings/work-week", json={
            "preset": "custom",
            "start_day": 2,
            "end_day": 6,
            "timezone": "US/Pacific"
        })
        
        # Validate with only preset change
        response = client.post("/api/settings/work-week/validate", json={
            "preset": "monday_friday"
        })
        assert response.status_code == 200
        
        data = response.json()
        preview = data["preview"]
        # Should show new preset but preserve timezone
        assert preview["preset"] == "monday_friday"
        assert preview["start_day"] == 1  # From preset
        assert preview["end_day"] == 5    # From preset
        # Timezone should be preserved from current settings
        assert preview["timezone"] == "US/Pacific"


class TestWorkWeekAPIIntegration:
    """Test work week API integration with other systems."""
    
    @pytest_asyncio.fixture
    async def test_app(self):
        """Create test app with real database for integration testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()
        
        config = AppConfig()
        log_config = LogConfig()
        logger = JournalSummarizerLogger(log_config)
        settings_service = SettingsService(config, logger, db_manager)
        
        app = FastAPI()
        app.include_router(router)
        
        async def override_get_settings_service():
            return settings_service
        
        app.dependency_overrides[get_settings_service] = override_get_settings_service
        
        yield app
        
        await db_manager.engine.dispose()
        os.unlink(db_path)
    
    def test_work_week_api_with_general_settings(self, test_app):
        """Test work week API integration with general settings API."""
        with TestClient(test_app) as client:
            # Update some general settings
            client.put("/api/settings/ui.theme", json={"value": "dark"})
            client.put("/api/settings/editor.font_size", json={"value": "18"})
            
            # Update work week settings
            client.post("/api/settings/work-week", json={
                "preset": "sunday_thursday",
                "timezone": "US/Eastern"
            })
            
            # Get all settings - should include both general and work week
            response = client.get("/api/settings/")
            assert response.status_code == 200
            
            data = response.json()
            # Check general settings
            assert "ui.theme" in data
            assert data["ui.theme"]["parsed_value"] == "dark"
            assert "editor.font_size" in data
            assert data["editor.font_size"]["parsed_value"] == 18
            
            # Check work week settings
            assert "work_week.preset" in data
            assert data["work_week.preset"]["parsed_value"] == "sunday_thursday"
            assert "work_week.timezone" in data
            assert data["work_week.timezone"]["parsed_value"] == "US/Eastern"
    
    def test_work_week_api_categories(self, test_app):
        """Test that work week settings appear in categories."""
        with TestClient(test_app) as client:
            response = client.get("/api/settings/categories")
            assert response.status_code == 200
            
            data = response.json()
            categories = data["categories"]
            
            # Check that work_week category exists
            assert "work_week" in categories
            work_week_settings = categories["work_week"]
            
            expected_settings = [
                "work_week.preset",
                "work_week.start_day", 
                "work_week.end_day",
                "work_week.timezone"
            ]
            
            for setting in expected_settings:
                assert setting in work_week_settings
    
    @pytest.mark.asyncio 
    async def test_work_week_api_export_import(self, test_app):
        """Test work week settings in export/import functionality."""
        with TestClient(test_app) as client:
            # Set custom work week configuration
            client.post("/api/settings/work-week", json={
                "preset": "custom",
                "start_day": 3,  # Wednesday
                "end_day": 7,    # Sunday
                "timezone": "Europe/London"
            })
            
            # Export settings
            response = client.get("/api/settings/export/current")
            assert response.status_code == 200
            
            export_data = response.json()
            settings = export_data["settings"]
            
            # Check work week settings in export
            assert "work_week.preset" in settings
            assert settings["work_week.preset"]["value"] == "custom" 
            assert "work_week.start_day" in settings
            assert settings["work_week.start_day"]["value"] == 3
            assert "work_week.end_day" in settings
            assert settings["work_week.end_day"]["value"] == 7
            assert "work_week.timezone" in settings
            assert settings["work_week.timezone"]["value"] == "Europe/London"
            
            # Reset to defaults
            client.post("/api/settings/work-week", json={"preset": "monday_friday"})
            
            # Import settings
            response = client.post("/api/settings/import", json={"settings": settings})
            assert response.status_code == 200
            
            # Verify imported settings
            response = client.get("/api/settings/work-week")
            assert response.status_code == 200
            
            data = response.json()
            assert data["preset"] == "custom"
            assert data["start_day"] == 3
            assert data["end_day"] == 7
            assert data["timezone"] == "Europe/London"


@pytest.mark.asyncio
async def test_work_week_api_performance():
    """Test work week API performance requirements."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()
        
        config = AppConfig()
        log_config = LogConfig()
        logger = JournalSummarizerLogger(log_config)
        settings_service = SettingsService(config, logger, db_manager)
        
        app = FastAPI()
        app.include_router(router)
        
        async def override_get_settings_service():
            return settings_service
        
        app.dependency_overrides[get_settings_service] = override_get_settings_service
        
        with TestClient(app) as client:
            import time
            
            # Test GET performance
            start_time = time.time()
            response = client.get("/api/settings/work-week")
            get_time = time.time() - start_time
            
            assert response.status_code == 200
            assert get_time < 0.1  # Should be < 100ms
            
            # Test POST performance
            start_time = time.time()
            response = client.post("/api/settings/work-week", json={
                "preset": "sunday_thursday"
            })
            post_time = time.time() - start_time
            
            assert response.status_code == 200
            assert post_time < 0.1  # Should be < 100ms
            
            # Test validation performance
            start_time = time.time()
            response = client.post("/api/settings/work-week/validate", json={
                "preset": "custom",
                "start_day": 2,
                "end_day": 6
            })
            validate_time = time.time() - start_time
            
            assert response.status_code == 200
            assert validate_time < 0.1  # Should be < 100ms
        
        await db_manager.engine.dispose()
        
    finally:
        os.unlink(db_path)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])