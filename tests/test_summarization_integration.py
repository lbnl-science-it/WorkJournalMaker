"""
Integration Tests for Web Summarization Service

This module contains integration tests that verify the complete summarization
pipeline works correctly with real components and configurations.
"""

import pytest
import asyncio
from datetime import date, datetime, timedelta
from pathlib import Path
import tempfile
import os
import yaml
from unittest.mock import Mock, patch

from config_manager import AppConfig, ProcessingConfig, LogConfig, LLMConfig
from logger import JournalSummarizerLogger
from web.database import DatabaseManager
from web.services.web_summarizer import WebSummarizationService, SummaryType, SummaryTaskStatus


@pytest.fixture
def temp_journal_dir():
    """Create temporary directory with sample journal files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create sample journal files
        journal_file1 = temp_path / "2024-01-01.md"
        journal_file1.write_text("""
# Monday, January 1, 2024

## Work Tasks
- Completed project setup
- Reviewed requirements document
- Started initial development

## Notes
- Team meeting scheduled for tomorrow
- Need to follow up on client feedback
""")
        
        journal_file2 = temp_path / "2024-01-02.md"
        journal_file2.write_text("""
# Tuesday, January 2, 2024

## Work Tasks
- Attended team meeting
- Implemented core functionality
- Fixed several bugs

