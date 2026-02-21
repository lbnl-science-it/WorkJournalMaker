# ABOUTME: Tests that frontend JS URLs match the backend API routes.
# ABOUTME: Validates the summarization.js file calls correct endpoint paths.

"""
Tests for summarization route alignment between frontend and backend.

Ensures the JavaScript frontend calls the same URL paths that the
FastAPI backend exposes, preventing 404 errors at runtime.
"""

import re
from pathlib import Path

import pytest


JS_FILE = Path(__file__).parent.parent / "web" / "static" / "js" / "summarization.js"
PY_FILE = Path(__file__).parent.parent / "web" / "api" / "summarization.py"


class TestSummarizationRouteAlignment:
    """Verify frontend JS URLs match backend API routes."""

    def test_js_file_exists(self):
        """The summarization.js file must exist."""
        assert JS_FILE.is_file(), f"Expected JS file at {JS_FILE}"

    def test_py_file_exists(self):
        """The summarization.py backend file must exist."""
        assert PY_FILE.is_file(), f"Expected Python file at {PY_FILE}"

    def test_create_task_url(self):
        """Frontend must POST to /api/summarization/tasks to create a task."""
        source = JS_FILE.read_text()
        # Should use /api/summarization/tasks (the backend route)
        assert "/api/summarization/tasks" in source, (
            "Frontend must call POST /api/summarization/tasks to create tasks. "
            "Found calls to a different path."
        )
        # Should NOT use the wrong /api/summarization/create path
        assert "/api/summarization/create" not in source, (
            "Frontend must not call /api/summarization/create — "
            "the backend route is POST /api/summarization/tasks"
        )

    def test_no_separate_start_call(self):
        """Frontend must not call a separate /start endpoint.

        The backend auto-starts tasks via BackgroundTasks in the create
        endpoint, so a separate start call would 404.
        """
        source = JS_FILE.read_text()
        assert "/start" not in source, (
            "Frontend must not call a /start endpoint — "
            "the backend auto-starts tasks on creation"
        )

    def test_task_status_url_uses_tasks_prefix(self):
        """Frontend status polling must use /api/summarization/tasks/{id}."""
        source = JS_FILE.read_text()
        # Should NOT have /{id}/status pattern (wrong)
        # The correct pattern uses /tasks/{id} which is the GET route
        status_wrong_pattern = re.compile(
            r"""/api/summarization/\$\{[^}]+\}/status"""
        )
        matches = status_wrong_pattern.findall(source)
        assert matches == [], (
            f"Found wrong status URL pattern(s): {matches}. "
            "Use /api/summarization/tasks/${{taskId}} instead."
        )

    def test_cancel_url_uses_tasks_prefix(self):
        """Frontend cancel must use /api/summarization/tasks/{id}/cancel."""
        source = JS_FILE.read_text()
        # Check for the correct pattern with /tasks/ prefix
        cancel_correct = re.compile(
            r"""/api/summarization/tasks/\$\{[^}]+\}/cancel"""
        )
        assert cancel_correct.search(source), (
            "Frontend must call /api/summarization/tasks/{id}/cancel"
        )

    def test_result_url_uses_tasks_prefix(self):
        """Frontend result retrieval must use /api/summarization/tasks/{id}/result."""
        source = JS_FILE.read_text()
        result_correct = re.compile(
            r"""/api/summarization/tasks/\$\{[^}]+\}/result"""
        )
        assert result_correct.search(source), (
            "Frontend must call /api/summarization/tasks/{id}/result"
        )

    def test_download_url_uses_tasks_prefix(self):
        """Frontend download must use /api/summarization/tasks/{id}/download."""
        source = JS_FILE.read_text()
        download_correct = re.compile(
            r"""/api/summarization/tasks/\$\{[^}]+\}/download"""
        )
        assert download_correct.search(source), (
            "Frontend must call /api/summarization/tasks/{id}/download"
        )

    def test_history_uses_tasks_endpoint(self):
        """Frontend history must use /api/summarization/tasks (GET all tasks)."""
        source = JS_FILE.read_text()
        # Should NOT use the non-existent /history endpoint
        assert "/api/summarization/history" not in source, (
            "Frontend must not call /api/summarization/history — "
            "use GET /api/summarization/tasks instead"
        )

    def test_websocket_url_uses_ws_prefix(self):
        """Frontend WebSocket must connect to /api/summarization/ws/{id}."""
        source = JS_FILE.read_text()
        ws_correct = re.compile(
            r"""/api/summarization/ws/\$\{[^}]+\}"""
        )
        assert ws_correct.search(source), (
            "Frontend WebSocket must connect to /api/summarization/ws/{id}"
        )
        # Should NOT use /{id}/progress as WebSocket path
        ws_wrong = re.compile(
            r"""/api/summarization/\$\{[^}]+\}/progress"""
        )
        matches = ws_wrong.findall(source)
        assert matches == [], (
            f"Found wrong WebSocket URL pattern(s): {matches}. "
            "Use /api/summarization/ws/${{taskId}} instead."
        )
