# ABOUTME: Tests that client-side JavaScript uses local date formatting, not UTC.
# ABOUTME: Prevents timezone bugs where toISOString() returns tomorrow after ~5pm local time.

"""
Tests that JavaScript files use local date components for API date strings
instead of toISOString().split('T')[0], which returns UTC dates and causes
the calendar 'Today' button to select the wrong date after ~5pm local time.
"""

import re
from pathlib import Path

import pytest

JS_DIR = Path(__file__).resolve().parent.parent / "web" / "static" / "js"

# Files where toISOString().split('T')[0] is acceptable (cosmetic filename use only)
FILENAME_ONLY_ALLOWLIST = {
    "settings.js",       # export filename: journal-settings-YYYY-MM-DD.json
    "summarization.js",  # download filename: summary_..._YYYY-MM-DD.txt
}

# Pattern that matches the problematic toISOString().split('T')[0] usage
TO_ISO_DATE_RE = re.compile(r"\.toISOString\(\)\.split\(['\"]T['\"]\)\[0\]")


def _find_violations(source: str, filename: str) -> list[tuple[int, str]]:
    """Find lines using toISOString().split('T')[0] for non-filename purposes."""
    violations = []
    for i, line in enumerate(source.splitlines(), start=1):
        if TO_ISO_DATE_RE.search(line):
            # Allow in filename-only contexts (download attribute assignments)
            if filename in FILENAME_ONLY_ALLOWLIST and ".download" in line:
                continue
            violations.append((i, line.strip()))
    return violations


class TestLocalDateFormatting:
    """Verify JS code uses local date components, not UTC toISOString()."""

    @pytest.fixture
    def js_files(self) -> dict[str, str]:
        """Load all .js files from the static directory."""
        return {
            f.name: f.read_text()
            for f in JS_DIR.glob("*.js")
            if f.is_file()
        }

    def test_no_toISOString_for_api_dates(self, js_files):
        """No JS file should use toISOString().split('T')[0] for API date parameters."""
        all_violations = []

        for filename, source in js_files.items():
            for line_no, line_text in _find_violations(source, filename):
                all_violations.append(f"{filename}:{line_no}: {line_text}")

        assert not all_violations, (
            "toISOString().split('T')[0] returns UTC dates, causing timezone bugs. "
            "Use Utils.formatDate(date, 'iso') instead.\n"
            "Violations:\n" + "\n".join(all_violations)
        )

    def test_utils_formatDate_iso_uses_local_components(self, js_files):
        """Utils.formatDate(date, 'iso') must use getFullYear/getMonth/getDate, not toISOString."""
        source = js_files["utils.js"]

        # Find the formatDate method and extract the iso branch
        format_date_match = re.search(
            r"static\s+formatDate\s*\([^)]*\)\s*\{(.*?)^\s{4}\}",
            source,
            re.DOTALL | re.MULTILINE,
        )
        assert format_date_match, "Utils.formatDate() method not found in utils.js"

        method_body = format_date_match.group(1)

        # The iso branch should NOT use toISOString
        assert not TO_ISO_DATE_RE.search(method_body), (
            "Utils.formatDate('iso') still uses toISOString().split('T')[0]. "
            "Must use local date components (getFullYear, getMonth, getDate)."
        )

        # The iso branch SHOULD use local date accessors
        assert "getFullYear" in method_body, (
            "Utils.formatDate('iso') should use date.getFullYear() for local year"
        )
        assert "getMonth" in method_body, (
            "Utils.formatDate('iso') should use date.getMonth() for local month"
        )
        assert "getDate" in method_body, (
            "Utils.formatDate('iso') should use date.getDate() for local day"
        )
