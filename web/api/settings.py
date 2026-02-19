"""
Settings API Endpoints for Daily Work Journal Web Interface

This module provides REST API endpoints for managing web-specific settings
while maintaining compatibility with CLI configuration.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, status
from typing import Dict, Any, Optional, List
import json
from datetime import datetime
from pathlib import Path

from web.services.settings_service import SettingsService
from web.models.settings import (
    WebSettingResponse, WebSettingCreate, WebSettingUpdate,
    SettingsCollection, SettingsExport, SettingsImport,
    SettingsCategoryResponse, SettingsBulkUpdateRequest, SettingsBulkUpdateResponse,
    WorkWeekConfigRequest, WorkWeekConfigResponse, WorkWeekPresetsResponse,
    WorkWeekValidationRequest, WorkWeekValidationResponse, WorkWeekUpdateResponse,
    WorkWeekPresetInfo
)

router = APIRouter(prefix="/api/settings", tags=["settings"])


def get_settings_service(request: Request) -> SettingsService:
    """Dependency to get SettingsService from app state."""
    return request.app.state.settings_service

@router.get("/", response_model=Dict[str, WebSettingResponse])
async def get_all_settings(
    settings_service: SettingsService = Depends(get_settings_service)
):
    """Get all web settings with their current values."""
    try:
        settings = await settings_service.get_all_settings()
        return settings
    except Exception as e:
        settings_service.logger.logger.error(f"Failed to get all settings: {str(e)}")
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
        settings_service.logger.logger.error(f"Failed to get settings categories: {str(e)}")
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
        settings_service.logger.logger.error(f"Settings health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "database_connected": False
        }

# Work Week Settings Endpoints (must come before generic /{key} route)

def _get_day_name(day_num: int) -> str:
    """Convert day number to name."""
    day_names = {1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 
                 5: 'Friday', 6: 'Saturday', 7: 'Sunday'}
    return day_names.get(day_num, 'Unknown')

async def _build_work_week_config_response(settings: Dict[str, Any]) -> WorkWeekConfigResponse:
    """Build work week configuration response from settings."""
    preset = settings.get('preset', 'monday_friday')
    start_day = settings.get('start_day', 1)
    end_day = settings.get('end_day', 5)
    timezone = settings.get('timezone', 'UTC')
    
    # Validate configuration
    is_valid = True
    validation_errors = []
    
    if start_day == end_day:
        is_valid = False
        validation_errors.append("Start day and end day cannot be the same")
    
    if not (1 <= start_day <= 7):
        is_valid = False
        validation_errors.append("Start day must be between 1 and 7")
    
    if not (1 <= end_day <= 7):
        is_valid = False
        validation_errors.append("End day must be between 1 and 7")
    
    return WorkWeekConfigResponse(
        preset=preset,
        start_day=start_day,
        end_day=end_day,
        timezone=timezone,
        start_day_name=_get_day_name(start_day),
        end_day_name=_get_day_name(end_day),
        is_valid=is_valid,
        validation_errors=validation_errors
    )

@router.get("/work-week", response_model=WorkWeekConfigResponse)
async def get_work_week_configuration(
    settings_service: SettingsService = Depends(get_settings_service)
):
    """Get current work week configuration."""
    try:
        settings = await settings_service.get_work_week_settings()
        return await _build_work_week_config_response(settings)
    except Exception as e:
        settings_service.logger.logger.error(f"Failed to get work week configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve work week configuration: {str(e)}"
        )

@router.post("/work-week", response_model=WorkWeekUpdateResponse)
async def update_work_week_configuration(
    config_request: WorkWeekConfigRequest,
    settings_service: SettingsService = Depends(get_settings_service)
):
    """Update work week configuration."""
    try:
        # Update configuration
        result = await settings_service.update_work_week_configuration(
            preset=config_request.preset,
            start_day=config_request.start_day,
            end_day=config_request.end_day,
            timezone=config_request.timezone
        )
        
        # Get current configuration
        current_settings = await settings_service.get_work_week_settings()
        current_config = await _build_work_week_config_response(current_settings)
        
        return WorkWeekUpdateResponse(
            success=result['success'],
            updated_settings=result['updated_settings'],
            errors=result['errors'],
            current_config=current_config
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        settings_service.logger.logger.error(f"Failed to update work week configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update work week configuration: {str(e)}"
        )

@router.get("/work-week/presets", response_model=WorkWeekPresetsResponse)
async def get_work_week_presets(
    settings_service: SettingsService = Depends(get_settings_service)
):
    """Get available work week presets."""
    try:
        presets_data = await settings_service.get_work_week_presets()
        current_settings = await settings_service.get_work_week_settings()
        
        # Convert to API response format
        presets = {}
        for key, preset_info in presets_data.items():
            presets[key] = WorkWeekPresetInfo(
                name=preset_info['name'],
                description=preset_info['description'],
                start_day=preset_info['start_day'],
                end_day=preset_info['end_day'],
                start_day_name=preset_info['start_day_name'],
                end_day_name=preset_info['end_day_name']
            )
        
        return WorkWeekPresetsResponse(
            presets=presets,
            current_preset=current_settings.get('preset', 'monday_friday')
        )
        
    except Exception as e:
        settings_service.logger.logger.error(f"Failed to get work week presets: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve work week presets: {str(e)}"
        )

@router.post("/work-week/validate", response_model=WorkWeekValidationResponse)
async def validate_work_week_configuration(
    validation_request: WorkWeekValidationRequest,
    settings_service: SettingsService = Depends(get_settings_service)
):
    """Validate work week configuration without saving."""
    try:
        preset = validation_request.preset
        start_day = validation_request.start_day
        end_day = validation_request.end_day
        
        # Get defaults for preset if custom days not provided
        if preset != 'custom':
            presets_data = await settings_service.get_work_week_presets()
            if preset in presets_data:
                start_day = start_day or presets_data[preset]['start_day']
                end_day = end_day or presets_data[preset]['end_day']
        
        # Validate custom configuration if we have both days
        if start_day is not None and end_day is not None:
            validation_result = await settings_service.validate_custom_work_week(start_day, end_day)
        else:
            validation_result = {
                'valid': preset in ['monday_friday', 'sunday_thursday', 'custom'],
                'errors': [] if preset in ['monday_friday', 'sunday_thursday', 'custom'] else ['Invalid preset'],
                'warnings': [],
                'auto_corrections': {}
            }
        
        # Apply auto-corrections if any
        if validation_result.get('auto_corrections'):
            start_day = validation_result['auto_corrections'].get('start_day', start_day)
            end_day = validation_result['auto_corrections'].get('end_day', end_day)
        
        # Build preview configuration
        current_settings = await settings_service.get_work_week_settings()
        preview_settings = {
            'preset': preset,
            'start_day': start_day or current_settings.get('start_day', 1),
            'end_day': end_day or current_settings.get('end_day', 5),
            'timezone': current_settings.get('timezone', 'UTC')
        }
        preview_config = await _build_work_week_config_response(preview_settings)
        
        return WorkWeekValidationResponse(
            valid=validation_result['valid'],
            errors=validation_result['errors'],
            warnings=validation_result['warnings'],
            auto_corrections=validation_result['auto_corrections'],
            preview=preview_config
        )
        
    except Exception as e:
        settings_service.logger.logger.error(f"Failed to validate work week configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate work week configuration: {str(e)}"
        )

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
        settings_service.logger.logger.error(f"Failed to get setting {key}: {str(e)}")
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
        settings_service.logger.logger.error(f"Failed to update setting {key}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update setting: {str(e)}"
        )

@router.post("/bulk-update", response_model=SettingsBulkUpdateResponse)
async def bulk_update_settings(
    bulk_request: SettingsBulkUpdateRequest,
    settings_service: SettingsService = Depends(get_settings_service)
):
    """Update multiple settings at once with enhanced error handling and logging."""
    operation_start = datetime.now()
    request_id = f"api_{operation_start.strftime('%H%M%S')}_{id(bulk_request)}"
    
    settings_service.logger.logger.info(
        f"[API] Bulk update request received {request_id}",
        extra={
            'request_id': request_id,
            'settings_count': len(bulk_request.settings),
            'settings_keys': list(bulk_request.settings.keys()),
            'client_ip': 'unknown',  # Could be enhanced with actual client IP
            'timestamp': operation_start.isoformat()
        }
    )

    try:
        # Call the service method with comprehensive logging
        result = await settings_service.bulk_update_settings(bulk_request.settings)

        # Determine appropriate HTTP status code based on result
        if result.error_count == 0:
            # All settings updated successfully
            status_code = status.HTTP_200_OK
            settings_service.logger.logger.info(
                f"[API] Bulk update completed successfully {request_id}",
                extra={
                    'request_id': request_id,
                    'success_count': result.success_count,
                    'duration_ms': (datetime.now() - operation_start).total_seconds() * 1000
                }
            )
        elif result.success_count > 0:
            # Partial success - some settings updated, some failed
            status_code = status.HTTP_207_MULTI_STATUS
            settings_service.logger.logger.warning(
                f"[API] Bulk update partially successful {request_id}",
                extra={
                    'request_id': request_id,
                    'success_count': result.success_count,
                    'error_count': result.error_count,
                    'failed_settings': [error.key for error in result.validation_errors],
                    'duration_ms': (datetime.now() - operation_start).total_seconds() * 1000
                }
            )
        else:
            # Complete failure - no settings updated
            status_code = status.HTTP_400_BAD_REQUEST
            settings_service.logger.logger.error(
                f"[API] Bulk update completely failed {request_id}",
                extra={
                    'request_id': request_id,
                    'error_count': result.error_count,
                    'failed_settings': [error.key for error in result.validation_errors],
                    'duration_ms': (datetime.now() - operation_start).total_seconds() * 1000
                }
            )
        
        # Add metadata to response
        response_data = result.dict()
        response_data['request_id'] = request_id
        response_data['processing_time_ms'] = (datetime.now() - operation_start).total_seconds() * 1000
        response_data['timestamp'] = datetime.now().isoformat()
        
        # Create response with appropriate status code
        from fastapi import Response
        response = Response(
            content=json.dumps(response_data, default=str),
            media_type="application/json",
            status_code=status_code
        )
        
        return result  # FastAPI will handle the serialization, but we've logged the status
        
    except ValueError as ve:
        # Validation errors
        settings_service.logger.logger.error(
            f"[API] Bulk update validation error {request_id}: {str(ve)}",
            extra={
                'request_id': request_id,
                'error_type': 'validation_error',
                'error_message': str(ve),
                'duration_ms': (datetime.now() - operation_start).total_seconds() * 1000
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                'error': 'Validation failed',
                'message': str(ve),
                'request_id': request_id,
                'timestamp': datetime.now().isoformat()
            }
        )
    except ConnectionError as ce:
        # Database connection errors
        settings_service.logger.logger.error(
            f"[API] Bulk update database connection error {request_id}: {str(ce)}",
            extra={
                'request_id': request_id,
                'error_type': 'database_connection_error',
                'error_message': str(ce),
                'duration_ms': (datetime.now() - operation_start).total_seconds() * 1000
            }
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                'error': 'Database connection failed',
                'message': 'Unable to connect to settings database',
                'request_id': request_id,
                'timestamp': datetime.now().isoformat(),
                'retry_after': 30  # Suggest retry after 30 seconds
            }
        )
    except TimeoutError as te:
        # Operation timeout errors
        settings_service.logger.logger.error(
            f"[API] Bulk update timeout error {request_id}: {str(te)}",
            extra={
                'request_id': request_id,
                'error_type': 'timeout_error',
                'error_message': str(te),
                'duration_ms': (datetime.now() - operation_start).total_seconds() * 1000
            }
        )
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail={
                'error': 'Operation timeout',
                'message': 'Settings update operation took too long',
                'request_id': request_id,
                'timestamp': datetime.now().isoformat()
            }
        )
    except Exception as e:
        # Generic server errors
        settings_service.logger.logger.error(
            f"[API] Bulk update internal error {request_id}: {str(e)}",
            extra={
                'request_id': request_id,
                'error_type': 'internal_server_error',
                'error_message': str(e),
                'duration_ms': (datetime.now() - operation_start).total_seconds() * 1000
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                'error': 'Internal server error',
                'message': 'An unexpected error occurred while updating settings',
                'request_id': request_id,
                'timestamp': datetime.now().isoformat()
            }
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
        settings_service.logger.logger.error(f"Failed to reset setting {key}: {str(e)}")
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
        settings_service.logger.logger.error(f"Failed to reset all settings: {str(e)}")
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
        settings_service.logger.logger.error(f"Failed to export settings: {str(e)}")
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
        imported_settings = await settings_service.import_settings({"settings": import_data.settings})
        return imported_settings
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        settings_service.logger.logger.error(f"Failed to import settings: {str(e)}")
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
                settings_service.logger.logger.info(f"Created directory: {path_obj}")
            except Exception as e:
                settings_service.logger.logger.error(f"Failed to create directory {path_obj}: {str(e)}")
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
        settings_service.logger.logger.error(f"Failed to validate path {path}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid path: {str(e)}"
        )


