"""
Tests for Work Week Database Schema Extension

This module tests the database schema extension for work week functionality,
including the new WorkWeekSettings table, migration scripts, and utility methods.
"""

import pytest
import pytest_asyncio
import asyncio
import tempfile
import os
from pathlib import Path
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, text
import sys

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))
from web.database import (
    DatabaseManager, WorkWeekSettings, Base, db_manager
)
import importlib.util
import sys

# Import the migration module using importlib
migration_path = Path(__file__).parent.parent / "web" / "migrations" / "001_add_work_week_settings.py"
spec = importlib.util.spec_from_file_location("work_week_migration", migration_path)
migration_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration_module)
WorkWeekMigration = migration_module.WorkWeekMigration


class TestWorkWeekDatabaseSchema:
    """Test the work week database schema and operations."""
    
    @pytest_asyncio.fixture
    async def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # Initialize database manager with temp database
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()
        
        yield db_manager
        
        # Cleanup
        await db_manager.engine.dispose()
        os.unlink(db_path)
    
    @pytest.mark.asyncio
    async def test_work_week_settings_table_creation(self, temp_db):
        """Test that WorkWeekSettings table is created properly."""
        async with temp_db.get_session() as session:
            # Test table exists and can be queried
            stmt = select(WorkWeekSettings)
            result = await session.execute(stmt)
            settings = result.scalars().all()
            
            # Should have default settings from initialization
            assert len(settings) >= 1
            
            # Find default user settings
            default_settings = [s for s in settings if s.user_id == "default"]
            assert len(default_settings) == 1
            
            default = default_settings[0]
            assert default.work_week_preset == "monday_friday"
            assert default.work_week_start_day == 1  # Monday
            assert default.work_week_end_day == 5    # Friday
            assert default.timezone == "UTC"
    
    @pytest.mark.asyncio
    async def test_get_work_week_settings(self, temp_db):
        """Test getting work week settings."""
        # Test getting default user settings
        settings = await temp_db.get_work_week_settings("default")
        assert settings is not None
        assert settings["user_id"] == "default"
        assert settings["work_week_preset"] == "monday_friday"
        assert settings["work_week_start_day"] == 1
        assert settings["work_week_end_day"] == 5
        assert settings["timezone"] == "UTC"
        
        # Test getting non-existent user settings
        settings = await temp_db.get_work_week_settings("nonexistent")
        assert settings is None
    
    @pytest.mark.asyncio
    async def test_update_work_week_settings(self, temp_db):
        """Test updating work week settings."""
        # Update existing settings
        success = await temp_db.update_work_week_settings(
            user_id="default",
            preset="sunday_thursday",
            start_day=7,  # Sunday
            end_day=4,    # Thursday
            timezone="US/Pacific"
        )
        assert success is True
        
        # Verify update
        settings = await temp_db.get_work_week_settings("default")
        assert settings["work_week_preset"] == "sunday_thursday"
        assert settings["work_week_start_day"] == 7
        assert settings["work_week_end_day"] == 4
        assert settings["timezone"] == "US/Pacific"
        
        # Test creating new user settings
        success = await temp_db.update_work_week_settings(
            user_id="testuser",
            preset="custom",
            start_day=2,  # Tuesday
            end_day=6,    # Saturday
            timezone="Europe/London"
        )
        assert success is True
        
        # Verify new settings
        settings = await temp_db.get_work_week_settings("testuser")
        assert settings["user_id"] == "testuser"
        assert settings["work_week_preset"] == "custom"
        assert settings["work_week_start_day"] == 2
        assert settings["work_week_end_day"] == 6
        assert settings["timezone"] == "Europe/London"
    
    @pytest.mark.asyncio
    async def test_partial_work_week_updates(self, temp_db):
        """Test partial updates to work week settings."""
        # Update only preset
        success = await temp_db.update_work_week_settings(
            user_id="default",
            preset="sunday_thursday"
        )
        assert success is True
        
        settings = await temp_db.get_work_week_settings("default")
        assert settings["work_week_preset"] == "sunday_thursday"
        # Other fields should remain unchanged
        assert settings["work_week_start_day"] == 1  # Original value
        assert settings["work_week_end_day"] == 5    # Original value
        
        # Update only timezone
        success = await temp_db.update_work_week_settings(
            user_id="default",
            timezone="US/Eastern"
        )
        assert success is True
        
        settings = await temp_db.get_work_week_settings("default")
        assert settings["timezone"] == "US/Eastern"
        assert settings["work_week_preset"] == "sunday_thursday"  # Previous update preserved
    
    @pytest.mark.asyncio
    async def test_validate_work_week_settings(self, temp_db):
        """Test work week settings validation."""
        # Test valid settings
        result = await temp_db.validate_work_week_settings("monday_friday", 1, 5)
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        
        # Test invalid preset
        result = await temp_db.validate_work_week_settings("invalid_preset", 1, 5)
        assert result["valid"] is False
        assert any("Invalid preset" in error for error in result["errors"])
        
        # Test invalid day values
        result = await temp_db.validate_work_week_settings("monday_friday", 0, 5)
        assert result["valid"] is False
        assert any("Start day must be between" in error for error in result["errors"])
        
        result = await temp_db.validate_work_week_settings("monday_friday", 1, 8)
        assert result["valid"] is False
        assert any("End day must be between" in error for error in result["errors"])
        
        # Test same start and end day
        result = await temp_db.validate_work_week_settings("monday_friday", 3, 3)
        assert result["valid"] is False
        assert any("cannot be the same" in error for error in result["errors"])
        
        # Test auto-correction for same day with monday_friday preset
        result = await temp_db.validate_work_week_settings("monday_friday", 3, 3)
        assert "start_day" in result["auto_corrections"]
        assert "end_day" in result["auto_corrections"]
        assert result["auto_corrections"]["start_day"] == 1
        assert result["auto_corrections"]["end_day"] == 5
    
    @pytest.mark.asyncio
    async def test_work_week_database_indexes(self, temp_db):
        """Test that database indexes are created for work week queries."""
        async with temp_db.get_session() as session:
            # Test query performance with indexes
            # This is a basic test - in production, you'd measure query times
            
            # Query by user_id (should use idx_work_week_settings_user)
            stmt = select(WorkWeekSettings).where(WorkWeekSettings.user_id == "default")
            result = await session.execute(stmt)
            settings = result.scalar_one_or_none()
            assert settings is not None
            
            # Query by preset (should use idx_work_week_settings_preset)
            stmt = select(WorkWeekSettings).where(WorkWeekSettings.work_week_preset == "monday_friday")
            result = await session.execute(stmt)
            settings = result.scalars().all()
            assert len(settings) >= 1


