# ABOUTME: Pydantic models for settings management requests and responses.
# ABOUTME: Covers CRUD, bulk updates, work-week config, and import/export schemas.
"""
Settings Models for Daily Work Journal Web Interface

This module defines Pydantic models for settings management,
including validation, import/export, and response formatting.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Any, Dict, Optional, Union, List

class WebSettingCreate(BaseModel):
    """Model for creating a new web setting."""
    key: str = Field(..., description="Setting key")
    value: str = Field(..., description="Setting value as string")
    value_type: str = Field(..., description="Value type (string, integer, boolean, float, json)")
    description: Optional[str] = Field(None, description="Setting description")
    
    @field_validator('value_type')
    def validate_value_type(cls, v):
        """Validate value type is supported."""
        allowed_types = ['string', 'integer', 'boolean', 'float', 'json']
        if v not in allowed_types:
            raise ValueError(f'Value type must be one of: {", ".join(allowed_types)}')
        return v

class WebSettingUpdate(BaseModel):
    """Model for updating an existing web setting."""
    value: str = Field(..., description="New setting value as string")
    description: Optional[str] = Field(None, description="Updated description")

class WebSettingResponse(BaseModel):
    """Response model for web settings."""
    id: int = Field(..., description="Setting ID")
    key: str = Field(..., description="Setting key")
    value: str = Field(..., description="Raw setting value")
    value_type: str = Field(..., description="Value type")
    description: Optional[str] = Field(None, description="Setting description")
    parsed_value: Any = Field(..., description="Parsed value in correct type")
    created_at: datetime = Field(..., description="Creation timestamp")
    modified_at: datetime = Field(..., description="Last modification timestamp")

class SettingsCollection(BaseModel):
    """Collection of settings organized by category."""
    settings: Dict[str, WebSettingResponse] = Field(..., description="Settings by key")
    categories: Dict[str, List[str]] = Field(..., description="Settings organized by category")
    total_count: int = Field(..., description="Total number of settings")

class SettingsExport(BaseModel):
    """Model for settings export data."""
    version: str = Field(..., description="Export format version")
    exported_at: str = Field(..., description="Export timestamp")
    settings: Dict[str, Dict[str, Any]] = Field(..., description="Settings data")

class SettingsImport(BaseModel):
    """Model for settings import data."""
    settings: Dict[str, Any] = Field(..., description="Settings to import")
    
    @field_validator('settings')
    def validate_settings_format(cls, v):
        """Validate settings import format."""
        if not isinstance(v, dict):
            raise ValueError('Settings must be a dictionary')
        return v

class SettingsCategoryResponse(BaseModel):
    """Response model for settings organized by category."""
    categories: Dict[str, List[str]] = Field(..., description="Settings by category")

class SettingsValidationError(BaseModel):
    """Model for settings validation errors."""
    key: str = Field(..., description="Setting key that failed validation")
    error: str = Field(..., description="Validation error message")
    current_value: Any = Field(..., description="Current value that failed")
    expected_type: str = Field(..., description="Expected value type")

class SettingsBulkUpdateRequest(BaseModel):
    """Model for bulk settings update."""
    settings: Dict[str, Any] = Field(..., description="Settings to update")
    validate_only: bool = Field(False, description="Only validate without updating")

class SettingsBulkUpdateResponse(BaseModel):
    """Response model for bulk settings update."""
    updated_settings: Dict[str, WebSettingResponse] = Field(..., description="Successfully updated settings")
    validation_errors: List[SettingsValidationError] = Field(default_factory=list, description="Validation errors")
    success_count: int = Field(..., description="Number of successfully updated settings")
    error_count: int = Field(..., description="Number of failed updates")

class SettingsBackupInfo(BaseModel):
    """Information about a settings backup."""
    backup_id: str = Field(..., description="Unique backup identifier")
    created_at: datetime = Field(..., description="Backup creation time")
    settings_count: int = Field(..., description="Number of settings in backup")
    description: Optional[str] = Field(None, description="Backup description")
    file_size_bytes: int = Field(..., description="Backup file size in bytes")

class SettingsRestoreRequest(BaseModel):
    """Request model for settings restore."""
    backup_id: str = Field(..., description="Backup ID to restore from")
    restore_mode: str = Field("merge", description="Restore mode: 'merge' or 'replace'")
    
    @field_validator('restore_mode')
    def validate_restore_mode(cls, v):
        """Validate restore mode."""
        if v not in ['merge', 'replace']:
            raise ValueError("Restore mode must be 'merge' or 'replace'")
        return v

class SettingsRestoreResponse(BaseModel):
    """Response model for settings restore."""
    restored_settings: Dict[str, WebSettingResponse] = Field(..., description="Restored settings")
    skipped_settings: List[str] = Field(default_factory=list, description="Settings that were skipped")
    restore_count: int = Field(..., description="Number of settings restored")
    backup_info: SettingsBackupInfo = Field(..., description="Information about the backup used")


# Work Week Settings Models

class WorkWeekConfigRequest(BaseModel):
    """Request model for work week configuration."""
    preset: str = Field(..., description="Work week preset: monday_friday, sunday_thursday, or custom")
    start_day: Optional[int] = Field(None, description="Work week start day (1=Monday, 7=Sunday)")
    end_day: Optional[int] = Field(None, description="Work week end day (1=Monday, 7=Sunday)")
    timezone: Optional[str] = Field("UTC", description="Timezone for work week calculations")
    
    @field_validator('preset')
    def validate_preset(cls, v):
        """Validate work week preset."""
        allowed_presets = ['monday_friday', 'sunday_thursday', 'custom']
        if v not in allowed_presets:
            raise ValueError(f'Preset must be one of: {", ".join(allowed_presets)}')
        return v
    
    @field_validator('start_day')
    def validate_start_day(cls, v):
        """Validate start day."""
        if v is not None and not (1 <= v <= 7):
            raise ValueError('Start day must be between 1 (Monday) and 7 (Sunday)')
        return v
    
    @field_validator('end_day')
    def validate_end_day(cls, v):
        """Validate end day."""
        if v is not None and not (1 <= v <= 7):
            raise ValueError('End day must be between 1 (Monday) and 7 (Sunday)')
        return v

class WorkWeekConfigResponse(BaseModel):
    """Response model for work week configuration."""
    preset: str = Field(..., description="Current work week preset")
    start_day: int = Field(..., description="Work week start day")
    end_day: int = Field(..., description="Work week end day")
    timezone: str = Field(..., description="Timezone for calculations")
    start_day_name: str = Field(..., description="Start day name (e.g., 'Monday')")
    end_day_name: str = Field(..., description="End day name (e.g., 'Friday')")
    is_valid: bool = Field(..., description="Whether configuration is valid")
    validation_errors: List[str] = Field(default_factory=list, description="Validation error messages")
    
class WorkWeekPresetInfo(BaseModel):
    """Information about a work week preset."""
    name: str = Field(..., description="Preset display name")
    description: str = Field(..., description="Preset description")
    start_day: Optional[int] = Field(None, description="Preset start day")
    end_day: Optional[int] = Field(None, description="Preset end day")
    start_day_name: str = Field(..., description="Start day name")
    end_day_name: str = Field(..., description="End day name")

class WorkWeekPresetsResponse(BaseModel):
    """Response model for available work week presets."""
    presets: Dict[str, WorkWeekPresetInfo] = Field(..., description="Available presets")
    current_preset: str = Field(..., description="Currently selected preset")

class WorkWeekValidationRequest(BaseModel):
    """Request model for work week validation."""
    preset: str = Field(..., description="Work week preset to validate")
    start_day: Optional[int] = Field(None, description="Start day for custom preset")
    end_day: Optional[int] = Field(None, description="End day for custom preset")
    
    @field_validator('preset')
    def validate_preset(cls, v):
        """Validate work week preset."""
        allowed_presets = ['monday_friday', 'sunday_thursday', 'custom']
        if v not in allowed_presets:
            raise ValueError(f'Preset must be one of: {", ".join(allowed_presets)}')
        return v

class WorkWeekValidationResponse(BaseModel):
    """Response model for work week validation."""
    valid: bool = Field(..., description="Whether configuration is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    auto_corrections: Dict[str, Any] = Field(default_factory=dict, description="Auto-correction suggestions")
    preview: WorkWeekConfigResponse = Field(..., description="Preview of configuration if applied")

class WorkWeekUpdateResponse(BaseModel):
    """Response model for work week configuration updates."""
    success: bool = Field(..., description="Whether update was successful")
    updated_settings: Dict[str, Any] = Field(default_factory=dict, description="Settings that were updated")  
    errors: List[str] = Field(default_factory=list, description="Update errors")
    current_config: WorkWeekConfigResponse = Field(..., description="Current work week configuration")