## Notes
- Client feedback was positive
- Planning next sprint
""")
        
        yield temp_path


@pytest.fixture
def test_config(temp_journal_dir):
    """Create test configuration."""
    config = AppConfig()
    config.processing = ProcessingConfig()
    config.processing.base_path = temp_journal_dir
    config.processing.file_patterns = ["*.md"]
    
    from logger import LogLevel
    
    config.logging = LogConfig()
    config.logging.level = LogLevel.DEBUG
    config.logging.console_output = True
    config.logging.file_output = False
    
    config.llm = LLMConfig()
    config.llm.provider = "mock"  # Use mock provider for testing
    
    return config


@pytest.fixture
def test_logger(test_config):
    """Create test logger."""
    return JournalSummarizerLogger(test_config.logging)


@pytest.fixture
async def test_db_manager():
    """Create test database manager."""
    db_manager = DatabaseManager(":memory:")  # In-memory database for testing
    await db_manager.initialize()
    yield db_manager
    if db_manager.engine:
        await db_manager.engine.dispose()


@pytest.fixture
def summarization_service(test_config, test_logger, test_db_manager):
    """Create WebSummarizationService with real components."""
    # Mock the LLM client to avoid actual API calls
    with patch('web.services.web_summarizer.UnifiedLLMClient') as mock_llm_class:
        mock_llm = Mock()
        mock_llm_class.return_value = mock_llm
        
        # Mock the summary generator to return predictable results
        with patch('web.services.web_summarizer.SummaryGenerator') as mock_generator_class:
            mock_generator = Mock()
            mock_generator.generate_weekly_summary.return_value = "Weekly summary: Completed project setup and development tasks."
            mock_generator.generate_monthly_summary.return_value = "Monthly summary: Made significant progress on project."
            mock_generator.generate_custom_summary.return_value = "Custom summary: Various tasks completed."
            mock_generator_class.return_value = mock_generator
            
            # Mock the output manager to avoid file system operations
            with patch('web.services.web_summarizer.OutputManager') as mock_output_class:
                mock_output = Mock()
                mock_output.save_summary.return_value = "/tmp/test_summary.txt"
                mock_output_class.return_value = mock_output
                
                service = WebSummarizationService(test_config, test_logger, test_db_manager)
                return service


class TestSummarizationIntegration:
    """Integration test cases for summarization service."""
    
    @pytest.mark.asyncio
    async def test_complete_summarization_workflow(self, summarization_service):
        """Test complete summarization workflow from task creation to completion."""
        # Create task
        task_id = await summarization_service.create_summary_task(
            SummaryType.WEEKLY,
            date(2024, 1, 1),
            date(2024, 1, 7)
        )
        
        assert task_id is not None
        
        # Verify task was created
        task = await summarization_service.get_task_status(task_id)
        assert task is not None
        assert task.status == SummaryTaskStatus.PENDING
        assert task.summary_type == SummaryType.WEEKLY
        
        # Start summarization
        success = await summarization_service.start_summarization(task_id)
        assert success is True
        
        # Wait for task to complete (with timeout)
        max_wait = 30  # seconds
        wait_time = 0
        while wait_time < max_wait:
            task = await summarization_service.get_task_status(task_id)
            if task.status in [SummaryTaskStatus.COMPLETED, SummaryTaskStatus.FAILED]:
                break
            await asyncio.sleep(0.5)
            wait_time += 0.5
        
        # Verify task completed successfully
        final_task = await summarization_service.get_task_status(task_id)
        assert final_task.status == SummaryTaskStatus.COMPLETED
        assert final_task.result is not None
        assert "Weekly summary:" in final_task.result
        assert final_task.output_file_path is not None
        assert final_task.progress == 100.0
    
    @pytest.mark.asyncio
    async def test_monthly_summary_workflow(self, summarization_service):
        """Test monthly summary workflow."""
        task_id = await summarization_service.create_summary_task(
            SummaryType.MONTHLY,
            date(2024, 1, 1),
            date(2024, 1, 31)
        )
        
        success = await summarization_service.start_summarization(task_id)
        assert success is True
        
        # Wait for completion
        max_wait = 30
        wait_time = 0
        while wait_time < max_wait:
            task = await summarization_service.get_task_status(task_id)
            if task.status in [SummaryTaskStatus.COMPLETED, SummaryTaskStatus.FAILED]:
                break
            await asyncio.sleep(0.5)
            wait_time += 0.5
        
        final_task = await summarization_service.get_task_status(task_id)
        assert final_task.status == SummaryTaskStatus.COMPLETED
        assert "Monthly summary:" in final_task.result
    
    @pytest.mark.asyncio
    async def test_custom_summary_workflow(self, summarization_service):
        """Test custom summary workflow."""
        task_id = await summarization_service.create_summary_task(
            SummaryType.CUSTOM,
            date(2024, 1, 1),
            date(2024, 1, 15)
        )
        
        success = await summarization_service.start_summarization(task_id)
        assert success is True
        
        # Wait for completion
        max_wait = 30
        wait_time = 0
        while wait_time < max_wait:
            task = await summarization_service.get_task_status(task_id)
            if task.status in [SummaryTaskStatus.COMPLETED, SummaryTaskStatus.FAILED]:
                break
            await asyncio.sleep(0.5)
            wait_time += 0.5
        
        final_task = await summarization_service.get_task_status(task_id)
        assert final_task.status == SummaryTaskStatus.COMPLETED
        assert "Custom summary:" in final_task.result
    
    @pytest.mark.asyncio
    async def test_progress_tracking_during_execution(self, summarization_service):
        """Test that progress is tracked correctly during execution."""
        task_id = await summarization_service.create_summary_task(
            SummaryType.WEEKLY,
            date(2024, 1, 1),
            date(2024, 1, 7)
        )
        
        # Start task
        success = await summarization_service.start_summarization(task_id)
        assert success is True
        
        # Monitor progress
        progress_updates = []
        max_wait = 30
        wait_time = 0
        
        while wait_time < max_wait:
            progress = await summarization_service.get_task_progress(task_id)
            if progress:
                progress_updates.append((progress.progress, progress.current_step))
            
            task = await summarization_service.get_task_status(task_id)
            if task.status in [SummaryTaskStatus.COMPLETED, SummaryTaskStatus.FAILED]:
                break
                
            await asyncio.sleep(0.5)
            wait_time += 0.5
        
        # Verify we got progress updates
        assert len(progress_updates) > 0
        
        # Verify final progress is 100%
        final_progress = await summarization_service.get_task_progress(task_id)
        if final_progress:
            assert final_progress.progress == 100.0
    
    @pytest.mark.asyncio
    async def test_concurrent_tasks(self, summarization_service):
        """Test handling multiple concurrent summarization tasks."""
        # Create multiple tasks
        task_ids = []
        for i in range(3):
            start_date = date(2024, 1, 1 + i * 7)
            end_date = date(2024, 1, 7 + i * 7)
            task_id = await summarization_service.create_summary_task(
                SummaryType.WEEKLY,
                start_date,
                end_date
            )
            task_ids.append(task_id)
        
        # Start all tasks
        for task_id in task_ids:
            success = await summarization_service.start_summarization(task_id)
            assert success is True
        
        # Wait for all tasks to complete
        max_wait = 60  # Longer timeout for multiple tasks
        wait_time = 0
        
        while wait_time < max_wait:
            all_tasks = await summarization_service.get_all_tasks()
            completed_tasks = [t for t in all_tasks if t.status in [SummaryTaskStatus.COMPLETED, SummaryTaskStatus.FAILED]]
            
            if len(completed_tasks) >= 3:
                break
                
            await asyncio.sleep(1)
            wait_time += 1
        
        # Verify all tasks completed
        final_tasks = await summarization_service.get_all_tasks()
        completed_count = len([t for t in final_tasks if t.status == SummaryTaskStatus.COMPLETED])
        assert completed_count == 3
    
    @pytest.mark.asyncio
    async def test_task_cancellation_during_execution(self, summarization_service):
        """Test cancelling a task during execution."""
        task_id = await summarization_service.create_summary_task(
            SummaryType.WEEKLY,
            date(2024, 1, 1),
            date(2024, 1, 7)
        )
        
        # Start task
        success = await summarization_service.start_summarization(task_id)
        assert success is True
        
        # Wait a bit for task to start processing
        await asyncio.sleep(1)
        
        # Cancel task
        cancelled = await summarization_service.cancel_task(task_id)
        assert cancelled is True
        
        # Verify task was cancelled
        task = await summarization_service.get_task_status(task_id)
        assert task.status == SummaryTaskStatus.CANCELLED
        assert task.completed_at is not None
    
    @pytest.mark.asyncio
    async def test_task_cleanup(self, summarization_service):
        """Test cleanup of old completed tasks."""
        # Create and complete a task
        task_id = await summarization_service.create_summary_task(
            SummaryType.WEEKLY,
            date(2024, 1, 1),
            date(2024, 1, 7)
        )
        
        success = await summarization_service.start_summarization(task_id)
        assert success is True
        
        # Wait for completion
        max_wait = 30
        wait_time = 0
        while wait_time < max_wait:
            task = await summarization_service.get_task_status(task_id)
            if task.status in [SummaryTaskStatus.COMPLETED, SummaryTaskStatus.FAILED]:
                break
            await asyncio.sleep(0.5)
            wait_time += 0.5
        
        # Manually set completion time to be old
        async with summarization_service._task_lock:
            if task_id in summarization_service.active_tasks:
                summarization_service.active_tasks[task_id].completed_at = datetime.utcnow() - timedelta(hours=25)
        
        # Run cleanup
        cleaned_count = await summarization_service.cleanup_completed_tasks(24)
        assert cleaned_count == 1
        
        # Verify task was removed
        remaining_task = await summarization_service.get_task_status(task_id)
        assert remaining_task is None
    
    @pytest.mark.asyncio
    async def test_error_handling_no_files(self, summarization_service):
        """Test error handling when no journal files are found."""
        # Create task for date range with no files
        task_id = await summarization_service.create_summary_task(
            SummaryType.WEEKLY,
            date(2023, 12, 1),  # Date range with no files
            date(2023, 12, 7)
        )
        
        success = await summarization_service.start_summarization(task_id)
        assert success is True
        
        # Wait for task to fail
        max_wait = 30
        wait_time = 0
        while wait_time < max_wait:
            task = await summarization_service.get_task_status(task_id)
            if task.status in [SummaryTaskStatus.COMPLETED, SummaryTaskStatus.FAILED]:
                break
            await asyncio.sleep(0.5)
            wait_time += 0.5
        
        # Verify task failed with appropriate error
        final_task = await summarization_service.get_task_status(task_id)
        assert final_task.status == SummaryTaskStatus.FAILED
        assert "No journal files found" in final_task.error_message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])