"""
Database Management for Work Journal Maker Web Interface

This module provides SQLite database setup and management for web indexing
while maintaining the file system as the primary data store.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, Text, Float, Index, update
from datetime import datetime
from .utils.timezone_utils import now_utc, now_local
import aiosqlite
import json
import os
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List, Union


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""
    pass


class JournalEntryIndex(Base):
    """Database index for journal entries (file system remains primary store)."""
    __tablename__ = "journal_entries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, unique=True, nullable=False, index=True)
    file_path = Column(String, nullable=False)
    week_ending_date = Column(Date, nullable=False, index=True)
    word_count = Column(Integer, default=0)
    character_count = Column(Integer, default=0)
    line_count = Column(Integer, default=0)
    has_content = Column(Boolean, default=False, index=True)
    
    # File system metadata
    file_size_bytes = Column(Integer, default=0)
    file_modified_at = Column(DateTime)
    
    # Web-specific metadata
    last_accessed_at = Column(DateTime)
    access_count = Column(Integer, default=0)
    
    # Timestamps (timezone-aware)
    created_at = Column(DateTime, default=now_utc, index=True)
    modified_at = Column(DateTime, default=now_utc, onupdate=now_utc)
    synced_at = Column(DateTime, default=now_utc)


class WebSettings(Base):
    """Web-specific settings and preferences."""
    __tablename__ = "web_settings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    value_type = Column(String, nullable=False)  # 'string', 'integer', 'boolean', 'json'
    description = Column(String)
    created_at = Column(DateTime, default=now_utc)
    modified_at = Column(DateTime, default=now_utc, onupdate=now_utc)


class WorkWeekSettings(Base):
    """Work week configuration settings for users."""
    __tablename__ = "work_week_settings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False, index=True, default="default")  # For multi-user support later
    work_week_preset = Column(String, nullable=False, default="monday_friday")  # 'monday_friday', 'sunday_thursday', 'custom'
    work_week_start_day = Column(Integer, nullable=False, default=1)  # 1=Monday, 2=Tuesday, ..., 7=Sunday
    work_week_end_day = Column(Integer, nullable=False, default=5)    # 1=Monday, 2=Tuesday, ..., 7=Sunday
    timezone = Column(String, nullable=False, default="UTC")
    created_at = Column(DateTime, default=now_utc)
    modified_at = Column(DateTime, default=now_utc, onupdate=now_utc)


class SyncStatus(Base):
    """Track synchronization status between file system and database."""
    __tablename__ = "sync_status"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sync_type = Column(String, nullable=False)  # 'full', 'incremental', 'entry'
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    status = Column(String, nullable=False)  # 'running', 'completed', 'failed'
    entries_processed = Column(Integer, default=0)
    entries_added = Column(Integer, default=0)
    entries_updated = Column(Integer, default=0)
    entries_removed = Column(Integer, default=0)
    error_message = Column(Text)
    sync_metadata = Column(Text)  # JSON metadata


# Add database indexes for performance
Index('idx_journal_entries_date_content', JournalEntryIndex.date, JournalEntryIndex.has_content)
Index('idx_journal_entries_week_ending', JournalEntryIndex.week_ending_date)
Index('idx_sync_status_type_started', SyncStatus.sync_type, SyncStatus.started_at)
Index('idx_work_week_settings_user', WorkWeekSettings.user_id)
Index('idx_work_week_settings_preset', WorkWeekSettings.work_week_preset)


class DatabaseManager:
    """Manages database operations and migrations."""
    
    def __init__(self, database_path: Optional[str] = None):
        if database_path is None:
            self.database_path = self._get_default_database_path()
        else:
            # Use executable-safe path resolution
            self.database_path = self._resolve_path_executable_safe(database_path)
        self.engine = None
        self.SessionLocal = None
        
    def _get_default_database_path(self) -> str:
        """
        Get the default database path based on runtime environment.
        
        In desktop app mode (PyInstaller), uses OS-standard app data directory.
        In development mode, uses relative path in project directory.
        
        Returns:
            str: Path to the database file
        """
        try:
            # Import here to avoid circular imports
            from desktop.runtime_detector import get_app_data_dir, is_frozen_executable
            
            app_data_dir = get_app_data_dir()
            
            if is_frozen_executable():
                # Desktop app: <APP_DATA>/journal_index.db
                db_path = app_data_dir / "journal_index.db"
            else:
                # Development: ./web/journal_index.db
                db_path = app_data_dir / "web" / "journal_index.db"
            
            # Ensure directory exists
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            return str(db_path)
            
        except ImportError:
            # Fallback if runtime_detector is not available
            # This maintains backward compatibility
            fallback_path = Path("web/journal_index.db")
            fallback_path.parent.mkdir(parents=True, exist_ok=True)
            return str(fallback_path)
    
    def _resolve_path_executable_safe(self, path: str) -> str:
        """
        Resolve database path with executable-aware logic and fallback handling.
        
        This method implements robust path resolution that:
        1. Handles relative paths relative to executable directory
        2. Supports tilde expansion for user home directories
        3. Leaves absolute paths unchanged
        4. Creates necessary directories with fallback to user data directory
        5. Handles permission errors gracefully
        
        Args:
            path: Database path to resolve (relative, absolute, or with tilde)
            
        Returns:
            str: Resolved absolute path to database file
        """
        try:
            # Import ExecutableDetector for executable-aware path resolution
            from config_manager import ExecutableDetector
            
            path_obj = Path(path)
            
            # Handle tilde expansion first
            if path.startswith('~'):
                resolved_path = path_obj.expanduser()
            # Handle absolute paths (including Windows paths on Unix systems)
            elif path_obj.is_absolute() or self._is_windows_absolute_path(path):
                # For Windows paths on Unix systems, return the original string unchanged
                if self._is_windows_absolute_path(path) and not path_obj.is_absolute():
                    return path
                resolved_path = path_obj
            # Handle relative paths (resolve against executable directory)  
            else:
                executable_detector = ExecutableDetector()
                exe_dir = executable_detector.get_executable_directory()
                resolved_path = exe_dir / path_obj
            
            # Convert to absolute path but don't fully resolve symlinks/canonical form
            # to maintain the exact path the user specified
            if not resolved_path.is_absolute():
                resolved_path = resolved_path.resolve()
            else:
                # For absolute paths, just ensure parent directories exist
                resolved_path = Path(str(resolved_path))
            
            # Create parent directory with fallback handling
            if not self._ensure_directory_exists(resolved_path.parent):
                # Directory creation failed, use fallback path
                print(f"Warning: Using fallback path due to directory creation failure for {resolved_path}")
                return self._get_fallback_database_path(path)
            
            return str(resolved_path)
            
        except Exception as e:
            # Log the error and fallback to user data directory
            print(f"Warning: Path resolution failed for '{path}': {e}")
            return self._get_fallback_database_path(path)
    
    def _is_windows_absolute_path(self, path: str) -> bool:
        """
        Check if path is a Windows absolute path (e.g., C:\\Users\\...).
        
        This is needed because on Unix systems, Path.is_absolute() returns False
        for Windows paths, but we still want to treat them as absolute.
        
        Args:
            path: Path to check
            
        Returns:
            bool: True if path appears to be Windows absolute path
        """
        import re
        # Match Windows drive letters: C:, D:, etc.
        windows_drive_pattern = r'^[A-Za-z]:[/\\]'
        return bool(re.match(windows_drive_pattern, path))
    
    def _ensure_directory_exists(self, directory: Path) -> bool:
        """
        Create directory with fallback indication on permission errors.
        
        Args:
            directory: Directory path to create
            
        Returns:
            bool: True if directory was created successfully, False if fallback needed
        """
        try:
            directory.mkdir(parents=True, exist_ok=True)
            return True
        except (PermissionError, OSError) as e:
            print(f"Warning: Cannot create directory {directory}: {e}")
            return False
    
    def _get_user_data_directory(self) -> Path:
        """
        Get platform-appropriate user data directory for fallback paths.
        
        Returns:
            Path: User data directory for the application
        """
        import sys
        
        if sys.platform == "win32":
            # Windows: %APPDATA%\WorkJournalMaker
            appdata = os.environ.get('APPDATA')
            if appdata:
                return Path(appdata) / "WorkJournalMaker"
            else:
                return Path.home() / "AppData" / "Roaming" / "WorkJournalMaker"
        elif sys.platform == "darwin":
            # macOS: ~/Library/Application Support/WorkJournalMaker
            return Path.home() / "Library" / "Application Support" / "WorkJournalMaker"
        else:
            # Linux/Unix: ~/.local/share/WorkJournalMaker
            xdg_data_home = os.environ.get('XDG_DATA_HOME')
            if xdg_data_home:
                return Path(xdg_data_home) / "WorkJournalMaker"
            else:
                return Path.home() / ".local" / "share" / "WorkJournalMaker"
    
    def _get_fallback_database_path(self, original_path: str = None) -> str:
        """
        Get fallback database path in user data directory.
        
        Args:
            original_path: Optional original path that failed (for context)
        
        Returns:
            str: Fallback database path that should be writable
        """
        try:
            user_data_dir = self._get_user_data_directory()
            user_data_dir.mkdir(parents=True, exist_ok=True)
            
            # If we have original path context, create a more specific fallback
            if original_path:
                original_name = Path(original_path).name
                if not original_name.endswith('.db'):
                    original_name = f"{original_name}.db"
                fallback_path = user_data_dir / "WorkJournal" / "fallback" / original_name
            else:
                # Use default fallback name
                fallback_path = user_data_dir / "journal_index.db"
            
            # Ensure directory exists
            fallback_path.parent.mkdir(parents=True, exist_ok=True)
            return str(fallback_path)
        except Exception as e:
            # Last resort: current directory
            print(f"Warning: Cannot create user data directory: {e}")
            fallback_name = "journal_index.db"
            if original_path:
                original_name = Path(original_path).name
                if original_name.endswith('.db'):
                    fallback_name = original_name
            fallback_path = Path(fallback_name)
            return str(fallback_path.resolve())
    
    async def initialize(self):
        """Initialize database with proper async setup."""
        # Ensure directory exists
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.engine = create_async_engine(
            f"sqlite+aiosqlite:///{self.database_path}",
            echo=False,  # Set to True for SQL debugging
            pool_pre_ping=True
        )
        self.SessionLocal = async_sessionmaker(
            self.engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        # Initialize default settings
        await self._initialize_default_settings()
        
        # Initialize default work week settings
        await self._initialize_default_work_week_settings()
    
    async def _initialize_default_settings(self):
        """Initialize default web settings."""
        default_settings = [
            ("auto_save_interval", "30", "integer", "Auto-save interval in seconds"),
            ("theme", "light", "string", "UI theme preference"),
            ("editor_font_size", "14", "integer", "Editor font size"),
            ("show_word_count", "true", "boolean", "Show word count in editor"),
            ("calendar_start_day", "0", "integer", "Calendar start day (0=Sunday)"),
        ]
        
        async with self.get_session() as session:
            for key, value, value_type, description in default_settings:
                # Check if setting already exists
                from sqlalchemy import select
                stmt = select(WebSettings).where(WebSettings.key == key)
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if not existing:
                    setting = WebSettings(
                        key=key,
                        value=value,
                        value_type=value_type,
                        description=description
                    )
                    session.add(setting)
            await session.commit()
    
    async def _initialize_default_work_week_settings(self):
        """Initialize default work week settings."""
        async with self.get_session() as session:
            from sqlalchemy import select
            stmt = select(WorkWeekSettings).where(WorkWeekSettings.user_id == "default")
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if not existing:
                default_work_week = WorkWeekSettings(
                    user_id="default",
                    work_week_preset="monday_friday",
                    work_week_start_day=1,  # Monday
                    work_week_end_day=5,    # Friday
                    timezone="UTC"
                )
                session.add(default_work_week)
                await session.commit()
    
    def _parse_setting_value(self, value: str, value_type: str) -> Union[str, int, bool, float, Dict[str, Any]]:
        """Parse setting value based on its type."""
        try:
            if value_type == "integer":
                return int(value)
            elif value_type == "boolean":
                return value.lower() in ("true", "1", "yes", "on")
            elif value_type == "float":
                return float(value)
            elif value_type == "json":
                return json.loads(value)
            else:  # string
                return value
        except (ValueError, json.JSONDecodeError):
            return value  # Return original value if parsing fails
    
    async def get_setting(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a specific setting by key."""
        try:
            async with self.get_session() as session:
                from sqlalchemy import select
                stmt = select(WebSettings).where(WebSettings.key == key)
                result = await session.execute(stmt)
                setting = result.scalar_one_or_none()
                
                if setting:
                    return {
                        "key": setting.key,
                        "value": setting.value,
                        "parsed_value": self._parse_setting_value(setting.value, setting.value_type),
                        "value_type": setting.value_type,
                        "description": setting.description,
                        "created_at": setting.created_at,
                        "modified_at": setting.modified_at
                    }
                return None
        except Exception as e:
            return None
    
    async def set_setting(self, key: str, value: str, value_type: str, description: Optional[str] = None) -> bool:
        """Set or update a setting."""
        try:
            async with self.get_session() as session:
                from sqlalchemy import select, update
                
                # Check if setting exists
                stmt = select(WebSettings).where(WebSettings.key == key)
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if existing:
                    # Update existing setting
                    update_stmt = (
                        update(WebSettings)
                        .where(WebSettings.key == key)
                        .values(
                            value=value,
                            value_type=value_type,
                            description=description or existing.description,
                            modified_at=datetime.utcnow()
                        )
                    )
                    await session.execute(update_stmt)
                else:
                    # Create new setting
                    new_setting = WebSettings(
                        key=key,
                        value=value,
                        value_type=value_type,
                        description=description
                    )
                    session.add(new_setting)
                
                await session.commit()
                return True
        except Exception as e:
            return False
    
    async def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings as a dictionary."""
        try:
            async with self.get_session() as session:
                from sqlalchemy import select
                stmt = select(WebSettings)
                result = await session.execute(stmt)
                settings = result.scalars().all()
                
                return {
                    setting.key: self._parse_setting_value(setting.value, setting.value_type)
                    for setting in settings
                }
        except Exception as e:
            return {}
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics."""
        try:
            async with self.get_session() as session:
                from sqlalchemy import select, func, and_
                
                # Get entry statistics
                total_entries_stmt = select(func.count(JournalEntryIndex.id))
                total_entries = await session.scalar(total_entries_stmt)
                
                entries_with_content_stmt = select(func.count(JournalEntryIndex.id)).where(
                    JournalEntryIndex.has_content == True
                )
                entries_with_content = await session.scalar(entries_with_content_stmt)
                
                # Get date range
                date_range_stmt = select(
                    func.min(JournalEntryIndex.date),
                    func.max(JournalEntryIndex.date)
                )
                date_range_result = await session.execute(date_range_stmt)
                min_date, max_date = date_range_result.fetchone()
                
                # Get last sync info
                last_sync_stmt = select(func.max(SyncStatus.completed_at)).where(
                    and_(SyncStatus.status == "completed", SyncStatus.sync_type == "full")
                )
                last_sync = await session.scalar(last_sync_stmt)
                
                # Get database file size
                db_size_mb = 0.0
                if os.path.exists(self.database_path):
                    db_size_mb = os.path.getsize(self.database_path) / (1024 * 1024)
                
                return {
                    "total_entries": total_entries or 0,
                    "entries_with_content": entries_with_content or 0,
                    "date_range": {
                        "start": min_date.isoformat() if min_date else None,
                        "end": max_date.isoformat() if max_date else None
                    } if min_date and max_date else None,
                    "last_sync": last_sync.isoformat() if last_sync else None,
                    "database_size_mb": round(db_size_mb, 2)
                }
        except Exception as e:
            return {
                "total_entries": 0,
                "entries_with_content": 0,
                "date_range": None,
                "last_sync": None,
                "database_size_mb": 0.0,
                "error": str(e)
            }
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session with proper cleanup."""
        async with self.SessionLocal() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database health and return status."""
        try:
            async with self.get_session() as session:
                from sqlalchemy import text
                result = await session.execute(text("SELECT 1"))
                result.fetchone()
                
                # Get basic stats
                from sqlalchemy import select, func
                stmt = select(func.count(JournalEntryIndex.id))
                result = await session.execute(stmt)
                entry_count = result.scalar()
                
                return {
                    "status": "healthy",
                    "database_path": self.database_path,
                    "entry_count": entry_count,
                    "connection": "active"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "database_path": self.database_path
            }
    
    # Work Week Settings Methods
    
    async def get_work_week_settings(self, user_id: str = "default") -> Optional[Dict[str, Any]]:
        """Get work week settings for a user."""
        try:
            async with self.get_session() as session:
                from sqlalchemy import select
                stmt = select(WorkWeekSettings).where(WorkWeekSettings.user_id == user_id)
                result = await session.execute(stmt)
                settings = result.scalar_one_or_none()
                
                if settings:
                    return {
                        "user_id": settings.user_id,
                        "work_week_preset": settings.work_week_preset,
                        "work_week_start_day": settings.work_week_start_day,
                        "work_week_end_day": settings.work_week_end_day,
                        "timezone": settings.timezone,
                        "created_at": settings.created_at,
                        "modified_at": settings.modified_at
                    }
                return None
        except Exception as e:
            return None
    
    async def update_work_week_settings(self, user_id: str = "default", 
                                      preset: str = None, 
                                      start_day: int = None, 
                                      end_day: int = None, 
                                      timezone: str = None) -> bool:
        """Update work week settings for a user."""
        try:
            async with self.get_session() as session:
                from sqlalchemy import select, update
                
                # Check if settings exist
                stmt = select(WorkWeekSettings).where(WorkWeekSettings.user_id == user_id)
                result = await session.execute(stmt)
                existing = result.scalar_one_or_none()
                
                if existing:
                    # Update existing settings
                    update_data = {"modified_at": now_utc()}
                    if preset is not None:
                        update_data["work_week_preset"] = preset
                    if start_day is not None:
                        update_data["work_week_start_day"] = start_day
                    if end_day is not None:
                        update_data["work_week_end_day"] = end_day
                    if timezone is not None:
                        update_data["timezone"] = timezone
                    
                    update_stmt = (
                        update(WorkWeekSettings)
                        .where(WorkWeekSettings.user_id == user_id)
                        .values(**update_data)
                    )
                    await session.execute(update_stmt)
                else:
                    # Create new settings
                    new_settings = WorkWeekSettings(
                        user_id=user_id,
                        work_week_preset=preset or "monday_friday",
                        work_week_start_day=start_day or 1,
                        work_week_end_day=end_day or 5,
                        timezone=timezone or "UTC"
                    )
                    session.add(new_settings)
                
                await session.commit()
                return True
        except Exception as e:
            return False
    
    async def validate_work_week_settings(self, preset: str, start_day: int, end_day: int) -> Dict[str, Any]:
        """Validate work week settings and return validation result."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "auto_corrections": {}
        }
        
        # Validate preset
        valid_presets = ["monday_friday", "sunday_thursday", "custom"]
        if preset not in valid_presets:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Invalid preset '{preset}'. Must be one of: {', '.join(valid_presets)}")
        
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
            
            # Auto-correct: if Monday-Friday preset, fix the days
            if preset == "monday_friday":
                validation_result["auto_corrections"]["start_day"] = 1
                validation_result["auto_corrections"]["end_day"] = 5
                validation_result["warnings"].append("Auto-corrected to Monday-Friday work week")
            elif preset == "sunday_thursday":
                validation_result["auto_corrections"]["start_day"] = 7  # Sunday
                validation_result["auto_corrections"]["end_day"] = 4   # Thursday
                validation_result["warnings"].append("Auto-corrected to Sunday-Thursday work week")
        
        return validation_result
    
    async def create_work_week_migration(self) -> Dict[str, Any]:
        """Create migration for existing installations without work week settings."""
        migration_result = {
            "success": False,
            "users_migrated": 0,
            "errors": []
        }
        
        try:
            async with self.get_session() as session:
                from sqlalchemy import select
                
                # Check if WorkWeekSettings table exists and has data
                stmt = select(WorkWeekSettings)
                result = await session.execute(stmt)
                existing_settings = result.scalars().all()
                
                if not existing_settings:
                    # Create default work week settings for the default user
                    default_work_week = WorkWeekSettings(
                        user_id="default",
                        work_week_preset="monday_friday",
                        work_week_start_day=1,  # Monday
                        work_week_end_day=5,    # Friday
                        timezone="UTC"
                    )
                    session.add(default_work_week)
                    await session.commit()
                    migration_result["users_migrated"] = 1
                
                migration_result["success"] = True
                
        except Exception as e:
            migration_result["errors"].append(str(e))
        
        return migration_result
    
    async def migrate_week_ending_dates(self, work_week_service, batch_size: int = 100) -> Dict[str, Any]:
        """Migrate existing journal entries to use calculated week ending dates."""
        migration_result = {
            "success": False,
            "entries_processed": 0,
            "entries_updated": 0,
            "entries_with_errors": 0,
            "errors": [],
            "batches_processed": 0
        }
        
        try:
            async with self.get_session() as session:
                from sqlalchemy import select, func
                
                # Get total count for progress tracking
                count_stmt = select(func.count(JournalEntryIndex.id))
                total_entries = await session.scalar(count_stmt)
                
                if total_entries == 0:
                    migration_result["success"] = True
                    return migration_result
                
                # Process entries in batches
                offset = 0
                batch_count = 0
                
                while offset < total_entries:
                    batch_count += 1
                    
                    # Get batch of entries
                    batch_stmt = (
                        select(JournalEntryIndex)
                        .order_by(JournalEntryIndex.date)
                        .offset(offset)
                        .limit(batch_size)
                    )
                    batch_result = await session.execute(batch_stmt)
                    batch_entries = batch_result.scalars().all()
                    
                    if not batch_entries:
                        break
                    
                    # Process each entry in the batch
                    for entry in batch_entries:
                        try:
                            # Calculate new week ending date
                            new_week_ending = await work_week_service.calculate_week_ending_date(entry.date)
                            
                            # Update if different
                            if entry.week_ending_date != new_week_ending:
                                update_stmt = (
                                    update(JournalEntryIndex)
                                    .where(JournalEntryIndex.id == entry.id)
                                    .values(
                                        week_ending_date=new_week_ending,
                                        modified_at=now_utc(),
                                        synced_at=now_utc()
                                    )
                                )
                                await session.execute(update_stmt)
                                migration_result["entries_updated"] += 1
                            
                            migration_result["entries_processed"] += 1
                            
                        except Exception as e:
                            migration_result["entries_with_errors"] += 1
                            migration_result["errors"].append({
                                "entry_date": entry.date.isoformat(),
                                "error": str(e)
                            })
                    
                    # Commit batch
                    await session.commit()
                    migration_result["batches_processed"] = batch_count
                    
                    # Move to next batch
                    offset += batch_size
                
                migration_result["success"] = True
                
        except Exception as e:
            migration_result["errors"].append({"general": str(e)})
        
        return migration_result
    
    async def validate_week_ending_dates_integrity(self) -> Dict[str, Any]:
        """Validate the integrity of week ending dates in the database."""
        validation_result = {
            "success": False,
            "total_entries": 0,
            "valid_entries": 0,
            "invalid_entries": 0,
            "missing_week_endings": 0,
            "invalid_date_ranges": 0,
            "errors": []
        }
        
        try:
            async with self.get_session() as session:
                from sqlalchemy import select, func, and_
                
                # Get all entries
                stmt = select(JournalEntryIndex).order_by(JournalEntryIndex.date)
                result = await session.execute(stmt)
                entries = result.scalars().all()
                
                validation_result["total_entries"] = len(entries)
                
                for entry in entries:
                    try:
                        # Check if week ending date exists
                        if entry.week_ending_date is None:
                            validation_result["missing_week_endings"] += 1
                            validation_result["errors"].append({
                                "entry_date": entry.date.isoformat(),
                                "issue": "Missing week ending date"
                            })
                            continue
                        
                        # Check if week ending date is reasonable (within 7 days of entry date)
                        date_diff = abs((entry.week_ending_date - entry.date).days)
                        if date_diff > 7:
                            validation_result["invalid_date_ranges"] += 1
                            validation_result["errors"].append({
                                "entry_date": entry.date.isoformat(),
                                "week_ending_date": entry.week_ending_date.isoformat(),
                                "issue": f"Week ending date is {date_diff} days from entry date"
                            })
                            continue
                        
                        validation_result["valid_entries"] += 1
                        
                    except Exception as e:
                        validation_result["invalid_entries"] += 1
                        validation_result["errors"].append({
                            "entry_date": entry.date.isoformat() if entry.date else "unknown",
                            "issue": f"Validation error: {str(e)}"
                        })
                
                validation_result["success"] = True
                
        except Exception as e:
            validation_result["errors"].append({"general": str(e)})
        
        return validation_result
    
    # Phase 6: Error Handling & Fallbacks Methods
    
    def _validate_database_path(self, path: str, existing_path: Optional[str] = None) -> bool:
        """
        Validate database path and check for conflicts with existing databases.
        
        Args:
            path: Path to validate
            existing_path: Path to existing database (if any)
            
        Returns:
            bool: True if path is valid
            
        Raises:
            ValueError: If path conflicts with existing database or is invalid
        """
        if not path:
            raise ValueError("Database path cannot be empty")
        
        path_obj = Path(path)
        
        # Check for path conflicts with existing database
        if existing_path and Path(existing_path).exists():
            if not path_obj.exists() and str(path_obj) != existing_path:
                # Requesting new path but existing database exists - potential conflict
                raise ValueError(f"Database path conflict: requesting '{path}' but existing database at '{existing_path}'")
        
        # Validate path characters
        if not self._validate_path_characters(path):
            raise ValueError(f"Invalid characters in database path: {path}")
        
        return True
    
    def _raise_path_conflict_error(self, requested_path: str, existing_path: str, source: str) -> None:
        """
        Raise detailed error about database path conflicts.
        
        Args:
            requested_path: The path that was requested
            existing_path: Path to existing database
            source: Source of the conflicting path (CLI, config, etc.)
            
        Raises:
            ValueError: Detailed error about the conflict
        """
        error_msg = (
            f"Database path conflict detected!\n\n"
            f"Source: {source}\n"
            f"Requested path: {requested_path}\n"
            f"Existing database: {existing_path}\n\n"
            f"Resolution options:\n"
            f"1. Use existing database by omitting --database-path\n"
            f"2. Backup existing database and use new path\n"
            f"3. Choose a different path that doesn't conflict\n\n"
            f"To avoid data loss, this operation has been stopped."
        )
        raise ValueError(error_msg)
    
    
    def _create_path_error(self, path: str, source: str, issue: str) -> ValueError:
        """
        Create detailed path error with source attribution.
        
        Args:
            path: The problematic path
            source: Source of the path (CLI, config file, environment)
            issue: Description of the issue
            
        Returns:
            ValueError: Detailed error with source attribution
        """
        error_msg = (
            f"Database path error from {source}:\n\n"
            f"Path: {path}\n"
            f"Issue: {issue}\n\n"
            f"Please check the path and try again."
        )
        return ValueError(error_msg)
    
    def _validate_path_characters(self, path: str) -> bool:
        """
        Validate path contains only valid characters.
        
        Args:
            path: Path to validate
            
        Returns:
            bool: True if path has valid characters
        """
        import re
        
        # Check for null characters and other invalid chars
        if '\x00' in path or '\t' in path:
            return False
        
        # Check for Windows reserved names on any platform (for cross-platform compatibility)
        reserved_names = {'CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                         'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                         'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'}
        
        path_name = Path(path).name.upper()
        if path_name in reserved_names or path_name.split('.')[0] in reserved_names:
            return False
        
        return True
    
    def _resolve_path_with_fallback(self, path: str) -> str:
        """
        Resolve path with fallback handling for permission errors.
        
        Args:
            path: Original path to resolve
            
        Returns:
            str: Resolved path (original or fallback)
        """
        try:
            resolved_path = Path(path).resolve()
            
            # Try to ensure directory exists
            if self._ensure_directory_exists(resolved_path.parent):
                return str(resolved_path)
            
        except (PermissionError, OSError):
            pass  # Fall through to fallback
        
        # Use fallback path
        fallback_path = self._get_fallback_database_path(path)
        self._ensure_directory_exists(Path(fallback_path).parent)
        return str(fallback_path)
    
    def _handle_permission_error(self, path: str, operation: str) -> str:
        """
        Handle permission errors with fallback.
        
        Args:
            path: Path that caused permission error
            operation: Description of operation that failed
            
        Returns:
            str: Fallback path to use instead
        """
        fallback_path = self._get_fallback_database_path(path)
        
        # Ensure fallback directory exists
        try:
            self._ensure_directory_exists(Path(fallback_path).parent)
        except PermissionError:
            # If even fallback fails, use temp directory
            import tempfile
            temp_dir = Path(tempfile.gettempdir()) / "WorkJournal" / "emergency"
            temp_dir.mkdir(parents=True, exist_ok=True)
            fallback_path = temp_dir / "emergency_database.db"
        
        return str(fallback_path)
    
    def _handle_readonly_filesystem(self, path: str) -> str:
        """
        Handle read-only filesystem by providing writable alternative.
        
        Args:
            path: Path on read-only filesystem
            
        Returns:
            str: Alternative writable path
        """
        import tempfile
        
        # Use temp directory as last resort
        temp_dir = Path(tempfile.gettempdir()) / "WorkJournal" / "readonly_fallback"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        original_name = Path(path).name
        if not original_name.endswith('.db'):
            original_name = f"{original_name}.db"
        
        fallback_path = temp_dir / original_name
        return str(fallback_path)
    
    def _create_fallback_directory(self) -> Path:
        """
        Create fallback directory for database storage.
        
        Returns:
            Path: Created fallback directory
        """
        user_data_dir = self._get_user_data_directory()
        fallback_dir = user_data_dir / "WorkJournal" / "fallback"
        
        fallback_dir.mkdir(parents=True, exist_ok=True)
        return fallback_dir
    
    def _generate_fallback_guidance(self, original_path: str, fallback_path: str, reason: str) -> str:
        """
        Generate user guidance message for fallback scenarios.
        
        Args:
            original_path: The original path that failed
            fallback_path: The fallback path being used
            reason: Reason for fallback
            
        Returns:
            str: Guidance message for user
        """
        return (
            f"Database path fallback activated:\n\n"
            f"Original path: {original_path}\n"
            f"Reason: {reason}\n"
            f"Fallback path: {fallback_path}\n\n"
            f"Your data will be stored in the fallback location. "
            f"To use your preferred location, please resolve the issue with the original path "
            f"and restart the application."
        )
    
    def _resolve_with_multiple_fallbacks(self, path: str) -> str:
        """
        Resolve path with multiple fallback attempts.
        
        Args:
            path: Original path to resolve
            
        Returns:
            str: Successfully resolved path
        """
        # Try original path
        try:
            resolved_path = Path(path).resolve()
            if self._ensure_directory_exists(resolved_path.parent):
                return str(resolved_path)
        except Exception:
            pass
        
        # Try primary fallback
        try:
            fallback_path = self._get_fallback_database_path(path)
            if self._ensure_directory_exists(Path(fallback_path).parent):
                return str(fallback_path)
        except Exception:
            pass
        
        # Try secondary fallback in user home
        try:
            home_fallback = Path.home() / ".workjournal" / "database.db"
            if self._ensure_directory_exists(home_fallback.parent):
                return str(home_fallback)
        except Exception:
            pass
        
        # Last resort: temp directory
        import tempfile
        temp_path = Path(tempfile.gettempdir()) / "workjournal_emergency.db"
        return str(temp_path)
    
    def _get_recovery_guidance(self, error_type: str, path: str) -> str:
        """
        Get specific recovery guidance for different error types.
        
        Args:
            error_type: Type of error (permission_denied, directory_not_found, etc.)
            path: Path that caused the error
            
        Returns:
            str: Recovery guidance
        """
        if error_type == "permission_denied":
            return (
                f"Permission denied for path: {path}\n\n"
                f"Recovery options:\n"
                f"1. Check directory permissions: ls -la {Path(path).parent}\n"
                f"2. Fix permissions: chmod 755 {Path(path).parent}\n"
                f"3. Use alternative path with --database-path\n"
                f"4. Run with different user privileges"
            )
        elif error_type == "directory_not_found":
            return (
                f"Directory not found: {Path(path).parent}\n\n"
                f"Recovery options:\n"
                f"1. Create directory: mkdir -p {Path(path).parent}\n"
                f"2. Use existing directory path\n"
                f"3. Let application use default location"
            )
        elif error_type == "invalid_path":
            return (
                f"Invalid path format: {path}\n\n"
                f"Recovery options:\n"
                f"1. Use valid path format (no invalid characters)\n"
                f"2. Use absolute path instead of relative\n"
                f"3. Check path syntax for your operating system"
            )
        else:
            return f"Error with path: {path}. Please check path and try again."
    
    def _create_detailed_error(self, path: str, error_type: str, error_message: str, 
                              source: str, recovery_actions: List[str]) -> str:
        """
        Create detailed error message with recovery actions.
        
        Args:
            path: Path that caused error
            error_type: Type of error
            error_message: Original error message
            source: Source of the path
            recovery_actions: List of recovery actions
            
        Returns:
            str: Detailed error message
        """
        recovery_text = "\n".join(f"  - {action}" for action in recovery_actions)
        
        return (
            f"Database Path Error:\n\n"
            f"Error Type: {error_type}\n"
            f"Source: {source}\n"
            f"Path: {path}\n"
            f"Message: {error_message}\n\n"
            f"Recovery Actions:\n{recovery_text}\n\n"
            f"If the issue persists, the application will use a fallback location."
        )
    
    def _track_configuration_source(self, source: str, path: str) -> None:
        """
        Track configuration source for error attribution.
        
        Args:
            source: Source of configuration
            path: Path from that source
        """
        # This could be expanded to maintain a log of configuration sources
        # For now, it's a placeholder for tracking functionality
        pass
    
    def _aggregate_configuration_errors(self, errors: List[tuple]) -> str:
        """
        Aggregate multiple configuration errors into single message.
        
        Args:
            errors: List of (source, path, issue) tuples
            
        Returns:
            str: Aggregated error message
        """
        error_lines = ["Multiple configuration errors detected:\n"]
        
        for i, (source, path, issue) in enumerate(errors, 1):
            error_lines.append(f"{i}. {source}")
            error_lines.append(f"   Path: {path}")
            error_lines.append(f"   Issue: {issue}\n")
        
        error_lines.append("Please resolve these configuration issues and try again.")
        
        return "\n".join(error_lines)


# Global database manager instance
db_manager = DatabaseManager()