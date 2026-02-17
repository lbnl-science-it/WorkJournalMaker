# ABOUTME: Tests that the WebSocket client derives its URL from the browser location.
# ABOUTME: Verifies no hardcoded WebSocket URLs exist in the JavaScript client.

"""
Tests for WebSocket URL construction in websocket-client.js.

Ensures the WebSocket client dynamically derives its connection URL
from the browser's current location rather than using a hardcoded default.
"""

import re
from pathlib import Path

import pytest


# Path to the JavaScript file under test
JS_FILE = Path(__file__).parent.parent / "web" / "static" / "js" / "websocket-client.js"


class TestWebSocketUrl:
    """Verify that the WebSocket client uses dynamic URL derivation."""

    def test_js_file_exists(self):
        """The websocket-client.js file must exist."""
        assert JS_FILE.is_file(), f"Expected JS file at {JS_FILE}"

    def test_no_hardcoded_websocket_url(self):
        """Constructor must not contain a hardcoded ws:// or wss:// URL with a port."""
        source = JS_FILE.read_text()

        # Match patterns like ws://localhost:8000 or wss://127.0.0.1:9000
        hardcoded_url_pattern = re.compile(
            r"""['"]wss?://[^'"]*:\d+['"]""",
            re.IGNORECASE,
        )

        matches = hardcoded_url_pattern.findall(source)
        assert matches == [], (
            f"Found hardcoded WebSocket URL(s) in {JS_FILE.name}: {matches}. "
            "The URL should be derived from window.location instead."
        )

    def test_uses_window_location(self):
        """Constructor must derive the WebSocket URL from window.location."""
        source = JS_FILE.read_text()

        assert "window.location" in source, (
            f"{JS_FILE.name} must use window.location to derive the WebSocket URL."
        )

    def test_protocol_detection(self):
        """Constructor must select ws: or wss: based on page protocol."""
        source = JS_FILE.read_text()

        # Should reference the page protocol to decide ws vs wss
        assert "window.location.protocol" in source, (
            f"{JS_FILE.name} must inspect window.location.protocol "
            "to choose between ws: and wss:."
        )

    def test_host_from_location(self):
        """Constructor must use window.location.host for the connection target."""
        source = JS_FILE.read_text()

        assert "window.location.host" in source, (
            f"{JS_FILE.name} must use window.location.host "
            "so the WebSocket connects to the same host and port as the page."
        )

    def test_baseurl_default_is_null(self):
        """Constructor default for baseUrl must be null (not a string literal)."""
        source = JS_FILE.read_text()

        # Find the constructor signature
        constructor_match = re.search(
            r"constructor\s*\(\s*baseUrl\s*=\s*(.+?)\s*\)",
            source,
        )
        assert constructor_match is not None, (
            "Could not find constructor(baseUrl = ...) in the source."
        )

        default_value = constructor_match.group(1).strip()
        assert default_value == "null", (
            f"Expected constructor default baseUrl = null, got: {default_value}"
        )
