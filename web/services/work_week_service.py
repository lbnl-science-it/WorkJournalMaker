"""
Work Week Service for Daily Work Journal Web Interface

This service manages work week calculations and configuration management for proper
journal entry directory organization. It provides timezone-aware work week
calculations with configurable work schedules and intelligent weekend handling.
"""

import asyncio
from datetime import datetime, timezone, date, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
import sys

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from config_manager import AppConfig
from logger import JournalSummarizerLogger, ErrorCategory
from web.database import DatabaseManager, WebSettings
from web.services.base_service import BaseService
from web.utils.timezone_utils import get_timezone_manager, to_local, now_utc
from sqlalchemy import select, update


class WorkWeekPreset(Enum):
    """Predefined work week configurations."""
    MONDAY_FRIDAY = "monday-friday"
    SUNDAY_THURSDAY = "sunday-thursday"
    CUSTOM = "custom"


@dataclass
class WorkWeekConfig:
    """Work week configuration data structure."""
    preset: WorkWeekPreset
    start_day: int  # 1=Monday, 2=Tuesday, ..., 7=Sunday
    end_day: int    # 1=Monday, 2=Tuesday, ..., 7=Sunday
    timezone: Optional[str] = None  # User timezone, defaults to system timezone
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not (1 <= self.start_day <= 7):
            raise ValueError(f"start_day must be 1-7, got {self.start_day}")
        if not (1 <= self.end_day <= 7):
            raise ValueError(f"end_day must be 1-7, got {self.end_day}")
    
    @classmethod
    def from_preset(cls, preset: WorkWeekPreset) -> 'WorkWeekConfig':
        """Create configuration from preset."""
        if preset == WorkWeekPreset.MONDAY_FRIDAY:
            return cls(preset=preset, start_day=1, end_day=5)
        elif preset == WorkWeekPreset.SUNDAY_THURSDAY:
            return cls(preset=preset, start_day=7, end_day=4)
        else:
            # Custom preset requires explicit configuration
            return cls(preset=preset, start_day=1, end_day=5)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'preset': self.preset.value,
            'start_day': self.start_day,
            'end_day': self.end_day,
            'timezone': self.timezone
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkWeekConfig':
        """Create from dictionary representation."""
        preset = WorkWeekPreset(data.get('preset', 'monday-friday'))
        return cls(
            preset=preset,
            start_day=data.get('start_day', 1),
            end_day=data.get('end_day', 5),
            timezone=data.get('timezone')
        )


