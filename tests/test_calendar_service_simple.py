"""
Simple tests for CalendarService implementation
"""

import pytest
import asyncio
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent))

from config_manager import AppConfig
from logger import JournalSummarizerLogger, LogConfig, LogLevel
from web.database import DatabaseManager, JournalEntryIndex
from web.services.calendar_service import CalendarService
from web.models.journal import CalendarEntry, CalendarMonth, EntryStatus


@pytest.mark.asyncio
async def test_calendar_service_basic_functionality():
    """Test basic CalendarService functionality."""
    # Setup
    config = AppConfig()
    log_config = LogConfig(level=LogLevel.ERROR, console_output=False, file_output=False)
    logger = JournalSummarizerLogger(log_config)
    db_manager = DatabaseManager("tests/test_calendar_simple.db")
    await db_manager.initialize()
    
    service = CalendarService(config, logger, db_manager)
    
    try:
        # Test 1: Get current month calendar
        today = date.today()
        calendar_month = await service.get_calendar_month(today.year, today.month)
        
        assert isinstance(calendar_month, CalendarMonth)
        assert calendar_month.year == today.year
        assert calendar_month.month == today.month
        assert calendar_month.today == today
        assert len(calendar_month.entries) > 0
        
        # Test 2: Get adjacent months
        (prev_year, prev_month), (next_year, next_month) = await service.get_adjacent_months(today.year, today.month)
        
        if today.month == 1:
            assert (prev_year, prev_month) == (today.year - 1, 12)
            assert (next_year, next_month) == (today.year, 2)
        elif today.month == 12:
            assert (prev_year, prev_month) == (today.year, 11)
            assert (next_year, next_month) == (today.year + 1, 1)
        else:
            assert (prev_year, prev_month) == (today.year, today.month - 1)
            assert (next_year, next_month) == (today.year, today.month + 1)
        
        # Test 3: Check entry existence (should be False for new database)
        has_entry = await service.has_entry_for_date(today)
        assert has_entry is False
        
        # Test 4: Get today's info
        today_info = await service.get_today_info()
        assert today_info["today"] == today
        assert isinstance(today_info["day_name"], str)
        assert isinstance(today_info["formatted_date"], str)
        assert today_info["has_entry"] is False
        
        # Test 5: Week ending calculation
        week_ending = service.get_week_ending_date(today)
        assert isinstance(week_ending, date)
        
        print("✅ All basic CalendarService tests passed!")
        
    finally:
        # Cleanup
        try:
            Path("tests/test_calendar_simple.db").unlink(missing_ok=True)
        except:
            pass


@pytest.mark.asyncio
async def test_calendar_service_with_entries():
    """Test CalendarService with actual database entries."""
    # Setup
    config = AppConfig()
    log_config = LogConfig(level=LogLevel.ERROR, console_output=False, file_output=False)
    logger = JournalSummarizerLogger(log_config)
    db_manager = DatabaseManager("tests/test_calendar_entries.db")
    await db_manager.initialize()
    
    service = CalendarService(config, logger, db_manager)
    
    try:
        # Add test entries
        test_dates = [
            date(2024, 6, 10),
            date(2024, 6, 15),
            date(2024, 6, 20)
        ]
        
        async with db_manager.get_session() as session:
            for i, test_date in enumerate(test_dates):
                test_entry = JournalEntryIndex(
                    date=test_date,
                    file_path=f"/test/path_{i}.txt",
                    week_ending_date=test_date,
                    has_content=True,
                    word_count=(i + 1) * 100
                )
                session.add(test_entry)
            await session.commit()
        
        # Test calendar generation with entries
        calendar_month = await service.get_calendar_month(2024, 6)
        assert calendar_month.year == 2024
        assert calendar_month.month == 6
        assert len(calendar_month.entries) == 30  # June has 30 days
        
        # Check specific entries
        entry_10 = next((e for e in calendar_month.entries if e.date == date(2024, 6, 10)), None)
        assert entry_10 is not None
        assert entry_10.has_content is True
        assert entry_10.word_count == 100
        
        # Test date range queries
        entries = await service.get_entries_for_date_range(date(2024, 6, 12), date(2024, 6, 18))
        assert len(entries) == 1  # Should find entry for 6/15
        assert entries[0].date == date(2024, 6, 15)
        assert entries[0].word_count == 200
        
        # Test entry existence
        has_entry = await service.has_entry_for_date(date(2024, 6, 15))
        assert has_entry is True
        
        has_no_entry = await service.has_entry_for_date(date(2024, 6, 25))
        assert has_no_entry is False
        
        print("✅ All CalendarService entry tests passed!")
        
    finally:
        # Cleanup
        try:
            Path("tests/test_calendar_entries.db").unlink(missing_ok=True)
        except:
            pass


@pytest.mark.asyncio
async def test_calendar_service_validation():
    """Test CalendarService input validation."""
    # Setup
    config = AppConfig()
    log_config = LogConfig(level=LogLevel.ERROR, console_output=False, file_output=False)
    logger = JournalSummarizerLogger(log_config)
    db_manager = DatabaseManager("tests/test_calendar_validation.db")
    await db_manager.initialize()
    
    service = CalendarService(config, logger, db_manager)
    
    try:
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
        
        print("✅ All CalendarService validation tests passed!")
        
    finally:
        # Cleanup
        try:
            Path("tests/test_calendar_validation.db").unlink(missing_ok=True)
        except:
            pass


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(test_calendar_service_basic_functionality())
    asyncio.run(test_calendar_service_with_entries())
    asyncio.run(test_calendar_service_validation())
    print("🎉 All CalendarService tests completed successfully!")