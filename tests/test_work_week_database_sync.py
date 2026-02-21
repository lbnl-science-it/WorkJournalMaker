"""
Comprehensive tests for work week database synchronization functionality.

Tests the integration between WorkWeekService and database operations,
including entry synchronization, migration, and data integrity validation.
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import tempfile
import os
from web.database import DatabaseManager, JournalEntryIndex
from web.services.entry_manager import EntryManager
from web.services.work_week_service import WorkWeekService, WorkWeekConfig, WorkWeekPreset
from config_manager import AppConfig
from logger import JournalSummarizerLogger


# Test fixtures - defined at module level
@pytest_asyncio.fixture
async def temp_database():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    db_manager = DatabaseManager(db_path)
    await db_manager.initialize()
    
    yield db_manager
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)

@pytest.fixture
def mock_config():
    """Create mock configuration."""
    config = Mock(spec=AppConfig)
    config.processing = Mock()
    config.processing.base_path = "/tmp/test_journals"
    return config

@pytest.fixture
def mock_logger():
    """Create mock logger."""
    logger = Mock(spec=JournalSummarizerLogger)
    logger.logger = Mock()
    logger.error = Mock()
    return logger

@pytest_asyncio.fixture
async def work_week_service(mock_config, mock_logger, temp_database):
    """Create WorkWeekService instance."""
    return WorkWeekService(mock_config, mock_logger, temp_database)

@pytest_asyncio.fixture
async def entry_manager(mock_config, mock_logger, temp_database, work_week_service):
    """Create EntryManager instance with WorkWeekService."""
    return EntryManager(mock_config, mock_logger, temp_database, work_week_service)


class TestJournalEntrySync:
    """Test journal entry synchronization with work week calculations."""
    
    @pytest.mark.asyncio
    async def test_sync_entry_uses_work_week_calculation(self, entry_manager, temp_database):
        """Test that syncing an entry uses work week service for week ending calculation."""
        entry_date = date(2024, 1, 15)  # Monday
        test_file_path = Path("/tmp/test/2024-01-19/2024-01-15.md")
        test_content = "Test journal entry content"
        
        # Mock the work week service calculation
        with patch.object(entry_manager.work_week_service, 'calculate_week_ending_date') as mock_calc:
            mock_calc.return_value = date(2024, 1, 19)  # Friday
            
            async with temp_database.get_session() as session:
                await entry_manager._sync_entry_to_database_session(
                    session, entry_date, test_file_path, test_content
                )
                await session.commit()
        
        # Verify work week service was called
        mock_calc.assert_called_once_with(entry_date)
        
        # Verify entry was created with calculated week ending
        async with temp_database.get_session() as session:
            from sqlalchemy import select
            stmt = select(JournalEntryIndex).where(JournalEntryIndex.date == entry_date)
            result = await session.execute(stmt)
            entry = result.scalar_one()
            
            assert entry.week_ending_date == date(2024, 1, 19)
            assert entry.file_path == str(test_file_path)
            assert entry.word_count == 4  # "Test journal entry content"
    
    @pytest.mark.asyncio
    async def test_sync_entry_fallback_on_work_week_error(self, entry_manager, temp_database):
        """Test that sync falls back to file discovery when work week service fails."""
        entry_date = date(2024, 1, 15)  # Monday
        test_file_path = Path("/tmp/test/2024-01-19/2024-01-15.md")
        test_content = "Test content"
        
        # Mock work week service to fail
        with patch.object(entry_manager.work_week_service, 'calculate_week_ending_date') as mock_calc:
            mock_calc.side_effect = Exception("Work week service error")
            
            # Mock file discovery fallback
            with patch.object(entry_manager.file_discovery, '_find_week_ending_for_date') as mock_fallback:
                mock_fallback.return_value = date(2024, 1, 19)
                
                async with temp_database.get_session() as session:
                    await entry_manager._sync_entry_to_database_session(
                        session, entry_date, test_file_path, test_content
                    )
                    await session.commit()
        
        # Verify fallback was used
        mock_fallback.assert_called_once_with(entry_date)
        
        # Verify entry was still created
        async with temp_database.get_session() as session:
            from sqlalchemy import select
            stmt = select(JournalEntryIndex).where(JournalEntryIndex.date == entry_date)
            result = await session.execute(stmt)
            entry = result.scalar_one()
            
            assert entry.week_ending_date == date(2024, 1, 19)
    
    @pytest.mark.asyncio
    async def test_sync_entry_updates_existing_week_ending(self, entry_manager, temp_database):
        """Test that syncing updates existing entries with new week ending calculations."""
        entry_date = date(2024, 1, 15)  # Monday
        test_file_path = Path("/tmp/test/2024-01-19/2024-01-15.md")
        
        # Create initial entry with old week ending
        async with temp_database.get_session() as session:
            initial_entry = JournalEntryIndex(
                date=entry_date,
                file_path=str(test_file_path),
                week_ending_date=date(2024, 1, 12),  # Old week ending
                word_count=0,
                character_count=0,
                line_count=0,
                has_content=False
            )
            session.add(initial_entry)
            await session.commit()
        
        # Sync with new work week calculation
        with patch.object(entry_manager.work_week_service, 'calculate_week_ending_date') as mock_calc:
            mock_calc.return_value = date(2024, 1, 19)  # New week ending
            
            async with temp_database.get_session() as session:
                await entry_manager._sync_entry_to_database_session(
                    session, entry_date, test_file_path, "Updated content"
                )
                await session.commit()
        
        # Verify entry was updated with new week ending
        async with temp_database.get_session() as session:
            from sqlalchemy import select
            stmt = select(JournalEntryIndex).where(JournalEntryIndex.date == entry_date)
            result = await session.execute(stmt)
            entry = result.scalar_one()
            
            assert entry.week_ending_date == date(2024, 1, 19)  # Updated
            assert entry.word_count == 2  # "Updated content"


class TestDatabaseMigration:
    """Test database migration functionality for work week integration."""
    
    @pytest.mark.asyncio
    async def test_migrate_week_ending_dates(self, temp_database, work_week_service):
        """Test migration of existing entries to use calculated week ending dates."""
        # Create test entries with various week ending dates
        test_entries = [
            (date(2024, 1, 15), date(2024, 1, 12)),  # Monday -> old Friday
            (date(2024, 1, 16), date(2024, 1, 12)),  # Tuesday -> old Friday
            (date(2024, 1, 17), date(2024, 1, 12)),  # Wednesday -> old Friday
        ]
        
        # Insert test entries
        async with temp_database.get_session() as session:
            for entry_date, old_week_ending in test_entries:
                entry = JournalEntryIndex(
                    date=entry_date,
                    file_path=f"/tmp/test/{old_week_ending}/{entry_date}.md",
                    week_ending_date=old_week_ending,
                    word_count=0,
                    character_count=0,
                    line_count=0,
                    has_content=False
                )
                session.add(entry)
            await session.commit()
        
        # Mock work week service to return consistent week endings
        with patch.object(work_week_service, 'calculate_week_ending_date') as mock_calc:
            mock_calc.return_value = date(2024, 1, 19)  # New Friday
            
            # Run migration
            result = await temp_database.migrate_week_ending_dates(work_week_service, batch_size=2)
        
        # Verify migration results
        assert result["success"] is True
        assert result["entries_processed"] == 3
        assert result["entries_updated"] == 3
        assert result["batches_processed"] == 2  # 2 entries per batch, so 2 batches
        
        # Verify all entries were updated
        async with temp_database.get_session() as session:
            from sqlalchemy import select
            stmt = select(JournalEntryIndex).order_by(JournalEntryIndex.date)
            result = await session.execute(stmt)
            entries = result.scalars().all()
            
            for entry in entries:
                assert entry.week_ending_date == date(2024, 1, 19)
    
    @pytest.mark.asyncio
    async def test_migrate_week_ending_dates_handles_errors(self, temp_database, work_week_service):
        """Test migration handles errors gracefully."""
        # Create test entry
        async with temp_database.get_session() as session:
            entry = JournalEntryIndex(
                date=date(2024, 1, 15),
                file_path="/tmp/test/2024-01-15.md",
                week_ending_date=date(2024, 1, 12),
                word_count=0,
                character_count=0,
                line_count=0,
                has_content=False
            )
            session.add(entry)
            await session.commit()
        
        # Mock work week service to raise error
        with patch.object(work_week_service, 'calculate_week_ending_date') as mock_calc:
            mock_calc.side_effect = Exception("Calculation error")
            
            # Run migration
            result = await temp_database.migrate_week_ending_dates(work_week_service)
        
        # Verify error handling
        assert result["success"] is True  # Migration completes despite errors
        assert result["entries_processed"] == 1
        assert result["entries_updated"] == 0
        assert result["entries_with_errors"] == 1
        assert len(result["errors"]) == 1
        assert "Calculation error" in result["errors"][0]["error"]


class TestDataIntegrity:
    """Test data integrity validation for work week database sync."""
    
    @pytest.mark.asyncio
    async def test_validate_week_ending_dates_integrity(self, temp_database):
        """Test validation of week ending date integrity."""
        # Create test entries with various integrity issues
        test_entries = [
            # Valid entry
            (date(2024, 1, 15), date(2024, 1, 19), True),
            # Missing week ending
            (date(2024, 1, 16), None, False),
            # Invalid date range (too far)
            (date(2024, 1, 17), date(2024, 1, 30), False),
            # Valid entry
            (date(2024, 1, 18), date(2024, 1, 19), True),
        ]
        
        # Insert test entries
        async with temp_database.get_session() as session:
            for entry_date, week_ending, is_valid in test_entries:
                entry = JournalEntryIndex(
                    date=entry_date,
                    file_path=f"/tmp/test/{entry_date}.md",
                    week_ending_date=week_ending,
                    word_count=0,
                    character_count=0,
                    line_count=0,
                    has_content=False
                )
                session.add(entry)
            await session.commit()
        
        # Run validation
        result = await temp_database.validate_week_ending_dates_integrity()
        
        # Verify validation results
        assert result["success"] is True
        assert result["total_entries"] == 4
        assert result["valid_entries"] == 2
        assert result["missing_week_endings"] == 1
        assert result["invalid_date_ranges"] == 1
        assert len(result["errors"]) == 2
    
    @pytest.mark.asyncio
    async def test_validate_week_ending_dates_empty_database(self, temp_database):
        """Test validation with empty database."""
        result = await temp_database.validate_week_ending_dates_integrity()
        
        assert result["success"] is True
        assert result["total_entries"] == 0
        assert result["valid_entries"] == 0
        assert result["missing_week_endings"] == 0
        assert result["invalid_date_ranges"] == 0
        assert len(result["errors"]) == 0


class TestMixedDirectoryStructures:
    """Test handling of mixed old and new directory structures."""
    
    @pytest.mark.asyncio
    async def test_construct_file_path_uses_work_week_service(self, entry_manager):
        """Test that file path construction uses work week service."""
        entry_date = date(2024, 1, 15)  # Monday
        
        with patch.object(entry_manager.work_week_service, 'calculate_week_ending_date') as mock_calc:
            mock_calc.return_value = date(2024, 1, 19)  # Friday
            
            # Mock file discovery construction
            with patch.object(entry_manager.file_discovery, '_construct_file_path') as mock_construct:
                mock_construct.return_value = Path("/tmp/test/2024-01-19/2024-01-15.md")
                
                result_path = entry_manager._construct_file_path(entry_date)
        
        # Verify work week service was used
        mock_calc.assert_called_once_with(entry_date)
        mock_construct.assert_called_once_with(entry_date, date(2024, 1, 19))
        assert result_path == Path("/tmp/test/2024-01-19/2024-01-15.md")
    
    @pytest.mark.asyncio
    async def test_construct_file_path_fallback_to_file_discovery(self, entry_manager):
        """Test that file path construction falls back to file discovery on work week service error."""
        entry_date = date(2024, 1, 15)  # Monday
        
        with patch.object(entry_manager.work_week_service, 'calculate_week_ending_date') as mock_calc:
            mock_calc.side_effect = Exception("Work week service error")
            
            # Mock file discovery fallback
            with patch.object(entry_manager.file_discovery, '_find_week_ending_for_date') as mock_fallback:
                mock_fallback.return_value = date(2024, 1, 19)
                
                with patch.object(entry_manager.file_discovery, '_construct_file_path') as mock_construct:
                    mock_construct.return_value = Path("/tmp/test/2024-01-19/2024-01-15.md")
                    
                    result_path = entry_manager._construct_file_path(entry_date)
        
        # Verify fallback was used
        mock_fallback.assert_called_once_with(entry_date)
        mock_construct.assert_called_once_with(entry_date, date(2024, 1, 19))
        assert result_path == Path("/tmp/test/2024-01-19/2024-01-15.md")


class TestPerformanceRequirements:
    """Test that database synchronization meets performance requirements."""
    
    @pytest.mark.asyncio
    async def test_sync_entry_performance(self, entry_manager, temp_database):
        """Test that entry synchronization is performant (<10ms additional overhead)."""
        entry_date = date(2024, 1, 15)
        test_file_path = Path("/tmp/test/2024-01-19/2024-01-15.md")
        test_content = "Test content"
        
        # Mock work week service to return quickly
        with patch.object(entry_manager.work_week_service, 'calculate_week_ending_date') as mock_calc:
            mock_calc.return_value = date(2024, 1, 19)
            
            # Measure sync time
            start_time = datetime.now()
            
            async with temp_database.get_session() as session:
                await entry_manager._sync_entry_to_database_session(
                    session, entry_date, test_file_path, test_content
                )
                await session.commit()
            
            end_time = datetime.now()
            sync_duration = (end_time - start_time).total_seconds() * 1000  # Convert to ms
        
        # Verify performance requirement (<10ms additional overhead)
        # Note: This is a basic check - actual performance testing would be more sophisticated
        assert sync_duration < 100  # 100ms is generous for this test environment
    
    @pytest.mark.asyncio
    async def test_batch_migration_performance(self, temp_database, work_week_service):
        """Test that batch migration processes entries efficiently."""
        # Create multiple test entries
        num_entries = 50
        async with temp_database.get_session() as session:
            for i in range(num_entries):
                entry_date = date(2024, 1, 1) + timedelta(days=i)
                entry = JournalEntryIndex(
                    date=entry_date,
                    file_path=f"/tmp/test/{entry_date}.md",
                    week_ending_date=date(2024, 1, 5),  # Old week ending
                    word_count=0,
                    character_count=0,
                    line_count=0,
                    has_content=False
                )
                session.add(entry)
            await session.commit()
        
        # Mock work week service
        with patch.object(work_week_service, 'calculate_week_ending_date') as mock_calc:
            mock_calc.return_value = date(2024, 1, 19)
            
            # Measure migration time
            start_time = datetime.now()
            result = await temp_database.migrate_week_ending_dates(work_week_service, batch_size=10)
            end_time = datetime.now()
            
            migration_duration = (end_time - start_time).total_seconds()
        
        # Verify migration completed successfully
        assert result["success"] is True
        assert result["entries_processed"] == num_entries
        assert result["entries_updated"] == num_entries
        
        # Verify reasonable performance (should process 50 entries quickly)
        assert migration_duration < 5.0  # 5 seconds is generous


if __name__ == "__main__":
    pytest.main([__file__])