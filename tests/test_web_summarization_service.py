"""
Tests for WebSummarizationService

This module contains comprehensive tests for the WebSummarizationService,
including task management, progress tracking, and integration with existing
summarization components.
"""

import pytest
import asyncio
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import os

from config_manager import AppConfig, ProcessingConfig, LogConfig
from logger import JournalSummarizerLogger
from web.database import DatabaseManager
from web.services.web_summarizer import (
    WebSummarizationService, 
    SummaryType, 
    SummaryTaskStatus,
    SummaryTask,
    ProgressUpdate
)


@pytest.fixture
def mock_config():
    """Create mock configuration."""
    config = Mock(spec=AppConfig)
    config.processing = Mock(spec=ProcessingConfig)
    config.processing.base_path = Path("/tmp/test_journals")
    config.logging = Mock(spec=LogConfig)
    return config


@pytest.fixture
def mock_logger():
    """Create mock logger."""
    logger = Mock(spec=JournalSummarizerLogger)
    logger.logger = Mock()
    logger.logger.info = Mock()
    logger.logger.error = Mock()
    logger.logger.debug = Mock()
    logger.log_error_with_category = Mock()
    return logger


@pytest.fixture
def mock_db_manager():
    """Create mock database manager."""
    db_manager = Mock(spec=DatabaseManager)
    return db_manager


@pytest.fixture
def summarization_service(mock_config, mock_logger, mock_db_manager):
    """Create WebSummarizationService instance for testing."""
    with patch('web.services.web_summarizer.UnifiedLLMClient'):
        service = WebSummarizationService(mock_config, mock_logger, mock_db_manager)
        return service


