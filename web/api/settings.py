"""
Settings API Endpoints for Daily Work Journal Web Interface

This module provides REST API endpoints for managing web-specific settings
while maintaining compatibility with CLI configuration.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, Optional, List
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from config_manager import ConfigManager
from logger import JournalSummarizerLogger
from web.database import DatabaseManager
from web.services.settings_service import SettingsService
from web.models.settings import (
    WebSettingResponse, WebSettingCreate, WebSettingUpdate,
    SettingsCollection, SettingsExport, SettingsImport,
    SettingsCategoryResponse, SettingsBulkUpdateRequest, SettingsBulkUpdateResponse
)

# Initialize dependencies (will be initialized in dependency functions)
config_manager = None
config = None
logger = None
db_manager = None

router = APIRouter(prefix="/api/settings", tags=["settings"])

async def get_settings_service() -> SettingsService:
    """Dependency to get settings service instance."""
    global config_manager, config, logger, db_manager
    
    if config_manager is None:
        config_manager = ConfigManager()
        config = config_manager.get_config()
        logger = JournalSummarizerLogger(config.logging)
        db_manager = DatabaseManager()
    
    if not db_manager.engine:
        await db_manager.initialize()
    return SettingsService(config, logger, db_manager)

@router.get("/", response_model=Dict[str, WebSettingResponse])
async def get_all_settings(
    settings_service: SettingsService = Depends(get_settings_service)
):
    """Get all web settings with their current values."""
    try:
        settings = await settings_service.get_all_settings()
        return settings
    except Exception as e:
        logger.logger.error if logger else print if logger else print(f"Failed to get all settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve settings: {str(e)}"
        )

@router.get("/categories", response_model=SettingsCategoryResponse)
async def get_settings_categories(
    settings_service: SettingsService = Depends(get_settings_service)
):
    """Get settings organized by category."""
    try:
        categories = settings_service.get_setting_categories()
        return SettingsCategoryResponse(categories=categories)
    except Exception as e:
        logger.logger.error if logger else print(f"Failed to get settings categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve categories: {str(e)}"
        )

@router.get("/health")
async def settings_health_check(
    settings_service: SettingsService = Depends(get_settings_service)
):
    """Health check for settings service."""
    try:
        # Try to get a simple setting to test database connectivity
        test_setting = await settings_service.get_setting('ui.theme')
        
        return {
            "status": "healthy",
            "database_connected": test_setting is not None,
            "settings_count": len(await settings_service.get_all_settings()),
            "categories": list(settings_service.get_setting_categories().keys())
        }
    except Exception as e:
        if logger:
            logger.logger.error(f"Settings health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "database_connected": False
        }

@router.get("/{key}", response_model=WebSettingResponse)
async def get_setting(
    key: str,
    settings_service: SettingsService = Depends(get_settings_service)
):
    """Get a specific setting by key."""
    try:
        setting = await settings_service.get_setting(key)
        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{key}' not found"
            )
        return setting
    except HTTPException:
        raise
    except Exception as e:
        logger.logger.error if logger else print(f"Failed to get setting {key}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve setting: {str(e)}"
        )

@router.put("/{key}", response_model=WebSettingResponse)
async def update_setting(
    key: str,
    setting_update: WebSettingUpdate,
    settings_service: SettingsService = Depends(get_settings_service)
):
    """Update a specific setting."""
    try:
        updated_setting = await settings_service.update_setting(key, setting_update.value)
        if not updated_setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{key}' not found"
            )
        return updated_setting
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.logger.error if logger else print(f"Failed to update setting {key}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update setting: {str(e)}"
        )

@router.post("/bulk-update", response_model=SettingsBulkUpdateResponse)
async def bulk_update_settings(
    bulk_request: SettingsBulkUpdateRequest,
    settings_service: SettingsService = Depends(get_settings_service)
):
    """Update multiple settings at once."""
    try:
        result = await settings_service.bulk_update_settings(bulk_request.settings)
        return result
    except Exception as e:
        logger.logger.error if logger else print(f"Failed to bulk update settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk update settings: {str(e)}"
        )

@router.post("/{key}/reset", response_model=WebSettingResponse)
async def reset_setting(
    key: str,
    settings_service: SettingsService = Depends(get_settings_service)
):
    """Reset a setting to its default value."""
    try:
        reset_setting = await settings_service.reset_setting(key)
        if not reset_setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{key}' not found"
            )
        return reset_setting
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.logger.error if logger else print(f"Failed to reset setting {key}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset setting: {str(e)}"
        )

@router.post("/reset-all", response_model=Dict[str, WebSettingResponse])
async def reset_all_settings(
    settings_service: SettingsService = Depends(get_settings_service)
):
    """Reset all settings to their default values."""
    try:
        reset_settings = await settings_service.reset_all_settings()
        return reset_settings
    except Exception as e:
        logger.logger.error if logger else print(f"Failed to reset all settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset all settings: {str(e)}"
        )

@router.get("/export/current", response_model=SettingsExport)
async def export_settings(
    settings_service: SettingsService = Depends(get_settings_service)
):
    """Export all current settings for backup or transfer."""
    try:
        export_data = await settings_service.export_settings()
        return export_data
    except Exception as e:
        logger.logger.error if logger else print(f"Failed to export settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export settings: {str(e)}"
        )

@router.post("/import", response_model=Dict[str, WebSettingResponse])
async def import_settings(
    import_data: SettingsImport,
    settings_service: SettingsService = Depends(get_settings_service)
):
    """Import settings from exported data."""
    try:
        imported_settings = await settings_service.import_settings(import_data.settings)
        return imported_settings
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.logger.error if logger else print(f"Failed to import settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import settings: {str(e)}"
        )

@router.get("/filesystem/validate-path")
async def validate_filesystem_path(
    path: str,
    create_if_missing: bool = False,
    settings_service: SettingsService = Depends(get_settings_service)
):
    """Validate a filesystem path and optionally create it."""
    try:
        from pathlib import Path
        
        path_obj = Path(path)
        
        # Check if path is absolute or make it relative to current working directory
        if not path_obj.is_absolute():
            path_obj = Path.cwd() / path_obj
        
        exists = path_obj.exists()
        is_directory = path_obj.is_dir() if exists else None
        is_writable = None
        
        if exists:
            try:
                # Test write permissions
                test_file = path_obj / ".write_test"
                test_file.touch()
                test_file.unlink()
                is_writable = True
            except:
                is_writable = False
        elif create_if_missing:
            try:
                path_obj.mkdir(parents=True, exist_ok=True)
                exists = True
                is_directory = True
                is_writable = True
                logger.logger.info if logger else print(f"Created directory: {path_obj}")
            except Exception as e:
                logger.logger.error if logger else print(f"Failed to create directory {path_obj}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot create directory: {str(e)}"
                )
        
        return {
            "path": str(path_obj),
            "exists": exists,
            "is_directory": is_directory,
            "is_writable": is_writable,
            "absolute_path": str(path_obj.absolute())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.logger.error if logger else print(f"Failed to validate path {path}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid path: {str(e)}"
        )
