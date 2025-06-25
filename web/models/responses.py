"""
API Response Models

This module contains Pydantic models for standardized API responses,
error handling, and status reporting.
"""

from pydantic import BaseModel, Field
from datetime import datetime as DateTime
from typing import Optional, Dict, Any, List, Union
from enum import Enum


class ResponseStatus(str, Enum):
    """Standard response status values."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class APIResponse(BaseModel):
    """Base API response model."""
    status: ResponseStatus = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    timestamp: DateTime = Field(default_factory=DateTime.utcnow, description="Response timestamp")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request identifier")
    timestamp: DateTime = Field(default_factory=DateTime.utcnow, description="Error timestamp")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Overall health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: DateTime = Field(..., description="Health check timestamp")
    components: Dict[str, Dict[str, Any]] = Field(..., description="Component health status")


class ValidationErrorResponse(BaseModel):
    """Validation error response model."""
    error: str = Field("validation_error", description="Error type")
    message: str = Field(..., description="Validation error message")
    field_errors: List[Dict[str, Union[str, List[str]]]] = Field(..., description="Field-specific errors")
    timestamp: DateTime = Field(default_factory=DateTime.utcnow, description="Error timestamp")


class PaginationResponse(BaseModel):
    """Pagination metadata response."""
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, description="Items per page")
    total: int = Field(..., ge=0, description="Total number of items")
    pages: int = Field(..., ge=0, description="Total number of pages")
    has_prev: bool = Field(..., description="Whether there is a previous page")
    has_next: bool = Field(..., description="Whether there is a next page")
    prev_page: Optional[int] = Field(None, description="Previous page number")
    next_page: Optional[int] = Field(None, description="Next page number")


class OperationResponse(BaseModel):
    """Response model for operations."""
    success: bool = Field(..., description="Whether operation was successful")
    message: str = Field(..., description="Operation message")
    operation_id: Optional[str] = Field(None, description="Operation identifier")
    timestamp: DateTime = Field(default_factory=DateTime.utcnow, description="Operation timestamp")
    data: Optional[Dict[str, Any]] = Field(None, description="Operation result data")
    warnings: List[str] = Field(default_factory=list, description="Operation warnings")


class BulkOperationResponse(BaseModel):
    """Response model for bulk operations."""
    total_items: int = Field(..., ge=0, description="Total items processed")
    successful_items: int = Field(..., ge=0, description="Successfully processed items")
    failed_items: int = Field(..., ge=0, description="Failed items")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Item-specific errors")
    warnings: List[str] = Field(default_factory=list, description="Operation warnings")
    operation_id: str = Field(..., description="Bulk operation identifier")
    started_at: DateTime = Field(..., description="Operation start time")
    completed_at: Optional[DateTime] = Field(None, description="Operation completion time")
    status: str = Field(..., pattern="^(running|completed|failed|cancelled)$", description="Operation status")


class SyncStatusResponse(BaseModel):
    """Response model for synchronization status."""
    sync_in_progress: bool = Field(..., description="Whether sync is currently running")
    last_full_sync: Optional[DateTime] = Field(None, description="Last full sync timestamp")
    last_incremental_sync: Optional[DateTime] = Field(None, description="Last incremental sync timestamp")
    sync_health: str = Field(..., pattern="^(healthy|degraded|unhealthy)$", description="Sync health status")
    pending_changes: int = Field(0, ge=0, description="Number of pending changes")
    recent_syncs: List[Dict[str, Any]] = Field(default_factory=list, description="Recent sync operations")


class SystemStatusResponse(BaseModel):
    """Response model for system status."""
    overall_status: str = Field(..., pattern="^(healthy|degraded|unhealthy)$", description="Overall system status")
    components: Dict[str, Dict[str, Any]] = Field(..., description="Component status details")
    uptime_seconds: int = Field(..., ge=0, description="System uptime in seconds")
    version: str = Field(..., description="System version")
    timestamp: DateTime = Field(default_factory=DateTime.utcnow, description="Status check timestamp")
    performance_metrics: Dict[str, Union[int, float]] = Field(default_factory=dict, description="Performance metrics")


class ExportResponse(BaseModel):
    """Response model for data export operations."""
    export_id: str = Field(..., description="Export operation identifier")
    format: str = Field(..., description="Export format")
    file_size_bytes: int = Field(..., ge=0, description="Export file size in bytes")
    entry_count: int = Field(..., ge=0, description="Number of entries exported")
    created_at: DateTime = Field(..., description="Export creation timestamp")
    expires_at: Optional[DateTime] = Field(None, description="Export expiration timestamp")
    download_url: Optional[str] = Field(None, description="Download URL")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Export metadata")


class ImportResponse(BaseModel):
    """Response model for data import operations."""
    import_id: str = Field(..., description="Import operation identifier")
    status: str = Field(..., pattern="^(processing|completed|failed)$", description="Import status")
    total_entries: int = Field(..., ge=0, description="Total entries to import")
    processed_entries: int = Field(..., ge=0, description="Entries processed so far")
    successful_entries: int = Field(..., ge=0, description="Successfully imported entries")
    failed_entries: int = Field(..., ge=0, description="Failed entry imports")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Import errors")
    warnings: List[str] = Field(default_factory=list, description="Import warnings")
    started_at: DateTime = Field(..., description="Import start timestamp")
    completed_at: Optional[DateTime] = Field(None, description="Import completion timestamp")


class MetricsResponse(BaseModel):
    """Response model for system metrics."""
    database_metrics: Dict[str, Union[int, float]] = Field(..., description="Database performance metrics")
    file_system_metrics: Dict[str, Union[int, float]] = Field(..., description="File system metrics")
    api_metrics: Dict[str, Union[int, float]] = Field(..., description="API performance metrics")
    memory_usage_mb: float = Field(..., ge=0.0, description="Memory usage in MB")
    cpu_usage_percent: float = Field(..., ge=0.0, le=100.0, description="CPU usage percentage")
    disk_usage_mb: float = Field(..., ge=0.0, description="Disk usage in MB")
    timestamp: DateTime = Field(default_factory=DateTime.utcnow, description="Metrics timestamp")