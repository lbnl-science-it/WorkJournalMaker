# ABOUTME: Tests that client-side JavaScript includes CSRF headers in state-changing fetch() calls.
# ABOUTME: Catches regressions where raw fetch() bypasses the ApiClient's default headers.

"""
Tests that client-side JavaScript files include the X-Requested-With CSRF header
in all state-changing fetch() calls, preventing 403 Forbidden errors.
"""

import re
from pathlib import Path

import pytest

JS_DIR = Path(__file__).resolve().parent.parent / "web" / "static" / "js"

# Matches fetch() calls that specify a method (POST, PUT, DELETE, PATCH)
STATE_CHANGING_FETCH_RE = re.compile(
    r"fetch\([^)]*\{[^}]*method\s*:\s*['\"](?:POST|PUT|DELETE|PATCH)['\"]",
    re.DOTALL,
)

# Matches X-Requested-With in a headers block
CSRF_HEADER_RE = re.compile(r"['\"]X-Requested-With['\"]")


def _extract_fetch_blocks(source: str) -> list[tuple[int, str]]:
    """Extract (line_number, block_text) for each state-changing fetch() call."""
    blocks = []
    for match in STATE_CHANGING_FETCH_RE.finditer(source):
        start = match.start()
        line_no = source[:start].count("\n") + 1
        # Grab enough context to capture the headers object
        end = source.find(");", start)
        if end == -1:
            end = len(source)
        blocks.append((line_no, source[start:end]))
    return blocks


class TestClientCSRFHeaders:
    """Verify all JS fetch() calls with state-changing methods include CSRF header."""

    @pytest.fixture
    def js_files(self) -> dict[str, str]:
        """Load all .js files from the static directory."""
        return {
            f.name: f.read_text()
            for f in JS_DIR.glob("*.js")
            if f.is_file()
        }

    def test_all_state_changing_fetches_have_csrf_header(self, js_files):
        """Every POST/PUT/DELETE/PATCH fetch() must include X-Requested-With."""
        violations = []

        for filename, source in js_files.items():
            # Skip api.js — it's the centralized client with correct headers
            if filename == "api.js":
                continue

            for line_no, block in _extract_fetch_blocks(source):
                if not CSRF_HEADER_RE.search(block):
                    violations.append(f"{filename}:{line_no}")

        assert not violations, (
            f"State-changing fetch() calls missing X-Requested-With header: "
            f"{', '.join(violations)}"
        )

    def test_dashboard_create_entry_has_csrf_header(self, js_files):
        """dashboard.js createNewEntry() must include X-Requested-With."""
        source = js_files["dashboard.js"]
        blocks = _extract_fetch_blocks(source)

        post_blocks = [b for b in blocks if "POST" in b[1]]
        assert post_blocks, "dashboard.js should have a POST fetch() call"

        for line_no, block in post_blocks:
            assert CSRF_HEADER_RE.search(block), (
                f"dashboard.js:{line_no} — POST fetch() missing X-Requested-With"
            )

    def test_editor_save_entry_has_csrf_header(self, js_files):
        """editor.js saveEntry() must include X-Requested-With."""
        source = js_files["editor.js"]
        blocks = _extract_fetch_blocks(source)

        post_blocks = [b for b in blocks if "POST" in b[1]]
        assert post_blocks, "editor.js should have a POST fetch() call"

        for line_no, block in post_blocks:
            assert CSRF_HEADER_RE.search(block), (
                f"editor.js:{line_no} — POST fetch() missing X-Requested-With"
            )
