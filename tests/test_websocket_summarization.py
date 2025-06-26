"""
Test WebSocket functionality for summarization progress tracking.
"""

import pytest
import asyncio
import json
from datetime import date
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from web.api.summarization import router as summarization_router
from web.services.web_summarizer import SummaryType


# Create a test app without middleware restrictions
def create_test_app():
    """Create a test FastAPI app for WebSocket testing."""
    test_app = FastAPI()
    test_app.include_router(summarization_router)
    
    # Mock summarization service
    mock_service = AsyncMock()
    mock_service.get_task_status.return_value = None  # Task not found
    
    # Mock app state
    class MockState:
        def __init__(self):
            self.summarization_service = mock_service
    
    test_app.state = MockState()
    return test_app


class TestWebSocketSummarization:
    """Test WebSocket functionality for summarization progress tracking."""
    
    def setup_method(self):
        """Set up test method."""
        self.test_app = create_test_app()
        self.client = TestClient(self.test_app)
    
    def test_websocket_general_connection(self):
        """Test general WebSocket connection."""
        with self.client.websocket_connect("/api/summarization/ws") as websocket:
            # Send test message
            websocket.send_text("test")
            
            # Receive response
            data = websocket.receive_text()
            response = json.loads(data)
            
            assert response["type"] == "connection_status"
            assert response["status"] == "connected"
    
    def test_websocket_task_specific_connection(self):
        """Test task-specific WebSocket connection."""
        task_id = "test-task-123"
        
        with self.client.websocket_connect(f"/api/summarization/ws/{task_id}") as websocket:
            # Should receive initial status or error
            data = websocket.receive_text()
            response = json.loads(data)
            
            # Should be either initial_status or error (task not found)
            assert response["type"] in ["initial_status", "error"]
            
            if response["type"] == "error":
                assert "not found" in response["message"]
    
    @pytest.mark.asyncio
    async def test_progress_update_broadcast(self):
        """Test that progress updates are broadcast via WebSocket."""
        from web.api.summarization import connection_manager
        from web.services.web_summarizer import WebSummarizationService
        
        # Mock WebSocket
        mock_websocket = AsyncMock()
        task_id = "test-task-456"
        
        # Add mock websocket to connection manager
        connection_manager.task_subscribers[task_id] = {mock_websocket}
        
        # Send progress update
        progress_data = {
            "progress": 50.0,
            "current_step": "Processing content",
            "status": "running",
            "timestamp": "2024-01-01T12:00:00"
        }
        
        await connection_manager.send_progress_update(task_id, progress_data)
        
        # Verify WebSocket was called
        mock_websocket.send_text.assert_called_once()
        call_args = mock_websocket.send_text.call_args[0][0]
        sent_data = json.loads(call_args)
        
        assert sent_data["type"] == "progress_update"
        assert sent_data["task_id"] == task_id
        assert sent_data["data"]["progress"] == 50.0
        assert sent_data["data"]["current_step"] == "Processing content"
    
    @pytest.mark.asyncio
    async def test_task_status_broadcast(self):
        """Test that task status updates are broadcast via WebSocket."""
        from web.api.summarization import connection_manager
        
        # Mock WebSocket
        mock_websocket = AsyncMock()
        task_id = "test-task-789"
        
        # Add mock websocket to connection manager
        connection_manager.task_subscribers[task_id] = {mock_websocket}
        
        # Send status update
        status_data = {
            "status": "completed",
            "progress": 100.0,
            "current_step": "Summarization completed",
            "error_message": None,
            "completed_at": "2024-01-01T12:30:00",
            "timestamp": "2024-01-01T12:30:00"
        }
        
        await connection_manager.send_task_status(task_id, status_data)
        
        # Verify WebSocket was called
        mock_websocket.send_text.assert_called_once()
        call_args = mock_websocket.send_text.call_args[0][0]
        sent_data = json.loads(call_args)
        
        assert sent_data["type"] == "task_status"
        assert sent_data["task_id"] == task_id
        assert sent_data["data"]["status"] == "completed"
        assert sent_data["data"]["progress"] == 100.0
    
    def test_connection_manager_disconnect(self):
        """Test connection manager disconnect functionality."""
        from web.api.summarization import connection_manager
        
        # Mock WebSocket
        mock_websocket = MagicMock()
        task_id = "test-task-disconnect"
        
        # Add mock websocket to connection manager
        connection_manager.task_subscribers[task_id] = {mock_websocket}
        
        # Disconnect
        connection_manager.disconnect(mock_websocket, task_id)
        
        # Verify websocket was removed
        assert task_id not in connection_manager.task_subscribers
    
    def test_connection_manager_general_disconnect(self):
        """Test connection manager general disconnect functionality."""
        from web.api.summarization import connection_manager
        
        # Mock WebSocket
        mock_websocket = MagicMock()
        
        # Add mock websocket to general connections
        connection_manager.active_connections["general"] = {mock_websocket}
        
        # Disconnect
        connection_manager.disconnect(mock_websocket)
        
        # Verify websocket was removed
        assert mock_websocket not in connection_manager.active_connections.get("general", set())


if __name__ == "__main__":
    pytest.main([__file__])