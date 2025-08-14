"""
EntryManager Service for Work Journal Maker Web Interface

This service wraps the existing FileDiscovery system, providing web-friendly APIs
while maintaining full compatibility with the CLI codebase. It acts as the bridge
between the web interface and the existing file system operations.
"""

import asyncio
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import aiofiles
import os
import sys
from contextlib import asynccontextmanager

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from file_discovery import FileDiscovery, FileDiscoveryResult
from config_manager import AppConfig
from logger import JournalSummarizerLogger, ErrorCategory
from web.database import DatabaseManager, JournalEntryIndex
from web.models.journal import (
    JournalEntryResponse, JournalEntryMetadata, EntryStatus,
    RecentEntriesResponse, EntryListRequest
)
from web.services.base_service import BaseService
from web.services.work_week_service import WorkWeekService
from web.utils.timezone_utils import now_utc, to_local
from web.services.work_week_service import WorkWeekService
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.exc import IntegrityError


class EntryManager(BaseService):
    """
    Manages journal entries by wrapping the existing FileDiscovery system
    and providing web-friendly async APIs with database indexing.
    
    This service maintains compatibility with CLI operations while providing
    fast web queries through database indexing.
    """
    
    def __init__(self, config: AppConfig, logger: JournalSummarizerLogger, 
                 db_manager: DatabaseManager, work_week_service: Optional[WorkWeekService] = None):
        """
        Initialize EntryManager with core dependencies.
        
        Args:
            config: Application configuration
            logger: Logger instance
            db_manager: Database manager instance
            work_week_service: Optional work week service for directory calculations
        """
        super().__init__(config, logger, db_manager)
        
        # Store original config as fallback
        self._original_config = config
        
        # Initialize FileDiscovery with dynamic base path (will be updated)
        self.file_discovery = None
        self._current_base_path = None
        
        # Initialize WorkWeekService if provided, otherwise create one
        self.work_week_service = work_week_service or WorkWeekService(config, logger, db_manager)
        
        # Cache for frequently accessed data
        self._entry_cache = {}
        self._cache_ttl = 300  # 5 minutes
        
        # Settings cache
        self._settings_cache = {}
        self._settings_cache_expiry = None
        self._settings_cache_ttl = 300  # 5 minutes
        
    
    async def _get_current_settings(self) -> Dict[str, Any]:
        """Get current settings from database with caching."""
        from datetime import timezone
        
        # Check cache
        now = datetime.now(timezone.utc)
        if (self._settings_cache_expiry and 
            now < self._settings_cache_expiry and 
            self._settings_cache):
            return self._settings_cache
        
        try:
            # Get settings from SettingsService
            from web.services.settings_service import SettingsService
            settings_service = SettingsService(self._original_config, self.logger, self.db_manager)
            
            # Get filesystem settings
            base_path_setting = await settings_service.get_setting('filesystem.base_path')
            output_path_setting = await settings_service.get_setting('filesystem.output_path')
            
            current_settings = {
                'base_path': base_path_setting.parsed_value if base_path_setting else self._original_config.processing.base_path,
                'output_path': output_path_setting.parsed_value if output_path_setting else self._original_config.processing.output_path
            }
            
            # Cache settings
            self._settings_cache = current_settings
            self._settings_cache_expiry = now + timedelta(seconds=self._settings_cache_ttl)
            
            return current_settings
            
        except Exception as e:
            self.logger.logger.warning(f"Failed to get current settings, using defaults: {e}")
            return {
                'base_path': self._original_config.processing.base_path,
                'output_path': self._original_config.processing.output_path
            }
    
    async def _ensure_file_discovery_initialized(self):
        """Ensure FileDiscovery is initialized with current base path."""
        current_settings = await self._get_current_settings()
        current_base_path = current_settings['base_path']
        
        # Initialize or update FileDiscovery if base path changed
        if (self.file_discovery is None or 
            self._current_base_path != current_base_path):
            
            self.file_discovery = FileDiscovery(current_base_path)
            self._current_base_path = current_base_path
            self.logger.logger.info(f"FileDiscovery initialized with base path: {current_base_path}")
    async def get_entry_content(self, entry_date: date) -> Optional[str]:
        """
        Get content for a specific journal entry date.
        
        This method now handles both new work week organized directories and
        existing legacy directories for backward compatibility.
        
        Args:
            entry_date: Date of the entry to retrieve
            
        Returns:
            Entry content as string, or None if entry doesn't exist
        """
        self._log_operation_start("get_entry_content", date=entry_date)
        
        try:
            # Ensure FileDiscovery is initialized with current settings
            await self._ensure_file_discovery_initialized()
            
            # Construct file path using work week calculations when available
            file_path = await self._construct_file_path_async(entry_date)
            
            if not file_path.exists():
                # Backward compatibility: try to find entry in legacy directory structure
                legacy_file_path = await self._try_find_entry_in_legacy_structure(entry_date)
                if legacy_file_path and legacy_file_path.exists():
                    file_path = legacy_file_path
                    self.logger.logger.debug(f"Found entry in legacy location: {file_path}")
                else:
                    self.logger.logger.info(f"Entry file does not exist: {file_path}")
                    return None
            
            # Read file content asynchronously
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                content = await file.read()
            
            # Update database index with access information
            await self._update_entry_access(entry_date, file_path)
            
            self._log_operation_success("get_entry_content", date=entry_date, 
                                      content_length=len(content))
            return content
            
        except Exception as e:
            self._log_operation_error("get_entry_content", e, date=entry_date)
            return None
    
    async def save_entry_content(self, entry_date: date, content: str) -> bool:
        """
        Save content for a specific journal entry date.
        
        Args:
            entry_date: Date of the entry to save
            content: Content to save
            
        Returns:
            True if save was successful, False otherwise
        """
        self._log_operation_start("save_entry_content", date=entry_date, 
                                content_length=len(content))
        
        try:
            # Ensure FileDiscovery is initialized with current settings
            await self._ensure_file_discovery_initialized()
            
            # Use work week calculations for file path construction
            file_path = await self._construct_file_path_async(entry_date)
            
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file content asynchronously
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as file:
                await file.write(content)
            
            # Update database index
            await self._sync_entry_to_database(entry_date, file_path, content)
            
            self._log_operation_success("save_entry_content", date=entry_date)
            return True
            
        except Exception as e:
            self._log_operation_error("save_entry_content", e, date=entry_date)
            return False
    
    def is_work_week_service_available(self) -> bool:
        """
        Check if WorkWeekService is available for use.
        
        Returns:
            bool: True if work week service is available, False otherwise
        """
        return self.work_week_service is not None
    
    async def get_work_week_integration_status(self) -> Dict[str, Any]:
        """
        Get status information about work week integration.
        
        Returns:
            Dict containing integration status and configuration
        """
        try:
            status = {
                'work_week_service_available': self.is_work_week_service_available(),
                'integration_enabled': self.work_week_service is not None,
                'fallback_mode': self.work_week_service is None,
                'file_discovery_available': True,
                'timestamp': now_utc().isoformat()
            }
            
            if self.work_week_service:
                # Get work week service health status
                work_week_status = self.work_week_service.get_service_health_status()
                status['work_week_service_status'] = work_week_status
                
                # Get current user configuration
                try:
                    user_config = await self.work_week_service.get_user_work_week_config()
                    status['current_work_week_config'] = user_config.to_dict()
                except Exception as e:
                    status['config_error'] = str(e)
            
            return status
            
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': now_utc().isoformat()
            }
    
    async def get_recent_entries(self, limit: int = 10) -> RecentEntriesResponse:
        """
        Get recent journal entries with metadata.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            RecentEntriesResponse with entry list and metadata
        """
        self._log_operation_start("get_recent_entries", limit=limit)
        
        try:
            async with self.db_manager.get_session() as session:
                # Query recent entries from database index
                stmt = (
                    select(JournalEntryIndex)
                    .order_by(JournalEntryIndex.date.desc())
                    .limit(limit + 1)  # Get one extra to check if there are more
                )
                result = await session.execute(stmt)
                db_entries = result.scalars().all()
                
                # Check if there are more entries
                has_more = len(db_entries) > limit
                if has_more:
                    db_entries = db_entries[:limit]
                
                # Convert to response models
                entries = []
                for db_entry in db_entries:
                    entry_response = await self._db_entry_to_response(db_entry)
                    if entry_response:
                        entries.append(entry_response)
                
                response = RecentEntriesResponse(
                    entries=entries,
                    total_count=len(entries),
                    has_more=has_more,
                    pagination={
                        "limit": limit,
                        "offset": 0,
                        "has_next": has_more
                    }
                )
                
                self._log_operation_success("get_recent_entries", 
                                          entries_returned=len(entries))
                return response
                
        except Exception as e:
            self._log_operation_error("get_recent_entries", e, limit=limit)
            return RecentEntriesResponse(entries=[], total_count=0, has_more=False, pagination={})
    
    async def list_entries(self, request: EntryListRequest) -> RecentEntriesResponse:
        """
        List entries with filtering and pagination.
        
        Args:
            request: Entry list request with filters and pagination
            
        Returns:
            RecentEntriesResponse with filtered entries
        """
        self._log_operation_start("list_entries", 
                                start_date=request.start_date,
                                end_date=request.end_date,
                                limit=request.limit,
                                offset=request.offset)
        
        try:
            async with self.db_manager.get_session() as session:
                # Build query with filters
                stmt = select(JournalEntryIndex)
                
                # Date range filter
                if request.start_date:
                    stmt = stmt.where(JournalEntryIndex.date >= request.start_date)
                if request.end_date:
                    stmt = stmt.where(JournalEntryIndex.date <= request.end_date)
                
                # Content filter
                if request.has_content is not None:
                    stmt = stmt.where(JournalEntryIndex.has_content == request.has_content)
                
                # Sorting
                if request.sort_by == "date":
                    if request.sort_order == "desc":
                        stmt = stmt.order_by(JournalEntryIndex.date.desc())
                    else:
                        stmt = stmt.order_by(JournalEntryIndex.date.asc())
                elif request.sort_by == "word_count":
                    if request.sort_order == "desc":
                        stmt = stmt.order_by(JournalEntryIndex.word_count.desc())
                    else:
                        stmt = stmt.order_by(JournalEntryIndex.word_count.asc())
                elif request.sort_by == "created_at":
                    if request.sort_order == "desc":
                        stmt = stmt.order_by(JournalEntryIndex.created_at.desc())
                    else:
                        stmt = stmt.order_by(JournalEntryIndex.created_at.asc())
                elif request.sort_by == "modified_at":
                    if request.sort_order == "desc":
                        stmt = stmt.order_by(JournalEntryIndex.modified_at.desc())
                    else:
                        stmt = stmt.order_by(JournalEntryIndex.modified_at.asc())
                
                # Get total count for pagination
                count_stmt = select(JournalEntryIndex.id).where(stmt.whereclause)
                total_count_result = await session.execute(count_stmt)
                total_count = len(total_count_result.scalars().all())
                
                # Apply pagination
                stmt = stmt.offset(request.offset).limit(request.limit + 1)
                
                result = await session.execute(stmt)
                db_entries = result.scalars().all()
                
                # Check if there are more entries
                has_more = len(db_entries) > request.limit
                if has_more:
                    db_entries = db_entries[:request.limit]
                
                # Convert to response models
                entries = []
                for db_entry in db_entries:
                    entry_response = await self._db_entry_to_response(db_entry)
                    if entry_response:
                        entries.append(entry_response)
                
                response = RecentEntriesResponse(
                    entries=entries,
                    total_count=total_count,
                    has_more=has_more,
                    pagination={
                        "limit": request.limit,
                        "offset": request.offset,
                        "total": total_count,
                        "has_next": has_more,
                        "has_prev": request.offset > 0
                    }
                )
                
                self._log_operation_success("list_entries", 
                                          entries_returned=len(entries),
                                          total_count=total_count)
                return response
                
        except Exception as e:
            self._log_operation_error("list_entries", e, 
                                    start_date=request.start_date,
                                    end_date=request.end_date)
            return RecentEntriesResponse(entries=[], total_count=0, has_more=False, pagination={})
    
    async def get_entry_by_date(self, entry_date: date, include_content: bool = False) -> Optional[JournalEntryResponse]:
        """
        Get a specific entry by date with optional content.
        
        Args:
            entry_date: Date of the entry to retrieve
            include_content: Whether to include entry content
            
        Returns:
            JournalEntryResponse or None if not found
        """
        self._log_operation_start("get_entry_by_date", date=entry_date, 
                                include_content=include_content)
        
        try:
            async with self.db_manager.get_session() as session:
                stmt = select(JournalEntryIndex).where(JournalEntryIndex.date == entry_date)
                result = await session.execute(stmt)
                db_entry = result.scalar_one_or_none()
                
                if not db_entry:
                    # Check if file exists but not in database
                    file_path = await self._construct_file_path_async(entry_date)
                    if file_path.exists():
                        # Sync to database and try again
                        await self._sync_entry_to_database(entry_date, file_path)
                        result = await session.execute(stmt)
                        db_entry = result.scalar_one_or_none()
                
                if not db_entry:
                    return None
                
                # Convert to response model
                entry_response = await self._db_entry_to_response(db_entry, include_content)
                
                # Update access statistics
                if entry_response:
                    await self._update_entry_access(entry_date, Path(db_entry.file_path))
                
                self._log_operation_success("get_entry_by_date", date=entry_date)
                return entry_response
                
        except Exception as e:
            self._log_operation_error("get_entry_by_date", e, date=entry_date)
            return None
    
    async def delete_entry(self, entry_date: date) -> bool:
        """
        Delete an entry (both file and database record).
        
        Args:
            entry_date: Date of the entry to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        self._log_operation_start("delete_entry", date=entry_date)
        
        try:
            # Get file path
            file_path = await self._construct_file_path_async(entry_date)
            
            # Delete file if it exists
            if file_path.exists():
                file_path.unlink()
            
            # Remove from database
            async with self.db_manager.get_session() as session:
                delete_stmt = delete(JournalEntryIndex).where(JournalEntryIndex.date == entry_date)
                await session.execute(delete_stmt)
                await session.commit()
            
            self._log_operation_success("delete_entry", date=entry_date)
            return True
            
        except Exception as e:
            self._log_operation_error("delete_entry", e, date=entry_date)
            return False
    
    def _construct_file_path(self, entry_date: date) -> Path:
        """
        Construct file path for a given date using work week calculations with fallback.
        
        Args:
            entry_date: Date of the entry
            
        Returns:
            Path to the entry file
        """
        try:
            # Try to get week ending date from work week service
            week_ending_date = asyncio.run(self.work_week_service.calculate_week_ending_date(entry_date))
        except Exception as e:
            self.logger.logger.warning(f"Failed to calculate work week ending date for {entry_date}, using fallback: {str(e)}")
            # Fallback to existing file discovery logic
            week_ending_date = self.file_discovery._find_week_ending_for_date(entry_date)
        
        # Use existing FileDiscovery method to construct path
        return self.file_discovery._construct_file_path(entry_date, week_ending_date)
    
    async def _construct_file_path_async(self, entry_date: date) -> Path:
        """
        Async version of file path construction using work week calculations.

        Args:
            entry_date: Date of the entry

        Returns:
            Path to the entry file
        """
        try:
            # Use work week service for proper weekly organization
            week_ending_date = await self.work_week_service.calculate_week_ending_date(entry_date)
            self.logger.logger.debug(f"Work week calculation (async): {entry_date} -> week ending {week_ending_date}")
        except Exception as e:
            # Fallback to existing logic if work week calculation fails
            self.logger.logger.warning(f"Async work week calculation failed for {entry_date}: {str(e)}, falling back to legacy logic")
            week_ending_date = self.file_discovery._find_week_ending_for_date(entry_date)
        
        # Use existing FileDiscovery method to construct path
        return self.file_discovery._construct_file_path(entry_date, week_ending_date)
    
    async def _sync_entry_to_database(self, entry_date: date, file_path: Path, 
                                    content: Optional[str] = None) -> None:
        """Sync a single entry to database."""
        async with self.db_manager.get_session() as session:
            await self._sync_entry_to_database_session(session, entry_date, file_path, content)
            await session.commit()
    
    async def _sync_entry_to_database_session(self, session, entry_date: date, 
                                            file_path: Path, content: Optional[str] = None) -> None:
        """Sync a single entry to database within an existing session with work week calculations."""
        try:
            # Get file stats
            file_stats = file_path.stat() if file_path.exists() else None
            
            # Read content if not provided
            if content is None and file_path.exists():
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    content = await f.read()
            
            # Calculate metadata
            metadata = self._calculate_entry_metadata(content or "")
            
            # Calculate week ending date using work week service with fallback
            try:
                week_ending_date = await self.work_week_service.calculate_week_ending_date(entry_date)
                self.logger.logger.debug(f"Calculated week ending date for {entry_date}: {week_ending_date}")
            except Exception as e:
                self.logger.logger.warning(f"Failed to calculate work week ending date for {entry_date}, using fallback: {str(e)}")
                # Fallback to existing file discovery logic for compatibility
                week_ending_date = self.file_discovery._find_week_ending_for_date(entry_date)
            
            # Check if entry exists in database
            stmt = select(JournalEntryIndex).where(JournalEntryIndex.date == entry_date)
            result = await session.execute(stmt)
            existing_entry = result.scalar_one_or_none()
            
            if existing_entry:
                # Update existing entry with new week ending date calculation
                update_stmt = (
                    update(JournalEntryIndex)
                    .where(JournalEntryIndex.date == entry_date)
                    .values(
                        file_path=str(file_path),
                        week_ending_date=week_ending_date,
                        word_count=metadata["word_count"],
                        character_count=metadata["character_count"],
                        line_count=metadata["line_count"],
                        has_content=metadata["has_content"],
                        file_size_bytes=file_stats.st_size if file_stats else 0,
                        file_modified_at=datetime.fromtimestamp(file_stats.st_mtime) if file_stats else None,
                        modified_at=now_utc(),
                        synced_at=now_utc()
                    )
                )
                await session.execute(update_stmt)
            else:
                # Create new entry with calculated week ending date
                new_entry = JournalEntryIndex(
                    date=entry_date,
                    file_path=str(file_path),
                    week_ending_date=week_ending_date,
                    word_count=metadata["word_count"],
                    character_count=metadata["character_count"],
                    line_count=metadata["line_count"],
                    has_content=metadata["has_content"],
                    file_size_bytes=file_stats.st_size if file_stats else 0,
                    file_modified_at=datetime.fromtimestamp(file_stats.st_mtime) if file_stats else None,
                    created_at=now_utc(),
                    modified_at=now_utc(),
                    synced_at=now_utc()
                )
                session.add(new_entry)
                
        except Exception as e:
            self.logger.logger.error(f"Failed to sync entry {entry_date} to database: {str(e)}")
            raise
    
    def _calculate_entry_metadata(self, content: str) -> Dict[str, Any]:
        """Calculate metadata for entry content."""
        lines = content.split('\n')
        words = content.split()
        
        return {
            "word_count": len(words),
            "character_count": len(content),
            "line_count": len(lines),
            "has_content": len(content.strip()) > 0
        }
    
    async def _db_entry_to_response(self, db_entry: JournalEntryIndex, 
                                  include_content: bool = False) -> Optional[JournalEntryResponse]:
        """Convert database entry to response model."""
        try:
            metadata = JournalEntryMetadata(
                word_count=db_entry.word_count,
                character_count=getattr(db_entry, 'character_count', 0),
                line_count=getattr(db_entry, 'line_count', 0),
                file_size_bytes=getattr(db_entry, 'file_size_bytes', 0),
                has_content=db_entry.has_content,
                status=EntryStatus.COMPLETE if db_entry.has_content else EntryStatus.EMPTY
            )
            
            # Get content if requested
            content = None
            if include_content:
                content = await self.get_entry_content(db_entry.date)
            
            # Convert timestamps to local timezone before creating response
            created_at_local = to_local(db_entry.created_at) if db_entry.created_at else None
            modified_at_local = to_local(db_entry.modified_at) if db_entry.modified_at else None
            last_accessed_at_local = to_local(getattr(db_entry, 'last_accessed_at', None)) if getattr(db_entry, 'last_accessed_at', None) else None
            file_modified_at_local = to_local(getattr(db_entry, 'file_modified_at', None)) if getattr(db_entry, 'file_modified_at', None) else None
            
            return JournalEntryResponse(
                date=db_entry.date,
                content=content,
                file_path=db_entry.file_path,
                week_ending_date=db_entry.week_ending_date,
                metadata=metadata,
                created_at=created_at_local,
                modified_at=modified_at_local,
                last_accessed_at=last_accessed_at_local,
                file_modified_at=file_modified_at_local
            )
        except Exception as e:
            self.logger.logger.error(f"Failed to convert db entry to response: {str(e)}")
            return None
    
    async def _update_entry_access(self, entry_date: date, file_path: Path) -> None:
        """Update entry access statistics in database."""
        try:
            async with self.db_manager.get_session() as session:
                update_stmt = (
                    update(JournalEntryIndex)
                    .where(JournalEntryIndex.date == entry_date)
                    .values(
                        last_accessed_at=now_utc(),
                        access_count=JournalEntryIndex.access_count + 1
                    )
                )
                await session.execute(update_stmt)
                await session.commit()
        except Exception as e:
            self.logger.logger.info(f"Failed to update entry access for {entry_date}: {str(e)}")
    
    async def _calculate_week_ending_date(self, entry_date: date) -> date:
        """
        Calculate week ending date using work week service when available.
        
        This method provides a centralized way to calculate week ending dates,
        with fallback to legacy logic for backward compatibility.
        
        Args:
            entry_date: Date of the entry
            
        Returns:
            date: Week ending date for the entry
        """
        try:
            if self.work_week_service:
                # Use work week service for proper weekly organization
                week_ending_date = await self.work_week_service.calculate_week_ending_date(entry_date)
                self.logger.logger.debug(f"Work week calculation: {entry_date} -> week ending {week_ending_date}")
                return week_ending_date
            else:
                # Fallback to existing directory structure scanning
                week_ending_date = self.file_discovery._find_week_ending_for_date(entry_date)
                self.logger.logger.debug(f"Legacy file discovery: {entry_date} -> week ending {week_ending_date}")
                return week_ending_date
                
        except Exception as e:
            # Ultimate fallback to existing logic
            self.logger.logger.warning(f"Week ending calculation failed for {entry_date}: {str(e)}, using fallback")
            return self.file_discovery._find_week_ending_for_date(entry_date)
    
    async def _try_find_entry_in_legacy_structure(self, entry_date: date) -> Optional[Path]:
        """
        Attempt to find entry in legacy directory structure for backward compatibility.
        
        This method tries to locate entries that were created before the work week
        integration, when entries were organized in daily directories.
        
        Args:
            entry_date: Date of the entry to find
            
        Returns:
            Path to the entry file if found in legacy structure, None otherwise
        """
        try:
            # Use FileDiscovery to scan existing directory structure
            legacy_week_ending = self.file_discovery._find_week_ending_for_date(entry_date)
            legacy_file_path = self.file_discovery._construct_file_path(entry_date, legacy_week_ending)
            
            if legacy_file_path.exists():
                self.logger.logger.debug(f"Found legacy entry: {entry_date} -> {legacy_file_path}")
                return legacy_file_path
            
            return None
            
        except Exception as e:
            self.logger.logger.warning(f"Failed to search legacy structure for {entry_date}: {str(e)}")
            return None