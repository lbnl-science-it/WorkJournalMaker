"""
Tests for Summarization API Endpoints

This module contains comprehensive tests for the summarization API endpoints,
including task creation, progress tracking, and file download functionality.
"""

import pytest
import asyncio
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import os
from fastapi.testclient import TestClient
from fastapi import FastAPI

from web.api.summarization import router
from web.services.web_summarizer import (
    WebSummarizationService, 
    SummaryType, 
    SummaryTaskStatus,
    SummaryTask,
    ProgressUpdate
)
from web.models.journal import SummaryRequest


@pytest.fixture
def mock_summarization_service():
    """Create mock WebSummarizationService."""
    service = Mock(spec=WebSummarizationService)
    return service


@pytest.fixture
def test_app(mock_summarization_service):
    """Create test FastAPI app with mocked service."""
    from web.api.summarization import get_summarization_service
    
    app = FastAPI()
    app.include_router(router)
    
    # Mock the dependency
    def get_mock_service():
        return mock_summarization_service
    
    app.dependency_overrides[get_summarization_service] = get_mock_service
    return app


@pytest.fixture
def client(test_app):
    """Create test client."""
    return TestClient(test_app)


@pytest.fixture
def sample_task():
    """Create sample summarization task."""
    return SummaryTask(
        task_id="test-task-123",
        summary_type=SummaryType.WEEKLY,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 7),
        status=SummaryTaskStatus.PENDING,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        progress=0.0,
        current_step="Initializing"
    )


@pytest.fixture
def sample_progress():
    """Create sample progress update."""
    return ProgressUpdate(
        task_id="test-task-123",
        progress=50.0,
        current_step="Processing content",
        status=SummaryTaskStatus.RUNNING,
        timestamp=datetime(2024, 1, 1, 12, 30, 0)
    )


