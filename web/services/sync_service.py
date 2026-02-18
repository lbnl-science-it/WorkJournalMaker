"""
Database Synchronization Service for Work Journal Maker Web Interface

This service manages synchronization between the SQLite index and the existing file system,
ensuring consistency between web and CLI operations while maintaining the file system
as the source of truth.
"""

import asyncio
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
import json

from file_discovery import FileDiscovery, FileDiscoveryResult
from config_manager import AppConfig
from logger import JournalSummarizerLogger, ErrorCategory
from web.database import DatabaseManager, JournalEntryIndex, SyncStatus
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.exc import IntegrityError


class SyncType(Enum):
    """Types of synchronization operations."""
    FULL = "full"
    INCREMENTAL = "incremental"
    SINGLE_ENTRY = "single_entry"
    CLEANUP = "cleanup"


@dataclass
class SyncResult:
    """Result of a synchronization operation."""
    sync_type: SyncType
    started_at: datetime
    completed_at: Optional[datetime]
    success: bool
    entries_processed: int = 0
    entries_added: int = 0
    entries_updated: int = 0
    entries_removed: int = 0
    errors: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}


class DatabaseSyncService:
    """
    Manages synchronization between file system and database index.
    Ensures data consistency while maintaining file system as source of truth.
    """
    
    def __init__(self, config: AppConfig, logger: JournalSummarizerLogger, 
                 db_manager: DatabaseManager):
        self.config = config
        self.logger = logger
        self.db_manager = db_manager
        self.file_discovery = FileDiscovery(config.processing.base_path)
        
        # Sync configuration
        self.sync_batch_size = 100
        self.sync_date_range_days = 730  # 2 years default
        self.cleanup_threshold_days = 30  # Remove orphaned entries older than 30 days
        
        # Sync state tracking
        self._sync_in_progress = False
        self._last_full_sync = None
        self._sync_lock = asyncio.Lock()
    
    async def full_sync(self, date_range_days: Optional[int] = None) -> SyncResult:
        """
        Perform full synchronization between file system and database.
        
        Args:
            date_range_days: Number of days to scan (default: 730)
            
        Returns:
            SyncResult with operation details
        """
        if self._sync_in_progress:
            raise RuntimeError("Sync already in progress")
        
        async with self._sync_lock:
            if self._sync_in_progress:
                raise RuntimeError("Sync already in progress")
            
            self._sync_in_progress = True
            
        sync_result = SyncResult(
            sync_type=SyncType.FULL,
            started_at=datetime.utcnow(),
            completed_at=None,
            success=False
        )
        
        try:
            self.logger.logger.info("Starting full database synchronization")
            
            # Record sync start in database
            sync_id = await self._record_sync_start(SyncType.FULL)
            
            # Determine date range
            days = date_range_days or self.sync_date_range_days
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            # Discover files using existing FileDiscovery
            self.logger.logger.info(f"Discovering files from {start_date} to {end_date}")
            discovery_result = self.file_discovery.discover_files(start_date, end_date)
            
            # Process files in batches
            file_batches = self._batch_files(discovery_result.found_files, self.sync_batch_size)
            
            for batch_num, file_batch in enumerate(file_batches, 1):
                self.logger.logger.debug(f"Processing batch {batch_num}/{len(file_batches)}")
                batch_result = await self._process_file_batch(file_batch)
                
                sync_result.entries_processed += batch_result["processed"]
                sync_result.entries_added += batch_result["added"]
                sync_result.entries_updated += batch_result["updated"]
                sync_result.errors.extend(batch_result["errors"])
            
            # Cleanup orphaned database entries
            cleanup_result = await self._cleanup_orphaned_entries(discovery_result.found_files)
            sync_result.entries_removed = cleanup_result["removed"]
            sync_result.errors.extend(cleanup_result["errors"])
            
            # Mark sync as completed
            sync_result.completed_at = datetime.utcnow()
            sync_result.success = True
            sync_result.metadata = {
                "date_range": {"start": start_date.isoformat(), "end": end_date.isoformat()},
                "files_discovered": len(discovery_result.found_files),
                "batches_processed": len(file_batches),
                "discovery_stats": discovery_result.directory_scan_stats
            }
            
            await self._record_sync_completion(sync_id, sync_result)
            self._last_full_sync = datetime.utcnow()
            
            self.logger.logger.info(f"Full sync completed: {sync_result.entries_processed} processed, "
                           f"{sync_result.entries_added} added, {sync_result.entries_updated} updated, "
                           f"{sync_result.entries_removed} removed")
            
        except Exception as e:
            sync_result.errors.append(str(e))
            self.logger.log_error_with_category(ErrorCategory.DATABASE_ERROR, f"Full sync failed: {str(e)}")
            await self._record_sync_failure(sync_id, str(e))
            
        finally:
            self._sync_in_progress = False
            
        return sync_result
    
    async def incremental_sync(self, since_date: Optional[date] = None) -> SyncResult:
        """
        Perform incremental synchronization for recent changes.
        
        Args:
            since_date: Date to sync from (default: last 7 days)
            
        Returns:
            SyncResult with operation details
        """
        sync_result = SyncResult(
            sync_type=SyncType.INCREMENTAL,
            started_at=datetime.utcnow(),
            completed_at=None,
            success=False
        )
        
        try:
            # Determine sync date range
            if since_date is None:
                since_date = date.today() - timedelta(days=7)
            end_date = date.today()
            
            self.logger.logger.info(f"Starting incremental sync from {since_date}")
            
            # Record sync start
            sync_id = await self._record_sync_start(SyncType.INCREMENTAL)
            
            # Discover recent files
            discovery_result = self.file_discovery.discover_files(since_date, end_date)
            
            # Process files
            batch_result = await self._process_file_batch(discovery_result.found_files)
            
            sync_result.entries_processed = batch_result["processed"]
            sync_result.entries_added = batch_result["added"]
            sync_result.entries_updated = batch_result["updated"]
            sync_result.errors = batch_result["errors"]
            sync_result.completed_at = datetime.utcnow()
            sync_result.success = True
            sync_result.metadata = {
                "date_range": {"start": since_date.isoformat(), "end": end_date.isoformat()},
                "files_discovered": len(discovery_result.found_files)
            }
            
            await self._record_sync_completion(sync_id, sync_result)
            
            self.logger.logger.info(f"Incremental sync completed: {sync_result.entries_processed} processed")
            
        except Exception as e:
            sync_result.errors.append(str(e))
            self.logger.log_error_with_category(ErrorCategory.DATABASE_ERROR, f"Incremental sync failed: {str(e)}")
            await self._record_sync_failure(sync_id, str(e))
            
        return sync_result
    
    async def sync_single_entry(self, entry_date: date) -> SyncResult:
        """
        Synchronize a single entry between file system and database.
        
        Args:
            entry_date: Date of entry to synchronize
            
        Returns:
            SyncResult with operation details
        """
        sync_result = SyncResult(
            sync_type=SyncType.SINGLE_ENTRY,
            started_at=datetime.utcnow(),
            completed_at=None,
            success=False
        )
        
        try:
            self.logger.logger.debug(f"Starting single entry sync for {entry_date}")
            
            # Record sync start
            sync_id = await self._record_sync_start(SyncType.SINGLE_ENTRY)
            
            # Get file path using existing FileDiscovery
            week_ending_date = self.file_discovery._find_week_ending_for_date(entry_date)
            file_path = self.file_discovery._construct_file_path(entry_date, week_ending_date)
            
            if file_path.exists():
                batch_result = await self._process_file_batch([file_path])
                sync_result.entries_processed = batch_result["processed"]
                sync_result.entries_added = batch_result["added"]
                sync_result.entries_updated = batch_result["updated"]
                sync_result.errors = batch_result["errors"]
            else:
                # Remove from database if file doesn't exist
                await self._remove_entry_from_database(entry_date)
                sync_result.entries_removed = 1
            
            sync_result.completed_at = datetime.utcnow()
            sync_result.success = True
            sync_result.metadata = {"entry_date": entry_date.isoformat()}
            
            await self._record_sync_completion(sync_id, sync_result)
            
        except Exception as e:
            sync_result.errors.append(str(e))
            self.logger.log_error_with_category(ErrorCategory.DATABASE_ERROR, f"Single entry sync failed for {entry_date}: {str(e)}")
            await self._record_sync_failure(sync_id, str(e))
            
        return sync_result
    
    async def _process_file_batch(self, file_paths: List[Path]) -> Dict[str, Any]:
        """Process a batch of files for synchronization."""
        result = {
            "processed": 0,
            "added": 0,
            "updated": 0,
            "errors": []
        }
        
        async with self.db_manager.get_session() as session:
            for file_path in file_paths:
                try:
                    entry_date = self._extract_date_from_path(file_path)
                    if not entry_date:
                        result["errors"].append(f"Could not extract date from {file_path}")
                        continue
                    
                    # Check if entry exists in database
                    stmt = select(JournalEntryIndex).where(JournalEntryIndex.date == entry_date)
                    existing_entry = await session.scalar(stmt)
                    
                    # Get file stats and content metadata
                    file_stats = file_path.stat()
                    content_metadata = await self._get_file_metadata(file_path)
                    
                    # Calculate week ending date using existing logic
                    week_ending_date = self.file_discovery._find_week_ending_for_date(entry_date)
                    
                    if existing_entry:
                        # Check if update is needed
                        if (not existing_entry.file_modified_at or 
                            existing_entry.file_modified_at < datetime.fromtimestamp(file_stats.st_mtime)):
                            
                            # Update existing entry
                            update_stmt = (
                                update(JournalEntryIndex)
                                .where(JournalEntryIndex.date == entry_date)
                                .values(
                                    file_path=str(file_path),
                                    week_ending_date=week_ending_date,
                                    word_count=content_metadata["word_count"],
                                    character_count=content_metadata["character_count"],
                                    line_count=content_metadata["line_count"],
                                    has_content=content_metadata["has_content"],
                                    file_size_bytes=file_stats.st_size,
                                    file_modified_at=datetime.fromtimestamp(file_stats.st_mtime),
                                    modified_at=datetime.utcnow(),
                                    synced_at=datetime.utcnow()
                                )
                            )
                            await session.execute(update_stmt)
                            result["updated"] += 1
                    else:
                        # Create new entry
                        new_entry = JournalEntryIndex(
                            date=entry_date,
                            file_path=str(file_path),
                            week_ending_date=week_ending_date,
                            word_count=content_metadata["word_count"],
                            character_count=content_metadata["character_count"],
                            line_count=content_metadata["line_count"],
                            has_content=content_metadata["has_content"],
                            file_size_bytes=file_stats.st_size,
                            file_modified_at=datetime.fromtimestamp(file_stats.st_mtime),
                            created_at=datetime.utcnow(),
                            modified_at=datetime.utcnow(),
                            synced_at=datetime.utcnow()
                        )
                        session.add(new_entry)
                        result["added"] += 1
                    
                    result["processed"] += 1
                    
                except Exception as e:
                    result["errors"].append(f"Error processing {file_path}: {str(e)}")
                    self.logger.log_error_with_category(ErrorCategory.FILE_ACCESS_ERROR, f"Error processing file {file_path}: {str(e)}")
            
            await session.commit()
        
        return result
    
    async def _cleanup_orphaned_entries(self, existing_files: List[Path]) -> Dict[str, Any]:
        """Remove database entries for files that no longer exist."""
        result = {"removed": 0, "errors": []}
        
        try:
            # Get set of existing file paths
            existing_paths = {str(path) for path in existing_files}
            
            async with self.db_manager.get_session() as session:
                # Find database entries not in existing files
                stmt = select(JournalEntryIndex)
                all_entries = await session.scalars(stmt)
                
                entries_to_remove = []
                for entry in all_entries:
                    if entry.file_path not in existing_paths:
                        # Double-check that file doesn't exist
                        if not Path(entry.file_path).exists():
                            entries_to_remove.append(entry.date)
                
                # Remove orphaned entries
                if entries_to_remove:
                    delete_stmt = delete(JournalEntryIndex).where(
                        JournalEntryIndex.date.in_(entries_to_remove)
                    )
                    await session.execute(delete_stmt)
                    await session.commit()
                    result["removed"] = len(entries_to_remove)
                    
                    self.logger.logger.info(f"Removed {len(entries_to_remove)} orphaned database entries")
        
        except Exception as e:
            result["errors"].append(f"Cleanup error: {str(e)}")
            self.logger.log_error_with_category(ErrorCategory.DATABASE_ERROR, f"Cleanup failed: {str(e)}")
        
        return result
    
    async def _remove_entry_from_database(self, entry_date: date) -> None:
        """Remove a specific entry from the database."""
        try:
            async with self.db_manager.get_session() as session:
                delete_stmt = delete(JournalEntryIndex).where(JournalEntryIndex.date == entry_date)
                await session.execute(delete_stmt)
                await session.commit()
        except Exception as e:
            self.logger.log_error_with_category(ErrorCategory.DATABASE_ERROR, f"Failed to remove entry {entry_date} from database: {str(e)}")
    
    async def _get_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Get metadata for a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            words = content.split()
            
            return {
                "word_count": len(words),
                "character_count": len(content),
                "line_count": len(lines),
                "has_content": len(content.strip()) > 0
            }
        except Exception as e:
            self.logger.log_error_with_category(ErrorCategory.FILE_ACCESS_ERROR, f"Failed to get metadata for {file_path}: {str(e)}")
            return {
                "word_count": 0,
                "character_count": 0,
                "line_count": 0,
                "has_content": False
            }
    
    def _extract_date_from_path(self, file_path: Path) -> Optional[date]:
        """Extract date from file path using existing naming convention."""
        try:
            # File name format: worklog_YYYY-MM-DD.txt
            filename = file_path.stem
            if filename.startswith('worklog_'):
                date_str = filename[8:]  # Remove 'worklog_' prefix
                return datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception:
            pass
        return None
    
    def _batch_files(self, files: List[Path], batch_size: int) -> List[List[Path]]:
        """Split files into batches for processing."""
        return [files[i:i + batch_size] for i in range(0, len(files), batch_size)]
    
    async def _record_sync_start(self, sync_type: SyncType) -> int:
        """Record sync start in database."""
        async with self.db_manager.get_session() as session:
            sync_record = SyncStatus(
                sync_type=sync_type.value,
                started_at=datetime.utcnow(),
                status="running"
            )
            session.add(sync_record)
            await session.commit()
            await session.refresh(sync_record)
            return sync_record.id
    
    async def _record_sync_completion(self, sync_id: int, result: SyncResult) -> None:
        """Record sync completion in database."""
        async with self.db_manager.get_session() as session:
            update_stmt = (
                update(SyncStatus)
                .where(SyncStatus.id == sync_id)
                .values(
                    completed_at=result.completed_at,
                    status="completed",
                    entries_processed=result.entries_processed,
                    entries_added=result.entries_added,
                    entries_updated=result.entries_updated,
                    entries_removed=result.entries_removed,
                    sync_metadata=json.dumps(result.metadata) if result.metadata else None
                )
            )
            await session.execute(update_stmt)
            await session.commit()
    
    async def _record_sync_failure(self, sync_id: int, error_message: str) -> None:
        """Record sync failure in database."""
        async with self.db_manager.get_session() as session:
            update_stmt = (
                update(SyncStatus)
                .where(SyncStatus.id == sync_id)
                .values(
                    completed_at=datetime.utcnow(),
                    status="failed",
                    error_message=error_message
                )
            )
            await session.execute(update_stmt)
            await session.commit()
    
    async def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status."""
        async with self.db_manager.get_session() as session:
            # Get latest sync records
            stmt = (
                select(SyncStatus)
                .order_by(SyncStatus.started_at.desc())
                .limit(5)
            )
            recent_syncs = await session.scalars(stmt)
            
            return {
                "sync_in_progress": self._sync_in_progress,
                "last_full_sync": self._last_full_sync.isoformat() if self._last_full_sync else None,
                "recent_syncs": [
                    {
                        "id": sync.id,
                        "type": sync.sync_type,
                        "status": sync.status,
                        "started_at": sync.started_at.isoformat(),
                        "completed_at": sync.completed_at.isoformat() if sync.completed_at else None,
                        "entries_processed": sync.entries_processed,
                        "entries_added": sync.entries_added,
                        "entries_updated": sync.entries_updated,
                        "entries_removed": sync.entries_removed,
                        "error_message": sync.error_message
                    }
                    for sync in recent_syncs
                ]
            }
    
    async def force_sync_entry(self, entry_date: date) -> bool:
        """
        Force synchronization of a specific entry, useful for web operations.
        
        Args:
            entry_date: Date of entry to force sync
            
        Returns:
            True if sync was successful, False otherwise
        """
        try:
            result = await self.sync_single_entry(entry_date)
            return result.success
        except Exception as e:
            self.logger.log_error_with_category(ErrorCategory.DATABASE_ERROR, f"Force sync failed for {entry_date}: {str(e)}")
            return False