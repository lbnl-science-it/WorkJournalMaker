"""
Calendar Service for Work Journal Maker Web Interface

This module provides calendar navigation and date-based entry queries
using the existing FileDiscovery system while maintaining compatibility
with the existing file structure.
"""

import asyncio
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import calendar
import sys
from dataclasses import dataclass

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from file_discovery import FileDiscovery
from config_manager import AppConfig
from logger import JournalSummarizerLogger, ErrorCategory
from web.database import DatabaseManager, JournalEntryIndex
from web.models.journal import CalendarEntry, CalendarMonth, EntryStatus
from web.services.base_service import BaseService
from sqlalchemy import select, and_, extract


@dataclass
class CalendarDay:
    """Represents a single day in the calendar."""
    date: date
    day_number: int
    is_current_month: bool
    is_today: bool
    has_entry: bool
    entry_status: EntryStatus
    word_count: int = 0


class CalendarService(BaseService):
    """
    Manages calendar data and navigation for the web interface.
    
    Provides calendar grid generation, entry indicators, and navigation
    while integrating with existing FileDiscovery for date calculations.
    """
    
    def __init__(self, config: AppConfig, logger: JournalSummarizerLogger, 
                 db_manager: DatabaseManager):
        """Initialize CalendarService with core dependencies."""
        super().__init__(config, logger, db_manager)
        
        # Initialize FileDiscovery for date calculations
        self.file_discovery = FileDiscovery(config.processing.base_path)
        
        # Calendar configuration
        self.first_day_of_week = 0  # 0 = Sunday, 1 = Monday
        self.calendar_instance = calendar.Calendar(self.first_day_of_week)
    
    async def get_calendar_month(self, year: int, month: int) -> CalendarMonth:
        """Generate calendar data for a specific month."""
        try:
            self._log_operation_start("get_calendar_month", year=year, month=month)
            
            # Validate month/year
            if not (1 <= month <= 12):
                raise ValueError(f"Invalid month: {month}")
            if not (1900 <= year <= 3000):
                raise ValueError(f"Invalid year: {year}")
            
            # Get entries for the month from database
            entries_dict = await self._get_month_entries(year, month)
            
            # Generate calendar grid
            calendar_days = await self._generate_calendar_grid(year, month, entries_dict)
            
            # Create calendar entries list
            calendar_entries = []
            for day in calendar_days:
                if day.is_current_month:
                    calendar_entries.append(CalendarEntry(
                        date=day.date,
                        has_content=day.has_entry,
                        word_count=day.word_count,
                        status=day.entry_status
                    ))
            
            result = CalendarMonth(
                year=year,
                month=month,
                month_name=calendar.month_name[month],
                entries=calendar_entries,
                today=date.today()
            )
            
            self._log_operation_success("get_calendar_month", year=year, month=month, entries=len(calendar_entries))
            return result
            
        except Exception as e:
            self._log_operation_error("get_calendar_month", e, year=year, month=month)
            self.logger.log_error_with_category(
                ErrorCategory.PROCESSING_ERROR,
                f"Failed to generate calendar for {year}-{month}: {str(e)}"
            )
            raise
    
    async def get_adjacent_months(self, year: int, month: int) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """Get previous and next month for navigation."""
        # Calculate previous month
        if month == 1:
            prev_year, prev_month = year - 1, 12
        else:
            prev_year, prev_month = year, month - 1
        
        # Calculate next month
        if month == 12:
            next_year, next_month = year + 1, 1
        else:
            next_year, next_month = year, month + 1
        
        return (prev_year, prev_month), (next_year, next_month)
    
    async def has_entry_for_date(self, entry_date: date) -> bool:
        """Check if an entry exists for a specific date."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = select(JournalEntryIndex).where(JournalEntryIndex.date == entry_date)
                result = await session.execute(stmt)
                entry = result.scalar_one_or_none()
                
                return entry is not None and entry.has_content
                
        except Exception as e:
            self.logger.log_error_with_category(
                ErrorCategory.PROCESSING_ERROR,
                f"Failed to check entry existence for {entry_date}: {str(e)}"
            )
            return False
    
    async def get_entries_for_date_range(self, start_date: date, end_date: date) -> List[CalendarEntry]:
        """Get all entries within a date range."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = (
                    select(JournalEntryIndex)
                    .where(
                        and_(
                            JournalEntryIndex.date >= start_date,
                            JournalEntryIndex.date <= end_date
                        )
                    )
                    .order_by(JournalEntryIndex.date)
                )
                
                result = await session.execute(stmt)
                db_entries = result.scalars().all()
                
                entries = []
                for entry in db_entries:
                    entries.append(CalendarEntry(
                        date=entry.date,
                        has_content=entry.has_content,
                        word_count=entry.word_count,
                        status=EntryStatus.COMPLETE if entry.has_content else EntryStatus.EMPTY
                    ))
                
                return entries
                
        except Exception as e:
            self.logger.log_error_with_category(
                ErrorCategory.PROCESSING_ERROR,
                f"Failed to get entries for date range {start_date} to {end_date}: {str(e)}"
            )
            return []
    
    def get_week_ending_date(self, entry_date: date) -> date:
        """Get week ending date using existing FileDiscovery logic."""
        return self.file_discovery._find_week_ending_for_date(entry_date)
    
    async def get_today_info(self) -> Dict[str, Any]:
        """Get information about today's date and entry status."""
        today = date.today()
        
        try:
            # Check if today has an entry
            has_entry = await self.has_entry_for_date(today)
            
            # Get entry metadata if it exists
            entry_metadata = None
            if has_entry:
                async with self.db_manager.get_session() as session:
                    stmt = select(JournalEntryIndex).where(JournalEntryIndex.date == today)
                    result = await session.execute(stmt)
                    entry = result.scalar_one_or_none()
                    
                    if entry:
                        entry_metadata = {
                            "word_count": entry.word_count,
                            "has_content": entry.has_content,
                            "file_path": entry.file_path,
                            "modified_at": entry.modified_at
                        }
            
            # Calculate week ending date using existing logic
            week_ending = self.file_discovery._find_week_ending_for_date(today)
            
            return {
                "today": today,
                "day_name": today.strftime("%A"),
                "formatted_date": today.strftime("%B %d, %Y"),
                "has_entry": has_entry,
                "entry_metadata": entry_metadata,
                "week_ending_date": week_ending,
                "current_month": today.month,
                "current_year": today.year
            }
            
        except Exception as e:
            self.logger.log_error_with_category(
                ErrorCategory.PROCESSING_ERROR,
                f"Failed to get today info: {str(e)}"
            )
            return {
                "today": today,
                "day_name": today.strftime("%A"),
                "formatted_date": today.strftime("%B %d, %Y"),
                "has_entry": False,
                "entry_metadata": None,
                "week_ending_date": today,
                "current_month": today.month,
                "current_year": today.year
            }
    
    async def _get_month_entries(self, year: int, month: int) -> Dict[date, Dict[str, Any]]:
        """Get all entries for a specific month from database."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = (
                    select(JournalEntryIndex)
                    .where(
                        and_(
                            extract('year', JournalEntryIndex.date) == year,
                            extract('month', JournalEntryIndex.date) == month
                        )
                    )
                )
                
                result = await session.execute(stmt)
                db_entries = result.scalars().all()
                
                entries_dict = {}
                for entry in db_entries:
                    entries_dict[entry.date] = {
                        "has_content": entry.has_content,
                        "word_count": entry.word_count,
                        "status": EntryStatus.COMPLETE if entry.has_content else EntryStatus.EMPTY
                    }
                
                return entries_dict
                
        except Exception as e:
            self.logger.log_error_with_category(
                ErrorCategory.PROCESSING_ERROR,
                f"Failed to get month entries for {year}-{month}: {str(e)}"
            )
            return {}
    
    async def _generate_calendar_grid(self, year: int, month: int, 
                                    entries_dict: Dict[date, Dict[str, Any]]) -> List[CalendarDay]:
        """Generate calendar grid with entry indicators."""
        calendar_days = []
        today = date.today()
        
        # Get calendar days for the month
        month_calendar = self.calendar_instance.monthdayscalendar(year, month)
        
        for week in month_calendar:
            for day in week:
                if day == 0:
                    continue
                
                day_date = date(year, month, day)
                is_current_month = day_date.month == month
                is_today = day_date == today
                
                # Get entry information
                entry_info = entries_dict.get(day_date, {})
                has_entry = entry_info.get("has_content", False)
                word_count = entry_info.get("word_count", 0)
                entry_status = entry_info.get("status", EntryStatus.EMPTY)
                
                calendar_days.append(CalendarDay(
                    date=day_date,
                    day_number=day,
                    is_current_month=is_current_month,
                    is_today=is_today,
                    has_entry=has_entry,
                    entry_status=entry_status,
                    word_count=word_count
                ))
        
        return calendar_days