class TestSummarizationAPI:
    """Test cases for summarization API endpoints."""
    
    def test_create_summarization_task_success(self, client, mock_summarization_service, sample_task):
        """Test successful task creation."""
        # Mock service methods
        mock_summarization_service.create_summary_task = AsyncMock(return_value="test-task-123")
        mock_summarization_service.start_summarization = AsyncMock(return_value=True)
        mock_summarization_service.get_task_status = AsyncMock(return_value=sample_task)
        
        # Make request
        response = client.post("/api/summarization/tasks", json={
            "summary_type": "weekly",
            "start_date": "2024-01-01",
            "end_date": "2024-01-07"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-123"
        assert data["summary_type"] == "weekly"
        assert data["start_date"] == "2024-01-01"
        assert data["end_date"] == "2024-01-07"
        assert data["status"] == "pending"
    
    def test_create_summarization_task_invalid_type(self, client, mock_summarization_service):
        """Test task creation with invalid summary type."""
        response = client.post("/api/summarization/tasks", json={
            "summary_type": "invalid",
            "start_date": "2024-01-01",
            "end_date": "2024-01-07"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_create_summarization_task_invalid_date_range(self, client, mock_summarization_service):
        """Test task creation with invalid date range."""
        response = client.post("/api/summarization/tasks", json={
            "summary_type": "weekly",
            "start_date": "2024-01-07",
            "end_date": "2024-01-01"  # End before start
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_create_summarization_task_future_date(self, client, mock_summarization_service):
        """Test task creation with future start date."""
        future_date = (date.today() + timedelta(days=1)).isoformat()
        
        response = client.post("/api/summarization/tasks", json={
            "summary_type": "weekly",
            "start_date": future_date,
            "end_date": future_date
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_create_summarization_task_service_error(self, client, mock_summarization_service):
        """Test task creation when service raises error."""
        mock_summarization_service.create_summary_task = AsyncMock(side_effect=ValueError("Service error"))
        
        response = client.post("/api/summarization/tasks", json={
            "summary_type": "weekly",
            "start_date": "2024-01-01",
            "end_date": "2024-01-07"
        })
        
        assert response.status_code == 400
        assert "Service error" in response.json()["detail"]
    
    def test_get_all_tasks(self, client, mock_summarization_service, sample_task):
        """Test getting all tasks."""
        mock_summarization_service.get_all_tasks = AsyncMock(return_value=[sample_task])
        
        response = client.get("/api/summarization/tasks")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["task_id"] == "test-task-123"
        assert data[0]["summary_type"] == "weekly"
    
    def test_get_task_status_success(self, client, mock_summarization_service, sample_task):
        """Test getting task status."""
        mock_summarization_service.get_task_status = AsyncMock(return_value=sample_task)
        
        response = client.get("/api/summarization/tasks/test-task-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-123"
        assert data["status"] == "pending"
    
    def test_get_task_status_not_found(self, client, mock_summarization_service):
        """Test getting status of non-existent task."""
        mock_summarization_service.get_task_status = AsyncMock(return_value=None)
        
        response = client.get("/api/summarization/tasks/non-existent")
        
        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]
    
    def test_get_task_progress_success(self, client, mock_summarization_service, sample_progress):
        """Test getting task progress."""
        mock_summarization_service.get_task_progress = AsyncMock(return_value=sample_progress)
        
        response = client.get("/api/summarization/tasks/test-task-123/progress")
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-123"
        assert data["progress"] == 50.0
        assert data["current_step"] == "Processing content"
        assert data["status"] == "running"
    
    def test_get_task_progress_fallback_to_task(self, client, mock_summarization_service, sample_task):
        """Test getting task progress when no progress update exists."""
        mock_summarization_service.get_task_progress = AsyncMock(return_value=None)
        mock_summarization_service.get_task_status = AsyncMock(return_value=sample_task)
        
        response = client.get("/api/summarization/tasks/test-task-123/progress")
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-123"
        assert data["progress"] == 0.0
        assert data["current_step"] == "Initializing"
    
    def test_get_task_progress_not_found(self, client, mock_summarization_service):
        """Test getting progress of non-existent task."""
        mock_summarization_service.get_task_progress = AsyncMock(return_value=None)
        mock_summarization_service.get_task_status = AsyncMock(return_value=None)
        
        response = client.get("/api/summarization/tasks/non-existent/progress")
        
        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]
    
    def test_cancel_task_success(self, client, mock_summarization_service):
        """Test successful task cancellation."""
        mock_summarization_service.cancel_task = AsyncMock(return_value=True)
        
        response = client.post("/api/summarization/tasks/test-task-123/cancel")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Task cancelled successfully"
        assert data["task_id"] == "test-task-123"
    
    def test_cancel_task_failure(self, client, mock_summarization_service):
        """Test task cancellation failure."""
        mock_summarization_service.cancel_task = AsyncMock(return_value=False)
        
        response = client.post("/api/summarization/tasks/test-task-123/cancel")
        
        assert response.status_code == 400
        assert "cannot be cancelled" in response.json()["detail"]
    
    def test_get_task_result_success(self, client, mock_summarization_service):
        """Test getting task result."""
        completed_task = SummaryTask(
            task_id="test-task-123",
            summary_type=SummaryType.WEEKLY,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
            status=SummaryTaskStatus.COMPLETED,
            result="This is the summary result",
            completed_at=datetime(2024, 1, 1, 13, 0, 0)
        )
        
        mock_summarization_service.get_task_status = AsyncMock(return_value=completed_task)
        
        response = client.get("/api/summarization/tasks/test-task-123/result")
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-123"
        assert data["result"] == "This is the summary result"
        assert data["summary_type"] == "weekly"
    
    def test_get_task_result_not_completed(self, client, mock_summarization_service, sample_task):
        """Test getting result of non-completed task."""
        mock_summarization_service.get_task_status = AsyncMock(return_value=sample_task)
        
        response = client.get("/api/summarization/tasks/test-task-123/result")
        
        assert response.status_code == 400
        assert "not completed" in response.json()["detail"]
    
    def test_get_task_result_no_result(self, client, mock_summarization_service):
        """Test getting result when no result available."""
        completed_task = SummaryTask(
            task_id="test-task-123",
            summary_type=SummaryType.WEEKLY,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
            status=SummaryTaskStatus.COMPLETED,
            result=None  # No result
        )
        
        mock_summarization_service.get_task_status = AsyncMock(return_value=completed_task)
        
        response = client.get("/api/summarization/tasks/test-task-123/result")
        
        assert response.status_code == 404
        assert "result not available" in response.json()["detail"]
    
    def test_download_task_result_success(self, client, mock_summarization_service):
        """Test downloading task result file."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test summary content")
            temp_file_path = f.name
        
        try:
            completed_task = SummaryTask(
                task_id="test-task-123",
                summary_type=SummaryType.WEEKLY,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 7),
                status=SummaryTaskStatus.COMPLETED,
                output_file_path=temp_file_path
            )
            
            mock_summarization_service.get_task_status = AsyncMock(return_value=completed_task)
            
            response = client.get("/api/summarization/tasks/test-task-123/download")
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/plain; charset=utf-8"
            assert "summary_weekly_2024-01-01_2024-01-07.txt" in response.headers.get("content-disposition", "")
            assert response.content == b"Test summary content"
            
        finally:
            # Clean up
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    def test_download_task_result_file_not_found(self, client, mock_summarization_service):
        """Test downloading when output file doesn't exist."""
        completed_task = SummaryTask(
            task_id="test-task-123",
            summary_type=SummaryType.WEEKLY,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
            status=SummaryTaskStatus.COMPLETED,
            output_file_path="/non/existent/file.txt"
        )
        
        mock_summarization_service.get_task_status = AsyncMock(return_value=completed_task)
        
        response = client.get("/api/summarization/tasks/test-task-123/download")
        
        assert response.status_code == 404
        assert "Output file not found" in response.json()["detail"]
    
    def test_delete_task_success(self, client, mock_summarization_service):
        """Test successful task deletion."""
        completed_task = SummaryTask(
            task_id="test-task-123",
            summary_type=SummaryType.WEEKLY,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
            status=SummaryTaskStatus.COMPLETED
        )
        
        mock_summarization_service.get_task_status = AsyncMock(return_value=completed_task)
        mock_summarization_service._task_lock = AsyncMock()
        mock_summarization_service.active_tasks = {"test-task-123": completed_task}
        mock_summarization_service.task_progress = {}
        
        response = client.delete("/api/summarization/tasks/test-task-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Task deleted successfully"
        assert data["task_id"] == "test-task-123"
    
    def test_delete_running_task(self, client, mock_summarization_service):
        """Test deleting running task (should fail)."""
        running_task = SummaryTask(
            task_id="test-task-123",
            summary_type=SummaryType.WEEKLY,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),
            status=SummaryTaskStatus.RUNNING
        )
        
        mock_summarization_service.get_task_status = AsyncMock(return_value=running_task)
        
        response = client.delete("/api/summarization/tasks/test-task-123")
        
        assert response.status_code == 400
        assert "Cannot delete running task" in response.json()["detail"]
    
    def test_cleanup_completed_tasks(self, client, mock_summarization_service):
        """Test cleanup of completed tasks."""
        mock_summarization_service.cleanup_completed_tasks = AsyncMock(return_value=3)
        
        response = client.post("/api/summarization/cleanup?older_than_hours=48")
        
        assert response.status_code == 200
        data = response.json()
        assert data["cleaned_count"] == 3
        assert data["older_than_hours"] == 48
        assert "Cleaned up 3 completed tasks" in data["message"]
    
    def test_cleanup_invalid_hours(self, client, mock_summarization_service):
        """Test cleanup with invalid hours parameter."""
        response = client.post("/api/summarization/cleanup?older_than_hours=200")
        
        assert response.status_code == 400
        assert "must be between 1 and 168" in response.json()["detail"]
    
    def test_get_summarization_stats(self, client, mock_summarization_service):
        """Test getting summarization statistics."""
        tasks = [
            SummaryTask("task1", SummaryType.WEEKLY, date(2024, 1, 1), date(2024, 1, 7), SummaryTaskStatus.COMPLETED),
            SummaryTask("task2", SummaryType.MONTHLY, date(2024, 1, 1), date(2024, 1, 31), SummaryTaskStatus.RUNNING),
            SummaryTask("task3", SummaryType.WEEKLY, date(2024, 1, 8), date(2024, 1, 14), SummaryTaskStatus.FAILED),
        ]
        
        mock_summarization_service.get_all_tasks = AsyncMock(return_value=tasks)
        
        response = client.get("/api/summarization/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_tasks"] == 3
        assert data["completed_tasks"] == 1
        assert data["running_tasks"] == 1
        assert data["failed_tasks"] == 1
        assert data["task_types"]["weekly"] == 2
        assert data["task_types"]["monthly"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])