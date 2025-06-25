"""
Journal Entry Pydantic Models

This module contains Pydantic models for journal entry operations,
validation, and API responses.
"""

from pydantic import BaseModel, Field, validator
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class EntryStatus(str, Enum):
    """Entry status enumeration."""
    EMPTY = "empty"
    DRAFT = "draft"
    COMPLETE = "complete"


class JournalEntryMetadata(BaseModel):
    """Metadata for journal entries."""
    word_count: int = Field(0, ge=0, description="Word count")
    character_count: int = Field(0, ge=0, description="Character count")
    line_count: int = Field(0, ge=0, description="Line count")
    file_size_bytes: int = Field(0, ge=0, description="File size in bytes")
    has_content: bool = Field(False, description="Whether entry has content")
    status: EntryStatus = Field(EntryStatus.EMPTY, description="Entry status")


class JournalEntryBase(BaseModel):
    """Base model for journal entries."""
    date: date = Field(..., description="Entry date")
    
    @validator('date')
    def validate_date(cls, v):
        if v > date.today():
            raise ValueError('Entry date cannot be in the future')
        return v


class JournalEntryCreate(JournalEntryBase):
    """Model for creating journal entries."""
    content: str = Field("", description="Entry content")


class JournalEntryUpdate(BaseModel):
    """Model for updating journal entries."""
    content: str = Field(..., description="Updated entry content")


class JournalEntryResponse(JournalEntryBase):
    """Model for journal entry API responses."""
    content: Optional[str] = Field(None, description="Entry content")
    file_path: str = Field(..., description="File system path")
    week_ending_date: date = Field(..., description="Week ending date")
    metadata: JournalEntryMetadata = Field(..., description="Entry metadata")
    
    # Timestamps
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    last_accessed_at: Optional[datetime] = None
    file_modified_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class EntryListRequest(BaseModel):
    """Request model for entry listing."""
    start_date: Optional[date] = Field(None, description="Start date filter")
    end_date: Optional[date] = Field(None, description="End date filter")
    has_content: Optional[bool] = Field(None, description="Filter by content presence")
    limit: int = Field(10, ge=1, le=100, description="Number of entries to return")
    offset: int = Field(0, ge=0, description="Offset for pagination")
    sort_by: str = Field("date", description="Sort field")
    sort_order: str = Field("desc", regex="^(asc|desc)$", description="Sort order")


class RecentEntriesResponse(BaseModel):
    """Response model for recent entries list."""
    entries: List[JournalEntryResponse]
    total_count: int = Field(..., ge=0, description="Total number of entries")
    has_more: bool = Field(..., description="Whether more entries are available")
    pagination: Dict[str, Any] = Field(..., description="Pagination metadata")


class CalendarEntry(BaseModel):
    """Model for calendar entry indicators."""
    date: date = Field(..., description="Entry date")
    has_content: bool = Field(False, description="Whether entry has content")
    word_count: int = Field(0, ge=0, description="Word count")
    status: EntryStatus = Field(EntryStatus.EMPTY, description="Entry status")


class CalendarMonth(BaseModel):
    """Model for calendar month data."""
    year: int = Field(..., ge=1900, le=3000, description="Year")
    month: int = Field(..., ge=1, le=12, description="Month")
    month_name: str = Field(..., description="Month name")
    entries: List[CalendarEntry] = Field(..., description="Entries in month")
    today: date = Field(..., description="Today's date")


class DatabaseStats(BaseModel):
    """Database statistics model."""
    total_entries: int = Field(0, ge=0, description="Total entries in database")
    entries_with_content: int = Field(0, ge=0, description="Entries with content")
    date_range: Optional[Dict[str, date]] = Field(None, description="Date range of entries")
    last_sync: Optional[datetime] = Field(None, description="Last sync timestamp")
    database_size_mb: float = Field(0.0, ge=0.0, description="Database size in MB")