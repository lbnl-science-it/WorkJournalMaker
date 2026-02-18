"""
Integration Tests for Calendar Service

This module contains integration tests for the CalendarService,
testing its interaction with the database and FileDiscovery components.
"""

import pytest
import asyncio
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from web.services.calendar_service import CalendarService, CalendarDay
from web.models.journal import CalendarEntry, CalendarMonth, EntryStatus
from web.database import DatabaseManager, JournalEntryIndex
from config_manager import AppConfig
from logger import JournalSummarizerLogger
from file_discovery import FileDiscovery


class TestCalendarServiceIntegration:
    """Integration tests for CalendarService."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = MagicMock(spec=AppConfig)
        mock_processing = MagicMock()
        mock_processing.base_path = Path("/test/journal/path")
        config.processing = mock_processing
        return config
    
    @pytest.fixture
    def mock_logger(self):
        """Create mock logger."""
        return MagicMock(spec=JournalSummarizerLogger)
    
    @pytest.fixture
    def mock_db_manager(self):
        """Create mock database manager."""
        return AsyncMock(spec=DatabaseManager)
    
    @pytest.fixture
    def mock_file_discovery(self):
        """Create mock file discovery."""
        return MagicMock(spec=FileDiscovery)
    
    @pytest.fixture
    def calendar_service(self, mock_config, mock_logger, mock_db_manager):
        """Create CalendarService instance with mocked dependencies."""
        with patch('web.services.calendar_service.FileDiscovery') as mock_fd_class:
            mock_fd_instance = MagicMock(spec=FileDiscovery)
            mock_fd_class.return_value = mock_fd_instance
            
            service = CalendarService(mock_config, mock_logger, mock_db_manager)
            service.file_discovery = mock_fd_instance
            return service
    
    @pytest.fixture
    def sample_db_entries(self):
        """Sample database entries for testing."""
        entries = []
        for day in range(1, 6):  # 5 entries
            entry = MagicMock(spec=JournalEntryIndex)
            entry.date = date(2024, 1, day)
            entry.has_content = day % 2 == 1  # Odd days have content
            entry.word_count = 150 if entry.has_content else 0
            entry.file_path = f"/test/path/2024-01-{day:02d}.md"
            entry.modified_at = datetime(2024, 1, day, 10, 0, 0)
            entries.append(entry)
        return entries
    
    @pytest.mark.asyncio
    async def test_get_calendar_month_success(self, calendar_service, mock_db_manager, sample_db_entries):
        """Test successful calendar month generation."""
        # Mock database session and query
        mock_session = AsyncMock()
        mock_db_manager.get_session.return_value.__aenter__.return_value = mock_session
        
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = sample_db_entries
        mock_session.execute.return_value = mock_result
        
        # Test the method
        result = await calendar_service.get_calendar_month(2024, 1)
        
        # Verify result
        assert isinstance(result, CalendarMonth)
        assert result.year == 2024
        assert result.month == 1
        assert result.month_name == "January"
        assert len(result.entries) > 0
        
        # Verify database was queried
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_calendar_month_invalid_month(self, calendar_service):
        """Test calendar month generation with invalid month."""
        with pytest.raises(ValueError, match="Invalid month"):
            await calendar_service.get_calendar_month(2024, 13)
    
    @pytest.mark.asyncio
    async def test_get_calendar_month_invalid_year(self, calendar_service):
        """Test calendar month generation with invalid year."""
        with pytest.raises(ValueError, match="Invalid year"):
            await calendar_service.get_calendar_month(1800, 1)
    
    @pytest.mark.asyncio
    async def test_has_entry_for_date_exists(self, calendar_service, mock_db_manager):
        """Test checking entry existence when entry exists."""
        # Mock database session and query
        mock_session = AsyncMock()
        mock_db_manager.get_session.return_value.__aenter__.return_value = mock_session
        
        mock_entry = MagicMock(spec=JournalEntryIndex)
        mock_entry.has_content = True
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_entry
        mock_session.execute.return_value = mock_result
        
        # Test the method
        test_date = date(2024, 1, 15)
        result = await calendar_service.has_entry_for_date(test_date)
        
        # Verify result
        assert result is True
        mock_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_has_entry_for_date_not_exists(self, calendar_service, mock_db_manager):
        """Test checking entry existence when entry doesn't exist."""
        # Mock database session and query
        mock_session = AsyncMock()
        mock_db_manager.get_session.return_value.__aenter__.return_value = mock_session
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        # Test the method
        test_date = date(2024, 1, 15)
        result = await calendar_service.has_entry_for_date(test_date)
        
        # Verify result
        assert result is False
    
    @pytest.mark.asyncio
    async def test_has_entry_for_date_database_error(self, calendar_service, mock_db_manager, mock_logger):
        """Test entry existence check with database error."""
        # Mock database session to raise an error
        mock_db_manager.get_session.side_effect = Exception("Database error")
        
        # Test the method
        test_date = date(2024, 1, 15)
        result = await calendar_service.has_entry_for_date(test_date)
        
        # Should return False on error and log the error
        assert result is False
        mock_logger.log_error_with_category.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_entries_for_date_range_success(self, calendar_service, mock_db_manager, sample_db_entries):
        """Test successful retrieval of entries for date range."""
        # Mock database session and query
        mock_session = AsyncMock()
        mock_db_manager.get_session.return_value.__aenter__.return_value = mock_session
        
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = sample_db_entries
        mock_session.execute.return_value = mock_result
        
        # Test the method
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 5)
        result = await calendar_service.get_entries_for_date_range(start_date, end_date)
        
        # Verify result
        assert len(result) == 5
        assert all(isinstance(entry, CalendarEntry) for entry in result)
        
        # Check that entries are properly converted
        for i, entry in enumerate(result):
            assert entry.date == sample_db_entries[i].date
            assert entry.has_content == sample_db_entries[i].has_content
            assert entry.word_count == sample_db_entries[i].word_count
    
    @pytest.mark.asyncio
    async def test_get_entries_for_date_range_database_error(self, calendar_service, mock_db_manager, mock_logger):
        """Test date range query with database error."""
        # Mock database session to raise an error
        mock_db_manager.get_session.side_effect = Exception("Database error")
        
        # Test the method
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 5)
        result = await calendar_service.get_entries_for_date_range(start_date, end_date)
        
        # Should return empty list on error and log the error
        assert result == []
        mock_logger.log_error_with_category.assert_called_once()
    
    def test_get_week_ending_date(self, calendar_service):
        """Test week ending date calculation."""
        # Mock the file discovery method
        test_date = date(2024, 1, 15)  # Monday
        expected_week_ending = date(2024, 1, 19)  # Friday
        
        calendar_service.file_discovery._calculate_week_ending_for_date.return_value = expected_week_ending
        
        # Test the method
        result = calendar_service.get_week_ending_date(test_date)
        
        # Verify result
        assert result == expected_week_ending
        calendar_service.file_discovery._calculate_week_ending_for_date.assert_called_once_with(test_date)
    
    @pytest.mark.asyncio
    async def test_get_today_info_success(self, calendar_service, mock_db_manager):
        """Test successful retrieval of today's information."""
        today = date.today()
        
        # Mock database session for entry check
        mock_session = AsyncMock()
        mock_db_manager.get_session.return_value.__aenter__.return_value = mock_session
        
        mock_entry = MagicMock(spec=JournalEntryIndex)
        mock_entry.word_count = 150
        mock_entry.has_content = True
        mock_entry.file_path = "/test/path/today.md"
        mock_entry.modified_at = datetime.now()
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_entry
        mock_session.execute.return_value = mock_result
        
        # Mock week ending calculation
        week_ending = today + timedelta(days=4)
        calendar_service.file_discovery._calculate_week_ending_for_date.return_value = week_ending
        
        # Test the method
        result = await calendar_service.get_today_info()
        
        # Verify result
        assert result["today"] == today
        assert result["has_entry"] is True
        assert result["entry_metadata"]["word_count"] == 150
        assert result["week_ending_date"] == week_ending
        assert result["current_month"] == today.month
        assert result["current_year"] == today.year
    
    @pytest.mark.asyncio
    async def test_get_today_info_no_entry(self, calendar_service, mock_db_manager):
        """Test today's information when no entry exists."""
        today = date.today()
        
        # Mock database session for entry check
        mock_session = AsyncMock()
        mock_db_manager.get_session.return_value.__aenter__.return_value = mock_session
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result
        
        # Mock week ending calculation
        week_ending = today + timedelta(days=4)
        calendar_service.file_discovery._calculate_week_ending_for_date.return_value = week_ending
        
        # Test the method
        result = await calendar_service.get_today_info()
        
        # Verify result
        assert result["today"] == today
        assert result["has_entry"] is False
        assert result["entry_metadata"] is None
        assert result["week_ending_date"] == week_ending
    
    @pytest.mark.asyncio
    async def test_get_today_info_database_error(self, calendar_service, mock_db_manager, mock_logger):
        """Test today's information with database error."""
        today = date.today()
        
        # Mock database session to raise an error
        mock_db_manager.get_session.side_effect = Exception("Database error")
        
        # Test the method
        result = await calendar_service.get_today_info()
        
        # Should return default values on error
        assert result["today"] == today
        assert result["has_entry"] is False
        assert result["entry_metadata"] is None
        mock_logger.log_error_with_category.assert_called_once()
    
    def test_get_adjacent_months_january(self, calendar_service):
        """Test adjacent months calculation for January."""
        prev, next_month = asyncio.run(calendar_service.get_adjacent_months(2024, 1))
        
        assert prev == (2023, 12)  # Previous December
        assert next_month == (2024, 2)  # Next February
    
    def test_get_adjacent_months_december(self, calendar_service):
        """Test adjacent months calculation for December."""
        prev, next_month = asyncio.run(calendar_service.get_adjacent_months(2024, 12))
        
        assert prev == (2024, 11)  # Previous November
        assert next_month == (2025, 1)  # Next January
    
    def test_get_adjacent_months_regular(self, calendar_service):
        """Test adjacent months calculation for regular month."""
        prev, next_month = asyncio.run(calendar_service.get_adjacent_months(2024, 6))
        
        assert prev == (2024, 5)  # Previous May
        assert next_month == (2024, 7)  # Next July
    
    @pytest.mark.asyncio
    async def test_generate_calendar_grid(self, calendar_service):
        """Test calendar grid generation."""
        # Create test entries dictionary
        entries_dict = {
            date(2024, 1, 1): {
                "has_content": True,
                "word_count": 150,
                "status": EntryStatus.COMPLETE
            },
            date(2024, 1, 15): {
                "has_content": False,
                "word_count": 0,
                "status": EntryStatus.EMPTY
            }
        }
        
        # Test the private method
        result = await calendar_service._generate_calendar_grid(2024, 1, entries_dict)
        
        # Verify result
        assert len(result) > 0
        assert all(isinstance(day, CalendarDay) for day in result)
        
        # Find specific days to verify
        jan_1 = next((day for day in result if day.date == date(2024, 1, 1)), None)
        jan_15 = next((day for day in result if day.date == date(2024, 1, 15)), None)
        
        assert jan_1 is not None
        assert jan_1.has_entry is True
        assert jan_1.word_count == 150
        
        assert jan_15 is not None
        assert jan_15.has_entry is False
        assert jan_15.word_count == 0


class TestCalendarServiceEdgeCases:
    """Test edge cases for CalendarService."""
    
    @pytest.fixture
    def calendar_service(self):
        """Create minimal CalendarService for edge case testing."""
        mock_config = MagicMock()
        mock_config.processing.base_path = Path("/test")
        mock_logger = MagicMock()
        mock_db_manager = AsyncMock()
        
        with patch('web.services.calendar_service.FileDiscovery'):
            return CalendarService(mock_config, mock_logger, mock_db_manager)
    
    @pytest.mark.asyncio
    async def test_leap_year_february(self, calendar_service, mock_db_manager):
        """Test calendar generation for February in a leap year."""
        # Mock empty database response
        mock_session = AsyncMock()
        mock_db_manager.get_session.return_value.__aenter__.return_value = mock_session
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        
        # Test leap year February (2024)
        result = await calendar_service.get_calendar_month(2024, 2)
        
        assert result.year == 2024
        assert result.month == 2
        assert result.month_name == "February"
    
    @pytest.mark.asyncio
    async def test_non_leap_year_february(self, calendar_service, mock_db_manager):
        """Test calendar generation for February in a non-leap year."""
        # Mock empty database response
        mock_session = AsyncMock()
        mock_db_manager.get_session.return_value.__aenter__.return_value = mock_session
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        
        # Test non-leap year February (2023)
        result = await calendar_service.get_calendar_month(2023, 2)
        
        assert result.year == 2023
        assert result.month == 2
        assert result.month_name == "February"
    
    @pytest.mark.asyncio
    async def test_boundary_years(self, calendar_service, mock_db_manager):
        """Test calendar generation for boundary years."""
        # Mock empty database response
        mock_session = AsyncMock()
        mock_db_manager.get_session.return_value.__aenter__.return_value = mock_session
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result
        
        # Test minimum year
        result = await calendar_service.get_calendar_month(1900, 1)
        assert result.year == 1900
        
        # Test maximum year
        result = await calendar_service.get_calendar_month(3000, 12)
        assert result.year == 3000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])