class TestWebSummarizationService:
    """Test cases for WebSummarizationService."""
    
    @pytest.mark.asyncio
    async def test_create_summary_task_success(self, summarization_service):
        """Test successful task creation."""
        start_date = date(2024, 1, 1)
        end_date = date(2024, 1, 7)
        
        task_id = await summarization_service.create_summary_task(
            SummaryType.WEEKLY, start_date, end_date
        )
        
        assert task_id is not None
        assert len(task_id) > 0
        
        # Verify task was created
        task = await summarization_service.get_task_status(task_id)
        assert task is not None
        assert task.summary_type == SummaryType.WEEKLY
        assert task.start_date == start_date
        assert task.end_date == end_date
        assert task.status == SummaryTaskStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_create_summary_task_invalid_date_range(self, summarization_service):
        """Test task creation with invalid date range."""
        start_date = date(2024, 1, 7)
        end_date = date(2024, 1, 1)  # End before start
        
        with pytest.raises(ValueError, match="Start date must be before or equal to end date"):
            await summarization_service.create_summary_task(
                SummaryType.WEEKLY, start_date, end_date
            )
    
    @pytest.mark.asyncio
    async def test_create_summary_task_future_date(self, summarization_service):
        """Test task creation with future start date."""
        start_date = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=7)
        
        with pytest.raises(ValueError, match="Start date cannot be in the future"):
            await summarization_service.create_summary_task(
                SummaryType.WEEKLY, start_date, end_date
            )
    
    @pytest.mark.asyncio
    async def test_start_summarization_success(self, summarization_service):
        """Test successful task start."""
        # Create task
        task_id = await summarization_service.create_summary_task(
            SummaryType.WEEKLY, date(2024, 1, 1), date(2024, 1, 7)
        )
        
        # Mock the execution method to avoid actual processing
        with patch.object(summarization_service, '_execute_summarization', new_callable=AsyncMock):
            success = await summarization_service.start_summarization(task_id)
            assert success is True
            
            # Verify task status changed
            task = await summarization_service.get_task_status(task_id)
            assert task.status == SummaryTaskStatus.RUNNING
            assert task.started_at is not None
    
    @pytest.mark.asyncio
    async def test_start_summarization_task_not_found(self, summarization_service):
        """Test starting non-existent task."""
        success = await summarization_service.start_summarization("non-existent-id")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_start_summarization_task_not_pending(self, summarization_service):
        """Test starting task that's not in pending state."""
        # Create and start task
        task_id = await summarization_service.create_summary_task(
            SummaryType.WEEKLY, date(2024, 1, 1), date(2024, 1, 7)
        )
        
        # Manually set task to running state
        async with summarization_service._task_lock:
            summarization_service.active_tasks[task_id].status = SummaryTaskStatus.RUNNING
        
        success = await summarization_service.start_summarization(task_id)
        assert success is False
    
    @pytest.mark.asyncio
    async def test_cancel_task_success(self, summarization_service):
        """Test successful task cancellation."""
        # Create and start task
        task_id = await summarization_service.create_summary_task(
            SummaryType.WEEKLY, date(2024, 1, 1), date(2024, 1, 7)
        )
        
        # Set task to running state
        async with summarization_service._task_lock:
            summarization_service.active_tasks[task_id].status = SummaryTaskStatus.RUNNING
        
        success = await summarization_service.cancel_task(task_id)
        assert success is True
        
        # Verify task was cancelled
        task = await summarization_service.get_task_status(task_id)
        assert task.status == SummaryTaskStatus.CANCELLED
        assert task.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_cancel_task_not_running(self, summarization_service):
        """Test cancelling task that's not running."""
        task_id = await summarization_service.create_summary_task(
            SummaryType.WEEKLY, date(2024, 1, 1), date(2024, 1, 7)
        )
        
        success = await summarization_service.cancel_task(task_id)
        assert success is False
    
    @pytest.mark.asyncio
    async def test_get_task_progress(self, summarization_service):
        """Test getting task progress."""
        task_id = await summarization_service.create_summary_task(
            SummaryType.WEEKLY, date(2024, 1, 1), date(2024, 1, 7)
        )
        
        # Update progress
        await summarization_service._update_progress(task_id, 50.0, "Processing content")
        
        progress = await summarization_service.get_task_progress(task_id)
        assert progress is not None
        assert progress.task_id == task_id
        assert progress.progress == 50.0
        assert progress.current_step == "Processing content"
    
    @pytest.mark.asyncio
    async def test_get_all_tasks(self, summarization_service):
        """Test getting all tasks."""
        # Create multiple tasks
        task_id1 = await summarization_service.create_summary_task(
            SummaryType.WEEKLY, date(2024, 1, 1), date(2024, 1, 7)
        )
        task_id2 = await summarization_service.create_summary_task(
            SummaryType.MONTHLY, date(2024, 1, 1), date(2024, 1, 31)
        )
        
        tasks = await summarization_service.get_all_tasks()
        assert len(tasks) == 2
        
        task_ids = [task.task_id for task in tasks]
        assert task_id1 in task_ids
        assert task_id2 in task_ids
    
    @pytest.mark.asyncio
    async def test_cleanup_completed_tasks(self, summarization_service):
        """Test cleanup of completed tasks."""
        # Create task and mark as completed
        task_id = await summarization_service.create_summary_task(
            SummaryType.WEEKLY, date(2024, 1, 1), date(2024, 1, 7)
        )
        
        # Set task as completed with old timestamp
        old_time = datetime.utcnow() - timedelta(hours=25)
        async with summarization_service._task_lock:
            task = summarization_service.active_tasks[task_id]
            task.status = SummaryTaskStatus.COMPLETED
            task.completed_at = old_time
        
        # Run cleanup
        cleaned_count = await summarization_service.cleanup_completed_tasks(24)
        assert cleaned_count == 1
        
        # Verify task was removed
        remaining_task = await summarization_service.get_task_status(task_id)
        assert remaining_task is None
    
    @pytest.mark.asyncio
    async def test_execute_summarization_success(self, summarization_service):
        """Test successful summarization via the 4-phase pipeline."""
        task_id = await summarization_service.create_summary_task(
            SummaryType.WEEKLY, date(2024, 1, 1), date(2024, 1, 7)
        )

        mock_discovery = Mock()
        mock_discovery.found_files = [Path("/tmp/test1.md"), Path("/tmp/test2.md")]

        mock_processed = [Mock(content="day 1"), Mock(content="day 2")]
        mock_proc_stats = Mock()

        mock_analysis = [Mock(), Mock()]
        mock_api_stats = Mock()
        mock_llm_client = Mock()

        mock_period = Mock()
        mock_period.summary_text = "Weekly summary of work."
        mock_sum_stats = Mock()

        with patch('web.services.web_summarizer.summarization_pipeline') as mock_pipeline:
            mock_pipeline.discover_files.return_value = mock_discovery
            mock_pipeline.process_content.return_value = (mock_processed, mock_proc_stats)
            mock_pipeline.analyze_content.return_value = (mock_analysis, mock_api_stats, mock_llm_client)
            mock_pipeline.generate_summaries.return_value = ([mock_period], mock_sum_stats)

            await summarization_service._execute_summarization(task_id)

        task = await summarization_service.get_task_status(task_id)
        assert task.status == SummaryTaskStatus.COMPLETED
        assert task.result == "Weekly summary of work."
        assert task.progress == 100.0

    @pytest.mark.asyncio
    async def test_execute_summarization_no_files_found(self, summarization_service):
        """Test summarization when no journal files are found."""
        task_id = await summarization_service.create_summary_task(
            SummaryType.WEEKLY, date(2024, 1, 1), date(2024, 1, 7)
        )

        mock_discovery = Mock()
        mock_discovery.found_files = []

        with patch('web.services.web_summarizer.summarization_pipeline') as mock_pipeline:
            mock_pipeline.discover_files.return_value = mock_discovery

            await summarization_service._execute_summarization(task_id)

        task = await summarization_service.get_task_status(task_id)
        assert task.status == SummaryTaskStatus.FAILED
        assert "No journal files found" in task.error_message

    @pytest.mark.asyncio
    async def test_execute_summarization_with_cancellation(self, summarization_service):
        """Test summarization respects task cancellation."""
        task_id = await summarization_service.create_summary_task(
            SummaryType.WEEKLY, date(2024, 1, 1), date(2024, 1, 7)
        )

        async with summarization_service._task_lock:
            summarization_service.active_tasks[task_id].status = SummaryTaskStatus.CANCELLED

        mock_discovery = Mock()
        mock_discovery.found_files = [Path("/tmp/test1.md")]

        with patch('web.services.web_summarizer.summarization_pipeline') as mock_pipeline:
            mock_pipeline.discover_files.return_value = mock_discovery

            await summarization_service._execute_summarization(task_id)

        task = await summarization_service.get_task_status(task_id)
        assert task.status == SummaryTaskStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_execute_summarization_calls_all_four_phases(self, summarization_service):
        """Test that _execute_summarization calls all 4 pipeline phases in order."""
        task_id = await summarization_service.create_summary_task(
            SummaryType.WEEKLY, date(2024, 1, 1), date(2024, 1, 7)
        )

        mock_discovery = Mock()
        mock_discovery.found_files = [Path("/tmp/test1.md")]

        mock_processed = [Mock(content="content")]
        mock_proc_stats = Mock()

        mock_analysis = [Mock()]
        mock_api_stats = Mock()
        mock_llm_client = Mock()

        mock_period = Mock()
        mock_period.summary_text = "Summary."
        mock_sum_stats = Mock()

        with patch('web.services.web_summarizer.summarization_pipeline') as mock_pipeline:
            mock_pipeline.discover_files.return_value = mock_discovery
            mock_pipeline.process_content.return_value = (mock_processed, mock_proc_stats)
            mock_pipeline.analyze_content.return_value = (mock_analysis, mock_api_stats, mock_llm_client)
            mock_pipeline.generate_summaries.return_value = ([mock_period], mock_sum_stats)

            await summarization_service._execute_summarization(task_id)

        # Verify all 4 pipeline phases were called
        mock_pipeline.discover_files.assert_called_once()
        mock_pipeline.process_content.assert_called_once()
        mock_pipeline.analyze_content.assert_called_once()
        mock_pipeline.generate_summaries.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_progress(self, summarization_service):
        """Test progress update functionality."""
        task_id = await summarization_service.create_summary_task(
            SummaryType.WEEKLY, date(2024, 1, 1), date(2024, 1, 7)
        )

        await summarization_service._update_progress(task_id, 75.0, "Generating summary")

        # Check task progress
        task = await summarization_service.get_task_status(task_id)
        assert task.progress == 75.0
        assert task.current_step == "Generating summary"

        # Check progress update
        progress = await summarization_service.get_task_progress(task_id)
        assert progress.progress == 75.0
        assert progress.current_step == "Generating summary"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])