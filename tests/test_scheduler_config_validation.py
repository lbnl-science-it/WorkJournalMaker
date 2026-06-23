# ABOUTME: Tests that scheduler config endpoint rejects invalid intervals.
# ABOUTME: Validates server-side bounds on incremental_seconds and full_hours.
"""
Tests for Issue #5: Scheduler config must reject zero/negative intervals.

The PUT /api/sync/scheduler/config endpoint must enforce minimum and
maximum bounds on incremental_seconds and full_hours to prevent DoS
via tight polling loops.
"""

import pytest


class TestSchedulerConfigValidation:
    """Verify scheduler config rejects out-of-bounds intervals."""

    def test_incremental_seconds_zero_rejected(self, isolated_app_client):
        """Zero incremental_seconds would cause a tight loop."""
        response = isolated_app_client.put(
            "/api/sync/scheduler/config",
            json={"incremental_seconds": 0}
        )
        assert response.status_code == 422

    def test_incremental_seconds_negative_rejected(self, isolated_app_client):
        """Negative incremental_seconds is invalid."""
        response = isolated_app_client.put(
            "/api/sync/scheduler/config",
            json={"incremental_seconds": -1}
        )
        assert response.status_code == 422

    def test_incremental_seconds_too_large_rejected(self, isolated_app_client):
        """Intervals larger than 24 hours are unreasonable."""
        response = isolated_app_client.put(
            "/api/sync/scheduler/config",
            json={"incremental_seconds": 86401}
        )
        assert response.status_code == 422

    def test_full_hours_zero_rejected(self, isolated_app_client):
        """Zero full_hours would cause continuous full syncs."""
        response = isolated_app_client.put(
            "/api/sync/scheduler/config",
            json={"full_hours": 0}
        )
        assert response.status_code == 422

    def test_full_hours_negative_rejected(self, isolated_app_client):
        """Negative full_hours is invalid."""
        response = isolated_app_client.put(
            "/api/sync/scheduler/config",
            json={"full_hours": -5}
        )
        assert response.status_code == 422

    def test_full_hours_too_large_rejected(self, isolated_app_client):
        """Intervals larger than one week are unreasonable."""
        response = isolated_app_client.put(
            "/api/sync/scheduler/config",
            json={"full_hours": 169}
        )
        assert response.status_code == 422

    def test_valid_config_not_rejected_by_validation(self, isolated_app_client):
        """Valid values must pass validation (may still fail due to scheduler state)."""
        response = isolated_app_client.put(
            "/api/sync/scheduler/config",
            json={"incremental_seconds": 300, "full_hours": 24}
        )
        # 200 or 503 (scheduler not running) — but NOT 422
        assert response.status_code != 422

    def test_null_fields_accepted(self, isolated_app_client):
        """Omitted fields (None) should pass validation."""
        response = isolated_app_client.put(
            "/api/sync/scheduler/config",
            json={}
        )
        assert response.status_code != 422
