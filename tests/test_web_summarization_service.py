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
    with patch('web.services.web_summarizer.UnifiedLLMClient'), \
         patch('web.services.web_summarizer.FileDiscovery'), \
         patch('web.services.web_summarizer.ContentProcessor'), \
         patch('web.services.web_summarizer.SummaryGenerator'), \
         patch('web.services.web_summarizer.OutputManager'):
        
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
        """Test successful summarization execution."""
        # Create task
        task_id = await summarization_service.create_summary_task(
            SummaryType.WEEKLY, date(2024, 1, 1), date(2024, 1, 7)
        )
        
        # Mock all the dependencies
        mock_discovery_result = Mock()
        mock_discovery_result.found_files = [Path("/tmp/test1.md"), Path("/tmp/test2.md")]
        
        with patch.object(summarization_service.file_discovery, 'discover_files', return_value=mock_discovery_result), \
             patch.object(summarization_service, '_process_content_async', new_callable=AsyncMock, return_value="processed content"), \
             patch.object(summarization_service, '_generate_summary_async', new_callable=AsyncMock, return_value="generated summary"), \
             patch.object(summarization_service, '_save_output_async', new_callable=AsyncMock, return_value="/tmp/output.txt"):
            
            await summarization_service._execute_summarization(task_id)
            
            # Verify task completion
            task = await summarization_service.get_task_status(task_id)
            assert task.status == SummaryTaskStatus.COMPLETED
            assert task.result == "generated summary"
            assert task.output_file_path == "/tmp/output.txt"
            assert task.progress == 100.0
    
    @pytest.mark.asyncio
    async def test_execute_summarization_no_files_found(self, summarization_service):
        """Test summarization execution when no files are found."""
        # Create task
        task_id = await summarization_service.create_summary_task(
            SummaryType.WEEKLY, date(2024, 1, 1), date(2024, 1, 7)
        )
        
        # Mock discovery to return no files
        mock_discovery_result = Mock()
        mock_discovery_result.found_files = []
        
        with patch.object(summarization_service.file_discovery, 'discover_files', return_value=mock_discovery_result):
            await summarization_service._execute_summarization(task_id)
            
            # Verify task failed
            task = await summarization_service.get_task_status(task_id)
            assert task.status == SummaryTaskStatus.FAILED
            assert "No journal files found" in task.error_message
    
    @pytest.mark.asyncio
    async def test_execute_summarization_with_cancellation(self, summarization_service):
        """Test summarization execution with task cancellation."""
        # Create task
        task_id = await summarization_service.create_summary_task(
            SummaryType.WEEKLY, date(2024, 1, 1), date(2024, 1, 7)
        )
        
        # Cancel task before execution
        async with summarization_service._task_lock:
            summarization_service.active_tasks[task_id].status = SummaryTaskStatus.CANCELLED
        
        # Mock discovery
        mock_discovery_result = Mock()
        mock_discovery_result.found_files = [Path("/tmp/test1.md")]
        
        with patch.object(summarization_service.file_discovery, 'discover_files', return_value=mock_discovery_result):
            await summarization_service._execute_summarization(task_id)
            
            # Verify task remains cancelled and execution stopped early
            task = await summarization_service.get_task_status(task_id)
            assert task.status == SummaryTaskStatus.CANCELLED
    
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
    
    @pytest.mark.asyncio
    async def test_async_content_processing(self, summarization_service):
        """Test async content processing wrapper."""
        test_files = [Path("/tmp/test1.md"), Path("/tmp/test2.md")]
        expected_content = "processed content"
        
        # Mock the return value as a tuple (processed_content_list, stats)
        mock_processed_content = [Mock(content="processed content")]
        mock_stats = Mock()
        
        with patch.object(summarization_service.content_processor, 'process_files', return_value=(mock_processed_content, mock_stats)):
            result = await summarization_service._process_content_async(test_files)
            assert result == expected_content
            summarization_service.content_processor.process_files.assert_called_once_with(test_files)
    
    @pytest.mark.asyncio
    async def test_async_summary_generation(self, summarization_service):
        """Test async summary generation wrapper."""
        content = "test content"
        expected_summary = "generated summary"
        
        # Test weekly summary
        with patch.object(summarization_service.summary_generator, 'generate_weekly_summary', return_value=expected_summary):
            result = await summarization_service._generate_summary_async(
                content, SummaryType.WEEKLY, date(2024, 1, 1), date(2024, 1, 7)
            )
            assert result == expected_summary
        
        # Test monthly summary
        with patch.object(summarization_service.summary_generator, 'generate_monthly_summary', return_value=expected_summary):
            result = await summarization_service._generate_summary_async(
                content, SummaryType.MONTHLY, date(2024, 1, 1), date(2024, 1, 31)
            )
            assert result == expected_summary
        
        # Test custom summary
        with patch.object(summarization_service.summary_generator, 'generate_custom_summary', return_value=expected_summary):
            result = await summarization_service._generate_summary_async(
                content, SummaryType.CUSTOM, date(2024, 1, 1), date(2024, 1, 15)
            )
            assert result == expected_summary
    
    @pytest.mark.asyncio
    async def test_async_output_saving(self, summarization_service):
        """Test async output saving wrapper."""
        summary = "test summary"
        
        # Create test task
        task_id = await summarization_service.create_summary_task(
            SummaryType.WEEKLY, date(2024, 1, 1), date(2024, 1, 7)
        )
        task = await summarization_service.get_task_status(task_id)
        
        # Test that the method returns a file path (the actual implementation creates a temp file)
        result = await summarization_service._save_output_async(summary, task)
        
        # Verify it returns a string path
        assert isinstance(result, str)
        assert result.endswith('.txt')
        
        # Clean up the temp file if it exists
        import os
        if os.path.exists(result):
            os.unlink(result)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])