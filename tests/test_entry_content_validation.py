# ABOUTME: Tests that entry content POST endpoint enforces size limits.
# ABOUTME: Validates server-side max_length constraint on content body.
"""
Tests for Issue #6: Entry content POST must enforce a size limit.

The POST /{entry_date}/content endpoint must reject content exceeding
the configured maximum length to prevent memory exhaustion.
"""

import pytest
from datetime import date


class TestEntryContentSizeLimit:
    """Verify content size limit is enforced server-side."""

    def test_oversized_content_rejected_via_update_endpoint(self, isolated_app_client):
        """Content exceeding 500,000 characters must be rejected on /content endpoint."""
        oversized = "x" * 500_001
        response = isolated_app_client.post(
            "/api/entries/2026-01-15/content",
            json={"content": oversized}
        )
        assert response.status_code == 422, \
            f"Expected 422 for oversized content, got {response.status_code}"

    def test_oversized_content_rejected_via_create_endpoint(self, isolated_app_client):
        """Content exceeding 500,000 characters must be rejected on main POST endpoint."""
        oversized = "x" * 500_001
        response = isolated_app_client.post(
            "/api/entries/2026-01-15",
            json={"date": "2026-01-15", "content": oversized}
        )
        assert response.status_code == 422, \
            f"Expected 422 for oversized content, got {response.status_code}"

    def test_normal_content_accepted(self, isolated_app_client):
        """Normal-length content must pass validation on /content endpoint."""
        response = isolated_app_client.post(
            "/api/entries/2026-01-15/content",
            json={"content": "Today I worked on the security fixes."}
        )
        # Should not be 422 (may be 200 or other status depending on file state)
        assert response.status_code != 422

    def test_empty_content_accepted(self, isolated_app_client):
        """Empty content is a valid entry (clearing content)."""
        response = isolated_app_client.post(
            "/api/entries/2026-01-15/content",
            json={"content": ""}
        )
        assert response.status_code != 422

    def test_missing_content_field_rejected(self, isolated_app_client):
        """Missing content field should be rejected."""
        response = isolated_app_client.post(
            "/api/entries/2026-01-15/content",
            json={}
        )
        assert response.status_code == 422
