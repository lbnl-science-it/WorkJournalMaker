"""
Settings Service for Daily Work Journal Web Interface

This service manages web-specific settings while maintaining compatibility
with the existing CLI configuration system.
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
import sys
from dataclasses import dataclass
import uuid
import os

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from config_manager import ConfigManager, AppConfig
from logger import JournalSummarizerLogger, ErrorCategory, LogConfig
from web.database import DatabaseManager, WebSettings
from web.services.base_service import BaseService
from web.models.settings import (
    WebSettingResponse, WebSettingCreate, WebSettingUpdate, 
    SettingsCollection, SettingsExport, SettingsImport,
    SettingsCategoryResponse, SettingsValidationError,
    SettingsBulkUpdateRequest, SettingsBulkUpdateResponse,
    SettingsBackupInfo, SettingsRestoreRequest, SettingsRestoreResponse
)
from sqlalchemy import select, update, delete

@dataclass
class SettingDefinition:
    """Definition of a web setting."""
    key: str
    default_value: Any
    value_type: str
    description: str
    category: str
    validation_rules: Dict[str, Any] = None
    requires_restart: bool = False

class SettingsService(BaseService):
    """
    Manages web-specific settings while maintaining compatibility
    with existing CLI configuration system.
    """
    
    def __init__(self, config: AppConfig, logger: JournalSummarizerLogger, 
                 db_manager: DatabaseManager):
        """Initialize SettingsService with core dependencies."""
        super().__init__(config, logger, db_manager)
        self.db_manager = db_manager
        self.config_manager = ConfigManager()
        
        # Define web-specific settings
        self.setting_definitions = {
            # File System Settings (Core Configuration)
            'filesystem.base_path': SettingDefinition(
                key='filesystem.base_path',
                default_value=str(self.config.processing.base_path),
                value_type='string',
                description='Base directory where journal text files are stored',
                category='filesystem',
                validation_rules={'path_must_exist': False, 'max_length': 500},
                requires_restart=True
            ),
            'filesystem.output_path': SettingDefinition(
                key='filesystem.output_path',
                default_value=str(self.config.processing.output_path),
                value_type='string',
                description='Directory where summary outputs are saved',
                category='filesystem',
                validation_rules={'path_must_exist': False, 'max_length': 500},
                requires_restart=True
            ),
            'filesystem.backup_path': SettingDefinition(
                key='filesystem.backup_path',
                default_value=str(Path(self.config.processing.base_path).parent / 'backups'),
                value_type='string',
                description='Directory where backups are stored',
                category='filesystem',
                validation_rules={'path_must_exist': False, 'max_length': 500}
            ),
            'filesystem.max_file_size_mb': SettingDefinition(
                key='filesystem.max_file_size_mb',
                default_value=self.config.processing.max_file_size_mb,
                value_type='integer',
                description='Maximum file size in MB for journal entries',
                category='filesystem',
                validation_rules={'min': 1, 'max': 100}
            ),
            'filesystem.auto_create_directories': SettingDefinition(
                key='filesystem.auto_create_directories',
                default_value=True,
                value_type='boolean',
                description='Automatically create directories if they don\'t exist',
                category='filesystem'
            ),
            
            # Editor Settings
            'editor.auto_save_interval': SettingDefinition(
                key='editor.auto_save_interval',
                default_value=30,
                value_type='integer',
                description='Auto-save interval in seconds',
                category='editor',
                validation_rules={'min': 10, 'max': 300}
            ),
            'editor.font_size': SettingDefinition(
                key='editor.font_size',
                default_value=16,
                value_type='integer',
                description='Editor font size in pixels',
                category='editor',
                validation_rules={'min': 12, 'max': 24}
            ),
            'editor.font_family': SettingDefinition(
                key='editor.font_family',
                default_value='Inter',
                value_type='string',
                description='Editor font family',
                category='editor',
                validation_rules={'max_length': 100}
            ),
            'editor.line_height': SettingDefinition(
                key='editor.line_height',
                default_value=1.6,
                value_type='float',
                description='Editor line height',
                category='editor',
                validation_rules={'min': 1.2, 'max': 2.0}
            ),
            'editor.show_word_count': SettingDefinition(
                key='editor.show_word_count',
                default_value=True,
                value_type='boolean',
                description='Show word count in editor',
                category='editor'
            ),
            'editor.markdown_preview': SettingDefinition(
                key='editor.markdown_preview',
                default_value=True,
                value_type='boolean',
                description='Enable markdown preview',
                category='editor'
            ),
            'editor.default_template': SettingDefinition(
                key='editor.default_template',
                default_value='# {date}\n\n## Tasks\n\n## Notes\n\n## Reflections\n\n',
                value_type='string',
                description='Default template for new journal entries ({date} will be replaced)',
                category='editor',
                validation_rules={'max_length': 1000}
            ),
            
            # UI Settings
            'ui.theme': SettingDefinition(
                key='ui.theme',
                default_value='light',
                value_type='string',
                description='UI theme preference',
                category='ui',
                validation_rules={'options': ['light', 'dark', 'auto']}
            ),
            'ui.compact_mode': SettingDefinition(
                key='ui.compact_mode',
                default_value=False,
                value_type='boolean',
                description='Use compact UI layout',
                category='ui'
            ),
            'ui.animations_enabled': SettingDefinition(
                key='ui.animations_enabled',
                default_value=True,
                value_type='boolean',
                description='Enable UI animations',
                category='ui'
            ),
            'ui.sidebar_collapsed': SettingDefinition(
                key='ui.sidebar_collapsed',
                default_value=False,
                value_type='boolean',
                description='Start with sidebar collapsed',
                category='ui'
            ),
            
            # Calendar Settings
            'calendar.start_week_on': SettingDefinition(
                key='calendar.start_week_on',
                default_value=0,
                value_type='integer',
                description='First day of week (0=Sunday, 1=Monday)',
                category='calendar',
                validation_rules={'min': 0, 'max': 6}
            ),
            'calendar.show_week_numbers': SettingDefinition(
                key='calendar.show_week_numbers',
                default_value=False,
                value_type='boolean',
                description='Show week numbers in calendar',
                category='calendar'
            ),
            'calendar.highlight_today': SettingDefinition(
                key='calendar.highlight_today',
                default_value=True,
                value_type='boolean',
                description='Highlight today\'s date in calendar',
                category='calendar'
            ),
            
            # Backup Settings
            'backup.auto_backup': SettingDefinition(
                key='backup.auto_backup',
                default_value=True,
                value_type='boolean',
                description='Enable automatic backups',
                category='backup'
            ),
            'backup.backup_interval_days': SettingDefinition(
                key='backup.backup_interval_days',
                default_value=7,
                value_type='integer',
                description='Backup interval in days',
                category='backup',
                validation_rules={'min': 1, 'max': 30}
            ),
            'backup.max_backups': SettingDefinition(
                key='backup.max_backups',
                default_value=10,
                value_type='integer',
                description='Maximum number of backups to keep',
                category='backup',
                validation_rules={'min': 5, 'max': 50}
            ),
            'backup.include_database': SettingDefinition(
                key='backup.include_database',
                default_value=True,
                value_type='boolean',
                description='Include database in backups',
                category='backup'
            ),
            
            # LLM Settings (Read-only, for display purposes)
            'llm.provider': SettingDefinition(
                key='llm.provider',
                default_value=self.config.llm.provider,
                value_type='string',
                description='Current LLM provider (configured via CLI config)',
                category='llm',
                validation_rules={'readonly': True}
            ),
            'llm.timeout_seconds': SettingDefinition(
                key='llm.timeout_seconds',
                default_value=getattr(self.config.llm, 'timeout_seconds', 120),
                value_type='integer',
                description='LLM request timeout in seconds',
                category='llm',
                validation_rules={'min': 30, 'max': 300}
            )
        }
    
    async def get_all_settings(self) -> Dict[str, WebSettingResponse]:
        """Get all web settings with their current values."""
        try:
            settings = {}
            
            async with self.db_manager.get_session() as session:
                # Get all settings from database
                stmt = select(WebSettings)
                result = await session.execute(stmt)
                db_settings = result.scalars().all()
                
                # Create lookup for existing settings
                db_lookup = {setting.key: setting for setting in db_settings}
                
                # Process all defined settings
                for key, definition in self.setting_definitions.items():
                    if key in db_lookup:
                        # Use database value
                        db_setting = db_lookup[key]
                        parsed_value = self._parse_setting_value(
                            db_setting.value, db_setting.value_type
                        )
                        
                        settings[key] = WebSettingResponse(
                            id=db_setting.id,
                            key=db_setting.key,
                            value=db_setting.value,
                            value_type=db_setting.value_type,
                            description=db_setting.description or definition.description,
                            parsed_value=parsed_value,
                            created_at=db_setting.created_at,
                            modified_at=db_setting.modified_at
                        )
                    else:
                        # Use default value and create database entry
                        await self._create_default_setting(session, definition)
                        
                        settings[key] = WebSettingResponse(
                            id=0,  # Will be updated after creation
                            key=definition.key,
                            value=str(definition.default_value),
                            value_type=definition.value_type,
                            description=definition.description,
                            parsed_value=definition.default_value,
                            created_at=datetime.now(timezone.utc),
                            modified_at=datetime.now(timezone.utc)
                        )
                
                await session.commit()
            
            return settings
            
        except Exception as e:
            self.logger.logger.error(f"Failed to get all settings: {str(e)}", ErrorCategory.DATABASE_ERROR)
            raise
    
    async def get_setting(self, key: str) -> Optional[WebSettingResponse]:
        """Get a specific setting by key."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = select(WebSettings).where(WebSettings.key == key)
                result = await session.execute(stmt)
                db_setting = result.scalar_one_or_none()
                
                if db_setting:
                    parsed_value = self._parse_setting_value(
                        db_setting.value, db_setting.value_type
                    )
                    
                    return WebSettingResponse(
                        id=db_setting.id,
                        key=db_setting.key,
                        value=db_setting.value,
                        value_type=db_setting.value_type,
                        description=db_setting.description,
                        parsed_value=parsed_value,
                        created_at=db_setting.created_at,
                        modified_at=db_setting.modified_at
                    )
                
                # Return default if not found
                if key in self.setting_definitions:
                    definition = self.setting_definitions[key]
                    return WebSettingResponse(
                        id=0,
                        key=definition.key,
                        value=str(definition.default_value),
                        value_type=definition.value_type,
                        description=definition.description,
                        parsed_value=definition.default_value,
                        created_at=datetime.now(timezone.utc),
                        modified_at=datetime.now(timezone.utc)
                    )
                
                return None
                
        except Exception as e:
            self.logger.logger.error(f"Failed to get setting {key}: {str(e)}")
            return None
    
    async def update_setting(self, key: str, value: str) -> Optional[WebSettingResponse]:
        """Update a setting value."""
        try:
            # Validate setting exists and value is valid
            if key not in self.setting_definitions:
                raise ValueError(f"Unknown setting: {key}")
            
            definition = self.setting_definitions[key]
            
            # Check if setting is read-only
            if definition.validation_rules and definition.validation_rules.get('readonly', False):
                raise ValueError(f"Setting {key} is read-only")
            
            parsed_value = self._parse_setting_value(value, definition.value_type)
            
            # Validate value
            if not self._validate_setting_value(parsed_value, definition):
                raise ValueError(f"Invalid value for setting {key}")
            
            # Special handling for filesystem paths
            if key.startswith('filesystem.') and key.endswith('_path'):
                await self._validate_and_create_path(parsed_value, definition)
            
            async with self.db_manager.get_session() as session:
                # Check if setting exists
                stmt = select(WebSettings).where(WebSettings.key == key)
                result = await session.execute(stmt)
                existing_setting = result.scalar_one_or_none()
                
                if existing_setting:
                    # Update existing setting
                    update_stmt = (
                        update(WebSettings)
                        .where(WebSettings.key == key)
                        .values(
                            value=value,
                            modified_at=datetime.now(timezone.utc)
                        )
                    )
                    await session.execute(update_stmt)
                    
                    # Return updated setting
                    updated_setting = await session.scalar(
                        select(WebSettings).where(WebSettings.key == key)
                    )
                    
                else:
                    # Create new setting
                    new_setting = WebSettings(
                        key=key,
                        value=value,
                        value_type=definition.value_type,
                        description=definition.description,
                        created_at=datetime.now(timezone.utc),
                        modified_at=datetime.now(timezone.utc)
                    )
                    session.add(new_setting)
                    await session.flush()
                    updated_setting = new_setting
                
                await session.commit()
                
                # Update CLI config if this is a core setting
                if definition.requires_restart:
                    await self._sync_to_cli_config(key, parsed_value)
                
                return WebSettingResponse(
                    id=updated_setting.id,
                    key=updated_setting.key,
                    value=updated_setting.value,
                    value_type=updated_setting.value_type,
                    description=updated_setting.description,
                    parsed_value=parsed_value,
                    created_at=updated_setting.created_at,
                    modified_at=updated_setting.modified_at
                )
                
        except Exception as e:
            self.logger.logger.error(f"Failed to update setting {key}: {str(e)}")
            raise
    
    async def _validate_and_create_path(self, path_value: str, definition: SettingDefinition):
        """Validate and optionally create filesystem paths."""
        try:
            path = Path(path_value).expanduser()  # Handle ~ expansion
            
            # Check if path is absolute or make it relative to current working directory
            if not path.is_absolute():
                path = Path.cwd() / path
            
            # For now, just validate the path format - don't auto-create during validation
            # This avoids circular dependency issues during setting updates
            self.logger.logger.info(f"Validating path: {path}")
            
            # Basic path validation - ensure it's a valid path format
            if not str(path).strip():
                raise ValueError("Path cannot be empty")
                
        except Exception as e:
            self.logger.logger.error(f"Failed to validate path {path_value}: {str(e)}")
            raise ValueError(f"Invalid path: {path_value}")
    
    async def _sync_to_cli_config(self, key: str, value: Any):
        """Sync critical settings back to CLI configuration."""
        try:
            # Map web settings to CLI config paths
            cli_mapping = {
                'filesystem.base_path': 'processing.base_path',
                'filesystem.output_path': 'processing.output_path',
                'filesystem.max_file_size_mb': 'processing.max_file_size_mb',
                'llm.timeout_seconds': 'llm.timeout_seconds'
            }
            
            if key in cli_mapping:
                # This would require extending ConfigManager to support runtime updates
                # For now, log the change and note that restart is required
                self.logger.logger.info(f"Setting {key} changed to {value}. Restart required for CLI compatibility.")
                
        except Exception as e:
            self.logger.logger.error(f"Failed to sync setting {key} to CLI config: {str(e)}")
    
    async def bulk_update_settings(self, settings: Dict[str, Any]) -> SettingsBulkUpdateResponse:
        """Update multiple settings at once."""
        try:
            updated_settings = {}
            validation_errors = []
            
            for key, value in settings.items():
                try:
                    updated_setting = await self.update_setting(key, str(value))
                    if updated_setting:
                        updated_settings[key] = updated_setting
                except Exception as e:
                    validation_errors.append(SettingsValidationError(
                        key=key,
                        error=str(e),
                        current_value=value,
                        expected_type=self.setting_definitions.get(key, {}).value_type if key in self.setting_definitions else "unknown"
                    ))
            
            return SettingsBulkUpdateResponse(
                updated_settings=updated_settings,
                validation_errors=validation_errors,
                success_count=len(updated_settings),
                error_count=len(validation_errors)
            )
            
        except Exception as e:
            self.logger.logger.error(f"Failed to bulk update settings: {str(e)}")
            raise
    
    async def reset_setting(self, key: str) -> Optional[WebSettingResponse]:
        """Reset a setting to its default value."""
        if key not in self.setting_definitions:
            raise ValueError(f"Unknown setting: {key}")
        
        definition = self.setting_definitions[key]
        return await self.update_setting(key, str(definition.default_value))
    
    async def reset_all_settings(self) -> Dict[str, WebSettingResponse]:
        """Reset all settings to their default values."""
        try:
            reset_settings = {}
            
            for key, definition in self.setting_definitions.items():
                try:
                    # Skip read-only settings
                    if definition.validation_rules and definition.validation_rules.get('readonly', False):
                        continue
                        
                    reset_setting = await self.reset_setting(key)
                    if reset_setting:
                        reset_settings[key] = reset_setting
                except Exception as e:
                    self.logger.logger.error(f"Failed to reset setting {key}: {str(e)}")
            
            return reset_settings
            
        except Exception as e:
            self.logger.logger.error(f"Failed to reset all settings: {str(e)}")
            raise
    
    async def export_settings(self) -> SettingsExport:
        """Export all settings for backup or transfer."""
        try:
            settings = await self.get_all_settings()
            
            export_data = {
                'version': '1.0',
                'exported_at': datetime.now(timezone.utc).isoformat(),
                'settings': {
                    key: {
                        'value': setting.parsed_value,
                        'type': setting.value_type,
                        'description': setting.description
                    }
                    for key, setting in settings.items()
                    # Exclude read-only settings from export
                    if not (key in self.setting_definitions and 
                           self.setting_definitions[key].validation_rules and 
                           self.setting_definitions[key].validation_rules.get('readonly', False))
                }
            }
            
            return SettingsExport(
                version=export_data['version'],
                exported_at=export_data['exported_at'],
                settings=export_data['settings']
            )
            
        except Exception as e:
            self.logger.logger.error(f"Failed to export settings: {str(e)}")
            raise
    
    async def import_settings(self, settings_data: Dict[str, Any]) -> Dict[str, WebSettingResponse]:
        """Import settings from exported data."""
        try:
            imported_settings = {}
            
            if 'settings' not in settings_data:
                raise ValueError("Invalid settings export format")
            
            for key, setting_data in settings_data['settings'].items():
                try:
                    if key in self.setting_definitions:
                        # Skip read-only settings
                        definition = self.setting_definitions[key]
                        if definition.validation_rules and definition.validation_rules.get('readonly', False):
                            continue
                            
                        value = setting_data.get('value')
                        if value is not None:
                            imported_setting = await self.update_setting(key, str(value))
                            if imported_setting:
                                imported_settings[key] = imported_setting
                except Exception as e:
                    self.logger.logger.error(f"Failed to import setting {key}: {str(e)}")
            
            return imported_settings
            
        except Exception as e:
            self.logger.logger.error(f"Failed to import settings: {str(e)}")
            raise
    
    def get_setting_categories(self) -> Dict[str, List[str]]:
        """Get settings organized by category."""
        categories = {}
        
        for key, definition in self.setting_definitions.items():
            category = definition.category
            if category not in categories:
                categories[category] = []
            categories[category].append(key)
        
        return categories
    
    def _parse_setting_value(self, value: str, value_type: str) -> Any:
        """Parse string value to appropriate type."""
        try:
            if value_type == 'boolean':
                return value.lower() in ('true', '1', 'yes', 'on')
            elif value_type == 'integer':
                return int(value)
            elif value_type == 'float':
                return float(value)
            elif value_type == 'json':
                return json.loads(value)
            else:  # string
                return value
        except Exception:
            # Return original value if parsing fails
            return value
    
    def _validate_setting_value(self, value: Any, definition: SettingDefinition) -> bool:
        """Validate a setting value against its definition."""
        if not definition.validation_rules:
            return True
        
        rules = definition.validation_rules
        
        # Check if read-only
        if rules.get('readonly', False):
            return False
        
        # Check minimum value
        if 'min' in rules and isinstance(value, (int, float)):
            if value < rules['min']:
                return False
        
        # Check maximum value
        if 'max' in rules and isinstance(value, (int, float)):
            if value > rules['max']:
                return False
        
        # Check allowed options
        if 'options' in rules:
            if value not in rules['options']:
                return False
        
        # Check string length
        if 'max_length' in rules and isinstance(value, str):
            if len(value) > rules['max_length']:
                return False
        
        # Check path validation
        if 'path_must_exist' in rules and isinstance(value, str):
            path = Path(value)
            if rules['path_must_exist'] and not path.exists():
                return False
        
        return True
    
    async def _create_default_setting(self, session, definition: SettingDefinition):
        """Create a default setting in the database."""
        try:
            new_setting = WebSettings(
                key=definition.key,
                value=str(definition.default_value),
                value_type=definition.value_type,
                description=definition.description,
                created_at=datetime.now(timezone.utc),
                modified_at=datetime.now(timezone.utc)
            )
            session.add(new_setting)
            
        except Exception as e:
            self.logger.logger.error(f"Failed to create default setting {definition.key}: {str(e)}")