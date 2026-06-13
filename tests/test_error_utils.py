# ABOUTME: Tests for the error message sanitization utility.
# ABOUTME: Validates that raw exception strings are never passed through to callers.
"""Tests for web.utils.error_utils."""

from web.utils.error_utils import sanitize_error_message


class TestSanitizeErrorMessage:
    """Tests for sanitize_error_message()."""

    def test_none_returns_none(self):
        """None input means no error occurred — should pass through as None."""
        assert sanitize_error_message(None) is None

    def test_non_none_returns_generic(self):
        """Any real error string should be replaced with the generic message."""
        result = sanitize_error_message("FATAL: unable to open /var/db/journal.db")
        assert result == "An error occurred"
        assert "/var/db" not in result

    def test_custom_generic(self):
        """Caller can specify a domain-specific generic message."""
        result = sanitize_error_message("connection refused", generic="Sync failed")
        assert result == "Sync failed"

    def test_empty_string_returns_generic(self):
        """Empty string is still a non-None value — sanitize it."""
        result = sanitize_error_message("")
        assert result == "An error occurred"
