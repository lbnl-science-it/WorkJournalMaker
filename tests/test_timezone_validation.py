# ABOUTME: Tests that timezone settings are validated against IANA timezone database.
# ABOUTME: Validates rejection of arbitrary strings in work_week_service and settings_service.
"""
Tests for Issue #10: Timezone must be validated against IANA tz database.

The timezone setting must be a real IANA timezone identifier
(e.g., "America/Los_Angeles"), not just any non-empty string.
Invalid timezones must cause validation errors, not warnings.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from web.services.work_week_service import WorkWeekService, WorkWeekConfig, WorkWeekPreset


@pytest.fixture
def work_week_service():
    """Create a WorkWeekService with mocked dependencies."""
    mock_config = MagicMock()
    mock_logger = MagicMock()
    mock_db = MagicMock()
    service = WorkWeekService(mock_config, mock_logger, mock_db)
    return service


def _make_config(timezone):
    """Create a WorkWeekConfig with the given timezone and default day settings."""
    return WorkWeekConfig(
        preset=WorkWeekPreset.MONDAY_FRIDAY,
        start_day=1,
        end_day=5,
        timezone=timezone,
    )


class TestTimezoneValidation:
    """Verify timezone validation uses IANA tz database."""

    def test_valid_timezone_accepted(self, work_week_service):
        """Standard IANA timezone must pass validation."""
        config = _make_config("America/Los_Angeles")
        is_valid, msg = work_week_service._validate_timezone(config)
        assert is_valid is True

    def test_utc_timezone_accepted(self, work_week_service):
        """UTC must pass validation."""
        config = _make_config("UTC")
        is_valid, msg = work_week_service._validate_timezone(config)
        assert is_valid is True

    def test_fictional_timezone_rejected(self, work_week_service):
        """Non-existent timezone must be rejected."""
        config = _make_config("America/Fictional")
        is_valid, msg = work_week_service._validate_timezone(config)
        assert is_valid is False

    def test_arbitrary_string_rejected(self, work_week_service):
        """Arbitrary strings must be rejected."""
        config = _make_config("not-a-timezone")
        is_valid, msg = work_week_service._validate_timezone(config)
        assert is_valid is False

    def test_empty_timezone_accepted(self, work_week_service):
        """Empty/None timezone means 'use system default'."""
        config = _make_config(None)
        is_valid, msg = work_week_service._validate_timezone(config)
        assert is_valid is True

    def test_empty_string_timezone_accepted(self, work_week_service):
        """Empty string timezone means 'use system default'."""
        config = _make_config("")
        is_valid, msg = work_week_service._validate_timezone(config)
        assert is_valid is True


class TestSettingsServiceTimezoneValidation:
    """Verify settings_service also validates timezone properly."""

    def test_settings_service_rejects_bogus_timezone(self):
        """The settings service timezone validation must reject bogus values."""
        from web.services.settings_service import SettingsService
        mock_config = MagicMock()
        mock_logger = MagicMock()
        mock_db = MagicMock()
        service = SettingsService(mock_config, mock_logger, mock_db)
        result = service._validate_work_week_setting("work_week.timezone", "Bogus/Zone")
        assert result is False

    def test_settings_service_accepts_valid_timezone(self):
        """The settings service must accept real IANA timezones."""
        from web.services.settings_service import SettingsService
        mock_config = MagicMock()
        mock_logger = MagicMock()
        mock_db = MagicMock()
        service = SettingsService(mock_config, mock_logger, mock_db)
        result = service._validate_work_week_setting("work_week.timezone", "Europe/London")
        assert result is True
