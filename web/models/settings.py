"""
Settings Models for Web Interface

This module contains Pydantic models for web-specific settings management,
validation, and API operations.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Any, Dict, Optional, Union, List
from datetime import datetime as DateTime
from enum import Enum


class SettingValueType(str, Enum):
    """Setting value type enumeration."""
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    JSON = "json"
    FLOAT = "float"


class WebSettingBase(BaseModel):
    """Base model for web settings."""
    key: str = Field(..., min_length=1, max_length=100, description="Setting key")
    value: str = Field(..., description="Setting value as string")
    value_type: SettingValueType = Field(..., description="Value type")
    description: Optional[str] = Field(None, max_length=500, description="Setting description")
    
    @field_validator('key')
    def validate_key_format(cls, v):
        """Validate setting key format."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Setting key must contain only alphanumeric characters, underscores, and hyphens')
        return v.lower()


class WebSettingCreate(WebSettingBase):
    """Model for creating web settings."""
    pass


class WebSettingUpdate(BaseModel):
    """Model for updating web settings."""
    value: str = Field(..., description="Updated setting value")
    description: Optional[str] = Field(None, max_length=500, description="Updated description")
    
    @field_validator('value')
    def validate_value_not_empty(cls, v):
        """Ensure value is not empty."""
        if not v.strip():
            raise ValueError('Setting value cannot be empty')
        return v


class WebSettingResponse(WebSettingBase):
    """Model for web setting API responses."""
    id: int = Field(..., description="Setting ID")
    parsed_value: Union[str, int, bool, float, Dict[str, Any]] = Field(..., description="Parsed value")
    created_at: DateTime = Field(..., description="Creation timestamp")
    modified_at: DateTime = Field(..., description="Last modification timestamp")
    
    class Config:
        from_attributes = True


class SettingsCollection(BaseModel):
    """Collection of settings for bulk operations."""
    settings: Dict[str, Union[str, int, bool, float, Dict[str, Any]]] = Field(..., description="Settings dictionary")
    
    @field_validator('settings')
    def validate_settings_keys(cls, v):
        """Validate setting keys against allowed values."""
        allowed_keys = {
            'auto_save_interval', 'theme', 'editor_font_size', 
            'show_word_count', 'calendar_start_day', 'editor_theme',
            'show_line_numbers', 'word_wrap', 'auto_backup',
            'backup_interval', 'max_backup_files', 'enable_spell_check',
            'default_view', 'entries_per_page', 'date_format',
            'time_format', 'timezone'
        }
        invalid_keys = set(v.keys()) - allowed_keys
        if invalid_keys:
            raise ValueError(f'Invalid setting keys: {invalid_keys}')
        return v


class SettingsBulkUpdate(BaseModel):
    """Model for bulk settings updates."""
    updates: List[Dict[str, Union[str, int, bool, float]]] = Field(..., description="List of setting updates")
    
    @field_validator('updates')
    def validate_updates_format(cls, v):
        """Validate bulk update format."""
        for update in v:
            if 'key' not in update or 'value' not in update:
                raise ValueError('Each update must contain "key" and "value" fields')
        return v


class SettingsExport(BaseModel):
    """Model for settings export."""
    settings: Dict[str, Any] = Field(..., description="Exported settings")
    export_timestamp: DateTime = Field(default_factory=DateTime.utcnow, description="Export timestamp")
    version: str = Field("1.0", description="Export format version")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Export metadata")


class SettingsImport(BaseModel):
    """Model for settings import."""
    settings: Dict[str, Any] = Field(..., description="Settings to import")
    overwrite_existing: bool = Field(False, description="Whether to overwrite existing settings")
    validate_only: bool = Field(False, description="Only validate without importing")
    
    @field_validator('settings')
    def validate_import_settings(cls, v):
        """Validate imported settings structure."""
        if not isinstance(v, dict):
            raise ValueError('Settings must be a dictionary')
        return v


class UserPreferences(BaseModel):
    """Model for user preferences."""
    theme: str = Field("light", pattern="^(light|dark|auto)$", description="UI theme")
    editor_font_size: int = Field(14, ge=8, le=32, description="Editor font size")
    editor_theme: str = Field("default", description="Editor theme")
    auto_save_interval: int = Field(30, ge=5, le=300, description="Auto-save interval in seconds")
    show_word_count: bool = Field(True, description="Show word count in editor")
    show_line_numbers: bool = Field(True, description="Show line numbers in editor")
    word_wrap: bool = Field(True, description="Enable word wrap in editor")
    calendar_start_day: int = Field(0, ge=0, le=6, description="Calendar start day (0=Sunday)")
    entries_per_page: int = Field(20, ge=5, le=100, description="Entries per page in lists")
    date_format: str = Field("YYYY-MM-DD", description="Preferred date format")
    time_format: str = Field("24h", pattern="^(12h|24h)$", description="Time format preference")
    enable_spell_check: bool = Field(False, description="Enable spell checking")
    auto_backup: bool = Field(True, description="Enable automatic backups")
    backup_interval: int = Field(24, ge=1, le=168, description="Backup interval in hours")
    max_backup_files: int = Field(30, ge=1, le=365, description="Maximum backup files to keep")


class SettingsValidationResult(BaseModel):
    """Result of settings validation."""
    valid: bool = Field(..., description="Whether settings are valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    corrected_values: Dict[str, Any] = Field(default_factory=dict, description="Auto-corrected values")


class SettingsBackup(BaseModel):
    """Model for settings backup."""
    backup_id: str = Field(..., description="Backup identifier")
    settings: Dict[str, Any] = Field(..., description="Backed up settings")
    created_at: DateTime = Field(..., description="Backup creation timestamp")
    description: Optional[str] = Field(None, description="Backup description")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Backup metadata")