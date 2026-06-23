# ABOUTME: Tests for server-side validation matching client-side checks.
# ABOUTME: Covers summarization date range max and work week start_day != end_day.
"""
Tests for Issue #14: Server-side validation for client-only checks.

The summarization date range must be limited to 365 days server-side.
The work week start_day and end_day must differ when both are provided.
"""

import pytest
from datetime import date, timedelta


class TestSummarizationDateRangeValidation:
    """Verify server-side date range limit for summarization requests."""

    def test_date_range_exceeding_365_days_rejected(self, isolated_app_client):
        """Date range > 365 days must be rejected."""
        start = date(2025, 1, 1)
        end = start + timedelta(days=366)
        response = isolated_app_client.post(
            "/api/summarization/tasks",
            json={
                "summary_type": "custom",
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            }
        )
        assert response.status_code == 422, \
            f"Expected 422 for 366-day range, got {response.status_code}"

    def test_date_range_exactly_365_accepted(self, isolated_app_client):
        """365-day range should pass validation (may fail for other reasons)."""
        start = date(2025, 1, 1)
        end = start + timedelta(days=365)
        response = isolated_app_client.post(
            "/api/summarization/tasks",
            json={
                "summary_type": "custom",
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
            }
        )
        # Should not fail validation (may fail for other reasons like missing LLM)
        assert response.status_code != 422

    def test_short_date_range_accepted(self, isolated_app_client):
        """Short date range should pass validation."""
        response = isolated_app_client.post(
            "/api/summarization/tasks",
            json={
                "summary_type": "weekly",
                "start_date": "2025-06-01",
                "end_date": "2025-06-07",
            }
        )
        assert response.status_code != 422


class TestWorkWeekDayValidation:
    """Verify start_day != end_day is enforced server-side."""

    def test_same_start_and_end_day_rejected(self, isolated_app_client):
        """start_day == end_day must be rejected."""
        response = isolated_app_client.post(
            "/api/settings/work-week",
            json={
                "preset": "custom",
                "start_day": 3,
                "end_day": 3,
                "timezone": "UTC",
            }
        )
        assert response.status_code == 422, \
            f"Expected 422 for same start/end day, got {response.status_code}"

    def test_different_start_and_end_day_accepted(self, isolated_app_client):
        """Different start_day and end_day should pass validation."""
        response = isolated_app_client.post(
            "/api/settings/work-week",
            json={
                "preset": "custom",
                "start_day": 1,
                "end_day": 5,
                "timezone": "UTC",
            }
        )
        # Should not fail validation
        assert response.status_code != 422
