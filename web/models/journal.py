"""
Journal Entry Pydantic Models

This module contains Pydantic models for journal entry operations,
validation, and API responses.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import date as Date, datetime as DateTime, timedelta
from typing import Optional, List, Dict, Any, Union
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
    date: Date = Field(..., description="Entry date")
    
    @field_validator('date')
    def validate_Date(cls, v):
        if v > Date.today():
            raise ValueError('Entry date cannot be in the future')
        return v


class JournalEntryCreate(JournalEntryBase):
    """Model for creating journal entries."""
    content: str = Field("", description="Entry content")


class JournalEntryUpDate(BaseModel):
    """Model for updating journal entries."""
    content: str = Field(..., description="Updated entry content")


class JournalEntryResponse(JournalEntryBase):
    """Model for journal entry API responses."""
    content: Optional[str] = Field(None, description="Entry content")
    file_path: str = Field(..., description="File system path")
    week_ending_date: Date = Field(..., description="Week ending date")
    metadata: JournalEntryMetadata = Field(..., description="Entry metadata")
    
    # Timestamps
    created_at: Optional[DateTime] = None
    modified_at: Optional[DateTime] = None
    last_accessed_at: Optional[DateTime] = None
    file_modified_at: Optional[DateTime] = None
    
    class Config:
        from_attributes = True


class EntryListRequest(BaseModel):
    """Request model for entry listing."""
    start_date: Optional[Date] = Field(None, description="Start date filter")
    end_date: Optional[Date] = Field(None, description="End date filter")
    has_content: Optional[bool] = Field(None, description="Filter by content presence")
    limit: int = Field(10, ge=1, le=100, description="Number of entries to return")
    offset: int = Field(0, ge=0, description="Offset for pagination")
    sort_by: str = Field("date", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$", description="Sort order")
    
    @model_validator(mode='after')
    def validate_date_range(self):
        """Validate date range consistency."""
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError('start_date must be before or equal to end_date')
            
            # Prevent overly large date ranges
            if (self.end_date - self.start_date).days > 365 * 2:  # 2 years max
                raise ValueError('Date range cannot exceed 2 years')
        
        return self
    
    @field_validator('sort_by')
    def validate_sort_field(cls, v):
        """Validate sort field."""
        allowed_fields = ['date', 'word_count', 'created_at', 'modified_at']
        if v not in allowed_fields:
            raise ValueError(f'sort_by must be one of: {", ".join(allowed_fields)}')
        return v


class RecentEntriesResponse(BaseModel):
    """Response model for recent entries list."""
    entries: List[JournalEntryResponse]
    total_count: int = Field(..., ge=0, description="Total number of entries")
    has_more: bool = Field(..., description="Whether more entries are available")
    pagination: Dict[str, Any] = Field(..., description="Pagination metadata")


class CalendarEntry(BaseModel):
    """Model for calendar entry indicators."""
    date: Date = Field(..., description="Entry date")
    has_content: bool = Field(False, description="Whether entry has content")
    word_count: int = Field(0, ge=0, description="Word count")
    status: EntryStatus = Field(EntryStatus.EMPTY, description="Entry status")


class CalendarMonth(BaseModel):
    """Model for calendar month data."""
    year: int = Field(..., ge=1900, le=3000, description="Year")
    month: int = Field(..., ge=1, le=12, description="Month")
    month_name: str = Field(..., description="Month name")
    entries: List[CalendarEntry] = Field(..., description="Entries in month")
    today: Date = Field(..., description="Today's date")


class DatabaseStats(BaseModel):
    """Database statistics model."""
    total_entries: int = Field(0, ge=0, description="Total entries in database")
    entries_with_content: int = Field(0, ge=0, description="Entries with content")
    date_range: Optional[Dict[str, Date]] = Field(None, description="Date range of entries")
    last_sync: Optional[DateTime] = Field(None, description="Last sync timestamp")
    database_size_mb: float = Field(0.0, ge=0.0, description="Database size in MB")


class EntrySearchRequest(BaseModel):
    """Request model for entry search."""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    search_content: bool = Field(True, description="Search in entry content")
    search_dates: bool = Field(False, description="Search in dates")
    start_date: Optional[Date] = Field(None, description="Start date filter")
    end_date: Optional[Date] = Field(None, description="End date filter")
    limit: int = Field(20, ge=1, le=100, description="Number of results to return")
    offset: int = Field(0, ge=0, description="Offset for pagination")
    
    @field_validator('query')
    def validate_query(cls, v):
        """Validate search query."""
        # Remove excessive whitespace
        v = ' '.join(v.split())
        if len(v.strip()) == 0:
            raise ValueError('Search query cannot be empty')
        return v


class EntrySearchResult(BaseModel):
    """Search result for a single entry."""
    entry: JournalEntryResponse = Field(..., description="Entry data")
    relevance_score: float = Field(0.0, ge=0.0, le=1.0, description="Search relevance score")
    matched_snippets: List[str] = Field(default_factory=list, description="Matched text snippets")


class EntrySearchResponse(BaseModel):
    """Response model for entry search."""
    results: List[EntrySearchResult] = Field(..., description="Search results")
    total_count: int = Field(..., ge=0, description="Total number of matching entries")
    query: str = Field(..., description="Original search query")
    search_time_ms: int = Field(..., ge=0, description="Search execution time in milliseconds")
    pagination: Dict[str, Any] = Field(..., description="Pagination metadata")


class EntryBulkOperation(BaseModel):
    """Model for bulk entry operations."""
    entry_dates: List[Date] = Field(..., min_items=1, max_items=100, description="List of entry dates")
    operation: str = Field(..., pattern="^(delete|export|backup)$", description="Operation type")
    options: Dict[str, Any] = Field(default_factory=dict, description="Operation-specific options")


class EntryExportRequest(BaseModel):
    """Request model for entry export."""
    start_date: Optional[Date] = Field(None, description="Start date for export")
    end_date: Optional[Date] = Field(None, description="End date for export")
    format: str = Field("json", pattern="^(json|csv|txt|markdown)$", description="Export format")
    include_metadata: bool = Field(True, description="Include entry metadata")
    include_empty_entries: bool = Field(False, description="Include entries without content")
    
    @model_validator(mode='after')
    def validate_export_range(cls, values):
        """Validate export date range."""
        start_date = values.get('start_date')
        end_date = values.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise ValueError('start_date must be before or equal to end_date')
        
        return values


class EntryValidationResult(BaseModel):
    """Result of entry validation."""
    valid: bool = Field(..., description="Whether entry is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    entry_date: Optional[Date] = Field(None, description="Entry date if valid")


class TodayResponse(BaseModel):
    """Response model for today's information."""
    today: Date = Field(..., description="Today's date")
    day_name: str = Field(..., description="Day name")
    formatted_date: str = Field(..., description="Formatted date string")
    has_entry: bool = Field(False, description="Whether today has an entry")
    entry_metadata: Optional[Dict[str, Any]] = Field(None, description="Entry metadata")
    week_ending_date: Date = Field(..., description="Week ending date")
    current_month: int = Field(..., description="Current month number")
    current_year: int = Field(..., description="Current year")