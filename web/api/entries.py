"""
Entry API Endpoints for Work Journal Maker Web Interface

This module provides REST API endpoints for journal entry operations,
including CRUD functionality, listing, and metadata operations.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from datetime import date, datetime
from typing import Optional, List
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from config_manager import AppConfig
from logger import JournalSummarizerLogger, ErrorCategory
from web.services.entry_manager import EntryManager
from web.models.journal import (
    JournalEntryCreate, JournalEntryUpDate, JournalEntryResponse,
    RecentEntriesResponse, EntryListRequest, DatabaseStats
)

router = APIRouter(prefix="/api/entries", tags=["entries"])


def get_entry_manager(request: Request) -> EntryManager:
    """Dependency to get EntryManager from app state."""
    return request.app.state.entry_manager


@router.get("/", response_model=RecentEntriesResponse)
async def list_entries(
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    has_content: Optional[bool] = Query(None, description="Filter by content presence"),
    limit: int = Query(10, ge=1, le=100, description="Number of entries to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    sort_by: str = Query("date", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    entry_manager: EntryManager = Depends(get_entry_manager)
):
    """
    List journal entries with filtering and pagination.
    
    Returns a paginated list of journal entries with metadata.
    Supports filtering by date range and content presence.
    """
    try:
        # Create request model
        request_model = EntryListRequest(
            start_date=start_date,
            end_date=end_date,
            has_content=has_content,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Get entries from EntryManager
        result = await entry_manager.list_entries(request_model)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve entries")


@router.get("/recent", response_model=RecentEntriesResponse)
async def get_recent_entries(
    limit: int = Query(10, ge=1, le=50, description="Number of recent entries to return"),
    entry_manager: EntryManager = Depends(get_entry_manager)
):
    """
    Get recent journal entries.
    
    Returns the most recent journal entries ordered by date.
    """
    try:
        result = await entry_manager.get_recent_entries(limit=limit)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve recent entries")


@router.get("/{entry_date}", response_model=JournalEntryResponse)
async def get_entry(
    entry_date: date,
    include_content: bool = Query(False, description="Include entry content"),
    entry_manager: EntryManager = Depends(get_entry_manager)
):
    """
    Get a specific journal entry by date.
    
    Returns the journal entry for the specified date with optional content.
    """
    try:
        entry = await entry_manager.get_entry_by_date(entry_date, include_content=include_content)
        
        if not entry:
            raise HTTPException(status_code=404, detail=f"Entry not found for date {entry_date}")
        
        return entry
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve entry")


@router.post("/{entry_date}", response_model=JournalEntryResponse)
async def create_or_update_entry(
    entry_date: date,
    entry_data: JournalEntryCreate,
    entry_manager: EntryManager = Depends(get_entry_manager)
):
    """
    Create or update a journal entry.
    
    Creates a new entry or updates an existing entry for the specified date.
    """
    try:
        # Validate that the date matches
        if entry_data.date != entry_date:
            raise HTTPException(
                status_code=400, 
                detail="Entry date in URL must match date in request body"
            )
        
        # Save the entry content
        success = await entry_manager.save_entry_content(entry_date, entry_data.content)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save entry")
        
        # Return the updated entry
        entry = await entry_manager.get_entry_by_date(entry_date, include_content=True)
        
        if not entry:
            raise HTTPException(status_code=500, detail="Failed to retrieve saved entry")
        
        return entry
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create or update entry")


@router.put("/{entry_date}", response_model=JournalEntryResponse)
async def update_entry(
    entry_date: date,
    entry_data: JournalEntryUpDate,
    entry_manager: EntryManager = Depends(get_entry_manager)
):
    """
    Update an existing journal entry.
    
    Updates the content of an existing journal entry.
    """
    try:
        # Check if entry exists
        existing_entry = await entry_manager.get_entry_by_date(entry_date)
        if not existing_entry:
            raise HTTPException(status_code=404, detail=f"Entry not found for date {entry_date}")
        
        # Save the updated content
        success = await entry_manager.save_entry_content(entry_date, entry_data.content)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update entry")
        
        # Return the updated entry
        entry = await entry_manager.get_entry_by_date(entry_date, include_content=True)
        
        if not entry:
            raise HTTPException(status_code=500, detail="Failed to retrieve updated entry")
        
        return entry
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update entry")


@router.delete("/{entry_date}")
async def delete_entry(
    entry_date: date,
    entry_manager: EntryManager = Depends(get_entry_manager)
):
    """
    Delete a journal entry.
    
    Removes the journal entry for the specified date from both
    the file system and database index.
    """
    try:
        # Check if entry exists
        existing_entry = await entry_manager.get_entry_by_date(entry_date)
        if not existing_entry:
            raise HTTPException(status_code=404, detail=f"Entry not found for date {entry_date}")
        
        # Delete the entry
        success = await entry_manager.delete_entry(entry_date)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete entry")
        
        return {"message": f"Entry for {entry_date} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete entry")


@router.get("/{entry_date}/content")
async def get_entry_content(
    entry_date: date,
    entry_manager: EntryManager = Depends(get_entry_manager)
):
    """
    Get the raw content of a journal entry.
    
    Returns just the text content of the entry without metadata.
    """
    try:
        content = await entry_manager.get_entry_content(entry_date)
        
        if content is None:
            raise HTTPException(status_code=404, detail=f"Entry not found for date {entry_date}")
        
        return {"date": entry_date, "content": content}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve entry content")


@router.post("/{entry_date}/content")
async def update_entry_content(
    entry_date: date,
    content: str,
    entry_manager: EntryManager = Depends(get_entry_manager)
):
    """
    Update just the content of a journal entry.
    
    Updates only the text content without requiring full entry model.
    """
    try:
        success = await entry_manager.save_entry_content(entry_date, content)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save entry content")
        
        return {"message": f"Content for {entry_date} updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update entry content")


@router.get("/stats/database", response_model=DatabaseStats)
async def get_database_stats(
    request: Request,
    entry_manager: EntryManager = Depends(get_entry_manager)
):
    """
    Get database statistics.
    
    Returns statistics about the journal entry database index.
    """
    try:
        db_manager = request.app.state.db_manager
        
        async with db_manager.get_session() as session:
            # Get total entry count
            from sqlalchemy import select, func
            from web.database import JournalEntryIndex
            
            total_count_result = await session.execute(
                select(func.count(JournalEntryIndex.id))
            )
            total_count = total_count_result.scalar()
            
            # Get entries with content count
            content_count_result = await session.execute(
                select(func.count(JournalEntryIndex.id))
                .where(JournalEntryIndex.has_content == True)
            )
            content_count = content_count_result.scalar()
            
            # Get date range
            date_range_result = await session.execute(
                select(
                    func.min(JournalEntryIndex.date),
                    func.max(JournalEntryIndex.date)
                )
            )
            min_date, max_date = date_range_result.first()
            
            # Get database file size
            db_path = Path(db_manager.database_path)
            db_size_mb = 0.0
            if db_path.exists():
                db_size_mb = db_path.stat().st_size / (1024 * 1024)
            
            return DatabaseStats(
                total_entries=total_count or 0,
                entries_with_content=content_count or 0,
                date_range={"start": min_date, "end": max_date} if min_date and max_date else None,
                last_sync=None,  # Will be implemented in sync service
                database_size_mb=round(db_size_mb, 2)
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve database statistics")