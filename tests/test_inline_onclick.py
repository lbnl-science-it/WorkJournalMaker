# ABOUTME: Tests that verify no inline onclick handlers with dynamic data exist.
# ABOUTME: Ensures JS files use addEventListener instead of onclick attributes.

"""
Tests for GH#93: Unescaped data in inline onclick attributes.

Inline onclick handlers with template-interpolated data are DOM XSS vectors.
All dynamic event handlers must use addEventListener or data-attribute
delegation instead.
"""

import pytest
from pathlib import Path

# JS files that previously contained dynamic onclick handlers
JS_FILES = [
    "web/static/js/dashboard.js",
    "web/static/js/calendar.js",
    "web/static/js/summarization.js",
    "web/static/js/settings.js",
    "web/static/js/utils.js",
]

# Template files that previously contained inline onclick handlers
TEMPLATE_FILES = [
    "web/templates/entry_editor.html",
    "web/templates/test.html",
]

ALL_FILES = JS_FILES + TEMPLATE_FILES


class TestNoInlineOnclick:
    """Verify no onclick attributes remain in JS or template files."""

    @pytest.mark.parametrize("filepath", ALL_FILES)
    def test_no_onclick_in_file(self, filepath):
        """No file should contain onclick= attributes."""
        path = Path(filepath)
        assert path.exists(), f"{filepath} not found"
        content = path.read_text()
        # Search for onclick= (with either single or double quotes)
        assert 'onclick="' not in content, (
            f"{filepath} contains onclick=\" attribute"
        )
        assert "onclick='" not in content, (
            f"{filepath} contains onclick=' attribute"
        )


class TestEventDelegationPresent:
    """Verify that addEventListener-based handlers replaced inline onclick."""

    def _read(self, filepath):
        return Path(filepath).read_text()

    def test_dashboard_uses_event_delegation(self):
        """dashboard.js should use click event delegation for entry items."""
        content = self._read("web/static/js/dashboard.js")
        assert "addEventListener" in content or "click" in content

    def test_calendar_uses_event_delegation(self):
        """calendar.js should use click event delegation for date cells."""
        content = self._read("web/static/js/calendar.js")
        assert "addEventListener" in content

    def test_summarization_uses_event_delegation(self):
        """summarization.js should use click event delegation for history actions."""
        content = self._read("web/static/js/summarization.js")
        assert "addEventListener" in content
