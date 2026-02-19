# ABOUTME: REST API endpoints for calendar navigation and date-range queries.
# ABOUTME: Provides month/week views of journal entries via CalendarService.
"""
Calendar API Endpoints for Work Journal Maker Web Interface

This module provides REST API endpoints for calendar functionality,
including calendar data, navigation, and date-based queries.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from datetime import date, datetime, timedelta
from typing import Optional, List
from config_manager import AppConfig
from logger import JournalSummarizerLogger, ErrorCategory
from web.services.calendar_service import CalendarService
from web.models.journal import CalendarMonth, CalendarEntry, TodayResponse

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


def get_calendar_service(request: Request) -> CalendarService:
    """Dependency to get CalendarService from app state."""
    return request.app.state.calendar_service


@router.get("/today", response_model=TodayResponse)
async def get_today_info(
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """Get information about today's date and entry status."""
    try:
        today_info = await calendar_service.get_today_info()
        
        return TodayResponse(
            today=today_info["today"],
            day_name=today_info["day_name"],
            formatted_date=today_info["formatted_date"],
            has_entry=today_info["has_entry"],
            entry_metadata=today_info["entry_metadata"],
            week_ending_date=today_info["week_ending_date"],
            current_month=today_info["current_month"],
            current_year=today_info["current_year"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail="Failed to retrieve today's information"
        )


# Move specific routes before general ones to avoid path conflicts

@router.get("/current")
async def get_current_month(
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """Get current month calendar data."""
    try:
        today = date.today()
        calendar_data = await calendar_service.get_calendar_month(today.year, today.month)
        return calendar_data
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve current month data"
        )


@router.get("/week/{entry_date}")
async def get_week_info(
    entry_date: date,
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """Get week information for a specific date."""
    try:
        week_ending = calendar_service.get_week_ending_date(entry_date)
        
        # Calculate week start (Monday)
        week_start = week_ending - timedelta(days=4)  # Friday - 4 = Monday
        
        # Get entries for the week
        week_entries = await calendar_service.get_entries_for_date_range(week_start, week_ending)
        
        return {
            "entry_date": entry_date,
            "week_start": week_start,
            "week_ending": week_ending,
            "entries": week_entries,
            "total_entries": len([e for e in week_entries if e.has_content])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve week information"
        )


@router.get("/stats")
async def get_calendar_stats(
    year: Optional[int] = Query(None, description="Year for stats (default: current year)"),
    month: Optional[int] = Query(None, description="Month for stats (default: all months)"),
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """Get calendar statistics for a specific year or month."""
    try:
        # Default to current year if not specified
        if year is None:
            year = date.today().year
        
        # Validate year
        if not (1900 <= year <= 3000):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid year: {year}. Must be between 1900 and 3000."
            )
        
        # Validate month if specified
        if month is not None and not (1 <= month <= 12):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid month: {month}. Must be between 1 and 12."
            )
        
        # Calculate date range
        if month is not None:
            # Single month stats
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
        else:
            # Full year stats
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
        
        # Get entries for the period
        entries = await calendar_service.get_entries_for_date_range(start_date, end_date)
        
        # Calculate statistics
        total_entries = len(entries)
        entries_with_content = len([e for e in entries if e.has_content])
        total_words = sum(e.word_count for e in entries if e.has_content)
        
        # Calculate completion rate
        total_days = (end_date - start_date).days + 1
        completion_rate = (entries_with_content / total_days) * 100 if total_days > 0 else 0
        
        return {
            "period": {
                "start_date": start_date,
                "end_date": end_date,
                "year": year,
                "month": month,
                "total_days": total_days
            },
            "entries": {
                "total_entries": total_entries,
                "entries_with_content": entries_with_content,
                "empty_entries": total_entries - entries_with_content,
                "completion_rate": round(completion_rate, 2)
            },
            "content": {
                "total_words": total_words,
                "average_words_per_entry": round(total_words / entries_with_content, 2) if entries_with_content > 0 else 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve calendar statistics"
        )


@router.get("/months/{year}")
async def get_year_overview(
    year: int,
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """Get overview of all months in a year with entry counts."""
    try:
        # Validate year
        if not (1900 <= year <= 3000):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid year: {year}. Must be between 1900 and 3000."
            )
        
        months_data = []
        
        for month in range(1, 13):
            # Get entries for the month
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
            
            entries = await calendar_service.get_entries_for_date_range(start_date, end_date)
            entries_with_content = len([e for e in entries if e.has_content])
            total_days = (end_date - start_date).days + 1
            
            months_data.append({
                "month": month,
                "month_name": start_date.strftime("%B"),
                "total_days": total_days,
                "entries_with_content": entries_with_content,
                "completion_rate": round((entries_with_content / total_days) * 100, 2) if total_days > 0 else 0
            })
        
        return {
            "year": year,
            "months": months_data,
            "total_entries": sum(m["entries_with_content"] for m in months_data),
            "average_completion_rate": round(sum(m["completion_rate"] for m in months_data) / 12, 2)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve year overview"
        )


@router.get("/date/{entry_date}/exists")
async def check_entry_exists(
    entry_date: date,
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """Check if an entry exists for a specific date."""
    try:
        has_entry = await calendar_service.has_entry_for_date(entry_date)
        
        return {
            "date": entry_date,
            "has_entry": has_entry,
            "formatted_date": entry_date.strftime("%B %d, %Y"),
            "day_name": entry_date.strftime("%A")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to check entry existence"
        )


@router.get("/range/{start_date}/{end_date}", response_model=List[CalendarEntry])
async def get_entries_in_range(
    start_date: date,
    end_date: date,
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """Get all entries within a date range."""
    try:
        # Validate date range
        if start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail="Start date must be before or equal to end date"
            )
        
        # Prevent overly large ranges
        if (end_date - start_date).days > 365:
            raise HTTPException(
                status_code=400,
                detail="Date range cannot exceed 365 days"
            )
        
        entries = await calendar_service.get_entries_for_date_range(start_date, end_date)
        return entries
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve entries in range"
        )


@router.get("/{year}/{month}", response_model=CalendarMonth)
async def get_calendar_month(
    year: int,
    month: int,
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """Get calendar data for a specific month and year."""
    try:
        # Validate year and month
        if not (1900 <= year <= 3000):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid year: {year}. Must be between 1900 and 3000."
            )
        if not (1 <= month <= 12):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid month: {month}. Must be between 1 and 12."
            )
        
        calendar_data = await calendar_service.get_calendar_month(year, month)
        return calendar_data
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve calendar data"
        )


@router.get("/{year}/{month}/navigation")
async def get_calendar_navigation(
    year: int,
    month: int,
    calendar_service: CalendarService = Depends(get_calendar_service)
):
    """Get navigation information for calendar month view."""
    try:
        # Validate year and month
        if not (1900 <= year <= 3000):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid year: {year}. Must be between 1900 and 3000."
            )
        if not (1 <= month <= 12):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid month: {month}. Must be between 1 and 12."
            )
        
        (prev_year, prev_month), (next_year, next_month) = await calendar_service.get_adjacent_months(year, month)
        
        return {
            "current": {"year": year, "month": month},
            "previous": {"year": prev_year, "month": prev_month},
            "next": {"year": next_year, "month": next_month},
            "today": {
                "year": date.today().year,
                "month": date.today().month,
                "day": date.today().day
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve navigation data"
        )