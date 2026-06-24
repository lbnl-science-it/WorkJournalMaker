#!/usr/bin/env python3
# ABOUTME: Tests that journal entry API responses do not expose server filesystem paths.
# ABOUTME: Ensures file_path is absent from all JournalEntryResponse API payloads.
"""
Information Disclosure Tests for file_path in API Responses

Verifies that GET endpoints for journal entries do not include a
file_path field in their JSON responses, preventing disclosure of
server-side filesystem layout to API consumers.
"""

import pytest
from datetime import date, timedelta

from fastapi.testclient import TestClient
from web.app import app


class TestFilePathNotExposedInEntryResponse:
    """Verify file_path is absent from all journal entry API endpoints."""

    def test_get_entry_by_date_excludes_file_path(self, isolated_app_client):
        """GET /api/entries/{date} must not return file_path."""
        client = isolated_app_client

        # Create an entry so the endpoint returns data
        entry_date = date.today() - timedelta(days=1)
        date_str = entry_date.isoformat()

        create_resp = client.post(
            f"/api/entries/{date_str}",
            json={"date": date_str, "content": "Test content for file_path disclosure check."},
        )
        assert create_resp.status_code in (200, 201), (
            f"Entry creation failed: {create_resp.status_code} {create_resp.text}"
        )

        get_resp = client.get(f"/api/entries/{date_str}")
        assert get_resp.status_code == 200

        data = get_resp.json()
        assert "file_path" not in data, (
            f"file_path must not be present in GET /api/entries/{date_str} response"
        )

    def test_list_entries_excludes_file_path(self, isolated_app_client):
        """GET /api/entries must not return file_path in any entry."""
        client = isolated_app_client

        entry_date = date.today() - timedelta(days=2)
        date_str = entry_date.isoformat()

        client.post(
            f"/api/entries/{date_str}",
            json={"date": date_str, "content": "Another test entry for list endpoint."},
        )

        list_resp = client.get("/api/entries")
        assert list_resp.status_code == 200

        data = list_resp.json()
        entries = data.get("entries", [])
        for entry in entries:
            assert "file_path" not in entry, (
                "file_path must not be present in any entry from GET /api/entries"
            )

    def test_recent_entries_excludes_file_path(self, isolated_app_client):
        """GET /api/entries/recent must not return file_path in any entry."""
        client = isolated_app_client

        entry_date = date.today() - timedelta(days=3)
        date_str = entry_date.isoformat()

        client.post(
            f"/api/entries/{date_str}",
            json={"date": date_str, "content": "Recent entries test."},
        )

        recent_resp = client.get("/api/entries/recent")
        assert recent_resp.status_code == 200

        data = recent_resp.json()
        entries = data.get("entries", [])
        for entry in entries:
            assert "file_path" not in entry, (
                "file_path must not be present in any entry from GET /api/entries/recent"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