class TestWorkWeekMigration:
    """Test the work week migration script."""
    
    @pytest_asyncio.fixture
    async def temp_migration_db(self):
        """Create a temporary database for migration testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # Create basic database without work week settings
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
        async with engine.begin() as conn:
            # Create only basic tables, not work week settings
            await conn.execute(text("""
                CREATE TABLE web_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key VARCHAR UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    value_type VARCHAR NOT NULL,
                    description VARCHAR,
                    created_at DATETIME,
                    modified_at DATETIME
                );
            """))
        
        await engine.dispose()
        
        yield db_path
        
        # Cleanup
        os.unlink(db_path)
    
    @pytest.mark.asyncio
    async def test_migration_check_needed(self, temp_migration_db):
        """Test checking if migration is needed."""
        migration = WorkWeekMigration(temp_migration_db)
        await migration.initialize()
        
        try:
            # Should need migration since work_week_settings table doesn't exist
            needs_migration = await migration.check_migration_needed()
            assert needs_migration is True
        finally:
            await migration.close()
    
    @pytest.mark.asyncio
    async def test_run_migration(self, temp_migration_db):
        """Test running the migration."""
        migration = WorkWeekMigration(temp_migration_db)
        await migration.initialize()
        
        try:
            # Run migration
            result = await migration.run_migration()
            assert result["success"] is True
            assert result["tables_created"] == 1
            assert result["records_created"] == 1
            assert len(result["errors"]) == 0
            
            # Verify migration worked
            validation = await migration.validate_migration()
            assert validation["valid"] is True
            assert validation["table_exists"] is True
            assert validation["default_settings_exist"] is True
            
        finally:
            await migration.close()
    
    @pytest.mark.asyncio
    async def test_migration_rollback(self, temp_migration_db):
        """Test migration rollback."""
        migration = WorkWeekMigration(temp_migration_db)
        await migration.initialize()
        
        try:
            # Run migration first
            result = await migration.run_migration()
            assert result["success"] is True
            
            # Then rollback
            rollback_result = await migration.rollback_migration()
            assert rollback_result["success"] is True
            assert rollback_result["tables_dropped"] == 1
            
            # Verify rollback worked - migration should be needed again
            needs_migration = await migration.check_migration_needed()
            assert needs_migration is True
            
        finally:
            await migration.close()
    
    @pytest.mark.asyncio
    async def test_migration_idempotency(self, temp_migration_db):
        """Test that migration can be run multiple times safely."""
        migration = WorkWeekMigration(temp_migration_db)
        await migration.initialize()
        
        try:
            # Run migration first time
            result1 = await migration.run_migration()
            assert result1["success"] is True
            
            # Run migration second time
            result2 = await migration.run_migration()
            assert result2["success"] is True
            
            # Should still be valid
            validation = await migration.validate_migration()
            assert validation["valid"] is True
            
        finally:
            await migration.close()


class TestWorkWeekDatabaseIntegration:
    """Test integration between work week settings and existing database operations."""
    
    @pytest_asyncio.fixture
    async def integrated_db(self):
        """Create a database with both existing and work week schema."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # Initialize full database
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()
        
        yield db_manager
        
        # Cleanup
        await db_manager.engine.dispose()
        os.unlink(db_path)
    
    @pytest.mark.asyncio
    async def test_database_health_check_with_work_week(self, integrated_db):
        """Test that database health check works with work week schema."""
        health = await integrated_db.health_check()
        assert health["status"] == "healthy"
        assert "entry_count" in health
        assert health["connection"] == "active"
    
    @pytest.mark.asyncio
    async def test_create_work_week_migration_utility(self, integrated_db):
        """Test the create_work_week_migration utility method."""
        # This should work even if settings already exist
        result = await integrated_db.create_work_week_migration()
        assert result["success"] is True
        assert len(result["errors"]) == 0
        
        # Verify settings exist
        settings = await integrated_db.get_work_week_settings("default")
        assert settings is not None
    
    @pytest.mark.asyncio
    async def test_work_week_settings_timestamps(self, integrated_db):
        """Test that work week settings have proper timestamps."""
        # Get initial settings
        settings = await integrated_db.get_work_week_settings("default")
        initial_modified = settings["modified_at"]
        
        # Wait a bit to ensure timestamp difference
        await asyncio.sleep(0.1)
        
        # Update settings
        await integrated_db.update_work_week_settings(
            user_id="default",
            preset="sunday_thursday"
        )
        
        # Check that modified_at was updated
        updated_settings = await integrated_db.get_work_week_settings("default")
        assert updated_settings["modified_at"] > initial_modified
        # created_at should be very close to initial_modified (within 1 second)
        time_diff = abs((updated_settings["created_at"] - initial_modified).total_seconds())
        assert time_diff < 1.0, f"Created timestamp changed unexpectedly: {time_diff} seconds difference"


@pytest.mark.asyncio
async def test_work_week_schema_backward_compatibility():
    """Test that existing database operations still work with work week schema."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager(db_path)
        await db_manager.initialize()
        
        # Test existing functionality still works
        stats = await db_manager.get_database_stats()
        assert "total_entries" in stats
        assert "database_size_mb" in stats
        
        # Test settings operations still work
        success = await db_manager.set_setting("test_key", "test_value", "string", "Test setting")
        assert success is True
        
        setting = await db_manager.get_setting("test_key")
        assert setting is not None
        assert setting["value"] == "test_value"
        
        all_settings = await db_manager.get_all_settings()
        assert "test_key" in all_settings
        
        # Cleanup
        await db_manager.engine.dispose()
        
    finally:
        os.unlink(db_path)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])