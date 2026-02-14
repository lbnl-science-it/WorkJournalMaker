"""
Sync Scheduler for Work Journal Maker Web Interface

This service manages scheduled synchronization tasks, ensuring the database
stays synchronized with the file system through automated background processes.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import sys
from pathlib import Path

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from config_manager import AppConfig
from logger import JournalSummarizerLogger, ErrorCategory
from web.database import DatabaseManager
from web.services.sync_service import DatabaseSyncService, SyncType


class SyncScheduler:
    """Manages scheduled synchronization tasks."""
    
    def __init__(self, config: AppConfig, logger: JournalSummarizerLogger, 
                 db_manager: DatabaseManager):
        self.config = config
        self.logger = logger
        self.sync_service = DatabaseSyncService(config, logger, db_manager)
        
        # Scheduling configuration
        self.incremental_sync_interval = 300  # 5 minutes
        self.full_sync_interval = 3600 * 24  # 24 hours
        self.startup_sync_delay = 30  # 30 seconds after startup
        
        # Task tracking
        self._scheduler_task: Optional[asyncio.Task] = None
        self._running = False
        self._startup_sync_done = False
        
        # Statistics
        self._sync_stats = {
            "incremental_syncs": 0,
            "full_syncs": 0,
            "failed_syncs": 0,
            "last_incremental_sync": None,
            "last_full_sync": None,
            "scheduler_started_at": None
        }
    
    async def start(self):
        """Start the sync scheduler."""
        if self._running:
            self.logger.logger.warning("Sync scheduler is already running")
            return
        
        self._running = True
        self._sync_stats["scheduler_started_at"] = datetime.utcnow()
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        self.logger.logger.info("Sync scheduler started")
    
    async def stop(self):
        """Stop the sync scheduler."""
        if not self._running:
            return
            
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        self.logger.logger.info("Sync scheduler stopped")
    
    async def trigger_incremental_sync(self) -> bool:
        """
        Manually trigger an incremental sync.
        
        Returns:
            True if sync was successful, False otherwise
        """
        try:
            self.logger.logger.info("Manual incremental sync triggered")
            result = await self.sync_service.incremental_sync()
            
            if result.success:
                self._sync_stats["incremental_syncs"] += 1
                self._sync_stats["last_incremental_sync"] = result.completed_at
                self.logger.logger.info(f"Manual incremental sync completed: {result.entries_processed} processed")
                return True
            else:
                self._sync_stats["failed_syncs"] += 1
                self.logger.log_error_with_category(ErrorCategory.DATABASE_ERROR, f"Manual incremental sync failed: {result.errors}")
                return False
                
        except Exception as e:
            self._sync_stats["failed_syncs"] += 1
            self.logger.log_error_with_category(ErrorCategory.DATABASE_ERROR, f"Manual incremental sync exception: {str(e)}")
            return False
    
    async def trigger_full_sync(self) -> bool:
        """
        Manually trigger a full sync.
        
        Returns:
            True if sync was successful, False otherwise
        """
        try:
            self.logger.logger.info("Manual full sync triggered")
            result = await self.sync_service.full_sync()
            
            if result.success:
                self._sync_stats["full_syncs"] += 1
                self._sync_stats["last_full_sync"] = result.completed_at
                self.logger.logger.info(f"Manual full sync completed: {result.entries_processed} processed")
                return True
            else:
                self._sync_stats["failed_syncs"] += 1
                self.logger.log_error_with_category(ErrorCategory.DATABASE_ERROR, f"Manual full sync failed: {result.errors}")
                return False
                
        except Exception as e:
            self._sync_stats["failed_syncs"] += 1
            self.logger.log_error_with_category(ErrorCategory.DATABASE_ERROR, f"Manual full sync exception: {str(e)}")
            return False
    
    async def _scheduler_loop(self):
        """Main scheduler loop."""
        last_incremental_sync = None
        last_full_sync = None
        
        # Wait for startup delay
        await asyncio.sleep(self.startup_sync_delay)
        
        # Perform startup sync
        if not self._startup_sync_done:
            await self._run_startup_sync()
            self._startup_sync_done = True
        
        while self._running:
            try:
                current_time = datetime.utcnow()
                
                # Check for incremental sync
                if (last_incremental_sync is None or 
                    (current_time - last_incremental_sync).total_seconds() >= self.incremental_sync_interval):
                    
                    if await self._run_incremental_sync():
                        last_incremental_sync = current_time
                
                # Check for full sync
                if (last_full_sync is None or 
                    (current_time - last_full_sync).total_seconds() >= self.full_sync_interval):
                    
                    if await self._run_full_sync():
                        last_full_sync = current_time
                
                # Sleep for a short interval
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.log_error_with_category(ErrorCategory.SYSTEM_ERROR, f"Scheduler loop error: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _run_startup_sync(self):
        """Run initial sync on startup."""
        try:
            self.logger.logger.info("Running startup synchronization")
            
            # Check if database is empty or very outdated
            db_stats = await self.sync_service.db_manager.get_database_stats()
            
            if db_stats["total_entries"] == 0:
                # Database is empty, run full sync
                self.logger.logger.info("Database is empty, running full sync on startup")
                await self._run_full_sync()
            else:
                # Database has data, run incremental sync
                self.logger.logger.info("Database has data, running incremental sync on startup")
                await self._run_incremental_sync()
                
        except Exception as e:
            self.logger.log_error_with_category(ErrorCategory.DATABASE_ERROR, f"Startup sync failed: {str(e)}")
    
    async def _run_incremental_sync(self) -> bool:
        """Run incremental synchronization."""
        try:
            result = await self.sync_service.incremental_sync()
            if result.success:
                self._sync_stats["incremental_syncs"] += 1
                self._sync_stats["last_incremental_sync"] = result.completed_at
                
                if result.entries_processed > 0:
                    self.logger.logger.info(f"Incremental sync completed: {result.entries_processed} processed, "
                                   f"{result.entries_added} added, {result.entries_updated} updated")
                else:
                    self.logger.logger.debug("Incremental sync completed: no changes detected")
                return True
            else:
                self._sync_stats["failed_syncs"] += 1
                self.logger.logger.warning(f"Incremental sync had errors: {result.errors}")
                return False
        except Exception as e:
            self._sync_stats["failed_syncs"] += 1
            self.logger.log_error_with_category(ErrorCategory.DATABASE_ERROR, f"Incremental sync failed: {str(e)}")
            return False
    
    async def _run_full_sync(self) -> bool:
        """Run full synchronization."""
        try:
            result = await self.sync_service.full_sync()
            if result.success:
                self._sync_stats["full_syncs"] += 1
                self._sync_stats["last_full_sync"] = result.completed_at
                self.logger.logger.info(f"Full sync completed: {result.entries_processed} processed, "
                               f"{result.entries_added} added, {result.entries_updated} updated, "
                               f"{result.entries_removed} removed")
                return True
            else:
                self._sync_stats["failed_syncs"] += 1
                self.logger.log_error_with_category(ErrorCategory.DATABASE_ERROR, f"Full sync failed: {result.errors}")
                return False
        except Exception as e:
            self._sync_stats["failed_syncs"] += 1
            self.logger.log_error_with_category(ErrorCategory.DATABASE_ERROR, f"Full sync failed: {str(e)}")
            return False
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status and statistics."""
        return {
            "running": self._running,
            "startup_sync_done": self._startup_sync_done,
            "configuration": {
                "incremental_sync_interval_seconds": self.incremental_sync_interval,
                "full_sync_interval_seconds": self.full_sync_interval,
                "startup_sync_delay_seconds": self.startup_sync_delay
            },
            "statistics": {
                **self._sync_stats,
                "last_incremental_sync": self._sync_stats["last_incremental_sync"].isoformat() 
                    if self._sync_stats["last_incremental_sync"] else None,
                "last_full_sync": self._sync_stats["last_full_sync"].isoformat() 
                    if self._sync_stats["last_full_sync"] else None,
                "scheduler_started_at": self._sync_stats["scheduler_started_at"].isoformat() 
                    if self._sync_stats["scheduler_started_at"] else None
            },
            "next_sync_estimates": self._calculate_next_sync_times()
        }
    
    def _calculate_next_sync_times(self) -> Dict[str, Optional[str]]:
        """Calculate estimated times for next syncs."""
        if not self._running:
            return {"incremental": None, "full": None}
        
        current_time = datetime.utcnow()
        
        # Calculate next incremental sync
        next_incremental = None
        if self._sync_stats["last_incremental_sync"]:
            next_incremental = (self._sync_stats["last_incremental_sync"] + 
                              timedelta(seconds=self.incremental_sync_interval))
        else:
            next_incremental = current_time + timedelta(seconds=self.incremental_sync_interval)
        
        # Calculate next full sync
        next_full = None
        if self._sync_stats["last_full_sync"]:
            next_full = (self._sync_stats["last_full_sync"] + 
                        timedelta(seconds=self.full_sync_interval))
        else:
            next_full = current_time + timedelta(seconds=self.full_sync_interval)
        
        return {
            "incremental": next_incremental.isoformat() if next_incremental else None,
            "full": next_full.isoformat() if next_full else None
        }
    
    async def sync_entry_on_save(self, entry_date) -> bool:
        """
        Sync a specific entry immediately after it's saved via web interface.
        This ensures the database is updated immediately for web operations.
        
        Args:
            entry_date: Date of the entry that was saved
            
        Returns:
            True if sync was successful, False otherwise
        """
        try:
            result = await self.sync_service.sync_single_entry(entry_date)
            if result.success:
                self.logger.logger.debug(f"Entry sync completed for {entry_date}")
                return True
            else:
                self.logger.logger.warning(f"Entry sync failed for {entry_date}: {result.errors}")
                return False
        except Exception as e:
            self.logger.log_error_with_category(ErrorCategory.DATABASE_ERROR, f"Entry sync exception for {entry_date}: {str(e)}")
            return False
    
    def update_sync_intervals(self, incremental_seconds: Optional[int] = None, 
                            full_hours: Optional[int] = None):
        """
        Update sync intervals dynamically.
        
        Args:
            incremental_seconds: New incremental sync interval in seconds
            full_hours: New full sync interval in hours
        """
        if incremental_seconds is not None and incremental_seconds > 0:
            self.incremental_sync_interval = incremental_seconds
            self.logger.logger.info(f"Updated incremental sync interval to {incremental_seconds} seconds")
        
        if full_hours is not None and full_hours > 0:
            self.full_sync_interval = full_hours * 3600
            self.logger.logger.info(f"Updated full sync interval to {full_hours} hours")