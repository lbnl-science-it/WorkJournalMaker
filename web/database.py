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
    
    def __init__(self, database_path: str = None):
        from web.resource_utils import get_user_data_dir

        if database_path is None:
            # Use the user data directory for the database
            database_path = os.path.join(get_user_data_dir(), 'journal.db')
        else:
            # If a path is provided, use it as is
            database_path = database_path

        self.database_path = database_path
        self.engine = None
        self.SessionLocal = None
        
    async def initialize(self):
        """Initialize database with proper async setup."""
        import logging

        try:
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

        except Exception as e:
            logging.error(f"Error initializing database: {str(e)}", exc_info=True)
            raise
    
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


# Global database manager instance
db_manager = DatabaseManager()