"""
Summarization API Endpoints

This module provides REST API endpoints for summarization operations with
real-time progress tracking and task management.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from datetime import date, datetime
from typing import Optional, List
import sys
from pathlib import Path
import os

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from config_manager import AppConfig
from logger import JournalSummarizerLogger, ErrorCategory
from web.services.web_summarizer import WebSummarizationService, SummaryType, SummaryTaskStatus
from web.models.journal import SummaryRequest, SummaryTaskResponse, ProgressResponse

router = APIRouter(prefix="/api/summarization", tags=["summarization"])


def get_summarization_service(request: Request) -> WebSummarizationService:
    """Dependency to get WebSummarizationService from app state."""
    return request.app.state.summarization_service


@router.post("/tasks", response_model=SummaryTaskResponse)
async def create_summarization_task(
    request: SummaryRequest,
    background_tasks: BackgroundTasks,
    summarization_service: WebSummarizationService = Depends(get_summarization_service)
):
    """Create a new summarization task."""
    try:
        # Convert string to enum
        summary_type = SummaryType(request.summary_type)
        
        # Create task
        task_id = await summarization_service.create_summary_task(
            summary_type, request.start_date, request.end_date
        )
        
        # Start task in background
        background_tasks.add_task(summarization_service.start_summarization, task_id)
        
        # Get task details
        task = await summarization_service.get_task_status(task_id)
        if not task:
            raise HTTPException(status_code=500, detail="Failed to retrieve created task")
        
        return SummaryTaskResponse(
            task_id=task.task_id,
            summary_type=task.summary_type.value,
            start_date=task.start_date,
            end_date=task.end_date,
            status=task.status.value,
            progress=task.progress,
            current_step=task.current_step,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            result=task.result,
            error_message=task.error_message,
            output_file_path=task.output_file_path
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create summarization task")


@router.get("/tasks", response_model=List[SummaryTaskResponse])
async def get_all_tasks(
    summarization_service: WebSummarizationService = Depends(get_summarization_service)
):
    """Get all summarization tasks."""
    try:
        tasks = await summarization_service.get_all_tasks()
        
        return [
            SummaryTaskResponse(
                task_id=task.task_id,
                summary_type=task.summary_type.value,
                start_date=task.start_date,
                end_date=task.end_date,
                status=task.status.value,
                progress=task.progress,
                current_step=task.current_step,
                created_at=task.created_at,
                started_at=task.started_at,
                completed_at=task.completed_at,
                result=task.result,
                error_message=task.error_message,
                output_file_path=task.output_file_path
            )
            for task in tasks
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve tasks")


@router.get("/tasks/{task_id}", response_model=SummaryTaskResponse)
async def get_task_status(
    task_id: str,
    summarization_service: WebSummarizationService = Depends(get_summarization_service)
):
    """Get the status of a specific summarization task."""
    try:
        task = await summarization_service.get_task_status(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return SummaryTaskResponse(
            task_id=task.task_id,
            summary_type=task.summary_type.value,
            start_date=task.start_date,
            end_date=task.end_date,
            status=task.status.value,
            progress=task.progress,
            current_step=task.current_step,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            result=task.result,
            error_message=task.error_message,
            output_file_path=task.output_file_path
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve task status")


@router.get("/tasks/{task_id}/progress", response_model=ProgressResponse)
async def get_task_progress(
    task_id: str,
    summarization_service: WebSummarizationService = Depends(get_summarization_service)
):
    """Get the progress of a specific summarization task."""
    try:
        progress = await summarization_service.get_task_progress(task_id)
        if not progress:
            # Try to get task status instead
            task = await summarization_service.get_task_status(task_id)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            
            # Create progress response from task
            return ProgressResponse(
                task_id=task.task_id,
                progress=task.progress,
                current_step=task.current_step,
                status=task.status.value,
                timestamp=task.created_at
            )
        
        return ProgressResponse(
            task_id=progress.task_id,
            progress=progress.progress,
            current_step=progress.current_step,
            status=progress.status.value,
            message=progress.message,
            timestamp=progress.timestamp
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve task progress")


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    summarization_service: WebSummarizationService = Depends(get_summarization_service)
):
    """Cancel a running summarization task."""
    try:
        success = await summarization_service.cancel_task(task_id)
        if not success:
            raise HTTPException(status_code=400, detail="Task cannot be cancelled or not found")
        
        return {"message": "Task cancelled successfully", "task_id": task_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to cancel task")


@router.get("/tasks/{task_id}/result")
async def get_task_result(
    task_id: str,
    summarization_service: WebSummarizationService = Depends(get_summarization_service)
):
    """Get the result of a completed summarization task."""
    try:
        task = await summarization_service.get_task_status(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if task.status != SummaryTaskStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Task is not completed")
        
        if not task.result:
            raise HTTPException(status_code=404, detail="Task result not available")
        
        return {
            "task_id": task_id,
            "summary_type": task.summary_type.value,
            "start_date": task.start_date,
            "end_date": task.end_date,
            "result": task.result,
            "completed_at": task.completed_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve task result")


@router.get("/tasks/{task_id}/download")
async def download_task_result(
    task_id: str,
    summarization_service: WebSummarizationService = Depends(get_summarization_service)
):
    """Download the result file of a completed summarization task."""
    try:
        task = await summarization_service.get_task_status(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if task.status != SummaryTaskStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Task is not completed")
        
        if not task.output_file_path or not os.path.exists(task.output_file_path):
            raise HTTPException(status_code=404, detail="Output file not found")
        
        # Generate filename
        filename = f"summary_{task.summary_type.value}_{task.start_date}_{task.end_date}.txt"
        
        return FileResponse(
            path=task.output_file_path,
            filename=filename,
            media_type='text/plain'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to download task result")


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    summarization_service: WebSummarizationService = Depends(get_summarization_service)
):
    """Delete a summarization task."""
    try:
        task = await summarization_service.get_task_status(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Only allow deletion of completed, failed, or cancelled tasks
        if task.status == SummaryTaskStatus.RUNNING:
            raise HTTPException(status_code=400, detail="Cannot delete running task. Cancel it first.")
        
        # Remove from active tasks
        async with summarization_service._task_lock:
            if task_id in summarization_service.active_tasks:
                del summarization_service.active_tasks[task_id]
            if task_id in summarization_service.task_progress:
                del summarization_service.task_progress[task_id]
        
        return {"message": "Task deleted successfully", "task_id": task_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete task")


@router.post("/cleanup")
async def cleanup_completed_tasks(
    older_than_hours: int = 24,
    summarization_service: WebSummarizationService = Depends(get_summarization_service)
):
    """Clean up completed tasks older than specified hours."""
    try:
        if older_than_hours < 1 or older_than_hours > 168:  # Max 1 week
            raise HTTPException(status_code=400, detail="older_than_hours must be between 1 and 168")
        
        cleaned_count = await summarization_service.cleanup_completed_tasks(older_than_hours)
        
        return {
            "message": f"Cleaned up {cleaned_count} completed tasks",
            "cleaned_count": cleaned_count,
            "older_than_hours": older_than_hours
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to cleanup tasks")


@router.get("/stats")
async def get_summarization_stats(
    summarization_service: WebSummarizationService = Depends(get_summarization_service)
):
    """Get summarization service statistics."""
    try:
        tasks = await summarization_service.get_all_tasks()
        
        stats = {
            "total_tasks": len(tasks),
            "pending_tasks": len([t for t in tasks if t.status == SummaryTaskStatus.PENDING]),
            "running_tasks": len([t for t in tasks if t.status == SummaryTaskStatus.RUNNING]),
            "completed_tasks": len([t for t in tasks if t.status == SummaryTaskStatus.COMPLETED]),
            "failed_tasks": len([t for t in tasks if t.status == SummaryTaskStatus.FAILED]),
            "cancelled_tasks": len([t for t in tasks if t.status == SummaryTaskStatus.CANCELLED]),
        }
        
        # Add task type breakdown
        task_types = {}
        for task in tasks:
            task_type = task.summary_type.value
            if task_type not in task_types:
                task_types[task_type] = 0
            task_types[task_type] += 1
        
        stats["task_types"] = task_types
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")