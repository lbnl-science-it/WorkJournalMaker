"""
Database Management for Work Journal Maker Web Interface

This module provides SQLite database setup and management for web indexing
while maintaining the file system as the primary data store.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, Text
from datetime import datetime
import aiosqlite
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any


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


class DatabaseManager:
    """Manages database operations and migrations."""
    
    def __init__(self, database_path: str = "web/journal_index.db"):
        self.database_path = database_path
        self.engine = None
        self.SessionLocal = None
        
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