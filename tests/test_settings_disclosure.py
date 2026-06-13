# ABOUTME: Security tests for settings API error response sanitization.
# ABOUTME: Verifies raw exception strings never leak through HTTPException details.
"""Tests that settings API endpoints do not disclose internal error details."""

import json
import pytest
from unittest.mock import patch, AsyncMock

from web.app import app


SENTINEL = "SENTINEL_LEAK_TEST_xyz789"


class TestSettingsErrorDisclosure:
    """Settings endpoints must not expose raw exception strings in responses."""

    def test_get_all_settings_500_no_leak(self, isolated_app_client):
        """GET /api/settings/ must not leak exception details on 500."""
        with patch.object(
            app.state.settings_service, 'get_all_settings',
            new_callable=AsyncMock, side_effect=Exception(SENTINEL)
        ):
            response = isolated_app_client.get("/api/settings/")
            assert response.status_code == 500
            assert SENTINEL not in json.dumps(response.json())

    def test_get_setting_500_no_leak(self, isolated_app_client):
        """GET /api/settings/{key} must not leak exception details on 500."""
        with patch.object(
            app.state.settings_service, 'get_setting',
            new_callable=AsyncMock, side_effect=Exception(SENTINEL)
        ):
            response = isolated_app_client.get("/api/settings/ui.theme")
            assert response.status_code == 500
            assert SENTINEL not in json.dumps(response.json())

    def test_update_setting_valueerror_no_leak(self, isolated_app_client):
        """PUT /api/settings/{key} must not leak ValueError details on 400."""
        with patch.object(
            app.state.settings_service, 'update_setting',
            new_callable=AsyncMock, side_effect=ValueError(SENTINEL)
        ):
            response = isolated_app_client.put(
                "/api/settings/ui.theme",
                json={"value": "dark"}
            )
            assert response.status_code == 400
            assert SENTINEL not in json.dumps(response.json())

    def test_settings_health_unhealthy_no_error_key(self, isolated_app_client):
        """GET /api/settings/health unhealthy path must not include 'error' key."""
        with patch.object(
            app.state.settings_service, 'get_setting',
            new_callable=AsyncMock, side_effect=Exception(SENTINEL)
        ):
            response = isolated_app_client.get("/api/settings/health")
            data = response.json()
            assert "error" not in data
            if data.get("status") == "unhealthy":
                assert SENTINEL not in json.dumps(data)

    def test_bulk_update_valueerror_no_leak(self, isolated_app_client):
        """POST /api/settings/bulk-update must not leak ValueError details."""
        with patch.object(
            app.state.settings_service, 'bulk_update_settings',
            new_callable=AsyncMock, side_effect=ValueError(SENTINEL)
        ):
            response = isolated_app_client.post(
                "/api/settings/bulk-update",
                json={"settings": {"ui.theme": "dark"}}
            )
            assert response.status_code == 400
            assert SENTINEL not in json.dumps(response.json())

    def test_reset_setting_valueerror_no_leak(self, isolated_app_client):
        """POST /api/settings/{key}/reset must not leak ValueError details."""
        with patch.object(
            app.state.settings_service, 'reset_setting',
            new_callable=AsyncMock, side_effect=ValueError(SENTINEL)
        ):
            response = isolated_app_client.post("/api/settings/ui.theme/reset")
            assert response.status_code == 400
            assert SENTINEL not in json.dumps(response.json())

    def test_import_settings_valueerror_no_leak(self, isolated_app_client):
        """POST /api/settings/import must not leak ValueError details."""
        with patch.object(
            app.state.settings_service, 'import_settings',
            new_callable=AsyncMock, side_effect=ValueError(SENTINEL)
        ):
            response = isolated_app_client.post(
                "/api/settings/import",
                json={"settings": {"ui.theme": "dark"}}
            )
            assert response.status_code == 400
            assert SENTINEL not in json.dumps(response.json())

    def test_work_week_500_no_leak(self, isolated_app_client):
        """GET /api/settings/work-week must not leak exception details."""
        with patch.object(
            app.state.settings_service, 'get_work_week_settings',
            new_callable=AsyncMock, side_effect=Exception(SENTINEL)
        ):
            response = isolated_app_client.get("/api/settings/work-week")
            assert response.status_code == 500
            assert SENTINEL not in json.dumps(response.json())

    def test_update_work_week_valueerror_no_leak(self, isolated_app_client):
        """POST /api/settings/work-week must not leak ValueError details."""
        with patch.object(
            app.state.settings_service, 'update_work_week_configuration',
            new_callable=AsyncMock, side_effect=ValueError(SENTINEL)
        ):
            response = isolated_app_client.post(
                "/api/settings/work-week",
                json={"preset": "custom", "start_day": 1, "end_day": 5}
            )
            assert response.status_code == 400
            assert SENTINEL not in json.dumps(response.json())
