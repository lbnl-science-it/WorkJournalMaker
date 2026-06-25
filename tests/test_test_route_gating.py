# ABOUTME: Tests that test/debug pages are not accessible in production mode.
# ABOUTME: Validates that /test route and test static files are gated behind WORK_JOURNAL_DEBUG.
"""
Tests for Issue #7: Test/debug pages must not be accessible in production.

The /test route should only be registered when WORK_JOURNAL_DEBUG=1.
The test_date_parsing_fix.html static file should not exist in the
static directory at all (it is a dev artifact).
"""

import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient


class TestDebugPagesNotAccessibleInProduction:
    """Verify test/debug pages are gated behind debug mode."""

    def test_test_route_returns_404_in_production_mode(self, isolated_app_client):
        """The /test route must return 404 when WORK_JOURNAL_DEBUG is not set."""
        # Default environment has no WORK_JOURNAL_DEBUG set
        response = isolated_app_client.get("/test")
        assert response.status_code == 404, \
            f"Expected 404 for /test in production mode, got {response.status_code}"

    def test_static_test_file_not_present(self):
        """The test_date_parsing_fix.html dev artifact must not exist in static/."""
        static_dir = Path(__file__).parent.parent / "web" / "static"
        test_file = static_dir / "test_date_parsing_fix.html"
        assert not test_file.exists(), \
            f"Dev artifact {test_file} should not be in the static directory"

    def test_debug_mode_flag_defaults_to_false(self):
        """The _DEBUG_MODE sentinel must be False without the env var."""
        from web.app import _DEBUG_MODE
        assert _DEBUG_MODE is False, \
            "_DEBUG_MODE should default to False without WORK_JOURNAL_DEBUG"
