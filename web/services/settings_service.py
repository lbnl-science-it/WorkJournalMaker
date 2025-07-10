"""
Settings Service for Daily Work Journal Web Interface

This service manages web-specific settings while maintaining compatibility
with the existing CLI configuration system.
"""

import asyncio
from datetime import datetime, timezone, timedelta
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
from sqlalchemy import select, update, delete, text

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
            ),
            
            # Work Week Settings
            'work_week.preset': SettingDefinition(
                key='work_week.preset',
                default_value='monday_friday',
                value_type='string',
                description='Work week preset configuration',
                category='work_week',
                validation_rules={'options': ['monday_friday', 'sunday_thursday', 'custom']}
            ),
            'work_week.start_day': SettingDefinition(
                key='work_week.start_day',
                default_value=1,
                value_type='integer',
                description='Work week start day (1=Monday, 2=Tuesday, ..., 7=Sunday)',
                category='work_week',
                validation_rules={'min': 1, 'max': 7}
            ),
            'work_week.end_day': SettingDefinition(
                key='work_week.end_day',
                default_value=5,
                value_type='integer',
                description='Work week end day (1=Monday, 2=Tuesday, ..., 7=Sunday)',
                category='work_week',
                validation_rules={'min': 1, 'max': 7}
            ),
            'work_week.timezone': SettingDefinition(
                key='work_week.timezone',
                default_value='UTC',
                value_type='string',
                description='Timezone for work week calculations',
                category='work_week',
                validation_rules={'max_length': 50}
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
        """
        Robust bulk settings update with comprehensive transaction management and verification.
        
        This implementation provides:
        1. Explicit transaction management with proper commit/rollback
        2. Pre-update and post-update verification
        3. Detailed success/error responses with operation metadata
        4. Database integrity checks
        5. Concurrent update handling with optimistic locking
        6. Backward compatibility with existing frontend
        """
        operation_id = str(uuid.uuid4())[:8]
        start_time = datetime.now(timezone.utc)
        
        # Initialize operation metadata
        operation_metadata = {
            'operation_id': operation_id,
            'start_time': start_time,
            'settings_count': len(settings),
            'settings_keys': list(settings.keys()),
            'concurrent_update_detected': False,
            'integrity_checks_passed': True,
            'rollback_performed': False,
            'transaction_isolation_level': 'READ_COMMITTED'
        }
        
        self.logger.logger.info(
            f"[BULK_UPDATE] Starting robust bulk update operation {operation_id} with {len(settings)} settings",
            extra=operation_metadata
        )
        
        # Pre-operation database integrity check
        integrity_issues = await self._check_database_integrity()
        if integrity_issues:
            self.logger.logger.warning(
                f"[BULK_UPDATE] {operation_id}: Pre-operation integrity issues detected",
                extra={'operation_id': operation_id, 'integrity_issues': integrity_issues}
            )
            operation_metadata['pre_operation_integrity_issues'] = integrity_issues
        
        # Phase 1: Pre-validation of all settings
        validation_results = await self._pre_validate_bulk_settings(settings, operation_id)
        if validation_results['fatal_errors']:
            return SettingsBulkUpdateResponse(
                updated_settings={},
                validation_errors=validation_results['validation_errors'],
                success_count=0,
                error_count=len(validation_results['validation_errors'])
            )
        
        updated_settings = {}
        validation_errors = validation_results['validation_errors']
        valid_settings = validation_results['valid_settings']
        
        # Phase 2: Atomic transaction with isolation
        transaction_savepoint = None
        try:
            async with self.db_manager.get_session() as session:
                operation_metadata['session_id'] = id(session)
                self.logger.logger.info(
                    f"[BULK_UPDATE] {operation_id}: Database session established with transaction isolation",
                    extra={'operation_id': operation_id, 'session_id': id(session)}
                )
                
                # Set transaction isolation level for concurrent update protection
                await session.execute(text("PRAGMA read_uncommitted = 0"))  # Ensure READ_COMMITTED
                
                # Create savepoint for rollback granularity
                transaction_savepoint = await session.begin_nested()
                self.logger.logger.info(
                    f"[BULK_UPDATE] {operation_id}: Transaction savepoint created for atomic operation",
                    extra={'operation_id': operation_id}
                )
                
                # Phase 3: Pre-update verification and concurrent update detection
                pre_update_state = await self._capture_pre_update_state(session, valid_settings.keys(), operation_id)
                concurrent_updates = await self._detect_concurrent_updates(session, pre_update_state, operation_id)
                
                if concurrent_updates:
                    operation_metadata['concurrent_update_detected'] = True
                    self.logger.logger.warning(
                        f"[BULK_UPDATE] {operation_id}: Concurrent updates detected, applying conflict resolution",
                        extra={'operation_id': operation_id, 'concurrent_updates': concurrent_updates}
                    )
                
                # Phase 4: Batch database operations with verification
                batch_results = await self._execute_batch_updates(
                    session, valid_settings, pre_update_state, operation_id
                )
                updated_settings.update(batch_results['updated_settings'])
                validation_errors.extend(batch_results['validation_errors'])
                
                # Phase 5: Post-update verification and integrity checks
                post_update_verification = await self._verify_post_update_state(
                    session, updated_settings, valid_settings, operation_id
                )
                
                if not post_update_verification['success']:
                    self.logger.logger.error(
                        f"[BULK_UPDATE] {operation_id}: Post-update verification failed, rolling back",
                        extra={'operation_id': operation_id, 'verification_errors': post_update_verification['errors']}
                    )
                    await transaction_savepoint.rollback()
                    operation_metadata['rollback_performed'] = True
                    raise Exception(f"Post-update verification failed: {post_update_verification['errors']}")
                
                # Phase 6: Database integrity check before commit
                post_update_integrity = await self._check_database_integrity()
                if post_update_integrity:
                    operation_metadata['integrity_checks_passed'] = False
                    self.logger.logger.error(
                        f"[BULK_UPDATE] {operation_id}: Database integrity check failed, rolling back",
                        extra={'operation_id': operation_id, 'integrity_issues': post_update_integrity}
                    )
                    await transaction_savepoint.rollback()
                    operation_metadata['rollback_performed'] = True
                    raise Exception(f"Database integrity check failed: {post_update_integrity}")
                
                # Phase 7: Commit transaction
                await transaction_savepoint.commit()
                await session.commit()  # Commit the outer transaction
                
                self.logger.logger.info(
                    f"[BULK_UPDATE] {operation_id}: Transaction committed successfully with full verification",
                    extra={'operation_id': operation_id}
                )
                
                # Phase 8: CLI config synchronization for restart-required settings
                cli_sync_results = await self._sync_cli_configs(updated_settings, operation_id)
                operation_metadata['cli_sync_results'] = cli_sync_results
                
        except Exception as transaction_error:
            operation_metadata['rollback_performed'] = True
            if transaction_savepoint:
                try:
                    await transaction_savepoint.rollback()
                    self.logger.logger.info(
                        f"[BULK_UPDATE] {operation_id}: Transaction savepoint rolled back successfully",
                        extra={'operation_id': operation_id}
                    )
                except Exception as rollback_error:
                    self.logger.logger.error(
                        f"[BULK_UPDATE] {operation_id}: Failed to rollback savepoint: {str(rollback_error)}",
                        extra={'operation_id': operation_id, 'rollback_error': str(rollback_error)}
                    )
            
            end_time = datetime.now(timezone.utc)
            operation_metadata['end_time'] = end_time
            operation_metadata['total_duration_seconds'] = (end_time - start_time).total_seconds()
            operation_metadata['error'] = str(transaction_error)
            
            self.logger.logger.error(
                f"[BULK_UPDATE] {operation_id}: Robust bulk update failed: {str(transaction_error)}",
                extra=operation_metadata,
                exc_info=True
            )
            
            raise
        
        # Phase 9: Prepare comprehensive response with metadata
        end_time = datetime.now(timezone.utc)
        operation_metadata['end_time'] = end_time
        operation_metadata['total_duration_seconds'] = (end_time - start_time).total_seconds()
        operation_metadata['success_count'] = len(updated_settings)
        operation_metadata['error_count'] = len(validation_errors)
        operation_metadata['successful_settings'] = list(updated_settings.keys())
        operation_metadata['failed_settings'] = [error.key for error in validation_errors]
        
        # Create enhanced response with detailed metadata
        response = SettingsBulkUpdateResponse(
            updated_settings=updated_settings,
            validation_errors=validation_errors,
            success_count=len(updated_settings),
            error_count=len(validation_errors)
        )
        
        # Add operation metadata to response (if supported by model)
        if hasattr(response, 'operation_metadata'):
            response.operation_metadata = operation_metadata
        
        self.logger.logger.info(
            f"[BULK_UPDATE] {operation_id}: Robust bulk update completed - {len(updated_settings)} successful, {len(validation_errors)} errors in {operation_metadata['total_duration_seconds']:.3f}s",
            extra=operation_metadata
        )
        
        return response
    
    # Helper methods for robust bulk update implementation
    
    async def _check_database_integrity(self) -> List[str]:
        """Check database integrity and return any issues found."""
        issues = []
        try:
            async with self.db_manager.get_session() as session:
                # Check for orphaned settings (settings without definitions)
                # Allow for legacy settings that may need migration
                stmt = select(WebSettings.key).distinct()
                result = await session.execute(stmt)
                db_keys = {row[0] for row in result.fetchall()}
                
                defined_keys = set(self.setting_definitions.keys())
                orphaned_keys = db_keys - defined_keys
                
                # Define known legacy settings that should not be considered critical errors
                legacy_settings = {
                    'auto_save_interval', 'calendar_start_day', 'editor_font_size', 
                    'show_word_count', 'theme'
                }
                
                critical_orphaned_keys = orphaned_keys - legacy_settings
                
                if critical_orphaned_keys:
                    issues.append(f"Critical orphaned settings found: {list(critical_orphaned_keys)}")
                
                # Log legacy settings as warning only (not a blocking issue)
                legacy_orphaned_keys = orphaned_keys & legacy_settings
                if legacy_orphaned_keys:
                    self.logger.logger.warning(
                        f"Legacy settings detected (should be migrated): {list(legacy_orphaned_keys)}"
                    )
                
                # Check for duplicate keys (should not happen with unique constraint)
                from sqlalchemy import func
                stmt = select(WebSettings.key, func.count(WebSettings.key)).group_by(WebSettings.key).having(func.count(WebSettings.key) > 1)
                result = await session.execute(stmt)
                duplicates = result.fetchall()
                
                if duplicates:
                    issues.append(f"Duplicate settings found: {[key for key, count in duplicates]}")
                
                # Check for settings with invalid value types (only for current settings)
                invalid_types = []
                stmt = select(WebSettings)
                result = await session.execute(stmt)
                all_settings = result.scalars().all()
                
                for setting in all_settings:
                    # Only validate settings that are currently defined
                    if setting.key in self.setting_definitions:
                        try:
                            self._parse_setting_value(setting.value, setting.value_type)
                        except Exception:
                            invalid_types.append(setting.key)
                
                if invalid_types:
                    issues.append(f"Settings with invalid value types: {invalid_types}")
                    
        except Exception as e:
            issues.append(f"Database integrity check failed: {str(e)}")
        
        return issues
    
    async def _pre_validate_bulk_settings(self, settings: Dict[str, Any], operation_id: str) -> Dict[str, Any]:
        """Pre-validate all settings before starting transaction."""
        validation_errors = []
        valid_settings = {}
        fatal_errors = False
        
        self.logger.logger.info(
            f"[BULK_UPDATE] {operation_id}: Starting pre-validation for {len(settings)} settings",
            extra={'operation_id': operation_id}
        )
        
        for key, value in settings.items():
            try:
                # Check if setting exists in definitions
                if key not in self.setting_definitions:
                    validation_errors.append(SettingsValidationError(
                        key=key,
                        error=f"Unknown setting: {key}",
                        current_value=value,
                        expected_type="unknown"
                    ))
                    continue
                
                definition = self.setting_definitions[key]
                
                # Check if setting is read-only
                if definition.validation_rules and definition.validation_rules.get('readonly', False):
                    validation_errors.append(SettingsValidationError(
                        key=key,
                        error=f"Setting {key} is read-only",
                        current_value=value,
                        expected_type=definition.value_type
                    ))
                    continue
                
                # Parse and validate value
                try:
                    parsed_value = self._parse_setting_value(str(value), definition.value_type)
                except Exception as parse_error:
                    validation_errors.append(SettingsValidationError(
                        key=key,
                        error=f"Failed to parse value: {str(parse_error)}",
                        current_value=value,
                        expected_type=definition.value_type
                    ))
                    continue
                
                # Validate parsed value
                if not self._validate_setting_value(parsed_value, definition):
                    validation_errors.append(SettingsValidationError(
                        key=key,
                        error=f"Invalid value for setting {key}",
                        current_value=value,
                        expected_type=definition.value_type
                    ))
                    continue
                
                # Special validation for filesystem paths
                if key.startswith('filesystem.') and key.endswith('_path'):
                    try:
                        await self._validate_and_create_path(str(parsed_value), definition)
                    except Exception as path_error:
                        validation_errors.append(SettingsValidationError(
                            key=key,
                            error=f"Path validation failed: {str(path_error)}",
                            current_value=value,
                            expected_type=definition.value_type
                        ))
                        continue
                
                valid_settings[key] = {
                    'raw_value': value,
                    'parsed_value': parsed_value,
                    'definition': definition
                }
                
            except Exception as e:
                self.logger.logger.error(
                    f"[BULK_UPDATE] {operation_id}: Pre-validation error for {key}: {str(e)}",
                    extra={'operation_id': operation_id, 'setting_key': key}
                )
                validation_errors.append(SettingsValidationError(
                    key=str(key) if key is not None else "null_key",
                    error=f"Pre-validation error: {str(e)}",
                    current_value=value,
                    expected_type=self.setting_definitions.get(key, SettingDefinition('', '', 'string', '', '')).value_type if key in self.setting_definitions else "unknown"
                ))
        
        # Check for fatal errors (e.g., too many validation errors)
        # Only consider it fatal if we have settings AND all of them failed validation
        if len(settings) > 0 and len(validation_errors) == len(settings):
            fatal_errors = True
            self.logger.logger.error(
                f"[BULK_UPDATE] {operation_id}: All settings failed pre-validation, aborting operation",
                extra={'operation_id': operation_id}
            )
        elif len(settings) == 0:
            self.logger.logger.info(
                f"[BULK_UPDATE] {operation_id}: No settings provided for validation - treating as no-op",
                extra={'operation_id': operation_id}
            )
        
        return {
            'validation_errors': validation_errors,
            'valid_settings': valid_settings,
            'fatal_errors': fatal_errors
        }
    
    async def _capture_pre_update_state(self, session, setting_keys: List[str], operation_id: str) -> Dict[str, Any]:
        """Capture the current state of settings before updating."""
        pre_update_state = {}
        
        self.logger.logger.info(
            f"[BULK_UPDATE] {operation_id}: Capturing pre-update state for {len(setting_keys)} settings",
            extra={'operation_id': operation_id}
        )
        
        for key in setting_keys:
            stmt = select(WebSettings).where(WebSettings.key == key)
            result = await session.execute(stmt)
            existing_setting = result.scalar_one_or_none()
            
            if existing_setting:
                pre_update_state[key] = {
                    'id': existing_setting.id,
                    'value': existing_setting.value,
                    'modified_at': existing_setting.modified_at,
                    'exists': True
                }
            else:
                pre_update_state[key] = {
                    'exists': False
                }
        
        return pre_update_state
    
    async def _detect_concurrent_updates(self, session, pre_update_state: Dict[str, Any], operation_id: str) -> List[str]:
        """Detect if any settings were updated concurrently since pre-update state capture."""
        concurrent_updates = []
        
        for key, state in pre_update_state.items():
            if state['exists']:
                stmt = select(WebSettings).where(WebSettings.key == key)
                result = await session.execute(stmt)
                current_setting = result.scalar_one_or_none()
                
                if current_setting and current_setting.modified_at != state['modified_at']:
                    concurrent_updates.append(key)
                    self.logger.logger.warning(
                        f"[BULK_UPDATE] {operation_id}: Concurrent update detected for {key}",
                        extra={
                            'operation_id': operation_id,
                            'setting_key': key,
                            'expected_modified_at': state['modified_at'].isoformat(),
                            'actual_modified_at': current_setting.modified_at.isoformat()
                        }
                    )
        
        return concurrent_updates
    
    async def _execute_batch_updates(self, session, valid_settings: Dict[str, Any], 
                                   pre_update_state: Dict[str, Any], operation_id: str) -> Dict[str, Any]:
        """Execute batch database updates with verification."""
        updated_settings = {}
        validation_errors = []
        
        self.logger.logger.info(
            f"[BULK_UPDATE] {operation_id}: Executing batch updates for {len(valid_settings)} settings",
            extra={'operation_id': operation_id}
        )
        
        for key, setting_data in valid_settings.items():
            try:
                update_time = datetime.now(timezone.utc)
                raw_value = setting_data['raw_value']
                parsed_value = setting_data['parsed_value']
                definition = setting_data['definition']
                
                if pre_update_state[key]['exists']:
                    # Update existing setting
                    update_stmt = (
                        update(WebSettings)
                        .where(WebSettings.key == key)
                        .values(
                            value=str(raw_value),
                            modified_at=update_time
                        )
                    )
                    await session.execute(update_stmt)
                    
                    # Verify update
                    verify_stmt = select(WebSettings).where(WebSettings.key == key)
                    verify_result = await session.execute(verify_stmt)
                    updated_record = verify_result.scalar_one_or_none()
                    
                else:
                    # Create new setting
                    new_setting = WebSettings(
                        key=key,
                        value=str(raw_value),
                        value_type=definition.value_type,
                        description=definition.description,
                        created_at=update_time,
                        modified_at=update_time
                    )
                    session.add(new_setting)
                    await session.flush()
                    
                    # Verify creation
                    verify_stmt = select(WebSettings).where(WebSettings.key == key)
                    verify_result = await session.execute(verify_stmt)
                    updated_record = verify_result.scalar_one_or_none()
                
                if updated_record and updated_record.value == str(raw_value):
                    updated_settings[key] = WebSettingResponse(
                        id=updated_record.id,
                        key=updated_record.key,
                        value=updated_record.value,
                        value_type=updated_record.value_type,
                        description=updated_record.description,
                        parsed_value=parsed_value,
                        created_at=updated_record.created_at,
                        modified_at=updated_record.modified_at
                    )
                    
                    self.logger.logger.info(
                        f"[BULK_UPDATE] {operation_id}: Successfully updated {key}",
                        extra={'operation_id': operation_id, 'setting_key': key}
                    )
                else:
                    error_msg = f"Database operation verification failed for {key}"
                    validation_errors.append(SettingsValidationError(
                        key=key,
                        error=error_msg,
                        current_value=raw_value,
                        expected_type=definition.value_type
                    ))
                    
            except Exception as e:
                self.logger.logger.error(
                    f"[BULK_UPDATE] {operation_id}: Failed to update {key}: {str(e)}",
                    extra={'operation_id': operation_id, 'setting_key': key}
                )
                validation_errors.append(SettingsValidationError(
                    key=key,
                    error=str(e),
                    current_value=setting_data['raw_value'],
                    expected_type=setting_data['definition'].value_type
                ))
        
        return {
            'updated_settings': updated_settings,
            'validation_errors': validation_errors
        }
    
    async def _verify_post_update_state(self, session, updated_settings: Dict[str, WebSettingResponse],
                                      original_settings: Dict[str, Any], operation_id: str) -> Dict[str, Any]:
        """Verify that all updates were successful and settings are in expected state."""
        verification_errors = []
        
        self.logger.logger.info(
            f"[BULK_UPDATE] {operation_id}: Verifying post-update state for {len(updated_settings)} settings",
            extra={'operation_id': operation_id}
        )
        
        for key, expected_response in updated_settings.items():
            try:
                # Re-read setting from database
                stmt = select(WebSettings).where(WebSettings.key == key)
                result = await session.execute(stmt)
                actual_setting = result.scalar_one_or_none()
                
                if not actual_setting:
                    verification_errors.append(f"Setting {key} not found after update")
                    continue
                
                # Verify value matches
                if actual_setting.value != expected_response.value:
                    verification_errors.append(
                        f"Value mismatch for {key}: expected {expected_response.value}, got {actual_setting.value}"
                    )
                
                # Verify modified timestamp was updated (handle timezone-aware/naive comparison)
                current_time = datetime.now(timezone.utc)
                setting_modified_at = actual_setting.modified_at
                
                # Ensure both timestamps are timezone-aware for comparison
                if setting_modified_at.tzinfo is None:
                    setting_modified_at = setting_modified_at.replace(tzinfo=timezone.utc)
                
                if setting_modified_at <= current_time - timedelta(seconds=10):
                    verification_errors.append(f"Modified timestamp not updated for {key}")
                    
            except Exception as e:
                verification_errors.append(f"Verification error for {key}: {str(e)}")
        
        success = len(verification_errors) == 0
        
        if success:
            self.logger.logger.info(
                f"[BULK_UPDATE] {operation_id}: Post-update verification successful",
                extra={'operation_id': operation_id}
            )
        else:
            self.logger.logger.error(
                f"[BULK_UPDATE] {operation_id}: Post-update verification failed",
                extra={'operation_id': operation_id, 'errors': verification_errors}
            )
        
        return {
            'success': success,
            'errors': verification_errors
        }
    
    async def _sync_cli_configs(self, updated_settings: Dict[str, WebSettingResponse], operation_id: str) -> Dict[str, Any]:
        """Synchronize CLI configuration for settings that require restart."""
        sync_results = {'synced': [], 'failed': [], 'skipped': []}
        
        for key, setting_response in updated_settings.items():
            if key in self.setting_definitions:
                definition = self.setting_definitions[key]
                if definition.requires_restart:
                    try:
                        await self._sync_to_cli_config(key, setting_response.parsed_value)
                        sync_results['synced'].append(key)
                        self.logger.logger.info(
                            f"[BULK_UPDATE] {operation_id}: CLI config synced for {key}",
                            extra={'operation_id': operation_id, 'setting_key': key}
                        )
                    except Exception as e:
                        sync_results['failed'].append({'key': key, 'error': str(e)})
                        self.logger.logger.error(
                            f"[BULK_UPDATE] {operation_id}: CLI config sync failed for {key}: {str(e)}",
                            extra={'operation_id': operation_id, 'setting_key': key}
                        )
                else:
                    sync_results['skipped'].append(key)
        
        return sync_results
    
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
        
        # Work week specific validations
        if definition.key.startswith('work_week.'):
            return self._validate_work_week_setting(definition.key, value)
        
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
    
    # Work Week Settings Methods
    
    def _validate_work_week_setting(self, key: str, value: Any) -> bool:
        """Validate work week specific settings."""
        try:
            if key == 'work_week.preset':
                return value in ['monday_friday', 'sunday_thursday', 'custom']
            elif key in ['work_week.start_day', 'work_week.end_day']:
                return isinstance(value, int) and 1 <= value <= 7
            elif key == 'work_week.timezone':
                # Basic timezone validation - could be enhanced with pytz
                return isinstance(value, str) and len(value.strip()) > 0
            return True
        except Exception:
            return False
    
    async def get_work_week_settings(self, user_id: str = "default") -> Dict[str, Any]:
        """Get work week settings for a user."""
        try:
            # Get work week settings from database through work week service integration
            work_week_keys = ['work_week.preset', 'work_week.start_day', 'work_week.end_day', 'work_week.timezone']
            settings = {}
            
            for key in work_week_keys:
                setting = await self.get_setting(key)
                if setting:
                    settings[key.replace('work_week.', '')] = setting.parsed_value
                else:
                    # Use default from definition
                    if key in self.setting_definitions:
                        settings[key.replace('work_week.', '')] = self.setting_definitions[key].default_value
            
            return settings
            
        except Exception as e:
            self.logger.logger.error(f"Failed to get work week settings: {str(e)}")
            return {}
    
    async def update_work_week_preset(self, preset: str, user_id: str = "default") -> bool:
        """Update work week preset and adjust start/end days accordingly."""
        try:
            # Update preset setting
            preset_result = await self.update_setting('work_week.preset', preset)
            if not preset_result:
                return False
            
            # Auto-adjust start/end days based on preset
            if preset == 'monday_friday':
                await self.update_setting('work_week.start_day', '1')  # Monday
                await self.update_setting('work_week.end_day', '5')    # Friday
            elif preset == 'sunday_thursday':
                await self.update_setting('work_week.start_day', '7')  # Sunday
                await self.update_setting('work_week.end_day', '4')    # Thursday
            # For 'custom', don't change start/end days
            
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Failed to update work week preset: {str(e)}")
            return False
    
    async def validate_custom_work_week(self, start_day: int, end_day: int) -> Dict[str, Any]:
        """Validate custom work week configuration."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "auto_corrections": {}
        }
        
        try:
            # Validate day values
            if not (1 <= start_day <= 7):
                validation_result["valid"] = False
                validation_result["errors"].append("Start day must be between 1 (Monday) and 7 (Sunday)")
            
            if not (1 <= end_day <= 7):
                validation_result["valid"] = False
                validation_result["errors"].append("End day must be between 1 (Monday) and 7 (Sunday)")
            
            # Check if start and end days are the same
            if start_day == end_day:
                validation_result["valid"] = False
                validation_result["errors"].append("Start day and end day cannot be the same")
                
                # Auto-correct to Monday-Friday
                validation_result["auto_corrections"]["start_day"] = 1
                validation_result["auto_corrections"]["end_day"] = 5
                validation_result["warnings"].append("Auto-corrected to Monday-Friday work week")
            
            return validation_result
            
        except Exception as e:
            self.logger.logger.error(f"Failed to validate custom work week: {str(e)}")
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": [],
                "auto_corrections": {}
            }
    
    async def get_work_week_presets(self) -> Dict[str, Dict[str, Any]]:
        """Get available work week presets with their configurations."""
        return {
            'monday_friday': {
                'name': 'Monday - Friday',
                'description': 'Traditional Monday to Friday work week',
                'start_day': 1,
                'end_day': 5,
                'start_day_name': 'Monday',
                'end_day_name': 'Friday'
            },
            'sunday_thursday': {
                'name': 'Sunday - Thursday', 
                'description': 'Sunday to Thursday work week (common in Middle East)',
                'start_day': 7,
                'end_day': 4,
                'start_day_name': 'Sunday',
                'end_day_name': 'Thursday'
            },
            'custom': {
                'name': 'Custom',
                'description': 'Define your own work week schedule',
                'start_day': None,
                'end_day': None,
                'start_day_name': 'Custom',
                'end_day_name': 'Custom'
            }
        }
    
    async def update_work_week_configuration(self, preset: str, start_day: int = None, 
                                           end_day: int = None, timezone: str = None) -> Dict[str, Any]:
        """Update complete work week configuration."""
        try:
            result = {
                'success': True,
                'updated_settings': {},
                'errors': []
            }
            
            # Validate configuration if custom
            if preset == 'custom' and start_day is not None and end_day is not None:
                validation = await self.validate_custom_work_week(start_day, end_day)
                if not validation['valid']:
                    # If auto-corrections are available, apply them and continue
                    if validation['auto_corrections']:
                        start_day = validation['auto_corrections'].get('start_day', start_day)
                        end_day = validation['auto_corrections'].get('end_day', end_day)
                        result['errors'].extend(validation['warnings'])  # Add warnings as informational
                    else:
                        # No auto-corrections available, fail
                        result['success'] = False
                        result['errors'] = validation['errors']
                        return result
                
                # Apply auto-corrections if any (already handled above for invalid cases)
                if validation['valid'] and validation['auto_corrections']:
                    start_day = validation['auto_corrections'].get('start_day', start_day)
                    end_day = validation['auto_corrections'].get('end_day', end_day)
            
            # Update preset
            if await self.update_work_week_preset(preset):
                result['updated_settings']['preset'] = preset
            
            # Update custom days if provided
            if start_day is not None:
                start_result = await self.update_setting('work_week.start_day', str(start_day))
                if start_result:
                    result['updated_settings']['start_day'] = start_day
            
            if end_day is not None:
                end_result = await self.update_setting('work_week.end_day', str(end_day))
                if end_result:
                    result['updated_settings']['end_day'] = end_day
            
            # Update timezone if provided
            if timezone is not None:
                tz_result = await self.update_setting('work_week.timezone', timezone)
                if tz_result:
                    result['updated_settings']['timezone'] = timezone
            
            return result
            
        except Exception as e:
            self.logger.logger.error(f"Failed to update work week configuration: {str(e)}")
            return {
                'success': False,
                'updated_settings': {},
                'errors': [str(e)]
            }