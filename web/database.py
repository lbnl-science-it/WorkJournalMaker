"""
Database Management for Work Journal Maker Web Interface

This module provides SQLite database setup and management for web indexing
while maintaining the file system as the primary data store.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, Text, Float, Index
from datetime import datetime
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
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    synced_at = Column(DateTime, default=datetime.utcnow)


class WebSettings(Base):
    """Web-specific settings and preferences."""
    __tablename__ = "web_settings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    value_type = Column(String, nullable=False)  # 'string', 'integer', 'boolean', 'json'
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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


class DatabaseManager:
    """Manages database operations and migrations."""
    
    def __init__(self, database_path: Optional[str] = None):
        if database_path is None:
            self.database_path = self._get_default_database_path()
        else:
            self.database_path = database_path
            # Ensure directory exists for explicit paths too
            Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
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


# Global database manager instance
db_manager = DatabaseManager()