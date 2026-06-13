# ABOUTME: Security tests for sync API error response sanitization.
# ABOUTME: Verifies raw exception strings and stored error messages don't leak.
"""Tests that sync API endpoints do not disclose internal error details."""

import json
import pytest
from unittest.mock import patch, AsyncMock

from web.app import app


SENTINEL = "SENTINEL_SYNC_LEAK_xyz789"


class TestSyncErrorDisclosure:
    """Sync endpoints must not expose raw exception strings in responses."""

    def test_get_sync_status_500_no_leak(self, isolated_app_client):
        """GET /api/sync/status must not leak exception details on 500."""
        with patch.object(
            app.state.sync_service, 'get_sync_status',
            new_callable=AsyncMock, side_effect=Exception(SENTINEL)
        ):
            response = isolated_app_client.get("/api/sync/status")
            assert response.status_code == 500
            assert SENTINEL not in json.dumps(response.json())

    def test_get_scheduler_status_500_no_leak(self, isolated_app_client):
        """GET /api/sync/scheduler/status must not leak exception details."""
        if hasattr(app.state, 'scheduler') and app.state.scheduler:
            with patch.object(
                app.state.scheduler, 'get_scheduler_status',
                side_effect=Exception(SENTINEL)
            ):
                response = isolated_app_client.get("/api/sync/scheduler/status")
                if response.status_code == 500:
                    assert SENTINEL not in json.dumps(response.json())

    def test_full_sync_500_no_leak(self, isolated_app_client):
        """POST /api/sync/full must not leak exception details on 500."""
        with patch.object(
            app.state.sync_service, 'get_sync_status',
            new_callable=AsyncMock, side_effect=Exception(SENTINEL)
        ):
            response = isolated_app_client.post("/api/sync/full")
            assert response.status_code == 500
            assert SENTINEL not in json.dumps(response.json())

    def test_sync_history_500_no_leak(self, isolated_app_client):
        """GET /api/sync/history must not leak exception details on 500."""
        with patch.object(
            app.state.sync_service.db_manager, 'get_session',
            side_effect=Exception(SENTINEL)
        ):
            response = isolated_app_client.get("/api/sync/history")
            assert response.status_code == 500
            assert SENTINEL not in json.dumps(response.json())


class TestSyncHistoryErrorMessageSanitization:
    """Stored error_message values must be sanitized before returning to clients."""

    def test_sync_status_error_message_sanitized(self, isolated_app_client):
        """GET /api/sync/status should not return raw error_message strings."""
        response = isolated_app_client.get("/api/sync/status")
        if response.status_code == 200:
            data = response.json()
            for sync in data.get("sync_status", {}).get("recent_syncs", []):
                if sync.get("error_message") is not None:
                    # Should be a generic message, not a raw exception
                    assert sync["error_message"] == "Sync failed"


class TestIncrementalSyncInputValidation:
    """POST /api/sync/incremental must validate since_days bounds."""

    def test_negative_since_days_rejected(self, isolated_app_client):
        """Negative since_days must be rejected."""
        response = isolated_app_client.post(
            "/api/sync/incremental",
            json={"since_days": -1}
        )
        assert response.status_code == 422

    def test_zero_since_days_rejected(self, isolated_app_client):
        """Zero since_days must be rejected."""
        response = isolated_app_client.post(
            "/api/sync/incremental",
            json={"since_days": 0}
        )
        assert response.status_code == 422

    def test_excessive_since_days_rejected(self, isolated_app_client):
        """since_days > 365 must be rejected."""
        response = isolated_app_client.post(
            "/api/sync/incremental",
            json={"since_days": 999}
        )
        assert response.status_code == 422

    def test_valid_since_days_accepted(self, isolated_app_client):
        """Valid since_days should be accepted (returns 200 even if sync can't run)."""
        response = isolated_app_client.post(
            "/api/sync/incremental",
            json={"since_days": 7}
        )
        # 200 or 409 (already in progress) are both acceptable
        assert response.status_code in (200, 409)

    def test_non_integer_since_days_rejected(self, isolated_app_client):
        """Non-integer since_days must be rejected."""
        response = isolated_app_client.post(
            "/api/sync/incremental",
            json={"since_days": "abc"}
        )
        assert response.status_code == 422
