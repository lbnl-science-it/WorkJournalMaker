# ABOUTME: Async wrapper around the CLI summarization pipeline for the web interface.
# ABOUTME: Adds progress tracking, task management, and WebSocket-based status updates.
"""
Web Summarization Service

This module provides web-friendly wrapper for the existing summarization pipeline,
adding async interfaces, progress tracking, and task management while maintaining
full compatibility with existing CLI components.
"""

import asyncio
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional, List, AsyncGenerator
import uuid
from dataclasses import dataclass, field
from enum import Enum

from config_manager import AppConfig
from logger import JournalSummarizerLogger, ErrorCategory
from unified_llm_client import UnifiedLLMClient
import summarization_pipeline
from web.services.base_service import BaseService
from web.database import DatabaseManager


class SummaryTaskStatus(str, Enum):
    """Status of summarization tasks."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SummaryType(str, Enum):
    """Types of summaries that can be generated."""
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


@dataclass
class SummaryTask:
    """Represents a summarization task."""
    task_id: str
    summary_type: SummaryType
    start_date: date
    end_date: date
    status: SummaryTaskStatus = SummaryTaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    current_step: str = ""
    result: Optional[str] = None
    error_message: Optional[str] = None
    output_file_path: Optional[str] = None


@dataclass
class ProgressUpdate:
    """Progress update for summarization tasks."""
    task_id: str
    progress: float
    current_step: str
    status: SummaryTaskStatus
    message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class WebSummarizationService(BaseService):
    """
    Web-friendly wrapper for the existing summarization pipeline.
    
    Provides async interfaces, progress tracking, and task management
    while maintaining full compatibility with existing CLI components.
    """
    
    def __init__(self, config: AppConfig, logger: JournalSummarizerLogger,
                 db_manager: DatabaseManager):
        """Initialize WebSummarizationService with core dependencies."""
        super().__init__(config, logger, db_manager)

        # Keep llm_client for WebSocket endpoint configuration checks
        self.llm_client = UnifiedLLMClient(config)

        # Task management
        self.active_tasks: Dict[str, SummaryTask] = {}
        self.task_progress: Dict[str, ProgressUpdate] = {}
        self._task_lock = asyncio.Lock()

        # WebSocket connection manager (will be set by the API)
        self.connection_manager = None
    
    def set_connection_manager(self, connection_manager):
        """Set the WebSocket connection manager for real-time updates."""
        self.connection_manager = connection_manager
    
    async def create_summary_task(self, summary_type: SummaryType,
                                start_date: date, end_date: date) -> str:
        """
        Create a new summarization task.
        
        Args:
            summary_type: Type of summary to generate
            start_date: Start date for summarization
            end_date: End date for summarization
            
        Returns:
            Task ID for tracking progress
        """
        try:
            # Validate date range
            if start_date > end_date:
                raise ValueError("Start date must be before or equal to end date")
            
            if start_date > date.today():
                raise ValueError("Start date cannot be in the future")
            
            # Generate unique task ID
            task_id = str(uuid.uuid4())
            
            # Create task
            task = SummaryTask(
                task_id=task_id,
                summary_type=summary_type,
                start_date=start_date,
                end_date=end_date
            )
            
            async with self._task_lock:
                self.active_tasks[task_id] = task
            
            self.logger.logger.info(f"Created summarization task {task_id} for {start_date} to {end_date}")
            
            return task_id
            
        except Exception as e:
            self.logger.log_error_with_category(ErrorCategory.PROCESSING_ERROR, f"Failed to create summary task: {str(e)}")
            raise
    
    async def start_summarization(self, task_id: str, user_id: str = "local") -> bool:
        """
        Start executing a summarization task.
        
        Args:
            task_id: ID of the task to start
            
        Returns:
            True if task started successfully, False otherwise
        """
        try:
            async with self._task_lock:
                if task_id not in self.active_tasks:
                    raise ValueError(f"Task {task_id} not found")
                
                task = self.active_tasks[task_id]
                if task.status != SummaryTaskStatus.PENDING:
                    raise ValueError(f"Task {task_id} is not in pending state")
                
                task.status = SummaryTaskStatus.RUNNING
                task.started_at = datetime.utcnow()
            
            # Start the summarization process in background
            asyncio.create_task(self._execute_summarization(task_id))
            
            self.logger.logger.info(f"Started summarization task {task_id}")
            return True
            
        except Exception as e:
            self.logger.logger.error(f"Failed to start summarization task {task_id}: {str(e)}")
            await self._update_task_status(task_id, SummaryTaskStatus.FAILED, error_message=str(e))
            return False
    
    async def get_task_status(self, task_id: str) -> Optional[SummaryTask]:
        """Get the current status of a summarization task."""
        async with self._task_lock:
            return self.active_tasks.get(task_id)
    
    async def get_task_progress(self, task_id: str) -> Optional[ProgressUpdate]:
        """Get the latest progress update for a task."""
        return self.task_progress.get(task_id)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running summarization task."""
        try:
            async with self._task_lock:
                if task_id not in self.active_tasks:
                    return False
                
                task = self.active_tasks[task_id]
                if task.status == SummaryTaskStatus.RUNNING:
                    task.status = SummaryTaskStatus.CANCELLED
                    task.completed_at = datetime.utcnow()
                    
                    self.logger.logger.info(f"Cancelled summarization task {task_id}")
                    return True
                
                return False
                
        except Exception as e:
            self.logger.logger.error(f"Failed to cancel task {task_id}: {str(e)}")
            return False
    
    async def get_all_tasks(self) -> List[SummaryTask]:
        """Get all active tasks."""
        async with self._task_lock:
            return list(self.active_tasks.values())
    
    async def cleanup_completed_tasks(self, older_than_hours: int = 24) -> int:
        """Clean up completed tasks older than specified hours."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
            cleaned_count = 0
            
            async with self._task_lock:
                tasks_to_remove = []
                for task_id, task in self.active_tasks.items():
                    if (task.status in [SummaryTaskStatus.COMPLETED, SummaryTaskStatus.FAILED, SummaryTaskStatus.CANCELLED] 
                        and task.completed_at and task.completed_at < cutoff_time):
                        tasks_to_remove.append(task_id)
                
                for task_id in tasks_to_remove:
                    del self.active_tasks[task_id]
                    if task_id in self.task_progress:
                        del self.task_progress[task_id]
                    cleaned_count += 1
            
            if cleaned_count > 0:
                self.logger.logger.info(f"Cleaned up {cleaned_count} completed tasks")
            
            return cleaned_count
            
        except Exception as e:
            self.logger.logger.error(f"Failed to cleanup tasks: {str(e)}")
            return 0
    
    async def _execute_summarization(self, task_id: str) -> None:
        """Execute the 4-phase summarization pipeline for a task."""
        try:
            task = self.active_tasks[task_id]
            if task.status == SummaryTaskStatus.CANCELLED:
                return

            await self._update_progress(task_id, 0.0, "Initializing summarization")
            loop = asyncio.get_running_loop()

            # Phase 1: File Discovery
            await self._update_progress(task_id, 10.0, "Discovering journal files")
            discovery_result = await loop.run_in_executor(
                None, summarization_pipeline.discover_files,
                self.config.processing.base_path, task.start_date, task.end_date
            )
            if not discovery_result.found_files:
                raise ValueError("No journal files found in the specified date range")
            if task.status == SummaryTaskStatus.CANCELLED:
                return

            # Phase 2: Content Processing
            await self._update_progress(task_id, 30.0, "Processing journal content")
            processed_content, processing_stats = await loop.run_in_executor(
                None, summarization_pipeline.process_content,
                discovery_result.found_files, self.config.processing.max_file_size_mb
            )
            if task.status == SummaryTaskStatus.CANCELLED:
                return

            # Phase 3: LLM Analysis
            await self._update_progress(task_id, 50.0, "Analyzing content with LLM")
            analysis_results, api_stats, llm_client = await loop.run_in_executor(
                None, summarization_pipeline.analyze_content,
                processed_content, self.config
            )
            if task.status == SummaryTaskStatus.CANCELLED:
                return

            # Phase 4: Summary Generation
            await self._update_progress(task_id, 80.0, "Generating summary")
            summaries, summary_stats = await loop.run_in_executor(
                None, summarization_pipeline.generate_summaries,
                analysis_results, llm_client, task.summary_type.value,
                task.start_date, task.end_date
            )

            # Combine summary texts for storage
            combined_result = "\n\n".join(s.summary_text for s in summaries)

            await self._update_progress(task_id, 100.0, "Summarization completed")
            await self._complete_task(task_id, combined_result, None)

        except Exception as e:
            self.logger.logger.error(f"Summarization task {task_id} failed: {str(e)}")
            await self._update_task_status(task_id, SummaryTaskStatus.FAILED, error_message=str(e))
    
    async def _update_progress(self, task_id: str, progress: float, current_step: str) -> None:
        """Update task progress."""
        try:
            async with self._task_lock:
                if task_id in self.active_tasks:
                    task = self.active_tasks[task_id]
                    task.progress = progress
                    task.current_step = current_step
                    
                    # Create progress update
                    progress_update = ProgressUpdate(
                        task_id=task_id,
                        progress=progress,
                        current_step=current_step,
                        status=task.status
                    )
                    
                    self.task_progress[task_id] = progress_update
                    
                    # Send WebSocket update if connection manager is available
                    if self.connection_manager:
                        progress_data = {
                            "progress": progress,
                            "current_step": current_step,
                            "status": task.status.value,
                            "timestamp": progress_update.timestamp.isoformat()
                        }
                        await self.connection_manager.send_progress_update(task_id, progress_data)
                    
        except Exception as e:
            self.logger.logger.error(f"Failed to update progress for task {task_id}: {str(e)}")
    
    async def _update_task_status(self, task_id: str, status: SummaryTaskStatus,
                                error_message: Optional[str] = None) -> None:
        """Update task status."""
        try:
            async with self._task_lock:
                if task_id in self.active_tasks:
                    task = self.active_tasks[task_id]
                    task.status = status
                    task.error_message = error_message
                    
                    if status in [SummaryTaskStatus.COMPLETED, SummaryTaskStatus.FAILED, SummaryTaskStatus.CANCELLED]:
                        task.completed_at = datetime.utcnow()
                    
                    # Send WebSocket update if connection manager is available
                    if self.connection_manager:
                        status_data = {
                            "status": status.value,
                            "progress": task.progress,
                            "current_step": task.current_step,
                            "error_message": error_message,
                            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        await self.connection_manager.send_task_status(task_id, status_data)
                        
        except Exception as e:
            self.logger.logger.error(f"Failed to update status for task {task_id}: {str(e)}")
    
    async def _complete_task(self, task_id: str, result: str, output_path: str) -> None:
        """Complete a summarization task."""
        try:
            async with self._task_lock:
                if task_id in self.active_tasks:
                    task = self.active_tasks[task_id]
                    task.status = SummaryTaskStatus.COMPLETED
                    task.result = result
                    task.output_file_path = output_path
                    task.completed_at = datetime.utcnow()
                    
            self.logger.logger.info(f"Completed summarization task {task_id}")
            
        except Exception as e:
            self.logger.logger.error(f"Failed to complete task {task_id}: {str(e)}")