class WorkWeekService(BaseService):
    """
    Service for managing work week calculations and configuration.
    
    This service provides timezone-aware work week calculations with configurable
    work schedules and intelligent weekend handling for proper journal entry
    directory organization.
    """
    
    # Database keys for work week settings
    WORK_WEEK_PRESET_KEY = "work_week.preset"
    WORK_WEEK_START_DAY_KEY = "work_week.start_day"
    WORK_WEEK_END_DAY_KEY = "work_week.end_day"
    WORK_WEEK_TIMEZONE_KEY = "work_week.timezone"
    
    def __init__(self, config: AppConfig, logger: JournalSummarizerLogger, 
                 db_manager: DatabaseManager):
        """Initialize WorkWeekService with core dependencies."""
        super().__init__(config, logger, db_manager)
        self.timezone_manager = get_timezone_manager()
        
        # Cache for user configurations to improve performance
        self._config_cache: Dict[str, WorkWeekConfig] = {}
        self._cache_expiry: Dict[str, datetime] = {}
        self._cache_duration = timedelta(minutes=15)
    
    async def get_user_work_week_config(self, user_id: Optional[str] = None) -> WorkWeekConfig:
        """
        Retrieve user's work week configuration.
        
        Args:
            user_id: User identifier (optional, defaults to system-wide config)
            
        Returns:
            WorkWeekConfig: User's work week configuration
        """
        try:
            self._log_operation_start("get_user_work_week_config", user_id=user_id)
            
            # Check cache first
            cache_key = user_id or "default"
            if self._is_config_cached(cache_key):
                config = self._config_cache[cache_key]
                self._log_operation_success("get_user_work_week_config (cached)", user_id=user_id)
                return config
            
            # Load from database
            async with self.db_manager.get_session() as session:
                # Get work week settings from database
                preset_stmt = select(WebSettings).where(WebSettings.key == self.WORK_WEEK_PRESET_KEY)
                start_day_stmt = select(WebSettings).where(WebSettings.key == self.WORK_WEEK_START_DAY_KEY)
                end_day_stmt = select(WebSettings).where(WebSettings.key == self.WORK_WEEK_END_DAY_KEY)
                timezone_stmt = select(WebSettings).where(WebSettings.key == self.WORK_WEEK_TIMEZONE_KEY)
                
                preset_result = await session.execute(preset_stmt)
                start_day_result = await session.execute(start_day_stmt)
                end_day_result = await session.execute(end_day_stmt)
                timezone_result = await session.execute(timezone_stmt)
                
                preset_setting = preset_result.scalar_one_or_none()
                start_day_setting = start_day_result.scalar_one_or_none()
                end_day_setting = end_day_result.scalar_one_or_none()
                timezone_setting = timezone_result.scalar_one_or_none()
                
                # Build configuration from database settings or use defaults
                if preset_setting:
                    try:
                        preset = WorkWeekPreset(preset_setting.value)
                    except ValueError:
                        preset = WorkWeekPreset.MONDAY_FRIDAY
                else:
                    preset = WorkWeekPreset.MONDAY_FRIDAY
                
                start_day = int(start_day_setting.value) if start_day_setting else 1
                end_day = int(end_day_setting.value) if end_day_setting else 5
                user_timezone = timezone_setting.value if timezone_setting else None
                
                config = WorkWeekConfig(
                    preset=preset,
                    start_day=start_day,
                    end_day=end_day,
                    timezone=user_timezone
                )
                
                # Cache the configuration
                self._cache_config(cache_key, config)
                
                self._log_operation_success("get_user_work_week_config", user_id=user_id, preset=preset.value)
                return config
                
        except Exception as e:
            self._log_operation_error("get_user_work_week_config", e, user_id=user_id)
            # Return default configuration on error
            return self.get_default_work_week_config()
    
    async def update_work_week_config(self, config: WorkWeekConfig, user_id: Optional[str] = None) -> WorkWeekConfig:
        """
        Update user's work week configuration with validation.
        
        Args:
            config: New work week configuration
            user_id: User identifier (optional, defaults to system-wide config)
            
        Returns:
            WorkWeekConfig: Updated and validated configuration
        """
        try:
            self._log_operation_start("update_work_week_config", 
                                    user_id=user_id, preset=config.preset.value)
            
            # Validate configuration
            validated_config = self.validate_work_week_config(config)
            
            async with self.db_manager.get_session() as session:
                # Update or create settings in database
                await self._upsert_setting(session, self.WORK_WEEK_PRESET_KEY, validated_config.preset.value)
                await self._upsert_setting(session, self.WORK_WEEK_START_DAY_KEY, str(validated_config.start_day))
                await self._upsert_setting(session, self.WORK_WEEK_END_DAY_KEY, str(validated_config.end_day))
                
                if validated_config.timezone:
                    await self._upsert_setting(session, self.WORK_WEEK_TIMEZONE_KEY, validated_config.timezone)
                
                await session.commit()
            
            # Update cache
            cache_key = user_id or "default"
            self._cache_config(cache_key, validated_config)
            
            self._log_operation_success("update_work_week_config", 
                                     user_id=user_id, preset=validated_config.preset.value)
            return validated_config
            
        except Exception as e:
            self._log_operation_error("update_work_week_config", e, user_id=user_id)
            raise
    
    def validate_work_week_config(self, config: WorkWeekConfig) -> WorkWeekConfig:
        """
        Validate and auto-correct work week configuration.
        
        Args:
            config: Configuration to validate
            
        Returns:
            WorkWeekConfig: Validated and potentially corrected configuration
        """
        try:
            self._log_operation_start("validate_work_week_config", preset=config.preset.value)
            
            # Validate day ranges first
            if not (1 <= config.start_day <= 7):
                raise ValueError(f"Invalid start_day: {config.start_day}. Must be 1-7.")
            if not (1 <= config.end_day <= 7):
                raise ValueError(f"Invalid end_day: {config.end_day}. Must be 1-7.")
            
            # Auto-correct if start and end day are the same
            if config.start_day == config.end_day:
                self.logger.logger.warning(
                    f"Work week start and end day are the same ({config.start_day}), auto-correcting"
                )
                # Extend end day to next day
                new_end_day = (config.end_day % 7) + 1
                config = WorkWeekConfig(
                    preset=WorkWeekPreset.CUSTOM,
                    start_day=config.start_day,
                    end_day=new_end_day,
                    timezone=config.timezone
                )
            
            # Validate preset consistency
            if config.preset == WorkWeekPreset.MONDAY_FRIDAY:
                if config.start_day != 1 or config.end_day != 5:
                    self.logger.logger.info(
                        "Configuration doesn't match Monday-Friday preset, changing to custom"
                    )
                    config = WorkWeekConfig(
                        preset=WorkWeekPreset.CUSTOM,
                        start_day=config.start_day,
                        end_day=config.end_day,
                        timezone=config.timezone
                    )
            elif config.preset == WorkWeekPreset.SUNDAY_THURSDAY:
                if config.start_day != 7 or config.end_day != 4:
                    self.logger.logger.info(
                        "Configuration doesn't match Sunday-Thursday preset, changing to custom"
                    )
                    config = WorkWeekConfig(
                        preset=WorkWeekPreset.CUSTOM,
                        start_day=config.start_day,
                        end_day=config.end_day,
                        timezone=config.timezone
                    )
            
            self._log_operation_success("validate_work_week_config", preset=config.preset.value)
            return config
            
        except Exception as e:
            self._log_operation_error("validate_work_week_config", e)
            # Return default configuration on validation error
            return self.get_default_work_week_config()
    
    def get_default_work_week_config(self) -> WorkWeekConfig:
        """
        Return system default work week configuration.
        
        Returns:
            WorkWeekConfig: Default Monday-Friday configuration
        """
        return WorkWeekConfig.from_preset(WorkWeekPreset.MONDAY_FRIDAY)
    
    def get_available_presets(self) -> Dict[str, Dict[str, Any]]:
        """
        Get available work week presets with descriptions.
        
        Returns:
            Dict mapping preset values to their configurations and descriptions
        """
        return {
            WorkWeekPreset.MONDAY_FRIDAY.value: {
                'name': 'Monday - Friday',
                'description': 'Standard business week (Monday through Friday)',
                'start_day': 1,
                'end_day': 5,
                'example': 'Work: Mon-Fri, Weekend: Sat (→previous week), Sun (→next week)'
            },
            WorkWeekPreset.SUNDAY_THURSDAY.value: {
                'name': 'Sunday - Thursday', 
                'description': 'Alternative work week (Sunday through Thursday)',
                'start_day': 7,
                'end_day': 4,
                'example': 'Work: Sun-Thu, Weekend: Fri (→previous week), Sat (→next week)'
            },
            WorkWeekPreset.CUSTOM.value: {
                'name': 'Custom Schedule',
                'description': 'Define your own work week start and end days',
                'start_day': None,
                'end_day': None,
                'example': 'Configure custom start and end days for your work week'
            }
        }
    
    async def _upsert_setting(self, session, key: str, value: str):
        """Helper method to update or insert a setting."""
        # Check if setting exists
        stmt = select(WebSettings).where(WebSettings.key == key)
        result = await session.execute(stmt)
        existing_setting = result.scalar_one_or_none()
        
        if existing_setting:
            # Update existing setting
            update_stmt = (
                update(WebSettings)
                .where(WebSettings.key == key)
                .values(value=value, modified_at=now_utc())
            )
            await session.execute(update_stmt)
        else:
            # Create new setting
            new_setting = WebSettings(
                key=key,
                value=value,
                value_type='string',
                description=f'Work week configuration: {key}',
                created_at=now_utc(),
                modified_at=now_utc()
            )
            session.add(new_setting)
    
    def _is_config_cached(self, cache_key: str) -> bool:
        """Check if configuration is cached and not expired."""
        if cache_key not in self._config_cache:
            return False
        
        if cache_key not in self._cache_expiry:
            return False
        
        return datetime.now() < self._cache_expiry[cache_key]
    
    def _cache_config(self, cache_key: str, config: WorkWeekConfig):
        """Cache configuration with expiry."""
        self._config_cache[cache_key] = config
        self._cache_expiry[cache_key] = datetime.now() + self._cache_duration
    
    def _clear_config_cache(self, cache_key: Optional[str] = None):
        """Clear configuration cache."""
        if cache_key:
            self._config_cache.pop(cache_key, None)
            self._cache_expiry.pop(cache_key, None)
        else:
            self._config_cache.clear()
            self._cache_expiry.clear()
    
    async def calculate_week_ending_date(self, entry_date: Union[date, datetime], 
                                       user_id: Optional[str] = None) -> date:
        """
        Calculate the appropriate week ending date for a journal entry.
        
        This is the core algorithm that determines which weekly directory
        a journal entry should be placed in based on the user's work week
        configuration and intelligent weekend handling.
        
        Args:
            entry_date: Date of journal entry (date or datetime)
            user_id: User identifier for configuration lookup
            
        Returns:
            date: The week ending date for the entry's directory
        """
        try:
            self._log_operation_start("calculate_week_ending_date", 
                                    entry_date=entry_date, user_id=user_id)
            
            # Get user's work week configuration
            work_week_config = await self.get_user_work_week_config(user_id)
            
            # Convert entry_date to date if it's datetime
            if isinstance(entry_date, datetime):
                # Convert to local timezone first to get correct date
                local_dt = to_local(entry_date)
                entry_date = local_dt.date()
            
            # Calculate the week ending date
            week_ending = self._calculate_week_ending_for_date(entry_date, work_week_config)
            
            self._log_operation_success("calculate_week_ending_date", 
                                      entry_date=entry_date, week_ending=week_ending)
            return week_ending
            
        except Exception as e:
            self._log_operation_error("calculate_week_ending_date", e, 
                                    entry_date=entry_date, user_id=user_id)
            # Fallback to simple Friday-ending week
            return self._calculate_simple_friday_week_ending(entry_date)
    
    def _calculate_week_ending_for_date(self, entry_date: date, config: WorkWeekConfig) -> date:
        """
        Core calculation logic for week ending date.
        
        Args:
            entry_date: The date to calculate week ending for
            config: Work week configuration
            
        Returns:
            date: Week ending date
        """
        # Get day of week (1=Monday, 7=Sunday)
        entry_weekday = entry_date.weekday() + 1
        
        # Determine if entry falls within work week or is weekend
        if self._is_within_work_week(entry_weekday, config.start_day, config.end_day):
            # Entry is within work week - find the end date of this work week
            return self._find_work_week_end(entry_date, config.start_day, config.end_day)
        else:
            # Entry is on weekend - apply nearest work week logic
            return self._assign_weekend_to_work_week(entry_date, config.start_day, config.end_day)
    
    def _is_within_work_week(self, entry_day: int, start_day: int, end_day: int) -> bool:
        """
        Check if entry day falls within the work week.
        
        Args:
            entry_day: Day of week for entry (1=Monday, 7=Sunday)
            start_day: Work week start day
            end_day: Work week end day
            
        Returns:
            bool: True if within work week, False if weekend
        """
        if start_day <= end_day:
            # Normal week (e.g., Mon-Fri: 1-5)
            return start_day <= entry_day <= end_day
        else:
            # Week spans weekend (e.g., Fri-Thu: 5-4)
            return entry_day >= start_day or entry_day <= end_day
    
    def _find_work_week_end(self, entry_date: date, start_day: int, end_day: int) -> date:
        """
        Find the end date of the work week containing the entry date.
        
        Args:
            entry_date: Date within the work week
            start_day: Work week start day (1=Monday, 7=Sunday)
            end_day: Work week end day (1=Monday, 7=Sunday)
            
        Returns:
            date: End date of the work week
        """
        entry_weekday = entry_date.weekday() + 1
        
        if start_day <= end_day:
            # Normal work week (e.g., Mon-Fri)
            days_to_end = end_day - entry_weekday
            return entry_date + timedelta(days=days_to_end)
        else:
            # Work week spans weekend (e.g., Fri-Thu)
            if entry_weekday >= start_day:
                # Entry is in first part of work week (e.g., Friday-Sunday)
                days_to_end = (7 - entry_weekday) + end_day
            else:
                # Entry is in second part of work week (e.g., Monday-Thursday)
                days_to_end = end_day - entry_weekday
            return entry_date + timedelta(days=days_to_end)
    
    def _assign_weekend_to_work_week(self, entry_date: date, start_day: int, end_day: int) -> date:
        """
        Assign weekend entries to nearest work week.
        
        Weekend assignment logic:
        - Saturday entries → assigned to previous work week
        - Sunday entries → assigned to next work week
        
        Args:
            entry_date: Weekend date
            start_day: Work week start day
            end_day: Work week end day
            
        Returns:
            date: Week ending date for the assigned work week
        """
        entry_weekday = entry_date.weekday() + 1
        
        if entry_weekday == 6:  # Saturday
            # Assign to previous work week
            return self._find_previous_work_week_end(entry_date, start_day, end_day)
        elif entry_weekday == 7:  # Sunday
            # Assign to next work week  
            return self._find_next_work_week_end(entry_date, start_day, end_day)
        else:
            # This shouldn't happen if called correctly
            self.logger.logger.warning(f"assign_weekend_to_work_week called with non-weekend day: {entry_weekday}")
            return self._calculate_simple_friday_week_ending(entry_date)
    
    def _find_previous_work_week_end(self, entry_date: date, start_day: int, end_day: int) -> date:
        """Find the end date of the previous work week."""
        # Go back to find the previous work week end
        current_date = entry_date - timedelta(days=1)  # Start from Friday if Saturday entry
        
        # Find a date that's within the work week, then find its end
        for _ in range(7):  # Max one week back
            current_weekday = current_date.weekday() + 1
            if self._is_within_work_week(current_weekday, start_day, end_day):
                return self._find_work_week_end(current_date, start_day, end_day)
            current_date -= timedelta(days=1)
        
        # Fallback - should not happen with valid configuration
        return self._calculate_simple_friday_week_ending(entry_date)
    
    def _find_next_work_week_end(self, entry_date: date, start_day: int, end_day: int) -> date:
        """Find the end date of the next work week."""
        # Go forward to find the next work week end
        current_date = entry_date + timedelta(days=1)  # Start from Monday if Sunday entry
        
        # Find a date that's within the work week, then find its end
        for _ in range(7):  # Max one week forward
            current_weekday = current_date.weekday() + 1
            if self._is_within_work_week(current_weekday, start_day, end_day):
                return self._find_work_week_end(current_date, start_day, end_day)
            current_date += timedelta(days=1)
        
        # Fallback - should not happen with valid configuration
        return self._calculate_simple_friday_week_ending(entry_date)
    
    def _calculate_simple_friday_week_ending(self, entry_date: Union[date, datetime]) -> date:
        """
        Fallback calculation for simple Friday-ending weeks.
        
        Args:
            entry_date: Entry date
            
        Returns:
            date: Friday of the week containing entry_date
        """
        if isinstance(entry_date, datetime):
            entry_date = entry_date.date()
        
        # Calculate Friday of this week
        days_since_monday = entry_date.weekday()
        friday = entry_date + timedelta(days=(4 - days_since_monday))
        return friday
    
    def get_week_ending_preview(self, config: WorkWeekConfig, sample_dates: Optional[List[date]] = None) -> Dict[str, Any]:
        """
        Generate preview information for a work week configuration.
        
        Args:
            config: Work week configuration to preview
            sample_dates: Optional list of dates to show examples (defaults to current week)
            
        Returns:
            Dict containing preview information and examples
        """
        try:
            if not sample_dates:
                # Generate sample dates for current week
                today = date.today()
                start_of_week = today - timedelta(days=today.weekday())  # Monday
                sample_dates = [start_of_week + timedelta(days=i) for i in range(7)]
            
            examples = []
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            for sample_date in sample_dates:
                weekday = sample_date.weekday() + 1
                day_name = day_names[weekday - 1]
                week_ending = self._calculate_week_ending_for_date(sample_date, config)
                is_work_day = self._is_within_work_week(weekday, config.start_day, config.end_day)
                
                examples.append({
                    'date': sample_date.isoformat(),
                    'day_name': day_name,
                    'week_ending': week_ending.isoformat(),
                    'is_work_day': is_work_day,
                    'assignment': 'work week' if is_work_day else 'weekend'
                })
            
            return {
                'config': config.to_dict(),
                'work_week_description': self._format_work_week_description(config),
                'weekend_handling': 'Saturday → Previous week, Sunday → Next week',
                'examples': examples
            }
            
        except Exception as e:
            self.logger.logger.error(f"Failed to generate preview: {str(e)}")
            return {
                'config': config.to_dict(),
                'error': 'Failed to generate preview examples'
            }
    
    def _format_work_week_description(self, config: WorkWeekConfig) -> str:
        """Format work week configuration as human-readable description."""
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        start_name = day_names[config.start_day - 1]
        end_name = day_names[config.end_day - 1]
        return f"{start_name} - {end_name}"
    
    async def validate_and_repair_database_settings(self) -> Dict[str, Any]:
        """
        Validate and repair work week settings in database.
        
        This method checks for corrupted or invalid work week settings
        and repairs them with defaults if necessary.
        
        Returns:
            Dict containing validation results and any repairs made
        """
        repair_log = {
            'validated_settings': [],
            'repaired_settings': [],
            'errors': []
        }
        
        try:
            self._log_operation_start("validate_and_repair_database_settings")
            
            async with self.db_manager.get_session() as session:
                # Check each work week setting
                settings_to_check = [
                    (self.WORK_WEEK_PRESET_KEY, 'monday-friday'),
                    (self.WORK_WEEK_START_DAY_KEY, '1'),
                    (self.WORK_WEEK_END_DAY_KEY, '5'),
                    (self.WORK_WEEK_TIMEZONE_KEY, None)
                ]
                
                for setting_key, default_value in settings_to_check:
                    try:
                        stmt = select(WebSettings).where(WebSettings.key == setting_key)
                        result = await session.execute(stmt)
                        setting = result.scalar_one_or_none()
                        
                        if setting:
                            # Validate existing setting
                            is_valid = self._validate_database_setting(setting_key, setting.value)
                            if is_valid:
                                repair_log['validated_settings'].append(setting_key)
                            else:
                                # Repair invalid setting
                                if default_value:
                                    await self._upsert_setting(session, setting_key, default_value)
                                    repair_log['repaired_settings'].append({
                                        'key': setting_key,
                                        'old_value': setting.value,
                                        'new_value': default_value,
                                        'reason': 'Invalid value'
                                    })
                        else:
                            # Create missing setting
                            if default_value:
                                await self._upsert_setting(session, setting_key, default_value)
                                repair_log['repaired_settings'].append({
                                    'key': setting_key,
                                    'old_value': None,
                                    'new_value': default_value,
                                    'reason': 'Missing setting'
                                })
                    
                    except Exception as e:
                        repair_log['errors'].append({
                            'key': setting_key,
                            'error': str(e)
                        })
                        self.logger.logger.error(f"Failed to validate setting {setting_key}: {str(e)}")
                
                await session.commit()
            
            # Clear cache after repairs
            self._clear_config_cache()
            
            self._log_operation_success("validate_and_repair_database_settings", 
                                      repaired=len(repair_log['repaired_settings']))
            return repair_log
            
        except Exception as e:
            self._log_operation_error("validate_and_repair_database_settings", e)
            repair_log['errors'].append({'general': str(e)})
            return repair_log
    
    def _validate_database_setting(self, key: str, value: str) -> bool:
        """Validate a specific database setting value."""
        try:
            if key == self.WORK_WEEK_PRESET_KEY:
                return value in [preset.value for preset in WorkWeekPreset]
            elif key in [self.WORK_WEEK_START_DAY_KEY, self.WORK_WEEK_END_DAY_KEY]:
                day_val = int(value)
                return 1 <= day_val <= 7
            elif key == self.WORK_WEEK_TIMEZONE_KEY:
                # Timezone validation could be more sophisticated
                return True  # For now, accept any timezone string
            return True
        except (ValueError, TypeError):
            return False
    
    def get_service_health_status(self) -> Dict[str, Any]:
        """
        Get health status of the WorkWeekService.
        
        Returns:
            Dict containing service health information
        """
        try:
            health_status = {
                'service_name': 'WorkWeekService',
                'status': 'healthy',
                'cache_size': len(self._config_cache),
                'cached_configs': list(self._config_cache.keys()),
                'timezone_manager': {
                    'system_timezone': str(self.timezone_manager.get_system_timezone()),
                    'current_local_time': self.timezone_manager.now_local().isoformat(),
                    'current_utc_time': self.timezone_manager.now_utc().isoformat()
                },
                'available_presets': list(self.get_available_presets().keys()),
                'last_check': datetime.now().isoformat()
            }
            
            return health_status
            
        except Exception as e:
            return {
                'service_name': 'WorkWeekService',
                'status': 'unhealthy',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }