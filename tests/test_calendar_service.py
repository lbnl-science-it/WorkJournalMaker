"""
Comprehensive tests for CalendarService implementation

Tests calendar functionality, navigation, entry indicators, and integration
with existing FileDiscovery and database components.
"""

import pytest
import pytest_asyncio
import asyncio
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from config_manager import AppConfig
from logger import JournalSummarizerLogger, LogConfig, LogLevel
from web.database import DatabaseManager, JournalEntryIndex
from web.services.calendar_service import CalendarService, CalendarDay
from web.models.journal import CalendarEntry, CalendarMonth, EntryStatus, TodayResponse

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


class TestCalendarService:
    """Test suite for CalendarService functionality."""
    
    @pytest_asyncio.fixture
    async def setup_service(self):
        """Set up CalendarService with test dependencies."""
        # Create test configuration
        config = AppConfig()
        log_config = LogConfig(level=LogLevel.INFO, console_output=False, file_output=False)
        logger = JournalSummarizerLogger(log_config)
        
        # Create test database
        db_manager = DatabaseManager("tests/test_calendar_service.db")
        await db_manager.initialize()
        
        # Create service
        service = CalendarService(config, logger, db_manager)
        
        yield service, db_manager
        
        # Cleanup
        try:
            Path("tests/test_calendar_service.db").unlink(missing_ok=True)
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_calendar_month_generation(self, setup_service):
        """Test calendar month generation with various scenarios."""
        service, db_manager = setup_service
        
        # Test current month
        today = date.today()
        calendar_month = await service.get_calendar_month(today.year, today.month)
        
        assert isinstance(calendar_month, CalendarMonth)
        assert calendar_month.year == today.year
        assert calendar_month.month == today.month
        assert calendar_month.today == today
        assert len(calendar_month.entries) > 0  # Should have entries for all days in month
        
        # Test specific month
        calendar_month = await service.get_calendar_month(2024, 6)
        assert calendar_month.year == 2024
        assert calendar_month.month == 6
        assert calendar_month.month_name == "June"
        assert len(calendar_month.entries) == 30  # June has 30 days
    
    @pytest.mark.asyncio
    async def test_calendar_month_validation(self, setup_service):
        """Test calendar month validation with invalid inputs."""
        service, db_manager = await setup_service
        
        # Test invalid month
        with pytest.raises(ValueError, match="Invalid month"):
            await service.get_calendar_month(2024, 13)
        
        with pytest.raises(ValueError, match="Invalid month"):
            await service.get_calendar_month(2024, 0)
        
        # Test invalid year
        with pytest.raises(ValueError, match="Invalid year"):
            await service.get_calendar_month(1800, 6)
        
        with pytest.raises(ValueError, match="Invalid year"):
            await service.get_calendar_month(3100, 6)
    
    @pytest.mark.asyncio
    async def test_adjacent_months_navigation(self, setup_service):
        """Test month navigation calculations."""
        service, db_manager = await setup_service
        
        # Test regular month
        (prev_year, prev_month), (next_year, next_month) = await service.get_adjacent_months(2024, 6)
        assert (prev_year, prev_month) == (2024, 5)
        assert (next_year, next_month) == (2024, 7)
        
        # Test January (year boundary)
        (prev_year, prev_month), (next_year, next_month) = await service.get_adjacent_months(2024, 1)
        assert (prev_year, prev_month) == (2023, 12)
        assert (next_year, next_month) == (2024, 2)
        
        # Test December (year boundary)
        (prev_year, prev_month), (next_year, next_month) = await service.get_adjacent_months(2024, 12)
        assert (prev_year, prev_month) == (2024, 11)
        assert (next_year, next_month) == (2025, 1)
    
    @pytest.mark.asyncio
    async def test_entry_existence_checking(self, setup_service):
        """Test entry existence checking functionality."""
        service, db_manager = await setup_service
        
        test_date = date(2024, 6, 15)
        
        # Test with no entry
        has_entry = await service.has_entry_for_date(test_date)
        assert has_entry is False
        
        # Add test entry to database
        async with db_manager.get_session() as session:
            test_entry = JournalEntryIndex(
                date=test_date,
                file_path="/test/path.txt",
                week_ending_date=test_date,
                has_content=True,
                word_count=100
            )
            session.add(test_entry)
            await session.commit()
        
        # Test with entry
        has_entry = await service.has_entry_for_date(test_date)
        assert has_entry is True
    
    @pytest.mark.asyncio
    async def test_date_range_queries(self, setup_service):
        """Test date range entry retrieval."""
        service, db_manager = await setup_service
        
        # Add test entries
        test_dates = [
            date(2024, 6, 10),
            date(2024, 6, 15),
            date(2024, 6, 20),
            date(2024, 6, 25)
        ]
        
        async with db_manager.get_session() as session:
            for test_date in test_dates:
                test_entry = JournalEntryIndex(
                    date=test_date,
                    file_path=f"/test/path_{test_date.isoformat()}.txt",
                    week_ending_date=test_date,
                    has_content=True,
                    word_count=50 + test_date.day
                )
                session.add(test_entry)
            await session.commit()
        
        # Test date range query
        entries = await service.get_entries_for_date_range(
            date(2024, 6, 12), 
            date(2024, 6, 22)
        )
        
        assert len(entries) == 2  # Should find entries for 6/15 and 6/20
        assert all(isinstance(entry, CalendarEntry) for entry in entries)
        assert all(entry.has_content for entry in entries)
        
        # Test empty range
        entries = await service.get_entries_for_date_range(
            date(2024, 5, 1), 
            date(2024, 5, 31)
        )
        assert len(entries) == 0
    
    @pytest.mark.asyncio
    async def test_today_info_generation(self, setup_service):
        """Test today's information generation."""
        service, db_manager = await setup_service
        
        today_info = await service.get_today_info()
        
        assert isinstance(today_info, dict)
        assert today_info["today"] == date.today()
        assert isinstance(today_info["day_name"], str)
        assert isinstance(today_info["formatted_date"], str)
        assert isinstance(today_info["has_entry"], bool)
        assert isinstance(today_info["week_ending_date"], date)
        assert isinstance(today_info["current_month"], int)
        assert isinstance(today_info["current_year"], int)
        
        # Test with today's entry
        today = date.today()
        async with db_manager.get_session() as session:
            today_entry = JournalEntryIndex(
                date=today,
                file_path="/test/today.txt",
                week_ending_date=today,
                has_content=True,
                word_count=200
            )
            session.add(today_entry)
            await session.commit()
        
        today_info = await service.get_today_info()
        assert today_info["has_entry"] is True
        assert today_info["entry_metadata"] is not None
        assert today_info["entry_metadata"]["word_count"] == 200
    
    @pytest.mark.asyncio
    async def test_week_ending_calculation(self, setup_service):
        """Test week ending date calculation integration."""
        service, db_manager = await setup_service
        
        test_date = date(2024, 6, 15)
        week_ending = service.get_week_ending_date(test_date)
        
        # Should use FileDiscovery logic (currently returns same date)
        assert isinstance(week_ending, date)
        assert week_ending == test_date
    
    @pytest.mark.asyncio
    async def test_calendar_day_dataclass(self, setup_service):
        """Test CalendarDay dataclass functionality."""
        service, db_manager = await setup_service
        
        test_date = date(2024, 6, 15)
        calendar_day = CalendarDay(
            date=test_date,
            day_number=15,
            is_current_month=True,
            is_today=False,
            has_entry=True,
            entry_status=EntryStatus.COMPLETE,
            word_count=150
        )
        
        assert calendar_day.date == test_date
        assert calendar_day.day_number == 15
        assert calendar_day.is_current_month is True
        assert calendar_day.is_today is False
        assert calendar_day.has_entry is True
        assert calendar_day.entry_status == EntryStatus.COMPLETE
        assert calendar_day.word_count == 150
    
    @pytest.mark.asyncio
    async def test_calendar_grid_generation(self, setup_service):
        """Test internal calendar grid generation."""
        service, db_manager = await setup_service
        
        # Add some test entries
        test_entries = {
            date(2024, 6, 10): {"has_content": True, "word_count": 100, "status": EntryStatus.COMPLETE},
            date(2024, 6, 15): {"has_content": False, "word_count": 0, "status": EntryStatus.EMPTY},
        }
        
        calendar_days = await service._generate_calendar_grid(2024, 6, test_entries)
        
        assert len(calendar_days) == 30  # June has 30 days
        assert all(isinstance(day, CalendarDay) for day in calendar_days)
        
        # Check specific entries
        day_10 = next(day for day in calendar_days if day.day_number == 10)
        assert day_10.has_entry is True
        assert day_10.word_count == 100
        assert day_10.entry_status == EntryStatus.COMPLETE
        
        day_15 = next(day for day in calendar_days if day.day_number == 15)
        assert day_15.has_entry is False
        assert day_15.word_count == 0
        assert day_15.entry_status == EntryStatus.EMPTY
    
    @pytest.mark.asyncio
    async def test_error_handling(self, setup_service):
        """Test error handling in various scenarios."""
        service, db_manager = await setup_service
        
        # Test database error handling
        with patch.object(db_manager, 'get_session', side_effect=Exception("Database error")):
            has_entry = await service.has_entry_for_date(date.today())
            assert has_entry is False  # Should return False on error
            
            entries = await service.get_entries_for_date_range(date.today(), date.today())
            assert entries == []  # Should return empty list on error
    
    @pytest.mark.asyncio
    async def test_month_entries_retrieval(self, setup_service):
        """Test internal month entries retrieval."""
        service, db_manager = await setup_service
        
        # Add test entries for June 2024
        test_dates = [date(2024, 6, i) for i in [5, 10, 15, 20, 25]]
        
        async with db_manager.get_session() as session:
            for i, test_date in enumerate(test_dates):
                test_entry = JournalEntryIndex(
                    date=test_date,
                    file_path=f"/test/path_{i}.txt",
                    week_ending_date=test_date,
                    has_content=i % 2 == 0,  # Alternate between has_content
                    word_count=(i + 1) * 50
                )
                session.add(test_entry)
            await session.commit()
        
        entries_dict = await service._get_month_entries(2024, 6)
        
        assert len(entries_dict) == 5
        assert date(2024, 6, 5) in entries_dict
        assert entries_dict[date(2024, 6, 5)]["has_content"] is True
        assert entries_dict[date(2024, 6, 5)]["word_count"] == 50
        assert entries_dict[date(2024, 6, 10)]["has_content"] is False
        assert entries_dict[date(2024, 6, 10)]["word_count"] == 100


class TestCalendarServiceIntegration:
    """Integration tests for CalendarService with real components."""
    
    @pytest_asyncio.fixture
    async def real_service(self):
        """Set up CalendarService with real FileDiscovery integration."""
        config = AppConfig()
        log_config = LogConfig(level=LogLevel.ERROR, console_output=False, file_output=False)
        logger = JournalSummarizerLogger(log_config)
        db_manager = DatabaseManager("tests/test_calendar_integration.db")
        await db_manager.initialize()
        
        service = CalendarService(config, logger, db_manager)
        
        yield service, db_manager
        
        # Cleanup
        try:
            Path("tests/test_calendar_integration.db").unlink(missing_ok=True)
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_file_discovery_integration(self, real_service):
        """Test integration with real FileDiscovery component."""
        service, db_manager = await real_service
        
        # Test that FileDiscovery is properly initialized
        assert service.file_discovery is not None
        assert hasattr(service.file_discovery, '_calculate_week_ending_for_date')
        
        # Test week ending calculation
        test_date = date(2024, 6, 15)
        week_ending = service.get_week_ending_date(test_date)
        assert isinstance(week_ending, date)
    
    @pytest.mark.asyncio
    async def test_calendar_configuration(self, real_service):
        """Test calendar configuration and setup."""
        service, db_manager = await real_service
        
        # Test calendar instance configuration
        assert service.first_day_of_week == 0  # Sunday
        assert service.calendar_instance is not None
        
        # Test calendar generation with real calendar instance
        calendar_month = await service.get_calendar_month(2024, 6)
        assert len(calendar_month.entries) == 30  # June 2024 has 30 days


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])