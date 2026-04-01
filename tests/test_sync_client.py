# ABOUTME: Tests for sync client
# ABOUTME: Verifies HTTP client functionality for syncing local journal files with remote server
"""Tests for sync client."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sync_client import SyncClient


class TestSyncClient:
    def test_init_with_config(self):
        """SyncClient initializes with remote URL and token."""
        client = SyncClient(
            remote_url="https://journal.example.com",
            auth_token="test-token",
            local_root="/home/user/worklogs",
        )
        assert client.remote_url == "https://journal.example.com"
        assert client.auth_token == "test-token"

    def test_build_headers(self):
        """Client includes auth token in request headers."""
        client = SyncClient(
            remote_url="https://journal.example.com",
            auth_token="test-token",
            local_root="/tmp",
        )
        headers = client._build_headers()
        assert headers["X-API-Key"] == "test-token"

    def test_generate_local_manifest(self, tmp_path):
        """Client generates manifest from local files."""
        journal_file = tmp_path / "worklog_2024-01-15.txt"
        journal_file.write_text("Work notes.")

        client = SyncClient(
            remote_url="https://journal.example.com",
            auth_token="test-token",
            local_root=str(tmp_path),
        )
        manifest = client.generate_local_manifest()
        assert len(manifest.entries) == 1
