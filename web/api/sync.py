"""
Sync API Endpoints for Work Journal Maker Web Interface

This module provides REST API endpoints for managing and monitoring
database synchronization operations.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from config_manager import AppConfig
from logger import JournalSummarizerLogger
from web.database import DatabaseManager
from web.services.sync_service import DatabaseSyncService, SyncType
from web.services.scheduler import SyncScheduler

router = APIRouter(prefix="/api/sync", tags=["synchronization"])


def get_sync_service(request: Request) -> DatabaseSyncService:
    """Dependency to get sync service from app state."""
    return request.app.state.sync_service


def get_scheduler(request: Request) -> SyncScheduler:
    """Dependency to get scheduler from app state."""
    return getattr(request.app.state, 'scheduler', None)


@router.get("/status")
async def get_sync_status(sync_service: DatabaseSyncService = Depends(get_sync_service)):
    """
    Get current synchronization status and recent sync history.
    
    Returns:
        Dict containing sync status, recent operations, and statistics
    """
    try:
        status = await sync_service.get_sync_status()
        db_stats = await sync_service.db_manager.get_database_stats()
        
        return {
            "sync_status": status,
            "database_stats": db_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sync status: {str(e)}")


@router.get("/scheduler/status")
async def get_scheduler_status(scheduler: SyncScheduler = Depends(get_scheduler)):
    """
    Get scheduler status and configuration.
    
    Returns:
        Dict containing scheduler status and statistics
    """
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available")
    
    try:
        return scheduler.get_scheduler_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}")


@router.post("/full")
async def trigger_full_sync(
    background_tasks: BackgroundTasks,
    date_range_days: Optional[int] = None,
    sync_service: DatabaseSyncService = Depends(get_sync_service)
):
    """
    Trigger a full synchronization between file system and database.
    
    Args:
        date_range_days: Number of days to scan (default: 730)
        
    Returns:
        Dict with sync operation details
    """
    try:
        # Check if sync is already in progress
        status = await sync_service.get_sync_status()
        if status["sync_in_progress"]:
            raise HTTPException(status_code=409, detail="Sync already in progress")
        
        # Start sync in background
        background_tasks.add_task(_run_full_sync, sync_service, date_range_days)
        
        return {
            "message": "Full sync started",
            "sync_type": "full",
            "date_range_days": date_range_days or 730,
            "started_at": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start full sync: {str(e)}")


@router.post("/incremental")
async def trigger_incremental_sync(
    request: Request,
    background_tasks: BackgroundTasks,
    sync_service: DatabaseSyncService = Depends(get_sync_service)
):
    """
    Trigger an incremental synchronization for recent changes.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dict with sync operation details
    """
    try:
        # Parse request body
        body = await request.json() if request.headers.get("content-type") == "application/json" else {}
        since_days = body.get("since_days", 7)
        
        # Log for debugging
        sync_service.logger.logger.info(f"API triggered incremental sync with since_days: {since_days}")
        
        since_date = date.today() - timedelta(days=since_days)
        
        # Start sync in background
        background_tasks.add_task(_run_incremental_sync, sync_service, since_date)
        
        return {
            "message": "Incremental sync started",
            "sync_type": "incremental",
            "since_days": since_days,
            "since_date": since_date.isoformat(),
            "started_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start incremental sync: {str(e)}")


@router.post("/entry/{entry_date}")
async def sync_single_entry(
    entry_date: date,
    background_tasks: BackgroundTasks,
    sync_service: DatabaseSyncService = Depends(get_sync_service)
):
    """
    Synchronize a specific entry by date.
    
    Args:
        entry_date: Date of the entry to synchronize
        
    Returns:
        Dict with sync operation details
    """
    try:
        # Start sync in background
        background_tasks.add_task(_run_single_entry_sync, sync_service, entry_date)
        
        return {
            "message": f"Entry sync started for {entry_date}",
            "sync_type": "single_entry",
            "entry_date": entry_date.isoformat(),
            "started_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start entry sync: {str(e)}")


@router.post("/scheduler/start")
async def start_scheduler(scheduler: SyncScheduler = Depends(get_scheduler)):
    """
    Start the sync scheduler.
    
    Returns:
        Dict with scheduler start confirmation
    """
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available")
    
    try:
        await scheduler.start()
        return {
            "message": "Scheduler started",
            "started_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scheduler: {str(e)}")


@router.post("/scheduler/stop")
async def stop_scheduler(scheduler: SyncScheduler = Depends(get_scheduler)):
    """
    Stop the sync scheduler.
    
    Returns:
        Dict with scheduler stop confirmation
    """
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available")
    
    try:
        await scheduler.stop()
        return {
            "message": "Scheduler stopped",
            "stopped_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop scheduler: {str(e)}")


@router.post("/scheduler/trigger/incremental")
async def trigger_scheduler_incremental(scheduler: SyncScheduler = Depends(get_scheduler)):
    """
    Manually trigger an incremental sync via scheduler.
    
    Returns:
        Dict with sync result
    """
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available")
    
    try:
        success = await scheduler.trigger_incremental_sync()
        return {
            "message": "Incremental sync triggered",
            "success": success,
            "triggered_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger incremental sync: {str(e)}")


@router.post("/scheduler/trigger/full")
async def trigger_scheduler_full(scheduler: SyncScheduler = Depends(get_scheduler)):
    """
    Manually trigger a full sync via scheduler.
    
    Returns:
        Dict with sync result
    """
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available")
    
    try:
        success = await scheduler.trigger_full_sync()
        return {
            "message": "Full sync triggered",
            "success": success,
            "triggered_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger full sync: {str(e)}")


@router.put("/scheduler/config")
async def update_scheduler_config(
    incremental_seconds: Optional[int] = None,
    full_hours: Optional[int] = None,
    scheduler: SyncScheduler = Depends(get_scheduler)
):
    """
    Update scheduler configuration.
    
    Args:
        incremental_seconds: New incremental sync interval in seconds
        full_hours: New full sync interval in hours
        
    Returns:
        Dict with updated configuration
    """
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available")
    
    try:
        scheduler.update_sync_intervals(incremental_seconds, full_hours)
        return {
            "message": "Scheduler configuration updated",
            "updated_at": datetime.utcnow().isoformat(),
            "new_config": {
                "incremental_seconds": incremental_seconds,
                "full_hours": full_hours
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update scheduler config: {str(e)}")


@router.get("/history")
async def get_sync_history(
    limit: int = 10,
    sync_type: Optional[str] = None,
    sync_service: DatabaseSyncService = Depends(get_sync_service)
):
    """
    Get synchronization history.
    
    Args:
        limit: Maximum number of records to return
        sync_type: Filter by sync type (full, incremental, single_entry)
        
    Returns:
        List of sync history records
    """
    try:
        async with sync_service.db_manager.get_session() as session:
            from sqlalchemy import select, desc
            from web.database import SyncStatus
            
            stmt = select(SyncStatus).order_by(desc(SyncStatus.started_at)).limit(limit)
            
            if sync_type:
                stmt = stmt.where(SyncStatus.sync_type == sync_type)
            
            result = await session.execute(stmt)
            sync_records = result.scalars().all()
            
            return {
                "history": [
                    {
                        "id": record.id,
                        "sync_type": record.sync_type,
                        "status": record.status,
                        "started_at": record.started_at.isoformat(),
                        "completed_at": record.completed_at.isoformat() if record.completed_at else None,
                        "entries_processed": record.entries_processed,
                        "entries_added": record.entries_added,
                        "entries_updated": record.entries_updated,
                        "entries_removed": record.entries_removed,
                        "error_message": record.error_message,
                        "duration_seconds": (
                            (record.completed_at - record.started_at).total_seconds()
                            if record.completed_at else None
                        )
                    }
                    for record in sync_records
                ],
                "total_records": len(sync_records),
                "retrieved_at": datetime.utcnow().isoformat()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sync history: {str(e)}")


# Background task functions
async def _run_full_sync(sync_service: DatabaseSyncService, date_range_days: Optional[int]):
    """Background task to run full sync."""
    try:
        result = await sync_service.full_sync(date_range_days)
        # Log result but don't return it since this is a background task
        if result.success:
            sync_service.logger.logger.info(f"Background full sync completed: {result.entries_processed} processed")
        else:
            sync_service.logger.logger.error(f"Background full sync failed: {result.errors}")
    except Exception as e:
        sync_service.logger.logger.error(f"Background full sync exception: {str(e)}")


async def _run_incremental_sync(sync_service: DatabaseSyncService, since_date: date):
    """Background task to run incremental sync."""
    try:
        result = await sync_service.incremental_sync(since_date)
        if result.success:
            sync_service.logger.logger.info(f"Background incremental sync completed: {result.entries_processed} processed")
        else:
            sync_service.logger.logger.error(f"Background incremental sync failed: {result.errors}")
    except Exception as e:
        sync_service.logger.logger.error(f"Background incremental sync exception: {str(e)}")


async def _run_single_entry_sync(sync_service: DatabaseSyncService, entry_date: date):
    """Background task to run single entry sync."""
    try:
        result = await sync_service.sync_single_entry(entry_date)
        if result.success:
            sync_service.logger.logger.debug(f"Background entry sync completed for {entry_date}")

        else:
            sync_service.logger.logger.warning(f"Background entry sync failed for {entry_date}: {result.errors}")
    except Exception as e:
        sync_service.logger.logger.error(f"Background entry sync exception for {entry_date}: {str(e)}")