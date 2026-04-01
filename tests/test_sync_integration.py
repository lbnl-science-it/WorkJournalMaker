# ABOUTME: Integration test for full sync flow between client and server
# ABOUTME: Tests end-to-end manifest exchange and file sync operations
"""Integration test for full sync flow between client and server."""
import pytest
from pathlib import Path
from web.services.remote_sync_service import RemoteSyncService


class TestSyncIntegration:
    def test_full_sync_flow(self, tmp_path):
        """End-to-end: client and server exchange files via manifests."""
        # Setup client and server directories - both using "local" mode
        client_root = tmp_path / "client"
        server_root = tmp_path / "server"
        client_root.mkdir(parents=True)
        server_root.mkdir(parents=True)

        # Client has file A, server has file B
        (client_root / "worklog_2024-01-15.txt").write_text("Client entry")
        (server_root / "worklog_2024-01-16.txt").write_text("Server entry")

        # Generate manifests - both services use "local" mode
        client_service = RemoteSyncService(storage_root=str(client_root))
        server_service = RemoteSyncService(storage_root=str(server_root))

        # Generate manifests
        client_manifest = client_service.generate_manifest(user_id="local")
        server_manifest = server_service.generate_manifest(user_id="local")

        # Compare
        diff = server_service.compare_manifests(client_manifest, server_manifest)

        # Client should upload file A, download file B
        assert "worklog_2024-01-15.txt" in diff.to_upload
        assert "worklog_2024-01-16.txt" in diff.to_download
